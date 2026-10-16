import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {createRequire} from "node:module";

const require = createRequire(import.meta.url);
const {load} = require("js-yaml");
const workflow = load(readFileSync(new URL("../../.github/workflows/pilot-backup.yml", import.meta.url), "utf8"));
const {admission, backup, "alert-failure": alert} = workflow.jobs;
const archive = backup.steps.find(step => step.id === "archive");

test("retain 22:00 Nairobi and budget all three serial scheduled opportunities", () => {
  assert.deepEqual(workflow.on.schedule.map(item => item.cron), ["0 19 * * *", "17 19 * * *", "17 20 * * *"]);
  assert.equal(workflow.concurrency.group, "qinetra-pilot-backup");
  assert.equal(workflow.concurrency["cancel-in-progress"], false);
  assert.equal(Number(archive.env.QLMS_BACKUP_MAX_DAILY_COPIES), workflow.on.schedule.length);
  assert.equal(archive.env.QLMS_BACKUP_RETENTION_DAYS, "90");
  assert.equal(archive.env.QLMS_BACKUP_STORAGE_BUDGET_BYTES, "5000000000");
});

test("public admission cannot access backup secrets or bypass existing main and activation gates", () => {
  assert.equal(admission.environment, undefined);
  assert.equal(JSON.stringify(admission).includes("secrets."), false);
  assert.match(admission.if, /github\.ref == 'refs\/heads\/main'/);
  assert.match(admission.if, /vars\.QLMS_HOSTED_BACKUP_ENABLED == 'true'/);
  assert.match(admission.if, /inputs\.mode == 'qualification'/);
  assert.match(admission.if, /vars\.QLMS_BACKUP_QUALIFICATION_ENABLED == 'true'/);
  assert.equal(backup.needs, "admission");
  assert.equal(backup.if, "needs.admission.outputs.required == 'true'");
  assert.equal(admission.outputs.required, "${{ steps.proof.outputs.required }}");
  assert.equal(backup.environment, "qinetra-pilot-backup");
  assert.deepEqual(workflow.permissions, {contents: "read"});
});

test("all backup jobs use the same immutable operations pin without persisted checkout credentials", () => {
  const checkouts = [admission, backup, alert].map(job => job.steps.find(step => step.uses?.startsWith("actions/checkout@")));
  assert.equal(new Set(checkouts.map(step => step.with.ref)).size, 1);
  for (const step of checkouts) {
    assert.match(step.with.ref, /^[a-f0-9]{40}$/);
    assert.equal(step.with["persist-credentials"], false);
    assert.match(step.uses, /^actions\/checkout@[a-f0-9]{40}$/);
  }
  assert.equal(admission.steps.find(step => step.id === "proof")["working-directory"], "backend");
  assert.match(admission.steps.find(step => step.id === "proof").run, /python -m ops\.backup_schedule --scheduled/);
});

test("catch-ups cannot extend cron-monitor grace or claim success without the archive job", () => {
  const start = backup.steps.find(step => step.name === "Signal start to the independent monitor");
  const complete = backup.steps.find(step => step.name === "Signal verified completion");
  const failure = backup.steps.find(step => step.name === "Signal failure or cancellation");
  assert.equal(start.if, "github.event_name == 'workflow_dispatch' && inputs.mode == 'qualification'");
  assert.equal(complete.if, undefined);
  assert.equal(failure.if, "failure() || cancelled()");
  assert.equal(backup.steps.find(step => step.name === "Require qualified retention before a scheduled run").if,
    "github.event_name == 'schedule' || inputs.mode == 'daily-trigger'");
  assert.equal(backup.steps.some(step => /upload-artifact|actions\/cache/.test(step.uses || "")), false);
});

test("independent dispatch has its own daily gate, validated slot and no fourth ordinary export", () => {
  assert.ok(workflow.on.workflow_dispatch.inputs.mode.options.includes("daily-trigger"));
  assert.equal(workflow.on.workflow_dispatch.inputs.slot.type, "string");
  assert.match(admission.if, /inputs\.mode == 'daily-trigger'/);
  assert.match(admission.if, /vars\.QLMS_INDEPENDENT_BACKUP_ENABLED == 'true'/);
  assert.match(admission.if, /github\.event\.schedule != '17 19 \* \* \*'/);
  const proof = admission.steps.find(step => step.id === "proof");
  assert.equal(proof.env.TRIGGER_SLOT, "${{ inputs.slot }}");
  assert.match(proof.run, /--trigger-slot "\$TRIGGER_SLOT"/);
  assert.match(proof.run, /DAILY_MODE/);
  const summary = admission.steps.find(step => step.name === "Record public trigger and admission decision");
  assert.equal(summary.env.TRIGGER_SLOT, "${{ inputs.slot }}");
  assert.match(summary.run, /TRIGGER_SLOT/);
});
