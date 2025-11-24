import os
import json
import random
from datetime import datetime

import pandas as pd
from PIL import Image
from faker import Faker

# ---------------------------------------------------
# CONFIGURACIÓN PRINCIPAL
# ---------------------------------------------------
ROOT = os.path.dirname(os.path.abspath(__file__))

RACES_PATH = os.path.join(ROOT, "Races")
CLASSES_PATH = os.path.join(ROOT, "Classes")
BACKGROUNDS_PATH = os.path.join(ROOT, "Backgrounds")

OUTPUT_IMAGES = os.path.join(ROOT, "output_images")
OUTPUT_METADATA = os.path.join(ROOT, "output_metadata")

LOOKUP_FILE = os.path.join(ROOT, "lookup_tables.json")
COMPATIBILITY_FILE = os.path.join(ROOT, "compatibility.json")
BASE_STATS_FILE = os.path.join(ROOT, "base_statsf.xlsx")

IPFS_CID = "TO_BE_DEFINED"  # <-- cambia esto por tu CID real

# ---------------------------------------------------
# CARGA DE CONFIGURACIÓN
# ---------------------------------------------------
with open(LOOKUP_FILE, "r", encoding="utf-8") as f:
    LOOKUP = json.load(f)

with open(COMPATIBILITY_FILE, "r", encoding="utf-8") as f:
    COMPAT = json.load(f)

BASE_STATS = pd.read_excel(BASE_STATS_FILE)

# ---------------------------------------------------
# SISTEMA DE RAREZAS
# ---------------------------------------------------
RARITY_BY_RACE = {
    "Human": "Common",
    "Elf": "Common",
    "Orc": "Common",
    "Triton": "Common",
    "Barbarian": "Rare",
    "Beast": "Rare",
    "Demon": "Rare",
    "Demonkin": "Rare",
    "Draconic": "Rare",
    "Voidborn": "Rare",
    "Spectral": "Legendary",
}

# ---------------------------------------------------
# FAKER + GENERADOR DE NOMBRES v2 EXPANDIDO
# ---------------------------------------------------
fake = Faker()
Faker.seed(42)

# ===================================================
# SUFIJOS BASE (60)
# ===================================================
NAME_SUFFIXES = [
    "ar", "en", "eth", "ion", "is", "ir", "or", "ael", "yn", "ira", "oth",
    "rak", "gor", "gra", "drax", "riel", "ash", "vyr", "zor", "reth", "thal",
    "drin", "vash", "morn", "kesh", "zeth", "kar", "syl", "vor", "rion",
    "wen", "leth", "mir", "thas", "nar", "ris", "dael", "vyn", "orn", "iel",
    "ath", "eus", "ios", "aen", "ux", "ax", "eon", "ian", "ius",
    "xar", "zul", "kron", "vex", "nyx", "thrax", "gul", "mor", "bane", "doom"
]

# ===================================================
# PALABRAS BASE COMPARTIDAS
# ===================================================
ARCANE_WORDS = [
    "Ember", "Ash", "Cinder", "Gloom", "Echo", "Void", "Frost", "Dawn",
    "Dusk", "Hollow", "Broken", "Shattered", "Silent", "Burning",
    "Fading", "Forgotten", "Whispering", "Ancient", "Molten", "Obsidian",
    "Smoldering", "Scorched", "Blazing", "Charred", "Ignited", "Searing",
    "Umbral", "Tenebrous", "Abyssal", "Shadowed", "Veiled", "Eclipsed",
    "Withered", "Crumbling", "Eroded", "Timeworn", "Rusted", "Decayed",
    "Crystalline", "Ethereal", "Spectral", "Phantom", "Wraith", "Arcane",
    "Blighted", "Thorned", "Rotting", "Petrified", "Cursed", "Twisted",
    "Sovereign", "Exalted", "Primordial", "Eternal", "Undying", "Relentless"
]

