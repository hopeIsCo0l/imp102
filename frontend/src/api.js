const API = import.meta.env.VITE_API_URL || "http://localhost:18000";

export async function api(path, { method = "GET", token, body, headers = {} } = {}) {
  const resolvedHeaders = {
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...headers
  };
  if (!(body instanceof FormData)) {
    resolvedHeaders["Content-Type"] = "application/json";
  }
  const res = await fetch(`${API}${path}`, {
    method,
    headers: resolvedHeaders,
    body: body
      ? body instanceof FormData
        ? body
        : JSON.stringify(body)
      : undefined
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Request failed");
  }
  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) return res.json();
  return res.blob();
}
