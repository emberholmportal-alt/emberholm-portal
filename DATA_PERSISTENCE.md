# Sistema de Persistencia de Datos - Emberholm Portal

## 📊 Dónde se Guardan las Stats de Cada NFT

### Archivo Principal: `data/players.json`

Cada NFT tiene sus stats individuales guardadas en `data/players.json`, organizado por wallet del propietario:

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
          "xp_total": 250,                    // ✅ Se actualiza con cada misión
          "xp_level": 3,                      // ✅ Calculado desde xp_total
          "aura_level": 15,                   // ✅ Se acumula con misiones exitosas
          "energy_current": 80,               // ✅ Se consume/regenera
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
          "total_missions_completed": 3,      // ✅ Contador de misiones exitosas
          "last_mission": "Flame Shard Extraction",
          "current_mission_id": null,
          "mission_start_time": null,
          "death_count": 0                    // ✅ Cuenta cuántas veces ha muerto
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

## 🔄 Flujo de Actualización de Stats

### 1. Usuario Mintea NFT
```
Usuario mintea NFT #1 en /mint
  ↓
Contrato crea NFT en blockchain
  ↓
totalMinted() = 1
  ↓
⚠️ Backend AÚN NO tiene el NFT
```

### 2. Usuario Sincroniza Wallet (Primera Vez)
```
Usuario conecta wallet en PROFILE
  ↓
Frontend consulta: contract.tokensOfOwner(address)
  → Resultado: [1]
  ↓
Frontend envía: POST /api/player/{wallet}
  Body: { token_ids: [1], total_supply: 1 }
  ↓
Backend ejecuta ensure_player(wallet):
  1. Lee wallet_nfts.json para saber qué NFTs tiene
  2. Para cada NFT nuevo:
     - Llama create_hero_from_metadata(1)
     - Lee data/metadata/00001.json
     - Extrae: name, race, class, starting_guild, stats
     - Crea héroe con dynamic_state inicial:
       {
         xp_total: 0,
         aura_level: 0,
         energy_current: 100,
         state: "READY",
         current_guild: "Circle of Mist",  // Desde metadata
         ...
       }
  3. Guarda en data/players.json
  ↓
✅ NFT ahora existe en players.json con stats en 0
```

### 3. Usuario Envía Héroe a Misión
```
Usuario selecciona héroe #1 en PROFILE
  ↓
Click en [MISSIONS] → Selecciona misión
  ↓
Frontend: POST /api/missions/start
  Body: { wallet, hero_id: "00001", mission_id: "001", energy_request: 30 }
  ↓
Backend (app.py líneas 1010-1070):
  1. Carga stats_obj desde stats.json
  2. Carga player_obj desde players.json
  3. Encuentra héroe #00001
  4. Verifica energía suficiente (80 >= 30)
  5. Actualiza dynamic_state:
     hero.dynamic_state.energy_current = 80 - 30 = 50
     hero.dynamic_state.state = "ON_MISSION"
     hero.dynamic_state.current_mission_id = "001"
     hero.dynamic_state.mission_start_time = "2025-11-09T12:30:00Z"
  6. Guarda en players.json
  ↓
✅ Stats del héroe actualizadas: Energy = 50, State = ON_MISSION
```

### 4. Misión Completa - Éxito
```
Pasan las horas requeridas de la misión
  ↓
Usuario hace click en "Complete Mission"
  ↓
Frontend: POST /api/missions/complete
  Body: { wallet, hero_id: "00001", mission_id: "001" }
  ↓
Backend (app.py líneas 1196-1321):
  1. Carga player_obj desde players.json
  2. Encuentra héroe #00001
  3. Verifica que pasaron las horas necesarias
  4. Ejecuta roll_mission_outcome(hero, mission)
     → Calcula probabilidad de éxito/fallo/muerte
  5. Si ÉXITO:
     - Calcula recompensas: xp_gain = 50, aura_gain = 3
     - Actualiza dynamic_state:
       hero.dynamic_state.xp_total = 0 + 50 = 50
       hero.dynamic_state.aura_level = 0 + 3 = 3
       hero.dynamic_state.state = "READY"
       hero.dynamic_state.last_mission = "Flame Shard Extraction"
       hero.dynamic_state.total_missions_completed = 1
       hero.dynamic_state.mission_history["001"] = "2025-11-09T14:30:00Z"
     - Actualiza stats globales:
       stats.missions_completed += 1
       stats.total_exp_collected += 50
       stats.total_aura_collected += 3
     - Actualiza guild stats
  6. Guarda players.json
  7. Guarda stats.json
  ↓
✅ Stats del héroe actualizadas: XP = 50, Aura = 3, Misiones = 1
✅ Stats globales actualizadas
```

### 5. Misión Completa - Fallo
```
Si la misión FALLA:
  - XP loss calculado (ej: pierde 10 XP)
  - Actualiza dynamic_state:
    hero.dynamic_state.xp_total = max(0, 50 - 10) = 40
    hero.dynamic_state.state = "READY"
    hero.dynamic_state.last_mission = "Flame Shard Extraction (Failed)"
  - Actualiza stats globales:
    stats.missions_failed += 1
  ↓
✅ Héroe pierde XP pero sigue vivo
```

### 6. Misión Completa - Muerte
```
Si el héroe MUERE:
  - Actualiza dynamic_state:
    hero.dynamic_state.state = "FALLEN"
    hero.dynamic_state.death_count += 1
    hero.dynamic_state.last_mission = "Flame Shard Extraction (Fallen)"
  - Calcula costo de reinvocación basado en death_count
  - Actualiza stats globales:
    stats.missions_failed += 1
    stats.total_deaths += 1
  ↓
✅ Héroe queda FALLEN, necesita reinvocación
```