MYTHIC_PLACES = [
    "Emberholm", "the Broken Gate", "the Last Spire", "the Ashen Reach",
    "the Hollow Coast", "the Sunken Archive", "the Shardfields",
    "the Ember Vaults", "the Silent Bastion", "the Fractured Range",
    "the Fallen Citadel", "the Crumbling Throne", "the Obsidian Keep",
    "the Shattered Cathedral", "the Forsaken Tower", "the Ruined Sanctum",
    "the Blackened Halls", "the Cindered Palace", "the Desolate Fortress",
    "the Ashen Wastes", "the Blighted Moor", "the Crimson Valley",
    "the Dying Marsh", "the Endless Crypt", "the Frozen Abyss",
    "the Gleaming Depths", "the Howling Peaks", "the Iron Desert",
    "the Leyline Nexus", "the Maw of Eternity", "the Nightmare Realm",
    "the Oracle's Grave", "the Prismatic Void", "the Scarred Earth"
]

CHAOS_WORDS = [
    "Madness", "Decay", "Abyss", "Storms", "Shadows", "Ruins", "Night",
    "Entropy", "Cataclism", "Echoes", "Annihilation", "Devastation",
    "Oblivion", "Ruin", "Collapse", "Corruption", "Pestilence", "Blight",
    "Rot", "Taint", "Despair", "Dread", "Horror", "Torment", "Anguish",
    "Tempests", "Silence", "Famine", "Plague", "Chaos"
]

PLURAL_THINGS = [
    "Stars", "Bones", "Sigils", "Chains", "Dreams", "Oaths", "Sparks",
    "Fragments", "Wards", "Relics", "Runes", "Seals", "Glyphs", "Totems",
    "Talismans", "Crystals", "Memories", "Visions", "Whispers", "Secrets",
    "Truths", "Lies", "Flames", "Ashes", "Thorns", "Embers", "Storms",
    "Remnants", "Echoes", "Vestiges", "Shards", "Splinters"
]

HONORIFICS = [
    "the Undaunted", "the Accursed", "the Forsaken", "the Exiled",
    "the Nameless", "the Branded", "the Scarred", "the Hollow",
    "the Twice-Born", "the Deathless", "the Soulbound", "the Marked",
    "the Unbowed", "the Shackled", "the Liberated", "the Condemned",
    "the Awakened", "the Slumbering", "the Veiled", "the Unveiled",
    "the First", "the Last", "the Forgotten", "the Remembered", "the Chosen"
]

ACTION_VERBS = [
    "Who Walked", "Who Fell at", "Who Burned", "Who Rose from",
    "Who Conquered", "Who Defied", "Who Shattered", "Who Bound",
    "Who Sealed", "Who Unleashed", "Who Survived", "Who Witnessed",
    "Who Claimed", "Who Sacrificed at", "Who Guards", "Who Haunts",
    "Who Seeks", "Who Remembers", "Who Forgot", "Who Endures"
]

ACTION_SIMPLE = [
    "Saved", "Destroyed", "Rebuilt", "Betrayed", "Protected",
    "Abandoned", "Conquered", "Lost", "Found", "Cursed"
]

# ===================================================
# TÍTULOS GENÉRICOS (base)
# ===================================================
GENERIC_PATTERNS = [
    "Shadow of {arcane} {things}",
    "Echo of {arcane} {chaos}",
    "Warden of {place}",
    "Bearer of the {arcane} {arcane2}",
    "Keeper of {arcane} {things}",
    "Harbinger of {chaos}",
    "Voice of {place}",
    "Bound to the {arcane} Coil",
    "Walker of {place}",
    "Last Flame of {place}",
    "{honorific}, Blade of {place}",
    "{honorific}, Scourge of {chaos}",
    "{honorific}, Seeker of {things}",
    "{action} {place}",
    "{action} the {arcane} {things}",
    "Heir to the {arcane} {things}",
    "Bane of {arcane} {chaos}",
    "Vessel of {chaos}",
    "Scion of {place}",
    "Champion of the {arcane} Flame",
    "Witness to {arcane} {chaos}",
    "Disciple of {arcane} {things}",
    "Pilgrim of {place}",
    "Remnant of the {arcane} Age",
    "Soul of {arcane} {things}",
    "Hand of {chaos}",
    "Eye of the {arcane} Storm",
    "Heart of {place}",
    "Last of the {arcane} {things}"
]

