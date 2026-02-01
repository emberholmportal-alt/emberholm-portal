/**
 * EMBERHOLM PORTAL - Micro-Missions Module
 * Handles quick adventures that take 1-5 minutes
 */

// =========================================================================
// STATE
// =========================================================================

let microMissionsState = {
    availableMissions: [],
    activeMission: null,
    selectedEmissary: null,
    countdownInterval: null,
    isLoading: false
};

// Difficulty colors and labels
const DIFFICULTY_CONFIG = {
    EASY: { color: '#22c55e', label: 'EASY', icon: '●' },
    MEDIUM: { color: '#eab308', label: 'MEDIUM', icon: '●●' },
    HARD: { color: '#ef4444', label: 'HARD', icon: '●●●' }
};

// =========================================================================
// API CALLS
// =========================================================================

/**
 * Get available micro-missions
 */
async function getMicroMissions() {
    try {
        const response = await fetch('/api/micro-missions');
        const data = await response.json();
        if (data.success) {
            microMissionsState.availableMissions = data.missions;
            return data.missions;
        }
        return [];
    } catch (error) {
        console.error('[MicroMissions] Error fetching missions:', error);
        return [];
    }
}

/**
 * Get active micro-mission for wallet
 */
async function getActiveMicroMission(wallet) {
    try {
        const response = await fetch(`/api/micro-mission/active/${wallet.toLowerCase()}`);
        const data = await response.json();
        if (data.success && data.active) {
            microMissionsState.activeMission = data.micro_mission;
            return data.micro_mission;
        }
        microMissionsState.activeMission = null;
        return null;
    } catch (error) {
        console.error('[MicroMissions] Error fetching active mission:', error);
        return null;
    }
}

/**
 * Start a micro-mission
 */
async function startMicroMission(wallet, tokenId, missionId) {
    try {
        const response = await fetch('/api/micro-mission/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                wallet: wallet.toLowerCase(),
                emissary_token_id: tokenId,
                micro_mission_id: missionId
            })
        });
        const data = await response.json();
        if (data.success) {
            microMissionsState.activeMission = data.active_mission;
            return data;
        }
        if (data.error) {
            showInfoModal('MISSION ERROR', data.error);
        }
        return null;
    } catch (error) {
        console.error('[MicroMissions] Error starting mission:', error);
        return null;
    }
}

/**
 * Make a choice in a micro-mission
 */
async function makeMicroMissionChoice(wallet, activeId, choice) {
    try {
        const response = await fetch('/api/micro-mission/choice', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                wallet: wallet.toLowerCase(),
                active_micro_mission_id: activeId,
                choice: choice
            })
        });
        const data = await response.json();
        if (data.success) {
            // Update local state
            if (microMissionsState.activeMission) {
                microMissionsState.activeMission.choice_made = choice;
            }
            return data;
        }
        return null;
    } catch (error) {
        console.error('[MicroMissions] Error making choice:', error);
        return null;
    }
}

/**
 * Complete a micro-mission and claim rewards
 */
async function completeMicroMission(wallet, activeId) {
    try {
        const response = await fetch('/api/micro-mission/complete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                wallet: wallet.toLowerCase(),
                active_micro_mission_id: activeId
            })
        });
        const data = await response.json();
        if (data.success) {
            // Show rewards
            showMissionRewardsModal(data);
            microMissionsState.activeMission = null;
            return data;
        }
        if (data.error) {
            if (data.remaining_seconds) {
                // Mission not complete yet
                return { waiting: true, remaining: data.remaining_seconds };
            }
            showInfoModal('ERROR', data.error);
        }
        return null;
    } catch (error) {
        console.error('[MicroMissions] Error completing mission:', error);
        return null;
    }
}

// =========================================================================
// UI RENDERING
// =========================================================================

/**
 * Initialize micro-missions section
 */
async function initMicroMissionsSection() {
    const wallet = window.connectedWallet;

    if (!wallet) {
        showInfoModal('CONNECT WALLET', 'Please connect your wallet to access Micro-Missions.');
        return false;
    }

    microMissionsState.isLoading = true;
    updateMicroMissionsLoading(true);

    // Check for active mission first
    const activeMission = await getActiveMicroMission(wallet);

    if (activeMission) {
        // Show active mission UI
        renderActiveMission(activeMission);
    } else {
        // Load available missions
        const missions = await getMicroMissions();
        renderMissionsList(missions);
    }

    microMissionsState.isLoading = false;
    updateMicroMissionsLoading(false);
    return true;
}

/**
 * Update loading state
 */
function updateMicroMissionsLoading(isLoading) {
    const container = document.getElementById('micro-missions-content');
    if (!container) return;

    if (isLoading) {
        container.innerHTML = `
            <div class="loading-container">
                <div class="loading-spinner"></div>
                <p>Loading missions...</p>
            </div>
        `;
    }
}

