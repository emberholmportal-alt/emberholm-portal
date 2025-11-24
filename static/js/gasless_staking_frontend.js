/**
 * 🔥 EMBERHOLM PORTAL - GASLESS STAKING (FRONTEND)
 * ==================================================
 *
 * Funciones JavaScript para firmar mensajes off-chain (sin gas)
 * y enviar transacciones al backend.
 *
 * Usuario NO paga gas - solo firma mensajes para autorizar acciones.
 * Backend ejecuta las transacciones on-chain y paga el gas.
 *
 * @author Emberholm Team
 * @version 1.0
 */

// ====================================
// UTILITY: Sign Message (NO GAS)
// ====================================

/**
 * Firma un mensaje off-chain (GRATIS, sin gas).
 *
 * @param {string} message - Mensaje a firmar
 * @param {string} wallet - Address de la wallet conectada
 * @returns {Promise<string>} Firma en formato hex
 */
async function signMessage(message, wallet) {
    try {
        if (!window.ethereum) {
            throw new Error("MetaMask not installed");
        }

        console.log(`📝 Signing message: "${message}"`);

        // Firma con personal_sign (gratis, solo confirmación de usuario)
        const signature = await ethereum.request({
            method: 'personal_sign',
            params: [
                message,  // Mensaje en texto plano
                wallet    // Address del firmante
            ]
        });

        console.log(`✅ Message signed: ${signature}`);
        return signature;

    } catch (error) {
        console.error("❌ Signing failed:", error);

        if (error.code === 4001) {
            throw new Error("User rejected signature");
        }

        throw new Error(`Failed to sign message: ${error.message}`);
    }
}


// ====================================
// START MISSION (Gasless)
// ====================================

/**
 * Inicia una misión de forma gasless.
 * Usuario solo firma mensaje de autorización (sin gas).
 * Backend stakea el NFT y paga el gas.
 *
 * @param {string} tokenId - ID del NFT (ej: "00123")
 * @param {string} missionId - ID de la misión (ej: "001")
 * @param {string} wallet - Address de la wallet
 * @returns {Promise<object>} Respuesta del backend
 */
async function startMissionGasless(tokenId, missionId, wallet) {
    try {
        // 1. Crear mensaje de autorización
        const timestamp = Date.now();
        const message = `Start mission ${missionId} with token ${tokenId} at ${timestamp}`;

        console.log(`🎮 Starting mission ${missionId} for NFT #${tokenId}...`);

        // 2. Firmar mensaje (GRATIS - solo confirmación)
        const signature = await signMessage(message, wallet);

        // 3. Enviar al backend (backend paga el gas)
        const response = await fetch('/api/mission/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                wallet: wallet,
                token_id: tokenId,
                mission_id: missionId,
                message: message,
                signature: signature
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to start mission');
        }

        console.log(`✅ Mission started! TX: ${data.tx_hash}`);

        // 4. Mostrar notificación al usuario
        showNotification(
            `✅ Mission Started!\n` +
            `Mission: ${missionId}\n` +
            `Duration: ${data.duration_hours}h\n` +
            `(No gas paid by you!)`,
            'success'
        );

        return data;

    } catch (error) {
        console.error("❌ Start mission failed:", error);

        showNotification(
            `❌ Failed to start mission:\n${error.message}`,
            'error'
        );

        throw error;
    }
}


// ====================================
// COMPLETE MISSION (Gasless)
// ====================================

/**
 * Completa una misión de forma gasless.
 * Usuario solo firma mensaje de autorización (sin gas).
 * Backend unstakea el NFT y paga el gas.
 *
 * @param {string} tokenId - ID del NFT
 * @param {string} wallet - Address de la wallet
 * @returns {Promise<object>} Respuesta con recompensas
 */
