"""The three content pages: Dashboard (timers), Combo Trainer and Settings."""

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication, QComboBox, QGridLayout, QHBoxLayout, QLabel, QScrollArea,
    QSlider, QSpinBox, QVBoxLayout, QWidget,
)

from .combos import Combo, combos_for, heroes
from .game_state import GameState, fmt
from .theme import Colors, app_font, mono_font
from .widgets import (
    GlassCard, IOSSwitch, KeyCap, PillButton, StatRow, hairline, section_label,
)


def _scrollable(inner: QWidget) -> QScrollArea:
    area = QScrollArea()
    area.setWidgetResizable(True)
    area.setWidget(inner)
    area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    return area


# ===================================================================== dashboard

class DashboardPage(QWidget):
    def __init__(self, state: GameState, parent=None):
        super().__init__(parent)
        self.state = state

        inner = QWidget()
        col = QVBoxLayout(inner)
        col.setContentsMargins(24, 20, 24, 24)
        col.setSpacing(14)

        # ---- game clock card
        col.addWidget(section_label("Game clock"))
        clock_card = GlassCard()
        cc = QVBoxLayout(clock_card)
        cc.setContentsMargins(20, 18, 20, 18)
        cc.setSpacing(12)

        self.clock = QLabel("0:00")
        self.clock.setFont(mono_font(52, QFont.Weight.Bold))
        self.clock.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cc.addWidget(self.clock)

        hint = QLabel("Sync with the in-game timer, then every rune / stack / objective is tracked for you.")
        hint.setFont(app_font(11))
        hint.setStyleSheet(f"color: {Colors.LABEL_SECONDARY};")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setWordWrap(True)
        cc.addWidget(hint)

        controls = QHBoxLayout()
        controls.setSpacing(8)
        self.start_btn = PillButton("Start", Colors.GREEN)
        self.start_btn.clicked.connect(self._toggle_run)
        reset_btn = PillButton("Reset", Colors.RED, filled=False)
        reset_btn.clicked.connect(self.state.reset)
        controls.addStretch(1)
        for delta, label in ((-60, "-1m"), (-5, "-5s"), (5, "+5s"), (60, "+1m")):
            b = PillButton(label, Colors.BLUE, filled=False)
            b.clicked.connect(lambda _=False, d=delta: self.state.nudge(d))
            controls.addWidget(b)
        controls.addWidget(self.start_btn)
        controls.addWidget(reset_btn)
        controls.addStretch(1)
        cc.addLayout(controls)
        col.addWidget(clock_card)

        # ---- objectives card
        col.addWidget(section_label("Objectives"))
        obj_card = GlassCard()
        oc = QVBoxLayout(obj_card)
        oc.setContentsMargins(4, 6, 4, 6)
        oc.setSpacing(0)

        self.roshan_label = QLabel("Alive")
        self.roshan_label.setFont(app_font(13, QFont.Weight.DemiBold))
        rosh_btn = PillButton("Killed!", Colors.RED, filled=False)
        rosh_btn.clicked.connect(self._roshan_killed)
        rosh_right = QWidget()
        rr = QHBoxLayout(rosh_right)
        rr.setContentsMargins(0, 0, 0, 0)
        rr.setSpacing(12)
        rr.addWidget(self.roshan_label)
        rr.addWidget(rosh_btn)
        oc.addWidget(StatRow("⚔  Roshan", "Respawns 8:00–11:00 after death · Aegis lasts 5:00", rosh_right))
        oc.addWidget(hairline())

        for side in ("Radiant", "Dire"):
            btn = PillButton("Killed", Colors.ORANGE, filled=False)
            btn.clicked.connect(lambda _=False, s=side: self.state.kill_tormentor(s))
            oc.addWidget(StatRow(f"🛡  Tormentor — {side}", "First spawn 20:00 · respawns in 10:00", btn))
            oc.addWidget(hairline())

        ward_btn = PillButton("Placed", Colors.GREEN, filled=False)
        ward_btn.clicked.connect(self.state.place_ward)
        oc.addWidget(StatRow("👁  Observer ward", "Tap when you place one — alert 30s before it expires (6:00)", ward_btn))
        col.addWidget(obj_card)

        # ---- buyback calculator card
        col.addWidget(section_label("Buyback"))
        bb_card = GlassCard()
        bb = QHBoxLayout(bb_card)
        bb.setContentsMargins(20, 14, 20, 14)
        bb.setSpacing(12)
        bb_label = QLabel("Net worth")
        bb_label.setFont(app_font(13, QFont.Weight.DemiBold))
        bb.addWidget(bb_label)
        self.networth = QSpinBox()
        self.networth.setRange(0, 200_000)
        self.networth.setSingleStep(500)
        self.networth.setValue(10_000)
        self.networth.valueChanged.connect(self._update_buyback)
        bb.addWidget(self.networth)
        self.bb_result = QLabel("")
        self.bb_result.setFont(app_font(13))
        bb.addWidget(self.bb_result, 1)
        col.addWidget(bb_card)
        self._update_buyback(self.networth.value())

        # ---- upcoming events card
        col.addWidget(section_label("Upcoming"))
        ev_card = GlassCard()
        self.ev_layout = QVBoxLayout(ev_card)
        self.ev_layout.setContentsMargins(20, 14, 20, 14)
        self.ev_layout.setSpacing(8)
        self.ev_labels = [QLabel("") for _ in range(6)]
        for lbl in self.ev_labels:
            lbl.setFont(app_font(13))
            self.ev_layout.addWidget(lbl)
        col.addWidget(ev_card)
        col.addStretch(1)

        page = QVBoxLayout(self)
        page.setContentsMargins(0, 0, 0, 0)
        page.addWidget(_scrollable(inner))

        state.tick.connect(self._refresh)

    def _toggle_run(self) -> None:
        if self.state.running:
            self.state.pause()
            self.start_btn.setText("Start")
        else:
            self.state.start()
            self.start_btn.setText("Pause")

    def _roshan_killed(self) -> None:
        self.state.kill_roshan()

    def _update_buyback(self, networth: int) -> None:
        cost = 100 + networth // 13
        self.bb_result.setText(f"Buyback cost: {cost} gold   ·   cooldown 8:00")
        self.bb_result.setStyleSheet(f"color: {Colors.LABEL_SECONDARY};")

    def _refresh(self, seconds: int) -> None:
        self.clock.setText(fmt(seconds))
        text, color = self.state.roshan_status()
        self.roshan_label.setText(text)
        self.roshan_label.setStyleSheet(f"color: {color};")

        events = self.state.upcoming(count=len(self.ev_labels))
        for i, lbl in enumerate(self.ev_labels):
            if i < len(events):
                ev = events[i]
                left = ev.time - seconds
                lbl.setText(f"{ev.icon}  {ev.name}   ·   in {fmt(left)}  (at {fmt(ev.time)})")
                lbl.setStyleSheet(f"color: {ev.color if left <= ev.remind_before else Colors.LABEL};")
            else:
                lbl.setText("")


