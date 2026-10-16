// Dispatch only; archive verification and monitor success stay in the protected GitHub job.
export default {
  async scheduled(controller, env) {
    const slot = new Date(controller.scheduledTime).toISOString().replace(".000Z", "Z");
    if (controller.cron !== "0 19 * * *" || !slot.endsWith("T19:00:00Z")) {
      throw new Error("Invalid backup trigger");
    }
    if (!env.GITHUB_BACKUP_DISPATCH) throw new Error("Missing backup dispatch credential");
    let response;
    try {
      response = await fetch("https://api.github.com/repos/1ann0/Qinetra-Laundry-Management-System/actions/workflows/pilot-backup.yml/dispatches", {
        method: "POST",
        redirect: "error",
        signal: AbortSignal.timeout(20000),
        headers: {
          Authorization: `Bearer ${env.GITHUB_BACKUP_DISPATCH}`,
          Accept: "application/vnd.github+json",
          "Content-Type": "application/json",
          "User-Agent": "QLMS-backup-trigger",
          "X-GitHub-Api-Version": "2026-03-10",
        },
        body: JSON.stringify({ref: "main", inputs: {mode: "daily-trigger", slot}}),
      });
    } catch {
      throw new Error("Backup dispatch failed");
    }
    await response.body?.cancel();
    if (response.status !== 200 && response.status !== 204) {
      throw new Error(`Backup dispatch rejected (${response.status})`);
    }
  },
};
