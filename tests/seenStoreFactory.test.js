import assert from "node:assert/strict";
import test from "node:test";

import { createSeenOpportunityStore, isRemoteStoreEnabled } from "../seenStoreFactory.js";
import { RedisSeenOpportunityStore } from "../redisSeenOpportunityStore.js";
import { SeenOpportunityStore } from "../seenOpportunityStore.js";

test("isRemoteStoreEnabled is false without Upstash env vars", () => {
  withEnv({}, () => {
    assert.equal(isRemoteStoreEnabled(), false);
  });
});

test("isRemoteStoreEnabled is true when Upstash env vars are set", () => {
  withEnv(
    {
      UPSTASH_REDIS_REST_URL: "https://example.upstash.io",
      UPSTASH_REDIS_REST_TOKEN: "token",
    },
    () => {
      assert.equal(isRemoteStoreEnabled(), true);
    },
  );
});

test("createSeenOpportunityStore returns file store by default", () => {
  withEnv({}, () => {
    const store = createSeenOpportunityStore();
    assert.ok(store instanceof SeenOpportunityStore);
  });
});

test("createSeenOpportunityStore returns Redis store when configured", () => {
  withEnv(
    {
      UPSTASH_REDIS_REST_URL: "https://example.upstash.io",
      UPSTASH_REDIS_REST_TOKEN: "token",
    },
    () => {
      const store = createSeenOpportunityStore();
      assert.ok(store instanceof RedisSeenOpportunityStore);
    },
  );
});

function withEnv(values, fn) {
  const previous = {};
  for (const [key, value] of Object.entries(values)) {
    previous[key] = process.env[key];
    process.env[key] = value;
  }

  for (const key of ["UPSTASH_REDIS_REST_URL", "UPSTASH_REDIS_REST_TOKEN"]) {
    if (!(key in values) && previous[key] === undefined) {
      delete process.env[key];
    }
  }

  try {
    return fn();
  } finally {
    for (const [key, value] of Object.entries(previous)) {
      if (value === undefined) {
        delete process.env[key];
      } else {
        process.env[key] = value;
      }
    }
  }
}
