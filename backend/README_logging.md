# Logging System Documentation

## Overview

A FastAPI alkalmazás egy átfogó logging rendszert implementál, amely request ID-kkal követi nyomon a kéréseket és válaszokat.

## Főbb jellemzők

- **Request ID tracking**: Minden HTTP kérés egyedi request ID-t kap
- **Kontextuális logging**: A request ID minden log bejegyzésben megjelenik
- **Színezett konzol kimenet**: Különböző log szintek különböző színekkel
- **Fájl rotáció**: Automatikus log fájl rotáció méret alapján
- **Környezeti változók**: Teljes konfigurálhatóság .env fájlból

## Konfiguráció

### Környezeti változók

```bash
# Logging szint (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL=INFO

# Fájlba írás engedélyezése
LOG_TO_FILE=true

# Konzolra írás engedélyezése
LOG_TO_CONSOLE=true

# Log fájl útvonala (opcionális, alapértelmezett: logs/app.log)
LOG_FILE_PATH=logs/app.log

# Maximális fájl méret bájtban (alapértelmezett: 10MB)
LOG_MAX_FILE_SIZE=10485760

# Backup fájlok száma (alapértelmezett: 5)
LOG_BACKUP_COUNT=5
```

### Programozói konfiguráció

```python
from app_logging import setup_logging

# Manuális konfiguráció
setup_logging(
    log_level="DEBUG",
    log_to_file=True,
    log_to_console=True,
    log_file_path="custom/path/app.log",
    max_file_size=20 * 1024 * 1024,  # 20MB
    backup_count=10
)

# Környezeti változókból
from app_logging import configure_from_env
configure_from_env()
```

## Használat

### Logger megszerzése

```python
from app_logging import get_logger

logger = get_logger(__name__)
```

### Logging használata

```python
# Különböző log szintek
logger.debug("Debug információ")
logger.info("Információs üzenet")
logger.warning("Figyelmeztetés")
logger.error("Hiba történt")
logger.critical("Kritikus hiba")

# Request ID automatikusan hozzáadódik minden log bejegyzéshez
```

### Request ID kezelés

```python
from app_logging import get_request_id, set_request_id, generate_request_id

# Aktuális request ID lekérése
current_request_id = get_request_id()

# Request ID beállítása (middleware automatikusan csinálja)
request_id = generate_request_id()
set_request_id(request_id)
```

## Log formátum

### Konzol kimenet
```
2024-01-15 10:30:45 - auth.routes - INFO - [abc123ef] - Successful login for user: testuser
```

### Fájl kimenet
```
2024-01-15 10:30:45 - auth.routes - INFO - [abc123ef] - login:45 - Successful login for user: testuser
```

## Middleware

A `logging_middleware` automatikusan:
- Generál egyedi request ID-t minden kéréshez
- Logolja a bejövő kéréseket
- Logolja a kimenő válaszokat feldolgozási idővel
- Hozzáadja a request ID-t a response headerekhez
- Logolja a hibákat

## Példa implementáció

```python
from app_logging import get_logger

logger = get_logger(__name__)

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    logger.info(f"Login attempt for user: {form_data.username}")
    
    try:
        # Login logika
        user = authenticate_user(form_data.username, form_data.password)
        logger.info(f"Successful login for user: {form_data.username}")
        return {"token": "..."}
    except Exception as e:
        logger.error(f"Login failed for user: {form_data.username} - {str(e)}")
        raise HTTPException(status_code=401, detail="Login failed")
```

## Fájl struktúra

```
backend/
├── app_logging.py          # Logging konfiguráció és utilities
├── logs/                   # Log fájlok könyvtára
│   ├── app.log            # Aktuális log fájl
│   ├── app.log.1          # Rotált log fájl
│   └── ...
└── main.py                # Middleware integráció
```

## Troubleshooting

### Problémák

1. **Log fájl nem jön létre**
   - Ellenőrizd a `LOG_TO_FILE` környezeti változót
   - Ellenőrizd a könyvtár írási jogosultságokat

2. **Nincs színes kimenet**
   - Ellenőrizd a `LOG_TO_CONSOLE` beállítást
   - Egyes terminálok nem támogatják a színeket

3. **Request ID hiányzik**
   - Ellenőrizd, hogy a middleware megfelelően van regisztrálva
   - Async/await használata esetén a context megfelelően továbbítódik

### Debug mód

```python
# Debug szint beállítása
LOG_LEVEL=DEBUG

# Részletes SQL logginghoz
import logging
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
```

## Teljesítmény

- A logging rendszer minimális overhead-del rendelkezik
- Async context variables használata thread-safe
- Fájl rotáció automatikus, nem blokkolja az alkalmazást
- Request ID generálás gyors UUID alapú 