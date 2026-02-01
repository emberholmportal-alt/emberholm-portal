/**
 * EMBERHOLM PORTAL - Countries Data
 * ISO 3166-1 alpha-2 country codes with flags, names, and coordinates for 3D globe
 */

const COUNTRIES_DATA = [
    // Popular countries first
    { code: "US", name: "United States", flag: "\ud83c\uddfa\ud83c\uddf8", lat: 37.0902, lon: -95.7129, popular: true },
    { code: "GB", name: "United Kingdom", flag: "\ud83c\uddec\ud83c\udde7", lat: 55.3781, lon: -3.4360, popular: true },
    { code: "JP", name: "Japan", flag: "\ud83c\uddef\ud83c\uddf5", lat: 36.2048, lon: 138.2529, popular: true },
    { code: "BR", name: "Brazil", flag: "\ud83c\udde7\ud83c\uddf7", lat: -14.2350, lon: -51.9253, popular: true },
    { code: "DE", name: "Germany", flag: "\ud83c\udde9\ud83c\uddea", lat: 51.1657, lon: 10.4515, popular: true },
    { code: "FR", name: "France", flag: "\ud83c\uddeb\ud83c\uddf7", lat: 46.2276, lon: 2.2137, popular: true },
    { code: "ES", name: "Spain", flag: "\ud83c\uddea\ud83c\uddf8", lat: 40.4637, lon: -3.7492, popular: true },
    { code: "KR", name: "South Korea", flag: "\ud83c\uddf0\ud83c\uddf7", lat: 35.9078, lon: 127.7669, popular: true },

    // All countries alphabetically
    { code: "AF", name: "Afghanistan", flag: "\ud83c\udde6\ud83c\uddeb", lat: 33.9391, lon: 67.7100 },
    { code: "AL", name: "Albania", flag: "\ud83c\udde6\ud83c\uddf1", lat: 41.1533, lon: 20.1683 },
    { code: "DZ", name: "Algeria", flag: "\ud83c\udde9\ud83c\uddff", lat: 28.0339, lon: 1.6596 },
    { code: "AD", name: "Andorra", flag: "\ud83c\udde6\ud83c\udde9", lat: 42.5063, lon: 1.5218 },
    { code: "AO", name: "Angola", flag: "\ud83c\udde6\ud83c\uddf4", lat: -11.2027, lon: 17.8739 },
    { code: "AG", name: "Antigua and Barbuda", flag: "\ud83c\udde6\ud83c\uddec", lat: 17.0608, lon: -61.7964 },
    { code: "AR", name: "Argentina", flag: "\ud83c\udde6\ud83c\uddf7", lat: -38.4161, lon: -63.6167 },
    { code: "AM", name: "Armenia", flag: "\ud83c\udde6\ud83c\uddf2", lat: 40.0691, lon: 45.0382 },
    { code: "AU", name: "Australia", flag: "\ud83c\udde6\ud83c\uddfa", lat: -25.2744, lon: 133.7751 },
    { code: "AT", name: "Austria", flag: "\ud83c\udde6\ud83c\uddf9", lat: 47.5162, lon: 14.5501 },
    { code: "AZ", name: "Azerbaijan", flag: "\ud83c\udde6\ud83c\uddff", lat: 40.1431, lon: 47.5769 },
    { code: "BS", name: "Bahamas", flag: "\ud83c\udde7\ud83c\uddf8", lat: 25.0343, lon: -77.3963 },
    { code: "BH", name: "Bahrain", flag: "\ud83c\udde7\ud83c\udded", lat: 25.9304, lon: 50.6378 },
    { code: "BD", name: "Bangladesh", flag: "\ud83c\udde7\ud83c\udde9", lat: 23.6850, lon: 90.3563 },
    { code: "BB", name: "Barbados", flag: "\ud83c\udde7\ud83c\udde7", lat: 13.1939, lon: -59.5432 },
    { code: "BY", name: "Belarus", flag: "\ud83c\udde7\ud83c\uddfe", lat: 53.7098, lon: 27.9534 },
    { code: "BE", name: "Belgium", flag: "\ud83c\udde7\ud83c\uddea", lat: 50.5039, lon: 4.4699 },
    { code: "BZ", name: "Belize", flag: "\ud83c\udde7\ud83c\uddff", lat: 17.1899, lon: -88.4976 },
    { code: "BJ", name: "Benin", flag: "\ud83c\udde7\ud83c\uddef", lat: 9.3077, lon: 2.3158 },
    { code: "BT", name: "Bhutan", flag: "\ud83c\udde7\ud83c\uddf9", lat: 27.5142, lon: 90.4336 },
    { code: "BO", name: "Bolivia", flag: "\ud83c\udde7\ud83c\uddf4", lat: -16.2902, lon: -63.5887 },
    { code: "BA", name: "Bosnia and Herzegovina", flag: "\ud83c\udde7\ud83c\udde6", lat: 43.9159, lon: 17.6791 },
    { code: "BW", name: "Botswana", flag: "\ud83c\udde7\ud83c\uddfc", lat: -22.3285, lon: 24.6849 },
    { code: "BN", name: "Brunei", flag: "\ud83c\udde7\ud83c\uddf3", lat: 4.5353, lon: 114.7277 },
    { code: "BG", name: "Bulgaria", flag: "\ud83c\udde7\ud83c\uddec", lat: 42.7339, lon: 25.4858 },
    { code: "BF", name: "Burkina Faso", flag: "\ud83c\udde7\ud83c\uddeb", lat: 12.2383, lon: -1.5616 },
    { code: "BI", name: "Burundi", flag: "\ud83c\udde7\ud83c\uddee", lat: -3.3731, lon: 29.9189 },
    { code: "CV", name: "Cabo Verde", flag: "\ud83c\udde8\ud83c\uddfb", lat: 16.5388, lon: -23.0418 },
    { code: "KH", name: "Cambodia", flag: "\ud83c\uddf0\ud83c\udded", lat: 12.5657, lon: 104.9910 },
    { code: "CM", name: "Cameroon", flag: "\ud83c\udde8\ud83c\uddf2", lat: 7.3697, lon: 12.3547 },
    { code: "CA", name: "Canada", flag: "\ud83c\udde8\ud83c\udde6", lat: 56.1304, lon: -106.3468 },
    { code: "CF", name: "Central African Republic", flag: "\ud83c\udde8\ud83c\uddeb", lat: 6.6111, lon: 20.9394 },
    { code: "TD", name: "Chad", flag: "\ud83c\uddf9\ud83c\udde9", lat: 15.4542, lon: 18.7322 },
    { code: "CL", name: "Chile", flag: "\ud83c\udde8\ud83c\uddf1", lat: -35.6751, lon: -71.5430 },
    { code: "CN", name: "China", flag: "\ud83c\udde8\ud83c\uddf3", lat: 35.8617, lon: 104.1954 },
    { code: "CO", name: "Colombia", flag: "\ud83c\udde8\ud83c\uddf4", lat: 4.5709, lon: -74.2973 },
    { code: "KM", name: "Comoros", flag: "\ud83c\uddf0\ud83c\uddf2", lat: -11.6455, lon: 43.3333 },
    { code: "CG", name: "Congo", flag: "\ud83c\udde8\ud83c\uddec", lat: -0.2280, lon: 15.8277 },
    { code: "CR", name: "Costa Rica", flag: "\ud83c\udde8\ud83c\uddf7", lat: 9.7489, lon: -83.7534 },
    { code: "HR", name: "Croatia", flag: "\ud83c\udded\ud83c\uddf7", lat: 45.1000, lon: 15.2000 },
    { code: "CU", name: "Cuba", flag: "\ud83c\udde8\ud83c\uddfa", lat: 21.5218, lon: -77.7812 },
    { code: "CY", name: "Cyprus", flag: "\ud83c\udde8\ud83c\uddfe", lat: 35.1264, lon: 33.4299 },
    { code: "CZ", name: "Czechia", flag: "\ud83c\udde8\ud83c\uddff", lat: 49.8175, lon: 15.4730 },
    { code: "DK", name: "Denmark", flag: "\ud83c\udde9\ud83c\uddf0", lat: 56.2639, lon: 9.5018 },
    { code: "DJ", name: "Djibouti", flag: "\ud83c\udde9\ud83c\uddef", lat: 11.8251, lon: 42.5903 },
    { code: "DM", name: "Dominica", flag: "\ud83c\udde9\ud83c\uddf2", lat: 15.4150, lon: -61.3710 },
    { code: "DO", name: "Dominican Republic", flag: "\ud83c\udde9\ud83c\uddf4", lat: 18.7357, lon: -70.1627 },
    { code: "EC", name: "Ecuador", flag: "\ud83c\uddea\ud83c\udde8", lat: -1.8312, lon: -78.1834 },
    { code: "EG", name: "Egypt", flag: "\ud83c\uddea\ud83c\uddec", lat: 26.8206, lon: 30.8025 },
    { code: "SV", name: "El Salvador", flag: "\ud83c\uddf8\ud83c\uddfb", lat: 13.7942, lon: -88.8965 },
    { code: "GQ", name: "Equatorial Guinea", flag: "\ud83c\uddec\ud83c\uddf6", lat: 1.6508, lon: 10.2679 },
    { code: "ER", name: "Eritrea", flag: "\ud83c\uddea\ud83c\uddf7", lat: 15.1794, lon: 39.7823 },
    { code: "EE", name: "Estonia", flag: "\ud83c\uddea\ud83c\uddea", lat: 58.5953, lon: 25.0136 },
    { code: "SZ", name: "Eswatini", flag: "\ud83c\uddf8\ud83c\uddff", lat: -26.5225, lon: 31.4659 },
    { code: "ET", name: "Ethiopia", flag: "\ud83c\uddea\ud83c\uddf9", lat: 9.1450, lon: 40.4897 },
    { code: "FJ", name: "Fiji", flag: "\ud83c\uddeb\ud83c\uddef", lat: -17.7134, lon: 178.0650 },
    { code: "FI", name: "Finland", flag: "\ud83c\uddeb\ud83c\uddee", lat: 61.9241, lon: 25.7482 },
    { code: "GA", name: "Gabon", flag: "\ud83c\uddec\ud83c\udde6", lat: -0.8037, lon: 11.6094 },
    { code: "GM", name: "Gambia", flag: "\ud83c\uddec\ud83c\uddf2", lat: 13.4432, lon: -15.3101 },
    { code: "GE", name: "Georgia", flag: "\ud83c\uddec\ud83c\uddea", lat: 42.3154, lon: 43.3569 },
    { code: "GH", name: "Ghana", flag: "\ud83c\uddec\ud83c\udded", lat: 7.9465, lon: -1.0232 },
    { code: "GR", name: "Greece", flag: "\ud83c\uddec\ud83c\uddf7", lat: 39.0742, lon: 21.8243 },
    { code: "GD", name: "Grenada", flag: "\ud83c\uddec\ud83c\udde9", lat: 12.1165, lon: -61.6790 },
    { code: "GT", name: "Guatemala", flag: "\ud83c\uddec\ud83c\uddf9", lat: 15.7835, lon: -90.2308 },
    { code: "GN", name: "Guinea", flag: "\ud83c\uddec\ud83c\uddf3", lat: 9.9456, lon: -9.6966 },
    { code: "GW", name: "Guinea-Bissau", flag: "\ud83c\uddec\ud83c\uddfc", lat: 11.8037, lon: -15.1804 },
    { code: "GY", name: "Guyana", flag: "\ud83c\uddec\ud83c\uddfe", lat: 4.8604, lon: -58.9302 },
    { code: "HT", name: "Haiti", flag: "\ud83c\udded\ud83c\uddf9", lat: 18.9712, lon: -72.2852 },
    { code: "HN", name: "Honduras", flag: "\ud83c\udded\ud83c\uddf3", lat: 15.1999, lon: -86.2419 },
    { code: "HU", name: "Hungary", flag: "\ud83c\udded\ud83c\uddfa", lat: 47.1625, lon: 19.5033 },
    { code: "IS", name: "Iceland", flag: "\ud83c\uddee\ud83c\uddf8", lat: 64.9631, lon: -19.0208 },
    { code: "IN", name: "India", flag: "\ud83c\uddee\ud83c\uddf3", lat: 20.5937, lon: 78.9629 },
    { code: "ID", name: "Indonesia", flag: "\ud83c\uddee\ud83c\udde9", lat: -0.7893, lon: 113.9213 },
    { code: "IR", name: "Iran", flag: "\ud83c\uddee\ud83c\uddf7", lat: 32.4279, lon: 53.6880 },
    { code: "IQ", name: "Iraq", flag: "\ud83c\uddee\ud83c\uddf6", lat: 33.2232, lon: 43.6793 },
    { code: "IE", name: "Ireland", flag: "\ud83c\uddee\ud83c\uddea", lat: 53.1424, lon: -7.6921 },
    { code: "IL", name: "Israel", flag: "\ud83c\uddee\ud83c\uddf1", lat: 31.0461, lon: 34.8516 },
    { code: "IT", name: "Italy", flag: "\ud83c\uddee\ud83c\uddf9", lat: 41.8719, lon: 12.5674 },
    { code: "JM", name: "Jamaica", flag: "\ud83c\uddef\ud83c\uddf2", lat: 18.1096, lon: -77.2975 },
    { code: "JO", name: "Jordan", flag: "\ud83c\uddef\ud83c\uddf4", lat: 30.5852, lon: 36.2384 },
    { code: "KZ", name: "Kazakhstan", flag: "\ud83c\uddf0\ud83c\uddff", lat: 48.0196, lon: 66.9237 },
    { code: "KE", name: "Kenya", flag: "\ud83c\uddf0\ud83c\uddea", lat: -0.0236, lon: 37.9062 },
    { code: "KI", name: "Kiribati", flag: "\ud83c\uddf0\ud83c\uddee", lat: -3.3704, lon: -168.7340 },
    { code: "KW", name: "Kuwait", flag: "\ud83c\uddf0\ud83c\uddfc", lat: 29.3117, lon: 47.4818 },
    { code: "KG", name: "Kyrgyzstan", flag: "\ud83c\uddf0\ud83c\uddec", lat: 41.2044, lon: 74.7661 },
    { code: "LA", name: "Laos", flag: "\ud83c\uddf1\ud83c\udde6", lat: 19.8563, lon: 102.4955 },
    { code: "LV", name: "Latvia", flag: "\ud83c\uddf1\ud83c\uddfb", lat: 56.8796, lon: 24.6032 },
    { code: "LB", name: "Lebanon", flag: "\ud83c\uddf1\ud83c\udde7", lat: 33.8547, lon: 35.8623 },
    { code: "LS", name: "Lesotho", flag: "\ud83c\uddf1\ud83c\uddf8", lat: -29.6100, lon: 28.2336 },
    { code: "LR", name: "Liberia", flag: "\ud83c\uddf1\ud83c\uddf7", lat: 6.4281, lon: -9.4295 },
    { code: "LY", name: "Libya", flag: "\ud83c\uddf1\ud83c\uddfe", lat: 26.3351, lon: 17.2283 },
    { code: "LI", name: "Liechtenstein", flag: "\ud83c\uddf1\ud83c\uddee", lat: 47.1660, lon: 9.5554 },
    { code: "LT", name: "Lithuania", flag: "\ud83c\uddf1\ud83c\uddf9", lat: 55.1694, lon: 23.8813 },
    { code: "LU", name: "Luxembourg", flag: "\ud83c\uddf1\ud83c\uddfa", lat: 49.8153, lon: 6.1296 },
    { code: "MG", name: "Madagascar", flag: "\ud83c\uddf2\ud83c\uddec", lat: -18.7669, lon: 46.8691 },
    { code: "MW", name: "Malawi", flag: "\ud83c\uddf2\ud83c\uddfc", lat: -13.2543, lon: 34.3015 },
    { code: "MY", name: "Malaysia", flag: "\ud83c\uddf2\ud83c\uddfe", lat: 4.2105, lon: 101.9758 },
    { code: "MV", name: "Maldives", flag: "\ud83c\uddf2\ud83c\uddfb", lat: 3.2028, lon: 73.2207 },
    { code: "ML", name: "Mali", flag: "\ud83c\uddf2\ud83c\uddf1", lat: 17.5707, lon: -3.9962 },
    { code: "MT", name: "Malta", flag: "\ud83c\uddf2\ud83c\uddf9", lat: 35.9375, lon: 14.3754 },
    { code: "MH", name: "Marshall Islands", flag: "\ud83c\uddf2\ud83c\udded", lat: 7.1315, lon: 171.1845 },
    { code: "MR", name: "Mauritania", flag: "\ud83c\uddf2\ud83c\uddf7", lat: 21.0079, lon: -10.9408 },
    { code: "MU", name: "Mauritius", flag: "\ud83c\uddf2\ud83c\uddfa", lat: -20.3484, lon: 57.5522 },
    { code: "MX", name: "Mexico", flag: "\ud83c\uddf2\ud83c\uddfd", lat: 23.6345, lon: -102.5528 },
    { code: "FM", name: "Micronesia", flag: "\ud83c\uddeb\ud83c\uddf2", lat: 7.4256, lon: 150.5508 },
    { code: "MD", name: "Moldova", flag: "\ud83c\uddf2\ud83c\udde9", lat: 47.4116, lon: 28.3699 },
    { code: "MC", name: "Monaco", flag: "\ud83c\uddf2\ud83c\udde8", lat: 43.7384, lon: 7.4246 },
    { code: "MN", name: "Mongolia", flag: "\ud83c\uddf2\ud83c\uddf3", lat: 46.8625, lon: 103.8467 },
    { code: "ME", name: "Montenegro", flag: "\ud83c\uddf2\ud83c\uddea", lat: 42.7087, lon: 19.3744 },
    { code: "MA", name: "Morocco", flag: "\ud83c\uddf2\ud83c\udde6", lat: 31.7917, lon: -7.0926 },
    { code: "MZ", name: "Mozambique", flag: "\ud83c\uddf2\ud83c\uddff", lat: -18.6657, lon: 35.5296 },
    { code: "MM", name: "Myanmar", flag: "\ud83c\uddf2\ud83c\uddf2", lat: 21.9162, lon: 95.9560 },
    { code: "NA", name: "Namibia", flag: "\ud83c\uddf3\ud83c\udde6", lat: -22.9576, lon: 18.4904 },
    { code: "NR", name: "Nauru", flag: "\ud83c\uddf3\ud83c\uddf7", lat: -0.5228, lon: 166.9315 },
    { code: "NP", name: "Nepal", flag: "\ud83c\uddf3\ud83c\uddf5", lat: 28.3949, lon: 84.1240 },
    { code: "NL", name: "Netherlands", flag: "\ud83c\uddf3\ud83c\uddf1", lat: 52.1326, lon: 5.2913 },
    { code: "NZ", name: "New Zealand", flag: "\ud83c\uddf3\ud83c\uddff", lat: -40.9006, lon: 174.8860 },
    { code: "NI", name: "Nicaragua", flag: "\ud83c\uddf3\ud83c\uddee", lat: 12.8654, lon: -85.2072 },
    { code: "NE", name: "Niger", flag: "\ud83c\uddf3\ud83c\uddea", lat: 17.6078, lon: 8.0817 },
    { code: "NG", name: "Nigeria", flag: "\ud83c\uddf3\ud83c\uddec", lat: 9.0820, lon: 8.6753 },
    { code: "KP", name: "North Korea", flag: "\ud83c\uddf0\ud83c\uddf5", lat: 40.3399, lon: 127.5101 },
    { code: "MK", name: "North Macedonia", flag: "\ud83c\uddf2\ud83c\uddf0", lat: 41.5124, lon: 21.7453 },
    { code: "NO", name: "Norway", flag: "\ud83c\uddf3\ud83c\uddf4", lat: 60.4720, lon: 8.4689 },
    { code: "OM", name: "Oman", flag: "\ud83c\uddf4\ud83c\uddf2", lat: 21.4735, lon: 55.9754 },
    { code: "PK", name: "Pakistan", flag: "\ud83c\uddf5\ud83c\uddf0", lat: 30.3753, lon: 69.3451 },
    { code: "PW", name: "Palau", flag: "\ud83c\uddf5\ud83c\uddfc", lat: 7.5150, lon: 134.5825 },
    { code: "PS", name: "Palestine", flag: "\ud83c\uddf5\ud83c\uddf8", lat: 31.9522, lon: 35.2332 },
    { code: "PA", name: "Panama", flag: "\ud83c\uddf5\ud83c\udde6", lat: 8.5380, lon: -80.7821 },
    { code: "PG", name: "Papua New Guinea", flag: "\ud83c\uddf5\ud83c\uddec", lat: -6.3150, lon: 143.9555 },
    { code: "PY", name: "Paraguay", flag: "\ud83c\uddf5\ud83c\uddfe", lat: -23.4425, lon: -58.4438 },
    { code: "PE", name: "Peru", flag: "\ud83c\uddf5\ud83c\uddea", lat: -9.1900, lon: -75.0152 },
    { code: "PH", name: "Philippines", flag: "\ud83c\uddf5\ud83c\udded", lat: 12.8797, lon: 121.7740 },
    { code: "PL", name: "Poland", flag: "\ud83c\uddf5\ud83c\uddf1", lat: 51.9194, lon: 19.1451 },
    { code: "PT", name: "Portugal", flag: "\ud83c\uddf5\ud83c\uddf9", lat: 39.3999, lon: -8.2245 },
    { code: "QA", name: "Qatar", flag: "\ud83c\uddf6\ud83c\udde6", lat: 25.3548, lon: 51.1839 },
    { code: "RO", name: "Romania", flag: "\ud83c\uddf7\ud83c\uddf4", lat: 45.9432, lon: 24.9668 },
    { code: "RU", name: "Russia", flag: "\ud83c\uddf7\ud83c\uddfa", lat: 61.5240, lon: 105.3188 },
    { code: "RW", name: "Rwanda", flag: "\ud83c\uddf7\ud83c\uddfc", lat: -1.9403, lon: 29.8739 },
    { code: "KN", name: "Saint Kitts and Nevis", flag: "\ud83c\uddf0\ud83c\uddf3", lat: 17.3578, lon: -62.7830 },
    { code: "LC", name: "Saint Lucia", flag: "\ud83c\uddf1\ud83c\udde8", lat: 13.9094, lon: -60.9789 },
    { code: "VC", name: "Saint Vincent", flag: "\ud83c\uddfb\ud83c\udde8", lat: 12.9843, lon: -61.2872 },
    { code: "WS", name: "Samoa", flag: "\ud83c\uddfc\ud83c\uddf8", lat: -13.7590, lon: -172.1046 },
    { code: "SM", name: "San Marino", flag: "\ud83c\uddf8\ud83c\uddf2", lat: 43.9424, lon: 12.4578 },
    { code: "ST", name: "Sao Tome and Principe", flag: "\ud83c\uddf8\ud83c\uddf9", lat: 0.1864, lon: 6.6131 },
    { code: "SA", name: "Saudi Arabia", flag: "\ud83c\uddf8\ud83c\udde6", lat: 23.8859, lon: 45.0792 },
    { code: "SN", name: "Senegal", flag: "\ud83c\uddf8\ud83c\uddf3", lat: 14.4974, lon: -14.4524 },
    { code: "RS", name: "Serbia", flag: "\ud83c\uddf7\ud83c\uddf8", lat: 44.0165, lon: 21.0059 },
    { code: "SC", name: "Seychelles", flag: "\ud83c\uddf8\ud83c\udde8", lat: -4.6796, lon: 55.4920 },
    { code: "SL", name: "Sierra Leone", flag: "\ud83c\uddf8\ud83c\uddf1", lat: 8.4606, lon: -11.7799 },
    { code: "SG", name: "Singapore", flag: "\ud83c\uddf8\ud83c\uddec", lat: 1.3521, lon: 103.8198 },
    { code: "SK", name: "Slovakia", flag: "\ud83c\uddf8\ud83c\uddf0", lat: 48.6690, lon: 19.6990 },
    { code: "SI", name: "Slovenia", flag: "\ud83c\uddf8\ud83c\uddee", lat: 46.1512, lon: 14.9955 },
    { code: "SB", name: "Solomon Islands", flag: "\ud83c\uddf8\ud83c\udde7", lat: -9.6457, lon: 160.1562 },
    { code: "SO", name: "Somalia", flag: "\ud83c\uddf8\ud83c\uddf4", lat: 5.1521, lon: 46.1996 },
    { code: "ZA", name: "South Africa", flag: "\ud83c\uddff\ud83c\udde6", lat: -30.5595, lon: 22.9375 },
    { code: "SS", name: "South Sudan", flag: "\ud83c\uddf8\ud83c\uddf8", lat: 6.8770, lon: 31.3070 },
    { code: "LK", name: "Sri Lanka", flag: "\ud83c\uddf1\ud83c\uddf0", lat: 7.8731, lon: 80.7718 },
    { code: "SD", name: "Sudan", flag: "\ud83c\uddf8\ud83c\udde9", lat: 12.8628, lon: 30.2176 },
    { code: "SR", name: "Suriname", flag: "\ud83c\uddf8\ud83c\uddf7", lat: 3.9193, lon: -56.0278 },
    { code: "SE", name: "Sweden", flag: "\ud83c\uddf8\ud83c\uddea", lat: 60.1282, lon: 18.6435 },
    { code: "CH", name: "Switzerland", flag: "\ud83c\udde8\ud83c\udded", lat: 46.8182, lon: 8.2275 },
    { code: "SY", name: "Syria", flag: "\ud83c\uddf8\ud83c\uddfe", lat: 34.8021, lon: 38.9968 },
    { code: "TW", name: "Taiwan", flag: "\ud83c\uddf9\ud83c\uddfc", lat: 23.6978, lon: 120.9605 },
    { code: "TJ", name: "Tajikistan", flag: "\ud83c\uddf9\ud83c\uddef", lat: 38.8610, lon: 71.2761 },
    { code: "TZ", name: "Tanzania", flag: "\ud83c\uddf9\ud83c\uddff", lat: -6.3690, lon: 34.8888 },
    { code: "TH", name: "Thailand", flag: "\ud83c\uddf9\ud83c\udded", lat: 15.8700, lon: 100.9925 },
    { code: "TL", name: "Timor-Leste", flag: "\ud83c\uddf9\ud83c\uddf1", lat: -8.8742, lon: 125.7275 },
    { code: "TG", name: "Togo", flag: "\ud83c\uddf9\ud83c\uddec", lat: 8.6195, lon: 0.8248 },
    { code: "TO", name: "Tonga", flag: "\ud83c\uddf9\ud83c\uddf4", lat: -21.1790, lon: -175.1982 },
    { code: "TT", name: "Trinidad and Tobago", flag: "\ud83c\uddf9\ud83c\uddf9", lat: 10.6918, lon: -61.2225 },
    { code: "TN", name: "Tunisia", flag: "\ud83c\uddf9\ud83c\uddf3", lat: 33.8869, lon: 9.5375 },
    { code: "TR", name: "Turkey", flag: "\ud83c\uddf9\ud83c\uddf7", lat: 38.9637, lon: 35.2433 },
    { code: "TM", name: "Turkmenistan", flag: "\ud83c\uddf9\ud83c\uddf2", lat: 38.9697, lon: 59.5563 },
    { code: "TV", name: "Tuvalu", flag: "\ud83c\uddf9\ud83c\uddfb", lat: -7.1095, lon: 179.1940 },
    { code: "UG", name: "Uganda", flag: "\ud83c\uddfa\ud83c\uddec", lat: 1.3733, lon: 32.2903 },
    { code: "UA", name: "Ukraine", flag: "\ud83c\uddfa\ud83c\udde6", lat: 48.3794, lon: 31.1656 },
    { code: "AE", name: "United Arab Emirates", flag: "\ud83c\udde6\ud83c\uddea", lat: 23.4241, lon: 53.8478 },
    { code: "UY", name: "Uruguay", flag: "\ud83c\uddfa\ud83c\uddfe", lat: -32.5228, lon: -55.7658 },
    { code: "UZ", name: "Uzbekistan", flag: "\ud83c\uddfa\ud83c\uddff", lat: 41.3775, lon: 64.5853 },
    { code: "VU", name: "Vanuatu", flag: "\ud83c\uddfb\ud83c\uddfa", lat: -15.3767, lon: 166.9592 },
    { code: "VA", name: "Vatican City", flag: "\ud83c\uddfb\ud83c\udde6", lat: 41.9029, lon: 12.4534 },
    { code: "VE", name: "Venezuela", flag: "\ud83c\uddfb\ud83c\uddea", lat: 6.4238, lon: -66.5897 },
    { code: "VN", name: "Vietnam", flag: "\ud83c\uddfb\ud83c\uddf3", lat: 14.0583, lon: 108.2772 },
    { code: "YE", name: "Yemen", flag: "\ud83c\uddfe\ud83c\uddea", lat: 15.5527, lon: 48.5164 },
    { code: "ZM", name: "Zambia", flag: "\ud83c\uddff\ud83c\uddf2", lat: -13.1339, lon: 27.8493 },
    { code: "ZW", name: "Zimbabwe", flag: "\ud83c\uddff\ud83c\uddfc", lat: -19.0154, lon: 29.1549 }
];

