# Óriásplakát-tilalom 2026 – interaktív térkép

Egyoldalas weboldal (`index.html`): Magyarország térképén mutatja, hány óriásplakát van jelenleg az egyes vizsgált területeken, és a kormányrendelet-tervezet szerint ebből várhatóan mennyi marad meg. A kurzort egy területre víve (érintőképernyőn koppintásra) felugró ablak jelenik meg a két számmal.

## Számok

| Terület | Jelenleg | Várhatóan megmarad |
|---|---|---|
| Országosan | 20 562 | ≈ 1 000–1 300 |
| Budapest | 8 318 | 0 |
| Az ország többi része (vidék) | 12 244 | ≈ 1 000–1 300 |
| – belterület általában | ≈ 10 000–10 300 | 0 |
| – gazdasági és nagy kereskedelmi övezet | ≈ 1 000–1 300 | ≈ 1 000–1 300 |
| – külterület | 949 | 0 |

- **Jelenleg:** a Nemzeti Média- és Hírközlési Hatóság reklámkatasztere (2026. október 12-i állapot), „óriásplakát” típusú eszközök. Budapest a település, illetve a kerület alapján; belterület és külterület a helyrajzi szám alapján (a 0-val kezdődő helyrajzi szám külterületi, az utcacímmel nyilvántartott eszköz belterületinek számít).
- **Várhatóan megmarad:** becslés a Magyar Reklámszövetség két közölt számításából (a tervezet országosan mintegy 90%-ot szüntetne meg, Budapesten 780 maradna; a fővárosi tilalommal együtt mintegy 95% a csökkenés). Budapesten a fővárosi tilalom miatt nem marad nyilvántartott óriásplakát.
- A területi kategóriák a „Óriásplakátok: mi változott és mi változik” című, 2026. október 13-i összefoglalóból származnak. Az oldal jogszabályhelyet nem idéz.

## Újraépítés

```sh
pip install pandas openpyxl pyshp shapely pyproj
python3 tools/summarize_kataszter.py <reklameszkozok-nyilvantartasa.xlsx> data/kataszter_osszesites.json
python3 tools/build_geometry.py <natural_earth_mappa> data/geometry.json   # csak a térkép újrarajzolásához
python3 tools/build_page.py
```

- `src/template.html` – az oldal forrása
- `data/kataszter_osszesites.json` – a reklámkataszter területenkénti összesítése
- `data/geometry.json` – a térkép rajzolata (Natural Earth, Egységes Országos Vetület)

Térképalap: [Natural Earth](https://www.naturalearthdata.com/) (közkincs). A budapesti metróvonalak nyomvonala sematikus.
