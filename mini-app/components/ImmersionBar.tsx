'use client';

import { useEffect, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { getRealmStatus, RealmStatus } from '@/lib/api';

/**
 * ImmersionBar - Top bar showing realm status
 * Displays: Sound toggle, Flame state, Time/Date, Weather
 */

// Weather icons mapping
const WEATHER_ICONS: Record<string, string> = {
  sun: '☀️',
  clear: '☀️',
  cloud: '☁️',
  cloudy: '☁️',
  'cloud-lightning': '⛈️',
  storm: '⛈️',
  'cloud-drizzle': '🌧️',
  rain: '🌧️',
  drizzle: '🌧️',
  moon: '🌙',
  night: '🌙',
  wind: '💨',
  windy: '💨',
  fire: '🔥',
  ember: '🔥',
  ash: '🌫️',
  fog: '🌫️',
  snow: '❄️',
};

// Flame state colors
const FLAME_COLORS: Record<string, { text: string; glow: string }> = {
  BRIGHT: { text: 'text-amber-bright', glow: 'drop-shadow-[0_0_8px_#f59e0b]' },
  STRONG: { text: 'text-amber', glow: 'drop-shadow-[0_0_6px_#d97706]' },
  STEADY: { text: 'text-amber', glow: 'drop-shadow-[0_0_4px_#b45309]' },
  FLICKERING: { text: 'text-amber-dim', glow: 'drop-shadow-[0_0_3px_#92400e]' },
  WEAK: { text: 'text-red', glow: 'drop-shadow-[0_0_3px_#dc2626]' },
  DYING: { text: 'text-red', glow: 'drop-shadow-[0_0_2px_#991b1b]' },
};

export function ImmersionBar() {
  const [realm, setRealm] = useState<RealmStatus | null>(null);
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [showFlameTooltip, setShowFlameTooltip] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(false);

  // Load sound preference from localStorage
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('emberholm_sound');
      if (saved !== null) {
        setSoundEnabled(saved !== 'false');
      }
    }
  }, []);

  // Fetch realm status
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        setError(false);
        const status = await getRealmStatus();
        setRealm(status);
      } catch (err) {
        console.error('Failed to fetch realm status:', err);
        setError(true);
      } finally {
        setIsLoading(false);
      }
    };

    fetchStatus();

    // Refresh every minute
    const interval = setInterval(fetchStatus, 60000);
    return () => clearInterval(interval);
  }, []);

  // Toggle sound
  const toggleSound = useCallback(() => {
    const newValue = !soundEnabled;
    setSoundEnabled(newValue);
    if (typeof window !== 'undefined') {
      localStorage.setItem('emberholm_sound', String(newValue));
    }
  }, [soundEnabled]);

  // Get weather icon
  const getWeatherIcon = (iconName?: string): string => {
    if (!iconName) return '🔥';
    const normalized = iconName.toLowerCase();
    return WEATHER_ICONS[normalized] || '🔥';
  };

  // Get flame styling
  const getFlameStyle = (flameName?: string) => {
    if (!flameName) return FLAME_COLORS.STEADY;
    const normalized = flameName.toUpperCase();
    return FLAME_COLORS[normalized] || FLAME_COLORS.STEADY;
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="top-bar">
        <div className="top-bar-left">
          <button onClick={toggleSound} className="p-1 rounded hover:bg-amber-dark/20 transition-colors">
            {soundEnabled ? '🔊' : '🔇'}
          </button>
        </div>
        <div className="top-bar-center">
          <motion.span
            animate={{ opacity: [0.5, 1, 0.5] }}
            transition={{ duration: 1.5, repeat: Infinity }}
            className="text-amber-dim text-xs"
          >
            Connecting to realm...
          </motion.span>
        </div>
        <div className="top-bar-right">
          <span className="text-lg">🔥</span>
        </div>
      </div>
    );
  }

  // Error state
  if (error || !realm) {
    return (
      <div className="top-bar">
        <div className="top-bar-left">
          <button onClick={toggleSound} className="p-1 rounded hover:bg-amber-dark/20 transition-colors">
            {soundEnabled ? '🔊' : '🔇'}
          </button>
        </div>
        <div className="top-bar-center">
          <span className="text-amber-dim text-xs">Era of the Flame</span>
        </div>
        <div className="top-bar-right">
          <span className="text-lg">🔥</span>
        </div>
      </div>
    );
  }

  const weatherIcon = getWeatherIcon(realm.weather?.icon);
  const flameStyle = getFlameStyle(realm.flame?.name);

  return (
    <div className="top-bar">
      {/* Left: Sound toggle */}
      <div className="top-bar-left">
        <button
          onClick={toggleSound}
          className={`
            p-1 rounded transition-all duration-200
            hover:bg-amber-dark/20 active:scale-95
            ${!soundEnabled ? 'opacity-50' : ''}
          `}
          aria-label={soundEnabled ? 'Mute sound' : 'Enable sound'}
        >
          {soundEnabled ? '🔊' : '🔇'}
        </button>
      </div>

      {/* Center: Flame state + Time/Date */}
      <div className="top-bar-center relative">
        {/* Flame indicator */}
        <div
          className="relative cursor-help"
          onMouseEnter={() => setShowFlameTooltip(true)}
          onMouseLeave={() => setShowFlameTooltip(false)}
          onTouchStart={() => setShowFlameTooltip(!showFlameTooltip)}
        >
          <motion.span
            animate={realm.flame?.name === 'FLICKERING' || realm.flame?.name === 'WEAK'
              ? { opacity: [1, 0.6, 1] }
              : {}
            }
            transition={{ duration: 0.5, repeat: Infinity }}
            className={`text-lg ${flameStyle.text} ${flameStyle.glow}`}
          >
            🔥
          </motion.span>

          {/* Flame tooltip */}
          <AnimatePresence>
            {showFlameTooltip && realm.flame && (
              <motion.div
                initial={{ opacity: 0, y: -5 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -5 }}
                className="absolute top-full left-1/2 -translate-x-1/2 mt-2 z-50
                         bg-dark border border-amber-dark/50 rounded px-2 py-1
                         whitespace-nowrap text-xs"
              >
                <div className={`font-semibold ${flameStyle.text}`}>
                  The {realm.flame.name} Flame
                </div>
                {realm.flame.description && (
                  <div className="text-amber-dim mt-0.5 max-w-[200px] text-center">
                    {realm.flame.description}
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Time and Date */}
        <div className="flex flex-col items-center text-center">
          <span className="text-amber-bright text-xs font-medium">{realm.time}</span>
          <span className="text-amber-dim text-[10px]">{realm.date}</span>
        </div>
      </div>

      {/* Right: Weather */}
      <div className="top-bar-right" title={realm.weather?.description || realm.weather?.name}>
        <span className="text-lg">{weatherIcon}</span>
        {realm.weather?.name && (
          <span className="text-xs text-amber-dim hidden sm:inline ml-1">
            {realm.weather.name}
          </span>
        )}
      </div>
    </div>
  );
}

export default ImmersionBar;
