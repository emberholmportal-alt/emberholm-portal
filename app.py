import json
import os
import time
from datetime import datetime, timedelta
from flask import Flask, jsonify, send_from_directory, request, abort, render_template, render_template

# ---------------------------------
# Config
# ---------------------------------

BASE_DIR     = os.path.dirname(__file__)
DATA_DIR     = os.path.join(BASE_DIR, "data")
PLAYERS_PATH = os.path.join(DATA_DIR, "players.json")
STATS_PATH   = os.path.join(DATA_DIR, "stats.json")
GUILDS_PATH  = os.path.join(DATA_DIR, "guilds.json")

# Carpeta donde guardaste los metadatas base (00001.json, 00002.json, etc.)
METADATA_DIR = os.path.join(DATA_DIR, "metadata")

# Ganancia pasiva cada 24h por héroe
PASSIVE_XP_PER_DAY   = 5
PASSIVE_AURA_PER_DAY = 1

# Cada cuántas horas se refresca la energía natural completa
ENERGY_FULL_REFRESH_HOURS = 48

# Coste de RECOVER: cuánta XP cuesta recuperar 1 punto de energía
XP_COST_PER_ENERGY = 5

# En cuántas horas se resetea el cooldown de misión
ROTATION_HOURS = 72

# Misiones disponibles en la rotación actual
MISSIONS = [
    {
        "id": "001",
        "name": "The Lost Forge",
        "difficulty": "EASY",
        "energy_cost": 10,
        "reward_xp": 25,
        "reward_aura": 2,
        "favored": "Forge Legion / Orc Warrior"
    },
    {
        "id": "002",
        "name": "Circle Interference Node",
        "difficulty": "MEDIUM",
        "energy_cost": 18,
        "reward_xp": 60,
        "reward_aura": 5,
        "favored": "Circle of Mist / Human Wizard"
    },
    {
        "id": "003",
        "name": "Veil Breach Containment",
        "difficulty": "HARD",
        "energy_cost": 25,
        "reward_xp": 120,
        "reward_aura": 11,
        "favored": "Echoes of the Veil / Necromancer"
    }
]

# ---------------------------------
# Helpers de lectura/escritura JSON
# ---------------------------------

def load_json(path, fallback):
    if not os.path.exists(path):
        return fallback
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return fallback

def save_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=4)

# ---------------------------------
# Helpers de tiempo
# ---------------------------------

def now_utc_str():
    return datetime.utcnow().isoformat() + "Z"

def hours_since(ts_str):
    """Devuelve cuántas horas pasaron desde ts_str (ISO) hasta ahora."""
    if not ts_str:
        return 999999
    try:
        clean = ts_str.replace("Z", "")
        t = datetime.fromisoformat(clean)
    except Exception:
        return 999999
    delta = datetime.utcnow() - t
    return delta.total_seconds() / 3600.0

# ---------------------------------
# Progresión pasiva + regeneración de energía
# ---------------------------------

def apply_passive_and_regen(player_obj, stats_obj):
    """
    - Goteo pasivo XP/Aura cada 24h.
    - Regeneración completa de energía cada 48h.
    - Recalcula totales del jugador.
    - Acumula XP/Aura global en stats.json.
    """
    heroes = player_obj.get("heroes", [])
    wallet_tot_xp = 0
    wallet_tot_aura = 0
    wallet_tot_energy_avail = 0

    changed_global_xp = 0
    changed_global_aura = 0

    for hero in heroes:
        ds = hero.setdefault("dynamic_state", {})
        xp_total        = ds.get("xp_total", 0)
        aura_level      = ds.get("aura_level", 0)
        energy_current  = ds.get("energy_current", 100)
        energy_max      = ds.get("energy_max", 100)
        last_update     = ds.get("last_update")
        last_energy_ref = ds.get("last_energy_refresh")

        # Goteo pasivo cada 24h
        if hours_since(last_update) >= 24:
            xp_total   += PASSIVE_XP_PER_DAY
            aura_level += PASSIVE_AURA_PER_DAY

            changed_global_xp   += PASSIVE_XP_PER_DAY
            changed_global_aura += PASSIVE_AURA_PER_DAY

            ds["last_update"] = now_utc_str()

        # Regen natural de energía cada 48h
        if hours_since(last_energy_ref) >= ENERGY_FULL_REFRESH_HOURS:
            energy_current = energy_max
            ds["last_energy_refresh"] = now_utc_str()

        ds["xp_total"]       = xp_total
        ds["aura_level"]     = aura_level
        ds["energy_current"] = energy_current

        wallet_tot_xp            += xp_total
        wallet_tot_aura          += aura_level
        wallet_tot_energy_avail  += energy_current

    stats_obj["total_exp_collected"]  = stats_obj.get("total_exp_collected", 0) + changed_global_xp
    stats_obj["total_aura_collected"] = stats_obj.get("total_aura_collected", 0) + changed_global_aura

    player_obj["totals"] = {
        "heroes_count": len(heroes),
        "xp_total_all": wallet_tot_xp,
        "aura_total_all": wallet_tot_aura,
        "energy_total_available": wallet_tot_energy_avail
    }

    return player_obj, stats_obj

