'use client';

import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';

/**
 * CountrySelect - Country selection screen
 * Scrollable list with flags, search functionality, alphabetically sorted
 */

interface CountrySelectProps {
  onSelect: (countryCode: string) => void;
  onBack?: () => void;
}

// Full list of countries with flags (emoji)
const COUNTRIES = [
  { code: 'AF', name: 'Afghanistan', flag: '🇦🇫' },
  { code: 'AL', name: 'Albania', flag: '🇦🇱' },
  { code: 'DZ', name: 'Algeria', flag: '🇩🇿' },
  { code: 'AR', name: 'Argentina', flag: '🇦🇷' },
  { code: 'AU', name: 'Australia', flag: '🇦🇺' },
  { code: 'AT', name: 'Austria', flag: '🇦🇹' },
  { code: 'BE', name: 'Belgium', flag: '🇧🇪' },
  { code: 'BR', name: 'Brazil', flag: '🇧🇷' },
  { code: 'CA', name: 'Canada', flag: '🇨🇦' },
  { code: 'CL', name: 'Chile', flag: '🇨🇱' },
  { code: 'CN', name: 'China', flag: '🇨🇳' },
  { code: 'CO', name: 'Colombia', flag: '🇨🇴' },
  { code: 'HR', name: 'Croatia', flag: '🇭🇷' },
  { code: 'CZ', name: 'Czech Republic', flag: '🇨🇿' },
  { code: 'DK', name: 'Denmark', flag: '🇩🇰' },
  { code: 'EG', name: 'Egypt', flag: '🇪🇬' },
  { code: 'FI', name: 'Finland', flag: '🇫🇮' },
  { code: 'FR', name: 'France', flag: '🇫🇷' },
  { code: 'DE', name: 'Germany', flag: '🇩🇪' },
  { code: 'GR', name: 'Greece', flag: '🇬🇷' },
  { code: 'HK', name: 'Hong Kong', flag: '🇭🇰' },
  { code: 'HU', name: 'Hungary', flag: '🇭🇺' },
  { code: 'IN', name: 'India', flag: '🇮🇳' },
  { code: 'ID', name: 'Indonesia', flag: '🇮🇩' },
  { code: 'IE', name: 'Ireland', flag: '🇮🇪' },
  { code: 'IL', name: 'Israel', flag: '🇮🇱' },
  { code: 'IT', name: 'Italy', flag: '🇮🇹' },
  { code: 'JP', name: 'Japan', flag: '🇯🇵' },
  { code: 'KR', name: 'South Korea', flag: '🇰🇷' },
  { code: 'MY', name: 'Malaysia', flag: '🇲🇾' },
  { code: 'MX', name: 'Mexico', flag: '🇲🇽' },
  { code: 'NL', name: 'Netherlands', flag: '🇳🇱' },
  { code: 'NZ', name: 'New Zealand', flag: '🇳🇿' },
  { code: 'NO', name: 'Norway', flag: '🇳🇴' },
  { code: 'PK', name: 'Pakistan', flag: '🇵🇰' },
  { code: 'PE', name: 'Peru', flag: '🇵🇪' },
  { code: 'PH', name: 'Philippines', flag: '🇵🇭' },
  { code: 'PL', name: 'Poland', flag: '🇵🇱' },
  { code: 'PT', name: 'Portugal', flag: '🇵🇹' },
  { code: 'RO', name: 'Romania', flag: '🇷🇴' },
  { code: 'RU', name: 'Russia', flag: '🇷🇺' },
  { code: 'SA', name: 'Saudi Arabia', flag: '🇸🇦' },
  { code: 'SG', name: 'Singapore', flag: '🇸🇬' },
  { code: 'ZA', name: 'South Africa', flag: '🇿🇦' },
  { code: 'ES', name: 'Spain', flag: '🇪🇸' },
  { code: 'SE', name: 'Sweden', flag: '🇸🇪' },
  { code: 'CH', name: 'Switzerland', flag: '🇨🇭' },
  { code: 'TW', name: 'Taiwan', flag: '🇹🇼' },
  { code: 'TH', name: 'Thailand', flag: '🇹🇭' },
  { code: 'TR', name: 'Turkey', flag: '🇹🇷' },
  { code: 'UA', name: 'Ukraine', flag: '🇺🇦' },
  { code: 'AE', name: 'UAE', flag: '🇦🇪' },
  { code: 'GB', name: 'United Kingdom', flag: '🇬🇧' },
  { code: 'US', name: 'United States', flag: '🇺🇸' },
  { code: 'VN', name: 'Vietnam', flag: '🇻🇳' },
  { code: 'OTHER', name: 'Other', flag: '🌍' },
].sort((a, b) => a.name.localeCompare(b.name));

export function CountrySelect({ onSelect, onBack }: CountrySelectProps) {
  const [search, setSearch] = useState('');
  const [selectedCountry, setSelectedCountry] = useState<string | null>(null);

  // Filter countries based on search
  const filteredCountries = useMemo(() => {
    if (!search.trim()) return COUNTRIES;
    const searchLower = search.toLowerCase();
    return COUNTRIES.filter(
      c => c.name.toLowerCase().includes(searchLower) ||
           c.code.toLowerCase().includes(searchLower)
    );
  }, [search]);

  const handleSelect = (code: string) => {
    setSelectedCountry(code);
  };

  const handleContinue = () => {
    if (selectedCountry) {
      // Save to localStorage for persistence
      localStorage.setItem('emberholm_country', selectedCountry);
      onSelect(selectedCountry);
    }
  };

  return (
    <div className="screen-view flex flex-col min-h-screen p-4">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-4"
      >
        <h2 className="title text-xl mb-1">SELECT YOUR COUNTRY</h2>
        <p className="text-amber-dim text-xs">You'll appear on the World Map</p>
      </motion.div>

      {/* Search Input */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.1 }}
        className="mb-4"
      >
        <input
          type="text"
          placeholder="Search country..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full bg-bg-dark border border-amber-dark text-amber px-4 py-3 text-sm
                     focus:border-amber focus:outline-none placeholder:text-amber-darker"
        />
      </motion.div>

      {/* Country List - Scrollable */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="flex-1 overflow-y-auto scroll-area"
      >
        <div className="country-grid">
          {filteredCountries.map((country, index) => (
            <motion.button
              key={country.code}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.02 * index }}
              onClick={() => handleSelect(country.code)}
              className={`country-btn ${selectedCountry === country.code ? 'selected' : ''}`}
            >
              <span className="flag">{country.flag}</span>
              <span className="truncate">{country.name}</span>
            </motion.button>
          ))}
        </div>

        {filteredCountries.length === 0 && (
          <p className="text-center text-amber-dim text-sm py-8">
            No countries found matching "{search}"
          </p>
        )}
      </motion.div>

      {/* Privacy note */}
      <p className="text-center text-amber-darker text-xs my-3">
        Only your country will be shown publicly
      </p>

      {/* Continue button */}
      <motion.button
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
        onClick={handleContinue}
        disabled={!selectedCountry}
        className={`btn w-full ${!selectedCountry ? 'opacity-50 cursor-not-allowed' : ''}`}
      >
        [ CONTINUE ]
      </motion.button>
    </div>
  );
}
