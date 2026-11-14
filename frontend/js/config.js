/**
 * NASA Earth Systems Trend Detective
 * Global Frontend Configuration & Constants
 */

window.APP_CONFIG = {
  API_BASE: '', // Same-origin relative path for REST APIs
  
  // Observation Periods in Verified Export
  OBSERVATION_PERIODS: [
    { id: '2019-05', label: 'May 2019 (Pre-monsoon)', year: 2019, month: 5 },
    { id: '2021-02', label: 'Feb 2021 (Winter)', year: 2021, month: 2 },
    { id: '2021-08', label: 'Aug 2021 (Monsoon - Sparse)', year: 2021, month: 8 },
    { id: '2023-11', label: 'Nov 2023 (Post-monsoon)', year: 2023, month: 11 }
  ],

  // Evaluation Folds in Verified Release
  EVALUATION_FOLDS: [
    { fold: 1, period: '2021-02', train: '2019-05', evalNodes: 67 },
    { fold: 2, period: '2021-08', train: '2019-05, 2021-02', evalNodes: 11 },
    { fold: 3, period: '2023-11', train: '2019-05, 2021-02, 2021-08', evalNodes: 66 }
  ],

  // Evaluation Seeds
  SEEDS: [7, 21, 42, 77, 123],

  // India Spatial Bounds (Center for Leaflet)
  MAP_CENTER: [22.5, 82.5],
  MAP_DEFAULT_ZOOM: 5,

  // Six Geographic Regions
  REGIONS: [
    { id: 'ALL', name: 'All India Subcontinent' },
    { id: 'North_West', name: 'North-West (Lat >= 25°, Lon < 82°)' },
    { id: 'North_East', name: 'North-East (Lat >= 25°, Lon >= 82°)' },
    { id: 'Central_West', name: 'Central-West (15° <= Lat < 25°, Lon < 82°)' },
    { id: 'Central_East', name: 'Central-East (15° <= Lat < 25°, Lon >= 82°)' },
    { id: 'South_West', name: 'South-West (Lat < 15°, Lon < 82°)' },
    { id: 'South_East', name: 'South-East (Lat < 15°, Lon >= 82°)' }
  ],

  // Helper function to classify geographic region
  getRegionForCoords: function(lat, lon) {
    if (lat >= 25.0) {
      return lon < 82.0 ? 'North_West' : 'North_East';
    } else if (lat >= 15.0) {
      return lon < 82.0 ? 'Central_West' : 'Central_East';
    } else {
      return lon < 82.0 ? 'South_West' : 'South_East';
    }
  },

  // Color mapping function for CH4 concentration (ppb)
  getCH4Color: function(val) {
    if (val === null || val === undefined || isNaN(val)) return '#64748b'; // Missing/unobserved
    if (val < 1850) return '#10b981'; // Earth Green
    if (val < 1900) return '#38bdf8'; // Cyan
    if (val < 1950) return '#f59e0b'; // Amber
    return '#ef4444'; // Crimson
  }
};
