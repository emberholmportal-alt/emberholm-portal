'use client';

import { useEffect, useState } from 'react';
import { getRealmStatus, RealmStatus } from '@/lib/api';

/**
 * ImmersionBar - Top bar showing realm status
 * Displays: Weather icon, time, date (Era of the Flame, 1978)
 */

const WEATHER_ICONS: Record<string, string> = {
  sun: '☀️',
  cloud: '☁️',
  'cloud-lightning': '⛈️',
  'cloud-drizzle': '🔥',
  moon: '🌙',
  wind: '💨',
};

export function ImmersionBar() {
  const [realm, setRealm] = useState<RealmStatus | null>(null);

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

  if (!realm) {
    return (
      <div className="immersion-bar">
        <span className="opacity-50">Loading realm...</span>
      </div>
    );
  }

  const weatherIcon = WEATHER_ICONS[realm.weather.icon] || '🔥';

  return (
    <div className="immersion-bar safe-area-top">
      <span className="flex items-center gap-1">
        <span>{weatherIcon}</span>
        <span>{realm.weather.name}</span>
      </span>
      <span className="text-ember-400/50">·</span>
      <span>{realm.time}</span>
      <span className="text-ember-400/50">·</span>
      <span>{realm.date}</span>
    </div>
  );
}
