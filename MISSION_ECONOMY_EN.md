# MISSION ECONOMY SYSTEM
## Emberholm Portal - Detailed Report

---

## TABLE OF CONTENTS

1. [System Overview](#1-system-overview)
2. [Missions by Difficulty](#2-missions-by-difficulty)
3. [Success Rate Calculation](#3-success-rate-calculation)
4. [Rewards System](#4-rewards-system)
5. [Drop System (Items/Runes)](#5-drop-system-itemsrunes)
6. [Modifiers and Bonuses](#6-modifiers-and-bonuses)
7. [Expected Value Analysis](#7-expected-value-analysis)
8. [Optimal Strategies](#8-optimal-strategies)

---

## 1. SYSTEM OVERVIEW

### Mission Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MISSION CYCLE                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. START                                                            │
│     └── Energy consumed (10/18/25 based on difficulty)              │
│                                                                      │
│  2. DURATION                                                         │
│     └── Real time (3h/6h/12h based on difficulty)                   │
│                                                                      │
│  3. RESOLUTION                                                       │
│     ├── Success roll vs success rate                                │
│     └── If MEDIUM/HARD fails: Death roll                            │
│                                                                      │
│  4. OUTCOME                                                          │
│     ├── SUCCESS: +XP, +Aura, +$EMBER claimable, drop chance         │
│     ├── FAILURE: -XP (based on difficulty), no other rewards        │
│     └── DEATH: FALLEN state, requires resurrection                  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. MISSIONS BY DIFFICULTY

### Complete Comparison Table

| Attribute | EASY | MEDIUM | HARD | PARTY |
|-----------|------|--------|------|-------|
| **Duration** | 3 hours | 6 hours | 12 hours | Variable |
| **Energy** | 10 | 18 | 25 | Base x5 |
| **Base XP** | 60 | 150 | 350 | Base x1.2 |
| **Base Aura** | 4 | 10 | 25 | Base x1.2 |
| **$EMBER Range** | 10-25 | 30-75 | 80-200 | Base x1.2 |
| **Base Success Rate** | 92% | 78% | 60% | Variable |
| **Death Risk** | 0% | 0.5% | 2.0% | Based on base |
| **XP Lost (failure)** | -25 | -60 | -140 | Based on base |
| **Item Drop** | 5% | 10% | 20% | 25% |
| **Rune Drop** | 1% | 3% | 8% | 12% |

### Available Missions (Current Configuration)

#### EASY (3 missions)

| ID | Name | Favored Guild | Class | Race |
|----|------|---------------|-------|------|
| 001 | The Lost Forge | Forge Legion | Warrior | Orc |
| 002 | Circle Interference Node | Circle of Mist | Wizard | Human |
| 003 | Dawn Patrol (PARTY) | Order of Dawn | Paladin | Elf |

#### MEDIUM (3 missions)

| ID | Name | Favored Guild | Class | Race |
|----|------|---------------|-------|------|
| 004 | Shadow Infiltration | Shadow Guild | Rogue | Halfling |
| 005 | Horizon Survey | Horizon Watch | Ranger | Elf |
| 006 | Veil Breach Containment (PARTY) | Void Echoes | Necromancer | Undead |

#### HARD (3 missions)

| ID | Name | Favored Guild | Class | Race |
|----|------|---------------|-------|------|
| 007 | Dragons Crucible | Forge Legion | Warrior | Orc |
| 008 | Void Descent | Void Echoes | Necromancer | Undead |
| 009 | Eclipse Ritual (PARTY) | Circle of Mist | Wizard | Human |

---

## 3. SUCCESS RATE CALCULATION

### Main Formula

```
Final Rate = min(98%, Base Rate + Bonuses)
```

> **Note**: Success rate caps at 98%. There's always a 2% chance of failure.

### Applicable Bonuses

| Factor | Bonus | Condition |
|--------|-------|-----------|
| **Guild Match** | +12% | Hero's guild = Mission's favored guild |
| **Class Match** | +8% | Hero's class = Mission's favored class |
| **Race Match** | +5% | Hero's race = Mission's favored race |
| **Level** | +1% per 10 levels | Calculated from total XP |
| **Aura** | +1% per 100 Aura | Hero's accumulated aura |
| **Equipment** | Variable | Attack bonus from equipped items |
| **Ember Roll Buff** | Variable | If active buff from Ember Roll |

### Calculation Example

```
Mission: Dragons Crucible (HARD)
Base Rate: 60%

Hero:
- Guild: Forge Legion (MATCH) → +12%
- Class: Warrior (MATCH) → +8%
- Race: Orc (MATCH) → +5%
- Level: 35 (35 ÷ 10 = 3) → +3%
- Aura: 250 (250 ÷ 100 = 2) → +2%
- Equipment: Attack +5 → +5%

Calculation:
60% + 12% + 8% + 5% + 3% + 2% + 5% = 95%

Final Rate: 95% (below the 98% cap)
```

### Perfect Alignment

When **Guild + Class + Race** match the mission:

- **Reward multiplier: 1.5x**
- Applies to: XP, Aura, and $EMBER

```
Example with Perfect Alignment:
- Base XP: 350 → 350 x 1.5 = 525 XP
- Base Aura: 25 → 25 x 1.5 = 37 Aura
- Base $EMBER: 140 → 140 x 1.5 = 210 $EMBER
```

---

## 4. REWARDS SYSTEM

### XP and Aura

| Difficulty | XP Success | Aura Success | XP Failure |
|------------|------------|--------------|------------|
| EASY | 60 | 4 | -25 |
| MEDIUM | 150 | 10 | -60 |
| HARD | 350 | 25 | -140 |

### $EMBER per Mission

$EMBER rewards are calculated with variability:

| Difficulty | Minimum | Maximum | Average |
|------------|---------|---------|---------|
| EASY | 10 | 25 | ~17.5 |
| MEDIUM | 30 | 75 | ~52.5 |
| HARD | 80 | 200 | ~140 |

### Bonuses Affecting $EMBER

| Source | Maximum Bonus |
|--------|---------------|
| Perfect Alignment | +50% (x1.5) |
| Legendary Equipment | +18% per piece |
| Legendary Runes | +18% per rune |
| Rank (Legendary Tier 8) | +50% |
| Party Mission | +20% |

### Theoretical Maximum $EMBER Calculation

```
HARD Base: 200 $EMBER
+ Perfect Alignment (x1.5): 300
+ Legendary Weapon (+18%): 354
+ Legendary Armor (+18%): 417
+ Legendary Helmet (+18%): 492
+ Legendary Accessory (+18%): 580
+ Legendary Amulet (+18%): 685
+ 2x Legendary Runes (+36%): 931
+ Legendary Rank (+50%): 1,396
+ Party Bonus (+20%): 1,676 $EMBER

THEORETICAL MAXIMUM PER MISSION: ~1,676 $EMBER
(Requires: Perfect alignment, full legendary gear, Rank 8, Party mission)
```

---

## 5. DROP SYSTEM (ITEMS/RUNES)

### Drop Probabilities

| Difficulty | Item Drop | Rune Drop |
|------------|-----------|-----------|
| EASY | 5% | 1% |
| MEDIUM | 10% | 3% |
| HARD | 20% | 8% |
| PARTY | 25% | 12% |

### Rarity Distribution (when drop occurs)

| Difficulty | Common | Rare | Epic | Legendary |
|------------|--------|------|------|-----------|
| EASY | 70% | 25% | 4% | 1% |
| MEDIUM | 50% | 35% | 12% | 3% |
| HARD | 30% | 40% | 23% | 7% |
| PARTY | 20% | 40% | 30% | 10% |

### Combined Probability (Drop x Rarity)

**Getting a Legendary Item:**

| Difficulty | Calculation | Probability |
|------------|-------------|-------------|
| EASY | 5% x 1% | **0.05%** |
| MEDIUM | 10% x 3% | **0.30%** |
| HARD | 20% x 7% | **1.40%** |
| PARTY | 25% x 10% | **2.50%** |

**Getting a Legendary Rune:**

| Difficulty | Calculation | Probability |
|------------|-------------|-------------|
| EASY | 1% x 1% | **0.01%** |
| MEDIUM | 3% x 3% | **0.09%** |
| HARD | 8% x 7% | **0.56%** |
| PARTY | 12% x 10% | **1.20%** |

---

## 6. MODIFIERS AND BONUSES

### Equipment Bonuses by Rarity

#### Items

| Rarity | $EMBER% | XP% | Energy% | Death% | Speed% |
|--------|---------|-----|---------|--------|--------|
| Common | +3% | +2% | 0% | 0% | 0% |
| Uncommon | +5% | +4% | -2% | 0% | 0% |
| Rare | +8% | +6% | -3% | -2% | 0% |
| Epic | +12% | +10% | -5% | -4% | +3% |
| Legendary | +18% | +15% | -8% | -6% | +5% |

#### Runes (Balanced)

| Rarity | $EMBER% | XP% | Energy% | Death% | Speed% |
|--------|---------|-----|---------|--------|--------|
| Common | +3% | +3% | -2% | -2% | +2% |
| Uncommon | +5% | +5% | -3% | -3% | +3% |
| Rare | +8% | +8% | -5% | -5% | +5% |
| Epic | +12% | +12% | -8% | -8% | +8% |
| Legendary | +18% | +18% | -12% | -12% | +12% |

### Rank Bonuses (Emissary Rank)

| Rank | Tier | $EMBER% | XP% | Success% | Death% |
|------|------|---------|-----|----------|--------|
| Novice | 1 | +2% | +0% | +0% | 0% |
| Apprentice | 2 | +5% | +2% | +1% | -1% |
| Journeyman | 3 | +10% | +5% | +2% | -2% |
| Adept | 4 | +15% | +8% | +4% | -3% |
| Expert | 5 | +22% | +12% | +6% | -5% |
| Master | 6 | +30% | +18% | +8% | -8% |
| Grandmaster | 7 | +40% | +25% | +10% | -12% |
| Legendary | 8 | +50% | +35% | +12% | -15% |

---

## 7. EXPECTED VALUE ANALYSIS

### Expected Value per Mission (No Bonuses)

```
EV = (Prob_Success x Reward_Success) + (Prob_Failure x Penalty_Failure)
```

#### EASY

```
Success Rate: 92%
Failure Rate: 8%
Death: 0%

EV_XP = (0.92 x 60) + (0.08 x -25) = 55.2 - 2 = 53.2 XP
EV_Aura = 0.92 x 4 = 3.68 Aura
EV_EMBER = 0.92 x 17.5 = 16.1 $EMBER

Per hour: 53.2/3 = 17.7 XP/h, 5.37 $EMBER/h
```

#### MEDIUM

```
Success Rate: 78%
Failure Rate: 21.5% (22% - 0.5% death)
Death: 0.5%

EV_XP = (0.78 x 150) + (0.215 x -60) = 117 - 12.9 = 104.1 XP
EV_Aura = 0.78 x 10 = 7.8 Aura
EV_EMBER = 0.78 x 52.5 = 40.95 $EMBER

Per hour: 104.1/6 = 17.35 XP/h, 6.83 $EMBER/h
```

#### HARD

```
Success Rate: 60%
Failure Rate: 38% (40% - 2% death)
Death: 2%

EV_XP = (0.60 x 350) + (0.38 x -140) = 210 - 53.2 = 156.8 XP
EV_Aura = 0.60 x 25 = 15 Aura
EV_EMBER = 0.60 x 140 = 84 $EMBER

Per hour: 156.8/12 = 13.07 XP/h, 7 $EMBER/h
```

### Efficiency Summary Table

| Difficulty | XP/hour | Aura/hour | $EMBER/hour | Risk |
|------------|---------|-----------|-------------|------|
| EASY | **17.7** | 1.23 | 5.37 | 0% |
| MEDIUM | 17.35 | 1.30 | 6.83 | 0.5% |
| HARD | 13.07 | **1.25** | **7.00** | 2% |

### Analysis by Objective

| Objective | Best Option | Reason |
|-----------|-------------|--------|
| **Maximum XP/hour** | EASY | 17.7 XP/h, no risk |
| **Maximum $EMBER/hour** | HARD | 7 $EMBER/h |
| **Maximum Legendary Items** | PARTY HARD | 2.5% probability |
| **No death risk** | EASY | 0% death |
| **Risk/reward balance** | MEDIUM | Moderate risk, good rewards |

---

## 8. OPTIMAL STRATEGIES

### For New Players (Level 1-10)

```
Recommendation: EASY exclusively
- No death risk
- Build base XP and Aura
- Learn game mechanics
- Get first items (even if Common)

Goal: Reach Apprentice Rank (Tier 2)
Requirements: 1,000 XP, 50 Aura, 5 missions
Estimated time: ~1 week
```

### For Intermediate Players (Level 10-30)

```
Recommendation: Mix of EASY + MEDIUM
- Alternate based on available energy
- Use MEDIUM when you have Perfect Alignment
- EASY for safe grinding
- Start equipping Rare/Epic items

Goal: Reach Journeyman Rank (Tier 3)
Requirements: 5,000 XP, 150 Aura, 15 missions
```

### For Advanced Players (Level 30+)

```
Recommendation: MEDIUM + HARD + PARTY
- HARD only with good equipment (death protection)
- PARTY to maximize Legendary drops
- Focus on Perfect Alignment whenever possible

Goal: Reach Master+ Rank (Tier 6+)
Priority: Farm Legendary items to reduce risk
```

### Maximize $EMBER

```
1. Equip ALL Legendary (if possible)
2. Look for missions with Perfect Alignment
3. Use Party Missions (+20% bonus)
4. Rank up (up to +50% at Tier 8)
5. Do daily Ember Roll (first roll free, EV +200)

Optimal Configuration:
- 6 Legendary equipment slots: +108% $EMBER
- 2 Legendary Runes: +36% $EMBER
- Legendary Rank: +50% $EMBER
- Perfect Alignment: +50% $EMBER
- Party Bonus: +20% $EMBER

Total Bonus: +264% over base
```

### Minimize Death Risk

```
Protection by Level:
- Level 10+: +5% protection
- Level 30+: +15% protection
- Level 50+: +30% protection

Protection by Aura:
- 100+ Aura: +5% protection
- 250+ Aura: +10% protection
- 500+ Aura: +20% protection

Protection by Equipment:
- Epic/Legendary items reduce death_chance
- Runes give -12% death (Legendary)

MAXIMUM: 80% total protection

With 80% protection on HARD (2% base):
Effective death = 2% x (1 - 0.80) = 0.4%
```

---

## KEY FORMULAS

### Success Rate
```
success_rate = min(98%, base_rate + guild_bonus + class_bonus + race_bonus + level_bonus + aura_bonus + equipment_bonus)
```

### XP Reward
```
xp_final = xp_base x alignment_multiplier x (1 + equipment_boost%) x (1 + rank_boost%)
```

### $EMBER Reward
```
ember_final = ember_base x alignment_multiplier x (1 + equipment_boost%) x (1 + rank_boost%) x party_multiplier
```

### Effective Death Probability
```
death_effective = death_base x (1 - protection_total)
protection_total = min(80%, level_protection + aura_protection + equipment_protection)
```

### Mission Expected Value
```
EV = (success_rate x reward) + ((1 - success_rate - death_rate) x penalty) + (death_rate x death_cost)
```

---

*Mission Economy Document — Emberholm Portal*
*Based on missions_config.json and app.py*
*Version 1.0 | January 2026*
