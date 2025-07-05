# Teszt Adat Generátor (Többszálú)

## Leírás
A `generate_test_data.py` script teszt adatokat generál a Receipt Tracker alkalmazáshoz többszálú feldolgozással a gyors adatbeszúrásért.

## Új funkciók ✨
- **Többszálú feldolgozás**: Több CPU mag kihasználása párhuzamos adatbeszúráshoz
- **Skálázható**: Támogatja akár 1 millió+ rekord gyors beszúrását
- **Valós idejű progress**: Élő statisztikák a generálás során
- **Optimalizált batch-ek**: Intelligens batch méretezés a maximális teljesítményért
- **Thread-safe**: Biztonságos párhuzamos adatbázis műveletek

## Mit csinál?
- **10 bolt** létrehozása valós magyar bolt nevekkel (Tesco, Auchan, Spar, stb.)
- **Konfigurálható számú számla** generálása (alapértelmezett: 500, maximum: 1M+)
- **Minden számlához 1-10 tétel** random termékekkel és árakkal
- **Valós magyar adatok** használata (városok, utcák, termékek)
- **Párhuzamos feldolgozás** több szállal a gyorsaságért

## Használat

### Előfeltételek
1. Legalább egy felhasználó legyen az adatbázisban
2. Ha még nincs admin user, futtasd le a `create_admin.py` scriptet

### Futtatás
```bash
cd backend
python generate_test_data.py
```

### Interaktív használat
A script interaktív, megkérdi, hogy:
- Hány számlát akarsz generálni (alapértelmezett: 500)
- Folytatni akarod-e a generálást
- Ha már vannak boltok, akarsz-e újakat létrehozni

### Példa használat nagy mennyiségű adatra:
```bash
python generate_test_data.py
# Válaszd: 100000 (100 ezer számla)
# vagy: 1000000 (1 millió számla)
```

## Teljesítmény 🚀

### Optimalizációk
- **Connection pooling**: 20 kapcsolat pool + 30 overflow
- **Bulk insert**: Batch-enkénti tömeges beszúrás
- **Thread pool**: CPU magok számához igazított szálak (max 10)
- **Smart batching**: Minimum 50 számla per batch

### Várható sebesség
- **Kis adatbázis**: 100-500 számla/másodperc
- **Nagy adatbázis**: 50-200 számla/másodperc
- **1 millió rekord**: ~1-3 óra (géptől függően)

## Generált adatok

### Boltok
- Tesco, Auchan, Spar, CBA, Penny Market, Lidl, Aldi, Interspar, Coop, Match
- Minden bolt egyedi adószámmal

### Számlák
- Random dátumok (utóbbi 2 év)
- Valós magyar címek (Budapest, Debrecen, Szeged, stb.)
- Random blokk számok
- Thread-safe ID generálás

### Termékek
- Magyar terméknevek (kenyér, tej, tojás, stb.)
- 100-5000 HUF közötti árak
- 1-10 tétel számlánként

## Technikai részletek

### Többszálú architektúra
```
Main Thread
├── Market Creation (single-threaded)
├── Thread Pool Executor
│   ├── Worker Thread 1 (batch 1)
│   ├── Worker Thread 2 (batch 2)
│   ├── ...
│   └── Worker Thread N (batch N)
└── Progress Monitoring
```

### Batch feldolgozás
- Minden szál külön adatbázis session-t használ
- Batch méret: max(50, total_count / thread_count)
- Bulk insert receipt-ek → ID refresh → bulk insert item-ek

### Thread safety
- `threading.Lock` a progress reporting-hoz
- Külön session minden thread-hez
- Immutable ID listák a thread-ek között

## Figyelmeztetés
⚠️ **Csak tesztelési célra!** Ne futtasd éles adatbázison!

⚠️ **Nagy mennyiségű adat**: 1M+ rekord esetén győződj meg róla, hogy van elég hely az adatbázisban és memória a gépben.

## Hibaelhárítás

### Lassú futás
- Ellenőrizd az adatbázis kapcsolatot
- SQLite esetén fontold meg PostgreSQL használatát nagy mennyiségű adathoz
- Növeld a connection pool méretet ha szükséges

### Memory hibák
- Csökkentsd a batch méretet
- Csökkentsd a thread számot
- Ellenőrizd a rendelkezésre álló memóriát

## Statisztikák
A script futás után kiírja:
- Összesen létrehozott boltok száma
- Összesen létrehozott számlák száma
- Összesen létrehozott tételek száma
- Futási idő
- Átlagos sebesség (számla/másodperc)
- Átlagos tételszám számlánként 