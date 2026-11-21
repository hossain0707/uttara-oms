"use client";
import { useEffect, useState, type FormEvent } from "react";
import {
  UserCog,
  ShieldCheck,
  Plus,
  CheckCircle2,
  XCircle,
} from "lucide-react";
import { authClient } from "@/lib/supabase";
import MasterSecurity from "@/components/MasterSecurity";
import PersonalAssignments from "@/components/PersonalAssignments";
import Shell from "@/components/Shell";
import { api, type OrgNode, type Identity } from "@/lib/api";

type Request = {
  id: string;
  auth_sub: string;
  email: string;
  role: string;
  scope_node_id: string | null;
  operation: string;
  status: string;
  requested_by: string;
  requested_at: string;
  reviewed_at: string | null;
};
type User = {
  is_master_admin?: boolean;
  id: string;
  auth_sub: string;
  email: string;
  active: boolean;
  roles: { role: string; scope_node_id: string | null }[];
};
const roles = [
  "THANA_ADMIN",
  "THANA_VIEWER",
  "WARD_ADMIN",
  "UNIT_EDITOR",
] as const;
export default function AccessPage() {
  const [identity, setIdentity] = useState<Identity | null>(null);
  const [requests, setRequests] = useState<Request[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [nodes, setNodes] = useState<OrgNode[]>([]);
  const [role, setRole] = useState<string>("UNIT_EDITOR");
  const [operation, setOperation] = useState("GRANT");
  const [authSub, setAuthSub] = useState("");
  const [email, setEmail] = useState("");
  const [scope, setScope] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [actionId, setActionId] = useState("");
  const [loading, setLoading] = useState(true);
  const load = async () => {
    setLoading(true);
    try {
      const [req, people, org, me] = await Promise.all([
        api<{ items: Request[] }>("/access/requests"),
        api<{ items: User[] }>("/access/users"),
        api<{ items: OrgNode[] }>("/organization/nodes"),
        api<Identity>("/me"),
      ]);
      setIdentity(me);
      setRequests(req.items);
      setUsers(people.items);
      setNodes(org.items);
    } catch (err) {
      throw err;
    } finally { setLoading(false); }
  };
  useEffect(() => {
    let active=true;
    const refresh=()=>void load().catch(err=>{if(active)setMessage(err instanceof Error?err.message:String(err));});
    refresh();
    const {data}=authClient().auth.onAuthStateChange((event)=>{if(["SIGNED_IN","MFA_CHALLENGE_VERIFIED"].includes(event))setTimeout(()=>{if(active)refresh();},0);});
    return()=>{active=false;data.subscription.unsubscribe();};
  }, []);
  const requiresScope = role === "WARD_ADMIN" || role === "UNIT_EDITOR";
  const choices = nodes.filter(
    (n) => n.active && n.kind === (role === "WARD_ADMIN" ? "WARD" : "UNIT"),
  );
  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setMessage("");
    try {
      await api("/access/requests", {
        method: "POST",
        body: JSON.stringify({
          auth_sub: authSub,
          email,
          role,
          scope_node_id: requiresScope ? scope : null,
          operation,
        }),
      });
      setAuthSub("");
      setEmail("");
      setScope("");
      setMessage(
        "Role change submitted. A separate Thana Administrator must approve it.",
      );
      try { await load(); } catch { setMessage("Your change was saved, but the list could not be refreshed. Reload to view the latest state."); }
    } catch (err) {
      setMessage(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  };
  const decide = async (id: string, approve: boolean) => {
    if (
      !window.confirm(
        approve
          ? "Approve this account permission?"
          : "Reject this permission change?",
      )
    )
      return;
    setBusy(true);
    setActionId(id);
    setMessage("");
    try {
      const saved = await api<Request>("/access/requests/" + id + "/decision", {
        method: "POST",
        body: JSON.stringify({ approve }),
      });
      setRequests(rows=>rows.map(r=>r.id===saved.id?saved:r));
      setMessage(approve ? "Permission approved. The assigned role will appear below." : "Request rejected. No permission was granted.");
      try { await load(); } catch { setMessage("Your change was saved, but the list could not be refreshed. Reload to view the latest state."); }
    } catch (err) {
      setMessage(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  };
  const pendingRemoval = (user: User, grant: User["roles"][number]) => requests.some(r=>r.status==="PENDING"&&r.operation==="REVOKE"&&r.auth_sub===user.auth_sub&&r.role===grant.role&&r.scope_node_id===grant.scope_node_id);
  const removePermission = async (user: User, grant: User["roles"][number]) => {
    if (!window.confirm("Request removal of " + grant.role.replaceAll("_", " ") + " for " + user.email + "? A different main administrator must approve the removal. The account and personal profile will remain.")) return;
    setBusy(true); setActionId(user.id+grant.role+(grant.scope_node_id||"")); setMessage("");
    try {
      const saved=await api<Request>("/access/requests",{method:"POST",body:JSON.stringify({auth_sub:user.auth_sub,email:user.email,role:grant.role,scope_node_id:grant.scope_node_id,operation:"REVOKE"})});
      setRequests(rows=>[saved,...rows]);setMessage("Removal requested. A different main administrator must approve it before this permission is removed.");
      try {await load();} catch {setMessage("Removal request saved. Reload to refresh the directory.");}
    } catch(err){setMessage(err instanceof Error?err.message:String(err));}finally{setBusy(false);}
  };
  return (
    <Shell
      title="Access control"
      subtitle="Approve responsible-person applications and manage account permissions."
    >
      <button type="button" className="secondary-btn" disabled={busy||loading} onClick={()=>void load().catch(err=>setMessage(err instanceof Error?err.message:String(err)))}>Refresh permissions</button>
      {loading && <p role="status">Loading permissions…</p>}
      {message && (
        <div className="alert" role="status">
          {message}
        </div>
      )}
      <div className="panel" style={{ marginBottom: 20 }}>
        <div className="section-title">
          <h2>
            <UserCog size={19} /> Request account permission change
          </h2>
          <span className="pill">Two-person approval</span>
        </div>
        <p className="subhead">
          Select a registered account. Verify the person and their
          responsibility before requesting a permission change. An independent
          main administrator approves administrator-initiated changes.
        </p>
        <form onSubmit={submit}>
          <div className="form-grid">
            <div className="form-field">
              <label htmlFor="grant-account">Registered account</label>
              <select
                id="grant-account"
                className="select"
                required
                value={authSub}
                onChange={(e) => {
                  setAuthSub(e.target.value);
                  setEmail(
                    users.find((u) => u.auth_sub === e.target.value)?.email ||
                      "",
                  );
                }}
              >
                <option value="">Select account</option>
                {users.map((u) => (
                  <option key={u.id} value={u.auth_sub}>
                    {u.email}
                  </option>
                ))}
              </select>
            </div>
            <div className="form-field">
              <label>Verified account email</label>
              <input
                className="input"
                type="email"
                required
                readOnly
                value={email}
              />
            </div>
            <div className="form-field">
              <label>Operation</label>
              <select
                className="select"
                value={operation}
                onChange={(e) => setOperation(e.target.value)}
              >
                <option value="GRANT">Grant permission</option>
                <option value="REVOKE">Revoke permission</option>
              </select>
            </div>
            <div className="form-field">
              <label>Permission role</label>
              <select
                className="select"
                value={role}
                onChange={(e) => {
                  setRole(e.target.value);
                  setScope("");
                }}
              >
                {roles.map((value) => (
                  <option value={value} key={value}>
                    {value.replaceAll("_", " ")}
                  </option>
                ))}
              </select>
            </div>
            {requiresScope && (
              <div className="form-field full">
                <label>{role === "WARD_ADMIN" ? "Ward" : "Unit"} scope</label>
                <select
                  className="select"
                  required
                  value={scope}
                  onChange={(e) => setScope(e.target.value)}
                >
                  <option value="">Select authorized scope</option>
                  {choices.map((n) => (
                    <option value={n.id} key={n.id}>
                      {n.name} — {n.code}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>
          <div className="form-actions">
            <button
              className="primary-btn"
              disabled={busy || loading || (requiresScope && !scope)}
            >
              <Plus size={15} /> Submit permission request
            </button>
          </div>
        </form>
      </div>
      <div
        className="panel"
        style={{ marginBottom: 20, padding: 0, overflow: "hidden" }}
      >
        <div style={{ padding: 24 }}>
          <h2>Pending administrative approvals</h2>
          <p className="subhead">
            Approve users’ role applications here. A requesting administrator
            cannot approve a request they created. They can reject it. Removal also requires an independent review.
          </p>
        </div>
        {requests.some((r) => r.status === "PENDING") ? (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>User</th>
                  <th>Request</th>
                  <th>Scope</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {requests
                  .filter((r) => r.status === "PENDING")
                  .map((r) => (
                    <tr key={r.id}>
                      <td>
                        <b>{r.email}</b>
                        <p className="hint">{r.auth_sub.slice(0, 8)}…</p>
                      </td>
                      <td>
                        {r.operation} {r.role}
                      </td>
                      <td>
                        {nodes.find((n) => n.id === r.scope_node_id)?.name ||
                          "Thana-wide"}
                      </td>
                      <td>
                        <button
                          disabled={busy || loading || !identity || r.requested_by === identity.id}
                          title={r.requested_by===identity?.id?"A different main administrator must approve this request":"Approve permission change"}
                          onClick={() => void decide(r.id, true)}
                        >
                          <CheckCircle2 size={16} /> Approve
                        </button>
                        <button
                          disabled={busy || loading}
                          onClick={() => void decide(r.id, false)}
                        >
                          <XCircle size={16} /> Reject
                        </button>
                        {r.requested_by===identity?.id&&<p className="hint">You created this request. A different main administrator must approve it; you can reject it.</p>}
                        {actionId===r.id&&message&&<p role="status" className="hint">{message}</p>}
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="empty">
            <ShieldCheck size={25} />
            <strong>No access requests pending</strong>
            <span>
              New permission requests will require a separate reviewer.
            </span>
          </div>
        )}
      </div>
      <div className="panel" style={{marginBottom:20}}><h2>Reviewed requests</h2>{requests.filter(r=>r.status!=="PENDING").length ? <div className="table-wrap"><table className="data-table"><thead><tr><th>User</th><th>Permission</th><th>Scope</th><th>Decision</th></tr></thead><tbody>{requests.filter(r=>r.status!=="PENDING").map(r=><tr key={r.id}><td>{r.email}</td><td>{r.operation} {r.role.replaceAll("_"," ")}</td><td>{nodes.find(n=>n.id===r.scope_node_id)?.name||"Thana-wide"}</td><td><span className="pill">{r.status}</span></td></tr>)}</tbody></table></div>:<p>No reviewed requests yet.</p>}</div>
      <PersonalAssignments users={users} />
      <div className="panel" style={{ padding: 0, overflow: "hidden" }}>
        <div style={{ padding: 24 }}>
          <h2>Accounts and approved permissions</h2>
          <p className="subhead">
            Registered application accounts and assigned permissions.
          </p>
        </div>
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Email</th>
                <th>Identity</th>
                <th>Roles</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id}>
                  <td>{u.email}</td>
                  <td>{u.auth_sub.slice(0, 10)}…</td>
                  <td>
                    {u.roles.map((r, i) => (
                      <span className="pill" key={i} style={{ marginRight: 5 }}>
                        {r.role.replaceAll("_"," ")} · {nodes.find(n=>n.id===r.scope_node_id)?.name||"Thana-wide"}
                        {u.is_master_admin&&r.role==="THANA_ADMIN"?<span> · Protected owner</span>:<button type="button" aria-label={"Remove "+r.role+" for "+u.email+" in "+(nodes.find(n=>n.id===r.scope_node_id)?.name||"Thana-wide")} disabled={busy||loading||pendingRemoval(u,r)} onClick={()=>void removePermission(u,r)}>{pendingRemoval(u,r)?"Removal pending":"Remove"}</button>}
                      </span>
                    ))}
                    {!u.roles.length&&<span className="hint">Personal account — no administrative permissions</span>}
                    {actionId.startsWith(u.id)&&message&&<p className="hint" role="status">{message}</p>}
                  </td>
                  <td>{u.active ? "Active" : "Inactive"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      <MasterSecurity reviewsOnly/>
    </Shell>
  );
}
