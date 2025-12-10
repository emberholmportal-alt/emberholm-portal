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

    // Global state
    let currentWallet = null;
    let currentBalance = {
        ember_balance: 0,
        ash_balance: 0,
        gambit_rolls_today: 0,
        gambit_rolls_max: 5
    };
    let vaultItems = [];

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
            const remaining = currentBalance.gambit_rolls_max - currentBalance.gambit_rolls_today;
            gambitRollsEl.textContent = `${remaining}/${currentBalance.gambit_rolls_max}`;
        }
    }

    // ===============================================================
    // EQUIPMENT INDICATORS
    // ===============================================================

    window.renderEquipmentIndicators = function(emissary) {
        const itemCount = calculateEquipmentCount(emissary);
        const runeCount = calculateRuneCount(emissary);
        const hasLand = emissary.land_id ? true : false;

        let html = '<div class="equipment-indicators">';

        if (itemCount > 0 || runeCount > 0 || hasLand) {
            html += `<span class="eq-icon">╬</span>[<span class="eq-count">${itemCount}/5 ITM</span>] `;
            html += `<span class="eq-icon">◈</span>[<span class="eq-count">${runeCount}/2 RUN</span>] `;
            if (hasLand) {
                html += `<span class="eq-icon">⌂</span>[<span class="eq-count">LAND</span>]`;
            }
        } else {
            html += `<span class="eq-empty">--</span>`;
        }

        html += '</div>';
        return html;
    };

    // ===============================================================
    // INVENTORY MODAL
    // ===============================================================

    window.showInventoryModal = async function(emissaryId) {
        console.log('Opening inventory for emissary:', emissaryId);

        const modal = document.getElementById('inventory-modal');
        if (!modal) {
            console.error('Inventory modal not found');
            return;
        }

        const modalBody = modal.querySelector('.terminal-modal-body');
        if (!modalBody) return;

        // Show loading state
        modalBody.innerHTML = `
            <div class="mono-block" style="text-align:center; padding:40px;">
                <p>Loading inventory...</p>
            </div>
        `;
        modal.classList.add('active');

        try {
            // Fetch emissary data with equipment
            const emissaryResponse = await fetch(`/api/player/${encodeURIComponent(currentWallet)}`);
            const playerData = await emissaryResponse.json();
            const emissary = playerData.heroes?.find(h => h.token_id === emissaryId);

            if (!emissary) {
                modalBody.innerHTML = `
                    <div class="mono-block">
                        <p style="color:#ff4444;">Emissary not found!</p>
                        <button class="modal-btn" onclick="closeInventoryModal()">[CLOSE]</button>
                    </div>
                `;
                return;
            }

            // Fetch available vault items
            const vaultResponse = await fetch(`/api/vault?wallet=${currentWallet}`);
            const vaultData = await vaultResponse.json();
            const availableItems = vaultData.items || [];

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

        // Items equipados
        ['weapon', 'armor', 'helmet', 'accessory', 'amulet'].forEach(slot => {
            const itemId = emissary[`${slot}_id`];
            const item = availableItems.find(i => i.id === itemId);
            if (item && item.stats) {
                Object.keys(totals).forEach(key => {
                    if (item.stats[key]) totals[key] += item.stats[key];
                });
            }
        });

        // Runas equipadas
        (emissary.rune_ids || []).forEach(runeId => {
            const rune = availableItems.find(i => i.id === runeId);
            if (rune && rune.stats) {
                Object.keys(totals).forEach(key => {
                    if (rune.stats[key]) totals[key] += rune.stats[key];
                });
            }
        });

        // TODO: Agregar boosts de Land y Rank

        return totals;
    }

    function buildInventoryContent(emissary, availableItems) {
        const slots = [
            { key: 'weapon', label: 'WEAPON', type: 'weapon', icon: '⚔️' },
            { key: 'armor', label: 'ARMOR', type: 'armor', icon: '🛡️' },
            { key: 'helmet', label: 'HELMET', type: 'helmet', icon: '⛑️' },
            { key: 'accessory', label: 'ACCESSORY', type: 'accessory', icon: '💍' },
            { key: 'amulet', label: 'AMULET', type: 'amulet', icon: '📿' }
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
                        <div class="slot-item">
                            <strong>${equippedItem.name}</strong><br/>
                            <small>${formatStats(equippedItem.stats)}</small>
                        </div>
                        <button class="terminal-btn small-btn btn-unequip" data-item-id="${equippedItem.id}" data-slot="${slot.key}">
                            [UNEQUIP]
                        </button>
                    </div>
                `;
            } else {
                const availableForSlot = availableItems.filter(item =>
                    item.type === slot.type && !item.equipped_by
                );

                let optionsHtml = '<option value="">-- Select --</option>';
                availableForSlot.forEach(item => {
                    optionsHtml += `<option value="${item.id}">${item.name} [${item.rarity}]</option>`;
                });

                slotsHtml += `
                    <div class="equipment-slot empty" data-slot="${slot.key}">
                        <div class="slot-header">
                            <span>${slot.icon} ${slot.label}</span>
                            <span style="color:#666;">[EMPTY]</span>
                        </div>
                        <select class="equipment-select" data-slot="${slot.key}" style="width:100%; padding:8px; margin:10px 0; background:var(--bg-panel); color:var(--primary-green); border:1px solid var(--border-primary);">
                            ${optionsHtml}
                        </select>
                        <button class="terminal-btn small-btn btn-equip" data-slot="${slot.key}" ${availableForSlot.length === 0 ? 'disabled' : ''}>
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
                        <div class="slot-item">
                            <strong>${equippedRune.name}</strong><br/>
                            <small>${formatStats(equippedRune.stats)}</small>
                        </div>
                        <button class="terminal-btn small-btn btn-unequip-rune" data-item-id="${equippedRune.id}" data-rune-index="${i}">
                            [UNEQUIP]
                        </button>
                    </div>
                `;
            } else {
                const availableRunes = availableItems.filter(item =>
                    item.type === 'rune' && !item.equipped_by
                );

                let optionsHtml = '<option value="">-- Select --</option>';
                availableRunes.forEach(item => {
                    optionsHtml += `<option value="${item.id}">${item.name} [${item.rarity}]</option>`;
                });

                runesHtml += `
                    <div class="equipment-slot empty rune-slot">
                        <div class="slot-header">
                            <span>◈ RUNE ${i + 1}</span>
                            <span style="color:#666;">[EMPTY]</span>
                        </div>
                        <select class="rune-select" data-rune-index="${i}" style="width:100%; padding:8px; margin:10px 0; background:var(--bg-panel); color:var(--primary-green); border:1px solid var(--border-primary);">
                            ${optionsHtml}
                        </select>
                        <button class="terminal-btn small-btn btn-equip-rune" data-rune-index="${i}" ${availableRunes.length === 0 ? 'disabled' : ''}>
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
                📦 Equip items and runes to boost your emissary's performance in missions.
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
        try {
            const response = await fetch('/api/equipment/equip', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    wallet: currentWallet,
                    emissary_id: emissaryId,
                    item_id: parseInt(itemId),
                    slot: slot
                })
            });

            const data = await response.json();
            if (data.error) {
                alert('Error: ' + data.error);
            }
        } catch (error) {
            console.error('Error equipping item:', error);
            alert('Failed to equip item');
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
                alert('Error: ' + data.error);
            }
        } catch (error) {
            console.error('Error unequipping item:', error);
            alert('Failed to unequip item');
        }
    }

    async function equipRune(emissaryId, itemId) {
        try {
            const response = await fetch('/api/equipment/equip', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    wallet: currentWallet,
                    emissary_id: emissaryId,
                    item_id: parseInt(itemId),
                    slot: 'rune'
                })
            });

            const data = await response.json();
            if (data.error) {
                alert('Error: ' + data.error);
            }
        } catch (error) {
            console.error('Error equipping rune:', error);
            alert('Failed to equip rune');
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
                alert('Error: ' + data.error);
            }
        } catch (error) {
            console.error('Error unequipping rune:', error);
            alert('Failed to unequip rune');
        }
    }

    window.unequipAllItems = async function(emissaryId) {
        if (!confirm('Are you sure you want to unequip all items and runes from this emissary?')) {
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
                alert('Error: ' + data.error);
            } else {
                // Reload the modal
                window.showInventoryModal(emissaryId);
            }
        } catch (error) {
            console.error('Error unequipping all items:', error);
            alert('Failed to unequip all items');
        }
    };

    window.closeInventoryModal = function() {
        const modal = document.getElementById('inventory-modal');
        if (modal) {
            modal.classList.remove('active');
        }
    };

    // ===============================================================
    // VAULT PAGE
    // ===============================================================

    async function loadVault(wallet, filterType = null) {
        if (!wallet) return;

        try {
            let url = `/api/vault?wallet=${wallet}`;
            if (filterType) url += `&type=${filterType}`;

            const response = await fetch(url);
            const data = await response.json();

            if (data.error) {
                console.error('Error loading vault:', data.error);
                return;
            }

            vaultItems = data.items || [];
            renderVault();
        } catch (error) {
            console.error('Error loading vault:', error);
        }
    }

    function renderVault() {
        const container = document.getElementById('vault-items-container');
        if (!container) return;

        if (vaultItems.length === 0) {
            container.innerHTML = `
                <div class="mono-block" style="text-align:center; padding:40px;">
                    <p style="color:var(--dim-green);">No items in vault.</p>
                    <p style="margin-top:10px; font-size:11px;">
                        Complete missions to earn items and rewards.
                    </p>
                </div>
            `;
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

                html += `
                    <div class="item-card ${rarityClass} ${equippedClass}">
                        <div style="display:flex; gap:15px; align-items:flex-start;">
                            <img src="${item.image_url || '/img/items/placeholder.png'}"
                                 style="width:64px; height:64px; border:1px solid var(--border-primary);"
                                 onerror="this.src='/img/items/placeholder.png'"/>
                            <div style="flex:1;">
                                <div style="font-weight:600; color:${getRarityColor(item.rarity)};">
                                    ${item.name}
                                </div>
                                <div style="font-size:11px; color:var(--dim-green); margin-top:3px;">
                                    ${item.type.toUpperCase()} · ${item.rarity.toUpperCase()}
                                </div>
                                <div class="item-stats" style="margin-top:8px;">
                                    ${formatStats(item.stats)}
                                </div>
                                ${item.equipped_by ? `
                                    <div style="margin-top:8px; font-size:11px; color:var(--primary-green);">
                                        <span class="eq-icon">╬</span> Equipped: ${item.equipped_by_name || `#${item.equipped_by}`}
                                    </div>
                                ` : ''}
                            </div>
                        </div>
                        <div style="margin-top:15px; display:flex; gap:8px;">
                            ${item.equipped_by ? `
                                <button class="terminal-btn small-btn"
                                        onclick="unequipItem(${item.id})">[UNEQUIP]</button>
                            ` : `
                                <button class="terminal-btn small-btn"
                                        onclick="showEquipModal(${item.id})">[EQUIP]</button>
                            `}
                        </div>
                    </div>
                `;
            });

            html += `</div>`;
        }

        container.innerHTML = html;

        // Update stats
        const total = vaultItems.length;
        const equipped = vaultItems.filter(i => i.equipped_by).length;
        const available = total - equipped;
        const legendary = vaultItems.filter(i => i.rarity === 'legendary').length;

        document.getElementById('vault-total').textContent = total;
        document.getElementById('vault-equipped').textContent = equipped;
        document.getElementById('vault-available').textContent = available;
        document.getElementById('vault-legendary').textContent = legendary;
    }

    // Show emissary selection modal when equipping an item
    window.showEquipModal = function(itemId) {
        if (!currentWallet) {
            alert('Please connect your wallet first.');
            return;
        }

        const modal = document.getElementById('select-emissary-modal');
        if (!modal) return;

        // Find the item
        const item = vaultItems.find(i => i.id === itemId);
        if (!item) {
            alert('Item not found.');
            return;
        }

        // Get READY emissaries from current roster
        const readyEmissaries = currentEmissaries.filter(e => e.state === 'READY');

        if (readyEmissaries.length === 0) {
            alert('No READY emissaries available to equip items.\n\nEmissaries must be in READY state to equip items.');
            return;
        }

        // Build modal content
        let content = `
            <div class="subheading">SELECT EMISSARY TO EQUIP</div>

            <!-- Item Info Card -->
            <div style="border: 1px solid ${getRarityColor(item.rarity)}; padding: 12px; margin: 15px 0; background: rgba(0,0,0,0.3);">
                <div style="display: flex; gap: 12px; align-items: center;">
                    <img src="${item.image_url || '/img/items/placeholder.png'}"
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
                     onclick="selectEmissaryForEquip(${itemId}, '${emissary.token_id}')">
                    <div style="display: grid; grid-template-columns: 60px 1fr auto; gap: 12px; align-items: center;">
                        <img src="${emissary.image_url || '/img/emissary_placeholder.png'}"
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
        if (!currentWallet) {
            alert('Please connect your wallet first.');
            return;
        }

        try {
            const item = vaultItems.find(i => i.id === itemId);
            if (!item) {
                alert('Item not found.');
                return;
            }

            const endpoint = item.type === 'rune' ? '/api/equipment/equip-rune' : '/api/equipment/equip';

            const response = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    wallet: currentWallet,
                    emissary_id: emissaryId,
                    item_id: itemId
                })
            });

            const data = await response.json();

            if (response.ok && data.success) {
                alert(`✓ ${item.name} equipped successfully!`);

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
                alert(`✗ Error: ${data.error || 'Failed to equip item'}`);
            }
        } catch (error) {
            console.error('Error equipping item:', error);
            alert('✗ Network error. Please try again.');
        }
    };

    // ===============================================================
    // GAMBIT D20
    // ===============================================================

    window.showGambitModal = async function(emissaryId) {
        if (!FEATURES.EMBER_GAMBIT_ENABLED) {
            alert('EMBER ROLL is not available yet.');
            return;
        }

        if (!currentWallet) {
            alert('Please connect your wallet first.');
            return;
        }

        // Check status
        try {
            const response = await fetch(`/api/gambit/status?wallet=${currentWallet}`);
            const data = await response.json();

            const rollsToday = data.rolls_today || 0;
            const maxRolls = data.rolls_max || 5;
            const rollsRemaining = maxRolls - rollsToday;
            const isFreeRoll = rollsToday === 0;
            const costPerRoll = isFreeRoll ? 0 : 75;

            const modal = document.getElementById('gambit-modal');
            if (!modal) {
                console.error('Gambit modal not found');
                return;
            }

            const content = `
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:30px; margin-top:20px;">
                    <!-- LEFT COLUMN: Dice & Actions -->
                    <div style="display:flex; flex-direction:column; align-items:center; gap:15px;">
                        <div style="text-align:center;">
                            <div class="dice-display" id="dice-display" style="font-size:40px; font-family:'Alagard',serif; color:var(--gold); text-shadow: 0 0 15px var(--gold); line-height:1.2;">
                                ╔═╗<br/>
                                ║?║<br/>
                                ╚═╝<br/>
                                <span style="font-size:20px;">D20</span>
                            </div>
                        </div>

                        <div id="gambit-rolls-info" style="width:100%; text-align:center; padding:15px; border:1px solid var(--border-primary); background:rgba(0,0,0,0.3);">
                            <div style="font-size:14px;">
                                <strong>Rolls today:</strong> <span id="rolls-count">${rollsToday}/${maxRolls}</span><br/>
                                <strong>Next roll:</strong> <span id="next-roll-cost">${isFreeRoll ? '<span style="color:#4ade80;">FREE!</span>' : `<span style="color:var(--gold);">${costPerRoll} $EMBER</span>`}</span>
                            </div>
                        </div>

                        <div id="balance-display" style="width:100%; text-align:center; font-size:14px; margin-bottom:10px;">
                            Your Balance: <span style="color:var(--gold); font-weight:600;">[E] <span id="ember-balance">${currentBalance.ember_balance.toLocaleString()}</span> $EMBER</span>
                        </div>

                        ${rollsRemaining > 0 ? `
                            <button class="modal-btn btn-gambit" onclick="rollGambitDice('${emissaryId}', ${costPerRoll})" style="width:100%; background:#a855f7; border-color:#a855f7; color:#fff; padding:15px; font-size:14px;">
                                [ROLL THE D20${isFreeRoll ? ' - FREE' : ' - ' + costPerRoll + ' $EMBER'}]
                            </button>
                        ` : `
                            <button class="modal-btn" disabled style="width:100%; opacity:0.3; cursor:not-allowed; padding:15px;">
                                [NO ROLLS REMAINING TODAY]
                            </button>
                        `}

                        <!-- RESULT DISPLAY AREA - Initially hidden by being empty -->
                        <div id="gambit-result-display" style="width:100%; padding:20px; border:2px solid var(--gold); background:rgba(0,0,0,0.7); text-align:center; margin-top:20px; border-radius:4px;">
                            <div id="result-content" style="color:#888; font-size:14px; font-style:italic;">Roll the dice to see your result here...</div>
                        </div>

                        <button class="modal-btn" onclick="closeGambitModal()" style="width:100%; margin-top:10px;">[CLOSE]</button>
                    </div>

                    <!-- RIGHT COLUMN: Possible Outcomes -->
                    <div class="mono-block" style="padding:15px; border-left:3px solid #a855f7; background:rgba(168,85,247,0.05); max-height:600px; overflow-y:auto;">
                        <div class="subheading" style="margin-bottom:10px;">POSSIBLE OUTCOMES</div>
                        <div style="font-size:11px; line-height:2; font-family:monospace;">
                            <div style="display:grid; grid-template-columns:80px 140px 1fr; gap:10px;">
                                <div style="color:#ef4444;">[1]</div>
                                <div style="color:#ef4444;">CRITICAL FAIL</div>
                                <div style="color:#888;">-100 $EMBER</div>

                                <div style="color:#666;">[2-5]</div>
                                <div style="color:#666;">NOTHING</div>
                                <div style="color:#888;">Nothing happens</div>

                                <div style="color:#888;">[6-8]</div>
                                <div style="color:#888;">GRAZE</div>
                                <div style="color:#4ade80;">+50 $EMBER</div>

                                <div style="color:#888;">[9-11]</div>
                                <div style="color:#888;">HIT</div>
                                <div style="color:#4ade80;">+100 $EMBER</div>

                                <div style="color:var(--primary-green);">[12-14]</div>
                                <div style="color:var(--primary-green);">SOLID HIT</div>
                                <div style="color:#4ade80;">+200 $EMBER</div>

                                <div style="color:var(--primary-green);">[15-17]</div>
                                <div style="color:var(--primary-green);">GREAT HIT</div>
                                <div style="color:#4ade80;">+350 $EMBER</div>

                                <div style="color:#3b82f6;">[18]</div>
                                <div style="color:#3b82f6;">CRITICAL!</div>
                                <div style="color:#4ade80;">+500 $EMBER + Item</div>

                                <div style="color:#a855f7;">[19]</div>
                                <div style="color:#a855f7;">SUPERIOR</div>
                                <div style="color:#4ade80;">+500 $EMBER + Item</div>

                                <div style="color:var(--gold); font-weight:bold;">[20]</div>
                                <div style="color:var(--gold); font-weight:bold;">NATURAL 20!</div>
                                <div style="color:#4ade80;">+500 $EMBER + Item</div>
                            </div>
                        </div>
                    </div>
                </div>
            `;

            const modalBody = modal.querySelector('.terminal-modal-body');
            if (modalBody) {
                modalBody.innerHTML = content;
            }

            modal.classList.add('active');
        } catch (error) {
            console.error('Error showing gambit modal:', error);
            alert('Failed to load EMBER ROLL status');
        }
    };

    window.closeGambitModal = function() {
        const modal = document.getElementById('gambit-modal');
        if (modal) {
            modal.classList.remove('active');
        }
    };

    // Test function to verify result display works
    window.testGambitResultDisplay = function() {
        console.log('🧪 Testing result display area...');
        const resultContent = document.getElementById('result-content');
        const rollsCountElem = document.getElementById('rolls-count');
        const emberBalanceElem = document.getElementById('ember-balance');

        if (!resultContent) {
            console.error('❌ result-content element not found!');
            return;
        }

        console.log('✅ Elements found');
        resultContent.innerHTML = `
            <div style="font-size:18px; color:var(--gold); margin-bottom:15px; font-weight:600;">
                🧪 TEST RESULT
            </div>
            <div style="color:#4ade80; font-size:18px;">+999 $EMBER (TEST)</div>
        `;

        // Test updating counters
        if (rollsCountElem) rollsCountElem.textContent = '1/5';
        if (emberBalanceElem) emberBalanceElem.textContent = '999';

        console.log('✅ Test content inserted successfully');
    };

    window.rollGambitDice = async function(emissaryId, cost) {
        const diceDisplay = document.getElementById('dice-display');
        if (!diceDisplay) return;

        // Disable button during roll
        const rollBtn = document.querySelector('.btn-gambit');
        if (rollBtn) {
            rollBtn.disabled = true;
            rollBtn.textContent = '[ROLLING...]';
            rollBtn.style.color = '#fff'; // Keep text visible during roll
        }

        // Animate dice - faster animation
        let counter = 0;
        const interval = setInterval(() => {
            const randomNum = Math.floor(Math.random() * 20) + 1;
            diceDisplay.innerHTML = `╔═╗<br/>║${randomNum}║<br/>╚═╝<br/><span style="font-size:20px;">D20</span>`;
            counter++;
            if (counter > 25) {
                clearInterval(interval);
                performGambitRoll(emissaryId, cost);
            }
        }, 80);
    };

    async function performGambitRoll(emissaryId, cost) {
        try {
            console.log('📡 Sending roll request:', { wallet: currentWallet, cost });
            const response = await fetch('/api/gambit/roll', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    wallet: currentWallet,
                    emissary_id: emissaryId,
                    cost: cost
                })
            });

            console.log('📨 Response status:', response.status);
            const data = await response.json();
            console.log('📦 Response data:', data);

            if (data.error) {
                console.error('❌ Backend error:', data.error);
                // Show error in result area
                const resultContent = document.getElementById('result-content');

                if (resultContent) {
                    resultContent.innerHTML = `
                        <div style="font-size:18px; color:#ef4444; margin-bottom:15px; font-weight:600;">
                            ❌ ERROR
                        </div>
                        <div style="color:#888; font-size:14px;">${data.error}</div>
                    `;
                } else {
                    alert('Error: ' + data.error);
                }

                // Re-enable button
                const rollBtn = document.querySelector('.btn-gambit');
                if (rollBtn) {
                    rollBtn.disabled = false;
                    rollBtn.textContent = '[RETRY]';
                }
                return;
            }

            if (!data.success) {
                console.error('❌ Roll failed:', data);
                alert('Roll failed. Please try again.');
                return;
            }

            console.log('✅ Roll successful, showing result');
            showGambitResult(data, emissaryId);
        } catch (error) {
            console.error('❌ Error rolling dice:', error);
            // Show error in result area
            const resultContent = document.getElementById('result-content');

            if (resultContent) {
                resultContent.innerHTML = `
                    <div style="font-size:18px; color:#ef4444; margin-bottom:15px; font-weight:600;">
                        ❌ NETWORK ERROR
                    </div>
                    <div style="color:#888; font-size:14px;">${error.message}</div>
                `;
            } else {
                alert('Error rolling dice. Please try again.');
            }

            // Re-enable button
            const rollBtn = document.querySelector('.btn-gambit');
            if (rollBtn) {
                rollBtn.disabled = false;
                rollBtn.textContent = '[RETRY]';
            }
        }
    }

    function showGambitResult(result, emissaryId) {
        console.log('🎲 showGambitResult called with:', result);

        const diceDisplay = document.getElementById('dice-display');
        const resultContent = document.getElementById('result-content');
        const rollBtn = document.querySelector('.btn-gambit');
        const rollsCountElem = document.getElementById('rolls-count');
        const nextRollCostElem = document.getElementById('next-roll-cost');
        const emberBalanceElem = document.getElementById('ember-balance');

        console.log('Elements found:', {
            diceDisplay: !!diceDisplay,
            resultContent: !!resultContent,
            rollBtn: !!rollBtn,
            rollsCountElem: !!rollsCountElem,
            nextRollCostElem: !!nextRollCostElem,
            emberBalanceElem: !!emberBalanceElem
        });

        if (!diceDisplay || !resultContent) {
            console.error('❌ Missing required elements for result display');
            return;
        }

        const roll = result.roll || result.result;
        const emberChange = result.ember_change || 0;
        let title = '';
        let diceStyle = '';
        let outcomeText = '';
        let rewardsHtml = '';

        // Determine outcome based on roll
        if (roll === 1) {
            title = '✗ CRITICAL FAIL!';
            diceStyle = 'color:#ef4444; animation: shake 0.5s;';
            outcomeText = 'CRITICAL FAIL';
            rewardsHtml = `<div style="color:#ef4444; font-size:16px;">${emberChange} $EMBER</div>`;
        } else if (roll >= 2 && roll <= 5) {
            title = 'NOTHING';
            diceStyle = 'color:#666;';
            outcomeText = 'NOTHING';
            rewardsHtml = `<div style="color:#888; font-size:14px;">Nothing happens</div>`;
        } else if (roll >= 6 && roll <= 8) {
            title = 'GRAZE!';
            diceStyle = 'color:#888;';
            outcomeText = 'GRAZE';
            rewardsHtml = `<div style="color:#4ade80; font-size:18px;">+${emberChange} $EMBER</div>`;
        } else if (roll >= 9 && roll <= 11) {
            title = 'HIT!';
            diceStyle = 'color:#888;';
            outcomeText = 'HIT';
            rewardsHtml = `<div style="color:#4ade80; font-size:18px;">+${emberChange} $EMBER</div>`;
        } else if (roll >= 12 && roll <= 14) {
            title = '✓ SOLID HIT!';
            diceStyle = 'color:var(--primary-green);';
            outcomeText = 'SOLID HIT';
            rewardsHtml = `<div style="color:#4ade80; font-size:18px;">+${emberChange} $EMBER</div>`;
        } else if (roll >= 15 && roll <= 17) {
            title = '✓✓ GREAT HIT!';
            diceStyle = 'color:var(--primary-green);';
            outcomeText = 'GREAT HIT';
            rewardsHtml = `<div style="color:#4ade80; font-size:18px;">+${emberChange} $EMBER</div>`;
        } else if (roll === 18) {
            title = '⚡ CRITICAL!';
            diceStyle = 'color:#3b82f6; animation: pulse 1s infinite;';
            outcomeText = 'CRITICAL';
            rewardsHtml = `
                <div style="color:#4ade80; font-size:18px;">+${emberChange} $EMBER</div>
                ${result.item ? `<div style="color:#9ca3af; font-size:14px; margin-top:8px;">📦 ${result.item}</div>` : ''}
            `;
        } else if (roll === 19) {
            title = '⭐ SUPERIOR!';
            diceStyle = 'color:#a855f7; animation: pulse 1s infinite;';
            outcomeText = 'SUPERIOR';
            rewardsHtml = `
                <div style="color:#4ade80; font-size:18px;">+${emberChange} $EMBER</div>
                ${result.item ? `<div style="color:#9ca3af; font-size:14px; margin-top:8px;">📦 ${result.item}</div>` : ''}
            `;
        } else if (roll === 20) {
            title = '★ NATURAL 20! ★';
            diceStyle = 'color:var(--gold); animation: pulse 1s infinite; text-shadow: 0 0 30px var(--gold);';
            outcomeText = 'NATURAL 20!';
            rewardsHtml = `
                <div style="color:#4ade80; font-size:20px; font-weight:bold;">+${emberChange} $EMBER</div>
                ${result.item ? `<div style="color:#a855f7; font-size:14px; margin-top:8px;">📦 ${result.item}</div>` : ''}
            `;
        }

        // Update dice display with result
        diceDisplay.innerHTML = `╔═╗<br/>║${roll}║<br/>╚═╝<br/><span style="font-size:20px;">${outcomeText}</span>`;
        diceDisplay.style = `font-size:60px; font-family:'Alagard',serif; ${diceStyle} line-height:1.2;`;

        // Show result in dedicated area
        resultContent.innerHTML = `
            <div style="font-size:18px; color:var(--gold); margin-bottom:15px; font-weight:600;">
                ${title}
            </div>
            ${rewardsHtml}

            <style>
                @keyframes shake {
                    0%, 100% { transform: translateX(0); }
                    25% { transform: translateX(-10px); }
                    75% { transform: translateX(10px); }
                }
                @keyframes pulse {
                    0%, 100% { transform: scale(1); }
                    50% { transform: scale(1.05); }
                }
            </style>
        `;

        console.log('✅ Result content updated, innerHTML length:', resultContent.innerHTML.length);

        // Update the roll counter and balance display
        if (result.new_balance !== undefined && emberBalanceElem) {
            emberBalanceElem.textContent = result.new_balance.toLocaleString();
            console.log('💰 Updated balance display:', result.new_balance);
        }

        // Update rolls counter
        const rollsRemaining = result.rolls_remaining || 0;
        const maxRolls = result.gambit_rolls_max || 5;
        const rollsUsed = maxRolls - rollsRemaining;

        if (rollsCountElem) {
            rollsCountElem.textContent = `${rollsUsed}/${maxRolls}`;
            console.log(`📊 Updated rolls counter: ${rollsUsed}/${maxRolls}`);
        }

        // Update next roll cost display
        if (nextRollCostElem) {
            const nextCost = rollsRemaining === maxRolls - 1 ? 0 : 75;
            nextRollCostElem.innerHTML = nextCost === 0
                ? '<span style="color:#4ade80;">FREE!</span>'
                : `<span style="color:var(--gold);">${nextCost} $EMBER</span>`;
            console.log(`💵 Updated next roll cost: ${nextCost === 0 ? 'FREE' : nextCost + ' $EMBER'}`);
        }

        // Update button - enable for next roll if available
        if (rollBtn) {
            if (result.rolls_remaining && result.rolls_remaining > 0) {
                rollBtn.disabled = false;
                const nextCost = result.rolls_remaining === (result.gambit_rolls_max || 5) - 1 ? 0 : 75;
                rollBtn.textContent = `[ROLL THE D20${nextCost === 0 ? ' - FREE' : ' - ' + nextCost + ' $EMBER'}]`;
                console.log(`🔄 Button updated for next roll: ${nextCost} $EMBER`);
            } else {
                rollBtn.disabled = true;
                rollBtn.textContent = '[NO ROLLS REMAINING TODAY]';
                rollBtn.style.opacity = '0.3';
                rollBtn.style.cursor = 'not-allowed';
                console.log('🚫 No more rolls available');
            }
        }

        // Reload balance
        console.log('💰 Reloading balance...');
        loadBalance(currentWallet);
    }

    // ===============================================================
    // PUSH MODAL (Mission Acceleration)
    // ===============================================================

    window.showPushModal = async function(emissaryId) {
        console.log('Opening PUSH modal for emissary:', emissaryId);

        const modal = document.getElementById('push-modal');
        if (!modal) return;

        // Find emissary in current roster
        const emissary = currentEmissaries.find(e => String(e.token_id) === String(emissaryId));
        if (!emissary || emissary.state !== 'IN_PROGRESS') {
            alert('No active mission found for this emissary.');
            return;
        }

        // Calculate mission progress
        const now = new Date();
        const startTime = new Date(emissary.mission_start);
        const durationMs = emissary.mission_duration * 60 * 60 * 1000; // hours to ms
        const endTime = new Date(startTime.getTime() + durationMs);

        const elapsedMs = now - startTime;
        const remainingMs = Math.max(0, endTime - now);
        const totalMs = durationMs;

        const progressPercent = Math.min(100, (elapsedMs / totalMs) * 100);
        const remainingPercent = Math.max(0, (remainingMs / totalMs) * 100);

        // Format time remaining
        const remainingHours = Math.floor(remainingMs / (1000 * 60 * 60));
        const remainingMinutes = Math.floor((remainingMs % (1000 * 60 * 60)) / (1000 * 60));
        const timeRemainingStr = remainingHours > 0
            ? `${remainingHours}h ${remainingMinutes}m`
            : `${remainingMinutes}m`;

        // Get mission difficulty (from state message or default to medium)
        let difficulty = 'medium';
        if (emissary.state_message) {
            const msg = emissary.state_message.toLowerCase();
            if (msg.includes('easy')) difficulty = 'easy';
            else if (msg.includes('hard')) difficulty = 'hard';
            else if (msg.includes('legendary')) difficulty = 'legendary';
        }

        // Base costs by difficulty
        const baseCosts = {
            easy: { push25: 50, push50: 150, push100: 400 },
            medium: { push25: 100, push50: 300, push100: 800 },
            hard: { push25: 200, push50: 600, push100: 1500 },
            legendary: { push25: 500, push50: 1500, push100: 4000 }
        };

        // Scale costs based on REMAINING time (not total time)
        const costMultiplier = remainingPercent / 100;
        const costs = {
            push25: Math.ceil(baseCosts[difficulty].push25 * costMultiplier),
            push50: Math.ceil(baseCosts[difficulty].push50 * costMultiplier),
            push100: Math.ceil(baseCosts[difficulty].push100 * costMultiplier)
        };

        // Calculate time reductions
        const remainingHoursFloat = remainingMs / (1000 * 60 * 60);
        const timeReductions = {
            push25: (remainingHoursFloat * 0.25).toFixed(1),
            push50: (remainingHoursFloat * 0.50).toFixed(1),
            push100: remainingHoursFloat.toFixed(1)
        };

        // Build modal content
        const content = `
            <div class="subheading">MISSION ACCELERATION</div>

            <!-- Mission Info Card -->
            <div style="border: 1px solid var(--border-primary); padding: 12px; margin: 15px 0; background: rgba(0,0,0,0.3);">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 12px;">
                    <div>
                        <span style="color: #888;">EMISSARY:</span><br/>
                        <span style="color: var(--text-primary);">${emissary.name || `#${emissary.token_id}`}</span>
                    </div>
                    <div>
                        <span style="color: #888;">DIFFICULTY:</span><br/>
                        <span style="color: var(--text-primary); text-transform: uppercase;">${difficulty}</span>
                    </div>
                    <div>
                        <span style="color: #888;">TIME REMAINING:</span><br/>
                        <span style="color: var(--text-primary);">${timeRemainingStr}</span>
                    </div>
                    <div>
                        <span style="color: #888;">PROGRESS:</span><br/>
                        <span style="color: var(--text-primary);">${progressPercent.toFixed(1)}%</span>
                    </div>
                </div>

                <!-- Progress Bar -->
                <div style="margin-top: 12px;">
                    <div style="background: #1a1a1a; border: 1px solid var(--border-primary); height: 20px; position: relative; overflow: hidden;">
                        <div style="background: linear-gradient(90deg, var(--text-primary) 0%, #ffb84d 100%); height: 100%; width: ${progressPercent}%; transition: width 0.3s ease;"></div>
                        <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 11px; color: #fff; text-shadow: 0 0 3px #000;">
                            ${progressPercent.toFixed(1)}% COMPLETE
                        </div>
                    </div>
                </div>
            </div>

            <!-- Push Options -->
            <div class="subheading" style="margin-top: 20px;">ACCELERATION OPTIONS</div>
            <p style="font-size: 11px; color: #888; margin: 8px 0 15px 0;">
                Costs scaled to remaining time (${remainingPercent.toFixed(0)}% of base cost)
            </p>

            <div style="display: grid; gap: 12px; margin: 15px 0;">
                <!-- 25% Option -->
                <div style="border: 1px solid #f59e0b; padding: 12px; background: rgba(245,158,11,0.05);">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-size: 14px; color: #f59e0b; font-weight: bold;">[25% FASTER]</div>
                            <div style="font-size: 11px; color: #888; margin-top: 4px;">
                                Reduce time by ${timeReductions.push25}h
                            </div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 13px; color: var(--text-primary);">
                                ${costs.push25} $EMBER
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 50% Option -->
                <div style="border: 1px solid #f59e0b; padding: 12px; background: rgba(245,158,11,0.05);">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-size: 14px; color: #f59e0b; font-weight: bold;">[50% FASTER]</div>
                            <div style="font-size: 11px; color: #888; margin-top: 4px;">
                                Reduce time by ${timeReductions.push50}h
                            </div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 13px; color: var(--text-primary);">
                                ${costs.push50} $EMBER
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 100% Option (Instant) -->
                <div style="border: 1px solid #f59e0b; padding: 12px; background: rgba(245,158,11,0.1);">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-size: 14px; color: #f59e0b; font-weight: bold;">[100% INSTANT]</div>
                            <div style="font-size: 11px; color: #888; margin-top: 4px;">
                                Complete mission immediately
                            </div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 13px; color: var(--text-primary);">
                                ${costs.push100} $EMBER
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Action Buttons -->
            <div class="modal-buttons" style="margin-top: 20px;">
                <button class="modal-btn btn-push" onclick="performPush('${emissaryId}', 25, ${costs.push25})">
                    [PUSH 25%]
                </button>
                <button class="modal-btn btn-push" onclick="performPush('${emissaryId}', 50, ${costs.push50})">
                    [PUSH 50%]
                </button>
                <button class="modal-btn btn-push" onclick="performPush('${emissaryId}', 100, ${costs.push100})">
                    [PUSH 100%]
                </button>
                <button class="modal-btn" onclick="closePushModal()">
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

    window.closePushModal = function() {
        const modal = document.getElementById('push-modal');
        if (modal) {
            modal.classList.remove('active');
        }
    };

    window.performPush = async function(emissaryId, pushPercent, cost) {
        if (!currentWallet) {
            alert('Please connect your wallet first.');
            return;
        }

        // Confirm action
        const confirmMsg = `Push mission ${pushPercent}% for ${cost} $EMBER?\n\nThis will reduce the mission time immediately.`;
        if (!confirm(confirmMsg)) {
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
                alert(`✓ Mission accelerated by ${pushPercent}%!\n\nEMBER spent: ${data.ember_spent}\nTime reduced: ${data.time_reduced_hours}h`);

                // Close modal
                closePushModal();

                // Refresh data
                if (window.loadProfileData) {
                    await window.loadProfileData();
                }
            } else {
                alert(`✗ Error: ${data.error || 'Failed to push mission'}`);
            }
        } catch (error) {
            console.error('Error pushing mission:', error);
            alert('✗ Network error. Please try again.');
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
        const emissary = currentEmissaries.find(e => String(e.token_id) === String(emissaryId));
        if (!emissary) {
            alert('Emissary not found.');
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
            alert('Please connect your wallet first.');
            return;
        }

        // Confirm action
        const confirmMsg = `Restore ${amount} energy for ${cost} $EMBER?`;
        if (!confirm(confirmMsg)) {
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
                alert(`✓ Energy restored!\n\n+${amount} energy\nEMBER spent: ${data.ember_spent}\nNew energy: ${data.new_energy}/${data.energy_max}`);

                // Close modal
                closeRecoverModal();

                // Refresh data
                if (window.loadProfileData) {
                    await window.loadProfileData();
                }
            } else {
                alert(`✗ Error: ${data.error || 'Failed to restore energy'}`);
            }
        } catch (error) {
            console.error('Error recovering energy:', error);
            alert('✗ Network error. Please try again.');
        }
    };

    // ===============================================================
    // INITIALIZATION
    // ===============================================================

    window.initInventorySystem = function(wallet) {
        currentWallet = wallet;

        if (wallet) {
            loadBalance(wallet);
        }

        console.log('✅ Inventory system initialized');
    };

    window.switchToVault = function() {
        if (currentWallet) {
            loadVault(currentWallet);
        }
    };

    // Apply feature flags
    if (FEATURES.ASH_PROTOCOL_ENABLED) {
        document.getElementById('ash-balance-display')?.removeAttribute('style');
        document.getElementById('burn-ember-btn')?.removeAttribute('style');
    }

    console.log('%c[INVENTORY] System loaded', 'color: #ff9500; font-weight: bold;');

})();
