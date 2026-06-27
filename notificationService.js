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
