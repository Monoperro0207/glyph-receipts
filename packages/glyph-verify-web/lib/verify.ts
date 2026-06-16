// Independent TS verifier for Glyph Receipts.
//
// The *logic* (the four ordered checks) is reimplemented from scratch here — it
// does NOT import anything from the Python side. Canonicalization + hashing is
// reused from `@glyphp/core` (`canonicalHash`), which is conformance-tested
// byte-for-byte against the Python `canonical_hash`, so the two languages agree.

import { canonicalHash } from "@glyphp/core";
import { verifyAsync } from "@noble/ed25519";

export const GENESIS_PREV_HASH = "0".repeat(64);

// Must match Python's CORE_FIELDS exactly (order is irrelevant — JCS sorts keys).
const CORE_FIELDS = [
  "glyph_version",
  "receipt_id",
  "seq",
  "prev_hash",
  "agent",
  "action",
  "policy",
  "timestamp",
] as const;

export type Receipt = Record<string, any>;

export type FailedCheck = "schema" | "signature" | "hash" | "chain" | "sequence" | null;

export interface ReceiptResult {
  index: number;
  seq: unknown;
  ok: boolean;
  failedCheck: FailedCheck;
  detail: string;
  receipt: Receipt;
}

function coreView(receipt: Receipt): Record<string, unknown> {
  const out: Record<string, unknown> = {};
  for (const k of CORE_FIELDS) out[k] = receipt[k];
  return out;
}

async function verifySig(pubHex: string, message: string, sigHex: string): Promise<boolean> {
  try {
    const msg = new TextEncoder().encode(message);
    return await verifyAsync(sigHex, msg, pubHex);
  } catch {
    return false;
  }
}

const short = (s: string) => `${String(s).slice(0, 12)}…`;

export async function verifyReceipt(
  receipt: Receipt,
  prevPayloadHash: string,
  expectedSeq: number,
): Promise<{ ok: boolean; failedCheck: FailedCheck; detail: string }> {
  const pub = receipt?.agent?.pubkey;
  const storedHash = receipt?.payload_hash;
  const sig = receipt?.signature;
  if (typeof pub !== "string" || typeof storedHash !== "string" || typeof sig !== "string") {
    return { ok: false, failedCheck: "schema", detail: "receipt is missing required fields" };
  }

  // 1. signature over the stored payload_hash
  if (!(await verifySig(pub, storedHash, sig))) {
    return {
      ok: false,
      failedCheck: "signature",
      detail: "ed25519 signature does not verify against agent.pubkey",
    };
  }

  // 2. content actually hashes to the stored payload_hash
  const recomputed = canonicalHash(coreView(receipt));
  if (recomputed !== storedHash) {
    return {
      ok: false,
      failedCheck: "hash",
      detail: `content hashes to ${short(recomputed)} but receipt claims ${short(storedHash)}`,
    };
  }

  // 3. chain link to the previous receipt
  if (receipt.prev_hash !== prevPayloadHash) {
    return {
      ok: false,
      failedCheck: "chain",
      detail: `prev_hash ${short(receipt.prev_hash)} != previous payload_hash ${short(prevPayloadHash)}`,
    };
  }

  // 4. sequence monotonic, no gaps
  if (receipt.seq !== expectedSeq) {
    return {
      ok: false,
      failedCheck: "sequence",
      detail: `seq is ${receipt.seq}, expected ${expectedSeq}`,
    };
  }

  return { ok: true, failedCheck: null, detail: "ok" };
}

export async function verifyLedger(receipts: Receipt[]): Promise<ReceiptResult[]> {
  const results: ReceiptResult[] = [];
  let prev = GENESIS_PREV_HASH;
  for (let i = 0; i < receipts.length; i++) {
    const r = receipts[i];
    const { ok, failedCheck, detail } = await verifyReceipt(r, prev, i);
    results.push({ index: i, seq: r?.seq ?? i, ok, failedCheck, detail, receipt: r });
    // Advance by THIS receipt's stored hash so one tampered receipt only reddens itself.
    prev = typeof r?.payload_hash === "string" ? r.payload_hash : "";
  }
  return results;
}

export function parseLedger(text: string): Receipt[] {
  return text
    .split("\n")
    .map((l) => l.trim())
    .filter(Boolean)
    .map((l) => JSON.parse(l));
}
