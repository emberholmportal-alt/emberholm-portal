# Data Persistence System - Emberholm Portal

## Where Each NFT's Stats Are Stored

### Main File: `data/players.json`

Each NFT has its individual stats saved in `data/players.json`, organized by owner's wallet:

```json
{
  "0xWalletAddress123...": {
    "wallet": "0xWalletAddress123...",
    "totals": {
      "heroes_count": 2,
      "xp_total_all": 450,
      "aura_total_all": 25,
      "energy_total_available": 180
    },
    "heroes": [
      {
        "token_id": "00001",
        "name": "Entara, Bearer of Economy",
        "race_class": "Gith Druid",
        "guild": "Circle of Mist",
        "image_url": "ipfs://...",
        "dynamic_state": {
          "xp_total": 250,                    // Updates with each mission
          "xp_level": 3,                      // Calculated from xp_total
          "aura_level": 15,                   // Accumulates with successful missions
          "energy_current": 80,               // Consumed/regenerated
          "energy_max": 100,
          "power_current": 18,
          "current_guild": "Circle of Mist",
          "state": "READY",                   // READY | ON_MISSION | FALLEN
          "last_update": "2025-11-09T12:30:00Z",
          "last_energy_refresh": "2025-11-09T03:00:00Z",
          "mission_history": {
            "001": "2025-11-08T10:00:00Z",
            "002": "2025-11-08T15:00:00Z",
            "003": "2025-11-09T09:00:00Z"
          },
          "total_missions_completed": 3,      // Counter of successful missions
          "last_mission": "Flame Shard Extraction",
          "current_mission_id": null,
          "mission_start_time": null,
          "death_count": 0                    // Counts how many times hero has died
        }
      },
      {
        "token_id": "00077",
        "name": "Brax-Ironjaw",
        "race_class": "Orc Warrior",
        "guild": "Forge Legion",
        "dynamic_state": {
          "xp_total": 200,
          "aura_level": 10,
          // ... etc
        }
      }
    ]
  }
}
```

---

## Stats Update Flow

### 1. User Mints NFT
```
User mints NFT #1 at /mint
  ↓
Contract creates NFT on blockchain
  ↓
totalMinted() = 1
  ↓
⚠️ Backend does NOT have the NFT yet
```

### 2. User Syncs Wallet (First Time)
```
User connects wallet in PROFILE
  ↓
Frontend queries: contract.tokensOfOwner(address)
  → Result: [1]
  ↓
Frontend sends: POST /api/player/{wallet}
  Body: { token_ids: [1], total_supply: 1 }
  ↓
Backend executes ensure_player(wallet):
  1. Reads wallet_nfts.json to know which NFTs it has
  2. For each new NFT:
     - Calls create_hero_from_metadata(1)
     - Reads data/metadata/00001.json
     - Extracts: name, race, class, starting_guild, stats
     - Creates hero with initial dynamic_state:
       {
         xp_total: 0,
         aura_level: 0,
         energy_current: 100,
         state: "READY",
         current_guild: "Circle of Mist",  // From metadata
         ...
       }
  3. Saves to data/players.json
  ↓
✅ NFT now exists in players.json with stats at 0
```

### 3. User Sends Hero on Mission
```
User selects hero #1 in PROFILE
  ↓
Clicks [MISSIONS] → Selects mission
  ↓
Frontend: POST /api/missions/start
  Body: { wallet, hero_id: "00001", mission_id: "001", energy_request: 30 }
  ↓
Backend (app.py lines 1010-1070):
  1. Loads stats_obj from stats.json
  2. Loads player_obj from players.json
  3. Finds hero #00001
  4. Verifies sufficient energy (80 >= 30)
  5. Updates dynamic_state:
     hero.dynamic_state.energy_current = 80 - 30 = 50
     hero.dynamic_state.state = "ON_MISSION"
     hero.dynamic_state.current_mission_id = "001"
     hero.dynamic_state.mission_start_time = "2025-11-09T12:30:00Z"
  6. Saves to players.json
  ↓
✅ Hero stats updated: Energy = 50, State = ON_MISSION
```

