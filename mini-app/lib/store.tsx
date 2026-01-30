/**
 * EMBERHOLM MINI APP - Global State Store v2
 * Simple React context-based store for app state
 * Includes: Navigation, User, $EMBER, Social/Chat
 */

import { createContext, useContext, useReducer, ReactNode } from 'react';
import { Emissary, RealmStatus, ActiveMicroMission, UserProfile, Conversation, PrivateMessage, CountryStats } from './api';

// =========================================
// State Types
// =========================================

export type AppScreen =
  // Intro Flow
  | 'welcome'           // "Enter the Portal" initial screen
  | 'welcome-operator'  // "WELCOME OPERATOR" screen (after enter portal)
  | 'country-select'    // Country selector
  | 'portal-entry'      // "Accessing Emberholm..." animation
  // Main Navigation
  | 'menu'              // Main menu (6 options)
  // Social
  | 'social-globe'      // 3D Globe with countries
  | 'social-users'      // Users list from a country
  | 'global-chat'       // Global chat room
  | 'inbox'             // Private messages inbox
  | 'chat'              // 1:1 chat screen
  // Play
  | 'play'              // Play submenu (4 options)
  | 'emissary-list'     // Emissary list for selection
  | 'emissary-detail'   // Emissary detail + inventory
  | 'inventory'         // Full inventory view
  | 'missions'          // Normal missions list
  | 'micro-missions'    // Micro-missions list
  | 'timer'             // Active mission timer
  // Vault
  | 'vault'             // Tabs: Tokens/Items/Runes
  // Other
  | 'events'            // Events list
  | 'lore'              // Lore chapters
  | 'tutorial'          // Tutorial screen
  | 'leaderboard'       // Leaderboard
  | 'mint';             // Mint new emissary

export interface AppState {
  // Navigation
  currentScreen: AppScreen;
  screenHistory: AppScreen[];

  // User
  wallet: string | null;
  isConnected: boolean;
  userProfile: UserProfile | null;

  // Realm
  realmStatus: RealmStatus | null;

  // Emissaries
  emissaries: Emissary[];
  selectedEmissary: Emissary | null;

  // $EMBER
  emberBalance: number;
  emberTotalEarned: number;

  // Active Mission
  activeMission: ActiveMicroMission | null;
  selectedMissionId: string | null;

  // Social
  countries: CountryStats[];
  selectedCountry: string | null;
  conversations: Conversation[];
  currentChatWallet: string | null;
  chatMessages: PrivateMessage[];
  unreadCount: number;

  // UI State
  isLoading: boolean;
  error: string | null;
  soundEnabled: boolean;
  musicEnabled: boolean;
  musicVolume: number;
}

// =========================================
// Actions
// =========================================

type AppAction =
  // Navigation
  | { type: 'SET_SCREEN'; screen: AppScreen }
  | { type: 'GO_BACK' }
  | { type: 'RESET_HISTORY' }
  // User
  | { type: 'SET_WALLET'; wallet: string | null }
  | { type: 'SET_CONNECTED'; isConnected: boolean }
  | { type: 'SET_USER_PROFILE'; profile: UserProfile | null }
  // Realm
  | { type: 'SET_REALM_STATUS'; status: RealmStatus }
  // Emissaries
  | { type: 'SET_EMISSARIES'; emissaries: Emissary[] }
  | { type: 'SELECT_EMISSARY'; emissary: Emissary | null }
  // $EMBER
  | { type: 'SET_EMBER_BALANCE'; balance: number; totalEarned?: number }
  // Missions
  | { type: 'SET_ACTIVE_MISSION'; mission: ActiveMicroMission | null }
  | { type: 'SELECT_MISSION'; missionId: string | null }
  // Social
  | { type: 'SET_COUNTRIES'; countries: CountryStats[] }
  | { type: 'SELECT_COUNTRY'; countryCode: string | null }
  | { type: 'SET_CONVERSATIONS'; conversations: Conversation[] }
  | { type: 'SET_CURRENT_CHAT'; wallet: string | null }
  | { type: 'SET_CHAT_MESSAGES'; messages: PrivateMessage[] }
  | { type: 'ADD_CHAT_MESSAGE'; message: PrivateMessage }
  | { type: 'SET_UNREAD_COUNT'; count: number }
  // UI
  | { type: 'SET_LOADING'; isLoading: boolean }
  | { type: 'SET_ERROR'; error: string | null }
  | { type: 'TOGGLE_SOUND' }
  | { type: 'TOGGLE_MUSIC' }
  | { type: 'SET_MUSIC_VOLUME'; volume: number }
  | { type: 'RESET' };

