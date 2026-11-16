export type Row = Record<string, any>;
export async function api(
  path: string,
  method = "GET",
  body?: unknown,
): Promise<any> {
  const res = await fetch("/api" + path, {
    method,
    credentials: "include",
    headers:
      body instanceof FormData ? {} : { "Content-Type": "application/json" },
    body:
      body instanceof FormData
        ? body
        : body === undefined
          ? undefined
          : JSON.stringify(body),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(
      typeof data.detail === "string"
        ? data.detail
        : JSON.stringify(data.detail),
    );
  }
  return res.json();
}
export async function upload(file: File) {
  const data = new FormData();
  data.append("file", file);
  return api("/files", "POST", data);
}
export const money = (c: number) =>
  new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
  }).format(c / 100);
export const date = (s: string) =>
  s
    ? new Date(s).toLocaleDateString("en-IN", {
        day: "numeric",
        month: "short",
        year: "numeric",
      })
    : "Not scheduled";
export const short = (s: string) => "YEP-" + s.slice(0, 8).toUpperCase();
