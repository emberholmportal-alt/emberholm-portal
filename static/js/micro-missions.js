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

        console.log('[MicroMissions] Choice API response:', data);

        if (data.success) {
            // Update local state with multi-step progression
            if (microMissionsState.activeMission) {
                if (data.ending_reached) {
                    // Ending reached - update state
                    microMissionsState.activeMission.ending_reached = data.ending_id;
                    microMissionsState.activeMission.ending_type = data.ending_type;
                    microMissionsState.activeMission.narrative_intro = data.ending_text;
                    microMissionsState.activeMission.choices = [];
                    microMissionsState.activeMission.choices_path = data.choices_path;
                } else {
                    // More steps to go - update with new step data
                    microMissionsState.activeMission.current_step = data.current_step;
                    microMissionsState.activeMission.narrative_intro = data.narrative_text;
                    microMissionsState.activeMission.choices = data.choices;
                    microMissionsState.activeMission.choices_path = data.choices_path;
                }
            }
            return data;
        }

        // Return error info so it can be displayed
        if (data.error) {
            console.error('[MicroMissions] Choice error:', data.error);
            return { success: false, error: data.error };
        }

        return { success: false, error: 'Unknown error' };
    } catch (error) {
        console.error('[MicroMissions] Error making choice:', error);
        return { success: false, error: error.message };
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

/**
 * Abandon a micro-mission with XP penalty
 */
async function abandonMicroMission(wallet, activeId) {
    try {
        const response = await fetch('/api/micro-mission/abandon', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                wallet: wallet.toLowerCase(),
                active_micro_mission_id: activeId
            })
        });
        const data = await response.json();
        if (data.success) {
            microMissionsState.activeMission = null;
            showInfoModal('MISSION ABANDONED', `${data.mission_name}\n\nPenalty: -${data.xp_penalty} XP`);
            return data;
        }
        if (data.error) {
            showInfoModal('ERROR', data.error);
        }
        return null;
    } catch (error) {
        console.error('[MicroMissions] Error abandoning mission:', error);
        return null;
    }
}