// Get popular countries
function getPopularCountries() {
    return COUNTRIES_DATA.filter(c => c.popular);
}

// Get all countries sorted alphabetically
function getAllCountries() {
    return COUNTRIES_DATA.filter(c => !c.popular).sort((a, b) => a.name.localeCompare(b.name));
}

// Search countries by name
function searchCountries(query) {
    const q = query.toLowerCase();
    return COUNTRIES_DATA.filter(c =>
        c.name.toLowerCase().includes(q) ||
        c.code.toLowerCase().includes(q)
    );
}

// Get country by code
function getCountryByCode(code) {
    return COUNTRIES_DATA.find(c => c.code === code.toUpperCase());
}

// Get flag emoji by country code
function getCountryFlag(code) {
    const country = getCountryByCode(code);
    return country ? country.flag : "\ud83c\udff3\ufe0f";
}

// Get country name by code
function getCountryName(code) {
    const country = getCountryByCode(code);
    return country ? country.name : "Unknown";
}

// Convert lat/lon to 3D sphere coordinates (for Three.js globe)
function latLonToVector3(lat, lon, radius) {
    const phi = (90 - lat) * (Math.PI / 180);
    const theta = (lon + 180) * (Math.PI / 180);

    const x = -(radius * Math.sin(phi) * Math.cos(theta));
    const y = radius * Math.cos(phi);
    const z = radius * Math.sin(phi) * Math.sin(theta);

    return { x, y, z };
}

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.COUNTRIES_DATA = COUNTRIES_DATA;
    window.getPopularCountries = getPopularCountries;
    window.getAllCountries = getAllCountries;
    window.searchCountries = searchCountries;
    window.getCountryByCode = getCountryByCode;
    window.getCountryFlag = getCountryFlag;
    window.getCountryName = getCountryName;
    window.latLonToVector3 = latLonToVector3;
}
