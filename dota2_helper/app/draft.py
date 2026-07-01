"""Draft analysis engine: hero database, counter/synergy matrix and pick scoring.

Everything is computed from a curated offline matchup dataset — the app never
reads the game client, so you tick picks/bans by hand during the draft and get
live recommendations.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Hero:
    name: str
    attr: str                     # STR / AGI / INT / UNI
    positions: tuple[int, ...]    # 1 carry, 2 mid, 3 offlane, 4/5 supports
    dmg: str                      # phys / magic / mixed
    tags: frozenset[str] = field(default_factory=frozenset)


def _h(name, attr, positions, dmg, *tags):
    return Hero(name, attr, tuple(positions), dmg, frozenset(tags))


# tags: stun (hard disable), init (initiator), aoe (teamfight), save (protects allies),
#       push (tower pressure), late (late-game scaler), early (strong early), escape,
#       silence, illusion, summons, burst, sustain
HEROES: list[Hero] = [
    _h("Anti-Mage", "AGI", (1,), "phys", "late", "escape"),
    _h("Phantom Assassin", "AGI", (1,), "phys", "burst", "late"),
    _h("Juggernaut", "AGI", (1,), "phys", "early", "sustain"),
    _h("Faceless Void", "AGI", (1,), "phys", "late", "init", "aoe", "stun"),
    _h("Spectre", "AGI", (1,), "phys", "late", "init"),
    _h("Luna", "AGI", (1,), "mixed", "push", "aoe", "late"),
    _h("Terrorblade", "AGI", (1,), "phys", "push", "illusion", "late"),
    _h("Slark", "AGI", (1,), "phys", "escape", "sustain"),
    _h("Ursa", "AGI", (1,), "phys", "early", "burst"),
    _h("Lifestealer", "STR", (1,), "phys", "sustain", "early"),
    _h("Morphling", "AGI", (1,), "mixed", "late", "escape", "burst"),
    _h("Drow Ranger", "AGI", (1,), "phys", "push", "silence", "late"),
    _h("Medusa", "AGI", (1,), "phys", "late", "aoe"),
    _h("Phantom Lancer", "AGI", (1,), "phys", "illusion", "late"),
    _h("Sven", "STR", (1,), "phys", "stun", "aoe", "burst"),
    _h("Wraith King", "STR", (1,), "phys", "stun", "sustain", "late"),
    _h("Troll Warlord", "AGI", (1,), "phys", "push", "early"),

    _h("Invoker", "UNI", (2,), "magic", "aoe", "burst", "stun"),
    _h("Storm Spirit", "INT", (2,), "magic", "escape", "burst", "init"),
    _h("Shadow Fiend", "AGI", (2,), "mixed", "burst", "aoe", "push"),
    _h("Puck", "INT", (2,), "magic", "init", "escape", "silence", "aoe"),
    _h("Queen of Pain", "INT", (2,), "magic", "burst", "escape", "aoe", "silence"),
    _h("Templar Assassin", "AGI", (2,), "phys", "burst", "early", "push"),
    _h("Ember Spirit", "AGI", (2,), "mixed", "escape", "aoe"),
    _h("Void Spirit", "UNI", (2,), "magic", "escape", "burst", "init", "silence"),
    _h("Lina", "INT", (2, 5), "magic", "stun", "burst"),
    _h("Zeus", "INT", (2,), "magic", "aoe", "burst"),
    _h("Sniper", "AGI", (2,), "phys", "push", "late"),
    _h("Huskar", "STR", (2,), "mixed", "early", "sustain", "burst"),
    _h("Outworld Destroyer", "INT", (2,), "magic", "burst", "late"),
    _h("Death Prophet", "INT", (2,), "magic", "push", "silence", "sustain", "aoe"),
    _h("Tinker", "INT", (2,), "magic", "push", "burst"),

    _h("Axe", "STR", (3,), "mixed", "init", "aoe", "early"),
    _h("Mars", "STR", (3,), "phys", "stun", "init", "aoe"),
    _h("Tidehunter", "STR", (3, 5), "magic", "init", "aoe", "stun"),
    _h("Centaur Warrunner", "STR", (3,), "mixed", "init", "stun", "aoe", "save"),
    _h("Bristleback", "STR", (3,), "phys", "sustain", "early"),
    _h("Timbersaw", "UNI", (3,), "magic", "sustain", "escape", "early"),
    _h("Dark Seer", "UNI", (3,), "magic", "aoe", "init", "illusion"),
    _h("Beastmaster", "UNI", (3,), "phys", "push", "summons", "stun", "init"),
    _h("Underlord", "STR", (3,), "magic", "aoe", "push", "save"),
    _h("Doom", "STR", (3,), "mixed", "silence", "init", "late"),
    _h("Legion Commander", "STR", (3,), "phys", "init", "burst", "sustain"),
    _h("Night Stalker", "STR", (3,), "phys", "init", "silence", "early"),
    _h("Slardar", "STR", (3,), "phys", "stun", "init", "early"),
    _h("Magnus", "UNI", (3, 2), "mixed", "init", "stun", "aoe", "save"),
    _h("Pangolier", "UNI", (3, 2), "mixed", "init", "stun", "aoe", "escape"),
    _h("Earthshaker", "STR", (4, 3), "magic", "stun", "init", "aoe", "burst"),
    _h("Tusk", "STR", (4, 3), "phys", "stun", "init", "save", "early"),
    _h("Pudge", "STR", (4, 2), "mixed", "stun", "init", "sustain"),
    _h("Mirana", "UNI", (4, 2), "mixed", "stun", "save", "escape"),

    _h("Crystal Maiden", "INT", (5,), "magic", "stun", "aoe", "early"),
    _h("Lion", "INT", (5, 4), "magic", "stun", "burst"),
    _h("Shadow Shaman", "INT", (5,), "magic", "stun", "push", "early"),
    _h("Witch Doctor", "INT", (5,), "magic", "stun", "sustain", "burst"),
    _h("Warlock", "INT", (5,), "magic", "aoe", "stun", "sustain"),
    _h("Dazzle", "UNI", (5,), "magic", "save", "sustain", "push"),
    _h("Oracle", "INT", (5,), "magic", "save", "sustain", "silence"),
    _h("Winter Wyvern", "UNI", (5,), "magic", "save", "stun", "aoe"),
    _h("Disruptor", "INT", (5,), "magic", "aoe", "stun", "silence"),
    _h("Rubick", "INT", (4, 5), "magic", "stun", "aoe"),
    _h("Bane", "INT", (5, 4), "magic", "stun", "save"),
    _h("Grimstroke", "INT", (5,), "magic", "stun", "silence", "aoe"),
    _h("Jakiro", "INT", (5, 4), "magic", "stun", "aoe", "push"),
    _h("Silencer", "INT", (5, 4), "magic", "silence", "late"),
    _h("Ancient Apparition", "INT", (5, 4), "magic", "aoe", "burst"),
    _h("Io", "UNI", (5, 4), "magic", "save", "sustain"),
    _h("Treant Protector", "STR", (5, 4), "magic", "save", "stun", "aoe"),
    _h("Vengeful Spirit", "UNI", (5, 4), "phys", "stun", "save", "early"),
    _h("Undying", "STR", (5, 4), "mixed", "early", "sustain", "aoe"),
    _h("Snapfire", "UNI", (5, 4), "magic", "stun", "aoe", "burst"),
    _h("Hoodwink", "AGI", (4, 5), "mixed", "stun", "escape", "burst"),
    _h("Ogre Magi", "STR", (5, 4), "magic", "stun", "early", "sustain"),
    _h("Weaver", "AGI", (4, 1), "phys", "escape", "early", "late"),
    _h("Enchantress", "UNI", (5, 4), "phys", "summons", "sustain", "early"),
]

BY_NAME: dict[str, Hero] = {h.name: h for h in HEROES}


# ------------------------------------------------------------------ matchups
# COUNTERS[a][b] = weight: picking `a` is good against enemy `b` (1 = slight
# edge, 3 = hard counter). Curated from well-known matchup knowledge.

COUNTERS: dict[str, dict[str, float]] = {
    "Anti-Mage": {"Medusa": 3, "Storm Spirit": 2.5, "Invoker": 2, "Outworld Destroyer": 2, "Zeus": 2, "Crystal Maiden": 1.5},
    "Axe": {"Phantom Assassin": 3, "Phantom Lancer": 2.5, "Terrorblade": 2, "Anti-Mage": 2, "Juggernaut": 1.5, "Slark": 1.5},
    "Legion Commander": {"Anti-Mage": 2, "Slark": 2, "Storm Spirit": 1.5, "Ember Spirit": 1.5, "Weaver": 1.5},
    "Slardar": {"Phantom Assassin": 2.5, "Anti-Mage": 2, "Slark": 2, "Weaver": 2, "Morphling": 1.5},
    "Bristleback": {"Phantom Assassin": 2, "Ursa": 1.5, "Troll Warlord": 1.5, "Juggernaut": 1.5},
    "Timbersaw": {"Sven": 2.5, "Wraith King": 2.5, "Bristleback": 2, "Axe": 2, "Centaur Warrunner": 2, "Legion Commander": 2},
    "Ancient Apparition": {"Lifestealer": 3, "Huskar": 3, "Bristleback": 2.5, "Dazzle": 2.5, "Wraith King": 2, "Slark": 2, "Undying": 2},
    "Silencer": {"Storm Spirit": 2.5, "Puck": 2, "Void Spirit": 2, "Ember Spirit": 2, "Enchantress": 2, "Warlock": 1.5},
    "Doom": {"Tidehunter": 2.5, "Faceless Void": 2, "Warlock": 2, "Bristleback": 2, "Timbersaw": 2},
    "Faceless Void": {"Sniper": 2, "Drow Ranger": 2, "Zeus": 2, "Crystal Maiden": 1.5, "Witch Doctor": 1.5},
    "Lifestealer": {"Axe": 2, "Bristleback": 1.5, "Pudge": 2, "Bane": 1.5, "Medusa": 1.5},
    "Ursa": {"Medusa": 2, "Spectre": 1.5, "Terrorblade": 1.5},
    "Sven": {"Phantom Lancer": 2.5, "Terrorblade": 2, "Medusa": 1.5},
    "Earthshaker": {"Phantom Lancer": 3, "Terrorblade": 2.5, "Beastmaster": 2, "Enchantress": 1.5},
    "Winter Wyvern": {"Phantom Assassin": 2.5, "Sven": 2, "Wraith King": 2, "Juggernaut": 2, "Ursa": 2, "Troll Warlord": 2},
    "Puck": {"Sniper": 2, "Drow Ranger": 2, "Shadow Fiend": 1.5, "Tinker": 1.5, "Death Prophet": 1.5},
    "Storm Spirit": {"Sniper": 2.5, "Drow Ranger": 2, "Zeus": 2, "Tinker": 2, "Crystal Maiden": 2},
    "Queen of Pain": {"Storm Spirit": 1.5, "Tinker": 2, "Shadow Fiend": 1.5, "Invoker": 1.5},
    "Templar Assassin": {"Zeus": 2, "Sniper": 1.5, "Outworld Destroyer": 2, "Puck": 1.5},
    "Huskar": {"Sniper": 2.5, "Drow Ranger": 2, "Zeus": 2, "Shadow Fiend": 2, "Invoker": 1.5},
    "Night Stalker": {"Storm Spirit": 2, "Puck": 2, "Invoker": 2, "Tinker": 2.5, "Queen of Pain": 1.5, "Void Spirit": 1.5},
    "Zeus": {"Slark": 2, "Weaver": 2, "Storm Spirit": 1.5, "Ember Spirit": 1.5, "Phantom Lancer": 1.5},
    "Bane": {"Huskar": 2.5, "Lifestealer": 2, "Juggernaut": 1.5, "Sven": 1.5},
    "Shadow Shaman": {"Void Spirit": 1.5, "Slark": 1.5, "Weaver": 1.5, "Beastmaster": 2},
    "Lion": {"Storm Spirit": 2, "Puck": 1.5, "Morphling": 2, "Ember Spirit": 1.5},
    "Disruptor": {"Storm Spirit": 2.5, "Ember Spirit": 2, "Slark": 2, "Weaver": 2, "Anti-Mage": 1.5},
    "Grimstroke": {"Phantom Lancer": 2, "Terrorblade": 1.5, "Slark": 1.5, "Storm Spirit": 1.5},
    "Pudge": {"Sniper": 2, "Drow Ranger": 2, "Crystal Maiden": 1.5, "Shadow Fiend": 1.5},
    "Spectre": {"Sniper": 2.5, "Drow Ranger": 2, "Zeus": 2.5, "Storm Spirit": 1.5, "Tinker": 2},
    "Phantom Lancer": {"Sniper": 2, "Legion Commander": 2, "Ursa": 2, "Lion": 1.5, "Bane": 1.5},
    "Medusa": {"Phantom Lancer": 2.5, "Terrorblade": 2, "Sven": 1.5},
    "Tidehunter": {"Phantom Assassin": 2, "Ursa": 2, "Juggernaut": 1.5, "Legion Commander": 1.5},
    "Underlord": {"Ursa": 2, "Troll Warlord": 2, "Lifestealer": 1.5, "Phantom Assassin": 1.5},
    "Warlock": {"Phantom Lancer": 2, "Terrorblade": 2, "Luna": 1.5, "Medusa": 1.5},
    "Jakiro": {"Phantom Lancer": 2, "Terrorblade": 2, "Beastmaster": 2, "Enchantress": 1.5},
    "Dark Seer": {"Ursa": 2, "Sven": 2, "Phantom Assassin": 2, "Lifestealer": 1.5},
    "Outworld Destroyer": {"Bristleback": 2, "Centaur Warrunner": 2, "Wraith King": 2, "Medusa": 1.5},
    "Drow Ranger": {"Beastmaster": 2, "Enchantress": 2, "Phantom Lancer": 1.5, "Warlock": 1.5},
    "Luna": {"Beastmaster": 1.5, "Phantom Lancer": 1.5, "Terrorblade": 1.5},
    "Death Prophet": {"Bristleback": 2, "Underlord": 1.5, "Tidehunter": 1.5, "Timbersaw": 1.5},
    "Weaver": {"Axe": 1.5, "Bristleback": 1.5, "Tidehunter": 1.5},
    "Slark": {"Sniper": 2.5, "Drow Ranger": 2.5, "Crystal Maiden": 2, "Lion": 1.5, "Medusa": 1.5},
    "Mars": {"Sniper": 2.5, "Drow Ranger": 2.5, "Luna": 2, "Medusa": 1.5},
    "Magnus": {"Phantom Lancer": 2, "Medusa": 2, "Luna": 1.5, "Sniper": 1.5},
    "Centaur Warrunner": {"Sniper": 2, "Drow Ranger": 2, "Zeus": 1.5, "Tinker": 1.5},
    "Beastmaster": {"Puck": 1.5, "Void Spirit": 1.5, "Weaver": 1.5, "Slark": 1.5},
    "Oracle": {"Legion Commander": 2.5, "Doom": 2, "Bane": 2, "Axe": 2, "Phantom Assassin": 1.5},
    "Dazzle": {"Legion Commander": 2, "Axe": 2, "Lion": 1.5, "Sven": 1.5},
    "Io": {"Doom": 1.5, "Bane": 1.5, "Legion Commander": 1.5},
    "Treant Protector": {"Sniper": 1.5, "Drow Ranger": 1.5, "Templar Assassin": 1.5},
    "Vengeful Spirit": {"Phantom Assassin": 1.5, "Slark": 1.5, "Morphling": 1.5},
    "Witch Doctor": {"Phantom Lancer": 1.5, "Lifestealer": 1.5, "Huskar": 2, "Bristleback": 1.5},
    "Crystal Maiden": {"Lifestealer": 1.5, "Ursa": 1.5, "Legion Commander": 1.5},
    "Undying": {"Bristleback": 2, "Timbersaw": 1.5, "Axe": 1.5, "Huskar": 2},
    "Snapfire": {"Phantom Lancer": 1.5, "Terrorblade": 1.5, "Slark": 1.5},
    "Hoodwink": {"Sniper": 1.5, "Drow Ranger": 1.5, "Medusa": 1.5},
    "Rubick": {"Tidehunter": 2.5, "Warlock": 2.5, "Magnus": 2.5, "Earthshaker": 2, "Invoker": 2},
    "Ember Spirit": {"Sniper": 2, "Drow Ranger": 2, "Crystal Maiden": 2, "Phantom Lancer": 2},
    "Void Spirit": {"Sniper": 2, "Drow Ranger": 2, "Zeus": 2, "Tinker": 2, "Crystal Maiden": 1.5},
    "Invoker": {"Phantom Lancer": 2, "Terrorblade": 1.5, "Warlock": 1.5},
    "Shadow Fiend": {"Sniper": 1.5, "Tinker": 1.5, "Templar Assassin": 1.5},
    "Lina": {"Bristleback": 1.5, "Undying": 1.5, "Wraith King": 1.5},
    "Sniper": {"Wraith King": 1.5, "Bristleback": 1.5, "Axe": 1.5},
    "Tinker": {"Wraith King": 1.5, "Medusa": 1.5, "Spectre": 0.5},
    "Ogre Magi": {"Phantom Assassin": 1.5, "Troll Warlord": 1.5, "Ursa": 1.5},
    "Enchantress": {"Legion Commander": 2, "Ursa": 2, "Slardar": 1.5, "Night Stalker": 1.5},
    "Terrorblade": {"Crystal Maiden": 1.5, "Zeus": 0.5, "Witch Doctor": 1.5},
    "Juggernaut": {"Crystal Maiden": 2, "Shadow Shaman": 1.5, "Lion": 1.5, "Witch Doctor": 1.5},
    "Phantom Assassin": {"Crystal Maiden": 2, "Lion": 1.5, "Zeus": 1.5, "Lina": 1.5},
    "Wraith King": {"Crystal Maiden": 1.5, "Shadow Shaman": 1.5, "Sniper": 1.5},
    "Troll Warlord": {"Medusa": 1.5, "Terrorblade": 1.5, "Sniper": 1.5},
    "Morphling": {"Crystal Maiden": 2, "Lion": 2, "Shadow Shaman": 2, "Zeus": 1.5},
    "Pangolier": {"Ursa": 2, "Phantom Assassin": 2, "Troll Warlord": 2, "Juggernaut": 1.5},
    "Tusk": {"Sniper": 1.5, "Crystal Maiden": 1.5, "Hoodwink": 1.5},
    "Mirana": {"Crystal Maiden": 1.5, "Witch Doctor": 1.5, "Warlock": 1.5},
}
COUNTERS = {k: v for k, v in COUNTERS.items() if k in BY_NAME}
for _src, _targets in COUNTERS.items():
    for _t in list(_targets):
        if _t not in BY_NAME:
            del _targets[_t]


# SYNERGY: unordered pairs that combine especially well.
_SYNERGY_PAIRS: list[tuple[str, str, float]] = [
    ("Magnus", "Phantom Assassin", 2.5), ("Magnus", "Sven", 2.5), ("Magnus", "Juggernaut", 2),
    ("Magnus", "Medusa", 2), ("Magnus", "Luna", 2),
    ("Io", "Ursa", 2.5), ("Io", "Sven", 2), ("Io", "Lifestealer", 2), ("Io", "Wraith King", 2),
    ("Crystal Maiden", "Juggernaut", 2), ("Crystal Maiden", "Storm Spirit", 2), ("Crystal Maiden", "Medusa", 1.5),
    ("Faceless Void", "Invoker", 2.5), ("Faceless Void", "Witch Doctor", 2.5), ("Faceless Void", "Lina", 2),
    ("Faceless Void", "Jakiro", 2), ("Faceless Void", "Snapfire", 2),
    ("Warlock", "Faceless Void", 2), ("Warlock", "Magnus", 2), ("Warlock", "Tidehunter", 2),
    ("Tidehunter", "Sven", 2), ("Tidehunter", "Luna", 2), ("Tidehunter", "Zeus", 1.5),
    ("Dark Seer", "Luna", 2), ("Dark Seer", "Medusa", 2), ("Dark Seer", "Phantom Assassin", 1.5),
    ("Beastmaster", "Drow Ranger", 2), ("Beastmaster", "Luna", 1.5),
    ("Drow Ranger", "Vengeful Spirit", 2), ("Drow Ranger", "Shadow Shaman", 1.5),
    ("Winter Wyvern", "Medusa", 2), ("Winter Wyvern", "Sniper", 1.5), ("Winter Wyvern", "Drow Ranger", 1.5),
    ("Oracle", "Huskar", 2.5), ("Oracle", "Ursa", 1.5), ("Dazzle", "Huskar", 2),
    ("Dazzle", "Bristleback", 2), ("Oracle", "Bristleback", 1.5),
    ("Earthshaker", "Anti-Mage", 2), ("Earthshaker", "Storm Spirit", 1.5),
    ("Bane", "Sven", 1.5), ("Bane", "Phantom Assassin", 1.5),
    ("Shadow Shaman", "Beastmaster", 2), ("Shadow Shaman", "Death Prophet", 2), ("Shadow Shaman", "Sniper", 1.5),
    ("Jakiro", "Beastmaster", 1.5), ("Jakiro", "Death Prophet", 1.5),
    ("Lion", "Storm Spirit", 1.5), ("Lion", "Queen of Pain", 1.5),
    ("Grimstroke", "Lion", 2), ("Grimstroke", "Lina", 1.5), ("Grimstroke", "Bane", 2),
    ("Disruptor", "Sven", 1.5), ("Disruptor", "Luna", 1.5),
    ("Treant Protector", "Weaver", 1.5), ("Treant Protector", "Sniper", 1.5),
    ("Vengeful Spirit", "Luna", 2), ("Vengeful Spirit", "Terrorblade", 2),
    ("Undying", "Bristleback", 1.5), ("Undying", "Huskar", 1.5),
    ("Mirana", "Templar Assassin", 1.5), ("Mirana", "Sniper", 1.5),
    ("Tusk", "Templar Assassin", 2), ("Tusk", "Ursa", 1.5),
    ("Pudge", "Templar Assassin", 1.5), ("Pudge", "Sniper", 1.5),
    ("Snapfire", "Sven", 1.5), ("Snapfire", "Ursa", 1.5),
    ("Witch Doctor", "Sven", 1.5), ("Witch Doctor", "Faceless Void", 2),
    ("Ancient Apparition", "Sniper", 1.5), ("Ancient Apparition", "Zeus", 1.5),
    ("Zeus", "Ancient Apparition", 1.5), ("Silencer", "Legion Commander", 1.5),
    ("Centaur Warrunner", "Io", 1.5), ("Ogre Magi", "Troll Warlord", 1.5),
    ("Ogre Magi", "Ursa", 1.5), ("Hoodwink", "Sniper", 1.5),
    ("Puck", "Templar Assassin", 1.5), ("Enchantress", "Drow Ranger", 1.5),
]

SYNERGY: dict[frozenset[str], float] = {}
for a, b, w in _SYNERGY_PAIRS:
    if a in BY_NAME and b in BY_NAME:
        key = frozenset((a, b))
        SYNERGY[key] = max(SYNERGY.get(key, 0), w)


# ------------------------------------------------------------------ scoring

@dataclass
class Suggestion:
    hero: Hero
    score: float
    reasons: list[str]


def _counter_weight(attacker: str, defender: str) -> float:
    return COUNTERS.get(attacker, {}).get(defender, 0.0)


def suggest(
    allies: list[str],
    enemies: list[str],
    banned: list[str],
    position: int | None = None,
    count: int = 10,
) -> list[Suggestion]:
    """Rank the best remaining picks for the current draft state."""
    taken = set(allies) | set(enemies) | set(banned)
    ally_tags: set[str] = set()
    for a in allies:
        ally_tags |= BY_NAME[a].tags
    ally_positions = {p for a in allies for p in BY_NAME[a].positions[:1]}

    results: list[Suggestion] = []
    for hero in HEROES:
        if hero.name in taken:
            continue
        if position is not None and position not in hero.positions:
            continue

        score = 0.0
        reasons: list[str] = []

        for e in enemies:
            w = _counter_weight(hero.name, e)
            if w:
                score += w * 2.0
                reasons.append(f"counters {e}")
            w = _counter_weight(e, hero.name)
            if w:
                score -= w * 1.6
                reasons.append(f"weak vs {e}")

        for a in allies:
            w = SYNERGY.get(frozenset((hero.name, a)), 0.0)
            if w:
                score += w * 1.5
                reasons.append(f"synergy with {a}")

        # round out the team: reward what the lineup is missing
        if allies:
            if "stun" in hero.tags and "stun" not in ally_tags:
                score += 1.5
                reasons.append("adds hard disable")
            if "init" in hero.tags and "init" not in ally_tags:
                score += 1.2
                reasons.append("adds initiation")
            if "late" in hero.tags and "late" not in ally_tags:
                score += 0.8
                reasons.append("adds late game")
            if "save" in hero.tags and "save" not in ally_tags and len(allies) >= 2:
                score += 0.6
                reasons.append("adds a saving ability")
            if hero.positions[0] not in ally_positions:
                score += 0.5

        results.append(Suggestion(hero, round(score, 2), reasons[:4]))

    results.sort(key=lambda s: s.score, reverse=True)
    return results[:count]


# ------------------------------------------------------------------ team report

@dataclass
class TeamReport:
    control: int
    initiation: int
    saves: int
    physical: int
    magical: int
    late: int
    early: int
    warnings: list[str]


def analyze_team(allies: list[str]) -> TeamReport:
    heroes = [BY_NAME[a] for a in allies]
    tags = [h.tags for h in heroes]
    control = sum(1 for t in tags if "stun" in t)
    initiation = sum(1 for t in tags if "init" in t)
    saves = sum(1 for t in tags if "save" in t)
    physical = sum(1 for h in heroes if h.dmg in ("phys", "mixed"))
    magical = sum(1 for h in heroes if h.dmg in ("magic", "mixed"))
    late = sum(1 for t in tags if "late" in t)
    early = sum(1 for t in tags if "early" in t)

    warnings: list[str] = []
    if len(heroes) >= 3:
        if control == 0:
            warnings.append("No hard disable — kills will be hard to secure.")
        if initiation == 0:
            warnings.append("No initiator — fights will start on the enemy's terms.")
        if magical == 0:
            warnings.append("All-physical damage — a single Ghost Scepter ruins you.")
        if physical == 0:
            warnings.append("All-magical damage — Pipe/BKB timings will hurt.")
        if late == 0 and len(heroes) >= 4:
            warnings.append("No late-game scaler — close the game before 35:00.")
    return TeamReport(control, initiation, saves, physical, magical, late, early, warnings)
