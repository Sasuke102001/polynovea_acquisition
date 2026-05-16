/**
 * chat-api.ts
 * Client-side streaming wrapper for Polynovea venue intelligence AI.
 */

// Empty base → relative URLs. Vercel rewrites /api/* → EC2 backend (no mixed-content).
const API_BASE = "";

export interface ChatStreamOptions {
  onChunk: (chunk: string) => void;
  onError?: (error: string) => void;
  onComplete?: () => void;
}

/**
 * Stream chat response from backend.
 * Passes raw decoded chunks directly — no newline splitting — so markdown
 * formatting from the AI is preserved exactly as sent.
 */
export async function streamChat(
  venueId: number,
  tab: string,
  question: string,
  options: ChatStreamOptions,
): Promise<void> {
  let response: Response;

  try {
    response = await fetch(`${API_BASE}/api/venues/${venueId}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ tab, question }),
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

    // Flush any remaining bytes
    const tail = decoder.decode();
    if (tail) options.onChunk(tail);

    options.onComplete?.();
  } catch (err) {
    // Stream dropped mid-response — surface a clean message, not a raw error
    const msg = err instanceof Error ? err.message : "Stream interrupted";
    options.onError?.(msg);
  } finally {
    reader.releaseLock();
  }
}
