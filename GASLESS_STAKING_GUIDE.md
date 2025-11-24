# 🔥 GUÍA COMPLETA: STAKING GASLESS

## 📋 ÍNDICE

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Cómo Funciona](#cómo-funciona)
3. [Setup Inicial](#setup-inicial)
4. [Implementación Backend](#implementación-backend)
5. [Implementación Frontend](#implementación-frontend)
6. [Testing](#testing)
7. [Deployment](#deployment)
8. [Costos y Optimización](#costos-y-optimización)
9. [Troubleshooting](#troubleshooting)

---

## 📊 RESUMEN EJECUTIVO

### ¿Qué es Staking Gasless?

**Usuario:** Firma mensajes off-chain (GRATIS, sin gas)
**Backend:** Ejecuta transacciones on-chain y paga el gas (~$0.02 por misión)

### Beneficios

✅ **Usuarios no pagan gas** - Mejor UX
✅ **NFTs locked durante misiones** - Previene transferencias
✅ **Preparado para tokenomics** - Cuando agreguen $EMBER
✅ **Seguro** - Firma de mensajes + cooldown de unstake

### Costos Estimados

| Escenario | Misiones/Día | Costo/Día | Costo/Mes |
|-----------|--------------|-----------|-----------|
| **Pequeño** | 100 | $1.70 | $51 |
| **Medio** | 1,000 | $17 | $510 |
| **Grande** | 10,000 | $170 | $5,100 |

**ROI con $EMBER:** Si cobras 5 $EMBER por misión (~$0.10), ganas $0.08 neto por misión.

---

## 🔄 CÓMO FUNCIONA

### Flujo Completo

```
┌─────────────┐        ┌─────────────┐        ┌──────────────┐
│   USUARIO   │        │   BACKEND   │        │  BLOCKCHAIN  │
└──────┬──────┘        └──────┬──────┘        └──────┬───────┘
       │                      │                       │
       │ 1. "Start Mission"   │                       │
       │─────────────────────>│                       │
       │    (firma mensaje)   │                       │
       │                      │                       │
       │                      │ 2. Verifica firma     │
       │                      │─────────────>         │
       │                      │                       │
       │                      │ 3. stakeToken()       │
       │                      │──────────────────────>│
       │                      │    (backend paga gas) │
       │                      │                       │
       │                      │<─────────────────────┤│
       │                      │    4. Confirmación    │
       │                      │                       │
       │<────────────────────┤│                       │
       │  5. "Mission started"│                       │
       │                      │                       │
       │         ...         │         ...           │
       │    (misión en progreso - 3 horas)           │
       │         ...         │         ...           │
       │                      │                       │
       │ 6. "Complete Mission"│                       │
       │─────────────────────>│                       │
       │    (firma mensaje)   │                       │
       │                      │                       │
       │                      │ 7. Calcula rewards    │
       │                      │─────────────>         │
       │                      │                       │
       │                      │ 8. unstakeToken()     │
       │                      │──────────────────────>│
       │                      │    (backend paga gas) │
       │                      │                       │
       │                      │<─────────────────────┤│
       │                      │    9. Confirmación    │
       │                      │                       │
       │<────────────────────┤│                       │
       │  10. Recompensas     │                       │
       │   (+100 XP, +10 Aura)│                       │
       │                      │                       │
```

### Comparación: Con vs Sin Gas

| Acción | Usuario Paga Gas | Gasless (Backend Paga) |
|--------|------------------|------------------------|
| **Inicio misión** | $0.10 + firma | Solo firma (GRATIS) |
| **Fin misión** | $0.07 + firma | Solo firma (GRATIS) |
| **Total** | **$0.17** | **$0.00** |
| **Experiencia** | 😠 Fricción | 😊 Fluido |

---

## 🛠️ SETUP INICIAL

### Requisitos

- Python 3.9+
- Flask
- Web3.py
- Node RPC (Infura o Alchemy)
- Wallet con ETH en Base

### 1. Instalar Dependencias

```bash
pip install web3==6.11.0
pip install eth-account==0.10.0
```

### 2. Obtener API Keys

#### Opción A: Infura (Recomendado)
1. Ir a https://infura.io
2. Crear cuenta gratuita
3. Crear proyecto "Emberholm Portal"
4. Copiar API Key
5. Network: **Base Mainnet** (o Base Sepolia para testing)

#### Opción B: Alchemy (Alternativa)
1. Ir a https://alchemy.com
2. Crear cuenta
3. Crear app: Base Mainnet
4. Copiar API Key

### 3. Crear Mission Manager Wallet

```bash
# Opción 1: Generar nueva wallet
python3 -c "from eth_account import Account; acc = Account.create(); print(f'Address: {acc.address}'); print(f'Private Key: {acc.key.hex()}')"

# Opción 2: Usar wallet existente
# Solo necesitas la private key
```

**⚠️ IMPORTANTE:** Esta wallet **DEBE** tener balance de ETH.

**Fondear wallet:**
```
Testnet (Base Sepolia): https://www.coinbase.com/faucets/base-ethereum-goerli-faucet
Mainnet (Base): Transferir desde exchange (0.1 ETH recomendado)
```

### 4. Configurar Variables de Entorno

Copiar `.env.web3.example` a `.env`:

```bash
cp .env.web3.example .env
nano .env  # Editar con tus valores
```

**Completar con:**
```env
WEB3_RPC_URL=https://base-sepolia.infura.io/v3/TU_INFURA_KEY
MISSION_MANAGER_ADDRESS=0xTU_WALLET_ADDRESS
MISSION_MANAGER_PRIVATE_KEY=0xTU_PRIVATE_KEY
CONTRACT_ADDRESS=0xCONTRATO_DEPLOYADO
CONTRACT_ABI_PATH=EmberholmPortal_ABI.json
```

### 5. Obtener Contract ABI

Después de deployar el contrato en Basescan:

```bash
# Ir a Basescan
# Contract → Code → Contract ABI → Copy

# Guardar en EmberholmPortal_ABI.json
nano EmberholmPortal_ABI.json
# Pegar el JSON del ABI
```

---

## 💻 IMPLEMENTACIÓN BACKEND

### 1. Agregar Web3 Module a app.py

```python
# Al inicio de app.py
from web3_integration import get_web3_manager

# Después de crear Flask app
app = Flask(__name__)

# Inicializar Web3Manager
try:
    web3_mgr = get_web3_manager()
    logger.info("✅ Web3 integration initialized")
except Exception as e:
    logger.error(f"❌ Web3 initialization failed: {e}")
    web3_mgr = None
```

### 2. Modificar Endpoint: Start Mission

Reemplazar tu función `start_mission()` con:

```python
@app.route("/api/mission/start", methods=["POST"])
def start_mission():
    """
    Inicia una misión con staking gasless.
    """
    if not web3_mgr:
        return jsonify({"error": "Web3 not configured"}), 500

    data = request.json
    wallet = data.get("wallet")
    token_id_str = data.get("token_id")
    mission_id = data.get("mission_id")
    message = data.get("message")
    signature = data.get("signature")

    # Validaciones
    if not all([wallet, token_id_str, mission_id, message, signature]):
        return jsonify({"error": "Missing required fields"}), 400

    token_id = int(token_id_str)

    # Verificar firma
    is_valid = web3_mgr.verify_signature(message, signature, wallet)
    if not is_valid:
        return jsonify({"error": "Invalid signature"}), 401

    # Verificar timestamp (prevenir replay attacks)
    try:
        timestamp = int(message.split(" at ")[-1])
        if abs(time.time() * 1000 - timestamp) > 300000:  # 5 min
            return jsonify({"error": "Signature expired"}), 401
    except:
        return jsonify({"error": "Invalid message format"}), 400

    # Verificar ownership
    is_owner = web3_mgr.verify_nft_ownership(token_id, wallet)
    if not is_owner:
        return jsonify({"error": "Not the owner"}), 403

    # TU LÓGICA EXISTENTE
    db = load_nfts_database()
    hero = db.get(token_id_str)

    if not hero:
        return jsonify({"error": "Hero not found"}), 404

    if hero["dynamic_state"]["state"] != "READY":
        return jsonify({"error": "Hero not ready"}), 400

    # ... más validaciones ...

    # STAKEAR ON-CHAIN (backend paga gas)
    success, tx_hash = web3_mgr.stake_token(token_id)
    if not success:
        return jsonify({"error": "Failed to stake NFT"}), 500

    # Actualizar backend
    hero["dynamic_state"]["state"] = "ON_MISSION"
    hero["dynamic_state"]["current_mission_id"] = mission_id
    hero["dynamic_state"]["mission_start_time"] = now_utc_str()

    save_nfts_database(db)

    return jsonify({
        "success": True,
        "message": "Mission started!",
        "tx_hash": tx_hash
    }), 200
```

Ver **`gasless_staking_example.py`** para código completo.

### 3. Modificar Endpoint: Complete Mission

```python
@app.route("/api/mission/complete", methods=["POST"])
def complete_mission():
    """
    Completa misión con unstaking gasless.
    """
    # ... validaciones similares a start_mission ...

    # TU LÓGICA: calcular recompensas
    reward_xp = 100
    reward_aura = 10

    # Actualizar backend
    hero["dynamic_state"]["state"] = "READY"
    hero["dynamic_state"]["xp_total"] += reward_xp
    hero["dynamic_state"]["aura_level"] += reward_aura

    save_nfts_database(db)

    # UNSTAKEAR ON-CHAIN (backend paga gas)
    success, tx_hash = web3_mgr.unstake_token(token_id)

    if not success:
        logger.warning(f"Failed to unstake but rewards granted")

    return jsonify({
        "success": True,
        "rewards": {"xp": reward_xp, "aura": reward_aura},
        "tx_hash": tx_hash
    }), 200
```

---

## 🎨 IMPLEMENTACIÓN FRONTEND

### 1. Agregar Script a index.html

```html
<!-- Al final del <body>, antes de cerrar -->
<script src="/static/js/gasless_staking_frontend.js"></script>
```

### 2. Modificar Botones de Misiones

Antes:
```html
<button onclick="startMission('00123', '001')">
    Start Mission
</button>
```

Después:
```html
<button
    class="start-mission-btn"
    data-token-id="00123"
    data-mission-id="001">
    Start Mission (No Gas!)
</button>
```

### 3. JavaScript Actualizado

El archivo `gasless_staking_frontend.js` ya tiene todo el código.

**Funciones principales:**
- `startMissionGasless(tokenId, missionId, wallet)` - Inicia misión
- `completeMissionGasless(tokenId, wallet)` - Completa misión
- `signMessage(message, wallet)` - Firma mensajes off-chain

---

## 🧪 TESTING

### 1. Test en Testnet (Base Sepolia)

```bash
# 1. Configurar .env con Base Sepolia RPC
WEB3_RPC_URL=https://base-sepolia.infura.io/v3/YOUR_KEY

# 2. Fondear mission manager wallet
# Usar faucet: https://www.coinbase.com/faucets/base-ethereum-goerli-faucet

# 3. Deployar contrato en testnet
# (usar Remix o Hardhat)

# 4. Actualizar CONTRACT_ADDRESS en .env

# 5. Ejecutar backend
python app.py

# 6. Probar flujo completo:
# - Conectar wallet
# - Iniciar misión (firmar mensaje)
# - Verificar NFT stakeado on-chain
# - Esperar o simular tiempo
# - Completar misión (firmar mensaje)
# - Verificar NFT unstakeado
```

### 2. Verificar Transacciones

**Base Sepolia Explorer:**
https://sepolia.basescan.org/

Buscar:
- Transaction hash del stake
- Transaction hash del unstake
- Verificar `stakedTokens[tokenId]` en contract

### 3. Test de Seguridad

```javascript
// Test 1: Firma inválida (debe fallar)
await startMissionGasless('00001', '001', 'WRONG_WALLET');
// ❌ Expected: "Invalid signature"

// Test 2: No ownership (debe fallar)
await startMissionGasless('99999', '001', currentWallet);
// ❌ Expected: "Not the owner"

// Test 3: Firma expirada (debe fallar)
// Modificar timestamp en mensaje a hace 10 minutos
// ❌ Expected: "Signature expired"

// Test 4: Replay attack (debe fallar)
// Intentar reenviar misma firma 2 veces
// ❌ Expected: "Hero not ready" (ya en misión)
```

---

## 🚀 DEPLOYMENT

### Pre-Deployment Checklist

- [ ] Contract deployado en Base Mainnet
- [ ] Contract verificado en Basescan
- [ ] Mission Manager configurado como `missionManager` en contrato
- [ ] Mission Manager wallet fondeada (0.1 ETH+)
- [ ] `.env` con valores de producción
- [ ] `CONTRACT_ABI_PATH` correcto
- [ ] Testing completo en testnet

### Deployment Steps

```bash
# 1. Set production environment
export FLASK_ENV=production

# 2. Verificar configuración
python -c "from web3_integration import get_web3_manager; mgr = get_web3_manager(); print('✅ Config OK')"

# 3. Deploy backend
# (Render, Railway, AWS, etc.)

# 4. Verificar logs
# Debe aparecer: "✅ Web3 integration initialized"
```

### Post-Deployment

1. **Monitorear balance de Mission Manager:**
   ```python
   # Agregar endpoint de health check
   @app.route("/api/health/web3")
   def web3_health():
       balance = web3_mgr.w3.eth.get_balance(web3_mgr.mission_manager_address)
       balance_eth = web3_mgr.w3.from_wei(balance, 'ether')

       return jsonify({
           "web3_connected": web3_mgr.w3.is_connected(),
           "mission_manager_balance": float(balance_eth),
           "contract_address": web3_mgr.contract_address
       })
   ```

2. **Configurar alertas:**
   - Si balance < 0.01 ETH → enviar alerta
   - Si transacción falla → logging + alerta

---

## 💰 COSTOS Y OPTIMIZACIÓN

### Costos Detallados

**Base Mainnet (típico):**
- Gas price: 0.01-0.1 gwei
- Stake: ~50,000 gas
- Unstake: ~30,000 gas

**Costo por misión:**
```
Stake:   50,000 × 0.05 gwei = 0.0025 gwei = $0.01
Unstake: 30,000 × 0.05 gwei = 0.0015 gwei = $0.007
TOTAL: ~$0.017 por misión
```

### Optimizaciones

#### 1. Batch Unstaking
Si tienes muchas misiones completando al mismo tiempo:

```python
def batch_unstake(token_ids: list):
    """Unstakear múltiples NFTs en una transacción."""
    # Requiere modificar contrato para tener batchUnstake()
    pass
```

#### 2. Gas Price Optimization
```python
# En web3_integration.py
def get_optimal_gas_price():
    """Usa gas price bajo en horarios de poco uso."""
    current_hour = datetime.now().hour

    # Base es más barato en horarios de baja actividad
    if 2 <= current_hour <= 8:  # Madrugada
        return w3.eth.gas_price  # Precio normal
    else:
        return w3.eth.gas_price * 1.5  # Prioridad
```

#### 3. Queue System
Para manejar picos de demanda:

```python
# Usar Celery o RQ para cola de transacciones
from rq import Queue
from redis import Redis

q = Queue(connection=Redis())

def stake_async(token_id):
    job = q.enqueue(web3_mgr.stake_token, token_id)
    return job.id
```

### ROI con $EMBER Token

Cuando implementen tokenomics:

```
Fee por misión: 5 $EMBER tokens
Valor $EMBER: $0.02
Revenue: 5 × $0.02 = $0.10

Costo gas: $0.017
Profit: $0.10 - $0.017 = $0.083 por misión

Con 1,000 misiones/día: $83/día profit = $2,490/mes
```

---

## 🔧 TROUBLESHOOTING

### Error: "Web3 not configured"

**Causa:** `.env` no cargado o valores incorrectos

**Solución:**
```bash
# Verificar variables
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('WEB3_RPC_URL'))"

# Si no aparece, cargar dotenv:
pip install python-dotenv

# En app.py
from dotenv import load_dotenv
load_dotenv()
```

### Error: "Failed to connect to RPC"

**Causa:** RPC URL inválido o API key incorrecta

**Solución:**
```bash
# Test conexión manualmente
python -c "from web3 import Web3; w3 = Web3(Web3.HTTPProvider('TU_RPC_URL')); print(w3.is_connected())"

# Debe imprimir: True
```

### Error: "Insufficient funds"

**Causa:** Mission Manager wallet sin balance

**Solución:**
```bash
# Verificar balance
python -c "from web3_integration import get_web3_manager; mgr = get_web3_manager(); balance = mgr.w3.eth.get_balance(mgr.mission_manager_address); print(f'{mgr.w3.from_wei(balance, \"ether\")} ETH')"

# Fondear wallet desde exchange o bridge
```

### Error: "Invalid signature"

**Causa:** Mensaje no coincide o wallet incorrecta

**Solución:**
```javascript
// Verificar formato de mensaje
console.log(message);
// Debe ser: "Start mission 001 with token 00123 at 1732454400000"

// Verificar wallet usada para firmar
console.log(wallet, currentWallet);
// Deben coincidir exactamente
```

### Error: "Cooldown not elapsed"

**Causa:** Intentando unstakear muy rápido (cooldown de 2h)

**Solución:**
- Esperar 2 horas desde último unstake
- O remover cooldown del contrato (no recomendado)

### Transacción Pending por Mucho Tiempo

**Causa:** Gas price muy bajo

**Solución:**
```python
# Aumentar gas price en web3_integration.py
'maxFeePerGas': self.w3.eth.gas_price * 3,  # 3x en lugar de 2x
```

---

## 📚 RECURSOS ADICIONALES

- **Base Docs:** https://docs.base.org
- **Web3.py Docs:** https://web3py.readthedocs.io
- **Infura Docs:** https://docs.infura.io
- **Basescan:** https://basescan.org

---

## ✅ CHECKLIST FINAL

Antes de ir a producción:

- [ ] ✅ Contrato deployado y verificado
- [ ] ✅ Mission Manager configurado en contrato
- [ ] ✅ Web3 integration module agregado
- [ ] ✅ Endpoints modificados (start/complete)
- [ ] ✅ Frontend actualizado con firmas
- [ ] ✅ Testing completo en testnet
- [ ] ✅ `.env` con valores de producción
- [ ] ✅ Mission Manager wallet fondeada
- [ ] ✅ Monitoring y alertas configuradas
- [ ] ✅ Backup de private keys seguro

---

**🎉 ¡Listo! Tus usuarios ahora pueden jugar sin pagar gas.**

Para soporte: [Discord/Telegram de tu proyecto]
