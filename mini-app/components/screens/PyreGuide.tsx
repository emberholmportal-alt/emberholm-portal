'use client';

import { motion } from 'framer-motion';
import { FireIcon, CoinIcon, LightningIcon, ChartIcon, PinIcon, CheckIcon } from '@/components/ui/Icons';

/**
 * PyreGuide - $PYRE token guide
 */

interface PyreGuideProps {
  onBack: () => void;
}

interface EarnMethod {
  action: string;
  reward: string;
  limit: string;
}

const EARN_METHODS: EarnMethod[] = [
  { action: 'Complete Micro-Mission', reward: '10-50 $PYRE', limit: 'Per mission cooldown' },
  { action: 'Daily Login', reward: '100 $PYRE', limit: 'Once per day' },
  { action: 'Send Chat Message', reward: '5 $PYRE', limit: '50 messages/day' },
  { action: 'Win Event', reward: '500-5000 $PYRE', limit: 'Per event' },
  { action: 'Refer a Friend', reward: '250 $PYRE', limit: 'Unlimited' },
  { action: 'First Mission of Day', reward: '50 $PYRE', limit: 'Once per day' },
  { action: 'Level Up Emissary', reward: '25 × Level $PYRE', limit: 'Per level' },
  { action: 'Complete Daily Quest', reward: '75 $PYRE', limit: '3 quests/day' },
];

interface UseCase {
  name: string;
  cost: string;
  description: string;
}

const USE_CASES: UseCase[] = [
  { name: 'Energy Boost', cost: '100 $PYRE', description: 'Instantly restore 25 energy' },
  { name: 'XP Boost (1hr)', cost: '200 $PYRE', description: '+50% XP for 1 hour' },
  { name: 'Reveal Hidden Path', cost: '150 $PYRE', description: 'Unlock secret mission choices' },
  { name: 'Reduce Death Chance', cost: '500 $PYRE', description: '-5% death chance (once per mission)' },
  { name: 'Exclusive Cosmetics', cost: '1000+ $PYRE', description: 'Unique visual effects and titles' },
  { name: 'Early Access', cost: '2500 $PYRE', description: 'Access to new features before release' },
];

interface TokenomicsItem {
  category: string;
  percentage: number;
  amount: string;
}

const TOKENOMICS: TokenomicsItem[] = [
  { category: 'Player Rewards', percentage: 60, amount: '60B' },
  { category: 'Community Treasury', percentage: 20, amount: '20B' },
  { category: 'Development', percentage: 10, amount: '10B' },
  { category: 'Team & Advisors', percentage: 7, amount: '7B' },
  { category: 'Initial Liquidity', percentage: 3, amount: '3B' },
];

