"""
🔥 GASLESS STAKING EXAMPLE
==========================

Ejemplo de cómo modificar los endpoints de misiones en app.py
para implementar staking gasless (backend paga el gas).

IMPORTANTE: Este es un EJEMPLO. Copia las funciones relevantes a tu app.py.

Author: Emberholm Team
"""

from flask import Flask, request, jsonify
import time
from web3_integration import get_web3_manager

app = Flask(__name__)

# Obtener Web3Manager (singleton)
web3_mgr = get_web3_manager()


# ========================================
# EJEMPLO 1: START MISSION (Con Staking)
# ========================================

@app.route("/api/mission/start", methods=["POST"])
def start_mission():
    """
    Inicia una misión con staking gasless.

    Request body:
    {
        "wallet": "0x...",
        "token_id": "00123",
        "mission_id": "001",
        "message": "Start mission 001 with token 00123 at 1732454400000",
        "signature": "0x..."
    }
    """
    try:
        data = request.json
        wallet = data.get("wallet")
        token_id_str = data.get("token_id")
        mission_id = data.get("mission_id")
        message = data.get("message")
        signature = data.get("signature")

        # Validaciones básicas
        if not all([wallet, token_id_str, mission_id, message, signature]):
            return jsonify({"error": "Missing required fields"}), 400

        token_id = int(token_id_str)

        # 🔥 PASO 1: Verificar firma off-chain (GRATIS para usuario)
        is_valid_signature = web3_mgr.verify_signature(message, signature, wallet)
        if not is_valid_signature:
            return jsonify({"error": "Invalid signature"}), 401

        # 🔥 PASO 2: Verificar timestamp (prevenir replay attacks)
        try:
            timestamp = int(message.split(" at ")[-1])
            current_time = int(time.time() * 1000)
            time_diff = abs(current_time - timestamp)

            if time_diff > 300000:  # 5 minutos
                return jsonify({"error": "Signature expired"}), 401
        except:
            return jsonify({"error": "Invalid message format"}), 400

        # 🔥 PASO 3: Verificar ownership on-chain
        is_owner = web3_mgr.verify_nft_ownership(token_id, wallet)
        if not is_owner:
            return jsonify({"error": "You don't own this NFT"}), 403

        # 🔥 PASO 4: Cargar datos del héroe desde backend
        # (tu código existente)
        db = load_nfts_database()
        hero = db.get(token_id_str)
        if not hero:
            return jsonify({"error": "Hero not found"}), 404

        # Validar estado
        if hero["dynamic_state"]["state"] != "READY":
            return jsonify({"error": f"Hero is {hero['dynamic_state']['state']}"}), 400

        # Validar energía
        if hero["dynamic_state"]["energy_current"] < 10:
            return jsonify({"error": "Not enough energy"}), 400

        # ... más validaciones de tu lógica actual ...

        # 🔥 PASO 5: STAKEAR ON-CHAIN (Backend paga gas ~$0.01)
        success, tx_hash = web3_mgr.stake_token(token_id)

        if not success:
            return jsonify({
                "error": "Failed to stake NFT on-chain. Mission cannot start."
            }), 500

        # 🔥 PASO 6: Actualizar backend (tu lógica existente)
        hero["dynamic_state"]["state"] = "ON_MISSION"
        hero["dynamic_state"]["current_mission_id"] = mission_id
        hero["dynamic_state"]["mission_start_time"] = now_utc_str()
        hero["dynamic_state"]["energy_current"] -= 10

        save_nfts_database(db)

        # Log para analytics
        logger.info(
            f"✅ Mission started: Token #{token_id}, "
            f"Mission {mission_id}, TX: {tx_hash}"
        )

        return jsonify({
            "success": True,
            "message": "Mission started! (No gas paid by you)",
            "tx_hash": tx_hash,
            "mission_id": mission_id,
            "duration_hours": 3  # ejemplo
        }), 200

    except Exception as e:
        logger.error(f"❌ Start mission failed: {e}")
        return jsonify({"error": "Internal server error"}), 500


# ==========================================
# EJEMPLO 2: COMPLETE MISSION (Con Unstake)
# ==========================================

