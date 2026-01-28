/**
 * useGlobe Hook - Three.js Globe utilities for Emberholm Mini App
 * Provides country coordinates and interaction helpers
 */

import { useRef, useCallback } from 'react';
import * as THREE from 'three';

// Country center coordinates (lat, lng)
export const COUNTRY_COORDS: Record<string, { lat: number; lng: number; name: string }> = {
  // North America
  US: { lat: 39.8, lng: -98.5, name: 'United States' },
  CA: { lat: 56.1, lng: -106.3, name: 'Canada' },
  MX: { lat: 23.6, lng: -102.5, name: 'Mexico' },

  // Central America & Caribbean
  GT: { lat: 15.8, lng: -90.2, name: 'Guatemala' },
  BZ: { lat: 17.2, lng: -88.5, name: 'Belize' },
  HN: { lat: 15.0, lng: -86.5, name: 'Honduras' },
  SV: { lat: 13.8, lng: -88.9, name: 'El Salvador' },
  NI: { lat: 12.8, lng: -85.2, name: 'Nicaragua' },
  CR: { lat: 9.7, lng: -83.8, name: 'Costa Rica' },
  PA: { lat: 8.5, lng: -80.8, name: 'Panama' },
  CU: { lat: 21.5, lng: -77.8, name: 'Cuba' },
  DO: { lat: 18.7, lng: -70.2, name: 'Dominican Republic' },
  PR: { lat: 18.2, lng: -66.5, name: 'Puerto Rico' },

  // South America
  CO: { lat: 4.6, lng: -74.3, name: 'Colombia' },
  VE: { lat: 6.4, lng: -66.6, name: 'Venezuela' },
  EC: { lat: -1.8, lng: -78.2, name: 'Ecuador' },
  PE: { lat: -9.2, lng: -75.0, name: 'Peru' },
  BR: { lat: -14.2, lng: -51.9, name: 'Brazil' },
  BO: { lat: -16.3, lng: -63.6, name: 'Bolivia' },
  PY: { lat: -23.4, lng: -58.4, name: 'Paraguay' },
  UY: { lat: -32.5, lng: -55.8, name: 'Uruguay' },
  AR: { lat: -38.4, lng: -63.6, name: 'Argentina' },
  CL: { lat: -35.7, lng: -71.5, name: 'Chile' },

  // Europe
  GB: { lat: 55.4, lng: -3.4, name: 'United Kingdom' },
  IE: { lat: 53.1, lng: -7.7, name: 'Ireland' },
  FR: { lat: 46.2, lng: 2.2, name: 'France' },
  ES: { lat: 40.5, lng: -3.7, name: 'Spain' },
  PT: { lat: 39.4, lng: -8.2, name: 'Portugal' },
  DE: { lat: 51.2, lng: 10.5, name: 'Germany' },
  IT: { lat: 41.9, lng: 12.6, name: 'Italy' },
  NL: { lat: 52.1, lng: 5.3, name: 'Netherlands' },
  BE: { lat: 50.5, lng: 4.5, name: 'Belgium' },
  CH: { lat: 46.8, lng: 8.2, name: 'Switzerland' },
  AT: { lat: 47.5, lng: 14.6, name: 'Austria' },
  PL: { lat: 51.9, lng: 19.1, name: 'Poland' },
  CZ: { lat: 49.8, lng: 15.5, name: 'Czech Republic' },
  SE: { lat: 60.1, lng: 18.6, name: 'Sweden' },
  NO: { lat: 60.5, lng: 8.5, name: 'Norway' },
  DK: { lat: 56.3, lng: 9.5, name: 'Denmark' },
  FI: { lat: 61.9, lng: 25.7, name: 'Finland' },
  RU: { lat: 61.5, lng: 105.3, name: 'Russia' },
  UA: { lat: 48.4, lng: 31.2, name: 'Ukraine' },
  GR: { lat: 39.1, lng: 21.8, name: 'Greece' },
  TR: { lat: 39.0, lng: 35.2, name: 'Turkey' },

  // Asia
  JP: { lat: 36.2, lng: 138.3, name: 'Japan' },
  KR: { lat: 35.9, lng: 127.8, name: 'South Korea' },
  CN: { lat: 35.9, lng: 104.2, name: 'China' },
  TW: { lat: 23.7, lng: 121.0, name: 'Taiwan' },
  HK: { lat: 22.4, lng: 114.1, name: 'Hong Kong' },
  SG: { lat: 1.4, lng: 103.8, name: 'Singapore' },
  MY: { lat: 4.2, lng: 101.9, name: 'Malaysia' },
  TH: { lat: 15.9, lng: 100.9, name: 'Thailand' },
  VN: { lat: 14.1, lng: 108.3, name: 'Vietnam' },
  PH: { lat: 12.9, lng: 121.8, name: 'Philippines' },
  ID: { lat: -0.8, lng: 113.9, name: 'Indonesia' },
  IN: { lat: 20.6, lng: 79.0, name: 'India' },
  PK: { lat: 30.4, lng: 69.3, name: 'Pakistan' },
  BD: { lat: 23.7, lng: 90.4, name: 'Bangladesh' },
  AE: { lat: 23.4, lng: 53.8, name: 'UAE' },
  SA: { lat: 23.9, lng: 45.1, name: 'Saudi Arabia' },
  IL: { lat: 31.0, lng: 34.9, name: 'Israel' },

  // Africa
  ZA: { lat: -30.6, lng: 22.9, name: 'South Africa' },
  NG: { lat: 9.1, lng: 8.7, name: 'Nigeria' },
  EG: { lat: 26.8, lng: 30.8, name: 'Egypt' },
  KE: { lat: -0.0, lng: 37.9, name: 'Kenya' },
  MA: { lat: 31.8, lng: -7.1, name: 'Morocco' },

  // Oceania
  AU: { lat: -25.3, lng: 133.8, name: 'Australia' },
  NZ: { lat: -40.9, lng: 174.9, name: 'New Zealand' },
};

