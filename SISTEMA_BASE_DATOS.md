# 🗄️ Sistema de Base de Datos Centralizada - Emberholm Portal

## 📋 Resumen

Este proyecto utiliza un **sistema de base de datos centralizada completamente automático** que gestiona todos los NFTs, atributos dinámicos y estadísticas globales sin intervención manual.

---

## 🎯 Objetivo

Crear una base de datos que:
- ✅ Se alimente **automáticamente** cuando se mintean NFTs
- ✅ Se actualice **automáticamente** cuando usuarios conectan wallets
- ✅ Se actualice **automáticamente** cuando usuarios completan misiones
- ✅ Provea datos **reales** para STATS y GUILDS sin depender de wallets conectadas
- ✅ Persista atributos dinámicos de cada NFT (XP, Aura, estado, etc.)
- ✅ Funcione **sin intervención manual** del administrador

---

## 🏗️ Arquitectura

### **Fuente de Verdad: `data/nfts_database.json`**

Base de datos JSON centralizada que almacena:
- Todos los NFTs minteados
- Atributos dinámicos individuales (XP, Aura, Energy, estado ON_MISSION, etc.)
- Historial de misiones por NFT
- Último dueño conocido (last_known_owner)
- Timestamps de sincronización

```json
{
  "00001": {
    "token_id": "00001",
    "name": "Warrior #1",
    "guild": "Forge Legion",
    "race_class": "Orc Warrior",
    "image_url": "ipfs://...",
    "dynamic_state": {
      "xp_total": 450,
      "aura_level": 35,
      "energy_current": 80,
      "energy_max": 100,
      "state": "ON_MISSION",
      "current_mission_id": "007",
      "mission_start_time": "2025-01-09T12:00:00Z",
      "total_missions_completed": 5,
      "mission_history": {},
      "death_count": 0,
      "last_update": "2025-01-09T12:00:00Z"
    },
    "last_known_owner": "0xabc123...",
    "first_seen": "2025-01-09T10:00:00Z",
    "last_synced": "2025-01-09T12:00:00Z"
  }
}
```

### **Cache Temporal: `data/players.json`**

- Solo para sesiones activas de usuarios
- Se construye desde `nfts_database.json`
- **NO es fuente de verdad**
- Se puede borrar sin pérdida de datos

---

## ⚙️ Funcionamiento Automático

### **1. Usuario Mintea un NFT**

```
Blockchain: NFT #7 minteado → Usuario recibe NFT

(El NFT existe en blockchain pero aún NO en nuestra base de datos)
```

### **2. Usuario Conecta su Wallet al Portal (PRIMERA VEZ)**

```
Usuario: [CONNECT WALLET] → MetaMask

Frontend:
1. Consulta blockchain: contract.tokensOfOwner(address)
   → Retorna: [1, 2, 7]  (3 NFTs en esa wallet)

2. POST /api/player/0xabc123
   {
     "token_ids": ["00001", "00002", "00007"],
     "total_supply": 7
   }

Backend (AUTOMÁTICO):
3. Guarda wallet_nfts.json (cache)

4. 🔥 AUTO-SINCRONIZACIÓN:
   Para cada token_id en la lista:
   - Verifica si existe en nfts_database.json
   - Si NO existe → crea desde metadata/00007.json
   - Si SÍ existe → actualiza last_known_owner
   - Preserva dynamic_state existente

5. 🔥 AUTO-RECALCULO:
   - calculate_guilds_data() → lee nfts_database.json
   - Actualiza guilds.json con members reales
   - Actualiza stats.json

Resultado:
✅ NFT #7 ahora está en nfts_database.json
✅ STATS muestra "Total Emissaries: 7"
✅ GUILDS muestra el nuevo miembro
✅ Todo automático, sin intervención manual
```

### **3. Usuario Completa una Misión**

```
Usuario: [CLAIM REWARDS] en el portal

Backend (AUTOMÁTICO):
1. Calcula recompensas (XP, Aura)
2. 🔥 Actualiza nfts_database.json:
   update_nft_dynamic_state("00007", {
     "xp_total": 450 + 350,  // +350 XP
     "aura_level": 35 + 25,  // +25 Aura
     "state": "READY",
     "current_mission_id": null,
     ...
   })
3. Actualiza stats.json (global)
4. 🔥 Recalcula guilds.json desde DB
5. Actualiza players.json (cache)

Resultado:
✅ NFT #7 tiene 800 XP y 60 Aura permanentemente
✅ STATS actualizado (total_exp_collected)
✅ GUILDS actualizado (Forge Legion XP total)
✅ Todo persiste en nfts_database.json
```

