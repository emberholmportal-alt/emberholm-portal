/* ===============================================================
   ATMOSPHERIC PARTICLES SYSTEM - ASH FALLING EFFECT
   Emberholm Portal - Simple version with toggle control
   =============================================================== */

(function() {
    'use strict';

    // Estado del sistema - Por defecto ACTIVADO (true)
    // Solo se desactiva si el usuario explícitamente lo puso en 'false'
    let particlesEnabled = localStorage.getItem('ashParticlesEnabled') !== 'false';

    console.log('[Emberholm Ash] Initial state:', particlesEnabled ? 'ENABLED' : 'DISABLED');

    function createToggleButton() {
        // Verificar que no existe ya
        if (document.getElementById('ash-toggle-btn')) return;

        const button = document.createElement('button');
        button.id = 'ash-toggle-btn';
        button.className = 'ash-toggle-button';
        button.innerHTML = particlesEnabled ? '🔥 ASH: ON' : '❄️ ASH: OFF';
        button.title = 'Toggle ash particles';

        button.addEventListener('click', function() {
            particlesEnabled = !particlesEnabled;
            localStorage.setItem('ashParticlesEnabled', particlesEnabled);

            console.log('[Emberholm Ash] Toggle clicked, new state:', particlesEnabled ? 'ON' : 'OFF');

            if (particlesEnabled) {
                button.innerHTML = '🔥 ASH: ON';
                initializeAshParticles();
            } else {
                button.innerHTML = '❄️ ASH: OFF';
                removeAllParticles();
            }
        });

        document.body.appendChild(button);
        console.log('[Emberholm Ash] Toggle button created');
    }

    function removeAllParticles() {
        const existingParticles = document.querySelectorAll('.ash-particle');
        existingParticles.forEach(particle => particle.remove());
    }

    function initializeAshParticles() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initializeAshParticles);
            return;
        }

        // Limpiar partículas previas
        removeAllParticles();

        // Si está desactivado, no crear partículas
        if (!particlesEnabled) {
            console.log('[Emberholm Ash] Particles disabled by user');
            return;
        }

        console.log('[Emberholm Ash] Creating 30 particles...');

        // Crear 30 partículas
        for (let i = 0; i < 30; i++) {
            const ash = document.createElement('div');
            ash.className = 'ash-particle';
            ash.style.left = Math.random() * 100 + '%';
            ash.style.animationDuration = (Math.random() * 10 + 10) + 's';
            ash.style.animationDelay = Math.random() * 5 + 's';
            document.body.appendChild(ash);
        }

        console.log('[Emberholm Ash] ✓ 30 particles created and appended to body');

        // Verificar que se crearon
        const count = document.querySelectorAll('.ash-particle').length;
        console.log('[Emberholm Ash] Verification: Found', count, 'particles in DOM');
    }

    // Inicializar cuando cargue el DOM con delay de 3 segundos
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            createToggleButton();

            // Delay de 3 segundos antes de activar las partículas
            console.log('[Emberholm Ash] Waiting 3 seconds before auto-activation...');
            setTimeout(function() {
                console.log('[Emberholm Ash] 3 seconds elapsed, initializing particles...');
                initializeAshParticles();
            }, 3000);
        });
    } else {
        createToggleButton();

        // Delay de 3 segundos antes de activar las partículas
        console.log('[Emberholm Ash] Waiting 3 seconds before auto-activation...');
        setTimeout(function() {
            console.log('[Emberholm Ash] 3 seconds elapsed, initializing particles...');
            initializeAshParticles();
        }, 3000);
    }
})();
