# ReceiptTracker Dokumentáció

Üdvözlünk a ReceiptTracker projekt dokumentációjában! Itt megtalálod az alkalmazás architektúrájával, fejlesztésével és üzembe helyezésével kapcsolatos információkat.

## 📁 Dokumentációs Fájlok

### 🏗️ [Architektúra Dokumentáció](./architecture.md)
Részletes áttekintés az alkalmazás architektúrájáról, amely tartalmazza:
- **Rendszer architektúra ábra** (Mermaid diagram) - Produkciós és fejlesztési környezet
- **Komponens leírások** (Frontend, Backend, Adatbázis)
- **Nginx konfiguráció részletek** (statikus fájl kiszolgálás)
- **Kétirányú kommunikációs folyamatok**
- **JWT authentikáció rendszer** (RSA256, token rotation, RBAC)
- **Adatmodell diagram** (Entity Relationship Diagram)
- **Technológiai stack** részletei
- **Biztonsági megfontolások**
- **Skalázhatósági információk**

## 🎯 Projekt Áttekintés

A ReceiptTracker egy modern, többplatformos alkalmazás, amely:
- **Blokkok digitalizálását** és feldolgozását teszi lehetővé
- **AI-alapú szövegfelismerést** használ
- **Angular/Ionic frontend-del** rendelkezik mobil és web támogatással
- **FastAPI backend-et** használ
- **Google Cloud infrastruktúrán** fut


### Éles környezet Környezet
- **Frontend**: Google Cloud Run konténer
- **Backend**: Google Cloud Run konténer  
- **Adatbázis**: Google Cloud SQL (PostgreSQL)
- **Fájlok**: Google Cloud Storage

## 📱 Támogatott Platformok

- **🌐 Web alkalmazás**: Minden modern böngészőben
- **📱 Android app**: Google Play Store-ban elérhető
- **🍎 iOS app**: App Store-ban elérhető


## 🔧 Technológiák

### Backend
- FastAPI (Python)
- PostgreSQL
- SQLAlchemy ORM
- JWT Authentication (RSA256)
- bcrypt (jelszó hash-elés)
- OpenAI API integráció

### Frontend
- Angular
- Ionic Framework
- Standalone Components
- TypeScript
- Nginx (statikus web szerver)

### Infrastruktúra
- Docker
- Google Cloud Platform
- Cloud Run (konténer szolgáltatás)
- Cloud SQL (adatbázis)
- Cloud Storage (fájlkezelés)

### Biztonság
- JWT (JSON Web Token) authentikáció
- RSA256 aszimmetrikus titkosítás
- bcrypt jelszó hash-elés
- Role-based Access Control (RBAC)
- Refresh token rotation
- HTTPS titkosított kommunikáció


## 🚀 Gyors Kezdés

### Automatikus Setup (Ajánlott)

**Egyszerű automatikus inicializálás:**
```bash
# Futtasd a root mappában Command Prompt-ból
init-project.bat
```

Az automatikus script elvégzi:
- Python virtuális környezet létrehozása/aktiválása
- Requirements telepítése
- .env fájl létrehozása
- RSA kulcsok generálása és másolása
- Docker konténerek indítása
- Adatbázis inicializálása
- Admin felhasználó létrehozása (interaktív)
- Opcionálisan teszt adatok generálása

### Manuális Setup (Helyi Fejlesztési Környezet)

Ha szeretnéd lépésről lépésre végrehajtani, vagy problémába ütközöl az automatikus scripttel:

#### 1. Környezeti változók beállítása
Először hozz létre egy `.env` fájlt a `docker` mappában a `.env.example` alapján:

```bash
cd docker
# Másold át a .env.example-t .env-be és töltsd ki a szükséges értékeket
```

A `.env` fájl tartalma:
```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/receipt_tracker
# Access token lejárati idő (percben)
ACCESS_TOKEN_EXPIRE_MINUTES=15

# Refresh token lejárati idő (napokban)
REFRESH_TOKEN_EXPIRE_DAYS=7
AI_MODEL=gpt-4.1
OPENAI_API_KEY=your_openai_api_key_here
```

#### 2. RSA kulcsok generálása
A JWT authentikációhoz szükséges RSA kulcsokat generáld le:

```bash
cd backend
python generate_rsa_keys.py
```

Ez létrehozza a `backend/keys` mappát és benne a `private_key.pem` és `public_key.pem` fájlokat.

Ezután másold át a kulcsokat a docker mappába:

```bash
# PowerShell-ben (Windows)
Copy-Item -Path "keys\*" -Destination "..\docker\keys\" -Force

# Vagy manuálisan másold át a backend/keys mappából a docker/keys mappába:
# - private_key.pem
# - public_key.pem
```

#### 3. Docker konténerek indítása
```bash
cd ../docker
# Docker konténerek indítása (adatbázis szükséges a következő lépésekhez)
docker-compose up -d

# PostgreSQL: localhost:5432
```

#### 4. Adatbázis inicializálása
```bash
cd ../backend
# Adatbázis táblák és alapértelmezett szerepkörök létrehozása
python init_db.py
```

#### 5. Admin felhasználó létrehozása
```bash
# Admin felhasználó létrehozása interaktív módon
python create_admin.py
```

A script bekéri az admin felhasználónevet, email címet, teljes nevet és jelszót.

#### 6. Teszt adatok generálása (opcionális)
Ha szeretnél teszt adatokkal dolgozni, generálhatsz boltokat és számlákat:

```bash
python generate_test_data.py
```

A script interaktívan bekéri:
- Hány számlát generáljon (alapértelmezett: 500)
- Létrehoz 10 boltot magyar nevekkel
- Generál számlákat valós magyar adatokkal (címek, terméknevek)
- Többszálú feldolgozást használ a gyors generáláshoz

**Megjegyzés:** Ezt csak az admin felhasználó létrehozása után futtasd!

#### 7. Alkalmazás elérése
```bash
# Frontend elérhető: http://localhost
# Backend API: http://localhost:8000
# PostgreSQL: localhost:5432
```

## 🔗 Hasznos Linkek

- [Docker Compose konfiguráció](../docker/docker-compose.yaml)
- [Backend forrás](../backend/)
- [Frontend forrás](../frontend/ReceiptTracker/)
- [API dokumentáció](http://localhost:8000/docs) (helyi fejlesztés során)
