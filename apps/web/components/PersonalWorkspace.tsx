"use client";
import { useEffect, useState, type FormEvent } from "react";
import SearchSelect from './SearchSelect';
import AddressFields from './AddressFields';
import catalogs from '@/data/catalogs.json';
import ProfileCard from './ProfileCard';
import {prepareProfilePhoto} from '@/lib/profile-photo';
import Library from './Library';
import ReportingBook from './ReportingBook';
import {reportMetrics,dailyReportFields,type Reflections, type PersonalReport as Report, type ReportEntry as Entry} from '@/lib/report-book';
import { api, downloadPersonalReport } from "@/lib/api";
export const metrics = reportMetrics;
type Book = { title: string; total_pages: number; completed_pages: number };
type Details = {
  photo: string;
  directory_sharing: boolean;
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
type Node = {
  id: string;
  parent_id: string | null;
  kind: string;
  name: string;
};
const empty: Details = {
  photo: "",
  directory_sharing: false,
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
  const [editingProfile, setEditingProfile] = useState(false);
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
  const [reflection,setReflection]=useState<Reflections>({achievements:"",incomplete_work:"",next_plan:""});
  const [entryDirty, setEntryDirty] = useState(false);
  const [role, setRole] = useState("UNIT_EDITOR"),
    [scope, setScope] = useState(""),
    [notice, setNotice] = useState(""),
    [busy, setBusy] = useState(false),
    [consent, setConsent] = useState(false),
    [bookGroup, setBookGroup] = useState("");
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
      setEditingProfile(!p.details.full_name);
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
    const openLibrary = () => { if (window.location.hash === "#library") setTab("library"); };
    openLibrary();
    window.addEventListener("hashchange", openLibrary);
    void load();
    return () => window.removeEventListener("hashchange", openLibrary);
  }, []);
  useEffect(() => {
    const r = reports.find((r) => r.month === month + "-01");
    setEntries(r?.entries || []);
    setSummary(r?.summary || "");
    setReflection({achievements:r?.achievements||"",incomplete_work:r?.incomplete_work||"",next_plan:r?.next_plan||""});
    const selectedDay = month === today().slice(0, 7) ? today() : month + "-01";
    setDay(selectedDay);
    const existing = r?.entries.find(e=>e.day===selectedDay);
    setValues(Object.fromEntries(dailyReportFields.map(m=>[m.key,existing?.[m.key]==null?'':String(existing[m.key])])));
    setNotes(existing?.notes || "");
    setEntryDirty(false);
    setConsent(false);
  }, [reports, month]);
  const reportDirty = JSON.stringify(entries)!==JSON.stringify(selected?.entries||[]) || summary!==(selected?.summary||"") || entryDirty || Object.entries(reflection).some(([key,value])=>value!==(selected?.[key as keyof Reflections]||""));
  function chooseDay(value:string) {
    setDay(value);
    const old=entries.find(e=>e.day===value);
    setValues(Object.fromEntries(dailyReportFields.map(m=>[m.key,old?.[m.key]==null?"":String(old[m.key])])));
    setNotes(old?.notes||"");setEntryDirty(false);
  }
  useEffect(()=>{if(!reportDirty)return;const warn=(event:BeforeUnloadEvent)=>{event.preventDefault();};window.addEventListener('beforeunload',warn);return()=>window.removeEventListener('beforeunload',warn);},[reportDirty]);
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
  async function saveProfile(reading = false) {
    await act(async () => {
      if (!reading && !details.full_name.trim()) throw new Error("Enter your full name.");
      if (!reading && details.phone) {
        const phone = details.phone.replace(/[\s()\-]/g, "").replace(/^\+?880/, "0");
        if (!/^01[3-9][0-9]{8}$/.test(phone)) throw new Error("Mobile number: use a valid Bangladeshi mobile number, such as 017XXXXXXXX or +88017XXXXXXXX.");
      }
      const books = reading ? details.books.filter((b) => b.title.trim() || b.total_pages || b.completed_pages) : (profile?.details.books || []);
      if (reading) {
        for (const [i, book] of books.entries()) {
          if (!book.title.trim()) throw new Error(`Book ${i + 1}: enter a title or remove the unfinished entry.`);
          if (![book.total_pages, book.completed_pages].every((n) => Number.isInteger(n) && n >= 0 && n <= 100000)) throw new Error(`Book ${i + 1}: page counts must be whole numbers from 0 to 100000.`);
          if (book.total_pages && book.completed_pages > book.total_pages) throw new Error(`Book ${i + 1}: completed pages cannot exceed total pages.`);
        }
      }
      const saved = await api<Profile>("/self/profile", {
          method: "PUT",
          body: JSON.stringify({
            section: reading ? "reading" : "profile",
            expected_version: profile?.version || 0,
            details: reading ? { ...empty, ...Object.fromEntries(Object.entries(profile?.details || {}).filter(([k]) => k in empty)), books: books.map((b) => ({...b, title: b.title.trim()})), consent: details.consent } : { ...details, books },
          }),
        });
      setProfile(saved);
      if (reading) setDetails((d) => ({ ...d, books: saved.details.books || [] }));
      else { setDetails(d=>({...empty,...saved.details,books:d.books}));setEditingProfile(false); }
      setNotice(reading ? "Reading progress saved." : "Profile saved.");
    });
  }
  async function saveReport(submit: boolean) {
    await act(async () => {
      if (entryDirty) throw new Error("Click Add / update day before saving this report so your daily entry is included.");
      const r = await api<Report>("/self/reports", {
        method: "PUT",
        body: JSON.stringify({
          month: month + "-01",
          expected_version: selected?.version || 0,
          entries,
          summary,
          ...reflection,
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
    if (!editable || busy) return;
    if (!day || day.slice(0,7)!==month || day>today()) {setNotice("Choose a valid date in this reporting month.");return;}
    if (!Object.values(values).some(v=>v!=="") && !notes.trim()) {setNotice("Enter at least one daily value or a note.");return;}
    for (const m of dailyReportFields) {const v=values[m.key];if(m.kind==='number'&&v!==undefined&&v!==""&&((m.step===1?!Number.isInteger(Number(v)):!Number.isFinite(Number(v))||Math.abs(Number(v)*100-Math.round(Number(v)*100))>1e-7)||Number(v)<0||Number(v)>m.max)){setNotice(`${m.label}: enter a valid amount from 0 to ${m.max}.`);return;}}
    if(values.congregational_prayers!==undefined&&values.congregational_prayers!==""&&(!values.prayers||Number(values.congregational_prayers)>Number(values.prayers))){setNotice("মোট সালাত আগে লিখুন; জামাতে সালাত মোট সালাতের বেশি হতে পারবে না।");return;}
    const entry = {
      day,
      notes,
      ...Object.fromEntries(
        dailyReportFields.map((m) => [
          m.key,
          values[m.key]===undefined||values[m.key]===""?null:m.kind==='check'?values[m.key]==='true':Number(values[m.key]),
        ]),
      ),
    } as Entry;
    setEntries((old) =>
      [...old.filter((x) => x.day !== day), entry].sort((a, b) =>
        a.day.localeCompare(b.day),
      ),
    );
    setValues({});
    setNotes("");
    setEntryDirty(false);
    setNotice("দিন যোগ করা হয়েছে। স্থায়ীভাবে রাখতে খসড়া সংরক্ষণ করুন।");
  }
  const field = (key: keyof Details, label: string, type = "text") => key === "occupation" || key === "position" ? <SearchSelect key={key} label={label} placeholder={key === "occupation" ? "e.g. Teacher" : "e.g. Ward secretary"} value={String(details[key] || "")} maxLength={160} items={key === "occupation" ? catalogs.occupations : catalogs.positions} onChange={value=>setDetails(d=>({...d,[key]:value}))} /> : key === "current_address" || key === "permanent_address" ? <AddressFields key={key} label={label} value={String(details[key] || "")} onChange={value=>setDetails(d=>({...d,[key]:value}))} /> : (
    <div className="form-field" key={key}>
      <label htmlFor={key}>{label}</label>
      <input
        id={key}
        className="input"
        type={type}
        maxLength={key === "full_name" || key === "father_name" ? 200 : key === "phone" ? 40 : 1000}
        placeholder={key === "phone" ? "01XXXXXXXXX or +8801XXXXXXXXX" : undefined}
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
      <button disabled={busy} onClick={() => {if(window.confirm("Reload saved workspace data? Unsaved edits will be discarded.")) {setNotice(""); void load();}}}>Reload saved data</button>
      <div className="personal-tabs" role="tablist" aria-label="My workspace">
        {[
          ["profile", "My profile"],
          ["reports", "Daily & monthly reports"],
          ["targets", "Targets & books"],
          ["library", "Library & syllabus"],
          ["access", "Request permissions"],
        ].map(([id, label]) => (
          <button
            key={id}
            role="tab"
            aria-selected={tab === id}
            onClick={() => { setTab(id); setNotice(""); }}
          >
            {label}
          </button>
        ))}
      </div>
      {tab === "library" && <Library books={details.books} canAdd={!!profile?.details.consent && !busy} onAdd={book=>setDetails(d=>({...d,books:[...d.books,book]}))} onManage={()=>setTab("targets")} />}
      {notice && (
        <div className={notice.includes("saved.") ? "success-msg" : "alert"} role="status">
          {notice}
        </div>
      )}
      {!profile ? (
        <div><p>{notice ? "Your workspace could not be loaded." : "Loading your workspace…"}</p>{notice && <button onClick={() => void load()}>Retry loading workspace</button>}</div>
      ) : (
        <>
          {tab === "profile" && !editingProfile && <ProfileCard privateView profile={{...profile.details,unit:nodes.find(n=>n.id===profile.details.requested_unit_id)?.name}} onEdit={()=>{setEditingProfile(true);setNotice("");}}/>}
          {tab === "profile" && editingProfile && (
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
              <div className="photo-editor">
                {details.photo ? <img src={details.photo} alt="Profile photo preview"/> : <span>No photo added</span>}
                <div><label htmlFor="profile-photo">Profile photo</label><input id="profile-photo" type="file" accept="image/jpeg,image/png,image/webp" disabled={busy} onChange={e=>{const file=e.target.files?.[0];e.target.value="";if(file)void act(async()=>{const photo=await prepareProfilePhoto(file);setDetails(d=>({...d,photo}));});}}/><p className="hint">JPG, PNG or WebP, up to 5 MB. Your photo is cropped to a square.</p>{details.photo&&<button type="button" disabled={busy} className="secondary-btn" onClick={()=>setDetails(d=>({...d,photo:""}))}>Remove photo</button>}</div>
              </div>
              <div className="form-grid">
                <h3 className="form-field full">1. Personal information</h3>
                {field("full_name", "Full name")}
                {field("father_name", "Father’s name")}
                {field("phone", "Mobile number", "tel")}
                <h3 className="form-field full">2. Occupation & responsibility</h3>
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
                {!nodes.some((n) => n.kind === "UNIT") && <p>No active units have been configured. You can save your profile without a unit; ask an administrator to create units under the wards.</p>}
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
                <h3 className="form-field full">3. Organizational dates</h3>
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
                I consent to storing my profile information, photo and voluntary prayer, study and
                organizational reports. Authorized Thana administrators may find my basic profile summary. My assigned responsible person may
                review submitted reports and profile details. Main
                administrators manage assignments.
              </label>
              <label className="consent"><input type="checkbox" checked={details.directory_sharing} onChange={e=>setDetails(d=>({...d,directory_sharing:e.target.checked}))}/> Show my photo in authorized people search. My personal reports stay private.</label>
              <div className="profile-form-actions"><button className="primary-btn" disabled={busy}>Save my profile</button>{profile.details.full_name&&<button type="button" className="secondary-btn" disabled={busy} onClick={()=>{setDetails(d=>({...empty,...profile.details,books:d.books}));setEditingProfile(false);setNotice("");}}>Cancel editing</button>}</div>
            </form>
          )}
          {tab === "reports" && <ReportingBook month={month} onMonth={setMonth} day={day} onDay={chooseDay} entries={entries} values={values}
              onValue={(key,value)=>{setValues(v=>({...v,[key]:value}));setEntryDirty(true);}} notes={notes} onNotes={value=>{setNotes(value);setEntryDirty(true);}}
              summary={summary} onSummary={setSummary} reflection={reflection} onReflection={(key,value)=>setReflection(old=>({...old,[key]:value}))} selected={selected} goals={selected?.goals ?? profile.goals}
              editable={editable} busy={busy} consent={consent} onConsent={setConsent} profileConsented={!!profile.details.consent}
              reviewerAssigned={profile.reviewer_assigned} entryDirty={entryDirty} dirty={reportDirty}
              onAdd={addDay} onRemove={date=>{setEntries(old=>old.filter(e=>e.day!==date));if(day===date){setValues({});setNotes("");setEntryDirty(false);}}}
              onSave={submit=>void saveReport(submit)} onDownload={ext=>{if(selected)void act(()=>downloadPersonalReport(selected.id,ext));}}/>}
          {tab === "targets" && (
            <div className="panel">
              <h2>Monthly targets</h2>
              <label htmlFor="target-month">Target reporting month</label>
              <input id="target-month" className="input" type="month" max={today().slice(0,7)} value={month} onChange={(e) => {if(e.target.value && (!reportDirty || window.confirm("Discard unsaved report changes and switch month?"))) setMonth(e.target.value);}} />
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
              <p>Save your profile and consent first. Reading progress is saved separately from profile edits. Completely empty new book rows are ignored.</p>
              <label htmlFor="book-topic">Book section</label>
              <select id="book-topic" className="select" value={bookGroup} onChange={e=>setBookGroup(e.target.value)}><option value="">All sections</option>{[...new Set(catalogs.books.map(b=>b.group))].map(g=><option key={g} value={g}>{g.split(' / ')[0]}</option>)}</select>
              <p className="hint">Titles transcribed from your supplied syllabus photos. Confirm the exact title and edition; a custom title is allowed. Reading a book does not automatically change membership category.</p>
              {details.books.map((b, i) => (
                <div className="book-row" key={i}>
                  <SearchSelect label={"Book title"} placeholder="e.g. Islam Porichiti" value={b.title} items={catalogs.books.filter(x=>!bookGroup||x.group===bookGroup)} onChange={value=>setDetails(d=>({...d,books:d.books.map((x,j)=>j===i?{...x,title:value}:x)}))} />
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
                  disabled={busy || !profile.details.consent}
                  onClick={() => void saveProfile(true)}
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
                    setRequests((await api<{items: {id:string;role:string;status:string}[]}>("/access/my-requests")).items);
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