// =========================================
// Initial State
// =========================================

const initialState: AppState = {
  // Navigation
  currentScreen: 'welcome',
  screenHistory: [],

  // User
  wallet: null,
  isConnected: false,
  userProfile: null,

  // Realm
  realmStatus: null,

  // Emissaries
  emissaries: [],
  selectedEmissary: null,

  // $EMBER
  emberBalance: 0,
  emberTotalEarned: 0,

  // Missions
  activeMission: null,
  selectedMissionId: null,

  // Social
  countries: [],
  selectedCountry: null,
  conversations: [],
  currentChatWallet: null,
  chatMessages: [],
  unreadCount: 0,

  // UI
  isLoading: false,
  error: null,
  soundEnabled: true,
  musicEnabled: true,
  musicVolume: 0.5,
};

// =========================================
// Reducer
// =========================================

function appReducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    // Navigation
    case 'SET_SCREEN':
      return {
        ...state,
        screenHistory: [...state.screenHistory, state.currentScreen],
        currentScreen: action.screen,
      };

    case 'GO_BACK':
      if (state.screenHistory.length === 0) {
        return { ...state, currentScreen: 'menu' };
      }
      const history = [...state.screenHistory];
      const previousScreen = history.pop()!;
      return {
        ...state,
        screenHistory: history,
        currentScreen: previousScreen,
      };

    case 'RESET_HISTORY':
      return {
        ...state,
        screenHistory: [],
      };

    // User
    case 'SET_WALLET':
      return {
        ...state,
        wallet: action.wallet,
        isConnected: !!action.wallet,
      };

    case 'SET_CONNECTED':
      return {
        ...state,
        isConnected: action.isConnected,
      };

    case 'SET_USER_PROFILE':
      return {
        ...state,
        userProfile: action.profile,
      };

    // Realm
    case 'SET_REALM_STATUS':
      return {
        ...state,
        realmStatus: action.status,
      };

    // Emissaries
    case 'SET_EMISSARIES':
      return {
        ...state,
        emissaries: action.emissaries,
      };

    case 'SELECT_EMISSARY':
      return {
        ...state,
        selectedEmissary: action.emissary,
      };

    // $EMBER
    case 'SET_EMBER_BALANCE':
      return {
        ...state,
        emberBalance: action.balance,
        emberTotalEarned: action.totalEarned ?? state.emberTotalEarned,
      };

    // Missions
    case 'SET_ACTIVE_MISSION':
      return {
        ...state,
        activeMission: action.mission,
      };

    case 'SELECT_MISSION':
      return {
        ...state,
        selectedMissionId: action.missionId,
      };

    // Social
    case 'SET_COUNTRIES':
      return {
        ...state,
        countries: action.countries,
      };

    case 'SELECT_COUNTRY':
      return {
        ...state,
        selectedCountry: action.countryCode,
      };

    case 'SET_CONVERSATIONS':
      return {
        ...state,
        conversations: action.conversations,
        unreadCount: action.conversations.reduce((sum, c) => sum + c.unread_count, 0),
      };

    case 'SET_CURRENT_CHAT':
      return {
        ...state,
        currentChatWallet: action.wallet,
        chatMessages: action.wallet ? state.chatMessages : [],
      };

    case 'SET_CHAT_MESSAGES':
      return {
        ...state,
        chatMessages: action.messages,
      };

    case 'ADD_CHAT_MESSAGE':
      return {
        ...state,
        chatMessages: [...state.chatMessages, action.message],
      };

    case 'SET_UNREAD_COUNT':
      return {
        ...state,
        unreadCount: action.count,
      };

    // UI
    case 'SET_LOADING':
      return {
        ...state,
        isLoading: action.isLoading,
      };

    case 'SET_ERROR':
      return {
        ...state,
        error: action.error,
      };

    case 'TOGGLE_SOUND':
      return {
        ...state,
        soundEnabled: !state.soundEnabled,
      };

    case 'TOGGLE_MUSIC':
      return {
        ...state,
        musicEnabled: !state.musicEnabled,
      };

    case 'SET_MUSIC_VOLUME':
      return {
        ...state,
        musicVolume: action.volume,
      };

    case 'RESET':
      return {
        ...initialState,
        realmStatus: state.realmStatus,
        soundEnabled: state.soundEnabled,
      };

    default:
      return state;
  }
}

