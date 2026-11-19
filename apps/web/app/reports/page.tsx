"use client";
import {useEffect,useState} from "react";
import {FileSpreadsheet,FileText,ShieldCheck,Download,Activity} from "lucide-react";
import Shell from "@/components/Shell";
import {api,downloadReport,type Dashboard,type Identity} from "@/lib/api";

export default function ReportPage(){
  const [stats,setStats]=useState<Dashboard|null>(null);const [admin,setAdmin]=useState(false);const [notice,setNotice]=useState("");const [busy,setBusy]=useState(false);
  useEffect(()=>{Promise.all([api<Dashboard>("/reports/dashboard"),api<Identity>("/me")]).then(([s,i])=>{setStats(s);setAdmin(i.roles.some(r=>r.role==="THANA_ADMIN"));}).catch(e=>setNotice(String(e)));},[]);
  const download=async(type:"xlsx"|"pdf",personal=false)=>{setBusy(true);setNotice("");try{await downloadReport(type,personal);setNotice("Report downloaded. Handle the file as confidential.");}catch(e){setNotice(String(e));}finally{setBusy(false);}};
  return <Shell title="Reports & exports" subtitle="Permission-scoped reporting, monthly movement and audited document downloads.">
    {notice&&<div className="alert" role="status">{notice}</div>}
    <div className="cards" style={{gridTemplateColumns:"repeat(3,minmax(0,1fr))"}}><div className="stat-card"><div className="stat-label">Active total<ShieldCheck size={18}/></div><div className="stat-number">{stats?.total_active??"—"}</div></div><div className="stat-card"><div className="stat-label">Increases<Activity size={18}/></div><div className="stat-number">{stats?.this_month.increase??"—"}</div></div><div className="stat-card"><div className="stat-label">Decreases<Activity size={18}/></div><div className="stat-number">{stats?.this_month.decrease??"—"}</div></div></div>
    <div className="grid-of-cards">
      <div className="panel"><FileSpreadsheet size={27} color="#24815B"/><h2 style={{marginTop:18}}>Excel report</h2><p className="subhead">Organizational totals, unit counts, and month-to-date movement.</p><button className="primary-btn" style={{marginTop:20}} disabled={busy} onClick={()=>void download("xlsx")}><Download size={15}/> Download .xlsx</button></div>
      <div className="panel"><FileText size={27} color="#24815B"/><h2 style={{marginTop:18}}>PDF summary</h2><p className="subhead">A formatted, aggregate-only PDF for internal review.</p><button className="secondary-btn" style={{marginTop:20}} disabled={busy} onClick={()=>void download("pdf")}><Download size={15}/> Download .pdf</button></div>
      <div className="panel"><ShieldCheck size={27} color="#24815B"/><h2 style={{marginTop:18}}>Restricted personal export</h2><p className="subhead">Includes personal identifiers. Thana Admin only; every export creates an audit event.</p>{admin?<button className="secondary-btn" style={{marginTop:20}} disabled={busy} onClick={()=>{if(window.confirm("Export sensitive personal data? Ensure a legitimate purpose and secure storage."))void download("xlsx",true);}}>Export restricted .xlsx</button>:<p className="pill muted" style={{display:"inline-block",marginTop:20}}>Admin-only feature</p>}</div>
    </div>
    <p className="hint" style={{marginTop:22}}>Do not share exports through public links or messaging groups. Current-month events are determined from the audit/event ledger; historical point-in-time reconstruction requires expanded accounting before use in official reconciliations.</p>
  </Shell>;
}