# ===================================================
# TÍTULOS POR RAZA (exclusivos)
# ===================================================
RACE_PATTERNS = {
    "Human": [
        "Heir of the Mortal Throne",
        "Last Hope of {place}",
        "The Commoner Who {action_simple} {place}",
        "Bastard of {place}",
        "Peasant King of {arcane} {things}",
        "The Mortal Who Defied {chaos}",
        "Forgotten Son of {place}",
        "Daughter of the {arcane} Dawn",
        "Common Blood, {arcane} Spirit",
        "The One Who Remained"
    ],
    "Elf": [
        "Voice of the Eternal Grove",
        "Last Singer of {place}",
        "Starborn of the {arcane} Age",
        "Keeper of Ancient {things}",
        "Memory of {arcane} Twilight",
        "The Ageless Witness",
        "Dreamweaver of {place}",
        "Child of the First Dawn",
        "Echo of Elven {things}",
        "Guardian of Fading {things}"
    ],
    "Orc": [
        "Warchief of {arcane} Blood",
        "Breaker of {things}",
        "Iron Fist of {place}",
        "The Unbroken Tusk",
        "Conqueror of {place}",
        "Blood-Sworn to {chaos}",
        "The Green Tide",
        "Crusher of {arcane} {things}",
        "Born in {chaos}",
        "The Brutal {honorific}"
    ],
    "Triton": [
        "Voice of the Drowned Deep",
        "Tidecaller of {place}",
        "The Abyssal Sovereign",
        "Keeper of Sunken {things}",
        "Waveborn {honorific}",
        "Herald of the Deep {chaos}",
        "The One Who Swims in {arcane} Waters",
        "Child of the Endless Tide",
        "Coral-Crowned {honorific}",
        "Leviathan's Chosen"
    ],
    "Barbarian": [
        "Rage Incarnate",
        "Storm of the {arcane} Wastes",
        "The Unchained {honorific}",
        "Fury of {place}",
        "Blood of the Wild {things}",
        "The Savage {honorific}",
        "Bringer of {arcane} Ruin",
        "The Untamed One",
        "Berserker of {chaos}",
        "Wild Heart of {place}"
    ],
    "Beast": [
        "Fang of the {arcane} Wild",
        "Hunter in {arcane} Shadows",
        "The Primal {honorific}",
        "Pack Alpha of {place}",
        "Claw of {chaos}",
        "The Feral One",
        "Beast-Touched {honorific}",
        "Predator of {arcane} {things}",
        "Child of Tooth and Claw",
        "The Untamed Spirit"
    ],
    "Demon": [
        "Spawn of the {arcane} Pit",
        "Tormentor of {things}",
        "Hell-Forged {honorific}",
        "Bringer of {arcane} Damnation",
        "The Infernal {honorific}",
        "Corruptor of {place}",
        "Sin Incarnate",
        "The Damned {honorific}",
        "Flame of the Nether {chaos}",
        "Soul-Eater of {place}"
    ],
    "Demonkin": [
        "Half-Damned {honorific}",
        "The Tainted Blood",
        "Child of Two Realms",
        "Heir to {arcane} Sin",
        "The Cursed Lineage",
        "Born of {arcane} Flame",
        "Neither Mortal Nor Demon",
        "The Outcast {honorific}",
        "Blood of the {arcane} Pact",
        "The Twice-Cursed"
    ],
    "Draconic": [
        "Scion of the First Wyrm",
        "Dragon-Blooded {honorific}",
        "Scale of the {arcane} Flame",
        "Heir to the Hoard of {things}",
        "The Scaled {honorific}",
        "Voice of Ancient Wyrms",
        "Claw of the {arcane} Dragon",
        "Fire-Touched {honorific}",
        "The Draconic {honorific}",
        "Born of Wyrmfire"
    ],
    "Voidborn": [
        "Child of the Nothing",
        "Echo from Beyond {chaos}",
        "The Void-Touched {honorific}",
        "Walker Between Worlds",
        "Whisper of the {arcane} Void",
        "The Empty {honorific}",
        "Born of Starless Night",
        "Harbinger of the Null",
        "The One Who Sees Nothing",
        "Vessel of the {arcane} Void"
    ],
    "Spectral": [
        "The Unquiet Dead",
        "Wraith of {place}",
        "Soul Unbound from {arcane} Chains",
        "The Deathless {honorific}",
        "Echo of a Forgotten Life",
        "Phantom of {arcane} Memory",
        "The Haunting {honorific}",
        "Spirit of {place}",
        "The One Who Would Not Rest",
        "Ghost of {arcane} {things}",
        "Between Life and {chaos}",
        "The Ethereal {honorific}",
        "Memory Made Manifest",
        "Shade of the {arcane} Flame",
        "The Translucent {honorific}"
    ]
}

