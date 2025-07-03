import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'io.ionic.starter',
  appName: 'ReceiptTracker',
  webDir: 'www',
  plugins: {
    Camera: {
      permissions: ['camera']
    }
  },
  android: {
    allowMixedContent: true
  }
};

export default config;
