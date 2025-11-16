(function() {
    'use strict';

    let particlesEnabled = true;

    // Toggle visibility of the pure HTML particles container (CSP compliant - no inline styles)
    function toggleParticles() {
        const container = document.querySelector('.ash-particles-container');
        if (!container) {
            console.log('[Emberholm] Ash particles container not found');
            return;
        }

        if (particlesEnabled) {
            container.classList.remove('hidden');
            console.log('[Emberholm] Ash particles: ENABLED');
        } else {
            container.classList.add('hidden');
            console.log('[Emberholm] Ash particles: DISABLED');
        }
    }

    // Agregar event listener al botón toggle (CSP compliant)
    function initButton() {
        const btn = document.getElementById('particles-toggle');
        if (btn) {
            btn.addEventListener('click', function() {
                particlesEnabled = !particlesEnabled;
                try {
                    localStorage.setItem('emberholm_particles', particlesEnabled ? 'on' : 'off');
                } catch(e) {}
                toggleParticles();
                btn.textContent = particlesEnabled ? '🔥 ASH' : '❄️ ASH';
            });
        }
    }

    function init() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', init);
            return;
        }

        try {
            const saved = localStorage.getItem('emberholm_particles');
            if (saved === 'off') {
                particlesEnabled = false;
            }
        } catch(e) {}

        initButton();
        toggleParticles();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