# ===================================================
# TÍTULOS POR CLASE (exclusivos)
# ===================================================
CLASS_PATTERNS = {
    "Warrior": [
        "Blade of {arcane} Steel",
        "The Unyielding Shield",
        "Sworn Sword of {place}",
        "Iron-Willed {honorific}",
        "The Battle-Scarred",
        "Champion of a Thousand Kills",
        "The Living Weapon",
        "Steel-Born {honorific}",
        "Defender of {arcane} {things}",
        "The Undefeated"
    ],
    "Wizard": [
        "Weaver of {arcane} Truths",
        "Master of the {arcane} Arts",
        "Keeper of Forbidden {things}",
        "The Spell-Scarred",
        "Archmage of {place}",
        "Binder of {arcane} {chaos}",
        "The Enlightened {honorific}",
        "Seeker of {arcane} Knowledge",
        "Voice of the Arcane Storm",
        "The One Who Speaks to {things}"
    ],
    "Rogue": [
        "Shadow-Dancer of {place}",
        "The Unseen {honorific}",
        "Blade in the {arcane} Dark",
        "Thief of {arcane} {things}",
        "The Silent {honorific}",
        "Whisper of {chaos}",
        "Master of Hidden {things}",
        "The Cunning {honorific}",
        "Dagger of {place}",
        "The One Who Strikes Unseen"
    ],
    "Paladin": [
        "Oath-Bound to {arcane} Light",
        "The Righteous {honorific}",
        "Shield of the Innocent",
        "Holy Warrior of {place}",
        "Light-Bringer in {arcane} {chaos}",
        "The Just {honorific}",
        "Crusader of {arcane} Truth",
        "Divine Blade of {place}",
        "The Unwavering Faith",
        "Protector of {arcane} {things}"
    ],
    "Necromancer": [
        "Master of the {arcane} Dead",
        "Death-Speaker of {place}",
        "The Corpse-Caller",
        "Binder of {arcane} Souls",
        "Lord of {arcane} Graves",
        "The Life-Stealer",
        "Whisper to the Dead",
        "Keeper of Death's {things}",
        "The Bone-Crowned {honorific}",
        "Shepherd of Lost Souls"
    ],
    "Ranger": [
        "Hunter of {arcane} Prey",
        "Warden of the {arcane} Wild",
        "The Far-Walker",
        "Arrow of {place}",
        "Tracker of {arcane} {things}",
        "The Silent Stalker",
        "Beast-Friend {honorific}",
        "Guardian of {arcane} Paths",
        "The Horizon-Seeker",
        "Eye of the {arcane} Forest"
    ],
    "Druid": [
        "Voice of the {arcane} Wild",
        "Shape-Shifter of {place}",
        "The Nature-Bound",
        "Keeper of {arcane} Growth",
        "Speaker to {arcane} Beasts",
        "The Ever-Changing",
        "Root and Branch {honorific}",
        "Guardian of the {arcane} Cycle",
        "The Green {honorific}",
        "Child of Earth and Sky"
    ],
    "Cleric": [
        "Voice of the {arcane} Divine",
        "Healer of {arcane} Wounds",
        "The Faith-Keeper",
        "Channel of {arcane} Light",
        "Prayer-Singer of {place}",
        "The Blessed {honorific}",
        "Miracle-Worker of {place}",
        "Servant of {arcane} Powers",
        "The Devoted {honorific}",
        "Keeper of Sacred {things}"
    ],
    "Bard": [
        "Voice of {arcane} Songs",
        "Tale-Spinner of {place}",
        "The Wandering {honorific}",
        "Keeper of {arcane} Stories",
        "Melody of {chaos}",
        "The Silver-Tongued",
        "Song-Weaver of {place}",
        "Legend-Keeper {honorific}",
        "Voice That Moves {things}",
        "The Inspiring {honorific}"
    ],
    "Alchemist": [
        "Mixer of {arcane} Truths",
        "The Transmuter",
        "Seeker of the {arcane} Formula",
        "Brewer of {arcane} {chaos}",
        "The Experimental {honorific}",
        "Master of {arcane} Elixirs",
        "Catalyst of {chaos}",
        "The Flask-Bearer",
        "Philosopher of {arcane} Stone",
        "Creator of {arcane} {things}"
    ]
}

