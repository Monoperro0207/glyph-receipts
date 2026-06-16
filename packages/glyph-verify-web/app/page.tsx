"use client";

import { useCallback, useRef, useState } from "react";

interface ReceiptResult {
  index: number;
  seq: number | string;
  ok: boolean;
  failedCheck: string | null;
  detail: string;
  receipt: any;
}

const CHECK_LABEL: Record<string, string> = {
  schema: "Malformed receipt",
  signature: "Bad signature",
  hash: "Content doesn't match its hash",
  chain: "Broken hash chain",
  sequence: "Sequence gap",
};

export default function Page() {
  const [results, setResults] = useState<ReceiptResult[] | null>(null);
  const [fileName, setFileName] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [over, setOver] = useState(false);
  const [busy, setBusy] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const verify = useCallback(async (text: string, name: string) => {
    setBusy(true);
    setError("");
    setResults(null);
    setFileName(name);
    try {
      const res = await fetch("/api/verify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error ?? "verification failed");
        return;
      }
      setResults(data.results);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }, []);

  const onFile = useCallback(
    async (file: File) => {
      const text = await file.text();
      await verify(text, file.name);
    },
    [verify],
  );

  const loadDemo = useCallback(
    async (path: string) => {
      const res = await fetch(path);
      const text = await res.text();
      await verify(text, path.replace("/", ""));
    },
    [verify],
  );

  const tampered = results?.filter((r) => !r.ok) ?? [];
  const allOk = results !== null && tampered.length === 0;
  const firstBad = tampered[0];

  return (
    <main className="wrap">
      <header>
        <h1>
          Glyph Receipts <span className="dot">·</span> Independent Verifier
        </h1>
        <p>
          Every agent spend is a signed, hash-chained receipt. This verifier trusts neither the
          agent nor its runtime — it re-checks the cryptography in TypeScript. Drop a{" "}
          <code style={{ fontFamily: "var(--mono)" }}>ledger.jsonl</code>; tamper with one line and
          the chain gives it away.
        </p>
      </header>

      <div
        className={`drop${over ? " over" : ""}`}
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setOver(true);
        }}
        onDragLeave={() => setOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setOver(false);
          const f = e.dataTransfer.files?.[0];
          if (f) onFile(f);
        }}
      >
        <div className="big">{busy ? "Verifying…" : "Drop a ledger.jsonl here"}</div>
        <div className="sub">or click to browse · one receipt per line</div>
        <input
          ref={inputRef}
          type="file"
          accept=".jsonl,.json,.txt"
          hidden
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) onFile(f);
          }}
        />
      </div>

      <div className="demo-row">
        <button className="btn green" onClick={() => loadDemo("/seed_ledger.jsonl")}>
          <span className="k">load</span> valid ledger
        </button>
        <button className="btn red" onClick={() => loadDemo("/tamper_ledger.jsonl")}>
          <span className="k">load</span> tampered ledger
        </button>
      </div>

      {error && <div className="err">⚠ {error}</div>}

      {results && (
        <>
          <div className={`summary ${allOk ? "ok" : "bad"}`}>
            <span className="badge">{allOk ? "VERIFIED" : "TAMPERED"}</span>
            <div>
              <div className="title">
                {allOk
                  ? "Ledger intact — every receipt verifies"
                  : `Tampering detected on receipt #${firstBad.seq}`}
              </div>
              <div className="meta">
                {fileName} · {results.length} receipt{results.length === 1 ? "" : "s"}
                {!allOk && ` · ${CHECK_LABEL[firstBad.failedCheck ?? ""] ?? firstBad.failedCheck}`}
              </div>
            </div>
          </div>

          <div className="cards">
            {results.map((r) => {
              const a = r.receipt?.action ?? {};
              return (
                <div key={r.index} className={`card ${r.ok ? "ok" : "bad"}`}>
                  <div className="seqcol">
                    seq
                    <div className="n">{r.seq}</div>
                  </div>
                  <div className="mid">
                    <div className="line1">
                      <span className="amount">
                        {typeof a.amount === "number"
                          ? `$${(a.amount / 100).toFixed(2)}`
                          : String(a.amount)}
                      </span>{" "}
                      <span className="merchant">→ {a.merchant ?? "?"}</span>
                    </div>
                    {a.description && <div className="desc">{a.description}</div>}
                    {r.ok ? (
                      <div className="hash">
                        payload_hash {String(r.receipt?.payload_hash ?? "").slice(0, 24)}…
                      </div>
                    ) : (
                      <div className="fail">
                        <b>{CHECK_LABEL[r.failedCheck ?? ""] ?? r.failedCheck}</b> — {r.detail}
                      </div>
                    )}
                  </div>
                  <div className="statuscol">
                    <span className={`pill ${r.ok ? "ok" : "bad"}`}>
                      <span className="led" />
                      {r.ok ? "GREEN" : "RED"}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}

      <div className="footnote">
        Checks run in order, reporting the first failure: <code>signature</code> →{" "}
        <code>hash</code> → <code>chain</code> → <code>sequence</code>. Canonicalization (JCS /
        RFC&nbsp;8785) is reused from <code>@glyphp/core</code> — byte-identical to the Python
        signer, so the receipt this TypeScript verifier checks is the same one Python signed.
      </div>
    </main>
  );
}
