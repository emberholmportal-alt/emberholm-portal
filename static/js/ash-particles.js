(function() {
    'use strict';

    let particlesEnabled = true;
    let particles = [];

    function createParticles() {
        particles.forEach(p => p.remove());
        particles = [];

        if (!particlesEnabled) {
            console.log('[Emberholm] Ash particles: DISABLED');
            return;
        }

        for (let i = 0; i < 30; i++) {
            const ash = document.createElement('div');
            ash.className = 'ash-particle';

            // Usar setAttribute en lugar de .style para CSP compliance
            const leftPos = Math.floor(Math.random() * 100);
            ash.setAttribute('data-left', leftPos);

            document.body.appendChild(ash);
            particles.push(ash);
        }

        console.log('[Emberholm] Ash particles: ENABLED (' + particles.length + ' created)');
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
                createParticles();
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
        createParticles();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
