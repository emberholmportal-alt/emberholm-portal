'use client';

import { useRef, useMemo, useState, useCallback, useEffect } from 'react';
import { Canvas, useFrame, useThree, ThreeEvent } from '@react-three/fiber';
import * as THREE from 'three';
import {
  COUNTRY_COORDS,
  latLngToVector3,
  getCountryName,
} from '@/lib/hooks/useGlobe';
import { CountryStats } from '@/lib/api';

/**
 * Globe3D Component - Three.js globe for Emberholm
 * Based on prototype v8 exact specifications
 *
 * COLORS:
 * - Base sphere: 0x0a0502 (almost black with brown tint)
 * - Grid lines: 0x1a0f05, opacity 0.5
 * - Country borders WITH holders: 0xff9500, opacity 0.7
 * - Country borders WITHOUT holders: 0x2a1a0a, opacity 0.4
 * - Markers: 0xff9500 (amber)
 * - Marker centers: 0xffffff (white)
 */

interface Globe3DProps {
  countries: CountryStats[];
  onCountryClick: (countryCode: string) => void;
  onCountryHover?: (countryCode: string | null, userCount: number) => void;
}

const RADIUS = 1;
const GRID_COLOR = 0x1a0f05;
const AMBER = 0xff9500;
const WHITE = 0xffffff;

// Convert lat/lon to 3D position (exact formula from spec)
function latLonToVector3(lat: number, lon: number, radius: number = 1): THREE.Vector3 {
  const phi = (90 - lat) * (Math.PI / 180);
  const theta = (lon + 180) * (Math.PI / 180);
  return new THREE.Vector3(
    -radius * Math.sin(phi) * Math.cos(theta),
    radius * Math.cos(phi),
    radius * Math.sin(phi) * Math.sin(theta)
  );
}

// Globe wireframe with grid lines
function GlobeWireframe() {
  const gridRef = useRef<THREE.Group>(null);

  // Create latitude and longitude lines
  const gridLines = useMemo(() => {
    const lines: { points: THREE.Vector3[]; isLatitude: boolean }[] = [];

    // Latitude lines every 30 degrees (-60 to 60)
    for (let lat = -60; lat <= 60; lat += 30) {
      const points: THREE.Vector3[] = [];
      for (let lon = 0; lon <= 360; lon += 5) {
        points.push(latLonToVector3(lat, lon - 180, RADIUS));
      }
      lines.push({ points, isLatitude: true });
    }

    // Longitude lines every 30 degrees
    for (let lon = 0; lon < 360; lon += 30) {
      const points: THREE.Vector3[] = [];
      for (let lat = -90; lat <= 90; lat += 5) {
        points.push(latLonToVector3(lat, lon - 180, RADIUS));
      }
      lines.push({ points, isLatitude: false });
    }

    return lines;
  }, []);

  return (
    <group ref={gridRef}>
      {/* Base solid sphere - dark background */}
      <mesh>
        <sphereGeometry args={[RADIUS * 0.995, 64, 64]} />
        <meshBasicMaterial color={0x0a0502} />
      </mesh>

      {/* Grid lines */}
      {gridLines.map((line, i) => {
        const geometry = new THREE.BufferGeometry().setFromPoints(line.points);
        return (
          <line key={`grid-${i}`} geometry={geometry}>
            <lineBasicMaterial
              color={GRID_COLOR}
              transparent
              opacity={0.5}
            />
          </line>
        );
      })}

      {/* Equator highlight */}
      {(() => {
        const equatorPoints: THREE.Vector3[] = [];
        for (let lon = 0; lon <= 360; lon += 5) {
          equatorPoints.push(latLonToVector3(0, lon - 180, RADIUS * 1.001));
        }
        const geometry = new THREE.BufferGeometry().setFromPoints(equatorPoints);
        return (
          <line geometry={geometry}>
            <lineBasicMaterial color={AMBER} transparent opacity={0.3} />
          </line>
        );
      })()}
    </group>
  );
}

