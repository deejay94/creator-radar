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
    } catch (error) {
      console.error(`Failed to load seen opportunity store from Redis: ${error.message}`);
      this.seen = {};
    }
  }

  async save() {
    const keys = Object.keys(this.seen);
    if (keys.length === 0) {
      return true;
    }

    try {
      await this.redis.sadd(this.setKey, ...keys);
      return true;
    } catch (error) {
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
