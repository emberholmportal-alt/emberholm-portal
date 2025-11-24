# 🔥 CAMBIOS EN GENERATOR.PY PARA ITEMS Y RANGOS

## 📋 RESUMEN EJECUTIVO

El generador ha sido actualizado para crear metadata NFT compatible con los futuros sistemas de **Items** y **Rangos**, sin romper compatibilidad con NFTs existentes.

---

## 🆚 COMPARACIÓN: ANTES vs DESPUÉS

### ❌ METADATA ANTERIOR (generator.py original)

```json
{
  "dynamic_state": {
    "current_guild": "Order of Dawn",
    "xp_total": 0,
    "xp_level": 1,
    "aura_level": 0,
    "energy_current": 100,
    "energy_max": 100,
    "power_current": 12,
    "last_update": "2025-11-24T00:00:00Z"
  }
}
```

**Problemas:**
- ❌ No tiene `state` (READY/ON_MISSION/FALLEN)
- ❌ No tiene campos de misiones (`current_mission_id`, `mission_start_time`, etc.)
- ❌ No tiene `death_count`, `fallen_time`
- ❌ No tiene `mission_history`, `total_missions_completed`, `total_missions_failed`
- ❌ **NO TIENE SOPORTE PARA ITEMS**
- ❌ **NO TIENE SOPORTE PARA RANGOS**

---

### ✅ METADATA NUEVA (generator_v2_items_ranks.py)

```json
{
  "dynamic_state": {
    // --- Progresión ---
    "xp_total": 0,
    "xp_level": 1,
    "aura_level": 0,

    // --- Energía ---
    "energy_current": 100,
    "energy_max": 100,
    "last_energy_refresh": "2025-11-24T00:00:00Z",

    // --- Stats dinámicos ---
    "power_current": 12,

    // --- Estado actual ---
    "state": "READY",
    "current_guild": "Order of Dawn",
    "last_update": "2025-11-24T00:00:00Z",

    // --- Misiones ---
    "current_mission_id": null,
    "mission_start_time": null,
    "last_mission": "None",
    "mission_history": {},
    "total_missions_completed": 0,
    "total_missions_failed": 0,

    // --- Muerte ---
    "death_count": 0,
    "fallen_time": null,

    // 🔥 --- RANGOS SYSTEM ---
    "current_rank": "INITIATE",
    "rank_last_updated": "2025-11-24T00:00:00Z",

    // 🔥 --- ITEMS SYSTEM ---
    "equipped_items": {
      "weapon": null,
      "armor": null,
      "accessory": null,
      "trinket": null
    },
    "inventory": [],
    "item_bonuses": {
      "str": 0,
      "dex": 0,
      "con": 0,
      "int": 0,
      "wis": 0,
      "cha": 0,
      "power": 0,
      "success_rate": 0
    }
  },

  "attributes": [
    {"trait_type": "ID", "value": "00001"},
    {"trait_type": "Race", "value": "Human"},
    {"trait_type": "Class", "value": "Warrior"},
    {"trait_type": "Rarity", "value": "Common"},
    {"trait_type": "Guild", "value": "Order of Dawn"},
    {"trait_type": "Age", "value": 25},
    {"trait_type": "Rank", "value": "INITIATE"}  // 🔥 NUEVO
  ]
}
```

**Ventajas:**
- ✅ Tiene todos los campos del sistema de juego actual
- ✅ **PREPARADO PARA ITEMS:** `equipped_items`, `inventory`, `item_bonuses`
- ✅ **PREPARADO PARA RANGOS:** `current_rank`, `rank_last_updated`
- ✅ Rank visible en OpenSea como trait
- ✅ Compatibilidad hacia atrás (no rompe nada)

---

## 🔥 CAMPOS NUEVOS EXPLICADOS

### 1. SISTEMA DE RANGOS

```json
"current_rank": "INITIATE",
"rank_last_updated": "2025-11-24T00:00:00Z"
```

**Valores posibles:**
- `"INITIATE"` - Nivel 1-9 (por defecto para nuevos NFTs)
- `"ADEPT"` - Nivel 10-24
- `"VETERAN"` - Nivel 25-49
- `"MASTER"` - Nivel 50-99
- `"LEGEND"` - Nivel 100+

**Funcionalidad:**
- Los rangos **NO BLOQUEAN** misiones (según tu pedido)
- Los rangos otorgan bonificadores pasivos (energy_max, success_rate, etc.)
- Se calculan automáticamente en backend basados en `xp_level` y `total_missions_completed`
- `rank_last_updated` permite tracking de progresión