// Icon mapping for narrative choices
const CHOICE_ICONS = {
    sword: '⚔️',
    search: '🔍',
    scroll: '📜',
    balance: '⚖️',
    shield: '🛡️',
    compass: '🧭',
    flame: '🔥',
    eye: '👁️',
    ear: '👂',
    chat: '💬',
    run: '🏃',
    gem: '💎',
    rune: '✨',
    mind: '🧠',
    question: '❓',
    music: '🎵',
    book: '📖',
    wind: '💨',
    boxes: '📦',
    footprints: '👣',
    flag: '🚩',
    bell: '🔔',
    heart: '❤️',
    fist: '✊',
    void: '🌀',
    stealth: '🥷',
    trap: '⚡',
    mountain: '⛰️',
    anvil: '🔨'
};

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

    console.log('[MicroMissions] Initializing for wallet:', wallet);
    console.log('[MicroMissions] window.userEmissaries:', window.userEmissaries?.length || 0, 'emissaries');

    microMissionsState.isLoading = true;
    updateMicroMissionsLoading(true);

    // Check for active mission first
    const activeMission = await getActiveMicroMission(wallet);
    console.log('[MicroMissions] Active mission:', activeMission);

    // Show emergency button always if there are issues
    const emergencyDiv = document.getElementById('micro-missions-emergency');
    if (emergencyDiv) {
        // Show emergency button if there's an active mission OR if the mission data looks corrupted
        const isCorrupted = activeMission && (
            !activeMission.choices ||
            activeMission.choices.length === 0 ||
            activeMission.remaining_seconds > 600  // More than 10 minutes is suspicious for micro-missions
        );
        emergencyDiv.style.display = (activeMission || isCorrupted) ? 'block' : 'none';

        if (isCorrupted) {
            console.warn('[MicroMissions] CORRUPTED MISSION DETECTED:', {
                choices: activeMission?.choices?.length || 0,
                remaining: activeMission?.remaining_seconds
            });
        }
    }

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
    // Debug: log emissary states
    console.log('[MicroMissions] All emissaries:', emissaries.map(e => ({
        id: e.token_id || e.tokenId,
        name: e.name,
        current_state: e.current_state,
        dynamic_state: e.dynamic_state?.state
    })));

    // More permissive filter - accept emissaries that are:
    // 1. Explicitly READY
    // 2. Have no state info (assume READY)
    // 3. Have undefined/null state
    const readyEmissaries = emissaries.filter(e => {
        const state = e.current_state || e.dynamic_state?.state;
        // Accept if READY, or if state is missing/undefined
        const isReady = state === 'READY' || state === undefined || state === null || state === '';
        // Reject only if explicitly on mission or fallen
        const isBusy = state === 'ON_MISSION' || state === 'ON_MICRO_MISSION' || state === 'FALLEN' || state === 'CLAIMING';
        return isReady || !isBusy;
    });

    console.log('[MicroMissions] READY emissaries:', readyEmissaries.length);

    if (readyEmissaries.length === 0) {
        // Show more helpful error with debug info
        const states = emissaries.map(e => e.current_state || e.dynamic_state?.state || 'unknown');
        console.error('[MicroMissions] No READY emissaries! States:', states);
        showInfoModal('NO EMISSARIES', `You need at least one READY emissary to start a mission.\n\nAll your emissaries are currently busy or fallen.\n\nTip: Try the [EMERGENCY CLEANUP] button to free stuck emissaries.`);
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
 * Render active mission UI with narrative modal style - Multi-step adventure support
 */
function renderActiveMission(mission) {
    const container = document.getElementById('micro-missions-content');
    if (!container) return;

    const missionDetails = microMissionsState.availableMissions.find(m => m.id === mission.mission_id);
    const missionName = mission.name || missionDetails?.name || mission.mission_id;

    // Get emissary info for portrait
    const emissaries = window.userEmissaries || [];
    // Normalize token IDs for comparison (handle "00042" vs "42")
    const missionTokenId = String(mission.emissary_token_id).replace(/^0+/, '') || '0';
    const emissary = emissaries.find(e => {
        const eTokenId = String(e.token_id || e.tokenId || '').replace(/^0+/, '') || '0';
        return eTokenId === missionTokenId;
    });
    const emissaryName = emissary?.name || `Emissary #${mission.emissary_token_id}`;
    // Use image_url first (actual field name), then fallbacks
    const tokenIdForUrl = String(mission.emissary_token_id).replace(/^0+/, '') || '0';
    const emissaryImage = emissary?.image_url || emissary?.cached_image || emissary?.image ||
        `/img/emissary-placeholder.png`;

    // Get choices (no emojis)
    const choices = mission.choices || [];
    const choicesHTML = choices.map(choice => {
        return `
            <button class="narrative-choice-btn" onclick="handleMissionChoice('${mission.active_id}', '${choice.id}')">
                <span class="choice-icon">[${choice.id}]</span>
                <span class="choice-text">${choice.text}</span>
            </button>
        `;
    }).join('');

    // Calculate step progress for multi-step adventures
    const currentStep = mission.current_step || '1';
    const choicesPath = mission.choices_path || [];
    const stepNumber = choicesPath.length + 1;
    const endingReached = mission.ending_reached;
    const endingType = mission.ending_type;

    // Ending type styling
    const getEndingStyle = (type) => {
        switch(type) {
            case 'LEGENDARY': return 'ending-legendary';
            case 'PERFECT': return 'ending-perfect';
            case 'GOOD': return 'ending-good';
            case 'NEUTRAL': return 'ending-neutral';
            case 'BAD': return 'ending-bad';
            default: return 'ending-neutral';
        }
    };

    container.innerHTML = `
        <div class="narrative-mission-container">
            <!-- Header with emissary portrait -->
            <div class="narrative-header">
                <div class="emissary-portrait">
                    <img src="${emissaryImage}" alt="${emissaryName}" onerror="this.src='/static/images/placeholder-emissary.png'">
                </div>
                <div class="narrative-header-info">
                    <div class="emissary-name">${emissaryName}</div>
                    <div class="mission-title">${missionName}</div>
                    ${!endingReached ? `<div class="step-indicator">Step ${stepNumber}</div>` : ''}
                </div>
            </div>

            <!-- Narrative text -->
            <div class="narrative-scroll">
                ${endingReached ? `
                    <div class="ending-badge ${getEndingStyle(endingType)}">
                        ${endingType || 'COMPLETE'}
                    </div>
                ` : ''}
                <div class="narrative-text">
                    ${mission.narrative_intro || 'Your emissary ventures into the unknown...'}
                </div>
            </div>

            <!-- Timer -->
            <div class="mission-timer" id="mission-timer">
                <div class="timer-bar-container">
                    <div class="timer-progress" id="timer-progress"></div>
                </div>
                <div class="timer-value" id="timer-value">--:--</div>
            </div>

            <!-- Choices or ending state -->
            ${endingReached ? `
                <div class="ending-reached-section">
                    <div class="ending-message">Your journey has reached its conclusion.</div>
                    <div class="ending-hint">Wait for the timer to claim your rewards!</div>
                </div>
            ` : choices.length > 0 ? `
                <div class="narrative-choices">
                    <div class="choices-header">What do you do?</div>
                    <div class="choices-list">
                        ${choicesHTML}
                    </div>
                </div>
            ` : `
                <div class="choice-waiting-section">
                    <div class="choice-waiting">The story unfolds...</div>
                </div>
            `}

            <!-- Action buttons -->
            <div class="narrative-actions">
                <button class="terminal-btn primary-btn" id="complete-mission-btn" disabled onclick="handleMissionComplete('${mission.active_id}')">
                    [CLAIM REWARDS]
                </button>
                <button class="terminal-btn danger-btn" onclick="confirmAbandonMission('${mission.active_id}')">
                    [ABANDON MISSION]
                </button>
            </div>
        </div>
    `;

    // Start countdown
    startMissionCountdown(mission);
}

/**
 * Get choice text by ID (no emojis)
 */
function getChoiceText(choices, choiceId) {
    const choice = choices.find(c => c.id === choiceId);
    if (!choice) return `Option ${choiceId}`;
    return `[${choice.id}] ${choice.text}`;
}

/**
 * Confirm abandon mission dialog
 */
function confirmAbandonMission(activeId) {
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.id = 'abandon-confirm-modal';
    modal.onclick = function(e) { if (e.target === this) this.remove(); };

    modal.innerHTML = `
        <div class="terminal-modal" style="max-width: 400px;">
            <div class="terminal-modal-header">
                ABANDON MISSION?
                <button class="terminal-modal-close" onclick="document.getElementById('abandon-confirm-modal').remove()">×</button>
            </div>
            <div class="terminal-modal-body" style="padding: 20px; text-align: center;">
                <p style="color: #ef4444; margin-bottom: 15px;">⚠️ WARNING ⚠️</p>
                <p style="margin-bottom: 10px;">You will lose <strong style="color: #ef4444;">10 XP</strong> if you abandon this mission!</p>
                <p style="color: #888; font-size: 12px; margin-bottom: 20px;">This action cannot be undone.</p>
                <div style="display: flex; gap: 10px; justify-content: center;">
                    <button class="terminal-btn" onclick="document.getElementById('abandon-confirm-modal').remove()">
                        [CANCEL]
                    </button>
                    <button class="terminal-btn danger-btn" onclick="executeAbandonMission('${activeId}')">
                        [ABANDON]
                    </button>
                </div>
            </div>
        </div>
    `;

    document.body.appendChild(modal);
}

/**
 * Execute mission abandonment
 */
async function executeAbandonMission(activeId) {
    const modal = document.getElementById('abandon-confirm-modal');
    if (modal) modal.remove();

    const wallet = window.connectedWallet;
    if (!wallet) {
        showInfoModal('WALLET REQUIRED', 'Please connect your wallet first.');
        return;
    }

    const result = await abandonMicroMission(wallet, activeId);
    if (result && result.success) {
        // Refresh micro-missions section
        await initMicroMissionsSection();
    }
}

/**
 * Handle mission choice - Multi-step adventure support
 */
async function handleMissionChoice(activeId, choice) {
    const wallet = window.connectedWallet;
    if (!wallet) {
        showInfoModal('WALLET REQUIRED', 'Please connect your wallet first.');
        return;
    }

    console.log('[MicroMissions] Making choice:', choice, 'for mission:', activeId);

    const result = await makeMicroMissionChoice(wallet, activeId, choice);

    if (result && result.success) {
        console.log('[MicroMissions] Choice result:', result);

        // Use the local state which was updated by makeMicroMissionChoice
        if (microMissionsState.activeMission) {
            renderActiveMission(microMissionsState.activeMission);
        } else {
            // Fallback: refresh from server
            const activeMission = await getActiveMicroMission(wallet);
            if (activeMission) {
                renderActiveMission(activeMission);
            }
        }
    } else if (result && result.error) {
        console.error('[MicroMissions] Choice error:', result.error);
        showInfoModal('CHOICE ERROR', result.error);
    } else {
        console.error('[MicroMissions] Choice failed - no result');
        // Try to refresh from server anyway
        const activeMission = await getActiveMicroMission(wallet);
        if (activeMission) {
            renderActiveMission(activeMission);
        } else {
            showInfoModal('ERROR', 'Failed to process choice. Please try refreshing the page.');
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

/**
 * Show micro-missions for a specific hero (called from mission type selector)
 */
async function showMicroMissionsForHero(heroId) {
    const wallet = window.connectedWallet;
    if (!wallet) {
        showInfoModal('WALLET REQUIRED', 'Please connect your wallet first.');
        return;
    }

    // Store the selected hero
    microMissionsState.selectedEmissary = heroId;

    // Load missions if not already loaded
    if (microMissionsState.availableMissions.length === 0) {
        microMissionsState.isLoading = true;
        await getMicroMissions();
        microMissionsState.isLoading = false;
    }

    // Find the hero data
    const emissaries = window.userEmissaries || [];
    const hero = emissaries.find(e => (e.token_id || e.tokenId) === heroId);

    if (!hero) {
        showInfoModal('ERROR', 'Could not find the selected emissary.');
        return;
    }

    // Show modal with mission selection for this specific hero
    let modal = document.getElementById('micro-mission-select-modal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'micro-mission-select-modal';
        modal.className = 'modal-overlay';
        modal.onclick = function(e) { if (e.target === this) this.style.display = 'none'; };
        document.body.appendChild(modal);
    }

    const heroName = hero.name || `Emissary #${heroId}`;
    const missions = microMissionsState.availableMissions;

    modal.innerHTML = `
        <div class="terminal-modal" style="max-width: 600px;">
            <div class="terminal-modal-header">
                SELECT MICRO-MISSION
                <button class="terminal-modal-close" onclick="document.getElementById('micro-mission-select-modal').style.display='none'">×</button>
            </div>
            <div class="terminal-modal-body" style="padding: 15px;">
                <p style="color: #888; margin-bottom: 15px;">
                    Select a quick adventure for <span style="color: var(--gold, #f59e0b);">${heroName}</span>
                </p>
                <div class="micro-mission-list" style="max-height: 400px; overflow-y: auto;">
                    ${missions.map(m => {
                        const diff = DIFFICULTY_CONFIG[m.difficulty] || DIFFICULTY_CONFIG.EASY;
                        return `
                            <div class="micro-mission-item" style="padding: 12px; margin-bottom: 10px; border: 1px solid #333; cursor: pointer; transition: all 0.2s;"
                                 onmouseover="this.style.borderColor='var(--gold)'; this.style.background='rgba(245,158,11,0.1)';"
                                 onmouseout="this.style.borderColor='#333'; this.style.background='transparent';"
                                 onclick="startMicroMissionFromModal('${m.id}', '${heroId}')">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <div>
                                        <div style="color: var(--gold, #f59e0b); font-size: 14px; margin-bottom: 4px;">${m.name}</div>
                                        <div style="color: #888; font-size: 12px;">${m.description || ''}</div>
                                    </div>
                                    <div style="text-align: right;">
                                        <div style="color: ${diff.color}; font-size: 11px;">${diff.label}</div>
                                        <div style="color: #888; font-size: 11px;">${formatDuration(m.duration_seconds)}</div>
                                    </div>
                                </div>
                                <div style="margin-top: 8px; color: #666; font-size: 11px;">
                                    Rewards: ${m.ember_reward?.min || 0}-${m.ember_reward?.max || 0} $EMBER, ${m.pyre_reward?.min || 0}-${m.pyre_reward?.max || 0} $PYRE
                                </div>
                            </div>
                        `;
                    }).join('')}
                </div>
            </div>
        </div>
    `;

    modal.style.display = 'flex';
}

/**
 * Start a micro-mission from the hero-specific modal
 */
async function startMicroMissionFromModal(missionId, heroId) {
    // Hide the selection modal
    const modal = document.getElementById('micro-mission-select-modal');
    if (modal) modal.style.display = 'none';

    // Start the mission
    const wallet = window.connectedWallet;
    if (!wallet) {
        showInfoModal('WALLET REQUIRED', 'Please connect your wallet first.');
        return;
    }

    showInfoModal('STARTING MISSION', 'Preparing your emissary for adventure...');

    const result = await startMicroMission(wallet, heroId, missionId);

    if (result && result.success) {
        closeInfoModal();
        // Navigate to micro-missions section to show the active mission
        if (typeof switchScreen === 'function') {
            switchScreen('micro-missions');
        }
        // Render the active mission
        if (result.active_mission) {
            renderActiveMission(result.active_mission);
        } else {
            initMicroMissionsSection();
        }
    } else {
        showInfoModal('ERROR', result?.error || 'Failed to start mission');
    }
}

// =========================================================================
// EMERGENCY CLEANUP
// =========================================================================

/**
 * Call emergency cleanup endpoint to fix corrupted missions
 */
async function emergencyCleanupMissions() {
    if (!confirm('This will delete ALL active micro-missions and free all stuck emissaries. Continue?')) {
        return;
    }

    showInfoModal('CLEANING UP...', 'Removing corrupted missions...');

    try {
        const response = await fetch('/api/micro-mission/emergency-cleanup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await response.json();

        if (data.success) {
            showInfoModal('CLEANUP COMPLETE', data.message);
            // Refresh the section
            setTimeout(() => {
                closeInfoModal();
                initMicroMissionsSection();
            }, 2000);
        } else {
            showInfoModal('ERROR', data.error || 'Cleanup failed');
        }
    } catch (error) {
        console.error('[MicroMissions] Emergency cleanup error:', error);
        showInfoModal('ERROR', 'Failed to clean up missions: ' + error.message);
    }
}

/**
 * Force refresh emissaries data from backend
 */
async function forceRefreshEmissaries() {
    const wallet = window.connectedWallet;
    if (!wallet) {
        showInfoModal('WALLET REQUIRED', 'Please connect your wallet first.');
        return;
    }

    showInfoModal('REFRESHING...', 'Reloading emissary data...');

    try {
        // First, run emergency cleanup
        await fetch('/api/micro-mission/emergency-cleanup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        // Then reload the page to get fresh data
        setTimeout(() => {
            window.location.reload();
        }, 1000);

    } catch (error) {
        console.error('[MicroMissions] Refresh error:', error);
        showInfoModal('ERROR', 'Failed to refresh: ' + error.message);
    }
}

// =========================================================================
// BUTTON HELPER FUNCTIONS (called from emissary action buttons)
// =========================================================================

/**
 * Show active micro-mission for a specific emissary token
 * Called from [VIEW MISSION] button in emissary list
 */
async function showActiveMicroMissionByToken(tokenId) {
    const wallet = window.connectedWallet;
    if (!wallet) {
        showInfoModal('WALLET REQUIRED', 'Please connect your wallet first.');
        return;
    }

    console.log('[MicroMissions] VIEW MISSION clicked for token:', tokenId);

    // Get the active mission
    const activeMission = await getActiveMicroMission(wallet);

    console.log('[MicroMissions] Active mission data:', activeMission);

    if (activeMission) {
        // Normalize token IDs for comparison (handle "00042" vs "42")
        const requestedToken = String(tokenId).replace(/^0+/, '') || '0';
        const missionToken = String(activeMission.emissary_token_id).replace(/^0+/, '') || '0';

        console.log('[MicroMissions] Token comparison - requested:', requestedToken, 'mission:', missionToken);

        if (requestedToken === missionToken) {
            // Navigate to micro-missions section
            if (typeof switchScreen === 'function') {
                switchScreen('micro-missions');
            }
            // Render the active mission
            renderActiveMission(activeMission);
        } else {
            // Different emissary has the active mission
            showInfoModal('DIFFERENT EMISSARY', `Another emissary (Token #${activeMission.emissary_token_id}) is currently on a micro-mission. Complete or abandon that mission first.`);
        }
    } else {
        // No active mission found - this emissary might be stuck
        console.warn('[MicroMissions] No active mission found for emissary, cleaning up stuck state...');

        // Attempt to fix stuck emissary state via emergency cleanup
        try {
            await fetch('/api/micro-mission/emergency-cleanup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
        } catch (e) {
            console.error('[MicroMissions] Cleanup failed:', e);
        }

        showInfoModal('NO ACTIVE MISSION', 'This emissary has no active micro-mission. The stuck state has been cleaned up. Refreshing...');

        // Reload emissaries to fix stuck state
        setTimeout(() => {
            if (typeof loadHeroes === 'function') {
                loadHeroes();
            }
        }, 1000);
    }
}

/**
 * Abandon micro-mission for a specific emissary token
 * Called from [ABANDON] button in emissary list
 */
async function abandonMicroMissionByToken(tokenId) {
    const wallet = window.connectedWallet;
    if (!wallet) {
        showInfoModal('WALLET REQUIRED', 'Please connect your wallet first.');
        return;
    }

    // Get the active mission to find the activeId
    const activeMission = await getActiveMicroMission(wallet);

    if (!activeMission) {
        showInfoModal('NO MISSION', 'This emissary has no active micro-mission to abandon.');
        // Refresh emissaries to clear the stuck state
        if (typeof loadHeroes === 'function') {
            loadHeroes();
        }
        return;
    }

    // Confirm abandonment
    if (!confirm(`Abandon the current micro-mission? You will lose XP.`)) {
        return;
    }

    // Call the API to abandon
    const result = await abandonMicroMission(wallet, activeMission.id);

    if (result) {
        // Refresh emissaries to update their state
        if (typeof loadHeroes === 'function') {
            loadHeroes();
        }
    }
}

// =========================================================================
// EXPORTS
// =========================================================================

window.initMicroMissionsSection = initMicroMissionsSection;
window.emergencyCleanupMissions = emergencyCleanupMissions;
window.forceRefreshEmissaries = forceRefreshEmissaries;
window.cleanupMicroMissionsSection = cleanupMicroMissionsSection;
window.selectMicroMission = selectMicroMission;
window.confirmMissionStart = confirmMissionStart;
window.handleMissionChoice = handleMissionChoice;
window.handleMissionComplete = handleMissionComplete;
window.closeEmissarySelectModal = closeEmissarySelectModal;
window.showMicroMissionsForHero = showMicroMissionsForHero;
window.startMicroMissionFromModal = startMicroMissionFromModal;
window.confirmAbandonMission = confirmAbandonMission;
window.executeAbandonMission = executeAbandonMission;
window.abandonMicroMission = abandonMicroMission;
window.showActiveMicroMission = showActiveMicroMissionByToken;
window.abandonMicroMissionByToken = abandonMicroMissionByToken;
