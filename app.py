#!/usr/bin/env python3
"""
MERKINMURTAJA — Flask web-sovellus
Käynnistys: python app.py  →  http://localhost:5000
"""
import os
from flask import (Flask, render_template, request, redirect,
                   url_for, session, flash)
from datetime import datetime

from database import (
    init_db, get_asetukset, paivita_asetukset,
    hae_ottelut, luo_ottelu, hae_ottelu,
    hae_havainnot, hae_kaikki_havainnot,
    tallenna_havainto_db, poista_viimeisin_db,
)
from merkinmurtaja import (
    Havainto, Analysoija,
    VÄRIT, KÄSIEN_ASENNOT, TULOKSET, SARJAT, TILANTEET,
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "muuta-tama-tuotannossa-abc123")

TIIMI_KOODI = os.environ.get("TIIMI_KOODI", "")  # tyhjä = ei vaadita koodia

init_db()


# ── Auth-apufunktiot ───────────────────────────────────────────

def kirjautunut() -> bool:
    return bool(session.get("kayttaja"))


def vaadi_kirjautuminen():
    if not kirjautunut():
        return redirect(url_for("kirjaudu"))
    return None


# ── Kirjautuminen ──────────────────────────────────────────────

@app.route("/kirjaudu", methods=["GET", "POST"])
def kirjaudu():
    if request.method == "POST":
        nimi = request.form.get("nimi", "").strip()
        koodi = request.form.get("koodi", "").strip()
        if not nimi:
            flash("Anna nimesi.")
            return render_template("kirjaudu.html", vaatii_koodin=bool(TIIMI_KOODI))
        if TIIMI_KOODI and koodi != TIIMI_KOODI:
            flash("Väärä tiimiläisten koodi.")
            return render_template("kirjaudu.html", vaatii_koodin=True)
        session["kayttaja"] = nimi
        return redirect(url_for("etusivu"))
    return render_template("kirjaudu.html", vaatii_koodin=bool(TIIMI_KOODI))


@app.route("/kirjaudu/ulos")
def kirjaudu_ulos():
    session.clear()
    return redirect(url_for("kirjaudu"))


# ── Etusivu ────────────────────────────────────────────────────

@app.route("/")
def etusivu():
    ohjaus = vaadi_kirjautuminen()
    if ohjaus:
        return ohjaus
    return render_template("etusivu.html",
                           ottelut=hae_ottelut(),
                           kayttaja=session["kayttaja"],
                           now_pvm=datetime.now().strftime("%d.%m.%Y"))


# ── Ottelu: uusi ───────────────────────────────────────────────

@app.route("/ottelu/uusi", methods=["POST"])
def uusi_ottelu():
    ohjaus = vaadi_kirjautuminen()
    if ohjaus:
        return ohjaus
    vastustaja = request.form.get("vastustaja", "").strip()
    pvm = request.form.get("pvm", "").strip() or datetime.now().strftime("%d.%m.%Y")
    sarja = request.form.get("sarja", "").strip()
    if vastustaja:
        nimi = f"{vastustaja} {pvm}"
    else:
        nimi = f"Ottelu {pvm}"
    ottelu_id = nimi.replace(" ", "_").replace("/", "-").replace(".", "")
    luo_ottelu(ottelu_id, nimi, vastustaja, sarja)
    return redirect(url_for("ottelu_syotto", ottelu_id=ottelu_id))


# ── Ottelu: syöttö ─────────────────────────────────────────────

@app.route("/ottelu/<ottelu_id>")
def ottelu_syotto(ottelu_id: str):
    ohjaus = vaadi_kirjautuminen()
    if ohjaus:
        return ohjaus
    ottelu = hae_ottelu(ottelu_id)
    havainnot = hae_havainnot(ottelu_id)
    asetukset = get_asetukset()
    return render_template(
        "syotto.html",
        ottelu_id=ottelu_id,
        ottelu_nimi=ottelu["nimi"] if ottelu else ottelu_id.replace("_", " "),
        havainnot=havainnot,
        värit=VÄRIT,
        käsien_asennot=KÄSIEN_ASENNOT,
        tulokset=TULOKSET,
        asetukset=asetukset,
        tilanteet=TILANTEET,
        kayttaja=session["kayttaja"],
    )


# ── Ottelu: tallenna havainto ──────────────────────────────────

