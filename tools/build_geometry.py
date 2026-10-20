"""Natural Earth rétegekből SVG-útvonalakat készít a térképhez.

Használat:
    python3 tools/build_geometry.py <natural_earth_mappa> data/geometry.json

A mappában a Natural Earth 10m rétegek kicsomagolt shapefile-jai legyenek
(mindegyik a saját nevű almappában, pl. ne_10m_roads/ne_10m_roads.shp).
Vetület: Egységes Országos Vetület (EOV, EPSG:23700).
"""

import json
import sys

import shapefile
from pyproj import Transformer
from shapely.geometry import LineString, Point, Polygon, shape
from shapely.ops import transform, unary_union

NE_DIR, OUT = sys.argv[1], sys.argv[2]

TO_EOV = Transformer.from_crs("EPSG:4326", "EPSG:23700", always_xy=True).transform

# Fő térkép: 1000 egység széles rajzlap
MAIN_W = 1000
PAD = 18

# A megyei jogú városok nevei helyesen (a Natural Earth-ben ékezethibásak)
CITY_NAMES = {
    "HU-SN": "Sopron", "HU-SD": "Szeged", "HU-ST": "Salgótarján", "HU-SK": "Szolnok",
    "HU-ED": "Érd", "HU-EG": "Eger", "HU-MI": "Miskolc", "HU-HV": "Hódmezővásárhely",
    "HU-DU": "Dunaújváros", "HU-KM": "Kecskemét", "HU-TB": "Tatabánya", "HU-GY": "Győr",
    "HU-SH": "Szombathely", "HU-ZE": "Zalaegerszeg", "HU-NK": "Nagykanizsa",
    "HU-VM": "Veszprém", "HU-KV": "Kaposvár", "HU-PS": "Pécs", "HU-SS": "Szekszárd",
    "HU-SF": "Székesfehérvár", "HU-BC": "Békéscsaba", "HU-DE": "Debrecen",
    "HU-NY": "Nyíregyháza",
}
# Címkét kapó városok (a többi csak pontként jelenik meg)
LABELLED = {
    "Debrecen", "Szeged", "Miskolc", "Pécs", "Győr", "Nyíregyháza", "Kecskemét",
    "Székesfehérvár", "Szombathely", "Szolnok", "Kaposvár", "Veszprém", "Békéscsaba",
    "Zalaegerszeg", "Eger", "Sopron", "Szekszárd", "Salgótarján", "Nagykanizsa", "Tatabánya",
}

# Budapest metróvonalai – sematikus nyomvonal az állomások közelítő koordinátái alapján
# (szélesség, hosszúság). Nem földmérési pontosságú.
METRO = {
    "M1": [(47.4966, 19.0505), (47.4974, 19.0544), (47.5007, 19.0561), (47.5025, 19.0586),
           (47.5054, 19.0631), (47.5077, 19.0668), (47.5106, 19.0712), (47.5131, 19.0749),
           (47.5147, 19.0779), (47.5188, 19.0818), (47.5209, 19.0898)],
    "M2": [(47.5005, 19.0244), (47.5072, 19.0256), (47.5065, 19.0386), (47.5055, 19.0468),
           (47.4975, 19.0548), (47.4935, 19.0605), (47.4963, 19.0702), (47.5003, 19.0841),
           (47.5025, 19.1028), (47.5030, 19.1185), (47.5035, 19.1365)],
    "M3": [(47.5606, 19.0910), (47.5497, 19.0786), (47.5425, 19.0703), (47.5348, 19.0727),
           (47.5283, 19.0670), (47.5196, 19.0651), (47.5167, 19.0617), (47.5107, 19.0569),
           (47.5035, 19.0538), (47.4973, 19.0548), (47.4935, 19.0565), (47.4893, 19.0617),
           (47.4859, 19.0707), (47.4834, 19.0803), (47.4783, 19.0900), (47.4760, 19.0984),
           (47.4728, 19.1087), (47.4669, 19.1176), (47.4617, 19.1302), (47.4624, 19.1494)],
    "M4": [(47.4641, 19.0203), (47.4710, 19.0320), (47.4745, 19.0450), (47.4776, 19.0474),
           (47.4840, 19.0540), (47.4870, 19.0595), (47.4895, 19.0620), (47.4927, 19.0712),
           (47.4960, 19.0810), (47.5007, 19.0840)],
}


# Feliratok a nagyításon (szélesség, hosszúság)
INSET_LABELS = {"Buda": (47.505, 18.975), "Pest": (47.468, 19.175), "Csepel": (47.405, 19.072)}