**Visibilidad:**
- Aparece como trait en OpenSea: `"Rank": "INITIATE"`
- Se actualiza automáticamente cuando el héroe sube de nivel

---

### 2. SISTEMA DE ITEMS

#### 2.1 Items Equipados

```json
"equipped_items": {
  "weapon": null,      // "SWORD_001" cuando equipen arma
  "armor": null,       // "PLATE_ARMOR_001" cuando equipen armadura
  "accessory": null,   // "AMULET_AURA_001" cuando equipen accesorio
  "trinket": null      // "RING_POWER_001" cuando equipen trinket
}
```

**Slots disponibles:**
- `weapon` - Armas (espadas, bastones, arcos, etc.)
- `armor` - Armaduras (placas, túnicas, leather, etc.)
- `accessory` - Accesorios (amuletos, capas, etc.)
- `trinket` - Trinkets (anillos, talismanes, etc.)

**Funcionalidad:**
- Inicialmente todos en `null` (sin items equipados)
- Cuando equipen un item, se guarda su ID: `"weapon": "SWORD_EMBERFORGED_001"`
- Backend valida que el item existe en `items_config.json`
- Backend verifica requisitos (nivel, clase) antes de equipar

#### 2.2 Inventario

```json
"inventory": []
```

**Funcionalidad:**
- Array de IDs de items que posee el héroe pero NO está equipados
- Ejemplo cuando tenga items: `["SWORD_001", "POTION_HP_001", "ARMOR_PLATE_001"]`
- Límite sugerido: 100 items por héroe
- Items se obtienen por:
  - Mission rewards (drop aleatorio)
  - Event rewards (garantizados)
  - Achievement unlocks

#### 2.3 Bonos de Items

```json
"item_bonuses": {
  "str": 0,
  "dex": 0,
  "con": 0,
  "int": 0,
  "wis": 0,
  "cha": 0,
  "power": 0,
  "success_rate": 0
}
```

**Funcionalidad:**
- Suma acumulada de todos los items equipados
- Se calcula automáticamente cuando se equipa/desequipa un item
- Ejemplo con items equipados:
  ```json
  "item_bonuses": {
    "str": 5,        // +3 de espada, +2 de armadura
    "dex": 2,        // +2 de anillo
    "con": 0,
    "int": 0,
    "wis": 0,
    "cha": 0,
    "power": 8,      // +5 de espada, +3 de armadura
    "success_rate": 10  // +8 de espada, +2 de trinket
  }
  ```

**Stats totales del héroe:**
```
STR final = fixed_profile.str + item_bonuses.str
          = 12 (base) + 5 (items) = 17 TOTAL
```

---

## 🛠️ MIGRACIÓN DE NFTS EXISTENTES

### Opción 1: Script de Migración (Recomendado)

Si ya tienes NFTs generados con el generador viejo, ejecuta este script:

```python
# migrate_to_items_ranks.py
import json
import os
from datetime import datetime

METADATA_PATH = "./output_metadata"

def migrate_metadata():
    """Agrega campos de items y rangos a metadata existente."""
    files = [f for f in os.listdir(METADATA_PATH) if f.endswith('.json')]

    for filename in files:
        filepath = os.path.join(METADATA_PATH, filename)

        with open(filepath, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        ds = metadata.get("dynamic_state", {})
        timestamp_now = datetime.utcnow().isoformat() + "Z"

        # Agregar campos faltantes si no existen
        if "state" not in ds:
            ds["state"] = "READY"

        if "last_energy_refresh" not in ds:
            ds["last_energy_refresh"] = timestamp_now

        if "current_mission_id" not in ds:
            ds["current_mission_id"] = None

        if "mission_start_time" not in ds:
            ds["mission_start_time"] = None

        if "last_mission" not in ds:
            ds["last_mission"] = "None"

        if "mission_history" not in ds:
            ds["mission_history"] = {}

        if "total_missions_completed" not in ds:
            ds["total_missions_completed"] = 0

        if "total_missions_failed" not in ds:
            ds["total_missions_failed"] = 0

        if "death_count" not in ds:
            ds["death_count"] = 0

        if "fallen_time" not in ds:
            ds["fallen_time"] = None

        # 🔥 RANGOS
        if "current_rank" not in ds:
            ds["current_rank"] = "INITIATE"

        if "rank_last_updated" not in ds:
            ds["rank_last_updated"] = timestamp_now

        # 🔥 ITEMS
        if "equipped_items" not in ds:
            ds["equipped_items"] = {
                "weapon": None,
                "armor": None,
                "accessory": None,
                "trinket": None
            }

        if "inventory" not in ds:
            ds["inventory"] = []

        if "item_bonuses" not in ds:
            ds["item_bonuses"] = {
                "str": 0, "dex": 0, "con": 0,
                "int": 0, "wis": 0, "cha": 0,
                "power": 0, "success_rate": 0
            }

        # Agregar Rank a attributes si no existe
        attrs = metadata.get("attributes", [])
        has_rank = any(a.get("trait_type") == "Rank" for a in attrs)
        if not has_rank:
            attrs.append({"trait_type": "Rank", "value": "INITIATE"})

        # Guardar cambios
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        print(f"✅ Migrado: {filename}")

    print(f"\n🎉 Migración completada: {len(files)} archivos actualizados")

if __name__ == "__main__":
    migrate_metadata()
```

