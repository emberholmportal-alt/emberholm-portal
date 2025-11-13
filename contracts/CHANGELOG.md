# EmberholmPortal V2 - Ultra-Lightweight Contract

## 🚀 Version 2.0 - Backend-First Design (ZERO Gas for Gameplay)

This is a **NEW** contract with MINIMAL on-chain footprint. The old contract (`0x2F55...c47`) will be replaced.

**Design Philosophy:** Backend-first approach - on-chain ONLY for critical security (staking), everything else in backend/metadata for ZERO gas costs.

**💰 Cost Savings:**
- ❌ $0 gas for achievements (Backend + Metadata)
- ❌ $0 gas for guild changes (Backend + Metadata)
- ❌ $0 gas for name updates (Backend + Metadata)
- ❌ $0 gas for guild leadership (Backend database)
- ✅ Everything appears in OpenSea via metadata attributes!

---

## ✨ What's New vs Old Contract

### Old Contract (V1)
- ❌ Basic ERC721 only
- ❌ No totalMinted() function
- ❌ No tokensOfOwner() function
- ❌ tokenOfOwnerByIndex() didn't exist (non-Enumerable)
- ❌ Caused "CALL_EXCEPTION" errors
- ❌ Frontend had to scan blockchain events

### New Contract (V2) ✅
- ✅ Ultra-lightweight TIER 1+2 features
- ✅ All query functions work perfectly
- ✅ No blockchain scanning needed
- ✅ Backend-first: guilds, names, achievements in metadata (FREE!)
- ✅ Staking on-chain (CRITICAL security)
- ✅ Prepared for future items
- ✅ Production-ready

---

## 📦 Feature Breakdown

### TIER 1: Essential Query Functions

#### totalMinted()
```solidity
function totalMinted() public view returns (uint256)
```
**What it does:** Returns how many NFTs have been minted (e.g., 150 out of 35,000)
**Why important:** Frontend knows range to query, STATS shows correct number

#### tokensOfOwner(address)
```solidity
function tokensOfOwner(address owner) public view returns (uint256[] memory)
```
**What it does:** Returns all token IDs owned by an address
**Example:** `[1, 42, 150]` - user owns 3 NFTs
**Why important:** PROFILE/ROSTER shows all user's NFTs in ONE call

#### getTokenInfo(uint256)
```solidity
function getTokenInfo(uint256 tokenId) public view returns (TokenInfo memory)
```
**What it does:** Returns on-chain info for one token
**Returns:**
```javascript
{
    tokenId: 42,
    owner: "0x...",
    isStaked: false
    // Note: guild, name, and achievements are in metadata
}
```
**Why important:** Quick access to on-chain state (staking status)
**Note:** Guild, name, and achievements are in metadata - frontend fetches from tokenURI

---

### TIER 2: Performance & Gameplay

#### batchGetTokenInfo()
```solidity
function batchGetTokenInfo(uint256[] tokenIds) external view returns (TokenInfo[] memory)
```
**What it does:** Get info for MULTIPLE tokens in ONE call
**Example:** Get info for 10 NFTs → 1 call instead of 10
**Why important:** ROSTER loads 10x faster

#### getWalletProfile()
```solidity
function getWalletProfile(address owner) external view returns (
    uint256[] tokenIds,
    TokenInfo[] tokens,
    WalletStats stats
)
```
**What it does:** Get on-chain wallet data in ONE call
**Returns:**
```javascript
{
    tokenIds: [1, 42, 150],
    tokens: [{tokenId, owner, isStaked}, ...],
    stats: {
        totalTokens: 3,
        stakedCount: 1
    }
}
```
**Why important:** Efficient on-chain data fetching, combine with metadata for complete profile

#### Staking System (CRITICAL - On-Chain)
```solidity
function stakeToken(uint256 tokenId) external
function unstakeToken(uint256 tokenId) external
```
**What it does:** Lock NFT during missions (cannot transfer while staked)
**Why important:**
- ✅ Prevents exploits (selling NFT while in mission)
- ✅ Backend can unstake when mission ends
- ✅ On-chain verification of "in mission" status
- ✅ THIS MUST BE ON-CHAIN for security!

