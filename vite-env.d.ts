/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE?: string;
  // tambahkan environment variables lain di sini jika perlu
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}