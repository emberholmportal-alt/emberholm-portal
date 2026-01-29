'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import Image from 'next/image';
import { Emissary } from '@/lib/api';

/**
 * MissionsScreen - Normal missions list
 * Uses portal web endpoints for regular long-duration missions
 */

interface Mission {
  id: string;
  name: string;
  difficulty: 'EASY' | 'MEDIUM' | 'HARD';
  duration_hours: number;
  energy_cost: number;
  reward_xp: number;
  reward_aura: number;
  reward_ember_min?: number;
  reward_ember_max?: number;
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

  // Static missions data as fallback (from missions_config.json)
  const STATIC_MISSIONS: Mission[] = [
    { id: '001', name: 'The Lost Forge', difficulty: 'EASY', duration_hours: 3, energy_cost: 10, reward_xp: 60, reward_aura: 4, reward_ember_min: 10, reward_ember_max: 50, success_rate: 92, death_chance: 0, favored_guild: 'Forge Legion', description: 'Ancient forges rumble beneath the mountains. Reclaim lost smithing knowledge from the depths.' },
    { id: '002', name: 'Circle Interference Node', difficulty: 'EASY', duration_hours: 3, energy_cost: 10, reward_xp: 60, reward_aura: 4, reward_ember_min: 10, reward_ember_max: 50, success_rate: 92, death_chance: 0, favored_guild: 'Circle of Mist', description: 'Arcane nodes malfunction across the realm. Stabilize the magical interference before it spreads.' },
    { id: '003', name: 'Dawn Patrol', difficulty: 'EASY', duration_hours: 3, energy_cost: 10, reward_xp: 60, reward_aura: 4, reward_ember_min: 10, reward_ember_max: 50, success_rate: 92, death_chance: 0, favored_guild: 'Order of Dawn', description: 'Patrol the eastern borders as the sun rises. Defend settlements from nocturnal threats.', party_size: 5 },
    { id: '004', name: 'Shadow Infiltration', difficulty: 'MEDIUM', duration_hours: 6, energy_cost: 18, reward_xp: 150, reward_aura: 10, reward_ember_min: 25, reward_ember_max: 100, success_rate: 78, death_chance: 0.5, favored_guild: 'Shadow Guild', description: 'Infiltrate enemy strongholds under cover of darkness. Gather intelligence without being detected.' },
    { id: '005', name: 'Horizon Survey', difficulty: 'MEDIUM', duration_hours: 6, energy_cost: 18, reward_xp: 150, reward_aura: 10, reward_ember_min: 25, reward_ember_max: 100, success_rate: 78, death_chance: 0.5, favored_guild: 'Horizon Watch', description: 'Scout the uncharted territories beyond the known world. Map new routes and discover hidden dangers.' },
    { id: '006', name: 'Veil Breach Containment', difficulty: 'MEDIUM', duration_hours: 6, energy_cost: 18, reward_xp: 150, reward_aura: 10, reward_ember_min: 25, reward_ember_max: 100, success_rate: 78, death_chance: 0.5, favored_guild: 'Void Echoes', description: 'Reality tears open. Seal the breach before void entities pour through into our realm.', party_size: 5 },
    { id: '007', name: 'Dragons Crucible', difficulty: 'HARD', duration_hours: 12, energy_cost: 25, reward_xp: 350, reward_aura: 25, reward_ember_min: 50, reward_ember_max: 250, success_rate: 60, death_chance: 2.0, favored_guild: 'Forge Legion', description: 'Face the ancient dragon that guards the legendary forge. Only the strongest survive.' },
    { id: '008', name: 'Void Descent', difficulty: 'HARD', duration_hours: 12, energy_cost: 25, reward_xp: 350, reward_aura: 25, reward_ember_min: 50, reward_ember_max: 250, success_rate: 60, death_chance: 2.0, favored_guild: 'Void Echoes', description: 'Descend into the Void itself. Confront entities that should not exist. Few return unchanged.' },
    { id: '009', name: 'Eclipse Ritual', difficulty: 'HARD', duration_hours: 12, energy_cost: 25, reward_xp: 350, reward_aura: 25, reward_ember_min: 50, reward_ember_max: 250, success_rate: 60, death_chance: 2.0, favored_guild: 'Circle of Mist', description: 'Harness the power of a total eclipse. The ritual is dangerous, but the rewards transcendent.', party_size: 5 },
  ];

  // Load missions from portal API with static fallback
  useEffect(() => {
    async function loadMissions() {
      try {
        setIsLoading(true);
        const response = await fetch(`${API_BASE}/api/missions`);
        if (response.ok) {
          const data = await response.json();
          const loadedMissions = data.missions || [];
          // Only use API data if we got missions, otherwise use static
          setMissions(loadedMissions.length > 0 ? loadedMissions : STATIC_MISSIONS);
        } else {
          // API not available, use static data
          setMissions(STATIC_MISSIONS);
        }
      } catch (error) {
        console.error('Failed to load missions, using static data:', error);
        setMissions(STATIC_MISSIONS);
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
                  <Image src="/icons/Swords.png" alt="" width={24} height={24} className="pixel-icon" />
                )}
              </div>
              <div>
                <p className="text-amber text-sm font-semibold">
                  {emissary.name || `#${emissary.token_id}`}
                </p>
                <p className="text-xs text-amber-dim flex items-center gap-1">
                  LVL {emissary.stats.level} ·
                  <Image src="/icons/Lightning.png" alt="" width={12} height={12} className="pixel-icon inline" />
                  {emissary.stats.energy_current}
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
        {['ALL', 'EASY', 'MEDIUM', 'HARD'].map((diff) => (
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
            <Image
              src="/icons/map.gif"
              alt=""
              width={32}
              height={32}
              className="pixel-icon mx-auto animate-pulse mb-2"
            />
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
                      <span className="text-xs text-cyan">
                        👥 {mission.party_size}
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
                      <p className={`flex items-center gap-1 ${hasEnergy ? 'text-amber' : 'text-red'}`}>
                        <Image src="/icons/Lightning.png" alt="" width={12} height={12} className="pixel-icon" />
                        {mission.energy_cost}
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