#### Primary Token
```solidity
function setPrimaryToken(uint256 tokenId) external
function getPrimaryTokenInfo(address owner) external view returns (TokenInfo)
```
**What it does:** User selects which NFT shows in TOP EMISSARY
**Why important:** User chooses their favorite/strongest to display

---

### TIER 3: Equipment System (Future)

#### Equipment System (Prepared for Items)
```solidity
function setItemsContract(address) external onlyOwner
function equipItem(uint256 tokenId, string slot, uint256 itemId) external
function unequipItem(uint256 tokenId, string slot) external
function getEquippedItems(uint256 tokenId) external view returns (uint256, uint256, uint256, uint256)
function getTotalStats(uint256 tokenId) external view returns (uint16, uint16, uint16, uint16)
```
**What it does:** NFTs can equip items in 4 slots:
- weapon
- armor
- boots
- accessory

**Initially:** No items contract, slots empty
**Later:** Deploy separate Items contract (ERC1155), connect it, items work!

**Why important:**
- Progression system
- RPG mechanics
- Collectible items
- No need to redeploy NFT contract

---

## 🆓 Backend-First Features (ZERO Gas!)

### ✅ Guild Membership (Backend + Metadata)
**Implementation:** Backend database + metadata attributes
**Storage:**
```python
# Backend database or metadata JSON
{
  "attributes": [
    {"trait_type": "Starting Guild", "value": "Circle of Mist"},
    {"trait_type": "Current Guild", "value": "Shadow Guild"},
  ]
}
```
**Appears in:** Your portal + OpenSea
**Cost:** $0 (FREE!)
**Flexibility:** Backend can change guild instantly without blockchain transaction

**Guilds:** Circle of Mist, Order of Dawn, Horizon Watch, Shadow Guild, Forge Legion, Void Echoes

---

