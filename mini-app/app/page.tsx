'use client';

import { useEffect, useCallback } from 'react';
import { CRTOverlay } from '@/components/CRTOverlay';
import { ImmersionBar } from '@/components/ImmersionBar';
import { WelcomeScreen } from '@/components/screens/WelcomeScreen';
import { BootSequence } from '@/components/screens/BootSequence';
import { CountrySelect } from '@/components/screens/CountrySelect';
import { PortalEntry } from '@/components/screens/PortalEntry';
import { MainMenu } from '@/components/screens/MainMenu';
import { PlayScreen } from '@/components/screens/PlayScreen';
import { EmissaryList } from '@/components/screens/EmissaryList';
import { EmissaryDetail } from '@/components/screens/EmissaryDetail';
import { MissionsScreen } from '@/components/screens/MissionsScreen';
import { MicroMissionsScreen } from '@/components/screens/MicroMissionsScreen';
import { MissionPlayer } from '@/components/screens/MissionPlayer';
import { TimerScreen } from '@/components/screens/TimerScreen';
import { LeaderboardScreen } from '@/components/screens/LeaderboardScreen';
import { SocialGlobe } from '@/components/screens/SocialGlobe';
import { SocialUsers } from '@/components/screens/SocialUsers';
import { ChatScreen } from '@/components/screens/ChatScreen';
import { GlobalChatScreen } from '@/components/screens/GlobalChatScreen';
import { VaultScreen } from '@/components/screens/VaultScreen';
import { MintScreen } from '@/components/screens/MintScreen';
import { EventsScreen } from '@/components/screens/EventsScreen';
import { LoreScreen } from '@/components/screens/LoreScreen';
import { TutorialScreen } from '@/components/screens/TutorialScreen';
import { SettingsScreen } from '@/components/screens/SettingsScreen';
import { useApp, actions, AppScreen, AppProvider } from '@/lib/store';
import { SoundProvider } from '@/lib/SoundContext';
import { WalletProvider, useWallet } from '@/lib/WalletContext';
import { WallpaperProvider } from '@/lib/WallpaperContext';
import { LivingWallpaper } from '@/components/LivingWallpaper';
import {
  Emissary,
  MicroMission,
  getWalletEmissaries,
  getEmberBalance,
  getActiveMicroMission,
  updateProfile,
} from '@/lib/api';

/**
 * Main App Page
 * Handles navigation between screens using global store
 */