### 4. Mission Complete - Success
```
Required mission hours pass
  ↓
User clicks "Complete Mission"
  ↓
Frontend: POST /api/missions/complete
  Body: { wallet, hero_id: "00001", mission_id: "001" }
  ↓
Backend (app.py lines 1196-1321):
  1. Loads player_obj from players.json
  2. Finds hero #00001
  3. Verifies the required hours have passed
  4. Executes roll_mission_outcome(hero, mission)
     → Calculates success/failure/death probability
  5. If SUCCESS:
     - Calculates rewards: xp_gain = 50, aura_gain = 3
     - Updates dynamic_state:
       hero.dynamic_state.xp_total = 0 + 50 = 50
       hero.dynamic_state.aura_level = 0 + 3 = 3
       hero.dynamic_state.state = "READY"
       hero.dynamic_state.last_mission = "Flame Shard Extraction"
       hero.dynamic_state.total_missions_completed = 1
       hero.dynamic_state.mission_history["001"] = "2025-11-09T14:30:00Z"
     - Updates global stats:
       stats.missions_completed += 1
       stats.total_exp_collected += 50
       stats.total_aura_collected += 3
     - Updates guild stats
  6. Saves players.json
  7. Saves stats.json
  ↓
✅ Hero stats updated: XP = 50, Aura = 3, Missions = 1
✅ Global stats updated
```

### 5. Mission Complete - Failure
```
If mission FAILS:
  - XP loss calculated (e.g.: loses 10 XP)
  - Updates dynamic_state:
    hero.dynamic_state.xp_total = max(0, 50 - 10) = 40
    hero.dynamic_state.state = "READY"
    hero.dynamic_state.last_mission = "Flame Shard Extraction (Failed)"
  - Updates global stats:
    stats.missions_failed += 1
  ↓
✅ Hero loses XP but survives
```

### 6. Mission Complete - Death
```
If hero DIES:
  - Updates dynamic_state:
    hero.dynamic_state.state = "FALLEN"
    hero.dynamic_state.death_count += 1
    hero.dynamic_state.last_mission = "Flame Shard Extraction (Fallen)"
  - Calculates resurrection cost based on death_count
  - Updates global stats:
    stats.missions_failed += 1
    stats.total_deaths += 1
  ↓
✅ Hero becomes FALLEN, requires resurrection
```

---

## Dynamic Metadata for OpenSea/Marketplaces

### Endpoint: `/api/metadata/{token_id}`

The contract points to: `baseTokenURI = "https://emberholm-portal.onrender.com/api/metadata/"`

When OpenSea queries NFT #1:
```
GET https://emberholm-portal.onrender.com/api/metadata/00001
  ↓
Backend executes (app.py lines 1724-1793):
  1. load_base_metadata_for_token("00001")
     → Reads data/metadata/00001.json (STATIC metadata)
     → Extracts: name, race, class, STR, DEX, etc.

  2. find_dynamic_state_for_token("00001")
     → Searches in players.json for hero with token_id="00001"
     → Extracts current dynamic_state:
       - xp_total: 50
       - aura_level: 3
       - energy_current: 50
       - last_mission: "Flame Shard Extraction"
       - current_guild: "Circle of Mist"

  3. Combines both into attributes:
     {
       "name": "Entara, Bearer of Economy",
       "description": "Gith Druid of Emberholm...",
       "image": "ipfs://...",
       "attributes": [
         { "trait_type": "Race", "value": "Gith" },          // Static
         { "trait_type": "Class", "value": "Druid" },        // Static
         { "trait_type": "STR", "value": 11 },               // Static
         { "trait_type": "DEX", "value": 12 },               // Static
         { "trait_type": "Starting Guild", "value": "Circle of Mist" },  // Static
         { "trait_type": "Current Guild", "value": "Circle of Mist" },   // Dynamic
         { "trait_type": "XP Total", "value": 50 },          // Dynamic
         { "trait_type": "Level", "value": 3 },              // Dynamic
         { "trait_type": "Aura", "value": 3 },               // Dynamic
         { "trait_type": "Energy", "value": "50 / 100" },    // Dynamic
         { "trait_type": "Last Mission", "value": "Flame Shard Extraction" }, // Dynamic
         { "trait_type": "Last Update", "value": "2025-11-09T14:30:00Z" }     // Dynamic
       ]
     }
  ↓
✅ OpenSea displays stats updated in real time
```

