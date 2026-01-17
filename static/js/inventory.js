/* ===============================================================
   EMBERHOLM PORTAL - INVENTORY & VAULT SYSTEM
   =============================================================== */

(function() {
    'use strict';

    // Feature Flags (sincronizar con backend)
    const FEATURES = {
        ASH_PROTOCOL_ENABLED: false,
        EMBER_GAMBIT_ENABLED: true,
        EMBER_PUSH_ENABLED: true,
        LAND_STAKING_ENABLED: false
    };

    // ========== IPFS CIDs for Items & Runes ==========
    const IPFS_CONFIG = {
        ITEMS_METADATA_CID: "bafybeibs6mm5rghbpld7twbj35dbpryrfimmqkbnkev6ufs4kpbp343wfm",
        ITEMS_IMAGES_CID: "bafybeiegbqf3ypcn7uukahdf275yrmxu2g4zt4xmmrfwguufppbhzs4yx4",
        RUNES_METADATA_CID: "bafybeiajq22kxgm764srr55wsiz4t65so5laxe2nmrryzgailzpmfes3nq",
        RUNES_IMAGES_CID: "bafybeibmivzieas7beofrxspoqo5iughrzyvg3wgjibe626eqt37zg3sae",
        GATEWAY: "https://ipfs.io/ipfs/"
    };

    // ========== GAME-STYLED MODALS (replace browser alerts) ==========

    // Show a game-styled alert modal
    function showGameAlert(message, type = 'info') {
        const icons = { success: '✓', error: '✗', unequip: '✗', info: 'ℹ' };
        const titles = { success: 'SUCCESS', error: 'ERROR', unequip: 'UNEQUIPPED', info: 'NOTICE' };
        const icon = icons[type] || icons.info;
        const title = titles[type] || titles.info;

        const overlay = document.createElement('div');
        overlay.className = 'game-modal-overlay';
        // Use 'error' class for 'unequip' type to get red styling
        const styleClass = type === 'unequip' ? 'error' : type;
        overlay.innerHTML = `
            <div class="game-modal alert-modal ${styleClass}">
                <div class="modal-header">${icon} ${title}</div>
                <div class="modal-body">
                    <p>${message}</p>
                </div>
                <div class="modal-footer">
                    <button class="btn-accept" onclick="this.closest('.game-modal-overlay').remove();">[ACCEPT]</button>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);

        // Focus the button for keyboard accessibility
        overlay.querySelector('button').focus();

        // Close on ESC key
        const handleEsc = (e) => {
            if (e.key === 'Escape') {
                overlay.remove();
                document.removeEventListener('keydown', handleEsc);
            }
        };
        document.addEventListener('keydown', handleEsc);
    }

    // Show a game-styled confirm modal (returns Promise)
    function showGameConfirm(message, title = 'CONFIRM ACTION') {
        return new Promise((resolve) => {
            const overlay = document.createElement('div');
            overlay.className = 'game-modal-overlay';
            overlay.innerHTML = `
                <div class="game-modal confirm-modal">
                    <div class="modal-header">⚔️ ${title}</div>
                    <div class="modal-body">
                        <p>${message}</p>
                    </div>
                    <div class="modal-footer">
                        <button class="btn-confirm">[CONFIRM]</button>
                        <button class="btn-cancel">[CANCEL]</button>
                    </div>
                </div>
            `;

            const confirmBtn = overlay.querySelector('.btn-confirm');
            const cancelBtn = overlay.querySelector('.btn-cancel');

            confirmBtn.onclick = () => {
                overlay.remove();
                resolve(true);
            };

            cancelBtn.onclick = () => {
                overlay.remove();
                resolve(false);
            };

            document.body.appendChild(overlay);
            confirmBtn.focus();

            // Close on ESC key (cancel)
            const handleEsc = (e) => {
                if (e.key === 'Escape') {
                    overlay.remove();
                    document.removeEventListener('keydown', handleEsc);
                    resolve(false);
                }
            };
            document.addEventListener('keydown', handleEsc);
        });
    }

    // Expose globally for use in other scripts
    window.showGameAlert = showGameAlert;
    window.showGameConfirm = showGameConfirm;

    // Global state
    let currentWallet = null;
    let currentBalance = {
        ember_balance: 0,
        ash_balance: 0,
        gambit_rolls_today: 0,
        gambit_rolls_max: 5
    };
    let vaultItems = [];

    // Local formatNumber helper (fallback if global not available)
    function formatNumber(num) {
        if (typeof window.formatNumber === 'function') return window.formatNumber(num);
        if (num === null || num === undefined) return '0';
        const parsed = Number(num);
        if (isNaN(parsed)) return '0';
        return parsed.toLocaleString('en-US');
    }

    // Reference to global currentEmissaries (populated by index.html)
    // This getter ensures we always access the latest data
    const getCurrentEmissaries = () => window.currentEmissaries || [];

    // ===============================================================
    // UTILITY FUNCTIONS
    // ===============================================================

    function getRarityColor(rarity) {
        const colors = {
            'common': '#9ca3af',
            'rare': '#3b82f6',
            'epic': '#a855f7',
            'legendary': '#ff6b00'
        };
        return colors[rarity] || '#888';
    }

    function formatStats(stats) {
        if (!stats) return '';

        let html = '';
        if (stats.ember_boost) html += `<span class="stat-positive">+${stats.ember_boost}% EMBER</span> `;
        if (stats.xp_boost) html += `<span class="stat-positive">+${stats.xp_boost}% XP</span><br/>`;
        if (stats.energy_reduction) html += `<span class="stat-negative">-${stats.energy_reduction}% Energy</span> `;
        if (stats.death_protection) html += `<span class="stat-negative">-${stats.death_protection}% Death</span> `;
        if (stats.speed_boost) html += `<span class="stat-positive">+${stats.speed_boost}% Speed</span>`;

        return html;
    }

    // Get item bonuses based on type (item/rune) and rarity
    function getItemBonuses(item) {
        const isRune = item.type === 'rune';
        const rarity = (item.rarity || 'common').toLowerCase();

        const itemBonuses = {
            'common':    { ember: 3,  xp: 2,  energy: 0, death: 0, speed: 0 },
            'uncommon':  { ember: 5,  xp: 4,  energy: 2, death: 0, speed: 0 },
            'rare':      { ember: 8,  xp: 6,  energy: 3, death: 2, speed: 0 },
            'epic':      { ember: 12, xp: 10, energy: 5, death: 4, speed: 3 },
            'legendary': { ember: 18, xp: 15, energy: 8, death: 6, speed: 5 }
        };

        const runeBonuses = {
            'common':    { ember: 3,  xp: 3,  energy: 2,  death: 2,  speed: 2 },
            'uncommon':  { ember: 5,  xp: 5,  energy: 3,  death: 3,  speed: 3 },
            'rare':      { ember: 8,  xp: 8,  energy: 5,  death: 5,  speed: 5 },
            'epic':      { ember: 12, xp: 12, energy: 8,  death: 8,  speed: 8 },
            'legendary': { ember: 18, xp: 18, energy: 12, death: 12, speed: 12 }
        };

        const bonusTable = isRune ? runeBonuses : itemBonuses;
        return bonusTable[rarity] || bonusTable['common'];
    }

    // Render equipped item bonuses for INVENTORY modal (inline format)
    function renderEquippedItemBonuses(item) {
        if (!item) return '';

        const bonuses = getItemBonuses(item);
        let parts = [];

        if (bonuses.ember > 0) parts.push(`<span style="color:#ffa500;">EMBER +${bonuses.ember}%</span>`);
        if (bonuses.xp > 0) parts.push(`<span style="color:#22c55e;">XP +${bonuses.xp}%</span>`);
        if (bonuses.energy > 0) parts.push(`<span style="color:#3b82f6;">ENERGY -${bonuses.energy}%</span>`);
        if (bonuses.death > 0) parts.push(`<span style="color:#a855f7;">DEATH -${bonuses.death}%</span>`);
        if (bonuses.speed > 0) parts.push(`<span style="color:#eab308;">SPEED +${bonuses.speed}%</span>`);

        if (parts.length === 0) return '';

        return `<div style="font-size:0.75rem; margin-top:4px; color:#ccc;">${parts.join(' | ')}</div>`;
    }

    // Format item bonuses as styled tags (for vault cards)
    function formatAttributesAsTags(attributes, item) {
        // Use rarity-based bonuses instead of IPFS attributes
        if (!item) return '';

        const bonuses = getItemBonuses(item);

        let html = '<div class="item-stats-tags" style="display:flex; flex-wrap:wrap; gap:4px; margin-top:8px;">';

        // Only show non-zero bonuses, or all for visibility
        const stats = [
            { key: 'ember', label: 'EMBER', color: '#ff6b35' },
            { key: 'xp', label: 'XP', color: '#4ade80' },
            { key: 'energy', label: 'Energy', color: '#60a5fa' },
            { key: 'death', label: 'Death', color: '#a78bfa' },
            { key: 'speed', label: 'Speed', color: '#fbbf24' }
        ];

        stats.forEach(stat => {
            const value = bonuses[stat.key];
            const opacity = value > 0 ? '1' : '0.4';
            html += `<span class="stat-bonus" style="background:rgba(0,0,0,0.3); border:1px solid ${stat.color}; color:${stat.color}; padding:2px 6px; font-size:10px; border-radius:3px; opacity:${opacity};">
                ${value}% ${stat.label}
            </span>`;
        });

        html += '</div>';
        return html;
    }

    // Map IPFS item types to valid equipment slot types
    // IPFS may return: "Item", "Ranged Weapon", "Melee Weapon", "Pendant", etc.
    // Slots expect: "weapon", "armor", "helmet", "accessory", "amulet", "rune"
    // When ipfsType is generic ("Item"), uses itemName to infer the slot
    function mapItemTypeToSlot(ipfsType, itemName = null) {
        const type = ipfsType ? String(ipfsType).toLowerCase().trim() : '';
        const name = itemName ? String(itemName).toLowerCase().trim() : '';

        // Type mapping (specific types take priority)
        const typeMapping = {
            // Weapons
            'weapon': 'weapon',
            'weapons': 'weapon',
            'melee weapon': 'weapon',
            'ranged weapon': 'weapon',

            // Armor
            'armor': 'armor',
            'armour': 'armor',
            'chest': 'armor',
            'chestplate': 'armor',
            'body armor': 'armor',

            // Helmet
            'helmet': 'helmet',
            'helm': 'helmet',
            'headgear': 'helmet',

            // Accessory
            'accessory': 'accessory',
            'accessories': 'accessory',
            'trinket': 'accessory',

            // Amulet
            'amulet': 'amulet',
            'amulets': 'amulet',
            'necklace': 'amulet',
            'pendant': 'amulet',
            'talisman': 'amulet',

            // Rune
            'rune': 'rune',
            'runes': 'rune'
        };

        // Keywords to detect type from item name
        const nameKeywords = {
            weapon: ['bow', 'sword', 'axe', 'dagger', 'staff', 'wand', 'spear', 'mace', 'crossbow', 'blade', 'hammer', 'club', 'pike', 'halberd', 'scythe', 'flail', 'lance', 'knife', 'katana', 'rapier', 'scimitar', 'claymore', 'cutlass', 'saber'],
            armor: ['armor', 'armour', 'plate', 'mail', 'chest', 'breastplate', 'cuirass', 'vest', 'robe', 'tunic', 'jerkin', 'hauberk'],
            helmet: ['helm', 'helmet', 'hat', 'crown', 'hood', 'cap', 'mask', 'coif', 'circlet', 'diadem', 'headband', 'visor'],
            accessory: ['ring', 'glove', 'gauntlet', 'boot', 'belt', 'bracelet', 'bracer', 'cloak', 'cape', 'mantle', 'earring', 'anklet', 'sash', 'band'],
            amulet: ['pendant', 'necklace', 'amulet', 'locket', 'medallion', 'talisman', 'charm', 'choker', 'collar', 'torc', 'stone pendant']
        };

        // 1. First try direct type match (if not generic)
        if (type && type !== 'item' && type !== 'items') {
            if (typeMapping[type]) {
                return typeMapping[type];
            }

            // Partial match on type
            for (const [key, value] of Object.entries(typeMapping)) {
                if (type.includes(key)) {
                    return value;
                }
            }
        }

        // 2. If type is generic ("item") or not matched, use item name to infer
        if (name) {
            // Check each slot's keywords against the item name
            for (const [slot, keywords] of Object.entries(nameKeywords)) {
                for (const keyword of keywords) {
                    if (name.includes(keyword)) {
                        console.log(`   📦 Inferred slot from name: "${itemName}" contains "${keyword}" → "${slot}"`);
                        return slot;
                    }
                }
            }
        }

        // 3. Final fallback
        console.warn(`⚠️ Could not determine type for "${ipfsType}" / "${itemName}", defaulting to 'accessory'`);
        return 'accessory';
    }

    function calculateEquipmentCount(emissary) {
        let count = 0;
        if (emissary.weapon_id) count++;
        if (emissary.armor_id) count++;
        if (emissary.helmet_id) count++;
        if (emissary.accessory_id) count++;
        if (emissary.amulet_id) count++;
        return count;
    }

    function calculateRuneCount(emissary) {
        return emissary.rune_ids ? emissary.rune_ids.length : 0;
    }

    // ===============================================================
    // BALANCE & ECONOMY
    // ===============================================================

    async function loadBalance(wallet) {
        if (!wallet) return;

        try {
            const response = await fetch(`/api/balance?wallet=${wallet}`);
            const data = await response.json();

            if (data.error) {
                console.error('Error loading balance:', data.error);
                return;
            }

            currentBalance = data;
            updateBalanceDisplay();
        } catch (error) {
            console.error('Error loading balance:', error);
        }
    }

    function updateBalanceDisplay() {
        const emberEl = document.getElementById('ember-balance');
        const ashEl = document.getElementById('ash-balance');
        const gambitRollsEl = document.getElementById('gambit-rolls');

        if (emberEl) emberEl.textContent = currentBalance.ember_balance.toLocaleString();
        if (ashEl && FEATURES.ASH_PROTOCOL_ENABLED) {
            ashEl.textContent = currentBalance.ash_balance.toLocaleString();
            document.getElementById('ash-balance-display').style.display = 'inline';
        }
        if (gambitRollsEl) {
            const rollsToday = currentBalance.gambit_rolls_today || 0;
            const maxRolls = currentBalance.gambit_rolls_max || 5;
            gambitRollsEl.textContent = `${rollsToday}/${maxRolls}`;
        }
    }

    // ===============================================================
    // EQUIPMENT INDICATORS (PNG icons with bonuses for ROSTER)
    // ===============================================================

    window.renderEquipmentIndicators = function(emissary) {
        if (!emissary) return '';

        // Debug logging
        console.log("🎒 renderEquipmentIndicators for:", emissary.token_id || emissary.id, {
            weapon_id: emissary.weapon_id,
            armor_id: emissary.armor_id,
            helmet_id: emissary.helmet_id,
            accessory_id: emissary.accessory_id,
            amulet_id: emissary.amulet_id,
            rune_ids: emissary.rune_ids
        });

        const slots = [
            { key: 'weapon_id', icon: '/img/Swords.png', name: 'Weapon' },
            { key: 'armor_id', icon: '/img/shield.png', name: 'Armor' },
            { key: 'helmet_id', icon: '/img/helmet.png', name: 'Helmet' },
            { key: 'accessory_id', icon: '/img/ring.png', name: 'Accessory' },
            { key: 'amulet_id', icon: '/img/gem.png', name: 'Amulet' }
        ];

        // Styles for equipped (orange glow) vs empty (gray) icons
        const equippedStyle = 'width:16px; height:16px; image-rendering:pixelated; filter:sepia(100%) saturate(300%) brightness(1.1) hue-rotate(350deg) drop-shadow(0 0 2px #ffa500);';
        const emptyStyle = 'width:16px; height:16px; image-rendering:pixelated; opacity:0.25; filter:grayscale(100%);';

        // Build icons row
        let iconsHtml = '<div class="equipment-icons-row" style="display:flex; gap:2px; margin:4px 0; align-items:center;">';

        // Item slots (5)
        slots.forEach(slot => {
            const isEquipped = emissary[slot.key];
            iconsHtml += `<img src="${slot.icon}"
                               title="${slot.name}${isEquipped ? ': Equipped' : ': Empty'}"
                               style="${isEquipped ? equippedStyle : emptyStyle}"/>`;
        });

        // Separator
        iconsHtml += '<span style="color:#444; margin:0 3px;">|</span>';

        // Rune slots (2) - check rune_ids array
        const runes = emissary.rune_ids || [];
        for (let i = 0; i < 2; i++) {
            const isEquipped = runes[i];
            iconsHtml += `<img src="/img/runes.png"
                               title="Rune ${i+1}${isEquipped ? ': Equipped' : ': Empty'}"
                               style="${isEquipped ? equippedStyle : emptyStyle}"/>`;
        }
        iconsHtml += '</div>';

        // Calculate bonuses (common rarity baseline: items +3% EMBER +2% XP, runes +3% EMBER +3% XP)
        let totalEmber = 0;
        let totalXP = 0;

        let itemCount = 0;
        slots.forEach(slot => {
            if (emissary[slot.key]) {
                itemCount++;
                totalEmber += 3;
                totalXP += 2;
            }
        });

        let runeCount = 0;
        runes.forEach(runeId => {
            if (runeId) {
                runeCount++;
                totalEmber += 3;
                totalXP += 3;
            }
        });

        // Debug: Show calculation
        console.log(`   📊 Bonuses: ${itemCount} items (+${itemCount*3}% EMBER, +${itemCount*2}% XP) + ${runeCount} runes (+${runeCount*3}% EMBER, +${runeCount*3}% XP) = TOTAL: +${totalEmber}% EMBER, +${totalXP}% XP`);

        // Bonus text
        let bonusHtml = '';
        if (totalEmber > 0 || totalXP > 0) {
            bonusHtml = `<span style="font-size:0.7rem; color:#ffa500; margin-left:6px;">+${totalEmber}% EMBER | +${totalXP}% XP</span>`;
        }

        return iconsHtml + bonusHtml;
    };

    // ===============================================================
    // INVENTORY MODAL
    // ===============================================================

    window.showInventoryModal = async function(emissaryId) {
        console.log('Opening inventory for emissary:', emissaryId);

        // Sync wallet from global if not set locally
        if (!currentWallet && window.connectedWallet) {
            currentWallet = window.connectedWallet;
            console.log("📲 Synced currentWallet from connectedWallet:", currentWallet);
        }

        const modal = document.getElementById('inventory-modal');
        if (!modal) {
            console.error('Inventory modal not found');
            return;
        }

        const modalBody = modal.querySelector('.terminal-modal-body');
        if (!modalBody) return;

        // Show loading state with animation
        modalBody.innerHTML = `
            <div class="terminal-loading-container">
                <div class="terminal-loading-spinner">
                    <div class="spinner-ring"></div>
                    <div class="spinner-core">⚔</div>
                </div>
                <div class="terminal-loading-text">LOADING INVENTORY</div>
                <div class="terminal-loading-dots">
                    <span>.</span><span>.</span><span>.</span>
                </div>
                <div class="terminal-loading-subtext">Fetching equipment data...</div>
            </div>
        `;
        modal.classList.add('active');

        try {
            // Fetch emissary data with equipment
            const emissaryResponse = await fetch(`/api/player/${encodeURIComponent(currentWallet)}`);
            const playerData = await emissaryResponse.json();
            let emissary = playerData.heroes?.find(h => h.token_id === emissaryId);

            if (!emissary) {
                modalBody.innerHTML = `
                    <div class="mono-block">
                        <p style="color:#ff4444;">Emissary not found!</p>
                        <button class="modal-btn" onclick="closeInventoryModal()">[CLOSE]</button>
                    </div>
                `;
                return;
            }

            // Fetch fresh equipment data from dedicated endpoint
            try {
                const equipResponse = await fetch(`/api/equipment/${emissaryId}`);
                const equipData = await equipResponse.json();
                if (equipData.equipment) {
                    // Merge equipment data into emissary object
                    emissary.weapon_id = equipData.equipment.weapon_id;
                    emissary.armor_id = equipData.equipment.armor_id;
                    emissary.helmet_id = equipData.equipment.helmet_id;
                    emissary.accessory_id = equipData.equipment.accessory_id;
                    emissary.amulet_id = equipData.equipment.amulet_id;
                    emissary.rune_ids = equipData.equipment.rune_ids || [];
                    console.log("📦 Equipment data loaded:", equipData.equipment);
                }
                // Also check ON_MISSION state
                if (equipData.state === 'ON_MISSION') {
                    emissary.on_mission = true;
                }
            } catch (equipErr) {
                console.warn("Could not fetch equipment data:", equipErr);
            }

            // Use vaultItems from blockchain (not from /api/vault database)
            // vaultItems is loaded from blockchain events in loadVault()
            let availableItems = [];
            if (vaultItems && vaultItems.length > 0) {
                availableItems = vaultItems;
            } else {
                // Load from blockchain if not already loaded
                console.log("📦 Loading vault items from blockchain...");
                await loadVault(currentWallet);
                availableItems = vaultItems || [];
            }
            console.log(`📦 Available items for inventory: ${availableItems.length}`);

            // Build inventory HTML
            const content = buildInventoryContent(emissary, availableItems);
            modalBody.innerHTML = content;

            // Attach event listeners for equip/unequip buttons
            attachInventoryListeners(emissaryId);

        } catch (error) {
            console.error('Error loading inventory:', error);
            modalBody.innerHTML = `
                <div class="mono-block">
                    <p style="color:#ff4444;">Error loading inventory!</p>
                    <button class="modal-btn" onclick="closeInventoryModal()">[CLOSE]</button>
                </div>
            `;
        }
    };

    function calculateTotalBoosts(emissary, availableItems) {
        const totals = {
            ember_boost: 0,
            xp_boost: 0,
            energy_reduction: 0,
            death_protection: 0,
            speed_boost: 0
        };

        // Bonus tables by rarity - ITEMS
        const itemBonusByRarity = {
            'common':    { ember: 3,  xp: 2,  energy: 0, death: 0, speed: 0 },
            'uncommon':  { ember: 5,  xp: 4,  energy: 2, death: 0, speed: 0 },
            'rare':      { ember: 8,  xp: 6,  energy: 3, death: 2, speed: 0 },
            'epic':      { ember: 12, xp: 10, energy: 5, death: 4, speed: 3 },
            'legendary': { ember: 18, xp: 15, energy: 8, death: 6, speed: 5 }
        };

        // Bonus tables by rarity - RUNES (balanced)
        const runeBonusByRarity = {
            'common':    { ember: 3,  xp: 3,  energy: 2,  death: 2,  speed: 2 },
            'uncommon':  { ember: 5,  xp: 5,  energy: 3,  death: 3,  speed: 3 },
            'rare':      { ember: 8,  xp: 8,  energy: 5,  death: 5,  speed: 5 },
            'epic':      { ember: 12, xp: 12, energy: 8,  death: 8,  speed: 8 },
            'legendary': { ember: 18, xp: 18, energy: 12, death: 12, speed: 12 }
        };

        // Sum bonuses from equipped items
        ['weapon', 'armor', 'helmet', 'accessory', 'amulet'].forEach(slot => {
            const itemId = emissary[`${slot}_id`];
            if (itemId) {
                const item = availableItems.find(i => i.id === itemId);
                if (item) {
                    const rarity = (item.rarity || 'common').toLowerCase();
                    const bonus = itemBonusByRarity[rarity] || itemBonusByRarity['common'];
                    totals.ember_boost += bonus.ember;
                    totals.xp_boost += bonus.xp;
                    totals.energy_reduction += bonus.energy;
                    totals.death_protection += bonus.death;
                    totals.speed_boost += bonus.speed;
                }
            }
        });

        // Sum bonuses from equipped runes
        (emissary.rune_ids || []).forEach(runeId => {
            if (runeId) {
                const rune = availableItems.find(i => i.id === runeId);
                if (rune) {
                    const rarity = (rune.rarity || 'common').toLowerCase();
                    const bonus = runeBonusByRarity[rarity] || runeBonusByRarity['common'];
                    totals.ember_boost += bonus.ember;
                    totals.xp_boost += bonus.xp;
                    totals.energy_reduction += bonus.energy;
                    totals.death_protection += bonus.death;
                    totals.speed_boost += bonus.speed;
                }
            }
        });

        // TODO: Add boosts from Land and Rank

        return totals;
    }

    function buildInventoryContent(emissary, availableItems) {
        // ========== DEBUG: Log available items by type ==========
        console.log("========== INVENTORY DEBUG ==========");
        console.log("Total available items:", availableItems.length);
        console.log("Items by type:");
        ['weapon', 'armor', 'helmet', 'accessory', 'amulet', 'rune'].forEach(type => {
            const items = availableItems.filter(i => i.type === type);
            console.log(`  ${type}: ${items.length}`, items.map(i => ({id: i.id, name: i.name, type: i.type})));
        });
        console.log("All item types present:", [...new Set(availableItems.map(i => i.type))]);
        console.log("Emissary on_mission:", emissary.on_mission);
        console.log("=====================================");

        // Check if emissary is on mission - disable equip/unequip if so
        const isOnMission = emissary.on_mission || false;
        const disabledAttr = isOnMission ? 'disabled' : '';
        const missionWarning = isOnMission ? `
            <div class="mission-warning" style="background:#5a3030; border:1px solid #ff6666; padding:10px; margin-bottom:15px; text-align:center; color:#ff9999;">
                ⚠️ EMISSARY ON MISSION - Equipment changes disabled
            </div>
        ` : '';

        const slots = [
            { key: 'weapon', label: 'WEAPON', type: 'weapon', icon: '<img src="/img/dagger.png" class="pixel-icon" alt="">' },
            { key: 'armor', label: 'ARMOR', type: 'armor', icon: '<img src="/img/armor.png" class="pixel-icon" alt="">' },
            { key: 'helmet', label: 'HELMET', type: 'helmet', icon: '<img src="/img/helmet.png" class="pixel-icon" alt="">' },
            { key: 'accessory', label: 'ACCESSORY', type: 'accessory', icon: '<img src="/img/ring.png" class="pixel-icon" alt="">' },
            { key: 'amulet', label: 'AMULET', type: 'amulet', icon: '<img src="/img/beads.png" class="pixel-icon" alt="">' }
        ];

        let slotsHtml = '';
        slots.forEach(slot => {
            const itemId = emissary[`${slot.key}_id`];
            const equippedItem = availableItems.find(item => item.id === itemId);

            if (equippedItem) {
                slotsHtml += `
                    <div class="equipment-slot equipped" data-slot="${slot.key}">
                        <div class="slot-header">
                            <span>${slot.icon} ${slot.label}</span>
                            <span class="rarity-${equippedItem.rarity}">[${equippedItem.rarity.toUpperCase()}]</span>
                        </div>
                        <div class="slot-item" style="display:flex; gap:10px; align-items:center;">
                            <img src="${equippedItem.image_url || '/img/crossedswords.png'}"
                                 style="width:60px; height:60px; border:1px solid var(--border-primary); image-rendering:pixelated;"
                                 onerror="this.src='/img/crossedswords.png'"/>
                            <div>
                                <strong>${equippedItem.name}</strong><br/>
                                ${renderEquippedItemBonuses(equippedItem)}
                            </div>
                        </div>
                        <button class="terminal-btn small-btn btn-unequip" data-item-id="${equippedItem.id}" data-slot="${slot.key}" ${disabledAttr}>
                            [UNEQUIP]
                        </button>
                    </div>
                `;
            } else {
                const availableForSlot = availableItems.filter(item =>
                    item.type === slot.type && !item.equipped_by
                );

                // Build options with data-image attribute for preview
                let optionsHtml = '<option value="" data-image="/img/crossedswords.png">-- Select --</option>';
                availableForSlot.forEach(item => {
                    const imgUrl = item.image_url || '/img/crossedswords.png';
                    optionsHtml += `<option value="${item.id}" data-image="${imgUrl}">${item.name} [${item.rarity}]</option>`;
                });

                slotsHtml += `
                    <div class="equipment-slot empty" data-slot="${slot.key}">
                        <div class="slot-header">
                            <span>${slot.icon} ${slot.label}</span>
                            <span style="color:#666;">[EMPTY]</span>
                        </div>
                        <div style="display:flex; gap:10px; align-items:center; margin:10px 0;">
                            <img id="item-preview-${slot.key}"
                                 src="/img/crossedswords.png"
                                 style="width:60px; height:60px; border:1px solid var(--border-dim); image-rendering:pixelated; opacity:0.5;"
                                 onerror="this.src='/img/crossedswords.png'"/>
                            <select class="equipment-select" data-slot="${slot.key}"
                                    onchange="updateItemPreview(this, '${slot.key}')"
                                    style="flex:1; padding:8px; background:var(--bg-panel); color:var(--primary-green); border:1px solid var(--border-primary);">
                                ${optionsHtml}
                            </select>
                        </div>
                        <button class="terminal-btn small-btn btn-equip" data-slot="${slot.key}" ${availableForSlot.length === 0 || isOnMission ? 'disabled' : ''}>
                            [EQUIP]
                        </button>
                    </div>
                `;
            }
        });

        // Rune slots
        const runeIds = emissary.rune_ids || [];
        let runesHtml = '';
        for (let i = 0; i < 2; i++) {
            const runeId = runeIds[i];
            const equippedRune = availableItems.find(item => item.id === runeId);

            if (equippedRune) {
                runesHtml += `
                    <div class="equipment-slot equipped rune-slot">
                        <div class="slot-header">
                            <span>◈ RUNE ${i + 1}</span>
                            <span class="rarity-${equippedRune.rarity}">[${equippedRune.rarity.toUpperCase()}]</span>
                        </div>
                        <div class="slot-item" style="display:flex; gap:10px; align-items:center;">
                            <img src="${equippedRune.image_url || '/img/runes.png'}"
                                 style="width:60px; height:60px; border:1px solid var(--border-primary); image-rendering:pixelated;"
                                 onerror="this.src='/img/runes.png'"/>
                            <div>
                                <strong>${equippedRune.name}</strong><br/>
                                ${renderEquippedItemBonuses(equippedRune)}
                            </div>
                        </div>
                        <button class="terminal-btn small-btn btn-unequip-rune" data-item-id="${equippedRune.id}" data-rune-index="${i}" ${disabledAttr}>
                            [UNEQUIP]
                        </button>
                    </div>
                `;
            } else {
                const availableRunes = availableItems.filter(item =>
                    item.type === 'rune' && !item.equipped_by
                );

                // Build options with data-image attribute for preview
                let optionsHtml = '<option value="" data-image="/img/runes.png">-- Select --</option>';
                availableRunes.forEach(item => {
                    const imgUrl = item.image_url || '/img/runes.png';
                    optionsHtml += `<option value="${item.id}" data-image="${imgUrl}">${item.name} [${item.rarity}]</option>`;
                });

                runesHtml += `
                    <div class="equipment-slot empty rune-slot">
                        <div class="slot-header">
                            <span>◈ RUNE ${i + 1}</span>
                            <span style="color:#666;">[EMPTY]</span>
                        </div>
                        <div style="display:flex; gap:10px; align-items:center; margin:10px 0;">
                            <img id="rune-preview-${i}"
                                 src="/img/runes.png"
                                 style="width:60px; height:60px; border:1px solid var(--border-dim); image-rendering:pixelated; opacity:0.5;"
                                 onerror="this.src='/img/runes.png'"/>
                            <select class="rune-select" data-rune-index="${i}"
                                    onchange="updateRunePreview(this, ${i})"
                                    style="flex:1; padding:8px; background:var(--bg-panel); color:var(--primary-green); border:1px solid var(--border-primary);">
                                ${optionsHtml}
                            </select>
                        </div>
                        <button class="terminal-btn small-btn btn-equip-rune" data-rune-index="${i}" ${availableRunes.length === 0 || isOnMission ? 'disabled' : ''}>
                            [EQUIP]
                        </button>
                    </div>
                `;
            }
        }

        const ds = emissary.dynamic_state || {};
        const state = ds.state || "READY";
        const totalBoosts = calculateTotalBoosts(emissary, availableItems);

        // Determine state badge
        let stateBadge = '✓ READY';
        if (state === 'ON_MISSION') stateBadge = '⏳ IN PROGRESS';
        else if (state === 'FALLEN') stateBadge = '💀 FALLEN';

        return `
            ${missionWarning}
            <!-- Emissary Header -->
            <div style="display:grid; grid-template-columns: 120px 1fr; gap:20px; margin-bottom:20px; padding:15px; border:1px solid var(--border-primary); background:rgba(0,0,0,0.3);">
                <div style="text-align:center;">
                    ${emissary.image_url ? `<img src="${emissary.image_url}" style="max-width:100px; max-height:100px; image-rendering:pixelated;" alt="${emissary.name}"/>` : '<div style="width:100px; height:100px; background:#222; display:flex; align-items:center; justify-content:center; color:#666;">NO IMG</div>'}
                </div>
                <div>
                    <div style="font-size:16px; font-weight:600; color:var(--primary-green); margin-bottom:5px;">
                        ${emissary.name || emissary.token_id}
                    </div>
                    <div style="font-size:11px; color:#888; margin-bottom:10px;">
                        ID: #${emissary.token_id}  <span style="padding:2px 8px; background:rgba(68,170,255,0.2); color:var(--primary-green); border:1px solid var(--primary-green);">${stateBadge}</span>
                    </div>
                    <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:10px;">
                        <div style="border:1px solid var(--border-dim); padding:8px; font-size:11px;">
                            <strong>RACE:</strong> ${emissary.race || 'Unknown'}<br/>
                            <strong>GUILD:</strong> ${emissary.guild || ds.current_guild || 'None'}
                        </div>
                        <div style="border:1px solid var(--border-dim); padding:8px; font-size:11px;">
                            <strong>CLASS:</strong> ${emissary.class || 'Unknown'}<br/>
                            <strong>RANK:</strong> ${emissary.rank || 'Tier 1'}
                        </div>
                    </div>
                </div>
            </div>

            <!-- Stats Grid -->
            <div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:10px; margin-bottom:20px;">
                <div style="border:1px solid var(--border-primary); padding:10px; text-align:center;">
                    <div style="font-size:10px; color:#888;">XP</div>
                    <div style="font-size:16px; color:var(--primary-green); font-weight:600;">${(ds.xp_total || 0).toLocaleString()}</div>
                </div>
                <div style="border:1px solid var(--border-primary); padding:10px; text-align:center;">
                    <div style="font-size:10px; color:#888;">AURA</div>
                    <div style="font-size:16px; color:var(--gold); font-weight:600;">${ds.aura_level || 0}</div>
                </div>
                <div style="border:1px solid var(--border-primary); padding:10px; text-align:center;">
                    <div style="font-size:10px; color:#888;">ENERGY</div>
                    <div style="font-size:16px; color:#22c55e; font-weight:600;">${ds.energy_current || 0}/${ds.energy_max || 100}</div>
                </div>
                <div style="border:1px solid var(--border-primary); padding:10px; text-align:center;">
                    <div style="font-size:10px; color:#888;">DEATHS</div>
                    <div style="font-size:16px; color:#ef4444; font-weight:600;">${ds.death_count || 0}</div>
                </div>
            </div>

            <div class="mono-small-note" style="margin-bottom:20px; padding:10px; background:rgba(255,149,0,0.1); border-left:3px solid #ff9500;">
                <img src="/img/inventory.png" class="pixel-icon" alt=""> Equip items and runes to boost your emissary's performance in missions.
            </div>

            <!-- Equipment Slots -->
            <div style="margin-bottom:20px;">
                <div class="subheading" style="margin-bottom:10px;">// EQUIPMENT</div>
                <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(200px, 1fr)); gap:10px;">
                    ${slotsHtml}
                </div>
            </div>

            <!-- Rune Slots -->
            <div style="margin-bottom:20px;">
                <div class="subheading" style="margin-bottom:10px;">// RUNES [2 SLOTS]</div>
                <div style="display:grid; grid-template-columns:repeat(2, 1fr); gap:10px;">
                    ${runesHtml}
                </div>
            </div>

            <!-- Bound Land -->
            <div style="margin-bottom:20px;">
                <div class="subheading" style="margin-bottom:10px;">// BOUND LAND</div>
                ${emissary.land_id ? `
                    <div style="border:1px solid var(--border-primary); padding:15px; background:rgba(0,0,0,0.2);">
                        <div style="font-size:14px; font-weight:600; color:var(--primary-green);">⌂ Land #${emissary.land_id}</div>
                        <div style="font-size:11px; color:#888; margin:5px 0;">Bound • +5% EMBER  +5% XP</div>
                        <div style="margin-top:10px;">
                            <button class="terminal-btn small-btn" style="margin-right:5px;">[CHANGE]</button>
                            <button class="terminal-btn small-btn">[UNBIND]</button>
                        </div>
                    </div>
                ` : `
                    <div style="border:1px dashed var(--border-dim); padding:15px; text-align:center; color:#666;">
                        <div>No land bound</div>
                        <button class="terminal-btn small-btn" style="margin-top:10px;">[BIND LAND]</button>
                    </div>
                `}
            </div>

            <!-- Total Boosts -->
            <div style="margin-bottom:20px;">
                <div class="subheading" style="margin-bottom:10px;">// TOTAL BOOSTS</div>
                <div style="display:grid; grid-template-columns:repeat(5, 1fr); gap:10px;">
                    <div style="border:1px solid var(--border-primary); padding:10px; text-align:center;">
                        <div style="font-size:10px; color:#888;">EMBER</div>
                        <div style="font-size:16px; color:${totalBoosts.ember_boost > 0 ? '#4ade80' : '#888'}; font-weight:600;">+${totalBoosts.ember_boost}%</div>
                    </div>
                    <div style="border:1px solid var(--border-primary); padding:10px; text-align:center;">
                        <div style="font-size:10px; color:#888;">XP</div>
                        <div style="font-size:16px; color:${totalBoosts.xp_boost > 0 ? '#4ade80' : '#888'}; font-weight:600;">+${totalBoosts.xp_boost}%</div>
                    </div>
                    <div style="border:1px solid var(--border-primary); padding:10px; text-align:center;">
                        <div style="font-size:10px; color:#888;">ENERGY</div>
                        <div style="font-size:16px; color:${totalBoosts.energy_reduction > 0 ? '#3b82f6' : '#888'}; font-weight:600;">-${totalBoosts.energy_reduction}%</div>
                    </div>
                    <div style="border:1px solid var(--border-primary); padding:10px; text-align:center;">
                        <div style="font-size:10px; color:#888;">DEATH</div>
                        <div style="font-size:16px; color:${totalBoosts.death_protection > 0 ? '#3b82f6' : '#888'}; font-weight:600;">-${totalBoosts.death_protection}%</div>
                    </div>
                    <div style="border:1px solid var(--border-primary); padding:10px; text-align:center;">
                        <div style="font-size:10px; color:#888;">SPEED</div>
                        <div style="font-size:16px; color:${totalBoosts.speed_boost > 0 ? '#4ade80' : '#888'}; font-weight:600;">+${totalBoosts.speed_boost}%</div>
                    </div>
                </div>
            </div>

            <!-- Action Buttons -->
            <div class="modal-buttons" style="margin-top:30px; display:flex; gap:10px; justify-content:space-between;">
                <button class="modal-btn" style="background:#ef4444; border-color:#ef4444;" onclick="unequipAllItems('${emissary.token_id}')">[UNEQUIP ALL]</button>
                <button class="modal-btn" onclick="closeInventoryModal()">[CLOSE]</button>
            </div>
        `;
    }

    function attachInventoryListeners(emissaryId) {
        // Unequip item buttons
        document.querySelectorAll('.btn-unequip').forEach(btn => {
            btn.addEventListener('click', async () => {
                const itemId = btn.getAttribute('data-item-id');
                const slot = btn.getAttribute('data-slot');
                await unequipItem(emissaryId, slot);
                window.showInventoryModal(emissaryId); // Reload
            });
        });

        // Equip item buttons
        document.querySelectorAll('.btn-equip').forEach(btn => {
            btn.addEventListener('click', async () => {
                const slot = btn.getAttribute('data-slot');
                const select = document.querySelector(`.equipment-select[data-slot="${slot}"]`);
                const itemId = select?.value;
                if (itemId) {
                    await equipItem(emissaryId, slot, itemId);
                    window.showInventoryModal(emissaryId); // Reload
                }
            });
        });

        // Unequip rune buttons
        document.querySelectorAll('.btn-unequip-rune').forEach(btn => {
            btn.addEventListener('click', async () => {
                const itemId = btn.getAttribute('data-item-id');
                await unequipRune(emissaryId, itemId);
                window.showInventoryModal(emissaryId); // Reload
            });
        });

        // Equip rune buttons
        document.querySelectorAll('.btn-equip-rune').forEach(btn => {
            btn.addEventListener('click', async () => {
                const runeIndex = btn.getAttribute('data-rune-index');
                const select = document.querySelector(`.rune-select[data-rune-index="${runeIndex}"]`);
                const itemId = select?.value;
                if (itemId) {
                    await equipRune(emissaryId, itemId);
                    window.showInventoryModal(emissaryId); // Reload
                }
            });
        });
    }

    async function equipItem(emissaryId, slot, itemId) {
        // Use currentWallet or fallback to global
        const wallet = currentWallet || window.connectedWallet;
        if (!wallet) {
            showGameAlert('Please connect your wallet first.', 'error');
            return;
        }

        try {
            console.log('📤 Equipping item:', { wallet, emissary_id: emissaryId, item_id: itemId, slot });

            const response = await fetch('/api/equipment/equip', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    wallet: wallet,
                    emissary_id: emissaryId,
                    item_id: itemId,  // Keep as string (e.g. "item-5120")
                    item_type: slot   // weapon, armor, helmet, accessory, amulet
                })
            });

            const data = await response.json();
            if (data.error) {
                showGameAlert('Error: ' + data.error, 'error');
            }
        } catch (error) {
            console.error('Error equipping item:', error);
            showGameAlert('Failed to equip item', 'error');
        }
    }

    async function unequipItem(emissaryId, slot) {
        try {
            const response = await fetch('/api/equipment/unequip', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    wallet: currentWallet,
                    emissary_id: emissaryId,
                    slot: slot
                })
            });

            const data = await response.json();
            if (data.error) {
                showGameAlert('Error: ' + data.error, 'error');
            } else {
                const slotName = slot.replace('_', ' ').toUpperCase();
                showGameAlert(`${slotName} unequipped successfully!`, 'unequip');
            }
        } catch (error) {
            console.error('Error unequipping item:', error);
            showGameAlert('Failed to unequip item', 'error');
        }
    }

    async function equipRune(emissaryId, itemId) {
        // Use currentWallet or fallback to global
        const wallet = currentWallet || window.connectedWallet;
        if (!wallet) {
            showGameAlert('Please connect your wallet first.', 'error');
            return;
        }

        try {
            console.log('📤 Equipping rune:', { wallet, emissary_id: emissaryId, item_id: itemId });

            const response = await fetch('/api/equipment/equip', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    wallet: wallet,
                    emissary_id: emissaryId,
                    item_id: itemId,  // Keep as string (e.g. "rune-1059")
                    item_type: 'rune'
                })
            });

            const data = await response.json();
            if (data.error) {
                showGameAlert('Error: ' + data.error, 'error');
            }
        } catch (error) {
            console.error('Error equipping rune:', error);
            showGameAlert('Failed to equip rune', 'error');
        }
    }

    async function unequipRune(emissaryId, itemId) {
        try {
            const response = await fetch('/api/equipment/unequip', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    wallet: currentWallet,
                    emissary_id: emissaryId,
                    slot: 'rune',
                    item_id: parseInt(itemId)
                })
            });

            const data = await response.json();
            if (data.error) {
                showGameAlert('Error: ' + data.error, 'error');
            } else {
                showGameAlert('Rune unequipped successfully!', 'unequip');
            }
        } catch (error) {
            console.error('Error unequipping rune:', error);
            showGameAlert('Failed to unequip rune', 'error');
        }
    }

    // Update item preview image when dropdown selection changes
    window.updateItemPreview = function(selectElement, slotKey) {
        const selectedOption = selectElement.options[selectElement.selectedIndex];
        const imageUrl = selectedOption?.getAttribute('data-image') || '/img/crossedswords.png';
        const previewImg = document.getElementById(`item-preview-${slotKey}`);

        if (previewImg) {
            previewImg.src = imageUrl;
            // Full opacity when item is selected, dim when empty
            previewImg.style.opacity = selectElement.value ? '1' : '0.5';
            previewImg.style.borderColor = selectElement.value ? 'var(--primary-green)' : 'var(--border-dim)';
        }
    };

    // Update rune preview image when dropdown selection changes
    window.updateRunePreview = function(selectElement, runeIndex) {
        const selectedOption = selectElement.options[selectElement.selectedIndex];
        const imageUrl = selectedOption?.getAttribute('data-image') || '/img/runes.png';
        const previewImg = document.getElementById(`rune-preview-${runeIndex}`);

        if (previewImg) {
            previewImg.src = imageUrl;
            // Full opacity when rune is selected, dim when empty
            previewImg.style.opacity = selectElement.value ? '1' : '0.5';
            previewImg.style.borderColor = selectElement.value ? 'var(--primary-green)' : 'var(--border-dim)';
        }
    };

    window.unequipAllItems = async function(emissaryId) {
        const confirmed = await showGameConfirm('Are you sure you want to unequip all items and runes from this emissary?', 'UNEQUIP ALL');
        if (!confirmed) {
            return;
        }

        try {
            const response = await fetch('/api/equipment/unequip-all', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    wallet: currentWallet,
                    emissary_id: emissaryId
                })
            });

            const data = await response.json();
            if (data.error) {
                showGameAlert('Error: ' + data.error, 'error');
            } else {
                showGameAlert('All items and runes unequipped!', 'unequip');
                // Reload the modal
                window.showInventoryModal(emissaryId);
            }
        } catch (error) {
            console.error('Error unequipping all items:', error);
            showGameAlert('Failed to unequip all items', 'error');
        }
    };

    window.closeInventoryModal = function() {
        const modal = document.getElementById('inventory-modal');
        if (modal) {
            modal.classList.remove('active');
        }
    };

    // ===============================================================
    // VAULT PAGE - READS FROM BLOCKCHAIN
    // ===============================================================

    async function loadVault(wallet, filterType = null) {
        console.log("🔍 loadVault() called");
        console.log("   Wallet:", wallet);
        console.log("   Filter:", filterType);

        // Fallback to global wallet if not provided
        if (!wallet) {
            wallet = currentWallet || window.connectedWallet;
            console.log("   Using fallback wallet:", wallet);
        }

        if (!wallet) {
            console.warn("⚠️ No wallet provided to loadVault");
            return;
        }

        // Update currentWallet for consistency
        if (!currentWallet && wallet) {
            currentWallet = wallet;
            console.log("📲 Updated currentWallet:", currentWallet);
        }

        const container = document.getElementById('vault-items-container');
        if (container) {
            container.innerHTML = `
                <div class="mono-block" style="text-align:center; padding:40px;">
                    <div class="terminal-loading-spinner">
                        <div class="spinner-ring"></div>
                        <div class="spinner-core">⚔</div>
                    </div>
                    <p style="color:var(--dim-green); margin-top:15px;">Loading items from blockchain...</p>
                </div>
            `;
        }

        try {
            // Check if ethers and window.ethereum are available
            if (typeof ethers === 'undefined' || !window.ethereum) {
                console.error("❌ ethers.js or window.ethereum not available");
                showVaultError("Wallet not connected. Please connect your wallet.");
                return;
            }

            const provider = new ethers.providers.Web3Provider(window.ethereum);
            vaultItems = [];

            // ========== LOAD ITEMS FROM EmberItems CONTRACT ==========
            console.log("📦 Loading ITEMS from blockchain...");
            try {
                const itemsContract = new ethers.Contract(
                    CONTRACT_CONFIG.CONTRACTS.EmberItems,
                    CONTRACT_CONFIG.ITEMS_ABI,
                    provider
                );

                let itemTokenIds = [];

                // Try tokensOfOwner first (if contract supports it)
                try {
                    itemTokenIds = await itemsContract.tokensOfOwner(wallet);
                    console.log(`   tokensOfOwner returned ${itemTokenIds.length} items`);
                } catch (enumError) {
                    console.log("   tokensOfOwner not available, using ItemClaimed events...");

                    // Fallback: Query ItemClaimed events for this wallet
                    const filter = itemsContract.filters.ItemClaimed(wallet);
                    const events = await itemsContract.queryFilter(filter, 0, 'latest');
                    console.log(`   Found ${events.length} ItemClaimed events`);

                    // Extract unique token IDs
                    const tokenIdSet = new Set();
                    for (const event of events) {
                        if (event.args && event.args.tokenId) {
                            tokenIdSet.add(event.args.tokenId.toString());
                        }
                    }
                    itemTokenIds = Array.from(tokenIdSet);
                    console.log(`   Unique token IDs: ${itemTokenIds.length}`);
                }

                for (const tokenId of itemTokenIds) {
                    const id = tokenId.toString();

                    // Fetch metadata directly from IPFS (no tokenURI call)
                    const metadata = await getItemMetadataFromIPFS(id);

                    vaultItems.push({
                        id: `item-${id}`,
                        token_id: id,
                        contract: 'EmberItems',
                        name: metadata.name || `Item #${id}`,
                        type: metadata.type || 'weapon',
                        rarity: metadata.rarity || 'common',
                        image_url: metadata.image || '/img/crossedswords.png',
                        stats: metadata.stats || {},
                        attributes: metadata.attributes || [],
                        equipped_by: null
                    });
                    console.log(`   ✅ Loaded item #${id}: ${metadata.name || 'Item'}`);
                }
            } catch (itemsError) {
                console.error("❌ Error loading items:", itemsError);
            }

            // ========== LOAD RUNES FROM EmberRunes CONTRACT ==========
            console.log("📦 Loading RUNES from blockchain...");
            try {
                const runesContract = new ethers.Contract(
                    CONTRACT_CONFIG.CONTRACTS.EmberRunes,
                    CONTRACT_CONFIG.RUNES_ABI,
                    provider
                );

                let runeTokenIds = [];

                // Try tokensOfOwner first (if contract supports it)
                try {
                    runeTokenIds = await runesContract.tokensOfOwner(wallet);
                    console.log(`   tokensOfOwner returned ${runeTokenIds.length} runes`);
                } catch (enumError) {
                    console.log("   tokensOfOwner not available, using RuneClaimed events...");

                    // Fallback: Query RuneClaimed events for this wallet
                    const filter = runesContract.filters.RuneClaimed(wallet);
                    const events = await runesContract.queryFilter(filter, 0, 'latest');
                    console.log(`   Found ${events.length} RuneClaimed events`);

                    // Extract unique token IDs
                    const tokenIdSet = new Set();
                    for (const event of events) {
                        if (event.args && event.args.tokenId) {
                            tokenIdSet.add(event.args.tokenId.toString());
                        }
                    }
                    runeTokenIds = Array.from(tokenIdSet);
                    console.log(`   Unique token IDs: ${runeTokenIds.length}`);
                }

                for (const tokenId of runeTokenIds) {
                    const id = tokenId.toString();

                    // Fetch metadata directly from IPFS (no tokenURI call)
                    const metadata = await getRuneMetadataFromIPFS(id);

                    vaultItems.push({
                        id: `rune-${id}`,
                        token_id: id,
                        contract: 'EmberRunes',
                        name: metadata.name || `Rune #${id}`,
                        type: 'rune',
                        rarity: metadata.rarity || 'common',
                        image_url: metadata.image || '/img/runes.png',
                        stats: metadata.stats || { all_boost: 5 },
                        attributes: metadata.attributes || [],
                        equipped_by: null
                    });
                    console.log(`   ✅ Loaded rune #${id}: ${metadata.name || 'Rune'}`);
                }
            } catch (runesError) {
                console.error("❌ Error loading runes:", runesError);
            }

            // ========== CHECK EQUIPPED STATUS FROM DATABASE ==========
            try {
                console.log("📦 Fetching equipped items from database...");
                const response = await fetch(`/api/equipment/equipped-items?wallet=${wallet}`);
                const equippedData = await response.json();

                if (equippedData.equipped) {
                    console.log(`   Found ${equippedData.total_equipped} equipped items`);

                    // Helper to get emissary info from global state
                    const getEmissaryInfo = (emissaryId, backendName) => {
                        // Try to get full emissary data from window.currentEmissaries
                        if (window.currentEmissaries) {
                            const emissary = window.currentEmissaries.find(e =>
                                String(e.token_id) === String(emissaryId)
                            );
                            if (emissary) {
                                return {
                                    name: emissary.name || backendName || `Emissary #${emissaryId}`,
                                    state: emissary.state || 'READY',
                                    isOnMission: emissary.state === 'ON_MISSION'
                                };
                            }
                        }
                        // Fallback - assume not on mission if we can't find data
                        return {
                            name: backendName || `Emissary #${emissaryId}`,
                            state: 'READY',
                            isOnMission: false
                        };
                    };

                    // Mark items as equipped
                    vaultItems.forEach(item => {
                        const equippedInfo = equippedData.equipped[item.id];
                        if (equippedInfo) {
                            const emissaryInfo = getEmissaryInfo(
                                equippedInfo.emissary_id,
                                equippedInfo.emissary_name
                            );
                            item.equipped_by = equippedInfo.emissary_id;
                            item.equipped_by_name = emissaryInfo.name;
                            item.equipped_slot = equippedInfo.slot;
                            item.emissary_on_mission = emissaryInfo.isOnMission;
                            console.log(`   ✓ ${item.name} equipped to ${emissaryInfo.name} (${emissaryInfo.state})`);
                        } else {
                            item.equipped_by = null;
                            item.equipped_by_name = null;
                            item.equipped_slot = null;
                            item.emissary_on_mission = false;
                        }
                    });
                }
            } catch (dbError) {
                console.warn("⚠️ Could not fetch equipped status from DB:", dbError);
            }

            // Apply filter if specified
            if (filterType) {
                vaultItems = vaultItems.filter(item => item.type === filterType);
            }

            console.log(`✅ Total vault items: ${vaultItems.length}`);
            renderVault();
            updateVaultStats();

        } catch (error) {
            console.error('❌ Error loading vault:', error);
            showVaultError("Failed to load vault. Please try again.");
        }
    }

    // ========== IPFS METADATA FETCHING (Direct, no contract calls) ==========

    async function getItemMetadataFromIPFS(tokenId) {
        const paddedId = tokenId.toString().padStart(5, '0');
        const metadataUrl = `${IPFS_CONFIG.GATEWAY}${IPFS_CONFIG.ITEMS_METADATA_CID}/${paddedId}.json`;

        console.log(`   🔍 Fetching item metadata from IPFS: ${metadataUrl}`);

        try {
            const response = await fetch(metadataUrl);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const metadata = await response.json();
            console.log(`   ✅ Item ${tokenId}: ${metadata.name}`);

            // Convert ipfs:// to https://
            if (metadata.image && metadata.image.startsWith('ipfs://')) {
                metadata.image = metadata.image.replace('ipfs://', IPFS_CONFIG.GATEWAY);
            }

            // Extract type and rarity from attributes
            let rawType = null;
            if (metadata.attributes && Array.isArray(metadata.attributes)) {
                const typeAttr = metadata.attributes.find(a =>
                    a.trait_type === 'Type' || a.trait_type === 'type' || a.trait_type === 'Item Type'
                );
                const rarityAttr = metadata.attributes.find(a =>
                    a.trait_type === 'Rarity' || a.trait_type === 'rarity'
                );

                if (typeAttr) {
                    rawType = String(typeAttr.value);
                    // Use mapItemTypeToSlot to convert IPFS type to valid slot type
                    // Pass item name as second param to handle generic "Item" types
                    metadata.type = mapItemTypeToSlot(rawType, metadata.name);
                    console.log(`   📦 Item type mapping: "${rawType}" + name "${metadata.name}" → "${metadata.type}"`);
                }
                if (rarityAttr) metadata.rarity = String(rarityAttr.value).toLowerCase();
            }

            // If no type found in attributes, try to infer from name only
            if (!metadata.type && metadata.name) {
                metadata.type = mapItemTypeToSlot(null, metadata.name);
                console.log(`   📦 Inferred type from name only "${metadata.name}" → "${metadata.type}"`);
            }

            // Default image if missing
            if (!metadata.image) {
                metadata.image = `${IPFS_CONFIG.GATEWAY}${IPFS_CONFIG.ITEMS_IMAGES_CID}/${paddedId}.png`;
            }

            return metadata;

        } catch (error) {
            console.warn(`   ⚠️ Failed to fetch item ${tokenId} metadata:`, error.message);
            // Fallback with generic image
            const types = ['weapon', 'armor', 'helmet', 'accessory', 'amulet'];
            const randomType = types[parseInt(tokenId) % types.length];
            return {
                name: `Item #${tokenId}`,
                description: "Unknown item",
                type: randomType,
                rarity: 'common',
                image: '/img/crossedswords.png',
                stats: {},
                attributes: []
            };
        }
    }

    async function getRuneMetadataFromIPFS(tokenId) {
        const paddedId = tokenId.toString().padStart(5, '0');
        const metadataUrl = `${IPFS_CONFIG.GATEWAY}${IPFS_CONFIG.RUNES_METADATA_CID}/${paddedId}.json`;

        console.log(`   🔍 Fetching rune metadata from IPFS: ${metadataUrl}`);

        try {
            const response = await fetch(metadataUrl);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const metadata = await response.json();
            console.log(`   ✅ Rune ${tokenId}: ${metadata.name}`);

            // Convert ipfs:// to https://
            if (metadata.image && metadata.image.startsWith('ipfs://')) {
                metadata.image = metadata.image.replace('ipfs://', IPFS_CONFIG.GATEWAY);
            }

            // Extract rarity from attributes
            if (metadata.attributes && Array.isArray(metadata.attributes)) {
                const rarityAttr = metadata.attributes.find(a =>
                    a.trait_type === 'Rarity' || a.trait_type === 'rarity'
                );
                if (rarityAttr) metadata.rarity = String(rarityAttr.value).toLowerCase();
            }

            // Default image if missing
            if (!metadata.image) {
                metadata.image = `${IPFS_CONFIG.GATEWAY}${IPFS_CONFIG.RUNES_IMAGES_CID}/${paddedId}.png`;
            }

            return metadata;

        } catch (error) {
            console.warn(`   ⚠️ Failed to fetch rune ${tokenId} metadata:`, error.message);
            return {
                name: `Rune #${tokenId}`,
                description: "Unknown rune",
                type: 'rune',
                rarity: 'common',
                image: '/img/runes.png',
                stats: { all_boost: 5 },
                attributes: []
            };
        }
    }

    // Show error in vault container
    function showVaultError(message) {
        const container = document.getElementById('vault-items-container');
        if (container) {
            container.innerHTML = `
                <div class="mono-block" style="text-align:center; padding:40px;">
                    <p style="color:#ef4444;">⚠️ ${message}</p>
                    <button class="terminal-btn" onclick="loadVault(connectedWallet, null)" style="margin-top:15px;">
                        [RETRY]
                    </button>
                </div>
            `;
        }
    }

    // Update vault statistics
    function updateVaultStats() {
        const total = vaultItems.length;
        const equipped = vaultItems.filter(i => i.equipped_by).length;
        const available = total - equipped;
        const legendary = vaultItems.filter(i => i.rarity === 'legendary').length;

        const totalEl = document.getElementById('vault-total');
        const equippedEl = document.getElementById('vault-equipped');
        const availableEl = document.getElementById('vault-available');
        const legendaryEl = document.getElementById('vault-legendary');

        if (totalEl) totalEl.textContent = total;
        if (equippedEl) equippedEl.textContent = equipped;
        if (availableEl) availableEl.textContent = available;
        if (legendaryEl) legendaryEl.textContent = legendary;
    }

    function renderVault() {
        const container = document.getElementById('vault-items-container');
        if (!container) return;

        if (vaultItems.length === 0) {
            container.innerHTML = `
                <div class="mono-block" style="text-align:center; padding:40px;">
                    <p style="color:var(--dim-green);">No items in vault.</p>
                    <p style="margin-top:10px; font-size:11px;">
                        Complete missions to earn item and rune drops!
                    </p>
                </div>
            `;
            updateVaultStats();
            return;
        }

        // Group by type
        const grouped = {};
        vaultItems.forEach(item => {
            const type = item.type.toUpperCase() + 'S';
            if (!grouped[type]) grouped[type] = [];
            grouped[type].push(item);
        });

        let html = '';
        for (const [type, items] of Object.entries(grouped)) {
            html += `
                <div class="subheading" style="margin-top:30px;">// ${type} (${items.length})</div>
                <div class="vault-grid">
            `;

            items.forEach(item => {
                const rarityClass = `rarity-${item.rarity}`;
                const equippedClass = item.equipped_by ? 'equipped' : '';
                const placeholderImg = item.type === 'rune' ? '/img/runes.png' : '/img/crossedswords.png';
                const isOnMission = item.emissary_on_mission || false;

                // Status badge - show mission lock if emissary is on mission
                let statusBadge;
                if (item.equipped_by && isOnMission) {
                    statusBadge = `<div class="mission-locked-badge" style="background:#4a3a1a; border:1px solid #ffaa00; padding:4px 8px; font-size:10px; margin-top:8px; color:#ffaa00;">
                           🔒 ON MISSION: ${item.equipped_by_name || '#' + item.equipped_by}
                       </div>`;
                } else if (item.equipped_by) {
                    statusBadge = `<div class="equipped-badge" style="background:#1a4a1a; border:1px solid var(--primary-green); padding:4px 8px; font-size:10px; margin-top:8px;">
                           ⚔ EQUIPPED TO: ${item.equipped_by_name || '#' + item.equipped_by}
                       </div>`;
                } else {
                    statusBadge = `<div class="available-badge" style="background:#1a3a4a; border:1px solid #4a9eff; padding:4px 8px; font-size:10px; margin-top:8px; color:#4a9eff;">
                           ✓ AVAILABLE
                       </div>`;
                }

                // Buttons - disabled if emissary is on mission
                let actionButtons;
                if (item.equipped_by && isOnMission) {
                    actionButtons = `
                        <button class="terminal-btn small-btn" disabled style="opacity:0.4; cursor:not-allowed;"
                                title="Cannot change equipment while emissary is on mission">[CHANGE]</button>
                        <button class="terminal-btn small-btn" disabled style="background:#3a2020; opacity:0.4; cursor:not-allowed;"
                                title="Cannot unequip while emissary is on mission">[UNEQUIP]</button>
                    `;
                } else if (item.equipped_by) {
                    actionButtons = `
                        <button class="terminal-btn small-btn"
                                onclick="showEquipModal('${item.id}')">[CHANGE]</button>
                        <button class="terminal-btn small-btn" style="background:#5a2020;"
                                onclick="unequipItemFromVault('${item.id}', '${item.equipped_by}', '${item.type}')">[UNEQUIP]</button>
                    `;
                } else {
                    actionButtons = `
                        <button class="terminal-btn small-btn"
                                onclick="showEquipModal('${item.id}')">[EQUIP]</button>
                    `;
                }

                html += `
                    <div class="item-card ${rarityClass} ${equippedClass}">
                        <div style="display:flex; gap:20px; align-items:flex-start;">
                            <img src="${item.image_url || placeholderImg}"
                                 class="item-image"
                                 loading="lazy"
                                 onerror="this.src='${placeholderImg}'"/>
                            <div style="flex:1;">
                                <div class="item-name" style="color:${getRarityColor(item.rarity)};">
                                    ${item.name}
                                </div>
                                <div class="item-rarity">
                                    ${item.type.toUpperCase()} · ${item.rarity.toUpperCase()}
                                </div>
                                ${formatAttributesAsTags(item.attributes, item)}
                                ${statusBadge}
                            </div>
                        </div>
                        <div style="margin-top:15px; display:flex; gap:8px;">
                            ${actionButtons}
                        </div>
                    </div>
                `;
            });

            html += `</div>`;
        }

        container.innerHTML = html;
    }

    // Unequip item from vault view
    window.unequipItemFromVault = async function(itemId, emissaryId, itemType) {
        const wallet = currentWallet || window.connectedWallet;
        if (!wallet) {
            showGameAlert('Please connect your wallet first.', 'error');
            return;
        }

        const confirmed = await showGameConfirm(`Unequip this item from emissary #${emissaryId}?`, 'UNEQUIP ITEM');
        if (!confirmed) {
            return;
        }

        try {
            console.log('📤 Unequipping item from vault:', { itemId, emissaryId, itemType });

            const response = await fetch('/api/equipment/unequip', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    wallet: wallet,
                    emissary_id: emissaryId,
                    item_id: itemId,
                    item_type: itemType
                })
            });

            const data = await response.json();
            if (data.error) {
                showGameAlert('Error: ' + data.error, 'error');
            } else {
                console.log('✅ Item unequipped successfully');
                showGameAlert('Item unequipped successfully!', 'unequip');
                // Reload vault to reflect changes
                await loadVault(wallet);
            }
        } catch (error) {
            console.error('Error unequipping item:', error);
            showGameAlert('Failed to unequip item', 'error');
        }
    };

    // Show emissary selection modal when equipping an item
    window.showEquipModal = function(itemId) {
        // Sync wallet from global if not set locally
        const wallet = currentWallet || window.connectedWallet;
        if (!wallet) {
            showGameAlert('Please connect your wallet first.', 'error');
            return;
        }
        // Update local currentWallet if it was null
        if (!currentWallet && window.connectedWallet) {
            currentWallet = window.connectedWallet;
            console.log("📲 Synced currentWallet from connectedWallet:", currentWallet);
        }

        const modal = document.getElementById('select-emissary-modal');
        if (!modal) return;

        // Find the item
        const item = vaultItems.find(i => i.id === itemId);
        if (!item) {
            showGameAlert('Item not found.', 'error');
            return;
        }

        // Get all emissaries and filter by state
        const allEmissaries = getCurrentEmissaries();
        const readyEmissaries = allEmissaries.filter(e => e.state === 'READY');
        const onMissionCount = allEmissaries.filter(e => e.state === 'ON_MISSION').length;

        if (readyEmissaries.length === 0) {
            let message = 'No READY emissaries available to equip items.';
            if (onMissionCount > 0) {
                message += `\n\n⚠️ ${onMissionCount} emissary${onMissionCount > 1 ? 's are' : ' is'} currently ON MISSION.\nEquipment changes are disabled while on mission.`;
            } else {
                message += '\n\nEmissaries must be in READY state to equip items.';
            }
            showGameAlert(message, 'info');
            return;
        }

        // Build modal content
        let content = `
            <div class="subheading">SELECT EMISSARY TO EQUIP</div>

            <!-- Item Info Card -->
            <div style="border: 1px solid ${getRarityColor(item.rarity)}; padding: 12px; margin: 15px 0; background: rgba(0,0,0,0.3);">
                <div style="display: flex; gap: 12px; align-items: center;">
                    <img src="${item.image_url || '/img/items/placeholder.png'}"
                         loading="lazy"
                         style="width: 48px; height: 48px; border: 1px solid var(--border-primary);"
                         onerror="this.src='/img/items/placeholder.png'"/>
                    <div>
                        <div style="font-weight: bold; color: ${getRarityColor(item.rarity)};">
                            ${item.name}
                        </div>
                        <div style="font-size: 11px; color: #888; margin-top: 2px;">
                            ${item.type.toUpperCase()} · ${item.rarity.toUpperCase()}
                        </div>
                        <div style="font-size: 11px; margin-top: 4px;">
                            ${formatStats(item.stats)}
                        </div>
                    </div>
                </div>
            </div>

            <div class="subheading" style="margin-top: 20px;">AVAILABLE EMISSARIES (${readyEmissaries.length})</div>
            <p style="font-size: 11px; color: #888; margin: 8px 0 15px 0;">
                Select an emissary to equip this ${item.type}
            </p>

            <div style="display: grid; gap: 10px; margin: 15px 0; max-height: 400px; overflow-y: auto;">
        `;

        // List each READY emissary
        readyEmissaries.forEach(emissary => {
            const slotKey = item.type === 'rune' ? 'rune_ids' : `${item.type}_id`;
            const isSlotFull = item.type === 'rune'
                ? (emissary.rune_ids && emissary.rune_ids.length >= 2)
                : emissary[slotKey];

            content += `
                <div style="border: 1px solid var(--border-primary); padding: 12px; background: rgba(0,0,0,0.2); cursor: pointer; transition: all 0.2s;"
                     onmouseover="this.style.borderColor='var(--text-primary)'"
                     onmouseout="this.style.borderColor='var(--border-primary)'"
                     onclick="selectEmissaryForEquip('${itemId}', '${emissary.token_id}')">
                    <div style="display: grid; grid-template-columns: 60px 1fr auto; gap: 12px; align-items: center;">
                        <img src="${emissary.image_url || '/img/emissary_placeholder.png'}"
                             loading="lazy"
                             style="width: 60px; height: 60px; border: 1px solid var(--border-primary);"
                             onerror="this.src='/img/emissary_placeholder.png'"/>
                        <div>
                            <div style="font-weight: bold; color: var(--text-primary);">
                                ${emissary.name || `#${emissary.token_id}`}
                            </div>
                            <div style="font-size: 11px; color: #888; margin-top: 3px;">
                                ${emissary.race} ${emissary.guild ? `· ${emissary.guild}` : ''}
                            </div>
                            <div style="font-size: 11px; margin-top: 3px;">
                                ${emissary.class_type || 'Unknown Class'} · Rank ${emissary.rank || '?'}
                            </div>
                        </div>
                        <div style="text-align: right;">
                            ${isSlotFull ? `
                                <div style="font-size: 11px; color: #f59e0b;">
                                    ⚠ SLOT FULL
                                </div>
                            ` : `
                                <div style="font-size: 13px; color: var(--primary-green);">
                                    ✓ AVAILABLE
                                </div>
                            `}
                        </div>
                    </div>
                </div>
            `;
        });

        content += `
            </div>

            <div class="modal-buttons" style="margin-top: 20px;">
                <button class="modal-btn" onclick="closeSelectEmissaryModal()">
                    [CANCEL]
                </button>
            </div>
        `;

        const modalBody = modal.querySelector('.terminal-modal-body');
        if (modalBody) {
            modalBody.innerHTML = content;
        }

        modal.classList.add('active');
    };

    window.closeSelectEmissaryModal = function() {
        const modal = document.getElementById('select-emissary-modal');
        if (modal) {
            modal.classList.remove('active');
        }
    };

    window.selectEmissaryForEquip = async function(itemId, emissaryId) {
        // ========== DEBUG: Log equip attempt ==========
        console.log("========== EQUIP DEBUG ==========");
        console.log("itemId:", itemId, "type:", typeof itemId);
        console.log("emissaryId:", emissaryId, "type:", typeof emissaryId);
        console.log("currentWallet:", currentWallet);
        console.log("window.connectedWallet:", window.connectedWallet);
        console.log("vaultItems count:", vaultItems.length);
        console.log("vaultItems IDs:", vaultItems.map(i => i.id));
        console.log("=================================");

        // Use currentWallet or fallback to global connectedWallet
        const wallet = currentWallet || window.connectedWallet;

        if (!wallet) {
            console.error("❌ No wallet found - both currentWallet and connectedWallet are null");
            showGameAlert('Please connect your wallet first.', 'error');
            return;
        }

        console.log("✅ Using wallet:", wallet);

        try {
            const item = vaultItems.find(i => i.id === itemId);
            if (!item) {
                console.error("❌ Item not found in vaultItems");
                console.error("   Looking for:", itemId);
                console.error("   Available IDs:", vaultItems.map(i => i.id));
                showGameAlert('Item not found in vault.', 'error');
                return;
            }

            console.log("✅ Found item:", item.name, "type:", item.type);

            console.log('📤 Equipping item:', {
                wallet: wallet,
                emissary_id: emissaryId,
                item_id: itemId,
                item_type: item.type,
                token_id: item.token_id
            });

            // Use single endpoint for both items and runes
            const response = await fetch('/api/equipment/equip', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    wallet: wallet,
                    emissary_id: emissaryId,
                    item_id: itemId,
                    item_type: item.type,  // weapon, armor, helmet, accessory, amulet, or rune
                    token_id: item.token_id  // blockchain token ID
                })
            });

            const data = await response.json();

            if (response.ok && data.success) {
                showGameAlert(`✓ ${item.name} equipped successfully!`, 'success');

                // Close modal
                closeSelectEmissaryModal();

                // Reload vault
                if (window.loadVault) {
                    await loadVault(currentWallet);
                }

                // Refresh profile data
                if (window.loadProfileData) {
                    await window.loadProfileData();
                }
            } else {
                showGameAlert(`Error: ${data.error || 'Failed to equip item'}`, 'error');
            }
        } catch (error) {
            console.error('Error equipping item:', error);
            showGameAlert('Network error. Please try again.', 'error');
        }
    };

    // ===============================================================
    // EMBER ROLL - Reconstruido desde cero
    // ===============================================================

// ============================================================================
// EMBER ROLL FRONTEND - Reconstruido desde cero
// ============================================================================

// Show EMBER ROLL modal
window.showEmberRoll = async function(emissaryId) {
    if (!currentWallet) {
        showGameAlert('Please connect your wallet first', 'error');
        return;
    }

    try {
        // Get status
        const response = await fetch(`/api/ember-roll/status?wallet=${currentWallet}`);
        const data = await response.json();

        if (data.error) {
            showGameAlert(`Error: ${data.error}`, 'error');
            return;
        }

        const rolls_used = data.rolls_used || 0;
        const rolls_max = data.rolls_max || 5;
        const rolls_remaining = data.rolls_remaining || 0;
        const cost = rolls_used === 0 ? 0 : 75;

        // Build modal HTML
        const modalHTML = `
            <div style="max-width:600px; margin:0 auto;">
                <h2 style="text-align:center; color:var(--gold); margin-bottom:20px;">
                    🎲 EMBER ROLL
                </h2>

                <div id="ember-roll-dice" style="text-align:center; font-size:80px; margin:30px 0; color:var(--gold);">
                    <div style="font-family:'Alagard',serif;">D20</div>
                </div>

                <div id="ember-roll-result" style="text-align:center; min-height:100px; margin:20px 0; padding:20px; border:2px solid var(--gold); background:rgba(255,215,0,0.1);">
                    <p style="color:#888; font-style:italic;">Roll the dice to test your fate...</p>
                </div>

                <div style="text-align:center; margin:20px 0; padding:15px; background:rgba(0,0,0,0.3); border:1px solid var(--border-primary);">
                    <div><strong>Rolls today:</strong> ${rolls_used}/${rolls_max}</div>
                    <div><strong>Next roll cost:</strong> ${cost === 0 ? '<span style="color:#4ade80;">FREE</span>' : `<span style="color:var(--gold);">${cost} $EMBER</span>`}</div>
                </div>

                ${rolls_remaining > 0 ? `
                    <button class="modal-btn" id="ember-roll-btn" onclick="performEmberRoll('${emissaryId}')" style="width:100%; padding:15px; font-size:16px; background:#a855f7; border-color:#a855f7; color:#fff; margin-bottom:10px;">
                        [ROLL D20${cost === 0 ? ' - FREE!' : ' - ' + cost + ' $EMBER'}]
                    </button>
                ` : `
                    <button class="modal-btn" disabled style="width:100%; padding:15px; opacity:0.3; cursor:not-allowed; margin-bottom:10px;">
                        [NO ROLLS REMAINING TODAY]
                    </button>
                `}

                <button class="modal-btn" onclick="closeModal('ember-roll-modal')" style="width:100%;">
                    [CLOSE]
                </button>
            </div>
        `;

        // Show modal
        const modal = document.getElementById('ember-roll-modal');
        if (!modal) {
            console.error('ember-roll-modal not found');
            return;
        }

        const modalBody = modal.querySelector('.terminal-modal-body');
        if (modalBody) {
            modalBody.innerHTML = modalHTML;
        }

        modal.classList.add('active');

    } catch (error) {
        console.error('Error showing EMBER ROLL:', error);
        showGameAlert('Failed to load EMBER ROLL', 'error');
    }
};

// Perform roll
window.performEmberRoll = async function(emissaryId) {
    const btn = document.getElementById('ember-roll-btn');
    const dice = document.getElementById('ember-roll-dice');
    const resultDiv = document.getElementById('ember-roll-result');

    if (!btn || !dice || !resultDiv) return;

    // Disable button
    btn.disabled = true;
    btn.textContent = '[ROLLING...]';

    // Animate dice
    let count = 0;
    const animation = setInterval(() => {
        const random = Math.floor(Math.random() * 20) + 1;
        dice.innerHTML = `<div style="font-family:'Alagard',serif; font-size:120px; color:var(--gold);">${random}</div>`;
        count++;
        if (count > 20) clearInterval(animation);
    }, 80);

    try {
        // Perform roll
        const response = await fetch('/api/ember-roll/perform', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                wallet: currentWallet,
                emissary_id: emissaryId
            })
        });

        const data = await response.json();

        // Stop animation
        setTimeout(() => {
            clearInterval(animation);

            if (data.error) {
                // Show error
                dice.innerHTML = `<div style="font-family:'Alagard',serif; font-size:80px; color:#ef4444;">✗</div>`;
                resultDiv.innerHTML = `
                    <div style="color:#ef4444; font-size:18px; font-weight:600;">ERROR</div>
                    <p style="color:#888; margin-top:10px;">${data.error}</p>
                `;
                btn.disabled = false;
                btn.textContent = '[RETRY]';
                return;
            }

            // Show result
            const roll = data.roll;
            const name = data.name;
            const ember_change = data.ember_change;
            const buff = data.buff || {};

            // Update dice
            dice.innerHTML = `<div style="font-family:'Alagard',serif; font-size:120px; color:var(--gold);">${roll}</div>`;

            // Build result HTML
            let resultHTML = `
                <div style="font-size:24px; font-weight:600; color:var(--gold); margin-bottom:15px;">
                    ${name}
                </div>
            `;

            if (ember_change > 0) {
                resultHTML += `<div style="font-size:20px; color:#4ade80;">+${ember_change} $EMBER</div>`;
            } else if (ember_change < 0) {
                resultHTML += `<div style="font-size:20px; color:#ef4444;">${ember_change} $EMBER</div>`;
            } else {
                resultHTML += `<div style="font-size:16px; color:#888;">No EMBER change</div>`;
            }

            // Show buffs if any
            if (buff.duration_hours > 0) {
                const buffs = [];
                if (buff.success_bonus !== 0) buffs.push(`${buff.success_bonus > 0 ? '+' : ''}${buff.success_bonus}% Success`);
                if (buff.xp_bonus !== 0) buffs.push(`${buff.xp_bonus > 0 ? '+' : ''}${buff.xp_bonus}% XP`);
                if (buff.energy_reduction > 0) buffs.push(`-${buff.energy_reduction}% Energy`);

                if (buffs.length > 0) {
                    resultHTML += `
                        <div style="margin-top:15px; padding-top:15px; border-top:1px solid rgba(255,255,255,0.1);">
                            <div style="color:#888; font-size:14px; margin-bottom:8px;">🔮 Mission Buffs (${buff.duration_hours}h):</div>
                            <div style="color:var(--primary-green); font-size:14px;">${buffs.join(' • ')}</div>
                        </div>
                    `;
                }
            }

            resultDiv.innerHTML = resultHTML;

            // Update button
            if (data.rolls_used >= data.rolls_max) {
                btn.disabled = true;
                btn.textContent = '[NO ROLLS REMAINING TODAY]';
                btn.style.opacity = '0.3';
            } else {
                btn.disabled = false;
                const next_cost = data.rolls_used === 0 ? 0 : 75;
                btn.textContent = `[ROLL AGAIN${next_cost === 0 ? ' - FREE' : ' - ' + next_cost + ' $EMBER'}]`;
            }

            // Reload balance
            if (typeof loadBalance === 'function') {
                loadBalance(currentWallet);
            }

        }, 1500); // Wait for animation to finish

    } catch (error) {
        clearInterval(animation);
        console.error('Error performing roll:', error);
        dice.innerHTML = `<div style="font-family:'Alagard',serif; font-size:80px; color:#ef4444;">✗</div>`;
        resultDiv.innerHTML = `
            <div style="color:#ef4444; font-size:18px; font-weight:600;">NETWORK ERROR</div>
            <p style="color:#888; margin-top:10px;">${error.message}</p>
        `;
        btn.disabled = false;
        btn.textContent = '[RETRY]';
    }
};

    // ===============================================================
    // PUSH MODAL (Mission Acceleration) - TEMPORARILY DISABLED
    // ===============================================================

    window.showPushModal = async function(emissaryId) {
        console.log('Opening PUSH modal for emissary:', emissaryId);

        const modal = document.getElementById('push-modal');
        if (!modal) return;

        // Build disabled modal content
        const content = `
            <!-- DISABLED NOTICE -->
            <div class="warning-block" style="margin-bottom: 20px;">
                <span class="glow-yellow">⚠ TEMPORARILY DISABLED</span><br/>
                The EMBER PUSH system has been temporarily disabled by joint decision of the Guilds.<br/>
                It will be activated in the next phase of Emberholm.
            </div>

            <div class="subheading">WHAT IS EMBER PUSH?</div>
            <p style="margin: 10px 0;">
                EMBER PUSH allows you to accelerate your missions by spending $EMBER to skip time.
            </p>

            <div class="mono-block" style="margin: 20px 0;">
                <div class="subheading">OPTIONS (When Active)</div>
                <div style="font-size: 12px; line-height: 1.8; padding: 10px 0;">
                    [25%]  → Reduce remaining time by 25% — <span style="color:#ffaa00;">45 $EMBER/hour</span><br/>
                    [50%]  → Reduce remaining time by 50% — <span style="color:#ffaa00;">180 $EMBER/4h</span><br/>
                    [100%] → Complete mission instantly — <span style="color:#ffaa00;">Up to 7,200 $EMBER</span>
                </div>
            </div>

            <p style="color:#888; font-size: 12px;">
                Cost scales with remaining mission time. Useful for time-sensitive events.
            </p>

            <!-- Close Button -->
            <div class="modal-buttons" style="margin-top: 20px;">
                <button class="modal-btn" onclick="closePushModal()">[CLOSE]</button>
            </div>
        `;

        const modalBody = modal.querySelector('.terminal-modal-body');
        if (modalBody) {
            modalBody.innerHTML = content;
        }

        modal.classList.add('active');
    };

    window.closePushModal = function() {
        const modal = document.getElementById('push-modal');
        if (modal) {
            modal.classList.remove('active');
        }
    };

    window.performPush = async function(emissaryId, pushPercent, cost) {
        if (!currentWallet) {
            showGameAlert('Please connect your wallet first.', 'error');
            return;
        }

        // Confirm action
        const confirmMsg = `Push mission ${pushPercent}% for ${cost} $EMBER?\n\nThis will reduce the mission time immediately.`;
        const confirmed = await showGameConfirm(confirmMsg, 'EMBER PUSH');
        if (!confirmed) {
            return;
        }

        try {
            const response = await fetch('/api/mission/push', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    emissary_id: emissaryId,
                    push_percent: pushPercent,
                    wallet: currentWallet
                })
            });

            const data = await response.json();

            if (response.ok && data.success) {
                showGameAlert(`Mission accelerated by ${pushPercent}%!\n\nEMBER spent: ${data.ember_spent}\nTime reduced: ${data.time_reduced_hours}h`, 'success');

                // Close modal
                closePushModal();

                // Refresh data
                if (window.loadProfileData) {
                    await window.loadProfileData();
                }
            } else {
                showGameAlert(`Error: ${data.error || 'Failed to push mission'}`, 'error');
            }
        } catch (error) {
            console.error('Error pushing mission:', error);
            showGameAlert('Network error. Please try again.', 'error');
        }
    };

    // ===============================================================
    // RECOVER MODAL (Energy Restoration)
    // ===============================================================

    window.showRecoverModal = function(emissaryId) {
        console.log('Opening RECOVER modal for emissary:', emissaryId);

        const modal = document.getElementById('recover-modal');
        if (!modal) return;

        // Find emissary in current roster
        const emissary = getCurrentEmissaries().find(e => String(e.token_id) === String(emissaryId));
        if (!emissary) {
            showGameAlert('Emissary not found. Please refresh the page and try again.', 'error');
            return;
        }

        // Get energy data
        const energyCurrent = emissary.energy_current || 0;
        const energyMax = emissary.energy_max || 100;
        const energyPercent = (energyCurrent / energyMax) * 100;

        // Calculate time until next natural refresh (48h)
        const lastRefresh = emissary.last_energy_refresh ? new Date(emissary.last_energy_refresh) : new Date();
        const nextRefresh = new Date(lastRefresh.getTime() + 48 * 60 * 60 * 1000);
        const now = new Date();
        const timeUntilRefresh = Math.max(0, nextRefresh - now);

        const hoursUntilRefresh = Math.floor(timeUntilRefresh / (1000 * 60 * 60));
        const minutesUntilRefresh = Math.floor((timeUntilRefresh % (1000 * 60 * 60)) / (1000 * 60));
        const refreshTimeStr = hoursUntilRefresh > 0
            ? `${hoursUntilRefresh}h ${minutesUntilRefresh}m`
            : `${minutesUntilRefresh}m`;

        // Energy costs
        const costs = {
            25: 30,
            50: 75,
            100: 150
        };

        // Determine energy bar color
        let energyColor = '#22c55e'; // Green
        if (energyPercent < 30) energyColor = '#ef4444'; // Red
        else if (energyPercent < 60) energyColor = '#f59e0b'; // Orange

        // Build modal content
        const content = `
            <div class="subheading">ENERGY RESTORATION</div>

            <!-- Emissary Info Card -->
            <div style="border: 1px solid var(--border-primary); padding: 12px; margin: 15px 0; background: rgba(0,0,0,0.3);">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 12px;">
                    <div>
                        <span style="color: #888;">EMISSARY:</span><br/>
                        <span style="color: var(--text-primary);">${emissary.name || `#${emissary.token_id}`}</span>
                    </div>
                    <div>
                        <span style="color: #888;">STATE:</span><br/>
                        <span style="color: var(--text-primary); text-transform: uppercase;">${emissary.state || 'READY'}</span>
                    </div>
                    <div>
                        <span style="color: #888;">CURRENT ENERGY:</span><br/>
                        <span style="color: ${energyColor};">${energyCurrent} / ${energyMax}</span>
                    </div>
                    <div>
                        <span style="color: #888;">NEXT REFRESH:</span><br/>
                        <span style="color: var(--text-primary);">${refreshTimeStr}</span>
                    </div>
                </div>

                <!-- Energy Bar -->
                <div style="margin-top: 12px;">
                    <div style="background: #1a1a1a; border: 1px solid var(--border-primary); height: 24px; position: relative; overflow: hidden;">
                        <div style="background: linear-gradient(90deg, ${energyColor} 0%, ${energyColor}dd 100%); height: 100%; width: ${energyPercent}%; transition: width 0.3s ease;"></div>
                        <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 12px; color: #fff; text-shadow: 0 0 4px #000; font-weight: bold;">
                            ⚡ ${energyPercent.toFixed(0)}% ENERGY
                        </div>
                    </div>
                </div>
            </div>

            <!-- Recovery Options -->
            <div class="subheading" style="margin-top: 20px;">RECOVERY OPTIONS</div>
            <p style="font-size: 11px; color: #888; margin: 8px 0 15px 0;">
                Restore energy immediately using $EMBER or wait for natural recovery
            </p>

            <div style="display: grid; gap: 12px; margin: 15px 0;">
                <!-- +25 Energy Option -->
                <div style="border: 1px solid #22c55e; padding: 12px; background: rgba(34,197,94,0.05);">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-size: 14px; color: #22c55e; font-weight: bold;">[+25 ENERGY]</div>
                            <div style="font-size: 11px; color: #888; margin-top: 4px;">
                                Restore 25 energy points
                            </div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 13px; color: var(--text-primary);">
                                ${costs[25]} $EMBER
                            </div>
                        </div>
                    </div>
                </div>

                <!-- +50 Energy Option -->
                <div style="border: 1px solid #22c55e; padding: 12px; background: rgba(34,197,94,0.05);">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-size: 14px; color: #22c55e; font-weight: bold;">[+50 ENERGY]</div>
                            <div style="font-size: 11px; color: #888; margin-top: 4px;">
                                Restore 50 energy points
                            </div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 13px; color: var(--text-primary);">
                                ${costs[50]} $EMBER
                            </div>
                        </div>
                    </div>
                </div>

                <!-- +100 Energy Option (Full) -->
                <div style="border: 1px solid #22c55e; padding: 12px; background: rgba(34,197,94,0.1);">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-size: 14px; color: #22c55e; font-weight: bold;">[+100 ENERGY] FULL</div>
                            <div style="font-size: 11px; color: #888; margin-top: 4px;">
                                Restore to maximum energy
                            </div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 13px; color: var(--text-primary);">
                                ${costs[100]} $EMBER
                            </div>
                        </div>
                    </div>
                </div>

                <!-- WAIT Option (Free) -->
                <div style="border: 1px solid #666; padding: 12px; background: rgba(102,102,102,0.05);">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-size: 14px; color: #888; font-weight: bold;">[WAIT] FREE RECOVERY</div>
                            <div style="font-size: 11px; color: #666; margin-top: 4px;">
                                Natural recovery in ${refreshTimeStr} (48h cycle)
                            </div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 13px; color: #666;">
                                FREE
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Action Buttons -->
            <div class="modal-buttons" style="margin-top: 20px;">
                <button class="modal-btn btn-recover" onclick="performRecover('${emissaryId}', 25, ${costs[25]})">
                    [+25]
                </button>
                <button class="modal-btn btn-recover" onclick="performRecover('${emissaryId}', 50, ${costs[50]})">
                    [+50]
                </button>
                <button class="modal-btn btn-recover" onclick="performRecover('${emissaryId}', 100, ${costs[100]})">
                    [+100]
                </button>
                <button class="modal-btn" onclick="closeRecoverModal()">
                    [WAIT]
                </button>
            </div>
        `;

        const modalBody = modal.querySelector('.terminal-modal-body');
        if (modalBody) {
            modalBody.innerHTML = content;
        }

        modal.classList.add('active');
    };

    window.closeRecoverModal = function() {
        const modal = document.getElementById('recover-modal');
        if (modal) {
            modal.classList.remove('active');
        }
    };

    window.performRecover = async function(emissaryId, amount, cost) {
        if (!currentWallet) {
            showGameAlert('Please connect your wallet first.', 'error');
            return;
        }

        // Confirm action
        const confirmMsg = `Restore ${amount} energy for ${cost} $EMBER?`;
        const confirmed = await showGameConfirm(confirmMsg, 'RESTORE ENERGY');
        if (!confirmed) {
            return;
        }

        try {
            const response = await fetch('/api/energy/recover', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    emissary_id: emissaryId,
                    amount: amount,
                    wallet: currentWallet
                })
            });

            const data = await response.json();

            if (response.ok && data.success) {
                showGameAlert(`Energy restored!\n\n+${amount} energy\nEMBER spent: ${data.ember_spent}\nNew energy: ${data.new_energy}/${data.energy_max}`, 'success');

                // Close modal
                closeRecoverModal();

                // Refresh data
                if (window.loadProfileData) {
                    await window.loadProfileData();
                }
            } else {
                showGameAlert(`Error: ${data.error || 'Failed to restore energy'}`, 'error');
            }
        } catch (error) {
            console.error('Error recovering energy:', error);
            showGameAlert('Network error. Please try again.', 'error');
        }
    };

    // ===============================================================
    // $EMBER CLAIM & $ASH CONVERSION SYSTEM
    // ===============================================================

    // Load EMBER token balance (pending + on-chain)
    async function loadEmberBalance() {
        if (!currentWallet) return;

        try {
            const response = await fetch(`/api/ember/balance/${currentWallet}`);
            const data = await response.json();

            const pendingEl = document.getElementById('ember-pending');
            const onchainEl = document.getElementById('ember-onchain');
            const totalEl = document.getElementById('ember-total');
            const burnedEl = document.getElementById('vault-ember-burned');

            if (pendingEl) pendingEl.textContent = formatNumber(data.pending || 0);
            if (onchainEl) onchainEl.textContent = formatNumber(data.onchain || 0);

            // Total = pending + onchain + total_claimed
            const total = (data.pending || 0) + (data.onchain || 0) + (data.total_claimed || 0);
            if (totalEl) totalEl.textContent = formatNumber(total);

            // Show total burned
            if (burnedEl) burnedEl.textContent = formatNumber(data.total_burned || 0);

            // Enable/disable claim button
            const claimBtn = document.getElementById('claim-ember-btn');
            if (claimBtn) {
                if (data.pending > 0) {
                    claimBtn.disabled = false;
                    claimBtn.textContent = `[CLAIM ${formatNumber(data.pending)} $EMBER]`;
                } else {
                    claimBtn.disabled = true;
                    claimBtn.textContent = '[NO $EMBER TO CLAIM]';
                }
            }

            console.log(`📊 EMBER Balance loaded: pending=${data.pending}, onchain=${data.onchain}`);

        } catch (error) {
            console.error('Error loading EMBER balance:', error);
        }
    }

    // Load ASH token balance (on-chain only)
    async function loadAshBalance() {
        if (!currentWallet || !window.ethereum) return;

        try {
            const provider = new ethers.providers.Web3Provider(window.ethereum);
            const ashContract = new ethers.Contract(
                CONTRACT_CONFIG.CONTRACTS.AshToken,
                CONTRACT_CONFIG.ASH_TOKEN_ABI,
                provider
            );

            const balanceWei = await ashContract.balanceOf(currentWallet);
            const balance = parseFloat(ethers.utils.formatEther(balanceWei));

            const ashBalanceEl = document.getElementById('ash-wallet-balance');
            if (ashBalanceEl) ashBalanceEl.textContent = formatNumber(balance);

            console.log(`📊 ASH Balance: ${balance}`);

        } catch (error) {
            console.error('Error loading ASH balance:', error);
        }
    }

    // Claim pending $EMBER (gasless)
    async function claimEmber() {
        if (!currentWallet) {
            showGameAlert('Connect wallet first', 'error');
            return;
        }

        const claimBtn = document.getElementById('claim-ember-btn');
        const statusEl = document.getElementById('claim-status');

        if (!claimBtn) return;

        claimBtn.disabled = true;
        claimBtn.textContent = '[CLAIMING...]';
        if (statusEl) {
            statusEl.textContent = 'Processing claim...';
            statusEl.className = 'status-text';
        }

        try {
            const response = await fetch('/api/ember/claim', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ wallet: currentWallet })
            });

            const data = await response.json();

            if (data.success) {
                if (statusEl) {
                    statusEl.textContent = `Claimed ${data.amount} $EMBER! TX: ${data.tx_hash.slice(0, 10)}...`;
                    statusEl.className = 'status-text success';
                }

                showGameAlert(
                    `Successfully claimed ${data.amount} $EMBER!\n\nTransaction: ${data.tx_hash.slice(0, 20)}...`,
                    'success'
                );

                // Reload balances
                await loadEmberBalance();

            } else {
                if (statusEl) {
                    statusEl.textContent = `Error: ${data.error}`;
                    statusEl.className = 'status-text error';
                }
                claimBtn.disabled = false;
                claimBtn.textContent = '[CLAIM $EMBER]';
                showGameAlert(`Error: ${data.error}`, 'error');
            }

        } catch (error) {
            console.error('Claim error:', error);
            if (statusEl) {
                statusEl.textContent = `Error: ${error.message}`;
                statusEl.className = 'status-text error';
            }
            claimBtn.disabled = false;
            claimBtn.textContent = '[CLAIM $EMBER]';
            showGameAlert(`Error: ${error.message}`, 'error');
        }
    }

    // Convert EMBER to ASH (on-chain)
    async function convertEmberToAsh() {
        if (!currentWallet) {
            showGameAlert('Connect wallet first', 'error');
            return;
        }

        if (!window.ethereum) {
            showGameAlert('MetaMask not detected', 'error');
            return;
        }

        const amountInput = document.getElementById('ember-to-convert');
        const amount = parseInt(amountInput?.value || 0);

        if (!amount || amount < 100) {
            showGameAlert('Minimum 100 $EMBER to convert', 'error');
            return;
        }

        if (amount % 100 !== 0) {
            showGameAlert('Amount must be multiple of 100', 'error');
            return;
        }

        const convertBtn = document.getElementById('convert-btn');
        if (!convertBtn) return;

        convertBtn.disabled = true;
        convertBtn.textContent = '[CONVERTING...]';

        try {
            const provider = new ethers.providers.Web3Provider(window.ethereum);
            const signer = provider.getSigner();

            const emberContract = new ethers.Contract(
                CONTRACT_CONFIG.CONTRACTS.EmberToken,
                CONTRACT_CONFIG.EMBER_TOKEN_ABI,
                signer
            );

            const amountWei = ethers.utils.parseEther(amount.toString());

            // Call convertToAsh (contract burns EMBER and mints ASH)
            const tx = await emberContract.convertToAsh(amountWei);

            convertBtn.textContent = '[WAITING FOR CONFIRMATION...]';

            await tx.wait();

            const ashAmount = Math.floor(amount / 100);
            showGameAlert(
                `Successfully converted ${amount} $EMBER to ${ashAmount} $ASH!`,
                'success'
            );

            // Register burn in database
            try {
                await fetch('/api/ember/register-burn', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        wallet: currentWallet,
                        amount: amount,
                        tx_hash: tx.hash
                    })
                });
            } catch (registerError) {
                console.warn('Failed to register burn:', registerError);
            }

            // Clear input
            if (amountInput) amountInput.value = '';
            document.getElementById('ash-preview').textContent = '0 $ASH';

            // Reload balances
            await loadEmberBalance();
            await loadAshBalance();

        } catch (error) {
            console.error('Conversion error:', error);
            showGameAlert(`Error: ${error.message || 'Transaction failed'}`, 'error');
        } finally {
            convertBtn.disabled = false;
            convertBtn.textContent = '[CONVERT TO $ASH]';
        }
    }

    // Preview ASH conversion amount
    function updateAshPreview() {
        const amountInput = document.getElementById('ember-to-convert');
        const previewEl = document.getElementById('ash-preview');

        if (amountInput && previewEl) {
            const amount = parseInt(amountInput.value) || 0;
            const ashAmount = Math.floor(amount / 100);
            previewEl.textContent = `${ashAmount} $ASH`;
        }
    }

    // Setup EMBER/ASH event listeners
    function setupEmberAshListeners() {
        const claimBtn = document.getElementById('claim-ember-btn');
        const convertBtn = document.getElementById('convert-btn');
        const amountInput = document.getElementById('ember-to-convert');

        if (claimBtn) {
            claimBtn.addEventListener('click', claimEmber);
        }

        if (convertBtn) {
            convertBtn.addEventListener('click', convertEmberToAsh);
        }

        if (amountInput) {
            amountInput.addEventListener('input', updateAshPreview);
        }
    }

    // Export functions globally
    window.loadEmberBalance = loadEmberBalance;
    window.loadAshBalance = loadAshBalance;
    window.claimEmber = claimEmber;
    window.convertEmberToAsh = convertEmberToAsh;

    // Setup listeners when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', setupEmberAshListeners);
    } else {
        setupEmberAshListeners();
    }

    // ===============================================================
    // INITIALIZATION
    // ===============================================================

    // Export loadVault globally so it can be called from HTML onclick
    window.loadVault = loadVault;

    window.initInventorySystem = function(wallet) {
        currentWallet = wallet;

        if (wallet) {
            loadBalance(wallet);
            // Also load EMBER/ASH balances
            loadEmberBalance();
            loadAshBalance();
        }

        console.log('✅ Inventory system initialized');
    };

    window.switchToVault = function() {
        if (currentWallet) {
            loadVault(currentWallet);
            // Load EMBER/ASH balances when switching to vault
            loadEmberBalance();
            loadAshBalance();
        }
    };

    // Apply feature flags
    if (FEATURES.ASH_PROTOCOL_ENABLED) {
        document.getElementById('ash-balance-display')?.removeAttribute('style');
        document.getElementById('burn-ember-btn')?.removeAttribute('style');
    }

    console.log('%c[INVENTORY] System loaded', 'color: #ff9500; font-weight: bold;');

})();