// Atmosphere glow effect
function Atmosphere() {
  const meshRef = useRef<THREE.Mesh>(null);

  // Custom shader for subtle orange glow
  const atmosphereMaterial = useMemo(() => {
    return new THREE.ShaderMaterial({
      vertexShader: `
        varying vec3 vNormal;
        void main() {
          vNormal = normalize(normalMatrix * normal);
          gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
      `,
      fragmentShader: `
        varying vec3 vNormal;
        void main() {
          float intensity = pow(0.7 - dot(vNormal, vec3(0.0, 0.0, 1.0)), 2.0);
          gl_FragColor = vec4(1.0, 0.58, 0.0, 1.0) * intensity * 0.3;
        }
      `,
      blending: THREE.AdditiveBlending,
      side: THREE.BackSide,
      transparent: true,
    });
  }, []);

  return (
    <mesh ref={meshRef} material={atmosphereMaterial}>
      <sphereGeometry args={[RADIUS * 1.15, 64, 64]} />
    </mesh>
  );
}

// Pulsing country markers
interface MarkersProps {
  countries: CountryStats[];
  onCountryClick: (code: string) => void;
  onCountryHover: (code: string | null, count: number) => void;
}

function CountryMarkers({ countries, onCountryClick, onCountryHover }: MarkersProps) {
  const groupRef = useRef<THREE.Group>(null);
  const timeRef = useRef(0);
  const markersRef = useRef<Map<string, { ring: THREE.Mesh; dot: THREE.Mesh; center: THREE.Mesh }>>(new Map());

  // Filter countries with users
  const activeCountries = useMemo(() => {
    return countries.filter(
      c => c.user_count > 0 && COUNTRY_COORDS[c.country_code.toUpperCase()]
    );
  }, [countries]);

  // Animation loop
  useFrame(() => {
    timeRef.current += 0.02;
    const time = timeRef.current;

    markersRef.current.forEach((marker, code) => {
      const index = activeCountries.findIndex(c => c.country_code === code);
      const pulse = Math.sin(time * 2.5 + index * 0.8) * 0.5 + 0.5;

      // Ring scaling animation
      if (marker.ring) {
        const scale = 1 + pulse * 0.5;
        marker.ring.scale.setScalar(scale);
        (marker.ring.material as THREE.MeshBasicMaterial).opacity = 0.3;
      }

      // Dot opacity animation
      if (marker.dot) {
        (marker.dot.material as THREE.MeshBasicMaterial).opacity = 0.75 + pulse * 0.25;
      }

      // Center opacity animation
      if (marker.center) {
        (marker.center.material as THREE.MeshBasicMaterial).opacity = 0.6 + pulse * 0.4;
      }
    });
  });

  return (
    <group ref={groupRef}>
      {activeCountries.map((country, index) => {
        const coords = COUNTRY_COORDS[country.country_code.toUpperCase()];
        if (!coords) return null;

        const position = latLonToVector3(coords.lat, coords.lng, RADIUS * 1.01);

        // Base size calculation: 0.02 + min(online/40, 0.035)
        const online = country.online_count || 0;
        const baseSize = 0.02 + Math.min(online / 40, 0.035);

        // Look at center for proper orientation
        const lookAtMatrix = new THREE.Matrix4();
        lookAtMatrix.lookAt(position, new THREE.Vector3(0, 0, 0), new THREE.Vector3(0, 1, 0));
        const quaternion = new THREE.Quaternion().setFromRotationMatrix(lookAtMatrix);

        return (
          <group
            key={country.country_code}
            position={position}
            quaternion={quaternion}
            onClick={(e: ThreeEvent<MouseEvent>) => {
              e.stopPropagation();
              onCountryClick(country.country_code);
            }}
            onPointerEnter={() => onCountryHover(country.country_code, country.user_count)}
            onPointerLeave={() => onCountryHover(null, 0)}
          >
            {/* 1. RING exterior */}
            <mesh
              ref={(el) => {
                if (el) {
                  const existing = markersRef.current.get(country.country_code) || {} as any;
                  existing.ring = el;
                  markersRef.current.set(country.country_code, existing);
                }
              }}
            >
              <ringGeometry args={[baseSize * 1.8, baseSize * 2.5, 24]} />
              <meshBasicMaterial
                color={AMBER}
                transparent
                opacity={0.3}
                side={THREE.DoubleSide}
              />
            </mesh>

            {/* 2. DOT central */}
            <mesh
              ref={(el) => {
                if (el) {
                  const existing = markersRef.current.get(country.country_code) || {} as any;
                  existing.dot = el;
                  markersRef.current.set(country.country_code, existing);
                }
              }}
            >
              <circleGeometry args={[baseSize, 24]} />
              <meshBasicMaterial
                color={AMBER}
                transparent
                opacity={0.95}
                side={THREE.DoubleSide}
              />
            </mesh>

            {/* 3. CENTRO blanco */}
            <mesh
              position={[0, 0, 0.001]}
              ref={(el) => {
                if (el) {
                  const existing = markersRef.current.get(country.country_code) || {} as any;
                  existing.center = el;
                  markersRef.current.set(country.country_code, existing);
                }
              }}
            >
              <circleGeometry args={[baseSize * 0.35, 16]} />
              <meshBasicMaterial
                color={WHITE}
                transparent
                opacity={0.9}
                side={THREE.DoubleSide}
              />
            </mesh>
          </group>
        );
      })}
    </group>
  );
}

