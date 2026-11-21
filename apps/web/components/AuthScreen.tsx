"use client";
import {useEffect, useState, type FormEvent} from "react";
import Link from "next/link";
import {Eye, EyeOff, Network, ShieldCheck, Mail, ArrowLeft} from "lucide-react";
import {authClient} from "@/lib/supabase";
import EmailOtpSignIn from "./EmailOtpSignIn";
import "./AuthScreen.css";

export type AuthMode = "login" | "signup" | "forgot" | "reset";
const content = {
  login: ["Welcome back", "Sign in to your Uttara OMS workspace."],
  signup: ["Create your account", "Your own profile, reading and reports, in one place."],
  forgot: ["Forgot your password?", "We’ll email you a link to choose a new password."],
  reset: ["Choose a new password", "Use a strong password that you don’t use elsewhere."],
};
export default function AuthScreen({mode="login",onAuthenticated}:{mode?:AuthMode;onAuthenticated?:()=>void}) {
  const [email,setEmail]=useState(""),[password,setPassword]=useState(""),[confirm,setConfirm]=useState(""),[visible,setVisible]=useState(false),[busy,setBusy]=useState(false),[notice,setNotice]=useState(""),[issue,setIssue]=useState(""),[sent,setSent]=useState(false),[codeMode,setCodeMode]=useState(false),[code,setCode]=useState(""),[seconds,setSeconds]=useState(0),[resetReady,setResetReady]=useState(false),[resetLoading,setResetLoading]=useState(mode==="reset"),[updated,setUpdated]=useState(false);
  const emailEnabled=process.env.NEXT_PUBLIC_EMAIL_OTP_ENABLED==="true";
  useEffect(()=>{if(!seconds)return;const timer=setTimeout(()=>setSeconds(s=>s-1),1000);return()=>clearTimeout(timer);},[seconds]);
  useEffect(()=>{
    if(mode!=="reset")return;
    let active=true;
    try {
      const auth=authClient().auth;
      const {data}=auth.onAuthStateChange((event,session)=>{if(active&&event==="PASSWORD_RECOVERY"){setResetReady(!!session);setResetLoading(false);}});
      auth.getSession().then(({data,error})=>{if(!active)return;setResetReady(!error&&!!data.session);setResetLoading(false);if(error)setIssue("This reset link could not be opened. Request a new link.");}).catch(()=>{if(active){setIssue("This reset link could not be opened. Request a new link.");setResetLoading(false);}});
      return()=>{active=false;data.subscription.unsubscribe();};
    } catch {setIssue("Password recovery is unavailable. Please try again.");setResetLoading(false);}
    return()=>{active=false;};
  },[mode]);
  async function run(work:()=>Promise<void>){setBusy(true);setIssue("");setNotice("");try{await work();}catch(e){setIssue(e instanceof Error?e.message:"Please try again.");}finally{setBusy(false);}}
  async function submit(event:FormEvent){event.preventDefault();await run(async()=>{
    const auth=authClient().auth;
    if(mode==="forgot"){
      const {error}=await auth.resetPasswordForEmail(email.trim(),{redirectTo:window.location.origin+"/reset-password/"});if(error)throw error;
      setSent(true);setSeconds(60);setNotice("If this address can receive a reset email, you’ll find a link in its inbox. Check spam too. Open the link in this browser.");return;
    }
    if(mode==="signup"&&sent){
      const {error}=await auth.verifyOtp({email:email.trim(),token:code.trim(),type:"signup"});if(error)throw error;setCode("");onAuthenticated?.();return;
    }
    if(mode==="signup"||mode==="reset"){
      if(password.length<8)throw new Error("Use at least 8 characters for your password.");
      if(password!==confirm)throw new Error("The passwords don’t match. Please check them.");
    }
    if(mode==="reset"){
      if(!resetReady)throw new Error("Open a valid password-reset link from your email first.");
      const {error}=await auth.updateUser({password});if(error)throw error;
      setUpdated(true);setResetReady(false);setPassword("");setConfirm("");
      const signedOut=await auth.signOut();if(signedOut.error){setNotice("Your password was updated. Please sign out before signing in again.");return;}
      setNotice("Your password has been updated. You can now sign in with your new password.");return;
    }
    if(mode==="signup"){
      const {data,error}=await auth.signUp({email:email.trim(),password,options:{emailRedirectTo:window.location.origin}});if(error)throw error;
      setPassword("");setConfirm("");if(data.session){onAuthenticated?.();return;}
      setSent(true);setSeconds(60);setNotice("Check your email to confirm your account. Enter the verification code below. If you already have an account, sign in or reset your password.");return;
    }
    const {error}=await auth.signInWithPassword({email:email.trim(),password});if(error)throw error;setPassword("");onAuthenticated?.();
  });}
  async function google(){await run(async()=>{const {error}=await authClient().auth.signInWithOAuth({provider:"google",options:{redirectTo:window.location.origin}});if(error)throw error;});}
  async function resend(){await run(async()=>{const {error}=await authClient().auth.resend({type:"signup",email:email.trim(),options:{emailRedirectTo:window.location.origin}});if(error)throw error;setSeconds(60);setNotice("A new confirmation email has been requested. Check your inbox and spam folder.");});}
  const passwordField=(id:string,label:string,value:string,onChange:(s:string)=>void,confirmation=false)=><div className="auth-line"><label htmlFor={id}>{label}</label><div className="auth-password-input"><input id={id} type={visible?"text":"password"} autoComplete={mode==="login"?"current-password":"new-password"} required minLength={mode==="login"?undefined:8} maxLength={128} value={value} disabled={busy} onChange={e=>onChange(e.target.value)}/>{!confirmation&&<button type="button" className="auth-eye" aria-label={visible?"Hide password":"Show password"} aria-pressed={visible} onClick={()=>setVisible(!visible)}>{visible?<EyeOff size={18}/>:<Eye size={18}/>}</button>}</div></div>;
  return <div className="auth-scene"><section className="auth-panel" aria-labelledby="auth-title"><Link href="/" className="auth-home-brand"><span><Network size={25}/></span><div>Uttara <b>OMS</b><small>YOUR ORGANIZED WORKSPACE</small></div></Link><div className="auth-intro"><span className="auth-overline">{mode==="login"?"SIGN IN":mode==="signup"?"GET STARTED":"ACCOUNT RECOVERY"}</span><h1 id="auth-title">{content[mode][0]}</h1><p>{content[mode][1]}</p></div>
    {issue&&<p className="auth-message auth-error" role="alert">{issue}</p>}{notice&&<p className="auth-message" role="status">{notice}</p>}
    {resetLoading?<p role="status">Checking your reset link…</p>:mode==="reset"&&(!resetReady||updated)?<div className="auth-recovery-state">{!updated&&<p>This link has expired or no recovery session is available. Request a fresh reset link.</p>}<Link href={updated?"/login/":"/forgot-password/"} className="auth-submit">{updated?"Back to sign in":"Request a new reset link"}</Link></div>:codeMode&&mode==="login"?<><EmailOtpSignIn/><button className="auth-text-button" type="button" onClick={()=>setCodeMode(false)}>Use email and password</button></>:<form onSubmit={submit} className="auth-password-form">
      {mode!=="reset"&&<div className="auth-line"><label htmlFor="account-email">Email</label><input id="account-email" type="email" autoComplete="email" required maxLength={254} value={email} disabled={busy||(mode==="signup"&&sent)} onChange={e=>setEmail(e.target.value)}/></div>}
      {mode==="signup"&&sent?<><div className="auth-line"><label htmlFor="signup-code">Email verification code</label><input id="signup-code" required inputMode="numeric" autoComplete="one-time-code" pattern="[0-9]{6,10}" maxLength={10} value={code} disabled={busy} onChange={e=>setCode(e.target.value.replace(/\D/g,""))}/></div><button type="submit" className="auth-submit" disabled={busy}>{busy?"Verifying…":"Verify email"}</button><button className="auth-text-button" type="button" disabled={busy||seconds>0} onClick={()=>void resend()}>Resend confirmation{seconds>0?` (${seconds}s)`:""}</button><button className="auth-text-button" type="button" disabled={busy} onClick={()=>{setSent(false);setCode("");setNotice("");}}>Use a different email</button></>:<>
      {mode!=="forgot"&&passwordField("account-password",mode==="reset"?"New password":"Password",password,setPassword)}
      {(mode==="signup"||mode==="reset")&&<>{passwordField("account-confirm","Confirm password",confirm,setConfirm,true)}<p className="auth-password-hint">Use at least 8 characters.</p></>}
      {mode==="login"&&<Link href="/forgot-password/" className="auth-forgot">Forgot Password?</Link>}
      <button className="auth-submit" type="submit" disabled={busy||(mode==="forgot"&&seconds>0)}>{busy?"Please wait…":mode==="login"?"LOGIN":mode==="signup"?"CREATE ACCOUNT":mode==="forgot"?(seconds>0?`Resend in ${seconds}s`:"Send reset link"):"Save new password"}</button>
      </>}
    </form>}
    {(mode==="login"||mode==="signup")&&<><div className="auth-or"><span>OR</span></div><button className="auth-google" type="button" disabled={busy} onClick={()=>void google()}><span aria-hidden="true">G</span> Continue with Google</button>{mode==="login"&&emailEnabled&&!codeMode&&<button type="button" className="auth-code-button" onClick={()=>setCodeMode(true)}><Mail size={16}/> Sign in with an email code</button>}<p className="auth-switch">{mode==="login"?<>New User? <Link href="/signup/">Create an Account</Link></>:<>Already have an account? <Link href="/login/">Sign in</Link></>}</p></>}
    {mode==="forgot"&&<Link className="auth-back" href="/login/"><ArrowLeft size={15}/> Back to sign in</Link>}
    <div className="auth-security"><ShieldCheck size={15}/><span>Private workspace · Leaders use authenticator verification</span></div>
  </section></div>;
}
