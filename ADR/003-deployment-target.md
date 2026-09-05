# ADR-003: Deployment target — Fly.io from a committed `fly.toml`, deployed by CI

**Status:** accepted, 2026-09-05

## Context

The assignment requires a public URL for the API and the UI, container-level
visibility for the reviewers, infrastructure as code, secrets outside the
repository, reproducible builds, and a deploy that is safe to run twice.
The service is one container: FastAPI serving `/ask`, `/healthz`, and the
compiled TypeScript page. It holds no state; the corpus and the embeddings
ship inside the image. Traffic during review is a handful of requests a
day, so cold starts matter more than throughput.

The project CLAUDE.md originally named Cloud Run + Terraform. That was our
own stack choice, not the assignment's; the assignment lists `fly.toml`,
`render.yaml`, or docker-compose plus CI as acceptable.

## Alternatives

| | Cloud Run + Terraform | Cloud Run, `gcloud run deploy` | Fly.io, `fly.toml` | Render, `render.yaml` |
| --- | --- | --- | --- | --- |
| IaC in repo | yes, ~80 lines HCL + state to manage | no (a command, not a file) | yes, one file | yes, one file |
| Redeploy without UI steps | yes | yes | yes (`fly deploy`) | on git push, but the first blueprint is created in the dashboard |
| Idempotent | yes | yes | yes | yes |
| Secrets | Secret Manager, referenced by name | Secret Manager | `fly secrets set`, encrypted store | dashboard or `sync: false` env var |
| Container-level access for reviewers | IAM invite to project, Cloud Logging | same | org invite, `fly logs`, `fly status`, dashboard | dashboard invite |
| Scale to zero | yes | yes | yes (`auto_stop_machines`) | free tier sleeps, 30 s+ wake |
| Tools to install | gcloud + terraform | gcloud | flyctl | none |
| Cost at review traffic | free tier | free tier | free allowance, card required | free |

Criteria, in order: satisfies every deployment requirement of the
assignment; least ceremony for a one-container service; cold start short
enough that a reviewer's first request does not time out; a redeploy path
that CI can run.

## Decision

**Fly.io.** One committed `fly.toml`, the same Dockerfile used locally,
`fly deploy` from a GitHub Actions job on every push to `main` after the
test gate. The Anthropic key is set once with `fly secrets set` and reaches
the container as an environment variable; it is never in the repo, the
image, or CI. Reviewers get an invitation to the Fly organisation, which
shows machine status and logs, plus `fly logs` from the CLI. Machines stop
when idle and start on the first request; the cold-start cost is measured
and recorded in the README and SPEC section 6.

Terraform for two resources would have been more code than the service's
own infrastructure. Cloud Run without Terraform loses the IaC file. Render
loses the no-UI-steps rule on first creation and has the slowest wake.

## Conditions that invalidate this decision

- Traffic that needs more than one region or more than a few machines:
  Fly's per-machine model gets fiddly; Cloud Run's request-based scaling
  is simpler there.
- A requirement for the deployment to live in the same cloud as other
  company infrastructure (IAM, VPC, audit logging): move to Cloud Run with
  Terraform, keeping the same Dockerfile.
- A cold-start p95 above the latency budget once measured: set
  `min_machines_running = 1` (still one line of `fly.toml`) and accept the
  idle cost.

## Consequences

- `docker compose up` locally and `fly deploy` remotely build the same
  image from the same Dockerfile and pinned `requirements.txt`.
- The scale-to-zero setting interacts with the full-context prompt cache
  (ADR-002): a stopped machine means the next request pays both a machine
  start and a cache write. Both are measured in Block 7.
- Rollback is `fly releases` + `fly deploy --image <previous>`; no state to
  migrate.
