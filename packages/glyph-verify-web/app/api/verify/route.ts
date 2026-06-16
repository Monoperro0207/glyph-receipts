// Server-side verification. `@glyphp/core` hashes via node:crypto, so the
// independent TS verifier runs here (Node runtime), not in the client bundle.
// Still TypeScript, still zero dependency on the Python implementation.
import { NextRequest, NextResponse } from "next/server";
import { verifyLedger, parseLedger } from "../../../lib/verify";

export const runtime = "nodejs";

export async function POST(req: NextRequest) {
  let text: string;
  try {
    const body = await req.json();
    text = String(body.text ?? "");
  } catch {
    return NextResponse.json({ error: "invalid request body" }, { status: 400 });
  }

  let receipts;
  try {
    receipts = parseLedger(text);
  } catch (e) {
    return NextResponse.json(
      { error: `could not parse ledger: ${(e as Error).message}` },
      { status: 422 },
    );
  }

  if (receipts.length === 0) {
    return NextResponse.json({ error: "no receipts found" }, { status: 422 });
  }

  const results = await verifyLedger(receipts);
  return NextResponse.json({ results });
}
