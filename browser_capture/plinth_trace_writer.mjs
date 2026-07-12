// Repo-local writer for the Plinth synthetic-emr trajectory contract.
//
// This is a STANDALONE re-implementation of the record shapes + on-disk layout
// defined by the Plinth source (READ-ONLY, never imported/edited here):
//   - tools/plinth-app/workers/lib/capture-trace.ts  (RunHeader/StepRecord/
//     ArtifactRecord, TraceWriter, runDir/tracePath, sha256Hex, writeLegacyOnly)
//   - tools/plinth-app/lib/storage/obj-key.ts         (runArtifactKey shape)
//   - tools/plinth-app/lib/storage/drivers/hetzner-native.ts (disk mapping the
//     reader's resolveFile() uses)
//
// It writes byte-for-byte where the EXISTING Plinth reader (read-trace.ts) and
// replay harness consume runs, so the emitted run loads unchanged:
//   trace file : $HOME/clawd/state/projects/synthetic-emr-demo/runs/<runId>/trace.jsonl
//   artifact   : $HOME/clawd/state/projects/synthetic-emr-demo/runs/<runId>/<step_id>/<leaf>
//   storage_key: t/<tenant>/p/synthetic-emr-demo/runs/<runId>/<step_id>/<leaf>
//                (HetznerNativeDriver maps runId+nodeId(step_id)+artifact -> the
//                 disk path above, so resolveFile(storage_key) round-trips)
//
// Nothing here reaches a DB or the cloud; it appends to a plain JSONL file and
// writes artifact bytes atomically (mkdir -p -> tmp -> rename), exactly like the
// Plinth writeLegacyOnly the reader is paired with.

import { promises as fs } from "node:fs";
import path from "node:path";
import { createHash, randomBytes } from "node:crypto";

export const PROJECT_SLUG = "synthetic-emr-demo";
export const SCHEMA_VERSION = 2;

const HOME = process.env.HOME ?? "/home/clawd";
const STATE_ROOT_PROJECTS = path.join(HOME, "clawd", "state", "projects");

// Mirror of Plinth createId("run"|"step"|...) = `${prefix}_${randomBytes(6).hex}`
// which yields a 12-hex suffix; the reader's isSafeRunId requires run_[a-f0-9]{12}.
export function createId(prefix) {
  if (!/^[a-z][a-z0-9_]*$/.test(prefix)) throw new Error(`invalid_id_prefix:${prefix}`);
  return `${prefix}_${randomBytes(6).toString("hex")}`;
}

export function runDir(runId) {
  return path.join(STATE_ROOT_PROJECTS, PROJECT_SLUG, "runs", runId);
}

export function tracePath(runId) {
  return path.join(runDir(runId), "trace.jsonl");
}

export function sha256Hex(body) {
  return createHash("sha256").update(body).digest("hex");
}

export function nowIso() {
  return new Date().toISOString();
}

// Same canonical run-artifact object key Plinth's runArtifactKey mints:
//   t/<tenant_id>/p/<project_slug>/runs/<runId>/<nodeId>/<artifact>
// with nodeId = step_id. Re-validates the tenant/slug the way obj-key.ts does.
const TENANT_ID_RE = /^tnt_[a-f0-9]{12}$/;
const PROJECT_SLUG_RE = /^[a-z0-9][a-z0-9_-]{0,62}$/;
export function runArtifactKey(tenantId, projectSlug, runId, nodeId, artifactName) {
  if (!TENANT_ID_RE.test(tenantId)) throw new Error(`invalid_tenant_id:${tenantId}`);
  if (!PROJECT_SLUG_RE.test(projectSlug)) throw new Error(`invalid_project_slug:${projectSlug}`);
  if (!runId || runId.includes("/") || runId.length > 64) throw new Error(`invalid_run_id:${runId}`);
  if (!nodeId || nodeId.includes("/") || nodeId.length > 64) throw new Error(`invalid_node_id:${nodeId}`);
  if (!artifactName || /[/\0]/.test(artifactName) || artifactName.includes("..")) {
    throw new Error(`invalid_leaf:${artifactName}`);
  }
  return `t/${tenantId}/p/${projectSlug}/runs/${runId}/${nodeId}/${artifactName}`;
}

