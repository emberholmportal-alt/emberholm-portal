/**
 * EMBERHOLM PORTAL - 3D Globe
 * Interactive Three.js globe showing player locations worldwide
 */

// =========================================================================
// GLOBE STATE
// =========================================================================

let globeState = {
    scene: null,
    camera: null,
    renderer: null,
    globe: null,
    markers: [],
    raycaster: null,
    mouse: null,
    isRotating: true,
    isDragging: false,
    previousMousePosition: { x: 0, y: 0 },
    countryData: [],
    animationId: null,
    container: null
};

// Globe configuration
const GLOBE_CONFIG = {
    radius: 2,
    segments: 64,
    backgroundColor: 0x0a0f0a,
    globeColor: 0x020502,
    gridColor: 0xf59e0b,
    activeCountryColor: 0xffaa00,
    markerColor: 0xffaa00,
    glowColor: 0xf59e0b,
    rotationSpeed: 0.001,
    cameraDistance: 5
};

// =========================================================================
// INITIALIZATION
// =========================================================================

/**
 * Initialize the 3D globe
 */
function initGlobe(countryData = []) {
    const container = document.getElementById('globe-container');
    if (!container) {
        console.warn('[Globe] Container not found');
        return;
    }

    // Check if Three.js is loaded
    if (typeof THREE === 'undefined') {
        console.warn('[Globe] Three.js not loaded');
        showGlobeFallback(container);
        return;
    }

    globeState.container = container;
    globeState.countryData = countryData;

    // Clear any existing content
    container.innerHTML = '';

    try {
        setupScene(container);
        createGlobe();
        createGrid();
        createMarkers(countryData);
        createGlow();
        setupControls(container);
        animate();
        console.log('[Globe] Initialized successfully');
    } catch (error) {
        console.error('[Globe] Initialization failed:', error);
        showGlobeFallback(container);
    }
}

/**
 * Setup Three.js scene
 */
function setupScene(container) {
    const width = container.clientWidth;
    const height = container.clientHeight || 400;

    // Scene
    globeState.scene = new THREE.Scene();
    globeState.scene.background = new THREE.Color(GLOBE_CONFIG.backgroundColor);

    // Camera
    globeState.camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
    globeState.camera.position.z = GLOBE_CONFIG.cameraDistance;

    // Renderer
    globeState.renderer = new THREE.WebGLRenderer({
        antialias: true,
        alpha: true
    });
    globeState.renderer.setSize(width, height);
    globeState.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(globeState.renderer.domElement);

    // Raycaster for interaction
    globeState.raycaster = new THREE.Raycaster();
    globeState.mouse = new THREE.Vector2();

    // Lighting
    const ambientLight = new THREE.AmbientLight(0x404040, 0.5);
    globeState.scene.add(ambientLight);

    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(5, 3, 5);
    globeState.scene.add(directionalLight);

    // Handle resize
    window.addEventListener('resize', handleResize);
}

/**
 * Create the main globe sphere
 */
function createGlobe() {
    const geometry = new THREE.SphereGeometry(
        GLOBE_CONFIG.radius,
        GLOBE_CONFIG.segments,
        GLOBE_CONFIG.segments
    );

    const material = new THREE.MeshPhongMaterial({
        color: GLOBE_CONFIG.globeColor,
        transparent: true,
        opacity: 0.9,
        shininess: 5
    });

    globeState.globe = new THREE.Mesh(geometry, material);
    globeState.scene.add(globeState.globe);
}

/**
 * Create latitude/longitude grid lines
 */
function createGrid() {
    const lineMaterial = new THREE.LineBasicMaterial({
        color: GLOBE_CONFIG.gridColor,
        transparent: true,
        opacity: 0.15
    });

    // Latitude lines
    for (let lat = -60; lat <= 60; lat += 30) {
        const geometry = createLatitudeGeometry(lat, GLOBE_CONFIG.radius + 0.01);
        const line = new THREE.Line(geometry, lineMaterial);
        globeState.globe.add(line);
    }

    // Longitude lines
    for (let lon = 0; lon < 360; lon += 30) {
        const geometry = createLongitudeGeometry(lon, GLOBE_CONFIG.radius + 0.01);
        const line = new THREE.Line(geometry, lineMaterial);
        globeState.globe.add(line);
    }
}

/**
 * Create latitude circle geometry
 */
function createLatitudeGeometry(lat, radius) {
    const points = [];
    const phi = (90 - lat) * (Math.PI / 180);
    const r = radius * Math.sin(phi);
    const y = radius * Math.cos(phi);

    for (let i = 0; i <= 64; i++) {
        const theta = (i / 64) * Math.PI * 2;
        points.push(new THREE.Vector3(
            r * Math.cos(theta),
            y,
            r * Math.sin(theta)
        ));
    }

    return new THREE.BufferGeometry().setFromPoints(points);
}

/**
 * Create longitude arc geometry
 */
