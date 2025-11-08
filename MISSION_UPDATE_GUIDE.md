# 📝 Guía de Actualización Semanal de Misiones

Esta guía explica cómo actualizar las misiones semanalmente en Emberholm Portal. Las misiones tienen una **estructura fija** (dificultad, duración, recompensas, mecánicas) pero el **lore y nombres** pueden cambiar para mantener la experiencia fresca.

---

## 🎯 ¿Qué puedes cambiar semanalmente?

Para cada misión, puedes actualizar los siguientes campos en `/data/missions_config.json`:

### ✅ **Campos Editables** (Cambiar semanalmente):
- `name` - El nombre de la misión
- `description` - Descripción corta (1-2 líneas)
- `lore` - Historia de fondo de la misión
- `favored_guild` - Gremio favorecido
- `favored_class` - Clase favorecida
- `favored_race` - Raza favorecida

### ❌ **Campos Fijos** (NO cambiar):
- `id` - Identificador único de la misión
- `difficulty` - Dificultad (EASY, MEDIUM, HARD)
- `duration_hours` - Duración (3h, 6h, 12h)
- `energy_cost` - Costo de energía
- `reward_xp` - XP base de recompensa
- `reward_aura` - Aura base de recompensa
- `success_rate` - Tasa de éxito base
- `xp_loss_on_fail` - XP perdida al fallar
- `death_chance` - Probabilidad de muerte

---

## 📋 Pasos para Actualizar Misiones

### 1️⃣ **Edita el archivo de configuración**

Abre el archivo: `/data/missions_config.json`

```json
{
  "missions": [
    {
      "id": "001",
      "name": "CAMBIAR ESTE NOMBRE",
      "difficulty": "EASY",
      "duration_hours": 3,
      "energy_cost": 10,
      "reward_xp": 60,
      "reward_aura": 4,
      "success_rate": 92,
      "xp_loss_on_fail": 25,
      "death_chance": 0,
      "favored_guild": "CAMBIAR ESTE GREMIO",
      "favored_class": "CAMBIAR ESTA CLASE",
      "favored_race": "CAMBIAR ESTA RAZA",
      "description": "CAMBIAR ESTA DESCRIPCIÓN",
      "lore": "CAMBIAR ESTA HISTORIA"
    }
  ]
}
```

### 2️⃣ **Mantén la Coherencia**

Asegúrate de que cada **dificultad** mantenga sus valores:

#### **EASY (3 misiones):**
- `duration_hours`: **3**
- `energy_cost`: **10**
- `reward_xp`: **60**
- `reward_aura`: **4**
- `success_rate`: **92**
- `xp_loss_on_fail`: **25**
- `death_chance`: **0** (sin riesgo de muerte)

#### **MEDIUM (3 misiones):**
- `duration_hours`: **6**
- `energy_cost`: **18**
- `reward_xp`: **150**
- `reward_aura`: **10**
- `success_rate`: **78**
- `xp_loss_on_fail`: **60**
- `death_chance`: **0.5** (0.5% muerte)

#### **HARD (3 misiones):**
- `duration_hours`: **12**
- `energy_cost`: **25**
- `reward_xp`: **350**
- `reward_aura`: **25**
- `success_rate`: **60**
- `xp_loss_on_fail`: **140**
- `death_chance`: **2.0** (2% muerte)

### 3️⃣ **Reinicia el servidor**

Después de editar `missions_config.json`, reinicia el servidor para cargar la nueva configuración:

```bash
# Si estás corriendo localmente:
# Detén el servidor (Ctrl+C) y vuelve a ejecutar
python app.py

# Si estás en Render.com:
# El servidor se reiniciará automáticamente al hacer push del archivo actualizado
```

### 4️⃣ **Verifica los cambios**

1. Ve a la sección **[MISSIONS]** en el portal
2. Verifica que los nombres, descripciones y lore se hayan actualizado
3. Verifica que las recompensas y dificultades sigan siendo correctas

---

## 📝 Ejemplo de Actualización Semanal