### **4. Usuario Desconecta Wallet**

```
Usuario: Cierra navegador / desconecta MetaMask

Backend:
- players.json puede borrarse (solo cache)
- nfts_database.json mantiene TODOS los datos

Usuario vuelve mañana:
1. Conecta wallet → Auto-sincronización
2. NFT #7 carga con 800 XP y 60 Aura (desde DB)
3. STATS y GUILDS muestran datos correctos
```

### **5. Nuevo Usuario Mintea NFT #8**

```
Blockchain: NFT #8 minteado

Nuevo usuario conecta wallet:
1. Frontend detecta NFT #8
2. POST con token_ids: ["00008"]
3. 🔥 Backend automáticamente:
   - Sincroniza #8 a nfts_database.json
   - Recalcula guilds.json
   - Actualiza stats.json

Resultado:
✅ STATS muestra "Total Emissaries: 8"
✅ NFT #8 en la base de datos
✅ Sistema escalable a 10,000+ NFTs
```

---

## 📊 Estadísticas Globales (Automáticas)

### **STATS Panel**

Lee **directamente** de `nfts_database.json`:

```javascript
// Frontend llama GET /api/stats

Backend:
- count_active_missions() → cuenta ON_MISSION en DB
- calculate_guild_ranking() → suma XP/Aura por guild desde DB
- calculate_player_leaderboard() → agrupa por owner desde DB

Retorna datos REALES en tiempo real
```

### **GUILDS Panel**

Lee de `guilds.json` (recalculado desde DB):

```javascript
// Frontend llama GET /api/guilds

Backend:
- calculate_guilds_data() → lee nfts_database.json
- Cuenta members, avg_xp, avg_aura por guild
- Actualiza guilds.json
- Retorna datos actualizados
```

**Ejemplo:**
```json
{
  "name": "Forge Legion",
  "members": 3,           // 3 NFTs de Forge Legion en DB
  "total_xp": 1500,       // Suma de XP de esos 3 NFTs
  "total_aura": 95,       // Suma de Aura
  "avg_xp": 500.0,        // 1500 / 3
  "avg_aura": 31.67       // 95 / 3
}
```

---

## 🔄 Flujo de Datos Completo