async function writeLegacyOnly(absPath, body) {
  await fs.mkdir(path.dirname(absPath), { recursive: true });
  const tmp = `${absPath}.tmp.${process.pid}`;
  await fs.writeFile(tmp, body);
  await fs.rename(tmp, absPath);
}

const ARTIFACT_LEAVES = {
  screenshot: "screenshot.png",
  dom: "dom.html",
  elements: "elements.json",
};

export class TraceWriter {
  constructor(runId, tenantId, workflowId, captureVersion) {
    this.runId = runId;
    this.tenantId = tenantId;
    this.workflowId = workflowId;
    this.captureVersion = captureVersion;
    this.file = tracePath(runId);
  }

  static async createRun({ tenantId, workflowId, captureVersion }) {
    const runId = createId("run");
    const w = new TraceWriter(runId, tenantId, workflowId, captureVersion);
    await fs.mkdir(runDir(runId), { recursive: true });
    const header = {
      kind: "run",
      run_id: runId,
      tenant_id: tenantId,
      project_slug: PROJECT_SLUG,
      workflow_id: workflowId,
      capture_version: captureVersion,
      started_at: nowIso(),
    };
    await fs.writeFile(w.file, JSON.stringify(header) + "\n");
    return w;
  }

  async appendStep(fields) {
    const rec = {
      kind: "step",
      step_id: createId("step"),
      run_id: this.runId,
      tenant_id: this.tenantId,
      workflow_id: this.workflowId,
      task_id: null,
      step_idx: fields.step_idx,
      actor: "agent",
      step_type: "browser_action",
      phase: fields.phase,
      subgoal: fields.subgoal,
      ts_start: fields.ts_start,
      ts_end: fields.ts_end,
      observation: fields.observation ?? null,
      decision: fields.decision ?? null,
      action: fields.action ?? null,
      result: fields.result ?? null,
      labels: fields.labels ?? null,
      privacy: fields.privacy ?? { phi_status: "synthetic" },
      schema_version: SCHEMA_VERSION,
      capture_version: this.captureVersion,
    };
    await this.#appendLine(rec);
    return rec;
  }

  async appendArtifact(fields) {
    const rec = {
      kind: "artifact",
      artifact_id: createId("art"),
      run_id: this.runId,
      tenant_id: this.tenantId,
      step_id: fields.step_id,
      step_idx: fields.step_idx,
      storage_key: fields.storage_key,
      artifact_type: fields.artifact_type,
      sha256: fields.sha256,
      byte_size: fields.byte_size,
      created_at: nowIso(),
    };
    await this.#appendLine(rec);
    return rec;
  }

  // Persist one artifact's bytes to the HetznerNativeDriver disk path AND append
  // the record, minting the same storage_key the Plinth reader resolves.
  async persistArtifact(stepId, stepIdx, type, body) {
    const leaf = ARTIFACT_LEAVES[type];
    if (!leaf) throw new Error(`unknown artifact_type:${type}`);
    const storageKey = runArtifactKey(this.tenantId, PROJECT_SLUG, this.runId, stepId, leaf);
    const absPath = path.join(runDir(this.runId), stepId, leaf);
    await writeLegacyOnly(absPath, body);
    return this.appendArtifact({
      step_id: stepId,
      step_idx: stepIdx,
      storage_key: storageKey,
      artifact_type: type,
      sha256: sha256Hex(body),
      byte_size: body.byteLength,
    });
  }

  async #appendLine(rec) {
    await fs.appendFile(this.file, JSON.stringify(rec) + "\n");
  }
}
