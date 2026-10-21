export class ApiError extends Error {
  constructor(public status: number, public statusText: string, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

export class ApiClient {
  constructor(private baseUrl: string) {}

  setBaseUrl(url: string) {
    this.baseUrl = url.replace(/\/+$/, '');
  }

  async get<T>(path: string, params?: Record<string, string>): Promise<T> {
    let url = `${this.baseUrl}${path}`;
    if (params) {
      const search = new URLSearchParams(
        Object.entries(params).filter(([, v]) => v !== undefined && v !== '')
      );
      if (search.toString()) url += `?${search}`;
    }
    return this._fetch<T>(url, { method: 'GET' });
  }

  async post<T>(path: string, body?: unknown): Promise<T> {
    return this._fetch<T>(`${this.baseUrl}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  }

  async delete<T>(path: string): Promise<T> {
    return this._fetch<T>(`${this.baseUrl}${path}`, { method: 'DELETE' });
  }

  private async _fetch<T>(url: string, init: RequestInit): Promise<T> {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 10_000);
    try {
      const res = await fetch(url, { ...init, signal: controller.signal });
      if (!res.ok) {
        let msg = res.statusText;
        try {
          const body = await res.json();
          msg = body.detail || body.message || msg;
        } catch { /* ignore */ }
        throw new ApiError(res.status, res.statusText, msg);
      }
      return (await res.json()) as T;
    } catch (err) {
      if (err instanceof ApiError) throw err;
      if (err instanceof DOMException && err.name === 'AbortError')
        throw new ApiError(0, 'Timeout', 'Request timed out');
      throw new ApiError(0, 'NetworkError', err instanceof Error ? err.message : 'Network error');
    } finally {
      clearTimeout(timeout);
    }
  }
}
