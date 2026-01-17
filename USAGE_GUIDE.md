# 🎮 EMBERHOLM PORTAL - USAGE GUIDE
## Inventory & Vault System

---

## 🚀 Getting Started

### 1. Connect Your Wallet
- Navigate to the **[PROFILE]** section
- Click **[CONNECT WALLET]**
- Ensure you're on **Base Sepolia** network
- Your emissaries will load automatically

### 2. Check Your Balance
Once connected, you'll see your balance in the top console bar:
- **[E] XXX $EMBER** - Used for pushing missions, recovering energy, and gambling
- **[A] XXX $ASH** - Used for reviving fallen emissaries (when enabled)

---

## 📦 VAULT - Managing Your Items

### Accessing the Vault
1. Click **[VAULT]** in the navigation bar
2. Your items will load automatically

### Vault Features
- **Stats Summary**: See total items, equipped items, available items, and legendary count
- **Filter Tabs**: Filter by item type (Weapons, Armors, Helmets, Accessories, Amulets, Runes)
- **Item Cards**: Each item shows:
  - Name and rarity (Common, Rare, Epic, Legendary)
  - Stats and bonuses
  - Equipment status (who has it equipped)
  - **[EQUIP]** or **[UNEQUIP]** buttons

---

## ⚔️ INVENTORY - Equipment Management

### Opening Inventory
In the **[PROFILE]** section, each READY emissary has an **[INVENTORY]** button.

### Equipment Slots
Each emissary can equip:
- **5 Item Slots**:
  - Weapon
  - Armor
  - Helmet
  - Accessory
  - Amulet
- **2 Rune Slots**: Special enhancement runes
- **1 Land Slot**: Bind a land for stat bonuses

### Equipment Indicators
Below each emissary name, you'll see:
- `╬ [X/5 ITM]` - Items equipped (out of 5 slots)
- `◈ [X/2 RUN]` - Runes equipped (out of 2 slots)
- `⌂ [LAND]` - Land binding status

---

## 💰 $EMBER Economy Features

### 1. Mission Acceleration (PUSH)
Speed up missions using $EMBER:
- **25% Faster** - Costs vary by difficulty
- **50% Faster** - Higher cost
- **100% Instant** - Complete immediately (highest cost)

**Costs by Difficulty:**
| Difficulty | 25% | 50% | 100% (Instant) |
|------------|-----|-----|----------------|
| Easy | 50 | 150 | 400 |
| Medium | 100 | 300 | 800 |
| Hard | 200 | 600 | 1500 |
| Legendary | 500 | 1500 | 4000 |

### 2. Energy Restoration (RECOVER)
Click **[RECOVER]** on any emissary to restore energy:
- **+25 Energy** → 30 $EMBER
- **+50 Energy** → 75 $EMBER
- **+100 Energy (Full)** → 150 $EMBER

### 3. EMBER Gambit (D20 Dice Game)
Click **[D20 GAMBIT]** in the console bar to play:
- **Cost**: 100 $EMBER per roll
- **Limits**: 5 free rolls per day (resets at midnight UTC)

**Rewards Table:**
| Roll | Result |
|------|--------|
| 1 | ✗ CRITICAL FAIL - Lose 100 $EMBER |
| 2-5 | Nothing (lose your bet) |
| 6-8 | +50 $EMBER |
| 9-11 | +100 $EMBER (break even) |
| 12-14 | +200 $EMBER |
| 15-17 | +350 $EMBER |
| 18-19 | +500 $EMBER + Common Item |
| 20 | ★ NATURAL 20! +1,000 $EMBER + Rare/Epic Item |

---

## 🔥 ASH Protocol (Feature Flagged)

### Burning EMBER to ASH
**Currently disabled** - Will be enabled in future updates.

When enabled:
- **Conversion Rate**: 1000 $EMBER = 1 $ASH
- **Warning**: This conversion is IRREVERSIBLE!

### Reviving Fallen Emissaries
**Currently disabled** - Will be enabled in future updates.

When enabled:
- **1st Death**: 25 $ASH
- **2nd Death**: 50 $ASH
- **3rd Death**: 100 $ASH
- **4th+ Death**: 200 $ASH (max)

---

## 🎯 Tips & Strategy

### Maximizing Item Bonuses
- **Stack Bonuses**: Equip items with complementary stats
- **Legendary Items**: Save these for your most active emissaries
- **Runes**: Use runes for balanced stat boosts across multiple categories

### Economy Management
- **Save $EMBER**: Don't waste on low-value missions
- **Use PUSH Wisely**: Only accelerate high-reward legendary missions
- **Gambit Strategy**: Play when you have excess $EMBER (5+ rolls recommended)

### Energy Optimization
- **Natural Recovery**: Wait 48h for free full energy restore
- **Emergency Only**: Use $EMBER recovery only when absolutely needed
- **Plan Missions**: Schedule missions to minimize downtime

---

## 🐛 Troubleshooting

### Items Not Showing
- Ensure you're connected to the correct wallet
- Refresh the page and reconnect your wallet
- Check console for errors (F12 → Console tab)

### Balance Not Updating
- Click **[PROFILE]** to refresh data
- Reload the vault page
- Disconnect and reconnect wallet

### Gambit Rolls Not Available
- Rolls reset at midnight UTC
- Check remaining rolls in **[D20 GAMBIT]** button
- Ensure you have at least 100 $EMBER

---

## 📚 Additional Resources

- **Full Implementation Guide**: See `INVENTORY_VAULT_IMPLEMENTATION.md`
- **Backend API Endpoints**: `app.py` lines 3923-4819
- **Frontend Code**: `static/js/inventory.js`
- **Styling**: `static/css/hacknet-clean.css` lines 1717-2124

---

## 🎨 Design Notes

All features maintain the **retro CRT terminal aesthetic**:
- Orange (#ff9500) primary color theme
- Monospace fonts throughout
- CRT scan effects and glow
- Responsive grid layouts

---

## ⚙️ Feature Flags

Current status:
- ✅ **EMBER_GAMBIT_ENABLED**: true
- ✅ **EMBER_PUSH_ENABLED**: true
- ❌ **ASH_PROTOCOL_ENABLED**: false (coming soon)
- ❌ **LAND_STAKING_ENABLED**: false (future feature)

---

**Last Updated**: 2025-12-08
**Version**: 1.0
**Branch**: `claude/adapt-new-features-01Fjxhxhq5JQb1uz7tmBSdvD`
