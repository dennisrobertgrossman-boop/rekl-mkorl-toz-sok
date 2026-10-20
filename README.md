# Óriásplakát-tilalom 2026 – interaktív térkép

Egyoldalas weboldal (`index.html`): Magyarország térképén mutatja, hány óriásplakát van jelenleg az egyes vizsgált területeken, és a kormányrendelet-tervezet szerint ebből várhatóan mennyi marad meg. A kurzort egy területre víve (érintőképernyőn koppintásra) felugró ablak jelenik meg a két számmal.

## Számok

| Terület | Jelenleg | Várhatóan megmarad |
|---|---|---|
| Országosan | 20 562 | 1 000–1 550 |
| Budapest | 8 318 | 251 |
| – metró föld alatti üzemi területe | 251 | 251 |
| Az ország többi része (vidék) | 12 244 | 750–1 300 |
| – belterület általában | 9 650–10 450 | 0 |
| – gazdasági és nagy kereskedelmi övezet, gyalogos aluljáró | 750–1 300 | 750–1 300 |
| – külterület | 1 000–1 350 | 0 |

- **Jelenleg:** a Nemzeti Média- és Hírközlési Hatóság reklámkatasztere (2026. október 12-i állapot), „óriásplakát” típusú eszközök. Budapest a település, illetve a kerület alapján; a metróállomásokon lévő tételek a kiegészítő címleírás alapján. Belterület és külterület a helyrajzi szám alapján, azzal a módszertani feltevéssel, hogy a 0-val kezdődő helyrajzi számú ingatlan külterületen fekszik; az utcacímmel nyilvántartott, településen kívüli útszakaszt leíró tételek egy részét arányosan külterületinek becsültük. A felosztás közelítés, nem jogi minősítés.
- **Várhatóan megmarad:** becslés a Magyar Reklámszövetség két közölt számításából (a fővárosi tilalom nélkül számolva a tervezet országosan mintegy 90%-ot szüntetne meg, Budapesten 780 maradna; a fővárosi tilalommal együtt mintegy 95% a csökkenés). Budapesten a fővárosi tilalom miatt csak a metró föld alatti üzemi területén lévő óriásplakátok maradhatnak fenn.
- A területi kategóriák az „Óriásplakátok: mi változott és mi változik” című, 2026. október 13-i összefoglalóból származnak. Az oldal jogszabályhelyet nem idéz.

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
