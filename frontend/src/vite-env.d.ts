/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_BACKEND_HOST: string;
  readonly VITE_BACKEND_PORT: string;
  readonly VITE_BACKEND_PROTOCOL: string;
  readonly VITE_WS_PROTOCOL: string;
  readonly VITE_BIOMETRIC_DURATION: string;
  readonly VITE_BIOMETRIC_FPS: string;
  readonly VITE_ENABLE_VOICE: string;
  readonly VITE_FEATURE_OFFLINE: string;
  readonly VITE_FEATURE_ANALYTICS: string;
  readonly VITE_ANALYTICS_ID: string;
  readonly VITE_ANALYTICS_SAMPLE_RATE: string;
  readonly MODE: string;
  readonly PROD: boolean;
  readonly DEV: boolean;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

// Made with Bob
