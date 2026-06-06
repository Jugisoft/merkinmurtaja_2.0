#!/usr/bin/env python3
"""
MERKINMURTAJA — Pesäpallon merkkikielen analyysityökalu
=======================================================
Kerää havaintoja vastustajan viuhkamerkeistä ja analysoi
tilastollisesti mitä mikäkin merkki todennäköisesti tarkoittaa.
"""

import csv
import os
import json
from collections import defaultdict, Counter
from datetime import datetime
from pathlib import Path

# ─────────────────────────────────────────────────────────────
# Vakiot
# ─────────────────────────────────────────────────────────────

VÄRIT = [
    "punainen", "sininen", "vihreä", "keltainen", "oranssi",
    "musta", "valkoinen", "violetti", "ruskea", "harmaa"
]

LYHENTEET_VÄRIT = {
    "p": "punainen", "s": "sininen", "v": "vihreä", "k": "keltainen",
    "o": "oranssi", "m": "musta", "va": "valkoinen", "vi": "violetti",
    "r": "ruskea", "h": "harmaa", "-": "-"
}

KÄSIEN_ASENNOT = [
    "auki", "nyrkki", "taskussa", "lanteilla", "viuhkassa", "ei_näy"
]

LYHENTEET_KÄSI = {
    "a": "auki", "n": "nyrkki", "t": "taskussa",
    "l": "lanteilla", "vi": "viuhkassa", "e": "ei_näy"
}

TULOKSET = {
    "meni":         "Lähti — tyyppi epäselvä",
    "lento":        "Etenijä lähti suoraan syötöstä",
    "sikalento":    "Etenijä lähti kaikista syötöistä",
    "väärät_pois":  "Otettiin väärä, lähdettiin sen jälkeen",
    "nopea_väärä":  "Huudettiin nopea väärä nousevaan",
    "iso_väärä":    "Otettiin iso väärä (kulma/takamailamies)",
    "pois":         "Etenijä ei lähtenyt / merkki pois päältä",
    "epäselvä":     "Ei voitu varmuudella tulkita",
}

MENI_TULOKSET = {"meni", "lento", "sikalento", "väärät_pois", "nopea_väärä", "iso_väärä"}

SARJAT = ["MSU", "Talvisuper", "Divari", "Harjoitusottelu"]

TILANTEET = [
    "tyhjä", "0-tilanne", "1-tilanne", "2-tilanne", "3-tilanne",
    "1-2-tilanne", "1-3-tilanne", "0-2-tilanne", "2-3-tilanne",
    "0-3-tilanne", "1-2-3-tilanne", "ajolähtö",
]

LYHENTEET_TULOS = {
    "le": "lento", "si": "sikalento", "vp": "väärät_pois",
    "nv": "nopea_väärä", "iv": "iso_väärä", "po": "pois", "ep": "epäselvä"
}

DATA_HAKEMISTO = Path(__file__).parent / "data"
DATA_HAKEMISTO.mkdir(exist_ok=True)


# ─────────────────────────────────────────────────────────────
# Tietorakenteet
# ─────────────────────────────────────────────────────────────

