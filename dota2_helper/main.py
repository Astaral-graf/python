"""Dota 2 Helper — iOS-styled fair-play companion app.

Run:  python main.py
"""

import sys

from PySide6.QtWidgets import QApplication

from app.main_window import MainWindow
from app.theme import GLOBAL_QSS, app_font


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Dota 2 Helper")
    app.setFont(app_font(13))
    app.setStyleSheet(GLOBAL_QSS)

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
