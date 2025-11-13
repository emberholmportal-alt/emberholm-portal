# Troubleshooting - Emberholm Portal

> 📘 **Para entender cómo se guardan y actualizan las stats de cada NFT**, lee: [DATA_PERSISTENCE.md](DATA_PERSISTENCE.md)

---

## Problema: NFTs minteados no aparecen en mi PROFILE

### ¿Por qué sucede esto?

El sistema Emberholm Portal usa una **arquitectura híbrida**:
- **Blockchain**: Almacena la propiedad de NFTs (quién tiene qué NFT)
- **Backend**: Almacena datos dinámicos (XP, Aura, Energy, Misiones completadas)

Cuando minteas un NFT:
1. ✅ El NFT se crea en la blockchain
2. ❌ El backend AÚN NO sabe que tienes ese NFT
3. ❌ Por lo tanto, no aparece en tu PROFILE hasta que sincronices

### Solución: Sincronizar tu wallet con el backend

**Pasos para que tus NFTs aparezcan en PROFILE:**

1. **Ve a la página principal** (/)
2. **Haz click en [PROFILE]**
3. **Conecta tu wallet** (MetaMask en Base Sepolia)
4. **Espera la sincronización** (5-10 segundos):
   - El frontend consultará el contrato
   - Obtendrá la lista de tus NFTs
   - Enviará los datos al backend
   - El backend creará los héroes con sus guilds asignadas

5. **Verifica**:
   - Deberías ver tus NFTs listados con imagen, race, class
   - Cada NFT tendrá su guild asignada
   - Podrás enviarlos a misiones

### ¿Cuándo debo sincronizar?

- **Después de mintear**: Siempre que mintees nuevos NFTs
- **Después de recibir NFTs**: Si alguien te transfiere NFTs
- **Primera vez**: Al iniciar sesión en la app

---

## Problema: STATS globales muestran valores en 0

### ¿Cómo funcionan las estadísticas globales?

Las estadísticas en la sección [STATS] se **acumulan automáticamente** cuando los jugadores realizan acciones.

**NO necesitas conectar wallet para que se actualicen las stats globales.**

### Actualización automática por acción

#### ✅ Total Emissaries
- Se actualiza cuando alguien conecta su wallet en PROFILE
- El frontend envía `total_supply` desde el contrato al backend
- Backend guarda en `stats.json`

#### ✅ Missions Completed / Total XP / Total Aura
Se actualizan **automáticamente** cuando:
1. Un jugador envía su héroe a una misión
2. Esperan las horas requeridas
3. Hacen click en "Complete Mission"
4. Backend procesa el resultado:
   ```python
   # Si la misión tiene éxito:
   stats.missions_completed += 1
   stats.total_exp_collected += xp_ganado
   stats.total_aura_collected += aura_ganado

   # Si la misión falla:
   stats.missions_failed += 1
   ```
5. Se guarda automáticamente en `stats.json`

#### ✅ Missions Failed
Se actualiza automáticamente cuando una misión falla o un héroe muere.

### Estado actual

Como los archivos de datos fueron reseteados, las estadísticas están en 0 hasta que:
- ✅ **Total Emissaries**: Alguien conecta wallet en PROFILE (actualiza desde contrato)
- ⏳ **Missions Completed**: Alguien complete una misión
- ⏳ **Missions Failed**: Alguien falle una misión
- ⏳ **Total XP**: Alguien complete misiones (acumula XP ganado)
- ⏳ **Total Aura**: Alguien complete misiones (acumula Aura ganada)

**Las stats se acumulan progresivamente a medida que los jugadores juegan.**

---

## Problema: GUILDS muestra 0 members

### ¿Cómo se asignan los NFTs a guilds?

Cada NFT tiene metadata pre-generada en `data/metadata/00001.json` a `00035000.json` que incluye:
```json
{
  "fixed_profile": {
    "token_id": "00001",
    "race": "Gith",
    "class": "Druid",
    "starting_guild": "Circle of Mist"  // ← Guild asignada
  }
}
```

