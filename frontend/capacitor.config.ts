import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'dev.local.fitfinder',
  appName: 'FitFinder',
  webDir: 'out',
  server: {
    androidScheme: 'https',
    cleartext: true,
    allowNavigation: [
      'http://192.168.1.171:8000',
      'http://10.0.2.2:8000',
      'http://localhost:8000'
    ]
  },
  plugins: {
    CapacitorHttp: {
      enabled: true
    },
    CapacitorCookies: {
      enabled: true
    }
  },
  android: {
    buildOptions: {
      keystorePath: 'fitfinder.keystore',
      keystoreAlias: 'fitfinder'
    },
    allowMixedContent: true,
    captureInput: true,
    webContentsDebuggingEnabled: true
  }
};

export default config;
