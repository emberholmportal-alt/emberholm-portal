'use client';

import { createContext, useContext, ReactNode, useCallback, useEffect, useState, useRef } from 'react';

/**
 * SoundContext - Global sound management for Emberholm Mini App
 * Provides click sounds for all buttons and UI interactions
 */

interface SoundContextType {
  playClick: () => void;
  playBeep: (frequency?: number, duration?: number) => void;
  playSuccess: () => void;
  playError: () => void;
  playNotification: () => void;
  playLevelUp: () => void;
  playReward: () => void;
  soundEnabled: boolean;
  musicEnabled: boolean;
  toggleSound: () => void;
  toggleMusic: () => void;
  musicVolume: number;
  setMusicVolume: (volume: number) => void;
}

const SoundContext = createContext<SoundContextType | null>(null);

// Global audio context
let globalAudioCtx: AudioContext | null = null;

function getAudioContext(): AudioContext | null {
  if (typeof window === 'undefined') return null;

  if (!globalAudioCtx) {
    try {
      globalAudioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
    } catch (e) {
      return null;
    }
  }

  if (globalAudioCtx.state === 'suspended') {
    globalAudioCtx.resume();
  }

  return globalAudioCtx;
}

interface SoundProviderProps {
  children: ReactNode;
}

export function SoundProvider({ children }: SoundProviderProps) {
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [musicEnabled, setMusicEnabled] = useState(true);
  const [musicVolume, setMusicVolume] = useState(0.5);
  const musicRef = useRef<HTMLAudioElement | null>(null);
  const currentTrackRef = useRef(0);

  // Music tracks
  const MUSIC_TRACKS = [
    '/music/track01.wav',
    '/music/track02.wav',
    '/music/track03.wav',
    '/music/track04.wav',
    '/music/track05.wav',
    '/music/track06.wav',
    '/music/track07.wav',
    '/music/track08.wav',
    '/music/track09.wav',
    '/music/track10.wav',
    '/music/track11.wav',
  ];

  // Load preferences from localStorage
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const savedSound = localStorage.getItem('emberholm_sound');
      const savedMusic = localStorage.getItem('emberholm_music');
      const savedVolume = localStorage.getItem('emberholm_music_volume');

      if (savedSound !== null) setSoundEnabled(savedSound !== 'false');
      if (savedMusic !== null) setMusicEnabled(savedMusic !== 'false');
      if (savedVolume !== null) setMusicVolume(parseFloat(savedVolume) || 0.5);
    }
  }, []);

  // Initialize music player
  useEffect(() => {
    if (typeof window === 'undefined') return;

    const audio = new Audio();
    audio.volume = musicVolume;
    audio.loop = false;
    musicRef.current = audio;

    // Play next track when current ends
    audio.addEventListener('ended', () => {
      currentTrackRef.current = (currentTrackRef.current + 1) % MUSIC_TRACKS.length;
      if (musicEnabled) {
        audio.src = MUSIC_TRACKS[currentTrackRef.current];
        audio.play().catch(() => {});
      }
    });

    return () => {
      audio.pause();
      audio.src = '';
    };
  }, []);

  // Handle music enable/disable
  useEffect(() => {
    if (!musicRef.current) return;

    if (musicEnabled) {
      musicRef.current.src = MUSIC_TRACKS[currentTrackRef.current];
      musicRef.current.play().catch(() => {
        // Autoplay blocked - will play on next user interaction
      });
    } else {
      musicRef.current.pause();
    }
  }, [musicEnabled]);

  // Update music volume
  useEffect(() => {
    if (musicRef.current) {
      musicRef.current.volume = musicVolume;
    }
  }, [musicVolume]);

  const playBeep = useCallback(
    (frequency: number = 800, duration: number = 0.05) => {
      if (!soundEnabled) return;

      const audioCtx = getAudioContext();
      if (!audioCtx) return;

      try {
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();

        osc.connect(gain);
        gain.connect(audioCtx.destination);

        osc.frequency.value = frequency;
        osc.type = 'square';

        gain.gain.setValueAtTime(0.02, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + duration);

        osc.start(audioCtx.currentTime);
        osc.stop(audioCtx.currentTime + duration);
      } catch (e) {}
    },
    [soundEnabled]
  );

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

  const toggleSound = useCallback(() => {
    setSoundEnabled(prev => {
      const newValue = !prev;
      localStorage.setItem('emberholm_sound', String(newValue));
      return newValue;
    });
  }, []);

  const toggleMusic = useCallback(() => {
    setMusicEnabled(prev => {
      const newValue = !prev;
      localStorage.setItem('emberholm_music', String(newValue));
      return newValue;
    });
  }, []);

  const handleSetMusicVolume = useCallback((volume: number) => {
    setMusicVolume(volume);
    localStorage.setItem('emberholm_music_volume', String(volume));
  }, []);

  return (
    <SoundContext.Provider
      value={{
        playClick,
        playBeep,
        playSuccess,
        playError,
        playNotification,
        playLevelUp,
        playReward,
        soundEnabled,
        musicEnabled,
        toggleSound,
        toggleMusic,
        musicVolume,
        setMusicVolume: handleSetMusicVolume,
      }}
    >
      {children}
    </SoundContext.Provider>
  );
}

export function useSoundContext() {
  const context = useContext(SoundContext);
  if (!context) {
    throw new Error('useSoundContext must be used within SoundProvider');
  }
  return context;
}

// Optional hook for components that may not be inside provider
export function useSoundContextOptional() {
  return useContext(SoundContext);
}
