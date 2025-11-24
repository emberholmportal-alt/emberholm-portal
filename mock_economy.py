"""
MOCK ECONOMY SYSTEM FOR EMBERHOLM PORTAL
=========================================

This module simulates the $EMBER token economy BEFORE blockchain deployment.
All balances and transactions are stored in PostgreSQL.

When the $EMBER contract is deployed, this system will be migrated to use
real on-chain balances instead of mock data.

FEATURES:
- $EMBER balance tracking (wallet + pending rewards)
- ASH prestige currency system
- Burn tracking and statistics
- Utility spending (Ember Impulse, Revive, Energy Recovery)
- Global economy metrics
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import os

# Database connection from environment
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


# ============================================================================
# TOKENOMICS CONSTANTS
# ============================================================================

TOTAL_SUPPLY = 1_000_000_000  # 1 billion EMBER
ASH_CONVERSION_RATE = 100  # 100 EMBER burned = 1 ASH

# Mission rewards (based on difficulty)
MISSION_REWARDS = {
    "EASY": 50,
    "MEDIUM": 150,
    "HARD": 400
}

# Utility costs
UTILITY_COSTS = {
    "ember_impulse": 200,  # per hour
    "revive": 1500,
    "recover_energy": 500
}

# Burn rates (percentage of cost that gets burned)
BURN_RATES = {
    "ember_impulse": 20,  # 20% burned
    "revive": 20,  # 20% burned initially (50% final)
    "recover_energy": 50  # 50% burned initially (100% final)
}


# ============================================================================
# BALANCE FUNCTIONS
# ============================================================================

def get_ember_balance(wallet_address):
    """
    Get EMBER balance for a wallet

    Returns:
        {
            'wallet': amount in wallet (can be withdrawn),
            'pending': amount in pending rewards (not yet minted),
            'total': wallet + pending
        }
    """
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Get wallet balance
        cur.execute("""
            SELECT balance_wallet, balance_pending
            FROM ember_balances
            WHERE wallet_address = %s
        """, (wallet_address.lower(),))

        result = cur.fetchone()

        if result:
            return {
                'wallet': float(result['balance_wallet']),
                'pending': float(result['balance_pending']),
                'total': float(result['balance_wallet']) + float(result['balance_pending'])
            }
        else:
            # No balance record, create one
            cur.execute("""
                INSERT INTO ember_balances (wallet_address, balance_wallet, balance_pending)
                VALUES (%s, 0, 0)
            """, (wallet_address.lower(),))
            conn.commit()

            return {'wallet': 0, 'pending': 0, 'total': 0}

    finally:
        cur.close()
        conn.close()


def get_ash_balance(wallet_address):
    """
    Get ASH balance for a wallet

    Returns:
        {
            'balance': current ASH balance,
            'lifetime_earned': total ASH ever earned,
            'season_active': whether an ASH season is currently active
        }
    """
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Get ASH balance
        cur.execute("""
            SELECT ash_balance, ash_lifetime_earned
            FROM ash_balances
            WHERE wallet_address = %s
        """, (wallet_address.lower(),))

        result = cur.fetchone()

        # Check if season is active
        cur.execute("""
            SELECT is_active
            FROM ash_seasons
            WHERE is_active = TRUE
            ORDER BY start_date DESC
            LIMIT 1
        """)

        season = cur.fetchone()
        season_active = bool(season) if season else False

        if result:
            return {
                'balance': float(result['ash_balance']),
                'lifetime_earned': float(result['ash_lifetime_earned']),
                'season_active': season_active
            }
        else:
            # No ASH record, create one
            cur.execute("""
                INSERT INTO ash_balances (wallet_address, ash_balance, ash_lifetime_earned)
                VALUES (%s, 0, 0)
            """, (wallet_address.lower(),))
            conn.commit()

            return {'balance': 0, 'lifetime_earned': 0, 'season_active': season_active}

    finally:
        cur.close()
        conn.close()


# ============================================================================
# TRANSACTION FUNCTIONS
# ============================================================================

def spend_ember(wallet_address, amount, action, token_id=None):
    """
    Spend EMBER from a wallet

    Args:
        wallet_address: User's wallet
        amount: Amount to spend
        action: What the EMBER is being spent on (ember_impulse, revive, etc)
        token_id: Optional NFT token ID for tracking

    Returns:
        {
            'success': bool,
            'ember_spent': amount spent,
            'ember_burned': amount burned,
            'new_balance': remaining balance,
            'ash_earned': ASH earned from burn (if season active)
        }
    """
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Get current balance
        balance = get_ember_balance(wallet_address)

        if balance['total'] < amount:
            return {
                'success': False,
                'error': f'Insufficient EMBER balance. Need {amount}, have {balance["total"]}'
            }

        # Calculate burn amount
        burn_rate = BURN_RATES.get(action, 0)
        ember_burned = int(amount * burn_rate / 100)

        # Deduct from wallet first, then pending if needed
        wallet_deduction = min(amount, balance['wallet'])
        pending_deduction = amount - wallet_deduction

        new_wallet = balance['wallet'] - wallet_deduction
        new_pending = balance['pending'] - pending_deduction

        # Update balance
        cur.execute("""
            UPDATE ember_balances
            SET balance_wallet = %s,
                balance_pending = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE wallet_address = %s
        """, (new_wallet, new_pending, wallet_address.lower()))

        # Record burn
        cur.execute("""
            INSERT INTO burn_history
                (wallet_address, token_id, amount_burned, burn_type, created_at)
            VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
        """, (wallet_address.lower(), token_id, ember_burned, action))

        # Update global stats
        cur.execute("""
            UPDATE global_economy_stats
            SET total_ember_burned = total_ember_burned + %s,
                utility_ember_spent = utility_ember_spent + %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = 1
        """, (ember_burned, amount))

        # Calculate ASH earned (if season active)
        ash_earned = 0
        if ember_burned > 0:
            ash_balance = get_ash_balance(wallet_address)
            if ash_balance['season_active']:
                ash_earned = ember_burned / ASH_CONVERSION_RATE

                cur.execute("""
                    UPDATE ash_balances
                    SET ash_balance = ash_balance + %s,
                        ash_lifetime_earned = ash_lifetime_earned + %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE wallet_address = %s
                """, (ash_earned, ash_earned, wallet_address.lower()))

        conn.commit()

        return {
            'success': True,
            'ember_spent': amount,
            'ember_burned': ember_burned,
            'new_balance': new_wallet + new_pending,
            'ash_earned': ash_earned
        }

    except Exception as e:
        conn.rollback()
        return {'success': False, 'error': str(e)}

    finally:
        cur.close()
        conn.close()


def reward_ember(wallet_address, amount, source, token_id=None):
    """
    Reward EMBER to a wallet (goes to pending first)

    Args:
        wallet_address: User's wallet
        amount: Amount to reward
        source: Where the EMBER came from (mission_complete, etc)
        token_id: Optional NFT token ID for tracking

    Returns:
        {
            'success': bool,
            'ember_rewarded': amount,
            'new_balance': new total balance
        }
    """
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Add to pending balance
        cur.execute("""
            INSERT INTO ember_balances (wallet_address, balance_wallet, balance_pending)
            VALUES (%s, 0, %s)
            ON CONFLICT (wallet_address)
            DO UPDATE SET
                balance_pending = ember_balances.balance_pending + %s,
                updated_at = CURRENT_TIMESTAMP
        """, (wallet_address.lower(), amount, amount))

        # Update global stats
        cur.execute("""
            UPDATE global_economy_stats
            SET total_ember_minted = total_ember_minted + %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = 1
        """, (amount,))

        conn.commit()

        # Get new balance
        balance = get_ember_balance(wallet_address)

        return {
            'success': True,
            'ember_rewarded': amount,
            'new_balance': balance['total']
        }

    except Exception as e:
        conn.rollback()
        return {'success': False, 'error': str(e)}

    finally:
        cur.close()
        conn.close()


def claim_pending_ember(wallet_address, amount=None):
    """
    Move EMBER from pending to wallet (simulates minting)

    Args:
        wallet_address: User's wallet
        amount: Amount to claim (None = all pending)

    Returns:
        {
            'success': bool,
            'ember_claimed': amount claimed,
            'new_wallet_balance': new wallet balance
        }
    """
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        balance = get_ember_balance(wallet_address)

        # Determine how much to claim
        claim_amount = min(amount or balance['pending'], balance['pending'])

        if claim_amount <= 0:
            return {'success': False, 'error': 'No pending EMBER to claim'}

        # Move from pending to wallet
        cur.execute("""
            UPDATE ember_balances
            SET balance_wallet = balance_wallet + %s,
                balance_pending = balance_pending - %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE wallet_address = %s
        """, (claim_amount, claim_amount, wallet_address.lower()))

        conn.commit()

        new_balance = get_ember_balance(wallet_address)

        return {
            'success': True,
            'ember_claimed': claim_amount,
            'new_wallet_balance': new_balance['wallet']
        }

    except Exception as e:
        conn.rollback()
        return {'success': False, 'error': str(e)}

    finally:
        cur.close()
        conn.close()


# ============================================================================
# STATISTICS FUNCTIONS
# ============================================================================

def get_global_stats():
    """
    Get global economy statistics

    Returns complete economy metrics for the Economy tab
    """
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Get global stats
        cur.execute("SELECT * FROM global_economy_stats WHERE id = 1")
        stats = cur.fetchone()

        if not stats:
            # Initialize global stats
            cur.execute("""
                INSERT INTO global_economy_stats
                    (id, total_ember_minted, total_ember_burned, utility_ember_spent)
                VALUES (1, 0, 0, 0)
            """)
            conn.commit()

            cur.execute("SELECT * FROM global_economy_stats WHERE id = 1")
            stats = cur.fetchone()

        # Count unique holders
        cur.execute("SELECT COUNT(DISTINCT wallet_address) FROM ember_balances WHERE balance_wallet > 0 OR balance_pending > 0")
        unique_holders = cur.fetchone()['count']

        # Count NFT owners with EMBER
        cur.execute("""
            SELECT COUNT(DISTINCT eb.wallet_address)
            FROM ember_balances eb
            INNER JOIN players p ON eb.wallet_address = p.wallet
            WHERE (eb.balance_wallet > 0 OR eb.balance_pending > 0)
        """)
        nft_owners = cur.fetchone()['count']

        # Count utility usage
        cur.execute("""
            SELECT
                COUNT(*) FILTER (WHERE burn_type = 'ember_impulse') as impulse_count,
                COUNT(*) FILTER (WHERE burn_type = 'revive') as revive_count,
                COUNT(*) FILTER (WHERE burn_type = 'recover_energy') as energy_count
            FROM burn_history
        """)
        utility_stats = cur.fetchone()

        # ASH stats
        cur.execute("""
            SELECT
                COALESCE(SUM(ash_balance), 0) as total_ash,
                COALESCE(SUM(ash_lifetime_earned), 0) as total_ash_lifetime
            FROM ash_balances
        """)
        ash_stats = cur.fetchone()

        # Check if ASH season is active
        cur.execute("""
            SELECT is_active, season_name, end_date
            FROM ash_seasons
            WHERE is_active = TRUE
            ORDER BY start_date DESC
            LIMIT 1
        """)
        ash_season = cur.fetchone()

        # Calculate metrics
        total_minted = float(stats['total_ember_minted'])
        total_burned = float(stats['total_ember_burned'])
        utility_spent = float(stats['utility_ember_spent'])

        circulating = total_minted - total_burned
        burn_rate = (total_burned / total_minted * 100) if total_minted > 0 else 0
        mint_progress = (total_minted / TOTAL_SUPPLY * 100)

        return {
            'success': True,
            'ember': {
                'total_supply': TOTAL_SUPPLY,
                'total_minted': int(total_minted),
                'total_burned': int(total_burned),
                'circulating': int(circulating),
                'locked_in_vesting': 0,  # TODO: implement vesting
                'burn_rate': burn_rate,
                'price_usd': 0.0001  # Mock price for now
            },
            'ash': {
                'total_supply': float(ash_stats['total_ash']),
                'burned_for_rewards': 0,  # TODO: track ASH spending
                'conversion_rate': f'100 EMBER = 1 ASH',
                'season_active': bool(ash_season) if ash_season else False,
                'season_end_date': ash_season['end_date'].isoformat() if ash_season else None
            },
            'utilities': {
                'ember_impulse_count': utility_stats['impulse_count'] or 0,
                'revive_count': utility_stats['revive_count'] or 0,
                'energy_recover_count': utility_stats['energy_count'] or 0,
                'total_ember_spent': int(utility_spent),
                'total_ember_burned': int(total_burned)
            },
            'distribution': {
                'unique_holders': unique_holders,
                'nft_owners_with_ember': nft_owners,
                'total_minted': int(total_minted),
                'mint_progress': mint_progress
            }
        }

    finally:
        cur.close()
        conn.close()


def get_player_economy_stats(wallet_address):
    """
    Get economy stats for a specific player

    Returns EMBER, ASH, XP, and AURA totals for the profile display
    """
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Get EMBER balance
        ember = get_ember_balance(wallet_address)

        # Get ASH balance
        ash = get_ash_balance(wallet_address)

        # Get XP and AURA totals from heroes
        cur.execute("""
            SELECT
                COALESCE(SUM((dynamic_state->>'xp_total')::int), 0) as total_xp,
                COALESCE(SUM((dynamic_state->>'aura_level')::int), 0) as total_aura
            FROM heroes
            WHERE wallet = %s
        """, (wallet_address.lower(),))

        player_stats = cur.fetchone()

        return {
            'success': True,
            'ember': ember,
            'ash': ash,
            'stats': {
                'total_xp': player_stats['total_xp'] or 0,
                'total_aura': player_stats['total_aura'] or 0
            }
        }

    finally:
        cur.close()
        conn.close()
