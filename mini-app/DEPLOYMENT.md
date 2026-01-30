# Emberholm Mini-App Deployment Guide

## Required Server-Side Setup

### 1. Seed Micro-Missions Database

The micro-missions table must be populated for the missions feature to work.

```bash
# On the production server
cd /path/to/emberholm-portal
python seed_micro_missions.py
```

**Expected output:**
```
============================================================
EMBERHOLM MINI APP - Seed Micro Missions
============================================================

Encontrados 6 archivos de micro-misiones:
  - MM-E001.json
  - MM-E002.json
  - MM-E003.json
  - MM-H001.json
  - MM-M001.json
  - MM-M002.json

  [EASY] MM-E001: Ember Patrol
  [EASY] MM-E002: Market Reconnaissance
  [EASY] MM-E003: Tavern Gossip
  [HARD] MM-H001: Shadow Infiltration
  [MEDIUM] MM-M001: Guild Courier
  [MEDIUM] MM-M002: Ancient Ruins Survey

============================================================
SEED COMPLETE: 6 loaded, 0 errors
============================================================
```

### Alternative: Direct SQL Insert

If the Python script fails, you can insert missions directly:

```sql
-- Check if table exists
SELECT COUNT(*) FROM micro_missions;

-- Insert a sample mission
INSERT INTO micro_missions (
    id, name, description, difficulty, duration_seconds,
    energy_cost, pyre_reward_min, pyre_reward_max,
    xp_reward_min, xp_reward_max, aura_chance,
    narrative_intro, cooldown_minutes, is_active
) VALUES (
    'MM-E001', 'Ember Patrol', 'Scout the perimeter', 'EASY', 60,
    5, 10, 20, 5, 10, 0.05,
    'You set out to patrol the ember fields...', 5, TRUE
);
```

---

## Environment Variables

Ensure these are set on the production server:

```env
DATABASE_URL=postgresql://user:pass@host:5432/emberholm
NEXT_PUBLIC_API_URL=https://emberholmportal.xyz
```

---

## Contract Addresses (Base Mainnet)

- **EmberholmPortal**: `0x7AB2cf80FbfB8c89868b3dFa053729ecC86E39b3`
- **EmberItems**: `0xCE71702CE99Bc927216e64d57e4BD19254Ac28bA`
- **EmberRunes**: `0xDa2D1085053c3700645a13498293D17c1cc3f595`
- **EmberToken**: `0xbA7723fBfb44C7712C0B78108ad873DcFd5Dd73b`
- **AshToken**: `0xD4eef3eadb1Cf1B2905AA4Cd1022b8cCCC739DAb`

---

## IPFS CIDs

- **Items Metadata**: `bafybeibs6mm5rghbpld7twbj35dbpryrfimmqkbnkev6ufs4kpbp343wfm`
- **Items Images**: `bafybeiegbqf3ypcn7uukahdf275yrmxu2g4zt4xmmrfwguufppbhzs4yx4`
- **Runes Metadata**: `bafybeiajq22kxgm764srr55wsiz4t65so5laxe2nmrryzgailzpmfes3nq`
- **Runes Images**: `bafybeibmivzieas7beofrxspoqo5iughrzyvg3wgjibe626eqt37zg3sae`
- **Emissary Metadata**: `bafybeidd7wtx7izjgsociwe6ynjz6c3xslqmcedr7z4wojcxs4yd5u7pim`
- **Emissary Images**: `bafybeicnvc3zagcncablcovpxgt5mtuotowvuqom6kby754ve2gwbzdvkm`

---

## Troubleshooting

### Emissaries Not Detected

The mini-app must:
1. Query blockchain for `tokensOfOwner(wallet)`
2. POST token_ids to `/api/player/{wallet}`
3. Then GET `/api/player/{wallet}` returns heroes

This flow is implemented in `WalletContext.tsx`.

### Globe Empty (No Countries)

Users need to select their country in the registration flow. The country is stored in:
- `localStorage: emberholm_country`
- `user_profiles.country_code` (database)

### Items/Runes Not Loading

1. Check blockchain query for `tokensOfOwner()` in browser console
2. Verify IPFS gateway is accessible: `https://ipfs.io/ipfs/`
3. Check contract addresses match Base Mainnet

---

## Build Commands

```bash
cd mini-app
npm install
npm run build
npm start  # Production mode
```
