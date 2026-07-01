"""Frameless always-on-top overlay shown above the game.

A slim frosted-glass strip with the game clock, Roshan status and the next
few timed events. Draggable anywhere; optional click-through mode so it never
eats mouse input meant for the game.
"""

from PySide6.QtCore import QPoint, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from .game_state import GameState, fmt
from .theme import Colors, app_font, mono_font


class OverlayWindow(QWidget):
    def __init__(self, state: GameState):
        super().__init__(None)
        self.state = state
        self._drag_offset: QPoint | None = None
        self._opacity = 0.92

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowTitle("Dota 2 Helper — Overlay")

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 12, 18, 14)
        root.setSpacing(6)

        top = QHBoxLayout()
        top.setSpacing(12)
        self.clock = QLabel("0:00")
        self.clock.setFont(mono_font(22, QFont.Weight.Bold))
        top.addWidget(self.clock)

        self.roshan = QLabel("Roshan: Alive")
        self.roshan.setFont(app_font(12, QFont.Weight.DemiBold))
        top.addWidget(self.roshan, 1, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        root.addLayout(top)

        self.event_labels: list[QLabel] = []
        for _ in range(4):
            lbl = QLabel("")
            lbl.setFont(app_font(12))
            root.addWidget(lbl)
            self.event_labels.append(lbl)

        self.resize(300, 150)
        self.move(40, 40)
        state.tick.connect(self.refresh)

    # ------------------------------------------------------------ options

    def set_click_through(self, enabled: bool) -> None:
        self.setWindowFlag(Qt.WindowType.WindowTransparentForInput, enabled)
        if self.isVisible():
            self.show()  # re-apply flags

    def set_overlay_opacity(self, value: float) -> None:
        self._opacity = max(0.2, min(1.0, value))
        self.update()

    # ------------------------------------------------------------ updates

    def refresh(self, seconds: int) -> None:
        if not self.isVisible():
            return
        self.clock.setText(fmt(seconds))
        text, color = self.state.roshan_status()
        self.roshan.setText(f"⚔ {text}")
        self.roshan.setStyleSheet(f"color: {color};")

        events = self.state.upcoming(count=len(self.event_labels))
        for i, lbl in enumerate(self.event_labels):
            if i < len(events):
                ev = events[i]
                left = ev.time - seconds
                urgent = left <= ev.remind_before
                lbl.setText(f"{ev.icon}  {ev.name} — {fmt(left)}")
                lbl.setStyleSheet(f"color: {ev.color if urgent else Colors.LABEL_SECONDARY};")
            else:
                lbl.setText("")

    # ------------------------------------------------------------ painting

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        bg = QColor(Colors.BG_ELEVATED)
        bg.setAlphaF(self._opacity)
        p.setPen(QPen(QColor(255, 255, 255, 26), 1))
        p.setBrush(bg)
        p.drawRoundedRect(QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5), 20, 20)

    # ------------------------------------------------------------ dragging

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event) -> None:
        if self._drag_offset is not None:
            self.move(event.globalPosition().toPoint() - self._drag_offset)

    def mouseReleaseEvent(self, _event) -> None:
        self._drag_offset = None