# ---------------------------------
# Ranking y stats de gremios
# ---------------------------------

def update_guild_stats(guild_name, xp_gain, aura_gain, stats_obj):
    """
    - Suma XP/Aura ganadas por ese gremio a stats["guild_ranking"].
    - Refleja actividad en guilds.json (members, avg_xp, avg_aura).
    """
    if not guild_name:
        return stats_obj

    # 1) stats["guild_ranking"]
    guild_ranking = stats_obj.get("guild_ranking", {})
    if guild_name not in guild_ranking:
        guild_ranking[guild_name] = {
            "xp": 0,
            "aura": 0,
            "successes": 0,
            "failures": 0
        }

    guild_ranking[guild_name]["xp"]   += xp_gain
    guild_ranking[guild_name]["aura"] += aura_gain
    stats_obj["guild_ranking"] = guild_ranking

    # 2) guilds.json
    guilds_data = load_json(GUILDS_PATH, [])
    for g in guilds_data:
        if g.get("name","").lower() == guild_name.lower():
            current_members = g.get("members", 0)
            if current_members < 1:
                current_members = 1
            g["members"]  = current_members
            g["avg_xp"]   = round(g.get("avg_xp", 0)   + xp_gain,   2)
            g["avg_aura"] = round(g.get("avg_aura", 0) + aura_gain, 2)
    save_json(GUILDS_PATH, guilds_data)

    return stats_obj

# ---------------------------------
# Flask App
# ---------------------------------

app = Flask(
    __name__,
    static_folder="static",
    static_url_path=""  # sirve /img/... /music/... directo
)

# ---------------------------------
# Rutas estáticas base
# ---------------------------------

@app.route("/")
def serve_index():
    return send_from_directory(app.static_folder, "index.html")
@app.route("/mint")
def serve_mint():
    # mint.html está en la carpeta raíz del proyecto (C:\EmberholmServer)
    return render_template("mint.html")

# ---------------------------------
# API: STATS
# ---------------------------------

@app.route("/api/stats")
def api_stats():
    stats_obj = load_json(STATS_PATH, {})
    guild_rank_list = []
    for g_name, g_data in stats_obj.get("guild_ranking", {}).items():
        guild_rank_list.append({
            "name": g_name,
            "xp_total": g_data.get("xp", 0),
            "aura_total": g_data.get("aura", 0),
            "success_rate": f"{g_data.get('successes',0)}%"
        })

    leaderboard = stats_obj.get("player_leaderboard", [])

    resp = {
        "total_characters":     stats_obj.get("total_characters", 35000),
        "active_guilds":        stats_obj.get("active_guilds", 6),
        "missions_completed":   stats_obj.get("missions_completed", 0),
        "missions_failed":      stats_obj.get("missions_failed", 0),
        "total_exp_collected":  stats_obj.get("total_exp_collected", 0),
        "total_aura_collected": stats_obj.get("total_aura_collected", 0),
        "guild_ranking":        guild_rank_list,
        "player_leaderboard":   leaderboard
    }
    return jsonify(resp)

