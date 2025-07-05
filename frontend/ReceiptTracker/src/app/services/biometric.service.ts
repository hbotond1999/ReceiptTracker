import { Injectable } from '@angular/core';
import { NativeBiometric, BiometryType } from 'capacitor-native-biometric';

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