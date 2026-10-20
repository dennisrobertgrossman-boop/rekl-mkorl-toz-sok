"""Az NMHH reklámkataszter Excel-állományából területenkénti óriásplakát-összesítést készít.

Használat:
    python3 tools/summarize_kataszter.py <reklameszkozok-nyilvantartasa.xlsx> data/kataszter_osszesites.json

- Budapest: a település „Budapest”, vagy a vármegye/kerület mező budapesti kerületet jelöl.
  (Az irányítószám-mező nem megbízható: vidéki eszközöknél is előfordul 1-gyel kezdődő szám.)
- Külterület: a helyrajzi szám 0-val kezdődik. Az utcacímmel nyilvántartott eszköz belterületinek számít.
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

HRSZ = re.compile(r"^\s*(?:hrsz[\s_.:]*)?(\d[\d/]*[A-Za-z]?)\s*(?:hrsz\.?)?\s*$", re.I)


def foldreszlet(cim):
    """'kulterulet', 'belterulet' (helyrajzi szám alapján) vagy 'utcacim'."""
    if not isinstance(cim, str) or not cim.strip():
        return "utcacim"
    m = HRSZ.match(cim)
    if not m:
        return "utcacim"
    return "kulterulet" if m.group(1).startswith("0") else "belterulet"


df["budapest"] = df["telepules"].str.strip().str.lower().eq("budapest") | df["megye"].str.startswith("Budapest", na=False)
df["fold"] = df["cim"].map(foldreszlet)
o = df[df["tipus"] == "óriásplakát"]

bud = o[o["budapest"]]
vid = o[~o["budapest"]]
vid_kul = vid[vid["fold"] == "kulterulet"]
vid_bel = vid[vid["fold"] != "kulterulet"]

# A metró föld alatti felületei: nyilvántartott metrós óriásplakát (áruházlánc-nevek nélkül)
metro_mask = o["kieg"].fillna("").str.contains(r"\bmetr[oó]\b.*(?:állomás|peron|aluljáró|lejáró)|(?:állomás|peron|lejáró).*\bmetr[oó]\b", case=False, regex=True)
metro = o[metro_mask & o["budapest"]]

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
        "budapest_kulterulet": int((bud["fold"] == "kulterulet").sum()),
        "videk": int(len(vid)),
        "videk_belterulet": int(len(vid_bel)),
        "videk_belterulet_hrsz": int((vid["fold"] == "belterulet").sum()),
        "videk_belterulet_utcacim": int((vid["fold"] == "utcacim").sum()),
        "videk_kulterulet": int(len(vid_kul)),
        "budapest_metro_kulcsszo": int(len(metro)),
        "videk_megyenkent": {k: int(v) for k, v in vid["megye"].value_counts().items()},
        "budapest_keruletenkent": {k: int(v) for k, v in bud["megye"].value_counts().items()},
    },
    "tipusonkent": {k: int(v) for k, v in df["tipus"].value_counts().items()},
}
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(json.dumps({k: v for k, v in out["oriasplakat"].items() if not isinstance(v, dict)}, ensure_ascii=False, indent=1))
print("metro minták:", metro[["megye", "kieg"]].head(10).to_string() if len(metro) else "nincs")
print("külterületi vidéki minták:")
print(vid_kul[["telepules", "cim", "kieg"]].sample(min(12, len(vid_kul)), random_state=3).to_string())
