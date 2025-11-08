# 🔥 SISTEMA DE MISIONES COMPLETO - EMBERHOLM PORTAL
## "Mantener viva la llama"

Este documento describe el sistema completo de misiones con:
- ✅ Staking durante misiones (3h, 6h, 12h)
- ✅ Probabilidad de éxito/fallo
- ✅ Pérdida de XP si falla
- ✅ **Muerte del Emisario (muy rara, < 2%)**
- ✅ **Ritual de Reinvocación**
- ✅ Integración completa con el whitepaper

---

## 📋 CONFIGURACIÓN DE MISIONES

### Dificultades y Tiempos

| Difficulty | Duration | Energy | XP Reward | Aura | Success % | Fail Loss | Death % |
|------------|----------|--------|-----------|------|-----------|-----------|---------|
| **EASY**   | 3 horas  | 10     | 60        | 4    | 92%       | -25 XP    | 0%      |
| **MEDIUM** | 6 horas  | 18     | 180       | 12   | 78%       | -60 XP    | 0.5%    |
| **HARD**   | 12 horas | 30     | 500       | 30   | 60%       | -150 XP   | 2.0%    |

### Misiones por Gremio

#### Forge Legion
- **EASY**: The Lost Forge (Orc Warrior favored)
- **HARD**: Dragon's Flame Ritual (Dragonborn Warrior favored)

#### Circle of Mist
- **EASY**: Mist Archives Research (Elf Wizard favored)
- **MEDIUM**: Interference Node Containment (Elf Wizard favored)

#### Shadow Guild
- **EASY**: Shadow Patrol (Tiefling Rogue favored)
- **HARD**: Silent Infiltration: Core Vault (Demon Rogue favored)

#### Horizon Watch
- **MEDIUM**: Tideborn Rescue (Triton Ranger favored)

#### Dawnkeepers
- **MEDIUM**: Sanctum Defense (Human Paladin favored)

#### Echoes of the Veil
- **HARD**: Veil Breach Containment (Gith Necromancer favored)

---

## 🎲 SISTEMA DE PROBABILIDADES

### Cálculo de Éxito

```
Base Success Rate (de la misión)
+ Guild Bonus (+12% si guild coincide)
+ Class Bonus (+8% si class coincide)
+ Race Bonus (+5% si race coincide)
+ Level Bonus (+1% cada 10 niveles)
+ Aura Bonus (+1% cada 100 Aura)
= Total Success Rate (máx 98%)
```

### Perfect Alignment Bonus

Si **guild + class + race** coinciden:
- +50% XP reward
- +50% Aura reward
- Achievement: "Perfect Alignment"

### Ejemplos

**Ejemplo 1: Jugador Novato en EASY**
- Base: 92%
- No bonuses
- Total: 92% éxito
- Roll 1-100, si ≤ 92 = éxito

**Ejemplo 2: Veterano con Afinidades en HARD**
- Base: 60%
- Guild match: +12%
- Class match: +8%
- Race match: +5%
- Level 50: +5%
- Aura 300: +3%
- Total: 93% éxito (casi garantizado!)

---

## 💀 SISTEMA DE MUERTE

### Trigger de Muerte

1. La misión debe fallar primero (roll > success rate)
2. Si falla, hacer death roll (1-1000)
3. Si death roll ≤ (death_chance × 10 - protecciones):
   - MUERTE

### Protecciones contra Muerte

```python
# Nivel alto protege
if hero_level >= 50:
    protection += (hero_level // 50) * 5

# Aura alta protege
if hero_aura >= 500:
    protection += (hero_aura // 500) * 3
```

**Ejemplo:**
- Misión HARD: 2.0% death base = 20/1000
- Hero nivel 100: -10 protection
- Hero aura 1000: -6 protection
- Total: 20 - 10 - 6 = 4/1000 = 0.4% muerte

### Consecuencias de Muerte

```python
hero["status"] = "FALLEN"
hero["xp_total"] -= 300
hero["aura_level"] -= 50
hero["death_count"] += 1

# El NFT queda inutilizable hasta reinvocación
# NO puede hacer misiones
# NO puede ser transferido (sigue staked)
```