# ===================================================
# TÍTULOS ULTRA-RAROS (1.5% chance)
# ===================================================
ULTRA_RARE_PATTERNS = [
    # Títulos épicos únicos
    "The One Whose Name Was Erased",
    "First of the Last, Last of the First",
    "The Flame That Would Not Die",
    "Nameless, Yet Remembered",
    "The Weight of a Thousand Deaths",
    "Silence Before the Storm",
    "The Paradox of {place}",
    "Neither Here Nor There",
    "The Question Without Answer",
    "Memory of What Never Was",

    # Títulos con estructura única
    "...And So They Walked Alone",
    "Once Called Hero, Now Called {honorific}",
    "The Price of {arcane} Power",
    "What Remains After {chaos}",
    "The Last Word of {place}",
    "Before the {arcane} End",
    "After Everything Burned",
    "The Silence That Speaks",
    "Dream of a {arcane} Tomorrow",
    "Nightmare of {arcane} Yesterday",

    # Títulos poéticos
    "Ash on the Wind",
    "Dust and Memory",
    "The Fading Light",
    "A Candle in {arcane} {chaos}",
    "The Dying Ember",
    "Rain on {arcane} Ruins",
    "Echoes of What Was",
    "Shadow of Tomorrow",
    "The Unwritten Tale",
    "Song Without End",

    # Títulos ominosos
    "The Coming {chaos}",
    "Herald of the {arcane} End",
    "The Final {honorific}",
    "Omega of {place}",
    "The Conclusion",
    "End of All {things}",
    "The Last Chapter",
    "When All {things} Fade",
    "The {arcane} Apocalypse",
    "The Inevitable"
]

USED_NAMES = set()


def _make_fantasy_firstname():
    """Genera nombre base con sufijo fantástico"""
    base = fake.first_name()
    sfx = random.choice(NAME_SUFFIXES)

    roll = random.random()
    if roll < 0.33:
        return base + sfx
    elif roll < 0.66:
        mid = len(base) // 2
        return base[:mid] + sfx + base[mid:]
    else:
        sfx2 = random.choice(NAME_SUFFIXES[:20])
        return base[:3] + sfx + sfx2


