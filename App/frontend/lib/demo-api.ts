/**
 * demo-api.ts
 * Client-side API helpers for demo mode (JWT-gated shareable links).
 */

const API_BASE = "";

export interface VenueMetadata {
  venue_id: number;
  prospect_name: string;
  expires_at: string;
  venue_name: string;
  venue_area: string;
  venue_city: string;
  demo_level: number;
  demo_mode: string;
}

export interface DemoVerifyError {
  status: number;   // 410 = expired, 401 = invalid, 404 = venue not found
  detail: string;
}

/**
 * Verify a demo token and return venue metadata.
 * Returns null + error on any failure.
 */
export async function verifyDemoToken(
  token: string,
): Promise<{ data: VenueMetadata | null; error: DemoVerifyError | null }> {
  try {
    const res = await fetch(`${API_BASE}/api/demo/verify/${token}`);
    if (!res.ok) {
      let detail = `Server error ${res.status}`;
      try {
        const body = await res.json();
        detail = body.detail ?? detail;
      } catch {
        // ignore parse error
      }
      return { data: null, error: { status: res.status, detail } };
    }
    const data = (await res.json()) as VenueMetadata;
    return { data, error: null };
  } catch {
    return {
      data: null,
      error: { status: 0, detail: "Could not reach the server. Check your connection." },
    };
  }
}

export interface ChatStreamOptions {
  onChunk: (chunk: string) => void;
  onError?: (error: string) => void;
  onComplete?: () => void;
}

/**
 * Stream a demo chat response.
 * Same SSE pattern as the main chat but hits /api/demo/{token}/chat.
 */
export async function streamDemoChat(
  token: string,
  question: string,
  options: ChatStreamOptions,
): Promise<void> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}/api/demo/${token}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
  } catch {
    options.onError?.("Could not reach the server. Check your connection.");
    return;
  }

  if (!response.ok) {
    try {
      const err = await response.json();
      options.onError?.(err.detail ?? `Server error ${response.status}`);
    } catch {
      options.onError?.(`Server error ${response.status}`);
    }
    return;
  }

  const reader = response.body?.getReader();
  if (!reader) {
    options.onError?.("No response body from server.");
    return;
  }

  const decoder = new TextDecoder();
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const chunk = decoder.decode(value, { stream: true });
      if (chunk) options.onChunk(chunk);
    }
    const tail = decoder.decode();
    if (tail) options.onChunk(tail);
    options.onComplete?.();
  } catch (err) {
    const msg = err instanceof Error ? err.message : "Stream interrupted";
    options.onError?.(msg);
  } finally {
    reader.releaseLock();
  }
}
