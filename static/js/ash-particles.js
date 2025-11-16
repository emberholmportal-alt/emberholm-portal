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
            ash.style.left = Math.random() * 100 + '%';
            ash.style.animationDuration = (Math.random() * 10 + 10) + 's';
            ash.style.animationDelay = Math.random() * 5 + 's';
            document.body.appendChild(ash);
            particles.push(ash);
        }

        console.log('[Emberholm] Ash particles: ENABLED (' + particles.length + ' created)');
    }

    window.toggleAshParticles = function() {
        particlesEnabled = !particlesEnabled;
        createParticles();
        return particlesEnabled;
    };

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

        createParticles();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
