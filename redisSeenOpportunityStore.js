import { Redis } from "@upstash/redis";

export class RedisSeenOpportunityStore {
  constructor(options = {}) {
    this.setKey =
      options.setKey || process.env.SEEN_STORE_REDIS_KEY?.trim() || "creator-radar:seen";
    this.redis =
      options.redis ||
      new Redis({
        url: process.env.UPSTASH_REDIS_REST_URL,
        token: process.env.UPSTASH_REDIS_REST_TOKEN,
      });
    this.seen = {};
  }

  async load() {
    this.seen = {};

    try {
      const members = await this.redis.smembers(this.setKey);
      for (const key of members || []) {
        this.seen[key] = true;
      }
      // #region agent log
      fetch("http://127.0.0.1:7487/ingest/7631985e-2777-4bcc-91c0-d0567bba16f9", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "84bf78" },
        body: JSON.stringify({
          sessionId: "84bf78",
          runId: "dedup-debug",
          hypothesisId: "B,E",
          location: "redisSeenOpportunityStore.js:load",
          message: "Redis load completed",
          data: {
            setKey: this.setKey,
            memberCount: (members || []).length,
            loadedCount: Object.keys(this.seen).length,
            sampleKeys: Object.keys(this.seen).slice(0, 3),
          },
          timestamp: Date.now(),
        }),
      }).catch(() => {});
      // #endregion
    } catch (error) {
      // #region agent log
      fetch("http://127.0.0.1:7487/ingest/7631985e-2777-4bcc-91c0-d0567bba16f9", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "84bf78" },
        body: JSON.stringify({
          sessionId: "84bf78",
          runId: "dedup-debug",
          hypothesisId: "B",
          location: "redisSeenOpportunityStore.js:load",
          message: "Redis load failed",
          data: { setKey: this.setKey, error: error.message },
          timestamp: Date.now(),
        }),
      }).catch(() => {});
      // #endregion
      console.error(`Failed to load seen opportunity store from Redis: ${error.message}`);
      this.seen = {};
    }
  }

  async save() {
    const keys = Object.keys(this.seen);
    if (keys.length === 0) {
      // #region agent log
      fetch("http://127.0.0.1:7487/ingest/7631985e-2777-4bcc-91c0-d0567bba16f9", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "84bf78" },
        body: JSON.stringify({
          sessionId: "84bf78",
          runId: "dedup-debug",
          hypothesisId: "C",
          location: "redisSeenOpportunityStore.js:save",
          message: "Redis save skipped empty",
          data: { setKey: this.setKey },
          timestamp: Date.now(),
        }),
      }).catch(() => {});
      // #endregion
      return true;
    }

    try {
      const added = await this.redis.sadd(this.setKey, ...keys);
      // #region agent log
      fetch("http://127.0.0.1:7487/ingest/7631985e-2777-4bcc-91c0-d0567bba16f9", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "84bf78" },
        body: JSON.stringify({
          sessionId: "84bf78",
          runId: "dedup-debug",
          hypothesisId: "C",
          location: "redisSeenOpportunityStore.js:save",
          message: "Redis save succeeded",
          data: {
            setKey: this.setKey,
            keyCount: keys.length,
            saddAddedCount: added,
            sampleKeys: keys.slice(0, 3),
          },
          timestamp: Date.now(),
        }),
      }).catch(() => {});
      // #endregion
      return true;
    } catch (error) {
      // #region agent log
      fetch("http://127.0.0.1:7487/ingest/7631985e-2777-4bcc-91c0-d0567bba16f9", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "84bf78" },
        body: JSON.stringify({
          sessionId: "84bf78",
          runId: "dedup-debug",
          hypothesisId: "C",
          location: "redisSeenOpportunityStore.js:save",
          message: "Redis save failed",
          data: { setKey: this.setKey, keyCount: keys.length, error: error.message },
          timestamp: Date.now(),
        }),
      }).catch(() => {});
      // #endregion
      console.error(`Failed to save seen opportunity store to Redis: ${error.message}`);
      return false;
    }
  }

  has(key) {
    return Boolean(this.seen[key]);
  }

  mark(key) {
    this.seen[key] = true;
  }

  markMany(keys) {
    for (const key of keys) {
      this.mark(key);
    }
  }

  count() {
    return Object.keys(this.seen).length;
  }
}
