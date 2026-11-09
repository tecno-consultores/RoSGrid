/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

type WebFigDynamic = ReturnType<typeof JSON.parse>;
type WebFigRecord = Record<string, WebFigDynamic>;
