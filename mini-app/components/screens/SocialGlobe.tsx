'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import dynamic from 'next/dynamic';
import Image from 'next/image';
import { getCountries, getOnlineStats, CountryStats, OnlineStats } from '@/lib/api';
import { getCountryName } from '@/lib/hooks/useGlobe';

// Dynamically import Globe3D to avoid SSR issues with Three.js
const Globe3D = dynamic(() => import('@/components/Globe3D'), {
  ssr: false,
  loading: () => (
    <div className="w-full h-64 flex items-center justify-center">
      <div className="text-amber-dim animate-pulse">Loading globe...</div>
    </div>
  ),
});

/**
 * SocialGlobe Screen - 3D Globe with country stats
 */

interface SocialGlobeProps {
  onSelectCountry: (countryCode: string) => void;
  onGlobalChat: () => void;
  onBack: () => void;
}

export function SocialGlobe({ onSelectCountry, onGlobalChat, onBack }: SocialGlobeProps) {
  const [countries, setCountries] = useState<CountryStats[]>([]);
  const [stats, setStats] = useState<OnlineStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [hoveredCountry, setHoveredCountry] = useState<string | null>(null);

  // Load data
  useEffect(() => {
    async function loadData() {
      setIsLoading(true);
      try {
        const [countriesData, statsData] = await Promise.all([
          getCountries(),
          getOnlineStats(),
        ]);
        setCountries(countriesData);
        setStats(statsData);
      } catch (error) {
        console.error('Error loading social data:', error);
      } finally {
        setIsLoading(false);
      }
    }
    loadData();
  }, []);

  const handleCountryHover = (code: string | null) => {
    setHoveredCountry(code);
  };

  // Get top countries by user count
  const topCountries = [...countries]
    .sort((a, b) => b.user_count - a.user_count)
    .slice(0, 5);

  return (
    <div className="screen-view flex flex-col min-h-screen">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center p-4 pb-2"
      >
        <h1 className="title text-2xl">WORLD MAP</h1>
        <p className="subtitle">Operators across the Realm</p>
      </motion.div>

      {/* Globe Container - amber radial gradient background */}
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.1 }}
        className="flex-1 min-h-[300px] max-h-[400px] relative"
        style={{
          background: 'radial-gradient(ellipse at center, #1a0f05 0%, #0a0705 70%)',
        }}
      >
        {!isLoading && (
          <Globe3D
            countries={countries}
            onCountryClick={onSelectCountry}
            onCountryHover={handleCountryHover}
          />
        )}

        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-amber animate-pulse">
              Scanning dimensional frequencies...
            </div>
          </div>
        )}
      </motion.div>

      {/* Stats Panel */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="p-4 space-y-3"
      >
        {/* Global Stats */}
        <div className="data-box">
          <div className="ornament text-xs mb-2">═══ GLOBAL STATS ═══</div>
          <div className="grid grid-cols-3 gap-2 text-center">
            <div>
              <div className="text-xl text-amber-bright font-bold">
                {stats?.total_users || 0}
              </div>
              <div className="text-xs text-amber-dim">Total</div>
            </div>
            <div>
              <div className="text-xl text-green font-bold">
                {stats?.online_now || 0}
              </div>
              <div className="text-xs text-amber-dim">Online</div>
            </div>
            <div>
              <div className="text-xl text-cyan font-bold">
                {stats?.countries_represented || 0}
              </div>
              <div className="text-xs text-amber-dim">Nations</div>
            </div>
          </div>
        </div>

        {/* Top Countries */}
        <div className="data-box">
          <div className="ornament text-xs mb-2">═══ TOP NATIONS ═══</div>
          <div className="space-y-1">
            {topCountries.map((country, index) => (
              <button
                key={country.country_code}
                onClick={() => onSelectCountry(country.country_code)}
                className="w-full flex items-center justify-between px-2 py-1 rounded
                           hover:bg-amber/10 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <span className="text-amber-dim text-xs w-4">
                    {index + 1}.
                  </span>
                  <span className="text-amber">
                    {getCountryName(country.country_code)}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  {country.online_count > 0 && (
                    <span className="text-green text-xs">
                      {country.online_count} online
                    </span>
                  )}
                  <span className="text-amber-bright text-sm">
                    {country.user_count}
                  </span>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Global Chat Button */}
        <button
          onClick={onGlobalChat}
          className="w-full btn large flex items-center justify-center gap-2"
        >
          <Image
            src="/icons/fire.png"
            alt=""
            width={20}
            height={20}
            className="pixel-icon"
          />
          GLOBAL CHAT
        </button>

        {/* Instructions */}
        <div className="text-center text-xs text-amber-dim">
          Tap a glowing marker to view operators
        </div>
      </motion.div>

      {/* Back button */}
      <div className="p-4 pt-0">
        <button onClick={onBack} className="back-btn">
          ← BACK TO MENU
        </button>
      </div>
    </div>
  );
}

export default SocialGlobe;
