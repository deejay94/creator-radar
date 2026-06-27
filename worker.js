import { spawnSync } from "node:child_process";
import { readFileSync, existsSync } from "node:fs";
import { resolve } from "node:path";

import { formatSlackMessage } from "./formatSlackMessage.js";
import { processNewOpportunities } from "./notificationService.js";
import { createSeenOpportunityStore, isRemoteStoreEnabled } from "./seenStoreFactory.js";
import { sendSlackNotification } from "./slackNotifier.js";

function loadEnvFile(path = ".env") {
  const envPath = resolve(path);
  if (!existsSync(envPath)) {
    return;
  }

  for (const line of readFileSync(envPath, "utf8").split("\n")) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) {
      continue;
    }

    const separator = trimmed.indexOf("=");
    if (separator === -1) {
      continue;
    }

    const key = trimmed.slice(0, separator).trim();
    let value = trimmed.slice(separator + 1).trim();
    if (
      (value.startsWith('"') && value.endsWith('"')) ||
      (value.startsWith("'") && value.endsWith("'"))
    ) {
      value = value.slice(1, -1);
    }

    if (key) {
      process.env[key] = value;
    }
  }
}

function resolvePythonCommand() {
  const venvPython = resolve(".venv/bin/python");
  if (existsSync(venvPython)) {
    return venvPython;
  }

  for (const command of ["python3", "python"]) {
    const result = spawnSync(command, ["--version"], { encoding: "utf-8" });
    if (result.status === 0) {
      return command;
    }
  }

  return "python3";
}

function resolveRedditSubreddits() {
  return process.env.RADAR_REDDIT_SUBREDDITS?.trim() || "UGCCreators,ugc";
}

function fetchOpportunities(pythonCommand) {
  const subreddits = resolveRedditSubreddits();
  const result = spawnSync(
    pythonCommand,
    ["-m", "radar", "notify", "--platform", "reddit", "--subreddit", subreddits],
    {
      encoding: "utf-8",
      env: process.env,
    },
  );

  if (result.stderr?.trim()) {
    console.error(result.stderr.trim());
  }

  if (result.status !== 0) {
    console.error(`Notify fetch failed with exit code ${result.status ?? "unknown"}`);
    return null;
  }

  try {
    return JSON.parse(result.stdout || "[]");
  } catch (error) {
    console.error("Failed to parse notify JSON:", error);
    return null;
  }
}

async function main() {
  loadEnvFile();

  console.log("Worker started");
  const remoteEnabled = isRemoteStoreEnabled();
  console.log(`Redis dedup store: ${remoteEnabled ? "enabled" : "disabled"}`);

  const store = createSeenOpportunityStore();
  // #region agent log
  fetch("http://127.0.0.1:7487/ingest/7631985e-2777-4bcc-91c0-d0567bba16f9", {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "84bf78" },
    body: JSON.stringify({
      sessionId: "84bf78",
      runId: "dedup-debug",
      hypothesisId: "A",
      location: "worker.js:main",
      message: "Store backend selected",
      data: {
        remoteEnabled,
        storeType: store.constructor.name,
        redisKey: process.env.SEEN_STORE_REDIS_KEY || "creator-radar:seen",
        hasRedisUrl: Boolean(process.env.UPSTASH_REDIS_REST_URL?.trim()),
        hasRedisToken: Boolean(process.env.UPSTASH_REDIS_REST_TOKEN?.trim()),
      },
      timestamp: Date.now(),
    }),
  }).catch(() => {});
  // #endregion
  await store.load();
  console.log(`Loaded ${store.count()} previously seen opportunities`);

  const pythonCommand = resolvePythonCommand();
  const opportunities = fetchOpportunities(pythonCommand);

  if (opportunities === null) {
    console.log("Worker finished");
    return;
  }

  console.log(`Fetched ${opportunities.length} opportunities`);

  const result = await processNewOpportunities({
    opportunities,
    store,
    sendSlackNotification,
    formatSlackMessage,
  });

  if (result.persistFailed) {
    console.error("Failed to persist dedup state to remote store");
    process.exit(1);
  }

  console.log("Worker finished");
}

main().catch((error) => {
  console.error("Worker error:", error);
  process.exit(1);
});