### ✅ Character Names (Backend + Metadata)
**Implementation:** Fixed in metadata
**Storage:**
```python
{
  "name": "Ormary, Bearer of Cover the Last Soldier",
  "attributes": [
    {"trait_type": "Character Name", "value": "Ormary"}
  ]
}
```
**Appears in:** Your portal + OpenSea
**Cost:** $0 (FREE!)
**Note:** Names are FIXED (don't change)

---

### ✅ Achievements System (Backend + Metadata)
**Implementation:** Backend database + metadata attributes
**Storage:**
```python
# Backend tracks achievements per token_id
achievements_db = {
  "42": ["first_mission", "100_missions", "guild_champion"]
}

# Metadata shows:
{
  "attributes": [
    {"trait_type": "Achievement: First Mission", "value": "✅"},
    {"trait_type": "Achievement: 100 Missions", "value": "✅"},
    {"trait_type": "Achievement: Guild Champion", "value": "✅"},
    {"display_type": "number", "trait_type": "Total Achievements", "value": 3}
  ]
}
```
**Appears in:** Your portal + OpenSea
**Cost:** $0 (FREE! No gas to grant achievements)

**Example Achievements:**
- "First Mission Complete"
- "100 Missions Completed"
- "Dragon Slayer"
- "Guild Master"
- "Legendary Fighter"
- Unlimited possibilities!

---

### ✅ Guild Leadership (Backend Database)
**Implementation:** Backend database
**Storage:**
```python
# Backend database
guild_leaders = {
  0: "0xLeaderAddress...",  # Circle of Mist
  1: "0xAnotherAddress...",  # Order of Dawn
  # ...
}

guild_officers = {
  0: ["0xOfficer1...", "0xOfficer2..."],
  # ...
}
```
**Display:** Portal shows badges/icons for leaders
**Cost:** $0 (FREE! Change leaders anytime)
**Flexibility:** Backend can implement custom governance logic

---

## 📊 Comparison: On-Chain vs Backend

| Feature | On-Chain (Gas Cost) | Backend (FREE) | Recommendation |
|---------|---------------------|----------------|----------------|
| **Ownership** | ✅ ERC721 | ❌ | ✅ On-Chain (REQUIRED) |
| **Staking** | ✅ $0.50-$2 per stake/unstake | ❌ | ✅ On-Chain (SECURITY) |
| **Achievements** | ❌ $0.10-$0.50 per grant | ✅ FREE | ✅ Backend (SAVES $$) |
| **Guild Changes** | ❌ $0.50-$2 per change | ✅ FREE | ✅ Backend (SAVES $$) |
| **Names** | ❌ $1-$5 per change | ✅ FREE (fixed) | ✅ Backend (SAVES $$) |
| **Guild Leadership** | ❌ $1-$5 per change | ✅ FREE | ✅ Backend (SAVES $$) |
| **Equipment** | ✅ $0.50-$2 per equip | ❌ | ✅ On-Chain (ITEMS) |

**Total Savings:** Hundreds of dollars in gas per day! 🎉

---

## 🎮 How It Works

### Minting Flow:
```
1. User mints NFT → Contract emits token
2. Backend detects mint event
3. Backend generates metadata with:
   - starting_guild (random)
   - name (generated or user-chosen)
   - initial stats (XP: 0, Aura: 50)
4. tokenURI points to: https://emberholm-portal.onrender.com/api/metadata/42
5. OpenSea fetches metadata → Shows all attributes
```

### Mission Flow:
```
1. User starts mission in Portal
2. Backend calls contract.stakeToken(tokenId) → NFT locked
3. Mission runs (backend tracks progress)
4. Mission completes → Backend grants achievement (FREE!)
5. Backend updates metadata → New achievement appears
6. Backend calls contract.unstakeToken(tokenId) → NFT unlocked
7. OpenSea refreshes metadata → Shows new achievement! 🏆
```

### Guild Change Flow:
```
1. User completes guild quest
2. Backend changes current_guild in metadata
3. Backend regenerates metadata JSON
4. Frontend/OpenSea shows new guild
5. ZERO gas cost! 🎉
```

---

## 📝 Summary

### ✅ What's On-Chain (Essential Only):
- ERC721 ownership (REQUIRED)
- Staking system (SECURITY - prevents transfers during missions)
- Primary token selection (user preference)
- Equipment slots (future Items integration)
- Query functions (totalMinted, tokensOfOwner, etc)

### ✅ What's Off-Chain (Backend + Metadata):
- Guild membership (starting_guild, current_guild)
- Character names (fixed)
- Achievements (unlimited, FREE!)
- Guild leadership (flexible governance)
- Game stats (XP, Aura, level)
- Mission history
- Dynamic attributes

### 💰 Cost Comparison:

**If everything on-chain:**
- Mint: $2-$5
- Grant achievement: $0.10-$0.50
- Change guild: $0.50-$2
- **1000 users × 10 achievements = $1,000-$5,000 in gas!** 😱

**Backend-first approach:**
- Mint: $2-$5
- Grant achievement: FREE
- Change guild: FREE
- **1000 users × 10 achievements = $0 in gas!** 🎉

### 🏆 Best of Both Worlds:
- ✅ Blockchain security (staking, ownership)
- ✅ Zero gas for gameplay (achievements, guilds)
- ✅ Appears in OpenSea (metadata attributes)
- ✅ Full flexibility (backend can do anything)
- ✅ Ultra-lightweight contract
- ✅ Production-ready NOW

---

## 🚀 Ready to Deploy!

**You can:**
- Deploy to Base Sepolia NOW (testnet)
- Test everything
- Deploy to Base Mainnet when ready (same code)
- Never need to redeploy
- Change guilds, grant achievements, all FREE via backend

**See `DEPLOYMENT.md` for step-by-step instructions.**
