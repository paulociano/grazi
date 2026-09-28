import math
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, Signal, QObject, QPoint, QRectF, QLocale
from PySide6.QtGui import QColor, QPainter, QPixmap, QIcon, QAction, QFont
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QTextEdit, QComboBox, QCheckBox, QSlider,
    QDialog, QFormLayout, QMenu, QSystemTrayIcon, QMessageBox)
from PySide6.QtTextToSpeech import QTextToSpeech
from core import load_state, save_state, list_models, chat

ROOT = Path(__file__).resolve().parent
STYLE = """
QWidget { background: #191b22; color: #f5f0e8; font-family: 'Segoe UI'; font-size: 14px; }
QLabel#title { font-size: 29px; font-weight: 700; color: #edb273; }
QLabel#sub { color: #acadb8; font-size: 12px; }
QPushButton { background: #30333e; border: 0; border-radius: 9px; padding: 10px 14px; }
QPushButton:hover { background: #414653; }
QPushButton:disabled { color: #787b85; }
QPushButton#primary { background: #edb273; color: #251d16; font-weight: 600; }
QLineEdit, QTextEdit, QComboBox { background: #242731; border: 1px solid #414551;
 border-radius: 9px; padding: 9px; selection-background-color: #8b5d39; }
QCheckBox { padding: 4px; }
QMenu { background: #242731; padding: 8px; }
QMenu::item { padding: 8px 20px; }
QMenu::item:selected { background: #414653; }
"""


class Events(QObject):
    answer = Signal(str, bool)
    models = Signal(list, str)
    heard = Signal(str, bool)


