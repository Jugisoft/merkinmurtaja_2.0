# Merkinmurtaja — Railway-deploy (GitHub-pohjainen)

## Kerran: Railway-projektin luonti

1. Mene **railway.app** → kirjaudu GitHub-tunnuksilla
2. **New Project** → **Deploy from GitHub repo** → valitse `merkinmurtaja_2.0`
3. Railway tunnistaa Procfilen automaattisesti

## Ympäristömuuttujat (Railway → Variables)

| Muuttuja | Arvo | Selitys |
|----------|------|---------|
| `SECRET_KEY` | (satunnainen merkkijono, esim. 32 merkkiä) | Flask-sessioiden salausavain |
| `TIIMI_KOODI` | (esim. `jymy2026`) | Salasana sisäänpääsyyn — jätä tyhjäksi jos ei tarvita |

## Pysyvä tallennustila (tärkeä!)

SQLite-tietokanta tallennetaan `data/merkinmurtaja.db`:hen.
Railwayn levytila on **oletuksena väliaikainen** — data häviää uudelleenkäynnistyksessä.

**Lisää pysyvä levy:**
Railway → projektisi → **Add Volume** → mount path: `/app/data`

Tämä pitää tietokannan tallessa uudelleenkäynnistysten yli.

## Automaattinen deploy GitHubista

Railway deployaa automaattisesti kun pushaat `main`-haaraan:

```bash
git add .
git commit -m "päivitys"
git push
```

Railway huomaa pushin ja käynnistää uuden version ~30 sekunnissa.

## Paikallinen testaus ennen pushia

```bash
pip install -r requirements.txt
python app.py
# → http://localhost:5000
```

## Tiimikoodin asettaminen

Jos haluat suojata sovelluksen tiimikoodilla, aseta Railway-muuttuja:
`TIIMI_KOODI=teidänkoodi`

Kaikki käyttäjät syöttävät tämän koodin + nimensä kirjautuessaan.
