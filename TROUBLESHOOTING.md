# Troubleshooting - Emberholm Portal

## Problema: NFTs minteados no aparecen en GUILDS o STATS

### ¿Por qué sucede esto?

El sistema Emberholm Portal usa una **arquitectura híbrida**:
- **Blockchain**: Almacena la propiedad de NFTs y datos inmutables
- **Backend**: Almacena datos dinámicos (XP, Aura, Energy, Misiones)

Cuando minteas un NFT:
1. ✅ El NFT se crea en la blockchain
2. ❌ El backend AÚN NO sabe que tienes ese NFT
3. ❌ Por lo tanto, STATS y GUILDS no muestran el NFT

### Solución: Sincronizar tu wallet con el backend

**Pasos para que tus NFTs aparezcan en GUILDS y STATS:**

1. **Ve a la página principal** (/)
2. **Haz click en [PROFILE]**
3. **Conecta tu wallet** (MetaMask en Base Sepolia)
4. **Espera la sincronización**:
   - El frontend consultará el contrato
   - Obtendrá la lista de tus NFTs
   - Enviará los datos al backend
   - El backend creará los héroes y los asignará a guilds

5. **Verifica STATS y GUILDS**:
   - Ve a [STATS] - Verás "Total Emissaries" actualizado
   - Ve a [GUILDS] - Verás tus NFTs en sus respectivas guilds

### ¿Con qué frecuencia debo sincronizar?

- **Después de mintear**: Siempre que mintees nuevos NFTs
- **Después de recibir NFTs**: Si alguien te transfiere NFTs
- **Al iniciar sesión**: La primera vez que uses la app

### Detalles técnicos

**Flujo de sincronización:**
```
1. Usuario conecta wallet en PROFILE
   ↓
2. Frontend consulta: contract.tokensOfOwner(address)
   ↓
3. Frontend envía: POST /api/player/{wallet}
   Body: { token_ids: [1, 2, 3], total_supply: 100 }
   ↓
4. Backend:
   - Guarda token_ids en wallet_nfts.json
   - Carga metadata desde data/metadata/00XXX.json
   - Crea héroes con guild asignada
   - Guarda en players.json
   ↓
5. STATS y GUILDS leen desde players.json
```

**Archivos involucrados:**
- `data/wallet_nfts.json` - Mapeo de wallets → token_ids
- `data/players.json` - Datos de jugadores y héroes
- `data/stats.json` - Estadísticas globales
- `data/guilds.json` - Datos de guilds

### Errores comunes

**"Total Emissaries muestra 0"**
- Solución: Conecta tu wallet en PROFILE
- El backend actualizará `total_supply` automáticamente

**"Mis NFTs no tienen guild"**
- Verifica que existe `data/metadata/{tokenId}.json`
- La metadata debe tener `fixed_profile.starting_guild`

**"GUILDS muestra 0 members"**
- Nadie ha conectado su wallet todavía
- Conecta tu wallet en PROFILE para sincronizar

## Problema: Contador MINT muestra número incorrecto

### Solución aplicada

El contador ahora consulta **directamente el contrato** usando `totalMinted()`:
- ✅ Muestra el total real de NFTs minteados en blockchain
- ✅ Se actualiza automáticamente al cargar la página
- ✅ No usa localStorage (que podía tener valores viejos)

Si ves un número incorrecto:
1. Recarga la página (F5)
2. Verifica en la consola: "[DEBUG] Total minted on-chain: X"
3. Compara con Basescan: https://sepolia.basescan.org/address/0xA93C701F0dD91DE0E82f6796d56c4c7aeE053749

---

## Resumen de cambios recientes

### Commit: "FIX: Reset data files and update MINT page to use EmberholmPortal V2 contract"
- ✅ Actualizado CONTRACT_ADDRESS a EmberholmPortal V2
- ✅ Reseteados archivos de datos (stats, players, wallet_nfts)
- ✅ Contador MINT consulta blockchain directamente

### Contrato actual
- **Address**: `0xA93C701F0dD91DE0E82f6796d56c4c7aeE053749`
- **Network**: Base Sepolia (testnet)
- **Explorer**: https://sepolia.basescan.org/address/0xA93C701F0dD91DE0E82f6796d56c4c7aeE053749
