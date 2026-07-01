"""iOS-inspired design system: colors, fonts and the global stylesheet."""

from PySide6.QtGui import QColor, QFont, QFontDatabase


class Colors:
    """Palette lifted from Apple's iOS dark-mode system colors."""

    BG = "#000000"
    BG_ELEVATED = "#1C1C1E"
    CARD = "#2C2C2E"
    CARD_PRESSED = "#3A3A3C"
    SEPARATOR = "#38383A"

    LABEL = "#FFFFFF"
    LABEL_SECONDARY = "#98989F"
    LABEL_TERTIARY = "#5A5A5E"

    BLUE = "#0A84FF"
    GREEN = "#30D158"
    RED = "#FF453A"
    ORANGE = "#FF9F0A"
    YELLOW = "#FFD60A"
    PURPLE = "#BF5AF2"
    TEAL = "#64D2FF"
    PINK = "#FF375F"

    @staticmethod
    def q(hex_str: str, alpha: int = 255) -> QColor:
        c = QColor(hex_str)
        c.setAlpha(alpha)
        return c


def app_font(size: int = 13, weight: QFont.Weight = QFont.Weight.Normal) -> QFont:
    """Best available stand-in for SF Pro on each platform."""
    families = QFontDatabase.families()
    for name in ("SF Pro Display", "SF Pro Text", "Helvetica Neue", "Segoe UI Variable", "Segoe UI", "Ubuntu", "Noto Sans"):
        if name in families:
            f = QFont(name, size)
            break
    else:
        f = QFont()
        f.setPointSize(size)
    f.setWeight(weight)
    return f


def mono_font(size: int = 13, weight: QFont.Weight = QFont.Weight.DemiBold) -> QFont:
    families = QFontDatabase.families()
    for name in ("SF Mono", "Cascadia Code", "JetBrains Mono", "Consolas", "DejaVu Sans Mono"):
        if name in families:
            f = QFont(name, size)
            break
    else:
        f = QFont("monospace", size)
    f.setWeight(weight)
    return f


GLOBAL_QSS = f"""
* {{
    outline: none;
}}

QWidget {{
    color: {Colors.LABEL};
    background: transparent;
    font-size: 13px;
}}

QScrollArea {{
    border: none;
}}

QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    margin: 4px 2px;
}}
QScrollBar::handle:vertical {{
    background: rgba(255, 255, 255, 60);
    border-radius: 3px;
    min-height: 32px;
}}
QScrollBar::handle:vertical:hover {{
    background: rgba(255, 255, 255, 110);
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: transparent;
}}

QToolTip {{
    background: {Colors.CARD};
    color: {Colors.LABEL};
    border: 1px solid {Colors.SEPARATOR};
    border-radius: 8px;
    padding: 6px 10px;
}}

QLineEdit, QSpinBox, QDoubleSpinBox {{
    background: {Colors.CARD};
    border: 1px solid {Colors.SEPARATOR};
    border-radius: 10px;
    padding: 7px 12px;
    selection-background-color: {Colors.BLUE};
}}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
    border: 1px solid {Colors.BLUE};
}}
QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
    width: 0;
    border: none;
}}

QComboBox {{
    background: {Colors.CARD};
    border: 1px solid {Colors.SEPARATOR};
    border-radius: 10px;
    padding: 7px 12px;
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox QAbstractItemView {{
    background: {Colors.BG_ELEVATED};
    border: 1px solid {Colors.SEPARATOR};
    border-radius: 10px;
    selection-background-color: {Colors.BLUE};
    padding: 4px;
}}

QSlider::groove:horizontal {{
    height: 4px;
    background: {Colors.CARD_PRESSED};
    border-radius: 2px;
}}
QSlider::sub-page:horizontal {{
    background: {Colors.BLUE};
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: white;
    width: 20px;
    height: 20px;
    margin: -8px 0;
    border-radius: 10px;
}}
"""
