# Merkinmurtaja — Claude-konteksti

## Projektin tarkoitus
Pesäpallon merkkikielen analysointityökalu. Sisäpelijoukkueen pelinjohtaja käyttää väriviuhkaa viestiäkseen etenijöille ja lyöjälle miten tilanteessa toimitaan. Tämä ohjelma kerää havaintoja vastustajan merkeistä ja selvittää tilastollisesti mitä kukin merkki tarkoittaa.

## Tekninen stack
- **Backend:** Python + Flask
- **Frontend:** Jinja2-templatet, vanilla JS, mobiilioptimioitu dark-teema
- **Data:** CSV-tiedostot `data/`-kansiossa
- **Käynnistys:** `python app.py` → http://localhost:5000

## Tiedostorakenne
```
merkinmurtaja/
├── app.py               # Flask-reitit ja web-sovellus
├── merkinmurtaja.py     # Analyysimoottorin ydin + CLI
├── templates/
│   ├── base.html        # Pohja: dark-teema, mobiili-layout, CSS-muuttujat
│   ├── etusivu.html     # Otteluiden listaus ja uuden luonti
│   ├── syotto.html      # Havaintojen syöttö (värit, käsi, tilanne, tulos)
│   └── analyysi.html    # Analyysiraportti
├── data/                # CSV-tiedostot otteluittain (gitignoressa)
├── requirements.txt     # flask>=3.0.0
└── CLAUDE.md            # Tämä tiedosto
```

## Tietorakenteet (merkinmurtaja.py)

### Havainto-luokka
Yksi pelitilanteen havainto sisältää:
- `ottelu` — ottelun nimi
- `vuoro` — 1–9
- `pallot` — 0, 1 tai 2
- `etenijat` — "1", "12", "123", "ei" jne.
- `värit` — lista järjestyksessä, esim. `["musta", "vihreä"]`
- `vapaa_käsi` — "auki", "nyrkki", "taskussa", "lanteilla", "viuhkassa", "ei_näy"
- `tulos` — "lento", "sikalento", "väärät_pois", "nopea_väärä", "iso_väärä", "pois", "epäselvä"
- `huomio` — vapaa tekstikenttä

### Analysoija-luokka
Analyysimoottorin metodit:
- `värikuvio_korrelaatiot()` — {värikuvio: Counter({tulos: määrä})}
- `vahvimmat_kuviot(min_havainnot)` — lista kuvioista varmuusprosentteineen
- `etsi_kieltomerkki()` — värit jotka korreloivat "pois"-tulokseen
- `etsi_pikamerkki()` — käden asennot jotka korreloivat lentoon
- `tilanneriippuvuus()` — sama kuvio eri merkitys eri pallomäärällä
- `yhteenveto()` — kaikki yllä yhdistettynä

## Merkkipelin logiikka (domain-tieto)

### Viuhka
- Koostuu värisuikaleista (lakuista), tyypillisesti 6–10 väriä molemmin puolin
- Värien järjestys ja paikka merkitsevät, ei pelkkä väri

### Tärkeimmät merkit
| Merkki | Tarkoitus |
|--------|-----------|
| **lento** | Etenijä lähtee suoraan syötöstä |
| **sikalento** | Lähtö kaikista syötöistä (myös väärät) |
| **väärät pois** | Kuunnellaan väärä, lähdetään sen jälkeen |
| **nopea väärä** | Huudetaan väärä nousevaan palloon |
| **iso väärä** | Kulma-/takamailamies huutaa ison väärän |
| **pois** | Ei lähdöä, merkki ei päällä |

### Merkin rakenteet
- **Kieltomerkki:** tietty väri nollaa muut merkit (esim. jos musta kolmantena → merkki ei päällä vaikka vihreä näkyy)
- **Pikamerkki:** käden asento tai näkyvä liike overridaa kaiken → välitön lento
- **Automaattimerkki:** laukeaa tapahtumasta (esim. lukkari heittää kerran ykköselle → merkki päälle)
- **Tilanneriippuvuus:** sama kuvio eri merkitys 0-pallolla vs. 1-pallolla

## Flask-reitit (app.py)
| Reitti | Metodi | Toiminto |
|--------|--------|----------|
| `/` | GET | Etusivu, otteluiden lista |
| `/ottelu/uusi` | POST | Luo uusi ottelu |
| `/ottelu/<id>` | GET | Syöttönäkymä |
| `/ottelu/<id>/tallenna` | POST | Tallenna havainto |
| `/ottelu/<id>/analyysi` | GET | Analyysinäkymä |
| `/analyysi/kaikki` | GET | Kaikki ottelut yhdistettynä |
| `/ottelu/<id>/poista_viimeisin` | POST | Poistaa viimeisen havainnon |

## UI-design (base.html)
Dark-teema CSS-muuttujilla:
- `--bg: #0f1117` — tausta
- `--surface: #1a1d27` — kortit
- `--accent: #4f8ef7` — sininen korostus
- `--success: #4fcf7a` — vihreä (lento)
- `--danger: #f75757` — punainen (pois/varoitus)
- `--warning: #f7e14f` — keltainen (väärät pois)

## GitHub
- Repo: https://github.com/Jugisoft/merkinmurtaja_2.0
- Branch: main

## Kehitysideoita (ei toteutettu)
- Visuaalinen viuhka-editori (raahaus väreille)
- Todennäköisyysnäyttö reaaliajassa syötön aikana
- Vientitoiminto (PDF-raportti ottelusta)
- Tietokanta CSV:n tilalle (pysyvä tallennus pilvipalvelussa)
- Pelaajaprofiilit (eri etenijöillä eri merkit)
- Lukkarin käden analysoiminen (miten heittelee → automaattimerkki)
