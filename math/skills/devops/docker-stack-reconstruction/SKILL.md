---
name: docker-stack-reconstruction
description: "Rebuild or validate a live Docker compose stack."
version: 1.0.0
author: hermes-curator
license: MIT
metadata:
  hermes:
    tags: [docker, compose, self-hosted, audit, ssh, verification]
    related_skills: [hermes-profile-packaging, agent-tool-diagnostics]
related_skills: [hermes-profile-packaging, agent-tool-diagnostics]
---

# Docker Stack Reconstruction

Use when a live self-hosted deployment — typically the service plane that a set of Hermes
profiles, skills or MCP servers talk to — must become a reproducible `docker compose` project,
or when an existing compose file must be validated against what is actually running on a host.
The deliverable is a validated stack folder plus a service map that names which skill or MCP
server consumes each container.

## When to Use

- "Put together a docker-compose setup that creates the entire stack", "make the stack reproducible"
- Documenting or auditing which containers back a set of skills / MCP servers
- Collapsing N per-service compose projects into one stack, or migrating it to another host
- Verifying a compose file against a live host **before** deploying it

## When Not to Use

- Installing/configuring Hermes itself — use the `hermes-agent` skill.
- A single-container task (one `docker run`) — no reconstruction needed.
- Packaging the config tree that talks to the stack — use `hermes-profile-packaging`.

## Procedure

1. **Recon over SSH; never assume the layout.** Confirm access first:
   `ssh -o BatchMode=yes user@host 'hostname; docker --version; docker compose version'`.
   Then `docker compose ls -a` — this is the project → compose-file map, the single most useful
   recon command. Follow with `docker ps --format "{{.Names}}\t{{.Image}}\t{{.Ports}}"`,
   `docker network ls`, `docker volume ls`, and `ss -tlnp | grep -E ':(1234|9876|8080)'` to catch
   **host-level** services that are not containers at all.
2. **Read the real compose files.** `cat` each project's file rather than inventing a plausible
   stack. Record per service: image vs `build:`, container_name, published ports, volumes,
   environment, healthcheck, depends_on. A container whose image is `<project>-<service>` is a
   **local build** and cannot be reproduced from an image reference alone.
3. **Extract environment variable NAMES, not values.** The variable surface is what you need:
   `grep -oE "^[A-Za-z_][A-Za-z0-9_]*=" .env | tr -d "=" | sort`. Print values only for a
   whitelist of clearly non-secret keys (`*_MODEL`, `*_HOST`, `*_PORT`, `*_TIMEOUT`, `*_BINDING`,
   storage-type and dimension keys). This keeps secrets out of the transcript while still giving
   a faithful template.
4. **Write one compose project.** Keep `container_name`, image, published ports and healthchecks
   compatible with the live ones so a later parity diff is meaningful. Interpolate every
   credential from `${VAR}`; ship `.env.example` with placeholders and git-ignore the real `.env`.
   Where the host runs a local build, either keep the `build:` context or use the published
   upstream image — and say which in a comment plus the README.
5. **Keep service names equal to the hostnames the env files reference.** Separate projects have
   separate bridge networks; one project means one network, so `NEO4J_URI=bolt://neo4j:7687`,
   `redis://searxng-redis:6379`, `@database:5432` only keep resolving if the compose service names
   match. Renaming a service while unifying silently breaks every dependent container.
6. **Validate on the host, not locally.** Copy the folder to a temp dir there, fill a throwaway
   `.env` from the example, create stub files for any bind mount whose absence would fail
   resolution, then run `docker compose config -q` (syntax + interpolation) and
   `docker compose up --dry-run` (full creation plan, no side effects).
7. **Verify parity in code, not in prose.** Resolve the plan with
   `docker compose config --format json` and diff it against `docker ps` output: container names,
   images, published host ports. Use `scripts/compare_compose_to_live.py`.
8. **Do not deploy over a live stack.** A reconstruction reuses container names and host ports, so
   `up` collides with what is running. Deliver the validated folder and offer migration as a
   separate, explicitly confirmed step: stop the old projects, point the data directory at the
   existing tree, bring the unified stack up.
