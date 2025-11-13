/**
 * Reconnection logic with exponential backoff
 */

export interface ReconnectConfig {
  initialDelay: number;
  maxDelay: number;
  maxAttempts: number;
  backoffMultiplier: number;
  jitter: boolean;
}

export const DEFAULT_RECONNECT_CONFIG: ReconnectConfig = {
  initialDelay: 1000, // 1 second
  maxDelay: 30000, // 30 seconds
  maxAttempts: 10,
  backoffMultiplier: 2,
  jitter: true,
};

export class ReconnectManager {
  private attempts = 0;
  private config: ReconnectConfig;
  private reconnectTimeout?: NodeJS.Timeout;

  constructor(config: Partial<ReconnectConfig> = {}) {
    this.config = { ...DEFAULT_RECONNECT_CONFIG, ...config };
  }

  /**
   * Calculate the next reconnect delay using exponential backoff
   */
  calculateDelay(): number {
    const { initialDelay, maxDelay, backoffMultiplier, jitter } = this.config;

    // Exponential backoff: initialDelay * (backoffMultiplier ^ attempts)
    let delay = initialDelay * Math.pow(backoffMultiplier, this.attempts);

    // Cap at maxDelay
    delay = Math.min(delay, maxDelay);

    // Add jitter to prevent thundering herd
    if (jitter) {
      const jitterAmount = delay * 0.3; // ±30% jitter
      delay = delay + (Math.random() * 2 - 1) * jitterAmount;
    }

    return Math.floor(delay);
  }

  /**
   * Schedule a reconnect attempt
   */
  scheduleReconnect(callback: () => void): void {
    if (this.attempts >= this.config.maxAttempts) {
      throw new Error(
        `Max reconnect attempts (${this.config.maxAttempts}) exceeded`
      );
    }

    const delay = this.calculateDelay();
    this.attempts++;

    this.reconnectTimeout = setTimeout(() => {
      callback();
    }, delay);
  }

  /**
   * Cancel pending reconnect
   */
  cancel(): void {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = undefined;
    }
  }

  /**
   * Reset attempts counter (call after successful connection)
   */
  reset(): void {
    this.attempts = 0;
    this.cancel();
  }

  /**
   * Get current attempt count
   */
  getAttempts(): number {
    return this.attempts;
  }

  /**
   * Check if max attempts reached
   */
  isMaxed(): boolean {
    return this.attempts >= this.config.maxAttempts;
  }
}

/**
 * Calculate connection quality based on latency
 */
export function calculateConnectionQuality(
  latency: number
): "excellent" | "good" | "poor" | "offline" {
  if (latency < 0) return "offline";
  if (latency < 100) return "excellent";
  if (latency < 500) return "good";
  return "poor";
}

/**
 * Create a timeout promise that rejects after a specified duration
 */
export function withTimeout<T>(
  promise: Promise<T>,
  timeoutMs: number,
  errorMessage = "Operation timed out"
): Promise<T> {
  return Promise.race([
    promise,
    new Promise<T>((_, reject) =>
      setTimeout(() => reject(new Error(errorMessage)), timeoutMs)
    ),
  ]);
}
