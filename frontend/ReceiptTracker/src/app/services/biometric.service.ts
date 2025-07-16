import {Injectable} from '@angular/core';
import {BiometryType, NativeBiometric, BiometricOptions} from 'capacitor-native-biometric';

@Injectable({
  providedIn: 'root'
})
export class BiometricService {

  constructor() { }

  async isBiometricAvailable(): Promise<boolean> {
    try {
      const result = await NativeBiometric.isAvailable();
      return result.isAvailable;
    } catch (error) {
      console.error('Biometric availability check failed:', error);
      return false;
    }
  }

  async getBiometricType(): Promise<BiometryType | null> {
    try {
      const result = await NativeBiometric.isAvailable();
      return result.biometryType || null;
    } catch (error) {
      console.error('Biometric type check failed:', error);
      return null;
    }
  }

  async hasBiometricCredentials(): Promise<boolean> {
    try {
      const credentials = await NativeBiometric.getCredentials({
        server: 'ReceiptTracker'
      });
      return !!(credentials.username && credentials.password);
    } catch (error) {
      console.error('Biometric credentials check failed:', error);
      return false;
    }
  }

  async setCredentials(username: string, password: string): Promise<void> {
    try {
      await NativeBiometric.setCredentials({
        username,
        password,
        server: 'ReceiptTracker'
      });
    } catch (error) {
      console.error('Set biometric credentials failed:', error);
      throw error;
    }
  }

  async verifyIdentity(): Promise<any> {
    try {
      return await NativeBiometric.verifyIdentity({
        reason: 'Bejelentkezés biometrikus azonosítással',
        title: 'Biometrikus azonosítás',
        subtitle: 'Használja ujjlenyomatát vagy arcfelismerést a bejelentkezéshez',
        description: 'Helyezze ujját a szenzorra vagy nézzen a kamerába'
      } as BiometricOptions);
    } catch (error) {
      console.error('Biometric verification failed:', error);
      throw error;
    }
  }

  async getCredentials(): Promise<{username: string, password: string}> {
    try {
      return await NativeBiometric.getCredentials({
        server: 'ReceiptTracker'
      });
    } catch (error) {
      console.error('Get biometric credentials failed:', error);
      throw error;
    }
  }

  async deleteBiometricCredentials(): Promise<void> {
    try {
      await NativeBiometric.deleteCredentials({
        server: 'ReceiptTracker'
      });
    } catch (error) {
      console.error('Delete biometric credentials failed:', error);
      throw error;
    }
  }

  getBiometricTypeDisplayName(biometryType: BiometryType | null): string {
    switch (biometryType) {
      case BiometryType.FINGERPRINT:
        return 'Ujjlenyomat';
      case BiometryType.FACE_ID:
        return 'Arcfelismerés';
      case BiometryType.TOUCH_ID:
        return 'Touch ID';
      case BiometryType.FACE_AUTHENTICATION:
        return 'Arcfelismerés';
      default:
        return 'Biometrikus azonosítás';
    }
  }
}
