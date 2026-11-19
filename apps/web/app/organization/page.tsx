"use client";
import {useEffect,useState,type FormEvent} from "react";
import {GitBranch,Plus,Landmark,Layers3,Boxes} from "lucide-react";
import Shell from "@/components/Shell";
import {api,type OrgNode,type Identity} from "@/lib/api";

export default function OrgPage(){
  const [editing,setEditing]=useState<OrgNode|null>(null);const [editName,setEditName]=useState("");const [editActive,setEditActive]=useState(true);const [busy,setBusy]=useState(false);
  const [nodes,setNodes]=useState<OrgNode[]>([]);const [admin,setAdmin]=useState(false);
  const [kind,setKind]=useState<"THANA"|"WARD"|"UNIT">("UNIT");const [parent,setParent]=useState("");
  const [code,setCode]=useState("");const [name,setName]=useState("");const [notice,setNotice]=useState("");
  const load=async()=>{try{const [n,me]=await Promise.all([api<{items:OrgNode[]}>("/organization/nodes"),api<Identity>("/me")]);setNodes(n.items);setAdmin(me.roles.some(r=>r.role==="THANA_ADMIN"));}catch(e){setNotice(String(e));}};
  useEffect(()=>{void load();},[]);
  const root=nodes.filter(n=>n.kind==="THANA");const wards=nodes.filter(n=>n.kind==="WARD");
  const submit=async(e:FormEvent)=>{e.preventDefault();try{
    await api("/organization/nodes",{method:"POST",body:JSON.stringify({kind,name,code,parent_id:kind==="THANA"?null:parent||null})});
    setNotice("Organizational node added.");setCode("");setName("");setParent("");await load();
  }catch(err){setNotice(err instanceof Error?err.message:String(err));}};
  const save=async(e:FormEvent)=>{e.preventDefault();if(!editing)return;setBusy(true);setNotice("");
    try{await api("/organization/nodes/"+editing.id,{method:"PATCH",body:JSON.stringify({name:editName,active:editActive})});setEditing(null);setNotice("Organization updated; historical records preserved.");await load();}
    catch(err){setNotice(err instanceof Error?err.message:String(err));}finally{setBusy(false);}};
  return <Shell title="Organization" subtitle="A configurable Thana → Ward → Unit hierarchy with scope-based visibility.">
    {notice&&<div role="status" className="alert">{notice}</div>}
    {admin&&<div className="panel" style={{marginBottom:20}}><div className="section-title"><h2><Plus size={17}/> Add organizational node</h2><span className="subhead">Thana administrator only</span></div><form onSubmit={submit}><div className="form-grid">
      <div className="form-field"><label>Node type</label><select className="select" value={kind} onChange={e=>{setKind(e.target.value as typeof kind);setParent("");}}><option value="THANA">Thana</option><option value="WARD">Ward</option><option value="UNIT">Unit</option></select></div>
      <div className="form-field"><label>Parent</label><select className="select" disabled={kind==="THANA"} required={kind!=="THANA"} value={parent} onChange={e=>setParent(e.target.value)}><option value="">Select parent</option>{(kind==="WARD"?root:kind==="UNIT"?wards:[]).filter(n=>n.active).map(n=><option value={n.id} key={n.id}>{n.name}</option>)}</select></div>
      <div className="form-field"><label>Code</label><input required className="input" value={code} onChange={e=>setCode(e.target.value)} placeholder="e.g. unit-01"/></div>
      <div className="form-field"><label>Name</label><input required className="input" value={name} onChange={e=>setName(e.target.value)} placeholder="e.g. Unit 01"/></div></div>
      <div className="form-actions"><button className="primary-btn"><Plus size={15}/> Create node</button></div></form></div>}
    {editing&&admin&&<div className="panel" style={{marginBottom:20}}><h2>Edit {editing.code}</h2><form onSubmit={save}><label>Name<input className="input" required minLength={2} maxLength={160} value={editName} onChange={e=>setEditName(e.target.value)}/></label><label className="checkbox-row"><input type="checkbox" checked={editActive} onChange={e=>setEditActive(e.target.checked)}/>Active</label><p className="hint">Deactivate children and relocate active people before disabling a node. Activate parents before children.</p><div className="form-actions"><button type="button" className="secondary-btn" onClick={()=>setEditing(null)}>Cancel</button><button className="primary-btn" disabled={busy}>Save organization</button></div></form></div>}
    <div className="panel"><div className="panel-head"><div><h2>Organizational structure</h2><span className="subhead">{nodes.length} authorized nodes currently visible</span></div><GitBranch color="#338A66"/></div>
      <div className="grid-of-cards">{nodes.map(n=>{const Icon=n.kind==="THANA"?Landmark:n.kind==="WARD"?Layers3:Boxes;return <article className="org-card" key={n.id}>
        <Icon size={22} color="#268561"/><div className="org-tag">{n.kind}</div><h3>{n.name}</h3>
        <div className="org-meta">Code: {n.code}</div><div className="org-meta" style={{marginTop:7}}>{n.active?"Active":"Inactive"}</div>
        {admin&&<button className="secondary-btn" onClick={()=>{setEditing(n);setEditName(n.name);setEditActive(n.active);}}>Edit / change status</button>}
      </article>})}</div>
      {!nodes.length&&<div className="empty"><GitBranch size={27}/><strong>No organizational nodes visible</strong><span>An administrator can initialize the structure.</span></div>}
    </div>
  </Shell>;
}