# ---------------------------------
# API: GUILDS
# ---------------------------------

@app.route("/api/guilds")
def api_guilds():
    guilds_data = load_json(GUILDS_PATH, [])
    return jsonify(guilds_data)

# ---------------------------------
# API: MISSIONS
# ---------------------------------

@app.route("/api/missions")
def api_missions():
    return jsonify(MISSIONS)

# ---------------------------------
# Helper: asegurar jugador
# ---------------------------------

def ensure_player(wallet):
    """
    Devuelve el objeto del jugador para esa wallet.
    Si no existe, lo crea con 2 héroes demo.
    """
    players = load_json(PLAYERS_PATH, {})

    if wallet not in players:
        players[wallet] = {
            "wallet": wallet,
            "heroes": [
                {
                    "token_id": "00001",
                    "name": "Entaal, Bearer of Acordry of the Broken Choose",
                    "race_class": "Gith Druid",
                    "guild": "Circle of Mist",
                    "image_url": "/img/00001.png",
                    "dynamic_state": {
                        "xp_total": 120,
                        "aura_level": 14,
                        "energy_current": 80,
                        "energy_max": 100,
                        "state": "READY",
                        "current_guild": "Circle of Mist",
                        "last_update": now_utc_str(),
                        "last_energy_refresh": now_utc_str(),
                        "mission_history": {},
                        "power_current": 12,
                        "xp_level": 1,
                        "last_mission": "The Lost Forge"
                    }
                },
                {
                    "token_id": "00002",
                    "name": "Brax-Ironjaw",
                    "race_class": "Orc Warrior",
                    "guild": "Forge Legion",
                    "image_url": "/img/00002.png",
                    "dynamic_state": {
                        "xp_total": 210,
                        "aura_level": 7,
                        "energy_current": 45,
                        "energy_max": 100,
                        "state": "READY",
                        "current_guild": "Forge Legion",
                        "last_update": now_utc_str(),
                        "last_energy_refresh": now_utc_str(),
                        "mission_history": {},
                        "power_current": 18,
                        "xp_level": 2,
                        "last_mission": "Veil Breach Containment"
                    }
                }
            ],
            "totals": {
                "heroes_count": 2,
                "xp_total_all": 330,
                "aura_total_all": 21,
                "energy_total_available": 125
            }
        }
        save_json(PLAYERS_PATH, players)

    return players[wallet], players

# ---------------------------------
# API: PLAYER PROFILE
# ---------------------------------

@app.route("/api/player/<wallet>")
def api_player(wallet):
    stats_obj = load_json(STATS_PATH, {
        "total_characters": 35000,
        "active_guilds": 6,
        "missions_completed": 0,
        "missions_failed": 0,
        "total_exp_collected": 0,
        "total_aura_collected": 0,
        "guild_ranking": {},
        "player_leaderboard": []
    })

    player_obj, players_all = ensure_player(wallet)

    # aplicar pasivo/regen antes de mostrar
    player_obj, stats_obj = apply_passive_and_regen(player_obj, stats_obj)

    # guardar cambios
    players_all[wallet] = player_obj
    save_json(PLAYERS_PATH, players_all)
    save_json(STATS_PATH, stats_obj)

    return jsonify(player_obj)

# ---------------------------------
# API: RECOVER ENERGY (gastar XP para recargar energía temprano)
# ---------------------------------

