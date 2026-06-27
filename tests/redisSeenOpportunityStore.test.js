import assert from "node:assert/strict";
import test from "node:test";

import { RedisSeenOpportunityStore } from "../redisSeenOpportunityStore.js";

function createMockRedis() {
  const sets = new Map();

  return {
    async smembers(key) {
      return [...(sets.get(key) || [])];
    },
    async sadd(key, ...members) {
      const current = new Set(sets.get(key) || []);
      for (const member of members) {
        current.add(member);
      }
      sets.set(key, current);
      return members.length;
    },
    _sets: sets,
  };
}

test("RedisSeenOpportunityStore loads members into memory", async () => {
  const redis = createMockRedis();
  redis._sets.set("creator-radar:seen", new Set(["reddit:abc123"]));

  const store = new RedisSeenOpportunityStore({ redis, setKey: "creator-radar:seen" });
  await store.load();

  assert.equal(store.count(), 1);
  assert.equal(store.has("reddit:abc123"), true);
});

test("RedisSeenOpportunityStore save adds all seen keys to Redis set", async () => {
  const redis = createMockRedis();
  const store = new RedisSeenOpportunityStore({ redis, setKey: "creator-radar:seen" });

  store.markMany(["reddit:new1", "reddit:new2"]);
  assert.equal(await store.save(), true);

  const members = await redis.smembers("creator-radar:seen");
  assert.deepEqual(members.sort(), ["reddit:new1", "reddit:new2"]);
});

test("RedisSeenOpportunityStore save returns false when Redis fails", async () => {
  const store = new RedisSeenOpportunityStore({
    redis: {
      async smembers() {
        return [];
      },
      async sadd() {
        throw new Error("connection refused");
      },
    },
    setKey: "creator-radar:seen",
  });

  store.mark("reddit:abc123");
  assert.equal(await store.save(), false);
});

test("RedisSeenOpportunityStore reloads saved keys", async () => {
  const redis = createMockRedis();
  const writer = new RedisSeenOpportunityStore({ redis, setKey: "creator-radar:seen" });
  writer.markMany(["reddit:abc123"]);
  assert.equal(await writer.save(), true);

  const reader = new RedisSeenOpportunityStore({ redis, setKey: "creator-radar:seen" });
  await reader.load();

  assert.equal(reader.has("reddit:abc123"), true);
});
