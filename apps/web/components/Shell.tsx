"use client";
import { useEffect, useState, type ReactNode } from "react";
import { usePathname } from "next/navigation";
import Link from "next/link";
import { LayoutDashboard, Users, GitBranch, ShieldCheck, FileBarChart2, LogOut, Menu, Network, ShieldAlert, UserCog } from "lucide-react";
import { api, type Identity } from "@/lib/api";
import { authClient } from "@/lib/supabase";

const items = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/members", label: "People & records", icon: Users },
  { href: "/organization", label: "Organization", icon: GitBranch },
  { href: "/approvals", label: "Approvals", icon: ShieldCheck },
  { href: "/reports", label: "Reports", icon: FileBarChart2 },
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
    let unsubscribe: (() => void) | undefined;
    try {
      const auth = authClient();
      const check = async (signedIn: boolean) => {
        if (!active) return;
        setSession(signedIn);
        setIdentity(null);
        if (signedIn) {
          try { const me = await api<Identity>("/me"); if (active) {setIdentity(me); setIssue("");} }
          catch (err) {if (active) setIssue(err instanceof Error ? err.message : "Access denied");}
        }
        if (active) setPending(false);
      };
      auth.auth.getSession().then(({data}) => check(!!data.session)).catch(err => {setIssue(String(err)); setPending(false);});
      const {data} = auth.auth.onAuthStateChange((event, current) => {
        if (event === "SIGNED_IN" || event === "SIGNED_OUT") void check(!!current);
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
    <h1>{session ? "Access needs approval" : "Organized. Secure. Connected."}</h1>
    <p>{session ? "Your Google identity is signed in, but it is not approved for this workspace. Contact your authorized administrator." : "A private organizational management workspace. Only explicitly approved accounts can view records."}</p>
    {issue && <div className="alert"><ShieldAlert size={17}/>{issue}</div>}
    <button className="primary-btn wide" onClick={session ? signOut : signIn}>{session ? "Sign out" : "Continue with Google"}</button>
    <span className="quiet">Sensitive information · Authorized access only</span>
  </div></div>;
  return <div className="app-shell">
    <aside className={"sidebar " + (mobile ? "sidebar-open" : "")}>
      <Link className="sidebar-brand" href="/"><span className="brand-icon"><Network size={24}/></span><span>Uttara <b>OMS</b><small>MANAGEMENT SYSTEM</small></span></Link>
      <div className="nav-caption">WORKSPACE</div>
      <nav>{items.filter(item => item.href!=="/access" || identity.roles.some(r=>r.role==="THANA_ADMIN")).map(({href,label,icon:Icon}) => <Link onClick={()=>setMobile(false)} key={href} className={"nav-link " + (path === href ? "active" : "")} href={href}><Icon size={19}/>{label}</Link>)}</nav>
      <div className="sidebar-foot"><div className="sidebar-lock"><ShieldCheck size={17}/> Private workspace</div><div className="account-name">{identity.email}</div><button className="logout-btn" onClick={signOut}><LogOut size={16}/> Sign out</button></div>
    </aside>
    {mobile && <button className="nav-backdrop" aria-label="Close navigation" onClick={()=>setMobile(false)}/>}
    <div className="main-area"><header className="topbar"><button className="mobile-menu" aria-label="Open navigation" onClick={()=>setMobile(!mobile)}><Menu size={22}/></button><div className="breadcrumb">Uttara OMS <span>/</span> {title}</div><span className="secure-chip"><ShieldCheck size={14}/> Secure workspace</span></header>
      <main className="content"><div className="page-header"><div><p className="eyebrow">ORGANIZATIONAL INTELLIGENCE</p><h1>{title}</h1><p>{subtitle}</p></div></div>{children}</main>
      <footer className="footer">Uttara OMS · Confidential internal system · © {new Date().getFullYear()}</footer>
    </div>
  </div>;
}
