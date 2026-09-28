"""Compact conversation anchored to the desktop companion."""
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QPainter, QColor, QPolygonF
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit
from speech import speech_chunks


class SpeechBalloon(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.c = controller
        self.pages = ['Oi! Estou por aqui. O que vamos fazer hoje?']
        self.index = 0
        self.pointer_right = True
        self.tip_y = 75
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(270, 196)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(19, 10, 19, 10)
        layout.setSpacing(4)
        heading = QHBoxLayout()
        title = QLabel('Grazi'); title.setStyleSheet('color: #edb273; font-weight: bold; background: transparent')
        heading.addWidget(title); heading.addStretch()
        close = QPushButton('×'); close.setToolTip('Fechar balão'); close.clicked.connect(self.hide)
        close.setFixedSize(26, 26); heading.addWidget(close); layout.addLayout(heading)
        self.label = QLabel(); self.label.setWordWrap(True)
        self.label.setTextFormat(Qt.TextFormat.PlainText)
        self.label.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.label.setStyleSheet('background: transparent; font-size: 13px')
        layout.addWidget(self.label, 1)
        nav = QHBoxLayout()
        for title, delta in [('‹', -1), ('›', 1)]:
            button = QPushButton(title); button.setFixedSize(24, 24)
            button.clicked.connect(lambda checked=False, d=delta: self.navigate(d)); nav.addWidget(button)
        self.counter = QLabel(); self.counter.setStyleSheet('background: transparent; font-size: 11px')
        nav.addWidget(self.counter); nav.addStretch()
        replay = QPushButton("Ouvir"); replay.setToolTip("Ouvir a última resposta com a voz selecionada")
        replay.clicked.connect(controller.replay_answer); nav.addWidget(replay)
        stop = QPushButton('Parar'); stop.clicked.connect(controller.stop_voice); nav.addWidget(stop)
        more = QPushButton('⋯'); more.setToolTip('Conversa completa'); more.clicked.connect(controller.show_chat)
        nav.addWidget(more); layout.addLayout(nav)
        row = QHBoxLayout()
        self.input = QLineEdit(); self.input.setPlaceholderText('Fale comigo…'); self.input.setMaxLength(6000)
        self.input.returnPressed.connect(self.send); row.addWidget(self.input)
        self.send_button = QPushButton('↑'); self.send_button.setToolTip('Enviar'); self.send_button.clicked.connect(self.send)
        row.addWidget(self.send_button); layout.addLayout(row)
        self.setStyleSheet('QPushButton { padding: 3px 5px; } QLineEdit { padding: 6px; }')
        self.select_page(0)

    def send(self):
        if self.c.busy or self.c.listening:
            return
        self.c.window.input.setText(self.input.text())
        self.c.send()

    def message(self, text):
        self.pages = speech_chunks(text) or ['…']
        self.select_page(0)
        self.reanchor()
        self.show()

    def select_page(self, index):
        self.index = max(0, min(index, len(self.pages)-1))
        self.label.setText(self.pages[self.index])
        self.counter.setText(f'{self.index+1}/{len(self.pages)}')

    def navigate(self, delta):
        self.c.stop_voice()
        self.select_page(self.index + delta)

    def reanchor(self):
        pet = self.c.pet
        screen = self.c.app.screenAt(pet.frameGeometry().center()) or self.c.app.primaryScreen()
        bounds = screen.availableGeometry()
        self.pointer_right = pet.x() - self.width() + 18 >= bounds.left()
        x = pet.x() - self.width() + 18 if self.pointer_right else pet.x() + pet.width() - 18
        target_y = pet.y() + 100
        y = max(bounds.top(), min(target_y-75, bounds.bottom()-self.height()+1))
        x = max(bounds.left(), min(x, bounds.right()-self.width()+1))
        self.tip_y = max(35, min(self.height()-35, target_y-y))
        self.move(x, y)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen); painter.setBrush(QColor('#242731'))
        painter.drawRoundedRect(QRectF(12, 0, self.width()-24, self.height()), 18, 18)
        x, tip = (self.width()-12, self.width()) if self.pointer_right else (12, 0)
        painter.drawPolygon(QPolygonF([QPointF(x, self.tip_y-11), QPointF(tip, self.tip_y), QPointF(x, self.tip_y+11)]))