---

## Data Files

### `data/players.json`
- **What it stores**: Individual stats for each NFT by wallet
- **Updated when**:
  - User connects wallet → New heroes are created
  - User sends on mission → energy_current, state
  - Mission completes → xp_total, aura_level, mission_history
  - Passive regeneration → energy_current (every 24h)
- **Used by**:
  - `/api/player/{wallet}` - Player's PROFILE
  - `/api/metadata/{token_id}` - Dynamic metadata for OpenSea
  - `/api/guilds` - Calculates members/XP/Aura per guild

### `data/stats.json`
- **What it stores**: Accumulated global statistics
- **Updated when**:
  - User connects wallet → total_characters
  - Mission completes successfully → missions_completed, total_exp_collected, total_aura_collected
  - Mission fails → missions_failed
  - Hero dies → total_deaths
- **Used by**:
  - `/api/stats` - Global STATS page

### `data/wallet_nfts.json`
- **What it stores**: Cache of which NFTs each wallet owns
- **Updated when**: User connects wallet
- **Used by**: `get_wallet_token_ids()` to know which NFTs a wallet has

### `data/metadata/00001.json` to `00035000.json`
- **What it stores**: STATIC metadata for each NFT
  - name, race, class, starting_guild
  - STR, DEX, CON, INT, WIS, CHA
  - image IPFS URL
- **NEVER modified** (it's immutable)
- **Used by**:
  - `create_hero_from_metadata()` when loading a new NFT
  - `/api/metadata/{token_id}` to combine with dynamic data

### `data/guilds.json`
- **What it stores**: Info for each guild (name, description, badge)
- **Updated**: Rarely (only if new guilds are added)
- **Stats calculated in real time** from `players.json`:
  - members
  - total_xp
  - total_aura

---

## Verifying an NFT's Stats

### Option 1: Query API directly
```bash
curl https://emberholm-portal.onrender.com/api/metadata/00001
```

Returns:
```json
{
  "name": "Entara, Bearer of Economy",
  "attributes": [
    { "trait_type": "XP Total", "value": 50 },
    { "trait_type": "Aura", "value": 3 },
    { "trait_type": "Energy", "value": "50 / 100" },
    { "trait_type": "Last Mission", "value": "Flame Shard Extraction" }
  ]
}
```

### Option 2: View in PROFILE
```
1. Connect wallet in PROFILE
2. You'll see a list of your NFTs with:
   - XP Total
   - Aura Level
   - Energy Current
   - State (READY / ON_MISSION / FALLEN)
```

### Option 3: View file directly
```bash
cat data/players.json | jq '.["0xWalletAddress"].heroes[] | select(.token_id=="00001") | .dynamic_state'
```

---

## Summary

### Individual Stats per NFT
- Stored in `data/players.json`
- Automatically updated with each action
- Persist between sessions
- Served via `/api/metadata/{token_id}` for OpenSea

### Global Stats
- Stored in `data/stats.json`
- Automatically accumulated
- Don't depend on everyone connecting their wallet

### Dynamic Metadata
- Combines static data (race, class) + dynamic data (XP, Aura)
- OpenSea/marketplaces see stats updated in real time
- Contract points to the correct endpoint

**Everything is implemented and working correctly.**
