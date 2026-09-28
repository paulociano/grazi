"""Optional Windows-local wake phrase. Only one microphone consumer runs at a time."""
import subprocess
import sys
import threading
from pathlib import Path
from PySide6.QtCore import QObject, Signal


class WakeListener(QObject):
    detected = Signal()
    failed = Signal(str)
    finished = Signal(int, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = False
        self.token = 0
        self.process = None
        self.lock = threading.Lock()
        self.finished.connect(self._finished)

    def start(self):
        if self.running:
            return
        if sys.platform != 'win32':
            self.failed.emit('A ativação por voz desta versão requer Windows e reconhecedor local pt-BR.')
            return
        self.running = True
        self.token += 1
        token = self.token
        def run():
            try:
                script = (Path(__file__).parent / 'wake_word.ps1').read_text(encoding='utf-8')
                with self.lock:
                    if token != self.token:
                        return
                    process = subprocess.Popen(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', script],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
                    self.process = process
                output, error = process.communicate()
                if process.returncode == 0 and output.decode('utf-8', errors='replace').strip() == 'WAKE':
                    result = 'wake'
                else:
                    detail = error.decode('utf-8', errors='replace').strip().splitlines()[-1:] or ['código de saída inesperado']
                    result = 'error:' + detail[0][:300]
            except Exception as exc:
                result = 'error:' + str(exc)[:300]
            self.finished.emit(token, result)
        threading.Thread(target=run, daemon=True).start()

    def stop(self):
        with self.lock:
            self.token += 1
            self.running = False
            process, self.process = self.process, None
            if process is not None and process.poll() is None:
                process.terminate()
        # The microphone must be released before a dictation process starts.
        if process is not None:
            try:
                process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                process.kill()  # Only our own microphone helper, never a user's app.
                process.wait(timeout=1)

    def _finished(self, token, result):
        if token != self.token:
            return
        self.running = False
        self.process = None
        if result == 'wake':
            self.detected.emit()
        else:
            detail = result.removeprefix('error:').strip()
            self.failed.emit('A ativação por voz não iniciou. Confira o microfone, a permissão do Windows e um reconhecedor System.Speech pt-BR. Detalhe: ' + detail + '. A Grazi tentará novamente; a digitação e o ditado manual continuam disponíveis.')
