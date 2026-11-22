"use client";
import {useEffect,useState} from "react";
import {ShieldCheck,Clock3,CheckCircle2,XCircle} from "lucide-react";
import Shell from "@/components/Shell";
import {api,type Approval,type Identity} from "@/lib/api";

export default function ApprovalPage(){
  const [items,setItems]=useState<Approval[]>([]);const [identity,setIdentity]=useState<Identity|null>(null);
  const [notice,setNotice]=useState("");const [busy,setBusy]=useState("");
  const load=async()=>{try{const [r,me]=await Promise.all([api<{items:Approval[]}>("/approvals"),api<Identity>("/me")]);setItems(r.items);setIdentity(me);}catch(e){setNotice(String(e));}};
  useEffect(()=>{void load();},[]);
  const approveRole=identity?.roles.some(r=>r.role==="THANA_ADMIN"||r.role==="WARD_ADMIN");
  const decide=async(id:string,approved:boolean)=>{if(!window.confirm(approved?"Approve this sensitive change?":"Reject this request?"))return;setBusy(id);setNotice("");
    try{await api("/approvals/"+id+"/decision",{method:"POST",body:JSON.stringify({approve:approved})});setNotice("Decision recorded in the audit history.");await load();}
    catch(e){setNotice(e instanceof Error?e.message:String(e));}finally{setBusy("");}};
  const pending=items.filter(i=>i.status==="PENDING");
  return <Shell title="Approval center" subtitle="Independent authorization for important profile and organizational changes.">
    {notice&&<div className="alert" role="status">{notice}</div>}
    <div className="cards" style={{gridTemplateColumns:"repeat(2,minmax(0,1fr))"}}><div className="stat-card"><div className="stat-label">Pending review <Clock3 size={18}/></div><div className="stat-number">{pending.length}</div><div className="stat-foot">Requests awaiting an independent decision</div></div><div className="stat-card"><div className="stat-label">Visible requests <ShieldCheck size={18}/></div><div className="stat-number">{items.length}</div><div className="stat-foot">Limited to your authorized scope</div></div></div>
    <div className="panel" style={{padding:0,overflow:"hidden"}}><div style={{padding:"25px 26px 14px"}}><h2>Pending change requests</h2><p className="subhead">Ordinary administrators cannot approve their own changes. The Master Admin can decide directly. Cross-ward transfers require Thana Admin authority.</p></div>
      {pending.length?<div className="table-wrap"><table className="data-table"><thead><tr><th>Type</th><th>Member reference</th><th>Proposed value</th><th>Requested</th><th>Decision</th></tr></thead><tbody>{pending.map(r=><tr key={r.id}><td><b>{r.kind}</b></td><td>{r.member_id.slice(0,8)}…</td><td>{r.proposed_value}</td><td>{new Date(r.requested_at).toLocaleDateString()}</td><td>{approveRole?<div style={{display:"flex",gap:8}}><button disabled={!!busy||r.requested_by===identity?.id&&!identity?.is_master_admin} onClick={()=>void decide(r.id,true)}><CheckCircle2 size={16}/> Approve</button><button disabled={!!busy||r.requested_by===identity?.id&&!identity?.is_master_admin} onClick={()=>void decide(r.id,false)}><XCircle size={16}/> Reject</button></div>:<span className="pill muted">Review only</span>}</td></tr>)}</tbody></table></div>:<div className="empty"><ShieldCheck size={28}/><strong>All caught up</strong><span>No pending requests currently visible.</span></div>}
    </div>
    <p className="hint" style={{marginTop:20}}>Reviewing a request changes the current record only after server-side role, scope, version and independent-review checks succeed. The configured Master Admin can decide directly.</p>
  </Shell>;
}
