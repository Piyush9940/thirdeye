/**
 * NASA Earth Systems Trend Detective
 * Analysis Service
 */

const datasetService = require('./dataset.service');

class AnalysisService {
  getMethaneOverview() {
    const kpis = datasetService.getKPIs();
    const metrics = datasetService.getFoldMetrics();
    return {
      kpis,
      metrics
    };
  }

  getHotspots(period = '2023-11') {
    const obs = datasetService.getMethaneObservations({ period, limit: 10000 }).records;
    return obs
      .sort((a, b) => b.methane_median_ppb - a.methane_median_ppb)
      .slice(0, 20)
      .map((o, idx) => ({
        rank: idx + 1,
        ...o,
        category: o.methane_median_ppb > 1950 ? 'Candidate Area for Investigation' : 'Nominal Background'
      }));
  }

  getTrends() {
    const obs = datasetService.getMethaneObservations({ limit: 10000 }).records;
    const periodMap = {};
    ['2019-05', '2021-02', '2021-08', '2023-11'].forEach(p => {
      const records = obs.filter(o => o.observation_period === p);
      const vals = records.map(r => r.methane_median_ppb);
      const mean = vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : 0;
      periodMap[p] = {
        count: records.length,
        mean: parseFloat(mean.toFixed(2)),
        records
      };
    });
    return periodMap;
  }
}

module.exports = new AnalysisService();
