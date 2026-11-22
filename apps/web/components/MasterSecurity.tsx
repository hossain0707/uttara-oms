'use client';
import Link from 'next/link';
import {useEffect,useState} from 'react';
import {api,type Identity} from '@/lib/api';
import MfaChallenge from './MfaChallenge';
import MasterConsole from './MasterConsole';
type Pending={id:string;user_id:string;email:string;requested_by:string;until:string|null;reason:string};
type Data={pending:Pending[]};
export default function MasterSecurity({reviewsOnly=false}:{reviewsOnly?:boolean}){
 const [me,setMe]=useState<Identity|null>(null),[data,setData]=useState<Data|null>(null),[error,setError]=useState(''),[success,setSuccess]=useState(''),[busy,setBusy]=useState(false);
 const [decision,setDecision]=useState<Pending & {approve:boolean}|null>(null);
 async function load(){const identity=await api<Identity>('/me');setMe(identity);if(identity.mfa&&!identity.is_master_admin)setData(await api<Data>('/master/security'));}
 useEffect(()=>{void load().catch(e=>setError(e instanceof Error?e.message:String(e)));},[]);
 async function decide(){if(!decision)return;setBusy(true);setError('');setSuccess('');let saved=false;try{await api(`/master/exceptions/${decision.id}/decision`,{method:'POST',body:JSON.stringify({approve:decision.approve})});saved=true;setSuccess(decision.approve?'Exception approved.':'Exception rejected.');setDecision(null);await load();}catch(e){setError(saved?'Saved, but refresh failed. Refresh before another decision.':e instanceof Error?e.message:String(e));}finally{setBusy(false);}}
 if(me&&!me.roles.some(r=>r.role==='THANA_ADMIN'))return reviewsOnly?null:<div className="alert">Master Admin access is required.</div>;
 if(me?.is_master_admin&&me.mfa)return reviewsOnly?<p className="hint">Use the <Link href="/master/">Master Admin panel</Link> for direct account, permission and security controls.</p>:<MasterConsole/>;
 return <section className="master-security">
  {error&&<div className="alert" role="alert">{error}</div>}{success&&<div className="success-msg" role="status">{success}</div>}
  {me&&!me.mfa?<div className="panel"><h2>Verify before managing security</h2><p>Security decisions require an authenticator-verified Thana Admin, even when your workspace has an exception.</p><MfaChallenge/></div>:!data?<p role="status">{error?'Unable to load security settings.':'Loading security settings…'}<button className="secondary-btn" onClick={()=>void load().catch(e=>setError(String(e)))}>Retry</button></p>:<>
   {decision&&<div className="panel security-confirm" role="dialog" aria-modal="false" aria-labelledby="security-decision-title"><h2 id="security-decision-title">{decision.approve?'Approve authenticator exception?':'Reject authenticator exception?'}</h2><p><strong>{decision.email}</strong></p><p>{decision.approve?`This account will skip the authenticator step ${decision.until?'until '+new Date(decision.until).toLocaleString():'until the exception is revoked'}. Normal sign-in and existing permissions remain unchanged.`:'The account will keep its current authenticator requirement.'}</p><div className="form-actions"><button className="secondary-btn" autoFocus disabled={busy} onClick={()=>setDecision(null)}>Cancel decision</button><button className="primary-btn" disabled={busy} onClick={()=>void decide()}>{decision.approve?'Confirm approval':'Confirm rejection'}</button></div></div>}
   <div className="panel"><h2>Pending security approvals</h2><p>Ordinary administrators retain independent review. The requester and recipient cannot approve their own request. The configured Master Admin can act directly.</p><button className="secondary-btn" disabled={busy} onClick={()=>void load().catch(e=>setError(String(e)))}>Refresh security</button>{!data.pending.length?<p className="hint">No security exceptions awaiting review.</p>:<div className="table-wrap"><table className="data-table"><thead><tr><th>Account</th><th>Duration</th><th>Reason</th><th>Decision</th></tr></thead><tbody>{data.pending.map(r=><tr key={r.id}><td>{r.email}</td><td>{r.until?new Date(r.until).toLocaleString():'Until revoked'}</td><td>{r.reason}</td><td><button disabled={busy||r.requested_by===me?.id||r.user_id===me?.id} onClick={()=>setDecision({...r,approve:true})}>Approve</button> <button disabled={busy} onClick={()=>setDecision({...r,approve:false})}>Reject</button>{(r.requested_by===me?.id||r.user_id===me?.id)&&<small>Independent reviewer required</small>}</td></tr>)}</tbody></table></div>}</div>
  </>}
 </section>;
}
