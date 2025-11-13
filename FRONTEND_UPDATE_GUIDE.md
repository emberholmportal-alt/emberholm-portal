# 📝 Guía de Actualización del Frontend

## Paso 1: Actualizar Contract Address

Después de deployar el contrato a Base Sepolia, actualiza la dirección en `static/contract-config.js`:

```javascript
const CONTRACT_CONFIG = {
    ADDRESS: "0xTU_CONTRACT_ADDRESS_AQUI",  // ⚠️ CAMBIA ESTO
    CHAIN_ID: 84532,
    // ... resto de config
};
```

---

## Paso 2: Actualizar index.html

### 2.1 Agregar el script de configuración

En `static/index.html`, después de la línea donde cargas ethers.js, agrega:

```html
<script src="https://cdn.ethers.io/lib/ethers-5.7.2.umd.min.js"></script>
<script src="/static/contract-config.js"></script>  <!-- ⬅️ AGREGAR ESTO -->
```

### 2.2 Reemplazar configuración antigua

Busca en `static/index.html` donde está la configuración del contrato (probablemente cerca de línea 1000-1100):

**❌ ANTES (Borrar esto):**
```javascript
const CONTRACT_ADDRESS = "0x2F55e14F0b2B2118d2026d20Ad2C39EAcBdCAc47";
const CONTRACT_ABI = [
    // ABI viejo largo...
];
```

**✅ DESPUÉS (Reemplazar por esto):**
```javascript
const CONTRACT_ADDRESS = CONTRACT_CONFIG.ADDRESS;
const CONTRACT_ABI = CONTRACT_CONFIG.ABI;
const BASE_SEPOLIA_CHAIN_ID = CONTRACT_CONFIG.CHAIN_ID;
const BASE_SEPOLIA_CHAIN_ID_HEX = CONTRACT_CONFIG.CHAIN_ID_HEX;
```

### 2.3 Actualizar Queries del Contrato

Busca las funciones que hacen queries al contrato y actualízalas:

**getTokenInfo() cambió:**

❌ ANTES:
```javascript
const info = await contract.getTokenInfo(tokenId);
// info = { tokenId, owner, guild, guildName, characterName, isStaked, achievements }
```

✅ DESPUÉS:
```javascript
const info = await contract.getTokenInfo(tokenId);
// info = { tokenId, owner, isStaked }  ← Más simple
// Guild, name, achievements están en metadata
```

**getWalletProfile() cambió:**

❌ ANTES:
```javascript
const profile = await contract.getWalletProfile(address);
// stats = { totalTokens, stakedCount, guildsRepresented }
```

✅ DESPUÉS:
```javascript
const profile = await contract.getWalletProfile(address);
// stats = { totalTokens, stakedCount }  ← guildsRepresented removido
```

### 2.4 Actualizar Función de Fetch de Metadata

Ahora la metadata incluye achievements. Actualiza donde procesas metadata:

```javascript
async function fetchNFTMetadata(tokenId) {
    const tokenURI = await contract.tokenURI(tokenId);
    // tokenURI = "https://emberholm-portal.onrender.com/api/metadata/42"

    const response = await fetch(tokenURI);
    const metadata = await response.json();

    // metadata.attributes ahora incluye:
    // - Starting Guild
    // - Current Guild
    // - Achievement: First Mission
    // - Achievement: Veteran Explorer
    // - Total Achievements
    // etc.

    return metadata;
}
```

### 2.5 Mostrar Achievements en el Frontend

En la sección PROFILE, agrega visualización de achievements:

```javascript
async function displayAchievements(tokenId) {
    const metadata = await fetchNFTMetadata(tokenId);

    // Filtrar achievements de attributes
    const achievements = metadata.attributes.filter(attr =>
        attr.trait_type.startsWith("Achievement:")
    );

    // Mostrar en UI
    const achievementsHTML = achievements.map(ach => `
        <div class="achievement">
            <span>✅ ${ach.trait_type.replace("Achievement: ", "")}</span>
        </div>
    `).join("");

    document.getElementById("achievements-container").innerHTML = achievementsHTML;
}
```

---

## Paso 3: Ejemplo Completo de Integración

Aquí está un ejemplo completo de cómo cargar datos de un NFT:

```javascript
async function loadNFTProfile(tokenId) {
    try {
        // 1. Obtener info on-chain (staking)
        const contractInfo = await contract.getTokenInfo(tokenId);
        console.log("On-chain info:", contractInfo);
        // { tokenId: 42, owner: "0x...", isStaked: false }

        // 2. Obtener metadata (guild, name, achievements, stats)
        const tokenURI = await contract.tokenURI(tokenId);
        const metadata = await fetch(tokenURI).then(r => r.json());
        console.log("Metadata:", metadata);

        // 3. Combinar datos
        const profile = {
            tokenId: contractInfo.tokenId,
            owner: contractInfo.owner,
            isStaked: contractInfo.isStaked,

            // De metadata:
            name: metadata.name,
            image: metadata.image,
            startingGuild: metadata.attributes.find(a => a.trait_type === "Starting Guild")?.value,
            currentGuild: metadata.attributes.find(a => a.trait_type === "Current Guild")?.value,
            level: metadata.attributes.find(a => a.trait_type === "Level")?.value,
            xp: metadata.attributes.find(a => a.trait_type === "XP Total")?.value,
            aura: metadata.attributes.find(a => a.trait_type === "Aura")?.value,

            // Achievements
            achievements: metadata.attributes
                .filter(a => a.trait_type.startsWith("Achievement:"))
                .map(a => a.trait_type.replace("Achievement: ", ""))
        };

        console.log("Complete profile:", profile);

        // 4. Mostrar en UI
        displayProfile(profile);

    } catch (error) {
        console.error("Error loading NFT:", error);
    }
}
```

