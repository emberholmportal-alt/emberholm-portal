'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Image from 'next/image';

/**
 * WelcomeScreen - Initial splash screen
 * Shows logo with random lore phrases and "Enter Portal" button
 * Matches portal web design exactly
 */

const LORE_PHRASES = [
  "The Eternal Flame awaits...",
  "Emissaries rise from the ashes...",
  "In the Era of the Flame, legends are forged...",
  "The Void stirs in the shadows...",
  "Six guilds. One destiny.",
  "Ember burns eternal...",
  "The Order of Dawn calls...",
  "Whispers from the Circle of Mist...",
];

interface WelcomeScreenProps {
  onEnter: () => void;
}

export function WelcomeScreen({ onEnter }: WelcomeScreenProps) {
  const [phrase, setPhrase] = useState(LORE_PHRASES[0]);
  const [fadeKey, setFadeKey] = useState(0);

  // Check for skip intro in localStorage
  useEffect(() => {
    const skipIntro = localStorage.getItem('emberholm_skip_intro');
    if (skipIntro === 'true') {
      // Optionally skip directly to next screen
      // For now, still show but could add skip logic
    }
  }, []);

  useEffect(() => {
    // Rotate phrases every 3 seconds
    const interval = setInterval(() => {
      const randomIndex = Math.floor(Math.random() * LORE_PHRASES.length);
      setPhrase(LORE_PHRASES[randomIndex]);
      setFadeKey(prev => prev + 1);
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  const handleEnter = () => {
    // Set skip intro for future visits
    localStorage.setItem('emberholm_skip_intro', 'true');
    onEnter();
  };

  return (
    <div className="screen-view flex flex-col items-center justify-center min-h-screen p-6">
      {/* Portal Box */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.8 }}
        className="portal-box"
      >
        {/* Top Ornament */}
        <div className="ornament">═══ ◈ ═══</div>

        {/* Logo */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.6 }}
          className="my-6"
        >
          <Image
            src="/logo.png"
            alt="Emberholm"
            width={200}
            height={80}
            className="mx-auto"
            priority
          />
        </motion.div>

        {/* Subtitle */}
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 0.6 }}
          transition={{ delay: 0.5 }}
          className="text-amber text-sm tracking-widest uppercase mb-4"
        >
          MINI APP
        </motion.p>

        {/* Rotating lore phrase */}
        <div className="h-16 flex items-center justify-center my-4">
          <AnimatePresence mode="wait">
            <motion.p
              key={fadeKey}
              initial={{ opacity: 0 }}
              animate={{ opacity: 0.7 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.5 }}
              className="text-amber-dim text-sm italic text-center px-4"
            >
              "{phrase}"
            </motion.p>
          </AnimatePresence>
        </div>

        {/* Bottom Ornament */}
        <div className="ornament">═══ ◈ ═══</div>
      </motion.div>

      {/* Enter button */}
      <motion.button
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.8, duration: 0.5 }}
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        onClick={handleEnter}
        className="btn mt-8 px-8"
      >
        [ ENTER THE PORTAL ]
      </motion.button>

      {/* Version */}
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 0.4 }}
        transition={{ delay: 1.2 }}
        className="absolute bottom-6 text-xs text-amber-dim"
      >
        v2.0.0 · Era of the Flame
      </motion.p>
    </div>
  );
}
