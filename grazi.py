import math
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, Signal, QObject, QPoint, QRectF, QEvent
from PySide6.QtGui import QColor, QPainter, QPixmap, QIcon, QAction, QFont
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QTextEdit, QComboBox, QCheckBox, QSlider,
    QDialog, QFormLayout, QSpinBox, QFileDialog, QScrollArea, QMenu, QSystemTrayIcon, QMessageBox)
from assistance import AssistantActions
from wake import WakeListener
from idle import IdleState
from speech import Speech
from balloon import SpeechBalloon
from core import load_state, save_state, list_models, chat, local_command

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


def pose_parameters(phase, motion, listening, thinking, speaking):
    """Small state-based motion that stays cheap on integrated graphics."""
    if not motion:
        return {"angle": 0.0, "scale": 1.0, "indicator": None, "pulse": 0.0}
    wave = math.sin(phase)
    if listening:
        return {"angle": wave * 2.0, "scale": 1.012 + wave * .004,
                "indicator": "#edb273", "pulse": (wave + 1) * 2.0}
    if thinking:
        return {"angle": wave * .8, "scale": 1.006 + wave * .003,
                "indicator": "#65c7d9", "pulse": (wave + 1) * 2.0}
    if speaking:
        return {"angle": wave * 1.0, "scale": 1.01 + wave * .004,
                "indicator": "#ef729b", "pulse": (wave + 1) * 2.5}
    return {"angle": wave * .45, "scale": 1.0 + wave * .002,
            "indicator": None, "pulse": 0.0}


class Events(QObject):
    answer = Signal(str, bool)
    models = Signal(list, str)
    heard = Signal(str, bool)


class ActivityFilter(QObject):
    def __init__(self, controller):
        super().__init__(controller.app)
        self.c = controller

    def eventFilter(self, obj, event):
        if event.type() in (QEvent.Type.MouseButtonPress, QEvent.Type.KeyPress, QEvent.Type.Wheel):
            self.c.touch()
        return False


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
        self.frames = []
        atlas = QPixmap(str(ROOT / "assets/grazi-expressions.png"))
        if not atlas.isNull() and atlas.size().width() == 1141 and atlas.size().height() == 1378:
            self.frames = [atlas.copy(x, y, 510, 675) for x, y in
                           [(96, 8), (621, 8), (96, 694), (621, 694)]]
        self.sleep_pix = QPixmap(str(ROOT / "assets/grazi-sleep.png"))
        self.sleep_blend = 0.0
        self.phase = 0
        self.status = "Vamos conversar?"
        self.drag = None
        self.resize_pet()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(50)
        self.setToolTip("Arraste para mover • Duplo clique para abrir o balão • Botão direito para conversa completa")

    def resize_pet(self):
        size = self.c.state["size"]
        self.setFixedSize(size, int(size * 1.23) + 48)

    def tick(self):
        self.c.sync_wake()
        self.phase += .07
        was_sleeping = self.c.idle.sleeping
        sleeping = self.c.idle.update(self.c.busy or self.c.listening or self.c.connecting or self.c.speech.active or self.drag is not None, enabled=self.c.state["auto_sleep"])
        if sleeping and not was_sleeping:
            self.c.balloon.hide()
        target = 1.0 if sleeping and not self.sleep_pix.isNull() else 0.0
        previous = self.sleep_blend
        if self.c.state["motion"]:
            self.sleep_blend += max(-.08, min(.08, target-self.sleep_blend))
        else:
            self.sleep_blend = target
        if self.c.state["motion"] or previous != self.sleep_blend:
            self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        bob = math.sin(self.phase) * 2 if self.c.state["motion"] else 0
        p.setOpacity(1.0-self.sleep_blend)
        p.setBrush(QColor("#242731")); p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(QRectF(12, 4, self.width()-24, 31), 15, 15)
        p.setPen(QColor("#f5d1a5")); p.setFont(QFont("Segoe UI", 10))
        p.drawText(QRectF(12, 4, self.width()-24, 31), Qt.AlignmentFlag.AlignCenter, self.status)
        area = QRectF(9, 42 + bob, self.width()-18, self.height()-51)
        pix = self.pix
        if self.frames:
            frame = 0
            if self.c.state["motion"]:
                if self.c.speaking: frame = 2 if int(time.monotonic() * 6) % 2 else 0
                elif self.c.listening: frame = 3
                elif time.monotonic() % 4.7 < .18: frame = 1
            pix = self.frames[frame]
        fitted = pix.size().scaled(area.size().toSize(), Qt.AspectRatioMode.KeepAspectRatio)
        rect = QRectF(area.x()+(area.width()-fitted.width())/2, area.y(), fitted.width(), fitted.height())
        pose = pose_parameters(self.phase, self.c.state["motion"], self.c.listening,
                               self.c.busy, self.c.speaking)
        if pose["indicator"]:
            glow = 9 + pose["pulse"]
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(pose["indicator"]))
            p.setOpacity(.10 * (1.0-self.sleep_blend))
            p.drawEllipse(rect.adjusted(-glow, -glow, glow, glow))
            p.setOpacity(1.0-self.sleep_blend)
        p.save()
        p.translate(rect.center().x(), rect.bottom())
        p.rotate(pose["angle"])
        p.scale(pose["scale"], pose["scale"])
        p.translate(-rect.center().x(), -rect.bottom())
        p.drawPixmap(rect, pix, QRectF(pix.rect()))
        p.restore()
        if self.sleep_blend > 0:
            area = QRectF(9, 42, self.width()-18, self.height()-51)
            fitted = self.sleep_pix.size().scaled(area.size().toSize(), Qt.AspectRatioMode.KeepAspectRatio)
            rect = QRectF(area.center().x()-fitted.width()/2, area.bottom()-fitted.height(), fitted.width(), fitted.height())
            breath = math.sin(time.monotonic()*1.6) * .007 if self.c.state["motion"] else 0
            p.save(); p.setOpacity(self.sleep_blend)
            p.translate(rect.center().x(), rect.bottom())
            p.scale(1.0, 1.0+breath)
            p.translate(-rect.center().x(), -rect.bottom())
            p.drawPixmap(rect, self.sleep_pix, QRectF(self.sleep_pix.rect()))
            p.restore()
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
        self.c.show_balloon()

    def moveEvent(self, event):
        if hasattr(self.c, "balloon"): self.c.balloon.reanchor()
        super().moveEvent(event)

    def contextMenuEvent(self, event):
        self.c.menu().exec(event.globalPos())


