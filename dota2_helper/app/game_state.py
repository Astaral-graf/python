"""Game clock and event scheduling for Dota 2 (patch 7.3x timings).

The clock is synced manually by the player (start / pause / nudge), then every
periodic event — runes, camp stacking, day/night, Roshan, Tormentor — is
derived from it.
"""

from dataclasses import dataclass
from time import monotonic

from PySide6.QtCore import QObject, QTimer, Signal

from .theme import Colors


@dataclass
class GameEvent:
    name: str
    time: int              # game-time in seconds when it happens
    color: str
    icon: str              # emoji glyph shown in lists / overlay
    remind_before: int = 20


# ---------------------------------------------------------------- schedules

BOUNTY_INTERVAL = 180          # bounty runes every 3:00 (first at 0:00)
POWER_START, POWER_INTERVAL = 360, 120    # power runes from 6:00 every 2:00
WISDOM_INTERVAL = 420          # wisdom runes every 7:00
LOTUS_INTERVAL = 180           # lotus pool every 3:00
WATER_RUNES = (120, 240)       # water runes at 2:00 and 4:00
STACK_SECOND = 53              # pull at x:53 to stack a camp
DAYNIGHT_INTERVAL = 300        # day/night flips every 5:00
TORMENTOR_FIRST, TORMENTOR_RESPAWN = 1200, 600
ROSHAN_MIN, ROSHAN_MAX = 480, 660          # respawn window 8:00 – 11:00
AEGIS_DURATION = 300
OBSERVER_DURATION = 360        # observer wards last 6:00
NEUTRAL_TIERS = ((420, "I"), (1020, "II"), (1620, "III"), (2220, "IV"), (3600, "V"))


def fmt(seconds: int) -> str:
    """-75 -> '-1:15', 754 -> '12:34'."""
    sign = "-" if seconds < 0 else ""
    seconds = abs(int(seconds))
    return f"{sign}{seconds // 60}:{seconds % 60:02d}"


