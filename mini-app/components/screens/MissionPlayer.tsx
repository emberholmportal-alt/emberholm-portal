'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
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
 * Shows narrative with typewriter, choices, timer, and results
 * Uses $PYRE rewards
 */

type MissionPhase = 'starting' | 'narrative' | 'choosing' | 'waiting' | 'completing' | 'complete';

interface MissionPlayerProps {
  mission: MicroMission;
  emissary: Emissary;
  wallet: string;
  onComplete: (rewards: { pyre: number; xp: number; aura: number }) => void;
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
  const [displayedText, setDisplayedText] = useState('');
  const [choices, setChoices] = useState<{ id: string; text: string; icon?: string }[]>([]);
  const [selectedChoice, setSelectedChoice] = useState<string | null>(null);
  const [outcomeText, setOutcomeText] = useState('');
  const [rewards, setRewards] = useState<{ pyre: number; xp: number; aura: number } | null>(null);
  const [timeRemaining, setTimeRemaining] = useState(mission.duration_seconds);
  const [error, setError] = useState<string | null>(null);
  const typewriterRef = useRef<NodeJS.Timeout | null>(null);

  // Typewriter effect for narrative
  useEffect(() => {
    if (phase !== 'narrative' || !narrativeText) return;

    let i = 0;
    setDisplayedText('');

    const typeChar = () => {
      if (i < narrativeText.length) {
        setDisplayedText(prev => prev + narrativeText.charAt(i));
        i++;
        const speed = 25 + Math.random() * 25; // 25-50ms per character
        typewriterRef.current = setTimeout(typeChar, speed);
      }
    };

    typeChar();

    return () => {
      if (typewriterRef.current) clearTimeout(typewriterRef.current);
    };
  }, [phase, narrativeText]);

  // Skip typewriter on tap
  const skipTypewriter = () => {
    if (typewriterRef.current) {
      clearTimeout(typewriterRef.current);
      setDisplayedText(narrativeText);
    }
  };

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
      <div className="screen-view flex flex-col min-h-screen p-4">
        <div className="flex-1 flex items-center justify-center">
          <div className="portal-box">
            <div className="ornament">═══ ◈ ═══</div>
            <div className="text-4xl my-4">❌</div>
            <h3 className="text-red font-semibold mb-2">Mission Failed</h3>
            <p className="text-amber-dim text-sm mb-4">{error}</p>
            <div className="ornament">═══ ◈ ═══</div>
          </div>
        </div>
        <button onClick={onCancel} className="back-btn">
          ← RETURN
        </button>
      </div>
    );
  }

  return (
    <div className="screen-view flex flex-col min-h-screen p-4">
      {/* Header with timer */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="title text-lg">{mission.name}</h2>
          <p className="text-xs text-amber-dim">
            {emissary.name || `Emissary #${emissary.token_id}`}
          </p>
        </div>
        <div className="text-right">
          <div className="text-2xl font-mono text-amber-bright animate-pulse-glow">
            {formatTime(timeRemaining)}
          </div>
          <p className="text-xs text-amber-dim">remaining</p>
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
              <div className="portal-box">
                <div className="ornament">═══ ◈ ═══</div>
                <div className="text-4xl animate-pulse my-6">🔥</div>
                <p className="text-amber-dim">Initiating mission...</p>
                <div className="ornament mt-4">═══ ◈ ═══</div>
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
              <div
                className="data-box mb-6 cursor-pointer"
                onClick={skipTypewriter}
              >
                <p className="text-amber leading-relaxed whitespace-pre-line">
                  {displayedText}
                  {displayedText.length < narrativeText.length && (
                    <span className="inline-block w-2 h-4 bg-amber animate-blink ml-1" />
                  )}
                </p>
              </div>

              {displayedText.length === narrativeText.length && choices.length > 0 && (
                <>
                  <p className="text-center text-amber-dim text-sm mb-4">
                    What do you do?
                  </p>

                  <div className="space-y-3">
                    {choices.map((choice, index) => (
                      <motion.button
                        key={choice.id}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.1 * index }}
                        onClick={() => handleChoice(choice.id)}
                        className="menu-btn w-full"
                      >
                        <span className="icon text-lg">{choice.id}</span>
                        <span className="flex-1 text-left text-sm">
                          {choice.text}
                        </span>
                      </motion.button>
                    ))}
                  </div>
                </>
              )}
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
              <div className="data-box mb-6">
                <p className="text-amber-dim text-sm mb-2">
                  Your choice: <span className="text-amber">{selectedChoice}</span>
                </p>
                {outcomeText && (
                  <p className="text-amber leading-relaxed mt-4">
                    {outcomeText}
                  </p>
                )}
              </div>

              <div className="portal-box">
                <div className="ornament">═══ ◈ ═══</div>
                <div className="text-4xl animate-pulse my-6">⏳</div>
                <p className="text-amber-dim">
                  {phase === 'choosing' ? 'Recording choice...' : 'Awaiting outcome...'}
                </p>
                <div className="ornament mt-4">═══ ◈ ═══</div>
              </div>
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
              <div className="portal-box">
                <div className="ornament">═══ ◈ ═══</div>
                <div className="text-4xl animate-pulse my-6">✨</div>
                <p className="text-amber-dim">Calculating rewards...</p>
                <div className="ornament mt-4">═══ ◈ ═══</div>
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
              <h3 className="title text-2xl mb-4">
                MISSION COMPLETE
              </h3>

              {outcomeText && (
                <div className="data-box mb-6 text-left">
                  <p className="text-amber text-sm leading-relaxed">
                    {outcomeText}
                  </p>
                </div>
              )}

              <div className="data-box mb-6">
                <div className="section-title">REWARDS EARNED</div>
                <div className="flex justify-center gap-8 mt-4">
                  <div className="text-center">
                    <p className="text-2xl text-cyan font-bold">+{rewards.pyre}</p>
                    <p className="text-xs text-amber-dim">◈ PYRE</p>
                  </div>
                  {rewards.xp > 0 && (
                    <div className="text-center">
                      <p className="text-2xl text-amber font-bold">+{rewards.xp}</p>
                      <p className="text-xs text-amber-dim">XP</p>
                    </div>
                  )}
                  {rewards.aura > 0 && (
                    <div className="text-center">
                      <p className="text-2xl text-amber-bright font-bold">+{rewards.aura}</p>
                      <p className="text-xs text-amber-dim">AURA</p>
                    </div>
                  )}
                </div>
              </div>

              <button
                onClick={() => onComplete(rewards)}
                className="btn w-full"
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
