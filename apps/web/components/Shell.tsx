"use client";
import { useEffect, useState, type ReactNode } from "react";
import { usePathname } from "next/navigation";
import Link from "next/link";
import { LayoutDashboard, Users, GitBranch, ShieldCheck, FileBarChart2, LogOut, Menu, Network, ShieldAlert, UserCog } from "lucide-react";
import { api, type Identity } from "@/lib/api";
import MfaChallenge from "./MfaChallenge";
import EmailOtpSignIn from "./EmailOtpSignIn";
import PersonalWorkspace from "./PersonalWorkspace";
import { authClient } from "@/lib/supabase";

const items = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/members", label: "People & records", icon: Users },
  { href: "/organization", label: "Organization", icon: GitBranch },
  { href: "/approvals", label: "Approvals", icon: ShieldCheck },
  { href: "/reports", label: "Reports", icon: FileBarChart2 },
  { href: "/my", label: "My workspace", icon: Users },
  { href: "/reviews", label: "Personal report reviews", icon: ShieldCheck },
  { href: "/access", label: "Access control", icon: UserCog },
];

export default function Shell({ title, subtitle, children }: {title: string; subtitle: string; children: ReactNode}) {
  const path = usePathname();
  const [session, setSession] = useState(false);
  const [identity, setIdentity] = useState<Identity | null>(null);
  const [pending, setPending] = useState(true);
  const [issue, setIssue] = useState("");
  const [mobile, setMobile] = useState(false);
  useEffect(() => {
    let active = true;
    let generation = 0;
    let unsubscribe: (() => void) | undefined;
    try {
      const auth = authClient();
      const check = async (signedIn: boolean) => {
        if (!active) return;
        const requestGeneration = ++generation;
        setPending(true);
        setSession(signedIn);
        setIdentity(null);
        if (signedIn) {
          try {
            let me: Identity;
            try {me=await api<Identity>("/me");}
            catch (error) {
              if (!(error instanceof Error)||error.message!=="Account has not been approved for OMS") throw error;
              await api("/account/register", {method:"POST"});
              me=await api<Identity>("/me");
            }
            if (active && requestGeneration === generation) {setIdentity(me); setIssue("");}
          }
          catch (err) {if (active && requestGeneration === generation) setIssue(err instanceof Error ? err.message : "Access denied");}
        }
        if (active && requestGeneration === generation) setPending(false);
      };
      auth.auth.getSession().then(({data}) => check(!!data.session)).catch(err => {setIssue(String(err)); setPending(false);});
      const {data} = auth.auth.onAuthStateChange((event, current) => {
        if (["SIGNED_IN", "SIGNED_OUT", "MFA_CHALLENGE_VERIFIED", "TOKEN_REFRESHED"].includes(event)) {
          // Defer calls to auth.getSession until the auth-state callback releases its lock.
          setTimeout(() => {void check(!!current);}, 0);
        }
      });
      unsubscribe = () => data.subscription.unsubscribe();
    } catch (err) { setIssue(String(err)); setPending(false); }
    return () => {active = false; unsubscribe?.();};
  }, []);
  const signIn = async () => {
    try {
      setIssue("");
      const {error} = await authClient().auth.signInWithOAuth({
        provider: "google",
        options: {redirectTo: window.location.origin},
      });
      if (error) setIssue(error.message);
    } catch (err) {setIssue(String(err));}
  };
  const signOut = async () => {await authClient().auth.signOut(); setIdentity(null); setSession(false);};
  if (pending) return <div className="center-screen"><div className="loading-logo"><Network size={30}/></div><p>Verifying secure session…</p></div>;
  if (!identity) return <div className="center-screen"><div className="auth-card">
    <div className="auth-brand"><span className="brand-icon"><Network size={25}/></span><span>Uttara <b>OMS</b></span></div>
    <h1>{session ? (issue==="Administrator MFA required"?"Leader verification":"Access needs approval") : "Organized. Secure. Connected."}</h1>
    <p>{session ? (issue==="Administrator MFA required"?"Your account is signed in. Complete authenticator verification to continue.":"Your account could not be opened. Check the message below or contact your administrator.") : "Use an email code to sign up or sign in. You can manage your own profile and reports. Leaders also complete authenticator verification."}</p>
    {issue && <div className="alert"><ShieldAlert size={17}/>{issue}</div>}
    {session&&issue==="Administrator MFA required"&&<MfaChallenge/>}
    {!session&&<EmailOtpSignIn/>}
    <button className="primary-btn wide" onClick={session ? signOut : signIn}>{session ? "Sign out" : "Continue with Google"}</button>
    <span className="quiet">Sensitive information · Authorized access only</span>
  </div></div>;
  if (identity.roles.length===0) return <div className="personal-shell"><header className="personal-header"><strong>Uttara OMS · My workspace</strong><span>{identity.email}</span><button onClick={()=>void signOut()}>Sign out</button></header><main className="content"><PersonalWorkspace/></main></div>;
  return <div className="app-shell">
    <aside className={"sidebar " + (mobile ? "sidebar-open" : "")}>
      <Link className="sidebar-brand" href="/"><span className="brand-icon"><Network size={24}/></span><span>Uttara <b>OMS</b><small>MANAGEMENT SYSTEM</small></span></Link>
      <div className="nav-caption">WORKSPACE</div>
      <nav>{items.filter(item => (item.href!=="/access" || identity.roles.some(r=>r.role==="THANA_ADMIN")) && (!["/members","/approvals"].includes(item.href) || identity.roles.some(r=>["THANA_ADMIN","WARD_ADMIN","UNIT_EDITOR"].includes(r.role)))).map(({href,label,icon:Icon}) => <Link onClick={()=>setMobile(false)} key={href} className={"nav-link " + (path === href ? "active" : "")} href={href}><Icon size={19}/>{label}</Link>)}</nav>
      <div className="sidebar-foot"><div className="sidebar-lock"><ShieldCheck size={17}/> Private workspace</div><div className="account-name">{identity.email}</div><button className="logout-btn" onClick={signOut}><LogOut size={16}/> Sign out</button></div>
    </aside>
    {mobile && <button className="nav-backdrop" aria-label="Close navigation" onClick={()=>setMobile(false)}/>}
    <div className="main-area"><header className="topbar"><button className="mobile-menu" aria-label="Open navigation" onClick={()=>setMobile(!mobile)}><Menu size={22}/></button><div className="breadcrumb">Uttara OMS <span>/</span> {title}</div><span className="secure-chip"><ShieldCheck size={14}/> Secure workspace</span></header>
      <main className="content"><div className="page-header"><div><p className="eyebrow">ORGANIZATIONAL INTELLIGENCE</p><h1>{title}</h1><p>{subtitle}</p></div></div>{children}</main>
      <footer className="footer">Uttara OMS · Confidential internal system · © {new Date().getFullYear()}</footer>
    </div>
  </div>;
}
