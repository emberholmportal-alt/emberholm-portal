/* ===============================================================
   EMBERHOLM PORTAL - HACKNET UI INTERACTIONS
   =============================================================== */

(function() {
    'use strict';

    // ===============================================================
    // BOOT SEQUENCE EN CONSOLA
    // ===============================================================
    console.clear();
    console.log('%c╔══════════════════════════════════════════════════════╗', 'color: #4af; font-family: monospace;');
    console.log('%c║           EMBERHOLM PORTAL SYSTEM v2.1.4          ║', 'color: #4af; font-family: monospace;');
    console.log('%c║              Hacknet Clean Interface              ║', 'color: #4af; font-family: monospace;');
    console.log('%c╚══════════════════════════════════════════════════════╝', 'color: #4af; font-family: monospace;');
    console.log('');
    console.log('%c[✓] System initialized', 'color: #4f8; font-weight: bold;');
    console.log('%c[✓] CRT effects loaded', 'color: #4f8;');
    console.log('%c[✓] Audio system ready', 'color: #4f8;');
    console.log('%c[✓] Navigation active', 'color: #4f8;');
    console.log('%c[✓] REALM MONITOR online', 'color: #fc0; font-weight: bold;');
    console.log('');
    console.log('%c[!] CORE STABILITY: 12% - CRITICAL', 'color: #f24; font-weight: bold;');
    console.log('');
    console.log('%c> Type "help" for commands', 'color: #2a8;');

    // ===============================================================
    // NAVEGACIÓN ACTIVA
    // ===============================================================
    function initNavigation() {
        const navButtons = document.querySelectorAll('.cmd, .nav-button, .cmd-link, .menu-item');

        navButtons.forEach(button => {
            button.addEventListener('click', function() {
                // Skip logo items
                if (this.classList.contains('logo')) {
                    return;
                }

                // Remover active de todos los botones del mismo grupo
                const parent = this.parentElement;
                const siblings = parent.querySelectorAll('.cmd, .nav-button, .cmd-link, .menu-item');
                siblings.forEach(btn => btn.classList.remove('active', 'is-active'));

                // Agregar active al clickeado
                this.classList.add('active');

                // Log en consola
                const buttonText = this.textContent.trim();
                console.log(`%c> NAV: ${buttonText}`, 'color: #4af; font-family: monospace;');
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
                    if (node.classList && (node.classList.contains('feed-item') || node.classList.contains('log-entry'))) {
                        // Agregar clase 'new' temporalmente
                        node.classList.add('new');
                        setTimeout(() => node.classList.remove('new'), 1000);

                        // Log en consola
                        console.log('%c[+] New feed entry', 'color: #fc0; font-family: monospace;');
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
    // HOVER EFFECTS PARA PANELES
    // ===============================================================
    function initHoverEffects() {
        const panels = document.querySelectorAll('.terminal-block, .data-panel, .campaign-box');

        panels.forEach(panel => {
            panel.addEventListener('mouseenter', function() {
                this.style.transform = 'translateY(-2px)';
                this.style.transition = 'transform 0.2s';
            });

            panel.addEventListener('mouseleave', function() {
                this.style.transform = 'translateY(0)';
            });
        });
    }

    // ===============================================================
    // STATUS DOTS ANIMATION
    // ===============================================================
    function initStatusDots() {
        const dots = document.querySelectorAll('.status-dot, .status-segment::before');

        // Ya tienen animación CSS, pero podemos agregar interactividad
        setInterval(() => {
            const criticalDots = document.querySelectorAll('.status-dot.critical');
            criticalDots.forEach(dot => {
                dot.style.opacity = Math.random() > 0.3 ? '1' : '0.3';
            });
        }, 500);
    }

    // ===============================================================
    // SIMULACIÓN DE TYPING EFFECT (Opcional)
    // ===============================================================
    function typeWriter(element, text, speed = 30) {
        let i = 0;
        element.textContent = '';

        function type() {
            if (i < text.length) {
                element.textContent += text.charAt(i);
                i++;
                setTimeout(type, speed);
            }
        }

        type();
    }

    // ===============================================================
    // COMMAND INPUT (si existe)
    // ===============================================================
    function initCommandInput() {
        const commandInput = document.querySelector('.command-input');

        if (commandInput) {
            commandInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    const command = this.value.trim();
                    if (command) {
                        console.log(`%c> COMMAND: ${command}`, 'color: #fc0; font-family: monospace;');

                        // Simular respuesta
                        setTimeout(() => {
                            if (command.toLowerCase() === 'help') {
                                console.log('%cAvailable commands: status, missions, guilds, help', 'color: #4af;');
                            } else {
                                console.log(`%c[!] Unknown command: ${command}`, 'color: #f24;');
                            }
                        }, 100);

                        this.value = '';
                    }
                }
            });
        }
    }

    // ===============================================================
    // INICIALIZACIÓN
    // ===============================================================
    function init() {
        console.log('%c[HACKNET UI] Initializing interface...', 'color: #4af; font-family: monospace;');

        initNavigation();
        initVolumeBar();
        animateFeedEntries();
        initHoverEffects();
        initStatusDots();
        initCommandInput();

        console.log('%c[HACKNET UI] Interface ready', 'color: #4f8; font-weight: bold; font-family: monospace;');
    }

    // Esperar a que el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
