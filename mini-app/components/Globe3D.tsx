'use client';

import { useRef, useMemo, useState, useCallback } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { OrbitControls, Sphere, Line } from '@react-three/drei';
import * as THREE from 'three';
import {
  COUNTRY_COORDS,
  latLngToVector3,
  getCountryName,
} from '@/lib/hooks/useGlobe';
import { CountryStats } from '@/lib/api';

/**
 * Globe3D Component - Three.js wireframe globe for Emberholm
 * Digital system style with cyan/amber colors
 */

interface Globe3DProps {
  countries: CountryStats[];
  onCountryClick: (countryCode: string) => void;
  onCountryHover?: (countryCode: string | null, userCount: number) => void;
}

// Simplified continent outlines (key points)
const CONTINENT_OUTLINES: [number, number][][] = [
  // North America
  [[70, -170], [60, -140], [55, -130], [48, -125], [35, -120], [25, -110], [20, -105], [18, -95], [25, -80], [30, -82], [35, -75], [40, -74], [45, -70], [47, -65], [50, -55], [52, -58], [55, -60], [60, -65], [65, -70], [70, -80], [72, -100], [70, -140], [70, -170]],
  // South America
  [[12, -75], [10, -72], [5, -77], [-5, -80], [-15, -75], [-25, -70], [-35, -70], [-45, -75], [-55, -68], [-55, -65], [-50, -55], [-35, -55], [-25, -50], [-15, -40], [-5, -35], [0, -50], [5, -60], [10, -70], [12, -75]],
  // Europe
  [[36, -10], [38, -5], [43, -8], [48, -5], [50, 2], [52, 5], [55, 10], [58, 10], [60, 5], [60, 20], [55, 25], [50, 20], [45, 15], [40, 15], [38, 0], [36, -10]],
  // Africa
  [[35, -5], [30, -10], [25, -15], [15, -17], [5, -5], [0, 10], [-10, 15], [-20, 25], [-35, 20], [-35, 30], [-25, 35], [-15, 40], [-5, 42], [5, 45], [15, 50], [25, 35], [30, 32], [35, 10], [35, -5]],
  // Asia
  [[45, 30], [50, 40], [55, 60], [60, 80], [65, 100], [70, 120], [65, 140], [55, 140], [45, 135], [35, 130], [25, 120], [20, 110], [10, 105], [0, 100], [10, 80], [25, 70], [35, 55], [40, 45], [45, 30]],
  // Australia
  [[-15, 125], [-20, 115], [-30, 115], [-35, 120], [-38, 145], [-30, 150], [-25, 153], [-15, 145], [-12, 135], [-15, 125]],
];

