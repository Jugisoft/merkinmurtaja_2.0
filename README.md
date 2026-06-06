# 🏟 Merkinmurtaja

**Pesäpallon merkkikielen analysointityökalu**

Merkinmurtaja kerää havaintoja vastustajan joukkueen viuhkamerkeistä ja analysoi tilastollisesti mitä kukin merkki todennäköisesti tarkoittaa.

## Ominaisuudet

- 📱 **Mobiiliystävällinen web-käyttöliittymä** — syötä havaintoja suoraan puhelimella livepelin aikana
- 🎨 **Visuaalinen värinvalinta** — napauta viuhkan värit järjestyksessä
- 🔍 **Automaattinen analyysi** tunnistaa:
  - Vahvimmat värikuvio → tulos -yhteydet varmuusprosentteineen
  - Kieltomerkit (väri joka nollaa muut → "pois")
  - Pikamerkit (käden asento → välitön lento)
  - Tilanneriippuvat merkit (sama kuvio, eri merkitys eri pallomäärillä)
- 💾 **CSV-tallennus** — data säilyy otteluittain, voi analysoida kaikki yhdistettynä
- 🖥️ **CLI-versio** myös saatavilla

## Asennus

```bash
pip install -r requirements.txt
```

## Käynnistys

### Web-sovellus (suositeltu)
```bash
python app.py
```
Avaa selaimessa: `http://localhost:5000`

Puhelimella samassa wifi-verkossa: `http://<tietokoneen-ip>:5000`

### Komentorivityökalu
```bash
python merkinmurtaja.py
```

## Käyttö

1. Luo uusi ottelu (joukkueen nimi + päivämäärä)
2. Syötä havainto jokaisesta pelitilanteesta:
   - Vuoro ja pallojen määrä
   - Etenijöiden paikat
   - Viuhkan värit **järjestyksessä**
   - Vapaan käden asento
   - Mitä tapahtui (lento / väärät pois / pois / jne.)
3. Avaa analyysi — ohjelma näyttää mitkä kuviot korreloivat mihinkin toimintaan

## Merkkien selitykset

| Merkki | Tarkoitus |
|--------|-----------|
| **lento** | Etenijä lähtee suoraan syötöstä |
| **sikalento** | Etenijä lähtee kaikista syötöistä |
| **väärät pois** | Otetaan väärä, lähdetään sen jälkeen |
| **nopea väärä** | Huudetaan nopea väärä nousevaan palloon |
| **iso väärä** | Otetaan iso väärä (kulma- tai takamailamies) |
| **pois** | Etenijä ei lähde / merkki pois päältä |

## Projektin rakenne

```
merkinmurtaja/
├── app.py              # Flask web-sovellus
├── merkinmurtaja.py    # Analyysimoottorin ydin + CLI
├── requirements.txt
├── templates/
│   ├── base.html
│   ├── etusivu.html
│   ├── syotto.html
│   └── analyysi.html
└── data/               # CSV-tiedostot (gitignoressa)
```

## Tausta

Pesäpallossa sisäpelijoukkueen pelinjohtaja käyttää viuhkaa (värillisiä suikaleita) viestiäkseen etenijöille ja lyöjälle miten tilanteessa toimitaan. Vastustajan merkin selvittäminen on iso osa huippupesäpallon taktiikkaa.

Tämä työkalu automatisoi kaavojen etsimisen suuresta havaintojoukosta.
