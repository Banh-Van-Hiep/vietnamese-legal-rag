// Cấu hình base URL và xử lý lỗi. Nơi duy nhất gọi backend.
const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8080";

export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    throw new Error(`Lỗi ${res.status}: ${await res.text()}`);
  }
  return res.status === 204 ? (undefined as T) : ((await res.json()) as T);
}

export { BASE_URL };