class Settings(QDialog):
    def __init__(self, c):
        super().__init__(c.window)
        self.c = c
        self.setWindowTitle("Personalizar a Grazi")
        self.resize(470, 500)
        outer = QVBoxLayout(self)
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        content = QWidget(); layout = QFormLayout(content)
        scroll.setWidget(content); outer.addWidget(scroll)
        self.model = QComboBox(); self.model.setEditable(True)
        self.model.addItems(c.available_models or [c.state["model"]])
        self.model.setCurrentText(c.state["model"])
        layout.addRow("Modelo local", self.model)
        hint = QLabel("Abra o Ollama e baixe um modelo Qwen.\nO botão Conectar atualiza a lista de modelos.")
        hint.setObjectName("sub"); layout.addRow(hint)
        self.voice = QCheckBox("Ler respostas em voz alta")
        self.voice.setChecked(c.state["voice"]); layout.addRow(self.voice)
        self.engine = QComboBox()
        self.engine.addItem("Windows — instalada no computador", "windows")
        self.engine.addItem("Francisca — feminina pt-BR (online)", "edge")
        self.engine.setCurrentIndex(1 if c.state["voice_engine"] == "edge" else 0)
        layout.addRow("Voz", self.engine)
        privacy = QLabel("Francisca usa internet e envia o texto da fala ao serviço da Microsoft. A IA continua no Ollama local. A voz do Windows não usa esse serviço.")
        privacy.setWordWrap(True); privacy.setObjectName("sub"); layout.addRow(privacy)
        test = QPushButton("Ouvir amostra da voz selecionada")
        test.clicked.connect(self.test_voice); layout.addRow(test)
        self.wake_word = QCheckBox('Ativar ao ouvir “Grazi” (microfone local)')
        self.wake_word.setChecked(c.state['wake_word']); layout.addRow(self.wake_word)
        wake_note = QLabel('Mantém o microfone em escuta enquanto a Grazi está livre. Diga Grazi, espere “Ouvindo” e fale. O texto reconhecido fica para revisar e enviar. Exige reconhecedor local pt-BR do Windows.')
        wake_note.setWordWrap(True); wake_note.setObjectName('sub'); layout.addRow(wake_note)
        self.file_root = QLineEdit(c.state['file_root']); self.file_root.setReadOnly(True)
        self.file_root.setPlaceholderText('Escolha a pasta para trabalhar com arquivos')
        folder_row = QHBoxLayout(); folder_row.addWidget(self.file_root)
        choose = QPushButton('Escolher'); choose.clicked.connect(self.choose_folder); folder_row.addWidget(choose)
        layout.addRow('Pasta de trabalho', folder_row)
        self.motion = QCheckBox("Movimento suave do mascote")
        self.motion.setChecked(c.state["motion"]); layout.addRow(self.motion)
        self.auto_sleep = QCheckBox("Descansar automaticamente com o macaquinho")
        self.auto_sleep.setChecked(c.state["auto_sleep"]); layout.addRow(self.auto_sleep)
        self.sleep_minutes = QSpinBox(); self.sleep_minutes.setRange(1, 30)
        self.sleep_minutes.setSuffix(" min"); self.sleep_minutes.setValue(c.state["sleep_minutes"])
        self.sleep_minutes.setEnabled(self.auto_sleep.isChecked())
        self.auto_sleep.toggled.connect(self.sleep_minutes.setEnabled)
        layout.addRow("Tempo sem interação", self.sleep_minutes)
        self.size = QSlider(Qt.Orientation.Horizontal); self.size.setRange(120, 460)
        self.size.setValue(c.state["size"]); layout.addRow("Tamanho", self.size)
        self.memory = QTextEdit(); self.memory.setPlainText(c.state["memory"])
        self.memory.setPlaceholderText("Preferências que a Grazi deve lembrar")
        layout.addRow("Memória editável", self.memory)
        note = QLabel("Salva neste computador. Enviada ao modelo local ao conversar.")
        note.setObjectName("sub"); note.setWordWrap(True); layout.addRow(note)
        button = QPushButton("Salvar"); button.setObjectName("primary")
        button.clicked.connect(self.save); layout.addRow(button)

    def choose_folder(self):
        path = QFileDialog.getExistingDirectory(self, 'Pasta de trabalho da Grazi', self.file_root.text() or str(Path.home()))
        if path: self.file_root.setText(path)

    def test_voice(self):
        self.c.wake.stop()
        self.c.stop_voice()
        text = "Oi, Paulo! Eu sou a Grazi. Estou aqui para ajudar você."
        self.c.balloon.message(text)
        self.c.speech.say(text, self.engine.currentData())

    def save(self):
        model = self.model.currentText().strip()
        if not model or "cloud" in model.lower():
            QMessageBox.warning(self, "Modelo local", "Informe o nome de um modelo local do Ollama.")
            return
        self.c.state.update(model=model, voice=self.voice.isChecked(), voice_engine=self.engine.currentData(), motion=self.motion.isChecked(),
            wake_word=self.wake_word.isChecked(), file_root=self.file_root.text(),
            auto_sleep=self.auto_sleep.isChecked(), sleep_minutes=self.sleep_minutes.value(),
            size=self.size.value(), memory=self.memory.toPlainText()[:8000])
        self.c.idle.timeout = self.c.state["sleep_minutes"] * 60
        self.c.touch()
        self.c.pet.resize_pet(); self.c.pet.update(); self.c.place_pet()
        self.c.stop_voice(); self.c.balloon.reanchor()
        self.c.persist(); self.c.update_label(); self.c.sync_wake(); self.accept()


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
        help_label = QLabel("Botão direito na Grazi abre esta conversa. Fechar a janela mantém o mascote.")
        help_label.setObjectName("sub"); help_label.setWordWrap(True); layout.addWidget(help_label)

    def line(self, who, text):
        self.log.moveCursor(self.log.textCursor().MoveOperation.End)
        # Plain text only: model output cannot create active links or HTML.
        self.log.insertPlainText(f"{who}\n{text}\n\n")
        self.log.ensureCursorVisible()


