"use client";
import {useCallback, useEffect, useState, type FormEvent} from "react";
import {Plus, Search, RefreshCcw, UserRoundPlus, Save, ShieldCheck} from "lucide-react";
import SearchSelect from '@/components/SearchSelect';
import AddressFields from '@/components/AddressFields';
import catalogs from '@/data/catalogs.json';
import Shell from "@/components/Shell";
import {api, type Category, type Member, type OrgNode} from "@/lib/api";

type NewProfile = {member_number:string;full_name:string;father_name:string;phone:string;address:string;occupation:string;position:string;category:Category;org_node_id:string;joined_on:string};
const blank:NewProfile={member_number:"",full_name:"",father_name:"",phone:"",address:"",occupation:"",position:"",category:"SUPPORTER",org_node_id:"",joined_on:""};
type HistoryItem={id:string;action:string;before:string|null;after:string|null;actor_id:string;created_at:string};
const labels:Record<Category,string>={RUKON:"Rukon · রুকন",WORKER:"Worker · কর্মী",ASSOCIATE:"Associate · সহযোগী",SUPPORTER:"Supporter · সমর্থক"};

export default function PeoplePage(){
  const [members,setMembers]=useState<Member[]>([]);
  const [total,setTotal]=useState(0);
  const [offset,setOffset]=useState(0);
  const [status,setStatus]=useState("");
  const [units,setUnits]=useState<OrgNode[]>([]);
  const [search,setSearch]=useState("");
  const [category,setCategory]=useState("");
  const [showCreate,setShowCreate]=useState(false);
  const [profile,setProfile]=useState<NewProfile>(blank);
  const [consented,setConsented]=useState(false);
  const [editing,setEditing]=useState<Member|null>(null);
  const [history,setHistory]=useState<HistoryItem[]>([]);
  const [routine,setRoutine]=useState({full_name:"",father_name:"",phone:"",address:"",occupation:"",position:""});
  const [changeKind,setChangeKind]=useState("CATEGORY");
  const [changeValue,setChangeValue]=useState("WORKER");
  const [notice,setNotice]=useState("");
  const [busy,setBusy]=useState(false);
  const load=useCallback(async()=>{try{
    const query = new URLSearchParams({limit:"30",offset:String(offset)});if(search.trim())query.set("q",search.trim());if(category)query.set("category",category);if(status)query.set("status",status);
    const [people,org]=await Promise.all([api<{items:Member[];total:number}>("/members?"+query),api<{items:OrgNode[]}>("/organization/nodes")]);
    setMembers(people.items);setTotal(people.total);setUnits(org.items.filter(n=>n.kind==="UNIT" && n.active));
  }catch(err){setNotice(err instanceof Error?err.message:String(err));}},[search,category,offset,status]);
  useEffect(()=>{void load();},[load]);
  const setField=(key:keyof NewProfile,value:string)=>setProfile(prev=>({...prev,[key]:value}));
  const create=async(e:FormEvent)=>{e.preventDefault();setBusy(true);setNotice("");
    try{
      await api<Member>("/members",{method:"POST",body:JSON.stringify({...profile,joined_on:profile.joined_on||null,consent_attested:consented,consent_version:"v1"})});
      setProfile(blank);setConsented(false);setShowCreate(false);setNotice("Profile saved securely.");await load();
    }catch(err){setNotice(err instanceof Error?err.message:String(err));}finally{setBusy(false);}
  };
  const choose=(m:Member)=>{setEditing(m);setHistory([]);void api<{items:HistoryItem[]}>("/members/"+m.id+"/history").then(data=>setHistory(data.items)).catch(err=>setNotice(String(err)));setRoutine({full_name:m.full_name,father_name:m.father_name||"",phone:m.phone||"",address:m.address||"",occupation:m.occupation||"",position:m.position||""});setChangeKind("CATEGORY");setChangeValue(m.category==="WORKER"?"RUKON":"WORKER");};
  const saveRoutine=async(e:FormEvent)=>{e.preventDefault();if(!editing)return;setBusy(true);setNotice("");
    try{await api("/members/"+editing.id,{method:"PATCH",body:JSON.stringify({...routine,expected_version:editing.version})});setEditing(null);setNotice("Routine changes saved.");await load();}
    catch(err){setNotice(err instanceof Error?err.message:String(err));}finally{setBusy(false);}
  };
  const propose=async(e:FormEvent)=>{e.preventDefault();if(!editing)return;setBusy(true);setNotice("");
    const proposed_value = changeKind==="DEACTIVATE"?"INACTIVE":changeKind==="REACTIVATE"?"ACTIVE":changeValue;
    try{await api("/approvals/members/"+editing.id,{method:"POST",body:JSON.stringify({kind:changeKind,proposed_value})});setNotice("Change submitted for independent approval.");setEditing(null);}
    catch(err){setNotice(err instanceof Error?err.message:String(err));}finally{setBusy(false);}
  };
  return <Shell title="People & records" subtitle="Manage authorized people profiles, searchable records, and important change requests.">
    {notice&&<div className={notice.includes("saved")||notice.includes("submitted")?"success-msg":"alert"} role="status">{notice}</div>}
    <div className="toolbar"><input className="input search-field" value={search} aria-label="Search people" onChange={e=>{setSearch(e.target.value);setOffset(0);}} placeholder="Search name, member ID or full mobile number"/><select className="select" value={category} aria-label="Filter category" onChange={e=>{setCategory(e.target.value);setOffset(0);}}><option value="">All categories</option>{Object.entries(labels).map(([k,v])=><option key={k} value={k}>{v}</option>)}</select><select aria-label="Filter status" className="select" value={status} onChange={e=>{setStatus(e.target.value);setOffset(0);}}><option value="">All statuses</option><option value="ACTIVE">Active</option><option value="INACTIVE">Inactive</option></select><button className="secondary-btn" onClick={()=>void load()}><RefreshCcw size={15}/> Refresh</button><div className="grow"/><button className="primary-btn" onClick={()=>{setShowCreate(!showCreate);setEditing(null);}}><Plus size={16}/> Add person</button></div>
    {showCreate&&<div className="panel" style={{marginBottom:20}}><div className="section-title"><h2>New person profile</h2><button className="secondary-btn" onClick={()=>setShowCreate(false)}>Close</button></div>
      <form onSubmit={create}><div className="form-grid">
        {([["member_number","Member ID"],["full_name","Full name"],["father_name","Father's name"],["phone","Mobile number"],["occupation","Occupation"],["position","Position / responsibility"],["address","Address"],["joined_on","Joined on"]] as [keyof NewProfile,string][]).map(([key,label])=>key==='occupation'||key==='position'?<SearchSelect key={key} label={label} value={profile[key]} maxLength={160} items={key==='occupation'?catalogs.occupations:catalogs.positions} onChange={v=>setField(key,v)}/>:key==='address'?<AddressFields key={key} label={label} value={profile.address} onChange={v=>setField('address',v)}/>:<div className="form-field" key={key}><label htmlFor={key}>{label}</label><input id={key} type={key==="joined_on"?"date":"text"} className="input" value={profile[key]} onChange={e=>setField(key,e.target.value)} required={key==="member_number"||key==="full_name"}/></div>)}
        <div className="form-field"><label>Organizational category</label><select className="select" value={profile.category} onChange={e=>setField("category",e.target.value)}>{Object.entries(labels).map(([k,v])=><option value={k} key={k}>{v}</option>)}</select></div>
        <div className="form-field"><label>Assigned unit</label><select required className="select" value={profile.org_node_id} onChange={e=>setField("org_node_id",e.target.value)}><option value="">Select unit</option>{units.map(n=><option value={n.id} key={n.id}>{n.name} ({n.code})</option>)}</select></div>
        <div className="form-field full"><label className="checkbox-row"><input type="checkbox" checked={consented} onChange={e=>setConsented(e.target.checked)} required/>I confirm that the person was informed about the purpose of processing their sensitive organizational information and gave valid consent under the approved privacy notice (v1). No record should be entered without this basis.</label></div>
      </div><div className="form-actions"><button className="secondary-btn" type="button" onClick={()=>setShowCreate(false)}>Cancel</button><button className="primary-btn" disabled={busy||!consented||!profile.org_node_id}><UserRoundPlus size={16}/> Save profile</button></div></form></div>}
    <div className="panel" style={{padding:0,overflow:"hidden"}}><div style={{padding:"23px 24px 13px"}}><h2>People directory</h2><span className="subhead">{total} matching records within your approved scope</span></div>
      {members.length?<div className="table-wrap"><table className="data-table"><thead><tr><th>Member ID</th><th>Name</th><th>Category</th><th>Mobile</th><th>Status</th><th>Actions</th></tr></thead><tbody>{members.map(m=><tr key={m.id}><td>{m.member_number}</td><td><b>{m.full_name}</b></td><td>{labels[m.category]}</td><td>{m.phone||"—"}</td><td><span className={"pill "+(m.status==="ACTIVE"?"":"muted")}>{m.status}</span></td><td><button onClick={()=>{choose(m);setShowCreate(false);}}>Open / edit</button></td></tr>)}</tbody></table></div>:<div className="empty"><Search size={28}/><strong>No matching records</strong><span>Records will appear when authorized data is added.</span></div>}
    </div>
    <div className="toolbar" style={{marginTop:16}}><button className="secondary-btn" disabled={offset===0} onClick={()=>setOffset(Math.max(0,offset-30))}>Previous</button><span role="status">{total?`${offset+1}–${Math.min(offset+30,total)} of ${total}`:"0 records"}</span><button className="secondary-btn" disabled={offset+30>=total} onClick={()=>setOffset(offset+30)}>Next</button></div>
    {editing&&<div className="panel" style={{marginTop:20}}><div className="section-title"><h2>Edit: {editing.full_name}</h2><button className="secondary-btn" onClick={()=>setEditing(null)}>Close</button></div>
      <p className="subhead">Routine fields can be updated directly. Category, transfer and status changes require independent approval.</p>
      <form onSubmit={saveRoutine}><div className="form-grid">{([["full_name","Full name"],["father_name","Father's name"],["phone","Mobile"],["address","Address"],["occupation","Occupation"],["position","Position"]] as const).map(([key,label])=>key==='occupation'||key==='position'?<SearchSelect key={key} label={label} value={routine[key]} maxLength={160} items={key==='occupation'?catalogs.occupations:catalogs.positions} onChange={v=>setRoutine(p=>({...p,[key]:v}))}/>:key==='address'?<AddressFields key={key} label={label} value={routine.address} onChange={v=>setRoutine(p=>({...p,address:v}))}/>:<div className="form-field" key={key}><label>{label}</label><input required={key==="full_name"} className="input" value={routine[key]} onChange={e=>setRoutine(p=>({...p,[key]:e.target.value}))}/></div>)}</div><div className="form-actions"><button className="primary-btn" disabled={busy}><Save size={15}/> Save routine details</button></div></form>
      <hr className="subtle-divider"/><h2><ShieldCheck size={17} color="#2C8264"/> Sensitive change request</h2>
      <form onSubmit={propose}><div className="form-grid"><div className="form-field"><label>Change type</label><select className="select" value={changeKind} onChange={e=>{setChangeKind(e.target.value);setChangeValue(e.target.value==="TRANSFER"?"":e.target.value==="CATEGORY"?"WORKER":"");}}><option value="CATEGORY">Change category</option><option value="TRANSFER">Transfer unit</option><option value="DEACTIVATE">Deactivate</option><option value="REACTIVATE">Reactivate</option></select></div>
        {changeKind==="CATEGORY"?<div className="form-field"><label>New category</label><select className="select" value={changeValue} onChange={e=>setChangeValue(e.target.value)}>{Object.entries(labels).map(([key,label])=><option value={key} key={key}>{label}</option>)}</select></div>:changeKind==="TRANSFER"?<div className="form-field"><label>Destination unit</label><select className="select" required value={changeValue} onChange={e=>setChangeValue(e.target.value)}><option value="">Choose a unit</option>{units.filter(n=>n.id!==editing.org_node_id).map(n=><option key={n.id} value={n.id}>{n.name}</option>)}</select></div>:<p className="hint">This change will not take effect until a separate, authorized officer approves it.</p>}
      </div><div className="form-actions"><button disabled={busy||(changeKind==="TRANSFER"&&!changeValue)} className="secondary-btn"><ShieldCheck size={15}/> Submit for approval</button></div></form>
      <hr className="subtle-divider"/>
      <h2>Record activity history</h2>
      <p className="subhead">Most recent organizational transitions and routine edits, with actor and timestamp.</p>
      {history.length ? <div className="table-wrap"><table className="data-table"><thead><tr><th>Date</th><th>Action</th><th>Previous</th><th>Updated</th><th>Recorded by</th></tr></thead><tbody>{history.map(entry=><tr key={entry.id}><td>{new Date(entry.created_at).toLocaleString()}</td><td>{entry.action.replaceAll("_"," ")}</td><td>{entry.before||"—"}</td><td>{entry.after||"—"}</td><td>{entry.actor_id.slice(0,8)}…</td></tr>)}</tbody></table></div> : <p className="hint">No additional history entries are available.</p>}
    </div>}
  </Shell>;
}
