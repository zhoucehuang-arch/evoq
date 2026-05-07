"use server";

type RedirectTargets = {
  success: string;
  failurePrefix: string;
  unavailable: string;
};

const API_BASE_URL = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000").replace(/\/$/, "");
const DASHBOARD_API_TOKEN = (process.env.QE_DASHBOARD_API_TOKEN ?? "").trim();

export async function postDashboardJson(path: string, payload: unknown): Promise<Response> {
  return fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(DASHBOARD_API_TOKEN ? { "X-Quant-Evo-Dashboard-Token": DASHBOARD_API_TOKEN } : {}),
    },
    body: JSON.stringify(payload),
    cache: "no-store",
  });
}

export async function redirectTargetForPost(
  path: string,
  payload: unknown,
  targets: RedirectTargets,
): Promise<string> {
  try {
    const response = await postDashboardJson(path, payload);
    return response.ok ? targets.success : `${targets.failurePrefix}${response.status}`;
  } catch {
    return targets.unavailable;
  }
}
