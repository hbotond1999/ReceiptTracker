# Autentikációs Rendszer Dokumentáció

Ez a dokumentáció leírja az NgRx alapú autentikációs rendszer működését az Ionic Angular alkalmazásban.

## 🏗️ Architektúra

### Store Struktúra
```
src/app/store/auth/
├── auth.actions.ts      # Actions (login, logout, refresh token)
├── auth.reducer.ts      # State management
├── auth.selectors.ts    # State selectors
├── auth.state.ts        # State interface
└── auth.effects.ts      # Side effects (API calls)
```

### Komponensek
```
src/app/
├── pages/login/         # Login oldal
├── guards/auth.guard.ts # Route protection
├── interceptors/        # HTTP interceptor
└── services/api.service.ts # API wrapper
```

## 🔐 Autentikációs Folyamat

### 1. Login Folyamat
1. Felhasználó megadja a felhasználónevet és jelszót
2. `AuthActions.login()` action dispatch-elődik
3. `AuthEffects.login$` effect kezeli az API hívást
4. Token elmentődik az Ionic Storage-ba
5. Felhasználó adatok lekérése
6. `AuthActions.loginSuccess()` action dispatch-elődik
7. Felhasználó átirányítódik a home oldalra

### 2. Auto Login Folyamat
1. Alkalmazás indításakor `AuthActions.autoLogin()` dispatch-elődik
2. Refresh token ellenőrzése az Ionic Storage-ból
3. Ha van refresh token, új access token kérése
4. Ha sikeres, felhasználó automatikusan bejelentkezik
5. Ha sikertelen, login oldalra irányítás

### 3. Token Refresh Folyamat
1. HTTP interceptor észleli a 401 hibát
2. `AuthActions.refreshToken()` action dispatch-elődik
3. Refresh token használatával új access token kérése
4. Új token elmentése az Ionic Storage-ba
5. Eredeti kérés újrapróbálása az új tokennel

### 4. Logout Folyamat
1. `AuthActions.logout()` action dispatch-elődik
2. Tokenek törlése az Ionic Storage-ból
3. Store reset-elése
4. Felhasználó átirányítása a login oldalra

## 🛡️ Route Védelme

### AuthGuard
- Védi a védett oldalakat (pl. `/home`)
- Ellenőrzi az autentikációs állapotot
- Ha nincs bejelentkezve, átirányít a login oldalra

### Használat
```typescript
{
  path: 'home',
  loadChildren: () => import('./home/home.module').then(m => m.HomePageModule),
  canActivate: [AuthGuard]
}
```

## 🔄 HTTP Interceptor

### AuthInterceptor
- Automatikusan hozzáadja az access token-t minden HTTP kéréshez
- Kivéve: `/auth/login` és `/auth/register` végpontok
- 401 hiba esetén automatikus token refresh
- Sikertelen refresh esetén logout

### Konfiguráció
```typescript
{
  provide: HTTP_INTERCEPTORS,
  useClass: AuthInterceptor,
  multi: true
}
```

## 💾 Adattárolás

### Ionic Storage
- Access token és refresh token tárolása
- Automatikus token kezelés
- Offline támogatás

### Store State
```typescript
interface AuthState {
  user: UserOut | null;
  token: TokenOut | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  isRefreshing: boolean;
}
```

## 🎯 Használat Komponensekben

### Login Komponens
```typescript
export class LoginPage {
  constructor(private store: Store) {}

  onSubmit() {
    const { username, password } = this.loginForm.value;
    this.store.dispatch(AuthActions.login({ username, password }));
  }
}
```

### Home Komponens
```typescript
export class HomePage {
  user$ = this.store.select(selectUser);
  isAuthenticated$ = this.store.select(selectIsAuthenticated);

  logout() {
    this.store.dispatch(AuthActions.logout());
  }
}
```

### Selectors Használata
```typescript
// Felhasználó adatok
this.store.select(selectUser)

// Autentikációs állapot
this.store.select(selectIsAuthenticated)

// Loading állapot
this.store.select(selectIsLoading)

// Hibaüzenetek
this.store.select(selectError)
```

## 🔧 Konfiguráció

### App Module
```typescript
@NgModule({
  imports: [
    StoreModule.forRoot({ auth: authReducer }),
    EffectsModule.forRoot([AuthEffects]),
    IonicStorageModule.forRoot(),
    // ... other imports
  ],
  providers: [
    { provide: HTTP_INTERCEPTORS, useClass: AuthInterceptor, multi: true }
  ]
})
```

### API Konfiguráció
```typescript
ApiModule.forRoot(() => new Configuration({
  basePath: 'http://localhost:8000'
}))
```

## 🚀 Indítás

1. **Backend szerver indítása**
   ```bash
   cd backend
   python main.py
   ```

2. **Frontend alkalmazás indítása**
   ```bash
   cd frontend/ReceiptTracker
   npm start
   ```

3. **Alkalmazás megnyitása**
   - Nyissa meg a `http://localhost:4200` címet
   - Automatikusan a login oldalra kerül
   - Bejelentkezés után a home oldalra irányít

## 🐛 Hibaelhárítás

### CORS Hibák
- Ellenőrizd, hogy a backend szerver fut-e
- Ellenőrizd a `basePath` beállítást

### Token Hibák
- Ellenőrizd az Ionic Storage működését
- Nézd meg a browser DevTools-ban a Network tab-ot

### Store Hibák
- Használd a Redux DevTools-t a store állapot ellenőrzéséhez
- Ellenőrizd a console-ban a hibaüzeneteket

## 📱 Ionic Komponensek

### Login Oldal
- `ion-input` - Felhasználónév és jelszó mezők
- `ion-button` - Bejelentkezés gomb
- `ion-spinner` - Loading állapot
- `ion-text` - Hibaüzenetek

### Home Oldal
- `ion-card` - Tartalom kártyák
- `ion-button` - Műveletek
- `ion-icon` - Ikonok

## 🔄 Frissítések

### API Kliens Újragenerálása
```bash
npm run generate:api
```

### Store Frissítése
- Actions, reducers, effects módosítása után újraindítás szükséges
- Ionic Storage cache törlése szükséges lehet

## 📚 További Források

- [NgRx Dokumentáció](https://ngrx.io/)
- [Ionic Framework](https://ionicframework.com/docs)
- [Angular HTTP Client](https://angular.io/guide/http)
- [Ionic Storage](https://ionicframework.com/docs/angular/storage) 