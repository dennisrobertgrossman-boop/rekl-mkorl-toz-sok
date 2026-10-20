"""Az NMHH reklámkataszter Excel-állományából területenkénti óriásplakát-összesítést készít.

Használat:
    python3 tools/summarize_kataszter.py <reklameszkozok-nyilvantartasa.xlsx> data/kataszter_osszesites.json

- Budapest: a település „Budapest”, vagy a vármegye/kerület mező budapesti kerületet jelöl.
  (Az irányítószám-mező nem megbízható: vidéki eszközöknél is előfordul 1-gyel kezdődő szám.)
- Metró: budapesti tétel, amelynek kiegészítő címleírása „METRÓ”-val kezdődik, a felszíni Pillangó utca és
  Örs vezér tere állomás (HRSZ_39206/32) nélkül.
- Külterület (módszertani feltevés, nem jogi minősítés): a helyrajzi szám 0-val kezdődik. A helyrajzi számot
  a cím, ennek hiányában a kiegészítő címleírás mezőben keressük. Az utcacímmel nyilvántartott vidéki
  eszközök közül a településen kívüli útszakaszt leíró tételeket arányosan becsüljük külterületinek
  (a helyrajzi számmal is rendelkező, hasonló leírású tételek külterületi aránya alapján).
"""

import json
import re
import sys

import pandas as pd

SRC, OUT = sys.argv[1], sys.argv[2]
COLS = ["sorszam", "azon", "megye", "irsz", "telepules", "cim", "kieg", "tipus", "feluletek", "megj"]

xl = pd.ExcelFile(SRC)
sheet = xl.sheet_names[0]
df = pd.read_excel(xl, sheet_name=sheet, header=1, dtype=str)
df.columns = COLS
snapshot = re.search(r"\((.*?)\)", sheet).group(1) if "(" in sheet else sheet

MARKER_BEFORE = re.compile(r"(?:hrsz|\bhr\.|helyrajzi\s*sz[aá]m)\.?\s*[:.]?\s*(\d[\d/]*)", re.I)
MARKER_AFTER = re.compile(r"(?<![\d/])(\d[\d/]*)\.?\s*(?:hrsz|helyrajzi)", re.I)
BARE_FIELD = re.compile(r"\s*(\d[\d/]*)\.?\s*")
BARE_ZERO = re.compile(r"(?<![\d/])(0\d*/\d+)(?![\d/])")


def norm(text):
    text = re.sub(r"(?<=\d)_(?=\d)", "/", text)
    return text.replace("_", " ")


def parcel(text, whole_field=True):
    """A mezőben szereplő helyrajzi szám, vagy None."""
    if not isinstance(text, str) or not text.strip():
        return None
    t = norm(text)
    for rx in (MARKER_BEFORE, MARKER_AFTER):
        m = rx.search(t)
        if m:
            return m.group(1)
    if whole_field:
        m = BARE_FIELD.fullmatch(t)
        if m:
            return m.group(1)
    m = BARE_ZERO.search(t)
    return m.group(1) if m else None


def foldreszlet(row):
    """'kulterulet', 'belterulet' (helyrajzi szám alapján) vagy 'utcacim'."""
    p = parcel(row["cim"]) or parcel(row["kieg"], whole_field=False)
    if p is None:
        return "utcacim"
    return "kulterulet" if p.startswith("0") else "belterulet"


# Településen kívüli útszakaszt leíró szövegek (autópálya-kilométer, városhatár, főút-kilométer utcanév nélkül)
STREET = re.compile(r"\b(utca|u\.|út\s+\d|útja|tér|krt|körút|sor|köz|sétány|park|lakótelep)\b", re.I)
MOTORWAY_KM = re.compile(r"(\bM\s?\d{1,2}\b|autópálya|autóút).*?\d+\s*[+,.]\s*\d+\s*(km|kmsz)|(\bM\s?\d{1,2}\b|autópálya|autóút).*?\bkm", re.I)
CITY_LIMIT = re.compile(r"városhatár|település\s*határ|községhatár", re.I)
ROAD_KM = re.compile(r"\b\d{1,3}\s*[-.]?\s*(es|as|ös|os|sz\.?)?\s*(fő)?út.*?\d+\s*[+,.]\s*\d+\s*(km|kmsz)|\bkm\s*sz", re.I)


def leiras_tipus(row):
    text = " ".join(x for x in (row["cim"], row["kieg"]) if isinstance(x, str))
    if MOTORWAY_KM.search(text) and not STREET.search(text):
        return "autopalya_km"
    if CITY_LIMIT.search(text):
        return "varoshatar"
    if ROAD_KM.search(text) and not STREET.search(text):
        return "fout_km"
    return None


df["budapest"] = df["telepules"].str.strip().str.lower().eq("budapest") | df["megye"].str.startswith("Budapest", na=False)
df["fold"] = df.apply(foldreszlet, axis=1)
df["leiras"] = df.apply(leiras_tipus, axis=1)
o = df[df["tipus"] == "óriásplakát"]

bud = o[o["budapest"]]
vid = o[~o["budapest"]]
FELSZINI = {"HRSZ_39206/32"}  # Pillangó utca, Örs vezér tere: felszíni M2-állomás
metro = bud[bud["kieg"].fillna("").str.match(r"^\s*METR[OÓ]\b", case=False) & ~bud["cim"].isin(FELSZINI)]

vid_kul = vid[vid["fold"] == "kulterulet"]
vid_utca = vid[vid["fold"] == "utcacim"]
# Becslés: a hasonló leírású, helyrajzi számmal is rendelkező vidéki tételek külterületi aránya
becsult_kul = 0.0
arany = {}
for tipus in ("autopalya_km", "varoshatar", "fout_km"):
    ref = vid[(vid["leiras"] == tipus) & (vid["fold"] != "utcacim")]
    r = float((ref["fold"] == "kulterulet").mean()) if len(ref) else 0.0
    n = int((vid_utca["leiras"] == tipus).sum())
    arany[tipus] = {"utcacimes_tetel": n, "referencia_tetel": int(len(ref)), "kulterulet_arany": round(r, 3)}
    becsult_kul += n * r

HONAP = ["január", "február", "március", "április", "május", "június", "július", "augusztus",
         "szeptember", "október", "november", "december"]
d = re.match(r"(\d{4})\.(\d{2})\.(\d{2})", snapshot)
allapot = f"{d.group(1)}. {HONAP[int(d.group(2)) - 1]} {int(d.group(3))}." if d else snapshot

out = {
    "forras": "NMHH reklámkataszter, " + snapshot,
    "allapot_hu": allapot,
    "osszes_reklameszkoz": int(len(df)),
    "oriasplakat": {
        "orszagos": int(len(o)),
        "budapest": int(len(bud)),
        "budapest_metro": int(len(metro)),
        "videk": int(len(vid)),
        "videk_kulterulet_hrsz": int(len(vid_kul)),
        "videk_kulterulet_becsult_utcacimes": round(becsult_kul),
        "videk_belterulet_hrsz": int((vid["fold"] == "belterulet").sum()),
        "videk_utcacim": int(len(vid_utca)),
        "kulterulet_becsles": arany,
        "videk_megyenkent": {k: int(v) for k, v in vid["megye"].value_counts().items()},
        "budapest_keruletenkent": {k: int(v) for k, v in bud["megye"].value_counts().items()},
    },
    "tipusonkent": {k: int(v) for k, v in df["tipus"].value_counts().items()},
}
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(json.dumps({k: v for k, v in out["oriasplakat"].items() if k not in ("videk_megyenkent", "budapest_keruletenkent")}, ensure_ascii=False, indent=1))
