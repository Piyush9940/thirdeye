const fs = require('fs');
const path = require('path');
const env = require('../config/environment');
const logger = require('../utils/logger');

class MethaneService {
  constructor() {
    this.observationsCache = null;
  }

  getRegionalSummary() {
    return {
      title: "Sentinel-5P / TROPOMI Methane Pilot Observations",
      total_pixels_filtered: 73045,
      qa_threshold: ">= 0.50",
      granules_evaluated: 7,
      total_node_months: 226,
      unique_spatial_nodes: 98,
      snapshots: [
        { period: "2019-05", season: "Pre-Monsoon", valid_nodes: 82, mean_ppb: 1874.2, description: "Broad national coverage, high soundings count." },
        { period: "2021-02", season: "Winter", valid_nodes: 67, mean_ppb: 1856.8, description: "Stable winter boundary layer observations." },
        { period: "2021-08", season: "Monsoon", valid_nodes: 11, mean_ppb: 1842.1, description: "Severe cloud gap: 95% of soundings blocked by convective cloud cover." },
        { period: "2023-11", season: "Post-Monsoon", valid_nodes: 66, mean_ppb: 1888.4, description: "Post-harvest and post-monsoon elevated column concentrations." }
      ],
      regions: [
        {
          code: "NW",
          name: "Northwest India",
          pixel_count: 21726,
          median_ppb: 1890.06,
          status: "Observed",
          notes: "Agricultural and urban corridor, high sounding density."
        },
        {
          code: "CW",
          name: "Central-West India",
          pixel_count: 28485,
          median_ppb: 1884.68,
          status: "Observed",
          notes: "Highest raw pixel count in pilot release."
        },
        {
          code: "CE",
          name: "Central-East India",
          pixel_count: 12882,
          median_ppb: 1955.43,
          status: "Observed",
          notes: "Elevated tropospheric column; extensive mining and wetland influence."
        },
        {
          code: "NE",
          name: "Northeast India",
          pixel_count: 6990,
          median_ppb: 1960.07,
          status: "Observed",
          notes: "Highest regional median; river basins and topography."
        },
        {
          code: "SW",
          name: "Southwest India",
          pixel_count: 2962,
          median_ppb: 1910.62,
          status: "Observed",
          notes: "Sparse soundings along coastal Ghats."
        },
        {
          code: "SE",
          name: "Southeast India",
          pixel_count: 0,
          median_ppb: null,
          status: "No Valid Soundings",
          notes: "DATA GAP: 0 valid QA>=0.5 pixels in pilot granules. Displayed as unavailable, never zero."
        }
      ],
      scientific_caveats: [
        "Sentinel-5P soundings represent total column dry-air mole fraction (XCH4), NOT surface emission rates.",
        "Methane column variations reflect atmospheric transport, advection, and planetary boundary layer dynamics.",
        "Monsoon convective clouds create systematic seasonal missingness in optical satellite soundings."
      ]
    };
  }

  getObservations() {
    // Generate/serve the 226 climate-matched node-month observations
    if (this.observationsCache) return this.observationsCache;

    // Check if exported json exists
    const exportPath = path.resolve(env.PATHS.DASHBOARD_EXPORTS, 'methane_observations.json');
    if (fs.existsSync(exportPath)) {
      try {
        const raw = fs.readFileSync(exportPath, 'utf-8');
        this.observationsCache = JSON.parse(raw);
        return this.observationsCache;
      } catch (e) {
        logger.warn(`[MethaneService] Could not parse exported observations: ${e.message}`);
      }
    }

    // Default structured observations array
    return this.getRegionalSummary();
  }
}

module.exports = new MethaneService();
