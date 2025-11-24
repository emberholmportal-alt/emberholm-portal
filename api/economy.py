"""
ECONOMY API ENDPOINTS
===================

Flask blueprint for economy-related API endpoints.
Handles all $EMBER and ASH transactions.
"""

from flask import Blueprint, request, jsonify
import mock_economy
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import os

economy_bp = Blueprint('economy', __name__)

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


# ============================================================================
# GET ENDPOINTS
# ============================================================================

@economy_bp.route('/api/economy/balance/<wallet_address>', methods=['GET'])
def get_balance(wallet_address):
    """
    Get EMBER and ASH balances for a wallet
    Also returns XP and AURA totals
    """
    try:
        stats = mock_economy.get_player_economy_stats(wallet_address)
        return jsonify(stats)

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@economy_bp.route('/api/economy/stats', methods=['GET'])
def get_stats():
    """
    Get global economy statistics
    Used by the Economy tab in STATS/GUILDS
    """
    try:
        stats = mock_economy.get_global_stats()
        return jsonify(stats)

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# POST ENDPOINTS - UTILITIES
# ============================================================================

@economy_bp.route('/api/economy/ember-impulse', methods=['POST'])
def ember_impulse():
    """
    EMBER IMPULSE - Instantly complete a mission
    Cost: 200 EMBER per hour remaining (20% burned)
    """
    data = request.get_json()
    wallet = data.get('wallet')
    hero_id = data.get('hero_id')
    mission_id = data.get('mission_id')

    if not all([wallet, hero_id, mission_id]):
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Get hero data
        cur.execute("""
            SELECT dynamic_state, wallet
            FROM heroes
            WHERE token_id = %s
        """, (hero_id,))

        hero = cur.fetchone()

        if not hero:
            return jsonify({'success': False, 'error': 'Hero not found'}), 404

        if hero['wallet'].lower() != wallet.lower():
            return jsonify({'success': False, 'error': 'Hero does not belong to this wallet'}), 403

        ds = hero['dynamic_state']

        if ds.get('state') != 'ON_MISSION':
            return jsonify({'success': False, 'error': 'Hero is not on a mission'}), 400

        if ds.get('current_mission_id') != mission_id:
            return jsonify({'success': False, 'error': 'Mission ID mismatch'}), 400

        # Calculate time remaining
        mission_start_time = datetime.fromisoformat(ds.get('mission_start_time').replace('Z', ''))
        now = datetime.utcnow()
        elapsed_hours = (now - mission_start_time).total_seconds() / 3600

        # Get mission duration
        cur.execute("SELECT duration_hours, name FROM missions WHERE id = %s", (mission_id,))
        mission = cur.fetchone()

        if not mission:
            # Try events
            cur.execute("SELECT duration_hours, name FROM events WHERE id = %s", (mission_id,))
            mission = cur.fetchone()

        if not mission:
            return jsonify({'success': False, 'error': 'Mission not found'}), 404

        duration_hours = mission['duration_hours']
        mission_name = mission['name']

        hours_remaining = max(0, duration_hours - elapsed_hours)

        if hours_remaining < 0.1:
            return jsonify({'success': False, 'error': 'Mission is already complete'}), 400

        # Calculate cost
        ember_cost = int(hours_remaining * mock_economy.UTILITY_COSTS['ember_impulse'])

        # Spend EMBER
        spend_result = mock_economy.spend_ember(wallet, ember_cost, 'ember_impulse', hero_id)

        if not spend_result['success']:
            return jsonify(spend_result), 400

        # Complete mission immediately
        # Import mission completion logic from app.py
        # For now, we'll manually set mission end time to now
        cur.execute("""
            UPDATE heroes
            SET dynamic_state = jsonb_set(
                dynamic_state,
                '{mission_start_time}',
                to_jsonb(%s::text)
            )
            WHERE token_id = %s
        """, ((now - duration_hours * 3600).isoformat() + 'Z', hero_id))

        conn.commit()

        # Now trigger mission completion
        # This is a simplified version - in production, call the actual mission complete endpoint
        from app import complete_mission_logic  # Import from main app

        mission_result = complete_mission_logic(wallet, hero_id)

        return jsonify({
            'success': True,
            'ember_spent': ember_cost,
            'ember_burned': spend_result['ember_burned'],
            'ash_earned': spend_result['ash_earned'],
            'mission_name': mission_name,
            'outcome': mission_result.get('outcome', 'SUCCESS'),
            'ember_gained': mission_result.get('ember_gained', 0),
            'aura_gained': mission_result.get('aura_gained', 0),
            'hero_ember_now': mock_economy.get_ember_balance(wallet)['total'],
            'hero_aura_now': mission_result.get('hero_aura_now', 0),
            'perfect_alignment': mission_result.get('perfect_alignment', False),
            'hero_died': mission_result.get('outcome') == 'DEATH'
        })

    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

    finally:
        cur.close()
        conn.close()


