'use client';
import Link from 'next/link';
import {useEffect,useState} from 'react';
import {api,type Identity,type Category} from '@/lib/api';
export type RegisteredSummary={active_accounts:number;total_profiles:number;by_category:Record<Category|'UNSPECIFIED',number>;linked_profiles:number;awaiting_confirmation:number;profiles_missing:number;active_units:number;global_scope:boolean;generated_at:string};
const categories:[Category|'UNSPECIFIED',string][]=[['RUKON','Rukon'],['WORKER','Worker'],['ASSOCIATE','Associate'],['SUPPORTER','Supporter'],['UNSPECIFIED','Not specified']];
export default function RegisteredOverview(){
 const [data,setData]=useState<RegisteredSummary|null>(null),[me,setMe]=useState<Identity|null>(null),[error,setError]=useState(''),[loading,setLoading]=useState(true);
 async function load(){setLoading(true);setError('');try{const [summary,identity]=await Promise.all([api<RegisteredSummary>('/reports/registered-summary'),api<Identity>('/me')]);setData(summary);setMe(identity);}catch(e){setData(null);setError(e instanceof Error?e.message:String(e));}finally{setLoading(false);}}
 useEffect(()=>{void load();},[]);
 return <section className="panel registered-overview" aria-label="Registered people summary"><div className="section-title"><div><h2>Registered people</h2><p className="subhead">Current saved profiles · self-reported categories · separate from official membership</p></div><button className="secondary-btn" disabled={loading} onClick={()=>void load()}>Refresh profile totals</button></div>
 {error&&<p className="alert" role="alert">Unable to load registered profiles: {error}</p>}
 <div className="registration-totals"><div><strong>{data?data.active_accounts.toLocaleString():'—'}</strong><span>Active registered accounts</span></div><div><strong>{data?data.total_profiles.toLocaleString():'—'}</strong><span>Saved profiles</span></div><div><strong>{data?data.profiles_missing.toLocaleString():'—'}</strong><span>Profile not completed</span></div></div>
 <div className="registered-categories">{categories.map(([key,label])=><article key={key}><span>{label}</span><strong>{data?(data.by_category[key]||0).toLocaleString():'—'}</strong><small>Self-reported</small></article>)}</div>
 {data&&<><div className="confirmation-summary"><div><h3>Awaiting confirmation: {data.awaiting_confirmation}</h3><p>{data.linked_profiles} saved profile(s) linked to official records. Registered and official totals overlap and must not be added together.</p></div>{me?.is_master_admin&&<Link className="primary-btn" href="/master/#membership-confirmation">Review awaiting profiles</Link>}</div>{data.active_units===0&&<div className="registration-notice"><strong>No active units configured</strong><p>An active unit is required before creating an official member. Registered profiles remain visible here while setup is pending.</p>{me?.roles.some(r=>r.role==='THANA_ADMIN')&&<Link className="secondary-btn" href="/organization/">Set up units</Link>}</div>}<p className="hint">{data.global_scope?'Current active accounts across the Thana.':'Only accounts linked to official records within your approved scope are included; self-requested units do not grant visibility.'} Date filters below affect official membership only. These figures are a current snapshot.</p></>}
 </section>;
}
