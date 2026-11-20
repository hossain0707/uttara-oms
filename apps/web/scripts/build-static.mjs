// Static deployment keeps auth/data requests in the existing FastAPI service.
import {createRequire} from "node:module";
import {spawnSync} from "node:child_process";
import {writeFileSync} from "node:fs";
const require = createRequire(import.meta.url);
require("@next/env").loadEnvConfig(process.cwd());
const required = ["NEXT_PUBLIC_API_URL", "NEXT_PUBLIC_SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY"];
for (const name of required) {
  if (!process.env[name]?.trim()) throw new Error(`${name} is required for a static deployment`);
}
const origins = ["NEXT_PUBLIC_API_URL", "NEXT_PUBLIC_SUPABASE_URL"].map(name=>{
  const url = new URL(process.env[name]);
  if (!["http:","https:"].includes(url.protocol) || url.username || url.password) {
    throw new Error(`${name} must be an HTTP(S) URL without credentials`);
  }
  return url.origin;
});
const result = spawnSync(process.execPath,[require.resolve("next/dist/bin/next"),"build"],{
  env:{...process.env,NEXT_OUTPUT_MODE:"export"},stdio:"inherit",
});
if(result.error)throw result.error;
if(result.status!==0)process.exit(result.status??1);
const csp = ["default-src 'self'", "script-src 'self' 'unsafe-inline'", "style-src 'self' 'unsafe-inline'",
  "img-src 'self' data:", `connect-src 'self' ${origins.join(" ")}`, "base-uri 'none'",
  "object-src 'none'", "frame-ancestors 'none'", "form-action 'self'"].join("; ");
writeFileSync("out/_headers",`/*
  X-Content-Type-Options: nosniff
  Referrer-Policy: no-referrer
  X-Frame-Options: DENY
  Permissions-Policy: camera=(), microphone=(), geolocation=()
  Cache-Control: no-store
  Content-Security-Policy: ${csp}
`);
