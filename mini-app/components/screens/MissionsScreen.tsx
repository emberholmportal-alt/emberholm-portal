'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Emissary } from '@/lib/api';
import { SwordsIcon, LightningIcon, MapIcon, UsersIcon } from '@/components/ui/Icons';

/**
 * MissionsScreen - Normal missions list
 * Uses portal web endpoints for regular long-duration missions
 */

interface Mission {
  id: string;
  name: string;
  difficulty: 'EASY' | 'MEDIUM' | 'HARD' | 'LEGENDARY';
  duration_hours: number;
  energy_cost: number;
  reward_xp: number;
  reward_aura: number;
  success_rate: number;
  death_chance: number;
  favored_guild: string;
  description: string;
  party_size?: number;
}

interface MissionsScreenProps {
  emissary: Emissary | null;
  onSelectMission: (mission: Mission) => void;
  onSelectEmissary: () => void;
  onBack: () => void;
}

const DIFFICULTY_STYLES: Record<string, { color: string; label: string }> = {
  EASY: { color: 'text-green', label: 'EASY' },
  MEDIUM: { color: 'text-amber', label: 'MEDIUM' },
  HARD: { color: 'text-red', label: 'HARD' },
  LEGENDARY: { color: 'text-cyan', label: 'LEGENDARY' },
};

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

export function MissionsScreen({
  emissary,
  onSelectMission,
  onSelectEmissary,
  onBack,
}: MissionsScreenProps) {
  const [missions, setMissions] = useState<Mission[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState<string>('ALL');

  // Load missions from portal API
  useEffect(() => {
    async function loadMissions() {
      try {
        setIsLoading(true);
        const response = await fetch(`${API_BASE}/api/missions`);
        if (response.ok) {
          const data = await response.json();
          setMissions(data.missions || []);
        }
      } catch (error) {
        console.error('Failed to load missions:', error);
      } finally {
        setIsLoading(false);
      }
    }

    loadMissions();
  }, []);

  // Filter missions
  const filteredMissions = filter === 'ALL'
    ? missions
    : missions.filter(m => m.difficulty === filter);

  // Format duration
  const formatDuration = (hours: number) => {
    if (hours < 1) return `${Math.round(hours * 60)}m`;
    return `${hours}h`;
  };

  return (
    <div className="screen-view flex flex-col min-h-screen p-4">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-4"
      >
        <h2 className="title text-xl">MISSIONS</h2>
        <p className="text-amber-dim text-xs">Long adventures with risks and rewards</p>
      </motion.div>

      {/* Selected emissary */}
      {emissary ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="data-box mb-4"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 border border-amber-dark bg-bg-dark flex items-center justify-center">
                {emissary.image_url ? (
                  <img
                    src={emissary.image_url}
                    alt={emissary.name}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <SwordsIcon size={20} className="text-amber" />
                )}
              </div>
              <div>
                <p className="text-amber text-sm font-semibold">
                  {emissary.name || `#${emissary.token_id}`}
                </p>
                <p className="text-xs text-amber-dim flex items-center gap-1">
                  LVL {emissary.stats.level} · <LightningIcon size={10} className="text-cyan" />{emissary.stats.energy_current}
                </p>
              </div>
            </div>
            <button
              onClick={onSelectEmissary}
              className="btn small secondary"
            >
              CHANGE
            </button>
          </div>
        </motion.div>
      ) : (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="data-box mb-4"
        >
          <div className="text-center py-2">
            <p className="text-amber-dim text-sm mb-2">No emissary selected</p>
            <button onClick={onSelectEmissary} className="btn small">
              SELECT EMISSARY
            </button>
          </div>
        </motion.div>
      )}

      {/* Difficulty filter */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.1 }}
        className="flex gap-2 mb-4 overflow-x-auto"
      >
        {['ALL', 'EASY', 'MEDIUM', 'HARD', 'LEGENDARY'].map((diff) => (
          <button
            key={diff}
            onClick={() => setFilter(diff)}
            className={`tab ${filter === diff ? 'active' : ''}`}
          >
            {diff}
          </button>
        ))}
      </motion.div>

      {/* Loading state */}
      {isLoading && (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <MapIcon size={48} className="text-amber animate-pulse mx-auto mb-2" />
            <p className="text-amber-dim text-sm">Loading missions...</p>
          </div>
        </div>
      )}

      {/* Mission list */}
      {!isLoading && (
        <div className="flex-1 scroll-area space-y-2">
          {filteredMissions.map((mission, index) => {
            const diffStyle = DIFFICULTY_STYLES[mission.difficulty] || DIFFICULTY_STYLES.EASY;
            const hasEnergy = emissary && emissary.stats.energy_current >= mission.energy_cost;
            const canStart = emissary && hasEnergy && emissary.current_state === 'READY';

            return (
              <motion.div
                key={mission.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.02 * index }}
              >
                <button
                  onClick={() => canStart && onSelectMission(mission)}
                  disabled={!canStart}
                  className={`data-box w-full text-left ${!canStart ? 'opacity-60' : ''}`}
                >
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <h3 className="text-amber-bright font-semibold text-sm">
                        {mission.name}
                      </h3>
                      <span className={`text-xs ${diffStyle.color}`}>
                        {diffStyle.label}
                      </span>
                    </div>
                    {mission.party_size && (
                      <span className="text-xs text-cyan flex items-center gap-1">
                        <UsersIcon size={12} className="text-cyan" /> {mission.party_size}
                      </span>
                    )}
                  </div>

                  <p className="text-xs text-amber-dim mb-2 line-clamp-2">
                    {mission.description}
                  </p>

                  <div className="divider" />

                  <div className="grid grid-cols-4 gap-2 text-xs mt-2">
                    <div>
                      <span className="text-amber-darker">Duration</span>
                      <p className="text-amber">{formatDuration(mission.duration_hours)}</p>
                    </div>
                    <div>
                      <span className="text-amber-darker">Energy</span>
                      <p className={`flex items-center gap-0.5 ${hasEnergy ? 'text-amber' : 'text-red'}`}>
                        <LightningIcon size={10} className={hasEnergy ? 'text-cyan' : 'text-red'} />{mission.energy_cost}
                      </p>
                    </div>
                    <div>
                      <span className="text-amber-darker">XP</span>
                      <p className="text-amber">+{mission.reward_xp}</p>
                    </div>
                    <div>
                      <span className="text-amber-darker">Death</span>
                      <p className={mission.death_chance > 0 ? 'text-red' : 'text-green'}>
                        {mission.death_chance}%
                      </p>
                    </div>
                  </div>

                  {mission.favored_guild && (
                    <p className="text-xs text-cyan mt-2">
                      Favored: {mission.favored_guild}
                    </p>
                  )}
                </button>
              </motion.div>
            );
          })}

          {filteredMissions.length === 0 && (
            <div className="text-center text-amber-dim py-8">
              No missions found for this difficulty.
            </div>
          )}
        </div>
      )}

      {/* Back button */}
      <button onClick={onBack} className="back-btn">
        ← BACK
      </button>
    </div>
  );
}