async function completeMissionGasless(tokenId, wallet) {
    try {
        // 1. Crear mensaje de autorización
        const timestamp = Date.now();
        const message = `Complete mission for token ${tokenId} at ${timestamp}`;

        console.log(`🎁 Completing mission for NFT #${tokenId}...`);

        // 2. Firmar mensaje (GRATIS)
        const signature = await signMessage(message, wallet);

        // 3. Enviar al backend (backend paga el gas)
        const response = await fetch('/api/mission/complete', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                wallet: wallet,
                token_id: tokenId,
                message: message,
                signature: signature
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to complete mission');
        }

        console.log(`✅ Mission completed! Rewards:`, data.rewards);

        // 4. Mostrar recompensas
        showNotification(
            `🎉 Mission Completed!\n` +
            `Rewards:\n` +
            `+${data.rewards.xp} XP\n` +
            `+${data.rewards.aura} Aura\n` +
            `(No gas paid by you!)`,
            'success'
        );

        // 5. Recargar perfil
        await loadProfile(wallet);

        return data;

    } catch (error) {
        console.error("❌ Complete mission failed:", error);

        showNotification(
            `❌ Failed to complete mission:\n${error.message}`,
            'error'
        );

        throw error;
    }
}


// ====================================
// CHECK STAKE STATUS (Info)
// ====================================

/**
 * Verifica el estado de staking de un NFT on-chain.
 * Útil para debugging o mostrar status en UI.
 *
 * @param {string} tokenId - ID del NFT
 * @returns {Promise<object>} Status de staking
 */
async function checkStakeStatus(tokenId) {
    try {
        const response = await fetch(`/api/nft/${tokenId}/stake-status`);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to check stake status');
        }

        console.log(`📊 Stake status for #${tokenId}:`, data);
        return data;

    } catch (error) {
        console.error("❌ Check stake status failed:", error);
        throw error;
    }
}


// ====================================
// UI HELPER: Show Notification
// ====================================

/**
 * Muestra notificación al usuario.
 *
 * @param {string} message - Mensaje a mostrar
 * @param {string} type - Tipo: 'success', 'error', 'info'
 */
function showNotification(message, type = 'info') {
    // Implementación básica - puedes mejorarla
    if (type === 'success') {
        alert(`✅ ${message}`);
    } else if (type === 'error') {
        alert(`❌ ${message}`);
    } else {
        alert(`ℹ️ ${message}`);
    }

    // TODO: Reemplazar con tu sistema de notificaciones
    // (toast, modal, etc.)
}


// ====================================
// EXAMPLE: Add Click Handlers
// ====================================

/**
 * Ejemplo de cómo conectar los botones en tu UI.
 * Agregar esto en tu código de inicialización.
 */
function setupMissionButtons() {
    // Botón "Start Mission"
    document.querySelectorAll('.start-mission-btn').forEach(button => {
        button.addEventListener('click', async (e) => {
            e.preventDefault();

            const tokenId = button.dataset.tokenId;
            const missionId = button.dataset.missionId;
            const wallet = currentWallet; // Tu variable global de wallet

            try {
                button.disabled = true;
                button.textContent = 'Starting...';

                await startMissionGasless(tokenId, missionId, wallet);

            } catch (error) {
                console.error(error);
            } finally {
                button.disabled = false;
                button.textContent = 'Start Mission';
            }
        });
    });

    // Botón "Claim Rewards"
    document.querySelectorAll('.claim-rewards-btn').forEach(button => {
        button.addEventListener('click', async (e) => {
            e.preventDefault();

            const tokenId = button.dataset.tokenId;
            const wallet = currentWallet;

            try {
                button.disabled = true;
                button.textContent = 'Claiming...';

                await completeMissionGasless(tokenId, wallet);

            } catch (error) {
                console.error(error);
            } finally {
                button.disabled = false;
                button.textContent = 'Claim Rewards';
            }
        });
    });
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    setupMissionButtons();
    console.log('✅ Gasless staking initialized');
});


// ====================================
// EXPORT (si usas modules)
// ====================================

if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        signMessage,
        startMissionGasless,
        completeMissionGasless,
        checkStakeStatus
    };
}
