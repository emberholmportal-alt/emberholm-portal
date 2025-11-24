"""
🔥 EMBER POINTS INTEGRATION - PHASE 1
======================================

Código de ejemplo para integrar EMBER Points en app.py

IMPORTANTE: Copia las funciones relevantes a tu app.py actual.

Author: Emberholm Team
"""

# ========================================
# EMBER POINTS CONFIGURATION
# ========================================

EMBER_POINTS_REWARDS = {
    "EASY": 75,
    "MEDIUM": 200,
    "HARD": 400
}

# Multipliers
PARTY_MISSION_MULTIPLIER = 1.5  # 50% bonus
EVENT_MISSION_MULTIPLIER = 2.0  # 2x bonus


# ========================================
# EMBER POINTS CALCULATION
# ========================================

def calculate_ember_points_reward(mission_id, difficulty, is_party=False, is_event=False):
    """
    Calcula recompensa de EMBER Points basado en misión.

    Args:
        mission_id: ID de la misión
        difficulty: EASY, MEDIUM, HARD
        is_party: True si es party mission
        is_event: True si es evento

    Returns:
        int: Cantidad de EMBER Points
    """
    base_reward = EMBER_POINTS_REWARDS.get(difficulty, 100)

    # Apply multipliers
    if is_party:
        base_reward *= PARTY_MISSION_MULTIPLIER

    if is_event:
        base_reward *= EVENT_MISSION_MULTIPLIER

    return int(base_reward)


# ========================================
# EXAMPLE: UPDATE MISSION COMPLETE
# ========================================

@app.route("/api/mission/complete", methods=["POST"])
def complete_mission():
    """
    Ejemplo de cómo modificar tu función de completar misión
    para incluir EMBER Points.
    """
    data = request.json
    wallet = data.get("wallet")
    token_id_str = data.get("token_id")

    # ... TU CÓDIGO EXISTENTE: validaciones, load hero, etc ...

    # Cargar datos de misión
    mission_id = hero["dynamic_state"]["current_mission_id"]
    mission_data = get_mission_by_id(mission_id)

    # Calcular éxito/fracaso (TU LÓGICA EXISTENTE)
    success = calculate_mission_success(hero, mission_data)

    if success:
        # ========================================
        # RECOMPENSAS EXISTENTES
        # ========================================
        reward_xp = mission_data["reward_xp"]
        reward_aura = mission_data["reward_aura"]

        hero["dynamic_state"]["xp_total"] += reward_xp
        hero["dynamic_state"]["aura_level"] += reward_aura
        hero["dynamic_state"]["total_missions_completed"] += 1

        # ========================================
        # 🔥 NUEVA RECOMPENSA: EMBER POINTS
        # ========================================

        # Detectar si es party mission o evento
        is_party = mission_data.get("party_size") == 5
        is_event = mission_id.startswith("EVENT_")

        # Calcular EMBER Points
        ember_reward = calculate_ember_points_reward(
            mission_id,
            mission_data["difficulty"],
            is_party=is_party,
            is_event=is_event
        )

        # Actualizar hero
        hero["dynamic_state"]["ember_points"] = hero["dynamic_state"].get("ember_points", 0) + ember_reward
        hero["dynamic_state"]["ember_points_lifetime"] = hero["dynamic_state"].get("ember_points_lifetime", 0) + ember_reward

        logger.info(f"✅ Mission complete: Token #{token_id_str}")
        logger.info(f"   Rewards: {reward_xp} XP, {reward_aura} Aura, {ember_reward} EMBER Points")

        # Estado a READY
        hero["dynamic_state"]["state"] = "READY"
        hero["dynamic_state"]["current_mission_id"] = None
        hero["dynamic_state"]["mission_start_time"] = None

        save_nfts_database(db)

        return jsonify({
            "success": True,
            "mission_success": True,
            "rewards": {
                "xp": reward_xp,
                "aura": reward_aura,
                "ember_points": ember_reward  # 🔥 NUEVO
            }
        }), 200

    else:
        # Misión fallida
        hero["dynamic_state"]["total_missions_failed"] += 1
        hero["dynamic_state"]["state"] = "READY"

        save_nfts_database(db)

        return jsonify({
            "success": True,
            "mission_success": False,
            "message": "Mission failed"
        }), 200


# ========================================
# NEW ENDPOINT: GET EMBER POINTS
# ========================================