**Ejecutar:**
```bash
python migrate_to_items_ranks.py
```

---

### Opción 2: Re-generar desde Cero

Si prefieres empezar limpio:

```bash
# Backup del generador viejo
cp generator.py generator_OLD.py

# Usar nuevo generador
cp generator_v2_items_ranks.py generator.py

# Re-generar todos los NFTs
python generator.py
```

---

## 📊 COMPARACIÓN DE TAMAÑO DE METADATA

**Metadata anterior:**
- ~500 bytes por NFT
- Sin soporte para items/rangos

**Metadata nueva:**
- ~800 bytes por NFT (+60%)
- **Completamente preparada para items y rangos**

**Costo adicional de almacenamiento:**
- 35,000 NFTs × 300 bytes adicionales = **10.5 MB extra**
- Insignificante comparado con las imágenes (35,000 × ~50KB = 1.75 GB)

---

## 🎯 PRÓXIMOS PASOS

### 1. **Actualizar el Generador**
```bash
cp generator_v2_items_ranks.py generator.py
```

### 2. **Migrar NFTs Existentes (si aplica)**
```bash
python migrate_to_items_ranks.py
```

### 3. **Actualizar Backend (app.py)**
El backend ya está preparado. Solo falta agregar:
- Sistema de items: `/api/items`, `/api/equip`, `/api/unequip`
- Sistema de rangos: `calculate_hero_rank()` ya diseñado en el audit

### 4. **Implementar Items Config**
Crear `/data/items_config.json` con los items del juego:
```json
{
  "items": [
    {
      "id": "SWORD_EMBERFORGED_001",
      "name": "Emberforged Blade",
      "rarity": "RARE",
      "slot": "weapon",
      "stat_bonuses": {"str": 3, "power": 5},
      "mission_bonuses": {"success_rate": 8}
    }
  ]
}
```

### 5. **Implementar Ranks Config**
Crear `/data/ranks_config.json` con los rangos (ya diseñado en audit anterior).

---

## ❓ PREGUNTAS FRECUENTES

### ¿Rompe compatibilidad con NFTs existentes?
**NO.** Los nuevos campos tienen valores por defecto seguros (`null`, `[]`, `0`, `"INITIATE"`).

### ¿Funciona con el backend actual?
**SÍ.** Backend de `app.py` ignora campos que no usa. Solo lee lo que necesita.

### ¿Qué pasa si subo metadata nueva a IPFS?
La metadata es **inmutable en IPFS** una vez subida. Para NFTs ya minteados:
- La metadata on-chain NO cambia (fixed_profile)
- El backend maneja `dynamic_state` en su propia base de datos

### ¿Los rangos bloquean misiones?
**NO.** Según tu pedido, los rangos solo otorgan bonificadores. Todos los héroes pueden hacer todas las misiones.

### ¿Cuándo se implementarán los items?
Cuando decidas. La metadata ya está lista. Solo falta:
1. Crear `items_config.json`
2. Agregar endpoints de items a `app.py`
3. Agregar UI de inventario a `index.html`

---

## 🎉 RESUMEN

✅ **Generador actualizado** con soporte completo para items y rangos
✅ **Metadata preparada** para implementación futura
✅ **No rompe compatibilidad** con sistema actual
✅ **Rangos como bonificadores**, no como restricciones
✅ **Items con 4 slots**: weapon, armor, accessory, trinket
✅ **Inventario ilimitado** (recomendado: límite de 100 items)
✅ **Rank visible en OpenSea** como trait

**Archivo listo para usar:** `generator_v2_items_ranks.py`