class GameState(QObject):
    """Single source of truth: the synced game clock plus Roshan/Tormentor state."""

    tick = Signal(int)                 # emitted every 250 ms with game seconds
    event_due = Signal(GameEvent)      # emitted once when a reminder fires

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = False
        self._base = 0.0               # game seconds at the moment of the last sync
        self._synced_at = 0.0          # monotonic() at the moment of the last sync
        self._fired: set[tuple[str, int]] = set()

        self.roshan_killed_at: int | None = None
        self.roshan_kill_count = 0
        self.tormentor_killed_at: dict[str, int | None] = {"Radiant": None, "Dire": None}
        self.wards: list[int] = []     # game-times when observers were placed

        self._timer = QTimer(self)
        self._timer.setInterval(250)
        self._timer.timeout.connect(self._on_tick)
        self._timer.start()

    # ------------------------------------------------------------- clock

    @property
    def seconds(self) -> int:
        if self._running:
            return int(self._base + (monotonic() - self._synced_at))
        return int(self._base)

    @property
    def running(self) -> bool:
        return self._running

    def start(self) -> None:
        if not self._running:
            self._synced_at = monotonic()
            self._running = True

    def pause(self) -> None:
        if self._running:
            self._base = self._base + (monotonic() - self._synced_at)
            self._running = False

    def reset(self) -> None:
        self._running = False
        self._base = 0.0
        self._fired.clear()
        self.roshan_killed_at = None
        self.roshan_kill_count = 0
        self.tormentor_killed_at = {"Radiant": None, "Dire": None}
        self.wards.clear()
        self.tick.emit(0)

    def nudge(self, delta: int) -> None:
        """Adjust the clock by +-delta seconds to match the in-game timer."""
        self._base = max(0.0, self._base + (monotonic() - self._synced_at if self._running else 0) + delta)
        self._synced_at = monotonic()
        self.tick.emit(self.seconds)

    def set_time(self, seconds: int) -> None:
        self._base = float(max(0, seconds))
        self._synced_at = monotonic()
        self._fired = {k for k in self._fired if k[1] <= seconds}
        self.tick.emit(self.seconds)

    # ------------------------------------------------------------- events

    def upcoming(self, count: int = 6, horizon: int = 900) -> list[GameEvent]:
        """Next events within `horizon` seconds, soonest first."""
        now = self.seconds
        events: list[GameEvent] = []

        def next_periodic(start: int, interval: int) -> int:
            if now < start:
                return start
            return start + ((now - start) // interval + 1) * interval

        events.append(GameEvent("Bounty runes", next_periodic(0, BOUNTY_INTERVAL), Colors.YELLOW, "🟡"))
        events.append(GameEvent("Power rune", next_periodic(POWER_START, POWER_INTERVAL), Colors.PURPLE, "🔮"))
        events.append(GameEvent("Wisdom runes", next_periodic(WISDOM_INTERVAL, WISDOM_INTERVAL), Colors.TEAL, "📘"))
        events.append(GameEvent("Lotus pool", next_periodic(LOTUS_INTERVAL, LOTUS_INTERVAL), Colors.PINK, "🪷"))
        for t in WATER_RUNES:
            if now < t:
                events.append(GameEvent("Water runes", t, Colors.TEAL, "💧"))

        next_min = (now // 60) + (1 if now % 60 >= STACK_SECOND else 0)
        events.append(GameEvent("Stack camps (x:53)", next_min * 60 + STACK_SECOND, Colors.ORANGE, "🐺", remind_before=8))

        flip = next_periodic(DAYNIGHT_INTERVAL, DAYNIGHT_INTERVAL)
        is_day_next = (flip // DAYNIGHT_INTERVAL) % 2 == 0
        events.append(GameEvent("Dawn" if is_day_next else "Nightfall", flip, Colors.BLUE, "🌞" if is_day_next else "🌙"))

        for side, killed in self.tormentor_killed_at.items():
            t = TORMENTOR_FIRST if killed is None else killed + TORMENTOR_RESPAWN
            if t > now:
                events.append(GameEvent(f"Tormentor ({side})", t, Colors.RED, "🛡"))

        for tier_time, tier in NEUTRAL_TIERS:
            if now < tier_time:
                events.append(GameEvent(f"Neutral items tier {tier}", tier_time, Colors.PURPLE, "🎁", remind_before=10))
                break

        for placed in self.wards:
            expiry = placed + OBSERVER_DURATION
            if expiry > now:
                events.append(GameEvent(f"Ward expires (placed {fmt(placed)})", expiry, Colors.GREEN, "👁", remind_before=30))

        if self.roshan_killed_at is not None:
            events.append(GameEvent("Roshan window opens", self.roshan_killed_at + ROSHAN_MIN, Colors.RED, "⚔", remind_before=30))
            events.append(GameEvent("Roshan guaranteed", self.roshan_killed_at + ROSHAN_MAX, Colors.RED, "⚔", remind_before=30))
            aegis_end = self.roshan_killed_at + AEGIS_DURATION
            if aegis_end > now:
                events.append(GameEvent("Aegis expires", aegis_end, Colors.GREEN, "🥚", remind_before=30))

        events = [e for e in events if now < e.time <= now + horizon]
        events.sort(key=lambda e: e.time)
        return events[:count]

    def roshan_status(self) -> tuple[str, str]:
        """(text, color) describing Roshan for the dashboard and overlay."""
        if self.roshan_killed_at is None:
            return "Alive", Colors.GREEN
        now = self.seconds
        opens, closes = self.roshan_killed_at + ROSHAN_MIN, self.roshan_killed_at + ROSHAN_MAX
        if now < opens:
            return f"Dead — window in {fmt(opens - now)}", Colors.RED
        if now < closes:
            return f"May be up! (sure in {fmt(closes - now)})", Colors.ORANGE
        return "Definitely up", Colors.GREEN

    def kill_roshan(self) -> None:
        self.roshan_killed_at = self.seconds
        self.roshan_kill_count += 1

    def kill_tormentor(self, side: str) -> None:
        self.tormentor_killed_at[side] = self.seconds

    def place_ward(self) -> None:
        now = self.seconds
        self.wards.append(now)
        # forget wards that already expired to keep the list short
        self.wards = [w for w in self.wards if w + OBSERVER_DURATION > now]

    # ------------------------------------------------------------- ticking

    def _on_tick(self) -> None:
        now = self.seconds
        self.tick.emit(now)
        if not self._running:
            return
        for ev in self.upcoming(count=12, horizon=120):
            key = (ev.name, ev.time)
            if key not in self._fired and 0 <= ev.time - now <= ev.remind_before:
                self._fired.add(key)
                self.event_due.emit(ev)
