/**
 * EMBERHOLM MINI APP - API Client v2
 * Connects to Flask backend endpoints
 * Includes: Realm Status, $PYRE, Micro-Missions, Social Chat
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
// Types - $PYRE
// =========================================

export interface PyreBalance {
  wallet: string;
  balance: number;
  total_earned: number;
  total_spent: number;
  daily_streak: number;
  daily_available: boolean;
}

export interface PyreTransaction {
  id: number;
  amount: number;
  type: string;
  reference_id: string;
  description: string;
  created_at: string;
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
  pyre_reward: { min: number; max: number };
  xp_reward: { min: number; max: number };
  aura_chance: number;
  narrative_intro: string;
  cooldown_minutes: number;
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
    pyre_modifier: number;
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
  pyre: number;
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

async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Unknown error' }));
    throw new Error(error.error || `API Error: ${response.status}`);
  }

  return response.json();
}

// =========================================
// Realm Status
// =========================================

export async function getRealmStatus(): Promise<RealmStatus> {
  const data = await fetchAPI<{ success: boolean; realm: RealmStatus }>('/api/realm-status');
  return data.realm;
}

// =========================================
// $PYRE
// =========================================

export async function getPyreBalance(wallet: string): Promise<PyreBalance> {
  const data = await fetchAPI<{ success: boolean } & PyreBalance>(`/api/pyre/${wallet}`);
  return data;
}

export async function getPyreHistory(wallet: string, limit = 50): Promise<PyreTransaction[]> {
  const data = await fetchAPI<{ success: boolean; transactions: PyreTransaction[] }>(
    `/api/pyre/history/${wallet}?limit=${limit}`
  );
  return data.transactions;
}

// =========================================
// Micro-Missions
// =========================================

export async function getMicroMissions(): Promise<MicroMission[]> {
  const data = await fetchAPI<{ success: boolean; missions: MicroMission[] }>('/api/micro-missions');
  return data.missions;
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

export async function getEmissaryFullStatus(tokenId: string): Promise<Emissary> {
  const data = await fetchAPI<{ success: boolean; emissary: Emissary }>(`/api/emissary/${tokenId}/full-status`);
  return data.emissary;
}

export async function getWalletEmissaries(wallet: string): Promise<Emissary[]> {
  try {
    const data = await fetchAPI<any>(`/api/player/${wallet}`);
    const heroes = data.player?.heroes || [];

    return heroes.map((hero: any) => ({
      token_id: hero.token_id,
      name: hero.name || `Emissary #${hero.token_id}`,
      guild: hero.guild || 'Unknown',
      race_class: hero.race_class || 'Unknown',
      owner: wallet,
      image_url: hero.image_url || '',
      stats: {
        level: hero.dynamic_state?.xp_level || 1,
        xp_total: hero.dynamic_state?.xp_total || 0,
        aura_level: hero.dynamic_state?.aura_level || 0,
        energy_current: hero.dynamic_state?.energy_current || 100,
        energy_max: hero.dynamic_state?.energy_max || 100,
        power: hero.dynamic_state?.power_current || 10,
        death_count: hero.dynamic_state?.death_count || 0,
      },
      current_state: hero.dynamic_state?.state || 'READY',
      active_mission: null,
      active_micro_mission: null,
      equipment: {},
      chronicle: {
        total_missions: hero.dynamic_state?.total_missions_completed || 0,
        total_deaths: hero.dynamic_state?.death_count || 0,
        items_found: hero.dynamic_state?.items_found || 0,
        runes_found: hero.dynamic_state?.runes_found || 0,
      },
    }));
  } catch (error) {
    console.error('Error fetching emissaries:', error);
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
  const data = await fetchAPI<{ success: boolean; countries: CountryStats[] }>('/api/social/countries');
  return data.countries;
}

export async function getCountryUsers(countryCode: string): Promise<CountryUser[]> {
  const data = await fetchAPI<{ success: boolean; users: CountryUser[] }>(
    `/api/social/country/${countryCode}/users`
  );
  return data.users;
}

export async function getOnlineStats(): Promise<OnlineStats> {
  const data = await fetchAPI<{ success: boolean; stats: OnlineStats }>('/api/social/online-stats');
  return data.stats;
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
// Social - NFT Stats (Emissary Census)
// =========================================

export interface NftStats {
  total_minted: number;
  registered: number;
  unregistered: number;
}

export async function getNftStats(): Promise<NftStats> {
  try {
    const data = await fetchAPI<{ success: boolean; stats: NftStats }>('/api/social/nft-stats');
    return data.stats;
  } catch {
    // Return default stats if endpoint fails
    return { total_minted: 0, registered: 0, unregistered: 0 };
  }
}
