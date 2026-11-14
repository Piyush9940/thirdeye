/**
 * NASA Earth Systems Trend Detective
 * Background Queue Utility
 */

class SimpleQueue {
  constructor() {
    this.jobs = [];
  }

  enqueue(job) {
    this.jobs.push(job);
    return job;
  }

  getJobs() {
    return this.jobs;
  }
}

module.exports = new SimpleQueue();
