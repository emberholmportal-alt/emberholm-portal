'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import dynamic from 'next/dynamic';
import { getCountries, getOnlineStats, getNftStats, CountryStats, OnlineStats, NftStats } from '@/lib/api';
import { getCountryName } from '@/lib/hooks/useGlobe';
import { ChatIcon, GemIcon, NftIcon, GhostIcon, UsersIcon } from '@/components/ui/Icons';

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
  onGlobalChat?: () => void;
  onBack: () => void;
}

export function SocialGlobe({ onSelectCountry, onGlobalChat, onBack }: SocialGlobeProps) {
  const [countries, setCountries] = useState<CountryStats[]>([]);
  const [stats, setStats] = useState<OnlineStats | null>(null);
  const [nftStats, setNftStats] = useState<NftStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [hoveredCountry, setHoveredCountry] = useState<string | null>(null);

  // Load data
  useEffect(() => {
    async function loadData() {
      setIsLoading(true);
      try {
        const [countriesData, statsData, nftStatsData] = await Promise.all([
          getCountries(),
          getOnlineStats(),
          getNftStats(),
        ]);
        setCountries(countriesData);
        setStats(statsData);
        setNftStats(nftStatsData);
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

      {/* Globe Container */}
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.1 }}
        className="flex-1 min-h-[300px] max-h-[400px] relative"
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

        {/* NFT Community Stats */}
        {nftStats && (
          <div className="data-box">
            <div className="ornament text-xs mb-2">═══ EMISSARY CENSUS ═══</div>
            <div className="grid grid-cols-3 gap-2 text-center">
              <div>
                <div className="flex items-center justify-center gap-1">
                  <NftIcon size={16} className="text-amber" />
                  <span className="text-xl text-amber-bright font-bold">
                    {nftStats.total_minted}
                  </span>
                </div>
                <div className="text-xs text-amber-dim">Minted</div>
              </div>
              <div>
                <div className="flex items-center justify-center gap-1">
                  <UsersIcon size={16} className="text-green" />
                  <span className="text-xl text-green font-bold">
                    {nftStats.registered}
                  </span>
                </div>
                <div className="text-xs text-amber-dim">Registered</div>
              </div>
              <div>
                <div className="flex items-center justify-center gap-1">
                  <GhostIcon size={16} className="text-amber-dark" />
                  <span className="text-xl text-amber-dark font-bold">
                    {nftStats.unregistered}
                  </span>
                </div>
                <div className="text-xs text-amber-dim">Unregistered</div>
              </div>
            </div>
            {/* Progress bar showing registration percentage */}
            <div className="mt-3">
              <div className="h-2 bg-bg-dark rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-amber to-green transition-all duration-500"
                  style={{
                    width: `${nftStats.total_minted > 0
                      ? (nftStats.registered / nftStats.total_minted) * 100
                      : 0}%`
                  }}
                />
              </div>
              <p className="text-xs text-amber-dim text-center mt-1">
                {nftStats.total_minted > 0
                  ? Math.round((nftStats.registered / nftStats.total_minted) * 100)
                  : 0}% of Emissaries have joined the Realm
              </p>
            </div>
          </div>
        )}

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
        {onGlobalChat && (
          <button
            onClick={onGlobalChat}
            className="w-full data-box flex items-center justify-between hover:border-amber transition-colors"
          >
            <div className="flex items-center gap-3">
              <ChatIcon size={24} className="text-cyan" />
              <div className="text-left">
                <div className="text-amber-bright font-semibold">GLOBAL CHAT</div>
                <div className="text-xs text-amber-dim">Chat with all operators</div>
              </div>
            </div>
            <div className="flex items-center gap-1 text-cyan text-xs">
              <GemIcon size={12} className="text-cyan" />
              +5 PYRE
            </div>
          </button>
        )}

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
