/* ===============================================================
   EMBERHOLM PORTAL - TERMINAL EFFECTS & BOOT SEQUENCE
   =============================================================== */

(function() {
    'use strict';

    // ===============================================================
    // BOOT SEQUENCE EN CONSOLA
    // ===============================================================
    console.clear();
    console.log('%c█████████████████████████████████████████████████', 'color: #00ff41; font-family: monospace;');
    console.log('%c  EMBERHOLM PORTAL SYSTEM v2.1.4                 ', 'color: #00ff41; font-family: monospace;');
    console.log('%c  Booting Realm Monitor...                       ', 'color: #ffb000; font-family: monospace;');
    console.log('%c█████████████████████████████████████████████████', 'color: #00ff41; font-family: monospace;');
    console.log('%c> Loading guild protocols...          [OK]', 'color: #00aa2e; font-family: monospace;');
    console.log('%c> Initializing mission matrix...      [OK]', 'color: #00aa2e; font-family: monospace;');
    console.log('%c> Connecting to Ember Core...         [OK]', 'color: #00aa2e; font-family: monospace;');
    console.log('%c> ACCESS GRANTED: CITIZEN LEVEL            ', 'color: #ffb000; font-family: monospace; font-weight: bold;');
    console.log('%c> System Ready. May the Ember guide your path.  ', 'color: #ffd700; font-family: monospace;');

    // ===============================================================
    // NAVEGACIÓN ACTIVA
    // ===============================================================
    function initNavigation() {
        const navButtons = document.querySelectorAll('.cmd, .nav-button, .cmd-link');

        navButtons.forEach(button => {
            button.addEventListener('click', function() {
                // Remover active de todos
                navButtons.forEach(btn => btn.classList.remove('active', 'is-active'));

                // Agregar active al clickeado
                this.classList.add('active');

                // Log en consola
                const buttonText = this.textContent.trim();
                console.log('%c> COMMAND: ' + buttonText, 'color: #00ff41; font-family: monospace;');
            });
        });
    }

    // ===============================================================
    // VOLUME BAR VISUAL
    // ===============================================================
    function initVolumeBar() {
        const volumeSlider = document.getElementById('console-volume');
        const volumeDisplay = document.getElementById('volume-display');

        if (volumeSlider && volumeDisplay) {
            function updateVolumeBar() {
                const value = volumeSlider.value;
                const filled = Math.floor((value / 100) * 10);
                const empty = 10 - filled;

                const bar = 'VOL ' + '▓'.repeat(filled) + '░'.repeat(empty);
                volumeDisplay.textContent = bar;
            }

            volumeSlider.addEventListener('input', updateVolumeBar);
            updateVolumeBar(); // Initial update
        }
    }

    // ===============================================================
    // FEED ENTRIES ANIMATION
    // ===============================================================
    function animateFeedEntries() {
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                mutation.addedNodes.forEach(function(node) {
                    if (node.classList && node.classList.contains('feed-item')) {
                        node.classList.add('new');
                        setTimeout(() => node.classList.remove('new'), 500);
                    }
                });
            });
        });

        const feedContainer = document.getElementById('realm-feed-container');
        if (feedContainer) {
            observer.observe(feedContainer, {
                childList: true,
                subtree: true
            });
        }
    }

    // ===============================================================
    // INICIALIZACIÓN
    // ===============================================================
    function init() {
        console.log('%c[TERMINAL EFFECTS] Initializing...', 'color: #00ff41; font-family: monospace;');

        initNavigation();
        initVolumeBar();
        animateFeedEntries();

        console.log('%c[TERMINAL EFFECTS] Ready', 'color: #ffd700; font-family: monospace;');
    }

    // Esperar a que el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
