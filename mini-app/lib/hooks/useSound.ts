/**
 * useSound Hook - Sound effects for Emberholm Mini App
 * Plays UI sounds with global toggle support
 */

import { useCallback, useRef, useEffect } from 'react';

// Sound file paths (these would be in /public/sounds/)
const SOUNDS = {
  click: '/sounds/click.mp3',
  success: '/sounds/success.mp3',
  error: '/sounds/error.mp3',
  notification: '/sounds/notification.mp3',
  levelUp: '/sounds/level-up.mp3',
  reward: '/sounds/reward.mp3',
  death: '/sounds/death.mp3',
};

type SoundName = keyof typeof SOUNDS;

interface UseSoundOptions {
  enabled?: boolean;
  volume?: number;
}

export function useSound(options: UseSoundOptions = {}) {
  const { enabled = true, volume = 0.5 } = options;
  const audioRefs = useRef<Map<SoundName, HTMLAudioElement>>(new Map());

  // Preload sounds
  useEffect(() => {
    if (typeof window === 'undefined') return;

    Object.entries(SOUNDS).forEach(([name, path]) => {
      try {
        const audio = new Audio(path);
        audio.preload = 'auto';
        audio.volume = volume;
        audioRefs.current.set(name as SoundName, audio);
      } catch (e) {
        // Sound file might not exist yet
        console.debug(`Sound not loaded: ${name}`);
      }
    });

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

  // Play a sound by name
  const play = useCallback(
    (soundName: SoundName) => {
      if (!enabled) return;

      const audio = audioRefs.current.get(soundName);
      if (audio) {
        // Reset to start if already playing
        audio.currentTime = 0;
        audio.play().catch(() => {
          // Autoplay might be blocked
        });
      }
    },
    [enabled]
  );

  // Convenience methods
  const playClick = useCallback(() => play('click'), [play]);
  const playSuccess = useCallback(() => play('success'), [play]);
  const playError = useCallback(() => play('error'), [play]);
  const playNotification = useCallback(() => play('notification'), [play]);
  const playLevelUp = useCallback(() => play('levelUp'), [play]);
  const playReward = useCallback(() => play('reward'), [play]);
  const playDeath = useCallback(() => play('death'), [play]);

  return {
    play,
    playClick,
    playSuccess,
    playError,
    playNotification,
    playLevelUp,
    playReward,
    playDeath,
  };
}

// Hook that uses global store for sound enabled state
export function useAppSound() {
  // This would connect to the global store's soundEnabled state
  // For now, we'll use a simple implementation
  const enabled = typeof window !== 'undefined'
    ? localStorage.getItem('emberholm_sound') !== 'false'
    : true;

  return useSound({ enabled });
}

export default useSound;
