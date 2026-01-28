'use client';

import { motion } from 'framer-motion';
import { AppScreen } from '@/lib/store';
import { ActiveMicroMission } from '@/lib/api';

/**
 * PlayScreen - Play submenu with 4 options
 * MISSIONS, MICRO-MISSIONS, ACTIVE EMISSARIES, LEADERBOARDS
 */

interface PlayScreenProps {
  emissaryCount: number;
  activeMission: ActiveMicroMission | null;
  onNavigate: (screen: AppScreen) => void;
  onBack: () => void;
}

interface MenuItem {
  id: AppScreen | 'emissary-list';
  title: string;
  subtitle: string;
  icon: string;
  description: string;
}

export function PlayScreen({
  emissaryCount,
  activeMission,
  onNavigate,
  onBack,
}: PlayScreenProps) {
  const hasActiveMission = activeMission !== null;

  const menuItems: MenuItem[] = [
    {
      id: 'missions',
      title: 'MISSIONS',
      subtitle: 'Full adventures',
      icon: '🗺️',
      description: 'Long quests with rare rewards and risks',
    },
    {
      id: 'micro-missions',
      title: 'MICRO-MISSIONS',
      subtitle: 'Quick adventures',
      icon: '⚡',
      description: 'Short 1-5 min quests for $PYRE rewards',
    },
    {
      id: 'emissary-list',
      title: 'EMISSARIES',
      subtitle: `${emissaryCount} owned`,
      icon: '⚔️',
      description: 'View and manage your Emissaries',
    },
    {
      id: 'leaderboard',
      title: 'LEADERBOARDS',
      subtitle: 'Rankings',
      icon: '🏆',
      description: 'Global rankings and guild standings',
    },
  ];

  return (
    <div className="screen-view flex flex-col min-h-screen p-4">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-6"
      >
        <h1 className="title text-2xl">PLAY</h1>
        <p className="subtitle">Choose your adventure</p>
      </motion.div>

      {/* Active mission indicator */}
      {hasActiveMission && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="data-box mb-4"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="animate-pulse">🔥</span>
              <span className="text-amber text-sm">
                Active: {activeMission?.name || 'Micro-Mission'}
              </span>
            </div>
            <button
              onClick={() => onNavigate('timer')}
              className="btn small"
            >
              VIEW
            </button>
          </div>
        </motion.div>
      )}

      {/* Menu items */}
      <div className="flex-1 space-y-3">
        {menuItems.map((item, index) => (
          <motion.button
            key={item.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.05 * index }}
            onClick={() => onNavigate(item.id as AppScreen)}
            className="w-full data-box text-left transition-all duration-200
                       hover:border-amber active:scale-[0.98]"
          >
            <div className="flex items-start gap-3">
              <span className="text-2xl">{item.icon}</span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <h3 className="text-amber-bright font-semibold">
                    {item.title}
                  </h3>
                  <span className="text-xs text-amber-dim">
                    {item.subtitle}
                  </span>
                </div>
                <p className="text-xs text-amber-dim mt-1">
                  {item.description}
                </p>
              </div>
              <span className="text-amber-dark">›</span>
            </div>
          </motion.button>
        ))}
      </div>

      {/* Back button */}
      <button onClick={onBack} className="back-btn">
        ← BACK TO MENU
      </button>
    </div>
  );
}
