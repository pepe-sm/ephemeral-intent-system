/**
 * Analytics Service
 * Tracks user interactions and system performance
 */

import { ANALYTICS_CONFIG } from '@/config';

export interface AnalyticsEvent {
  category: string;
  action: string;
  label?: string;
  value?: number;
  metadata?: Record<string, any>;
}

export interface PerformanceMetric {
  name: string;
  value: number;
  unit: 'ms' | 'bytes' | 'count';
  timestamp: string;
}

class AnalyticsService {
  private enabled: boolean;
  private queue: AnalyticsEvent[] = [];
  private sessionId: string;
  private startTime: number;

  constructor() {
    this.enabled = ANALYTICS_CONFIG.enabled;
    this.sessionId = this.generateSessionId();
    this.startTime = Date.now();

    if (this.enabled) {
      this.initializeAnalytics();
    }
  }

  /**
   * Initialize analytics tracking
   */
  private initializeAnalytics(): void {
    // Track page load
    this.trackEvent({
      category: 'System',
      action: 'PageLoad',
      label: window.location.pathname,
    });

    // Track performance metrics
    if (window.performance && window.performance.timing) {
      window.addEventListener('load', () => {
        setTimeout(() => this.trackPerformanceMetrics(), 0);
      });
    }

    // Track errors
    window.addEventListener('error', (event) => {
      this.trackError(event.error);
    });

    // Track unhandled promise rejections
    window.addEventListener('unhandledrejection', (event) => {
      this.trackError(event.reason);
    });

    // Flush queue before page unload
    window.addEventListener('beforeunload', () => {
      this.flush();
    });
  }

  /**
   * Generate unique session ID
   */
  private generateSessionId(): string {
    return `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Track an event
   */
  trackEvent(event: AnalyticsEvent): void {
    if (!this.enabled) return;

    const enrichedEvent = {
      ...event,
      sessionId: this.sessionId,
      timestamp: new Date().toISOString(),
      url: window.location.href,
      userAgent: navigator.userAgent,
    };

    this.queue.push(enrichedEvent);

    // Send if queue is large enough
    if (this.queue.length >= 10) {
      this.flush();
    }

    // Log in development
    if (import.meta.env.DEV) {
      console.log('[Analytics]', enrichedEvent);
    }
  }

  /**
   * Track biometric capture
   */
  trackBiometricCapture(duration: number, framesProcessed: number): void {
    this.trackEvent({
      category: 'Biometric',
      action: 'CaptureComplete',
      label: 'BiometricCapture',
      value: duration,
      metadata: {
        framesProcessed,
        fps: framesProcessed / duration,
      },
    });
  }

  /**
   * Track knowledge query
   */
  trackKnowledgeQuery(query: string, responseTime: number): void {
    this.trackEvent({
      category: 'Knowledge',
      action: 'QuerySubmitted',
      label: query.substring(0, 100), // Truncate for privacy
      value: responseTime,
    });
  }

  /**
   * Track module completion
   */
  trackModuleCompletion(moduleId: string, timeSpent: number): void {
    this.trackEvent({
      category: 'Learning',
      action: 'ModuleCompleted',
      label: moduleId,
      value: timeSpent,
    });
  }

  /**
   * Track user engagement
   */
  trackEngagement(action: 'understood' | 'confused' | 'need_more' | 'complete'): void {
    this.trackEvent({
      category: 'Engagement',
      action: 'UserFeedback',
      label: action,
    });
  }

  /**
   * Track error
   */
  trackError(error: Error | any): void {
    this.trackEvent({
      category: 'Error',
      action: 'ErrorOccurred',
      label: error?.message || 'Unknown error',
      metadata: {
        stack: error?.stack,
        name: error?.name,
      },
    });
  }

  /**
   * Track performance metrics
   */
  private trackPerformanceMetrics(): void {
    const timing = window.performance.timing;
    const metrics: PerformanceMetric[] = [
      {
        name: 'PageLoadTime',
        value: timing.loadEventEnd - timing.navigationStart,
        unit: 'ms',
        timestamp: new Date().toISOString(),
      },
      {
        name: 'DOMContentLoaded',
        value: timing.domContentLoadedEventEnd - timing.navigationStart,
        unit: 'ms',
        timestamp: new Date().toISOString(),
      },
      {
        name: 'TimeToFirstByte',
        value: timing.responseStart - timing.navigationStart,
        unit: 'ms',
        timestamp: new Date().toISOString(),
      },
    ];

    metrics.forEach((metric) => {
      this.trackEvent({
        category: 'Performance',
        action: metric.name,
        value: metric.value,
        metadata: { unit: metric.unit },
      });
    });
  }

  /**
   * Track custom metric
   */
  trackMetric(metric: PerformanceMetric): void {
    this.trackEvent({
      category: 'Metric',
      action: metric.name,
      value: metric.value,
      metadata: { unit: metric.unit },
    });
  }

  /**
   * Flush queued events
   */
  private flush(): void {
    if (this.queue.length === 0) return;

    // In a real implementation, send to analytics backend
    // For now, we'll just log and clear
    if (import.meta.env.DEV) {
      console.log('[Analytics] Flushing queue:', this.queue.length, 'events');
    }

    // TODO: Send to analytics service
    // fetch('/api/analytics', {
    //   method: 'POST',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify(this.queue),
    // });

    this.queue = [];
  }

  /**
   * Get session duration
   */
  getSessionDuration(): number {
    return Date.now() - this.startTime;
  }

  /**
   * Get session ID
   */
  getSessionId(): string {
    return this.sessionId;
  }

  /**
   * Enable/disable analytics
   */
  setEnabled(enabled: boolean): void {
    this.enabled = enabled;
  }

  /**
   * Check if analytics is enabled
   */
  isEnabled(): boolean {
    return this.enabled;
  }
}

// Singleton instance
let analyticsInstance: AnalyticsService | null = null;

/**
 * Get analytics service instance
 */
export function getAnalyticsService(): AnalyticsService {
  if (!analyticsInstance) {
    analyticsInstance = new AnalyticsService();
  }
  return analyticsInstance;
}

/**
 * Convenience function to track events
 */
export function trackEvent(event: AnalyticsEvent): void {
  getAnalyticsService().trackEvent(event);
}

/**
 * Convenience function to track errors
 */
export function trackError(error: Error | any): void {
  getAnalyticsService().trackError(error);
}

// Made with Bob for IBM AI Builders Challenge