### **Antes** (Semana 1):
```json
{
  "id": "001",
  "name": "The Lost Forge",
  "favored_guild": "Forge Legion",
  "favored_class": "Warrior",
  "favored_race": "Orc",
  "description": "Ancient forges rumble beneath the mountains.",
  "lore": "The ancient dwarven forges were abandoned centuries ago."
}
```

### **Después** (Semana 2):
```json
{
  "id": "001",
  "name": "Ember Vault Excavation",
  "favored_guild": "Horizon Watch",
  "favored_class": "Ranger",
  "favored_race": "Elf",
  "description": "Uncover hidden vaults beneath the Emberholm ruins.",
  "lore": "Scouts report strange energy signatures emanating from collapsed tunnels."
}
```

**Resultado:** Misma dificultad EASY, mismas recompensas, pero con **nuevo tema y lore**.

---

## 🎨 Consejos para Crear Lore

### **Temáticas recomendadas:**
- 🔥 Ember Core y su deterioro
- 🌌 Veil (el velo entre dimensiones)
- ⚔️ Conflictos entre gremios
- 🏰 Descubrimientos arqueológicos
- 💀 Amenazas del Void
- 🌅 Misiones de patrulla y vigilancia
- 🗡️ Artefactos legendarios

### **Formato sugerido:**
- **Nombre:** Corto, impactante, memorable (3-5 palabras)
- **Descripción:** 1-2 oraciones, objetivo claro
- **Lore:** 1-3 oraciones, contexto narrativo

---

## 🔄 Rotación Recomendada

### **Semana 1:** Misiones de exploración
### **Semana 2:** Misiones de combate
### **Semana 3:** Misiones de investigación arcana
### **Semana 4:** Misiones de defensa del reino

Ciclo infinito. Cada 4 semanas, reinicia con variaciones del lore.

---

## ⚠️ Errores Comunes

### **❌ Error 1: Cambiar el ID**
```json
{
  "id": "010",  // ❌ NO CAMBIAR
  "name": "Nueva Misión"
}
```
**Solución:** El `id` debe permanecer como "001", "002", etc.

### **❌ Error 2: Cambiar difficulty sin ajustar valores**
```json
{
  "id": "001",
  "difficulty": "HARD",  // ❌ Cambió a HARD
  "duration_hours": 3,   // ❌ Pero sigue con duración EASY
  "reward_xp": 60        // ❌ Recompensa de EASY
}
```
**Solución:** NO cambiar `difficulty`. Mantén los bloques de EASY/MEDIUM/HARD intactos.

### **❌ Error 3: Gremios que no existen**
```json
{
  "favored_guild": "Dragon Riders"  // ❌ Este gremio no existe
}
```
**Solución:** Usa solo gremios existentes:
- Circle of Mist
- Order of Dawn
- Horizon Watch
- Shadow Guild
- Forge Legion
- Void Echoes

---

## 🚀 Despliegue en Render

Si estás usando Render.com para hosting:

1. Edita `/data/missions_config.json` localmente
2. Haz commit de los cambios:
   ```bash
   git add data/missions_config.json
   git commit -m "UPDATE: Weekly missions rotation (Week X)"
   git push origin main
   ```
3. Render detectará el cambio y redesplegará automáticamente
4. Espera 2-3 minutos y las misiones estarán actualizadas

---

## 📊 Validación

Antes de desplegar, verifica:

✅ Las 9 misiones tienen IDs únicos (001-009)
✅ Hay exactamente 3 misiones EASY, 3 MEDIUM, 3 HARD
✅ Todos los gremios mencionados existen
✅ Las descripciones y lore tienen sentido narrativamente
✅ No hay typos o errores de sintaxis JSON
✅ Los valores de reward/duration/success_rate NO cambiaron

---

## 📞 Soporte

Si necesitas ayuda o quieres sugerencias de lore, contacta al equipo de desarrollo.

**¡Disfruta creando nuevas historias para Emberholm!** 🔥
