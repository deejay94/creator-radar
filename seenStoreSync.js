import { mkdirSync, readFileSync, writeFileSync, existsSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { GetObjectCommand, PutObjectCommand, S3Client } from "@aws-sdk/client-s3";

function resolveStorePath() {
  return resolve(process.env.SEEN_OPPORTUNITIES_PATH || "seen_opportunities.json");
}

function isSyncEnabled() {
  return Boolean(
    process.env.SEEN_STORE_S3_BUCKET?.trim() && process.env.SEEN_STORE_S3_KEY?.trim(),
  );
}

function createS3Client() {
  const config = {
    region: process.env.SEEN_STORE_S3_REGION || process.env.AWS_REGION || "auto",
  };

  const endpoint = process.env.SEEN_STORE_S3_ENDPOINT?.trim();
  if (endpoint) {
    config.endpoint = endpoint;
    config.forcePathStyle = true;
  }

  return new S3Client(config);
}

export async function downloadSeenStore() {
  if (!isSyncEnabled()) {
    return;
  }

  const filePath = resolveStorePath();
  mkdirSync(dirname(filePath), { recursive: true });

  const client = createS3Client();

  try {
    const response = await client.send(
      new GetObjectCommand({
        Bucket: process.env.SEEN_STORE_S3_BUCKET,
        Key: process.env.SEEN_STORE_S3_KEY,
      }),
    );
    const body = await response.Body.transformToString();
    writeFileSync(filePath, body || "{}\n", "utf8");
    console.log("Downloaded seen opportunity store from object storage");
  } catch (error) {
    if (error.name === "NoSuchKey" || error.$metadata?.httpStatusCode === 404) {
      writeFileSync(filePath, "{}\n", "utf8");
      console.log("Seen opportunity store not found in object storage; starting empty");
      return;
    }

    console.error(`Failed to download seen opportunity store: ${error.message}`);
  }
}

export async function uploadSeenStore() {
  if (!isSyncEnabled()) {
    return;
  }

  const filePath = resolveStorePath();
  if (!existsSync(filePath)) {
    console.error("Seen opportunity store file missing; skipping upload");
    return;
  }

  const client = createS3Client();
  const body = readFileSync(filePath);

  try {
    await client.send(
      new PutObjectCommand({
        Bucket: process.env.SEEN_STORE_S3_BUCKET,
        Key: process.env.SEEN_STORE_S3_KEY,
        Body: body,
        ContentType: "application/json",
      }),
    );
    console.log("Uploaded seen opportunity store to object storage");
  } catch (error) {
    console.error(`Failed to upload seen opportunity store: ${error.message}`);
  }
}