// Convert lat/lng to 3D position on sphere
export function latLngToVector3(lat: number, lng: number, radius: number): THREE.Vector3 {
  const phi = (90 - lat) * (Math.PI / 180);
  const theta = (lng + 180) * (Math.PI / 180);

  const x = -(radius * Math.sin(phi) * Math.cos(theta));
  const y = radius * Math.cos(phi);
  const z = radius * Math.sin(phi) * Math.sin(theta);

  return new THREE.Vector3(x, y, z);
}

// Get position for a country code
export function getCountryPosition(countryCode: string, radius: number): THREE.Vector3 | null {
  const coords = COUNTRY_COORDS[countryCode.toUpperCase()];
  if (!coords) return null;
  return latLngToVector3(coords.lat, coords.lng, radius);
}

// Get country name from code
export function getCountryName(countryCode: string): string {
  return COUNTRY_COORDS[countryCode.toUpperCase()]?.name || countryCode;
}

// Hook for managing globe interactions
interface UseGlobeOptions {
  autoRotate?: boolean;
  rotationSpeed?: number;
}

export function useGlobe(options: UseGlobeOptions = {}) {
  const { autoRotate = true, rotationSpeed = 0.001 } = options;

  const globeRef = useRef<THREE.Group | null>(null);
  const isDraggingRef = useRef(false);
  const previousMouseRef = useRef({ x: 0, y: 0 });
  const targetRotationRef = useRef({ x: 0, y: 0 });
  const currentRotationRef = useRef({ x: 0, y: 0 });

  // Handle mouse/touch start
  const handlePointerDown = useCallback((e: THREE.Event) => {
    isDraggingRef.current = true;
    const event = e as unknown as { clientX: number; clientY: number };
    previousMouseRef.current = { x: event.clientX, y: event.clientY };
  }, []);

  // Handle mouse/touch move
  const handlePointerMove = useCallback((e: THREE.Event) => {
    if (!isDraggingRef.current) return;

    const event = e as unknown as { clientX: number; clientY: number };
    const deltaX = event.clientX - previousMouseRef.current.x;
    const deltaY = event.clientY - previousMouseRef.current.y;

    targetRotationRef.current.y += deltaX * 0.005;
    targetRotationRef.current.x += deltaY * 0.005;

    // Clamp vertical rotation
    targetRotationRef.current.x = Math.max(
      -Math.PI / 2,
      Math.min(Math.PI / 2, targetRotationRef.current.x)
    );

    previousMouseRef.current = { x: event.clientX, y: event.clientY };
  }, []);

  // Handle mouse/touch end
  const handlePointerUp = useCallback(() => {
    isDraggingRef.current = false;
  }, []);

  // Animation frame update
  const updateRotation = useCallback((delta: number) => {
    if (!globeRef.current) return;

    // Auto-rotate when not dragging
    if (autoRotate && !isDraggingRef.current) {
      targetRotationRef.current.y += rotationSpeed;
    }

    // Smooth interpolation
    currentRotationRef.current.x += (targetRotationRef.current.x - currentRotationRef.current.x) * 0.1;
    currentRotationRef.current.y += (targetRotationRef.current.y - currentRotationRef.current.y) * 0.1;

    globeRef.current.rotation.x = currentRotationRef.current.x;
    globeRef.current.rotation.y = currentRotationRef.current.y;
  }, [autoRotate, rotationSpeed]);

  return {
    globeRef,
    handlePointerDown,
    handlePointerMove,
    handlePointerUp,
    updateRotation,
    isDragging: () => isDraggingRef.current,
  };
}

export default useGlobe;
