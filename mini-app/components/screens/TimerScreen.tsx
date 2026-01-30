'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Emissary, ActiveMicroMission, completeMicroMission } from '@/lib/api';

/**
 * TimerScreen - Active mission countdown timer
 * Shows emissary, mission name, and countdown
 * COMPLETE button appears when timer reaches zero
 */

interface TimerScreenProps {
  emissary: Emissary;
  activeMission: ActiveMicroMission;
  wallet: string;
  onComplete: (rewards: { ember: number; xp: number; aura: number }) => void;
  onBack: () => void;
}

export function TimerScreen({
  emissary,
  activeMission,
  wallet,
  onComplete,
  onBack,
}: TimerScreenProps) {
  const [timeRemaining, setTimeRemaining] = useState(activeMission.remaining_seconds);
  const [isCompleting, setIsCompleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Timer countdown
  useEffect(() => {
    if (timeRemaining <= 0) return;

    const interval = setInterval(() => {
      setTimeRemaining((prev) => {
        if (prev <= 1) {
          clearInterval(interval);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  // Format time
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // Calculate progress percentage
  const totalDuration = activeMission.remaining_seconds +
    (Date.now() - new Date(activeMission.started_at).getTime()) / 1000;
  const progress = Math.max(0, (1 - timeRemaining / totalDuration) * 100);

  // Handle complete
  const handleComplete = async () => {
    try {
      setIsCompleting(true);
      setError(null);
      const result = await completeMicroMission(wallet, activeMission.active_id);
      onComplete(result.rewards);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to complete mission');
      setIsCompleting(false);
    }
  };

  const isReady = timeRemaining <= 0;

  return (
    <div className="screen-view flex flex-col min-h-screen p-4">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-6"
      >
        <h2 className="title text-xl">ACTIVE MISSION</h2>
        <p className="text-amber-dim text-xs">{activeMission.name}</p>
      </motion.div>

      {/* Emissary info */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.1 }}
        className="data-box mb-6"
      >
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 border-2 border-amber bg-bg-dark flex items-center justify-center overflow-hidden">
            {emissary.image_url ? (
              <img
                src={emissary.image_url}
                alt={emissary.name}
                className="w-full h-full object-cover"
                style={{ imageRendering: 'pixelated' }}
              />
            ) : (
              <span className="text-3xl">⚔️</span>
            )}
          </div>
          <div>
            <p className="text-amber-bright font-semibold">
              {emissary.name || `Emissary #${emissary.token_id}`}
            </p>
            <p className="text-xs text-amber-dim">
              {emissary.race_class} · {emissary.guild}
            </p>
            <p className="text-xs text-cyan mt-1">
              ON MICRO-MISSION
            </p>
          </div>
        </div>
      </motion.div>

      {/* Timer display */}
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.2 }}
        className="flex-1 flex items-center justify-center"
      >
        <div className="portal-box w-full max-w-xs">
          <div className="ornament">═══ ◈ ═══</div>

          {!isReady ? (
            <>
              <div className="my-8">
                <motion.div
                  animate={{
                    opacity: [1, 0.5, 1],
                    scale: [1, 1.05, 1],
                  }}
                  transition={{
                    duration: 2,
                    repeat: Infinity,
                    ease: "easeInOut",
                  }}
                  className="text-5xl font-mono text-amber-bright"
                >
                  {formatTime(timeRemaining)}
                </motion.div>
                <p className="text-amber-dim text-sm mt-2">Time Remaining</p>
              </div>

              {/* Progress bar */}
              <div className="progress-bar mx-4 mb-4">
                <motion.div
                  className="progress-bar-fill"
                  initial={{ width: `${progress}%` }}
                  animate={{ width: `${Math.min(progress + 1, 100)}%` }}
                  transition={{ duration: 1, ease: 'linear' }}
                />
              </div>

              <p className="text-amber-darker text-xs">
                Mission in progress...
              </p>
            </>
          ) : (
            <>
              <div className="text-5xl my-6">✨</div>
              <p className="text-green font-semibold text-lg mb-2">
                MISSION COMPLETE
              </p>
              <p className="text-amber-dim text-sm mb-4">
                Claim your rewards!
              </p>
            </>
          )}

          <div className="ornament mt-4">═══ ◈ ═══</div>
        </div>
      </motion.div>

      {/* Choice made indicator */}
      {activeMission.choice_made && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="data-box mb-4"
        >
          <p className="text-xs text-amber-dim">
            Choice made: <span className="text-amber">{activeMission.choice_made}</span>
          </p>
        </motion.div>
      )}

      {/* Error message */}
      {error && (
        <div className="text-center text-red text-sm mb-4">
          {error}
        </div>
      )}

      {/* Action button */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        {isReady ? (
          <button
            onClick={handleComplete}
            disabled={isCompleting}
            className={`btn w-full ${isCompleting ? 'opacity-60' : ''}`}
          >
            {isCompleting ? 'COMPLETING...' : 'CLAIM REWARDS'}
          </button>
        ) : (
          <button onClick={onBack} className="back-btn">
            ← BACK (Mission continues)
          </button>
        )}
      </motion.div>
    </div>
  );
}
