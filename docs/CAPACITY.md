# Free-tier limits and measured capacity evidence

Reviewed 2026-11-22. Quotas are provider allowances, not a simultaneous-user benchmark. Current dashboard values and actual usage must be checked by an authorized operator before a rollout. No application user limit was added.

## Services in this deployment

| Service | Free configuration / documented allowance | Relevance |
| --- | --- | --- |
| Cloudflare Pages | Static export; Free docs list 500 builds/month and one build at a time | Build quota is not a login/user-count quota; API work happens elsewhere |
| Render Free web service | 0.1 CPU, 512 MB RAM; spins down after inactivity | Main API processing bottleneck and cold-start latency; no always-on guarantee |
| Supabase Free | 500 MB database, 50,000 monthly active Auth users, 5 GB egress | Active users are not concurrency; database includes encrypted photos/reports/audit |
| Supabase Auth custom SMTP | Initial documented 30 messages/hour unless changed | Current project rate setting was not rechecked for this capacity note |
| Standard Gmail sender | More than approximately 500 messages/day can trigger sending limits | Shared with other mailbox sends; OTP resend/recovery consumes allowance |

Sources checked for this update: [Cloudflare Pages limits](https://developers.cloudflare.com/pages/platform/limits/), [Render compute plans](https://render.com/docs/compute-plans), [Render free limitations](https://render.com/docs/free), [Supabase billing quotas](https://supabase.com/docs/guides/platform/billing-on-supabase), [Supabase SMTP](https://supabase.com/docs/guides/auth/auth-smtp), [Gmail sending limits](https://support.google.com/mail/answer/22839?hl=en). Recheck official documentation; do not treat these figures as contractual guarantees. No paid resource is enabled by this guide.

## Read-only burst test — 2026-11-22

The owner authorized a small 50-at-once test without configuration changes, new accounts or emails. Tests were run sequentially from one remote runner, with 50 threads released together for each burst. Requests used separate client connections. TLS, runner scheduling, network/proxy and server queue time are included in client wall times. A readiness warm-up returned HTTP 200 in 6.900 seconds; a cold-start latency distribution was not measured.

| Endpoint / client | Successful responses | Burst duration | Median | 95th percentile | Maximum |
| --- | --- | --- | --- | --- | --- |
| `/login/`, initial Python urllib | 0/50; HTTP 403 | 6.008 s | 5.964 s | 5.997 s | 5.998 s |
| `/health/ready`, Python urllib | 50/50 HTTP 200 + ready body | 7.837 s | 7.333 s | 7.787 s | 7.833 s |
| `/login/`, subsequent curl | 50/50 HTTP 200 + page marker | 7.189 s | 7.175 s | 7.186 s | 7.186 s |

The initial frontend 403 cause was not established. A single curl probe and subsequent 50-request curl burst succeeded. Do not erase the failed attempt or claim every tested client passed. These calls were read-only readiness/page requests; no logged-in business data was fetched, no accounts were created, no emails were sent and no configuration was changed.

Observed completions divided by burst wall time were 6.38/s for successful readiness and 6.96/s for the successful frontend burst. **These are not sustained throughput limits or peak capacity.** Median is not an arithmetic average. One burst cannot establish reliability, resource saturation, p99 behavior or an availability SLO. The JSON evidence records the observed values; raw HTTP bodies and private user data are not included.

[Machine-readable result](evidence/load-smoke-2026-11-22.json).

## What can be concluded

The deployment answered these successful 50-request bursts. This is encouraging for a small pilot, but it is not a 50-authenticated-user certification. It does not test JWT verification under load, concurrent profile writes, report saves, directory scans, root-lock contention, SMTP or exports. Fifty open browsers can produce very different request rates depending on activity.

The current Access control and Master Admin account listings each return at most 500 rows; this is a management-list limitation, not a signup cap. Request queues and report lists also have bounded results. Pagination/search beyond these caps needs a separate implementation before claiming complete management of 1,000 accounts.

A 1,000-account target is not blocked by the published Auth monthly-user allowance alone. It was **not tested by creating 1,000 users**. Database/photo/report/audit growth, email delivery and concurrent workload must still be measured. Photo data currently consumes database space, including base64/encryption overhead; the unused object-storage allowance cannot be counted as database headroom.

## Next capacity test (separate authorization/environment)

Use synthetic identities in isolated staging with production-equivalent resource sizing. Establish workload and success thresholds before execution: 50 authenticated sessions, realistic think time, approved read/write mix, dataset near the expected 1,000-account size, representative photos/reports, no uncontrolled email delivery. Measure latency distribution, errors, CPU/RAM, pool/DB wait, encrypted directory cost, root-lock waits, export memory, storage/egress and recovery after a burst. Include authentication policy variants without weakening production MFA or approvals. Run sustained and cold-start phases separately and retain sanitized evidence. This test has not been performed.
