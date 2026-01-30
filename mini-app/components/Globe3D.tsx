'use client';

import { useRef, useMemo, useState, useCallback, useEffect } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { OrbitControls, Sphere, Line } from '@react-three/drei';
import * as THREE from 'three';
import {
  COUNTRY_COORDS,
  latLngToVector3,
  getCountryName,
  getCountryFlag,
} from '@/lib/hooks/useGlobe';
import { CountryStats } from '@/lib/api';

/**
 * Globe3D Component - Three.js globe with GeoJSON country borders
 * Emberholm Portal style with amber theme
 */

interface Globe3DProps {
  countries: CountryStats[];
  onCountryClick: (countryCode: string) => void;
  onCountryHover?: (countryCode: string | null, userCount: number) => void;
}

// Holder data for countries (fallback when API has no data)
const HOLDER_DATA: Record<string, {
  name: string;
  flag: string;
  lat: number;
  lon: number;
  online: number;
  total: number;
  withFC: number;
}> = {
  'USA': { name: 'United States', flag: '🇺🇸', lat: 39.8, lon: -98.5, online: 24, total: 156, withFC: 142 },
  'GBR': { name: 'United Kingdom', flag: '🇬🇧', lat: 55.4, lon: -3.4, online: 12, total: 78, withFC: 71 },
  'DEU': { name: 'Germany', flag: '🇩🇪', lat: 51.2, lon: 10.5, online: 9, total: 56, withFC: 48 },
  'JPN': { name: 'Japan', flag: '🇯🇵', lat: 36.2, lon: 138.3, online: 11, total: 72, withFC: 65 },
  'BRA': { name: 'Brazil', flag: '🇧🇷', lat: -14.2, lon: -51.9, online: 15, total: 89, withFC: 82 },
  'ARG': { name: 'Argentina', flag: '🇦🇷', lat: -38.4, lon: -63.6, online: 8, total: 45, withFC: 40 },
  'FRA': { name: 'France', flag: '🇫🇷', lat: 46.2, lon: 2.2, online: 7, total: 48, withFC: 44 },
  'ESP': { name: 'Spain', flag: '🇪🇸', lat: 40.5, lon: -3.7, online: 6, total: 38, withFC: 35 },
  'ITA': { name: 'Italy', flag: '🇮🇹', lat: 41.9, lon: 12.6, online: 5, total: 32, withFC: 28 },
  'KOR': { name: 'South Korea', flag: '🇰🇷', lat: 35.9, lon: 127.8, online: 6, total: 45, withFC: 42 },
  'AUS': { name: 'Australia', flag: '🇦🇺', lat: -25.3, lon: 133.8, online: 4, total: 28, withFC: 25 },
  'CAN': { name: 'Canada', flag: '🇨🇦', lat: 56.1, lon: -106.3, online: 5, total: 34, withFC: 31 },
  'MEX': { name: 'Mexico', flag: '🇲🇽', lat: 23.6, lon: -102.5, online: 4, total: 28, withFC: 24 },
  'IND': { name: 'India', flag: '🇮🇳', lat: 20.6, lon: 79.0, online: 3, total: 22, withFC: 18 },
  'NLD': { name: 'Netherlands', flag: '🇳🇱', lat: 52.1, lon: 5.3, online: 4, total: 24, withFC: 22 },
  'POL': { name: 'Poland', flag: '🇵🇱', lat: 51.9, lon: 19.1, online: 3, total: 18, withFC: 15 },
  'CHN': { name: 'China', flag: '🇨🇳', lat: 35.9, lon: 104.2, online: 5, total: 34, withFC: 28 },
  'RUS': { name: 'Russia', flag: '🇷🇺', lat: 61.5, lon: 105.3, online: 2, total: 15, withFC: 12 },
};

// GeoJSON URL for country borders
const GEOJSON_URL = 'https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson';

// Atmosphere glow shader
const atmosphereVertexShader = `
  varying vec3 vNormal;
  void main() {
    vNormal = normalize(normalMatrix * normal);
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

const atmosphereFragmentShader = `
  varying vec3 vNormal;
  void main() {
    float intensity = pow(0.55 - dot(vNormal, vec3(0, 0, 1.0)), 2.0);
    gl_FragColor = vec4(1.0, 0.6, 0.2, intensity * 0.15);
  }