class Controller:
    def __init__(self, app):
        self.app = app; self.state = load_state(); self.available_models = []
        self.idle = IdleState(timeout=self.state["sleep_minutes"] * 60)
        self.speaking = False
        self.busy = False; self.listening = False; self.connecting = False
        self.events = Events(); self.events.answer.connect(self.on_answer)
        self.events.models.connect(self.on_models); self.events.heard.connect(self.on_heard)
        self.wake = WakeListener(app)
        self.next_wake = time.monotonic() + 2
        self.wake.detected.connect(self.on_wake)
        self.wake.failed.connect(self.wake_error)
        self.actions = AssistantActions(self.state, self.confirm_action)
        self.speech = Speech(app)
        self.window = ChatWindow(self)
        self.pet = Mascot(self)
        self.balloon = SpeechBalloon(self)
        self.activity_filter = ActivityFilter(self)
        app.installEventFilter(self.activity_filter)
        self.speech.speaking.connect(self.voice_state)
        self.speech.page.connect(self.balloon.select_page)
        self.speech.error.connect(self.voice_error)
        app.aboutToQuit.connect(self.stop_voice)
        app.aboutToQuit.connect(self.wake.stop)
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

    def touch(self):
        self.idle.touch()
        self.pet.update()

    def persist(self):
        try: save_state(self.state)
        except OSError:
            self.window.status.setText("Não consegui salvar as preferências. Verifique a permissão da pasta de dados.")

    def confirm_action(self, title, description):
        self.wake.stop()
        return QMessageBox.question(self.balloon, title, description,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes

    def sync_wake(self):
        allowed = (self.state['wake_word'] and not (self.busy or self.listening or self.speech.active)
                   and self.app.activeModalWidget() is None and time.monotonic() >= self.next_wake)
        if allowed:
            self.wake.start()
        elif self.wake.running:
            self.wake.stop()

    def disable_wake(self):
        self.state['wake_word'] = False; self.wake.stop(); self.persist(); self.update_label()

    def wake_error(self, text):
        self.disable_wake()
        self.window.line('Microfone', text); self.balloon.message(text)

    def on_wake(self):
        if not self.state['wake_word'] or self.busy or self.listening or self.speech.active:
            return
        self.show_balloon()
        self.listen()

    def update_label(self):
        self.tray.setToolTip("Grazi • microfone de ativação " + ("habilitado" if self.state["wake_word"] else "desligado"))
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
        for title, callback in [("Abrir balão", self.show_balloon), ("Abrir conversa completa", self.show_chat), ("Ditado", self.listen), ("Parar voz", self.stop_voice), ("Ouvir última resposta", self.replay_answer), ("Descansar agora", self.rest_now), ("Acordar", self.show_balloon), ("Desativar ativação por voz", self.disable_wake), ("Comandos disponíveis", self.show_help), ("Personalizar", self.settings),
                                ("Mostrar Grazi", self.show_pet), ("Ocultar Grazi", self.hide_pet),
                                ("Sair", self.app.quit)]:
            action = QAction(title, menu); action.triggered.connect(callback); menu.addAction(action)
        return menu

    def show_help(self):
        self.show_balloon(); self.balloon.message(self.actions.execute('ajuda'))

    def rest_now(self):
        if self.busy or self.listening or self.connecting:
            return
        self.stop_voice()
        self.idle.sleeping = True
        self.balloon.hide()
        self.pet.show(); self.pet.tick()

    def replay_answer(self):
        if self.busy or self.listening:
            return
        self.stop_voice()
        text = next((m["content"] for m in reversed(self.state["history"])
                     if m["role"] == "assistant"), None)
        self.show_balloon()
        if text is None:
            self.balloon.message("Ainda não tenho uma resposta para repetir. Envie uma mensagem primeiro.")
            return
        self.balloon.message(text)
        self.wake.stop()
        self.speech.say(text, self.state["voice_engine"])

    def show_pet(self): self.touch(); self.pet.show()
    def show_balloon(self):
        self.touch()
        self.pet.show(); self.balloon.reanchor(); self.balloon.show()
        self.balloon.raise_(); self.balloon.activateWindow(); self.balloon.input.setFocus()
    def hide_pet(self):
        if self.tray.isVisible(): self.pet.hide(); self.balloon.hide()
        else: self.show_chat()
    def show_chat(self):
        self.touch()
        self.window.show(); self.window.raise_(); self.window.activateWindow(); self.window.input.setFocus()
    def settings(self): Settings(self).exec()
    def clear(self):
        if self.busy or self.listening: return
        if QMessageBox.question(self.window, "Limpar conversa", "Apagar o histórico local? A memória editável será mantida.") == QMessageBox.StandardButton.Yes:
            self.state["history"] = []; self.window.log.clear(); self.persist()
    def set_status(self, text): self.pet.status = text; self.pet.update()
    def stop_voice(self): self.speech.stop()
    def voice_state(self, state):
        self.next_wake = time.monotonic() + 2
        self.touch()
        self.speaking = state
        if state: self.set_status("Falando com você")
        elif not self.busy and not self.listening: self.set_status("Estou por aqui")

    def voice_error(self, text):
        self.window.line("Voz", text)
        self.balloon.message(text)

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
        self.wake.stop()
        self.touch(); self.stop_voice(); self.busy = True
        self.window.send_button.setEnabled(False); self.window.mic.setEnabled(False)
        self.balloon.input.clear(); self.balloon.send_button.setEnabled(False)
        self.balloon.message("Pensando…")
        self.window.input.clear(); self.window.line("Você", text)
        self.pending = {"role": "user", "content": text}
        try:
            last_answer = next((m['content'] for m in reversed(self.state['history']) if m['role'] == 'assistant'), '')
            immediate = self.actions.execute(text, last_answer)
            if immediate is None:
                immediate = local_command(text)
        except Exception as exc:
            self.on_answer(f"Não consegui executar esse comando: {exc}", False)
            return
        if immediate is not None:
            self.on_answer(immediate, True)
            return
        self.set_status("Pensando…")
        model, memory = self.state["model"], self.state["memory"]
        history = self.state["history"] + [self.pending]
        def run():
            try: self.events.answer.emit(chat(model, memory, history), True)
            except Exception as exc: self.events.answer.emit(str(exc), False)
        threading.Thread(target=run, daemon=True).start()

    def on_answer(self, text, ok):
        self.touch()
        self.busy = False; self.window.send_button.setEnabled(True); self.window.mic.setEnabled(True)
        self.balloon.send_button.setEnabled(True); self.balloon.message(text)
        self.window.line("Grazi" if ok else "Conexão", text); self.set_status("Estou por aqui" if ok else "Confira a conexão")
        if ok:
            self.state["history"] = (self.state["history"] + [self.pending, {"role": "assistant", "content": text}])[-40:]
            self.persist()
            if self.state["voice"]:
                self.wake.stop()
                self.speech.say(text, self.state["voice_engine"])
        else:
            self.window.input.setText(self.pending["content"])
            self.balloon.input.setText(self.pending["content"])

    def listen(self):
        if self.busy or self.listening: return
        self.wake.stop()
        self.touch(); self.stop_voice()
        if sys.platform != "win32":
            self.window.line("Ditado", "O ditado desta versão usa o reconhecimento instalado no Windows."); return
        self.balloon.message("Estou ouvindo por até 10 segundos…")
        self.balloon.send_button.setEnabled(False)
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
        self.touch()
        self.listening = False; self.window.mic.setEnabled(True); self.window.send_button.setEnabled(True)
        self.set_status("Revise e envie" if ok else "Estou por aqui")
        self.balloon.send_button.setEnabled(True)
        if ok:
            self.window.input.setText(text); self.balloon.input.setText(text)
            self.balloon.message("Revise o texto e pressione Enviar."); self.show_balloon()
        else:
            self.window.line("Ditado", text); self.balloon.message(text)


def main():
    app = QApplication(sys.argv); app.setApplicationName("Grazi")
    app.setQuitOnLastWindowClosed(False); app.setStyleSheet(STYLE)
    app.setWindowIcon(QIcon(str(ROOT / "assets/grazi.png")))
    controller = Controller(app)
    controller.show_balloon()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