export function PyreGuide({ onBack }: PyreGuideProps) {
  return (
    <div className="screen-view flex flex-col min-h-screen">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="p-4 text-center"
      >
        <h1 className="title text-2xl">$PYRE GUIDE</h1>
        <p className="subtitle">Your reputation in Emberholm</p>
      </motion.div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {/* What is $PYRE */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <h2 className="text-amber-bright font-semibold mb-3 flex items-center gap-2">
            <FireIcon size={20} className="text-amber" /> WHAT IS $PYRE?
          </h2>
          <div className="portal-box">
            <p className="text-amber-dim text-sm leading-relaxed">
              $PYRE is the reputation token of Emberholm. Unlike $EMBER (which can be traded),
              $PYRE is <span className="text-amber-bright">soulbound</span>—meaning it cannot
              be transferred or sold.
            </p>
            <p className="text-amber-dim text-sm leading-relaxed mt-3">
              Think of it as your standing in the community. The more $PYRE you accumulate,
              the more you can unlock—from gameplay boosts to exclusive features and cosmetics.
            </p>
            <div className="mt-4 pt-4 border-t border-amber-dark/30 text-center">
              <div className="text-xs text-amber-dark uppercase">Total Supply</div>
              <div className="text-2xl text-amber-bright font-bold">100,000,000,000</div>
              <div className="text-amber-dim text-sm">100 Billion $PYRE</div>
            </div>
          </div>
        </motion.section>

        {/* How to Earn */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <h2 className="text-amber-bright font-semibold mb-3 flex items-center gap-2">
            <CoinIcon size={20} className="text-amber" /> HOW TO EARN
          </h2>
          <div className="data-box">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-amber-dark text-xs">
                  <th className="text-left pb-2">Action</th>
                  <th className="text-right pb-2">Reward</th>
                  <th className="text-right pb-2">Limit</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-amber-dark/20">
                {EARN_METHODS.map((method, i) => (
                  <tr key={i}>
                    <td className="py-2 text-amber-dim">{method.action}</td>
                    <td className="py-2 text-amber text-right">{method.reward}</td>
                    <td className="py-2 text-amber-dark text-right text-xs">{method.limit}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </motion.section>

        {/* How to Use */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <h2 className="text-amber-bright font-semibold mb-3 flex items-center gap-2">
            <LightningIcon size={20} className="text-cyan" /> HOW TO USE
          </h2>
          <div className="space-y-2">
            {USE_CASES.map((useCase, i) => (
              <div key={i} className="data-box">
                <div className="flex items-center justify-between">
                  <span className="text-amber font-semibold">{useCase.name}</span>
                  <span className="text-amber-bright">{useCase.cost}</span>
                </div>
                <p className="text-xs text-amber-dim mt-1">{useCase.description}</p>
              </div>
            ))}
          </div>
        </motion.section>

        {/* Tokenomics */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <h2 className="text-amber-bright font-semibold mb-3 flex items-center gap-2">
            <ChartIcon size={20} className="text-amber" /> TOKENOMICS
          </h2>
          <div className="portal-box">
            <div className="space-y-3">
              {TOKENOMICS.map((item, i) => (
                <div key={i}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-amber-dim">{item.category}</span>
                    <span className="text-amber">{item.percentage}% ({item.amount})</span>
                  </div>
                  <div className="w-full h-2 bg-dark rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${item.percentage}%` }}
                      transition={{ duration: 0.5, delay: 0.3 + i * 0.1 }}
                      className={`h-full ${
                        i === 0 ? 'bg-amber' :
                        i === 1 ? 'bg-cyan' :
                        i === 2 ? 'bg-green' :
                        i === 3 ? 'bg-amber-dark' : 'bg-amber-dim'
                      }`}
                    />
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-4 pt-4 border-t border-amber-dark/30">
              <p className="text-xs text-amber-dark leading-relaxed">
                60% of all $PYRE is allocated to player rewards, ensuring the community
                is the primary beneficiary. Tokens are distributed gradually through
                gameplay to maintain long-term value and engagement.
              </p>
            </div>
          </div>
        </motion.section>

        {/* Key Points */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <h2 className="text-amber-bright font-semibold mb-3 flex items-center gap-2">
            <PinIcon size={20} className="text-amber" /> KEY POINTS
          </h2>
          <div className="data-box space-y-2">
            <div className="flex items-start gap-2">
              <CheckIcon size={16} className="text-green flex-shrink-0 mt-0.5" />
              <span className="text-amber-dim text-sm">$PYRE is soulbound (non-transferable)</span>
            </div>
            <div className="flex items-start gap-2">
              <CheckIcon size={16} className="text-green flex-shrink-0 mt-0.5" />
              <span className="text-amber-dim text-sm">Earned through gameplay and social activity</span>
            </div>
            <div className="flex items-start gap-2">
              <CheckIcon size={16} className="text-green flex-shrink-0 mt-0.5" />
              <span className="text-amber-dim text-sm">Used for boosts, unlocks, and cosmetics</span>
            </div>
            <div className="flex items-start gap-2">
              <CheckIcon size={16} className="text-green flex-shrink-0 mt-0.5" />
              <span className="text-amber-dim text-sm">No purchase required—100% earned</span>
            </div>
            <div className="flex items-start gap-2">
              <CheckIcon size={16} className="text-green flex-shrink-0 mt-0.5" />
              <span className="text-amber-dim text-sm">Higher $PYRE = more privileges</span>
            </div>
          </div>
        </motion.section>
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

export default PyreGuide;