// Main scene with auto-rotation and drag controls
interface SceneProps extends MarkersProps {
  isDragging: boolean;
  setIsDragging: (dragging: boolean) => void;
}

function GlobeScene({ countries, onCountryClick, onCountryHover, isDragging, setIsDragging }: SceneProps) {
  const globeRef = useRef<THREE.Group>(null);
  const { gl, camera } = useThree();

  // Drag state
  const dragState = useRef({
    isDragging: false,
    previousMousePosition: { x: 0, y: 0 },
    rotationVelocity: { x: 0, y: 0 },
  });

  // Auto-rotation when not dragging
  useFrame(() => {
    if (globeRef.current && !dragState.current.isDragging) {
      globeRef.current.rotation.y += 0.0012;
    }
  });

  // Mouse/touch handlers for drag rotation
  useEffect(() => {
    const canvas = gl.domElement;

    const handleStart = (clientX: number, clientY: number) => {
      dragState.current.isDragging = true;
      dragState.current.previousMousePosition = { x: clientX, y: clientY };
      setIsDragging(true);
    };

    const handleMove = (clientX: number, clientY: number) => {
      if (!dragState.current.isDragging || !globeRef.current) return;

      const deltaX = clientX - dragState.current.previousMousePosition.x;
      const deltaY = clientY - dragState.current.previousMousePosition.y;

      globeRef.current.rotation.y += deltaX * 0.005;
      globeRef.current.rotation.x += deltaY * 0.005;

      // Clamp vertical rotation
      globeRef.current.rotation.x = Math.max(
        -Math.PI / 3,
        Math.min(Math.PI / 3, globeRef.current.rotation.x)
      );

      dragState.current.previousMousePosition = { x: clientX, y: clientY };
    };

    const handleEnd = () => {
      dragState.current.isDragging = false;
      setIsDragging(false);
    };

    // Mouse events
    const onMouseDown = (e: MouseEvent) => handleStart(e.clientX, e.clientY);
    const onMouseMove = (e: MouseEvent) => handleMove(e.clientX, e.clientY);
    const onMouseUp = () => handleEnd();

    // Touch events
    const onTouchStart = (e: TouchEvent) => {
      if (e.touches.length === 1) {
        handleStart(e.touches[0].clientX, e.touches[0].clientY);
      }
    };
    const onTouchMove = (e: TouchEvent) => {
      if (e.touches.length === 1) {
        handleMove(e.touches[0].clientX, e.touches[0].clientY);
      }
    };
    const onTouchEnd = () => handleEnd();

    canvas.addEventListener('mousedown', onMouseDown);
    canvas.addEventListener('mousemove', onMouseMove);
    canvas.addEventListener('mouseup', onMouseUp);
    canvas.addEventListener('mouseleave', onMouseUp);
    canvas.addEventListener('touchstart', onTouchStart);
    canvas.addEventListener('touchmove', onTouchMove);
    canvas.addEventListener('touchend', onTouchEnd);

    return () => {
      canvas.removeEventListener('mousedown', onMouseDown);
      canvas.removeEventListener('mousemove', onMouseMove);
      canvas.removeEventListener('mouseup', onMouseUp);
      canvas.removeEventListener('mouseleave', onMouseUp);
      canvas.removeEventListener('touchstart', onTouchStart);
      canvas.removeEventListener('touchmove', onTouchMove);
      canvas.removeEventListener('touchend', onTouchEnd);
    };
  }, [gl, setIsDragging]);

  return (
    <>
      {/* Ambient light */}
      <ambientLight intensity={0.6} />

      {/* Directional light for depth */}
      <directionalLight position={[5, 3, 5]} intensity={0.3} />

      {/* Globe group */}
      <group ref={globeRef}>
        <GlobeWireframe />
        <Atmosphere />
        <CountryMarkers
          countries={countries}
          onCountryClick={onCountryClick}
          onCountryHover={onCountryHover}
        />
      </group>
    </>
  );
}