```
┌─────────────────────────────────────────────────────────────┐
│                    MINTEAR NFT (Blockchain)                  │
│                            ↓                                 │
│              Usuario conecta wallet al portal                │
│                            ↓                                 │
│   Frontend: contract.tokensOfOwner(address) → [token_ids]   │
│                            ↓                                 │
│           POST /api/player/{wallet} con token_ids            │
│                            ↓                                 │
│    ┌───────────────────────────────────────────────┐        │
│    │  🔥 AUTO-SINCRONIZACIÓN (AUTOMÁTICO)          │        │
│    │                                                │        │
│    │  Para cada token_id:                          │        │
│    │  1. sync_nft_to_database(token_id, owner)     │        │
│    │     - Si es nuevo → crea desde metadata       │        │
│    │     - Si existe → actualiza owner             │        │
│    │     - Preserva dynamic_state                  │        │
│    │                                                │        │
│    │  2. calculate_guilds_data()                   │        │
│    │     - Lee todos NFTs de DB                    │        │
│    │     - Recalcula members por guild             │        │
│    │     - Actualiza guilds.json                   │        │
│    │                                                │        │
│    │  ✅ NFT en nfts_database.json                 │        │
│    │  ✅ STATS actualizado                         │        │
│    │  ✅ GUILDS actualizado                        │        │
│    └───────────────────────────────────────────────┘        │
│                            ↓                                 │
│              Usuario completa misiones                       │
│                            ↓                                 │
│    ┌───────────────────────────────────────────────┐        │
│    │  🔥 AUTO-ACTUALIZACIÓN (AUTOMÁTICO)           │        │
│    │                                                │        │
│    │  1. update_nft_dynamic_state(token_id, {...}) │        │
│    │     - Actualiza XP, Aura, estado              │        │
│    │     - Persiste en nfts_database.json          │        │
│    │                                                │        │
│    │  2. update_guild_stats()                      │        │
│    │     - Actualiza stats.json                    │        │
│    │     - Recalcula guilds.json desde DB          │        │
│    │                                                │        │
│    │  ✅ Datos persistentes                        │        │
│    │  ✅ STATS/GUILDS actualizados                 │        │
│    └───────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

---

## ✅ Ventajas del Sistema

1. **100% Automático:**
   - No requiere endpoints de admin manuales
   - Se auto-sincroniza cuando usuarios conectan
   - Se auto-actualiza cuando completan misiones

2. **Escalable:**
   - Funciona con 6 NFTs o 10,000 NFTs
   - Performance optimizada (JSON + índices)

3. **Persistente:**
   - Atributos dinámicos NO se pierden
   - Sobrevive reinicios del servidor
   - Independent de blockchain (datos off-chain)

4. **Real-time Stats:**
   - STATS y GUILDS siempre actualizados
   - No dependen de wallets conectadas
   - Datos públicos para todos los usuarios

5. **Backup-friendly:**
   - Solo necesitas respaldar `nfts_database.json`
   - `players.json` es reconstruible
   - Metadata original en `data/metadata/`

---

## 🎮 Uso para el Administrador

### **No se requiere acción manual**

El sistema funciona automáticamente cuando:
- ✅ Usuarios conectan wallets
- ✅ Usuarios completan misiones
- ✅ Se mintean nuevos NFTs

### **Endpoint opcional (solo para casos especiales):**

```bash
# Si necesitas poblar DB manualmente (ej: importar NFTs antiguos)
POST /api/admin/populate_database
{
  "start_token": 1,
  "end_token": 100,
  "overwrite": false
}
```

**Casos de uso:**
- Importar NFTs minteados antes de implementar el sistema
- Resetear un NFT específico (con overwrite: true)
- Debugging/testing

---

## 📁 Estructura de Archivos

```
data/
├── nfts_database.json        ← 🔥 FUENTE DE VERDAD (atributos dinámicos)
├── players.json              ← Cache temporal (puede borrarse)
├── stats.json                ← Estadísticas globales
├── guilds.json               ← Stats por guild (recalculado desde DB)
├── wallet_nfts.json          ← Cache de NFTs por wallet
├── achievements.json         ← Logros de jugadores
├── active_missions.json      ← Misiones activas
└── metadata/
    ├── 00001.json            ← Metadata estática (nombre, guild, imagen)
    ├── 00002.json
    └── ...
```

---

## 🔧 Mantenimiento

### **Backup:**
```bash
# Respaldar solo la fuente de verdad
cp data/nfts_database.json backups/nfts_database_2025-01-09.json
```

### **Restaurar:**
```bash
# Restaurar desde backup
cp backups/nfts_database_2025-01-09.json data/nfts_database.json
```

### **Limpiar cache (seguro):**
```bash
# Estos archivos se reconstruyen automáticamente
rm data/players.json
rm data/wallet_nfts.json
```

---

## 🎯 Resultado Final

✅ **Sistema completamente automático**
✅ **Sin intervención manual requerida**
✅ **NFTs se sincronizan al conectar wallet**
✅ **Stats reales sin depender de conexiones**
✅ **Atributos dinámicos persistentes**
✅ **Escalable a miles de NFTs**
✅ **STATS y GUILDS siempre actualizados**

---

## 📝 Notas Técnicas

- **sync_nft_to_database()**: Preserva dynamic_state si el NFT ya existe
- **update_nft_dynamic_state()**: Solo actualiza campos específicos (no reemplaza todo)
- **calculate_guilds_data()**: Lee toda la DB pero es eficiente con <10k NFTs
- **ensure_player()**: Usa la DB como fuente de verdad, no players.json

---

## 🚀 Próximos Pasos (Opcional)

Para optimización futura (solo si tienes >10,000 NFTs):
- Migrar a PostgreSQL o MongoDB
- Implementar índices por guild/owner
- Cache Redis para queries frecuentes
- Webhooks de blockchain para auto-sync en tiempo real

Pero con el sistema JSON actual funciona perfecto hasta 10,000 NFTs.
