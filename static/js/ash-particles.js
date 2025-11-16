/* ===============================================================
   ATMOSPHERIC PARTICLES SYSTEM - EMBERHOLM PORTAL
   Sistema de partículas de ceniza con toggle ON/OFF
   CSP-COMPLIANT VERSION (sin onclick inline, sin eval)
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
            const duration = (Math.random() * 10 + 10);
            ash.style.animationDuration = duration + 's';

            // Delay inicial aleatorio (0-5 segundos)
            const delay = Math.random() * 5;
            ash.style.animationDelay = delay + 's';

            document.body.appendChild(ash);
            particles.push(ash);
        }

        console.log('[Emberholm] Ash particles:', particlesEnabled ? 'ENABLED' : 'DISABLED');
    }

    // Función para toggle ON/OFF
    function toggleAshParticles() {
        particlesEnabled = !particlesEnabled;
        createParticles();

        // Guardar preferencia en localStorage
        try {
            localStorage.setItem('emberholm_particles', particlesEnabled ? 'on' : 'off');
        } catch(e) {
            // Si localStorage no está disponible, ignorar
        }

        return particlesEnabled;
    }

    // Función para obtener estado
    function getAshParticlesState() {
        return particlesEnabled;
    }

    // Actualizar texto del botón
    function updateParticlesButton() {
        const btn = document.getElementById('particles-toggle');
        if (btn) {
            btn.textContent = particlesEnabled ? '🔥 ASH' : '❄️ ASH';
        }
    }

    // Inicialización del botón (CSP-compliant con addEventListener)
    function initButton() {
        const btn = document.getElementById('particles-toggle');
        if (btn) {
            // Agregar event listener (CSP-compliant)
            btn.addEventListener('click', function() {
                toggleAshParticles();
                updateParticlesButton();
            });

            // Actualizar estado inicial del botón
            updateParticlesButton();
        }
    }

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

        // Inicializar botón
        initButton();

        // Crear partículas
        createParticles();
    }

    // Auto-inicializar
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
