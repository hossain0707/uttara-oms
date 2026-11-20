import { authClient } from "./supabase";

export type Role = { role: string; scope_node_id: string | null };
export type Identity = { id: string; email: string; roles: Role[]; mfa: boolean };
export type OrgNode = { id: string; parent_id: string | null; kind: "THANA" | "WARD" | "UNIT"; name: string; code: string; active: boolean };
export type Category = "RUKON" | "WORKER" | "ASSOCIATE" | "SUPPORTER";
export type Member = {
  id: string; member_number: string; full_name: string; father_name: string | null;
  phone: string | null; address: string | null; occupation: string | null;
  position: string | null; category: Category; status: string; org_node_id: string;
  joined_on: string | null; version: number;
};
export type Approval = {
  id: string; member_id: string; kind: string; proposed_value: string; status: string;
  requested_by: string; requested_at: string; reviewed_at: string | null; review_note: string | null;
};
export type Dashboard = {
  total_active: number; by_category: Record<Category, number>;
  this_month: {increase: number; decrease: number; net: number};
  by_unit: { id: string; name: string; code: string; count: number }[];
  by_ward: { id: string; name: string; code: string; count: number }[];
  period: {start_date:string; end_date:string; increase:number; decrease:number; net:number};
  comparison: {start_date:string; end_date:string; total_active:number; increase:number; decrease:number; net:number};
  monthly_history: {month:string; start_date:string; end_date:string; increase:number; decrease:number; net:number}[];
  timezone: string; as_of: string;
  generated_at: string;
};

const base = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const {data} = await authClient().auth.getSession();
  if (!data.session?.access_token) throw new Error("Please sign in again");
  const response = await fetch(base + "/api/v1" + path, {
    ...options,
    cache: "no-store",
    headers: {
      Authorization: "Bearer " + data.session.access_token,
      ...(options.body ? {"Content-Type": "application/json"} : {}),
      ...(options.headers || {}),
    },
  });
  if (!response.ok) {
    let message = "Request failed (" + response.status + ")";
    try { const detail = (await response.json()).detail; if (detail) message = typeof detail === "string" ? detail : Array.isArray(detail) ? detail.map((issue: {loc?: (string | number)[]; msg?: string}) => {
      const location = (issue.loc || []).filter((part) => part !== "body" && part !== "details").map((part) => typeof part === "number" ? `#${part + 1}` : part.replaceAll("_", " ")).join(" → ");
      return `${location ? location + ": " : ""}${issue.msg || "Check this value"}`;
    }).join("; ") : "Please check your entries and try again."; } catch {}
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}

export async function downloadReport(extension: "xlsx" | "pdf", personal = false, filters = "") {
  const {data} = await authClient().auth.getSession();
  if (!data.session?.access_token) throw new Error("Please sign in");
  const url = base + "/api/v1/reports/export." + extension + "?" + new URLSearchParams({...Object.fromEntries(new URLSearchParams(filters)), ...(personal ? {include_personal:"true"} : {})});
  const res = await fetch(url, {headers: {Authorization: "Bearer " + data.session.access_token}, cache: "no-store"});
  if (!res.ok) throw new Error("Export failed: " + res.status);
  const link = document.createElement("a");
  const objectUrl = URL.createObjectURL(await res.blob());
  link.href = objectUrl; link.download = "uttara-oms-report." + extension;
  document.body.append(link); link.click(); link.remove();
  setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);
}

export async function downloadPersonalReport(id:string, extension:"pdf"|"xlsx") {
  const {data}=await authClient().auth.getSession();
  if(!data.session?.access_token)throw new Error("Please sign in");
  const response=await fetch(base+"/api/v1/self/reports/"+encodeURIComponent(id)+"/export/"+extension,{cache:"no-store",headers:{Authorization:"Bearer "+data.session.access_token}});
  if(!response.ok)throw new Error("Personal export failed: "+response.status);
  const url=URL.createObjectURL(await response.blob()),link=document.createElement("a");
  link.href=url;link.download="my-personal-report."+extension;document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
