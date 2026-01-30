/**
 * EMBERHOLM MINI APP - API Client v2
 * Connects to Flask backend endpoints
 * Includes: Realm Status, $EMBER, Micro-Missions, Social Chat
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

// =========================================
// Types - Realm
// =========================================

export interface RealmStatus {
  date: string;
  time: string;
  era: string;
  year: number;
  weather: {
    name: string;
    icon: string;
    description: string;
  };
  flame: {
    name: string;
    color: string;
    description: string;
  };
}

// =========================================
// Types - $EMBER Balance
// =========================================

export interface EmberBalance {
  wallet: string;
  balance: number;
  total_earned: number;
  pending: number;
}

// =========================================
// Types - Micro-Missions
// =========================================

export interface MicroMission {
  id: string;
  name: string;
  description: string;
  difficulty: 'EASY' | 'MEDIUM' | 'HARD';
  duration_seconds: number;
  energy_cost: number;
  ember_reward: { min: number; max: number };
  xp_reward: { min: number; max: number };
  aura_chance: number;
  narrative_intro: string;
  cooldown_minutes: number;
  // Keep pyre_reward for backwards compatibility with backend
  pyre_reward?: { min: number; max: number };
}

export interface MicroMissionDetail extends MicroMission {
  narrative_choices: {
    id: string;
    text: string;
    icon?: string;
  }[];
  narrative_outcomes: Record<string, {
    type: string;
    text: string;
    ember_modifier: number;
    xp_modifier: number;
  }>;
}

export interface ActiveMicroMission {
  active_id: number;
  emissary_token_id: string;
  mission_id: string;
  started_at: string;
  ends_at: string;
  remaining_seconds: number;
  status: string;
  choice_made: string | null;
  name: string;
  narrative_intro: string;
  choices: { id: string; text: string; icon?: string }[];
}

export interface MissionRewards {
  ember: number;
  xp: number;
  aura: number;
}

// =========================================
// Types - Emissaries
// =========================================

export interface Emissary {
  token_id: string;
  name: string;
  guild: string;
  race_class: string;
  owner: string;
  image_url: string;
  stats: {
    level: number;
    xp_total: number;
    aura_level: number;
    energy_current: number;
    energy_max: number;
    power: number;
    death_count: number;
  };
  current_state: 'READY' | 'ON_MISSION' | 'ON_MICRO_MISSION' | 'FALLEN' | 'CLAIMING';
  active_mission: any | null;
  active_micro_mission: any | null;
  equipment: Record<string, string | null>;
  chronicle: {
    total_missions: number;
    total_deaths: number;
    items_found: number;
    runes_found: number;
  };
}

// =========================================
// Types - Social
// =========================================

export interface UserProfile {
  id: number;
  wallet: string;
  country_code: string | null;
  display_name: string | null;
  farcaster_fid: number | null;
  farcaster_username: string | null;
  farcaster_pfp_url: string | null;
  last_seen: string | null;
}

export interface CountryStats {
  country_code: string;
  user_count: number;
  online_count: number;
}

export interface CountryUser {
  wallet: string;
  display_name: string | null;
  farcaster_username: string | null;
  farcaster_pfp_url: string | null;
  last_seen: string | null;
  is_online: boolean;
}

export interface Conversation {
  other_wallet: string;
  last_message: string | null;
  last_message_at: string | null;
  unread_count: number;
  other_user: {
    display_name: string | null;
    farcaster_username: string | null;
    farcaster_pfp_url: string | null;
  };
}

export interface PrivateMessage {
  id: number;
  from_wallet: string;
  to_wallet: string;
  message: string;
  read: boolean;
  created_at: string;
  is_mine: boolean;
}

export interface OnlineStats {
  total_users: number;
  online_now: number;
  countries_represented: number;
}

// =========================================
// API Fetch Helper
// =========================================

// Request timeout in milliseconds
const API_TIMEOUT = 10000;

async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT);

  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'Unknown error' }));
      throw new Error(error.error || `API Error: ${response.status}`);
    }

    return response.json();
  } catch (error: any) {
    clearTimeout(timeoutId);
    if (error.name === 'AbortError') {
      throw new Error('Request timeout - server did not respond');
    }
    throw error;
  }
}

// =========================================
// Realm Status
// =========================================

export async function getRealmStatus(): Promise<RealmStatus> {
  const data = await fetchAPI<{ success: boolean; realm: RealmStatus }>('/api/realm-status');
  return data.realm;
}

// =========================================
// $EMBER Balance
// =========================================

export async function getEmberBalance(wallet: string): Promise<EmberBalance> {
  try {
    const data = await fetchAPI<{ success: boolean; ember_balance: number; total_ember_earned: number }>(
      `/api/player/${wallet}/ember`
    );
    return {
      wallet,
      balance: data.ember_balance || 0,
      total_earned: data.total_ember_earned || 0,
      pending: 0,
    };
  } catch {
    // Return zero balance if endpoint not available
    return { wallet, balance: 0, total_earned: 0, pending: 0 };
  }
}

// =========================================
// Micro-Missions
// =========================================

export async function getMicroMissions(): Promise<MicroMission[]> {
  try {
    console.debug('[MicroMissions] Fetching available missions...');
    const data = await fetchAPI<{ success: boolean; missions: any[]; count?: number }>('/api/micro-missions');

    console.debug(`[MicroMissions] Received ${data.missions?.length || 0} missions`);

    if (!data.missions || data.missions.length === 0) {
      console.warn('[MicroMissions] No missions available from API');
      return [];
    }

    // Map backend response to frontend interface
    // Backend uses pyre_reward, frontend expects ember_reward
    return data.missions.map(mission => ({
      ...mission,
      ember_reward: mission.ember_reward || mission.pyre_reward || { min: 0, max: 0 },
      xp_reward: mission.xp_reward || { min: 0, max: 0 },
    }));
  } catch (error) {
    console.error('[MicroMissions] Failed to load:', error);
    return [];
  }
}

export async function getMicroMissionDetail(id: string): Promise<MicroMissionDetail> {
  const data = await fetchAPI<{ success: boolean; mission: MicroMissionDetail }>(`/api/micro-mission/${id}`);
  return data.mission;
}

export async function startMicroMission(
  wallet: string,
  emissaryTokenId: string,
  microMissionId: string
): Promise<{
  active_micro_mission_id: number;
  mission: { id: string; name: string; narrative_intro: string; choices: any[] };
  started_at: string;
  ends_at: string;
}> {
  const data = await fetchAPI<any>('/api/micro-mission/start', {
    method: 'POST',
    body: JSON.stringify({
      wallet,
      emissary_token_id: emissaryTokenId,
      micro_mission_id: microMissionId,
    }),
  });
  return data;
}

export async function submitMicroMissionChoice(
  wallet: string,
  activeMicroMissionId: number,
  choice: string
): Promise<{ choice: string; outcome_preview: string }> {
  const data = await fetchAPI<any>('/api/micro-mission/choice', {
    method: 'POST',
    body: JSON.stringify({
      wallet,
      active_micro_mission_id: activeMicroMissionId,
      choice,
    }),
  });
  return data;
}

export async function completeMicroMission(
  wallet: string,
  activeMicroMissionId: number
): Promise<{
  rewards: MissionRewards;
  mission_name: string;
  outcome_text: string;
  choice_made: string;
}> {
  const data = await fetchAPI<any>('/api/micro-mission/complete', {
    method: 'POST',
    body: JSON.stringify({
      wallet,
      active_micro_mission_id: activeMicroMissionId,
    }),
  });
  return data;
}

export async function getActiveMicroMission(wallet: string): Promise<ActiveMicroMission | null> {
  const data = await fetchAPI<{ success: boolean; active: boolean; micro_mission?: ActiveMicroMission }>(
    `/api/micro-mission/active/${wallet}`
  );
  return data.active ? data.micro_mission! : null;
}

// =========================================
// Emissaries
// =========================================

/**
 * CRITICAL: Register wallet's NFT token_ids with the backend
 * This must be called BEFORE getWalletEmissaries to sync blockchain data
 * Replicates the portal web flow: POST token_ids -> GET heroes
 */