// =========================================
// Context
// =========================================

interface AppContextType {
  state: AppState;
  dispatch: React.Dispatch<AppAction>;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

// =========================================
// Provider
// =========================================

export function AppProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(appReducer, initialState);

  return (
    <AppContext.Provider value={{ state, dispatch }}>
      {children}
    </AppContext.Provider>
  );
}

// =========================================
// Hook
// =========================================

export function useApp() {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within AppProvider');
  }
  return context;
}

// =========================================
// Action Helpers
// =========================================

export const actions = {
  // Navigation
  setScreen: (screen: AppScreen): AppAction => ({ type: 'SET_SCREEN', screen }),
  goBack: (): AppAction => ({ type: 'GO_BACK' }),
  resetHistory: (): AppAction => ({ type: 'RESET_HISTORY' }),

  // User
  setWallet: (wallet: string | null): AppAction => ({ type: 'SET_WALLET', wallet }),
  setConnected: (isConnected: boolean): AppAction => ({ type: 'SET_CONNECTED', isConnected }),
  setUserProfile: (profile: UserProfile | null): AppAction => ({ type: 'SET_USER_PROFILE', profile }),

  // Realm
  setRealmStatus: (status: RealmStatus): AppAction => ({ type: 'SET_REALM_STATUS', status }),

  // Emissaries
  setEmissaries: (emissaries: Emissary[]): AppAction => ({ type: 'SET_EMISSARIES', emissaries }),
  selectEmissary: (emissary: Emissary | null): AppAction => ({ type: 'SELECT_EMISSARY', emissary }),

  // $EMBER
  setEmberBalance: (balance: number, totalEarned?: number): AppAction =>
    ({ type: 'SET_EMBER_BALANCE', balance, totalEarned }),

  // Missions
  setActiveMission: (mission: ActiveMicroMission | null): AppAction => ({ type: 'SET_ACTIVE_MISSION', mission }),
  selectMission: (missionId: string | null): AppAction => ({ type: 'SELECT_MISSION', missionId }),

  // Social
  setCountries: (countries: CountryStats[]): AppAction => ({ type: 'SET_COUNTRIES', countries }),
  selectCountry: (countryCode: string | null): AppAction => ({ type: 'SELECT_COUNTRY', countryCode }),
  setConversations: (conversations: Conversation[]): AppAction => ({ type: 'SET_CONVERSATIONS', conversations }),
  setCurrentChat: (wallet: string | null): AppAction => ({ type: 'SET_CURRENT_CHAT', wallet }),
  setChatMessages: (messages: PrivateMessage[]): AppAction => ({ type: 'SET_CHAT_MESSAGES', messages }),
  addChatMessage: (message: PrivateMessage): AppAction => ({ type: 'ADD_CHAT_MESSAGE', message }),
  setUnreadCount: (count: number): AppAction => ({ type: 'SET_UNREAD_COUNT', count }),

  // UI
  setLoading: (isLoading: boolean): AppAction => ({ type: 'SET_LOADING', isLoading }),
  setError: (error: string | null): AppAction => ({ type: 'SET_ERROR', error }),
  toggleSound: (): AppAction => ({ type: 'TOGGLE_SOUND' }),
  toggleMusic: (): AppAction => ({ type: 'TOGGLE_MUSIC' }),
  setMusicVolume: (volume: number): AppAction => ({ type: 'SET_MUSIC_VOLUME', volume }),
  reset: (): AppAction => ({ type: 'RESET' }),
};