// Globe wireframe component
function GlobeWireframe() {
  const RADIUS = 2;
  const SEGMENTS = 32;

  // Create latitude/longitude lines - denser grid
  const latLines = useMemo(() => {
    const lines: THREE.Vector3[][] = [];

    // Latitude lines (every 20 degrees for cleaner look)
    for (let lat = -60; lat <= 60; lat += 20) {
      const points: THREE.Vector3[] = [];
      for (let lng = 0; lng <= 360; lng += 5) {
        points.push(latLngToVector3(lat, lng - 180, RADIUS));
      }
      lines.push(points);
    }

    // Longitude lines (every 30 degrees)
    for (let lng = 0; lng < 360; lng += 30) {
      const points: THREE.Vector3[] = [];
      for (let lat = -90; lat <= 90; lat += 5) {
        points.push(latLngToVector3(lat, lng - 180, RADIUS));
      }
      lines.push(points);
    }

    return lines;
  }, []);

  // Convert continent outlines to 3D points
  const continentLines = useMemo(() => {
    return CONTINENT_OUTLINES.map(outline =>
      outline.map(([lat, lng]) => latLngToVector3(lat, lng, RADIUS * 1.001))
    );
  }, []);

  // Tropic lines for geographic reference
  const tropicLines = useMemo(() => {
    const lines: { lat: number; color: string }[] = [
      { lat: 23.5, color: '#2a1505' },   // Tropic of Cancer
      { lat: -23.5, color: '#2a1505' },  // Tropic of Capricorn
      { lat: 66.5, color: '#1a0f05' },   // Arctic Circle
      { lat: -66.5, color: '#1a0f05' },  // Antarctic Circle
    ];
    return lines.map(({ lat, color }) => ({
      points: Array.from({ length: 73 }, (_, i) =>
        latLngToVector3(lat, i * 5 - 180, RADIUS)
      ),
      color,
    }));
  }, []);

  return (
    <group>
      {/* Outer glow sphere */}
      <Sphere args={[RADIUS * 1.02, SEGMENTS, SEGMENTS]}>
        <meshBasicMaterial
          color="#ff9500"
          transparent
          opacity={0.03}
        />
      </Sphere>

      {/* Base sphere - dark amber fill (prototype v8 style) */}
      <Sphere args={[RADIUS * 0.99, SEGMENTS, SEGMENTS]}>
        <meshBasicMaterial
          color="#0a0502"
          transparent
          opacity={0.95}
          side={THREE.BackSide}
        />
      </Sphere>

      {/* Wireframe lines - amber tinted */}
      {latLines.map((points, i) => (
        <Line
          key={i}
          points={points}
          color="#1a0f05"
          lineWidth={0.5}
          transparent
          opacity={0.3}
        />
      ))}

      {/* Continent outlines - more visible amber */}
      {continentLines.map((points, i) => (
        <Line
          key={`continent-${i}`}
          points={points}
          color="#ff9500"
          lineWidth={1.2}
          transparent
          opacity={0.6}
        />
      ))}

      {/* Tropic and polar lines */}
      {tropicLines.map((line, i) => (
        <Line
          key={`tropic-${i}`}
          points={line.points}
          color={line.color}
          lineWidth={0.8}
          transparent
          opacity={0.5}
        />
      ))}

      {/* Equator highlight - amber glow */}
      <Line
        points={Array.from({ length: 73 }, (_, i) =>
          latLngToVector3(0, i * 5 - 180, RADIUS)
        )}
        color="#ff9500"
        lineWidth={1.5}
        transparent
        opacity={0.7}
      />

      {/* Prime Meridian highlight */}
      <Line
        points={Array.from({ length: 37 }, (_, i) =>
          latLngToVector3(i * 5 - 90, 0, RADIUS)
        )}
        color="#ff9500"
        lineWidth={1}
        transparent
        opacity={0.4}
      />
    </group>
  );
}

// Country markers component
interface CountryMarkersProps {
  countries: CountryStats[];
  onCountryClick: (countryCode: string) => void;
  onCountryHover: (countryCode: string | null, userCount: number) => void;
}

function CountryMarkers({
  countries,
  onCountryClick,
  onCountryHover,
}: CountryMarkersProps) {
  const RADIUS = 2.02;
  const meshRefs = useRef<Map<string, THREE.Mesh>>(new Map());

  // Filter countries with users and valid coordinates
  const activeCountries = useMemo(() => {
    return countries.filter(
      c => c.user_count > 0 && COUNTRY_COORDS[c.country_code.toUpperCase()]
    );
  }, [countries]);

  // Pulsing animation
  useFrame(({ clock }) => {
    const time = clock.getElapsedTime();
    meshRefs.current.forEach((mesh, code) => {
      if (mesh) {
        const scale = 1 + Math.sin(time * 2) * 0.15;
        mesh.scale.setScalar(scale);
      }
    });
  });

  return (
    <group>
      {activeCountries.map(country => {
        const coords = COUNTRY_COORDS[country.country_code.toUpperCase()];
        if (!coords) return null;

        const position = latLngToVector3(coords.lat, coords.lng, RADIUS);

        // Size based on user count (min 0.04, max 0.15)
        const size = Math.min(0.15, Math.max(0.04, country.user_count * 0.01));

        // Color based on online status (amber theme from prototype v8)
        const hasOnline = country.online_count > 0;
        const color = hasOnline ? '#ffb340' : '#ff9500'; // amber-bright : amber

        return (
          <mesh
            key={country.country_code}
            ref={el => {
              if (el) meshRefs.current.set(country.country_code, el);
            }}
            position={position}
            onClick={(e) => {
              e.stopPropagation();
              onCountryClick(country.country_code);
            }}
            onPointerEnter={() => onCountryHover(country.country_code, country.user_count)}
            onPointerLeave={() => onCountryHover(null, 0)}
          >
            <sphereGeometry args={[size, 16, 16]} />
            <meshBasicMaterial
              color={color}
              transparent
              opacity={0.9}
            />
          </mesh>
        );
      })}
    </group>
  );
}

