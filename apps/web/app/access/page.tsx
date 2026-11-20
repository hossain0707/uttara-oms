"use client";
import { useEffect, useState, type FormEvent } from "react";
import {
  UserCog,
  ShieldCheck,
  Plus,
  CheckCircle2,
  XCircle,
} from "lucide-react";
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
  const load = async () => {
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
      setMessage(err instanceof Error ? err.message : String(err));
    }
  };
  useEffect(() => {
    void load();
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
      await load();
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
    setMessage("");
    try {
      await api("/access/requests/" + id + "/decision", {
        method: "POST",
        body: JSON.stringify({ approve }),
      });
      setMessage("Access decision saved and audited.");
      await load();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  };
  return (
    <Shell
      title="Access control"
      subtitle="Approve responsible-person applications and manage account permissions."
    >
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
              disabled={busy || (requiresScope && !scope)}
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
            cannot approve their own permission change.
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
                          disabled={busy || r.requested_by === identity?.id}
                          onClick={() => void decide(r.id, true)}
                        >
                          <CheckCircle2 size={16} /> Approve
                        </button>
                        <button
                          disabled={busy || r.requested_by === identity?.id}
                          onClick={() => void decide(r.id, false)}
                        >
                          <XCircle size={16} /> Reject
                        </button>
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
      <PersonalAssignments users={users} />
      <div className="panel" style={{ padding: 0, overflow: "hidden" }}>
        <div style={{ padding: 24 }}>
          <h2>Approved account directory</h2>
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
                        {r.role}
                      </span>
                    ))}
                  </td>
                  <td>{u.active ? "Active" : "Inactive"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </Shell>
  );
}
