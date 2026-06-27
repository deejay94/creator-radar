import { RedisSeenOpportunityStore } from "./redisSeenOpportunityStore.js";
import { SeenOpportunityStore } from "./seenOpportunityStore.js";

export function isRemoteStoreEnabled() {
  return Boolean(
    process.env.UPSTASH_REDIS_REST_URL?.trim() && process.env.UPSTASH_REDIS_REST_TOKEN?.trim(),
  );
}

export function createSeenOpportunityStore() {
  if (isRemoteStoreEnabled()) {
    return new RedisSeenOpportunityStore();
  }

  return new SeenOpportunityStore();
}
