import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'dev.local.fitfinder',
  appName: 'FitFinder',
  webDir: 'out',
  server: {
    androidScheme: 'https',
    cleartext: true
  },
  plugins: {
    CapacitorHttp: {
      enabled: true
    }
  },
  android: {
    buildOptions: {
      keystorePath: 'fitfinder.keystore',
      keystoreAlias: 'fitfinder'
    }
  }
};

export default config;