# ===================================================================== combo trainer

class ComboTrainerPage(QWidget):
    """Steps through a combo, lighting up each keycap at real cast timing.

    Deliberately *not* an input macro: it trains the player's hands instead of
    replacing them, so it can't get an account banned.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._combo: Combo | None = None
        self._step = -1
        self._caps: list[KeyCap] = []
        self._rows: list[QLabel] = []
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._advance)

        inner = QWidget()
        col = QVBoxLayout(inner)
        col.setContentsMargins(24, 20, 24, 24)
        col.setSpacing(14)

        col.addWidget(section_label("Combo trainer"))
        picker_card = GlassCard()
        pc = QHBoxLayout(picker_card)
        pc.setContentsMargins(16, 12, 16, 12)
        pc.setSpacing(10)
        self.hero_box = QComboBox()
        self.hero_box.addItems(heroes())
        self.hero_box.currentTextChanged.connect(self._hero_changed)
        self.combo_box = QComboBox()
        self.combo_box.currentIndexChanged.connect(self._combo_changed)
        pc.addWidget(QLabel("Hero"))
        pc.addWidget(self.hero_box, 1)
        pc.addWidget(QLabel("Combo"))
        pc.addWidget(self.combo_box, 2)
        col.addWidget(picker_card)

        self.detail_card = GlassCard()
        dc = QVBoxLayout(self.detail_card)
        dc.setContentsMargins(20, 16, 20, 18)
        dc.setSpacing(10)

        head = QHBoxLayout()
        self.title = QLabel("")
        self.title.setFont(app_font(17, QFont.Weight.Bold))
        self.badge = QLabel("")
        self.badge.setFont(app_font(11, QFont.Weight.DemiBold))
        head.addWidget(self.title, 1)
        head.addWidget(self.badge)
        dc.addLayout(head)

        self.desc = QLabel("")
        self.desc.setFont(app_font(12))
        self.desc.setStyleSheet(f"color: {Colors.LABEL_SECONDARY};")
        self.desc.setWordWrap(True)
        dc.addWidget(self.desc)
        dc.addWidget(hairline())

        self.steps_grid = QGridLayout()
        self.steps_grid.setHorizontalSpacing(14)
        self.steps_grid.setVerticalSpacing(10)
        dc.addLayout(self.steps_grid)

        controls = QHBoxLayout()
        controls.setSpacing(10)
        self.play_btn = PillButton("▶  Practice", Colors.GREEN)
        self.play_btn.clicked.connect(self._toggle_play)
        controls.addWidget(self.play_btn)
        controls.addSpacing(8)
        controls.addWidget(QLabel("Speed"))
        self.speed = QSlider(Qt.Orientation.Horizontal)
        self.speed.setRange(25, 150)          # percent of real timing speed
        self.speed.setValue(60)
        self.speed.setFixedWidth(160)
        controls.addWidget(self.speed)
        self.speed_lbl = QLabel("0.60x")
        self.speed_lbl.setStyleSheet(f"color: {Colors.LABEL_SECONDARY};")
        self.speed.valueChanged.connect(lambda v: self.speed_lbl.setText(f"{v / 100:.2f}x"))
        controls.addWidget(self.speed_lbl)
        controls.addStretch(1)
        dc.addLayout(controls)

        note = QLabel(
            "💡 The trainer highlights keys at real cast timing — press them yourself "
            "(in Demo Hero mode) to build muscle memory. It never sends input to the game: "
            "auto-executing combos is bannable and, honestly, worse practice."
        )
        note.setFont(app_font(11))
        note.setStyleSheet(f"color: {Colors.LABEL_TERTIARY};")
        note.setWordWrap(True)
        dc.addWidget(note)

        col.addWidget(self.detail_card)
        col.addStretch(1)

        page = QVBoxLayout(self)
        page.setContentsMargins(0, 0, 0, 0)
        page.addWidget(_scrollable(inner))

        self._hero_changed(self.hero_box.currentText())

    # ------------------------------------------------------------- selection

    def _hero_changed(self, hero: str) -> None:
        self._stop()
        self.combo_box.blockSignals(True)
        self.combo_box.clear()
        for c in combos_for(hero):
            self.combo_box.addItem(c.name)
        self.combo_box.blockSignals(False)
        self._combo_changed(0)

    def _combo_changed(self, index: int) -> None:
        self._stop()
        options = combos_for(self.hero_box.currentText())
        if not options:
            return
        self._combo = options[max(0, index)]
        self._build_steps()

    def _build_steps(self) -> None:
        while self.steps_grid.count():
            item = self.steps_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._caps, self._rows = [], []
        assert self._combo is not None

        diff_colors = {"Easy": Colors.GREEN, "Medium": Colors.ORANGE, "Hard": Colors.RED}
        color = diff_colors.get(self._combo.difficulty, Colors.BLUE)
        self.title.setText(f"{self._combo.hero} — {self._combo.name}")
        self.badge.setText(self._combo.difficulty)
        self.badge.setStyleSheet(f"color: {color}; border: 1px solid {color}; border-radius: 8px; padding: 2px 10px;")
        self.desc.setText(self._combo.description)

        for row, step in enumerate(self._combo.steps):
            cap = KeyCap(step.key)
            text = QLabel(step.action + (f"   —   {step.note}" if step.note else ""))
            text.setFont(app_font(12))
            text.setWordWrap(True)
            self.steps_grid.addWidget(cap, row, 0, Qt.AlignmentFlag.AlignTop)
            self.steps_grid.addWidget(text, row, 1)
            self.steps_grid.setColumnStretch(1, 1)
            self._caps.append(cap)
            self._rows.append(text)

    # ------------------------------------------------------------- playback

    def _toggle_play(self) -> None:
        if self._timer.isActive() or self._step >= 0:
            self._stop()
        else:
            self._step = -1
            self.play_btn.setText("■  Stop")
            self._advance()

    def _advance(self) -> None:
        if self._combo is None:
            return
        if 0 <= self._step < len(self._caps):
            self._caps[self._step].set_active(False)
            self._rows[self._step].setStyleSheet("")
        self._step += 1
        if self._step >= len(self._combo.steps):
            self._stop()
            return
        step = self._combo.steps[self._step]
        self._caps[self._step].set_active(True)
        self._rows[self._step].setStyleSheet(f"color: {Colors.GREEN};")
        QApplication.beep()
        speed = self.speed.value() / 100
        self._timer.start(max(120, int((step.delay_ms + 250) / speed)))

    def _stop(self) -> None:
        self._timer.stop()
        for cap, row in zip(self._caps, self._rows):
            cap.set_active(False)
            row.setStyleSheet("")
        self._step = -1
        self.play_btn.setText("▶  Practice")


# ===================================================================== settings

class SettingsPage(QWidget):
    overlay_toggled = Signal(bool)
    click_through_toggled = Signal(bool)
    opacity_changed = Signal(float)
    sound_toggled = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        inner = QWidget()
        col = QVBoxLayout(inner)
        col.setContentsMargins(24, 20, 24, 24)
        col.setSpacing(14)

        col.addWidget(section_label("Overlay"))
        card = GlassCard()
        cc = QVBoxLayout(card)
        cc.setContentsMargins(4, 6, 4, 6)
        cc.setSpacing(0)

        self.overlay_switch = IOSSwitch()
        self.overlay_switch.toggled.connect(self.overlay_toggled)
        cc.addWidget(StatRow("Show overlay", "Frameless timer panel on top of the game (run Dota 2 in Borderless Window mode)", self.overlay_switch))
        cc.addWidget(hairline())

        self.click_switch = IOSSwitch()
        self.click_switch.toggled.connect(self.click_through_toggled)
        cc.addWidget(StatRow("Click-through", "Mouse clicks pass through the overlay into the game", self.click_switch))
        cc.addWidget(hairline())

        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(20, 100)
        slider.setValue(92)
        slider.setFixedWidth(180)
        slider.valueChanged.connect(lambda v: self.opacity_changed.emit(v / 100))
        cc.addWidget(StatRow("Opacity", "How solid the overlay background looks", slider))
        col.addWidget(card)

        col.addWidget(section_label("Alerts"))
        card2 = GlassCard()
        c2 = QVBoxLayout(card2)
        c2.setContentsMargins(4, 6, 4, 6)
        c2.setSpacing(0)
        self.sound_switch = IOSSwitch(checked=True)
        self.sound_switch.toggled.connect(self.sound_toggled)
        c2.addWidget(StatRow("Sound alerts", "Beep shortly before runes, stacks and objectives", self.sound_switch))
        col.addWidget(card2)

        col.addWidget(section_label("About"))
        about = GlassCard()
        ac = QVBoxLayout(about)
        ac.setContentsMargins(20, 16, 20, 16)
        info = QLabel(
            "Dota 2 Helper — a fair-play companion app.\n\n"
            "It reads nothing from the game and sends nothing to it, so it can't "
            "trigger a VAC/Overwatch ban. All timers are driven by the clock you "
            "sync on the Dashboard. Combo Trainer teaches sequences instead of "
            "automating them — your hands do the plays."
        )
        info.setFont(app_font(12))
        info.setStyleSheet(f"color: {Colors.LABEL_SECONDARY};")
        info.setWordWrap(True)
        ac.addWidget(info)
        col.addWidget(about)
        col.addStretch(1)

        page = QVBoxLayout(self)
        page.setContentsMargins(0, 0, 0, 0)
        page.addWidget(_scrollable(inner))
