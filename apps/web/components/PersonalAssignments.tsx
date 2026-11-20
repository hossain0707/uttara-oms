"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { metrics } from "./PersonalWorkspace";
type User = {
  id: string;
  email: string;
  active: boolean;
  roles: { role: string }[];
};
type Assignment = {
  version: number;
  reviewer_id: string | null;
  member_id: string | null;
  goals: { metric: string; target: number }[];
};
export default function PersonalAssignments({ users }: { users: User[] }) {
  const [user, setUser] = useState(""),
    [assignment, setAssignment] = useState<Assignment | null>(null),
    [targets, setTargets] = useState<Record<string, string>>({}),
    [notice, setNotice] = useState(""),
    [busy, setBusy] = useState(false);
  useEffect(() => {
    let active = true;
    setAssignment(null);
    setNotice("");
    if (user)
      api<Assignment>("/access/personal/" + user)
        .then((a) => {
          if (active) {
            setAssignment(a);
            setTargets(
              Object.fromEntries(
                a.goals.map((g) => [g.metric, String(g.target)]),
              ),
            );
          }
        })
        .catch((e) => {
          if (active) setNotice(String(e));
        });
    return () => {
      active = false;
    };
  }, [user]);
  return (
    <div className="panel" style={{ marginBottom: 20 }}>
      <h2>Personal reviewers & monthly targets</h2>
      <p>
        Assign a responsible person to review a user’s submitted reports.
        Assignment management does not reveal private report content.
      </p>
      {notice && (
        <div className="alert" role="status">
          {notice}
        </div>
      )}
      <label htmlFor="assignment-user">Account</label>
      <select
        id="assignment-user"
        className="select"
        value={user}
        onChange={(e) => setUser(e.target.value)}
      >
        <option value="">Select registered user</option>
        {users
          .filter((u) => u.active)
          .map((u) => (
            <option key={u.id} value={u.id}>
              {u.email}
            </option>
          ))}
      </select>
      {assignment && (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            setBusy(true);
            setNotice("");
            api<Assignment>("/access/personal/" + user, {
              method: "PUT",
              body: JSON.stringify({
                ...assignment,
                expected_version: assignment.version,
                version: undefined,
                goals: metrics
                  .filter((m) => targets[m.key])
                  .map((m) => ({
                    metric: m.key,
                    target: Number(targets[m.key]),
                  })),
              }),
            })
              .then((a) => {
                setAssignment(a);
                setNotice("Reviewer and targets saved.");
              })
              .catch((e) => setNotice(String(e)))
              .finally(() => setBusy(false));
          }}
        >
          <div className="form-grid">
            <div className="form-field">
              <label htmlFor="reviewer">Responsible reviewer</label>
              <select
                id="reviewer"
                className="select"
                value={assignment.reviewer_id || ""}
                onChange={(e) =>
                  setAssignment((a) =>
                    a ? { ...a, reviewer_id: e.target.value || null } : a,
                  )
                }
              >
                <option value="">No reviewer</option>
                {users
                  .filter((u) => u.active && u.roles.length && u.id !== user)
                  .map((u) => (
                    <option key={u.id} value={u.id}>
                      {u.email}
                    </option>
                  ))}
              </select>
            </div>
            {metrics.map((m) => (
              <div className="form-field" key={m.key}>
                <label htmlFor={"target-" + m.key}>
                  {m.label} target ({m.unit} / month)
                </label>
                <input
                  id={"target-" + m.key}
                  className="input"
                  type="number"
                  min={1}
                  max={1000000}
                  step={1}
                  placeholder="Not assigned"
                  value={targets[m.key] || ""}
                  onChange={(e) =>
                    setTargets((v) => ({ ...v, [m.key]: e.target.value }))
                  }
                />
              </div>
            ))}
          </div>
          <p>
            Blank targets are unassigned. Confirm the units before entering
            targets such as 140, 300 or 90.
          </p>
          <button className="primary-btn" disabled={busy}>
            Save reviewer & targets
          </button>
        </form>
      )}
    </div>
  );
}
