# Merkinmurtaja — Claude-analyysikonteksti

Tämä dokumentti on tarkoitettu liitettäväksi Claude-projektiin (Project Instructions) tai kopioitavaksi keskustelun alkuun ennen havaintojen liittämistä. Se antaa Claudelle tarvittavan taustatiedon pesäpallon merkkipelin analysointiin.

---

## Mikä on pesäpallon merkkipeli?

Pesäpallossa **pelinjohtaja** viestii sisäpelin pelaajille — erityisesti **etenijöille** (pesillä oleville juoksijoille) ja **lyöjälle** — miten tilanteessa toimitaan kun lukkari heittää pallon. Tätä kutsutaan **merkkipeliksi**.

Viestintä tapahtuu **väriviuhkalla** (kokoelma värillisiä suikaleita, "lakuja") ja **vapaalla kädellä**. Viuhkassa voi olla 6–10 väriä molemmin puolin; värien järjestys, paikka ja viuhkan asento määrittävät merkin. Vapaa käsi — se jossa ei ole viuhkaa — antaa lisäinformaatiota asennollaan.

Merkkipeli on salattua: vastustaja ei saa tietää, mitä merkki tarkoittaa. Siksi käytetään kieltomerkkejä, pikamerkkejä ja muita hämäyksiä.

### Yleisimmät merkit (mitä etenijälle viestitään)

| Merkki | Tarkoitus |
|--------|-----------|
| **Lento** | Etenijä lähtee heti syötöstä (suoraan syötöstä -lähtö) |
| **Sikalento** | Lähtö kaikista syötöistä, myös vääriin |
| **Väärät pois** | Kuunnellaan väärä-huuto, lähdetään sen jälkeen |
| **Nopea väärä** | Vääränhuutajat huutavat nousevaan palloon |
| **Iso väärä** | Kulma- tai takamailamies huutaa väärän ensimmäisellä askeleella |
| **Pois / ei merkki** | Ei lähtöä — etenijä pysyy pesällä |

### Merkin rakenne ja muuttujat

Merkkiä määrittelee mm.:
- Viuhkan **puoli** (mihin suuntaan viuhka osoittaa)
- Viuhkan **korkeus** (ylhäällä / sivulla / alhaalla)
- Viuhkaote: **rystyset** kentälle päin vs. **peukalo** kentälle päin
- Vapaan käden asento: **auki** / **nyrkissä** / **kiinni viuhkasta** / taskussa / lanteilla
- Pallotilanne (0, 1 vai 2 paloa)
- Vuoropari, lyöjä, etenijät pesillä
- Kieltomerkki: tietty väri tai asento kumoaa muun merkin

---

## Merkinmurtaja-sovelluksen datamalli

Joukkueen jäsenet kirjaavat reaaliajassa ottelusta havaintoja: **mikä asento pelinjohtajalla oli**, ja **lähtiikö etenijä pesältä vai ei**.

### Asentomerkinnät

**Viuhkakäsi 🔵:**
- **Puoli:** `3-puoli` = lähtöpesän puoli (vasen), `Edessä` = suoraan edessä, `2-puoli` = menopesän puoli (oikea)
- **Korkeus:** `ylh.` = ylhäällä, `keski` = sivutasolla suorana, `koukussa` = kyynärpää alaspäin V-muodossa (olkapään tasolla), `alh.` = alhaalla
- **Ote:** `rystyset` = rystyset kentälle päin, `peukalo` = peukalo kentälle päin, `ei näy` = ote ei näy

**Vapaa käsi 🟠:**
- **Asento:** `auki` = avoin kämmen, `nyrkki` = nyrkki, `kiinni viuhkasta` = pitää kiinni viuhkasta, `passiivinen` = käsi roikkuu passiivisena sivulla (voi olla merkityksetön tai merkkaava), `ei näy` = ei näy

### Tilannetiedot (lisäinfo)
- **Jakso:** 1 / 2 / K (kolmas erä / jatkoerät)
- **Vuoropari:** 1A / 1L / 2A / 2L / ... / K (vuoro ja lyöntijärjestys: A=alku, L=loppu)
- **Palot:** montako paloa alla (0, 1, 2 paloa)
- **Lyöjä:** lyöjän numero (1–12)
- **Monesko lyönti:** 1., 2. vai 3. lyönti
- **Etenijät:** millä pesillä etenijöitä (1, 2, 3 = ykkös-, kakkos-, kolmospesä)
- **Värit:** kirjatut värit viuhkassa (esim. musta, punainen, vihreä...)
- **Kuvaus:** vapaa tekstikenttä — kirjaajan omin sanoin kuvailema havainto

### Tulos
- **MENI** = etenijä lähti pesältä (lento / sikalento / väärät pois / nopea väärä / iso väärä)
- **EI MENNYT** = etenijä ei lähtenyt (merkki ei ollut päällä, tai oli "pois")

---

## Analyysitehtävä

Sinulle annetaan havaintoja yhdestä tai useammasta ottelusta. Tehtäväsi on **selvittää vastustajan lähtemismerkki**: millä asennolla tai asennon osatekijöillä etenijä lähtee, ja millä asennolla hän ei lähde.

### Ohjeet analyysiin

1. **Etsi toistuvia asennon osatekijöitä MENI-ryhmässä** jotka puuttuvat tai ovat harvinaisia EI MENNYT -ryhmässä.
2. **Huomioi yhdistelmät:** viuhkan puoli + korkeus + ote on usein yhdessä merkitsevä. Vapaa käsi voi olla itsenäinen merkki tai tarkenne.
3. **Etsi mahdollinen kieltomerkki:** asento tai väri joka esiintyy EI MENNYT -tilanteissa, vaikka muu asento olisi sama kuin MENI-tilanteessa.
4. **Pallotilanne ja vuoropari** voivat muuttaa merkin merkitystä — sama asento voi tarkoittaa eri asiaa 0-palolla vs. 1-palolla.
5. **Vapaiden kuvausten** avulla voi löytää merkittäviä yksityiskohtia (esim. "viuhka liikkui" tai "kämmen ylöspäin vain hetken").
6. **Värit** ovat keskeisiä mutta niitä ei aina kirjata — kun kirjattu, ne voivat paljastaa kieltomerkin tai pikamerkin logiikan.

### Vastausohje

Vastaa **suomeksi**. Rakenna analyysi näin:
- **Johtopäätös:** mikä todennäköisesti on lähtemismerkki (tai merkit)
- **Perustelut:** mitkä datapisteet tukevat päätelmää
- **Poikkeukset:** tilanteet jotka eivät sovi malliin — voisiko kyse olla kieltomerkistä, tilanneriippuvuudesta tai merkki vaihdettu?
- **Varmuusaste:** kuinka vahva evidenssi on (havaintojen määrä, johdonmukaisuus)
- **Lisäkysymykset:** mitä pitäisi kirjata lisää analyysin vahvistamiseksi

---

## Havaintodata

*Liitä tähän Merkinmurtaja-sovelluksen "Kopioi Claude AI -analyysiin" -napin generoima teksti.*

