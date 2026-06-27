import { mkdirSync, readFileSync, renameSync, writeFileSync, existsSync } from "node:fs";
import { dirname, resolve } from "node:path";

export class SeenOpportunityStore {
  constructor(filePath = process.env.SEEN_OPPORTUNITIES_PATH || "seen_opportunities.json") {
    this.filePath = resolve(filePath);
    this.seen = {};
  }

  async load() {
    this.seen = {};

    if (!existsSync(this.filePath)) {
      return;
    }

    try {
      const raw = readFileSync(this.filePath, "utf8").trim();
      if (!raw) {
        return;
      }

      const parsed = JSON.parse(raw);
      if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
        throw new Error("Seen opportunity store must be a JSON object");
      }

      this.seen = parsed;
    } catch (error) {
      console.error(`Failed to load seen opportunity store: ${error.message}`);
      this.seen = {};
    }
  }

  async save() {
    try {
      mkdirSync(dirname(this.filePath), { recursive: true });
      const tempPath = `${this.filePath}.tmp`;
      writeFileSync(tempPath, `${JSON.stringify(this.seen, null, 2)}\n`, "utf8");
      renameSync(tempPath, this.filePath);
      return true;
    } catch (error) {
      console.error(`Failed to save seen opportunity store: ${error.message}`);
      return false;
    }
  }

  has(key) {
    return Boolean(this.seen[key]);
  }

  mark(key) {
    this.seen[key] = true;
  }

  markMany(keys) {
    for (const key of keys) {
      this.mark(key);
    }
  }

  count() {
    return Object.keys(this.seen).length;
  }
}
