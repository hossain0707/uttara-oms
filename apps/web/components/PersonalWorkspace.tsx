"use client";
import { useEffect, useState, type FormEvent } from "react";
import { api, downloadPersonalReport } from "@/lib/api";
export const metrics = [
  { key: "prayers", label: "Prayers", unit: "prayers" },
  { key: "literature", label: "Literature", unit: "pages" },
  { key: "organization", label: "Organizational work", unit: "minutes" },
  { key: "quran", label: "Quran study", unit: "pages" },
  { key: "hadith", label: "Hadith study", unit: "items" },
] as const;
type Book = { title: string; total_pages: number; completed_pages: number };
type Details = {
  full_name: string;
  father_name: string;
  phone: string;
  current_address: string;
  permanent_address: string;
  occupation: string;
  position: string;
  requested_unit_id: string | null;
  category: string;
  joined_on: string | null;
  worker_since: string | null;
  candidate_since: string | null;
  oath_on: string | null;
  books: Book[];
  consent: boolean;
};
type Profile = {
  version: number;
  details: Partial<Details>;
  goals: { metric: string; target: number }[];
  reviewer_assigned: boolean;
};
type Entry = { day: string; notes: string } & Record<
  "prayers" | "literature" | "organization" | "quran" | "hadith",
  number | null
>;
type Report = {
  id: string;
  month: string;
  version: number;
  status: string;
  entries: Entry[];
  summary: string;
  totals: Record<string, number>;
  review_note: string | null;
  entered_days: number;
};
type Node = {
  id: string;
  parent_id: string | null;
  kind: string;
  name: string;
};
const empty: Details = {
  full_name: "",
  father_name: "",
  phone: "",
  current_address: "",
  permanent_address: "",
  occupation: "",
  position: "",
  requested_unit_id: null,
  category: "",
  joined_on: null,
  worker_since: null,
  candidate_since: null,
  oath_on: null,
  books: [],
  consent: false,
};
const today = () =>
  new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Dhaka",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date());
