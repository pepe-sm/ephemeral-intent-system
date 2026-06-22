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
  UIComponentTree,
  FaceLandmark,
} from '@/types';

interface UseWebSocketOptions {
  sessionId: string;
  autoConnect?: boolean;
  onBiometricToken?: (token: BiometricToken) => void;
  onKnowledgePayload?: (payload: KnowledgePayload) => void;
  onUIUpdate?: (componentTree: UIComponentTree) => void;
  onSessionComplete?: () => void;
  onError?: (error: Error) => void;
}

export function useWebSocket(options: UseWebSocketOptions) {
  const {
    sessionId,
    autoConnect = true,
    onBiometricToken,
    onKnowledgePayload,
    onUIUpdate,
    onSessionComplete,
    onError,
  } = options;

  const wsServiceRef = useRef(getWebSocketService({ url: config.ws_url }));
  const {
    setWsConnected,
    setBiometricToken,
    setKnowledgePayload,
    setError,
    updateSessionStatus,
  } = useAppStore();

  // Handle incoming messages
  const handleMessage = useCallback(
    (message: WebSocketMessage) => {
      console.log('WebSocket message received:', message.type);

      switch (message.type) {
        case WS_MESSAGE_TYPES.BIOMETRIC_TOKEN:
          const biometricToken = message.data as BiometricToken;
          setBiometricToken(biometricToken);
          onBiometricToken?.(biometricToken);
          updateSessionStatus('analyzing');
          break;

        case WS_MESSAGE_TYPES.KNOWLEDGE_PAYLOAD:
          const knowledgePayload = message.data as KnowledgePayload;
          setKnowledgePayload(knowledgePayload);
          onKnowledgePayload?.(knowledgePayload);
          updateSessionStatus('generating_ui');
          break;

        case WS_MESSAGE_TYPES.UI_UPDATE:
          const uiData = message.data as { component_tree: UIComponentTree };
          onUIUpdate?.(uiData.component_tree);
          updateSessionStatus('active');
          break;

        case WS_MESSAGE_TYPES.SESSION_COMPLETE:
          onSessionComplete?.();
          updateSessionStatus('completing');
          break;

        case WS_MESSAGE_TYPES.ERROR:
          const errorMessage = message.data?.message || 'Unknown error occurred';
          setError(errorMessage);
          onError?.(new Error(errorMessage));
          break;

        default:
          console.warn('Unknown message type:', message.type);
      }
    },
    [
      setBiometricToken,
      setKnowledgePayload,
      setError,
      updateSessionStatus,
      onBiometricToken,
      onKnowledgePayload,
      onUIUpdate,
      onSessionComplete,
      onError,
    ]
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
      setError(error.message);
      onError?.(error);
    },
    [setError, onError]
  );

  // Connect to WebSocket
  const connect = useCallback(() => {
    const wsService = wsServiceRef.current;
    wsService.connect(sessionId);
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

  // Send full pipeline request
  const sendFullPipeline = useCallback(
    (query: string, landmarks: FaceLandmark[][], frameCount: number) => {
      const wsService = wsServiceRef.current;
      wsService.sendFullPipeline(sessionId, query, landmarks, frameCount);
      updateSessionStatus('capturing_biometrics');
    },
    [sessionId, updateSessionStatus]
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
    sendBiometricData,
    sendKnowledgeQuery,
    sendFullPipeline,
    sendEngagementSignal,
    isConnected: wsServiceRef.current.isConnected(),
  };
}

// Made with Bob for IBM AI Builders Challenge