import {Component, OnDestroy, OnInit} from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, FormsModule, Validators, AbstractControl, ValidationErrors } from '@angular/forms';
import { Store } from '@ngrx/store';
import { login, biometricLogin, enableBiometric, register, registerSuccess, registerFailure } from '../../store/auth/auth.actions';
import {
  selectAuthError,
  selectAuthLoading,
  selectIsAuthenticated,
  selectRegister
} from '../../store/auth/auth.selectors';
import { IonContent, IonHeader, IonTitle, IonToolbar, IonInput, IonButton, IonItem, IonLabel, IonSpinner, IonIcon, IonCheckbox, IonToast, IonAlert } from '@ionic/angular/standalone';
import { CommonModule } from '@angular/common';
import {Observable, Subscription, combineLatest} from 'rxjs';
import { Router } from '@angular/router';
import { BiometricService } from '../../services/biometric.service';
import { BiometryType } from 'capacitor-native-biometric';
import { addIcons } from 'ionicons';
import { fingerPrint, eye, checkmark } from 'ionicons/icons';
import { PublicUserRegister } from '../../api/model/publicUserRegister';
import { Actions, ofType } from '@ngrx/effects';

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
export class LoginPage implements OnInit, OnDestroy {
  loginForm: FormGroup;
  registerForm: FormGroup;
  loading$: Observable<boolean>;
  error$: Observable<string | null>;
  isLoginMode = true;

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
  sub !: Subscription;
  private registrationSub?: Subscription;

  constructor(
    private fb: FormBuilder,
    private store: Store,
    private router: Router,
    private biometricService: BiometricService,
    private actions$: Actions
  ) {
    addIcons({ fingerPrint, eye, checkmark });

    this.loginForm = this.fb.group({
      username: ['', Validators.required],
      password: ['', Validators.required]
    });

    this.registerForm = this.fb.group({
      username: ['', [Validators.required, Validators.minLength(3)]],
      email: ['', [Validators.email]],
      fullname: [''],
      password: ['', [Validators.required, Validators.minLength(6)]],
      confirmPassword: ['', Validators.required]
    }, { validators: this.passwordMatchValidator });

    this.loading$ = this.store.select(selectAuthLoading);
    this.error$ = this.store.select(selectAuthError);

    this.store.select(selectIsAuthenticated).subscribe(isAuth => {
      if (isAuth) {
        this.router.navigate(['home']);
      }
    });

    // Listen for successful registration and errors
      this.store.select(selectRegister).subscribe((register) => {

      if (!register.loading && !this.isLoginMode) {
        if (!register.error) {
          // Sikeres regisztráció - automatikus bejelentkezés történt
          this.showToast('Sikeres regisztráció és bejelentkezés!', 'success');
          this.isLoginMode = true;
          this.registerForm.reset();
        } else {
          // Hiba történt regisztráció során
          this.showToast(register.error, 'danger');
        }
      }
    });
  }

  async ngOnInit() {
    await this.checkBiometricAvailability();
    if (this.biometricAvailable && this.hasBiometricCredentials)
    {
      this.sub = this.store.select(selectIsAuthenticated).subscribe(isAuthenticated => {
        if (!isAuthenticated) {
          this.biometricLogin()
        }
      });
    }
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
    if (this.isLoginMode) {
      this.submitLogin();
    } else {
      this.submitRegister();
    }
  }

  submitLogin() {
    if (this.loginForm.valid) {
      const { username, password } = this.loginForm.value;
      this.store.dispatch(login({ username, password }));

      // If biometric is available and user wants to enable it
      if (this.biometricAvailable && this.enableBiometricAfterLogin) {
        this.store.dispatch(enableBiometric({ username, password }));
      }
    } else {
      this.loginForm.markAllAsTouched();
    }
  }

  submitRegister() {
    if (this.registerForm.valid) {
      const { username, email, fullname, password } = this.registerForm.value;
      const userData: PublicUserRegister = {
        username,
        email: email || null,
        fullname: fullname || null,
        password
      };
      this.store.dispatch(register({ userData }));
    } else {
      this.registerForm.markAllAsTouched();
    }
  }

  toggleMode() {
    this.isLoginMode = !this.isLoginMode;
    // Reset forms when switching modes
    if (this.isLoginMode) {
      this.registerForm.reset();
    } else {
      this.loginForm.reset();
    }
  }

  passwordMatchValidator(control: AbstractControl): ValidationErrors | null {
    const password = control.get('password');
    const confirmPassword = control.get('confirmPassword');

    if (password && confirmPassword && password.value !== confirmPassword.value) {
      return { passwordMismatch: true };
    }

    return null;
  }

  biometricLogin() {
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

  ngOnDestroy() {
    if (this.sub)
    {
      this.sub.unsubscribe();
    }
    if (this.registrationSub) {
      this.registrationSub.unsubscribe();
    }
  }
}