@app.route("/api/player/<wallet>/ember-points", methods=["GET"])
def get_ember_points(wallet):
    """
    Obtiene el total de EMBER Points de un wallet.

    Returns:
    {
        "wallet": "0x...",
        "ember_points": 5000,
        "ember_points_claimed": 0,
        "ember_points_lifetime": 5000
    }
    """
    try:
        db = load_nfts_database()

        total_points = 0
        total_claimed = 0
        total_lifetime = 0

        # Sumar puntos de todos los NFTs del wallet
        for token_id, nft in db.items():
            # Verificar ownership (puedes usar tu lógica existente)
            if is_owned_by_wallet(nft, wallet):
                ds = nft.get("dynamic_state", {})
                total_points += ds.get("ember_points", 0)
                total_claimed += ds.get("ember_points_claimed", 0)
                total_lifetime += ds.get("ember_points_lifetime", 0)

        return jsonify({
            "wallet": wallet,
            "ember_points": total_points,
            "ember_points_claimed": total_claimed,
            "ember_points_lifetime": total_lifetime
        }), 200

    except Exception as e:
        logger.error(f"❌ Get EMBER Points failed: {e}")
        return jsonify({"error": "Internal server error"}), 500


# ========================================
# NEW ENDPOINT: LEADERBOARD
# ========================================

@app.route("/api/leaderboard/ember-points", methods=["GET"])
def get_ember_leaderboard():
    """
    Top 100 players por EMBER Points lifetime.

    Returns:
    {
        "leaderboard": [
            {
                "rank": 1,
                "wallet": "0x...",
                "name": "Entara, Bearer of...",
                "ember_points": 45000,
                "token_id": "00001"
            },
            ...
        ]
    }
    """
    try:
        db = load_nfts_database()

        # Crear lista de NFTs con points
        nfts_with_points = []

        for token_id, nft in db.items():
            ds = nft.get("dynamic_state", {})
            lifetime_points = ds.get("ember_points_lifetime", 0)

            if lifetime_points > 0:
                nfts_with_points.append({
                    "token_id": token_id,
                    "name": nft.get("name", f"Emissary #{token_id}"),
                    "wallet": "0x...",  # Extraer de ownership
                    "ember_points": lifetime_points
                })

        # Ordenar por points (descendente)
        nfts_with_points.sort(key=lambda x: x["ember_points"], reverse=True)

        # Top 100
        leaderboard = []
        for rank, nft in enumerate(nfts_with_points[:100], start=1):
            leaderboard.append({
                "rank": rank,
                "token_id": nft["token_id"],
                "name": nft["name"],
                "wallet": nft["wallet"],
                "ember_points": nft["ember_points"]
            })

        return jsonify({"leaderboard": leaderboard}), 200

    except Exception as e:
        logger.error(f"❌ Leaderboard failed: {e}")
        return jsonify({"error": "Internal server error"}), 500


# ========================================
# HELPER: Check Mission Type
# ========================================

def is_owned_by_wallet(nft, wallet):
    """
    Verifica si un NFT es owned por un wallet.
    (Implementa tu lógica existente)
    """
    # Ejemplo simplificado
    return True  # Implementar lógica real


def get_mission_by_id(mission_id):
    """
    Obtiene datos de misión por ID.
    (Tu función existente)
    """
    missions_data = load_json("data/missions_config.json", {})
    missions = missions_data.get("missions", [])

    for mission in missions:
        if mission["id"] == mission_id:
            return mission

    # Si no se encuentra en missions, buscar en events
    events_data = load_json("data/events_config.json", {})
    events = events_data.get("events", [])

    for event in events:
        if event["id"] == mission_id:
            return event

    return None


# ========================================
# MIGRATION: Add EMBER Points to Existing NFTs
# ========================================

def migrate_add_ember_points_to_existing_nfts():
    """
    Script de migración para agregar campos de EMBER Points
    a NFTs existentes en la base de datos.

    EJECUTAR UNA SOLA VEZ después de actualizar el código.
    """
    logger.info("🔄 Migrating NFTs to add EMBER Points fields...")

    db = load_nfts_database()
    count = 0

    for token_id, nft in db.items():
        ds = nft.get("dynamic_state", {})

        # Agregar campos si no existen
        if "ember_points" not in ds:
            ds["ember_points"] = 0
            ds["ember_points_claimed"] = 0
            ds["ember_points_lifetime"] = 0
            count += 1

    save_nfts_database(db)

    logger.info(f"✅ Migration complete: {count} NFTs updated")
    return count


# ========================================
# EXAMPLE USAGE
# ========================================

if __name__ == "__main__":
    # Ejecutar migración (una sola vez)
    # migrate_add_ember_points_to_existing_nfts()

    # Luego iniciar app
    # app.run()
    pass