def _fill_pattern(pattern):
    """Rellena un patrón con valores aleatorios"""
    replacements = {
        "{arcane}": random.choice(ARCANE_WORDS),
        "{arcane2}": random.choice(ARCANE_WORDS),
        "{place}": random.choice(MYTHIC_PLACES),
        "{chaos}": random.choice(CHAOS_WORDS),
        "{things}": random.choice(PLURAL_THINGS),
        "{honorific}": random.choice(HONORIFICS),
        "{action}": random.choice(ACTION_VERBS),
        "{action_simple}": random.choice(ACTION_SIMPLE),
    }

    result = pattern
    for key, value in replacements.items():
        result = result.replace(key, value)

    return result


def _make_title(race_final, class_final):
    """
    Genera título con sistema de prioridad:
    1. 1.5% - Ultra raro
    2. 25% - Título de raza
    3. 25% - Título de clase
    4. 48.5% - Título genérico
    """
    roll = random.random()

    # Ultra raro (1.5%)
    if roll < 0.015:
        pattern = random.choice(ULTRA_RARE_PATTERNS)
        return _fill_pattern(pattern)

    # Título de raza (25%)
    elif roll < 0.265:
        race_patterns = RACE_PATTERNS.get(race_final, GENERIC_PATTERNS)
        pattern = random.choice(race_patterns)
        return _fill_pattern(pattern)

    # Título de clase (25%)
    elif roll < 0.515:
        class_patterns = CLASS_PATTERNS.get(class_final, GENERIC_PATTERNS)
        pattern = random.choice(class_patterns)
        return _fill_pattern(pattern)

    # Genérico (48.5%)
    else:
        pattern = random.choice(GENERIC_PATTERNS)
        return _fill_pattern(pattern)


def build_epic_name(race_final, class_final):
    """
    Genera nombres únicos estilo Elden Ring con sistema expandido.
    """
    Faker.seed(hash(race_final + class_final + str(random.random())) % 999999)

    first_name = _make_fantasy_firstname()
    title = _make_title(race_final, class_final)
    full = f"{first_name}, {title}"

    # Sistema de colisión mejorado
    attempts = 0
    while full in USED_NAMES and attempts < 15:
        if attempts < 5:
            title = _make_title(race_final, class_final)
        elif attempts < 10:
            first_name = _make_fantasy_firstname()
            title = _make_title(race_final, class_final)
        else:
            extra = random.choice(HONORIFICS)
            title = f"{title} {extra}"

        full = f"{first_name}, {title}"
        attempts += 1

    if full in USED_NAMES:
        full = f"{first_name}, {title} #{len(USED_NAMES) + 1}"

    USED_NAMES.add(full)
    return full


# ---------------------------------------------------
# UTILIDADES
# ---------------------------------------------------
def list_pngs(path):
    if not os.path.exists(path):
        return []
    return [f for f in os.listdir(path) if f.lower().endswith(".png")]


def random_age(min_age, max_age):
    return random.randint(int(min_age), int(max_age))


def get_final_name(mapping_dict, visual_name):
    """
    Convierte 'Human01' -> 'Human', 'SpectralWizard01' -> 'Wizard', etc.
    """
    return mapping_dict.get(visual_name, visual_name)


def compose_image(background_file, race_file, class_file, output_path):
    """
    Orden correcto de capas:
    1) Background
    2) Race
    3) Class
    """
    bg = Image.open(background_file).convert("RGBA")
    race = Image.open(race_file).convert("RGBA")
    clazz = Image.open(class_file).convert("RGBA")

    composed = Image.alpha_composite(bg, race)
    composed = Image.alpha_composite(composed, clazz)
    composed.save(output_path, "PNG")


