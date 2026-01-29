'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { TrophyIcon, CrownIcon, Medal1Icon, Medal2Icon, Medal3Icon } from '@/components/ui/Icons';

/**
 * LeaderboardScreen - Player rankings
 * Tabs: GLOBAL | BY GUILD | WEEKLY | $PYRE
 * Top 50 players with user position highlighted
 */

interface LeaderboardEntry {
  rank: number;
  wallet: string;
  display_name: string | null;
  guild: string | null;
  xp_total: number;
  pyre_total: number;
  missions_completed: number;
  is_current_user?: boolean;
}

interface LeaderboardScreenProps {
  currentWallet: string | null;
  onBack: () => void;
}

type LeaderboardTab = 'global' | 'guild' | 'weekly' | 'pyre';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

export function LeaderboardScreen({
  currentWallet,
  onBack,
}: LeaderboardScreenProps) {
  const [activeTab, setActiveTab] = useState<LeaderboardTab>('global');
  const [entries, setEntries] = useState<LeaderboardEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [userRank, setUserRank] = useState<number | null>(null);

  // Load leaderboard data
  useEffect(() => {
    async function loadLeaderboard() {
      try {
        setIsLoading(true);

        // In production, this would call the actual leaderboard API
        // For now, using mock data
        const mockData: LeaderboardEntry[] = Array.from({ length: 50 }, (_, i) => ({
          rank: i + 1,
          wallet: `0x${(i + 1).toString().padStart(40, '0')}`,
          display_name: i < 10 ? `Player${i + 1}` : null,
          guild: ['Forge Legion', 'Circle of Mist', 'Order of Dawn', 'Shadow Guild', 'Horizon Watch', 'Void Echoes'][i % 6],
          xp_total: 10000 - i * 150,
          pyre_total: 5000 - i * 80,
          missions_completed: 100 - i * 2,
          is_current_user: currentWallet && i === 15, // Mock: current user at position 16
        }));

        // Sort based on active tab
        let sortedData = [...mockData];
        switch (activeTab) {
          case 'pyre':
            sortedData.sort((a, b) => b.pyre_total - a.pyre_total);
            break;
          case 'weekly':
            // Would use weekly stats in production
            sortedData.sort((a, b) => b.missions_completed - a.missions_completed);
            break;
          default:
            sortedData.sort((a, b) => b.xp_total - a.xp_total);
        }

        // Re-assign ranks after sorting
        sortedData = sortedData.map((entry, i) => ({ ...entry, rank: i + 1 }));

        setEntries(sortedData);

        // Find user rank
        const userEntry = sortedData.find(e => e.is_current_user);
        setUserRank(userEntry?.rank || null);
      } catch (error) {
        console.error('Failed to load leaderboard:', error);
      } finally {
        setIsLoading(false);
      }
    }

    loadLeaderboard();
  }, [activeTab, currentWallet]);

  // Format wallet address
  const formatWallet = (wallet: string) => {
    return `${wallet.slice(0, 6)}...${wallet.slice(-4)}`;
  };

  // Get rank color
  const getRankColor = (rank: number) => {
    if (rank === 1) return 'text-amber-bright';
    if (rank === 2) return 'text-amber';
    if (rank === 3) return 'text-amber-dim';
    return 'text-amber-darker';
  };

  // Get rank icon
  const getRankIcon = (rank: number) => {
    if (rank === 1) return <CrownIcon size={18} className="text-amber-bright" />;
    if (rank === 2) return <Medal2Icon size={18} className="text-gray-300" />;
    if (rank === 3) return <Medal3Icon size={18} className="text-amber-dark" />;
    return `#${rank}`;
  };

  const tabs: { id: LeaderboardTab; label: string }[] = [
    { id: 'global', label: 'GLOBAL' },
    { id: 'guild', label: 'BY GUILD' },
    { id: 'weekly', label: 'WEEKLY' },
    { id: 'pyre', label: '◈ PYRE' },
  ];

  return (
    <div className="screen-view flex flex-col min-h-screen p-4">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-4"
      >
        <h2 className="title text-xl">LEADERBOARDS</h2>
        <p className="text-amber-dim text-xs">Top 50 Emissaries</p>
      </motion.div>

      {/* User rank indicator */}
      {userRank && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="data-box mb-4"
        >
          <div className="flex items-center justify-between">
            <span className="text-amber-dim text-sm">Your Rank</span>
            <span className="text-amber-bright font-semibold">#{userRank}</span>
          </div>
        </motion.div>
      )}

      {/* Tabs */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.1 }}
        className="flex gap-1 mb-4 overflow-x-auto pb-1"
      >
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`tab whitespace-nowrap ${activeTab === tab.id ? 'active' : ''}`}
          >
            {tab.label}
          </button>
        ))}
      </motion.div>

      {/* Loading state */}
      {isLoading && (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <TrophyIcon size={48} className="text-amber animate-pulse mx-auto mb-2" />
            <p className="text-amber-dim text-sm">Loading rankings...</p>
          </div>
        </div>
      )}

      {/* Leaderboard list */}
      {!isLoading && (
        <div className="flex-1 scroll-area">
          {entries.map((entry, index) => (
            <motion.div
              key={entry.wallet}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.01 * index }}
              className={`data-box mb-2 ${entry.is_current_user ? 'border-amber' : ''}`}
            >
              <div className="flex items-center gap-3">
                {/* Rank */}
                <div className={`w-10 text-center font-semibold ${getRankColor(entry.rank)}`}>
                  {getRankIcon(entry.rank)}
                </div>

                {/* Player info */}
                <div className="flex-1 min-w-0">
                  <p className={`text-sm truncate ${entry.is_current_user ? 'text-amber-bright' : 'text-amber'}`}>
                    {entry.display_name || formatWallet(entry.wallet)}
                    {entry.is_current_user && <span className="text-cyan text-xs ml-2">(You)</span>}
                  </p>
                  {activeTab === 'guild' && entry.guild && (
                    <p className="text-xs text-amber-dim truncate">{entry.guild}</p>
                  )}
                </div>

                {/* Stats based on tab */}
                <div className="text-right">
                  {activeTab === 'pyre' ? (
                    <>
                      <p className="text-cyan font-semibold">{entry.pyre_total.toLocaleString()}</p>
                      <p className="text-xs text-amber-dim">◈ PYRE</p>
                    </>
                  ) : activeTab === 'weekly' ? (
                    <>
                      <p className="text-amber font-semibold">{entry.missions_completed}</p>
                      <p className="text-xs text-amber-dim">Missions</p>
                    </>
                  ) : (
                    <>
                      <p className="text-amber font-semibold">{entry.xp_total.toLocaleString()}</p>
                      <p className="text-xs text-amber-dim">XP</p>
                    </>
                  )}
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      )}

      {/* Back button */}
      <button onClick={onBack} className="back-btn">
        ← BACK
      </button>
    </div>
  );
}
