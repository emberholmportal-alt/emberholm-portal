/**
 * useSound Hook - Sound effects for Emberholm Mini App
 * Uses Web Audio API for beep sounds (like prototype v8)
 * Also supports mp3 files for more complex sounds
 */

import { useCallback, useRef, useEffect, useState } from 'react';

// Sound file paths (these would be in /public/sounds/)
const SOUNDS = {
  success: '/sounds/success.mp3',
  error: '/sounds/error.mp3',
  notification: '/sounds/notification.mp3',
  levelUp: '/sounds/level-up.mp3',
  reward: '/sounds/reward.mp3',
  death: '/sounds/death.mp3',
};

type SoundName = keyof typeof SOUNDS | 'click' | 'beep';

interface UseSoundOptions {
  enabled?: boolean;
  volume?: number;
}

// Global audio context (shared across hooks)
let globalAudioCtx: AudioContext | null = null;

function getAudioContext(): AudioContext | null {
  if (typeof window === 'undefined') return null;

  if (!globalAudioCtx) {
    try {
      globalAudioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
    } catch (e) {
      console.debug('Web Audio API not supported');
      return null;
    }
  }

  // Resume if suspended (browsers require user interaction)
  if (globalAudioCtx.state === 'suspended') {
    globalAudioCtx.resume();
  }

  return globalAudioCtx;
}

export function useSound(options: UseSoundOptions = {}) {
  const { enabled = true, volume = 0.5 } = options;
  const audioRefs = useRef<Map<string, HTMLAudioElement>>(new Map());
  const [isReady, setIsReady] = useState(false);

  // Preload mp3 sounds
  useEffect(() => {
    if (typeof window === 'undefined') return;

    Object.entries(SOUNDS).forEach(([name, path]) => {
      try {
        const audio = new Audio(path);
        audio.preload = 'auto';
        audio.volume = volume;
        audioRefs.current.set(name, audio);
      } catch (e) {
        // Sound file might not exist yet
      }
    });

    setIsReady(true);

    return () => {
      audioRefs.current.clear();
    };
  }, [volume]);

  // Update volume when it changes
  useEffect(() => {
    audioRefs.current.forEach(audio => {
      audio.volume = volume;
    });
  }, [volume]);

  /**
   * Play a beep sound using Web Audio API
   * Based on prototype v8 implementation
   */
  const playBeep = useCallback(
    (frequency: number = 800, duration: number = 0.05) => {
      if (!enabled) return;

      const audioCtx = getAudioContext();
      if (!audioCtx) return;

      try {
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();

        osc.connect(gain);
        gain.connect(audioCtx.destination);

        osc.frequency.value = frequency;
        osc.type = 'square';

        // Start at low volume and ramp down
        gain.gain.setValueAtTime(0.02 * volume, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01 * volume, audioCtx.currentTime + duration);

        osc.start(audioCtx.currentTime);
        osc.stop(audioCtx.currentTime + duration);
      } catch (e) {
        // Audio might be blocked
      }
    },
    [enabled, volume]
  );

  // Play a sound by name
  const play = useCallback(
    (soundName: SoundName) => {
      if (!enabled) return;

      // Use Web Audio API for click/beep sounds
      if (soundName === 'click' || soundName === 'beep') {
        playBeep(800, 0.05);
        return;
      }

      // Use mp3 for other sounds
      const audio = audioRefs.current.get(soundName);
      if (audio) {
        audio.currentTime = 0;
        audio.play().catch(() => {
          // Autoplay might be blocked
        });
      }
    },
    [enabled, playBeep]
  );

  // Convenience methods
  const playClick = useCallback(() => playBeep(800, 0.05), [playBeep]);
  const playSuccess = useCallback(() => {
    playBeep(1000, 0.1);
    setTimeout(() => playBeep(1200, 0.15), 100);
  }, [playBeep]);
  const playError = useCallback(() => playBeep(300, 0.2), [playBeep]);
  const playNotification = useCallback(() => {
    playBeep(600, 0.08);
    setTimeout(() => playBeep(800, 0.08), 100);
  }, [playBeep]);
  const playLevelUp = useCallback(() => {
    playBeep(400, 0.1);
    setTimeout(() => playBeep(600, 0.1), 100);
    setTimeout(() => playBeep(800, 0.1), 200);
    setTimeout(() => playBeep(1000, 0.2), 300);
  }, [playBeep]);
  const playReward = useCallback(() => {
    playBeep(800, 0.1);
    setTimeout(() => playBeep(1000, 0.15), 120);
  }, [playBeep]);
  const playDeath = useCallback(() => {
    playBeep(400, 0.2);
    setTimeout(() => playBeep(300, 0.3), 200);
    setTimeout(() => playBeep(200, 0.4), 450);
  }, [playBeep]);

  return {
    play,
    playClick,
    playBeep,
    playSuccess,
    playError,
    playNotification,
    playLevelUp,
    playReward,
    playDeath,
    isReady,
  };
}

// Hook that uses global store for sound enabled state
export function useAppSound() {
  const [enabled, setEnabled] = useState(true);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      setEnabled(localStorage.getItem('emberholm_sound') !== 'false');
    }
  }, []);

  return useSound({ enabled });
}

export default useSound;