// Main Globe3D export
export function Globe3D({ countries, onCountryClick, onCountryHover }: Globe3DProps) {
  const [hoveredCountry, setHoveredCountry] = useState<{
    code: string;
    count: number;
  } | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleHover = useCallback((code: string | null, count: number) => {
    if (code) {
      setHoveredCountry({ code, count });
    } else {
      setHoveredCountry(null);
    }
    onCountryHover?.(code, count);
  }, [onCountryHover]);

  return (
    <div
      className="relative w-full h-full"
      style={{
        background: 'radial-gradient(ellipse at center, #1a0f05 0%, #0a0705 70%)',
      }}
    >
      {/* Legend - top right */}
      <div
        className="absolute top-2 right-2 z-10"
        style={{ fontSize: '10px' }}
      >
        <div className="flex items-center gap-1 justify-end">
          <span className="text-amber-dim">Holders</span>
          <div
            className="w-2 h-2 rounded-full"
            style={{
              background: '#ff9500',
              boxShadow: '0 0 6px #ff9500',
            }}
          />
        </div>
        <div className="flex items-center gap-1 justify-end mt-1">
          <span className="text-amber-dim">Borders</span>
          <div
            className="w-2 h-2 rounded-full"
            style={{
              border: '1px solid #804d00',
              background: 'transparent',
            }}
          />
        </div>
      </div>

      {/* Three.js Canvas */}
      <Canvas
        camera={{ position: [0, 0, 2.8], fov: 50 }}
        gl={{ antialias: true, alpha: true }}
        style={{ background: 'transparent' }}
      >
        <GlobeScene
          countries={countries}
          onCountryClick={onCountryClick}
          onCountryHover={handleHover}
          isDragging={isDragging}
          setIsDragging={setIsDragging}
        />
      </Canvas>

      {/* Hover tooltip - bottom center */}
      {hoveredCountry && (
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 pointer-events-none z-10">
          <div className="data-box px-3 py-2 text-center text-sm">
            <span className="text-amber-bright">
              {getCountryName(hoveredCountry.code)}
            </span>
            <span className="text-amber-dim mx-1">·</span>
            <span className="text-cyan">
              {hoveredCountry.count} holder{hoveredCountry.count !== 1 ? 's' : ''}
            </span>
          </div>
        </div>
      )}

      {/* Instructions - only when not hovering */}
      {!hoveredCountry && (
        <div className="absolute bottom-2 left-1/2 -translate-x-1/2 pointer-events-none z-10">
          <span className="text-amber-dim text-xs">
            Drag to rotate · Tap marker for details
          </span>
        </div>
      )}
    </div>
  );
}

export default Globe3D;
