'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { motion } from 'framer-motion';

/**
 * BootSequence - Welcome Operator typewriter screen
 * Shows terminal-style boot messages with typewriter effect
 */

interface BootSequenceProps {
  onComplete: () => void;
}

const WELCOME_TEXT = `════════════════════════════════════════
WELCOME, OPERATOR.
The Dying Flame grows weaker.
This terminal is your gateway to save Emberholm.
Summon Emissaries. Send them on missions.
Earn $EMBER. Rise in rank. Conquer lands.
Collect runes and legendary items to aid your quest.
But beware — death can be permanent.
════════════════════════════════════════`;

export function BootSequence({ onComplete }: BootSequenceProps) {
  const [phase, setPhase] = useState<'connecting' | 'welcome' | 'ready'>('connecting');
  const [displayedText, setDisplayedText] = useState('');
  const [showContinue, setShowContinue] = useState(false);
  const typewriterRef = useRef<NodeJS.Timeout | null>(null);

  // Typewriter effect
  const typeText = useCallback((text: string, speed: number, onDone: () => void) => {
    let i = 0;
    setDisplayedText('');

    const type = () => {
      if (i < text.length) {
        setDisplayedText(prev => prev + text.charAt(i));
        i++;
        typewriterRef.current = setTimeout(type, speed);
      } else {
        onDone();
      }
    };

    type();
  }, []);

  // Boot sequence
  useEffect(() => {
    // Phase 1: Show header and "CONNECTING..."
    const timer1 = setTimeout(() => {
      setDisplayedText('CONNECTING TO EMBERHOLM... ');

      // Phase 2: Show OK
      const timer2 = setTimeout(() => {
        setDisplayedText('CONNECTING TO EMBERHOLM... OK');

        // Phase 3: Start welcome text
        const timer3 = setTimeout(() => {
          setPhase('welcome');
          typeText(WELCOME_TEXT, 25, () => {
            setPhase('ready');
            setShowContinue(true);
          });
        }, 500);

        return () => clearTimeout(timer3);
      }, 1000);

      return () => clearTimeout(timer2);
    }, 500);

    return () => {
      clearTimeout(timer1);
      if (typewriterRef.current) clearTimeout(typewriterRef.current);
    };
  }, [typeText]);

  // Handle skip (any key press)
  useEffect(() => {
    const handleKeyPress = () => {
      if (phase === 'welcome' && typewriterRef.current) {
        // Skip to end
        clearTimeout(typewriterRef.current);
        setDisplayedText(WELCOME_TEXT);
        setPhase('ready');
        setShowContinue(true);
      } else if (phase === 'ready') {
        onComplete();
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    window.addEventListener('click', handleKeyPress);

    return () => {
      window.removeEventListener('keydown', handleKeyPress);
      window.removeEventListener('click', handleKeyPress);
    };
  }, [phase, onComplete]);

  return (
    <div className="screen-view flex flex-col min-h-screen p-4 pt-6">
      {/* Terminal header */}
      <div className="text-center mb-4">
        <p className="text-amber font-mono text-sm tracking-wider">
          [EMBER PROTOCOL v0.1978 // INITIALIZING...]
        </p>
      </div>

      {/* Content */}
      <div className="flex-1 font-mono text-sm">
        {phase === 'connecting' && (
          <div className="text-amber">
            {displayedText}
            <span className="inline-block w-2 h-4 bg-amber animate-blink ml-1" />
          </div>
        )}

        {(phase === 'welcome' || phase === 'ready') && (
          <div>
            <div className="text-green mb-4">
              CONNECTING TO EMBERHOLM... OK
            </div>
            <pre className="text-amber whitespace-pre-wrap leading-relaxed">
              {displayedText}
              {phase === 'welcome' && (
                <span className="inline-block w-2 h-4 bg-amber animate-blink" />
              )}
            </pre>
          </div>
        )}
      </div>

      {/* Continue prompt */}
      {showContinue && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-6"
        >
          <p className="text-amber-dim text-sm animate-pulse">
            [PRESS ANY KEY TO CONTINUE]
          </p>
        </motion.div>
      )}

      {/* Skip hint during typing */}
      {phase === 'welcome' && !showContinue && (
        <div className="text-center py-4">
          <p className="text-amber-dark text-xs">
            [TAP TO SKIP]
          </p>
        </div>
      )}
    </div>
  );
}

export default BootSequence;
