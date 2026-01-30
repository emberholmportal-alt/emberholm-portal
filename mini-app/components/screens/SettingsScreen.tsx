'use client';

import { motion } from 'framer-motion';
import { useWallpaper, WallpaperSettings } from '@/lib/WallpaperContext';
import { useSoundContext } from '@/lib/SoundContext';

/**
 * SettingsScreen - Configuration for wallpaper effects and audio
 */

interface SettingsScreenProps {
  onBack: () => void;
}

// Toggle Switch Component
function ToggleSwitch({
  enabled,
  onChange,
}: {
  enabled: boolean;
  onChange: (value: boolean) => void;
}) {
  return (
    <button
      onClick={() => onChange(!enabled)}
      className={`toggle-switch ${enabled ? 'active' : ''}`}
      style={{
        width: '44px',
        height: '24px',
        background: enabled ? '#ff9500' : '#0a0705',
        border: `2px solid ${enabled ? '#ff9500' : '#804d00'}`,
        borderRadius: '12px',
        position: 'relative',
        cursor: 'pointer',
        transition: 'all 0.2s',
      }}
    >
      <span
        style={{
          position: 'absolute',
          width: '16px',
          height: '16px',
          background: enabled ? '#0a0705' : '#cc7700',
          borderRadius: '50%',
          top: '2px',
          left: enabled ? '22px' : '2px',
          transition: 'all 0.2s',
        }}
      />
    </button>
  );
}

// Slider Component
function Slider({
  value,
  min,
  max,
  onChange,
  disabled,
}: {
  value: number;
  min: number;
  max: number;
  onChange: (value: number) => void;
  disabled?: boolean;
}) {
  return (
    <input
      type="range"
      min={min}
      max={max}
      value={value}
      onChange={(e) => onChange(parseInt(e.target.value))}
      disabled={disabled}
      className="settings-slider"
      style={{
        width: '100px',
        height: '6px',
        background: '#0a0705',
        border: '1px solid #804d00',
        borderRadius: '3px',
        outline: 'none',
        opacity: disabled ? 0.4 : 1,
        cursor: disabled ? 'not-allowed' : 'pointer',
        accentColor: '#ff9500',
      }}
    />
  );
}

// Setting Row Component
function SettingRow({
  label,
  enabled,
  onToggle,
  sliderValue,
  sliderMin,
  sliderMax,
  onSliderChange,
}: {
  label: string;
  enabled: boolean;
  onToggle: () => void;
  sliderValue?: number;
  sliderMin?: number;
  sliderMax?: number;
  onSliderChange?: (value: number) => void;
}) {
  return (
    <div className="flex items-center justify-between py-2">
      <div className="flex items-center gap-3">
        <ToggleSwitch enabled={enabled} onChange={onToggle} />
        <span className={`text-sm ${enabled ? 'text-amber' : 'text-amber-dim'}`}>
          {label}
        </span>
      </div>
      {sliderValue !== undefined && onSliderChange && (
        <Slider
          value={sliderValue}
          min={sliderMin || 0}
          max={sliderMax || 100}
          onChange={onSliderChange}
          disabled={!enabled}
        />
      )}
    </div>
  );
}

