'use client';

import { useEffect, useRef, useState, useMemo, useCallback } from 'react';
import { useWallpaperOptional } from '@/lib/WallpaperContext';

/**
 * LivingWallpaper - Animated terminal-style background
 * 11 configurable layers for immersive cyberpunk aesthetic
 */

// Characters for ghost code effect
const GHOST_CHARS = '0123456789ABCDEF>_[]{}|◈⚔🔥';

// Data stream texts
const DATA_STREAMS = [
  '>>> 0x7AB2cf80...EMBER_PROTOCOL_v0.1978 >>> STATUS: ONLINE >>> SYNC: 100% >>> BLOCK: CONFIRMED >>> GUILD: ACTIVE >>> ',
  '>>> EMISSARY_#00042 >>> MISSION: VOID_DESCENT >>> TIME: 02:34:17 >>> AURA: 847 >>> STATUS: IN_PROGRESS >>> ',
  '>>> BLOCK: 18294756 >>> TX: 0x4f2a8b... >>> CONFIRMED >>> GAS: 0.0012 ETH >>> EMBER_TRANSFER: SUCCESS >>> ',
];

interface GhostColumn {
  id: number;
  x: number;
  chars: string[];
  speed: number;
  startTime: number;
}

export function LivingWallpaper() {
  const context = useWallpaperOptional();
  const settings = context?.settings;
  const isVisible = context?.isVisible ?? true;

  const [ghostColumns, setGhostColumns] = useState<GhostColumn[]>([]);
  const [glitchLines, setGlitchLines] = useState<{ id: number; top: number }[]>([]);
  const columnIdRef = useRef(0);
  const glitchIdRef = useRef(0);
  const animationFrameRef = useRef<number | null>(null);

  // Generate random ghost code column
  const createGhostColumn = useCallback(() => {
    const chars: string[] = [];
    const length = Math.floor(Math.random() * 15) + 10;
    for (let i = 0; i < length; i++) {
      chars.push(GHOST_CHARS[Math.floor(Math.random() * GHOST_CHARS.length)]);
    }
    return {
      id: columnIdRef.current++,
      x: Math.random() * 100,
      chars,
      speed: 12 + Math.random() * 15, // 12-27s duration
      startTime: Date.now(),
    };
  }, []);

  // Ghost code column spawner
  useEffect(() => {
    if (!settings?.ghostCodeEnabled || !isVisible) return;

    const spawnColumn = () => {
      setGhostColumns(prev => {
        // Remove old columns and add new one
        const now = Date.now();
        const active = prev.filter(col => now - col.startTime < col.speed * 1000);
        if (active.length < 15) {
          return [...active, createGhostColumn()];
        }
        return active;
      });
    };

    // Initial columns
    for (let i = 0; i < 5; i++) {
      setTimeout(() => spawnColumn(), i * 400);
    }

    const interval = setInterval(spawnColumn, 2000);
    return () => clearInterval(interval);
  }, [settings?.ghostCodeEnabled, isVisible, createGhostColumn]);

  // Glitch lines spawner
  useEffect(() => {
    if (!settings?.glitchEnabled || !isVisible) return;

    const spawnGlitch = () => {
      const newGlitch = {
        id: glitchIdRef.current++,
        top: Math.random() * 100,
      };
      setGlitchLines(prev => [...prev.slice(-2), newGlitch]);

      // Remove glitch after animation
      setTimeout(() => {
        setGlitchLines(prev => prev.filter(g => g.id !== newGlitch.id));
      }, 200);
    };

    const interval = setInterval(spawnGlitch, 4000);
    return () => clearInterval(interval);
  }, [settings?.glitchEnabled, isVisible]);

  // Noise SVG filter
  const noiseSvg = useMemo(() => (
    <svg className="hidden">
      <defs>
        <filter id="noise-filter">
          <feTurbulence
            type="fractalNoise"
            baseFrequency="0.9"
            numOctaves="4"
            stitchTiles="stitch"
          />
          <feColorMatrix type="saturate" values="0" />
        </filter>
      </defs>
    </svg>
  ), []);

  // Don't render if no context (SSR safety)
  if (!settings) {
    return null;
  }

  const dotOpacity = settings.dotGridOpacity / 100;
  const ghostOpacity = settings.ghostCodeOpacity / 100;
  const streamOpacity = settings.dataStreamOpacity / 100;

  return (
    <div
      className="living-wallpaper"
      style={{
        position: 'fixed',
        inset: 0,
        width: '100%',
        height: '100%',
        overflow: 'hidden',
        pointerEvents: 'none',
        zIndex: 0,
      }}
    >
      {noiseSvg}

      {/* Layer 1: Gradient Pulse */}
      {settings.gradientEnabled && (
        <div
          className="wallpaper-gradient"
          style={{
            position: 'absolute',
            inset: 0,
            background: 'radial-gradient(ellipse at center, rgba(255, 149, 0, 0.08) 0%, transparent 70%)',
            animation: isVisible ? 'gradient-pulse 6s ease-in-out infinite' : 'none',
          }}
        />
      )}

      {/* Layer 2: Dot Grid */}
      {settings.dotGridEnabled && (
        <div
          className="wallpaper-dots"
          style={{
            position: 'absolute',
            inset: 0,
            backgroundImage: 'radial-gradient(rgba(255, 149, 0, 0.15) 1px, transparent 1px)',
            backgroundSize: '30px 30px',
            opacity: dotOpacity,
            animation: isVisible ? 'dot-pulse 4s ease-in-out infinite' : 'none',
          }}
        />
      )}

      {/* Layer 3: Moving Lines */}
      {settings.movingLinesEnabled && (
        <div
          className="wallpaper-lines"
          style={{
            position: 'absolute',
            inset: 0,
            backgroundImage: 'repeating-linear-gradient(0deg, transparent, transparent 99px, rgba(255, 149, 0, 0.03) 99px, rgba(255, 149, 0, 0.03) 100px)',
            backgroundSize: '100% 100px',
            animation: isVisible ? 'scroll-up 10s linear infinite' : 'none',
            willChange: 'transform',
          }}
        />
      )}

      {/* Layer 4: Noise */}
      {settings.noiseEnabled && (
        <div
          className="wallpaper-noise"
          style={{
            position: 'absolute',
            inset: 0,
            opacity: 0.06,
            filter: 'url(#noise-filter)',
            animation: isVisible ? 'noise-shift 0.3s steps(2) infinite' : 'none',
          }}
        />
      )}

      {/* Layer 5: Ghost Code Columns */}
      {settings.ghostCodeEnabled && (
        <div
          className="wallpaper-ghost-code"
          style={{
            position: 'absolute',
            inset: 0,
            overflow: 'hidden',
          }}
        >
          {ghostColumns.map(column => (
            <div
              key={column.id}
              className="ghost-column"
              style={{
                position: 'absolute',
                left: `${column.x}%`,
                top: 0,
                fontFamily: 'VT323, monospace',
                fontSize: '14px',
                color: 'rgba(255, 149, 0, 0.15)',
                opacity: ghostOpacity,
                writingMode: 'vertical-rl',
                textOrientation: 'mixed',
                animation: isVisible ? `fall-down ${column.speed}s linear forwards` : 'none',
                willChange: 'transform',
              }}
            >
              {column.chars.join('')}
            </div>
          ))}
        </div>
      )}

      {/* Layer 6: Data Streams */}
      {settings.dataStreamEnabled && (
        <div className="wallpaper-streams">
          {DATA_STREAMS.map((text, i) => (
            <div
              key={i}
              className="data-stream"
              style={{
                position: 'absolute',
                top: `${12 + i * 35}%`,
                left: 0,
                width: '200%',
                fontFamily: 'VT323, monospace',
                fontSize: '11px',
                color: '#ff9500',
                opacity: streamOpacity,
                whiteSpace: 'nowrap',
                animation: isVisible ? `scroll-left ${20 + i * 5}s linear infinite` : 'none',
                willChange: 'transform',
              }}
            >
              {text.repeat(3)}
            </div>
          ))}
        </div>
      )}

      {/* Layer 7: Glitch Lines */}
      {settings.glitchEnabled && glitchLines.map(glitch => (
        <div
          key={glitch.id}
          className="glitch-line"
          style={{
            position: 'absolute',
            top: `${glitch.top}%`,
            left: 0,
            width: '100%',
            height: '2px',
            background: 'linear-gradient(90deg, transparent, #ff9500, #ffb340, #ff9500, transparent)',
            boxShadow: '0 0 10px #ff9500, 0 0 20px rgba(255, 149, 0, 0.5)',
            animation: 'glitch-flash 0.2s ease-out forwards',
          }}
        />
      ))}

      {/* Layer 8: Scanlines */}
      {settings.scanlinesEnabled && (
        <div
          className="wallpaper-scanlines"
          style={{
            position: 'absolute',
            inset: 0,
            backgroundImage: 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0, 0, 0, 0.15) 2px, rgba(0, 0, 0, 0.15) 3px)',
            pointerEvents: 'none',
          }}
        />
      )}

      {/* Layer 9: Vignette */}
      {settings.vignetteEnabled && (
        <div
          className="wallpaper-vignette"
          style={{
            position: 'absolute',
            inset: 0,
            background: 'radial-gradient(ellipse at center, transparent 30%, rgba(0, 0, 0, 0.6) 100%)',
            pointerEvents: 'none',
          }}
        />
      )}

      {/* Layer 10: CRT Flicker */}
      {settings.flickerEnabled && (
        <div
          className="wallpaper-flicker"
          style={{
            position: 'absolute',
            inset: 0,
            backgroundColor: 'rgba(255, 149, 0, 0.02)',
            animation: isVisible ? 'crt-flicker 0.1s steps(2) infinite' : 'none',
            pointerEvents: 'none',
          }}
        />
      )}

      {/* Layer 11: Border Glow */}
      <div
        className="wallpaper-border"
        style={{
          position: 'absolute',
          inset: 0,
          border: '1px solid rgba(255, 149, 0, 0.2)',
          boxShadow: 'inset 0 0 50px rgba(255, 149, 0, 0.05), inset 0 0 100px rgba(0, 0, 0, 0.3)',
          pointerEvents: 'none',
        }}
      />
    </div>
  );
}

export default LivingWallpaper;
