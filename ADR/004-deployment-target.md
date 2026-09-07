# ADR-004: Deployment target — Fly.io from a committed `fly.toml`, deployed by CI

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
| Redeploy without UI steps | yes | yes | yes (`fly deploy`, or Fly's GitHub integration on push after a one-time connection) | on git push, but the first blueprint is created in the dashboard |
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
deployed on every push to `main` by Fly's GitHub integration (user decision
2026-09-05; the original plan was a GitHub Actions job holding a Fly token,
dropped so there is one deploy path and no Fly credential in GitHub). The
GitHub Actions workflow is the test gate only. The Anthropic key is set once
with `fly secrets set` and reaches
the container as an environment variable; it is never in the repo, the
image, or CI. Reviewers get the second of the assignment's two visibility
options, access to logs and container status, through `GET /ops` behind
`OPS_TOKEN` (README, Deployment). The dashboard invitation was the first
choice and was dropped for a fact learned late: the app lives in a Fly
personal organisation, and a personal organisation cannot take members.
Moving the app to a new organisation would mean a second billing account and
re-allocating the public IPs, which is the step that already failed once on
this app, so the cost outweighed a nicer viewing experience. Machines stop
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

## Addendum, 2026-09-07: moved to Render

Fly's trial ended and the account now refuses every write, including
`apps destroy`: "trial has ended, please add a credit card". A second Fly
account behaves the same way, because Fly asks for a card before it will
create an app in any new organisation. The service was suspended and the
public URL was dead, which is a hard failure two days before review.

**The condition that fired was not on the list above.** The three
invalidation conditions were about traffic, cloud affinity and cold-start
latency; none of them anticipated the host withdrawing its free tier. That
is the honest lesson of this ADR: for a deliverable that must stay reachable
without a payment method, "cost at review traffic" belongs in the criteria
with the same weight as the technical rows, and the Fly row of the table
already said "card required".

**New decision: Render**, from a committed [render.yaml](../render.yaml),
the same Dockerfile, on the free plan in `frankfurt`. Everything that
mattered about the Fly setup survives the move:

- The unit of deployment is still the committed image. No application code
  changed; the Dockerfile already binds to `$PORT`, which is what Render
  injects.
- Redeploy still happens with no UI step: `autoDeployTrigger: commit` in the
  blueprint rebuilds and rolls the service on every push to `main`. Verified
  on the commit that fixed `/ops`, which reached the running service without
  anyone touching the dashboard.
- Secrets are still outside the repository and the image: `sync: false`
  marks `ANTHROPIC_API_KEY` and `OPS_TOKEN` as values Render asks for once
  and stores encrypted.
- Reviewer visibility is unchanged, `GET /ops` behind `OPS_TOKEN`, and now
  also the Render dashboard's own logs and status.

What is worse, stated plainly: the free instance is 512 MB and 0.1 CPU
against Fly's shared CPU, and it sleeps after 15 minutes of inactivity with
a wake that is much slower than Fly's machine start. The cold-start figure
in the README and SPEC section 6 is re-measured on Render; the earlier Fly
numbers are kept alongside, labelled, because they are the evidence for the
comparison. The blueprint's first creation was a dashboard step, which is
the one row of the table where Render is genuinely weaker and the reason it
lost the original decision.

**This decision is invalid if** the review window closes and the service
needs a warm p95 (Render's free plan has no always-on option, so that means
paying on Render or returning to Fly with a card), if traffic ever exceeds
the 750 free instance hours a month, or if the 512 MB limit stops fitting
the corpus and the index.

## Consequences

- `docker compose up` locally and `fly deploy` remotely build the same
  image from the same Dockerfile and pinned `requirements.txt`.
- The scale-to-zero setting interacts with the full-context prompt cache
  (ADR-002): a stopped machine means the next request pays both a machine
  start and a cache write. Both are measured in Block 7.
- Rollback is `fly releases` + `fly deploy --image <previous>`; no state to
  migrate.
