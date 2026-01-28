'use client';

import { useEffect, useState } from 'react';
import { getRealmStatus, RealmStatus } from '@/lib/api';

/**
 * ImmersionBar - Top bar showing realm status
 * Displays: Music toggle, Weather icon, time, date (Era of the Flame, 1978)
 */

const WEATHER_ICONS: Record<string, string> = {
  sun: '☀️',
  cloud: '☁️',
  'cloud-lightning': '⛈️',
  'cloud-drizzle': '🌧️',
  moon: '🌙',
  wind: '💨',
  fire: '🔥',
};

export function ImmersionBar() {
  const [realm, setRealm] = useState<RealmStatus | null>(null);
  const [soundEnabled, setSoundEnabled] = useState(true);

  useEffect(() => {
    // Fetch realm status
    const fetchStatus = async () => {
      try {
        const status = await getRealmStatus();
        setRealm(status);
      } catch (error) {
        console.error('Failed to fetch realm status:', error);
      }
    };

    fetchStatus();

    // Refresh every minute
    const interval = setInterval(fetchStatus, 60000);
    return () => clearInterval(interval);
  }, []);

  const toggleSound = () => {
    setSoundEnabled(!soundEnabled);
  };

  if (!realm) {
    return (
      <div className="top-bar">
        <div className="top-bar-left">
          <span className="music-icon" onClick={toggleSound}>
            {soundEnabled ? '🔊' : '🔇'}
          </span>
        </div>
        <div className="top-bar-center">
          <span className="text-amber-dim">Loading realm...</span>
        </div>
        <div className="top-bar-right">
          <span className="weather-icon">🔥</span>
        </div>
      </div>
    );
  }

  const weatherIcon = WEATHER_ICONS[realm.weather.icon] || '🔥';

  return (
    <div className="top-bar">
      {/* Left: Sound toggle */}
      <div className="top-bar-left">
        <span
          className={`music-icon ${!soundEnabled ? 'muted' : ''}`}
          onClick={toggleSound}
        >
          {soundEnabled ? '🔊' : '🔇'}
        </span>
      </div>

      {/* Center: Time and Date */}
      <div className="top-bar-center">
        <span>{realm.time}</span>
        <span>{realm.date}</span>
      </div>

      {/* Right: Weather */}
      <div className="top-bar-right">
        <span className="weather-icon">{weatherIcon}</span>
        <span className="text-xs">{realm.weather.name}</span>
      </div>
    </div>
  );
}