---

## Paso 4: Testing

### 4.1 Test Básico en Console

Abre DevTools en el navegador y prueba:

```javascript
// 1. Verificar configuración
console.log("Contract Address:", CONTRACT_CONFIG.ADDRESS);
console.log("Chain ID:", CONTRACT_CONFIG.CHAIN_ID);

// 2. Conectar wallet
await ethereum.request({ method: 'eth_requestAccounts' });

// 3. Test totalMinted
const minted = await contract.totalMinted();
console.log("Total minted:", minted.toString());

// 4. Test tokensOfOwner
const myAddress = (await ethereum.request({ method: 'eth_accounts' }))[0];
const myTokens = await contract.tokensOfOwner(myAddress);
console.log("My tokens:", myTokens.map(t => t.toString()));

// 5. Test metadata
if (myTokens.length > 0) {
    const tokenId = myTokens[0];
    const uri = await contract.tokenURI(tokenId);
    console.log("Token URI:", uri);

    const metadata = await fetch(uri).then(r => r.json());
    console.log("Metadata:", metadata);
}
```

### 4.2 Test de Staking

```javascript
const tokenId = 1; // Tu NFT

// Stakear
console.log("Staking token...");
const stakeTx = await contract.stakeToken(tokenId);
await stakeTx.wait();
console.log("✅ Token staked!");

// Verificar
const isStaked = await contract.stakedTokens(tokenId);
console.log("Is staked:", isStaked); // true

// Unstakear
console.log("Unstaking token...");
const unstakeTx = await contract.unstakeToken(tokenId);
await unstakeTx.wait();
console.log("✅ Token unstaked!");
```

### 4.3 Test de Achievements

```javascript
// Otorgar achievement desde backend (cURL)
curl -X POST https://emberholm-portal.onrender.com/api/achievements/grant \
  -H "Content-Type: application/json" \
  -d '{"token_id": "00001", "achievement_id": "first_mission"}'

// Verificar en frontend
const metadata = await fetch("https://emberholm-portal.onrender.com/api/metadata/1").then(r => r.json());
const achievements = metadata.attributes.filter(a => a.trait_type.startsWith("Achievement:"));
console.log("Achievements:", achievements);
```

---

## Paso 5: Checklist de Actualización

### Configuración ✅
- [ ] `static/contract-config.js` tiene el contract address correcto
- [ ] Chain ID configurado a 84532 (Base Sepolia)
- [ ] `static/index.html` carga `contract-config.js`

### Código Actualizado ✅
- [ ] CONTRACT_ADDRESS usa `CONTRACT_CONFIG.ADDRESS`
- [ ] CONTRACT_ABI usa `CONTRACT_CONFIG.ABI`
- [ ] Queries actualizadas (getTokenInfo, getWalletProfile)
- [ ] Metadata fetch incluye achievements
- [ ] UI muestra Starting Guild y Current Guild
- [ ] UI muestra achievements con ✅

### Testing ✅
- [ ] Connect wallet funciona
- [ ] Network switch a Base Sepolia funciona
- [ ] totalMinted() retorna valor correcto
- [ ] tokensOfOwner() retorna mis NFTs
- [ ] Metadata carga correctamente
- [ ] Achievements aparecen en metadata
- [ ] Staking bloquea transfers
- [ ] Unstaking permite transfers

### Deploy ✅
- [ ] Cambios pusheados a Render
- [ ] Backend reiniciado
- [ ] Frontend funciona en producción
- [ ] OpenSea muestra NFTs correctamente
- [ ] Achievements visibles en OpenSea

---

## Paso 6: Deploy a Producción

Cuando todo funcione en testnet:

```bash
# 1. Commit cambios
git add static/contract-config.js static/index.html
git commit -m "feat: Update frontend for EmberholmPortal V2 contract"
git push

# 2. Render auto-deploys

# 3. Verificar
# Visit: https://emberholm-portal.onrender.com
# Test: Connect wallet, load NFTs, check achievements
```

---

## Archivos Modificados

```
/static/contract-config.js         ← NUEVO
/static/index.html                  ← MODIFICADO
/app.py                             ← MODIFICADO (achievements)
/data/achievements.json             ← NUEVO
/contracts/EmberholmPortal.sol     ← NUEVO V2
```

---

## Troubleshooting

### "Contract not deployed"
- Verifica que CONTRACT_CONFIG.ADDRESS esté correcto
- Verifica que estés en Base Sepolia (Chain ID 84532)

### "Metadata not loading"
- Verifica que backend esté corriendo
- Check: https://emberholm-portal.onrender.com/api/metadata/1
- Debería retornar JSON con achievements

### "Achievements not showing"
- Verifica que backend tenga achievements.json
- Check: https://emberholm-portal.onrender.com/api/achievements/00001
- Grant test achievement: POST /api/achievements/grant

### "OpenSea not showing attributes"
- OpenSea cachea metadata (24-48 horas)
- Force refresh: Click "Refresh metadata" en OpenSea
- O espera 24-48 horas para auto-refresh

---

**¡Listo para actualizar el frontend!** 🚀
