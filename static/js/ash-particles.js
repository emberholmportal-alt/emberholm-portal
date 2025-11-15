/* ===============================================================
   ATMOSPHERIC PARTICLES SYSTEM - ASH FALLING EFFECT
   Emberholm Portal - Simple version with toggle control
   =============================================================== */

(function() {
    'use strict';

    // Estado del sistema (activado/desactivado)
    let particlesEnabled = localStorage.getItem('ashParticlesEnabled') !== 'false';

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

            if (particlesEnabled) {
                button.innerHTML = '🔥 ASH: ON';
                initializeAshParticles();
            } else {
                button.innerHTML = '❄️ ASH: OFF';
                removeAllParticles();
            }
        });

        document.body.appendChild(button);
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

        // Crear 30 partículas
        for (let i = 0; i < 30; i++) {
            const ash = document.createElement('div');
            ash.className = 'ash-particle';
            ash.style.left = Math.random() * 100 + '%';
            ash.style.animationDuration = (Math.random() * 10 + 10) + 's';
            ash.style.animationDelay = Math.random() * 5 + 's';
            document.body.appendChild(ash);
        }

        console.log('[Emberholm Ash] 30 particles initialized');
    }

    // Inicializar cuando cargue el DOM
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            createToggleButton();
            initializeAshParticles();
        });
    } else {
        createToggleButton();
        initializeAshParticles();
    }
})();
