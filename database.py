"""
Merkinmurtaja — SQLite-tietokantakerros
"""
import sqlite3
import json
import csv
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / "data" / "merkinmurtaja.db"

OLETUS_ASETUKSET = {
    "lento_max_ms":       "500",
    "nopea_vaara_max_ms": "1200",
    "vaarat_pois_max_ms": "2800",
}


def _conn():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _conn() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS ottelut (
                id         TEXT PRIMARY KEY,
                nimi       TEXT NOT NULL,
                vastustaja TEXT DEFAULT '',
                luotu      TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS havainnot (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                ottelu_id      TEXT    NOT NULL,
                vuoro          INTEGER DEFAULT 1,
                pallot         INTEGER DEFAULT 0,
                etenijat       TEXT    DEFAULT 'ei',
                varit          TEXT    NOT NULL,
                vapaa_kasi     TEXT    DEFAULT 'ei_nay',
                tulos          TEXT    DEFAULT 'epasela',
                huomio         TEXT    DEFAULT '',
                syotto_aika_ms INTEGER,
                luotu          TEXT    NOT NULL,
                FOREIGN KEY (ottelu_id) REFERENCES ottelut(id)
            );
            CREATE TABLE IF NOT EXISTS asetukset (
                avain TEXT PRIMARY KEY,
                arvo  TEXT NOT NULL
            );
        """)
        for avain, arvo in OLETUS_ASETUKSET.items():
            db.execute(
                "INSERT OR IGNORE INTO asetukset (avain, arvo) VALUES (?, ?)",
                (avain, arvo),
            )
        db.commit()
    # Lisää puuttuvat sarakkeet vanhoihin tietokantoihin
    uudet_sarakkeet = [
        ("havainnot", "kuvaus",     "TEXT DEFAULT ''"),
        ("havainnot", "jakso",      "TEXT DEFAULT ''"),
        ("havainnot", "vuoropari",  "TEXT DEFAULT ''"),
        ("havainnot", "tilanne",    "TEXT DEFAULT ''"),
        ("havainnot", "lyoja",      "TEXT DEFAULT ''"),
        ("havainnot", "etenija_1",  "TEXT DEFAULT ''"),
        ("havainnot", "etenija_2",  "TEXT DEFAULT ''"),
        ("havainnot", "etenija_3",  "TEXT DEFAULT ''"),
        ("ottelut",   "sarja",      "TEXT DEFAULT ''"),
    ]
    with _conn() as db:
        for taulu, sarake, maarittely in uudet_sarakkeet:
            try:
                db.execute(f"ALTER TABLE {taulu} ADD COLUMN {sarake} {maarittely}")
                db.commit()
            except Exception:
                pass  # sarake on jo olemassa
    _migroi_csv()


# ── Asetukset ──────────────────────────────────────────────────

def get_asetukset() -> dict:
    with _conn() as db:
        rows = db.execute("SELECT avain, arvo FROM asetukset").fetchall()
    result = dict(OLETUS_ASETUKSET)
    for r in rows:
        result[r["avain"]] = r["arvo"]
    return result


def paivita_asetukset(muutokset: dict):
    with _conn() as db:
        for avain, arvo in muutokset.items():
            db.execute(
                "INSERT OR REPLACE INTO asetukset (avain, arvo) VALUES (?, ?)",
                (avain, str(arvo)),
            )
        db.commit()


# ── Ottelut ────────────────────────────────────────────────────

def hae_ottelut() -> list:
    with _conn() as db:
        rows = db.execute(
            "SELECT o.id, o.nimi, o.vastustaja, o.luotu, COUNT(h.id) AS havainnot "
            "FROM ottelut o LEFT JOIN havainnot h ON h.ottelu_id = o.id "
            "GROUP BY o.id ORDER BY o.luotu DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def luo_ottelu(ottelu_id: str, nimi: str, vastustaja: str = "", sarja: str = ""):
    with _conn() as db:
        db.execute(
            "INSERT OR IGNORE INTO ottelut (id, nimi, vastustaja, sarja, luotu) VALUES (?, ?, ?, ?, ?)",
            (ottelu_id, nimi, vastustaja, sarja, datetime.now().isoformat()),
        )
        db.commit()


def hae_ottelu(ottelu_id: str) -> dict | None:
    with _conn() as db:
        row = db.execute("SELECT * FROM ottelut WHERE id=?", (ottelu_id,)).fetchone()
    return dict(row) if row else None


# ── Havainnot ──────────────────────────────────────────────────

def hae_havainnot(ottelu_id: str) -> list:
    with _conn() as db:
        rows = db.execute(
            "SELECT * FROM havainnot WHERE ottelu_id=? ORDER BY id",
            (ottelu_id,),
        ).fetchall()
    return [_row_to_havainto(r) for r in rows]


def hae_kaikki_havainnot() -> list:
    with _conn() as db:
        rows = db.execute("SELECT * FROM havainnot ORDER BY id").fetchall()
    return [_row_to_havainto(r) for r in rows]


def tallenna_havainto_db(havainto, ottelu_id: str, syotto_aika_ms=None):
    def g(attr): return getattr(havainto, attr, "") or ""
    with _conn() as db:
        db.execute(
            "INSERT INTO havainnot "
            "(ottelu_id, vuoro, pallot, etenijat, varit, vapaa_kasi, tulos, huomio, kuvaus, "
            " jakso, vuoropari, tilanne, lyoja, etenija_1, etenija_2, etenija_3, "
            " syotto_aika_ms, luotu) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                ottelu_id,
                havainto.vuoro, havainto.pallot, havainto.etenijat,
                json.dumps(havainto.värit, ensure_ascii=False),
                havainto.vapaa_käsi, havainto.tulos,
                g("huomio"), g("kuvaus"),
                g("jakso"), g("vuoropari"), g("tilanne"), g("lyoja"),
                g("etenija_1"), g("etenija_2"), g("etenija_3"),
                syotto_aika_ms, datetime.now().isoformat(),
            ),
        )
        db.commit()


def poista_viimeisin_db(ottelu_id: str):
    with _conn() as db:
        row = db.execute(
            "SELECT id FROM havainnot WHERE ottelu_id=? ORDER BY id DESC LIMIT 1",
            (ottelu_id,),
        ).fetchone()
        if row:
            db.execute("DELETE FROM havainnot WHERE id=?", (row["id"],))
            db.commit()


# ── Sisäiset ───────────────────────────────────────────────────

def _row_to_havainto(row):
    from merkinmurtaja import Havainto
    h = Havainto.__new__(Havainto)
    h.ottelu    = row["ottelu_id"]
    h.vuoro     = row["vuoro"]
    h.pallot    = row["pallot"]
    h.etenijat  = row["etenijat"]
    h.värit     = json.loads(row["varit"])
    h.vapaa_käsi = row["vapaa_kasi"]
    h.tulos     = row["tulos"]
    def rg(key): return row[key] if key in row.keys() else ""
    h.huomio    = rg("huomio")
    h.kuvaus    = rg("kuvaus")
    h.jakso     = rg("jakso")
    h.vuoropari = rg("vuoropari")
    h.tilanne   = rg("tilanne")
    h.lyoja     = rg("lyoja")
    h.etenija_1 = rg("etenija_1")
    h.etenija_2 = rg("etenija_2")
    h.etenija_3 = rg("etenija_3")
    h.aikaleima = row["luotu"]
    return h


def _migroi_csv():
    """Tuo vanhat CSV-tiedostot SQLiteen kerran käynnistyksessä."""
    data_dir = Path(__file__).parent / "data"
    for csv_file in data_dir.glob("*.csv"):
        ottelu_id = csv_file.stem
        with _conn() as db:
            if db.execute("SELECT 1 FROM ottelut WHERE id=?", (ottelu_id,)).fetchone():
                continue
        try:
            with open(csv_file, newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
        except Exception:
            continue
        if not rows:
            continue
        luo_ottelu(ottelu_id, ottelu_id.replace("_", " "))
        with _conn() as db:
            for r in rows:
                try:
                    varit_raw = r.get("värit", "-")
                    varit = [v.strip() for v in varit_raw.split("|") if v.strip()] or ["-"]
                    db.execute(
                        "INSERT INTO havainnot "
                        "(ottelu_id, vuoro, pallot, etenijat, varit, vapaa_kasi, tulos, huomio, luotu) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            ottelu_id,
                            int(r.get("vuoro", 1)),
                            int(r.get("pallot", 0)),
                            r.get("etenijat", "ei"),
                            json.dumps(varit, ensure_ascii=False),
                            r.get("vapaa_käsi", "ei_näy"),
                            r.get("tulos", "epäselvä"),
                            r.get("huomio", ""),
                            r.get("aikaleima", datetime.now().isoformat()),
                        ),
                    )
                except Exception:
                    continue
            db.commit()
