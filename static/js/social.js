/**
 * EMBERHOLM PORTAL - Social Module
 * Handles country selection, global chat, and social features
 */

// =========================================================================
// STATE
// =========================================================================

let socialState = {
    userProfile: null,
    countries: [],
    messages: [],
    messagesToday: 0,
    dailyLimit: 50,
    emberPerMessage: 0.1,
    chatPollInterval: null,
    isLoadingChat: false
};

// =========================================================================
// API CALLS
// =========================================================================

/**
 * Get user profile from backend
 */
async function getSocialProfile(wallet) {
    try {
        const response = await fetch(`/api/social/profile/${wallet.toLowerCase()}`);
        const data = await response.json();
        if (data.success) {
            socialState.userProfile = data.profile;
            return data.profile;
        }
        return null;
    } catch (error) {
        console.error('[Social] Error fetching profile:', error);
        return null;
    }
}

/**
 * Save user profile (country, etc.)
 */
async function saveSocialProfile(wallet, countryCode, displayName) {
    console.log('[Social] Saving profile:', { wallet, countryCode, displayName });

    if (!wallet) {
        console.error('[Social] No wallet provided');
        return null;
    }

    try {
        const response = await fetch('/api/social/profile', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                wallet: wallet.toLowerCase(),
                country_code: countryCode,
                display_name: displayName || null
            })
        });

        const data = await response.json();
        console.log('[Social] Profile save response:', data);

        if (!response.ok) {
            console.error('[Social] HTTP error:', response.status, data.error);
            return null;
        }

        if (data.success) {
            socialState.userProfile = data.profile;
            return data.profile;
        }

        console.error('[Social] Save failed:', data.error || 'Unknown error');
        return null;
    } catch (error) {
        console.error('[Social] Error saving profile:', error);
        return null;
    }
}

/**
 * Get countries with user counts
 */
async function getCountriesWithUsers() {
    try {
        const response = await fetch('/api/social/countries');
        const data = await response.json();
        if (data.success) {
            socialState.countries = data.countries;
            return data.countries;
        }
        return [];
    } catch (error) {
        console.error('[Social] Error fetching countries:', error);
        return [];
    }
}

/**
 * Get online stats
 */
async function getOnlineStats() {
    try {
        const response = await fetch('/api/social/online-stats');
        const data = await response.json();
        return data.success ? data : null;
    } catch (error) {
        console.error('[Social] Error fetching online stats:', error);
        return null;
    }
}

/**
 * Get global chat messages
 */
async function getGlobalChatMessages(wallet, limit = 50) {
    try {
        const url = wallet
            ? `/api/social/global-chat?limit=${limit}&wallet=${wallet.toLowerCase()}`
            : `/api/social/global-chat?limit=${limit}`;
        const response = await fetch(url);
        const data = await response.json();
        if (data.success) {
            socialState.messages = data.messages;
            socialState.messagesToday = data.messages_today || 0;
            socialState.dailyLimit = data.daily_limit || 50;
            socialState.emberPerMessage = data.ember_per_message || 0.1;
            return data.messages;
        }
        return [];
    } catch (error) {
        console.error('[Social] Error fetching chat:', error);
        return [];
    }
}

/**
 * Send a message to global chat
 */
async function sendGlobalChatMessage(wallet, message) {
    try {
        const response = await fetch('/api/social/global-chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                wallet: wallet.toLowerCase(),
                message: message
            })
        });
        const data = await response.json();

        if (data.success) {
            // Add message to local state
            socialState.messages.push(data.message);
            socialState.messagesToday = data.messages_today;

            // Show ember reward toast
            if (data.ember_earned > 0) {
                showRewardToast(`+${data.ember_earned} $EMBER`, 'chat');
            }

            return data;
        } else {
            // Handle rate limit
            if (response.status === 429) {
                showInfoModal('DAILY LIMIT REACHED', `You've reached the daily message limit (${data.daily_limit}/day).\n\nCome back tomorrow to chat more!`);
            }
            return null;
        }
    } catch (error) {
        console.error('[Social] Error sending message:', error);
        return null;
    }
}

// =========================================================================
// COUNTRY SELECTION MODAL
// =========================================================================

/**
 * Show country selection modal
 */
function showCountrySelectionModal() {
    // Create modal if it doesn't exist
    let modal = document.getElementById('country-modal');
    if (!modal) {
        modal = createCountryModal();
        document.body.appendChild(modal);
    }

    // Show modal
    modal.style.display = 'flex';
    modal.classList.add('modal-active');

    // Render countries
    renderCountryList();

    // Focus search input
    const searchInput = document.getElementById('country-search');
    if (searchInput) {
        setTimeout(() => searchInput.focus(), 100);
    }
}

