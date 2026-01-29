'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Image from 'next/image';

/**
 * EventsScreen - Active and past events
 */

interface EventsScreenProps {
  wallet: string | null;
  onBack: () => void;
}

interface EventReward {
  place: string;
  reward: string;
}

interface ActiveEvent {
  id: string;
  name: string;
  description: string;
  endsAt: string;
  rewards: EventReward[];
  userProgress: number;
  userRank: number;
  totalParticipants: number;
  leaderboard: { wallet: string; name: string; score: number }[];
}

interface PastEvent {
  id: string;
  name: string;
  endedAt: string;
  winner: { wallet: string; name: string };
  userRank: number | null;
}

export function EventsScreen({ wallet, onBack }: EventsScreenProps) {
  const [activeEvent, setActiveEvent] = useState<ActiveEvent | null>(null);
  const [pastEvents, setPastEvents] = useState<PastEvent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [expandedPastEvent, setExpandedPastEvent] = useState<string | null>(null);

  // Load events
  useEffect(() => {
    async function loadEvents() {
      setIsLoading(true);
      try {
        // Mock data - replace with API calls
        setActiveEvent({
          id: 'event-1',
          name: 'THE GREAT EMBER HUNT',
          description: 'Collect the most $EMBER this week to win exclusive rewards!',
          endsAt: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString(),
          rewards: [
            { place: '1st', reward: '500 $EMBER + Legendary Rune' },
            { place: '2nd', reward: '250 $EMBER + Epic Rune' },
            { place: '3rd', reward: '100 $EMBER + Rare Rune' },
          ],
          userProgress: 67,
          userRank: 42,
          totalParticipants: 1234,
          leaderboard: [
            { wallet: '0x123...', name: 'DragonSlayer', score: 2450 },
            { wallet: '0x456...', name: 'EmberLord', score: 2180 },
            { wallet: '0x789...', name: 'FlameWarden', score: 1950 },
            { wallet: '0xabc...', name: 'AshWalker', score: 1820 },
            { wallet: '0xdef...', name: 'PyreKnight', score: 1750 },
          ],
        });

        setPastEvents([
          {
            id: 'past-1',
            name: 'SURVIVAL CHALLENGE',
            endedAt: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
            winner: { wallet: '0x111...', name: 'IronWill' },
            userRank: 15,
          },
          {
            id: 'past-2',
            name: 'GUILD WARS I',
            endedAt: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
            winner: { wallet: '0x222...', name: 'GuildMaster' },
            userRank: null,
          },
        ]);
      } catch (error) {
        console.error('Error loading events:', error);
      } finally {
        setIsLoading(false);
      }
    }

    loadEvents();
  }, [wallet]);

  // Calculate countdown
  const getCountdown = (endsAt: string): string => {
    const diff = new Date(endsAt).getTime() - Date.now();
    if (diff <= 0) return 'Ended';

    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

    if (days > 0) return `${days}d ${hours}h remaining`;
    if (hours > 0) return `${hours}h ${minutes}m remaining`;
    return `${minutes}m remaining`;
  };

  // Format date
  const formatDate = (dateStr: string): string => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  return (
    <div className="screen-view flex flex-col min-h-screen">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="p-4 text-center"
      >
        <h1 className="title text-2xl">EVENTS</h1>
        <p className="subtitle">Compete for glory and rewards</p>
      </motion.div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {isLoading ? (
          <div className="text-center py-8 text-amber-dim">Loading events...</div>
        ) : (
          <>
            {/* Active Event */}
            {activeEvent ? (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
              >
                <h2 className="text-amber-bright font-semibold mb-3 flex items-center gap-2">
                  <Image
                    src="/icons/fire.png"
                    alt=""
                    width={20}
                    height={20}
                    className="pixel-icon animate-pulse"
                  />
                  ACTIVE EVENT
                </h2>

                <div className="portal-box">
                  <div className="ornament text-sm">═══ ◈ ═══</div>

                  <h3 className="title text-lg my-3">{activeEvent.name}</h3>
                  <p className="text-amber-dim text-sm mb-4">{activeEvent.description}</p>

                  {/* Countdown */}
                  <div className="data-box mb-4">
                    <div className="text-center">
                      <div className="text-xs text-amber-dark uppercase mb-1">Ends in</div>
                      <div className="text-amber-bright font-semibold">
                        {getCountdown(activeEvent.endsAt)}
                      </div>
                    </div>
                  </div>

                  {/* User Progress */}
                  <div className="data-box mb-4">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-amber-dim text-sm">Your Progress</span>
                      <span className="text-amber-bright font-semibold">
                        {activeEvent.userProgress}%
                      </span>
                    </div>
                    <div className="w-full h-2 bg-dark rounded-full overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${activeEvent.userProgress}%` }}
                        className="h-full bg-gradient-to-r from-amber-dark to-amber"
                      />
                    </div>
                    <div className="flex justify-between items-center mt-2 text-xs">
                      <span className="text-amber-dim">
                        Rank: #{activeEvent.userRank}
                      </span>
                      <span className="text-amber-dark">
                        {activeEvent.totalParticipants} participants
                      </span>
                    </div>
                  </div>

                  {/* Rewards */}
                  <div className="mb-4">
                    <div className="text-xs text-amber-dark uppercase mb-2">Rewards</div>
                    <div className="space-y-1">
                      {activeEvent.rewards.map((reward, i) => (
                        <div key={i} className="flex justify-between text-sm">
                          <span className={i === 0 ? 'text-amber-bright' : 'text-amber-dim'}>
                            {reward.place}
                          </span>
                          <span className="text-amber">{reward.reward}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Leaderboard */}
                  <div>
                    <div className="text-xs text-amber-dark uppercase mb-2">Leaderboard</div>
                    <div className="space-y-1">
                      {activeEvent.leaderboard.map((entry, i) => (
                        <div
                          key={entry.wallet}
                          className="flex items-center justify-between text-sm py-1"
                        >
                          <div className="flex items-center gap-2">
                            {i < 3 ? (
                              <Image
                                src={i === 0 ? '/icons/crown.png' : '/icons/trophy.png'}
                                alt=""
                                width={16}
                                height={16}
                                className={`pixel-icon ${i === 0 ? 'brightness-125' : i === 1 ? 'brightness-100' : 'brightness-75'}`}
                              />
                            ) : (
                              <span className="text-amber-dim w-4 text-center">#{i + 1}</span>
                            )}
                            <span className="text-amber">{entry.name}</span>
                          </div>
                          <span className="text-amber-dim">{entry.score.toLocaleString()}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="ornament text-sm mt-4">═══ ◈ ═══</div>
                </div>
              </motion.div>
            ) : (
              <div className="data-box text-center py-6">
                <div className="text-amber-dim">No active event</div>
                <div className="text-xs text-amber-dark mt-1">
                  Check back soon for new challenges!
                </div>
              </div>
            )}

            {/* Past Events */}
            {pastEvents.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
              >
                <h2 className="text-amber-dim font-semibold mb-3">PAST EVENTS</h2>

                <div className="space-y-2">
                  {pastEvents.map(event => (
                    <div key={event.id} className="data-box">
                      <button
                        onClick={() => setExpandedPastEvent(
                          expandedPastEvent === event.id ? null : event.id
                        )}
                        className="w-full text-left"
                      >
                        <div className="flex items-center justify-between">
                          <div>
                            <div className="text-amber font-semibold">{event.name}</div>
                            <div className="text-xs text-amber-dark">
                              Ended {formatDate(event.endedAt)}
                            </div>
                          </div>
                          <span className="text-amber-dim">
                            {expandedPastEvent === event.id ? '−' : '+'}
                          </span>
                        </div>
                      </button>

                      <AnimatePresence>
                        {expandedPastEvent === event.id && (
                          <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            className="overflow-hidden"
                          >
                            <div className="pt-3 mt-3 border-t border-amber-dark/30">
                              <div className="flex justify-between text-sm items-center">
                                <span className="text-amber-dim">Winner:</span>
                                <span className="text-amber-bright flex items-center gap-1">
                                  <Image
                                    src="/icons/trophy.png"
                                    alt=""
                                    width={14}
                                    height={14}
                                    className="pixel-icon"
                                  />
                                  {event.winner.name}
                                </span>
                              </div>
                              {event.userRank && (
                                <div className="flex justify-between text-sm mt-1">
                                  <span className="text-amber-dim">Your Rank:</span>
                                  <span className="text-amber">#{event.userRank}</span>
                                </div>
                              )}
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}
          </>
        )}
      </div>

      {/* Back button */}
      <div className="p-4">
        <button onClick={onBack} className="back-btn">
          ← BACK
        </button>
      </div>
    </div>
  );
}

export default EventsScreen;
