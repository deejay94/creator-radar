const SLACK_TEXT_LIMIT = 4000;

function formatPlatform(platform) {
  const normalized = String(platform || "").trim().toLowerCase();
  if (!normalized) {
    return "Unknown";
  }
  return normalized.charAt(0).toUpperCase() + normalized.slice(1);
}

export function formatSlackMessage(opportunities) {
  if (!opportunities?.length) {
    return null;
  }

  const count = opportunities.length;
  const header = `🔥 ${count} New UGC Opportunit${count === 1 ? "y" : "ies"}`;
  const blocks = [header, ""];

  for (const opportunity of opportunities) {
    blocks.push(`• ${opportunity.title}`);
    blocks.push(`  Platform: ${formatPlatform(opportunity.platform)}`);
    blocks.push(`  ${opportunity.url}`);
    blocks.push("");
  }

  let message = blocks.join("\n").trimEnd();

  if (message.length > SLACK_TEXT_LIMIT) {
    const suffix = "\n…and more (message truncated)";
    message = `${message.slice(0, SLACK_TEXT_LIMIT - suffix.length).trimEnd()}${suffix}`;
  }

  return message;
}
