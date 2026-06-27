import assert from "node:assert/strict";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import { formatSlackMessage } from "../formatSlackMessage.js";
import { makeOpportunityKey } from "../opportunityKey.js";
import { filterNewOpportunities } from "../notificationService.js";
import { SeenOpportunityStore } from "../seenOpportunityStore.js";

test("makeOpportunityKey builds platform:external_id", () => {
  assert.equal(
    makeOpportunityKey({ platform: "reddit", external_id: "abc123" }),
    "reddit:abc123",
  );
});

test("SeenOpportunityStore loads missing file as empty", () => {
  const dir = mkdtempSync(join(tmpdir(), "seen-store-"));
  const filePath = join(dir, "seen_opportunities.json");
  const store = new SeenOpportunityStore(filePath);

  store.load();

  assert.equal(store.count(), 0);
  rmSync(dir, { recursive: true, force: true });
});

test("SeenOpportunityStore recovers from invalid JSON", () => {
  const dir = mkdtempSync(join(tmpdir(), "seen-store-"));
  const filePath = join(dir, "seen_opportunities.json");
  writeFileSync(filePath, "not-json", "utf8");

  const store = new SeenOpportunityStore(filePath);
  store.load();

  assert.equal(store.count(), 0);
  rmSync(dir, { recursive: true, force: true });
});

test("SeenOpportunityStore saves and reloads keys", () => {
  const dir = mkdtempSync(join(tmpdir(), "seen-store-"));
  const filePath = join(dir, "seen_opportunities.json");
  const store = new SeenOpportunityStore(filePath);

  store.mark("reddit:abc123");
  store.save();

  const reloaded = new SeenOpportunityStore(filePath);
  reloaded.load();

  assert.equal(reloaded.count(), 1);
  assert.equal(reloaded.has("reddit:abc123"), true);
  assert.equal(JSON.parse(readFileSync(filePath, "utf8"))["reddit:abc123"], true);
  rmSync(dir, { recursive: true, force: true });
});

test("filterNewOpportunities ignores previously seen keys", () => {
  const store = new SeenOpportunityStore(join(tmpdir(), "unused.json"));
  store.mark("reddit:old1");

  const opportunities = [
    { platform: "reddit", external_id: "old1", title: "Old", url: "https://example.com/old" },
    { platform: "reddit", external_id: "new1", title: "New", url: "https://example.com/new" },
  ];

  const { newOpportunities, keys } = filterNewOpportunities(opportunities, store);

  assert.equal(newOpportunities.length, 1);
  assert.equal(newOpportunities[0].external_id, "new1");
  assert.deepEqual(keys, ["reddit:new1"]);
});

test("formatSlackMessage renders batch notification", () => {
  const message = formatSlackMessage([
    {
      platform: "reddit",
      external_id: "abc123",
      title: "UGC Creator for Skincare Brand",
      url: "https://example.com/abc123",
    },
  ]);

  assert.match(message, /🔥 1 New UGC Opportunity/);
  assert.match(message, /UGC Creator for Skincare Brand/);
  assert.match(message, /Platform: Reddit/);
  assert.match(message, /https:\/\/example.com\/abc123/);
});