export async function registerWalletNFTs(
  wallet: string,
  tokenIds: string[],
  totalSupply?: number
): Promise<{ success: boolean; synced: number }> {
  if (!wallet || wallet === '0x0000000000000000000000000000000000000000') {
    console.debug('No valid wallet for NFT registration');
    return { success: false, synced: 0 };
  }

  try {
    console.debug(`[registerWalletNFTs] POSTing ${tokenIds.length} token_ids for ${wallet.slice(0, 8)}...`);

    const data = await fetchAPI<{
      success: boolean;
      token_ids_cached?: number;
      synced_to_database?: number;
    }>(`/api/player/${wallet}`, {
      method: 'POST',
      body: JSON.stringify({
        token_ids: tokenIds,
        total_supply: totalSupply,
      }),
    });

    console.debug(`[registerWalletNFTs] Backend response:`, data);
    return {
      success: data.success,
      synced: data.synced_to_database || data.token_ids_cached || 0
    };
  } catch (error) {
    console.error('[registerWalletNFTs] Error:', error);
    return { success: false, synced: 0 };
  }
}

export async function getEmissaryFullStatus(tokenId: string): Promise<Emissary> {
  const data = await fetchAPI<{ success: boolean; emissary: Emissary }>(`/api/emissary/${tokenId}/full-status`);
  return data.emissary;
}

