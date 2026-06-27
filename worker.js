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

function resolveNotifyPlatforms() {
  const raw = process.env.RADAR_NOTIFY_PLATFORMS?.trim() || "reddit,upwork";
  return raw
    .split(",")
    .map((platform) => platform.trim().toLowerCase())
    .filter(Boolean);
}

function buildNotifyArgs(platform) {
  if (platform === "reddit") {
    return [
      "-m",
      "radar",
      "notify",
      "--platform",
      "reddit",
      "--subreddit",
      resolveRedditSubreddits(),
    ];
  }

  if (platform === "upwork") {
    return ["-m", "radar", "notify", "--platform", "upwork", "--headless"];
  }

  throw new Error(`Unsupported notify platform: ${platform}`);
}

function fetchOpportunitiesForPlatform(pythonCommand, platform) {
  let args;
  try {
    args = buildNotifyArgs(platform);
  } catch (error) {
    console.error(error.message);
    return null;
  }

  const result = spawnSync(pythonCommand, args, {
    encoding: "utf-8",
    env: process.env,
  });

  if (result.stderr?.trim()) {
    console.error(result.stderr.trim());
  }

  if (result.status !== 0) {
    console.error(
      `Notify fetch failed for ${platform} with exit code ${result.status ?? "unknown"}`,
    );
    return null;
  }

  try {
    return JSON.parse(result.stdout || "[]");
  } catch (error) {
    console.error(`Failed to parse notify JSON for ${platform}:`, error);
    return null;
  }
}

function fetchAllOpportunities(pythonCommand) {
  const platforms = resolveNotifyPlatforms();
  if (platforms.length === 0) {
    console.error("No notify platforms configured in RADAR_NOTIFY_PLATFORMS");
    return null;
  }

  let anySucceeded = false;
  const combined = [];

  for (const platform of platforms) {
    console.log(`Fetching ${platform} opportunities...`);
    const opportunities = fetchOpportunitiesForPlatform(pythonCommand, platform);
    if (opportunities === null) {
      continue;
    }

    anySucceeded = true;
    console.log(`Fetched ${opportunities.length} ${platform} opportunities`);
    combined.push(...opportunities);
  }

  if (!anySucceeded) {
    return null;
  }

  return combined;
}

async function main() {
  loadEnvFile();

  console.log("Worker started");
  console.log(`Redis dedup store: ${isRemoteStoreEnabled() ? "enabled" : "disabled"}`);
  console.log(`Notify platforms: ${resolveNotifyPlatforms().join(", ")}`);

  const store = createSeenOpportunityStore();
  await store.load();
  console.log(`Loaded ${store.count()} previously seen opportunities`);

  const pythonCommand = resolvePythonCommand();
  const opportunities = fetchAllOpportunities(pythonCommand);

  if (opportunities === null) {
    console.log("Worker finished");
    return;
  }

  console.log(`Fetched ${opportunities.length} total opportunities`);

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
