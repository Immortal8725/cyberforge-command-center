# Architecture

CyberForge is organized as numbered zones. Phase 1 runs one zone: defenses. Every other zone directory is an empty placeholder and is outside this change.

## Zones

| Zone | Directory | Status in this repository |
| --- | --- | --- |
| Gateway / challenge import | `zone1-gateway/` | Out of scope. Not in this PR. |
| Target applications | `zone2-targets/` | Future / external. Not in this PR. No application code is shipped. |
| Defenses | `zone3-defenses/` | Shipped. Filebeat plus the anomaly engine. |
| Cloud and later range zones | `zone4-*` through `zone11-*` | Out of scope. Empty placeholders. |
| Shared labs (copilot, tenants, manuals, deploy) | several top-level folders | Out of scope. Empty placeholders. |

Zone 2 target applications and any CTF or exploit content are not part of this tree. They are not scheduled as in-repo work by this phase. See [ROADMAP.md](ROADMAP.md).

## Defensive core data flow

```text
log-generator
    writes benign JSON access lines
        -> volume cyberforge-logs
            -> filebeat
                -> elasticsearch (index cyberforge-access-*)
                    -> kibana

operator or health script
    POST /score  ->  ml_engine
                      Isolation Forest on request shape
                      plus a per-source rate z-score
```

The anomaly engine does not subscribe to Elasticsearch in this phase. Callers post request metadata directly. Features are numeric shape and rate fields: method, status class, path length, query length, body size, user-agent length, hour, and recent request count. The service does not keep a signature list and does not classify attack techniques.

Elasticsearch security is disabled inside the compose network so Filebeat and Kibana can start without an enrollment token. Host ports are bound to loopback. [SECURITY-REVIEW.md](SECURITY-REVIEW.md) explains why that default must not be copied onto a shared network.

## Processes

| Service | Image | Role |
| --- | --- | --- |
| `elasticsearch` | Elasticsearch 8.19 | Single-node log store |
| `kibana` | Kibana 8.19 | Search UI for `cyberforge-access-*` |
| `log-generator` | local Python image | Benign access-log source |
| `filebeat` | Filebeat 8.19 | Ships the log volume |
| `ml_engine` | local Python image | `/health` and `/score` |

Postgres is described in `.env.example` and is not part of the running architecture yet. `init-db/` stays unused until a database service exists.