@app.route("/api/mission/complete", methods=["POST"])
def complete_mission():
    """
    Completa una misión con unstaking gasless.

    Request body:
    {
        "wallet": "0x...",
        "token_id": "00123",
        "message": "Complete mission for token 00123 at 1732454400000",
        "signature": "0x..."
    }
    """
    try:
        data = request.json
        wallet = data.get("wallet")
        token_id_str = data.get("token_id")
        message = data.get("message")
        signature = data.get("signature")

        # Validaciones
        if not all([wallet, token_id_str, message, signature]):
            return jsonify({"error": "Missing required fields"}), 400

        token_id = int(token_id_str)

        # 🔥 PASO 1: Verificar firma
        is_valid_signature = web3_mgr.verify_signature(message, signature, wallet)
        if not is_valid_signature:
            return jsonify({"error": "Invalid signature"}), 401

        # 🔥 PASO 2: Verificar timestamp
        try:
            timestamp = int(message.split(" at ")[-1])
            current_time = int(time.time() * 1000)
            if abs(current_time - timestamp) > 300000:
                return jsonify({"error": "Signature expired"}), 401
        except:
            return jsonify({"error": "Invalid message format"}), 400

        # 🔥 PASO 3: Verificar ownership
        is_owner = web3_mgr.verify_nft_ownership(token_id, wallet)
        if not is_owner:
            return jsonify({"error": "You don't own this NFT"}), 403

        # 🔥 PASO 4: Cargar héroe
        db = load_nfts_database()
        hero = db.get(token_id_str)
        if not hero:
            return jsonify({"error": "Hero not found"}), 404

        # Validar que esté en misión
        if hero["dynamic_state"]["state"] != "ON_MISSION":
            return jsonify({"error": "Not on mission"}), 400

        # 🔥 PASO 5: Calcular recompensas (tu lógica existente)
        mission_id = hero["dynamic_state"]["current_mission_id"]
        start_time = hero["dynamic_state"]["mission_start_time"]

        # ... calcular elapsed time, success, rewards, etc ...

        reward_xp = 100  # ejemplo
        reward_aura = 10  # ejemplo
        success = True  # ejemplo

        # 🔥 PASO 6: Actualizar backend PRIMERO
        hero["dynamic_state"]["state"] = "READY"
        hero["dynamic_state"]["current_mission_id"] = None
        hero["dynamic_state"]["mission_start_time"] = None

        if success:
            hero["dynamic_state"]["xp_total"] += reward_xp
            hero["dynamic_state"]["aura_level"] += reward_aura
            hero["dynamic_state"]["total_missions_completed"] += 1
        else:
            hero["dynamic_state"]["total_missions_failed"] += 1

        save_nfts_database(db)

        # 🔥 PASO 7: UNSTAKEAR ON-CHAIN (Backend paga gas ~$0.007)
        # IMPORTANTE: Hacemos esto AL FINAL, después de dar recompensas
        # Si falla, el héroe ya tiene sus recompensas (prioritario)
        success_unstake, tx_hash = web3_mgr.unstake_token(token_id)

        if not success_unstake:
            # Log warning pero NO falla el endpoint
            # El héroe ya recibió sus recompensas
            logger.warning(
                f"⚠️ Failed to unstake token #{token_id} but rewards granted"
            )

        # Log para analytics
        logger.info(
            f"✅ Mission completed: Token #{token_id}, "
            f"Rewards: {reward_xp} XP, {reward_aura} Aura, "
            f"Unstake TX: {tx_hash}"
        )

        return jsonify({
            "success": True,
            "message": "Mission completed! (No gas paid by you)",
            "rewards": {
                "xp": reward_xp,
                "aura": reward_aura
            },
            "tx_hash": tx_hash,
            "mission_success": success
        }), 200

    except Exception as e:
        logger.error(f"❌ Complete mission failed: {e}")
        return jsonify({"error": "Internal server error"}), 500


# ======================================
# EJEMPLO 3: CHECK STAKE STATUS
# ======================================

@app.route("/api/nft/<token_id>/stake-status", methods=["GET"])
def check_stake_status(token_id):
    """
    Verifica el estado de staking de un NFT on-chain.

    Útil para debugging o mostrar en UI.
    """
    try:
        token_id_int = int(token_id)

        # Obtener info on-chain
        info = web3_mgr.get_token_info(token_id_int)

        if not info:
            return jsonify({"error": "Failed to get token info"}), 500

        return jsonify({
            "token_id": info['tokenId'],
            "owner": info['owner'],
            "is_staked": info['isStaked'],
            "staked_since": info['stakedSince'],
            "staked_duration_seconds": (
                int(time.time()) - info['stakedSince']
                if info['isStaked'] else 0
            )
        }), 200

    except Exception as e:
        logger.error(f"❌ Check stake status failed: {e}")
        return jsonify({"error": "Internal server error"}), 500


# ======================================
# HELPERS (tus funciones existentes)
# ======================================

def load_nfts_database():
    """Cargar tu base de datos de NFTs (ejemplo)"""
    pass

def save_nfts_database(db):
    """Guardar tu base de datos de NFTs (ejemplo)"""
    pass

def now_utc_str():
    """Timestamp UTC en formato ISO (ejemplo)"""
    from datetime import datetime
    return datetime.utcnow().isoformat() + "Z"


if __name__ == "__main__":
    app.run(debug=True)
