'use client';

import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  MicroMission,
  Emissary,
  startMicroMission,
  submitMicroMissionChoice,
  completeMicroMission,
  getMicroMissionDetail,
} from '@/lib/api';

/**
 * MissionPlayer - Interactive micro-mission experience
 * Shows narrative, choices, timer, and results
 */

type MissionPhase = 'starting' | 'narrative' | 'choosing' | 'waiting' | 'completing' | 'complete';

interface MissionPlayerProps {
  mission: MicroMission;
  emissary: Emissary;
  wallet: string;
  onComplete: (rewards: { spark: number; xp: number; aura: number }) => void;
  onCancel: () => void;
}

export function MissionPlayer({
  mission,
  emissary,
  wallet,
  onComplete,
  onCancel,
}: MissionPlayerProps) {
  const [phase, setPhase] = useState<MissionPhase>('starting');
  const [activeMissionId, setActiveMissionId] = useState<number | null>(null);
  const [narrativeText, setNarrativeText] = useState('');
  const [choices, setChoices] = useState<{ id: string; text: string; icon?: string }[]>([]);
  const [selectedChoice, setSelectedChoice] = useState<string | null>(null);
  const [outcomeText, setOutcomeText] = useState('');
  const [rewards, setRewards] = useState<{ spark: number; xp: number; aura: number } | null>(null);
  const [timeRemaining, setTimeRemaining] = useState(mission.duration_seconds);
  const [error, setError] = useState<string | null>(null);

  // Start the mission
  useEffect(() => {
    async function start() {
      try {
        setPhase('starting');

        // Get full mission details
        const detail = await getMicroMissionDetail(mission.id);

        // Start the mission
        const result = await startMicroMission(wallet, emissary.token_id, mission.id);

        setActiveMissionId(result.active_micro_mission_id);
        setNarrativeText(detail.narrative_intro || mission.narrative_intro);
        setChoices(detail.narrative_choices || []);

        // Calculate time remaining
        const endsAt = new Date(result.ends_at);
        const now = new Date();
        const remaining = Math.max(0, Math.floor((endsAt.getTime() - now.getTime()) / 1000));
        setTimeRemaining(remaining);

        setPhase('narrative');
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to start mission');
      }
    }

    start();
  }, [mission, emissary, wallet]);

  // Timer countdown
  useEffect(() => {
    if (phase !== 'narrative' && phase !== 'choosing' && phase !== 'waiting') return;

    const interval = setInterval(() => {
      setTimeRemaining((prev) => {
        if (prev <= 1) {
          clearInterval(interval);
          if (phase === 'waiting') {
            setPhase('completing');
          }
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [phase]);

  // Handle choice selection
  const handleChoice = useCallback(async (choiceId: string) => {
    if (!activeMissionId) return;

    try {
      setSelectedChoice(choiceId);
      setPhase('choosing');

      const result = await submitMicroMissionChoice(wallet, activeMissionId, choiceId);
      setOutcomeText(result.outcome_preview);
      setPhase('waiting');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit choice');
    }
  }, [wallet, activeMissionId]);

  // Complete mission when timer ends
  useEffect(() => {
    if (phase !== 'completing' || !activeMissionId) return;

    async function complete() {
      try {
        const result = await completeMicroMission(wallet, activeMissionId!);
        setRewards(result.rewards);
        setOutcomeText(result.outcome_text);
        setPhase('complete');
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to complete mission');
      }
    }

    complete();
  }, [phase, activeMissionId, wallet]);

  // Format time
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Error state
  if (error) {
    return (
      <div className="flex flex-col min-h-screen p-4 pt-12 items-center justify-center">
        <div className="text-center">
          <div className="text-4xl mb-4">❌</div>
          <h3 className="text-red-400 font-semibold mb-2">Mission Failed</h3>
          <p className="text-ember-400/60 text-sm mb-4">{error}</p>
          <button onClick={onCancel} className="btn-ember">
            Return
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col min-h-screen p-4 pt-12">
      {/* Header with timer */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="font-alagard text-lg text-ember-400 text-glow">
            {mission.name}
          </h2>
          <p className="text-xs text-ember-400/60">
            {emissary.name || `Emissary #${emissary.token_id}`}
          </p>
        </div>
        <div className="text-right">
          <div className="text-2xl font-mono text-ember-400 text-glow">
            {formatTime(timeRemaining)}
          </div>
          <p className="text-xs text-ember-400/50">remaining</p>
        </div>
      </div>

      {/* Progress bar */}
      <div className="progress-bar mb-6">
        <motion.div
          className="progress-bar-fill"
          initial={{ width: '100%' }}
          animate={{ width: `${(timeRemaining / mission.duration_seconds) * 100}%` }}
          transition={{ duration: 1, ease: 'linear' }}
        />
      </div>

      {/* Content area */}
      <div className="flex-1">
        <AnimatePresence mode="wait">
          {/* Starting phase */}
          {phase === 'starting' && (
            <motion.div
              key="starting"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex items-center justify-center h-full"
            >
              <div className="text-center">
                <div className="text-4xl animate-pulse mb-4">🔥</div>
                <p className="text-ember-400/70">Initiating mission...</p>
              </div>
            </motion.div>
          )}

          {/* Narrative phase */}
          {phase === 'narrative' && (
            <motion.div
              key="narrative"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
            >
              <div className="panel-glow p-4 mb-6">
                <p className="text-ember-400/90 leading-relaxed whitespace-pre-line">
                  {narrativeText}
                </p>
              </div>

              <p className="text-center text-ember-400/60 text-sm mb-4">
                What do you do?
              </p>

              <div className="space-y-3">
                {choices.map((choice) => (
                  <motion.button
                    key={choice.id}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => handleChoice(choice.id)}
                    className="w-full panel p-4 text-left hover:border-ember-400/50 hover:shadow-ember"
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-xl w-8 h-8 flex items-center justify-center bg-ember-400/10 rounded">
                        {choice.id}
                      </span>
                      <span className="text-ember-400/90 text-sm flex-1">
                        {choice.text}
                      </span>
                    </div>
                  </motion.button>
                ))}
              </div>
            </motion.div>
          )}

          {/* Waiting phase */}
          {(phase === 'choosing' || phase === 'waiting') && (
            <motion.div
              key="waiting"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="text-center"
            >
              <div className="panel-glow p-4 mb-6">
                <p className="text-ember-400/70 text-sm mb-2">
                  Your choice: <span className="text-ember-400">{selectedChoice}</span>
                </p>
                {outcomeText && (
                  <p className="text-ember-400/90 leading-relaxed">
                    {outcomeText}
                  </p>
                )}
              </div>

              <div className="text-4xl animate-pulse mb-4">⏳</div>
              <p className="text-ember-400/60">
                {phase === 'choosing' ? 'Recording choice...' : 'Awaiting outcome...'}
              </p>
            </motion.div>
          )}

          {/* Completing phase */}
          {phase === 'completing' && (
            <motion.div
              key="completing"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex items-center justify-center h-full"
            >
              <div className="text-center">
                <div className="text-4xl animate-pulse mb-4">✨</div>
                <p className="text-ember-400/70">Calculating rewards...</p>
              </div>
            </motion.div>
          )}

          {/* Complete phase */}
          {phase === 'complete' && rewards && (
            <motion.div
              key="complete"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="text-center"
            >
              <div className="text-5xl mb-4">🎉</div>
              <h3 className="font-alagard text-2xl text-ember-400 text-glow mb-4">
                MISSION COMPLETE
              </h3>

              {outcomeText && (
                <div className="panel-glow p-4 mb-6 text-left">
                  <p className="text-ember-400/90 text-sm leading-relaxed">
                    {outcomeText}
                  </p>
                </div>
              )}

              <div className="panel p-4 mb-6">
                <h4 className="text-ember-400/60 text-xs mb-3 uppercase tracking-wider">
                  Rewards Earned
                </h4>
                <div className="flex justify-center gap-6">
                  <div className="text-center">
                    <p className="text-2xl text-spark font-bold">+{rewards.spark}</p>
                    <p className="text-xs text-ember-400/50">$SPARK</p>
                  </div>
                  {rewards.xp > 0 && (
                    <div className="text-center">
                      <p className="text-2xl text-blue-400 font-bold">+{rewards.xp}</p>
                      <p className="text-xs text-ember-400/50">XP</p>
                    </div>
                  )}
                  {rewards.aura > 0 && (
                    <div className="text-center">
                      <p className="text-2xl text-purple-400 font-bold">+{rewards.aura}</p>
                      <p className="text-xs text-ember-400/50">AURA</p>
                    </div>
                  )}
                </div>
              </div>

              <button
                onClick={() => onComplete(rewards)}
                className="btn-ember-primary px-8 py-3"
              >
                CONTINUE
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
