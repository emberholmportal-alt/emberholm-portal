/* ===============================================================
   ATMOSPHERIC PARTICLES SYSTEM - EMBERHOLM PORTAL
   Sistema de partículas de ceniza con toggle ON/OFF
   =============================================================== */

(function() {
    'use strict';

    let particlesEnabled = true;
    let particles = [];

    // Crear partículas
    function createParticles() {
        // Limpiar partículas existentes
        particles.forEach(p => p.remove());
        particles = [];

        if (!particlesEnabled) return;

        // Crear 30 partículas
        for (let i = 0; i < 30; i++) {
            const ash = document.createElement('div');
            ash.className = 'ash-particle';

            // Posición horizontal aleatoria
            ash.style.left = Math.random() * 100 + '%';

            // Duración aleatoria (10-20 segundos)
            ash.style.animationDuration = (Math.random() * 10 + 10) + 's';

            // Delay inicial aleatorio (0-5 segundos)
            ash.style.animationDelay = Math.random() * 5 + 's';

            document.body.appendChild(ash);
            particles.push(ash);
        }

        console.log('[Emberholm] Ash particles:', particlesEnabled ? 'ENABLED' : 'DISABLED');
    }

    // Función para toggle ON/OFF
    window.toggleAshParticles = function() {
        particlesEnabled = !particlesEnabled;
        createParticles();

        // Guardar preferencia en localStorage
        try {
            localStorage.setItem('emberholm_particles', particlesEnabled ? 'on' : 'off');
        } catch(e) {
            // Si localStorage no está disponible, ignorar
        }

        return particlesEnabled;
    };

    // Función para obtener estado
    window.getAshParticlesState = function() {
        return particlesEnabled;
    };

    // Inicialización
    function init() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', init);
            return;
        }

        // Cargar preferencia guardada
        try {
            const saved = localStorage.getItem('emberholm_particles');
            if (saved === 'off') {
                particlesEnabled = false;
            }
        } catch(e) {
            // Si localStorage no está disponible, usar valor por defecto
        }

        createParticles();
    }

    // Auto-inicializar
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