export function SettingsScreen({ onBack }: SettingsScreenProps) {
  const {
    settings,
    updateSetting,
    toggleSetting,
    resetToDefaults,
  } = useWallpaper();

  const soundContext = useSoundContext();

  return (
    <div className="screen-view flex flex-col min-h-screen">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="p-4 text-center"
      >
        <h1 className="title text-2xl flex items-center justify-center gap-2">
          <span>⚙️</span> SETTINGS
        </h1>
        <p className="subtitle">Customize your experience</p>
      </motion.div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {/* Wallpaper Effects Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <div className="data-box">
            <div className="section-title text-xs text-amber-dark uppercase tracking-wider mb-4">
              WALLPAPER EFFECTS
            </div>

            <div className="space-y-1">
              <SettingRow
                label="Gradient Pulse"
                enabled={settings.gradientEnabled}
                onToggle={() => toggleSetting('gradientEnabled')}
              />

              <SettingRow
                label="Dot Grid"
                enabled={settings.dotGridEnabled}
                onToggle={() => toggleSetting('dotGridEnabled')}
                sliderValue={settings.dotGridOpacity}
                sliderMin={10}
                sliderMax={60}
                onSliderChange={(v) => updateSetting('dotGridOpacity', v)}
              />

              <SettingRow
                label="Moving Lines"
                enabled={settings.movingLinesEnabled}
                onToggle={() => toggleSetting('movingLinesEnabled')}
              />

              <SettingRow
                label="Noise"
                enabled={settings.noiseEnabled}
                onToggle={() => toggleSetting('noiseEnabled')}
              />

              <SettingRow
                label="Ghost Code"
                enabled={settings.ghostCodeEnabled}
                onToggle={() => toggleSetting('ghostCodeEnabled')}
                sliderValue={settings.ghostCodeOpacity}
                sliderMin={5}
                sliderMax={30}
                onSliderChange={(v) => updateSetting('ghostCodeOpacity', v)}
              />

              <SettingRow
                label="Data Stream"
                enabled={settings.dataStreamEnabled}
                onToggle={() => toggleSetting('dataStreamEnabled')}
                sliderValue={settings.dataStreamOpacity}
                sliderMin={5}
                sliderMax={25}
                onSliderChange={(v) => updateSetting('dataStreamOpacity', v)}
              />

              <SettingRow
                label="Glitch Lines"
                enabled={settings.glitchEnabled}
                onToggle={() => toggleSetting('glitchEnabled')}
              />

              <SettingRow
                label="Scanlines"
                enabled={settings.scanlinesEnabled}
                onToggle={() => toggleSetting('scanlinesEnabled')}
              />

              <SettingRow
                label="Vignette"
                enabled={settings.vignetteEnabled}
                onToggle={() => toggleSetting('vignetteEnabled')}
              />

              <SettingRow
                label="CRT Flicker"
                enabled={settings.flickerEnabled}
                onToggle={() => toggleSetting('flickerEnabled')}
              />
            </div>
          </div>
        </motion.div>

        {/* Audio Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <div className="data-box">
            <div className="section-title text-xs text-amber-dark uppercase tracking-wider mb-4">
              AUDIO
            </div>

            <div className="space-y-1">
              <div className="flex items-center justify-between py-2">
                <div className="flex items-center gap-3">
                  <ToggleSwitch
                    enabled={soundContext.soundEnabled}
                    onChange={() => soundContext.toggleSound()}
                  />
                  <span className={`text-sm ${soundContext.soundEnabled ? 'text-amber' : 'text-amber-dim'}`}>
                    Sound Effects
                  </span>
                </div>
              </div>

              <div className="flex items-center justify-between py-2">
                <div className="flex items-center gap-3">
                  <ToggleSwitch
                    enabled={soundContext.musicEnabled}
                    onChange={() => soundContext.toggleMusic()}
                  />
                  <span className={`text-sm ${soundContext.musicEnabled ? 'text-amber' : 'text-amber-dim'}`}>
                    Music
                  </span>
                </div>
                <Slider
                  value={Math.round(soundContext.musicVolume * 100)}
                  min={0}
                  max={100}
                  onChange={(v) => soundContext.setMusicVolume(v / 100)}
                  disabled={!soundContext.musicEnabled}
                />
              </div>
            </div>
          </div>
        </motion.div>

        {/* Reset Button */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="pt-4"
        >
          <button
            onClick={resetToDefaults}
            className="w-full py-3 border border-amber-dark/50 text-amber-dim text-sm
                     hover:border-amber hover:text-amber transition-colors rounded"
          >
            [ RESET TO DEFAULTS ]
          </button>
        </motion.div>
      </div>

      {/* Back button */}
      <div className="p-4">
        <button onClick={onBack} className="back-btn">
          ← BACK TO MENU
        </button>
      </div>
    </div>
  );
}

export default SettingsScreen;
