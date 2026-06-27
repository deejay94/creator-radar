export function makeOpportunityKey(opportunity) {
  const platform = String(opportunity.platform || "").trim().toLowerCase();
  const externalId = String(opportunity.external_id || "").trim();

  if (!platform || !externalId) {
    throw new Error("Opportunity must include platform and external_id");
  }

  return `${platform}:${externalId}`;
}