class Mascot(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.c = controller
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent")
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.asset_path = ROOT / "assets" / "grazi.png"
        if not self.asset_path.is_file():
            raise RuntimeError(f"Arquivo da Grazi não encontrado: {self.asset_path}")
        self.pix = QPixmap(str(self.asset_path))
        if self.pix.isNull():
            raise RuntimeError(f"Arquivo da Grazi não pôde ser carregado pelo Qt: {self.asset_path}")
        self.phase = 0
        self.status = "Vamos conversar?"
        self.drag = None
        self.resize_pet()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(50)
        self.setToolTip("Arraste para mover • Duplo clique para conversar • Botão direito para opções")

    def resize_pet(self):
        size = self.c.state["size"]
        self.setFixedSize(size, int(size * 1.23) + 48)

    def tick(self):
        self.phase += .07
        if self.c.state["motion"]:
            self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        bob = math.sin(self.phase) * 2 if self.c.state["motion"] else 0
        p.setBrush(QColor("#242731")); p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(QRectF(12, 4, self.width()-24, 31), 15, 15)
        p.setPen(QColor("#f5d1a5")); p.setFont(QFont("Segoe UI", 10))
        p.drawText(QRectF(12, 4, self.width()-24, 31), Qt.AlignmentFlag.AlignCenter, self.status)
        area = QRectF(9, 42 + bob, self.width()-18, self.height()-51)
        fitted = self.pix.size().scaled(area.size().toSize(), Qt.AspectRatioMode.KeepAspectRatio)
        rect = QRectF(area.x()+(area.width()-fitted.width())/2, area.y(), fitted.width(), fitted.height())
        p.drawPixmap(rect, self.pix, QRectF(self.pix.rect()))
        p.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag = event.globalPosition().toPoint() - self.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        if self.drag is not None:
            self.move(event.globalPosition().toPoint()-self.drag)

    def mouseReleaseEvent(self, event):
        self.drag = None
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.c.state["position"] = [self.x(), self.y()]
        self.c.persist()

    def mouseDoubleClickEvent(self, event):
        self.c.show_chat()

    def contextMenuEvent(self, event):
        self.c.menu().exec(event.globalPos())


class Settings(QDialog):
    def __init__(self, c):
        super().__init__(c.window)
        self.c = c
        self.setWindowTitle("Personalizar a Grazi")
        self.resize(470, 500)
        layout = QFormLayout(self)
        self.model = QComboBox(); self.model.setEditable(True)
        self.model.addItems(c.available_models or [c.state["model"]])
        self.model.setCurrentText(c.state["model"])
        layout.addRow("Modelo local", self.model)
        hint = QLabel("Abra o Ollama e baixe um modelo Qwen.\nO botão Conectar atualiza a lista de modelos.")
        hint.setObjectName("sub"); layout.addRow(hint)
        self.voice = QCheckBox("Ler respostas em voz alta")
        self.voice.setChecked(c.state["voice"]); layout.addRow(self.voice)
        self.motion = QCheckBox("Movimento suave do mascote")
        self.motion.setChecked(c.state["motion"]); layout.addRow(self.motion)
        self.size = QSlider(Qt.Orientation.Horizontal); self.size.setRange(200, 460)
        self.size.setValue(c.state["size"]); layout.addRow("Tamanho", self.size)
        self.memory = QTextEdit(); self.memory.setPlainText(c.state["memory"])
        self.memory.setPlaceholderText("Preferências que a Grazi deve lembrar")
        layout.addRow("Memória editável", self.memory)
        note = QLabel("Salva neste computador. Enviada ao modelo local ao conversar.")
        note.setObjectName("sub"); note.setWordWrap(True); layout.addRow(note)
        button = QPushButton("Salvar"); button.setObjectName("primary")
        button.clicked.connect(self.save); layout.addRow(button)

    def save(self):
        model = self.model.currentText().strip()
        if not model or "cloud" in model.lower():
            QMessageBox.warning(self, "Modelo local", "Informe o nome de um modelo local do Ollama.")
            return
        self.c.state.update(model=model, voice=self.voice.isChecked(), motion=self.motion.isChecked(),
            size=self.size.value(), memory=self.memory.toPlainText()[:8000])
        self.c.pet.resize_pet(); self.c.pet.update(); self.c.place_pet()
        self.c.persist(); self.c.update_label(); self.accept()


class ChatWindow(QWidget):
    def __init__(self, c):
        super().__init__(); self.c = c
        self.setWindowTitle("Grazi • sua companheira")
        self.resize(510, 660)
        self.setMinimumSize(410, 480)
        layout = QVBoxLayout(self); layout.setContentsMargins(24, 22, 24, 22); layout.setSpacing(13)
        heading = QLabel("Oi, Paulo. Sou a Grazi."); heading.setObjectName("title"); layout.addWidget(heading)
        self.status = QLabel(); self.status.setObjectName("sub"); self.status.setWordWrap(True); layout.addWidget(self.status)
        bar = QHBoxLayout()
        for text, fn in [("Conectar", c.connect_models), ("Configurar", c.settings), ("Limpar", c.clear)]:
            button = QPushButton(text); button.clicked.connect(fn); bar.addWidget(button)
        layout.addLayout(bar)
        self.log = QTextEdit(); self.log.setReadOnly(True); layout.addWidget(self.log, 1)
        self.input = QLineEdit(); self.input.setPlaceholderText("Converse com a Grazi…")
        self.input.setMaxLength(6000); self.input.returnPressed.connect(c.send); layout.addWidget(self.input)
        actions = QHBoxLayout()
        self.mic = QPushButton("Ditado"); self.mic.clicked.connect(c.listen); actions.addWidget(self.mic)
        stop = QPushButton("Parar voz"); stop.clicked.connect(c.stop_voice); actions.addWidget(stop)
        self.send_button = QPushButton("Enviar"); self.send_button.setObjectName("primary")
        self.send_button.clicked.connect(c.send); actions.addWidget(self.send_button)
        layout.addLayout(actions)
        help_label = QLabel("Duplo clique na Grazi abre esta conversa. Fechar a janela mantém o mascote.")
        help_label.setObjectName("sub"); help_label.setWordWrap(True); layout.addWidget(help_label)

    def line(self, who, text):
        self.log.moveCursor(self.log.textCursor().MoveOperation.End)
        # Plain text only: model output cannot create active links or HTML.
        self.log.insertPlainText(f"{who}\n{text}\n\n")
        self.log.ensureCursorVisible()


class Controller:
    def __init__(self, app):
        self.app = app; self.state = load_state(); self.available_models = []
        self.busy = False; self.listening = False; self.connecting = False
        self.events = Events(); self.events.answer.connect(self.on_answer)
        self.events.models.connect(self.on_models); self.events.heard.connect(self.on_heard)
        self.tts = QTextToSpeech(app)
        self.tts.setLocale(QLocale("pt_BR"))
        self.tts.stateChanged.connect(self.voice_state)
        self.window = ChatWindow(self)
        self.pet = Mascot(self)
        self.tray = QSystemTrayIcon(QIcon(str(ROOT / "assets/grazi.png")), app)
        self.tray.setToolTip("Grazi • duplo clique para conversar")
        self.tray.setContextMenu(self.menu())
        self.tray.activated.connect(lambda reason: self.show_chat() if reason == QSystemTrayIcon.ActivationReason.DoubleClick else None)
        if QSystemTrayIcon.isSystemTrayAvailable(): self.tray.show()
        self.place_pet(); self.pet.show(); self.update_label()
        for msg in self.state["history"]:
            self.window.line("Você" if msg["role"] == "user" else "Grazi", msg["content"])
        if not self.state["history"]:
            self.window.line("Grazi", "Minha casinha está pronta! Abra o Ollama, baixe um Qwen e clique em Conectar. Em Configurar você escolhe o modelo e as preferências que devo lembrar.")

    def persist(self):
        try: save_state(self.state)
        except OSError:
            self.window.status.setText("Não consegui salvar as preferências. Verifique a permissão da pasta de dados.")

    def update_label(self):
        self.window.status.setText(f"IA local · {self.state['model']} · Ollama em 127.0.0.1:11434")

    def place_pet(self):
        pos = self.state.get("position")
        screen = self.app.primaryScreen()
        if pos:
            screen = self.app.screenAt(QPoint(*pos)) or screen
        bounds = screen.availableGeometry()
        x, y = pos or [bounds.right()-self.pet.width()-25, bounds.bottom()-self.pet.height()-10]
        self.pet.move(max(bounds.left(), min(x, bounds.right()-self.pet.width()+1)),
                      max(bounds.top(), min(y, bounds.bottom()-self.pet.height()+1)))

    def menu(self):
        menu = QMenu()
        for title, callback in [("Conversar", self.show_chat), ("Personalizar", self.settings),
                                ("Mostrar Grazi", self.show_pet), ("Ocultar Grazi", self.hide_pet),
                                ("Sair", self.app.quit)]:
            action = QAction(title, menu); action.triggered.connect(callback); menu.addAction(action)
        return menu

    def show_pet(self): self.pet.show()
    def hide_pet(self):
        if self.tray.isVisible(): self.pet.hide()
        else: self.show_chat()
    def show_chat(self):
        self.window.show(); self.window.raise_(); self.window.activateWindow(); self.window.input.setFocus()
    def settings(self): Settings(self).exec()
    def clear(self):
        if self.busy or self.listening: return
        if QMessageBox.question(self.window, "Limpar conversa", "Apagar o histórico local? A memória editável será mantida.") == QMessageBox.StandardButton.Yes:
            self.state["history"] = []; self.window.log.clear(); self.persist()
    def set_status(self, text): self.pet.status = text; self.pet.update()
    def stop_voice(self): self.tts.stop()
    def voice_state(self, state):
        if state == QTextToSpeech.State.Speaking: self.set_status("Falando com você")
        elif not self.busy and not self.listening: self.set_status("Estou por aqui")

    def connect_models(self):
        if self.connecting: return
        self.connecting = True; self.window.status.setText("Procurando modelos locais…")
        def run():
            try: self.events.models.emit(list_models(), "")
            except Exception as exc: self.events.models.emit([], str(exc))
        threading.Thread(target=run, daemon=True).start()

    def on_models(self, models, error):
        self.connecting = False; self.available_models = models
        if error: self.window.status.setText(error)
        elif not models: self.window.status.setText("Ollama conectado, sem modelos locais. Baixe um Qwen primeiro.")
        else:
            if self.state["model"] not in models:
                self.state["model"] = next((m for m in models if m.startswith("qwen")), models[0]); self.persist()
            self.update_label(); self.window.status.setText(self.window.status.text()+" · Conectado")

    def send(self):
        text = self.window.input.text().strip()
        if not text or self.busy or self.listening: return
        self.stop_voice(); self.busy = True
        self.window.send_button.setEnabled(False); self.window.mic.setEnabled(False)
        self.window.input.clear(); self.window.line("Você", text); self.set_status("Pensando…")
        self.pending = {"role": "user", "content": text}
        model, memory = self.state["model"], self.state["memory"]
        history = self.state["history"] + [self.pending]
        def run():
            try: self.events.answer.emit(chat(model, memory, history), True)
            except Exception as exc: self.events.answer.emit(str(exc), False)
        threading.Thread(target=run, daemon=True).start()

    def on_answer(self, text, ok):
        self.busy = False; self.window.send_button.setEnabled(True); self.window.mic.setEnabled(True)
        self.window.line("Grazi" if ok else "Conexão", text); self.set_status("Estou por aqui" if ok else "Confira a conexão")
        if ok:
            self.state["history"] = (self.state["history"] + [self.pending, {"role": "assistant", "content": text}])[-40:]
            self.persist()
            if self.state["voice"]:
                if self.tts.state() == QTextToSpeech.State.Error:
                    self.window.line("Voz", "Voz indisponível. Instale uma voz de português nas configurações do Windows.")
                else: self.tts.say(text)
        else: self.window.input.setText(self.pending["content"])

    def listen(self):
        if self.busy or self.listening: return
        self.stop_voice()
        if sys.platform != "win32":
            self.window.line("Ditado", "O ditado desta versão usa o reconhecimento instalado no Windows."); return
        self.listening = True; self.set_status("Ouvindo por até 10 segundos")
        self.window.mic.setEnabled(False); self.window.send_button.setEnabled(False)
        def run():
            try:
                result = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
                    (ROOT / "dictation.ps1").read_text(encoding="utf-8")],
                    capture_output=True, timeout=18, creationflags=subprocess.CREATE_NO_WINDOW)
                output = result.stdout.decode("utf-8", errors="replace").strip()
                if result.returncode or not output:
                    raise RuntimeError("Ditado local indisponível ou sem fala detectada. Clique no campo e use Win+H, ou digite. O ditado Win+H pode usar serviços online do Windows.")
                self.events.heard.emit(output, True)
            except Exception as exc: self.events.heard.emit(str(exc), False)
        threading.Thread(target=run, daemon=True).start()

    def on_heard(self, text, ok):
        self.listening = False; self.window.mic.setEnabled(True); self.window.send_button.setEnabled(True)
        self.set_status("Revise e envie" if ok else "Estou por aqui")
        if ok: self.window.input.setText(text); self.window.input.setFocus()
        else: self.window.line("Ditado", text)


def main():
    app = QApplication(sys.argv); app.setApplicationName("Grazi")
    app.setQuitOnLastWindowClosed(False); app.setStyleSheet(STYLE)
    app.setWindowIcon(QIcon(str(ROOT / "assets/grazi.png")))
    controller = Controller(app)
    controller.show_chat()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

