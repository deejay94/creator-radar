import { spawnSync } from "node:child_process";
import { readFileSync, existsSync } from "node:fs";
import { resolve } from "node:path";

import { formatSlackMessage } from "./formatSlackMessage.js";
import { processNewOpportunities } from "./notificationService.js";
import { SeenOpportunityStore } from "./seenOpportunityStore.js";
import { downloadSeenStore, uploadSeenStore } from "./seenStoreSync.js";
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

  await downloadSeenStore();

  const store = new SeenOpportunityStore();
  store.load();
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

  if (result.sent) {
    await uploadSeenStore();
  }

  console.log("Worker finished");
}

main().catch((error) => {
  console.error("Worker error:", error);
  process.exit(0);
});
