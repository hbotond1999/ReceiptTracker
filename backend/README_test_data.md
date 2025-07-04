# Teszt Adat Generátor

## Leírás
A `generate_test_data.py` script teszt adatokat generál a Receipt Tracker alkalmazáshoz.

## Mit csinál?
- **10 bolt** létrehozása valós magyar bolt nevekkel (Tesco, Auchan, Spar, stb.)
- **5000-10000 számla** generálása random dátumokkal (utóbbi 2 évből)
- **Minden számlához 1-10 tétel** random termékekkel és árakkal
- **Valós magyar adatok** használata (városok, utcák, termékek)

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
- Folytatni akarod-e a generálást
- Ha már vannak boltok, akarsz-e újakat létrehozni

## Generált adatok

### Boltok
- Tesco, Auchan, Spar, CBA, Penny Market, Lidl, Aldi, Interspar, Coop, Match
- Minden bolt egyedi adószámmal

### Számlák
- Random dátumok (utóbbi 2 év)
- Valós magyar címek (Budapest, Debrecen, Szeged, stb.)
- Random blokk számok

### Termékek
- Magyar terméknevek (kenyér, tej, tojás, stb.)
- 100-5000 HUF közötti árak
- 1-10 tétel számlánként

## Figyelmeztetés
⚠️ **Csak tesztelési célra!** Ne futtasd éles adatbázison!

## Statisztikák
A script futás után kiírja:
- Összesen létrehozott boltok száma
- Összesen létrehozott számlák száma
- Összesen létrehozott tételek száma
- Átlagos tételszám számlánként 