class Havainto:
    """Yksi pelitilanteen havainto."""

    def __init__(self, ottelu: str, vuoro: int, pallot: int,
                 etenijat: str, värit: list[str], vapaa_käsi: str,
                 tulos: str, huomio: str = "", kuvaus: str = "",
                 jakso: str = "", vuoropari: str = "", tilanne: str = "",
                 lyoja: str = "", etenija_1: str = "", etenija_2: str = "",
                 etenija_3: str = ""):
        self.ottelu     = ottelu
        self.vuoro      = vuoro
        self.pallot     = pallot
        self.etenijat   = etenijat
        self.värit      = värit
        self.vapaa_käsi = vapaa_käsi
        self.tulos      = tulos
        self.huomio     = huomio
        self.kuvaus     = kuvaus
        self.jakso      = jakso       # 1 tai 2
        self.vuoropari  = vuoropari   # 1–5
        self.tilanne    = tilanne     # 0-tilanne, 1-tilanne, ajolähtö jne.
        self.lyoja      = lyoja       # lyöjän nimi tai numero
        self.etenija_1  = etenija_1   # pelaaja 1. pesällä
        self.etenija_2  = etenija_2   # pelaaja 2. pesällä
        self.etenija_3  = etenija_3   # pelaaja 3. pesällä
        self.aikaleima  = datetime.now().isoformat(timespec="seconds")

    def värikuvio(self) -> str:
        """Palauttaa värit yhdistettynä avaimeksi."""
        return "|".join(self.värit)

    def to_row(self) -> list:
        return [
            self.aikaleima, self.ottelu, self.vuoro, self.pallot,
            self.etenijat, "|".join(self.värit), self.vapaa_käsi,
            self.tulos, self.huomio, self.kuvaus,
            self.jakso, self.vuoropari, self.tilanne,
            self.lyoja, self.etenija_1, self.etenija_2, self.etenija_3,
        ]

    @classmethod
    def from_row(cls, row: dict) -> "Havainto":
        h = cls.__new__(cls)
        h.aikaleima  = row["aikaleima"]
        h.ottelu     = row["ottelu"]
        h.vuoro      = int(row["vuoro"])
        h.pallot     = int(row["pallot"])
        h.etenijat   = row["etenijat"]
        h.värit      = row["värit"].split("|") if row["värit"] else []
        h.vapaa_käsi = row["vapaa_käsi"]
        h.tulos      = row["tulos"]
        h.huomio     = row.get("huomio", "")
        h.kuvaus     = row.get("kuvaus", "")
        h.jakso      = row.get("jakso", "")
        h.vuoropari  = row.get("vuoropari", "")
        h.tilanne    = row.get("tilanne", "")
        h.lyoja      = row.get("lyoja", "")
        h.etenija_1  = row.get("etenija_1", "")
        h.etenija_2  = row.get("etenija_2", "")
        h.etenija_3  = row.get("etenija_3", "")
        return h


CSV_OTSIKOT = [
    "aikaleima", "ottelu", "vuoro", "pallot", "etenijat",
    "värit", "vapaa_käsi", "tulos", "huomio", "kuvaus",
    "jakso", "vuoropari", "tilanne", "lyoja",
    "etenija_1", "etenija_2", "etenija_3",
]


# ─────────────────────────────────────────────────────────────
# Tiedostotoiminnot
# ─────────────────────────────────────────────────────────────