// Glow rings for active countries
function GlowRings({ countries }: { countries: CountryStats[] }) {
  const RADIUS = 2.01;

  const activeCountries = useMemo(() => {
    return countries.filter(
      c => c.online_count > 0 && COUNTRY_COORDS[c.country_code.toUpperCase()]
    );
  }, [countries]);

  useFrame(({ clock }) => {
    // Animation handled in shader if needed
  });

  return (
    <group>
      {activeCountries.map(country => {
        const coords = COUNTRY_COORDS[country.country_code.toUpperCase()];
        if (!coords) return null;

        const position = latLngToVector3(coords.lat, coords.lng, RADIUS);

        return (
          <mesh key={`ring-${country.country_code}`} position={position}>
            <ringGeometry args={[0.08, 0.12, 32]} />
            <meshBasicMaterial
              color="#ff9500"
              transparent
              opacity={0.4}
              side={THREE.DoubleSide}
            />
          </mesh>
        );
      })}
    </group>
  );
}

// Scene component
function GlobeScene({
  countries,
  onCountryClick,
  onCountryHover,
}: CountryMarkersProps) {
  const groupRef = useRef<THREE.Group>(null);

  // Slow auto-rotation
  useFrame((state, delta) => {
    if (groupRef.current) {
      groupRef.current.rotation.y += delta * 0.05;
    }
  });

  return (
    <>
      {/* Ambient light */}
      <ambientLight intensity={0.5} />

      {/* Directional light */}
      <directionalLight position={[5, 3, 5]} intensity={0.5} />

      {/* Globe group */}
      <group ref={groupRef}>
        <GlobeWireframe />
        <CountryMarkers
          countries={countries}
          onCountryClick={onCountryClick}
          onCountryHover={onCountryHover}
        />
        <GlowRings countries={countries} />
      </group>

      {/* Controls */}
      <OrbitControls
        enablePan={false}
        enableZoom={true}
        minDistance={3}
        maxDistance={8}
        rotateSpeed={0.5}
        zoomSpeed={0.5}
        // Disable auto-rotate when user is interacting
        enableDamping={true}
        dampingFactor={0.05}
      />
    </>
  );
}

// Main Globe3D component
export function Globe3D({
  countries,
  onCountryClick,
  onCountryHover,
}: Globe3DProps) {
  const [hoveredCountry, setHoveredCountry] = useState<{
    code: string;
    count: number;
  } | null>(null);

  const handleHover = useCallback((code: string | null, count: number) => {
    if (code) {
      setHoveredCountry({ code, count });
    } else {
      setHoveredCountry(null);
    }
    onCountryHover?.(code, count);
  }, [onCountryHover]);

  return (
    <div className="relative w-full h-full" style={{ minHeight: '280px' }}>
      <Canvas
        camera={{ position: [0, 0, 3.2], fov: 50 }}
        gl={{ antialias: true, alpha: true }}
        style={{ background: 'transparent', width: '100%', height: '100%' }}
      >
        <GlobeScene
          countries={countries}
          onCountryClick={onCountryClick}
          onCountryHover={handleHover}
        />
      </Canvas>

      {/* Tooltip */}
      {hoveredCountry && (
        <div className="absolute top-4 left-1/2 -translate-x-1/2 pointer-events-none">
          <div className="data-box px-3 py-2 text-center">
            <div className="text-amber-bright font-semibold">
              {getCountryName(hoveredCountry.code)}
            </div>
            <div className="text-xs text-cyan">
              {hoveredCountry.count} Operator{hoveredCountry.count !== 1 ? 's' : ''}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Globe3D;
