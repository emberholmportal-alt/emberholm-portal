'use client';

import { motion } from 'framer-motion';
import { Emissary } from '@/lib/api';
import { AppScreen } from '@/lib/store';

/**
 * EmissaryDetail - Full emissary detail view
 * Stats, equipment, chronicle, and action buttons
 */

interface EmissaryDetailProps {
  emissary: Emissary;
  onNavigate: (screen: AppScreen) => void;
  onBack: () => void;
}

const STATE_STYLES: Record<string, { color: string; label: string; canAct: boolean }> = {
  READY: { color: 'text-green', label: 'IDLE - Ready for action', canAct: true },
  ON_MISSION: { color: 'text-cyan', label: 'ON MISSION', canAct: false },
  ON_MICRO_MISSION: { color: 'text-amber-bright', label: 'ON MICRO-MISSION', canAct: false },
  FALLEN: { color: 'text-red', label: 'DEAD - Cannot participate', canAct: false },
  CLAIMING: { color: 'text-amber', label: 'CLAIMING REWARDS', canAct: false },
};

const EQUIPMENT_SLOTS = ['weapon', 'armor', 'accessory', 'rune1', 'rune2', 'rune3'];

export function EmissaryDetail({
  emissary,
  onNavigate,
  onBack,
}: EmissaryDetailProps) {
  const stateStyle = STATE_STYLES[emissary.current_state] || STATE_STYLES.READY;
  const canStartMission = stateStyle.canAct && emissary.stats.energy_current >= 10;

  // Calculate XP progress to next level
  const xpForNextLevel = emissary.stats.level * 100;
  const xpProgress = Math.min((emissary.stats.xp_total % xpForNextLevel) / xpForNextLevel * 100, 100);

  return (
    <div className="screen-view flex flex-col min-h-screen p-4">
      {/* Header with image */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex gap-4 mb-4"
      >
        {/* Avatar */}
        <div className="w-24 h-24 border-2 border-amber bg-bg-dark flex items-center justify-center overflow-hidden">
          {emissary.image_url ? (
            <img
              src={emissary.image_url}
              alt={emissary.name}
              className="w-full h-full object-cover"
              style={{ imageRendering: 'pixelated' }}
            />
          ) : (
            <span className="text-4xl">⚔️</span>
          )}
        </div>

        {/* Basic info */}
        <div className="flex-1">
          <h2 className="title text-lg mb-1">
            {emissary.name || `Emissary #${emissary.token_id}`}
          </h2>
          <p className="text-xs text-amber-dim mb-1">
            {emissary.race_class}
          </p>
          <p className="text-xs text-amber-dim mb-2">
            {emissary.guild}
          </p>
          <span className={`text-xs ${stateStyle.color}`}>
            {stateStyle.label}
          </span>
        </div>
      </motion.div>

      {/* Stats section */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.1 }}
        className="data-box mb-4"
      >
        <div className="section-title">STATS</div>

        {/* Level and XP */}
        <div className="data-row">
          <span>Level</span>
          <span className="text-amber-bright">{emissary.stats.level}</span>
        </div>
        <div className="mb-2">
          <div className="flex justify-between text-xs text-amber-dim mb-1">
            <span>XP Progress</span>
            <span>{emissary.stats.xp_total} / {xpForNextLevel}</span>
          </div>
          <div className="progress-bar">
            <div className="progress-bar-fill" style={{ width: `${xpProgress}%` }} />
          </div>
        </div>

        <div className="divider" />

        {/* Core stats */}
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div className="data-row">
            <span>⚡ Energy</span>
            <span>{emissary.stats.energy_current}/{emissary.stats.energy_max}</span>
          </div>
          <div className="data-row">
            <span>⚔ Power</span>
            <span>{emissary.stats.power}</span>
          </div>
          <div className="data-row">
            <span>✧ Aura</span>
            <span>{emissary.stats.aura_level}</span>
          </div>
          <div className="data-row">
            <span>💀 Deaths</span>
            <span>{emissary.stats.death_count}</span>
          </div>
        </div>
      </motion.div>

      {/* Equipment section */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="data-box mb-4"
      >
        <div className="section-title">EQUIPMENT</div>
        <div className="grid grid-cols-3 gap-2">
          {EQUIPMENT_SLOTS.map((slot) => {
            const item = emissary.equipment?.[slot];
            const isRune = slot.startsWith('rune');
            return (
              <div
                key={slot}
                className="border border-amber-dark p-2 text-center bg-bg-dark"
              >
                <div className="text-xs text-amber-darker uppercase mb-1">
                  {isRune ? slot.replace('rune', 'Rune ') : slot}
                </div>
                {item ? (
                  <span className="text-xs text-amber">{item}</span>
                ) : (
                  <span className="text-xs text-amber-darker">Empty</span>
                )}
              </div>
            );
          })}
        </div>
      </motion.div>

      {/* Chronicle section */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
        className="data-box mb-4"
      >
        <div className="section-title">CHRONICLE</div>
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div className="data-row">
            <span>Missions</span>
            <span>{emissary.chronicle.total_missions}</span>
          </div>
          <div className="data-row">
            <span>Deaths</span>
            <span>{emissary.chronicle.total_deaths}</span>
          </div>
          <div className="data-row">
            <span>Items Found</span>
            <span>{emissary.chronicle.items_found}</span>
          </div>
          <div className="data-row">
            <span>Runes Found</span>
            <span>{emissary.chronicle.runes_found}</span>
          </div>
        </div>
      </motion.div>

      {/* Action buttons */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="space-y-2 mt-auto"
      >
        {emissary.current_state === 'ON_MISSION' && (
          <button
            onClick={() => onNavigate('timer')}
            className="btn w-full"
          >
            VIEW ACTIVE MISSION
          </button>
        )}

        {emissary.current_state === 'ON_MICRO_MISSION' && (
          <button
            onClick={() => onNavigate('timer')}
            className="btn w-full"
          >
            VIEW MICRO-MISSION
          </button>
        )}

        {canStartMission && (
          <>
            <button
              onClick={() => onNavigate('missions')}
              className="btn w-full"
            >
              START MISSION
            </button>
            <button
              onClick={() => onNavigate('micro-missions')}
              className="btn secondary w-full"
            >
              START MICRO-MISSION
            </button>
          </>
        )}

        {emissary.current_state === 'FALLEN' && (
          <div className="text-center text-red text-sm p-4">
            This Emissary has fallen and cannot participate in missions.
          </div>
        )}

        {!canStartMission && stateStyle.canAct && emissary.stats.energy_current < 10 && (
          <div className="text-center text-amber-dim text-sm p-2">
            Not enough energy. Wait for regeneration.
          </div>
        )}
      </motion.div>

      {/* Back button */}
      <button onClick={onBack} className="back-btn">
        ← BACK
      </button>
    </div>
  );
}
