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

// Globe wireframe component
function GlobeWireframe() {
  const RADIUS = 2;
  const SEGMENTS = 32;

  // Create latitude/longitude lines - denser grid
  const latLines = useMemo(() => {
    const lines: THREE.Vector3[][] = [];

    // Latitude lines (every 15 degrees for more definition)
    for (let lat = -75; lat <= 75; lat += 15) {
      const points: THREE.Vector3[] = [];
      for (let lng = 0; lng <= 360; lng += 5) {
        points.push(latLngToVector3(lat, lng - 180, RADIUS));
      }
      lines.push(points);
    }

    // Longitude lines (every 20 degrees)
    for (let lng = 0; lng < 360; lng += 20) {
      const points: THREE.Vector3[] = [];
      for (let lat = -90; lat <= 90; lat += 5) {
        points.push(latLngToVector3(lat, lng - 180, RADIUS));
      }
      lines.push(points);
    }

    return lines;
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
          opacity={0.4}
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
    <div className="relative w-full h-full">
      <Canvas
        camera={{ position: [0, 0, 5], fov: 45 }}
        gl={{ antialias: true, alpha: true }}
        style={{ background: 'transparent' }}
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
