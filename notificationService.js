import { makeOpportunityKey } from "./opportunityKey.js";

export function filterNewOpportunities(opportunities, store) {
  const newOpportunities = [];
  const keys = [];

  for (const opportunity of opportunities) {
    try {
      const key = makeOpportunityKey(opportunity);
      if (store.has(key)) {
        continue;
      }
      newOpportunities.push(opportunity);
      keys.push(key);
    } catch (error) {
      console.error(`Skipping invalid opportunity: ${error.message}`);
    }
  }

  return { newOpportunities, keys };
}

export async function processNewOpportunities({
  opportunities,
  store,
  sendSlackNotification,
  formatSlackMessage,
}) {
  const { newOpportunities, keys } = filterNewOpportunities(opportunities, store);

  // #region agent log
  fetch("http://127.0.0.1:7487/ingest/7631985e-2777-4bcc-91c0-d0567bba16f9", {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "84bf78" },
    body: JSON.stringify({
      sessionId: "84bf78",
      runId: "dedup-debug",
      hypothesisId: "D",
      location: "notificationService.js:filter",
      message: "Dedup filter result",
      data: {
        fetchedCount: opportunities.length,
        seenCount: store.count(),
        newCount: newOpportunities.length,
        sampleNewKeys: keys.slice(0, 3),
        sampleFetchedIds: opportunities.slice(0, 3).map((o) => o.external_id),
      },
      timestamp: Date.now(),
    }),
  }).catch(() => {});
  // #endregion

  console.log(`Found ${newOpportunities.length} new opportunities`);

  if (newOpportunities.length === 0) {
    console.log("No new opportunities found.");
    return { sent: false, newCount: 0 };
  }

  const message = formatSlackMessage(newOpportunities);
  if (!message) {
    console.log("No new opportunities found.");
    return { sent: false, newCount: 0 };
  }

  console.log("Sending Slack notification...");
  const sent = await sendSlackNotification(message);

  if (!sent) {
    console.error("Slack notification failed");
    return { sent: false, newCount: newOpportunities.length };
  }

  console.log("Slack notification sent successfully");
  store.markMany(keys);
  const saved = await store.save();
  if (!saved) {
    console.error("Failed to persist dedup state");
    return { sent: true, newCount: newOpportunities.length, persistFailed: true };
  }

  console.log("Saved seen opportunity store");
  return { sent: true, newCount: newOpportunities.length };
}