export async function getWalletEmissaries(wallet: string): Promise<Emissary[]> {
  if (!wallet || wallet === '0x0000000000000000000000000000000000000000') {
    console.debug('[Emissaries] No valid wallet provided');
    return [];
  }

  // Normalize wallet to lowercase (backend expects lowercase)
  const normalizedWallet = wallet.toLowerCase();

  try {
    // GET player data (should be called AFTER registerWalletNFTs syncs blockchain data)
    console.debug(`[Emissaries] Fetching for wallet ${normalizedWallet.slice(0, 8)}...`);
    const data = await fetchAPI<any>(`/api/player/${normalizedWallet}`);

    // Debug: Log response structure
    console.debug('[Emissaries] API response keys:', Object.keys(data || {}));

    // Handle different API response structures
    let heroes: any[] = [];

    if (data.player?.heroes) {
      heroes = data.player.heroes;
      console.debug('[Emissaries] Found heroes in data.player.heroes');
    } else if (data.heroes) {
      heroes = data.heroes;
      console.debug('[Emissaries] Found heroes in data.heroes');
    } else if (data.emissaries) {
      heroes = data.emissaries;
      console.debug('[Emissaries] Found heroes in data.emissaries');
    } else if (Array.isArray(data)) {
      heroes = data;
      console.debug('[Emissaries] Response is array');
    } else {
      console.warn('[Emissaries] No heroes found in response. Response:', JSON.stringify(data).slice(0, 500));
    }

    console.debug(`[Emissaries] Found ${heroes.length} emissaries for wallet ${normalizedWallet.slice(0, 8)}...`);

    if (heroes.length === 0) {
      return [];
    }

    return heroes.map((hero: any) => ({
      token_id: hero.token_id || hero.tokenId || hero.id?.toString() || '0',
      name: hero.name || `Emissary #${hero.token_id || hero.tokenId || '?'}`,
      guild: hero.guild || hero.faction || 'Unknown',
      race_class: hero.race_class || hero.raceClass || hero.class || 'Unknown',
      owner: normalizedWallet,
      image_url: hero.image_url || hero.imageUrl || hero.image || '',
      stats: {
        level: hero.dynamic_state?.xp_level || hero.level || hero.stats?.level || 1,
        xp_total: hero.dynamic_state?.xp_total || hero.xp || hero.stats?.xp || 0,
        aura_level: hero.dynamic_state?.aura_level || hero.aura || hero.stats?.aura || 0,
        energy_current: hero.dynamic_state?.energy_current || hero.energy || hero.stats?.energy || 100,
        energy_max: hero.dynamic_state?.energy_max || hero.maxEnergy || hero.stats?.maxEnergy || 100,
        power: hero.dynamic_state?.power_current || hero.power || hero.stats?.power || 10,
        death_count: hero.dynamic_state?.death_count || hero.deaths || hero.stats?.deaths || 0,
      },
      current_state: hero.dynamic_state?.state || hero.state || hero.status || 'READY',
      active_mission: hero.active_mission || null,
      active_micro_mission: hero.active_micro_mission || null,
      equipment: hero.equipment || {},
      chronicle: {
        total_missions: hero.dynamic_state?.total_missions_completed || hero.missions || 0,
        total_deaths: hero.dynamic_state?.death_count || hero.deaths || 0,
        items_found: hero.dynamic_state?.items_found || hero.items || 0,
        runes_found: hero.dynamic_state?.runes_found || hero.runes || 0,
      },
    }));
  } catch (error) {
    console.error('[Emissaries] Error fetching:', error);
    return [];
  }
}

// =========================================
// Social - Profile
// =========================================

export async function getProfile(wallet: string): Promise<UserProfile | null> {
  const data = await fetchAPI<{ success: boolean; profile: UserProfile | null }>(
    `/api/social/profile/${wallet}`
  );
  return data.profile;
}

export async function updateProfile(params: {
  wallet: string;
  country_code?: string;
  display_name?: string;
  farcaster_fid?: number;
  farcaster_username?: string;
  farcaster_pfp_url?: string;
}): Promise<UserProfile> {
  const data = await fetchAPI<{ success: boolean; profile: UserProfile }>('/api/social/profile', {
    method: 'POST',
    body: JSON.stringify(params),
  });
  return data.profile;
}

// =========================================
// Social - Countries (for 3D Globe)
// =========================================

export async function getCountries(): Promise<CountryStats[]> {
  try {
    const data = await fetchAPI<{ success: boolean; countries: CountryStats[] }>('/api/social/countries');
    return data.countries || [];
  } catch (error) {
    console.error('Failed to load countries:', error);
    return [];
  }
}

