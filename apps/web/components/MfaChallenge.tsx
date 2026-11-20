"use client";
import {useEffect,useState,type FormEvent} from "react";
import {authClient} from "@/lib/supabase";

export default function MfaChallenge(){
  const [factor,setFactor]=useState("");
  const [code,setCode]=useState("");
  const [qr,setQr]=useState("");
  const [message,setMessage]=useState("");
  const [busy,setBusy]=useState(false);
  const [loaded,setLoaded]=useState(false);
  const [unfinished,setUnfinished]=useState("");
  useEffect(()=>{let active=true;
    authClient().auth.mfa.listFactors().then(({data,error})=>{
      if(!active)return;
      if(error)setMessage(error.message);
      else {
        const verified=data.all.find(f=>f.factor_type==="totp"&&f.status==="verified");
        setFactor(verified?.id||"");
        setUnfinished(verified?"":data.all.find(f=>f.factor_type==="totp"&&f.status==="unverified")?.id||"");
      }
      setLoaded(true);
    }).catch(error=>{if(active){setMessage(String(error));setLoaded(true);}});
    return ()=>{active=false;};
  },[]);
  const resetUnfinished=async()=>{setBusy(true);setMessage("");
    try{
      const {data,error}=await authClient().auth.mfa.listFactors();
      if(error)throw error;
      const verified=data.all.find(f=>f.factor_type==="totp"&&f.status==="verified");
      if(verified){setFactor(verified.id);setUnfinished("");return;}
      const pending=data.all.find(f=>f.id===unfinished&&f.factor_type==="totp"&&f.status==="unverified");
      if(pending){const {error}=await authClient().auth.mfa.unenroll({factorId:pending.id});if(error)throw error;}
      setUnfinished("");setFactor("");setCode("");setQr("");
    }catch(error){setMessage(error instanceof Error?error.message:String(error));}finally{setBusy(false);}};
  const enroll=async()=>{setBusy(true);setMessage("");
    try{const {data,error}=await authClient().auth.mfa.enroll({factorType:"totp",friendlyName:"Uttara OMS "+Date.now()});
      if(error)throw error;
      setFactor(data.id);setUnfinished(data.id);setQr(data.totp.qr_code);
    }catch(error){setMessage(error instanceof Error?error.message:String(error));}finally{setBusy(false);}};
  const verify=async(event:FormEvent)=>{event.preventDefault();setBusy(true);setMessage("");
    try{const {error}=await authClient().auth.mfa.challengeAndVerify({factorId:factor,code});
      if(error)throw error;
      setCode("");setQr("");window.location.reload();
    }catch(error){setMessage(error instanceof Error?error.message:String(error));}finally{setBusy(false);}};
  return <section aria-label="Administrator verification"><h2>Verify your authenticator</h2>
    <p className="hint">Use your six-digit authenticator code to enter the administrator workspace.</p>
    {message&&<p role="alert" className="alert">{message}</p>}
    {loaded&&!factor&&!unfinished&&<button className="secondary-btn" disabled={busy} onClick={()=>void enroll()}>Set up authenticator</button>}
    {unfinished&&!qr&&<div><p className="hint">Your earlier setup was not verified. Its private QR code cannot be shown again. Reset the unfinished setup, then set up your authenticator again.</p><button className="secondary-btn" disabled={busy} onClick={()=>void resetUnfinished()}>Reset unfinished setup</button></div>}
    {qr&&<div><img src={qr} width={200} height={200} alt="Scan this private QR code with your authenticator"/><p className="hint">Keep this QR code private. Scan it, then verify the generated code.</p></div>}
    {factor&&<form onSubmit={verify}><label>Authenticator code<input className="input" autoComplete="one-time-code" inputMode="numeric" pattern="[0-9]{6}" maxLength={6} required value={code} onChange={e=>setCode(e.target.value)}/></label><button className="primary-btn" disabled={busy||code.length!==6}>Verify code</button></form>}
  </section>;
}
