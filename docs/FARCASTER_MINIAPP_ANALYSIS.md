# Emberholm Portal - Farcaster Mini App Analysis Document

**Version:** 1.0
**Date:** 2026-01-27
**Status:** Complete Analysis

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Current System Analysis](#2-current-system-analysis)
   - 2.1 Database Schema
   - 2.2 Smart Contracts
   - 2.3 Backend API
   - 2.4 Frontend Architecture
3. [Mission System Deep Dive](#3-mission-system-deep-dive)
4. [Progression System](#4-progression-system)
5. [Micro-Missions Design](#5-micro-missions-design)
6. [$SPARK Tokenomics](#6-spark-tokenomics)
7. [Technical Architecture](#7-technical-architecture)
8. [UI/UX Design](#8-uiux-design)
9. [Farcaster Integration](#9-farcaster-integration)
10. [Implementation Plan](#10-implementation-plan)
11. [Launch Checklist](#11-launch-checklist)

---

## 1. Executive Summary

### Project Overview

Emberholm Portal is a medieval fantasy RPG built on Base blockchain featuring:
- **35,000 unique NFTs** called "Emissaries"
- **7 verified smart contracts** on Base Mainnet
- **Dual-token economy**: $EMBER (utility) and $ASH (governance)
- **Mission system** with permadeath mechanics
- **6 Guilds** with unique identities and bonuses

### Mini App Objective

Create a **simplified gateway** to Emberholm Portal through Farcaster (Warpcast/Base App) that allows users to:
1. Mint their first Emissary (0.0011 ETH)
2. Complete micro-missions (1-5 minutes)
3. Earn $SPARK tokens (new mini-app currency)
4. Progress their Emissaries in the main game

### Key Findings

| Aspect | Current State | Mini App Requirement |
|--------|---------------|---------------------|
| Missions | 3-12 hours, permadeath risk | 1-5 minutes, no death |
| Backend | Flask API, 53 endpoints | Reuse 80%, add 6 new |
| Database | PostgreSQL, 10+ tables | Add 2 tables for micro-missions |
| Auth | Wallet-based (no signature) | Farcaster Frame handles auth |
| Frontend | Retro terminal CRT theme | Mobile-first, same color palette |

---

## 2. Current System Analysis

### 2.1 Database Schema

#### Core Tables

| Table | Purpose | Mini App Relevance |
|-------|---------|-------------------|
| `nfts` | 35,000 emissaries with dynamic_state (JSONB) | **CRITICAL** - Read/write emissary state |
| `active_missions` | Track ongoing missions | **ADAPT** - Shorter duration tracking |
| `user_balances` | $EMBER, $ASH, gambit rolls | **EXTEND** - Add $SPARK balance |
| `items` | Equipment inventory | **PARTIAL** - Read-only for bonuses |
| `pending_claims` | Item/rune drop claims | **REUSE** - Same claim flow |
| `players` | Player session cache | **REUSE** - Same structure |
| `global_stats` | Realm-wide statistics | **REUSE** - Add micro-mission counters |
| `revive_log` | Death/revival tracking | **NOT NEEDED** - No death in micro-missions |
| `achievements` | Achievement tracking | **EXTEND** - Mini-app achievements |
| `events` | Event system | **PARTIAL** - Time-limited micro-missions |
| `lands` | Land binding system | **NOT NEEDED** - Simplify for mini-app |

#### NFT Dynamic State Structure (JSONB)

```json
{
  "state": "READY|ON_MISSION|FALLEN",
  "xp_total": 500,
  "aura_level": 50,
  "energy_current": 75,
  "energy_max": 100,
  "missions_completed": 5,
  "missions_failed": 1,
  "death_count": 0,
  "current_guild": "Circle of Mist",
  "mission_history": {},
  "ember_roll_buff": {},
  "last_update": "2024-01-27T12:00:00Z"
}
```

#### New Tables Required

```sql
-- Table: micro_missions (active micro-mission tracking)
CREATE TABLE micro_missions (
    id SERIAL PRIMARY KEY,
    wallet VARCHAR(42) NOT NULL,
    emissary_id VARCHAR(10) NOT NULL,
    mission_type VARCHAR(50) NOT NULL,
    start_time TIMESTAMP NOT NULL,
    duration_seconds INTEGER NOT NULL,
    rewards_claimed BOOLEAN DEFAULT FALSE,
    rewards JSONB,
    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT fk_micro_mission_nft FOREIGN KEY (emissary_id)
        REFERENCES nfts(token_id) ON DELETE CASCADE
);

CREATE INDEX idx_micro_missions_wallet ON micro_missions(wallet);
CREATE INDEX idx_micro_missions_emissary ON micro_missions(emissary_id);

-- Table: spark_balances (mini-app token tracking)
CREATE TABLE spark_balances (
    wallet VARCHAR(42) PRIMARY KEY,
    spark_balance INTEGER DEFAULT 0,
    total_earned INTEGER DEFAULT 0,
    daily_streak INTEGER DEFAULT 0,
    last_mission_date DATE,
    missions_today INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    last_update TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_spark_wallet ON spark_balances(wallet);

-- Extend user_balances table
ALTER TABLE user_balances ADD COLUMN IF NOT EXISTS spark_balance INTEGER DEFAULT 0;
ALTER TABLE user_balances ADD COLUMN IF NOT EXISTS micro_missions_completed INTEGER DEFAULT 0;
```

---

### 2.2 Smart Contracts

#### Deployed Contracts (Base Mainnet)

| Contract | Address | Mini App Usage |
|----------|---------|----------------|
| EmberholmPortal (NFT) | `0x7AB2cf80FbfB8c89868b3dFa053729ecC86E39b3` | **MINT** - 0.0011 ETH per emissary |
| EmberToken ($EMBER) | `0xbA7723fBfb44C7712C0B78108ad873DcFd5Dd73b` | **READ** - Balance display |
| AshToken ($ASH) | `0xD4eef3eadb1Cf1B2905AA4Cd1022b8cCCC739DAb` | **READ** - Balance display |
| EmberItems | `0xCE71702CE99Bc927216e64d57e4BD19254Ac28bA` | **OPTIONAL** - Item claims |
| EmberRunes | `0xDa2D1085053c3700645a13498293D17c1cc3f595` | **OPTIONAL** - Rune claims |

#### EmberholmPortal Contract Functions

```solidity
// Relevant for Mini App
function mint(uint256 quantity) external payable;     // Mint emissaries (max 10)
function mintPrice() view returns (uint256);          // 0.0011 ETH
function totalMinted() view returns (uint256);        // Current supply
function maxSupply() pure returns (uint256);          // 35,000
function tokensOfOwner(address) view returns (uint256[]);  // User's NFTs
function balanceOf(address) view returns (uint256);   // NFT count
function ownerOf(uint256) view returns (address);     // Token owner

// Events to monitor
event Transfer(address indexed from, address indexed to, uint256 indexed tokenId);
```

#### Key Answers

| Question | Answer |
|----------|--------|
| Batch mint function? | Yes, `mint(quantity)` supports 1-10 NFTs per transaction |
| How to claim $EMBER? | Backend gasless claim via `/api/ember/claim` endpoint |
| Item registration on-chain? | Hybrid - Backend generates claim signature, user mints via contract |
| Staking/lockup contract? | Yes, built into EmberholmPortal (prevents transfer during missions) |

#### New Contract Considerations for $SPARK

**Option A: Clanker Launch (Recommended)**
- Fast deployment via Clanker platform
- Automatic liquidity
- Community-driven
- No contract development needed

**Option B: Custom ERC20**
```solidity
// SparkToken.sol - Simple ERC20 with controlled minting
contract SparkToken is ERC20, Ownable {
    address public missionManager;

    function mint(address to, uint256 amount) external {
        require(msg.sender == missionManager, "Not authorized");
        _mint(to, amount);
    }

    function setMissionManager(address _manager) external onlyOwner {
        missionManager = _manager;
    }
}
```

**Recommendation:** Start with off-chain $SPARK (database tracking) for MVP, deploy contract later based on demand.

---

### 2.3 Backend API Analysis

#### Endpoints to REUSE (17 endpoints)

| Endpoint | Method | Purpose | Changes Needed |
|----------|--------|---------|----------------|
| `/api/player/<wallet>` | GET | Get player + emissaries | None |
| `/api/player/<wallet>` | POST | Update player data | None |
| `/api/balance` | GET | Get token balances | Add $SPARK |
| `/api/missions` | GET | List missions config | Filter for mini-missions |
| `/api/stats` | GET | Global statistics | Add micro-mission stats |
| `/api/guilds` | GET | Guild information | None |
| `/api/equipment/<id>` | GET | Get equipment | None |
| `/api/claims/<wallet>` | GET | Pending claims | None |
| `/api/claims/confirm` | POST | Confirm claim | None |
| `/api/metadata/<id>` | GET | NFT metadata | None |
| `/api/ember/balance/<wallet>` | GET | $EMBER balance | None |
| `/api/events/active` | GET | Active events | Include micro-events |
| `/health` | GET | Health check | None |

#### Endpoints to ADAPT (4 endpoints)

| Endpoint | Current | Mini App Adaptation |
|----------|---------|---------------------|
| `/api/mission/start` | 3-12h missions | Support 60-300 second missions |
| `/api/mission/complete` | Death chance, complex rewards | Simplified, no death |
| `/api/ember-roll/perform` | D20 gambling | Integrate $SPARK rewards |
| `/api/equipment/equip` | Full equipment system | Quick-equip for active emissary |

#### NEW Endpoints Required (6 endpoints)

```python
# 1. List available micro-missions
@app.route('/api/miniapp/missions', methods=['GET'])
def get_micro_missions():
    """
    Returns: Array of micro-mission types with requirements
    """

# 2. Start micro-mission
@app.route('/api/miniapp/mission/start', methods=['POST'])
def start_micro_mission():
    """
    Body: { wallet, emissary_id, mission_type }
    Returns: { mission_id, duration_seconds, estimated_rewards }
    """

# 3. Complete/claim micro-mission
@app.route('/api/miniapp/mission/complete', methods=['POST'])
def complete_micro_mission():
    """
    Body: { wallet, mission_id }
    Returns: { success, xp_gained, spark_gained, items_dropped }
    """

# 4. Get $SPARK balance and stats
@app.route('/api/miniapp/spark', methods=['GET'])
def get_spark_balance():
    """
    Params: wallet
    Returns: { spark_balance, daily_streak, missions_today, can_claim_daily }
    """

# 5. Daily streak claim
@app.route('/api/miniapp/daily', methods=['POST'])
def claim_daily_bonus():
    """
    Body: { wallet }
    Returns: { spark_bonus, new_streak, next_milestone }
    """

# 6. Farcaster auth/link
@app.route('/api/miniapp/auth', methods=['POST'])
def miniapp_auth():
    """
    Body: { farcaster_fid, wallet_address }
    Returns: { linked, existing_account, emissaries_count }
    """
```

#### Authentication Flow

```
Current System:
1. User connects wallet via Web3 (MetaMask, etc.)
2. Wallet address sent with each request
3. No signature verification (vulnerability!)

Mini App System:
1. User opens mini app in Warpcast/Base App
2. Farcaster Frame SDK provides verified wallet
3. Frame signature proves ownership
4. Backend trusts Frame-verified wallets

Linking Flow:
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Farcaster     │────>│   Mini App API   │────>│   PostgreSQL    │
│   Frame SDK     │     │   /miniapp/auth  │     │   players table │
└─────────────────┘     └──────────────────┘     └─────────────────┘
        │                       │
        │ wallet_address        │ Check existing
        │ farcaster_fid         │ Link or create
        v                       v
    Verified by             Return status
    Farcaster               + emissaries
```

---

### 2.4 Frontend Architecture

#### Current Tech Stack
- **HTML/CSS/JS** - Single-page application (not React)
- **Styling** - Custom CSS with retro terminal theme
- **JavaScript** - Vanilla JS with modular files

#### Design System

**Color Palette (Core)**
```css
/* Primary - Orange/Gold */
--primary: #ff9900;
--bright: #ffbb00;
--gold: #ffcc00;

/* Backgrounds */
--bg-primary: #000000;
--bg-panel: #0f0f14;

/* Status */
--success: #44ff88;
--error: #ff3344;
--info: #00ffff;
```

**Typography**
- **Headers**: `Alagard` (custom medieval serif)
- **Body**: `Pixelify Sans`, `monospace`
- **Size Scale**: 11px (small) - 22px (titles)

**Component Library**
- `.roster-card` - Emissary display cards
- `.mission-card` - Mission selection cards
- `.terminal-modal` - Popup dialogs
- `.cmd-link` - Primary buttons (orange glow)
- `.cmd-link-mint` - CTA buttons (red glow)

#### Available Assets

| Category | Files | Usage in Mini App |
|----------|-------|-------------------|
| Guild Badges | 6 JPGs | Guild selection, rewards |
| Equipment Icons | 10+ PNGs | Inventory display |
| Status Icons | 15+ PNGs | UI feedback |
| Special Items | EternalTorch.png, GoldenRune.png | Achievement rewards |
| Branding | logo-site.png, favicon | App header |

---

## 3. Mission System Deep Dive

### Current Mission Types

| ID | Name | Difficulty | Duration | XP | AURA | Death% | Favored Guild |
|----|------|------------|----------|-----|------|--------|---------------|
| 001 | The Lost Forge | EASY | 3h | 60 | 4 | 0% | Forge Legion |
| 002 | Circle Interference | EASY | 3h | 60 | 4 | 0% | Circle of Mist |
| 003 | Dawn Patrol | EASY | 3h | 60 | 4 | 0% | Order of Dawn |
| 004 | Shadow Infiltration | MEDIUM | 6h | 150 | 10 | 0.5% | Shadow Guild |
| 005 | Horizon Survey | MEDIUM | 6h | 150 | 10 | 0.5% | Horizon Watch |
| 006 | Veil Breach | MEDIUM | 6h | 150 | 10 | 0.5% | Void Echoes |
| 007 | Dragons Crucible | HARD | 12h | 350 | 25 | 2% | Forge Legion |
| 008 | Void Descent | HARD | 12h | 350 | 25 | 2% | Void Echoes |
| 009 | Eclipse Ritual | HARD | 12h | 350 | 25 | 2% | Circle of Mist |

### Success Rate Formula

```
base_rate = mission.success_rate (60-92%)
bonus = 0
bonus += 12 if guild matches
bonus += 8 if class matches
bonus += 5 if race matches
bonus += level // 10
bonus += aura // 100
bonus += equipment.attack_bonus
final_rate = min(98%, base_rate + bonus)
```

### Death System

```
Death Trigger:
- Only on mission FAILURE
- Roll against death_chance (0-2%)
- Modified by death_protection

Death Protection:
- Level 50+: +30%
- Level 30+: +15%
- Level 10+: +5%
- Aura 500+: +20%
- Aura 250+: +10%
- Aura 100+: +5%
- Equipment: up to +80%

On Death:
- State → FALLEN
- XP, Aura, Energy → 0
- death_count++
- Requires $EMBER to revive (50-1000 based on death_count)
```

### Item Drop System

```
Drop Rates by Difficulty:
- EASY:   Item 5%, Rune 1%
- MEDIUM: Item 10%, Rune 3%
- HARD:   Item 20%, Rune 8%
- PARTY:  Item 25%, Rune 12%

Rarity Distribution (HARD):
- Common: 30%
- Rare: 40%
- Epic: 23%
- Legendary: 7%
```

---

## 4. Progression System

### XP & Levels

```
Level Calculation: level = xp_total // 100

Level Benefits:
- Success rate: +1% per 10 levels
- Death protection: Tiers at 10, 30, 50
- No level cap
```

### AURA System

```
AURA = Accumulated spiritual power from missions

Benefits:
- Success rate: +1% per 100 AURA
- Death protection: Tiers at 100, 250, 500
- Ranking qualification
- Visual prestige
```

### Ranking Tiers

| Tier | Name | XP Required | AURA Required | Missions |
|------|------|-------------|---------------|----------|
| 1 | Novice | 0 | 0 | 0 |
| 2 | Apprentice | 100 | 10 | 3 |
| 3 | Journeyman | 500 | 50 | 10 |
| 4 | Adept | 1,500 | 150 | 25 |
| 5 | Expert | 5,000 | 500 | 50 |
| 6 | Master | 15,000 | 1,500 | 100 |
| 7 | Grandmaster | 50,000 | 5,000 | 200 |
| 8 | Legendary | 150,000 | 15,000 | 500 |

### Equipment Bonuses by Rarity

| Rarity | EMBER | XP | Energy | Death | Speed |
|--------|-------|-----|--------|-------|-------|
| Common | +3% | +2% | -0% | -0% | -0% |
| Uncommon | +5% | +4% | -2% | -0% | -0% |
| Rare | +8% | +6% | -3% | -2% | -0% |
| Epic | +12% | +10% | -5% | -4% | -3% |
| Legendary | +18% | +15% | -8% | -6% | -5% |

---

## 5. Micro-Missions Design

### Design Philosophy

```
Main Game Missions:
- Duration: 3-12 hours
- Risk: Permadeath possible
- Rewards: High XP, AURA, rare items
- Engagement: Set and forget

Mini App Micro-Missions:
- Duration: 1-5 minutes
- Risk: Zero death chance
- Rewards: Low XP, $SPARK, common items
- Engagement: Quick dopamine hits while scrolling
```

### Micro-Mission Types (8 Types)

#### 1. Ember Patrol (QUICK)
```json
{
  "id": "MICRO_001",
  "name": "Ember Patrol",
  "duration_seconds": 60,
  "energy_cost": 2,
  "rewards": {
    "xp_guaranteed": 5,
    "spark_guaranteed": 10,
    "aura_chance": 10,
    "aura_amount": 1
  },
  "description": "Quick patrol around the camp perimeter.",
  "lore": "Even brief vigilance strengthens the flame."
}
```

#### 2. Spark Gathering (QUICK)
```json
{
  "id": "MICRO_002",
  "name": "Spark Gathering",
  "duration_seconds": 90,
  "energy_cost": 3,
  "rewards": {
    "xp_guaranteed": 3,
    "spark_guaranteed": 20,
    "spark_bonus_chance": 25,
    "spark_bonus_amount": 10
  },
  "description": "Collect residual sparks from dying embers.",
  "lore": "Where flames fade, sparks remain for those who seek."
}
```

#### 3. Scout Ahead (STANDARD)
```json
{
  "id": "MICRO_003",
  "name": "Scout Ahead",
  "duration_seconds": 180,
  "energy_cost": 5,
  "rewards": {
    "xp_guaranteed": 12,
    "spark_guaranteed": 25,
    "aura_guaranteed": 2,
    "item_chance": 5,
    "item_rarity": "common"
  },
  "description": "Survey nearby territories for threats.",
  "lore": "Knowledge of the land is the first defense."
}
```

#### 4. Ember Hunt (STANDARD)
```json
{
  "id": "MICRO_004",
  "name": "Ember Hunt",
  "duration_seconds": 180,
  "energy_cost": 5,
  "rewards": {
    "xp_guaranteed": 10,
    "spark_guaranteed": 35,
    "ember_chance": 10,
    "ember_amount": 5
  },
  "description": "Track and collect stray ember fragments.",
  "lore": "The dying flame leaves traces for those patient enough to follow."
}
```

#### 5. Training Grounds (STANDARD)
```json
{
  "id": "MICRO_005",
  "name": "Training Grounds",
  "duration_seconds": 240,
  "energy_cost": 6,
  "rewards": {
    "xp_guaranteed": 20,
    "spark_guaranteed": 15,
    "aura_guaranteed": 3,
    "xp_bonus_if_guild_match": 10
  },
  "description": "Practice combat techniques with fellow emissaries.",
  "lore": "Steel sharpens steel. The guild teaches its own."
}
```

#### 6. Supply Run (EXTENDED)
```json
{
  "id": "MICRO_006",
  "name": "Supply Run",
  "duration_seconds": 300,
  "energy_cost": 8,
  "rewards": {
    "xp_guaranteed": 25,
    "spark_guaranteed": 50,
    "aura_guaranteed": 4,
    "item_chance": 10,
    "item_rarity": "common_or_rare"
  },
  "description": "Deliver essential supplies to outposts.",
  "lore": "The lifeline of the realm flows through those who carry it."
}
```

#### 7. Shrine Blessing (DAILY SPECIAL)
```json
{
  "id": "MICRO_007",
  "name": "Shrine Blessing",
  "duration_seconds": 120,
  "energy_cost": 0,
  "daily_limit": 1,
  "rewards": {
    "xp_guaranteed": 15,
    "spark_guaranteed": 30,
    "aura_guaranteed": 5,
    "daily_streak_bonus": true
  },
  "description": "Receive the daily blessing at the eternal shrine.",
  "lore": "The flame remembers those who return each day."
}
```

#### 8. Guild Errand (GUILD-SPECIFIC)
```json
{
  "id": "MICRO_008",
  "name": "Guild Errand",
  "duration_seconds": 150,
  "energy_cost": 4,
  "requires_guild_match": true,
  "rewards": {
    "xp_guaranteed": 15,
    "spark_guaranteed": 40,
    "aura_guaranteed": 3,
    "guild_reputation": 1
  },
  "description": "Complete a task for your guild masters.",
  "lore": "Service to the guild is service to the realm."
}
```

### Micro-Mission Summary Table

| Mission | Duration | Energy | XP | SPARK | AURA | Special |
|---------|----------|--------|-----|-------|------|---------|
| Ember Patrol | 60s | 2 | 5 | 10 | 10% | Fastest |
| Spark Gathering | 90s | 3 | 3 | 20-30 | - | Best SPARK |
| Scout Ahead | 180s | 5 | 12 | 25 | 2 | 5% item |
| Ember Hunt | 180s | 5 | 10 | 35 | - | 10% $EMBER |
| Training Grounds | 240s | 6 | 20-30 | 15 | 3 | Guild bonus |
| Supply Run | 300s | 8 | 25 | 50 | 4 | 10% item |
| Shrine Blessing | 120s | 0 | 15 | 30 | 5 | Daily only |
| Guild Errand | 150s | 4 | 15 | 40 | 3 | Guild required |

### Integration with Main Game

| Aspect | Mini App Earned | Main Game Effect |
|--------|-----------------|------------------|
| XP | 3-30 per micro-mission | Adds directly to emissary XP |
| AURA | 1-5 per micro-mission | Adds directly to AURA |
| $SPARK | 10-50 per micro-mission | Exchangeable for items |
| Items | Common drops only | Same items, lower rarity |
| Rankings | Counts toward rank progression | Same ranking system |
| $EMBER | Rare chance (10%) | Direct to balance |

### Daily Limits & Cooldowns

```
Per Emissary:
- Max 10 micro-missions per day
- 5-minute cooldown between missions
- No mission-specific cooldowns

Per Wallet:
- Unlimited emissaries can run missions
- Daily streak bonus (1 free Shrine Blessing)
- Max $SPARK earn: ~500/day (soft cap via energy)

Energy System:
- Micro-missions use same energy pool
- Energy regen: Full in 48 hours (2.08/hour)
- Quick missions enable more total missions
```

---

## 6. $SPARK Tokenomics

### Token Overview

```
Name: SPARK
Symbol: $SPARK
Type: Mini-app utility token
Blockchain: Off-chain initially (database), on-chain later
Purpose: Bridge between casual play and main game economy
```

### Obtaining $SPARK

| Source | Amount | Frequency |
|--------|--------|-----------|
| Ember Patrol | 10 | Per mission |
| Spark Gathering | 20-30 | Per mission |
| Scout Ahead | 25 | Per mission |
| Ember Hunt | 35 | Per mission |
| Training Grounds | 15 | Per mission |
| Supply Run | 50 | Per mission |
| Shrine Blessing | 30 | Daily |
| Guild Errand | 40 | Per mission |
| Daily Streak Bonus | 10-100 | Daily (scaling) |
| First Mint Bonus | 500 | One-time |
| Referral Bonus | 100 | Per referral mint |

### Daily Streak System

| Days | Bonus SPARK | Cumulative |
|------|-------------|------------|
| 1 | 10 | 10 |
| 3 | 20 | 30 |
| 7 | 50 | 80 |
| 14 | 75 | 155 |
| 30 | 150 | 305 |
| 60 | 300 | 605 |
| 90+ | 500 | 1105+ |

### $SPARK Utility

#### In Mini App
| Use | Cost | Effect |
|-----|------|--------|
| Skip mission cooldown | 50 SPARK | Instant next mission |
| Energy boost (small) | 100 SPARK | +10 energy |
| Energy boost (large) | 200 SPARK | +25 energy |
| Lucky charm | 150 SPARK | +5% item drop for 1 mission |
| Double XP | 300 SPARK | 2x XP for next mission |

#### In Main Game
| Use | Cost | Effect |
|-----|------|--------|
| Common item crate | 500 SPARK | Random common item |
| Rare item crate | 2,000 SPARK | Random rare item |
| Energy potion | 300 SPARK | +25 energy |
| XP scroll | 1,000 SPARK | +100 XP |
| AURA crystal | 1,500 SPARK | +50 AURA |
| Convert to $EMBER | 10,000 SPARK | 10 $EMBER |

### Token Economics

```
Emission Rate:
- Average player: ~200 SPARK/day
- Active player: ~500 SPARK/day
- Hardcore grinder: ~800 SPARK/day (soft cap)

Sink Mechanisms:
- Item crates (permanent removal)
- Energy boosts (value consumed)
- $EMBER conversion (deflationary)
- Premium cosmetics (future)

No Hard Cap:
- Inflationary by design (engagement reward)
- Value maintained through utility demand
- $EMBER conversion acts as floor price
```

### Phase 2: On-Chain $SPARK

```
Deployment Trigger:
- 1,000+ daily active mini-app users
- 10,000,000 $SPARK total earned

Contract Features:
- ERC20 standard
- Controlled minting (backend only)
- Burn function for redemptions
- No transfer restrictions

Liquidity:
- Initial LP via Clanker or manual
- SPARK/ETH pair on Uniswap v3 (Base)
- Treasury-funded initial liquidity
```

---

## 7. Technical Architecture

### System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     FARCASTER ECOSYSTEM                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │  Warpcast   │  │  Base App   │  │  Other      │              │
│  │  Mobile     │  │  Mobile     │  │  Clients    │              │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘              │
│         │                │                │                      │
│         └────────────────┼────────────────┘                      │
│                          │                                       │
│                          ▼                                       │
│              ┌───────────────────────┐                          │
│              │   Farcaster Frame     │                          │
│              │   Mini App (Next.js)  │                          │
│              │   - MiniKit SDK       │                          │
│              │   - Wagmi/Viem        │                          │
│              │   - TailwindCSS       │                          │
│              └───────────┬───────────┘                          │
└──────────────────────────┼──────────────────────────────────────┘
                           │
                           │ HTTPS/JSON
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                    EMBERHOLM BACKEND                              │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                    Flask API Server                         │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │  │
│  │  │ Existing API │  │ Mini App API │  │ Auth Layer   │      │  │
│  │  │ /api/*       │  │ /api/miniapp │  │ Rate Limit   │      │  │
│  │  └──────┬───────┘  └──────┬───────┘  └──────────────┘      │  │
│  │         │                 │                                 │  │
│  │         └─────────────────┼─────────────────────────────────│  │
│  │                           │                                 │  │
│  │                           ▼                                 │  │
│  │              ┌────────────────────────┐                     │  │
│  │              │   PostgreSQL Database  │                     │  │
│  │              │   - nfts (35k records) │                     │  │
│  │              │   - micro_missions     │                     │  │
│  │              │   - spark_balances     │                     │  │
│  │              │   - user_balances      │                     │  │
│  │              └────────────────────────┘                     │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
                           │
                           │ Web3 RPC
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                    BASE BLOCKCHAIN                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │ Emberholm   │  │ $EMBER      │  │ $SPARK      │              │
│  │ Portal NFT  │  │ Token       │  │ Token       │              │
│  │ (ERC721)    │  │ (ERC20)     │  │ (Future)    │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└──────────────────────────────────────────────────────────────────┘
```

### Tech Stack Recommendation

#### Mini App Frontend

```
Framework: Next.js 14 (App Router)
Styling: TailwindCSS + Custom Emberholm theme
Web3:
  - @coinbase/onchainkit/minikit (Farcaster integration)
  - wagmi v2 (React hooks for Ethereum)
  - viem (TypeScript Ethereum library)
State: Zustand or React Context
Hosting: Vercel (optimal for Next.js)
```

#### Backend Extension

```
Option A (Recommended): Extend Existing Flask
- Add /api/miniapp/* routes to app.py
- Reuse database connections
- Share authentication logic
- Deploy alongside main app

Option B: Separate Node.js Service
- New Express/Fastify server
- Connect to same PostgreSQL
- Independent scaling
- More complex deployment
```

**Recommendation:** Option A - Extend Flask backend. Less complexity, shared data layer, easier maintenance.

### API Route Structure

```
Existing Routes (Reuse):
/api/player/<wallet>          GET/POST
/api/balance                  GET
/api/missions                 GET
/api/equipment/<id>           GET
/api/claims/<wallet>          GET
/api/stats                    GET

New Mini App Routes:
/api/miniapp/auth             POST   - Farcaster auth/link
/api/miniapp/missions         GET    - List micro-missions
/api/miniapp/mission/start    POST   - Start micro-mission
/api/miniapp/mission/complete POST   - Complete & claim
/api/miniapp/spark            GET    - $SPARK balance
/api/miniapp/daily            POST   - Daily streak claim
/api/miniapp/referral         POST   - Track referrals
```

### Data Flow: Start Micro-Mission

```
1. User taps "Start Mission" in mini app
   │
   ▼
2. Mini App → POST /api/miniapp/mission/start
   {
     "wallet": "0x...",
     "emissary_id": "00001",
     "mission_type": "MICRO_003"
   }
   │
   ▼
3. Backend validates:
   - Emissary belongs to wallet
   - Emissary state is READY
   - Energy >= cost
   - No active micro-mission
   - Daily limit not exceeded
   │
   ▼
4. Backend creates mission:
   - Insert into micro_missions table
   - Update nft.dynamic_state (energy, state)
   - Return mission details
   │
   ▼
5. Response:
   {
     "success": true,
     "mission_id": 12345,
     "ends_at": "2024-01-27T12:05:00Z",
     "duration_seconds": 180,
     "estimated_rewards": {
       "xp": 12,
       "spark": 25,
       "aura": 2
     }
   }
   │
   ▼
6. Mini App shows countdown timer
   │
   ▼
7. Timer reaches 0 → Auto-prompt claim
```

### Data Flow: Complete Micro-Mission

```
1. Timer ends / User taps "Claim"
   │
   ▼
2. Mini App → POST /api/miniapp/mission/complete
   {
     "wallet": "0x...",
     "mission_id": 12345
   }
   │
   ▼
3. Backend validates:
   - Mission exists and belongs to wallet
   - Current time >= ends_at
   - Not already claimed
   │
   ▼
4. Backend calculates rewards:
   - Base rewards from mission config
   - Apply equipment bonuses
   - Roll for bonus drops
   - Check streak bonuses
   │
   ▼
5. Backend updates:
   - nft.dynamic_state (xp, aura, energy regen)
   - spark_balances (add SPARK)
   - micro_missions (mark claimed)
   - global_stats (counters)
   │
   ▼
6. Response:
   {
     "success": true,
     "outcome": "SUCCESS",
     "rewards": {
       "xp": 14,
       "spark": 28,
       "aura": 2,
       "items": []
     },
     "streak_bonus": 10,
     "total_spark": 38,
     "emissary_xp_total": 514
   }
   │
   ▼
7. Mini App shows celebration + share prompt
```

---

## 8. UI/UX Design

### Screen Inventory

| # | Screen | Purpose | Priority |
|---|--------|---------|----------|
| 1 | Splash/Onboarding | First-time intro | HIGH |
| 2 | Home (No Emissary) | Prompt to mint | HIGH |
| 3 | Home (With Emissary) | Main dashboard | HIGH |
| 4 | Emissary Selector | Choose active hero | MEDIUM |
| 5 | Mission List | Browse micro-missions | HIGH |
| 6 | Mission Active | Timer countdown | HIGH |
| 7 | Mission Complete | Rewards celebration | HIGH |
| 8 | Mint Screen | Purchase emissary | HIGH |
| 9 | Inventory | View items | MEDIUM |
| 10 | Profile/Stats | Player overview | LOW |

### Screen Wireframes

#### 1. Splash Screen
```
┌─────────────────────────────┐
│                             │
│      [EMBERHOLM LOGO]       │
│                             │
│   ══════════════════════    │
│   THE DYING FLAME AWAITS    │
│   ══════════════════════    │
│                             │
│   In a world where the      │
│   eternal flame fades,      │
│   emissaries rise to        │
│   keep hope alive...        │
│                             │
│   ┌───────────────────────┐ │
│   │      ENTER PORTAL     │ │
│   └───────────────────────┘ │
│                             │
└─────────────────────────────┘
```

#### 2. Home (No Emissary)
```
┌─────────────────────────────┐
│ ☰  EMBERHOLM        ◈ 0    │
├─────────────────────────────┤
│                             │
│   ┌─────────────────────┐   │
│   │                     │   │
│   │   [EMISSARY ART]    │   │
│   │      Preview        │   │
│   │                     │   │
│   └─────────────────────┘   │
│                             │
│   NO EMISSARY YET           │
│                             │
│   Mint your first Emissary  │
│   and join the fight to     │
│   save the dying flame.     │
│                             │
│   ┌───────────────────────┐ │
│   │   MINT EMISSARY       │ │
│   │   0.0011 ETH          │ │
│   └───────────────────────┘ │
│                             │
│   Already have one?         │
│   [Refresh Wallet]          │
│                             │
└─────────────────────────────┘
```

#### 3. Home (With Emissary)
```
┌─────────────────────────────┐
│ ☰  EMBERHOLM    ◈ 1,250    │
├─────────────────────────────┤
│ ┌─────────────────────────┐ │
│ │ [IMG]  Valorian #00042  │ │
│ │        Human Warrior    │ │
│ │        Forge Legion     │ │
│ │ ─────────────────────── │ │
│ │ LVL 5    XP: 512/600    │ │
│ │ ▓▓▓▓▓▓▓▓░░░░ 85%       │ │
│ │                         │ │
│ │ ⚡ 72/100  ✧ 45  ◈ 1250 │ │
│ └─────────────────────────┘ │
│                             │
│ ═══ QUICK MISSIONS ═══      │
│                             │
│ ┌───────────┐ ┌───────────┐ │
│ │ Ember     │ │ Scout     │ │
│ │ Patrol    │ │ Ahead     │ │
│ │ 1 min     │ │ 3 min     │ │
│ │ +10 ◈     │ │ +25 ◈     │ │
│ └───────────┘ └───────────┘ │
│                             │
│ ┌───────────┐ ┌───────────┐ │
│ │ Shrine    │ │ Supply    │ │
│ │ Blessing  │ │ Run       │ │
│ │ FREE/DAY  │ │ 5 min     │ │
│ │ +30 ◈     │ │ +50 ◈     │ │
│ └───────────┘ └───────────┘ │
│                             │
│ [View All Missions]         │
│                             │
└─────────────────────────────┘

Legend:
⚡ = Energy
✧ = AURA
◈ = SPARK
```

#### 4. Mission Active
```
┌─────────────────────────────┐
│ ← Back      MISSION ACTIVE  │
├─────────────────────────────┤
│                             │
│   ┌─────────────────────┐   │
│   │                     │   │
│   │   [EMISSARY ART]    │   │
│   │    with animation   │   │
│   │                     │   │
│   └─────────────────────┘   │
│                             │
│        SCOUT AHEAD          │
│                             │
│   "Surveying nearby         │
│    territories..."          │
│                             │
│   ┌─────────────────────┐   │
│   │                     │   │
│   │       2:34          │   │
│   │     remaining       │   │
│   │                     │   │
│   │ ▓▓▓▓▓▓▓░░░░░░░░░░  │   │
│   └─────────────────────┘   │
│                             │
│   Expected Rewards:         │
│   +12 XP  +25 ◈  +2 ✧      │
│                             │
│   You can close this app.   │
│   We'll notify you when     │
│   the mission completes.    │
│                             │
└─────────────────────────────┘
```

#### 5. Mission Complete
```
┌─────────────────────────────┐
│        MISSION COMPLETE     │
├─────────────────────────────┤
│                             │
│         ✦ SUCCESS ✦         │
│                             │
│   ┌─────────────────────┐   │
│   │   [CELEBRATION      │   │
│   │    ANIMATION]       │   │
│   └─────────────────────┘   │
│                             │
│   ═══ REWARDS ═══           │
│                             │
│   ┌─────────────────────┐   │
│   │  +14 XP             │   │
│   │  +28 SPARK  ◈       │   │
│   │  +2 AURA    ✧       │   │
│   │                     │   │
│   │  🔥 STREAK BONUS!   │   │
│   │  +10 SPARK          │   │
│   └─────────────────────┘   │
│                             │
│   Total SPARK: 1,288        │
│                             │
│   ┌───────────────────────┐ │
│   │    SHARE ON FARCASTER │ │
│   └───────────────────────┘ │
│                             │
│   ┌───────────────────────┐ │
│   │    ANOTHER MISSION    │ │
│   └───────────────────────┘ │
│                             │
└─────────────────────────────┘
```

#### 6. Mint Screen
```
┌─────────────────────────────┐
│ ← Back       MINT EMISSARY  │
├─────────────────────────────┤
│                             │
│   ┌─────────────────────┐   │
│   │                     │   │
│   │   [RANDOM PREVIEW]  │   │
│   │   Animated shuffle  │   │
│   │                     │   │
│   └─────────────────────┘   │
│                             │
│   Each Emissary is unique.  │
│   Race, class, and guild    │
│   determined by fate.       │
│                             │
│   ─────────────────────     │
│                             │
│   Quantity: [1] [+] [-]     │
│                             │
│   Price: 0.0011 ETH         │
│   Total: 0.0011 ETH         │
│                             │
│   Supply: 42 / 35,000       │
│                             │
│   ┌───────────────────────┐ │
│   │      MINT NOW         │ │
│   └───────────────────────┘ │
│                             │
│   By minting, you agree to  │
│   the terms of the Portal.  │
│                             │
└─────────────────────────────┘
```

### Design System for Mini App

#### Color Tokens (TailwindCSS)
```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        ember: {
          primary: '#ff9900',
          bright: '#ffbb00',
          gold: '#ffcc00',
          dim: '#dd7700',
          dark: '#994400',
        },
        void: {
          primary: '#000000',
          secondary: '#0a0a0f',
          panel: '#0f0f14',
          elevated: '#14141a',
        },
        status: {
          success: '#44ff88',
          error: '#ff3344',
          info: '#00ffff',
          warning: '#ff8800',
        }
      }
    }
  }
}
```

#### Typography
```css
/* Fonts to include */
@font-face {
  font-family: 'Alagard';
  src: url('/fonts/alagard.ttf');
}

/* Font classes */
.font-medieval { font-family: 'Alagard', serif; }
.font-terminal { font-family: 'Pixelify Sans', monospace; }

/* Size scale */
.text-xs { font-size: 11px; }
.text-sm { font-size: 13px; }
.text-base { font-size: 14px; }
.text-lg { font-size: 16px; }
.text-xl { font-size: 18px; }
.text-2xl { font-size: 22px; }
```

#### Component Classes
```css
/* Primary Button */
.btn-primary {
  @apply bg-ember-primary text-black font-bold py-3 px-6 rounded;
  @apply hover:bg-ember-bright;
  @apply shadow-[0_0_10px_rgba(255,153,0,0.5)];
  @apply hover:shadow-[0_0_20px_rgba(255,153,0,0.7)];
  @apply transition-all duration-200;
  min-height: 48px;
}

/* CTA Button */
.btn-cta {
  @apply bg-status-error text-black font-bold py-3 px-6 rounded;
  @apply shadow-[0_0_15px_rgba(255,51,68,0.7)];
}

/* Card */
.card {
  @apply bg-void-panel border border-ember-primary/40 rounded-lg p-4;
}

/* Glow Text */
.glow-gold {
  text-shadow:
    0 0 3px #ffcc00,
    0 0 8px #ffcc00,
    0 0 15px #ffcc00;
}
```

---

## 9. Farcaster Integration

### Manifest Configuration

```json
// farcaster.json
{
  "accountAssociation": {
    "header": "...",
    "payload": "...",
    "signature": "..."
  },
  "frame": {
    "name": "Emberholm Portal",
    "version": "1.0.0",
    "iconUrl": "https://emberholm-portal.onrender.com/img/logowebfavicon.png",
    "homeUrl": "https://emberholm-miniapp.vercel.app",
    "splashImageUrl": "https://emberholm-portal.onrender.com/img/logo-site.png",
    "splashBackgroundColor": "#000000",
    "webhookUrl": "https://emberholm-portal.onrender.com/api/miniapp/webhook"
  }
}
```

### MiniKit Integration

```typescript
// app/providers.tsx
import { MiniKitProvider } from '@coinbase/onchainkit/minikit';

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <MiniKitProvider
      appId="emberholm-portal"
      chain={base}
    >
      {children}
    </MiniKitProvider>
  );
}

// hooks/useEmberholmUser.ts
import { useMiniKit } from '@coinbase/onchainkit/minikit';

export function useEmberholmUser() {
  const { user, isReady } = useMiniKit();

  // user.wallet contains verified wallet address
  // user.fid contains Farcaster ID

  return {
    wallet: user?.wallet,
    fid: user?.fid,
    isReady
  };
}
```

### Share Functionality

```typescript
// utils/share.ts
import { sdk } from '@coinbase/onchainkit/minikit';

export async function shareToFarcaster({
  text,
  imageUrl,
  embedUrl
}: {
  text: string;
  imageUrl?: string;
  embedUrl?: string;
}) {
  await sdk.actions.composeCast({
    text,
    embeds: embedUrl ? [embedUrl] : undefined
  });
}

// Usage: Share mission completion
shareToFarcaster({
  text: `🔥 My Emissary just completed a Scout mission!\n\n+14 XP | +28 SPARK\n\nJoin the fight: `,
  embedUrl: 'https://emberholm-miniapp.vercel.app'
});
```

### Notification System

```typescript
// api/notifications.ts
import { sdk } from '@coinbase/onchainkit/minikit';

// Request notification permission
await sdk.actions.requestNotificationPermission();

// Send notification when mission completes
export async function notifyMissionComplete(
  fid: number,
  missionName: string,
  rewards: { xp: number; spark: number }
) {
  await sdk.actions.sendNotification({
    title: "Mission Complete!",
    body: `${missionName}: +${rewards.xp} XP, +${rewards.spark} SPARK`,
    targetUrl: "https://emberholm-miniapp.vercel.app/claim"
  });
}
```

### Referral Tracking

```typescript
// Track referrals via URL params
// https://emberholm-miniapp.vercel.app?ref=0x1234...

// api/miniapp/referral
async function trackReferral(
  newUserWallet: string,
  referrerWallet: string
) {
  // On successful mint by new user:
  // 1. Credit referrer 100 SPARK
  // 2. Credit new user 500 SPARK (first mint bonus)
  // 3. Track in database for analytics
}
```

---

## 10. Implementation Plan

### Phase 1: Foundation (Week 1-2)

#### Backend Work
- [ ] Create micro_missions table migration
- [ ] Create spark_balances table migration
- [ ] Add /api/miniapp/auth endpoint
- [ ] Add /api/miniapp/missions endpoint
- [ ] Add /api/miniapp/mission/start endpoint
- [ ] Add /api/miniapp/mission/complete endpoint
- [ ] Add /api/miniapp/spark endpoint
- [ ] Add micro-mission configuration (JSON)

#### Frontend Setup
- [ ] Initialize Next.js project with MiniKit
- [ ] Configure TailwindCSS with Emberholm theme
- [ ] Set up Wagmi/Viem for blockchain interaction
- [ ] Create base layout components
- [ ] Implement splash/onboarding screen

### Phase 2: Core Features (Week 2-3)

#### Backend Work
- [ ] Implement daily streak logic
- [ ] Add /api/miniapp/daily endpoint
- [ ] Add referral tracking endpoint
- [ ] Integrate with existing player data
- [ ] Add micro-mission completion notifications

#### Frontend Work
- [ ] Build Home screen (with/without emissary)
- [ ] Build Mission List screen
- [ ] Build Mission Active screen (timer)
- [ ] Build Mission Complete screen
- [ ] Implement mint flow
- [ ] Add wallet connection flow

### Phase 3: Polish & Testing (Week 3-4)

#### Integration
- [ ] Connect all screens to backend APIs
- [ ] Test mission flow end-to-end
- [ ] Test mint flow with real transactions
- [ ] Implement error handling
- [ ] Add loading states

#### Testing
- [ ] Test on Warpcast iOS
- [ ] Test on Warpcast Android
- [ ] Test on Base App
- [ ] Test wallet connection edge cases
- [ ] Test rate limiting

### Phase 4: Launch Prep (Week 4)

#### Farcaster Setup
- [ ] Generate manifest signature
- [ ] Upload manifest to hosting
- [ ] Submit for Farcaster app review
- [ ] Configure notifications

#### Monitoring
- [ ] Set up error tracking (Sentry)
- [ ] Set up analytics (Mixpanel/Amplitude)
- [ ] Create admin dashboard for metrics
- [ ] Document runbook for issues

### Timeline Summary

| Week | Focus | Deliverables |
|------|-------|--------------|
| 1 | Backend foundation | New API endpoints, database migrations |
| 2 | Frontend foundation | Core screens, MiniKit integration |
| 3 | Integration | End-to-end flows working |
| 4 | Testing & Launch | Bug fixes, Farcaster submission |

---

## 11. Launch Checklist

### Technical Requirements

- [ ] All API endpoints tested and documented
- [ ] Database migrations applied to production
- [ ] SSL certificates valid
- [ ] Rate limiting configured appropriately
- [ ] Error monitoring active
- [ ] Backup/restore procedures documented

### Farcaster Requirements

- [ ] farcaster.json manifest deployed
- [ ] Account association verified
- [ ] Icon images uploaded (correct dimensions)
- [ ] Splash image uploaded
- [ ] Webhook URL responding
- [ ] Notifications permission working

### Security Review

- [ ] No sensitive keys in frontend code
- [ ] API authentication working
- [ ] Rate limits prevent abuse
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention verified
- [ ] CORS configured correctly

### User Experience

- [ ] Onboarding flow tested
- [ ] Mission flow tested end-to-end
- [ ] Mint flow tested with real ETH
- [ ] Share functionality working
- [ ] Notifications arriving
- [ ] Loading states graceful
- [ ] Error messages helpful

### Content

- [ ] All micro-mission descriptions written
- [ ] Lore text reviewed
- [ ] Help/FAQ content prepared
- [ ] Terms of service link active

### Analytics

- [ ] User registration events tracked
- [ ] Mission start/complete events tracked
- [ ] Mint events tracked
- [ ] Share events tracked
- [ ] Daily active users dashboard
- [ ] SPARK economy dashboard

### Launch Day

- [ ] Team available for monitoring
- [ ] Social media posts scheduled
- [ ] Community announcement prepared
- [ ] Backup plan for high traffic
- [ ] Rollback procedure documented

---

## Appendix A: API Reference

### New Endpoints Specification

#### POST /api/miniapp/auth
```
Request:
{
  "farcaster_fid": 12345,
  "wallet_address": "0x..."
}

Response (existing user):
{
  "success": true,
  "linked": true,
  "existing_account": true,
  "emissaries_count": 3,
  "spark_balance": 1250
}

Response (new user):
{
  "success": true,
  "linked": true,
  "existing_account": false,
  "emissaries_count": 0,
  "spark_balance": 0,
  "welcome_bonus_available": true
}
```

#### GET /api/miniapp/missions
```
Response:
{
  "missions": [
    {
      "id": "MICRO_001",
      "name": "Ember Patrol",
      "duration_seconds": 60,
      "energy_cost": 2,
      "rewards": {
        "xp_guaranteed": 5,
        "spark_guaranteed": 10,
        "aura_chance": 10,
        "aura_amount": 1
      },
      "available": true,
      "cooldown_remaining": 0
    }
  ],
  "daily_missions": {
    "shrine_blessing": {
      "available": true,
      "completed_today": false
    }
  }
}
```

#### POST /api/miniapp/mission/start
```
Request:
{
  "wallet": "0x...",
  "emissary_id": "00001",
  "mission_type": "MICRO_003"
}

Response:
{
  "success": true,
  "mission_id": 12345,
  "mission_type": "MICRO_003",
  "emissary_id": "00001",
  "start_time": "2024-01-27T12:00:00Z",
  "ends_at": "2024-01-27T12:03:00Z",
  "duration_seconds": 180,
  "energy_spent": 5,
  "energy_remaining": 67,
  "estimated_rewards": {
    "xp": 12,
    "spark": 25,
    "aura": 2,
    "item_chance_percent": 5
  }
}
```

#### POST /api/miniapp/mission/complete
```
Request:
{
  "wallet": "0x...",
  "mission_id": 12345
}

Response:
{
  "success": true,
  "outcome": "SUCCESS",
  "rewards": {
    "xp": 14,
    "spark": 28,
    "aura": 2,
    "items": []
  },
  "bonuses": {
    "equipment_xp_bonus": 2,
    "streak_spark_bonus": 10
  },
  "totals": {
    "xp_earned": 14,
    "spark_earned": 38,
    "emissary_xp_total": 526,
    "wallet_spark_total": 1288
  },
  "streak": {
    "current": 5,
    "next_milestone": 7,
    "next_bonus": 50
  }
}
```

#### GET /api/miniapp/spark
```
Request: ?wallet=0x...

Response:
{
  "wallet": "0x...",
  "spark_balance": 1288,
  "total_earned": 5420,
  "daily_streak": 5,
  "missions_today": 7,
  "missions_max_today": 10,
  "can_claim_daily": false,
  "next_daily_reset": "2024-01-28T00:00:00Z"
}
```

#### POST /api/miniapp/daily
```
Request:
{
  "wallet": "0x..."
}

Response:
{
  "success": true,
  "streak_day": 6,
  "spark_bonus": 20,
  "new_balance": 1308,
  "next_milestone": {
    "day": 7,
    "bonus": 50
  }
}
```

---

## Appendix B: Micro-Mission Configuration

```json
// data/micro_missions_config.json
{
  "missions": [
    {
      "id": "MICRO_001",
      "name": "Ember Patrol",
      "type": "quick",
      "duration_seconds": 60,
      "energy_cost": 2,
      "daily_limit": null,
      "cooldown_seconds": 300,
      "requirements": {},
      "rewards": {
        "xp_guaranteed": 5,
        "spark_guaranteed": 10,
        "aura_chance": 10,
        "aura_amount": 1
      },
      "description": "Quick patrol around the camp perimeter.",
      "lore": "Even brief vigilance strengthens the flame.",
      "active_text": "Patrolling the perimeter...",
      "complete_text": "The perimeter is secure."
    },
    {
      "id": "MICRO_002",
      "name": "Spark Gathering",
      "type": "quick",
      "duration_seconds": 90,
      "energy_cost": 3,
      "daily_limit": null,
      "cooldown_seconds": 300,
      "requirements": {},
      "rewards": {
        "xp_guaranteed": 3,
        "spark_guaranteed": 20,
        "spark_bonus_chance": 25,
        "spark_bonus_amount": 10
      },
      "description": "Collect residual sparks from dying embers.",
      "lore": "Where flames fade, sparks remain for those who seek.",
      "active_text": "Gathering scattered sparks...",
      "complete_text": "A handful of sparks, still warm."
    },
    {
      "id": "MICRO_003",
      "name": "Scout Ahead",
      "type": "standard",
      "duration_seconds": 180,
      "energy_cost": 5,
      "daily_limit": null,
      "cooldown_seconds": 300,
      "requirements": {},
      "rewards": {
        "xp_guaranteed": 12,
        "spark_guaranteed": 25,
        "aura_guaranteed": 2,
        "item_chance": 5,
        "item_rarity": ["common"]
      },
      "description": "Survey nearby territories for threats.",
      "lore": "Knowledge of the land is the first defense.",
      "active_text": "Surveying the territory...",
      "complete_text": "The path ahead is mapped."
    },
    {
      "id": "MICRO_004",
      "name": "Ember Hunt",
      "type": "standard",
      "duration_seconds": 180,
      "energy_cost": 5,
      "daily_limit": null,
      "cooldown_seconds": 300,
      "requirements": {},
      "rewards": {
        "xp_guaranteed": 10,
        "spark_guaranteed": 35,
        "ember_chance": 10,
        "ember_amount": 5
      },
      "description": "Track and collect stray ember fragments.",
      "lore": "The dying flame leaves traces for those patient enough to follow.",
      "active_text": "Tracking ember traces...",
      "complete_text": "Fragments of ember, carefully gathered."
    },
    {
      "id": "MICRO_005",
      "name": "Training Grounds",
      "type": "standard",
      "duration_seconds": 240,
      "energy_cost": 6,
      "daily_limit": null,
      "cooldown_seconds": 300,
      "requirements": {},
      "rewards": {
        "xp_guaranteed": 20,
        "spark_guaranteed": 15,
        "aura_guaranteed": 3,
        "xp_guild_bonus": 10
      },
      "description": "Practice combat techniques with fellow emissaries.",
      "lore": "Steel sharpens steel. The guild teaches its own.",
      "active_text": "Training with comrades...",
      "complete_text": "Skills honed, bonds strengthened."
    },
    {
      "id": "MICRO_006",
      "name": "Supply Run",
      "type": "extended",
      "duration_seconds": 300,
      "energy_cost": 8,
      "daily_limit": null,
      "cooldown_seconds": 300,
      "requirements": {},
      "rewards": {
        "xp_guaranteed": 25,
        "spark_guaranteed": 50,
        "aura_guaranteed": 4,
        "item_chance": 10,
        "item_rarity": ["common", "rare"]
      },
      "description": "Deliver essential supplies to outposts.",
      "lore": "The lifeline of the realm flows through those who carry it.",
      "active_text": "Delivering supplies...",
      "complete_text": "Supplies delivered. The outpost stands strong."
    },
    {
      "id": "MICRO_007",
      "name": "Shrine Blessing",
      "type": "daily",
      "duration_seconds": 120,
      "energy_cost": 0,
      "daily_limit": 1,
      "cooldown_seconds": 0,
      "requirements": {},
      "rewards": {
        "xp_guaranteed": 15,
        "spark_guaranteed": 30,
        "aura_guaranteed": 5,
        "streak_bonus": true
      },
      "description": "Receive the daily blessing at the eternal shrine.",
      "lore": "The flame remembers those who return each day.",
      "active_text": "Receiving the blessing...",
      "complete_text": "The flame's warmth fills you."
    },
    {
      "id": "MICRO_008",
      "name": "Guild Errand",
      "type": "guild",
      "duration_seconds": 150,
      "energy_cost": 4,
      "daily_limit": 3,
      "cooldown_seconds": 600,
      "requirements": {
        "guild_match": true
      },
      "rewards": {
        "xp_guaranteed": 15,
        "spark_guaranteed": 40,
        "aura_guaranteed": 3,
        "guild_reputation": 1
      },
      "description": "Complete a task for your guild masters.",
      "lore": "Service to the guild is service to the realm.",
      "active_text": "Serving the guild...",
      "complete_text": "The guild masters nod in approval."
    }
  ],
  "settings": {
    "max_missions_per_day": 10,
    "energy_regen_per_hour": 2.08,
    "default_cooldown_seconds": 300
  }
}
```

---

## Appendix C: Component Reference

### React Components for Mini App

```
/components
├── layout/
│   ├── AppShell.tsx         # Main app wrapper
│   ├── Header.tsx           # Top navigation
│   └── BottomNav.tsx        # Tab navigation
├── emissary/
│   ├── EmissaryCard.tsx     # Main emissary display
│   ├── EmissarySelector.tsx # Choose emissary
│   ├── EmissaryStats.tsx    # Stats display
│   └── EmissaryMini.tsx     # Compact card
├── mission/
│   ├── MissionCard.tsx      # Mission selection card
│   ├── MissionList.tsx      # Mission grid
│   ├── MissionActive.tsx    # Timer countdown
│   ├── MissionComplete.tsx  # Rewards display
│   └── MissionTimer.tsx     # Countdown component
├── mint/
│   ├── MintScreen.tsx       # Full mint flow
│   ├── MintPreview.tsx      # Preview component
│   └── MintButton.tsx       # CTA button
├── ui/
│   ├── Button.tsx           # Button variants
│   ├── Card.tsx             # Card container
│   ├── Modal.tsx            # Modal dialog
│   ├── Progress.tsx         # Progress bars
│   ├── Spinner.tsx          # Loading spinner
│   └── Toast.tsx            # Notifications
└── icons/
    ├── SparkIcon.tsx        # SPARK token icon
    ├── EnergyIcon.tsx       # Energy bolt
    ├── AuraIcon.tsx         # AURA star
    └── GuildIcons.tsx       # Guild badges
```

---

*Document generated for Emberholm Portal Farcaster Mini App development.*
*Last updated: 2026-01-27*