@app.route("/api/player/spend_xp_for_energy", methods=["POST"])
def api_spend_xp():
    data = request.get_json(force=True)
    wallet     = data.get("wallet")
    hero_id    = data.get("hero_id")
    energy_req = int(data.get("energy_request", 0))

    if not wallet or not hero_id or energy_req <= 0:
        abort(400, "invalid input")

    stats_obj = load_json(STATS_PATH, {
        "total_characters": 35000,
        "active_guilds": 6,
        "missions_completed": 0,
        "missions_failed": 0,
        "total_exp_collected": 0,
        "total_aura_collected": 0,
        "guild_ranking": {},
        "player_leaderboard": []
    })
    player_obj, players_all = ensure_player(wallet)

    # refrescamos pasivo/energía
    player_obj, stats_obj = apply_passive_and_regen(player_obj, stats_obj)

    # buscar héroe
    hero = None
    for h in player_obj.get("heroes", []):
        if h.get("token_id") == hero_id:
            hero = h
            break
    if not hero:
        abort(404, "hero not found")

    ds = hero["dynamic_state"]
    xp_total       = ds.get("xp_total", 0)
    aura_level     = ds.get("aura_level", 0)
    energy_current = ds.get("energy_current", 0)
    energy_max     = ds.get("energy_max", 100)

    xp_cost = energy_req * XP_COST_PER_ENERGY
    if xp_total < xp_cost:
        abort(400, "not enough xp")

    # aplicar recuperación
    xp_total       -= xp_cost
    energy_current = min(energy_max, energy_current + energy_req)

    ds["xp_total"]       = xp_total
    ds["aura_level"]     = aura_level
    ds["energy_current"] = energy_current
    ds["last_update"]    = now_utc_str()

    # recalcular totales de wallet (llama pasivo otra vez para coherencia)
    player_obj, stats_obj = apply_passive_and_regen(player_obj, stats_obj)

    players_all[wallet] = player_obj
    save_json(PLAYERS_PATH, players_all)
    save_json(STATS_PATH, stats_obj)

    return jsonify({
        "hero_id": hero_id,
        "energy_current": energy_current,
        "xp_total": xp_total
    })

# ---------------------------------
# API: EXECUTE MISSION (SEND)
# ---------------------------------

@app.route("/api/mission/execute", methods=["POST"])
def api_mission_execute():
    data = request.get_json(force=True)
    wallet     = data.get("wallet")
    hero_id    = data.get("hero_id")
    mission_id = data.get("mission_id")

    if not wallet or not hero_id or not mission_id:
        abort(400, "invalid input")

    stats_obj = load_json(STATS_PATH, {
        "total_characters": 35000,
        "active_guilds": 6,
        "missions_completed": 0,
        "missions_failed": 0,
        "total_exp_collected": 0,
        "total_aura_collected": 0,
        "guild_ranking": {},
        "player_leaderboard": []
    })
    player_obj, players_all = ensure_player(wallet)

    # refrescar antes de operar
    player_obj, stats_obj = apply_passive_and_regen(player_obj, stats_obj)

    # ubicar misión
    mission = None
    for m in MISSIONS:
        if m["id"] == mission_id:
            mission = m
            break
    if mission is None:
        abort(400, "mission not found")

    # ubicar héroe
    hero = None
    for h in player_obj.get("heroes", []):
        if h.get("token_id") == hero_id:
            hero = h
            break
    if hero is None:
        abort(404, "hero not found")

    ds = hero["dynamic_state"]
    xp_total        = ds.get("xp_total", 0)
    aura_level      = ds.get("aura_level", 0)
    energy_current  = ds.get("energy_current", 0)
    energy_max      = ds.get("energy_max", 100)
    mission_hist    = ds.get("mission_history", {})
    hero_guild_name = hero.get("guild") or ds.get("current_guild", "Unknown Guild")

    # check energía
    cost_energy = mission["energy_cost"]
    if energy_current < cost_energy:
        abort(400, "not enough energy")

    # check cooldown (72h)
    last_run_ts = mission_hist.get(mission_id)
    if last_run_ts and hours_since(last_run_ts) < ROTATION_HOURS:
        abort(400, "mission on cooldown")

    # resolver misión (por ahora siempre éxito)
    xp_gain   = mission["reward_xp"]
    aura_gain = mission["reward_aura"]

    xp_total       += xp_gain
    aura_level     += aura_gain
    energy_current -= cost_energy

    ds["xp_total"]        = xp_total
    ds["aura_level"]      = aura_level
    ds["energy_current"]  = max(0, energy_current)
    ds["last_update"]     = now_utc_str()
    ds["last_mission"]    = mission["name"]
    mission_hist[mission_id] = now_utc_str()
    ds["mission_history"]    = mission_hist

    stats_obj["missions_completed"]   = stats_obj.get("missions_completed", 0) + 1
    stats_obj["total_exp_collected"]  = stats_obj.get("total_exp_collected", 0) + xp_gain
    stats_obj["total_aura_collected"] = stats_obj.get("total_aura_collected", 0) + aura_gain

    # ranking gremio
    stats_obj = update_guild_stats(hero_guild_name, xp_gain, aura_gain, stats_obj)

    # recalcular totales, con pasivo otra vez
    player_obj, stats_obj = apply_passive_and_regen(player_obj, stats_obj)

    players_all[wallet] = player_obj
    save_json(PLAYERS_PATH, players_all)
    save_json(STATS_PATH, stats_obj)

    return jsonify({
        "hero_id": hero_id,
        "mission_id": mission_id,
        "mission_name": mission["name"],
        "energy_spent": cost_energy,
        "xp_gained": xp_gain,
        "aura_gained": aura_gain,
        "hero_energy_now": ds["energy_current"],
        "hero_xp_now": ds["xp_total"],
        "hero_aura_now": ds["aura_level"]
    })

