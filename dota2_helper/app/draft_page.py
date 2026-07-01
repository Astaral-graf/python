"""Draft Assistant page: tick picks/bans, get live counter-pick suggestions."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QGridLayout, QHBoxLayout, QLabel, QLineEdit, QProgressBar, QPushButton,
    QScrollArea, QVBoxLayout, QWidget,
)

from .draft import BY_NAME, HEROES, analyze_team, suggest
from .theme import Colors, app_font
from .widgets import GlassCard, PillButton, SegmentedControl, hairline, section_label

ALLY, ENEMY, BAN = "ally", "enemy", "ban"
GROUP_COLORS = {ALLY: Colors.BLUE, ENEMY: Colors.RED, BAN: Colors.LABEL_TERTIARY}


class HeroChip(QPushButton):
    def __init__(self, name: str, parent=None):
        super().__init__(name, parent)
        self.hero_name = name
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFont(app_font(11, QFont.Weight.DemiBold))
        self.set_group(None)

    def set_group(self, group: str | None) -> None:
        if group is None:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: {Colors.CARD}; color: {Colors.LABEL};
                    border: 1px solid {Colors.SEPARATOR}; border-radius: 10px; padding: 6px 8px;
                }}
                QPushButton:hover {{ border: 1px solid {Colors.BLUE}; }}
            """)
        else:
            c = GROUP_COLORS[group]
            deco = "text-decoration: line-through;" if group == BAN else ""
            self.setStyleSheet(f"""
                QPushButton {{
                    background: {c}; color: white; {deco}
                    border: 1px solid {c}; border-radius: 10px; padding: 6px 8px;
                }}
            """)


class DraftPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.assignments: dict[str, str] = {}     # hero -> ALLY/ENEMY/BAN

        inner = QWidget()
        col = QVBoxLayout(inner)
        col.setContentsMargins(24, 20, 24, 24)
        col.setSpacing(14)

        # ------------------------------------------------ controls
        col.addWidget(section_label("Draft assistant"))
        ctrl_card = GlassCard()
        cc = QVBoxLayout(ctrl_card)
        cc.setContentsMargins(16, 14, 16, 14)
        cc.setSpacing(10)

        row1 = QHBoxLayout()
        row1.setSpacing(10)
        mode_lbl = QLabel("Click a hero to mark as:")
        mode_lbl.setStyleSheet(f"color: {Colors.LABEL_SECONDARY};")
        self.mode = SegmentedControl(["🟦 My team", "🟥 Enemy", "🚫 Ban"])
        clear = PillButton("Clear draft", Colors.RED, filled=False)
        clear.clicked.connect(self._clear)
        row1.addWidget(mode_lbl)
        row1.addWidget(self.mode)
        row1.addStretch(1)
        row1.addWidget(clear)
        cc.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(10)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search hero…")
        self.search.textChanged.connect(self._refilter)
        self.pos_filter = SegmentedControl(["All", "1", "2", "3", "4", "5"])
        self.pos_filter.changed.connect(lambda _: self._refresh_suggestions())
        row2.addWidget(self.search, 1)
        pos_lbl = QLabel("Suggest for position:")
        pos_lbl.setStyleSheet(f"color: {Colors.LABEL_SECONDARY};")
        row2.addWidget(pos_lbl)
        row2.addWidget(self.pos_filter)
        cc.addLayout(row2)
        col.addWidget(ctrl_card)

        # ------------------------------------------------ hero grid
        grid_card = GlassCard()
        gc = QVBoxLayout(grid_card)
        gc.setContentsMargins(16, 14, 16, 14)
        self.grid = QGridLayout()
        self.grid.setHorizontalSpacing(8)
        self.grid.setVerticalSpacing(8)
        gc.addLayout(self.grid)

        self.chips: dict[str, HeroChip] = {}
        for hero in sorted(HEROES, key=lambda h: h.name):
            chip = HeroChip(hero.name)
            chip.clicked.connect(lambda _=False, n=hero.name: self._toggle(n))
            self.chips[hero.name] = chip
        self._relayout_grid(list(self.chips))
        col.addWidget(grid_card)

        # ------------------------------------------------ suggestions
        col.addWidget(section_label("Best picks right now"))
        sug_card = GlassCard()
        self.sug_layout = QVBoxLayout(sug_card)
        self.sug_layout.setContentsMargins(20, 14, 20, 14)
        self.sug_layout.setSpacing(6)
        self.sug_rows: list[tuple[QLabel, QProgressBar, QLabel]] = []
        for _ in range(8):
            name = QLabel("")
            name.setFont(app_font(13, QFont.Weight.DemiBold))
            name.setFixedWidth(210)
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setTextVisible(False)
            bar.setFixedHeight(6)
            bar.setStyleSheet(f"""
                QProgressBar {{ background: {Colors.CARD_PRESSED}; border-radius: 3px; }}
                QProgressBar::chunk {{ background: {Colors.GREEN}; border-radius: 3px; }}
            """)
            why = QLabel("")
            why.setFont(app_font(11))
            why.setStyleSheet(f"color: {Colors.LABEL_SECONDARY};")
            row = QHBoxLayout()
            row.setSpacing(12)
            row.addWidget(name)
            row.addWidget(bar, 1)
            row.addWidget(why, 2)
            self.sug_layout.addLayout(row)
            self.sug_rows.append((name, bar, why))
        col.addWidget(sug_card)

        # ------------------------------------------------ team report
        col.addWidget(section_label("Your team analysis"))
        rep_card = GlassCard()
        rc = QVBoxLayout(rep_card)
        rc.setContentsMargins(20, 14, 20, 14)
        rc.setSpacing(8)
        self.metrics = QLabel("Pick heroes to see the breakdown.")
        self.metrics.setFont(app_font(12))
        self.metrics.setStyleSheet(f"color: {Colors.LABEL_SECONDARY};")
        rc.addWidget(self.metrics)
        rc.addWidget(hairline())
        self.warn = QLabel("")
        self.warn.setFont(app_font(12))
        self.warn.setWordWrap(True)
        self.warn.setStyleSheet(f"color: {Colors.ORANGE};")
        rc.addWidget(self.warn)
        col.addWidget(rep_card)
        col.addStretch(1)

        page = QVBoxLayout(self)
        page.setContentsMargins(0, 0, 0, 0)
        page.addWidget(_make_scroll(inner))

        self._refresh_suggestions()

    # ---------------------------------------------------------------- grid

    def _relayout_grid(self, names: list[str]) -> None:
        while self.grid.count():
            self.grid.takeAt(0)
        for chip in self.chips.values():
            chip.setVisible(chip.hero_name in names)
        cols = 5
        for i, n in enumerate(names):
            self.grid.addWidget(self.chips[n], i // cols, i % cols)

    def _refilter(self) -> None:
        text = self.search.text().strip().lower()
        names = [n for n in sorted(self.chips) if text in n.lower()]
        self._relayout_grid(names)

    # ---------------------------------------------------------------- state

    def _toggle(self, name: str) -> None:
        modes = (ALLY, ENEMY, BAN)
        target = modes[self.mode.index()]
        current = self.assignments.get(name)
        if current == target:
            del self.assignments[name]
            self.chips[name].set_group(None)
        else:
            group_size = sum(1 for g in self.assignments.values() if g == target)
            if target in (ALLY, ENEMY) and current != target and group_size >= 5:
                return  # a team can't have more than five heroes
            self.assignments[name] = target
            self.chips[name].set_group(target)
        self._refresh_suggestions()

    def _clear(self) -> None:
        self.assignments.clear()
        for chip in self.chips.values():
            chip.set_group(None)
        self._refresh_suggestions()

    # ---------------------------------------------------------------- output

    def _refresh_suggestions(self) -> None:
        allies = [n for n, g in self.assignments.items() if g == ALLY]
        enemies = [n for n, g in self.assignments.items() if g == ENEMY]
        banned = [n for n, g in self.assignments.items() if g == BAN]
        pos = self.pos_filter.index() or None

        results = suggest(allies, enemies, banned, position=pos, count=len(self.sug_rows))
        top = max((s.score for s in results), default=0) or 1
        for i, (name, bar, why) in enumerate(self.sug_rows):
            if i < len(results):
                s = results[i]
                positions = "/".join(str(p) for p in s.hero.positions)
                name.setText(f"{s.hero.name}   ·   pos {positions}")
                bar.setValue(int(max(4.0, 100 * max(s.score, 0) / max(top, 0.01))))
                why.setText(", ".join(s.reasons) if s.reasons else "solid all-round pick")
            else:
                name.setText("")
                bar.setValue(0)
                why.setText("")

        report = analyze_team(allies)
        if allies:
            self.metrics.setText(
                f"Control: {report.control}   ·   Initiation: {report.initiation}   ·   "
                f"Saves: {report.saves}   ·   Physical: {report.physical}   ·   "
                f"Magical: {report.magical}   ·   Early: {report.early}   ·   Late: {report.late}"
            )
        else:
            self.metrics.setText("Pick heroes to see the breakdown.")
        self.warn.setText("\n".join(f"⚠ {w}" for w in report.warnings))
        self.warn.setVisible(bool(report.warnings))


def _make_scroll(inner: QWidget) -> QScrollArea:
    area = QScrollArea()
    area.setWidgetResizable(True)
    area.setWidget(inner)
    area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    return area