def chaikin(poly, rounds=2):
    """Lekerekíti a durva (24 csúcsú) Natural Earth fővároshatárt."""
    pts = list(poly.exterior.coords)[:-1]
    for _ in range(rounds):
        nxt = []
        for i, (x0, y0) in enumerate(pts):
            x1, y1 = pts[(i + 1) % len(pts)]
            nxt.append((0.75 * x0 + 0.25 * x1, 0.75 * y0 + 0.25 * y1))
            nxt.append((0.25 * x0 + 0.75 * x1, 0.25 * y0 + 0.75 * y1))
        pts = nxt
    return Polygon(pts)


def reader(name):
    return shapefile.Reader(f"{NE_DIR}/{name}/{name}", encoding="utf-8")


def records(name):
    r = reader(name)
    fields = [f[0] for f in r.fields[1:]]
    for sr in r.iterShapeRecords():
        yield dict(zip(fields, sr.record)), shape(sr.shape.__geo_interface__)


def eov(geom):
    return transform(TO_EOV, geom)


class Frame:
    """EOV méterből rajzlap-koordinátába (y lefelé nő)."""

    def __init__(self, bounds, width, pad):
        minx, miny, maxx, maxy = bounds
        self.k = (width - 2 * pad) / (maxx - minx)
        self.minx, self.maxy, self.pad = minx, maxy, pad
        self.w = width
        self.h = round((maxy - miny) * self.k + 2 * pad, 1)

    def xy(self, x, y):
        return ((x - self.minx) * self.k + self.pad, (self.maxy - y) * self.k + self.pad)

    def geom(self, g):
        return transform(lambda x, y, z=None: self.xy(x, y), g)


def fmt(v):
    s = f"{v:.1f}"
    return s[:-2] if s.endswith(".0") else s


def path_d(g):
    """Shapely geometriából SVG path 'd' attribútum."""
    parts = []

    def ring(coords, close):
        pts = list(coords)
        if len(pts) < 2:
            return
        out = [f"M{fmt(pts[0][0])} {fmt(pts[0][1])}"]
        for x, y in pts[1:]:
            out.append(f"L{fmt(x)} {fmt(y)}")
        if close:
            out.append("Z")
        parts.append("".join(out))

    def walk(geom):
        t = geom.geom_type
        if t == "Polygon":
            ring(geom.exterior.coords, True)
            for i in geom.interiors:
                ring(i.coords, True)
        elif t == "LineString":
            ring(geom.coords, False)
        elif t in ("MultiPolygon", "MultiLineString", "GeometryCollection"):
            for sub in geom.geoms:
                walk(sub)

    walk(g)
    return "".join(parts)


