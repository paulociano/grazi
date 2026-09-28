"""Sentence-sized speech, cancellable online synthesis and offline Windows TTS."""
import asyncio
import re
import tempfile
import threading
from pathlib import Path

from PySide6.QtCore import QObject, Signal, QLocale, QUrl, QTimer
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtTextToSpeech import QTextToSpeech


def speech_chunks(text, limit=180):
    """Bound balloon text without dropping words, even for long unbroken input."""
    result = []
    for sentence in re.split(r'(?<=[.!?])\s+|\n+', text.strip()):
        while len(sentence) > limit:
            split = sentence.rfind(' ', 0, limit + 1)
            if split < 1:
                split = limit
            result.append(sentence[:split])
            sentence = sentence[split:].lstrip()
        if sentence:
            result.append(sentence)
    return result


class Speech(QObject):
    speaking = Signal(bool)
    page = Signal(int)
    error = Signal(str)
    ready = Signal(int, str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.native = QTextToSpeech(self)
        self.native.setLocale(QLocale('pt_BR'))
        self.native.stateChanged.connect(self._native_state)
        self.player = QMediaPlayer(self)
        self.audio = QAudioOutput(self)
        self.player.setAudioOutput(self.audio)
        self.player.mediaStatusChanged.connect(self._media_status)
        self.player.playbackStateChanged.connect(
            lambda state: self.speaking.emit(state == QMediaPlayer.PlaybackState.PlayingState))
        self.player.errorOccurred.connect(self._media_error)
        self.ready.connect(self._ready)
        self.token = 0
        self.active = False
        self.index = 0
        self.chunks = []
        self.path = None
        self.cancel = threading.Event()
        self.engine = 'windows'

    def stop(self):
        self.token += 1
        self.cancel.set()
        self.active = False
        self.native.stop()
        self.player.stop()
        self.player.setSource(QUrl())
        self._delete_audio()
        self.speaking.emit(False)

    def _delete_audio(self):
        if self.path:
            Path(self.path).unlink(missing_ok=True)
            self.path = None

    def say(self, text, engine='windows'):
        self.stop()
        self.chunks = speech_chunks(text)
        self.engine = engine
        self.index = 0
        self.active = bool(self.chunks)
        self.cancel = threading.Event()
        if self.active:
            self._next()

    def _next(self):
        if not self.active:
            return
        if self.index >= len(self.chunks):
            self.stop()
            return
        text = self.chunks[self.index]
        self.page.emit(self.index)
        if self.engine == 'windows':
            if self.native.state() == QTextToSpeech.State.Error:
                self._fail('Voz do Windows indisponível. Instale uma voz pt-BR ou escolha Francisca online.')
                return
            self.native.say(text)
            return
        token, cancelled = self.token, self.cancel
        def run():
            path = None
            try:
                import edge_tts
                with tempfile.NamedTemporaryFile(prefix='grazi-voz-', suffix='.mp3', delete=False) as file:
                    path = file.name
                async def synthesize():
                    await edge_tts.Communicate(text, 'pt-BR-FranciscaNeural').save(path)
                asyncio.run(asyncio.wait_for(synthesize(), timeout=30))
                if cancelled.is_set():
                    Path(path).unlink(missing_ok=True)
                    return
                self.ready.emit(token, path, '')
            except Exception:
                if path:
                    Path(path).unlink(missing_ok=True)
                if not cancelled.is_set():
                    self.ready.emit(token, '', 'A voz online não respondeu. Confira a internet ou selecione a voz do Windows. O texto continua disponível.')
        threading.Thread(target=run, daemon=True).start()

    def _ready(self, token, path, error):
        if token != self.token or not self.active:
            if path:
                Path(path).unlink(missing_ok=True)
            return
        if error:
            self._fail(error)
            return
        self.path = path
        self.player.setSource(QUrl.fromLocalFile(path))
        self.player.play()

    def _advance(self):
        self.index += 1
        token = self.token
        QTimer.singleShot(0, lambda: self._next() if token == self.token else None)

    def _native_state(self, state):
        if not self.active or self.engine != 'windows':
            return
        self.speaking.emit(state == QTextToSpeech.State.Speaking)
        if state == QTextToSpeech.State.Ready:
            self._advance()
        elif state == QTextToSpeech.State.Error:
            self._fail('Não consegui reproduzir a voz do Windows. Confira a voz pt-BR instalada.')

    def _media_status(self, status):
        if self.active and self.engine == 'edge' and status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.player.setSource(QUrl())
            self._delete_audio()
            self._advance()

    def _media_error(self, error, message):
        if self.active and self.engine == 'edge' and error != QMediaPlayer.Error.NoError:
            self._fail('Não consegui reproduzir o áudio. Tente novamente ou use a voz do Windows.')

    def _fail(self, message):
        self.stop()
        self.error.emit(message)
