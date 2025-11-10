# ArxOS on Kubernetes

This guide outlines how to run ArxOS workloads on Kubernetes to support large-scale automation, scheduled processing, and managed deployments.

---

## 1. Containers & Runtime Requirements

### Supported Image
- `ghcr.io/arx-os/arxos:runtime` – CLI-focused runtime (non-root, bundled schemas and headers).

### Execution prerequisites
- Mount a writable workspace at `/workspace`.
- Provide Git credentials via Secrets (SSH keys or Personal Access Token).
- Optional: supply additional config files (YAML) via ConfigMaps.
- Network access to Git remote and data sources (S3, REST APIs).

### Long-running support
- Runtime image supports `arx` commands that complete after execution. For service-style workloads, wrap with a lightweight API binary (see Section 5).

---

## 2. Custom Resource Definitions

### `ArxJob`
Represents a single ArxOS CLI invocation.

Fields:
- `spec.repo` – Git repository (SSH/HTTPS) with building data.
- `spec.ref` – Git reference (branch, tag, commit).
- `spec.command` – CLI command and arguments (e.g., `["arx", "import", "Building.ifc", "--output", "hq"]`).
- `spec.env` – Environment variables (array of key/value).
- `spec.artifacts` – Output locations (PVC path, S3 upload, archive settings).
- `spec.resources` – CPU/memory requests/limits.
- `spec.timeoutSeconds` – Optional runtime limit.
- `status` – Phase, start/end timestamps, exit code, logs summary.

### `ArxSchedule`
Defines recurring tasks executed by CronJobs.

Fields:
- `spec.schedule` – Cron format.
- `spec.template` – Embedded `ArxJob` spec.
- `spec.historyLimit` – Completed Jobs retained.
- `status.lastScheduledTime` – Observability.

---

## 3. Operator Architecture

### Implementation
- Language: Rust with `kube-rs` or Go with `kubebuilder`.
- Components:
  1. **ArxJob Controller** – watches `ArxJob`, spawns Kubernetes Job, monitors Pods, updates status on completion/failure.
  2. **ArxSchedule Controller** – expands Cron schedules into `ArxJob` instances, managing concurrency policy (`Forbid`, `Replace`, `Allow`).

### Git Handling
- Init container clones repo into `/workspace/repo`.
- Optionally checks out `spec.ref` or defaults to branch.
- Credentials:
  - SSH: mount secret at `/credentials/ssh`, set `GIT_SSH_COMMAND`.
  - HTTPS: inject PAT via env var `GIT_TOKEN` and configure `git config credential.helper`.

### Artifacts
- Use `emptyDir` + `PersistentVolumeClaim` for workspace state.
- Optional sidecar to upload to S3 (`aws s3 sync`).
- Operator updates status with artifact URIs.

### Retry & Concurrency
- Kubernetes Job handles retry/backoff (`ttlSecondsAfterFinished`, `backoffLimit`).
- Operator enforces per-namespace limits (ConfigMap-driven) to avoid overwhelming Git remotes or sensors.

### Observability
- Controller metrics via Prometheus (`/metrics`).
- Structured logs (JSON) for job lifecycle.
- Optional OpenTelemetry spans per Job.

---

## 4. Helm Chart & Manifests

### Helm Structure
- Chart name: `arxos-k8s`.
- Templates:
  - `crds/` – `arxjob.yaml`, `arxschedule.yaml`.
  - `deployment.yaml` – operator Deployment with RBAC.
  - `serviceaccount.yaml`, `role.yaml`, `rolebinding.yaml`.
  - `configmap.yaml` – default settings (image tags, resource limits).
  - Optional `api-deployment.yaml` if API gateway enabled.

### Values
- `image.repository`, `image.tag`.
- `git.sshSecretName` or `git.tokenSecretName`.
- `storage.workspace.pvc` (existing claim or dynamic provisioner).
- `operator.resources` and `nodeSelector`, `tolerations`, `affinity`.
- `metrics.enabled` for Prometheus ServiceMonitor integration.
- `api.enabled`, `api.replicas`, `api.service.type`.

