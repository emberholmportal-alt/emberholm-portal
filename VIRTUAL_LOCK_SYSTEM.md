# 🔒 Sistema de Bloqueo Virtual - Emberholm Portal

## ✅ Decisión de Diseño

**Fecha:** 2025-01-09
**Decisión:** Usar **bloqueo virtual (solo backend)** en lugar de staking on-chain.

### Razón
Los usuarios **NO deben gastar gas** para jugar misiones. El costo de $0.20-0.50 USD por misión en mainnet crearía una barrera de entrada y quitaría diversión al juego.

---

## 🎮 Cómo Funciona

### **Sistema Actual: Bloqueo Virtual**

1. **Inicio de Misión:**
   - Usuario presiona `[SEND]` en PROFILE o MISSIONS
   - Frontend llama a `/api/mission/start`
   - Backend actualiza `dynamic_state.state = "ON_MISSION"` en `players.json`
   - **NO hay transacción blockchain**
   - **NO se paga gas**

2. **Durante la Misión:**
   - Hero en estado `ON_MISSION` (bloqueado virtualmente)
   - No puede iniciar otra misión hasta completar o cancelar
   - UI muestra botón `[IN PROGRESS]` (disabled)
   - Contador de tiempo restante

3. **Completar Misión:**
   - Cuando tiempo transcurre, botón cambia a `[CLAIM REWARDS]`
   - Usuario presiona botón
   - Backend calcula resultado (SUCCESS/FAILURE/DEATH)
   - Actualiza XP, Aura, Energy
   - Cambia estado a `READY` o `FALLEN`
   - **NO hay transacción blockchain**

4. **Si NFT se transfiere durante misión:**
   - Misión se cancela automáticamente (futura implementación)
   - Hero vuelve a estado `READY`
   - Energía ya gastada no se recupera

---

## 📁 Flujo de Datos

### **1. Inicio de Misión**

```
Frontend (index.html)
    ↓
POST /api/mission/start
    ↓
Backend (app.py:1059-1170)
    ↓
players.json:
    hero.dynamic_state.state = "ON_MISSION"
    hero.dynamic_state.mission_start_time = "2025-01-09T..."
    hero.dynamic_state.current_mission_id = "004"
    hero.dynamic_state.energy_current -= energy_cost
    ↓
active_missions.json:
    "0xWALLET_00001": {
        "wallet": "0xWALLET",
        "hero_id": "00001",
        "mission_id": "004",
        "start_time": "2025-01-09T...",
        "duration_hours": 6
    }
```

### **2. Completar Misión (SUCCESS)**

```
Frontend (index.html)
    ↓
POST /api/mission/complete
    ↓
Backend (app.py:1172-1405)
    ↓
Calcular resultado:
    - Roll probabilidad
    - Aplicar bonuses (guild, class, race)
    - Determinar outcome (SUCCESS/FAILURE/DEATH)
    ↓
Si SUCCESS:
    players.json:
        hero.dynamic_state.xp_total += xp_gained
        hero.dynamic_state.aura_level += aura_gained
        hero.dynamic_state.state = "READY"
        hero.dynamic_state.total_missions_completed += 1
    ↓
    stats.json:
        missions_completed += 1
        total_exp_collected += xp_gained
        total_aura_collected += aura_gained
        guild_ranking[guild_name].xp += xp_gained
        guild_ranking[guild_name].aura += aura_gained
        guild_ranking[guild_name].successes += 1
    ↓
    guilds.json (vía calculate_guilds_data()):
        Recalcula members, total_xp, total_aura, avg_xp, avg_aura
        por cada guild
    ↓
    Eliminar de active_missions.json
```

### **3. Acumulación de Stats Globales**

```
Mission Complete SUCCESS
    ↓
app.py:1267-1269
    stats_obj["missions_completed"] += 1
    stats_obj["total_exp_collected"] += xp_gain
    stats_obj["total_aura_collected"] += aura_gain
    ↓
app.py:1272
    update_guild_stats(guild_name, xp_gain, aura_gain, stats_obj)
        ↓
        app.py:609-617
        guild_ranking[guild_name]["xp"] += xp_gain
        guild_ranking[guild_name]["aura"] += aura_gain
        guild_ranking[guild_name]["successes"] += 1
        ↓
        app.py:620
        calculate_guilds_data()
            ↓
            app.py:543-588
            Itera todos los players.json
            Calcula stats reales por guild
            Actualiza guilds.json
    ↓
app.py:1288-1289
    save_json(PLAYERS_PATH, players_all)
    save_json(STATS_PATH, stats_obj)
```

---

## ✅ Ventajas del Sistema Virtual

1. **Gratis para usuarios**: $0 en gas, infinitas misiones
2. **UX perfecta**: Sin aprobaciones de MetaMask
3. **Rápido**: Instant start/complete
4. **Simple**: Solo código backend
5. **Escalable**: No depende de gas prices

---

## ⚠️ Consideraciones

### **Seguridad**

**No previene transfers durante misión:**
- Usuario PUEDE transferir/vender NFT mientras está en misión
- Si esto sucede, la misión se cancela automáticamente

