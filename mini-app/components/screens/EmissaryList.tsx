'use client';

import { motion } from 'framer-motion';
import { Emissary } from '@/lib/api';

/**
 * EmissaryList - Shows all user's emissaries
 * Each card shows status and quick actions
 */

interface EmissaryListProps {
  emissaries: Emissary[];
  onSelect: (emissary: Emissary) => void;
  onBack: () => void;
  isLoading?: boolean;
}

const STATE_COLORS: Record<string, string> = {
  READY: 'text-green-500',
  ON_MISSION: 'text-blue-400',
  ON_MICRO_MISSION: 'text-purple-400',
  FALLEN: 'text-red-500',
  CLAIMING: 'text-yellow-400',
};

const STATE_LABELS: Record<string, string> = {
  READY: '● Ready',
  ON_MISSION: '◐ On Mission',
  ON_MICRO_MISSION: '◐ Micro-Mission',
  FALLEN: '✖ Fallen',
  CLAIMING: '◉ Claiming',
};

export function EmissaryList({
  emissaries,
  onSelect,
  onBack,
  isLoading,
}: EmissaryListProps) {
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
          YOUR EMISSARIES
        </h1>
        <span className="text-ember-400/50 text-sm">
          {emissaries.length} total
        </span>
      </div>

      {/* Loading state */}
      {isLoading && (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="text-3xl animate-pulse mb-2">🔥</div>
            <p className="text-ember-400/60">Loading emissaries...</p>
          </div>
        </div>
      )}

      {/* Empty state */}
      {!isLoading && emissaries.length === 0 && (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center p-6">
            <div className="text-4xl mb-4">⚔️</div>
            <h3 className="text-ember-400 font-semibold mb-2">No Emissaries Found</h3>
            <p className="text-ember-400/60 text-sm mb-4">
              Mint your first Emissary at the main portal
            </p>
            <a
              href="https://emberholmportal.xyz/mint"
              target="_blank"
              rel="noopener noreferrer"
              className="btn-ember px-4 py-2 inline-block"
            >
              Mint Emissary
            </a>
          </div>
        </div>
      )}

      {/* Emissary cards */}
      {!isLoading && emissaries.length > 0 && (
        <div className="flex-1 space-y-3 pb-4">
          {emissaries.map((emissary, index) => (
            <motion.div
              key={emissary.token_id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.05 * index }}
            >
              <button
                onClick={() => onSelect(emissary)}
                disabled={emissary.current_state === 'FALLEN'}
                className="w-full card-emissary text-left disabled:opacity-60"
              >
                <div className="flex gap-3">
                  {/* Avatar placeholder */}
                  <div className="w-16 h-16 bg-void-lighter rounded border border-ember-400/20 flex items-center justify-center text-2xl">
                    ⚔️
                  </div>

                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <h3 className="font-pixel text-ember-400 truncate">
                        {emissary.name || `Emissary #${emissary.token_id}`}
                      </h3>
                      <span className="text-xs text-ember-400/50">
                        #{emissary.token_id}
                      </span>
                    </div>

                    <p className="text-xs text-ember-400/60 truncate">
                      {emissary.race_class} · {emissary.guild}
                    </p>

                    {/* Stats row */}
                    <div className="flex items-center gap-3 mt-1 text-xs">
                      <span className="text-ember-400/70">
                        LVL {emissary.stats.level}
                      </span>
                      <span className="text-ember-400/50">·</span>
                      <span className="text-ember-400/70">
                        ⚡ {emissary.stats.energy_current}/{emissary.stats.energy_max}
                      </span>
                      <span className="text-ember-400/50">·</span>
                      <span className="text-ember-400/70">
                        ✧ {emissary.stats.aura_level}
                      </span>
                    </div>

                    {/* State badge */}
                    <div className="mt-2">
                      <span className={`text-xs ${STATE_COLORS[emissary.current_state] || 'text-ember-400/50'}`}>
                        {STATE_LABELS[emissary.current_state] || emissary.current_state}
                      </span>
                    </div>
                  </div>

                  {/* Arrow */}
                  <div className="flex items-center">
                    <span className="text-ember-400/30">›</span>
                  </div>
                </div>
              </button>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