---

## 🌐 Metadata Dinámica para OpenSea/Marketplaces

### Endpoint: `/api/metadata/{token_id}`

El contrato apunta a: `baseTokenURI = "https://emberholm-portal.onrender.com/api/metadata/"`

Cuando OpenSea consulta el NFT #1:
```
GET https://emberholm-portal.onrender.com/api/metadata/00001
  ↓
Backend ejecuta (app.py líneas 1724-1793):
  1. load_base_metadata_for_token("00001")
     → Lee data/metadata/00001.json (metadata ESTÁTICA)
     → Extrae: name, race, class, STR, DEX, etc.

  2. find_dynamic_state_for_token("00001")
     → Busca en players.json el héroe con token_id="00001"
     → Extrae dynamic_state actual:
       - xp_total: 50
       - aura_level: 3
       - energy_current: 50
       - last_mission: "Flame Shard Extraction"
       - current_guild: "Circle of Mist"

  3. Combina ambos en attributes:
     {
       "name": "Entara, Bearer of Economy",
       "description": "Gith Druid of Emberholm...",
       "image": "ipfs://...",
       "attributes": [
         { "trait_type": "Race", "value": "Gith" },          // Estático
         { "trait_type": "Class", "value": "Druid" },        // Estático
         { "trait_type": "STR", "value": 11 },               // Estático
         { "trait_type": "DEX", "value": 12 },               // Estático
         { "trait_type": "Starting Guild", "value": "Circle of Mist" },  // Estático
         { "trait_type": "Current Guild", "value": "Circle of Mist" },   // Dinámico
         { "trait_type": "XP Total", "value": 50 },          // ✅ Dinámico
         { "trait_type": "Level", "value": 3 },              // ✅ Dinámico
         { "trait_type": "Aura", "value": 3 },               // ✅ Dinámico
         { "trait_type": "Energy", "value": "50 / 100" },    // ✅ Dinámico
         { "trait_type": "Last Mission", "value": "Flame Shard Extraction" }, // ✅ Dinámico
         { "trait_type": "Last Update", "value": "2025-11-09T14:30:00Z" }     // ✅ Dinámico
       ]
     }
  ↓
✅ OpenSea muestra stats actualizadas en tiempo real
```

---

## 📁 Archivos de Datos

### `data/players.json`
- **Qué guarda**: Stats individuales de cada NFT por wallet
- **Se actualiza cuando**:
  - Usuario conecta wallet → Se crean héroes nuevos
  - Usuario envía a misión → energy_current, state
  - Misión completa → xp_total, aura_level, mission_history
  - Regeneración pasiva → energy_current (cada 24h)
- **Usado por**:
  - `/api/player/{wallet}` - PROFILE del jugador
  - `/api/metadata/{token_id}` - Metadata dinámica para OpenSea
  - `/api/guilds` - Calcula members/XP/Aura por guild

### `data/stats.json`
- **Qué guarda**: Estadísticas globales acumuladas
- **Se actualiza cuando**:
  - Usuario conecta wallet → total_characters
  - Misión completa con éxito → missions_completed, total_exp_collected, total_aura_collected
  - Misión falla → missions_failed
  - Héroe muere → total_deaths
- **Usado por**:
  - `/api/stats` - Página STATS global

### `data/wallet_nfts.json`
- **Qué guarda**: Cache de qué NFTs tiene cada wallet
- **Se actualiza cuando**: Usuario conecta wallet
- **Usado por**: `get_wallet_token_ids()` para saber qué NFTs tiene una wallet

### `data/metadata/00001.json` a `00035000.json`
- **Qué guarda**: Metadata ESTÁTICA de cada NFT
  - name, race, class, starting_guild
  - STR, DEX, CON, INT, WIS, CHA
  - image IPFS URL
- **NUNCA se modifica** (es inmutable)
- **Usado por**:
  - `create_hero_from_metadata()` cuando se carga un NFT nuevo
  - `/api/metadata/{token_id}` para combinar con datos dinámicos

### `data/guilds.json`
- **Qué guarda**: Info de cada guild (nombre, descripción, badge)
- **Se actualiza**: Raramente (solo si se agregan nuevas guilds)
- **Stats calculadas en tiempo real** desde `players.json`:
  - members
  - total_xp
  - total_aura

---

## 🔍 Verificar Stats de un NFT

### Opción 1: Consultar API directamente
```bash
curl https://emberholm-portal.onrender.com/api/metadata/00001
```

Retorna:
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

### Opción 2: Ver en PROFILE
```
1. Conecta wallet en PROFILE
2. Verás lista de tus NFTs con:
   - XP Total
   - Aura Level
   - Energy Current
   - State (READY / ON_MISSION / FALLEN)
```

### Opción 3: Ver archivo directamente
```bash
cat data/players.json | jq '.["0xWalletAddress"].heroes[] | select(.token_id=="00001") | .dynamic_state'
```

---

## ✅ Resumen

### Stats Individuales por NFT
- ✅ Se guardan en `data/players.json`
- ✅ Se actualizan automáticamente con cada acción
- ✅ Persisten entre sesiones
- ✅ Se sirven vía `/api/metadata/{token_id}` para OpenSea

### Stats Globales
- ✅ Se guardan en `data/stats.json`
- ✅ Se acumulan automáticamente
- ✅ No dependen de que todos conecten wallet

### Metadata Dinámica
- ✅ Combina datos estáticos (race, class) + dinámicos (XP, Aura)
- ✅ OpenSea/marketplaces ven stats actualizadas en tiempo real
- ✅ El contrato apunta al endpoint correcto

**Todo está implementado y funcionando correctamente.**