9. **Clean up and re-check.** Remove the host temp dir, then confirm the live host is untouched:
   container count unchanged, no new containers (`docker ps -a --filter name=<project>` → 0),
   nothing unhealthy.

## Verification Standard

A reconstruction is "done" when all four hold, each backed by real output:

| Check | Command | Pass condition |
|---|---|---|
| Syntax + interpolation | `docker compose config -q` | exit 0 |
| Plan resolves | `docker compose up --dry-run` | every service reaches "Created" |
| Parity vs live | plan JSON diffed against `docker ps` | identical names and published ports |
| Host untouched | `docker ps \| wc -l`, leftover filter | counts unchanged, 0 leftovers |

State the intentional deviations explicitly (local builds kept as builds; a published image
substituted for a local build). An unexplained delta reads as a defect.

## Documenting the Stack

The reconstruction's companion document carries a **component inventory**, not just a README.
Per component, four columns: **Component | Endpoint | Image | Role in the workflow**.

- **Phrase the role by consumer, not by product.** "Task ledger: hypothesis trees and
  cross-session state, reached through the vikunja tool bridge and the kanban plugin" — not
  "an open-source task manager". The reader is asking which part of their workflow this container
  is load-bearing for.
- **Split the inventory into tables small enough to fit a page.** One row per container (16 is
  typical) in a single table silently truncates: the build reports zero errors while the last rows
  are cut off at the page boundary. Split by function — edge + knowledge management; retrieval +
  ingestion + memory — and drop dense reference tables to `\footnotesize`. Verify row presence in
  the rendered output, never by exit code alone; the mechanics live in `latex-manuscript`.
- **Add a workflow-stage mapping.** A second table: stage of the consuming pipeline → components
  that serve it → what they contribute. Include the stages the stack does **not** serve and say why
  (e.g. computation and formal verification run against a local toolchain, deliberately offline).
  An absent row is a design statement; omitting it invites a later session to "fix" the gap by
  adding services that cannot work.
- **List what is not containerised, one reason per row.** An inference server on another machine, a
  host `systemd` service, SaaS APIs — each gets a row and the one-clause reason it is out of scope.
- **Keep the document as scrubbed as the stack folder.** No LAN address, hostname or credential in
  the prose; the appendix is part of the same distributable and needs the same residual scan.

## Pitfalls

- **A naive port diff invents mismatches.** Live `docker ps` renders loopback binds
  (`127.0.0.1:5433->5432/tcp`), port ranges (`0.0.0.0:6333-6334->6333-6334/tcp`) and internal-only
  ports (`8000/tcp`). A regex expecting `0.0.0.0:<port>->` drops the first two and reports a
  difference that does not exist. Parse all forms before concluding anything.
- **`find / -name docker-compose.yml` is not the project map.** It misses projects and returns
  dormant drafts (an unused stack directory is not part of the running plane). `docker compose ls -a`
  is authoritative; use `find` only to locate files the map already named.
- **Host-level and SaaS dependencies belong in the README, not the compose.** An inference server
  on another machine, a `systemd` service on the host, and SaaS APIs cannot be containerized here.
  Naming them stops a later session from "fixing" the stack by adding services that cannot work.
- **Never commit the real `.env`.** Add it to `.gitignore` and confirm with
  `git ls-files | grep -E '\.env$'` that only the example is tracked.
- **Scrub the deployment document too.** A stack README naming the LAN address, hostname or a
  reused password leaks exactly what the packaging policy removes — run the same residual scan
  over the new folder (see `hermes-profile-packaging`).
- **Record audit findings during recon or lose them.** Reused credentials across services,
  plaintext secrets in compose files, a reverse proxy with zero configured hosts, unpinned derived
  images, a stack depending on a machine that is not the host. Write them down at once; they are
  the durable value of the exercise, and the reconstruction is what makes them fixable.
- **Don't hand-edit the generated stack after validating it.** Re-run the copy/validate/parity loop
  instead, so the verified state and the committed state stay the same object.

## Support Files

- `scripts/compare_compose_to_live.py` — diff a `docker compose config --format json` plan against
  `docker ps` output (names, images, published ports; loopback- and range-aware).
