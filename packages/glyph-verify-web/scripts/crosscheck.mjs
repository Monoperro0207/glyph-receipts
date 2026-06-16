// Cross-language guard (Gotcha #1): the TS verifier must agree with the Python
// CLI on the exact same demo files. Run: `npm run crosscheck`.
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { verifyLedger, parseLedger } from "../lib/verify.ts";

const here = dirname(fileURLToPath(import.meta.url));
const demo = resolve(here, "../../../demo");

async function run(file) {
  const text = readFileSync(resolve(demo, file), "utf8");
  const results = await verifyLedger(parseLedger(text));
  console.log(`\n${file}`);
  for (const r of results) {
    const tag = r.ok ? "GREEN" : `RED   (${r.failedCheck})`;
    console.log(`  #${r.seq}  ${tag}${r.ok ? "" : "  — " + r.detail}`);
  }
  return results;
}

const seed = await run("seed_ledger.jsonl");
const tamper = await run("tamper_ledger.jsonl");

const seedOk = seed.every((r) => r.ok);
const tamperRed = tamper.filter((r) => !r.ok);
const pass =
  seedOk &&
  tamperRed.length === 1 &&
  tamperRed[0].seq === 2 &&
  tamperRed[0].failedCheck === "hash";

console.log(`\n${pass ? "PASS" : "FAIL"}: TS verifier matches expected (seed all green, tamper red on seq 2 / hash).`);
process.exit(pass ? 0 : 1);
