# EMBERHOLM PORTAL

### A Medieval Fantasy RPG with Dynamic NFTs on Base

---

<div align="center">

**35,000 Emissaries** | **Dual Economy** | **Zero Gas Missions** | **Dynamic Metadata**

*The realm is dying. The Emissaries are its last hope.*

</div>

---

## TABLE OF CONTENTS

1. [Executive Summary](#1-executive-summary)
2. [The World of Emberholm](#2-the-world-of-emberholm)
3. [How the Game Works](#3-how-the-game-works)
4. [What Makes Us Different](#4-what-makes-us-different)
5. [Technical Architecture](#5-technical-architecture)
6. [Dual Economy: $EMBER and $ASH](#6-dual-economy-ember-and-ash)
7. [5 Smart Contracts on Base](#7-5-smart-contracts-on-base)
8. [Roadmap](#8-roadmap)
9. [About Development](#9-about-development)
10. [Frequently Asked Questions](#10-frequently-asked-questions)

---

## 1. EXECUTIVE SUMMARY

### What is Emberholm Portal?

**Emberholm Portal** is a medieval fantasy RPG where you control **Emissaries** — unique NFT warriors who complete missions, earn tokens, and determine the fate of a kingdom on the brink of extinction.

### In 30 Seconds

> *Mint an Emissary. Send them on missions. Earn $EMBER. Rise in rank. Equip legendary items. Conquer lands. But beware — death can be permanent.*

### Key Features

| Feature | Description |
|---------|-------------|
| **35,000 Unique NFTs** | Each Emissary has unique race, class, guild, and stats |
| **Dynamic Metadata** | Your NFT evolves — XP, level, achievements visible on OpenSea |
| **Zero Gas Missions** | Play without constant transaction fees |
| **Dual Economy** | $EMBER (utility) + $ASH (governance) |
| **On-Chain Items** | Weapons, armor, and runes as equippable NFTs |
| **11 Progression Ranks** | From Novice to Legendary — each rank grants more power |
| **Permanent Death** | Real risk, decisions that matter |

---

## 2. THE WORLD OF EMBERHOLM

### The Story

At the heart of the realm burns **The Eternal Flame** — sacred fire that keeps reality stable. But the flame is dying.

**The Veil** — the barrier separating our world from the **Void** — is tearing. Entities that should not exist are beginning to seep through.

The **Emissaries** are the last line of defense. Warriors, mages, rogues, and explorers who risk their lives on dangerous missions to gather resources, defend borders, and find a way to rekindle the flame.

### The Six Factions

```
┌─────────────────────────────────────────────────────────────────┐
│                   THE SIX GUILDS OF EMBERHOLM                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ⚗️  CIRCLE OF MIST     │  Alchemists and mages of forbidden    │
│      10,599 members     │  knowledge. Control magical flow       │
│                                                                  │
│  ☀️  ORDER OF DAWN      │  Paladins and clerics of light.       │
│      6,341 members      │  Protectors of civilization            │
│                                                                  │
│  🗡️  SHADOW GUILD       │  Spies and assassins. Information     │
│      6,234 members      │  is power, silence is survival         │
│                                                                  │
│  ⚒️  FORGE LEGION       │  Warriors and blacksmiths. Steel,     │
│      4,538 members      │  strength, and honor in battle         │
│                                                                  │
│  🌀  VOID ECHOES        │  Necromancers and spectrals.          │
│      4,302 members      │  Specialists in sealing the Void       │
│                                                                  │
│  🔭  HORIZON WATCH      │  Explorers and frontier scouts.       │
│      2,986 members      │  Cartographers of the unknown          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Races and Classes

**8 Races**: Human, Elf, Dwarf, Tiefling, Draconid, Gith, Triton, Goliath

**7 Classes**: Paladin, Cleric, Druid, Hunter, Rogue, Bard, Explorer

> Each combination of race + class + guild creates a unique Emissary with specific strengths for certain missions.

---

## 3. HOW THE GAME WORKS

### The Main Loop

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│    MINT      │────▶│   MISSIONS   │────▶│   PROGRESS   │
│  Emissary    │     │  3h / 6h /12h│     │  XP + Aura   │
└──────────────┘     └──────────────┘     └──────────────┘
                            │                    │
                            ▼                    ▼
                     ┌──────────────┐     ┌──────────────┐
                     │    EARN      │     │    EQUIP     │
                     │   $EMBER     │     │    Items     │
                     └──────────────┘     └──────────────┘
                            │                    │
                            └────────┬───────────┘
                                     ▼
                            ┌──────────────┐
                            │   RANK UP    │
                            │              │
                            └──────────────┘
```

### Mission System

| Difficulty | Duration | XP | $EMBER | Death Risk |
|------------|----------|-----|--------|------------|
| **EASY** | 3 hours | 60 | 10-25 | 0% |
| **MEDIUM** | 6 hours | 150 | 30-75 | 0.5% |
| **HARD** | 12 hours | 350 | 80-200 | 2% |
| **PARTY** | Variable | +20% | +20% | Variable |

> **Party Missions**: Require 5 Emissaries and grant 20% bonus on all rewards.

### Rank System (Emissary Rank)

Your Emissary ranks up based on progress. Each rank unlocks bonuses:

| Rank | Tier | Requirements | $EMBER Bonus |
|------|------|--------------|--------------|
| Novice | 1 | Starting | +2% |
| Apprentice | 2 | 1,000 XP, 50 Aura | +5% |
| Journeyman | 3 | 5,000 XP, 150 Aura | +10% |
| Adept | 4 | 15,000 XP, 400 Aura | +15% |
| Expert | 5 | 35,000 XP, 800 Aura | +22% |
| Master | 6 | 70,000 XP, 1,500 Aura | +30% |
| Grandmaster | 7 | 120,000 XP, 3,000 Aura | +40% |
| **Legendary** | 8 | 200,000 XP, 5,000 Aura | **+50%** |

### Death System

Death in Emberholm has real consequences:

- **EASY Missions**: 0% death risk
- **MEDIUM Missions**: 0.5% risk
- **HARD Missions**: 2% risk

When an Emissary dies, they enter **FALLEN** state. You can resurrect them by paying $EMBER:

| Death # | Cost |
|---------|------|
| 1st | 200 EMBER |
| 2nd | 500 EMBER |
| 3rd | 1,000 EMBER |
| 4th | 2,500 EMBER |
| 5th | 5,000 EMBER |
| 6th+ | 10,000 EMBER |

> Death protection increases with level, aura, and equipment (maximum 80% protection).

---

## 4. WHAT MAKES US DIFFERENT

### Comparison with Other NFT Projects

| Feature | Emberholm Portal | Typical Projects |
|---------|------------------|------------------|
| **Metadata** | Dynamic (changes in real-time) | Static (never changes) |
| **Cost to play** | **$0 on missions** | Gas on every action |
| **Progression** | 11 ranks + achievements | Basic levels or none |
| **Economy** | Dual token (utility + governance) | Single token |
| **Consequences** | Permanent death | No real risk |
| **Items** | On-chain equippable NFTs | Off-chain or nonexistent |
| **Visualization** | Stats visible on marketplaces | Image only |

### The 3 Key Differentiators

#### 1. REAL-TIME DYNAMIC METADATA

Your NFT is not just an image — it's a living character that evolves.

```
When you complete a mission:
  ├── Your XP increases
  ├── Your level rises
  ├── Your achievements update
  ├── Your rank may change
  └── ALL of this is visible on OpenSea instantly
```

Anyone can see your Emissary's progress directly on marketplaces. A level 50 Emissary with Legendary gear is worth more than a level 1.

#### 2. ZERO GAS ON MISSIONS

The blockchain is the foundation, not the friction.

```
┌─────────────────────────────────────────────────────────────┐
│                         ON-CHAIN                             │
│  • NFT ownership (indisputable)                             │
│  • $EMBER and $ASH tokens                                   │
│  • Items and Runes as NFTs                                  │
│  • Reward claims                                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        OFF-CHAIN                             │
│  • Start/complete missions (NO GAS)                         │
│  • Progression (XP, Aura, rankings)                         │
│  • Temporary events                                         │
│  • Energy system                                            │
└─────────────────────────────────────────────────────────────┘
```

You can play for hours without spending a cent on gas. You only pay when claiming rewards or minting items — actions that truly require blockchain.

#### 3. ROBUST PERSISTENCE SYSTEM

Your data is secure and portable:

- **PostgreSQL database** for real-time progress
- **Metadata served via API** for marketplaces
- **Redundant backups** of all information
- **No data loss** if server restarts

---

## 5. TECHNICAL ARCHITECTURE

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                           USER                                   │
│                    (Browser + MetaMask)                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  HTML/CSS   │  │  Vanilla JS │  │  ethers.js (Web3)       │  │
│  │  Terminal   │  │  Zero deps  │  │  Wallet connection      │  │
│  │  Aesthetic  │  │             │  │                         │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌──────────────────────┐        ┌──────────────────────────────┐
│      BACKEND         │        │        BLOCKCHAIN            │
│  ┌────────────────┐  │        │  ┌────────────────────────┐  │
│  │  Flask/Python  │  │        │  │     BASE MAINNET       │  │
│  │  REST API      │  │        │  │     (Ethereum L2)      │  │
│  └────────────────┘  │        │  └────────────────────────┘  │
│  ┌────────────────┐  │        │  ┌────────────────────────┐  │
│  │  PostgreSQL    │  │        │  │   5 Smart Contracts    │  │
│  │  Persistence   │  │        │  │   ERC721 + ERC20       │  │
│  └────────────────┘  │        │  └────────────────────────┘  │
└──────────────────────┘        └──────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                          IPFS                                    │
│              Decentralized images and metadata                   │
└─────────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Frontend | HTML5 + CSS3 + Vanilla JS | Retro terminal UI |
| Web3 | ethers.js | Blockchain connection |
| Backend | Python Flask | REST API |
| Database | PostgreSQL | State persistence |
| Blockchain | Base Mainnet | Low-cost L2 |
| Contracts | Solidity 0.8.20 | NFTs and tokens |
| Storage | IPFS | Decentralized images |
| Hosting | Render.com | Automatic deployment |

### Why Base?

| Reason | Detail |
|--------|--------|
| **~100x lower costs** | $0.01-0.05 gas vs $5-50 on Ethereum |
| **Backed by Coinbase** | Security and institutional adoption |
| **EVM Compatibility** | Same code as Ethereum |
| **Ideal for Gaming** | Frequent microtransactions viable |
| **Growing Ecosystem** | More projects and users every day |

---

## 6. DUAL ECONOMY: $EMBER AND $ASH

### $EMBER — Utility Token

**Total Supply: 100,000,000 EMBER**

#### Ways to Earn

| Method | Amount |
|--------|--------|
| EASY Missions | 10-25 EMBER |
| MEDIUM Missions | 30-75 EMBER |
| HARD Missions | 80-200 EMBER |
| Ember Roll (D20) | -100 to +1,000 EMBER |
| Staking (future) | 10-70 EMBER/day |

#### Ways to Spend

| Use | Cost |
|-----|------|
| Energy recharge | 30-150 EMBER |
| Additional Ember Roll | 75 EMBER |
| Resurrection | 200-10,000 EMBER |
| Convert to $ASH | 1,000 EMBER = 1 ASH |

#### Distribution

```
┌─────────────────────────────────────────────────────────────┐
│                    $EMBER DISTRIBUTION                       │
├─────────────────────────────────────────────────────────────┤
│  ████████████████████░░░░░░░░░░░░░░░  40% Staking Rewards   │
│  ████████░░░░░░░░░░░░░░░░░░░░░░░░░░░  20% Team (2yr vest)   │
│  ██████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  15% Liquidity         │
│  ████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  10% Marketing         │
│  ████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  10% Treasury/DAO      │
│  ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   5% Airdrop           │
└─────────────────────────────────────────────────────────────┘
```

### $ASH — Governance Token

**Acquisition**: Burn 1,000 $EMBER = 1 $ASH

| Utility | Description |
|---------|-------------|
| DAO Voting | 1 ASH = 1 vote |
| Proposals | Create game changes |
| Treasury | Decide fund allocation |
| Premium Features | Early access (future) |

---

## 7. 5 SMART CONTRACTS ON BASE

Emberholm is not one contract — it's an **ecosystem of 5 interconnected contracts**:

```
┌─────────────────────────────────────────────────────────────────┐
│                    EMBERHOLM ECOSYSTEM                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │              EMBERHOLM PORTAL (ERC721)                   │   │
│   │              35,000 Emissary NFTs                        │   │
│   │              0x7AB2cf80FbfB8c89868b3dFa053729ecC86E39b3  │   │
│   └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│              ┌───────────────┼───────────────┐                   │
│              ▼               ▼               ▼                   │
│   ┌─────────────────┐ ┌─────────────┐ ┌─────────────────────┐   │
│   │  EMBER TOKEN    │ │  ASH TOKEN  │ │                     │   │
│   │  (ERC20)        │ │  (ERC20)    │ │   EQUIPPABLES       │   │
│   │  Utility        │ │  Governance │ │                     │   │
│   │  0xbA77...      │ │  0xD4ee...  │ │  ┌───────────────┐  │   │
│   └─────────────────┘ └─────────────┘ │  │ EMBER ITEMS   │  │   │
│                                       │  │ 0xCE71...     │  │   │
│                                       │  └───────────────┘  │   │
│                                       │  ┌───────────────┐  │   │
│                                       │  │ EMBER RUNES   │  │   │
│                                       │  │ 0xDa2D...     │  │   │
│                                       │  └───────────────┘  │   │
│                                       └─────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

| Contract | Type | Function |
|----------|------|----------|
| **EmberholmPortal** | ERC721 | 35,000 Emissary NFTs |
| **EmberToken** | ERC20 | $EMBER utility token |
| **AshToken** | ERC20 | $ASH governance token |
| **EmberItems** | ERC721 | Weapons, armor, accessories |
| **EmberRunes** | ERC721 | Magical equippable runes |

---

## 8. ROADMAP

```
════════════════════════════════════════════════════════════════════

  2026 Q1                        ✅ COMPLETED
  ─────────────────────────────────────────────────────────────────
  ✅ Launch on Base Mainnet
  ✅ Complete mission system (Solo, Party)
  ✅ 11 progression ranks
  ✅ On-chain Items and Runes
  ✅ Dual economy ($EMBER + $ASH)
  ✅ Interactive tutorial
  ✅ Dynamic metadata

════════════════════════════════════════════════════════════════════

  2026 Q2                        🔲 IN DEVELOPMENT
  ─────────────────────────────────────────────────────────────────
  🔲 Staking rewards for holders
  🔲 P2P Item Marketplace
  🔲 Guild Wars (faction competition)
  🔲 Temporary events with exclusive rewards

════════════════════════════════════════════════════════════════════

  2026 Q3                        📋 PLANNED
  ─────────────────────────────────────────────────────────────────
  📋 Lands system (conquerable territories)
  📋 Passive income from land ownership
  📋 Active DAO governance with $ASH
  📋 Mobile companion app

════════════════════════════════════════════════════════════════════

  2026 Q4                        🔮 VISION
  ─────────────────────────────────────────────────────────────────
  🔮 Lore expansion and new missions
  🔮 Cross-chain bridge
  🔮 Strategic partnerships
  🔮 Second NFT collection

════════════════════════════════════════════════════════════════════
```

---

## 9. ABOUT DEVELOPMENT

### One Project, One Developer

Emberholm Portal was designed, developed, and deployed **100% by a single person**.

This includes:

- **Lore and world design** — Story, factions, characters
- **Smart contracts** — 5 contracts in Solidity
- **Complete backend** — Python/Flask API + PostgreSQL
- **Frontend** — Terminal-style UI from scratch
- **Game systems** — Missions, ranks, items, economy
- **Art direction** — Project visual aesthetic
- **Deployment** — Infrastructure on Base + Render + IPFS

> *"I wanted to prove that a single person with clear vision can create a complete on-chain gaming ecosystem."*

---

## 10. FREQUENTLY ASKED QUESTIONS

### GENERAL

**Q: What is Emberholm Portal?**
> A medieval fantasy RPG where 35,000 unique NFTs (Emissaries) complete missions, earn $EMBER tokens, and progress through 11 ranks while determining the fate of a dying kingdom.

**Q: How much does it cost to start playing?**
> Minting an Emissary costs 0.0011 ETH (~$2-3 USD) + minimal gas on Base (~$0.02-0.05). Once you have your NFT, missions are FREE.

**Q: Do I need crypto/NFT experience?**
> You only need MetaMask and ETH on Base. The game has an interactive tutorial that guides you step by step.

**Q: Can I play on mobile?**
> Currently web-only, but it works on mobile browsers with MetaMask mobile. A native app is on the roadmap.

---

### GAMEPLAY

**Q: How do missions work?**
> Select an Emissary, choose a mission (3h/6h/12h), and wait. Upon completion, you receive XP, Aura, $EMBER, and possible item drops.

**Q: What happens if my Emissary dies?**
> They enter FALLEN state. You can resurrect them by paying $EMBER (200-10,000 depending on previous deaths). XP and Aura reset.

**Q: Can I permanently lose my NFT?**
> No. The NFT is always yours. "Death" only affects the character's in-game state, not token ownership.

**Q: What is Ember Roll?**
> A D20 dice system where you can win $EMBER. First roll free, then 75 EMBER each. You can win up to 1,000 EMBER with a Natural 20.

**Q: How do I maximize earnings?**
> 1) Align guild/class/race with mission (1.5x rewards), 2) Equip Legendary items (+18% EMBER), 3) Do Party missions (+20%), 4) Rank up (up to +50% EMBER).

---

### TECHNICAL

**Q: Why don't missions cost gas?**
> Missions are processed off-chain on our backend. You only pay gas when minting, claiming items, or transferring tokens — actions that truly require blockchain.

**Q: Is my data safe?**
> Yes. Your NFT is on blockchain (impossible to lose). Your progress is in PostgreSQL with backups. Metadata syncs constantly.

**Q: What if the server goes down?**
> Your NFT remains yours on blockchain. When the server returns, your progress automatically restores from the database.

**Q: Why Base instead of Ethereum/Solana/Polygon?**
> Base offers: 1) ~100x lower costs than Ethereum, 2) Coinbase backing, 3) Full EVM compatibility, 4) Growing ecosystem. Ideal for gaming.

**Q: Are the NFTs really dynamic?**
> Yes. Every time you complete a mission, your metadata updates. You can see XP, level, rank, achievements, and equipment directly on OpenSea.

---

### ECONOMIC

**Q: How do I earn real money?**
> You earn $EMBER by completing missions. $EMBER is an ERC20 token you can trade. You can also sell your NFT — one with high level/rank is worth more.

**Q: Is there token inflation?**
> Controlled. Fixed 100M supply with decreasing emissions. Burn mechanisms in resurrections, future crafting, and marketplace fees.

**Q: What is $ASH?**
> Governance token obtained by burning $EMBER (1,000:1). Allows voting on project decisions and access to future premium features.

**Q: Can I make a living playing Emberholm?**
> Depends on the market and your dedication. The game is designed to be sustainable long-term, not a quick profit scheme.

---

### ITEMS AND RUNES

**Q: How do I get items?**
> Random drops when completing missions. Higher difficulty = higher probability. Party missions have the best drop rate (25% items, 12% runes).

**Q: How rare is a Legendary?**
> In EASY missions: 0.05%. In PARTY: 2.5%. They're hard to get but give +18% to all stats.

**Q: Are items NFTs?**
> Yes. Separate contracts (EmberItems, EmberRunes). You can trade or transfer them independently from your Emissary.

**Q: Can I equip multiple items?**
> Yes. Slots: Weapon, Armor, Helmet, Accessory, Amulet, and 2 Runes. Bonuses stack.

---

### COMMUNITY AND FUTURE

**Q: Is there a Discord/community?**
> The project is in growth phase. Community will be built organically.

**Q: What's coming next?**
> Coming soon: Staking rewards, Guild Wars, Lands System, and DAO governance. See complete roadmap above.

**Q: Can I suggest features?**
> When DAO is active, you can create proposals with $ASH. For now, feedback is welcome.

**Q: Will the project continue developing?**
> Yes. The roadmap has long-term vision. Development is continuous.

---

## LINKS

| Resource | URL |
|----------|-----|
| **Game** | [emberholm.com](https://emberholm.com) |
| **Mint** | [emberholm.com/mint](https://emberholm.com/mint) |
| **OpenSea** | [opensea.io/collection/emberholm-portal](https://opensea.io/collection/emberholm-portal) |
| **NFT Contract** | [basescan.org/address/0x7AB2cf80FbfB8c89868b3dFa053729ecC86E39b3](https://basescan.org/address/0x7AB2cf80FbfB8c89868b3dFa053729ecC86E39b3) |

---

<div align="center">

### THE REALM IS DYING. THE EMISSARIES ARE ITS LAST HOPE.

**Will you join the cause?**

*[MINT YOUR EMISSARY]*

</div>

---

*Presentation Document — Emberholm Portal*
*Version 1.0 | January 2026*