/**
 * Create the country selection modal HTML
 */
function createCountryModal() {
    const modal = document.createElement('div');
    modal.id = 'country-modal';
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal-content country-modal-content">
            <div class="modal-header">
                <h2 class="modal-title">SELECT YOUR COUNTRY</h2>
                <p class="modal-subtitle">Where are you connecting from, Emissary?</p>
            </div>

            <div class="country-search-container">
                <input type="text" id="country-search" class="terminal-input"
                       placeholder="Search country..." autocomplete="off">
            </div>

            <div class="country-section">
                <div class="country-section-title">Popular</div>
                <div id="popular-countries" class="country-grid"></div>
            </div>

            <div class="country-section">
                <div class="country-section-title">All Countries</div>
                <div id="all-countries" class="country-list"></div>
            </div>

            <div class="modal-footer">
                <p class="modal-note">Your selection will be visible to other players.</p>
                <button id="confirm-country-btn" class="terminal-btn large-btn" disabled>
                    [CONFIRM SELECTION]
                </button>
            </div>
        </div>
    `;

    // Add event listeners
    const searchInput = modal.querySelector('#country-search');
    searchInput.addEventListener('input', (e) => {
        filterCountries(e.target.value);
    });

    const confirmBtn = modal.querySelector('#confirm-country-btn');
    confirmBtn.addEventListener('click', confirmCountrySelection);

    return modal;
}

/**
 * Render country lists
 */
function renderCountryList(filterQuery = '') {
    const popularContainer = document.getElementById('popular-countries');
    const allContainer = document.getElementById('all-countries');

    if (!popularContainer || !allContainer) return;

    // Get countries
    let popular = getPopularCountries();
    let all = getAllCountries();

    // Filter if query provided
    if (filterQuery) {
        const results = searchCountries(filterQuery);
        popular = results.filter(c => c.popular);
        all = results.filter(c => !c.popular);
    }

    // Render popular countries
    popularContainer.innerHTML = popular.map(country => `
        <button class="country-btn" data-code="${country.code}" onclick="selectCountry('${country.code}')">
            <span class="country-flag">${country.flag}</span>
            <span class="country-name">${country.code}</span>
        </button>
    `).join('');

    // Render all countries
    allContainer.innerHTML = all.map(country => `
        <div class="country-row" data-code="${country.code}" onclick="selectCountry('${country.code}')">
            <span class="country-flag">${country.flag}</span>
            <span class="country-name">${country.name}</span>
        </div>
    `).join('');
}

/**
 * Filter countries based on search
 */
function filterCountries(query) {
    renderCountryList(query);
}

// Track selected country
let selectedCountryCode = null;

/**
 * Handle country selection
 */
function selectCountry(code) {
    selectedCountryCode = code;

    // Remove previous selection
    document.querySelectorAll('.country-btn.selected, .country-row.selected').forEach(el => {
        el.classList.remove('selected');
    });

    // Add selection to clicked element
    document.querySelectorAll(`[data-code="${code}"]`).forEach(el => {
        el.classList.add('selected');
    });

    // Enable confirm button
    const confirmBtn = document.getElementById('confirm-country-btn');
    if (confirmBtn) {
        confirmBtn.disabled = false;
        const country = getCountryByCode(code);
        confirmBtn.textContent = `[CONFIRM: ${country.flag} ${country.name}]`;
    }
}

/**
 * Confirm country selection and save to backend
 */
async function confirmCountrySelection() {
    const confirmBtn = document.getElementById('confirm-country-btn');

    // Get wallet from global variable (defined in index.html)
    const wallet = window.connectedWallet;

    console.log('[Social] confirmCountrySelection called:', {
        selectedCountryCode,
        wallet,
        connectedWalletGlobal: typeof connectedWallet !== 'undefined' ? connectedWallet : 'undefined'
    });

    if (!selectedCountryCode) {
        console.error('[Social] No country selected');
        if (confirmBtn) {
            confirmBtn.disabled = false;
            confirmBtn.textContent = '[SELECT A COUNTRY FIRST]';
        }
        return;
    }

    if (!wallet) {
        console.error('[Social] No wallet connected');
        if (confirmBtn) {
            confirmBtn.disabled = false;
            confirmBtn.textContent = '[CONNECT WALLET FIRST]';
        }
        // Show info modal
        if (typeof showInfoModal === 'function') {
            showInfoModal('WALLET REQUIRED', 'Please connect your wallet first to save your country selection.');
        }
        return;
    }

    if (confirmBtn) {
        confirmBtn.disabled = true;
        confirmBtn.textContent = '[SAVING...]';
    }

    const profile = await saveSocialProfile(wallet, selectedCountryCode);

    if (profile) {
        // Close modal
        closeCountryModal();

        // Show success message
        const country = getCountryByCode(selectedCountryCode);
        if (typeof showInfoModal === 'function') {
            showInfoModal('COUNTRY SET', `You are now representing ${country.flag} ${country.name}!\n\nWelcome to the global community, Emissary.`);
        }

        // Load social section
        setTimeout(() => {
            if (typeof loadSocialContent === 'function') {
                loadSocialContent();
            }
        }, 500);
    } else {
        console.error('[Social] Failed to save profile');
        if (confirmBtn) {
            confirmBtn.disabled = false;
            confirmBtn.textContent = '[ERROR - TRY AGAIN]';
        }
    }
}

/**
 * Close country modal
 */
function closeCountryModal() {
    const modal = document.getElementById('country-modal');
    if (modal) {
        modal.classList.remove('modal-active');
        setTimeout(() => {
            modal.style.display = 'none';
        }, 300);
    }
    selectedCountryCode = null;
}

// =========================================================================
// GLOBAL CHAT UI
// =========================================================================

/**
 * Render chat messages
 */
function renderChatMessages(messages) {
    const container = document.getElementById('global-chat-messages');
    if (!container) return;

    if (messages.length === 0) {
        container.innerHTML = `
            <div class="chat-empty">
                <p>No messages yet. Be the first to speak!</p>
            </div>
        `;
        return;
    }

    container.innerHTML = messages.map(msg => {
        const flag = msg.country_code ? getCountryFlag(msg.country_code) : '';
        const displayName = msg.farcaster_username
            ? `@${msg.farcaster_username}`
            : (msg.display_name || msg.wallet.slice(0, 8) + '...');
        const time = new Date(msg.created_at).toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit'
        });
        const isOwnMessage = window.connectedWallet && msg.wallet.toLowerCase() === window.connectedWallet.toLowerCase();

        return `
            <div class="chat-message ${isOwnMessage ? 'own-message' : ''}">
                <div class="chat-message-header">
                    <span class="chat-flag">[${flag}]</span>
                    <span class="chat-username">${displayName}</span>
                    <span class="chat-time">${time}</span>
                </div>
                <div class="chat-message-body">${escapeHtml(msg.message)}</div>
            </div>
        `;
    }).join('');

    // Scroll to bottom
    container.scrollTop = container.scrollHeight;
}

/**
 * Update chat stats display
 */
function updateChatStats() {
    const statsEl = document.getElementById('chat-daily-stats');
    if (statsEl) {
        const remaining = socialState.dailyLimit - socialState.messagesToday;
        statsEl.textContent = `Messages today: ${socialState.messagesToday}/${socialState.dailyLimit}`;
    }

    const rewardEl = document.getElementById('chat-ember-reward');
    if (rewardEl) {
        rewardEl.textContent = `+${socialState.emberPerMessage} $EMBER/msg`;
    }
}

/**
 * Handle chat form submission
 */
async function handleChatSubmit(e) {
    if (e) e.preventDefault();

    const input = document.getElementById('global-chat-input');
    const sendBtn = document.getElementById('global-chat-send');
    const wallet = window.connectedWallet;

    if (!input || !wallet) return;

    const message = input.value.trim();
    if (!message) return;

    // Disable while sending
    input.disabled = true;
    sendBtn.disabled = true;
    sendBtn.textContent = '...';

    const result = await sendGlobalChatMessage(wallet, message);

    if (result) {
        input.value = '';
        renderChatMessages(socialState.messages);
        updateChatStats();
    }

    // Re-enable
    input.disabled = false;
    sendBtn.disabled = false;
    sendBtn.textContent = 'SEND';
    input.focus();
}

/**
 * Start polling for new messages
 */
function startChatPolling(wallet) {
    if (socialState.chatPollInterval) {
        clearInterval(socialState.chatPollInterval);
    }

    // Poll every 10 seconds
    socialState.chatPollInterval = setInterval(async () => {
        if (socialState.isLoadingChat) return;

        socialState.isLoadingChat = true;
        await getGlobalChatMessages(wallet);
        renderChatMessages(socialState.messages);
        updateChatStats();
        socialState.isLoadingChat = false;
    }, 10000);
}

/**
 * Stop chat polling
 */
function stopChatPolling() {
    if (socialState.chatPollInterval) {
        clearInterval(socialState.chatPollInterval);
        socialState.chatPollInterval = null;
    }
}

// =========================================================================
// SOCIAL SECTION MAIN
// =========================================================================

/**
 * Initialize social section when entering
 */
async function initSocialSection() {
    // Use window.connectedWallet for global access
    const wallet = window.connectedWallet;

    console.log('[Social] initSocialSection called, wallet:', wallet);

    if (!wallet) {
        if (typeof showInfoModal === 'function') {
            showInfoModal('CONNECT WALLET', 'Please connect your wallet to access the Social features.');
        }
        return false;
    }

    // Check if user has country set
    const profile = await getSocialProfile(wallet);

    if (!profile || !profile.country_code) {
        // Show country selection modal
        console.log('[Social] No country set, showing modal');
        showCountrySelectionModal();
        return false;
    }

    // User has country, load content
    console.log('[Social] Country set:', profile.country_code);
    socialState.userProfile = profile;
    await loadSocialContent();
    return true;
}

/**
 * Load social content (globe, chat, stats)
 */
async function loadSocialContent() {
    const wallet = window.connectedWallet;

    // Load data in parallel
    const [countries, messages, stats] = await Promise.all([
        getCountriesWithUsers(),
        getGlobalChatMessages(wallet),
        getOnlineStats()
    ]);

    // Update stats display
    updateSocialStats(stats, countries);

    // Render chat
    renderChatMessages(messages);
    updateChatStats();

    // Initialize globe if available
    if (typeof initGlobe === 'function') {
        initGlobe(countries);
    }

    // Start chat polling
    startChatPolling(wallet);
}

/**
 * Update social stats display
 */
function updateSocialStats(stats, countries) {
    if (!stats) return;

    const totalOnline = document.getElementById('social-total-online');
    if (totalOnline) {
        totalOnline.textContent = stats.online_now || 0;
    }

    const totalCountries = document.getElementById('social-total-countries');
    if (totalCountries) {
        totalCountries.textContent = countries ? countries.length : 0;
    }

    const totalUsers = document.getElementById('social-total-users');
    if (totalUsers) {
        totalUsers.textContent = stats.total_users || 0;
    }

    // Update top countries
    const topCountriesEl = document.getElementById('social-top-countries');
    if (topCountriesEl && countries && countries.length > 0) {
        const top5 = countries.slice(0, 5);
        topCountriesEl.innerHTML = top5.map((c, i) => {
            const country = getCountryByCode(c.country_code);
            return `
                <div class="top-country-row">
                    <span class="rank">${i + 1}.</span>
                    <span class="flag">${country ? country.flag : ''}</span>
                    <span class="name">${country ? country.name : c.country_code}</span>
                    <span class="count">${c.user_count} operators</span>
                </div>
            `;
        }).join('');
    }
}

/**
 * Cleanup when leaving social section
 */
function cleanupSocialSection() {
    stopChatPolling();
}

// =========================================================================
// HELPER FUNCTIONS
// =========================================================================

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Show reward toast (uses existing toast system if available)
 */
function showRewardToast(text, type) {
    // Check if there's an existing toast system
    if (typeof showToast === 'function') {
        showToast(text, type);
        return;
    }

    // Simple fallback toast
    const toast = document.createElement('div');
    toast.className = 'reward-toast';
    toast.innerHTML = `<span class="reward-icon">+</span> ${text}`;
    document.body.appendChild(toast);

    setTimeout(() => toast.classList.add('show'), 10);
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// =========================================================================
// EXPORTS
// =========================================================================

// Make functions available globally
window.initSocialSection = initSocialSection;
window.cleanupSocialSection = cleanupSocialSection;
window.showCountrySelectionModal = showCountrySelectionModal;
window.closeCountryModal = closeCountryModal;
window.selectCountry = selectCountry;
window.confirmCountrySelection = confirmCountrySelection;
window.handleChatSubmit = handleChatSubmit;
window.getSocialProfile = getSocialProfile;
window.saveSocialProfile = saveSocialProfile;
window.getGlobalChatMessages = getGlobalChatMessages;
window.sendGlobalChatMessage = sendGlobalChatMessage;