# ---------------------------------
# Helpers internos para metadata dinámica (OpenSea-style)
# ---------------------------------

def load_base_metadata_for_token(token_id):
    """
    Carga data/metadata/<token_id>.json (ej 00001.json)
    y normaliza la info fija:
    - name / description / image
    - fixed_profile{}  (race, class, str, etc.)
    - attributes[]     (fallback si falta algo)
    Devuelve todo en un dict plano usable.
    """
    filename = f"{str(token_id).zfill(5)}.json"
    path = os.path.join(METADATA_DIR, filename)
    if not os.path.exists(path):
        return None

    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    # base del resultado
    meta = {
        "token_id":        str(token_id).zfill(5),
        "name":            raw.get("name", f"Emissary #{str(token_id).zfill(5)}"),
        "description":     raw.get("description", "Emissary of Emberholm."),
        "image":           raw.get("image", ""),
        "race":            "Unknown",
        "class":           "Unknown",
        "rarity":          "Unknown",
        "age":             0,
        "starting_guild":  "Unknown",
        "str":             0,
        "dex":             0,
        "con":             0,
        "int":             0,
        "wis":             0,
        "cha":             0,
    }

    # 1) fixed_profile: tu formato real
    fixed = raw.get("fixed_profile", {})
    if isinstance(fixed, dict):
        if "token_id"       in fixed: meta["token_id"]        = fixed["token_id"]
        if "race"           in fixed: meta["race"]            = fixed["race"]
        if "class"          in fixed: meta["class"]           = fixed["class"]
        if "rarity"         in fixed: meta["rarity"]          = fixed["rarity"]
        if "age"            in fixed: meta["age"]             = fixed["age"]
        if "starting_guild" in fixed: meta["starting_guild"]  = fixed["starting_guild"]
        if "str"            in fixed: meta["str"]             = fixed["str"]
        if "dex"            in fixed: meta["dex"]             = fixed["dex"]
        if "con"            in fixed: meta["con"]             = fixed["con"]
        if "int"            in fixed: meta["int"]             = fixed["int"]
        if "wis"            in fixed: meta["wis"]             = fixed["wis"]
        if "cha"            in fixed: meta["cha"]             = fixed["cha"]

    # 2) fallback desde attributes[] si todavía faltan cosas
    attrs = raw.get("attributes", [])
    for trait in attrs:
        ttype = trait.get("trait_type", "").lower()
        val   = trait.get("value")

        if ttype == "id" and meta["token_id"] == str(token_id).zfill(5):
            # ya tenemos token_id, no lo pisamos
            pass
        elif ttype == "race" and meta["race"] == "Unknown":
            meta["race"] = val
        elif ttype == "class" and meta["class"] == "Unknown":
            meta["class"] = val
        elif ttype == "rarity" and meta["rarity"] == "Unknown":
            meta["rarity"] = val
        elif ttype == "guild" and meta["starting_guild"] == "Unknown":
            meta["starting_guild"] = val
        elif ttype == "age" and meta["age"] == 0:
            meta["age"] = val

    return meta