---

## 🔥 RITUAL DE REINVOCACIÓN

### Costos Escalables

| Deaths | XP Cost | Aura Cost | Description |
|--------|---------|-----------|-------------|
| 1st    | 500     | 100       | "The Portal remembers your essence" |
| 2nd    | 1,500   | 300       | "The veil grows thicker" |
| 3rd    | 5,000   | 1,000     | "Your soul fragments scatter" |
| 4th+   | 10,000  | 2,500     | "The Flame barely recognizes you" |

### Mecánica del Ritual

1. **Usuario selecciona sus PROPIOS emisarios vivos** para sacrificar
2. **Dona XP y Aura** de esos emisarios (de tu misma wallet)
3. **Total debe alcanzar** el costo requerido
4. **Fallen Hero revive** con:
   - 100 XP
   - 20 Aura
   - 50% energy
   - Achievement "Reborn from Ash"

**Importante:** Solo puedes usar tus propios NFTs. No necesitas ayuda de otros jugadores.

### Ejemplo de Ritual

```
Fallen Hero: Kaelthar (#00042) - TU NFT
Death Count: 1
Required: 500 XP, 100 Aura

Sacrifice from TUS OTROS NFTs:
- Drax (#00001): 300 XP, 50 Aura (también tuyo)
- Sera (#00005): 200 XP, 50 Aura (también tuyo)
Total: 500 XP, 100 Aura ✅

Result:
✅ Kaelthar revives (100 XP, 20 Aura)
❌ Drax loses 300 XP, 50 Aura
❌ Sera loses 200 XP, 50 Aura

Todos siguen siendo tuyos, solo redistribuyes XP/Aura entre ellos.
```

---

## 🏆 ACHIEVEMENTS RELACIONADOS

### Muerte
- **Fallen Hero** 💀: Experience death for the first time
- **Phoenix Soul** 🦅: Be reinvoked 3 times
- **Unkillable** 👑: Be reinvoked 10 times

### Reinvocación
- **Reborn from Ash** 🔥: Complete your first reinvocation
- **Selfless Sacrifice** 🤝: Donate XP to reinvoke another
- **Resurrection Master** ✨: Reinvoke 5 different emissaries

### Misiones Perfectas
- **Perfect Alignment** ⭐: Complete mission with all afinities matching
- **Flawless Streak** 🌟: Complete 10 missions without failure
- **Death Defier** 🛡️: Survive 100 HARD missions without dying

---

## 🔄 FLUJO COMPLETO DE MISIÓN

### Fase 1: Iniciar Misión

```
1. Usuario selecciona misión en frontend
2. Frontend muestra:
   - Duración (3h, 6h, 12h)
   - Success rate calculada
   - Recompensas
   - Riesgos (XP loss, death %)
   - Lore de la misión
3. Usuario confirma
4. Frontend llama contract.stakeToken(tokenId)
5. Backend registra misión activa con timestamp
6. NFT queda bloqueado on-chain
```

### Fase 2: Misión en Progreso

```
1. NFT está staked (no se puede transferir)
2. Frontend muestra:
   - Tiempo restante
   - Barra de progreso
   - Estado "ON_MISSION"
3. Usuario puede ver otras estadísticas pero no puede:
   - Iniciar otra misión con ese NFT
   - Transferir el NFT
   - Vender en OpenSea
```

### Fase 3: Completar Misión

```
1. Usuario hace clic en "Complete Mission"
2. Backend verifica que tiempo haya pasado
3. Backend hace roll de éxito/fallo
4. Si falla y hay death_chance:
   - Hace death roll
   - Si death roll falla: MUERTE
5. Aplica recompensas o penalizaciones
6. Backend llama contract.unstakeToken(tokenId)
7. NFT queda desbloqueado
8. Grant achievements si aplica
9. Update metadata con nuevos stats
```

### Fase 4a: Si Murió

```
1. Hero status = "FALLEN"
2. Frontend muestra pantalla de muerte épica
3. Usuario puede:
   - Ver ritual de reinvocación
   - Seleccionar otros NFTs para sacrificar
   - Confirmar ritual
4. Fallen hero revive con stats bajos
5. Achievement "Reborn from Ash"
```