def lataa_havainnot(tiedosto: Path) -> list[Havainto]:
    if not tiedosto.exists():
        return []
    with open(tiedosto, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [Havainto.from_row(row) for row in reader]


def tallenna_havainto(havainto: Havainto, tiedosto: Path):
    on_uusi = not tiedosto.exists()
    with open(tiedosto, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if on_uusi:
            writer.writerow(CSV_OTSIKOT)
        writer.writerow(havainto.to_row())


def listaa_ottelutiedostot() -> list[Path]:
    return sorted(DATA_HAKEMISTO.glob("*.csv"))


# ─────────────────────────────────────────────────────────────
# Syöttöapurit
# ─────────────────────────────────────────────────────────────

def valitse_lyhenne(kysymys: str, lyhenteet: dict, oletusarvo: str = "") -> str:
    print(f"\n{kysymys}")
    for lyhenne, arvo in lyhenteet.items():
        print(f"  {lyhenne:4s} = {arvo}")
    while True:
        syöte = input("Valinta: ").strip().lower()
        if syöte == "" and oletusarvo:
            return oletusarvo
        if syöte in lyhenteet:
            return lyhenteet[syöte]
        print("  ⚠ Tuntematon valinta, yritä uudelleen.")


def syötä_värit() -> list[str]:
    print("\nViuhkan värit järjestyksessä (ylhäältä/vasemmalta).")
    print("Lyhenteet: p=punainen s=sininen v=vihreä k=keltainen o=oranssi")
    print("           m=musta va=valkoinen vi=violetti r=ruskea h=harmaa -=ei väriä")
    print("Syötä värit välilyönnillä erotettuna (esim: m p v) tai ENTER jos ei värejä.")
    while True:
        syöte = input("Värit: ").strip().lower()
        if syöte == "":
            return ["-"]
        osat = syöte.split()
        värit = []
        virhe = False
        for osa in osat:
            if osa in LYHENTEET_VÄRIT:
                värit.append(LYHENTEET_VÄRIT[osa])
            else:
                print(f"  ⚠ Tuntematon väri '{osa}'")
                virhe = True
                break
        if not virhe:
            return värit


def syötä_kokonaisluku(kysymys: str, minimi: int, maksimi: int) -> int:
    while True:
        try:
            arvo = int(input(f"{kysymys} ({minimi}–{maksimi}): ").strip())
            if minimi <= arvo <= maksimi:
                return arvo
            print(f"  ⚠ Anna luku väliltä {minimi}–{maksimi}.")
        except ValueError:
            print("  ⚠ Anna kokonaisluku.")


# ─────────────────────────────────────────────────────────────
# Havaintojen syöttö
# ─────────────────────────────────────────────────────────────

def syötä_havainto(ottelu: str) -> Havainto | None:
    print("\n" + "─" * 50)
    print("UUSI HAVAINTO  (tyhjä ENTER = peruuta)")
    print("─" * 50)

    vuoro = syötä_kokonaisluku("Vuoro", 1, 9)
    pallot = syötä_kokonaisluku("Palloja lyöjällä", 0, 2)

    print("\nEtenijöiden paikat (esim: 1  tai  12  tai  123  tai  ei):")
    etenijat = input("Etenijät: ").strip() or "ei"

    värit = syötä_värit()

    vapaa_käsi = valitse_lyhenne(
        "Vapaan käden asento:",
        LYHENTEET_KÄSI, "ei_näy"
    )

    tulos = valitse_lyhenne(
        "Mitä tapahtui? (tulos):",
        LYHENTEET_TULOS, "epäselvä"
    )

    huomio = input("\nVapaa huomio (ENTER ohittaa): ").strip()

    return Havainto(
        ottelu=ottelu,
        vuoro=vuoro,
        pallot=pallot,
        etenijat=etenijat,
        värit=värit,
        vapaa_käsi=vapaa_käsi,
        tulos=tulos,
        huomio=huomio,
    )


# ─────────────────────────────────────────────────────────────
# Analyysimoottori
# ─────────────────────────────────────────────────────────────

class Analysoija:
    """Analysoi havainnot ja etsii korrelaatioita."""

    def __init__(self, havainnot: list[Havainto]):
        self.havainnot = havainnot

    def n(self) -> int:
        return len(self.havainnot)

    # ── Värikuvio → tulos -korrelaatio ──────────────────────

    def värikuvio_korrelaatiot(self) -> dict[str, Counter]:
        """Palauttaa {värikuvio: Counter({tulos: määrä})}"""
        data: dict[str, Counter] = defaultdict(Counter)
        for h in self.havainnot:
            kuvio = h.värikuvio()
            data[kuvio][h.tulos] += 1
        return dict(data)

    def vahvimmat_kuviot(self, min_havainnot: int = 2) -> list[dict]:
        """
        Palauttaa lista {kuvio, tulos, varmuus%, määrä}
        järjestettynä varmuuden mukaan.
        """
        tulokset = []
        for kuvio, laskuri in self.värikuvio_korrelaatiot().items():
            yhteensä = sum(laskuri.values())
            if yhteensä < min_havainnot:
                continue
            yleisin_tulos, määrä = laskuri.most_common(1)[0]
            varmuus = määrä / yhteensä * 100
            tulokset.append({
                "kuvio": kuvio,
                "tulos": yleisin_tulos,
                "varmuus": varmuus,
                "määrä": yhteensä,
                "jakauma": dict(laskuri),
            })
        return sorted(tulokset, key=lambda x: (-x["varmuus"], -x["määrä"]))

    # ── Kieltomerkkianalyysi ─────────────────────────────────

    def etsi_kieltomerkki(self) -> list[dict]:
        """
        Etsi värejä, joiden läsnäolo muuttaa tuloksen 'pois'-suuntaan
        riippumatta muista väreistä.
        """
        epäilyt = []
        kaikki_värit = set()
        for h in self.havainnot:
            kaikki_värit.update(v for v in h.värit if v != "-")

        for väri in kaikki_värit:
            havainnot_väri = [h for h in self.havainnot if väri in h.värit]
            havainnot_ilman = [h for h in self.havainnot if väri not in h.värit]

            if len(havainnot_väri) < 2 or len(havainnot_ilman) < 2:
                continue

            pois_väri = sum(1 for h in havainnot_väri if h.tulos == "pois") / len(havainnot_väri)
            pois_ilman = sum(1 for h in havainnot_ilman if h.tulos == "pois") / len(havainnot_ilman)

            # Jos värin kanssa tulos on selvästi useammin "pois"
            if pois_väri - pois_ilman > 0.3:
                epäilyt.append({
                    "väri": väri,
                    "pois_värin_kanssa_%": round(pois_väri * 100, 1),
                    "pois_ilman_%": round(pois_ilman * 100, 1),
                    "havainnot": len(havainnot_väri),
                })

        return sorted(epäilyt, key=lambda x: -x["pois_värin_kanssa_%"])

    # ── Pikamerkki-analyysi ──────────────────────────────────

    def etsi_pikamerkki(self) -> list[dict]:
        """
        Etsi käden asentoja, jotka korreloivat vahvasti 'lento'-tulokseen.
        Pikamerkki näkyy useimmiten välittömänä lentona.
        """
        epäilyt = []
        for asento in KÄSIEN_ASENNOT:
            havainnot_asento = [h for h in self.havainnot if h.vapaa_käsi == asento]
            if len(havainnot_asento) < 2:
                continue
            lento_osuus = sum(
                1 for h in havainnot_asento if h.tulos in ("lento", "sikalento")
            ) / len(havainnot_asento)
            if lento_osuus > 0.7:
                epäilyt.append({
                    "asento": asento,
                    "lento_%": round(lento_osuus * 100, 1),
                    "havainnot": len(havainnot_asento),
                })
        return sorted(epäilyt, key=lambda x: -x["lento_%"])

    # ── Tilanneriippuvuus ────────────────────────────────────

    def tilanneriippuvuus(self) -> dict:
        """
        Onko samat värit eri merkityksiä eri palloilla tai etenijätilanteissa?
        """
        löydöt = {}
        kuviot = self.värikuvio_korrelaatiot()

        for kuvio, kaikki_laskuri in kuviot.items():
            if sum(kaikki_laskuri.values()) < 4:
                continue

            # Jaottele pallojen mukaan
            pallot_data = defaultdict(Counter)
            for h in self.havainnot:
                if h.värikuvio() == kuvio:
                    pallot_data[h.pallot][h.tulos] += 1

            # Onko eroa?
            tulokset_per_pallo = {}
            for pallo, laskuri in pallot_data.items():
                if sum(laskuri.values()) >= 2:
                    yleisin, _ = laskuri.most_common(1)[0]
                    tulokset_per_pallo[pallo] = yleisin

            erilaiset = len(set(tulokset_per_pallo.values())) > 1
            if erilaiset and len(tulokset_per_pallo) >= 2:
                löydöt[kuvio] = tulokset_per_pallo

        return löydöt

    # ── Meni/Ei-analyysi ────────────────────────────────────

    def meni_analyysi(self) -> dict:
        """Yhteenveto: kuinka monta meni vs. ei mennyt."""
        meni = sum(1 for h in self.havainnot if h.tulos in MENI_TULOKSET)
        ei   = sum(1 for h in self.havainnot if h.tulos == "pois")
        ep   = sum(1 for h in self.havainnot if h.tulos == "epäselvä")
        yht  = meni + ei
        return {
            "meni":     meni,
            "ei":       ei,
            "epäselvä": ep,
            "meni_pct": round(meni / yht * 100, 1) if yht else 0,
        }

    # ── Tekstianalyysi ───────────────────────────────────────

    def tekstianalyysi(self, min_havainnot: int = 2) -> list[dict]:
        """
        Vertaa sanoja/fraaseja meni- vs. ei-kuvauksissa.
        Palauttaa termit järjestettynä erottelukyvyn mukaan.
        """
        import re

        def hae_termit(teksti: str) -> set:
            teksti = teksti.lower()
            sanat = re.findall(r"[a-zäöå]{3,}", teksti)
            termit = set(sanat)
            for i in range(len(sanat) - 1):
                termit.add(sanat[i] + " " + sanat[i + 1])
            return termit

        termi_meni: dict[str, int] = defaultdict(int)
        termi_ei:   dict[str, int] = defaultdict(int)

        for h in self.havainnot:
            if not h.kuvaus or not h.kuvaus.strip():
                continue
            termit = hae_termit(h.kuvaus)
            if h.tulos in MENI_TULOKSET:
                for t in termit:
                    termi_meni[t] += 1
            elif h.tulos == "pois":
                for t in termit:
                    termi_ei[t] += 1

        kaikki = set(termi_meni) | set(termi_ei)
        tulokset = []
        for termi in kaikki:
            m = termi_meni[termi]
            e = termi_ei[termi]
            yht = m + e
            if yht < min_havainnot:
                continue
            meni_pct = round(m / yht * 100, 1)
            tulokset.append({
                "termi":      termi,
                "meni_maara": m,
                "ei_maara":   e,
                "yhteensa":   yht,
                "meni_pct":   meni_pct,
            })

        # Järjestä erottelukyvyn mukaan (kauimpana 50%:sta)
        tulokset.sort(key=lambda x: (-abs(x["meni_pct"] - 50), -x["yhteensa"]))
        return tulokset[:40]

    # ── Yhteenveto ───────────────────────────────────────────

    def yhteenveto(self) -> dict:
        return {
            "havainnot_yhteensä": self.n(),
            "meni_analyysi":      self.meni_analyysi(),
            "tekstianalyysi":     self.tekstianalyysi(),
            "vahvimmat_kuviot":   self.vahvimmat_kuviot(min_havainnot=2),
            "epäillyt_kieltomerkit": self.etsi_kieltomerkki(),
            "epäillyt_pikamerkit":   self.etsi_pikamerkki(),
            "tilanneriippuvat":      self.tilanneriippuvuus(),
        }


# ─────────────────────────────────────────────────────────────
# Raportointi
# ─────────────────────────────────────────────────────────────

def tulosta_raportti(havainnot: list[Havainto], otsikko: str = ""):
    if not havainnot:
        print("\n⚠  Ei havaintoja analysoitavaksi.")
        return

    a = Analysoija(havainnot)
    yhteenveto = a.yhteenveto()

    leveys = 60
    print("\n" + "═" * leveys)
    print(f"  MERKINMURTAJA — ANALYYSI")
    if otsikko:
        print(f"  {otsikko}")
    print(f"  Havaintoja yhteensä: {yhteenveto['havainnot_yhteensä']}")
    print("═" * leveys)

    # ── Vahvimmat kuviot ─────────────────────────────────────
    print("\n▶ VAHVIMMAT VÄRIKUVIO → TULOS -YHTEYDET")
    print("  (väh. 2 havaintoa vaaditaan)")
    kuviot = yhteenveto["vahvimmat_kuviot"]
    if not kuviot:
        print("  (ei riittävästi dataa — kerää lisää havaintoja)")
    else:
        print(f"\n  {'VÄRIKUVIO':<28} {'TULOS':<14} {'VARMUUS':>8}  {'N':>4}")
        print("  " + "─" * 56)
        for k in kuviot:
            kuvio_str = k["kuvio"].replace("|", " → ")
            tulos_str = k["tulos"]
            varmuus_str = f"{k['varmuus']:.0f}%"
            n_str = str(k["määrä"])
            print(f"  {kuvio_str:<28} {tulos_str:<14} {varmuus_str:>8}  {n_str:>4}")
            # Näytä jakauma jos ei 100%
            if k["varmuus"] < 100:
                jakauma = ", ".join(
                    f"{t}:{m}" for t, m in
                    sorted(k["jakauma"].items(), key=lambda x: -x[1])
                )
                print(f"  {'':>28}  [{jakauma}]")

    # ── Kieltomerkki ────────────────────────────────────────
    print("\n▶ EPÄILLYT KIELTOMERKIT")
    print("  (väri joka usein nollaa merkin → tulos 'pois')")
    kiellot = yhteenveto["epäillyt_kieltomerkit"]
    if not kiellot:
        print("  (ei havaittu selkeitä kieltomerkkejä vielä)")
    else:
        for k in kiellot:
            print(f"  ⚠  {k['väri'].upper():<12} → pois {k['pois_värin_kanssa_%']}% "
                  f"(ilman: {k['pois_ilman_%']}%)  [n={k['havainnot']}]")

    # ── Pikamerkki ───────────────────────────────────────────
    print("\n▶ EPÄILLYT PIKAMERKIT (käden asento)")
    print("  (asento joka korreloi vahvasti välittömään lentoon)")
    pikamerkit = yhteenveto["epäillyt_pikamerkit"]
    if not pikamerkit:
        print("  (ei havaittu selkeitä pikamerkkejä vielä)")
    else:
        for p in pikamerkit:
            print(f"  ⚡ {p['asento'].upper():<14} → lento {p['lento_%']}%  [n={p['havainnot']}]")

    # ── Tilanneriippuvuus ────────────────────────────────────
    print("\n▶ TILANNERIIPPUVAT MERKIT (sama kuvio, eri pallomäärä)")
    tilanteet = yhteenveto["tilanneriippuvat"]
    if not tilanteet:
        print("  (ei havaittu tilanneriippuvuutta vielä)")
    else:
        for kuvio, pallot_data in tilanteet.items():
            kuvio_str = kuvio.replace("|", " → ")
            print(f"  📊 {kuvio_str}")
            for pallo, tulos in sorted(pallot_data.items()):
                print(f"      {pallo} palloa → {tulos}")

    print("\n" + "═" * leveys)


# ─────────────────────────────────────────────────────────────
# Päävalikko
# ─────────────────────────────────────────────────────────────

def valitse_ottelu() -> tuple[str, Path]:
    """Valitse tai luo uusi ottelu, palauta (nimi, tiedostopolku)."""
    tiedostot = listaa_ottelutiedostot()

    print("\n── OTTELUT ──────────────────────────────")
    if tiedostot:
        for i, t in enumerate(tiedostot, 1):
            n = len(lataa_havainnot(t))
            print(f"  {i}. {t.stem}  ({n} havaintoa)")
    else:
        print("  (ei vielä yhtään ottelua)")
    print("  N. Uusi ottelu")
    print("─────────────────────────────────────────")

    while True:
        valinta = input("Valinta: ").strip().upper()
        if valinta == "N":
            nimi = input("Ottelu (esim. Haukipudas-Sotkamo 2024-07-20): ").strip()
            if not nimi:
                nimi = f"ottelu_{datetime.now().strftime('%Y%m%d_%H%M')}"
            # Siisti tiedostonimi
            tiedostonimi = nimi.replace(" ", "_").replace("/", "-") + ".csv"
            return nimi, DATA_HAKEMISTO / tiedostonimi
        try:
            idx = int(valinta) - 1
            if 0 <= idx < len(tiedostot):
                t = tiedostot[idx]
                return t.stem.replace("_", " "), t
        except ValueError:
            pass
        print("⚠  Virheellinen valinta.")


def päävalikko():
    print("\n╔══════════════════════════════════════╗")
    print("║       M E R K I N M U R T A J A      ║")
    print("║   Pesäpallon merkkikielen analysoija  ║")
    print("╚══════════════════════════════════════╝")

    ottelu_nimi, ottelu_tiedosto = valitse_ottelu()

    while True:
        havainnot = lataa_havainnot(ottelu_tiedosto)
        print(f"\n── {ottelu_nimi.upper()} ({len(havainnot)} havaintoa) ──")
        print("  1. Syötä uusi havainto")
        print("  2. Analysoi tämä ottelu")
        print("  3. Analysoi kaikki ottelut (vastustajan kokonaiskuva)")
        print("  4. Vaihda ottelu")
        print("  Q. Lopeta")

        valinta = input("\nValinta: ").strip().upper()

        if valinta == "1":
            havainto = syötä_havainto(ottelu_nimi)
            if havainto:
                tallenna_havainto(havainto, ottelu_tiedosto)
                print(f"✓ Havainto tallennettu ({ottelu_tiedosto.name})")

        elif valinta == "2":
            tulosta_raportti(havainnot, f"Ottelu: {ottelu_nimi}")

        elif valinta == "3":
            kaikki = []
            for t in listaa_ottelutiedostot():
                kaikki.extend(lataa_havainnot(t))
            tulosta_raportti(kaikki, "Kaikki ottelut yhdistettynä")

        elif valinta == "4":
            ottelu_nimi, ottelu_tiedosto = valitse_ottelu()

        elif valinta == "Q":
            print("\nNähdään kentällä! 🏟\n")
            break

        else:
            print("⚠  Tuntematon valinta.")


if __name__ == "__main__":
    päävalikko()