### Example Installation
```bash
helm repo add arxos https://arx-os.github.io/charts
helm install arxos arxos/arxos-k8s \
  --set image.tag=2.0.0 \
  --set git.sshSecretName=arxos-git-ssh \
  --set storage.workspace.storageClass=fast-ssd
```

---

## 5. Optional API Layer

- Lightweight microservice (Rust `axum` or Go `gin`) compiled into separate binary.
- Runs in same pod as runtime image or as separate deployment.
- Exposes REST/gRPC to enqueue `ArxJob` CRs (ensuring RBAC controls).
- Supports webhook triggers from BIM portals or facility monitoring systems.
- Feature-gated: only built and deployed when `api.enabled=true`.

---

## 6. GitOps & Secret Management

- Recommend GitOps approach (ArgoCD/Flux) to manage CRD instances.
- Secrets:
  - Use `SealedSecret` (bitnami) or SOPS for encrypted storage.
  - Mount SSH private key at `/credentials/ssh/id_ed25519` with `0400` permissions.
  - PAT via `envFrom` referencing `Secret` with `GIT_USERNAME` and `GIT_PASSWORD`.
- RBAC:
  - Operator service account needs `create/get/watch/list` on Jobs, Pods, Events, and CRDs.
  - Limit namespace scope; optionally use separate namespace per tenant.

---

## 7. Security Best Practices

- Run runtime container as non-root (`runAsUser`, `runAsGroup`).
- Read-only root filesystem; mount workspaces via PVC.
- Apply PodSecurity or PSP (if legacy) to enforce seccomp/apparmor.
- Use NetworkPolicies to restrict outbound traffic to Git hosts and approved services.
- Enable image verification (cosign) and admission control hooks for compliance.

---

## 8. Observability & Alerting

- Metrics exported via `/metrics`:
  - `arxos_jobs_total{status}`
  - `arxos_job_duration_seconds`
  - `arxos_git_checkout_failures_total`
- Logs aggregated via FluentBit/Vector; include job name, repo, command.
- Alerting examples:
  - High failure rate per command.
  - Long-running jobs exceeding SLA.
  - Git checkout failures due to auth issues.

---

## 9. Example Workflows

### Ad-hoc Job
```yaml
apiVersion: arxos.io/v1alpha1
kind: ArxJob
metadata:
  name: import-hq
spec:
  repo: git@github.com:arx-os/buildings.git
  ref: main
  command: ["arx", "import", "Building-Architecture.ifc", "--output", "hq"]
  artifacts:
    persistentVolumeClaim: arxos-workspace
  timeoutSeconds: 1800
```

### Scheduled Export
```yaml
apiVersion: arxos.io/v1alpha1
kind: ArxSchedule
metadata:
  name: nightly-docs
spec:
  schedule: "0 3 * * *"
  template:
    repo: git@github.com:arx-os/buildings.git
    command: ["arx", "docs", "--building", "HQ", "--output", "docs/hq"]
    artifacts:
      s3:
        bucket: arxos-exports
        prefix: nightly/hq
```

### GitOps Integration
- Store CR definitions in Git repo.
- ArgoCD monitors repository and applies changes.
- Pipeline updates CRs when new buildings/commands added.

---

## 10. CI/CD for Operator

- Build operator container with GitHub Actions (Rust/Go matrix).
- Run unit tests and integration tests (kind/minikube-based).
- Package Helm chart and push to OCI registry (e.g., GHCR).
- Generate CRD schema docs and publish alongside operator release.
- Automated release pipeline signs images and charts (cosign, helm provenance).

---

## 11. Roadmap Extensions

- Multi-cluster coordination (fleet of facilities).
- Integration with message queues (Kafka) to trigger ArxJobs.
- Web UI dashboard showing CR status and artifact history.
- Policy engine (OPA/Gatekeeper) enforcing command allow-lists per tenant.

---

## References

- `docs/development/DOCKER_GUIDE.md` – container usage background.
- `README.md` – CLI quick start (apply to container Jobs).
- `k8s/examples/` – sample manifests referenced above (to be populated).