def get_stats(race_final, class_final):
    row = BASE_STATS[
        (BASE_STATS["race_final"] == race_final)
        & (BASE_STATS["class_final"] == class_final)
    ]
    if row.empty:
        print(f"[WARN] No hay stats para {race_final}-{class_final}. Usando por defecto.")
        return {
            "str": 10,
            "dex": 10,
            "con": 10,
            "int": 10,
            "wis": 10,
            "cha": 10,
            "age_min": 20,
            "age_max": 80,
            "starting_guild": "Order of Dawn",
        }
    r = row.iloc[0]
    return {
        "str": int(r["str"]),
        "dex": int(r["dex"]),
        "con": int(r["con"]),
        "int": int(r["int"]),
        "wis": int(r["wis"]),
        "cha": int(r["cha"]),
        "age_min": int(r["age_min"]),
        "age_max": int(r["age_max"]),
        "starting_guild": str(r["starting_guild"]),
    }


def pick_valid_combo(all_races, all_backgrounds):
    """
    - Todas las razas pueden usar cualquier clase NORMAL.
    - Spectral01/02 sólo usan clases SpectralX.
    Esto se define en compatibility.json.
    """
    races_visual = [f.replace(".png", "") for f in all_races]

    while True:
        race_visual = random.choice(races_visual)

        # grupo en compatibility.json (Normal / Spectral)
        group = next(
            (k for k, v in COMPAT.items() if race_visual in v["races_visual"]),
            "Normal",
        )

        class_visual = random.choice(COMPAT[group]["classes_visual"])
        background_file = random.choice(all_backgrounds)

        race_path = os.path.join(RACES_PATH, race_visual + ".png")
        class_path = os.path.join(CLASSES_PATH, class_visual + ".png")
        bg_path = os.path.join(BACKGROUNDS_PATH, background_file)

        if all(os.path.exists(p) for p in (race_path, class_path, bg_path)):
            return race_visual, class_visual, race_path, class_path, bg_path


