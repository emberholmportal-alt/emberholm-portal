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

        return `
            <div class="subheading" style="margin-bottom:15px;">
                EMISSARY INVENTORY - ${emissary.name || emissary.token_id}
            </div>

            <div class="mono-small-note" style="margin-bottom:20px;">
                Equip items and runes to boost your emissary's performance in missions.
            </div>

            <div style="margin-bottom:20px;">
                <strong>Equipment Slots (5)</strong>
                <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(200px, 1fr)); gap:10px; margin-top:10px;">
                    ${slotsHtml}
                </div>
            </div>

            <div style="margin-bottom:20px;">
                <strong>Rune Slots (2)</strong>
                <div style="display:grid; grid-template-columns:repeat(2, 1fr); gap:10px; margin-top:10px;">
                    ${runesHtml}
                </div>
            </div>

            <div class="modal-buttons" style="margin-top:30px;">
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

    // ===============================================================
    // GAMBIT D20
    // ===============================================================

    window.showGambitModal = async function() {
        if (!FEATURES.EMBER_GAMBIT_ENABLED) {
            alert('EMBER GAMBIT is not available yet.');
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

            const rollsRemaining = data.rolls_remaining;

            const modal = document.getElementById('gambit-modal');
            if (!modal) {
                console.error('Gambit modal not found');
                return;
            }

            const content = `
                <div class="subheading">EMBER GAMBIT // ROLL THE D20</div>

                <div class="dice-display" id="dice-display">
                    [?]
                </div>

                <p>Cost per roll: 100 $EMBER</p>
                <p>Rolls remaining today: <span id="gambit-rolls-remaining">${rollsRemaining}</span>/5</p>

                <div class="mono-block" style="margin-top:20px;">
                    <div class="subheading">POSSIBLE REWARDS</div>
                    <div style="font-size:12px; line-height:1.8;">
                        [1]     → CRITICAL FAIL! Lose 100 $EMBER<br/>
                        [2-5]   → Nothing (lose your bet)<br/>
                        [6-8]   → +50 $EMBER<br/>
                        [9-11]  → +100 $EMBER (break even)<br/>
                        [12-14] → +200 $EMBER<br/>
                        [15-17] → +350 $EMBER<br/>
                        [18-19] → +500 $EMBER + Common Item<br/>
                        [20]    → NATURAL 20! +1000 $EMBER + Rare/Epic Item
                    </div>
                </div>

                <p style="margin-top:20px;">Your Balance: [E] ${currentBalance.ember_balance.toLocaleString()} $EMBER</p>

                <div class="modal-buttons">
                    ${rollsRemaining > 0 ? `
                        <button class="modal-btn btn-gambit" onclick="rollGambitDice()">[ROLL THE D20 - 100 $EMBER]</button>
                    ` : `
                        <button class="modal-btn btn-disabled" disabled>[NO ROLLS REMAINING]</button>
                    `}
                    <button class="modal-btn" onclick="closeGambitModal()">[CANCEL]</button>
                </div>
            `;

            const modalBody = modal.querySelector('.terminal-modal-body');
            if (modalBody) {
                modalBody.innerHTML = content;
            }

            modal.classList.add('active');
        } catch (error) {
            console.error('Error showing gambit modal:', error);
        }
    };

    window.closeGambitModal = function() {
        const modal = document.getElementById('gambit-modal');
        if (modal) {
            modal.classList.remove('active');
        }
    };

    window.rollGambitDice = async function() {
        const diceDisplay = document.getElementById('dice-display');
        if (!diceDisplay) return;

        // Animate dice
        let counter = 0;
        const interval = setInterval(() => {
            diceDisplay.textContent = `[${Math.floor(Math.random() * 20) + 1}]`;
            counter++;
            if (counter > 20) {
                clearInterval(interval);
                performGambitRoll();
            }
        }, 100);
    };

    async function performGambitRoll() {
        try {
            const response = await fetch('/api/gambit/roll', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ wallet: currentWallet })
            });

            const data = await response.json();

            if (data.error) {
                alert('Error: ' + data.error);
                closeGambitModal();
                return;
            }

            showGambitResult(data);
        } catch (error) {
            console.error('Error rolling dice:', error);
            alert('Error rolling dice. Please try again.');
            closeGambitModal();
        }
    }

    function showGambitResult(result) {
        const modal = document.getElementById('gambit-modal');
        if (!modal) return;

        let message = '';
        let title = '';

        if (result.roll === 1) {
            title = '✗ ✗ ✗ CRITICAL FAIL! ✗ ✗ ✗';
            message = `You rolled a [1] and lost 100 $EMBER!<br/>Better luck next time.`;
        } else if (result.roll === 20) {
            title = '★ ★ ★ NATURAL 20! ★ ★ ★';
            message = `You rolled a [20]!<br/><br/>[E] +1,000 $EMBER<br/>╬ ${result.item || 'Rare Item'}`;
        } else if (result.ember_change > 0) {
            title = `✓ YOU WON ${result.ember_change} $EMBER!`;
            message = `You rolled a [${result.roll}]`;
        } else {
            title = 'Nothing...';
            message = `You rolled a [${result.roll}]<br/>Better luck next time.`;
        }

        const content = `
            <div style="text-align:center;">
                <div style="font-size:18px; color:var(--gold); margin-bottom:20px;">${title}</div>

                <div class="dice-display">[${result.roll}]</div>

                <div style="font-size:16px; margin:30px 0;">
                    ${message}
                </div>

                <div class="modal-buttons">
                    <button class="modal-btn" onclick="closeGambitModal(); showGambitModal();">[ROLL AGAIN]</button>
                    <button class="modal-btn" onclick="closeGambitModal()">[CLOSE]</button>
                </div>
            </div>
        `;

        const modalBody = modal.querySelector('.terminal-modal-body');
        if (modalBody) {
            modalBody.innerHTML = content;
        }

        // Reload balance
        loadBalance(currentWallet);
    }

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
