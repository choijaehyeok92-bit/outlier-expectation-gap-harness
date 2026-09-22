import type { NextConfig } from 'next';

const config: NextConfig = {
  // The API is a separate FastAPI service; the browser talks to it directly so
  // the harness never has to run inside the Node process.
  env: { NEXT_PUBLIC_API_BASE: process.env.NEXT_PUBLIC_API_BASE ?? 'http://localhost:8000' },
};

export default config;
