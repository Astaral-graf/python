"""Reusable iOS-styled widgets: switches, cards, pills, segmented controls."""

from PySide6.QtCore import (
    Property, QEasingCurve, QPropertyAnimation, QRectF, Qt, Signal,
)
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel, QPushButton,
    QVBoxLayout, QWidget,
)

from .theme import Colors, app_font, mono_font


class IOSSwitch(QWidget):
    """The classic iOS toggle: green pill with a sliding white knob."""

    toggled = Signal(bool)

    def __init__(self, checked: bool = False, parent=None):
        super().__init__(parent)
        self._checked = checked
        self._pos = 1.0 if checked else 0.0
        self._anim = QPropertyAnimation(self, b"knobPos", self)
        self._anim.setDuration(180)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.setFixedSize(51, 31)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def _get_pos(self) -> float:
        return self._pos

    def _set_pos(self, v: float) -> None:
        self._pos = v
        self.update()

    knobPos = Property(float, _get_pos, _set_pos)

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, checked: bool) -> None:
        if checked == self._checked:
            return
        self._checked = checked
        self._anim.stop()
        self._anim.setEndValue(1.0 if checked else 0.0)
        self._anim.start()
        self.toggled.emit(checked)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.setChecked(not self._checked)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        track_off = QColor(Colors.CARD_PRESSED)
        track_on = QColor(Colors.GREEN)
        track = QColor(
            int(track_off.red() + (track_on.red() - track_off.red()) * self._pos),
            int(track_off.green() + (track_on.green() - track_off.green()) * self._pos),
            int(track_off.blue() + (track_on.blue() - track_off.blue()) * self._pos),
        )
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(track)
        p.drawRoundedRect(QRectF(0, 0, 51, 31), 15.5, 15.5)

        x = 2 + self._pos * (51 - 27 - 4)
        p.setBrush(QColor("#FFFFFF"))
        p.drawEllipse(QRectF(x, 2, 27, 27))


class GlassCard(QFrame):
    """Rounded translucent card, the basic building block of every page."""

    def __init__(self, parent=None, radius: int = 18, color: str = Colors.BG_ELEVATED, alpha: int = 235):
        super().__init__(parent)
        self._radius = radius
        self._color = Colors.q(color, alpha)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(28)
        shadow.setOffset(0, 6)
        shadow.setColor(QColor(0, 0, 0, 90))
        self.setGraphicsEffect(shadow)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QPen(QColor(255, 255, 255, 18), 1))
        p.setBrush(self._color)
        p.drawRoundedRect(QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5), self._radius, self._radius)


class PillButton(QPushButton):
    """Filled or tinted rounded button, like iOS action buttons."""

    def __init__(self, text: str, color: str = Colors.BLUE, filled: bool = True, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFont(app_font(13, QFont.Weight.DemiBold))
        self.setMinimumHeight(38)
        c = QColor(color)
        if filled:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: {color}; color: white; border: none;
                    border-radius: 19px; padding: 8px 20px;
                }}
                QPushButton:hover {{ background: {c.lighter(112).name()}; }}
                QPushButton:pressed {{ background: {c.darker(120).name()}; }}
                QPushButton:disabled {{ background: {Colors.CARD_PRESSED}; color: {Colors.LABEL_TERTIARY}; }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: rgba({c.red()}, {c.green()}, {c.blue()}, 36);
                    color: {color}; border: none; border-radius: 19px; padding: 8px 20px;
                }}
                QPushButton:hover {{ background: rgba({c.red()}, {c.green()}, {c.blue()}, 60); }}
                QPushButton:pressed {{ background: rgba({c.red()}, {c.green()}, {c.blue()}, 90); }}
            """)


class SegmentedControl(QWidget):
    """iOS segmented picker."""

    changed = Signal(int)

    def __init__(self, options: list[str], parent=None):
        super().__init__(parent)
        self._buttons: list[QPushButton] = []
        self._index = 0
        lay = QHBoxLayout(self)
        lay.setContentsMargins(3, 3, 3, 3)
        lay.setSpacing(2)
        self.setStyleSheet(f"background: {Colors.CARD}; border-radius: 10px;")
        for i, text in enumerate(options):
            btn = QPushButton(text)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFont(app_font(12, QFont.Weight.DemiBold))
            btn.clicked.connect(lambda _=False, ix=i: self.setIndex(ix))
            lay.addWidget(btn)
            self._buttons.append(btn)
        self._restyle()

    def setIndex(self, index: int) -> None:
        if index != self._index:
            self._index = index
            self._restyle()
            self.changed.emit(index)

    def index(self) -> int:
        return self._index

    def _restyle(self) -> None:
        for i, btn in enumerate(self._buttons):
            if i == self._index:
                btn.setStyleSheet(
                    f"background: {Colors.CARD_PRESSED}; color: white;"
                    "border-radius: 8px; padding: 6px 14px; border: none;"
                )
            else:
                btn.setStyleSheet(
                    f"background: transparent; color: {Colors.LABEL_SECONDARY};"
                    "border-radius: 8px; padding: 6px 14px; border: none;"
                )


class KeyCap(QLabel):
    """A keyboard-key badge used by the combo trainer (Q, W, E, R, items…)."""

    def __init__(self, key: str, accent: str = Colors.BLUE, parent=None):
        super().__init__(key, parent)
        self.setFont(mono_font(14, QFont.Weight.Bold))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedHeight(36)
        self.setMinimumWidth(36)
        self._accent = accent
        self.set_active(False)

    def set_active(self, active: bool) -> None:
        if active:
            self.setStyleSheet(
                f"background: {self._accent}; color: white; border-radius: 9px;"
                f"border: 1px solid {self._accent}; padding: 0 10px;"
            )
        else:
            self.setStyleSheet(
                f"background: {Colors.CARD}; color: {Colors.LABEL};"
                f"border: 1px solid {Colors.SEPARATOR}; border-radius: 9px; padding: 0 10px;"
            )


class StatRow(QWidget):
    """Label on the left, value (and optional control) on the right."""

    def __init__(self, title: str, subtitle: str = "", right: QWidget | None = None, parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 10, 16, 10)
        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        t = QLabel(title)
        t.setFont(app_font(13, QFont.Weight.DemiBold))
        text_col.addWidget(t)
        if subtitle:
            s = QLabel(subtitle)
            s.setFont(app_font(11))
            s.setStyleSheet(f"color: {Colors.LABEL_SECONDARY};")
            s.setWordWrap(True)
            text_col.addWidget(s)
        lay.addLayout(text_col, 1)
        if right is not None:
            lay.addWidget(right, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)


def section_label(text: str) -> QLabel:
    lbl = QLabel(text.upper())
    lbl.setFont(app_font(11, QFont.Weight.DemiBold))
    lbl.setStyleSheet(f"color: {Colors.LABEL_SECONDARY}; letter-spacing: 1px; padding-left: 6px;")
    return lbl


def hairline() -> QFrame:
    line = QFrame()
    line.setFixedHeight(1)
    line.setStyleSheet(f"background: {Colors.SEPARATOR};")
    return line
