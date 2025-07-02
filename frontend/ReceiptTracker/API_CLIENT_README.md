# API Client Documentation

Ez a dokumentáció leírja, hogyan használható a generált API kliens az Ionic Angular alkalmazásban.

## Generálás

Az API kliens az OpenAPI Generator segítségével lett generálva a backend FastAPI alkalmazásból. A generáláshoz használd:

```bash
npm run generate:api
```

## Beállítás

Az API kliens automatikusan be van állítva az `app.module.ts`-ben:

```typescript
import { ApiModule } from './api/api.module';
import { Configuration } from './api/configuration';

@NgModule({
  imports: [
    // ... other imports
    HttpClientModule,
    ApiModule.forRoot(() => new Configuration({
      basePath: 'http://localhost:8000'
    }))
  ],
})
export class AppModule {}
```

## Használat

### 1. API Service

A `src/app/services/api.service.ts` fájl egy wrapper szolgáltatást tartalmaz, ami egyszerűsíti az API hívásokat:

```typescript
import { ApiService } from '../services/api.service';

constructor(private apiService: ApiService) { }

// Receipts
this.apiService.getReceipts().subscribe(data => {
  console.log('Receipts:', data);
});

// Users
this.apiService.getCurrentUser().subscribe(data => {
  console.log('Users:', data);
});
```

### 2. Közvetlen API hívások

Használhatod közvetlenül a generált szolgáltatásokat is:

```typescript
import { AuthService } from '../api/api/auth.service';
import { ReceiptService } from '../api/api/receipt.service';

constructor(
  private authService: AuthService,
  private receiptService: ReceiptService
) { }

// Login
this.authService.loginAuthLoginPost('username', 'password').subscribe(token => {
  console.log('Token:', token);
});

// Get receipts
this.receiptService.getReceiptsReceiptGet().subscribe(receipts => {
  console.log('Receipts:', receipts);
});
```

### 3. Típusok

A generált típusok a `src/app/api/model/` mappában találhatók:

- `ReceiptOut` - Receipt objektum
- `ReceiptListOut` - Receipt lista
- `UserOut` - User objektum
- `UserListOut` - User lista
- `TokenOut` - Token objektum

## Példa komponens

A `src/app/components/api-example.component.ts` fájl egy példa komponenst tartalmaz, ami mutatja, hogyan használható az API kliens.

## Újragenerálás

Ha változtatásokat végzel a backend API-n, újra kell generálni a klienst:

1. Indítsd el a backend szervert
2. Futtasd: `npm run generate:api`
3. A generált fájlok felülíródnak a `src/app/api/` mappában

## Hibaelhárítás

### CORS hibák
Ha CORS hibákat tapasztalsz, ellenőrizd, hogy a backend szerver fut-e és a `basePath` helyesen van-e beállítva.

### Típus hibák
Ha típus hibákat tapasztalsz a generált kódban, ellenőrizd:
1. Az OpenAPI specifikáció helyességét
2. A generált típusok kompatibilitását
3. Az importok helyességét

### Authentication
Az API kliens automatikusan kezeli a Bearer token autentikációt. A token beállításához:

```typescript
// A Configuration objektumban
new Configuration({
  basePath: 'http://localhost:8000',
  accessToken: 'your-token-here'
})
```

## További információk

- [OpenAPI Generator dokumentáció](https://openapi-generator.tech/)
- [Angular HTTP Client](https://angular.io/guide/http)
- [Ionic Framework](https://ionicframework.com/docs) 