function createLongitudeGeometry(lon, radius) {
    const points = [];
    const theta = (lon + 180) * (Math.PI / 180);

    for (let i = 0; i <= 64; i++) {
        const phi = (i / 64) * Math.PI;
        points.push(new THREE.Vector3(
            -radius * Math.sin(phi) * Math.cos(theta),
            radius * Math.cos(phi),
            radius * Math.sin(phi) * Math.sin(theta)
        ));
    }

    return new THREE.BufferGeometry().setFromPoints(points);
}

/**
 * Create markers for countries with users
 */
function createMarkers(countryData) {
    // Clear existing markers
    globeState.markers.forEach(marker => {
        globeState.globe.remove(marker);
    });
    globeState.markers = [];

    if (!countryData || countryData.length === 0) return;

    countryData.forEach(country => {
        const countryInfo = getCountryByCode(country.country_code);
        if (!countryInfo) return;

        const position = latLonToVector3(
            countryInfo.lat,
            countryInfo.lon,
            GLOBE_CONFIG.radius + 0.02
        );

        // Size based on user count
        const size = Math.min(0.08 + (country.user_count * 0.01), 0.2);

        // Create marker
        const geometry = new THREE.SphereGeometry(size, 16, 16);
        const material = new THREE.MeshBasicMaterial({
            color: GLOBE_CONFIG.activeCountryColor,
            transparent: true,
            opacity: 0.8
        });

        const marker = new THREE.Mesh(geometry, material);
        marker.position.set(position.x, position.y, position.z);
        marker.userData = {
            countryCode: country.country_code,
            countryName: countryInfo.name,
            userCount: country.user_count,
            onlineCount: country.online_count
        };

        globeState.globe.add(marker);
        globeState.markers.push(marker);

        // Add pulsing animation ring
        if (country.online_count > 0) {
            const ringGeometry = new THREE.RingGeometry(size * 1.2, size * 1.5, 32);
            const ringMaterial = new THREE.MeshBasicMaterial({
                color: GLOBE_CONFIG.activeCountryColor,
                transparent: true,
                opacity: 0.5,
                side: THREE.DoubleSide
            });
            const ring = new THREE.Mesh(ringGeometry, ringMaterial);
            ring.position.set(position.x, position.y, position.z);
            ring.lookAt(0, 0, 0);
            ring.userData.isPulse = true;
            globeState.globe.add(ring);
            globeState.markers.push(ring);
        }
    });
}

/**
 * Create glow effect around globe
 */
function createGlow() {
    const glowGeometry = new THREE.SphereGeometry(
        GLOBE_CONFIG.radius * 1.02,
        32,
        32
    );

    const glowMaterial = new THREE.ShaderMaterial({
        uniforms: {
            c: { type: 'f', value: 0.1 },
            p: { type: 'f', value: 4.0 },
            glowColor: { type: 'c', value: new THREE.Color(GLOBE_CONFIG.glowColor) }
        },
        vertexShader: `
            varying vec3 vNormal;
            void main() {
                vNormal = normalize(normalMatrix * normal);
                gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
            }
        `,
        fragmentShader: `
            uniform vec3 glowColor;
            uniform float c;
            uniform float p;
            varying vec3 vNormal;
            void main() {
                float intensity = pow(c - dot(vNormal, vec3(0.0, 0.0, 1.0)), p);
                gl_FragColor = vec4(glowColor, intensity * 0.3);
            }
        `,
        side: THREE.BackSide,
        blending: THREE.AdditiveBlending,
        transparent: true
    });

    const glow = new THREE.Mesh(glowGeometry, glowMaterial);
    globeState.scene.add(glow);
}

// =========================================================================
// CONTROLS
// =========================================================================

/**
 * Setup mouse/touch controls
 */
function setupControls(container) {
    const canvas = globeState.renderer.domElement;

    // Mouse events
    canvas.addEventListener('mousedown', onMouseDown);
    canvas.addEventListener('mousemove', onMouseMove);
    canvas.addEventListener('mouseup', onMouseUp);
    canvas.addEventListener('mouseleave', onMouseUp);
    canvas.addEventListener('click', onMouseClick);

    // Touch events
    canvas.addEventListener('touchstart', onTouchStart, { passive: false });
    canvas.addEventListener('touchmove', onTouchMove, { passive: false });
    canvas.addEventListener('touchend', onTouchEnd);

    // Wheel for zoom
    canvas.addEventListener('wheel', onWheel, { passive: false });
}

function onMouseDown(e) {
    globeState.isDragging = true;
    globeState.isRotating = false;
    globeState.previousMousePosition = { x: e.clientX, y: e.clientY };
}

function onMouseMove(e) {
    if (!globeState.isDragging) return;

    const deltaX = e.clientX - globeState.previousMousePosition.x;
    const deltaY = e.clientY - globeState.previousMousePosition.y;

    globeState.globe.rotation.y += deltaX * 0.005;
    globeState.globe.rotation.x += deltaY * 0.005;

    // Clamp X rotation
    globeState.globe.rotation.x = Math.max(-Math.PI / 2, Math.min(Math.PI / 2, globeState.globe.rotation.x));

    globeState.previousMousePosition = { x: e.clientX, y: e.clientY };
}

