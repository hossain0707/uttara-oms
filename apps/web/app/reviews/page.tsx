"use client";
import { useEffect, useState } from "react";
import Shell from "@/components/Shell";
import { api } from "@/lib/api";
import { metrics } from "@/components/PersonalWorkspace";
type Report = {
  id: string;
  email: string;
  month: string;
  version: number;
  profile: { full_name?: string };
  summary: string;
  entries: ({ day: string; notes: string } & Record<
    string,
    string | number | null
  >)[];
  totals: Record<string, number>;
};
export default function Reviews() {
  const [items, setItems] = useState<Report[]>([]),
    [notes, setNotes] = useState<Record<string, string>>({}),
    [message, setMessage] = useState(""),
    [busy, setBusy] = useState(false);
  async function load() {
    try {
      setItems((await api<{ items: Report[] }>("/reviews")).items);
    } catch (e) {
      setMessage(String(e));
    }
  }
  useEffect(() => {
    void load();
  }, []);
  async function review(r: Report, decision: string) {
    setBusy(true);
    setMessage("");
    try {
      await api("/reviews/" + r.id, {
        method: "POST",
        body: JSON.stringify({
          expected_version: r.version,
          decision,
          note: notes[r.id],
        }),
      });
      await load();
      setMessage("Review saved and audited.");
    } catch (e) {
      setMessage(String(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <Shell
      title="Personal report reviews"
      subtitle="Only reports explicitly assigned to you appear here."
    >
      {message && (
        <div className="alert" role="status">
          {message}
        </div>
      )}
      {!items.length && (
        <div className="panel">No submitted reports await your review.</div>
      )}
      {items.map((r) => (
        <article className="panel" key={r.id} style={{ marginBottom: 20 }}>
          <h2>
            {r.profile.full_name || r.email} · {r.month.slice(0, 7)}
          </h2>
          <p>{r.email}</p>
          <p>{r.summary}</p>
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Date</th>
                  {metrics.map((m) => (
                    <th key={m.key}>
                      {m.label} ({m.unit})
                    </th>
                  ))}
                  <th>Notes</th>
                </tr>
              </thead>
              <tbody>
                {r.entries.map((e) => (
                  <tr key={e.day}>
                    <td>{e.day}</td>
                    {metrics.map((m) => (
                      <td key={m.key}>{e[m.key] ?? "—"}</td>
                    ))}
                    <td>{e.notes}</td>
                  </tr>
                ))}
                <tr>
                  <th>Total</th>
                  {metrics.map((m) => (
                    <td key={m.key}>{r.totals[m.key]}</td>
                  ))}
                  <td />
                </tr>
              </tbody>
            </table>
          </div>
          <label htmlFor={r.id}>Review note</label>
          <textarea
            className="input"
            id={r.id}
            maxLength={2000}
            value={notes[r.id] || ""}
            onChange={(e) =>
              setNotes((old) => ({ ...old, [r.id]: e.target.value }))
            }
          />
          <div className="form-actions">
            <button
              className="primary-btn"
              disabled={busy || !notes[r.id]?.trim()}
              onClick={() => void review(r, "REVIEWED")}
            >
              Mark reviewed
            </button>
            <button
              disabled={busy || !notes[r.id]?.trim()}
              onClick={() => void review(r, "RETURNED")}
            >
              Return for correction
            </button>
          </div>
          <p>
            Membership category changes require the separate organizational
            approval process.
          </p>
        </article>
      ))}
    </Shell>
  );
}