@app.route("/ottelu/<ottelu_id>/tallenna", methods=["POST"])
def tallenna(ottelu_id: str):
    ohjaus = vaadi_kirjautuminen()
    if ohjaus:
        return ohjaus
    f = request.form
    värit_valitut = f.getlist("värit") or ["-"]
    syotto_aika_ms = f.get("syotto_aika_ms", "").strip()
    syotto_aika_ms = int(syotto_aika_ms) if syotto_aika_ms.lstrip("-").isdigit() else None

    havainto = Havainto(
        ottelu=ottelu_id.replace("_", " "),
        vuoro=int(f.get("vuoro", 1)),
        pallot=int(f.get("pallot", 0)),
        etenijat=f.get("etenijat", "ei"),
        värit=värit_valitut,
        vapaa_käsi=f.get("vapaa_käsi", "ei_näy"),
        tulos=f.get("tulos", "epäselvä"),
        huomio=f.get("huomio", ""),
        kuvaus=f.get("kuvaus", ""),
        jakso=f.get("jakso", ""),
        vuoropari=f.get("vuoropari", ""),
        tilanne=f.get("tilanne", ""),
        lyoja=f.get("lyoja", ""),
        etenija_1=f.get("etenija_1", ""),
        etenija_2=f.get("etenija_2", ""),
        etenija_3=f.get("etenija_3", ""),
    )
    tallenna_havainto_db(havainto, ottelu_id, syotto_aika_ms)
    return redirect(url_for("ottelu_syotto", ottelu_id=ottelu_id))


# ── Ottelu: poista viimeisin ───────────────────────────────────

@app.route("/ottelu/<ottelu_id>/poista_viimeisin", methods=["POST"])
def poista_viimeisin(ottelu_id: str):
    ohjaus = vaadi_kirjautuminen()
    if ohjaus:
        return ohjaus
    poista_viimeisin_db(ottelu_id)
    return redirect(url_for("ottelu_syotto", ottelu_id=ottelu_id))


# ── Analyysi ───────────────────────────────────────────────────

@app.route("/ottelu/<ottelu_id>/analyysi")
def analyysi(ottelu_id: str):
    ohjaus = vaadi_kirjautuminen()
    if ohjaus:
        return ohjaus
    ottelu = hae_ottelu(ottelu_id)
    havainnot = hae_havainnot(ottelu_id)
    yhteenveto = Analysoija(havainnot).yhteenveto()
    return render_template(
        "analyysi.html",
        ottelu_id=ottelu_id,
        ottelu_nimi=ottelu["nimi"] if ottelu else ottelu_id.replace("_", " "),
        yhteenveto=yhteenveto,
        tulokset_selitykset=TULOKSET,
        kayttaja=session.get("kayttaja", ""),
    )


@app.route("/analyysi/kaikki")
def analyysi_kaikki():
    ohjaus = vaadi_kirjautuminen()
    if ohjaus:
        return ohjaus
    kaikki = hae_kaikki_havainnot()
    yhteenveto = Analysoija(kaikki).yhteenveto()
    return render_template(
        "analyysi.html",
        ottelu_id=None,
        ottelu_nimi=f"Kaikki ottelut ({len(kaikki)} havaintoa)",
        yhteenveto=yhteenveto,
        tulokset_selitykset=TULOKSET,
        kayttaja=session.get("kayttaja", ""),
    )


# ── Asetukset ──────────────────────────────────────────────────

@app.route("/asetukset", methods=["GET", "POST"])
def asetukset():
    ohjaus = vaadi_kirjautuminen()
    if ohjaus:
        return ohjaus
    if request.method == "POST":
        paivita_asetukset({
            "lento_max_ms":       request.form.get("lento_max_ms", "500"),
            "nopea_vaara_max_ms": request.form.get("nopea_vaara_max_ms", "1200"),
            "vaarat_pois_max_ms": request.form.get("vaarat_pois_max_ms", "2800"),
        })
        flash("Asetukset tallennettu!")
        return redirect(url_for("asetukset"))
    return render_template("asetukset.html",
                           asetukset=get_asetukset(),
                           kayttaja=session["kayttaja"])


# ── Käynnistys ─────────────────────────────────────────────────

if __name__ == "__main__":
    import socket
    try:
        local_ip = socket.gethostbyname(socket.gethostname())
    except Exception:
        local_ip = "127.0.0.1"
    print(f"\n🏟  MERKINMURTAJA käynnissä!")
    print(f"   Tietokone:  http://localhost:5000")
    print(f"   Puhelin:    http://{local_ip}:5000")
    if TIIMI_KOODI:
        print(f"   Tiimiläisten koodi: {TIIMI_KOODI}")
    print()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
