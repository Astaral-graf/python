"""Frameless main window: gradient glass background, sidebar navigation."""

from PySide6.QtCore import QPoint, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPen
from PySide6.QtWidgets import (
    QApplication, QHBoxLayout, QLabel, QPushButton, QStackedWidget,
    QVBoxLayout, QWidget,
)

from .draft_page import DraftPage
from .game_state import GameEvent, GameState
from .overlay import OverlayWindow
from .pages import ComboTrainerPage, DashboardPage, SettingsPage
from .theme import Colors, app_font
from .widgets import IOSSwitch


class TrafficLights(QWidget):
    """macOS/iOS style close & minimise dots."""

    def __init__(self, window: QWidget, parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        for color, handler in ((Colors.RED, window.close), (Colors.YELLOW, window.showMinimized)):
            dot = QPushButton()
            dot.setFixedSize(13, 13)
            dot.setCursor(Qt.CursorShape.PointingHandCursor)
            dot.setStyleSheet(
                f"QPushButton {{ background: {color}; border-radius: 6px; border: none; }}"
                f"QPushButton:hover {{ background: {QColor(color).lighter(120).name()}; }}"
            )
            dot.clicked.connect(handler)
            lay.addWidget(dot)


class NavButton(QPushButton):
    def __init__(self, icon: str, text: str, parent=None):
        super().__init__(f"{icon}   {text}", parent)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFont(app_font(13, QFont.Weight.DemiBold))
        self.setMinimumHeight(42)
        self.setStyleSheet(f"""
            QPushButton {{
                text-align: left; padding: 0 16px; border: none;
                border-radius: 12px; color: {Colors.LABEL_SECONDARY};
                background: transparent;
            }}
            QPushButton:hover {{ background: rgba(255, 255, 255, 14); color: white; }}
            QPushButton:checked {{ background: {Colors.BLUE}; color: white; }}
        """)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self._drag_offset: QPoint | None = None
        self._sound_alerts = True

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowTitle("Dota 2 Helper")
        self.resize(880, 640)

        self.state = GameState(self)
        self.overlay = OverlayWindow(self.state)
        self.state.event_due.connect(self._on_event_due)

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ------------------------------------------------------------ sidebar
        sidebar = QWidget()
        sidebar.setFixedWidth(224)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(16, 14, 16, 16)
        side.setSpacing(6)

        side.addWidget(TrafficLights(self))
        side.addSpacing(14)

        logo = QLabel("Dota 2\nHelper")
        logo.setFont(app_font(22, QFont.Weight.Black))
        side.addWidget(logo)
        tagline = QLabel("fair-play companion")
        tagline.setFont(app_font(11))
        tagline.setStyleSheet(f"color: {Colors.LABEL_TERTIARY};")
        side.addWidget(tagline)
        side.addSpacing(22)

        self.nav_buttons: list[NavButton] = []
        for i, (icon, text) in enumerate((("⏱", "Dashboard"), ("🎯", "Draft Assistant"), ("⚡", "Combo Trainer"), ("⚙", "Settings"))):
            btn = NavButton(icon, text)
            btn.clicked.connect(lambda _=False, ix=i: self._select(ix))
            side.addWidget(btn)
            self.nav_buttons.append(btn)

        side.addStretch(1)

        ov_row = QHBoxLayout()
        ov_label = QLabel("Overlay")
        ov_label.setFont(app_font(13, QFont.Weight.DemiBold))
        self.overlay_switch = IOSSwitch()
        self.overlay_switch.toggled.connect(self._set_overlay_visible)
        ov_row.addWidget(ov_label, 1)
        ov_row.addWidget(self.overlay_switch)
        side.addLayout(ov_row)
        root.addWidget(sidebar)

        # ------------------------------------------------------------ pages
        self.stack = QStackedWidget()
        self.dashboard = DashboardPage(self.state)
        self.draft = DraftPage()
        self.trainer = ComboTrainerPage()
        self.settings = SettingsPage()
        for page in (self.dashboard, self.draft, self.trainer, self.settings):
            self.stack.addWidget(page)
        root.addWidget(self.stack, 1)

        self.settings.overlay_toggled.connect(self._set_overlay_visible)
        self.settings.click_through_toggled.connect(self.overlay.set_click_through)
        self.settings.opacity_changed.connect(self.overlay.set_overlay_opacity)
        self.settings.sound_toggled.connect(self._set_sound)

        self._select(0)

    # ---------------------------------------------------------------- wiring

    def _select(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)

    def _set_overlay_visible(self, visible: bool) -> None:
        self.overlay.setVisible(visible)
        # keep both switches in agreement
        self.overlay_switch.setChecked(visible)
        self.settings.overlay_switch.setChecked(visible)

    def _set_sound(self, enabled: bool) -> None:
        self._sound_alerts = enabled

    def _on_event_due(self, _event: GameEvent) -> None:
        if self._sound_alerts:
            QApplication.beep()

    def closeEvent(self, event) -> None:
        self.overlay.close()
        super().closeEvent(event)

    # ---------------------------------------------------------------- visuals

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        grad = QLinearGradient(0, 0, self.width(), self.height())
        grad.setColorAt(0.0, QColor(16, 18, 34, 248))
        grad.setColorAt(0.55, QColor(10, 10, 14, 250))
        grad.setColorAt(1.0, QColor(28, 14, 30, 248))
        p.setPen(QPen(QColor(255, 255, 255, 22), 1))
        p.setBrush(grad)
        p.drawRoundedRect(QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5), 24, 24)

    # ---------------------------------------------------------------- dragging

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and event.position().y() < 64:
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event) -> None:
        if self._drag_offset is not None:
            self.move(event.globalPosition().toPoint() - self._drag_offset)

    def mouseReleaseEvent(self, _event) -> None:
        self._drag_offset = None