export default function PersonalWorkspace() {
  const [tab, setTab] = useState("profile"),
    [profile, setProfile] = useState<Profile | null>(null),
    [details, setDetails] = useState<Details>(empty),
    [reports, setReports] = useState<Report[]>([]),
    [nodes, setNodes] = useState<Node[]>([]),
    [requests, setRequests] = useState<
      { id: string; role: string; status: string }[]
    >([]);
  const [month, setMonth] = useState(today().slice(0, 7)),
    [entries, setEntries] = useState<Entry[]>([]),
    [summary, setSummary] = useState(""),
    [day, setDay] = useState(today()),
    [values, setValues] = useState<Record<string, string>>({}),
    [notes, setNotes] = useState("");
  const [role, setRole] = useState("UNIT_EDITOR"),
    [scope, setScope] = useState(""),
    [notice, setNotice] = useState(""),
    [busy, setBusy] = useState(false),
    [consent, setConsent] = useState(false);
  const selected = reports.find((r) => r.month === month + "-01"),
    editable = !selected || ["DRAFT", "RETURNED"].includes(selected.status);
  async function load() {
    try {
      const [p, r, n, a] = await Promise.all([
        api<Profile>("/self/profile"),
        api<{ items: Report[] }>("/self/reports"),
        api<{ items: Node[] }>("/self/organization"),
        api<{ items: { id: string; role: string; status: string }[] }>(
          "/access/my-requests",
        ),
      ]);
      setProfile(p);
      setDetails({
        ...empty,
        ...Object.fromEntries(
          Object.entries(p.details).filter(([k]) => k in empty),
        ),
      });
      setReports(r.items);
      setNodes(n.items);
      setRequests(a.items);
    } catch (e) {
      setNotice(String(e));
    }
  }
  useEffect(() => {
    void load();
  }, []);
  useEffect(() => {
    const r = reports.find((r) => r.month === month + "-01");
    setEntries(r?.entries || []);
    setSummary(r?.summary || "");
    setDay(month === today().slice(0, 7) ? today() : month + "-01");
    setValues({});
    setNotes("");
  }, [reports, month]);
  async function act(work: () => Promise<void>) {
    setBusy(true);
    setNotice("");
    try {
      await work();
    } catch (e) {
      setNotice(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }
  async function saveProfile() {
    await act(async () => {
      setProfile(
        await api<Profile>("/self/profile", {
          method: "PUT",
          body: JSON.stringify({
            expected_version: profile?.version || 0,
            details,
          }),
        }),
      );
      setNotice("Profile and reading progress saved.");
    });
  }
  async function saveReport(submit: boolean) {
    await act(async () => {
      const r = await api<Report>("/self/reports", {
        method: "PUT",
        body: JSON.stringify({
          month: month + "-01",
          expected_version: selected?.version || 0,
          entries,
          summary,
          submit,
          consent,
        }),
      });
      setReports((old) => [r, ...old.filter((x) => x.id !== r.id)]);
      setNotice(
        submit ? "Report submitted to your assigned reviewer." : "Draft saved.",
      );
    });
  }
  function addDay(e: FormEvent) {
    e.preventDefault();
    const entry = {
      day,
      notes,
      ...Object.fromEntries(
        metrics.map((m) => [
          m.key,
          values[m.key] ? Number(values[m.key]) : null,
        ]),
      ),
    } as Entry;
    setEntries((old) =>
      [...old.filter((x) => x.day !== day), entry].sort((a, b) =>
        a.day.localeCompare(b.day),
      ),
    );
    setNotice("Day added to the form. Save your draft to keep it.");
  }
  const field = (key: keyof Details, label: string, type = "text") => (
    <div className="form-field" key={key}>
      <label htmlFor={key}>{label}</label>
      <input
        id={key}
        className="input"
        type={type}
        maxLength={1000}
        value={String(details[key] || "")}
        onChange={(e) =>
          setDetails((d) => ({
            ...d,
            [key]: e.target.value || (type === "date" ? null : ""),
          }))
        }
      />
    </div>
  );
  return (
    <section className="personal-workspace">
      <h1>My workspace</h1>
      <p>
        Your private profile, reports and targets. Organizational records
        require a separately approved role.
      </p>
      <div className="personal-tabs" role="tablist" aria-label="My workspace">
        {[
          ["profile", "My profile"],
          ["reports", "Daily & monthly reports"],
          ["targets", "Targets & books"],
          ["access", "Request permissions"],
        ].map(([id, label]) => (
          <button
            key={id}
            role="tab"
            aria-selected={tab === id}
            onClick={() => setTab(id)}
          >
            {label}
          </button>
        ))}
      </div>
      {notice && (
        <div className="alert" role="status">
          {notice}
        </div>
      )}
      {!profile ? (
        <p>Loading your workspace…</p>
      ) : (
        <>
          {tab === "profile" && (
            <form
              className="panel"
              onSubmit={(e) => {
                e.preventDefault();
                void saveProfile();
              }}
            >
              <h2>Personal profile</h2>
              <p>
                Self-reported details do not change your official category,
                counts or permissions.
              </p>
              <div className="form-grid">
                {field("full_name", "Full name")}
                {field("father_name", "Father’s name")}
                {field("phone", "Mobile number", "tel")}
                {field("occupation", "Occupation")}
                {field("position", "Responsibility / position")}
                {field("current_address", "Current address")}
                {field("permanent_address", "Permanent address")}
                <div className="form-field">
                  <label htmlFor="profile-unit">Requested unit</label>
                  <select
                    id="profile-unit"
                    className="select"
                    value={details.requested_unit_id || ""}
                    onChange={(e) =>
                      setDetails((d) => ({
                        ...d,
                        requested_unit_id: e.target.value || null,
                      }))
                    }
                  >
                    <option value="">Not assigned</option>
                    {nodes
                      .filter((n) => n.kind === "UNIT")
                      .map((n) => (
                        <option key={n.id} value={n.id}>
                          {nodes.find((w) => w.id === n.parent_id)?.name} /{" "}
                          {n.name}
                        </option>
                      ))}
                  </select>
                </div>
                <div className="form-field">
                  <label htmlFor="profile-category">
                    Self-reported category
                  </label>
                  <select
                    id="profile-category"
                    className="select"
                    value={details.category}
                    onChange={(e) =>
                      setDetails((d) => ({ ...d, category: e.target.value }))
                    }
                  >
                    {[
                      ["", "Not specified"],
                      ["RUKON", "Rukon — রুকন"],
                      ["WORKER", "Worker — কর্মী"],
                      ["ASSOCIATE", "Associate — সহযোগী"],
                      ["SUPPORTER", "Supporter — সমর্থক"],
                    ].map(([v, l]) => (
                      <option key={v} value={v}>
                        {l}
                      </option>
                    ))}
                  </select>
                </div>
                {field("joined_on", "Joining date", "date")}
                {field("worker_since", "Worker enrollment date", "date")}
                {field("candidate_since", "Rukon candidate date", "date")}
                {field("oath_on", "Oath date", "date")}
              </div>
              <label className="consent">
                <input
                  type="checkbox"
                  required
                  checked={details.consent}
                  onChange={(e) =>
                    setDetails((d) => ({ ...d, consent: e.target.checked }))
                  }
                />{" "}
                I consent to storing my profile and voluntary prayer, study and
                organizational reports. My assigned responsible person may
                review submitted reports and profile details. Main
                administrators manage assignments.
              </label>
              <button className="primary-btn" disabled={busy}>
                Save my profile
              </button>
            </form>
          )}
          {tab === "reports" && (
            <div className="panel">
              <h2>Daily entries and monthly report</h2>
              <label htmlFor="report-month">Reporting month</label>
              <input
                id="report-month"
                className="input"
                type="month"
                max={today().slice(0, 7)}
                value={month}
                onChange={(e) => {
                  if (e.target.value) setMonth(e.target.value);
                }}
              />
              <p>
                Status: <strong>{selected?.status || "New draft"}</strong> ·{" "}
                {entries.length} days entered. Blank means not reported; zero
                means none.
              </p>
              {selected && (
                <div className="form-actions">
                  {(["pdf", "xlsx"] as const).map((ext) => (
                    <button
                      key={ext}
                      disabled={busy}
                      onClick={() =>
                        void act(() => downloadPersonalReport(selected.id, ext))
                      }
                    >
                      Download {ext.toUpperCase()}
                    </button>
                  ))}
                </div>
              )}
              {selected?.review_note && (
                <div className="alert">Reviewer: {selected.review_note}</div>
              )}
              {editable && (
                <form onSubmit={addDay}>
                  <div className="form-grid">
                    <div className="form-field">
                      <label htmlFor="entry-day">Date</label>
                      <input
                        id="entry-day"
                        className="input"
                        required
                        type="date"
                        min={month + "-01"}
                        max={
                          month === today().slice(0, 7)
                            ? today()
                            : month +
                              "-" +
                              new Date(
                                Number(month.slice(0, 4)),
                                Number(month.slice(5, 7)),
                                0,
                              ).getDate()
                        }
                        value={day}
                        onChange={(e) => {
                          setDay(e.target.value);
                          const old = entries.find(
                            (x) => x.day === e.target.value,
                          );
                          setValues(
                            Object.fromEntries(
                              metrics.map((m) => [
                                m.key,
                                old?.[m.key] == null ? "" : String(old[m.key]),
                              ]),
                            ),
                          );
                          setNotes(old?.notes || "");
                        }}
                      />
                    </div>
                    {metrics.map((m) => (
                      <div className="form-field" key={m.key}>
                        <label htmlFor={"entry-" + m.key}>
                          {m.label} ({m.unit})
                        </label>
                        <input
                          id={"entry-" + m.key}
                          className="input"
                          type="number"
                          min={0}
                          step={1}
                          max={
                            m.key === "prayers"
                              ? 100
                              : m.key === "organization"
                                ? 1440
                                : 100000
                          }
                          value={values[m.key] || ""}
                          onChange={(e) =>
                            setValues((v) => ({
                              ...v,
                              [m.key]: e.target.value,
                            }))
                          }
                        />
                      </div>
                    ))}
                    <div className="form-field full">
                      <label htmlFor="day-notes">Daily notes</label>
                      <input
                        id="day-notes"
                        className="input"
                        maxLength={1000}
                        value={notes}
                        onChange={(e) => setNotes(e.target.value)}
                      />
                    </div>
                  </div>
                  <button>Add / update day</button>
                </form>
              )}
              <div className="table-wrap">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Date</th>
                      {metrics.map((m) => (
                        <th key={m.key}>{m.label}</th>
                      ))}
                      <th>Notes</th>
                      {editable && <th>Remove</th>}
                    </tr>
                  </thead>
                  <tbody>
                    {entries.map((e) => (
                      <tr key={e.day}>
                        <td>{e.day}</td>
                        {metrics.map((m) => (
                          <td key={m.key}>{e[m.key] ?? "—"}</td>
                        ))}
                        <td>{e.notes}</td>
                        {editable && (
                          <td>
                            <button
                              aria-label={"Remove " + e.day}
                              onClick={() =>
                                setEntries((old) =>
                                  old.filter((x) => x.day !== e.day),
                                )
                              }
                            >
                              Remove
                            </button>
                          </td>
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="form-field">
                <label htmlFor="month-summary">Monthly summary</label>
                <textarea
                  id="month-summary"
                  className="input"
                  maxLength={2000}
                  disabled={!editable}
                  value={summary}
                  onChange={(e) => setSummary(e.target.value)}
                />
              </div>
              {editable && (
                <>
                  <label className="consent">
                    <input
                      type="checkbox"
                      checked={consent}
                      onChange={(e) => setConsent(e.target.checked)}
                    />{" "}
                    I consent to storing this report and sharing it with my
                    assigned reviewer when submitted.
                  </label>
                  <div className="form-actions">
                    <button
                      disabled={busy || !consent}
                      onClick={() => void saveReport(false)}
                    >
                      Save draft
                    </button>
                    <button
                      className="primary-btn"
                      disabled={
                        busy ||
                        !consent ||
                        !profile.reviewer_assigned ||
                        !entries.length
                      }
                      onClick={() => void saveReport(true)}
                    >
                      Submit for review
                    </button>
                  </div>
                  {!profile.reviewer_assigned && (
                    <p>
                      Drafts are available now. Ask the main administrator to
                      assign your reviewer before submitting.
                    </p>
                  )}
                </>
              )}
            </div>
          )}
          {tab === "targets" && (
            <div className="panel">
              <h2>Monthly targets</h2>
              <p>
                Targets are assigned by the main administrator. Reaching them
                never automatically changes your category.
              </p>
              {profile.goals.length ? (
                <div className="form-grid">
                  {profile.goals.map((g) => {
                    const m = metrics.find((m) => m.key === g.metric),
                      actual = selected?.totals[g.metric] || 0;
                    return (
                      <div className="target-card" key={g.metric}>
                        <strong>{m?.label}</strong>
                        <p>
                          {actual} / {g.target} {m?.unit} ({month})
                        </p>
                        <progress
                          value={Math.min(actual, g.target)}
                          max={g.target}
                        />
                        <p>
                          {Math.max(0, g.target - actual)} remaining ·{" "}
                          {selected?.entered_days || 0} days reported
                        </p>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p>No targets assigned yet.</p>
              )}
              <h2>My reading list</h2>
              {details.books.map((b, i) => (
                <div className="book-row" key={i}>
                  <label>
                    Book title
                    <input
                      className="input"
                      maxLength={250}
                      value={b.title}
                      onChange={(e) =>
                        setDetails((d) => ({
                          ...d,
                          books: d.books.map((x, j) =>
                            j === i ? { ...x, title: e.target.value } : x,
                          ),
                        }))
                      }
                    />
                  </label>
                  {(["total_pages", "completed_pages"] as const).map((k) => (
                    <label key={k}>
                      {k === "total_pages" ? "Total pages" : "Pages completed"}
                      <input
                        className="input"
                        type="number"
                        min={0}
                        max={100000}
                        value={b[k]}
                        onChange={(e) =>
                          setDetails((d) => ({
                            ...d,
                            books: d.books.map((x, j) =>
                              j === i
                                ? { ...x, [k]: Number(e.target.value) }
                                : x,
                            ),
                          }))
                        }
                      />
                    </label>
                  ))}
                  <button
                    onClick={() =>
                      setDetails((d) => ({
                        ...d,
                        books: d.books.filter((_, j) => j !== i),
                      }))
                    }
                  >
                    Remove
                  </button>
                </div>
              ))}
              <div className="form-actions">
                <button
                  disabled={details.books.length >= 100}
                  onClick={() =>
                    setDetails((d) => ({
                      ...d,
                      books: [
                        ...d.books,
                        { title: "", total_pages: 0, completed_pages: 0 },
                      ],
                    }))
                  }
                >
                  Add book
                </button>
                <button
                  disabled={busy || !details.consent}
                  onClick={() => void saveProfile()}
                >
                  Save reading progress
                </button>
              </div>
            </div>
          )}
          {tab === "access" && (
            <div className="panel">
              <h2>Request a responsible-person role</h2>
              <p>
                Your personal workspace works without administrative permission.
                Organizational access requires main administrator approval and
                an authenticator.
              </p>
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  void act(async () => {
                    await api("/access/apply", {
                      method: "POST",
                      body: JSON.stringify({
                        role,
                        scope_node_id: role === "THANA_VIEWER" ? null : scope,
                      }),
                    });
                    await load();
                    setNotice("Request sent to the main administrator.");
                  });
                }}
              >
                <div className="form-grid">
                  <div className="form-field">
                    <label htmlFor="requested-role">Requested role</label>
                    <select
                      id="requested-role"
                      className="select"
                      value={role}
                      onChange={(e) => {
                        setRole(e.target.value);
                        setScope("");
                      }}
                    >
                      <option value="UNIT_EDITOR">
                        Unit responsible person
                      </option>
                      <option value="WARD_ADMIN">Ward administrator</option>
                      <option value="THANA_VIEWER">Thana report viewer</option>
                    </select>
                  </div>
                  {role !== "THANA_VIEWER" && (
                    <div className="form-field">
                      <label htmlFor="requested-scope">Ward / unit</label>
                      <select
                        id="requested-scope"
                        className="select"
                        required
                        value={scope}
                        onChange={(e) => setScope(e.target.value)}
                      >
                        <option value="">Select scope</option>
                        {nodes
                          .filter(
                            (n) =>
                              n.kind ===
                              (role === "WARD_ADMIN" ? "WARD" : "UNIT"),
                          )
                          .map((n) => (
                            <option key={n.id} value={n.id}>
                              {n.name}
                            </option>
                          ))}
                      </select>
                    </div>
                  )}
                </div>
                <button className="primary-btn" disabled={busy}>
                  Request permission
                </button>
              </form>
              <h3>My requests</h3>
              {requests.map((r) => (
                <p key={r.id}>
                  {r.role.replaceAll("_", " ")} · {r.status}
                </p>
              ))}
              {!requests.length && <p>No permission requests yet.</p>}
            </div>
          )}
        </>
      )}
    </section>
  );
}
