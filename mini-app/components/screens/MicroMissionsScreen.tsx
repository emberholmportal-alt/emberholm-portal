'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Emissary, MicroMission, getMicroMissions } from '@/lib/api';

/**
 * MicroMissionsScreen - Micro-missions list
 * Quick 1-5 minute adventures for $PYRE rewards
 * Filter by difficulty: EASY, MEDIUM, HARD, LEGENDARY
 */

interface MicroMissionsScreenProps {
  emissary: Emissary | null;
  onSelectMission: (mission: MicroMission) => void;
  onSelectEmissary: () => void;
  onBack: () => void;
}

const DIFFICULTY_STYLES: Record<string, { color: string; label: string; bg: string }> = {
  EASY: { color: 'text-green', label: 'EASY', bg: 'bg-green/10' },
  MEDIUM: { color: 'text-amber', label: 'MEDIUM', bg: 'bg-amber/10' },
  HARD: { color: 'text-red', label: 'HARD', bg: 'bg-red/10' },
  LEGENDARY: { color: 'text-cyan', label: 'LEGENDARY', bg: 'bg-cyan/10' },
};

export function MicroMissionsScreen({
  emissary,
  onSelectMission,
  onSelectEmissary,
  onBack,
}: MicroMissionsScreenProps) {
  const [missions, setMissions] = useState<MicroMission[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState<string>('ALL');
  const [error, setError] = useState<string | null>(null);

  // Load micro-missions from API
  useEffect(() => {
    async function loadMissions() {
      try {
        setIsLoading(true);
        setError(null);
        const data = await getMicroMissions();
        setMissions(data);
      } catch (err) {
        console.error('Failed to load micro-missions:', err);
        setError('Failed to load missions');
      } finally {
        setIsLoading(false);
      }
    }

    loadMissions();
  }, []);

  // Filter missions by difficulty
  const filteredMissions = filter === 'ALL'
    ? missions
    : missions.filter(m => m.difficulty === filter);

  // Format duration
  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`;
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return secs > 0 ? `${mins}m ${secs}s` : `${mins}m`;
  };

  return (
    <div className="screen-view flex flex-col min-h-screen p-4">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-4"
      >
        <h2 className="title text-xl">MICRO-MISSIONS</h2>
        <p className="text-amber-dim text-xs">Quick adventures for ◈ PYRE</p>
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
                  <span>⚔️</span>
                )}
              </div>
              <div>
                <p className="text-amber text-sm font-semibold">
                  {emissary.name || `#${emissary.token_id}`}
                </p>
                <p className="text-xs text-amber-dim">
                  LVL {emissary.stats.level} · ⚡{emissary.stats.energy_current}
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

      {/* Difficulty filter tabs */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.1 }}
        className="flex gap-2 mb-4 overflow-x-auto pb-1"
      >
        {['ALL', 'EASY', 'MEDIUM', 'HARD'].map((diff) => (
          <button
            key={diff}
            onClick={() => setFilter(diff)}
            className={`tab whitespace-nowrap ${filter === diff ? 'active' : ''}`}
          >
            {diff}
          </button>
        ))}
      </motion.div>

      {/* Loading state */}
      {isLoading && (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="text-3xl animate-pulse mb-2">⚡</div>
            <p className="text-amber-dim text-sm">Loading micro-missions...</p>
          </div>
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="flex-1 flex items-center justify-center">
          <div className="portal-box">
            <div className="ornament">═══ ◈ ═══</div>
            <div className="text-3xl my-4">❌</div>
            <p className="text-red text-sm">{error}</p>
            <div className="ornament mt-4">═══ ◈ ═══</div>
          </div>
        </div>
      )}

      {/* Mission list */}
      {!isLoading && !error && (
        <div className="flex-1 scroll-area space-y-3">
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
                  className={`data-box w-full text-left transition-all
                             ${canStart ? 'hover:border-amber' : 'opacity-60'}`}
                >
                  {/* Header row */}
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <h3 className="text-amber-bright font-semibold">
                        {mission.name}
                      </h3>
                      <div className="flex items-center gap-2 mt-1">
                        <span className={`text-xs px-2 py-0.5 ${diffStyle.color} ${diffStyle.bg}`}>
                          {diffStyle.label}
                        </span>
                        <span className="text-xs text-amber-dim">
                          {formatDuration(mission.duration_seconds)}
                        </span>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-cyan font-semibold">
                        +{mission.pyre_reward.min}-{mission.pyre_reward.max}
                      </p>
                      <p className="text-xs text-cyan">◈ PYRE</p>
                    </div>
                  </div>

                  {/* Description */}
                  <p className="text-xs text-amber-dim mb-3 line-clamp-2">
                    {mission.description}
                  </p>

                  <div className="divider" />

                  {/* Stats row */}
                  <div className="flex justify-between items-center text-xs mt-2">
                    <div className="flex gap-4">
                      <span className={hasEnergy ? 'text-amber' : 'text-red'}>
                        ⚡ {mission.energy_cost} Energy
                      </span>
                      <span className="text-amber-dim">
                        +{mission.xp_reward.min}-{mission.xp_reward.max} XP
                      </span>
                    </div>
                    <span className="text-amber-dim">
                      {mission.aura_chance}% Aura
                    </span>
                  </div>

                  {/* Cooldown warning if applicable */}
                  {mission.cooldown_minutes > 0 && (
                    <p className="text-xs text-amber-darker mt-2">
                      ⏱️ {mission.cooldown_minutes}min cooldown after completion
                    </p>
                  )}
                </button>
              </motion.div>
            );
          })}

          {filteredMissions.length === 0 && (
            <div className="text-center text-amber-dim py-8">
              No micro-missions found for this difficulty.
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
