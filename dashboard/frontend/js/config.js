/**
 * NASA Earth Systems Trend Detective — Client Configuration
 */

const CONFIG = {
  API_BASE_URL: '/api',
  VARIABLES: {
    T2M: { name: 'Air Temperature at 2m', units: '°C', defaultMin: -10, defaultMax: 45, icon: 'fa-temperature-high' },
    PRECTOTCORR: { name: 'Precipitation Rate', units: 'mm/day', defaultMin: 0, defaultMax: 35, icon: 'fa-cloud-rain' },
    RH2M: { name: 'Relative Humidity at 2m', units: '%', defaultMin: 10, defaultMax: 100, icon: 'fa-droplet' },
    WS10M: { name: 'Wind Speed at 10m', units: 'm/s', defaultMin: 0, defaultMax: 15, icon: 'fa-wind' }
  },
  REGIONS: {
    ALL: 'All India (National Grid)',
    NW: 'Northwest India',
    NE: 'Northeast India',
    CW: 'Central-West India',
    CE: 'Central-East India',
    SW: 'Southwest India',
    SE: 'Southeast India'
  },
  DEFAULT_DATE_RANGE: {
    start: '2015-01',
    end: '2024-12'
  }
};