/**
 * Render list of available missions
 */
function renderMissionsList(missions) {
    const container = document.getElementById('micro-missions-content');
    if (!container) return;

    if (!missions || missions.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <p>No missions available at this time.</p>
                <p class="dim">Check back later for new adventures!</p>
            </div>
        `;
        return;
    }

    // Group by difficulty
    const easy = missions.filter(m => m.difficulty === 'EASY');
    const medium = missions.filter(m => m.difficulty === 'MEDIUM');
    const hard = missions.filter(m => m.difficulty === 'HARD');

    container.innerHTML = `
        <div class="micro-missions-header">
            <h3>AVAILABLE MICRO-MISSIONS</h3>
            <p class="subtitle">Quick adventures for your Emissaries</p>
        </div>

        ${easy.length > 0 ? `
            <div class="missions-section">
                <div class="section-title" style="color: ${DIFFICULTY_CONFIG.EASY.color}">
                    ${DIFFICULTY_CONFIG.EASY.icon} EASY MISSIONS
                </div>
                ${renderMissionCards(easy)}
            </div>
        ` : ''}

        ${medium.length > 0 ? `
            <div class="missions-section">
                <div class="section-title" style="color: ${DIFFICULTY_CONFIG.MEDIUM.color}">
                    ${DIFFICULTY_CONFIG.MEDIUM.icon} MEDIUM MISSIONS
                </div>
                ${renderMissionCards(medium)}
            </div>
        ` : ''}

        ${hard.length > 0 ? `
            <div class="missions-section">
                <div class="section-title" style="color: ${DIFFICULTY_CONFIG.HARD.color}">
                    ${DIFFICULTY_CONFIG.HARD.icon} HARD MISSIONS
                </div>
                ${renderMissionCards(hard)}
            </div>
        ` : ''}
    `;
}

/**
 * Render mission cards
 */
function renderMissionCards(missions) {
    return `
        <div class="missions-grid">
            ${missions.map(mission => {
                const diff = DIFFICULTY_CONFIG[mission.difficulty];
                const duration = formatDuration(mission.duration_seconds);
                const emberReward = mission.ember_reward || mission.pyre_reward;
                const rewardMin = emberReward?.min || 0;
                const rewardMax = emberReward?.max || 0;

                return `
                    <div class="mission-card" onclick="selectMicroMission('${mission.id}')">
                        <div class="mission-card-header">
                            <span class="mission-difficulty" style="color: ${diff.color}">
                                ${diff.label}
                            </span>
                            <span class="mission-duration">${duration}</span>
                        </div>
                        <h4 class="mission-name">${mission.name}</h4>
                        <p class="mission-description">${mission.description || ''}</p>
                        <div class="mission-rewards">
                            <span class="reward ember-reward">
                                ${rewardMin}-${rewardMax} EMBER
                            </span>
                            ${mission.xp_reward ? `
                                <span class="reward xp-reward">
                                    +${mission.xp_reward.min}-${mission.xp_reward.max} XP
                                </span>
                            ` : ''}
                            ${mission.aura_chance > 0 ? `
                                <span class="reward aura-reward">
                                    ${mission.aura_chance}% Aura
                                </span>
                            ` : ''}
                        </div>
                        <button class="terminal-btn start-mission-btn">
                            [START MISSION]
                        </button>
                    </div>
                `;
            }).join('')}
        </div>
    `;
}

/**
 * Handle mission selection
 */
function selectMicroMission(missionId) {
    const mission = microMissionsState.availableMissions.find(m => m.id === missionId);
    if (!mission) return;

    // Show emissary selection modal
    showEmissarySelectionModal(mission);
}

/**
 * Show emissary selection for mission
 */
function showEmissarySelectionModal(mission) {
    // Get available emissaries (READY state only)
    const emissaries = window.userEmissaries || [];
    const readyEmissaries = emissaries.filter(e => {
        const state = e.current_state || e.dynamic_state?.state;
        return state === 'READY' || !state;
    });

    if (readyEmissaries.length === 0) {
        showInfoModal('NO EMISSARIES', 'You need at least one READY emissary to start a mission.\n\nAll your emissaries are currently busy or fallen.');
        return;
    }

    let modal = document.getElementById('emissary-select-modal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'emissary-select-modal';
        modal.className = 'modal-overlay';
        document.body.appendChild(modal);
    }

    modal.innerHTML = `
        <div class="modal-content emissary-select-modal">
            <div class="modal-header">
                <h2 class="modal-title">SELECT EMISSARY</h2>
                <p class="modal-subtitle">Choose who will embark on: ${mission.name}</p>
            </div>

            <div class="emissary-list">
                ${readyEmissaries.map(e => {
                    const tokenId = e.token_id || e.tokenId;
                    const name = e.name || `Emissary #${tokenId}`;
                    const level = e.stats?.level || e.dynamic_state?.xp_level || 1;
                    const guild = e.guild || 'Unknown Guild';

                    return `
                        <div class="emissary-row" onclick="confirmMissionStart('${mission.id}', '${tokenId}')">
                            <div class="emissary-avatar">
                                <img src="${e.image_url || '/img/emissary-placeholder.png'}" alt="${name}">
                            </div>
                            <div class="emissary-info">
                                <div class="emissary-name">${name}</div>
                                <div class="emissary-details">
                                    Level ${level} | ${guild}
                                </div>
                            </div>
                            <div class="emissary-status ready">READY</div>
                        </div>
                    `;
                }).join('')}
            </div>

            <div class="modal-footer">
                <button class="terminal-btn secondary" onclick="closeEmissarySelectModal()">
                    [CANCEL]
                </button>
            </div>
        </div>
    `;

    modal.style.display = 'flex';
    modal.classList.add('modal-active');
}

/**
 * Close emissary selection modal
 */
function closeEmissarySelectModal() {
    const modal = document.getElementById('emissary-select-modal');
    if (modal) {
        modal.classList.remove('modal-active');
        setTimeout(() => modal.style.display = 'none', 300);
    }
}

/**
 * Confirm and start mission
 */
async function confirmMissionStart(missionId, tokenId) {
    closeEmissarySelectModal();

    const mission = microMissionsState.availableMissions.find(m => m.id === missionId);
    if (!mission) return;

    const wallet = window.connectedWallet;
    if (!wallet) {
        showInfoModal('WALLET REQUIRED', 'Please connect your wallet first.');
        return;
    }

    // Show loading
    showInfoModal('STARTING MISSION', 'Preparing your emissary for adventure...');

    const result = await startMicroMission(wallet, tokenId, missionId);

    if (result && result.success) {
        closeInfoModal();
        renderActiveMission(result.active_mission);
    }
}

/**
 * Render active mission UI
 */
function renderActiveMission(mission) {
    const container = document.getElementById('micro-missions-content');
    if (!container) return;

    const missionDetails = microMissionsState.availableMissions.find(m => m.id === mission.mission_id);
    const missionName = mission.name || missionDetails?.name || mission.mission_id;

    container.innerHTML = `
        <div class="active-mission-container">
            <div class="active-mission-header">
                <h3>MISSION IN PROGRESS</h3>
                <div class="mission-title">${missionName}</div>
            </div>

            <div class="mission-narrative">
                <p class="narrative-text">${mission.narrative_intro || 'Your emissary ventures forth...'}</p>
            </div>

            <div class="mission-timer" id="mission-timer">
                <div class="timer-label">Time Remaining</div>
                <div class="timer-value" id="timer-value">--:--</div>
                <div class="timer-bar">
                    <div class="timer-progress" id="timer-progress"></div>
                </div>
            </div>

            ${mission.status === 'active' && mission.choices && mission.choices.length > 0 && !mission.choice_made ? `
                <div class="mission-choices">
                    <h4>Choose Your Action</h4>
                    <div class="choices-grid">
                        ${mission.choices.map(choice => `
                            <button class="choice-btn" onclick="handleMissionChoice('${mission.active_id}', '${choice.id}')">
                                ${choice.icon ? `<span class="choice-icon">${choice.icon}</span>` : ''}
                                <span class="choice-text">${choice.text}</span>
                            </button>
                        `).join('')}
                    </div>
                </div>
            ` : mission.choice_made ? `
                <div class="choice-made">
                    <p>Choice made: <strong>${mission.choice_made}</strong></p>
                    <p class="dim">Awaiting results...</p>
                </div>
            ` : ''}

            <div class="mission-actions">
                <button class="terminal-btn large-btn" id="complete-mission-btn" disabled onclick="handleMissionComplete('${mission.active_id}')">
                    [CLAIM REWARDS]
                </button>
            </div>
        </div>
    `;

    // Start countdown
    startMissionCountdown(mission);
}

/**
 * Handle mission choice
 */
async function handleMissionChoice(activeId, choice) {
    const wallet = window.connectedWallet;
    if (!wallet) {
        showInfoModal('WALLET REQUIRED', 'Please connect your wallet first.');
        return;
    }

    const result = await makeMicroMissionChoice(wallet, activeId, choice);
    if (result) {
        // Refresh active mission view
        const activeMission = await getActiveMicroMission(wallet);
        if (activeMission) {
            renderActiveMission(activeMission);
        }
    }
}

/**
 * Handle mission completion
 */
async function handleMissionComplete(activeId) {
    const wallet = window.connectedWallet;
    if (!wallet) {
        showInfoModal('WALLET REQUIRED', 'Please connect your wallet first.');
        return;
    }

    const btn = document.getElementById('complete-mission-btn');
    if (btn) {
        btn.disabled = true;
        btn.textContent = '[CLAIMING...]';
    }

    const result = await completeMicroMission(wallet, activeId);

    if (result && result.waiting) {
        // Still waiting
        if (btn) {
            btn.disabled = true;
            btn.textContent = `[WAIT ${result.remaining}s]`;
        }
    } else if (result && result.success) {
        // Refresh to show missions list
        await initMicroMissionsSection();
    } else {
        if (btn) {
            btn.disabled = false;
            btn.textContent = '[CLAIM REWARDS]';
        }
    }
}

/**
 * Start countdown timer for active mission
 */
function startMissionCountdown(mission) {
    // Clear any existing interval
    if (microMissionsState.countdownInterval) {
        clearInterval(microMissionsState.countdownInterval);
    }

    const endsAt = new Date(mission.ends_at);
    const startedAt = new Date(mission.started_at);
    const totalDuration = endsAt - startedAt;

    function updateTimer() {
        const now = new Date();
        const remaining = Math.max(0, endsAt - now);
        const elapsed = now - startedAt;
        const progress = Math.min(100, (elapsed / totalDuration) * 100);

        const timerValue = document.getElementById('timer-value');
        const timerProgress = document.getElementById('timer-progress');
        const completeBtn = document.getElementById('complete-mission-btn');

        if (timerValue) {
            if (remaining <= 0) {
                timerValue.textContent = 'COMPLETE!';
                timerValue.classList.add('complete');
            } else {
                const minutes = Math.floor(remaining / 60000);
                const seconds = Math.floor((remaining % 60000) / 1000);
                timerValue.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            }
        }

        if (timerProgress) {
            timerProgress.style.width = `${progress}%`;
        }

        if (completeBtn) {
            if (remaining <= 0) {
                completeBtn.disabled = false;
                completeBtn.textContent = '[CLAIM REWARDS]';
            } else {
                completeBtn.disabled = true;
                completeBtn.textContent = '[WAITING...]';
            }
        }

        if (remaining <= 0) {
            clearInterval(microMissionsState.countdownInterval);
        }
    }

    updateTimer();
    microMissionsState.countdownInterval = setInterval(updateTimer, 1000);
}

/**
 * Show mission rewards modal
 */
function showMissionRewardsModal(result) {
    const rewards = result.rewards || {};

    let rewardsHtml = '<div class="rewards-list">';

    if (rewards.ember > 0) {
        rewardsHtml += `
            <div class="reward-item ember">
                <span class="reward-value">+${rewards.ember}</span>
                <span class="reward-label">$EMBER</span>
            </div>
        `;
    }

    if (rewards.pyre > 0) {
        rewardsHtml += `
            <div class="reward-item pyre">
                <span class="reward-value">+${rewards.pyre}</span>
                <span class="reward-label">$PYRE</span>
            </div>
        `;
    }

    if (rewards.xp > 0) {
        rewardsHtml += `
            <div class="reward-item xp">
                <span class="reward-value">+${rewards.xp}</span>
                <span class="reward-label">XP</span>
            </div>
        `;
    }

    if (rewards.aura > 0) {
        rewardsHtml += `
            <div class="reward-item aura">
                <span class="reward-value">+${rewards.aura}</span>
                <span class="reward-label">AURA</span>
            </div>
        `;
    }

    rewardsHtml += '</div>';

    const outcomeText = result.outcome_text || 'Mission completed successfully!';

    showInfoModal('MISSION COMPLETE', `
        ${outcomeText}

        ${rewardsHtml}
    `);
}

// =========================================================================
// HELPER FUNCTIONS
// =========================================================================

/**
 * Format duration in seconds to readable string
 */
function formatDuration(seconds) {
    if (seconds < 60) {
        return `${seconds}s`;
    }
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    if (remainingSeconds === 0) {
        return `${minutes}m`;
    }
    return `${minutes}m ${remainingSeconds}s`;
}

/**
 * Cleanup when leaving section
 */
function cleanupMicroMissionsSection() {
    if (microMissionsState.countdownInterval) {
        clearInterval(microMissionsState.countdownInterval);
        microMissionsState.countdownInterval = null;
    }
}

// =========================================================================
// EXPORTS
// =========================================================================

window.initMicroMissionsSection = initMicroMissionsSection;
window.cleanupMicroMissionsSection = cleanupMicroMissionsSection;
window.selectMicroMission = selectMicroMission;
window.confirmMissionStart = confirmMissionStart;
window.handleMissionChoice = handleMissionChoice;
window.handleMissionComplete = handleMissionComplete;
window.closeEmissarySelectModal = closeEmissarySelectModal;
