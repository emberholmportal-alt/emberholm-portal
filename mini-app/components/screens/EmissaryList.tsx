'use client';

import { motion } from 'framer-motion';
import { Emissary } from '@/lib/api';

/**
 * EmissaryList - Shows all user's emissaries
 * Displays: Image, name, level, guild, state
 * States: READY, ON_MISSION, ON_MICRO_MISSION, FALLEN
 */

interface EmissaryListProps {
  emissaries: Emissary[];
  onSelect: (emissary: Emissary) => void;
  onBack: () => void;
  isLoading?: boolean;
}

const STATE_STYLES: Record<string, { color: string; label: string; icon: string }> = {
  READY: { color: 'text-green', label: 'IDLE', icon: '●' },
  ON_MISSION: { color: 'text-cyan', label: 'ON MISSION', icon: '◐' },
  ON_MICRO_MISSION: { color: 'text-amber-bright', label: 'MICRO-MISSION', icon: '◐' },
  FALLEN: { color: 'text-red', label: 'DEAD', icon: '✖' },
  CLAIMING: { color: 'text-amber', label: 'CLAIMING', icon: '◉' },
};

export function EmissaryList({
  emissaries,
  onSelect,
  onBack,
  isLoading,
}: EmissaryListProps) {
  return (
    <div className="screen-view flex flex-col min-h-screen p-4">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-4"
      >
        <h2 className="title text-xl">YOUR EMISSARIES</h2>
        <p className="text-amber-dim text-xs">{emissaries.length} owned</p>
      </motion.div>

      {/* Loading state */}
      {isLoading && (
        <div className="flex-1 flex items-center justify-center">
          <div className="portal-box">
            <div className="ornament">═══ ◈ ═══</div>
            <div className="text-3xl animate-pulse my-6">🔥</div>
            <p className="text-amber-dim text-sm">Loading emissaries...</p>
            <div className="ornament mt-4">═══ ◈ ═══</div>
          </div>
        </div>
      )}

      {/* Empty state */}
      {!isLoading && emissaries.length === 0 && (
        <div className="flex-1 flex items-center justify-center">
          <div className="portal-box">
            <div className="ornament">═══ ◈ ═══</div>
            <div className="text-4xl my-4">⚔️</div>
            <h3 className="text-amber-bright font-semibold mb-2">No Emissaries Found</h3>
            <p className="text-amber-dim text-sm mb-4">
              Mint your first Emissary to begin
            </p>
            <div className="ornament">═══ ◈ ═══</div>
          </div>
        </div>
      )}

      {/* Emissary cards */}
      {!isLoading && emissaries.length > 0 && (
        <div className="flex-1 scroll-area space-y-2">
          {emissaries.map((emissary, index) => {
            const stateStyle = STATE_STYLES[emissary.current_state] || STATE_STYLES.READY;
            const isFallen = emissary.current_state === 'FALLEN';
            const isBusy = emissary.current_state === 'ON_MISSION' ||
                          emissary.current_state === 'ON_MICRO_MISSION';

            return (
              <motion.div
                key={emissary.token_id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.03 * index }}
              >
                <button
                  onClick={() => onSelect(emissary)}
                  disabled={isFallen}
                  className={`emissary-card w-full text-left ${isFallen ? 'opacity-60' : ''}`}
                >
                  <div className="emissary-header">
                    <span className="emissary-name">
                      {emissary.name || `Emissary #${emissary.token_id}`}
                    </span>
                    <span className={`emissary-status ${stateStyle.color}`}>
                      {stateStyle.icon} {stateStyle.label}
                    </span>
                  </div>

                  <div className="flex gap-3">
                    {/* Avatar */}
                    <div className="w-16 h-16 border border-amber-dark bg-bg-dark flex items-center justify-center overflow-hidden">
                      {emissary.image_url ? (
                        <img
                          src={emissary.image_url}
                          alt={emissary.name}
                          className="w-full h-full object-cover"
                          style={{ imageRendering: 'pixelated' }}
                        />
                      ) : (
                        <span className="text-2xl">⚔️</span>
                      )}
                    </div>

                    {/* Info */}
                    <div className="flex-1 min-w-0">
                      <p className="text-xs text-amber-dim truncate">
                        {emissary.race_class} · {emissary.guild}
                      </p>

                      {/* Stats row */}
                      <div className="data-row text-xs mt-2">
                        <span>LVL {emissary.stats.level}</span>
                        <span>⚡ {emissary.stats.energy_current}/{emissary.stats.energy_max}</span>
                        <span>✧ {emissary.stats.aura_level}</span>
                        <span>⚔ {emissary.stats.power}</span>
                      </div>

                      {/* Active mission indicator */}
                      {isBusy && (
                        <div className="mt-2 text-xs text-amber animate-pulse">
                          In progress...
                        </div>
                      )}
                    </div>

                    {/* Arrow */}
                    <div className="flex items-center">
                      <span className="text-amber-dark">›</span>
                    </div>
                  </div>
                </button>
              </motion.div>
            );
          })}
        </div>
      )}

      {/* Back button */}
      <button onClick={onBack} className="back-btn">
        ← BACK
      </button>
    </div>
  );
}