def find_dynamic_state_for_token(token_id):
    """
    Busca en players.json qué wallet contiene este héroe
    y devuelve su dynamic_state (XP / Aura / Energía / última misión).
    Si no está todavía, devolvemos defaults.
    """
    players_all = load_json(PLAYERS_PATH, {})

    for wallet_addr, pobj in players_all.items():
        for hero in pobj.get("heroes", []):
            if hero.get("token_id") == str(token_id).zfill(5):
                ds = hero.get("dynamic_state", {})
                last_mission_name = ds.get("last_mission", "None")
                return {
                    "current_guild":   ds.get("current_guild", hero.get("guild","Unknown")),
                    "xp_total":        ds.get("xp_total", 0),
                    "xp_level":        ds.get("xp_level", 1),
                    "aura_level":      ds.get("aura_level", 0),
                    "energy_current":  ds.get("energy_current", 100),
                    "energy_max":      ds.get("energy_max", 100),
                    "power_current":   ds.get("power_current", 0),
                    "last_update":     ds.get("last_update", now_utc_str()),
                    "last_mission":    last_mission_name,
                }

    return {
        "current_guild":   "Unassigned",
        "xp_total":        0,
        "xp_level":        1,
        "aura_level":      0,
        "energy_current":  100,
        "energy_max":      100,
        "power_current":   0,
        "last_update":     now_utc_str(),
        "last_mission":    "None"
    }

# ---------------------------------
# API: NFT METADATA dinámica tipo DX Terminal / OpenSea
# ---------------------------------

@app.route("/api/metadata/<token_id>")
def api_metadata(token_id):
    """
    Endpoint que OpenSea/marketplaces pueden consultar como tokenURI.
    Combina:
    - metadata fija del héroe (race, STR, etc.)
    - estado dinámico actual (XP, Aura, Energy, Last Mission)
    y lo devuelve TODO dentro de "attributes".
    """
    base_meta = load_base_metadata_for_token(token_id)
    if base_meta is None:
        abort(404, "token metadata not found")

    dyn = find_dynamic_state_for_token(token_id)

    current_guild = dyn.get("current_guild", base_meta.get("starting_guild", "Unknown"))
    energy_str = f"{dyn.get('energy_current',0)} / {dyn.get('energy_max',0)}"

    traits = [
        {"trait_type": "Token ID",      "value": base_meta.get("token_id")},
        {"trait_type": "Race",          "value": base_meta.get("race")},
        {"trait_type": "Class",         "value": base_meta.get("class")},
        {"trait_type": "Rarity",        "value": base_meta.get("rarity")},
        {"trait_type": "Guild",         "value": current_guild},
        {"trait_type": "Age",           "value": base_meta.get("age")},
        {"trait_type": "STR",           "value": base_meta.get("str")},
        {"trait_type": "DEX",           "value": base_meta.get("dex")},
        {"trait_type": "CON",           "value": base_meta.get("con")},
        {"trait_type": "INT",           "value": base_meta.get("int")},
        {"trait_type": "WIS",           "value": base_meta.get("wis")},
        {"trait_type": "CHA",           "value": base_meta.get("cha")},
        {"trait_type": "XP Total",      "value": dyn.get("xp_total", 0)},
        {"trait_type": "Level",         "value": dyn.get("xp_level", 1)},
        {"trait_type": "Aura",          "value": dyn.get("aura_level", 0)},
        {"trait_type": "Energy",        "value": energy_str},
        {"trait_type": "Power",         "value": dyn.get("power_current", 0)},
        {"trait_type": "Last Mission",  "value": dyn.get("last_mission", "None")},
        {"trait_type": "Last Update",   "value": dyn.get("last_update", now_utc_str())}
    ]

    response = {
        "name":        base_meta.get("name", f"Emissary #{str(token_id).zfill(5)}"),
        "description": base_meta.get("description", "Emissary of Emberholm."),
        "image":       base_meta.get("image", ""),
        "attributes":  traits
    }

    return jsonify(response)

# ---------------------------------
# Run local dev server
# ---------------------------------

if __name__ == "__main__":
    app.run(debug=True)
