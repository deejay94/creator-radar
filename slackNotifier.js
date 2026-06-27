const DEFAULT_MESSAGE = "UGC Worker is running successfully (heartbeat test)";

export async function sendSlackNotification(message = DEFAULT_MESSAGE) {
  const webhookUrl = process.env.SLACK_WEBHOOK_URL;

  if (!webhookUrl) {
    console.error("SLACK_WEBHOOK_URL is not set");
    return false;
  }

  try {
    const response = await fetch(webhookUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: message }),
    });

    if (!response.ok) {
      const body = await response.text();
      console.error(
        `Slack notification failed: ${response.status} ${response.statusText}${body ? ` — ${body}` : ""}`,
      );
      return false;
    }

    return true;
  } catch (error) {
    console.error("Slack notification failed:", error);
    return false;
  }
}
