/**
 * NASA Earth Systems Trend Detective
 * Input Validation Utilities
 */

const isValidCoordinate = (lat, lon) => {
  return (
    typeof lat === 'number' &&
    typeof lon === 'number' &&
    lat >= -90 &&
    lat <= 90 &&
    lon >= -180 &&
    lon <= 180
  );
};

const isValidPeriod = (period) => {
  const validPeriods = ['2019-05', '2021-02', '2021-08', '2023-11', 'ALL'];
  return validPeriods.includes(period);
};

const isValidEmail = (email) => {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(String(email).toLowerCase());
};

module.exports = {
  isValidCoordinate,
  isValidPeriod,
  isValidEmail
};
