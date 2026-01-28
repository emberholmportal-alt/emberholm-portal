'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

/**
 * PortalEntry - Portal confirmation screen
 * "The Portal pulses with unstable energy..."
 * Final confirmation before entering main menu
 */

interface PortalEntryProps {
  onEnter: () => void;
  onBack?: () => void;
}

export function PortalEntry({ onEnter, onBack }: PortalEntryProps) {
  const [isEntering, setIsEntering] = useState(false);
  const [loadingText, setLoadingText] = useState('');
  const [showGlitch, setShowGlitch] = useState(false);

  // Glitch effect
  useEffect(() => {
    const glitchInterval = setInterval(() => {
      setShowGlitch(true);
      setTimeout(() => setShowGlitch(false), 100);
    }, 3000 + Math.random() * 2000);

    return () => clearInterval(glitchInterval);
  }, []);

  const handleEnter = () => {
    setIsEntering(true);

    // Loading sequence
    const loadingSteps = [
      "ACCESSING",
      "ACCESSING.",
      "ACCESSING..",
      "ACCESSING...",
      "ACCESSING EMBERHOLM",
      "ACCESSING EMBERHOLM.",
      "ACCESSING EMBERHOLM..",
      "ACCESSING EMBERHOLM...",
      "PORTAL STABLE",
      "ENTERING REALM",
    ];

    let step = 0;
    const interval = setInterval(() => {
      if (step < loadingSteps.length) {
        setLoadingText(loadingSteps[step]);
        step++;
      } else {
        clearInterval(interval);
        setTimeout(onEnter, 300);
      }
    }, 200);
  };

  return (
    <div className="screen-view flex flex-col min-h-screen p-4">
      {/* Main content */}
      <div className="flex-1 flex items-center justify-center">
        <AnimatePresence mode="wait">
          {!isEntering ? (
            <motion.div
              key="portal-box"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 1.1 }}
              className={`portal-box ${showGlitch ? 'glitch' : ''}`}
            >
              {/* Top Ornament */}
              <div className="ornament">═══ ◈ ═══</div>

              {/* Portal message */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.3 }}
                className="my-6 space-y-2"
              >
                <p className="text-amber text-sm">
                  The Portal pulses with
                </p>
                <p className="text-amber text-sm">
                  unstable energy.
                </p>
              </motion.div>

              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.5 }}
                className="my-4 space-y-1"
              >
                <p className="text-amber-dim text-xs">
                  Glitches ripple through
                </p>
                <p className="text-amber-dim text-xs">
                  the veil.
                </p>
              </motion.div>

              <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.7 }}
                className="text-amber-bright text-lg font-semibold my-6"
              >
                Still wish to proceed?
              </motion.p>

              {/* Bottom Ornament */}
              <div className="ornament">═══ ◈ ═══</div>
            </motion.div>
          ) : (
            <motion.div
              key="loading"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-center"
            >
              {/* Loading animation */}
              <div className="portal-box">
                <div className="ornament">═══ ◈ ═══</div>

                <motion.div
                  animate={{
                    opacity: [0.5, 1, 0.5],
                    scale: [1, 1.02, 1],
                  }}
                  transition={{
                    duration: 1,
                    repeat: Infinity,
                    ease: "easeInOut",
                  }}
                  className="my-8"
                >
                  <p className="text-amber-bright text-lg font-semibold tracking-wider">
                    {loadingText}
                  </p>
                </motion.div>

                {/* Loading bar */}
                <div className="w-full h-1 bg-amber-darker overflow-hidden my-4">
                  <motion.div
                    className="h-full bg-amber"
                    initial={{ width: 0 }}
                    animate={{ width: '100%' }}
                    transition={{ duration: 2, ease: "easeInOut" }}
                  />
                </div>

                <div className="ornament">═══ ◈ ═══</div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Enter button */}
      {!isEntering && (
        <motion.button
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.9 }}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={handleEnter}
          className="btn w-full mb-4"
        >
          [ ENTER THE PORTAL ]
        </motion.button>
      )}
    </div>
  );
}
