"use client";
import {useEffect, useState, type FormEvent} from "react";
import Link from "next/link";
import {Users, UserCheck, UserPlus, UserRound, ArrowUpRight, ArrowDownRight, Activity, GitBranch, ShieldCheck, ArrowRight} from "lucide-react";
import Shell from "@/components/Shell";
import {api, type Dashboard} from "@/lib/api";

const categories = [
  {key: "RUKON", label: "Rukon", bangla: "রুকন", icon: UserCheck},
  {key: "WORKER", label: "Worker", bangla: "কর্মী", icon: Users},
  {key: "ASSOCIATE", label: "Associate", bangla: "সহযোগী", icon: UserPlus},
  {key: "SUPPORTER", label: "Supporter", bangla: "সমর্থক", icon: UserRound},
] as const;

export default function Home() {
  const [data,setData] = useState<Dashboard | null>(null);
  const [error,setError] = useState("");
  const [start,setStart] = useState("");
  const [end,setEnd] = useState("");
  const [personSearch,setPersonSearch] = useState("");
  const [query,setQuery] = useState("");
  const [loading,setLoading] = useState(false);
  useEffect(()=>{let active=true;setLoading(true);setError("");setData(null);
    api<Dashboard>("/reports/dashboard?"+query).then(value=>{if(active)setData(value);})
      .catch(err=>{if(active)setError(String(err));}).finally(()=>{if(active)setLoading(false);});
    return ()=>{active=false;};},[query]);
  const filter=(event:FormEvent)=>{event.preventDefault();const params=new URLSearchParams();
    if(start)params.set("start_date",start);if(end)params.set("end_date",end);setQuery(params.toString());};
  const max = Math.max(1,...categories.map(c=>data?.by_category[c.key] || 0));
  return <Shell title="Overview" subtitle="A clear, real-time view of authorized organizational records.">
    <form className="toolbar dashboard-search" action="/members/"><input className="input" name="q" aria-label="Search people by name or member ID" placeholder="Search people by name, member ID or mobile" value={personSearch} onChange={e=>setPersonSearch(e.target.value)}/><button className="secondary-btn" type="submit">Find profile</button></form>
    {error && <div className="alert" role="alert">{error}</div>}
    <form className="toolbar" onSubmit={filter}>
      <label>From <input aria-label="Start date" className="input" type="date" value={start} onChange={e=>setStart(e.target.value)}/></label>
      <label>Through <input aria-label="End date" className="input" type="date" value={end} onChange={e=>setEnd(e.target.value)}/></label>
      <button className="primary-btn" disabled={loading}>Apply dates</button>
      <button className="secondary-btn" type="button" onClick={()=>{setStart("");setEnd("");setQuery("");}}>Current month</button>
    </form>
    <p className="hint" role="status">{loading?"Loading report…":data?`Active totals as of ${data.as_of}; movement from ${data.period.start_date} through ${data.period.end_date} (${data.timezone}).`:"Choose a reporting period."}</p>
    <div className="cards">{categories.map(({key,label,bangla,icon:Icon})=><article key={key} className="stat-card">
      <div className="stat-label"><span>{label} · {bangla}</span><span className="stat-icon"><Icon size={18}/></span></div>
      <div className="stat-number">{data ? data.by_category[key].toLocaleString() : "—"}</div><div className="stat-foot">Active as of selected end date</div>
    </article>)}</div>
    <div className="two-col">
      <div className="panel"><div className="panel-head"><div><h2>Organizational distribution</h2><span className="subhead">Active records by organizational category</span></div><Activity size={20} color="#318A67"/></div>
        {categories.map(c=><div className="barrow" key={c.key}><label>{c.label}</label><div className="bartrack"><div className="barfill" style={{width: ((data?.by_category[c.key] || 0) / max * 100) + "%"}}/></div><strong>{data ? data.by_category[c.key] : "—"}</strong></div>)}
        <div className="hint" style={{marginTop:25}}>Counts are calculated from active database records, not manually entered dashboard totals.</div>
      </div>
      <div className="panel"><div className="panel-head"><div><h2>Period movement</h2><span className="subhead">Selected reporting dates</span></div><ArrowUpRight size={20} color="#318A67"/></div>
        <div style={{display:"flex",justifyContent:"space-between",gap:10,padding:"18px 0",borderBottom:"1px solid #E9EFEA"}}><span><ArrowUpRight size={17} color="#23885A"/> Increase</span><strong>{data ? data.period.increase : "—"}</strong></div>
        <div style={{display:"flex",justifyContent:"space-between",gap:10,padding:"18px 0",borderBottom:"1px solid #E9EFEA"}}><span><ArrowDownRight size={17} color="#C56A55"/> Decrease</span><strong>{data ? data.period.decrease : "—"}</strong></div>
        <div style={{display:"flex",justifyContent:"space-between",gap:10,padding:"20px 0"}}><span><Activity size={17} color="#23885A"/> Net change</span><strong style={{color:"#268661"}}>{data ? data.period.net : "—"}</strong></div>
      </div>
    </div>
    {data&&<div className="panel" style={{marginBottom:20}}><h2>Comparison period</h2><p className="subhead">{data.comparison.start_date} through {data.comparison.end_date} · {data.comparison.total_active} active at period end · +{data.comparison.increase} / −{data.comparison.decrease} · net {data.comparison.net}</p></div>}
    <div className="two-col" style={{marginTop:20}}>
      <div className="panel"><div className="panel-head"><div><h2>Unit overview</h2><span className="subhead">Authorized, active people across units</span></div><Link className="link-action" href="/organization">All units <ArrowRight size={13}/></Link></div>
        {data?.by_unit?.length ? <div className="table-wrap"><table className="data-table"><thead><tr><th>Unit</th><th>Code</th><th>Active</th></tr></thead><tbody>{data.by_unit.slice(0,7).map(u=><tr key={u.id}><td>{u.name}</td><td>{u.code}</td><td><b>{u.count}</b></td></tr>)}</tbody></table></div> : <div className="empty"><GitBranch size={28}/><strong>No units configured yet</strong><span>Authorized admins can create the organizational structure.</span></div>}
      </div>
      <div className="panel"><div className="panel-head"><div><h2>Workspace snapshot</h2><span className="subhead">Live server-calculated totals</span></div><ShieldCheck color="#318A67" size={20}/></div>
        <div className="stat-number">{data ? data.total_active.toLocaleString() : "—"}</div><p className="subhead">Total active records within your approved access scope.</p>
        <hr className="subtle-divider"/><p className="hint">Sensitive profile changes are reviewed through the independent approval process. Reports are permission-scoped.</p>
        <Link href="/reports" className="primary-btn" style={{marginTop:12}}>Open reports <ArrowRight size={15}/></Link>
      </div>
    </div>
    <div className="panel" style={{marginTop:20}}><div className="panel-head"><div><h2>Ward overview</h2><span className="subhead">Active people by ward, restricted to your assigned scope</span></div><GitBranch size={20} color="#318A67"/></div>
      {data?.by_ward?.length ? <div className="table-wrap"><table className="data-table"><thead><tr><th>Ward</th><th>Code</th><th>Active</th></tr></thead><tbody>{data.by_ward.map(w=><tr key={w.id}><td>{w.name}</td><td>{w.code}</td><td><b>{w.count}</b></td></tr>)}</tbody></table></div> : <div className="empty"><GitBranch size={26}/><strong>No wards visible</strong><span>Authorized ward records will appear here.</span></div>}
    </div>
    {data&&<div className="panel" style={{marginTop:20}}><h2>Monthly history</h2><div className="table-wrap"><table className="data-table"><thead><tr><th>Month</th><th>Increase</th><th>Decrease</th><th>Net</th></tr></thead><tbody>{data.monthly_history.map(m=><tr key={m.month}><td>{m.month}</td><td>{m.increase}</td><td>{m.decrease}</td><td>{m.net}</td></tr>)}</tbody></table></div><p className="hint">First and last months use the selected dates. Category changes and transfers within your scope preserve total people. Organization names use current labels.</p></div>}
  </Shell>;
}