Cuando conectas tu wallet en PROFILE:
1. Frontend consulta qué NFTs tienes
2. Backend carga la metadata de cada NFT
3. Backend asigna el héroe a su `starting_guild`
4. Backend guarda en `players.json`
5. GUILDS lee de `players.json` y calcula:
   - **Members**: Número de NFTs en esa guild
   - **Total XP**: Suma de XP de todos los miembros
   - **Total Aura**: Suma de Aura de todos los miembros

### Solución

1. **Mintea o adquiere NFTs**
2. **Conecta tu wallet en PROFILE** → Sincroniza tus NFTs
3. **Ve a GUILDS** → Verás tus NFTs en sus guilds correspondientes

---

## Problema: Contador MINT muestra número incorrecto

### Solución aplicada

El contador ahora consulta **directamente el contrato** usando `totalMinted()`:
- ✅ Muestra el total real de NFTs minteados en blockchain
- ✅ Se actualiza automáticamente al cargar la página
- ✅ No usa localStorage (que podía tener valores viejos)

Si ves un número incorrecto:
1. Recarga la página (F5)
2. Verifica en la consola del navegador: `[DEBUG] Total minted on-chain: X`
3. Compara con Basescan: https://sepolia.basescan.org/address/0xA93C701F0dD91DE0E82f6796d56c4c7aeE053749

---

## Flujo técnico completo

### Mintear NFT
```
Usuario mintea en /mint
  ↓
Contrato crea NFT en blockchain
  ↓
totalMinted() se incrementa
  ↓
Contador MINT se actualiza automáticamente
```

### Sincronizar NFTs (PROFILE)
```
Usuario conecta wallet en PROFILE
  ↓
Frontend: contract.tokensOfOwner(address)
  ↓
Frontend: POST /api/player/{wallet}
  Body: { token_ids: [1,2,3], total_supply: 100 }
  ↓
Backend:
  - Guarda token_ids en wallet_nfts.json
  - Carga metadata desde data/metadata/00XXX.json
  - Crea héroes con guild asignada
  - Guarda en players.json
  ↓
PROFILE muestra los NFTs del jugador
```

### Completar Misión (actualiza STATS globales)
```
Usuario completa misión
  ↓
Backend procesa resultado:
  - missions_completed++ (o missions_failed++)
  - total_exp_collected += xp
  - total_aura_collected += aura
  - Guarda en stats.json
  ↓
Página STATS lee stats.json
  ↓
Muestra estadísticas actualizadas
```

### Ver GUILDS
```
Usuario entra a GUILDS
  ↓
Backend lee players.json
  ↓
Calcula por cada guild:
  - Members: count de NFTs en esa guild
  - Total XP: sum de xp_total
  - Total Aura: sum de aura_level
  ↓
Muestra estadísticas de guilds
```

---

## Archivos de datos

- **`data/wallet_nfts.json`** - Mapeo de wallets → token_ids (cache)
- **`data/players.json`** - Datos de jugadores y sus héroes (XP, Aura, Energy)
- **`data/stats.json`** - Estadísticas globales (missions, XP total, Aura total)
- **`data/guilds.json`** - Datos de guilds (members, totales calculados)
- **`data/metadata/00XXX.json`** - Metadata fija de cada NFT (race, class, guild)

---

## Resumen de cambios recientes

### Commit: "FIX: Corregir contador MINT y documentar sincronización"
- ✅ Contador MINT consulta blockchain directamente (no localStorage)
- ✅ Documentación completa del sistema híbrido
- ✅ Aclarado que stats globales se acumulan automáticamente

### Contrato actual
- **Address**: `0xA93C701F0dD91DE0E82f6796d56c4c7aeE053749`
- **Network**: Base Sepolia (testnet)
- **Chain ID**: 84532
- **Explorer**: https://sepolia.basescan.org/address/0xA93C701F0dD91DE0E82f6796d56c4c7aeE053749
- **RPC**: https://sepolia.base.org