function onMouseUp() {
    globeState.isDragging = false;
    // Resume rotation after 3 seconds
    setTimeout(() => {
        if (!globeState.isDragging) {
            globeState.isRotating = true;
        }
    }, 3000);
}

function onMouseClick(e) {
    // Check for marker clicks
    const rect = globeState.renderer.domElement.getBoundingClientRect();
    globeState.mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
    globeState.mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

    globeState.raycaster.setFromCamera(globeState.mouse, globeState.camera);
    const intersects = globeState.raycaster.intersectObjects(globeState.markers);

    if (intersects.length > 0) {
        const marker = intersects[0].object;
        if (marker.userData.countryCode) {
            showCountryTooltip(marker.userData);
        }
    }
}

function onTouchStart(e) {
    e.preventDefault();
    if (e.touches.length === 1) {
        globeState.isDragging = true;
        globeState.isRotating = false;
        globeState.previousMousePosition = {
            x: e.touches[0].clientX,
            y: e.touches[0].clientY
        };
    }
}

function onTouchMove(e) {
    e.preventDefault();
    if (!globeState.isDragging || e.touches.length !== 1) return;

    const deltaX = e.touches[0].clientX - globeState.previousMousePosition.x;
    const deltaY = e.touches[0].clientY - globeState.previousMousePosition.y;

    globeState.globe.rotation.y += deltaX * 0.005;
    globeState.globe.rotation.x += deltaY * 0.005;
    globeState.globe.rotation.x = Math.max(-Math.PI / 2, Math.min(Math.PI / 2, globeState.globe.rotation.x));

    globeState.previousMousePosition = {
        x: e.touches[0].clientX,
        y: e.touches[0].clientY
    };
}

function onTouchEnd() {
    globeState.isDragging = false;
    setTimeout(() => {
        if (!globeState.isDragging) {
            globeState.isRotating = true;
        }
    }, 3000);
}

function onWheel(e) {
    e.preventDefault();
    const delta = e.deltaY * 0.001;
    globeState.camera.position.z = Math.max(3, Math.min(10, globeState.camera.position.z + delta));
}

// =========================================================================
// ANIMATION
// =========================================================================

/**
 * Animation loop
 */
function animate() {
    globeState.animationId = requestAnimationFrame(animate);

    // Auto-rotate
    if (globeState.isRotating && globeState.globe) {
        globeState.globe.rotation.y += GLOBE_CONFIG.rotationSpeed;
    }

    // Pulse animation for active markers
    const time = Date.now() * 0.001;
    globeState.markers.forEach(marker => {
        if (marker.userData && marker.userData.isPulse) {
            marker.material.opacity = 0.3 + Math.sin(time * 2) * 0.2;
            marker.scale.setScalar(1 + Math.sin(time * 2) * 0.1);
        }
    });

    if (globeState.renderer && globeState.scene && globeState.camera) {
        globeState.renderer.render(globeState.scene, globeState.camera);
    }
}

/**
 * Handle window resize
 */
function handleResize() {
    if (!globeState.container || !globeState.camera || !globeState.renderer) return;

    const width = globeState.container.clientWidth;
    const height = globeState.container.clientHeight || 400;

    globeState.camera.aspect = width / height;
    globeState.camera.updateProjectionMatrix();
    globeState.renderer.setSize(width, height);
}

// =========================================================================
// UI HELPERS
// =========================================================================

/**
 * Show tooltip for country
 */
function showCountryTooltip(data) {
    const country = getCountryByCode(data.countryCode);
    if (!country) return;

    const message = `${country.flag} ${country.name}\n\nOperators: ${data.userCount}\nOnline: ${data.onlineCount}`;
    showInfoModal('COUNTRY INFO', message);
}

/**
 * Show fallback when Three.js not available
 */
function showGlobeFallback(container) {
    container.innerHTML = `
        <div class="globe-fallback">
            <div class="globe-emoji">🌍</div>
            <p>Interactive globe requires WebGL</p>
            <p class="dim">View country stats below</p>
        </div>
    `;
}

/**
 * Update globe markers with new data
 */
function updateGlobeMarkers(countryData) {
    if (!globeState.globe) return;
    createMarkers(countryData);
}

/**
 * Cleanup globe resources
 */
function destroyGlobe() {
    if (globeState.animationId) {
        cancelAnimationFrame(globeState.animationId);
    }

    window.removeEventListener('resize', handleResize);

    if (globeState.renderer) {
        globeState.renderer.dispose();
    }

    if (globeState.container) {
        globeState.container.innerHTML = '';
    }

    globeState = {
        scene: null,
        camera: null,
        renderer: null,
        globe: null,
        markers: [],
        raycaster: null,
        mouse: null,
        isRotating: true,
        isDragging: false,
        previousMousePosition: { x: 0, y: 0 },
        countryData: [],
        animationId: null,
        container: null
    };
}

// =========================================================================
// EXPORTS
// =========================================================================

window.initGlobe = initGlobe;
window.updateGlobeMarkers = updateGlobeMarkers;
window.destroyGlobe = destroyGlobe;