def main():
    hun = next(g for rec, g in records("ne_10m_admin_0_countries") if rec["ADM0_A3"] == "HUN")
    hun_e = eov(hun)
    frame = Frame(hun_e.bounds, MAIN_W, PAD)

    adm1 = [(rec, eov(g)) for rec, g in records("ne_10m_admin_1_states_provinces") if rec["adm0_a3"] == "HUN"]
    bud_e = chaikin(next(g for rec, g in adm1 if rec["iso_3166_2"] == "HU-BU"))

    # Megyehatárok: a megyék (nem városok) körvonalai az ország határán belül
    counties = [g for rec, g in adm1 if rec["type_en"] == "County"]
    county_lines = unary_union([c.boundary for c in counties]).intersection(hun_e.buffer(-300))

    # Városok: megyei jogú városok poligonjainak középpontja + Natural Earth település-pontok
    cities = []
    for rec, g in adm1:
        code = rec["iso_3166_2"]
        if code in CITY_NAMES:
            c = g.representative_point()
            cities.append({"name": CITY_NAMES[code], "pt": c})
    # A Natural Earth pontok pontosabbak a városközpontra
    pp = {rec["NAME"]: eov(g) for rec, g in records("ne_10m_populated_places") if rec["ADM0_A3"] == "HUN"}
    for c in cities:
        if c["name"] in pp:
            c["pt"] = pp[c["name"]]

    # Beépített területek (vidék): Budapest közigazgatási területe nélkül
    urban = []
    for rec, g in records("ne_10m_urban_areas"):
        ge = eov(g)
        if not ge.intersects(hun_e):
            continue
        ge = ge.intersection(hun_e).difference(bud_e.buffer(150))
        if ge.is_empty or ge.area < 2.5e6:  # 2,5 km² alatti foltok elhagyása
            continue
        urban.append(ge.simplify(180))
    urban_u = unary_union(urban)

    # Utak: gyorsforgalmi (expressway=1) és egyéb főutak, az országhatáron belül
    motorways, mainroads = [], []
    for rec, g in records("ne_10m_roads"):
        ge = eov(g)
        if not ge.intersects(hun_e):
            continue
        ge = ge.intersection(hun_e)
        if ge.is_empty:
            continue
        (motorways if rec["expressway"] == 1 else mainroads).append(ge)
    motor_u = unary_union(motorways).simplify(200)
    main_u = unary_union(mainroads).simplify(200)

    # Vizek
    rivers = []
    keep = {"Danube", "Donau", "Tisza", "Tisa", "Drau", "Raab", "Soroksari Duna", "Mosoni-Duna",
            "Crisul Alb", "Sebes Koros", "Zagyva", "Slana", "Hornád", "Ipel", "Sió", "Zala"}
    for name in ("ne_10m_rivers_lake_centerlines", "ne_10m_rivers_europe"):
        for rec, g in records(name):
            if rec.get("name") in keep:
                ge = eov(g).intersection(hun_e.buffer(500))
                if not ge.is_empty:
                    rivers.append((rec.get("name"), ge))
    big_rivers = unary_union([g for n, g in rivers if n in ("Danube", "Donau", "Tisza", "Tisa", "Soroksari Duna")]).simplify(150)
    small_rivers = unary_union([g for n, g in rivers if n not in ("Danube", "Donau", "Tisza", "Tisa", "Soroksari Duna")]).simplify(200)
    lakes = []
    for name in ("ne_10m_lakes", "ne_10m_lakes_europe"):
        for rec, g in records(name):
            if rec.get("name") in ("Lake Balaton", "Lake Tisza"):
                lakes.append(eov(g).intersection(hun_e))
    lakes_u = unary_union(lakes).simplify(120)

    F = frame.geom
    out = {
        "main": {
            "w": frame.w,
            "h": frame.h,
            "country": path_d(F(hun_e.simplify(250))),
            "budapest": path_d(F(bud_e)),
            "counties": path_d(F(county_lines.simplify(250))),
            "urban": path_d(F(urban_u)),
            "motorways": path_d(F(motor_u)),
            "mainroads": path_d(F(main_u)),
            "rivers": path_d(F(big_rivers)),
            "smallRivers": path_d(F(small_rivers)),
            "lakes": path_d(F(lakes_u)),
            "cities": [],
        }
    }
    for c in sorted(cities, key=lambda c: c["name"]):
        x, y = frame.xy(c["pt"].x, c["pt"].y)
        out["main"]["cities"].append({"name": c["name"], "x": round(x, 1), "y": round(y, 1),
                                      "label": c["name"] in LABELLED})
    bx, by = frame.xy(bud_e.centroid.x, bud_e.centroid.y)
    out["main"]["budapestCenter"] = {"x": round(bx, 1), "y": round(by, 1)}
    bxmin, bymin = frame.xy(bud_e.bounds[0], bud_e.bounds[3])
    bxmax, bymax = frame.xy(bud_e.bounds[2], bud_e.bounds[1])
    out["main"]["budapestBox"] = [round(bxmin, 1), round(bymin, 1), round(bxmax, 1), round(bymax, 1)]

    # Budapest-nagyítás: saját keret a főváros határa körül
    inset_bounds = bud_e.buffer(1200).bounds
    iframe = Frame(inset_bounds, 420, 10)
    IF = iframe.geom
    danube_inset = unary_union([g for n, g in rivers if n in ("Danube", "Donau", "Soroksari Duna")])
    danube_inset = danube_inset.intersection(bud_e.buffer(1200).envelope)
    urban_ring = unary_union([eov(g) for rec, g in records("ne_10m_urban_areas")
                              if eov(g).intersects(bud_e)]).intersection(bud_e.buffer(1200).envelope).difference(bud_e)
    metro = {}
    for line, pts in METRO.items():
        ls = eov(LineString([(lon, lat) for lat, lon in pts]))
        metro[line] = path_d(IF(ls))
    stations = {}
    for line, pts in METRO.items():
        for lat, lon in (pts[0], pts[-1]):
            p = eov(Point(lon, lat))
            x, y = iframe.xy(p.x, p.y)
            stations.setdefault(line, []).append([round(x, 1), round(y, 1)])
    labels = {}
    for name, (lat, lon) in INSET_LABELS.items():
        p = eov(Point(lon, lat))
        x, y = iframe.xy(p.x, p.y)
        labels[name] = [round(x, 1), round(y, 1)]
    out["inset"] = {
        "w": iframe.w,
        "h": iframe.h,
        "budapest": path_d(IF(bud_e)),
        "danube": path_d(IF(danube_inset)),
        "agglo": path_d(IF(urban_ring.simplify(150))),
        "metro": metro,
        "termini": stations,
        "labels": labels,
    }

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    sizes = {k: len(v) for k, v in out["main"].items() if isinstance(v, str)}
    print("main", frame.w, frame.h, sizes)
    print("inset", iframe.w, iframe.h, {k: len(v) if isinstance(v, str) else len(json.dumps(v)) for k, v in out["inset"].items()})
    print("cities", len(out["main"]["cities"]))


if __name__ == "__main__":
    main()