### Fase 4b: Si Sobrevivió

```
1. Frontend muestra resultado (éxito/fallo)
2. XP y Aura actualizados
3. Achievements otorgados
4. Hero disponible para nueva misión
5. Metadata updated en OpenSea
```

---

## 💡 BALANCE Y ECONOMÍA

### Expected Value (EV) por Misión

**EASY:**
```
EV = (0.92 × 60) - (0.08 × 25) = 55.2 - 2 = +53.2 XP
Time: 3h
XP/hour: 17.7
```

**MEDIUM:**
```
EV = (0.78 × 180) - (0.22 × 60) - (0.005 × 300) = 140.4 - 13.2 - 1.5 = +125.7 XP
Time: 6h
XP/hour: 21.0
```

**HARD:**
```
EV = (0.60 × 500) - (0.38 × 150) - (0.02 × 300) = 300 - 57 - 6 = +237 XP
Time: 12h
XP/hour: 19.8
```

**Conclusión:**
- MEDIUM tiene mejor XP/hora
- HARD tiene mejor XP total pero más riesgo
- EASY es el más seguro pero más lento

### Estrategias de Jugadores

**Low-level players:**
- Hacer solo EASY hasta nivel 20
- 0% riesgo de muerte
- Progresión lenta pero segura

**Mid-level players:**
- MEDIUM con afinidades
- Balance riesgo/recompensa
- 0.5% muerte manejable

**High-level players:**
- HARD con afinidades perfectas
- 85%+ success rate
- Muerte < 1% con protecciones
- XP masivo

**Min-maxers:**
- Rotar MEDIUM (mejor XP/hora)
- Hacer HARD solo con perfect alignment
- Mantener 2-3 heroes de backup para ritual

---

## 🎮 UX/UI RECOMENDACIONES

### Mission Select Screen

```
╔════════════════════════════════════════════════════════╗
║  AVAILABLE MISSIONS — ROTATION ENDS IN 48H            ║
╠════════════════════════════════════════════════════════╣
║                                                         ║
║  [EASY] The Lost Forge                      3h  ⚡10   ║
║  ├─ Success: 92% → 100% (Perfect Match! ⭐)           ║
║  ├─ Reward: 60 XP, 4 Aura                              ║
║  └─ Risk: -25 XP on fail, 0% death                     ║
║                                                         ║
║  [MEDIUM] Interference Node               6h  ⚡18     ║
║  ├─ Success: 78% → 103% (Guaranteed ✓)                ║
║  ├─ Reward: 180 XP, 12 Aura                            ║
║  └─ Risk: -60 XP on fail, 0.5% death                   ║
║                                                         ║
║  [HARD] Veil Breach Containment          12h  ⚡30     ║
║  ├─ Success: 60% → 85% (Good Odds)                     ║
║  ├─ Reward: 500 XP, 30 Aura                            ║
║  └─ Risk: -150 XP on fail, 💀 2.0% DEATH              ║
║                                                         ║
╚════════════════════════════════════════════════════════╝
```

### Mission In Progress

```
╔════════════════════════════════════════════════════════╗
║  🔒 MISSION IN PROGRESS                                ║
╠════════════════════════════════════════════════════════╣
║                                                         ║
║  Veil Breach Containment (HARD)                        ║
║                                                         ║
║  Your emissary negotiates with spectrals beyond        ║
║  the veil. Will they return?                           ║
║                                                         ║
║  ⏱️ Time Remaining: 8h 32m 15s                         ║
║  📊 Progress: [████████░░░░] 67%                      ║
║                                                         ║
║  🔒 NFT #42 is STAKED                                  ║
║  Cannot transfer until mission completes               ║
║                                                         ║
║  Expected Completion: 2024-01-15 18:30 UTC            ║
║                                                         ║
║  [ REFRESH ]  [ VIEW STATS ]                           ║
╚════════════════════════════════════════════════════════╝
```

### Death Screen

