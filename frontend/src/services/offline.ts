/**
 * Offline Mode Service
 * Handles offline functionality and data persistence
 */

import { FEATURES } from '@/config';
import type { Session, KnowledgePayload, BiometricToken } from '@/types';

interface OfflineData {
  sessions: Session[];
  knowledgeCache: Map<string, KnowledgePayload>;
  biometricTokens: BiometricToken[];
  lastSync: string;
}

class OfflineService {
  private enabled: boolean;
  private db: IDBDatabase | null = null;
  private dbName = 'ephemeral-intent-db';
  private dbVersion = 1;

  constructor() {
    this.enabled = FEATURES.OFFLINE_MODE;
    if (this.enabled && typeof window !== 'undefined' && 'indexedDB' in window) {
      this.initializeDB();
      this.registerServiceWorker();
    }
  }

  /**
   * Initialize IndexedDB
   */
  private async initializeDB(): Promise<void> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, this.dbVersion);

      request.onerror = () => {
        console.error('Failed to open IndexedDB:', request.error);
        reject(request.error);
      };

      request.onsuccess = () => {
        this.db = request.result;
        console.log('IndexedDB initialized');
        resolve();
      };

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;

        // Create object stores
        if (!db.objectStoreNames.contains('sessions')) {
          const sessionStore = db.createObjectStore('sessions', { keyPath: 'id' });
          sessionStore.createIndex('created_at', 'created_at', { unique: false });
        }

        if (!db.objectStoreNames.contains('knowledge')) {
          const knowledgeStore = db.createObjectStore('knowledge', { keyPath: 'session_id' });
          knowledgeStore.createIndex('timestamp', 'timestamp', { unique: false });
        }

        if (!db.objectStoreNames.contains('biometrics')) {
          const biometricStore = db.createObjectStore('biometrics', { keyPath: 'session_id' });
          biometricStore.createIndex('timestamp', 'timestamp', { unique: false });
        }

        if (!db.objectStoreNames.contains('queue')) {
          db.createObjectStore('queue', { keyPath: 'id', autoIncrement: true });
        }
      };
    });
  }

  /**
   * Register service worker for offline support
   */
  private async registerServiceWorker(): Promise<void> {
    if ('serviceWorker' in navigator) {
      try {
        const registration = await navigator.serviceWorker.register('/sw.js');
        console.log('Service Worker registered:', registration);
      } catch (error) {
        console.error('Service Worker registration failed:', error);
      }
    }
  }

  /**
   * Save session to offline storage
   */
  async saveSession(session: Session): Promise<void> {
    if (!this.enabled || !this.db) return;

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['sessions'], 'readwrite');
      const store = transaction.objectStore('sessions');
      const request = store.put(session);

      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Get session from offline storage
   */
  async getSession(sessionId: string): Promise<Session | null> {
    if (!this.enabled || !this.db) return null;

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['sessions'], 'readonly');
      const store = transaction.objectStore('sessions');
      const request = store.get(sessionId);

      request.onsuccess = () => resolve(request.result || null);
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Get all sessions
   */
  async getAllSessions(): Promise<Session[]> {
    if (!this.enabled || !this.db) return [];

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['sessions'], 'readonly');
      const store = transaction.objectStore('sessions');
      const request = store.getAll();

      request.onsuccess = () => resolve(request.result || []);
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Save knowledge payload to cache
   */
  async saveKnowledge(payload: KnowledgePayload): Promise<void> {
    if (!this.enabled || !this.db) return;

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['knowledge'], 'readwrite');
      const store = transaction.objectStore('knowledge');
      const request = store.put(payload);

      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Get knowledge payload from cache
   */
  async getKnowledge(sessionId: string): Promise<KnowledgePayload | null> {
    if (!this.enabled || !this.db) return null;

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['knowledge'], 'readonly');
      const store = transaction.objectStore('knowledge');
      const request = store.get(sessionId);

      request.onsuccess = () => resolve(request.result || null);
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Save biometric token
   */
  async saveBiometricToken(token: BiometricToken): Promise<void> {
    if (!this.enabled || !this.db) return;

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['biometrics'], 'readwrite');
      const store = transaction.objectStore('biometrics');
      const request = store.put(token);

      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Queue action for later sync
   */
  async queueAction(action: any): Promise<void> {
    if (!this.enabled || !this.db) return;

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['queue'], 'readwrite');
      const store = transaction.objectStore('queue');
      const request = store.add({
        ...action,
        timestamp: new Date().toISOString(),
        synced: false,
      });

      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Get queued actions
   */
  async getQueuedActions(): Promise<any[]> {
    if (!this.enabled || !this.db) return [];

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['queue'], 'readonly');
      const store = transaction.objectStore('queue');
      const request = store.getAll();

      request.onsuccess = () => {
        const actions = request.result || [];
        resolve(actions.filter((a) => !a.synced));
      };
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Mark action as synced
   */
  async markActionSynced(actionId: number): Promise<void> {
    if (!this.enabled || !this.db) return;

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['queue'], 'readwrite');
      const store = transaction.objectStore('queue');
      const getRequest = store.get(actionId);

      getRequest.onsuccess = () => {
        const action = getRequest.result;
        if (action) {
          action.synced = true;
          const putRequest = store.put(action);
          putRequest.onsuccess = () => resolve();
          putRequest.onerror = () => reject(putRequest.error);
        } else {
          resolve();
        }
      };
      getRequest.onerror = () => reject(getRequest.error);
    });
  }

  /**
   * Sync queued actions when online
   */
  async syncQueuedActions(): Promise<void> {
    if (!navigator.onLine) return;

    const actions = await this.getQueuedActions();
    console.log(`Syncing ${actions.length} queued actions`);

    for (const action of actions) {
      try {
        // TODO: Send action to backend
        // await fetch('/api/sync', {
        //   method: 'POST',
        //   body: JSON.stringify(action),
        // });

        await this.markActionSynced(action.id);
      } catch (error) {
        console.error('Failed to sync action:', error);
      }
    }
  }

  /**
   * Clear old data
   */
  async clearOldData(daysToKeep: number = 7): Promise<void> {
    if (!this.enabled || !this.db) return;

    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - daysToKeep);
    const cutoffTimestamp = cutoffDate.toISOString();

    const stores = ['sessions', 'knowledge', 'biometrics'];

    for (const storeName of stores) {
      const transaction = this.db.transaction([storeName], 'readwrite');
      const store = transaction.objectStore(storeName);
      const index = store.index('timestamp') || store.index('created_at');

      const request = index.openCursor();

      request.onsuccess = (event) => {
        const cursor = (event.target as IDBRequest).result;
        if (cursor) {
          const timestamp = cursor.value.timestamp || cursor.value.created_at;
          if (timestamp < cutoffTimestamp) {
            cursor.delete();
          }
          cursor.continue();
        }
      };
    }
  }

  /**
   * Get storage usage
   */
  async getStorageUsage(): Promise<{ used: number; quota: number }> {
    if ('storage' in navigator && 'estimate' in navigator.storage) {
      const estimate = await navigator.storage.estimate();
      return {
        used: estimate.usage || 0,
        quota: estimate.quota || 0,
      };
    }
    return { used: 0, quota: 0 };
  }

  /**
   * Check if offline mode is enabled
   */
  isEnabled(): boolean {
    return this.enabled;
  }

  /**
   * Check if online
   */
  isOnline(): boolean {
    return navigator.onLine;
  }
}

// Singleton instance
let offlineServiceInstance: OfflineService | null = null;

/**
 * Get offline service instance
 */
export function getOfflineService(): OfflineService {
  if (!offlineServiceInstance) {
    offlineServiceInstance = new OfflineService();
  }
  return offlineServiceInstance;
}

// Setup online/offline event listeners
if (typeof window !== 'undefined') {
  window.addEventListener('online', () => {
    console.log('Back online - syncing queued actions');
    getOfflineService().syncQueuedActions();
  });

  window.addEventListener('offline', () => {
    console.log('Gone offline - enabling offline mode');
  });
}

// Made with Bob for IBM AI Builders Challenge