import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'hu.hb.receipttracker',
  appName: 'ReceiptTracker',
  webDir: 'www',
  plugins: {
    Camera: {
      permissions: ['camera']
    }
  },
  // android: { // csak localra a http-t kapcsolja ki
  //   allowMixedContent: true
  // }
};

export default config;
