# COMPLETE REPORT: EMBERHOLM PORTAL

> **Project Presentation Document**
> Version 2.1 | January 2026

---

## TABLE OF CONTENTS

1. [Introduction and Lore](#1-introduction-and-lore)
2. [Game Mechanics](#2-game-mechanics)
3. [NFTs with Dynamic Metadata](#3-nfts-with-dynamic-metadata)
4. [Items and Runes System](#4-items-and-runes-system)
5. [Drop System](#5-drop-system)
6. [Economy: $EMBER Token](#6-economy-ember-token)
7. [$ASH Token - Governance](#7-ash-token---governance)
8. [Rankings System](#8-rankings-system)
9. [Achievements System](#9-achievements-system)
10. [Technical Infrastructure](#10-technical-infrastructure)
11. [Executive Summary Q&A](#11-executive-summary-qa)

---

## 1. INTRODUCTION AND LORE

### 1.1 General Concept

**Emberholm Portal** is a medieval fantasy RPG where **35,000 unique Emissary NFTs** embark on missions, earn **$EMBER** tokens, and determine the fate of a **dying kingdom**.

### 1.2 The World of Emberholm

The game takes place in **Emberholm**, a realm threatened by cosmic forces:

- **The Eternal Flame**: Sacred fire at the heart of Emberholm that provides stability to the realm. Once a year it burns with extraordinary intensity.
- **The Ember Core**: Heart of the realm that provides stability and aura to all its inhabitants.
- **The Veil**: Barrier that separates the world of the living from the **Void**. When it tears, catastrophic consequences threaten reality.
- **The Void**: A dimension of horror where entities that should not exist lurk, waiting to cross over.

### 1.3 The Six Factions

| Faction | Members | Philosophy | Role |
|---------|----------|-----------|-----|
| **Circle of Mist** | 10,599 | Alchemy, mana, forbidden knowledge | Maintain arcane nodes that regulate magical flow |
| **Order of Dawn** | 6,341 | Clerics and paladins of the Core | Guardians of light, protectors of civilization |
| **Shadow Guild** | 6,234 | Information, silence, sanctioned crime | Covert operations, intelligence gathering |
| **Forge Legion** | 4,538 | Strength, steel, oaths | Warriors, blacksmiths, military strategists |
| **Void Echoes** | 4,302 | Necromancy, spectrals, death rights | Void specialists, seal dimensional breaches |
| **Horizon Watch** | 2,986 | Explorers, sentinels of the edge | Scouts and cartographers at the edge of civilization |

### 1.4 Races and Classes

**Available Races**: Gith, Human, Tiefling, Draconid, Elf, Dwarf, Triton, Goliath

**Available Classes**: Hunter, Druid, Cleric, Explorer, Bard, Rogue, Paladin

---

## 2. GAME MECHANICS

### 2.1 Mission System

Heroes complete **missions** that consume time and energy in exchange for rewards.

#### Mission Types by Difficulty

| Difficulty | Duration | XP | Aura | $EMBER | Success Rate | Death | Energy |
|------------|----------|----|----- |--------|------------|--------|---------|
| **EASY** | 3 hours | 60 | 4 | 10-25 | 92% | 0% | 10 |
| **MEDIUM** | 6 hours | 150 | 10 | 30-75 | 78% | 0.5% | 18 |
| **HARD** | 12 hours | 350 | 25 | 80-200 | 60% | 2.0% | 25 |
| **PARTY** | Variable | +20% | +20% | +20% | Variable | Variable | Variable |

> **Party Missions**: Require 5 heroes and grant a **1.2x multiplier** on ALL rewards.

### 2.2 Mission Outcomes

| Outcome | XP | Aura | $EMBER | Consequence |
|-----------|----|----- |--------|--------------|
| **SUCCESS** | 100% | 100% | 100% | Full rewards + drop chance |
| **FAILURE** | -25 to -60 | 0 | 0 | Loses XP based on difficulty |
| **DEATH** | -100% | -100% | -100% | Hero enters FALLEN state |

### 2.3 Success Rate Calculation

The base success rate is modified by several factors:

```
Final Rate = min(98%, Base Rate + Bonuses)
```

**Applicable Bonuses:**

| Factor | Bonus |
|--------|-------|
| Guild matches | +12% |
| Class matches | +8% |
| Race matches | +5% |
| Per 10 levels | +1% |
| Per 100 Aura | +1% |
| Equipment attack bonus | Direct |
| Ember Roll buffs | Variable |

> **Perfect Alignment**: If guild, class AND race all match = **1.5x multiplier** on rewards.

### 2.4 Progression System

#### Hero Attributes

| Attribute | Description | Range |
|----------|-------------|-------|
| `xp_total` | Total accumulated XP | 0 - ∞ |
| `level` | Level = 1 + (XP / 1000) | 1 - ∞ |
| `aura_level` | Total accumulated Aura | 0 - ∞ |
| `energy_current` | Available energy | 0 - 100 |
| `state` | Current state | READY / ON_MISSION / FALLEN |

#### Passive Generation (every 24 hours)

- **+5 XP** per day per hero
- **+1 Aura** per day per hero

#### Energy Regeneration

- Full recovery every **48 hours**
- Initial energy: **100 points**

### 2.5 Death and Resurrection System

#### Death Protection

Heroes gain protection based on their progress:

**By Level:**
| Level | Protection |
|-------|------------|
| 10+ | +5% |
| 30+ | +15% |
| 50+ | +30% |

**By Aura:**
| Aura | Protection |
|------|------------|
| 100+ | +5% |
| 250+ | +10% |
| 500+ | +20% |

- **Maximum from level/aura**: 50%
- **Equipment can add**: up to 30%
- **Maximum total protection**: 80%

#### Resurrection Costs with $EMBER

| Death # | $EMBER Cost | Description |
|----------|--------------|-------------|
| 1st | **200 EMBER** | "Death is merciful. The ritual is simple." |
| 2nd | **500 EMBER** | "Takes its toll. The spirits demand more." |
| 3rd | **1,000 EMBER** | "Is severe. Your soul weakens with each return." |
| 4th | **2,500 EMBER** | "The veil resists releasing you." |
| 5th | **5,000 EMBER** | "The forces beyond claim you." |
| 6th+ | **10,000 EMBER** | "Maximum price. Your existence hangs by a thread." |

**Post-resurrection state:**
- XP resets to **100**
- Aura resets to **20**
- Energy at **50%**

---

## 3. NFTs WITH DYNAMIC METADATA

### 3.1 Metadata Architecture

Emberholm NFTs are **dynamic**: their metadata changes in real time based on player actions.

#### Fixed Profile (Immutable)

This data is set at mint and **NEVER changes**:

```json
{
  "token_id": "00001",
  "name": "Entara, Bearer of Economy",
  "race": "Gith",
  "class": "Druid",
  "rarity": "Rare",
  "age": 127,
  "starting_guild": "Circle of Mist",
  "base_stats": {
    "str": 11, "dex": 12, "con": 12,
    "int": 15, "wis": 15, "cha": 11
  }
}
```

#### Dynamic State (Updated in Real Time)

This data changes with each action:

```json
{
  "dynamic_state": {
    "current_guild": "Circle of Mist",
    "xp_total": 2500,
    "xp_level": 3,
    "aura_level": 150,
    "energy_current": 80,
    "energy_max": 100,
    "power_current": 18,
    "state": "READY",
    "death_count": 0,
    "total_missions_completed": 25,
    "last_mission": "Echoes of the Deep",
    "mission_history": {
      "forest_patrol": "2026-01-20T10:00:00Z"
    },
    "ember_roll_buff": {
      "success_bonus": 15,
      "xp_bonus": 10,
      "expires": "2026-01-24T12:00:00Z"
    },
    "equipped_items": {
      "weapon_id": "W-0042",
      "armor_id": "A-0015",
      "helmet_id": null,
      "accessory_id": "AC-0003",
      "amulet_id": null,
      "rune_ids": ["R-0001", "R-0008"]
    },
    "achievements": ["first_mission", "10_missions", "reach_level_10"]
  }
}
```

### 3.2 When Metadata Updates

| Event | Metadata Changes |
|--------|---------------------|
| Complete mission | XP, Aura, missions_completed, last_mission |
| Die | state → FALLEN, death_count++ |
| Resurrect | state → READY, XP/Aura reset, energy 50% |
| Equip item | equipped_items updated |
| Ember Roll | ember_roll_buff with expiration |
| Change guild | current_guild updated |
| Earn achievement | achievements[] updated |

### 3.3 Marketplace Visualization

Dynamic metadata is automatically reflected on OpenSea and other marketplaces via the `/api/metadata/<token_id>` endpoint, showing:

- Hero's current level
- Accumulated aura
- Completed missions
- Unlocked achievements
- State (READY/ON_MISSION/FALLEN)

---

## 4. ITEMS AND RUNES SYSTEM

### 4.1 Equipment Types

| Type | Base Stats | Main Effect |
|------|------------|------------------|
| **WEAPON** | +10 attack, +5 XP boost | Increases success rate |
| **ARMOR** | +10 defense, +5 energy_regen | Protection and regeneration |
| **HELMET** | +5 defense, +5 aura_boost | Aura boost |
| **ACCESSORY** | +5 luck, +5 ember_boost | More $EMBER |
| **AMULET** | +10 aura_boost, +5 xp_boost | Double boost |
| **RUNE** | +5 all_boost | Affects ALL stats |

### 4.2 Rarities and Multipliers

| Rarity | Base Multiplier | Color |
|--------|-------------------|-------|
| Common | 1x | Gray |
| Uncommon | 1.5x | Green |
| Rare | 2x | Blue |
| Epic | 4x | Purple |
| Legendary | 8x | Gold |

### 4.3 Bonuses by Rarity

#### Items

| Rarity | $EMBER% | XP% | Energy% | Death% | Speed% |
|--------|---------|-----|----------|---------|------------|
| Common | +3% | +2% | 0% | 0% | 0% |
| Uncommon | +5% | +4% | -2% | 0% | 0% |
| Rare | +8% | +6% | -3% | -2% | 0% |
| Epic | +12% | +10% | -5% | -4% | +3% |
| Legendary | +18% | +15% | -8% | -6% | +5% |

#### Runes (More Balanced)

| Rarity | $EMBER% | XP% | Energy% | Death% | Speed% |
|--------|---------|-----|----------|---------|------------|
| Common | +3% | +3% | -2% | -2% | +2% |
| Uncommon | +5% | +5% | -3% | -3% | +3% |
| Rare | +8% | +8% | -5% | -5% | +5% |
| Epic | +12% | +12% | -8% | -8% | +8% |
| Legendary | +18% | +18% | -12% | -12% | +12% |

### 4.4 Legendary Items (Examples)

**Weapons:**
- Ashbringer, Staff of the Void, Soulreaver, Bow of the Phoenix

**Armor:**
- Armor of the Last Ember, Robes of Eternity, Voidwalker Cloak, Phoenix Plate

**Accessories:**
- Ring of the Last Ember, Void Pendant, Phoenix Charm

**Runes:**
- Rune of the Last Ember, Rune of Eternity, Rune of the Phoenix

### 4.5 How Equipment Affects Gameplay

| Stat | Gameplay Effect |
|------|-------------------|
| Attack Bonus | Added directly to success rate |
| XP Boost | `new_xp = xp × (100 + boost%) / 100` |
| Aura Boost | `new_aura = aura × (100 + boost%) / 100` |
| Energy Cost | Reduces mission energy consumption |
| Death Protection | Reduces effective death probability |
| Speed | Reduces mission duration |

---

## 5. DROP SYSTEM

### 5.1 Drop Probabilities by Difficulty

| Difficulty | Item Drop | Rune Drop |
|------------|-----------|-----------|
| **EASY** | 5% | 1% |
| **MEDIUM** | 10% | 3% |
| **HARD** | 20% | 8% |
| **PARTY** | 25% | 12% |

### 5.2 Rarity Distribution by Difficulty

#### When Obtaining an Item/Rune:

| Difficulty | Common | Rare | Epic | Legendary |
|------------|--------|------|------|-----------|
| **EASY** | 70% | 25% | 4% | 1% |
| **MEDIUM** | 50% | 35% | 12% | 3% |
| **HARD** | 30% | 40% | 23% | 7% |
| **PARTY** | 20% | 40% | 30% | 10% |

### 5.3 Combined Probability (Drop × Rarity)

**Example: Obtaining a Legendary Item**

| Difficulty | Calculation | Final Probability |
|------------|---------|-------------------|
| EASY | 5% × 1% | **0.05%** |
| MEDIUM | 10% × 3% | **0.30%** |
| HARD | 20% × 7% | **1.40%** |
| PARTY | 25% × 10% | **2.50%** |

> PARTY missions have **50 times** more probability of Legendary drop than EASY.

---

## 6. ECONOMY: $EMBER TOKEN

### 6.1 Ways to Earn $EMBER

#### Method 1: Mission Rewards

| Difficulty | Minimum $EMBER | Maximum $EMBER | Average |
|------------|---------------|---------------|----------|
| EASY | 10 | 25 | ~17 |
| MEDIUM | 30 | 75 | ~52 |
| HARD | 80 | 200 | ~140 |
| PARTY | +20% over base | +20% over base | Variable |

> With Legendary equipment (+18% EMBER): multiply rewards × 1.18

#### Method 2: Ember Roll (D20)

Dice system that allows earning $EMBER with risk/reward.

| Roll | Result | $EMBER | Success Bonus | XP Bonus | Duration |
|--------|-----------|--------|-------------|----------|----------|
| 1 | CRITICAL FAIL | **-100** | -20% | -10 | 24h |
| 2-5 | NOTHING | 0 | 0 | 0 | - |
| 6-8 | GRAZE | +50 | +5% | 0 | 12h |
| 9-11 | HIT | +100 | +10% | +5 | 24h |
| 12-14 | SOLID HIT | +200 | +15% | +10 | 24h |
| 15-17 | GREAT HIT | +350 | +20% | +15 | 24h |
| 18 | CRITICAL | +500 | +25% | +20 | 48h |
| 19 | SUPERIOR | +500 | +30% | +25 | 48h |
| **20** | **NATURAL 20** | **+1,000** | +35% | +30 | 72h |

**Ember Roll Rules:**
- Maximum **5 rolls per day**
- **1st roll**: FREE
- **2nd-5th rolls**: 75 $EMBER each
- Daily reset at 00:00 UTC

#### Method 3: NFT Staking (Planned Q3 2025)

| Mode | $EMBER/day per NFT |
|------|-------------------|
| No stake (in wallet) | 10 EMBER |
| Staked (locked) | 25 EMBER |
| Lock 30 days | 20 EMBER |
| Lock 90 days | 30 EMBER (+50%) |
| Lock 180 days | 45 EMBER (+125%) |
| Lock 365 days | 70 EMBER (+250%) |

### 6.2 Ember Roll Expected Value

**Probabilities (D20):**
```
P(1)     = 5%  → -100 $EMBER
P(2-5)   = 20% → 0 $EMBER
P(6-8)   = 15% → +50 $EMBER
P(9-11)  = 15% → +100 $EMBER
P(12-14) = 15% → +200 $EMBER
P(15-17) = 15% → +350 $EMBER
P(18)    = 5%  → +500 $EMBER
P(19)    = 5%  → +500 $EMBER
P(20)    = 5%  → +1,000 $EMBER

EV = +200 $EMBER per roll
```

> The system has a **positive expected value** of +200 $EMBER per roll.

### 6.3 Uses for $EMBER

| Use | $EMBER Cost |
|-----|-------------|
| **Recharge +25 Energy** | 30 |
| **Recharge +50 Energy** | 75 |
| **Recharge +100 Energy** | 150 |
| **Additional Ember Roll** | 75 |
| **Resurrection (1st death)** | 200 |
| **Resurrection (6th+ death)** | 10,000 |
| **Convert to $ASH** | 1,000 = 1 ASH |

### 6.4 $EMBER Token Distribution

**Total Supply: 100,000,000 EMBER**

| Allocation | Amount | Percentage | Vesting |
|------------|----------|------------|---------|
| **Staking Rewards** | 40,000,000 | 40% | 4 years |
| **Team & Development** | 20,000,000 | 20% | 2 years (linear) |
| **Liquidity Pools** | 15,000,000 | 15% | Immediate |
| **Marketing & Partnerships** | 10,000,000 | 10% | As needed |
| **Treasury/DAO Reserve** | 10,000,000 | 10% | Governance |
| **Initial Airdrop** | 5,000,000 | 5% | At launch |

### 6.5 Annual Emissions (Staking)

```
Year 1: 15,000,000 EMBER (~41,000/day)
Year 2: 12,000,000 EMBER (~33,000/day)
Year 3:  8,000,000 EMBER (~22,000/day)
Year 4:  5,000,000 EMBER (~14,000/day)
─────────────────────────────────────
Total:  40,000,000 EMBER (4 years)
```

### 6.6 Deflationary Mechanisms

| Mechanism | Description | % Burned |
|-----------|-------------|-----------|
| Crafting Burns | Each craft burns EMBER | 100% |
| Upgrade Burns | Guild/item upgrades | 100% |
| Marketplace Fees | Fee on each trade | 2% |
| Resurrections | EMBER spent on reviving | 100% |

> **5-year projection**: Supply could reduce to 80-85M EMBER.

### 6.7 Team Vesting

| Milestone | Percentage Released |
|------|---------------------|
| TGE (launch) | 0% |
| 6 months | 25% |
| 12 months | 50% |
| 18 months | 75% |
| 24 months | 100% |

---

## 7. $ASH TOKEN - GOVERNANCE

### 7.1 Concept

**$ASH** is Emberholm's premium governance token, obtained by burning $EMBER.

### 7.2 Acquisition

```
1,000 $EMBER = 1 $ASH (permanent burn)
```

- Minimum to convert: 100 EMBER (produces 0.1 ASH)
- No maximum conversion limit
- Irreversible process (EMBER is burned)

### 7.3 $ASH Utilities

| Utility | Description |
|----------|-------------|
| **DAO Governance** | 1 staked ASH = 1 vote |
| **Proposals** | Create change proposals |
| **Community Decisions** | Vote on: new missions, reward balance, treasury distribution, partnerships |
| **Premium Access** | Exclusive features (future) |
| **Treasury Management** | Participation in treasury decisions |

### 7.4 Voting Power

```
Voting Power = Staked ASH × time multiplier

Multipliers:
- 1 month stake:   1.0x
- 3 months stake: 1.25x
- 6 months stake: 1.5x
- 12 months stake: 2.0x
```

### 7.5 Current Status

> **NOTE**: The ASH protocol is currently **DISABLED** (ASH_PROTOCOL_ENABLED = False) during the beta phase. It will be activated in a future update.

---

## 8. RANKINGS SYSTEM

### 8.1 Guild Ranking

The 6 guilds compete for supremacy based on their members' collective performance.

**Ranking Metrics:**

| Metric | Description | Weight |
|---------|-------------|------|
| **Total XP** | Sum of XP from all active members | Primary |
| **Total Aura** | Sum of Aura from all members | Secondary |
| **Success Rate** | % of successful missions | Tertiary |
| **Active Members** | Players with recent activity | Bonus |

**Current Classification:**

| Position | Guild | Members | Philosophy |
|----------|-------|----------|-----------|
| 1 | Circle of Mist | 10,599 | Arcane knowledge |
| 2 | Order of Dawn | 6,341 | Sacred protection |
| 3 | Shadow Guild | 6,234 | Information and stealth |
| 4 | Forge Legion | 4,538 | Military strength |
| 5 | Void Echoes | 4,302 | Dark arts |
| 6 | Horizon Watch | 2,986 | Exploration |

### 8.2 Player Leaderboard

**Individual Metrics:**

| Metric | Description |
|---------|-------------|
| XP Total (All Heroes) | Sum of XP from all player's heroes |
| Aura Total (All Heroes) | Sum of Aura from all heroes |
| Heroes Count | Number of NFTs owned |
| Missions Completed | Total completed missions |

**Titles by Rank:**

| Total XP | Title |
|----------|--------|
| 0 - 999 | Initiate |
| 1,000 - 4,999 | Apprentice |
| 5,000 - 14,999 | Journeyman |
| 15,000 - 49,999 | Expert |
| 50,000 - 149,999 | Master |
| 150,000+ | Grandmaster |

### 8.3 Individual Level Calculation

```
Level = 1 + (Total XP ÷ 1,000)
```

| XP | Level |
|----|-------|
| 0-999 | 1 |
| 1,000-1,999 | 2 |
| 2,000-2,999 | 3 |
| 10,000-10,999 | 11 |
| 50,000-50,999 | 51 |

### 8.4 NFT Rank System (Emissary Rank)

Each individual NFT has a **rank** that determines reward bonuses.

#### Ranks and Requirements

| Rank | Tier | Required XP | Required Aura | Missions | $EMBER Bonus |
|-------|------|--------------|-----------|----------|--------------|
| **Novice** | Tier 1 | 0 | 0 | 0 | +2% |
| **Apprentice** | Tier 2 | 1,000 | 50 | 5 | +5% |
| **Journeyman** | Tier 3 | 5,000 | 150 | 15 | +10% |
| **Adept** | Tier 4 | 15,000 | 400 | 35 | +15% |
| **Expert** | Tier 5 | 35,000 | 800 | 60 | +22% |
| **Master** | Tier 6 | 70,000 | 1,500 | 100 | +30% |
| **Grandmaster** | Tier 7 | 120,000 | 3,000 | 150 | +40% |
| **Legendary** | Tier 8 | 200,000 | 5,000 | 250 | +50% |

> To rank up, you must meet **ALL** requirements (XP + Aura + Missions).

#### Benefits by Rank

| Rank | $EMBER% | XP% | Success% | Death% | Description |
|-------|---------|-----|--------|---------|-------------|
| Novice | +2% | +0% | +0% | 0% | "Newcomer to the realm" |
| Apprentice | +5% | +2% | +1% | -1% | "Learning the ways" |
| Journeyman | +10% | +5% | +2% | -2% | "Experienced traveler" |
| Adept | +15% | +8% | +4% | -3% | "Mastered the basic arts" |
| Expert | +22% | +12% | +6% | -5% | "Recognized in the realm" |
| Master | +30% | +18% | +8% | -8% | "Master of their craft" |
| Grandmaster | +40% | +25% | +10% | -12% | "Living legend" |
| Legendary | +50% | +35% | +12% | -15% | "Immortalized in history" |

#### Rank Visualization

The rank appears in:
- **NFT Metadata**: Visible on OpenSea as a trait
- **Game Interface**: Next to the hero's name
- **Leaderboards**: As a progress indicator

#### Calculation Formula

```
function getEmissaryRank(xp, aura, missions):
    if xp >= 200000 AND aura >= 5000 AND missions >= 250:
        return "Legendary (Tier 8)"
    elif xp >= 120000 AND aura >= 3000 AND missions >= 150:
        return "Grandmaster (Tier 7)"
    elif xp >= 70000 AND aura >= 1500 AND missions >= 100:
        return "Master (Tier 6)"
    elif xp >= 35000 AND aura >= 800 AND missions >= 60:
        return "Expert (Tier 5)"
    elif xp >= 15000 AND aura >= 400 AND missions >= 35:
        return "Adept (Tier 4)"
    elif xp >= 5000 AND aura >= 150 AND missions >= 15:
        return "Journeyman (Tier 3)"
    elif xp >= 1000 AND aura >= 50 AND missions >= 5:
        return "Apprentice (Tier 2)"
    else:
        return "Novice (Tier 1)"
```

#### Estimated Time to Reach Ranks

| Rank | Estimated Time | Approx. Missions |
|-------|-----------------|-----------------|
| Novice → Apprentice | ~1 week | 5-10 |
| Apprentice → Journeyman | ~3 weeks | 15-25 |
| Journeyman → Adept | ~2 months | 35-50 |
| Adept → Expert | ~4 months | 60-80 |
| Expert → Master | ~8 months | 100-120 |
| Master → Grandmaster | ~1 year | 150-180 |
| Grandmaster → Legendary | ~2 years | 250+ |

> Times assume active daily play with medium-hard difficulty missions.

---

## 9. ACHIEVEMENTS SYSTEM

### 9.1 Available Achievements

| ID | Name | Requirement | Icon |
|----|--------|-----------|-------|
| `first_mission` | First Mission | Complete 1st mission | 🎯 |
| `10_missions` | Veteran Explorer | Complete 10 missions | ⚔️ |
| `50_missions` | Seasoned Warrior | Complete 50 missions | 🏆 |
| `100_missions` | Legendary Hero | Complete 100 missions | 👑 |
| `reach_level_10` | Level 10 Achieved | Reach level 10 | ⭐ |
| `reach_level_50` | Level 50 Achieved | Reach level 50 | 💫 |
| `guild_master` | Guild Master | Become guild leader | 🏅 |
| `dragon_slayer` | Dragon Slayer | Defeat legendary dragon | 🐉 |
| `void_walker` | Void Walker | Complete all Void Echoes missions | 🌌 |
| `forge_master` | Forge Master | Complete all Forge Legion missions | ⚒️ |

### 9.2 Achievement Mechanics

- **Auto-granted**: Unlock automatically when requirements are met
- **Storage**: Saved in `achievements.json` by token_id
- **Visibility**: Appear in NFT metadata on OpenSea
- **Progression**: Represent important hero milestones

### 9.3 Special Achievements

| Achievement | Difficulty | Special Requirement |
|-------------|------------|---------------------|
| Dragon Slayer | Very High | Complete "Dragons Crucible" on HARD |
| Void Walker | High | 5+ Void Echoes missions |
| Guild Master | Epic | Top 1 in your guild's ranking |
| Legendary Hero | Epic | 100 missions = ~1,200 hours of gameplay |

---

## 10. TECHNICAL INFRASTRUCTURE

### 10.1 General Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   HTML/JS   │  │   CSS       │  │   Web3 (ethers.js)  │  │
│  │  Vanilla    │  │  Hacknet    │  │   MetaMask          │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        BACKEND                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Flask     │  │  PostgreSQL │  │   API Endpoints     │  │
│  │   Python    │  │  Database   │  │   /api/*            │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      BLOCKCHAIN                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  Base       │  │  Smart      │  │   IPFS              │  │
│  │  Mainnet    │  │  Contracts  │  │   Metadata          │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 10.2 Smart Contracts (Base Mainnet)

| Contract | Address | Function |
|----------|-----------|---------|
| **EmberholmPortal** | `0x7AB2cf80FbfB8c89868b3dFa053729ecC86E39b3` | NFTs ERC721 (35,000) |
| **EmberToken** | `0xbA7723fBfb44C7712C0B78108ad873DcFd5Dd73b` | $EMBER Token ERC20 |
| **AshToken** | `0xD4eef3eadb1Cf1B2905AA4Cd1022b8cCCC739DAb` | $ASH Token ERC20 |
| **EmberRunes** | `0xDa2D1085053c3700645a13498293D17c1cc3f595` | Rune NFTs |
| **EmberItems** | `0xCE71702CE99Bc927216e64d57e4BD19254Ac28bA` | Item NFTs |

### 10.3 User Costs

#### Minting Cost

| Concept | Value |
|----------|-------|
| Price per NFT | 0.0011 ETH (~$2-3 USD) |
| Estimated gas | ~0.0002-0.0005 ETH |
| Max per transaction | 10 NFTs |
| Total supply | 35,000 NFTs |

#### Transaction Costs (Estimated on Base L2)

| Operation | Estimated Gas | Cost ~USD |
|-----------|--------------|------------|
| Mint 1 NFT | ~100,000 gas | ~$0.02-0.05 |
| Stake Token | ~50,000 gas | ~$0.01-0.02 |
| Claim Item/Rune | ~80,000 gas | ~$0.02-0.03 |
| Equip Item | ~60,000 gas | ~$0.01-0.02 |
| Revive hero | ~70,000 gas | ~$0.01-0.03 |

> Base L2 offers **~100x lower** costs than Ethereum mainnet.

### 10.4 PostgreSQL Database

#### Table Schema

**Table `nfts`** (35,000+ records)
```sql
CREATE TABLE nfts (
    token_id VARCHAR(5) PRIMARY KEY,
    owner_address VARCHAR(42),
    guild VARCHAR(50),
    dynamic_state JSONB,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
-- Indexes: owner_address, guild, state
```

**Table `active_missions`**
```sql
CREATE TABLE active_missions (
    id SERIAL PRIMARY KEY,
    wallet_address VARCHAR(42),
    hero_id VARCHAR(5),
    mission_id VARCHAR(10),
    start_time TIMESTAMP,
    duration_hours INTEGER
);
```

**Table `players`** (Session cache)
```sql
CREATE TABLE players (
    wallet_address VARCHAR(42) PRIMARY KEY,
    player_data JSONB,
    last_sync TIMESTAMP
);
```

**Table `global_stats`** (Singleton)
```sql
CREATE TABLE global_stats (
    id INTEGER PRIMARY KEY DEFAULT 1,
    total_missions_completed INTEGER,
    total_missions_failed INTEGER,
    total_xp_collected BIGINT,
    total_aura_collected BIGINT,
    total_deaths INTEGER
);
```

### 10.5 Data Persistence Flow

```
1. User connects wallet → Frontend calls tokensOfOwner()
2. Frontend sends POST /api/player/{wallet}
3. Backend syncs with PostgreSQL
4. Backend recalculates stats and rankings
5. User plays → dynamic_state is updated
6. Dynamic metadata available via /api/metadata/{id}
7. OpenSea and marketplaces see changes in real time
```

### 10.6 IPFS Storage

| Content | CID |
|-----------|-----|
| Items Metadata | `bafybeibs6mm5rghbpld7twbj35dbpryrfimmqkbnkev6ufs4kpbp343wfm` |
| Items Images | `bafybeiegbqf3ypcn7uukahdf275yrmxu2g4zt4xmmrfwguufppbhzs4yx4` |
| Runes Metadata | `bafybeiajq22kxgm764srr55wsiz4t65so5laxe2nmrryzgailzpmfes3nq` |
| Runes Images | `bafybeibmivzieas7beofrxspoqo5iughrzyvg3wgjibe626eqt37zg3sae` |

### 10.7 Complete Technology Stack

| Layer | Technology |
|------|------------|
| **Frontend** | HTML5, CSS3, Vanilla JavaScript |
| **UI Theme** | Hacknet-inspired terminal aesthetic |
| **Backend** | Python Flask |
| **Database** | PostgreSQL (Render) |
| **Blockchain** | Base Mainnet (L2) |
| **Smart Contracts** | Solidity 0.8.20 |
| **Wallet** | MetaMask |
| **Web3 Library** | ethers.js |
| **Hosting** | Render.com |
| **Storage** | IPFS (metadata and images) |

---

## 11. EXECUTIVE SUMMARY Q&A

### General Questions

**Q: What is Emberholm Portal?**
> A: A medieval fantasy play-to-earn RPG where 35,000 unique NFTs (Emissaries) complete missions to earn $EMBER tokens, progress, and determine the fate of a realm threatened by the Void.

**Q: How much does it cost to start playing?**
> A: Minting an Emissary costs 0.0011 ETH (~$2-3 USD) + minimal gas fees on Base (~$0.02-0.05).

**Q: How many NFTs exist?**
> A: 35,000 unique Emissaries with different races, classes, guilds, and statistics.

**Q: Do NFTs change over time?**
> A: Yes, they have **dynamic metadata**. XP, Aura, level, equipment, and achievements update in real time and are reflected on marketplaces like OpenSea.

### Gameplay Questions

**Q: How do missions work?**
> A: Heroes are sent on 3-12 hour missions. Upon completion, they earn XP, Aura, $EMBER, and have a chance to drop items/runes.

**Q: What happens if my hero dies?**
> A: The hero enters FALLEN state. You can resurrect them by paying $EMBER. The cost increases with each death (200 EMBER first time, up to 10,000 EMBER for 6th+).

**Q: What's the best difficulty for farming?**
> A: Depends on your goal:
> - **Legendary Items**: PARTY (2.5% probability)
> - **Safety**: EASY (0% death, 92% success)
> - **XP/$EMBER Balance**: MEDIUM (150 XP, 30-75 EMBER)
> - **Maximum $EMBER**: HARD (80-200 EMBER, 2% death)

**Q: How do I maximize rewards?**
> A: Align guild/class/race with the mission (1.5x multiplier), equip Legendary items (+18% EMBER), use Party missions (1.2x bonus), and do Ember Rolls (EV +200).

### Economic Questions

**Q: How do I earn $EMBER?**
> A: Three main ways:
> 1. **Missions**: 10-200 EMBER per mission depending on difficulty
> 2. **Ember Roll**: D20 system with EV +200 EMBER/roll
> 3. **Staking** (future): 10-70 EMBER/day per NFT based on lock period

**Q: What can I do with $EMBER?**
> A: Buy energy, do Ember Rolls, resurrect fallen heroes, and convert 1,000 EMBER to 1 $ASH.

**Q: What is $ASH?**
> A: The governance token. Obtained by burning $EMBER (1,000:1). Allows voting on DAO decisions.

**Q: Is there token inflation?**
> A: Controlled. 100M supply with decreasing emissions (40M over 4 years). Burn mechanisms in crafting, resurrections, and marketplace fees.

### Technical Questions

**Q: Where is my data stored?**
> A: Ownership on-chain (Base). Progress (XP, Aura) in PostgreSQL. Metadata and images on IPFS.

**Q: Are the NFTs truly dynamic?**
> A: Yes. Metadata updates in real time. Changes are visible on OpenSea and other marketplaces.

**Q: What blockchain does it use?**
> A: Base Mainnet (Ethereum L2). Fast and economical transactions (~$0.01-0.05).

**Q: Is it secure?**
> A: Yes. Standard ERC721 NFTs. During missions, tokens are staked to prevent transfers. Audited contract with 5% royalty.

### Items/Runes Questions

**Q: What's the difference between Items and Runes?**
> A: Items give specific bonuses by type (weapon = attack). Runes give balanced bonus to ALL stats.

**Q: How rare is getting a Legendary?**
> A: EASY: 0.05% | MEDIUM: 0.30% | HARD: 1.40% | PARTY: 2.50%

**Q: Are items on-chain?**
> A: Yes. EmberItems and EmberRunes contracts. Cryptographically signed claims.

### Ranking Questions

**Q: How do rankings work?**
> A: There's guild ranking (by total XP of members) and player leaderboard (by XP across all their heroes).

**Q: What benefits do achievements give?**
> A: Achievements appear in the NFT metadata and represent milestones. They're prestige markers visible on marketplaces.

### NFT Rank Questions

**Q: What is Emissary Rank?**
> A: Each NFT has an individual rank (Tier 1-8) based on its XP, Aura, and completed missions. Higher rank means greater bonuses.

**Q: How many ranks exist?**
> A: 8 ranks: Novice (Tier 1), Apprentice (Tier 2), Journeyman (Tier 3), Adept (Tier 4), Expert (Tier 5), Master (Tier 6), Grandmaster (Tier 7), Legendary (Tier 8).

**Q: What bonus does the maximum rank give?**
> A: Legendary (Tier 8) gives: +50% $EMBER, +35% XP, +12% success, -15% death. Requires 200,000 XP, 5,000 Aura, and 250 missions.

**Q: How long does it take to reach Legendary?**
> A: Approximately 2+ years of active play. It's the maximum achievable prestige.

**Q: Does rank affect NFT value?**
> A: Yes. An NFT with high rank has more value because it produces more $EMBER and has better mission performance. The rank is visible in metadata.

---

## APPENDIX: KEY FORMULAS

### Level
```
level = 1 + (xp_total ÷ 1,000)
```

### Success Rate
```
success_rate = min(98%, base_rate + bonuses)
```

### Alignment Multiplier
```
multiplier = 1.5x if (guild + class + race all match)
```

### Equipment Stats Application
```
final_stat = base_stat × (100 + bonus%) ÷ 100
```

### Death Mitigation
```
effective_death = base_death × (1 - total_protection%)
total_protection = min(80%, level + aura + equipment)
```

### Party Bonus
```
party_reward = base_reward × 1.2 (only on success)
```

### ASH Conversion
```
ASH = burned_EMBER ÷ 1,000
```

### Ember Roll Expected Value
```
EV = +200 $EMBER per free roll
EV_net = +125 $EMBER per paid roll (200 - 75 cost)
```

### NFT Rank Calculation (Emissary Rank)
```
Rank = max_tier where:
  - XP >= required_xp[tier]
  - Aura >= required_aura[tier]
  - Missions >= required_missions[tier]

Total Bonus = ember_bonus[tier] + xp_bonus[tier] + success_bonus[tier] - death_reduction[tier]
```

### Cumulative Total Bonus
```
Final_Bonus = (1 + Rank%) × (1 + Equipment%) × (1 + Runes%) × (1 + Alignment%)

Maximum Example:
= (1 + 0.50) × (1 + 0.90) × (1 + 0.30) × (1 + 0.50)
= 1.50 × 1.90 × 1.30 × 1.50
= 5.56x (456% bonus over base)
```

---

*Document generated for Emberholm Portal project presentation*
*Version 2.0 | January 2026*
