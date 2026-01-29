'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import dynamic from 'next/dynamic';
import Image from 'next/image';
import { getCountries, getOnlineStats, getNftStats, CountryStats, OnlineStats, NftStats } from '@/lib/api';
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

// Flavor texts for the census panel
const CENSUS_FLAVOR = [
  'Emissaries await their Operators in the void...',
  'Unregistered souls wander the mist...',
  'The void calls to the unclaimed...',
  'Ember-less shadows drift between worlds...',
  'Lost ones seek their destined Operators...',
];

export function SocialGlobe({ onSelectCountry, onGlobalChat, onBack }: SocialGlobeProps) {
  const [countries, setCountries] = useState<CountryStats[]>([]);
  const [stats, setStats] = useState<OnlineStats | null>(null);
  const [nftStats, setNftStats] = useState<NftStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [hoveredCountry, setHoveredCountry] = useState<string | null>(null);
  const [censusFlavor, setCensusFlavor] = useState(CENSUS_FLAVOR[0]);

  // Load data
  useEffect(() => {
    async function loadData() {
      setIsLoading(true);
      try {
        const [countriesData, statsData, nftData] = await Promise.all([
          getCountries(),
          getOnlineStats(),
          getNftStats(),
        ]);
        setCountries(countriesData);
        setStats(statsData);
        setNftStats(nftData);
      } catch (error) {
        console.error('Error loading social data:', error);
      } finally {
        setIsLoading(false);
      }
    }
    loadData();
  }, []);

  // Rotate census flavor text
  useEffect(() => {
    const interval = setInterval(() => {
      setCensusFlavor(CENSUS_FLAVOR[Math.floor(Math.random() * CENSUS_FLAVOR.length)]);
    }, 8000);
    return () => clearInterval(interval);
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
        <p className="text-amber-dim text-xs">
          DRAG TO ROTATE · TAP MARKER FOR DETAILS
        </p>
      </motion.div>

      {/* Globe Container - 280px height per spec */}
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.1 }}
        className="relative mx-4"
        style={{
          height: '280px',
          border: '1px solid var(--amber-dark, #804d00)',
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

      {/* Stats Footer - 3 columns */}
      <div className="stats-footer mx-4 mt-2" style={{ borderTop: 'none', padding: '5px 0' }}>
        <div className="stat-item">
          <div className="stat-value">{stats?.countries_represented || 0}</div>
          <div className="stat-label">COUNTRIES</div>
        </div>
        <div className="stat-item">
          <div className="stat-value cyan">{stats?.online_now || 0}</div>
          <div className="stat-label">ONLINE</div>
        </div>
        <div className="stat-item">
          <div className="stat-value">{nftStats?.total_minted?.toLocaleString() || 0}</div>
          <div className="stat-label">HOLDERS</div>
        </div>
      </div>

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

        {/* Emissary Census Panel */}
        {nftStats && (
          <div className="data-box">
            <div className="ornament text-xs mb-3">═══ EMISSARY CENSUS ═══</div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Image
                    src="/icons/fire.png"
                    alt=""
                    width={16}
                    height={16}
                    className="pixel-icon"
                  />
                  <span className="text-amber-dim text-sm">Total Minted</span>
                </div>
                <span className="text-amber-bright font-bold">
                  {nftStats.total_minted.toLocaleString()}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Image
                    src="/icons/crystalball.png"
                    alt=""
                    width={16}
                    height={16}
                    className="pixel-icon"
                  />
                  <span className="text-amber-dim text-sm">Registered</span>
                </div>
                <span className="text-green font-bold">
                  {nftStats.registered.toLocaleString()}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Image
                    src="/icons/skull.png"
                    alt=""
                    width={16}
                    height={16}
                    className="pixel-icon"
                  />
                  <span className="text-amber-dim text-sm">Unregistered</span>
                </div>
                <span className="text-cyan font-bold">
                  {nftStats.unregistered.toLocaleString()}
                </span>
              </div>
            </div>
            {nftStats.unregistered > 0 && (
              <motion.div
                key={censusFlavor}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="text-xs text-amber-dim text-center mt-3 italic"
              >
                "{nftStats.unregistered.toLocaleString()} {censusFlavor}"
              </motion.div>
            )}
          </div>
        )}

        {/* Messages Button */}
        <button
          onClick={() => {}}
          className="menu-btn w-full"
          style={{ marginTop: '5px' }}
        >
          <span className="icon">
            <Image src="/icons/scroll.png" alt="" width={20} height={20} className="pixel-icon" />
          </span>
          <span className="flex-1 text-left">MESSAGES</span>
          <span className="notif-badge">3</span>
        </button>

        {/* Global Chat Button */}
        <button
          onClick={onGlobalChat}
          className="menu-btn w-full"
        >
          <span className="icon">
            <Image src="/icons/fire.png" alt="" width={20} height={20} className="pixel-icon" />
          </span>
          <span className="flex-1 text-left">GLOBAL CHAT</span>
        </button>
      </motion.div>

      {/* Back button */}
      <div className="p-4 pt-2">
        <button onClick={onBack} className="back-btn">
          ◄ BACK TO MENU
        </button>
      </div>
    </div>
  );
}

export default SocialGlobe;