```
╔════════════════════════════════════════════════════════╗
║           💀 THE FLAME HAS EXTINGUISHED 💀             ║
╠════════════════════════════════════════════════════════╣
║                                                         ║
║  Veil Breach Containment — MISSION FAILED              ║
║                                                         ║
║  "Death itself bleeds through the veil.                ║
║   Your emissary did not return."                       ║
║                                                         ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   ║
║                                                         ║
║  Kaelthar the Voidwalker has fallen.                   ║
║                                                         ║
║  Status: FALLEN 💀                                     ║
║  XP Lost: -300 (5,200 → 4,900)                        ║
║  Aura Lost: -50 (120 → 70)                            ║
║  Death Count: 1                                        ║
║                                                         ║
║  This emissary cannot be used until reinvoked.         ║
║                                                         ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   ║
║                                                         ║
║  🔥 REINVOCATION RITUAL AVAILABLE                      ║
║                                                         ║
║  Cost: 500 XP, 100 Aura (from other emissaries)       ║
║                                                         ║
║  "The Portal remembers. Sacrifice from the living      ║
║   to restore the fallen. Will you answer the call?"    ║
║                                                         ║
║  [ BEGIN RITUAL ]  [ RETURN TO PORTAL ]                ║
╚════════════════════════════════════════════════════════╝
```

---

## 🔐 INTEGRACIÓN CON SMART CONTRACT

### Staking Functions

```javascript
// Al iniciar misión
await contract.stakeToken(tokenId);
// NFT bloqueado, no se puede transferir

// Al completar misión
await contract.unstakeToken(tokenId);
// NFT desbloqueado
```

### Backend Monitoring

```python
# Backend escucha eventos
contract.events.TokenStaked().on('data', event => {
    # Registrar misión activa
    start_mission(event.returnValues.tokenId)
})

contract.events.TokenUnstaked().on('data', event => {
    # Completar misión
    complete_mission(event.returnValues.tokenId)
})
```

---

## 📝 METADATA ACTUALIZADA

### Dynamic Attributes

```json
{
  "name": "Kaelthar the Voidwalker",
  "image": "ipfs://...",
  "attributes": [
    {"trait_type": "Status", "value": "FALLEN 💀"},
    {"trait_type": "XP Total", "value": 4900},
    {"trait_type": "Aura", "value": 70},
    {"trait_type": "Death Count", "value": 1},
    {"trait_type": "Reinvocations", "value": 0},
    {"trait_type": "Last Mission", "value": "Veil Breach Containment"},
    {"trait_type": "Mission Result", "value": "DEATH"},
    {"trait_type": "Achievement: Fallen Hero", "value": "✅"},
    {"trait_type": "Total Missions", "value": 42},
    {"trait_type": "Success Rate", "value": "88%"}
  ]
}
```

---

## 🎯 IMPLEMENTACIÓN PRIORITARIA

### Fase 1 (MVP):
1. ✅ Sistema de misiones básico (3 dificultades)
2. ✅ Staking on-chain durante misión
3. ✅ Probabilidad de éxito/fallo
4. ✅ Pérdida de XP en fallo

### Fase 2 (Core):
5. ✅ Probabilidad de muerte (< 2%)
6. ✅ Estado FALLEN
7. ✅ Ritual de reinvocación básico
8. ✅ Achievements de muerte/reinvocación

### Fase 3 (Polish):
9. ✅ Perfect alignment bonuses
10. ✅ Costos escalables de ritual
11. ✅ Protecciones por nivel/aura
12. ✅ Lore messages épicos

---

## 🔥 CONCLUSIÓN

Este sistema:

✅ **Respeta el whitepaper** - "Mantener viva la llama" literal
✅ **Crea tensión** - Cada misión HARD es épica
✅ **Fomenta comunidad** - Necesitas ayuda para reinvocar
✅ **Balance económico** - EASY safe, MEDIUM optimal, HARD risky
✅ **Lore profundo** - Muerte y reinvocación son parte de la narrativa
✅ **Progresión justa** - Nivel/aura reducen riesgo de muerte
✅ **OpenSea integration** - Todo visible en metadata

**La muerte es rara pero REAL. Hace que Emberholm sea legendario.** 🔥

---

**Próximo paso: ¿Implementar en código?**