export async function getCountryUsers(countryCode: string): Promise<CountryUser[]> {
  try {
    const data = await fetchAPI<{ success: boolean; users: CountryUser[] }>(
      `/api/social/country/${countryCode}/users`
    );
    return data.users || [];
  } catch (error) {
    console.error('Failed to load country users:', error);
    return [];
  }
}

export async function getOnlineStats(): Promise<OnlineStats | null> {
  try {
    const data = await fetchAPI<{ success: boolean; stats: OnlineStats }>('/api/social/online-stats');
    return data.stats || null;
  } catch (error) {
    console.error('Failed to load online stats:', error);
    return null;
  }
}

// =========================================
// Social - Chat (1:1 Private Messages)
// =========================================

export async function getConversations(wallet: string): Promise<Conversation[]> {
  const data = await fetchAPI<{ success: boolean; conversations: Conversation[] }>(
    `/api/social/conversations/${wallet}`
  );
  return data.conversations;
}

export async function getMessages(wallet: string, otherWallet: string, limit = 50): Promise<PrivateMessage[]> {
  const data = await fetchAPI<{ success: boolean; messages: PrivateMessage[] }>(
    `/api/social/messages/${wallet}/${otherWallet}?limit=${limit}`
  );
  return data.messages;
}

export async function sendMessage(fromWallet: string, toWallet: string, message: string): Promise<PrivateMessage> {
  const data = await fetchAPI<{ success: boolean; message: PrivateMessage }>('/api/social/message', {
    method: 'POST',
    body: JSON.stringify({
      from_wallet: fromWallet,
      to_wallet: toWallet,
      message,
    }),
  });
  return data.message;
}

export async function markMessagesRead(wallet: string, fromWallet: string): Promise<number> {
  const data = await fetchAPI<{ success: boolean; marked_read: number }>('/api/social/message/read', {
    method: 'POST',
    body: JSON.stringify({
      wallet,
      from_wallet: fromWallet,
    }),
  });
  return data.marked_read;
}

// =========================================
// Social - Global Chat
// =========================================

export interface GlobalMessage {
  id: number;
  wallet: string;
  display_name: string | null;
  farcaster_username: string | null;
  farcaster_pfp_url: string | null;
  message: string;
  created_at: string;
}

export async function getGlobalMessages(limit = 100, before_id?: number): Promise<GlobalMessage[]> {
  const params = new URLSearchParams({ limit: String(limit) });
  if (before_id) params.append('before_id', String(before_id));

  try {
    const data = await fetchAPI<{ success: boolean; messages: GlobalMessage[] }>(
      `/api/social/global-chat?${params}`
    );
    return data.messages;
  } catch {
    // Return mock data if endpoint doesn't exist yet
    return [];
  }
}

export async function sendGlobalMessage(wallet: string, message: string): Promise<GlobalMessage> {
  const data = await fetchAPI<{ success: boolean; message: GlobalMessage }>('/api/social/global-chat', {
    method: 'POST',
    body: JSON.stringify({ wallet, message }),
  });
  return data.message;
}

// =========================================
// Social - All Operators (NFT Holders)
// =========================================

export async function getAllOperators(limit = 100, offset = 0): Promise<CountryUser[]> {
  try {
    const data = await fetchAPI<{ success: boolean; users: CountryUser[] }>(
      `/api/social/operators?limit=${limit}&offset=${offset}`
    );
    return data.users;
  } catch {
    // Return mock data if endpoint doesn't exist yet
    return [];
  }
}

// =========================================
// Events
// =========================================

export interface GameEvent {
  id: string;
  name: string;
  difficulty: 'EASY' | 'MEDIUM' | 'HARD' | 'HEROIC' | 'LEGENDARY';
  duration_hours: number;
  energy_cost: number;
  reward_xp: number;
  reward_aura: number;
  success_rate: number;
  xp_loss_on_fail: number;
  death_chance: number;
  available_from: string;
  available_until: string;
  event_active: boolean;
  favored_guild: string | null;
  favored_class: string | null;
  favored_race: string | null;
  description: string;
  lore: string;
  time_remaining_hours?: number;
}

export interface EventSettings {
  max_concurrent_events: number;
  cooldown_hours: number;
  bonus_multiplier: number;
}

export async function getEvents(): Promise<{ events: GameEvent[]; event_settings: EventSettings | null }> {
  try {
    const data = await fetchAPI<{ events: GameEvent[]; event_settings: EventSettings }>('/api/events');
    return {
      events: data.events || [],
      event_settings: data.event_settings || null,
    };
  } catch (error) {
    console.error('Failed to load events:', error);
    return { events: [], event_settings: null };
  }
}