# ---------------------------------------------------
# 🔥 GENERADOR PRINCIPAL - ACTUALIZADO PARA ITEMS Y RANGOS
# ---------------------------------------------------
def generate_nfts(total=35000):
    os.makedirs(OUTPUT_IMAGES, exist_ok=True)
    os.makedirs(OUTPUT_METADATA, exist_ok=True)

    all_races = list_pngs(RACES_PATH)
    all_backgrounds = list_pngs(BACKGROUNDS_PATH)

    if not all_races:
        raise RuntimeError("No se encontraron PNG en la carpeta Races/")
    if not all_backgrounds:
        raise RuntimeError("No se encontraron PNG en la carpeta Backgrounds/")

    for counter in range(1, total + 1):
        (
            race_visual,
            class_visual,
            race_path,
            class_path,
            bg_path,
        ) = pick_valid_combo(all_races, all_backgrounds)

        race_final = get_final_name(LOOKUP["raza_visual_to_raza_final"], race_visual)
        class_final = get_final_name(LOOKUP["clase_visual_to_clase_final"], class_visual)

        stats = get_stats(race_final, class_final)
        age_value = random_age(stats["age_min"], stats["age_max"])
        rarity_str = RARITY_BY_RACE.get(race_final, "Common")

        token_id_str = f"{counter:05}"
        timestamp_now = datetime.utcnow().isoformat() + "Z"

        # 1) Background, 2) Race, 3) Class
        out_img = os.path.join(OUTPUT_IMAGES, f"{token_id_str}.png")
        compose_image(bg_path, race_path, class_path, out_img)

        epic_name = build_epic_name(race_final, class_final)

        # 🔥 METADATA COMPLETA CON SOPORTE PARA ITEMS Y RANGOS
        metadata = {
            "name": epic_name,
            "description": (
                f"{race_final} {class_final} of Emberholm. "
                f"Rarity: {rarity_str}. Guild: {stats['starting_guild']}."
            ),
            "image": f"ipfs://{IPFS_CID}/{token_id_str}.png",

            # ========================================
            # FIXED PROFILE - Inmutable en blockchain
            # ========================================
            "fixed_profile": {
                "token_id": token_id_str,
                "race": race_final,
                "class": class_final,
                "rarity": rarity_str,
                "age": age_value,
                "starting_guild": stats["starting_guild"],
                # D&D Stats - base sin modificadores
                "str": stats["str"],
                "dex": stats["dex"],
                "con": stats["con"],
                "int": stats["int"],
                "wis": stats["wis"],
                "cha": stats["cha"],
            },

            # ========================================
            # DYNAMIC STATE - Mutable en juego
            # ========================================
            "dynamic_state": {
                # --- Progresión ---
                "xp_total": 0,
                "xp_level": 1,
                "aura_level": 0,

                # --- Energía ---
                "energy_current": 100,
                "energy_max": 100,
                "last_energy_refresh": timestamp_now,

                # --- Stats dinámicos ---
                "power_current": (stats["str"] + stats["dex"] + stats["con"]) // 3,

                # --- Estado actual ---
                "state": "READY",  # READY / ON_MISSION / FALLEN
                "current_guild": stats["starting_guild"],
                "last_update": timestamp_now,

                # --- Misiones ---
                "current_mission_id": None,
                "mission_start_time": None,
                "last_mission": "None",
                "mission_history": {},  # {mission_id: timestamp}
                "total_missions_completed": 0,
                "total_missions_failed": 0,

                # --- Muerte ---
                "death_count": 0,
                "fallen_time": None,

                # 🔥 --- EMBER POINTS SYSTEM (Phase 1 - Off-chain currency) ---
                "ember_points": 0,  # Virtual currency earned from missions
                "ember_points_claimed": 0,  # Amount converted to $EMBER token (Phase 2)
                "ember_points_lifetime": 0,  # Total earned (never decreases)

                # 🔥 --- RANGOS SYSTEM ---
                "current_rank": "INITIATE",  # INITIATE / ADEPT / VETERAN / MASTER / LEGEND
                "rank_last_updated": timestamp_now,

                # 🔥 --- ITEMS SYSTEM (preparado para futuro) ---
                "equipped_items": {
                    "weapon": None,      # Item ID o null
                    "armor": None,       # Item ID o null
                    "accessory": None,   # Item ID o null
                    "trinket": None      # Item ID o null
                },
                "inventory": [],  # Array de Item IDs ["SWORD_001", "POTION_HP_001"]
                "item_bonuses": {
                    # Bonos acumulados de items equipados
                    "str": 0,
                    "dex": 0,
                    "con": 0,
                    "int": 0,
                    "wis": 0,
                    "cha": 0,
                    "power": 0,
                    "success_rate": 0
                }
            },

            # ========================================
            # ATTRIBUTES - Para OpenSea y marketplaces
            # ========================================
            "attributes": [
                {"trait_type": "ID", "value": token_id_str},
                {"trait_type": "Race", "value": race_final},
                {"trait_type": "Class", "value": class_final},
                {"trait_type": "Rarity", "value": rarity_str},
                {"trait_type": "Guild", "value": stats["starting_guild"]},
                {"trait_type": "Age", "value": age_value},
                {"trait_type": "Rank", "value": "INITIATE"},  # 🔥 Rank visible en OpenSea
            ],
        }

        out_json = os.path.join(OUTPUT_METADATA, f"{token_id_str}.json")
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        print(f"[OK] #{token_id_str}: {epic_name} ({race_final} {class_final}, {rarity_str})")

    print(f"\n✅ Generation complete. Total NFTs generated: {total}")
    print(f"📦 Metadata preparada para sistema de ITEMS y RANGOS")
    print(f"   - Items: equipped_items, inventory, item_bonuses")
    print(f"   - Ranks: current_rank (INITIATE por defecto)")


if __name__ == "__main__":
    generate_nfts(total=35000)
