/* ===============================================================
   ATMOSPHERIC PARTICLES SYSTEM - GLOBAL
   Emberholm Portal - Ash Particles Effect
   Gothic Medieval Aesthetic
   ===============================================================

   DESCRIPCIÓN:
   Sistema de partículas de ceniza que caen constantemente en todas
   las páginas del portal, creando una atmósfera gótico-medieval.

   CARACTERÍSTICAS:
   - Optimizado con DocumentFragment (1 reflow vs 40)
   - Responsive (adapta cantidad en móviles)
   - Encapsulado con IIFE (no contamina scope global)
   - Maneja resize con throttling
   - Limpia partículas previas (hot-reload friendly)
   - Paleta de colores gótico-medieval

   =============================================================== */

(function() {
    'use strict';

    // =========================================
    // CONFIGURACIÓN
    // =========================================
    const CONFIG = {
        // Cantidad de partículas
        particleCount: 40,              // Desktop/tablet
        mobileParticleCount: 20,        // Móviles (< 768px)

        // Velocidad de caída (segundos)
        minDuration: 10,                // Más lento (atmosférico)
        maxDuration: 18,                // Más rápido

        // Delays iniciales (segundos)
        maxDelay: 8,                    // Delay máximo para inicio escalonado

        // Probabilidades de tamaños
        largeParticleChance: 0.30,      // 30% de partículas grandes
        smallParticleChance: 0.30,      // 30% de partículas pequeñas

        // Paleta de colores gótico-medieval
        colors: {
            normal: 'rgba(201, 184, 150, 0.2)',      // Dorado suave
            large: 'rgba(138, 112, 80, 0.25)',       // Marrón oscuro
            small: 'rgba(201, 184, 150, 0.12)',      // Dorado muy sutil
            shadow: 'rgba(201, 184, 150, 0.25)'      // Sombra dorada
        },

        // Responsive
        resizeThreshold: 100,           // Píxeles de cambio para re-init
        resizeDebounce: 250             // Milisegundos de espera después de resize
    };

    // =========================================
    // FUNCIÓN: CREAR UNA PARTÍCULA
    // =========================================
    function createAshParticle(index) {
        const ash = document.createElement('div');
        ash.className = 'ash-particle';

        // Determinar el tamaño de la partícula aleatoriamente
        const sizeRoll = Math.random();
        if (sizeRoll < CONFIG.smallParticleChance) {
            ash.classList.add('small');
        } else if (sizeRoll > (1 - CONFIG.largeParticleChance)) {
            ash.classList.add('large');
        }
        // Si no cumple ninguna condición, queda con tamaño normal (2px)

        // Posición horizontal aleatoria en toda la pantalla
        ash.style.left = Math.random() * 100 + '%';

        // Duración de animación aleatoria
        const duration = Math.random() *
            (CONFIG.maxDuration - CONFIG.minDuration) +
            CONFIG.minDuration;
        ash.style.animationDuration = duration + 's';

        // Delay inicial aleatorio para que no caigan todas a la vez
        ash.style.animationDelay = Math.random() * CONFIG.maxDelay + 's';

        return ash;
    }

    // =========================================
    // FUNCIÓN: INICIALIZAR PARTÍCULAS
    // =========================================
    function initializeAshParticles() {
        // Verificar que el DOM esté listo
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initializeAshParticles);
            return;
        }

        // Limpiar partículas previas si existen (útil para hot-reload)
        const existingParticles = document.querySelectorAll('.ash-particle');
        existingParticles.forEach(particle => particle.remove());

        // Determinar cantidad según dispositivo
        const isMobile = window.innerWidth < 768;
        const particleCount = isMobile ? CONFIG.mobileParticleCount : CONFIG.particleCount;

        // Crear y agregar nuevas partículas usando DocumentFragment (mejor performance)
        const fragment = document.createDocumentFragment();

        for (let i = 0; i < particleCount; i++) {
            const particle = createAshParticle(i);
            fragment.appendChild(particle);
        }

        document.body.appendChild(fragment);

        // Log de confirmación (útil para debugging)
        console.log(`[Emberholm Ash Particles] ${particleCount} particles initialized (${isMobile ? 'mobile' : 'desktop'} mode)`);
    }

    // =========================================
    // AUTO-INICIALIZACIÓN
    // =========================================

    // Inicializar cuando cargue el DOM
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeAshParticles);
    } else {
        // Si el DOM ya está listo, inicializar inmediatamente
        initializeAshParticles();
    }

    // =========================================
    // RESPONSIVE: RE-INICIALIZAR EN RESIZE
    // =========================================

    let resizeTimer;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function() {
            // Solo re-inicializar si el ancho cambió más de CONFIG.resizeThreshold px
            const currentWidth = window.innerWidth;
            const lastWidth = window.lastWidth || currentWidth;

            if (Math.abs(currentWidth - lastWidth) > CONFIG.resizeThreshold) {
                initializeAshParticles();
                window.lastWidth = currentWidth;
                console.log('[Emberholm Ash Particles] Re-initialized after resize');
            }
        }, CONFIG.resizeDebounce);
    });

    // =========================================
    // LOGGING PARA DEBUGGING
    // =========================================

    // Exportar CONFIG para debugging en consola (solo en desarrollo)
    if (typeof window !== 'undefined') {
        window.EmberholmAshConfig = CONFIG;
        console.log('[Emberholm Ash Particles] System loaded. Access config via: window.EmberholmAshConfig');
    }

})();
