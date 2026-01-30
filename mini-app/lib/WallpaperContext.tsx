'use client';

import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';

/**
 * WallpaperContext - Configuration for Living Terminal Wallpaper
 * Manages all animated background layers with localStorage persistence
 */

export interface WallpaperSettings {
  gradientEnabled: boolean;
  dotGridEnabled: boolean;
  dotGridOpacity: number; // 10-60
  movingLinesEnabled: boolean;
  noiseEnabled: boolean;
  ghostCodeEnabled: boolean;
  ghostCodeOpacity: number; // 5-30
  dataStreamEnabled: boolean;
  dataStreamOpacity: number; // 5-25
  glitchEnabled: boolean;
  scanlinesEnabled: boolean;
  vignetteEnabled: boolean;
  flickerEnabled: boolean;
}

export const DEFAULT_SETTINGS: WallpaperSettings = {
  gradientEnabled: true,
  dotGridEnabled: true,
  dotGridOpacity: 50,
  movingLinesEnabled: true,
  noiseEnabled: true,
  ghostCodeEnabled: true,
  ghostCodeOpacity: 15,
  dataStreamEnabled: true,
  dataStreamOpacity: 12,
  glitchEnabled: true,
  scanlinesEnabled: true,
  vignetteEnabled: true,
  flickerEnabled: true,
};

const STORAGE_KEY = 'emberholm_wallpaper_settings';

interface WallpaperContextType {
  settings: WallpaperSettings;
  updateSetting: <K extends keyof WallpaperSettings>(key: K, value: WallpaperSettings[K]) => void;
  toggleSetting: (key: keyof WallpaperSettings) => void;
  resetToDefaults: () => void;
  isVisible: boolean;
  setIsVisible: (visible: boolean) => void;
}

const WallpaperContext = createContext<WallpaperContextType | null>(null);

interface WallpaperProviderProps {
  children: ReactNode;
}

export function WallpaperProvider({ children }: WallpaperProviderProps) {
  const [settings, setSettings] = useState<WallpaperSettings>(DEFAULT_SETTINGS);
  const [isVisible, setIsVisible] = useState(true);
  const [isLoaded, setIsLoaded] = useState(false);

  // Load settings from localStorage on mount
  useEffect(() => {
    if (typeof window === 'undefined') return;

    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        // Merge with defaults to handle any new settings
        setSettings({ ...DEFAULT_SETTINGS, ...parsed });
      }
    } catch (e) {
      console.debug('Error loading wallpaper settings:', e);
    }
    setIsLoaded(true);
  }, []);

  // Save settings to localStorage whenever they change
  useEffect(() => {
    if (!isLoaded || typeof window === 'undefined') return;

    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
    } catch (e) {
      console.debug('Error saving wallpaper settings:', e);
    }
  }, [settings, isLoaded]);

  // Pause animations when app is in background
  useEffect(() => {
    if (typeof window === 'undefined') return;

    const handleVisibilityChange = () => {
      setIsVisible(!document.hidden);
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, []);

  const updateSetting = useCallback(<K extends keyof WallpaperSettings>(
    key: K,
    value: WallpaperSettings[K]
  ) => {
    setSettings(prev => ({ ...prev, [key]: value }));
  }, []);

  const toggleSetting = useCallback((key: keyof WallpaperSettings) => {
    setSettings(prev => {
      const currentValue = prev[key];
      if (typeof currentValue === 'boolean') {
        return { ...prev, [key]: !currentValue };
      }
      return prev;
    });
  }, []);

  const resetToDefaults = useCallback(() => {
    setSettings(DEFAULT_SETTINGS);
  }, []);

  return (
    <WallpaperContext.Provider
      value={{
        settings,
        updateSetting,
        toggleSetting,
        resetToDefaults,
        isVisible,
        setIsVisible,
      }}
    >
      {children}
    </WallpaperContext.Provider>
  );
}

export function useWallpaper() {
  const context = useContext(WallpaperContext);
  if (!context) {
    throw new Error('useWallpaper must be used within a WallpaperProvider');
  }
  return context;
}

// Optional hook that doesn't throw if outside provider
export function useWallpaperOptional() {
  return useContext(WallpaperContext);
}

export default WallpaperProvider;
