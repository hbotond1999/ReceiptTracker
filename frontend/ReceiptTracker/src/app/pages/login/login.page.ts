import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, FormsModule, Validators } from '@angular/forms';
import { Store } from '@ngrx/store';
import { login, biometricLogin, enableBiometric } from '../../store/auth/auth.actions';
import { selectAuthError, selectAuthLoading, selectIsAuthenticated } from '../../store/auth/auth.selectors';
import { IonContent, IonHeader, IonTitle, IonToolbar, IonInput, IonButton, IonItem, IonLabel, IonSpinner, IonIcon, IonCheckbox, IonToast, IonAlert } from '@ionic/angular/standalone';
import { CommonModule } from '@angular/common';
import { Observable } from 'rxjs';
import { Router } from '@angular/router';
import { BiometricService } from '../../services/biometric.service';
import { BiometryType } from 'capacitor-native-biometric';
import { addIcons } from 'ionicons';
import { fingerPrint, eye, checkmark } from 'ionicons/icons';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    FormsModule,
    IonContent,
    IonHeader,
    IonTitle,
    IonToolbar,
    IonInput,
    IonButton,
    IonItem,
    IonLabel,
    IonSpinner,
    IonIcon,
    IonCheckbox,
    IonToast,
    IonAlert
  ],
  templateUrl: './login.page.html',
  styleUrls: ['./login.page.scss']
})
export class LoginPage implements OnInit {
  form: FormGroup;
  loading$: Observable<boolean>;
  error$: Observable<string | null>;
  
  // Biometric properties
  biometricAvailable = false;
  biometricType: BiometryType | null = null;
  biometricTypeDisplayName = '';
  hasBiometricCredentials = false;
  enableBiometricAfterLogin = false;
  
  // Toast and alert states
  showSuccessToast = false;
  showErrorToast = false;
  showBiometricAlert = false;
  toastMessage = '';
  biometricAlertButtons = [
    {
      text: 'Törlés',
      role: 'destructive',
      handler: () => {
        this.removeBiometricCredentials();
      }
    },
    {
      text: 'Mégse',
      role: 'cancel'
    }
  ];

  constructor(
    private fb: FormBuilder, 
    private store: Store, 
    private router: Router,
    private biometricService: BiometricService
  ) {
    addIcons({ fingerPrint, eye, checkmark });
    
    this.form = this.fb.group({
      username: ['', Validators.required],
      password: ['', Validators.required]
    });
    this.loading$ = this.store.select(selectAuthLoading);
    this.error$ = this.store.select(selectAuthError);

    this.store.select(selectIsAuthenticated).subscribe(isAuth => {
      if (isAuth) {
        this.router.navigate(['home']);
      }
    });
  }

  async ngOnInit() {
    await this.checkBiometricAvailability();
  }

  async checkBiometricAvailability() {
    this.biometricAvailable = await this.biometricService.isBiometricAvailable();
    if (this.biometricAvailable) {
      this.biometricType = await this.biometricService.getBiometricType();
      this.biometricTypeDisplayName = this.biometricService.getBiometricTypeDisplayName(this.biometricType);
      this.hasBiometricCredentials = await this.biometricService.hasBiometricCredentials();
    }
  }

  submit() {
    if (this.form.valid) {
      const { username, password } = this.form.value;
      this.store.dispatch(login({ username, password }));
      
      // If biometric is available and user wants to enable it
      if (this.biometricAvailable && this.enableBiometricAfterLogin) {
        this.store.dispatch(enableBiometric({ username, password }));
      }
    } else {
      this.form.markAllAsTouched();
    }
  }

  async biometricLogin() {
    if (!this.biometricAvailable || !this.hasBiometricCredentials) {
      this.showToast('Biometrikus azonosítás nem érhető el', 'danger');
      return;
    }
    
    this.store.dispatch(biometricLogin());
  }

  onEnableBiometricChange(event: any) {
    this.enableBiometricAfterLogin = event.detail.checked;
  }

  showBiometricSetupAlert() {
    this.showBiometricAlert = true;
  }

  async removeBiometricCredentials() {
    try {
      await this.biometricService.deleteBiometricCredentials();
      this.hasBiometricCredentials = false;
      this.showToast('Biometrikus adatok törölve', 'success');
    } catch (error) {
      this.showToast('Hiba a biometrikus adatok törlése során', 'danger');
    }
  }

  private showToast(message: string, color: 'success' | 'danger') {
    this.toastMessage = message;
    if (color === 'success') {
      this.showSuccessToast = true;
    } else {
      this.showErrorToast = true;
    }
  }

  getBiometricIcon(): string {
    switch (this.biometricType) {
      case BiometryType.FACE_ID:
      case BiometryType.FACE_AUTHENTICATION:
        return 'eye';
      case BiometryType.FINGERPRINT:
      case BiometryType.TOUCH_ID:
      default:
        return 'finger-print';
    }
  }
} 