**Mitigación:**
```python
# Futura implementación en /api/mission/complete
current_owner = get_nft_owner(token_id)  # Leer de blockchain
if current_owner != mission_starter:
    # Cancelar misión
    hero.dynamic_state.state = "READY"
    return {"cancelled": True, "reason": "NFT ownership changed"}
```

### **Fairness**

**Si un usuario transfiere NFT durante misión:**
- La misión se cancela
- El NFT vuelve a estado `READY`
- Energía ya gastada **NO** se devuelve (penalización)
- Nuevo dueño puede usar el NFT normalmente

**No es un exploit crítico porque:**
- Vender NFT durante misión = perder progreso de esa misión
- No hay incentivo económico para hacerlo
- Energía perdida es suficiente penalización

---

## 📊 Archivos de Datos

### **players.json**
```json
{
  "0xWALLET_ADDRESS": {
    "wallet": "0xWALLET_ADDRESS",
    "heroes": [
      {
        "token_id": "00001",
        "name": "Thorin Ironheart",
        "race_class": "Orc Warrior",
        "guild": "Forge Legion",
        "dynamic_state": {
          "xp_total": 465,
          "aura_level": 23,
          "energy_current": 70,
          "energy_max": 100,
          "state": "ON_MISSION",  // ← Bloqueo virtual
          "current_mission_id": "007",
          "mission_start_time": "2025-01-09T10:00:00Z",
          "total_missions_completed": 15
        }
      }
    ]
  }
}
```

### **active_missions.json**
```json
{
  "0xWALLET_00001": {
    "wallet": "0xWALLET",
    "hero_id": "00001",
    "mission_id": "007",
    "start_time": "2025-01-09T10:00:00Z",
    "duration_hours": 12
  }
}
```

### **stats.json**
```json
{
  "total_characters": 2,
  "missions_completed": 27,
  "missions_failed": 8,
  "total_exp_collected": 3450,
  "total_aura_collected": 285,
  "guild_ranking": {
    "Forge Legion": {
      "xp": 1875,
      "aura": 150,
      "successes": 18,
      "failures": 4
    },
    "Circle of Mist": {
      "xp": 1575,
      "aura": 135,
      "successes": 9,
      "failures": 4
    }
  }
}
```

### **guilds.json**
```json
[
  {
    "name": "Forge Legion",
    "flavor": "strength, steel, sworn oaths",
    "members": 1,          // ← Calculado desde players.json
    "avg_xp": 465.0,       // ← total_xp / members
    "avg_aura": 23.0,      // ← total_aura / members
    "total_xp": 465,       // ← Suma de todos los heroes
    "total_aura": 23,
    "badge": "img/forge_legion.JPG"
  }
]
```

---

## 🔄 Posibles Mejoras Futuras

### **1. Detección de Transfers**
```python
# En /api/mission/complete o background job
def check_mission_ownership():
    for mission in active_missions:
        current_owner = contract.ownerOf(mission.token_id)
        if current_owner != mission.wallet:
            cancel_mission(mission)
```

### **2. Penalización por Transfer**
```python
# Si se detecta transfer durante misión
hero.dynamic_state.state = "READY"
hero.dynamic_state.current_mission_id = None
# NO devolver energía (penalización)
```

### **3. Sistema de Reputación**
```python
# Track usuarios que transfieren durante misiones
if transfer_during_mission_count > 3:
    wallet_reputation = "SUSPICIOUS"
    # Aplicar cooldowns más largos
```

---

## 🎯 Resumen

| Aspecto | Implementación |
|---------|----------------|
| **Bloqueo** | Virtual (solo backend) |
| **Gas Cost** | $0 |
| **Previene Transfers** | ❌ No (detecta y cancela) |
| **UX** | ⭐⭐⭐⭐⭐ Perfecta |
| **Seguridad** | ⭐⭐⭐ Suficiente |
| **Costo Proyecto** | $0 |
| **Escalabilidad** | ⭐⭐⭐⭐⭐ Infinita |

---

## 🚀 Comparación con Otras Opciones

### **❌ Staking On-Chain (Descartado)**
- Usuario paga $0.20-0.50 por misión
- Bloqueo real en blockchain
- UX con 2 aprobaciones MetaMask
- **Descartado:** Barrera de entrada muy alta

### **❌ Backend Paga Staking (Descartado)**
- Proyecto paga gas por todos los usuarios
- $20-50/día con 100 misiones
- Insostenible económicamente
- **Descartado:** Muy costoso

### **✅ Bloqueo Virtual (SELECCIONADO)**
- Gratis para todos
- UX perfecta
- Suficientemente seguro para el juego
- **Seleccionado:** Balance perfecto

---

## 📝 Conclusión

El sistema de **bloqueo virtual** permite que Emberholm Portal sea un juego **accesible y divertido** sin barreras económicas, mientras mantiene la integridad del gameplay y la acumulación correcta de stats.

**No nos interesa prevenir que un NFT se venda durante misión** - simplemente cancelamos la misión y devolvemos el NFT a estado READY. La energía perdida es penalización suficiente.

Todos los datos (XP, Aura, Misiones, Stats, Guilds) se acumulan correctamente en:
- ✅ `players.json` - Stats individuales por hero
- ✅ `stats.json` - Stats globales y guild ranking
- ✅ `guilds.json` - Stats por guild (recalculado automáticamente)
- ✅ `active_missions.json` - Misiones en curso
