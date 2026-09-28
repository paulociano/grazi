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
                output, _ = process.communicate()
                result = 'wake' if process.returncode == 0 and output.decode('utf-8', errors='replace').strip() == 'WAKE' else 'error'
            except Exception:
                result = 'error'
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
            self.failed.emit('Não consegui ativar a escuta local. Confira o microfone e a instalação de um reconhecedor System.Speech pt-BR no Windows. A ativação foi desligada; digitação e ditado manual continuam disponíveis.')
