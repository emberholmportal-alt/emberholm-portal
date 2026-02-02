'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import dynamic from 'next/dynamic';
import Image from 'next/image';
import { getCountries, getOnlineStats, CountryStats, OnlineStats } from '@/lib/api';
import { getCountryName } from '@/lib/hooks/useGlobe';
import { CONTRACT_CONFIG } from '@/lib/contracts';

// Use contract address from centralized config (Base Mainnet)
const CONTRACT_ADDRESS = CONTRACT_CONFIG.CONTRACTS.EmberholmPortal;
const RPC_URL = CONTRACT_CONFIG.RPC_URL;

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
  const [totalEmissaries, setTotalEmissaries] = useState<number | null>(null);
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

  // Load totalSupply from contract
  useEffect(() => {
    async function loadContractStats() {
      try {
        // Call totalSupply() on the contract
        const response = await fetch(RPC_URL, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            jsonrpc: '2.0',
            method: 'eth_call',
            params: [{
              to: CONTRACT_ADDRESS,
              data: '0x18160ddd', // totalSupply() selector
            }, 'latest'],
            id: 1,
          }),
        });
        const data = await response.json();
        if (data.result) {
          const supply = parseInt(data.result, 16);
          setTotalEmissaries(supply);
        }
      } catch (error) {
        console.error('Error loading contract stats:', error);
      }
    }
    loadContractStats();
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
      {/* FIX: Changed max-h to aspect-ratio for better responsiveness and no clipping */}
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.1 }}
        className="relative w-full overflow-hidden"
        style={{
          background: 'radial-gradient(ellipse at center, #1a0f05 0%, #0a0705 70%)',
          aspectRatio: '1 / 0.85',
          maxHeight: '45vh',
          minHeight: '280px',
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
          <div className="ornament text-xs mb-2">═══ REALM STATS ═══</div>
          <div className="grid grid-cols-2 gap-2 text-center mb-3">
            <div>
              <div className="text-xl text-amber-bright font-bold">
                {totalEmissaries !== null ? totalEmissaries.toLocaleString() : '--'}
              </div>
              <div className="text-xs text-amber-dim">Emissaries</div>
            </div>
            <div>
              <div className="text-xl text-cyan font-bold">
                {stats ? stats.countries_represented : '--'}
              </div>
              <div className="text-xs text-amber-dim">Nations</div>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-2 text-center">
            <div>
              <div className="text-lg text-amber font-bold">
                {stats ? stats.total_users : '--'}
              </div>
              <div className="text-xs text-amber-dim">Operators</div>
            </div>
            <div>
              <div className="text-lg text-green font-bold">
                {stats ? stats.online_now : '--'}
              </div>
              <div className="text-xs text-amber-dim">Online</div>
            </div>
          </div>
        </div>

        {/* Top Countries - TEMPORARILY DISABLED */}
        <div className="data-box">
          <div className="ornament text-xs mb-2">═══ TOP NATIONS ═══</div>
          <div className="space-y-1">
            {topCountries.map((country, index) => (
              <div
                key={country.country_code}
                className="w-full flex items-center justify-between px-2 py-1 rounded
                           opacity-50 cursor-not-allowed"
              >
                <div className="flex items-center gap-2">
                  <span className="text-gray-500 text-xs w-4">
                    {index + 1}.
                  </span>
                  <span className="text-gray-500">
                    {getCountryName(country.country_code)}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  {country.online_count > 0 && (
                    <span className="text-gray-500 text-xs">
                      {country.online_count} online
                    </span>
                  )}
                  <span className="text-gray-500 text-sm">
                    {country.user_count}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Global Chat Button - TEMPORARILY DISABLED */}
        <button
          onClick={onGlobalChat}
          disabled={true}
          className="w-full btn large flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
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