@economy_bp.route('/api/economy/revive', methods=['POST'])
def revive_hero():
    """
    REVIVE - Bring back a fallen hero
    Cost: 1500 EMBER (20% burned initially, 50% in future)
    """
    data = request.get_json()
    wallet = data.get('wallet')
    hero_id = data.get('hero_id')

    if not all([wallet, hero_id]):
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Get hero data
        cur.execute("""
            SELECT dynamic_state, wallet
            FROM heroes
            WHERE token_id = %s
        """, (hero_id,))

        hero = cur.fetchone()

        if not hero:
            return jsonify({'success': False, 'error': 'Hero not found'}), 404

        if hero['wallet'].lower() != wallet.lower():
            return jsonify({'success': False, 'error': 'Hero does not belong to this wallet'}), 403

        ds = hero['dynamic_state']

        if ds.get('state') != 'FALLEN':
            return jsonify({'success': False, 'error': 'Hero is not fallen'}), 400

        # Spend EMBER
        ember_cost = mock_economy.UTILITY_COSTS['revive']
        spend_result = mock_economy.spend_ember(wallet, ember_cost, 'revive', hero_id)

        if not spend_result['success']:
            return jsonify(spend_result), 400

        # Revive hero (set state to READY, restore energy to 50)
        ds['state'] = 'READY'
        ds['energy_current'] = 50
        ds['current_mission_id'] = None
        ds['mission_start_time'] = None

        cur.execute("""
            UPDATE heroes
            SET dynamic_state = %s
            WHERE token_id = %s
        """, (json.dumps(ds), hero_id))

        conn.commit()

        return jsonify({
            'success': True,
            'ember_spent': ember_cost,
            'ember_burned': spend_result['ember_burned'],
            'ash_earned': spend_result['ash_earned'],
            'hero_id': hero_id,
            'hero_state': 'READY',
            'hero_energy': 50
        })

    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

    finally:
        cur.close()
        conn.close()


@economy_bp.route('/api/economy/recover-energy', methods=['POST'])
def recover_energy():
    """
    RECOVER ENERGY - Restore hero energy using EMBER
    Cost: 500 EMBER for full restore (50% burned initially, 100% in future)
    """
    data = request.get_json()
    wallet = data.get('wallet')
    hero_id = data.get('hero_id')
    energy_amount = data.get('energy_amount', 100)

    if not all([wallet, hero_id]):
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Get hero data
        cur.execute("""
            SELECT dynamic_state, wallet
            FROM heroes
            WHERE token_id = %s
        """, (hero_id,))

        hero = cur.fetchone()

        if not hero:
            return jsonify({'success': False, 'error': 'Hero not found'}), 404

        if hero['wallet'].lower() != wallet.lower():
            return jsonify({'success': False, 'error': 'Hero does not belong to this wallet'}), 403

        ds = hero['dynamic_state']
        current_energy = ds.get('energy_current', 0)
        max_energy = ds.get('energy_max', 100)

        if current_energy >= max_energy:
            return jsonify({'success': False, 'error': 'Hero energy is already full'}), 400

        # Calculate cost (proportional to energy needed)
        needed_energy = min(energy_amount, max_energy - current_energy)
        ember_cost = int(mock_economy.UTILITY_COSTS['recover_energy'] * needed_energy / 100)

        # Spend EMBER
        spend_result = mock_economy.spend_ember(wallet, ember_cost, 'recover_energy', hero_id)

        if not spend_result['success']:
            return jsonify(spend_result), 400

        # Restore energy
        new_energy = min(max_energy, current_energy + needed_energy)
        ds['energy_current'] = new_energy

        cur.execute("""
            UPDATE heroes
            SET dynamic_state = %s
            WHERE token_id = %s
        """, (json.dumps(ds), hero_id))

        conn.commit()

        return jsonify({
            'success': True,
            'ember_spent': ember_cost,
            'ember_burned': spend_result['ember_burned'],
            'ash_earned': spend_result['ash_earned'],
            'hero_id': hero_id,
            'energy_restored': needed_energy,
            'new_energy': new_energy
        })

    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

    finally:
        cur.close()
        conn.close()


@economy_bp.route('/api/economy/claim-pending', methods=['POST'])
def claim_pending():
    """
    CLAIM PENDING EMBER - Move pending rewards to wallet
    """
    data = request.get_json()
    wallet = data.get('wallet')
    amount = data.get('amount')  # Optional, None = claim all

    if not wallet:
        return jsonify({'success': False, 'error': 'Missing wallet address'}), 400

    try:
        result = mock_economy.claim_pending_ember(wallet, amount)
        return jsonify(result)

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
