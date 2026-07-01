"""Combo library for the trainer.

Each combo is a sequence of steps the *player* practices by hand. The app
never sends input to the game — it teaches timing and order, like a rhythm
trainer, which is both ban-safe and actually builds muscle memory.
"""

from dataclasses import dataclass, field


@dataclass
class ComboStep:
    key: str          # what to press (hotkey shown as a keycap)
    action: str       # short description of the cast
    delay_ms: int     # pause AFTER this step at 1.0x speed
    note: str = ""    # optional timing tip


@dataclass
class Combo:
    hero: str
    name: str
    difficulty: str            # Easy / Medium / Hard
    description: str
    steps: list[ComboStep] = field(default_factory=list)


COMBOS: list[Combo] = [
    Combo(
        hero="Lion",
        name="Full disable burst",
        difficulty="Easy",
        description="Classic solo pick-off: chain the stuns first, burn mana, then nuke.",
        steps=[
            ComboStep("D", "Blink in range (Blink Dagger)", 250, "Blink to ~600 range, not on top of the target"),
            ComboStep("Q", "Earth Spike", 400, "Cast immediately after blink"),
            ComboStep("W", "Hex as the spike ends", 500, "Overlap disables, don't stack them"),
            ComboStep("E", "Mana Drain during hex", 900),
            ComboStep("R", "Finger of Death to finish", 0, "Save it if the target is already dead"),
        ],
    ),
    Combo(
        hero="Lina",
        name="Euls setup one-shot",
        difficulty="Medium",
        description="Guaranteed stun: Euls into Light Strike Array timed at landing.",
        steps=[
            ComboStep("1", "Euls the target", 1600, "LSA has a 0.5s delay — cast at ~1.6s of the cyclone"),
            ComboStep("W", "Light Strike Array under the landing spot", 500),
            ComboStep("Q", "Dragon Slave while stunned", 300),
            ComboStep("R", "Laguna Blade", 0, "Attack between casts for Fiery Soul stacks"),
        ],
    ),
    Combo(
        hero="Shadow Fiend",
        name="Blink triple raze",
        difficulty="Hard",
        description="Requiem into razes — the classic SF one-shot on mid targets.",
        steps=[
            ComboStep("D", "Blink on top of the target", 150, "Requiem needs point-blank range for max damage"),
            ComboStep("R", "Requiem of Souls", 900, "Or Euls yourself first to hide the cast time"),
            ComboStep("Q", "Shadowraze (close)", 350, "Target is feared away — razes chase the escape path"),
            ComboStep("W", "Shadowraze (medium)", 350),
            ComboStep("E", "Shadowraze (far)", 0),
        ],
    ),
    Combo(
        hero="Magnus",
        name="RP + Skewer team wipe",
        difficulty="Hard",
        description="Blink RP, Horn of the Fold, then skewer them back into your team.",
        steps=[
            ComboStep("D", "Blink into the enemy group", 150),
            ComboStep("R", "Reverse Polarity", 600, "Turn towards your team BEFORE skewering"),
            ComboStep("W", "Empower yourself / carry (pre-cast ideally)", 400),
            ComboStep("E", "Skewer the pile towards allies", 700),
            ComboStep("Q", "Shockwave as they land", 0),
        ],
    ),
    Combo(
        hero="Invoker (QW)",
        name="Tornado – EMP – Meteor – Deafening",
        difficulty="Hard",
        description="The bread-and-butter Euls-style lockdown combo for QW Invoker.",
        steps=[
            ComboStep("Q Q W R", "Invoke Tornado", 300),
            ComboStep("D", "Cast Tornado", 700, "Lead the target — it travels"),
            ComboStep("W W W R", "Invoke EMP while tornado flies", 300),
            ComboStep("F", "Cast EMP to land as they drop", 700),
            ComboStep("Q W E R", "Invoke Chaos Meteor", 300),
            ComboStep("D", "Meteor under the landing spot", 500),
            ComboStep("Q W W R", "Invoke Deafening Blast", 300),
            ComboStep("F", "Blast to push them along the meteor", 0),
        ],
    ),
    Combo(
        hero="Storm Spirit",
        name="Ball lightning pick-off",
        difficulty="Medium",
        description="Zip in, lock them down, orb-walk the kill before mana runs dry.",
        steps=[
            ComboStep("R", "Ball Lightning onto the target", 200, "Short zips: exit right on top of them"),
            ComboStep("E", "Electric Vortex", 300),
            ComboStep("Q", "Static Remnant point-blank", 400),
            ComboStep("A", "Attack for Overload procs", 800, "Overload slows — keep attacking"),
            ComboStep("R", "Small zip to refresh Overload", 400),
            ComboStep("A", "Finish with attacks", 0),
        ],
    ),
    Combo(
        hero="Puck",
        name="Dream Coil control",
        difficulty="Medium",
        description="Initiate with orb, coil the pile, silence, and phase the counter-burst.",
        steps=[
            ComboStep("Q", "Illusory Orb towards the fight", 500),
            ComboStep("D", "Ethereal Jaunt / Blink in", 200),
            ComboStep("R", "Dream Coil the group", 400),
            ComboStep("W", "Waning Rift (silence) inside the coil", 400),
            ComboStep("F", "Phase Shift to dodge the response", 900, "Count the enemy stun durations"),
            ComboStep("Q", "Orb out or chase the leash breakers", 0),
        ],
    ),
    Combo(
        hero="Earthshaker",
        name="Echo Slam jump",
        difficulty="Easy",
        description="Blink Echo — the more of them, the louder the slam.",
        steps=[
            ComboStep("D", "Blink into the middle of the fight", 100, "Echo instantly — don't let them scatter"),
            ComboStep("R", "Echo Slam", 400),
            ComboStep("Q", "Fissure to trap the survivors", 400),
            ComboStep("W", "Enchant Totem (Aghs: jump)", 300),
            ComboStep("A", "Totem hit", 0),
        ],
    ),
]


def heroes() -> list[str]:
    seen: list[str] = []
    for c in COMBOS:
        if c.hero not in seen:
            seen.append(c.hero)
    return seen


def combos_for(hero: str) -> list[Combo]:
    return [c for c in COMBOS if c.hero == hero]