function AppContent() {
  const { state, dispatch } = useApp();
  const wallet = useWallet();

  // Load all player data
  const loadPlayerData = useCallback(async (walletAddress: string) => {
    if (!walletAddress || walletAddress === '0x0000000000000000000000000000000000000000') {
      return;
    }

    try {
      dispatch(actions.setLoading(true));
      dispatch(actions.setError(null));

      // Load emissaries
      const emissaries = await getWalletEmissaries(walletAddress);
      dispatch(actions.setEmissaries(emissaries));
      console.debug(`Loaded ${emissaries.length} emissaries`);

      // Load EMBER balance
      const emberData = await getEmberBalance(walletAddress);
      dispatch(actions.setEmberBalance(
        emberData.balance,
        emberData.total_earned
      ));
      console.debug(`Loaded EMBER balance: ${emberData.balance}`);

      // Check for active micro-mission
      const activeMission = await getActiveMicroMission(walletAddress);
      if (activeMission) {
        dispatch(actions.setActiveMission(activeMission));
        console.debug('Found active mission');
      }
    } catch (error) {
      console.error('Failed to load player data:', error);
      dispatch(actions.setError('Failed to load data'));
    } finally {
      dispatch(actions.setLoading(false));
    }
  }, [dispatch]);

  // Sync wallet context with app store and load data
  useEffect(() => {
    if (wallet.address && wallet.address !== state.wallet) {
      dispatch(actions.setWallet(wallet.address));
      // Immediately load data when wallet changes
      loadPlayerData(wallet.address);
    }
  }, [wallet.address, state.wallet, dispatch, loadPlayerData]);

  // Check for existing session on mount
  useEffect(() => {
    const savedCountry = localStorage.getItem('emberholm_country');
    const skipIntro = localStorage.getItem('emberholm_skip_intro');

    // If returning user with saved data, skip to menu
    if (skipIntro === 'true' && savedCountry && wallet.isConnected) {
      dispatch(actions.setScreen('menu'));
    }
  }, [dispatch, wallet.isConnected]);

  // Reload data when returning to app or on initial mount with existing wallet
  useEffect(() => {
    if (state.wallet && state.emissaries.length === 0 && !state.isLoading) {
      loadPlayerData(state.wallet);
    }
  }, [state.wallet, state.emissaries.length, state.isLoading, loadPlayerData]);

  // Wallet connection handler - uses WalletContext
  const handleConnect = useCallback(async () => {
    const result = await wallet.connect();
    // Data will be loaded automatically by the wallet sync useEffect
    return result;
  }, [wallet]);

  // Refresh data handler for manual refresh
  const handleRefreshData = useCallback(async () => {
    if (state.wallet) {
      await loadPlayerData(state.wallet);
    }
  }, [state.wallet, loadPlayerData]);

  // Navigation handlers
  const handleNavigate = (screen: AppScreen) => {
    dispatch(actions.setScreen(screen));
  };

  const handleBack = () => {
    dispatch(actions.goBack());
  };

  // Intro flow handlers
  const handleWelcomeEnter = () => {
    // Go to Welcome Operator (boot sequence) first
    dispatch(actions.setScreen('welcome-operator'));
  };

  const handleBootComplete = () => {
    dispatch(actions.setScreen('country-select'));
  };

  const handleCountrySelect = async (countryCode: string) => {
    dispatch(actions.selectCountry(countryCode));

    // Update profile with country if wallet is connected
    if (state.wallet) {
      try {
        await updateProfile({
          wallet: state.wallet,
          country_code: countryCode,
        });
      } catch (error) {
        console.error('Failed to update profile:', error);
      }
    }

    dispatch(actions.setScreen('portal-entry'));
  };

  const handlePortalEnter = () => {
    dispatch(actions.setScreen('menu'));
    dispatch(actions.resetHistory());
  };

  // Emissary handlers
  const handleSelectEmissary = (emissary: Emissary) => {
    dispatch(actions.selectEmissary(emissary));
    dispatch(actions.setScreen('emissary-detail'));
  };

  const handleStartMission = () => {
    dispatch(actions.setScreen('missions'));
  };

  const handleStartMicroMission = () => {
    dispatch(actions.setScreen('micro-missions'));
  };

  // Mission handlers
  const handleSelectMission = (mission: MicroMission) => {
    if (!state.selectedEmissary) {
      dispatch(actions.setScreen('play'));
      return;
    }
    dispatch(actions.selectMission(mission.id));
    dispatch(actions.setScreen('timer'));
  };

  const handleMissionComplete = async (rewards: { ember: number; xp: number; aura: number }) => {
    // Update EMBER balance
    dispatch(actions.setEmberBalance(state.emberBalance + rewards.ember));

    // Refresh emissary data
    if (state.wallet) {
      const emissaries = await getWalletEmissaries(state.wallet);
      dispatch(actions.setEmissaries(emissaries));
    }

    // Clear mission state and go back to menu
    dispatch(actions.setActiveMission(null));
    dispatch(actions.selectMission(null));
    dispatch(actions.setScreen('menu'));
  };

  // Social handlers
  const handleSelectCountry = (countryCode: string) => {
    dispatch(actions.selectCountry(countryCode));
    dispatch(actions.setScreen('social-users'));
  };

  const handleMessageUser = (userWallet: string) => {
    dispatch(actions.setCurrentChat(userWallet));
    dispatch(actions.setScreen('chat'));
  };

  // Determine which screens should show the top bar
  const showTopBar = !['welcome', 'welcome-operator', 'country-select', 'portal-entry', 'chat'].includes(state.currentScreen);

  return (
    <main className="crt-screen relative">
      {/* Living Terminal Wallpaper - Background */}
      <LivingWallpaper />

      {/* CRT Effects */}
      <CRTOverlay />

      {/* Top Bar (Immersion Bar) - only on main screens */}
      {showTopBar && <ImmersionBar />}

      {/* Screen Content */}
      <div className="screen-content relative z-10">
        {/* Intro Flow */}
        {state.currentScreen === 'welcome' && (
          <WelcomeScreen onEnter={handleWelcomeEnter} />
        )}

        {state.currentScreen === 'welcome-operator' && (
          <BootSequence onComplete={handleBootComplete} />
        )}

        {state.currentScreen === 'country-select' && (
          <CountrySelect
            onSelect={handleCountrySelect}
            onBack={handleBack}
          />
        )}

        {state.currentScreen === 'portal-entry' && (
          <PortalEntry
            onEnter={handlePortalEnter}
            onBack={handleBack}
          />
        )}

        {/* Main Menu */}
        {state.currentScreen === 'menu' && (
          <MainMenu
            wallet={state.wallet}
            emberBalance={state.emberBalance}
            emissaryCount={state.emissaries.length}
            unreadMessages={state.unreadCount}
            onNavigate={handleNavigate}
            onConnect={handleConnect}
            onDisconnect={wallet.disconnect}
          />
        )}

        {/* Play Section */}
        {state.currentScreen === 'play' && (
          <PlayScreen
            emissaryCount={state.emissaries.length}
            activeMission={state.activeMission}
            onNavigate={handleNavigate}
            onBack={handleBack}
          />
        )}

        {state.currentScreen === 'emissary-detail' && state.selectedEmissary && (
          <EmissaryDetail
            emissary={state.selectedEmissary}
            onNavigate={handleNavigate}
            onBack={handleBack}
          />
        )}

        {state.currentScreen === 'missions' && (
          <MissionsScreen
            emissary={state.selectedEmissary}
            onSelectMission={(mission) => {
              // Normal missions - future implementation
            }}
            onSelectEmissary={() => handleNavigate('emissary-list')}
            onBack={handleBack}
          />
        )}

        {state.currentScreen === 'micro-missions' && (
          <MicroMissionsScreen
            emissary={state.selectedEmissary}
            onSelectMission={handleSelectMission}
            onSelectEmissary={() => handleNavigate('play')}
            onBack={handleBack}
          />
        )}

        {state.currentScreen === 'timer' && state.selectedMissionId && state.selectedEmissary && state.wallet && (
          <MissionPlayer
            mission={{ id: state.selectedMissionId } as MicroMission}
            emissary={state.selectedEmissary}
            wallet={state.wallet}
            onComplete={handleMissionComplete}
            onCancel={handleBack}
          />
        )}

        {state.currentScreen === 'timer' && state.activeMission && state.selectedEmissary && state.wallet && !state.selectedMissionId && (
          <TimerScreen
            emissary={state.selectedEmissary}
            activeMission={state.activeMission}
            wallet={state.wallet}
            onComplete={handleMissionComplete}
            onBack={handleBack}
          />
        )}

        {state.currentScreen === 'leaderboard' && (
          <LeaderboardScreen
            currentWallet={state.wallet}
            onBack={handleBack}
          />
        )}

        {/* Emissary List (for selecting emissary) */}
        {state.currentScreen === 'emissary-list' && (
          <EmissaryList
            emissaries={state.emissaries}
            onSelect={handleSelectEmissary}
            onBack={handleBack}
            isLoading={state.isLoading}
          />
        )}

        {/* Secondary Screens */}
        {state.currentScreen === 'mint' && (
          <MintScreen
            wallet={state.wallet}
            onMintSuccess={(tokenId) => {
              // Refresh emissaries after mint
              if (state.wallet) {
                getWalletEmissaries(state.wallet).then(emissaries => {
                  dispatch(actions.setEmissaries(emissaries));
                });
              }
            }}
            onBack={handleBack}
          />
        )}

        {state.currentScreen === 'vault' && (
          <VaultScreen
            wallet={state.wallet}
            emissaries={state.emissaries}
            onBack={handleBack}
          />
        )}

        {state.currentScreen === 'events' && (
          <EventsScreen
            wallet={state.wallet}
            onBack={handleBack}
          />
        )}

        {state.currentScreen === 'lore' && (
          <LoreScreen onBack={handleBack} />
        )}

        {state.currentScreen === 'tutorial' && (
          <TutorialScreen wallet={state.wallet} onBack={handleBack} />
        )}

        {/* Social Section */}
        {state.currentScreen === 'social-globe' && (
          <SocialGlobe
            onSelectCountry={handleSelectCountry}
            onGlobalChat={() => handleNavigate('global-chat')}
            onBack={handleBack}
          />
        )}

        {state.currentScreen === 'social-users' && state.selectedCountry && (
          <SocialUsers
            countryCode={state.selectedCountry}
            currentWallet={state.wallet}
            onMessageUser={handleMessageUser}
            onBack={handleBack}
          />
        )}

        {state.currentScreen === 'chat' && state.wallet && state.currentChatWallet && (
          <ChatScreen
            wallet={state.wallet}
            otherWallet={state.currentChatWallet}
            onBack={handleBack}
          />
        )}

        {state.currentScreen === 'global-chat' && (
          <GlobalChatScreen
            wallet={state.wallet}
            onBack={handleBack}
          />
        )}

        {/* Settings */}
        {state.currentScreen === 'settings' && (
          <SettingsScreen onBack={handleBack} />
        )}
      </div>
    </main>
  );
}

// Wrap with Providers
export default function Home() {
  return (
    <WallpaperProvider>
      <WalletProvider>
        <SoundProvider>
          <AppProvider>
            <AppContent />
          </AppProvider>
        </SoundProvider>
      </WalletProvider>
    </WallpaperProvider>
  );
}