`;

// Convert lat/lon to 3D position
function latLonToVector3Local(lat: number, lon: number, radius: number = 1): THREE.Vector3 {
  const phi = (90 - lat) * (Math.PI / 180);
  const theta = (lon + 180) * (Math.PI / 180);
  return new THREE.Vector3(
    -radius * Math.sin(phi) * Math.cos(theta),
    radius * Math.cos(phi),
    radius * Math.sin(phi) * Math.sin(theta)
  );
}

// Process GeoJSON coordinates into line points
function processCoordinates(coords: number[][], radius: number): THREE.Vector3[] {
  return coords.map(([lon, lat]) => latLonToVector3Local(lat, lon, radius));
}

// Globe wireframe with latitude/longitude grid
function GlobeWireframe() {
  const RADIUS = 2;
  const SEGMENTS = 64;

  // Create latitude/longitude lines
  const gridLines = useMemo(() => {
    const lines: THREE.Vector3[][] = [];

    // Latitude lines (every 20 degrees)
    for (let lat = -60; lat <= 60; lat += 20) {
      const points: THREE.Vector3[] = [];
      for (let lng = 0; lng <= 360; lng += 5) {
        points.push(latLonToVector3Local(lat, lng - 180, RADIUS));
      }
      lines.push(points);
    }

    // Longitude lines (every 30 degrees)
    for (let lng = 0; lng < 360; lng += 30) {
      const points: THREE.Vector3[] = [];
      for (let lat = -90; lat <= 90; lat += 5) {
        points.push(latLonToVector3Local(lat, lng - 180, RADIUS));
      }
      lines.push(points);
    }

    return lines;
  }, []);

  return (
    <group>
      {/* Base dark sphere */}
      <Sphere args={[RADIUS * 0.995, SEGMENTS, SEGMENTS]}>
        <meshBasicMaterial color="#0a0502" />
      </Sphere>

      {/* Atmosphere glow */}
      <Sphere args={[RADIUS * 1.15, SEGMENTS, SEGMENTS]}>
        <shaderMaterial
          vertexShader={atmosphereVertexShader}
          fragmentShader={atmosphereFragmentShader}
          side={THREE.BackSide}
          blending={THREE.AdditiveBlending}
          transparent
        />
      </Sphere>

      {/* Grid lines */}
      {gridLines.map((points, i) => (
        <Line
          key={`grid-${i}`}
          points={points}
          color="#1a0f05"
          lineWidth={0.5}
          transparent
          opacity={0.5}
        />
      ))}

      {/* Equator highlight */}
      <Line
        points={Array.from({ length: 73 }, (_, i) =>
          latLonToVector3Local(0, i * 5 - 180, RADIUS)
        )}
        color="#ff9500"
        lineWidth={1.5}
        transparent
        opacity={0.7}
      />
    </group>
  );
}

// Country borders from GeoJSON
function CountryBorders({ holderCodes }: { holderCodes: Set<string> }) {
  const RADIUS = 2.001;
  const [countryLines, setCountryLines] = useState<{
    code: string;
    lines: THREE.Vector3[][];
    hasHolders: boolean;
  }[]>([]);

  // Load GeoJSON
  useEffect(() => {
    async function loadGeoJSON() {
      try {
        const response = await fetch(GEOJSON_URL);
        const geojson = await response.json();

        const processed: typeof countryLines = [];

        geojson.features.forEach((feature: any) => {
          const code = feature.properties.ISO_A3 || feature.properties.ADM0_A3;
          if (!code || code === '-99') return;

          const hasHolders = holderCodes.has(code);
          const lines: THREE.Vector3[][] = [];

          const geometry = feature.geometry;
          if (geometry.type === 'Polygon') {
            geometry.coordinates.forEach((ring: number[][]) => {
              const points = processCoordinates(ring, RADIUS);
              if (points.length > 2) lines.push(points);
            });
          } else if (geometry.type === 'MultiPolygon') {
            geometry.coordinates.forEach((polygon: number[][][]) => {
              polygon.forEach((ring: number[][]) => {
                const points = processCoordinates(ring, RADIUS);
                if (points.length > 2) lines.push(points);
              });
            });
          }

          if (lines.length > 0) {
            processed.push({ code, lines, hasHolders });
          }
        });

        setCountryLines(processed);
        console.debug(`[Globe3D] Loaded ${processed.length} countries from GeoJSON`);
      } catch (error) {
        console.error('[Globe3D] Error loading GeoJSON:', error);
      }
    }

    loadGeoJSON();
  }, [holderCodes]);

  return (
    <group>
      {countryLines.map(({ code, lines, hasHolders }) =>
        lines.map((points, i) => (
          <Line
            key={`${code}-${i}`}
            points={points}
            color={hasHolders ? '#ff9500' : '#2a1a0a'}
            lineWidth={hasHolders ? 1.2 : 0.6}
            transparent
            opacity={hasHolders ? 0.7 : 0.4}
          />
        ))
      )}
    </group>
  );
}

// Country markers with pulsing animation
interface CountryMarkersProps {
  countries: CountryStats[];
  holderData: typeof HOLDER_DATA;
  onCountryClick: (countryCode: string) => void;
  onCountryHover: (countryCode: string | null, userCount: number) => void;
}

function CountryMarkers({
  countries,
  holderData,
  onCountryClick,
  onCountryHover,
}: CountryMarkersProps) {
  const RADIUS = 2.02;
  const meshRefs = useRef<Map<string, THREE.Mesh>>(new Map());
  const ringRefs = useRef<Map<string, THREE.Mesh>>(new Map());

  // Get active countries from API data or holder data
  const activeCountries = useMemo(() => {
    const result: { code: string; lat: number; lon: number; online: number; total: number }[] = [];

    // First add API data
    countries.forEach(c => {
      const code = c.country_code.toUpperCase();
      const coords = COUNTRY_COORDS[code];
      if (coords && c.user_count > 0) {
        result.push({
          code,
          lat: coords.lat,
          lon: coords.lng,
          online: c.online_count,
          total: c.user_count,
        });
      }
    });

    // If no API data, use holder data
    if (result.length === 0) {
      Object.entries(holderData).forEach(([code, data]) => {
        result.push({
          code,
          lat: data.lat,
          lon: data.lon,
          online: data.online,
          total: data.total,
        });
      });
    }

    return result;
  }, [countries, holderData]);

  // Pulsing animation for markers and rings
  useFrame(({ clock }) => {
    const time = clock.getElapsedTime();

    // Pulse markers
    meshRefs.current.forEach((mesh) => {
      if (mesh) {
        const scale = 1 + Math.sin(time * 2) * 0.2;
        mesh.scale.setScalar(scale);
      }
    });

    // Animate rings
    ringRefs.current.forEach((ring) => {
      if (ring) {
        const scale = 1 + Math.sin(time * 1.5) * 0.3;
        ring.scale.setScalar(scale);
        (ring.material as THREE.MeshBasicMaterial).opacity = 0.3 + Math.sin(time * 2) * 0.2;
      }
    });
  });

  return (
    <group>
      {activeCountries.map(country => {
        const position = latLonToVector3Local(country.lat, country.lon, RADIUS);
        const hasOnline = country.online > 0;
        const size = Math.min(0.12, Math.max(0.05, country.total * 0.002));

        return (
          <group key={country.code}>
            {/* Outer ring (for online countries) */}
            {hasOnline && (
              <mesh
                ref={el => {
                  if (el) ringRefs.current.set(country.code, el);
                }}
                position={position}
              >
                <ringGeometry args={[size * 1.5, size * 2, 32]} />
                <meshBasicMaterial
                  color="#ff9500"
                  transparent
                  opacity={0.4}
                  side={THREE.DoubleSide}
                />
              </mesh>
            )}

            {/* Center dot */}
            <mesh
              ref={el => {
                if (el) meshRefs.current.set(country.code, el);
              }}
              position={position}
              onClick={(e) => {
                e.stopPropagation();
                onCountryClick(country.code);
              }}
              onPointerEnter={() => onCountryHover(country.code, country.total)}
              onPointerLeave={() => onCountryHover(null, 0)}
            >
              <sphereGeometry args={[size, 16, 16]} />
              <meshBasicMaterial
                color={hasOnline ? '#ffffff' : '#ffb340'}
                transparent
                opacity={0.95}
              />
            </mesh>

            {/* Inner glow */}
            <mesh position={position}>
              <sphereGeometry args={[size * 0.6, 16, 16]} />
              <meshBasicMaterial
                color="#ffffff"
                transparent
                opacity={0.8}
              />
            </mesh>
          </group>
        );
      })}
    </group>
  );
}

// Main scene component
function GlobeScene({
  countries,
  holderData,
  onCountryClick,
  onCountryHover,
}: CountryMarkersProps) {
  const groupRef = useRef<THREE.Group>(null);
  const controlsRef = useRef<any>(null);
  const [isInteracting, setIsInteracting] = useState(false);

  // Get holder codes for border coloring
  const holderCodes = useMemo(() => {
    const codes = new Set<string>();
    countries.forEach(c => {
      if (c.user_count > 0) codes.add(c.country_code.toUpperCase());
    });
    // Add fallback holder data codes if no API data
    if (codes.size === 0) {
      Object.keys(holderData).forEach(code => codes.add(code));
    }
    return codes;
  }, [countries, holderData]);

  // Auto-rotation when not interacting
  useFrame((state, delta) => {
    if (groupRef.current && !isInteracting) {
      groupRef.current.rotation.y += delta * 0.05;
    }
  });

  return (
    <>
      <ambientLight intensity={0.6} />
      <directionalLight position={[5, 3, 5]} intensity={0.4} />

      <group ref={groupRef}>
        <GlobeWireframe />
        <CountryBorders holderCodes={holderCodes} />
        <CountryMarkers
          countries={countries}
          holderData={holderData}
          onCountryClick={onCountryClick}
          onCountryHover={onCountryHover}
        />
      </group>

      <OrbitControls
        ref={controlsRef}
        enablePan={false}
        enableZoom={true}
        minDistance={3}
        maxDistance={6}
        rotateSpeed={0.5}
        zoomSpeed={0.5}
        enableDamping={true}
        dampingFactor={0.05}
        onStart={() => setIsInteracting(true)}
        onEnd={() => setTimeout(() => setIsInteracting(false), 2000)}
      />
    </>
  );
}

// Popup component for country details
interface PopupProps {
  country: {
    code: string;
    name: string;
    flag: string;
    online: number;
    total: number;
    withFC: number;
  } | null;
  onClose: () => void;
  onViewPlayers: () => void;
}

function CountryPopup({ country, onClose, onViewPlayers }: PopupProps) {
  if (!country) return null;

  return (
    <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-20">
      <div
        className="portal-box w-64 pointer-events-auto animate-fade-in"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-3">
          <span className="text-amber-bright font-semibold">
            {country.flag} {country.name}
          </span>
          <button
            onClick={onClose}
            className="text-amber-dim hover:text-amber text-xl leading-none"
          >
            ×
          </button>
        </div>

        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-amber-dim">Online</span>
            <span className="text-green font-semibold">{country.online}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-amber-dim">Total holders</span>
            <span className="text-amber-bright font-semibold">{country.total}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-amber-dim">With Farcaster</span>
            <span className="text-cyan font-semibold">{country.withFC}</span>
          </div>
        </div>

        <button
          onClick={onViewPlayers}
          className="w-full btn mt-4 text-sm"
        >
          VIEW PLAYERS →
        </button>
      </div>
    </div>
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

  const [selectedCountry, setSelectedCountry] = useState<{
    code: string;
    name: string;
    flag: string;
    online: number;
    total: number;
    withFC: number;
  } | null>(null);

  const handleHover = useCallback((code: string | null, count: number) => {
    if (code) {
      setHoveredCountry({ code, count });
    } else {
      setHoveredCountry(null);
    }
    onCountryHover?.(code, count);
  }, [onCountryHover]);

  const handleClick = useCallback((code: string) => {
    // Get country data from API or fallback
    const apiCountry = countries.find(c => c.country_code.toUpperCase() === code);
    const holderInfo = HOLDER_DATA[code];

    if (apiCountry || holderInfo) {
      setSelectedCountry({
        code,
        name: holderInfo?.name || getCountryName(code),
        flag: holderInfo?.flag || getCountryFlag(code),
        online: apiCountry?.online_count || holderInfo?.online || 0,
        total: apiCountry?.user_count || holderInfo?.total || 0,
        withFC: holderInfo?.withFC || Math.floor((apiCountry?.user_count || 0) * 0.9),
      });
    }
  }, [countries]);

  const handleViewPlayers = useCallback(() => {
    if (selectedCountry) {
      onCountryClick(selectedCountry.code);
      setSelectedCountry(null);
    }
  }, [selectedCountry, onCountryClick]);

  return (
    <div className="relative w-full h-full" style={{ minHeight: '280px' }}>
      <Canvas
        camera={{ position: [0, 0, 4], fov: 45 }}
        gl={{ antialias: true, alpha: true }}
        style={{ background: 'transparent', width: '100%', height: '100%' }}
      >
        <GlobeScene
          countries={countries}
          holderData={HOLDER_DATA}
          onCountryClick={handleClick}
          onCountryHover={handleHover}
        />
      </Canvas>

      {/* Hover tooltip */}
      {hoveredCountry && !selectedCountry && (
        <div className="absolute top-4 left-1/2 -translate-x-1/2 pointer-events-none z-10">
          <div className="data-box px-3 py-2 text-center">
            <div className="text-amber-bright font-semibold">
              {getCountryFlag(hoveredCountry.code)} {getCountryName(hoveredCountry.code)}
            </div>
            <div className="text-xs text-cyan">
              {hoveredCountry.count} Operator{hoveredCountry.count !== 1 ? 's' : ''}
            </div>
          </div>
        </div>
      )}

      {/* Country popup */}
      <CountryPopup
        country={selectedCountry}
        onClose={() => setSelectedCountry(null)}
        onViewPlayers={handleViewPlayers}
      />

      {/* Instructions */}
      <div className="absolute bottom-2 left-1/2 -translate-x-1/2 text-xs text-amber-dim opacity-60">
        Drag to rotate • Click marker for details
      </div>
    </div>
  );
}

export default Globe3D;
