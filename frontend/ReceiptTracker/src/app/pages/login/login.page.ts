import {Component, OnDestroy, OnInit} from '@angular/core';
import {
  AbstractControl,
  FormBuilder,
  FormGroup,
  FormsModule,
  ReactiveFormsModule,
  ValidationErrors,
  Validators
} from '@angular/forms';
import {Store} from '@ngrx/store';
import {biometricLogin, clearError, clearRegisterState, enableBiometric, login, register} from '../../store/auth/auth.actions';
import {
  selectAuthError,
  selectAuthLoading,
  selectIsAuthenticated,
  selectRegister
} from '../../store/auth/auth.selectors';
import {
  IonAlert,
  IonButton,
  IonCheckbox,
  IonContent,
  IonIcon,
  IonInput,
  IonItem,
  IonLabel,
  IonSpinner,
  IonToast
} from '@ionic/angular/standalone';
import {CommonModule} from '@angular/common';
import {Subject, takeUntil} from 'rxjs';
import {Router} from '@angular/router';
import {BiometricService} from '../../services/biometric.service';
import {BiometryType} from 'capacitor-native-biometric';
import {PublicUserRegister} from '../../api/model/publicUserRegister';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    FormsModule,
    IonContent,
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
  loginForm: FormGroup = this.fb.group({
    username: ['', Validators.required],
    password: ['', Validators.required]
  });
  readonly unsub$ = new Subject<void>();
  registerForm: FormGroup = this.fb.group({
    username: ['', [Validators.required, Validators.minLength(3)]],
    email: ['', [Validators.email]],
    fullname: [''],
    password: ['', [Validators.required, Validators.minLength(6)]],
    confirmPassword: ['', Validators.required]
  }, { validators: this.passwordMatchValidator });

  loading$ = this.store.select(selectAuthLoading);
  error$ = this.store.select(selectAuthError);

  isLoginMode = true;

  // Biometric properties
  biometricAvailable = false;
  biometricType: BiometryType | null = null;
  biometricTypeDisplayName = '';
  hasBiometricCredentials = false;
  enableBiometricAfterLogin = false;
  showBiometricLoginButton = false;

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
    private biometricService: BiometricService,
  ) {

  }

  async ngOnInit() {
    await this.checkBiometricAvailability();

    this.store.select(selectIsAuthenticated).pipe(
      takeUntil(this.unsub$)
    ).subscribe(isAuth => {
      console.log('Authentication state changed:', isAuth);
      if (isAuth) {
        console.log('User authenticated, navigating to home...');
        this.router.navigate(['home']).then(success => {
          console.log('Navigation to home successful:', success);
        }).catch(error => {
          console.error('Navigation to home failed:', error);
        });
      }
      if (this.hasBiometricCredentials && !isAuth) {
        this.biometricLogin()
      }
    });

    // Listen for successful registration and errors
    this.store.select(selectRegister).pipe(
      takeUntil(this.unsub$)
    ).subscribe((register) => {
        if (!this.isLoginMode) { // Csak registration mode-ban figyelünk
          if (!register.loading) {
            if (register.success && !register.error) {
              // Sikeres regisztráció - automatikus bejelentkezés történt
              this.showToast('Sikeres regisztráció és bejelentkezés!', 'success');
              this.isLoginMode = true;
              this.registerForm.reset();
            } else if (register.error) {
              // Hiba történt regisztráció során
              this.showToast(register.error, 'danger');
            }
          }
        }
      });
  }

  async checkBiometricAvailability() {
    try {
      this.biometricAvailable = await this.biometricService.isBiometricAvailable();
      if (this.biometricAvailable) {
        this.biometricType = await this.biometricService.getBiometricType();
        this.biometricTypeDisplayName = this.biometricService.getBiometricTypeDisplayName(this.biometricType);
        this.hasBiometricCredentials = await this.biometricService.hasBiometricCredentials();
        this.showBiometricLoginButton = this.hasBiometricCredentials;
      }
    } catch (error) {
      console.error('Biometric availability check failed:', error);
      this.biometricAvailable = false;
      this.hasBiometricCredentials = false;
      this.showBiometricLoginButton = false;
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

      // First dispatch login
      this.store.dispatch(login({ username, password }));

      // If biometric is available and user wants to enable it, listen for login success
      if (this.biometricAvailable && this.enableBiometricAfterLogin) {
        this.store.select(selectIsAuthenticated).pipe(
          takeUntil(this.unsub$)
        ).subscribe(isAuthenticated => {
          if (isAuthenticated) {
            this.store.dispatch(enableBiometric({ username, password }));
            this.showToast('Biometrikus azonosítás beállítva!', 'success');
          }
        });
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
    // Reset any previous errors and register state
    this.store.dispatch(clearError());
    this.store.dispatch(clearRegisterState());
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
    if (!this.biometricAvailable) {
      this.showToast('Biometrikus azonosítás nem érhető el ezen az eszközön', 'danger');
      return;
    }

    if (!this.hasBiometricCredentials) {
      this.showToast('Nincsenek mentett biometrikus adatok. Kérjük jelentkezzen be felhasználónévvel és jelszóval, majd engedélyezze a biometrikus azonosítást.', 'danger');
      return;
    }

    try {
      this.store.dispatch(biometricLogin());
    } catch (error) {
      console.error('Biometric login error:', error);
      this.showToast('Hiba a biometrikus bejelentkezés során', 'danger');
    }
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
    this.unsub$.next();
    this.unsub$.complete();
  }
}
