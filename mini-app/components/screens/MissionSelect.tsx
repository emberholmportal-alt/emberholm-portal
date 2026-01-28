'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { getMicroMissions, MicroMission, Emissary } from '@/lib/api';

/**
 * MissionSelect - Choose a micro-mission to start
 */

interface MissionSelectProps {
  selectedEmissary: Emissary | null;
  onSelectMission: (mission: MicroMission) => void;
  onBack: () => void;
  onSelectEmissary: () => void;
}

const DIFFICULTY_COLORS: Record<string, string> = {
  EASY: 'text-green-500 border-green-500/30',
  MEDIUM: 'text-yellow-500 border-yellow-500/30',
  HARD: 'text-red-500 border-red-500/30',
};

const DIFFICULTY_BG: Record<string, string> = {
  EASY: 'bg-green-500/10',
  MEDIUM: 'bg-yellow-500/10',
  HARD: 'bg-red-500/10',
};

export function MissionSelect({
  selectedEmissary,
  onSelectMission,
  onBack,
  onSelectEmissary,
}: MissionSelectProps) {
  const [missions, setMissions] = useState<MicroMission[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadMissions() {
      try {
        setIsLoading(true);
        const data = await getMicroMissions();
        setMissions(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load missions');
      } finally {
        setIsLoading(false);
      }
    }
    loadMissions();
  }, []);

  const canStartMission = selectedEmissary?.current_state === 'READY';

  return (
    <div className="flex flex-col min-h-screen p-4 pt-12">
      {/* Header */}
      <div className="flex items-center gap-3 mb-4">
        <button
          onClick={onBack}
          className="text-ember-400/70 hover:text-ember-400"
        >
          ← Back
        </button>
        <h1 className="font-alagard text-xl text-ember-400 text-glow flex-1">
          MICRO-MISSIONS
        </h1>
      </div>

      {/* Selected emissary banner */}
      <div className="panel p-3 mb-4">
        {selectedEmissary ? (
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-xl">⚔️</span>
              <div>
                <p className="text-ember-400 text-sm font-semibold">
                  {selectedEmissary.name || `Emissary #${selectedEmissary.token_id}`}
                </p>
                <p className="text-ember-400/60 text-xs">
                  {canStartMission ? (
                    <span className="text-green-500">● Ready for mission</span>
                  ) : (
                    <span className="text-yellow-500">⚠ {selectedEmissary.current_state}</span>
                  )}
                </p>
              </div>
            </div>
            <button
              onClick={onSelectEmissary}
              className="text-xs text-ember-400/70 underline"
            >
              Change
            </button>
          </div>
        ) : (
          <button
            onClick={onSelectEmissary}
            className="w-full text-center py-2 text-ember-400/70"
          >
            Select an Emissary first →
          </button>
        )}
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="text-3xl animate-pulse mb-2">🗺️</div>
            <p className="text-ember-400/60">Loading missions...</p>
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center text-red-400">
            <p>{error}</p>
          </div>
        </div>
      )}

      {/* Missions list */}
      {!isLoading && !error && (
        <div className="flex-1 space-y-3 pb-4">
          {missions.map((mission, index) => (
            <motion.div
              key={mission.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.05 * index }}
            >
              <button
                onClick={() => onSelectMission(mission)}
                disabled={!canStartMission}
                className={`w-full panel p-4 text-left transition-all
                           ${DIFFICULTY_BG[mission.difficulty]}
                           hover:border-ember-400/50 hover:shadow-ember
                           disabled:opacity-50 disabled:cursor-not-allowed`}
              >
                {/* Mission header */}
                <div className="flex items-start justify-between gap-2 mb-2">
                  <h3 className="font-pixel text-ember-400 font-semibold">
                    {mission.name}
                  </h3>
                  <span className={`text-xs px-2 py-0.5 border rounded ${DIFFICULTY_COLORS[mission.difficulty]}`}>
                    {mission.difficulty}
                  </span>
                </div>

                {/* Description */}
                <p className="text-xs text-ember-400/60 mb-3 line-clamp-2">
                  {mission.description}
                </p>

                {/* Stats */}
                <div className="flex flex-wrap gap-3 text-xs">
                  <span className="text-ember-400/70">
                    ⏱️ {Math.floor(mission.duration_seconds / 60)}:{(mission.duration_seconds % 60).toString().padStart(2, '0')}
                  </span>
                  {mission.energy_cost > 0 && (
                    <span className="text-ember-400/70">
                      ⚡ {mission.energy_cost}
                    </span>
                  )}
                  <span className="text-spark">
                    ◈ {mission.spark_reward.min}-{mission.spark_reward.max}
                  </span>
                  {mission.xp_reward.max > 0 && (
                    <span className="text-blue-400">
                      XP {mission.xp_reward.min}-{mission.xp_reward.max}
                    </span>
                  )}
                  {mission.aura_chance > 0 && (
                    <span className="text-purple-400">
                      ✧ {mission.aura_chance}%
                    </span>
                  )}
                </div>
              </button>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
