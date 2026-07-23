/**
 * useWebSocket Hook
 * Custom hook for WebSocket communication with state management
 */

import { useEffect, useCallback, useRef } from 'react';
import { useAppStore } from '@/store/appStore';
import { getWebSocketService } from '@/services/websocket';
import { config, WS_MESSAGE_TYPES } from '@/config';
import type {
  WebSocketMessage,
  BiometricToken,
  KnowledgePayload,
  TeachingModule,
  UIComponentTree,
  FaceLandmark,
} from '@/types';

interface UseWebSocketOptions {
  sessionId: string;
  autoConnect?: boolean;
  onBiometricToken?: (token: BiometricToken) => void;
  onKnowledgePayload?: (payload: KnowledgePayload) => void;
  onModuleStream?: (module: TeachingModule, index: number, isFirst: boolean) => void;
  onUIUpdate?: (componentTree: UIComponentTree) => void;
  onSessionComplete?: () => void;
  onPipelineStatus?: (step: string, status: string) => void;
  onError?: (error: Error) => void;
}

export function useWebSocket(options: UseWebSocketOptions) {
  const {
    sessionId,
    autoConnect = true,
  } = options;

  const wsServiceRef = useRef(getWebSocketService({ url: config.ws_url }));
  const {
    setWsConnected,
    setBiometricToken,
    setKnowledgePayload,
    setError,
    updateSessionStatus,
  } = useAppStore();

  // Keep callback refs fresh so handleMessage never closes over stale props.
  // This is the canonical fix for stale-closure bugs with event handlers.
  const cbRef = useRef(options);
  useEffect(() => { cbRef.current = options; });

  // Stable message handler — never re-created, always reads latest callbacks via cbRef.
  const handleMessage = useCallback(
    (message: WebSocketMessage) => {
      const cb = cbRef.current;
      console.log('WebSocket message received:', message.type);

      switch (message.type) {
        case WS_MESSAGE_TYPES.BIOMETRIC_TOKEN: {
          const biometricToken = message.data as BiometricToken;
          setBiometricToken(biometricToken);
          cb.onBiometricToken?.(biometricToken);
          updateSessionStatus('analyzing');
          break;
        }

        case WS_MESSAGE_TYPES.MODULE_STREAM: {
          const streamData = message.data;
          const mod = streamData?.module as TeachingModule;
          if (mod) {
            cb.onModuleStream?.(mod, streamData.index ?? 0, streamData.is_first ?? false);
          }
          break;
        }

        case WS_MESSAGE_TYPES.KNOWLEDGE_PAYLOAD: {
          const knowledgePayload = message.data as KnowledgePayload;
          setKnowledgePayload(knowledgePayload);
          cb.onKnowledgePayload?.(knowledgePayload);
          updateSessionStatus('generating_ui');
          break;
        }

        case WS_MESSAGE_TYPES.UI_UPDATE: {
          const uiData = message.data as { component_tree: UIComponentTree };
          if (!uiData.component_tree) {
            console.error('ui_update missing component_tree', message.data);
            setError('Invalid UI configuration received');
            return;
          }
          cb.onUIUpdate?.(uiData.component_tree);
          updateSessionStatus('active');
          break;
        }

        case WS_MESSAGE_TYPES.SESSION_COMPLETE:
          cb.onSessionComplete?.();
          updateSessionStatus('completing');
          break;

        case WS_MESSAGE_TYPES.ERROR: {
          const errorCode = message.data?.error || '';
          const rawMsg = message.data?.message;
          const errorMessage = rawMsg || (errorCode ? `Server error: ${errorCode}` : 'An error occurred. Please try again.');
          console.error('WS error received:', errorMessage, message.data);
          setError(errorMessage);
          cb.onError?.(new Error(errorMessage));
          break;
        }

        case WS_MESSAGE_TYPES.PIPELINE_STATUS:
          if (message.data?.status === 'warming_up') {
            setError('⏳ Server is loading AI models — please wait a moment, then try again.');
          }
          cb.onPipelineStatus?.(message.data?.step ?? '', message.data?.status ?? '');
          break;

        case WS_MESSAGE_TYPES.PIPELINE_COMPLETE:
        case WS_MESSAGE_TYPES.CONNECTION_ESTABLISHED:
          break;

        default:
          console.warn('Unknown message type:', message.type);
      }
    },
    // Stable deps only — store setters never change
    [setBiometricToken, setKnowledgePayload, setError, updateSessionStatus]
  );

  // Handle connection status
  const handleConnection = useCallback(
    (connected: boolean) => {
      console.log('WebSocket connection status:', connected);
      setWsConnected(connected);

      if (connected) {
        updateSessionStatus('active');
      }
    },
    [setWsConnected, updateSessionStatus]
  );

  // Handle errors
  const handleError = useCallback(
    (error: Error) => {
      console.error('WebSocket error:', error);
      const msg = error.message || 'Connection error — please refresh and try again.';
      setError(msg);
      cbRef.current.onError?.(error);
    },
    [setError]
  );

  // Connect to WebSocket
  const connect = useCallback(() => {
    const wsService = wsServiceRef.current;
    wsService.connect(sessionId);
  }, [sessionId]);

  // Ensure the socket is open, reconnecting from scratch if needed.
  // Returns a Promise that resolves once connected (or rejects on timeout).
  const ensureConnected = useCallback((): Promise<void> => {
    const wsService = wsServiceRef.current;
    if (wsService.isConnected()) return Promise.resolve();

    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        unsubscribe();
        reject(new Error('Could not connect to server — is the backend running?'));
      }, 10_000);

      const unsubscribe = wsService.onConnection((connected) => {
        if (connected) {
          clearTimeout(timeout);
          unsubscribe();
          resolve();
        }
      });

      // Force a clean reconnect (resets exhausted retry counter)
      wsService.reconnect(sessionId);
    });
  }, [sessionId]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    const wsService = wsServiceRef.current;
    wsService.disconnect();
  }, []);

  // Send biometric data
  const sendBiometricData = useCallback(
    (landmarks: FaceLandmark[][], frameCount: number) => {
      const wsService = wsServiceRef.current;
      wsService.sendBiometricData(sessionId, landmarks, frameCount);
      updateSessionStatus('analyzing');
    },
    [sessionId, updateSessionStatus]
  );

  // Send knowledge query
  const sendKnowledgeQuery = useCallback(
    (query: string, biometricToken?: BiometricToken) => {
      const wsService = wsServiceRef.current;
      wsService.sendKnowledgeQuery(sessionId, query, biometricToken);
    },
    [sessionId]
  );

  // Send full pipeline request — reconnects automatically if socket is closed
  const sendFullPipeline = useCallback(
    async (query: string, landmarks: FaceLandmark[][], frameCount: number) => {
      const wsService = wsServiceRef.current;
      if (!wsService.isConnected()) {
        try {
          await ensureConnected();
        } catch (err) {
          setError(err instanceof Error ? err.message : 'Connection failed');
          return;
        }
      }
      wsService.sendFullPipeline(sessionId, query, landmarks, frameCount);
      updateSessionStatus('capturing_biometrics');
    },
    [sessionId, updateSessionStatus, ensureConnected, setError]
  );

  // Send engagement signal
  const sendEngagementSignal = useCallback(
    (action: 'understood' | 'confused' | 'need_more' | 'complete') => {
      const wsService = wsServiceRef.current;
      wsService.sendEngagementSignal(action);
    },
    []
  );

  // Setup WebSocket event handlers
  useEffect(() => {
    const wsService = wsServiceRef.current;

    const unsubscribeMessage = wsService.onMessage(handleMessage);
    const unsubscribeConnection = wsService.onConnection(handleConnection);
    const unsubscribeError = wsService.onError(handleError);

    return () => {
      unsubscribeMessage();
      unsubscribeConnection();
      unsubscribeError();
    };
  }, [handleMessage, handleConnection, handleError]);

  // Auto-connect if enabled
  useEffect(() => {
    if (autoConnect && sessionId) {
      connect();
    }

    return () => {
      if (autoConnect) {
        disconnect();
      }
    };
  }, [autoConnect, sessionId, connect, disconnect]);

  return {
    connect,
    disconnect,
    ensureConnected,
    sendBiometricData,
    sendKnowledgeQuery,
    sendFullPipeline,
    sendEngagementSignal,
    isConnected: wsServiceRef.current.isConnected(),
  };
}

// Made with Bob for IBM AI Builders Challenge