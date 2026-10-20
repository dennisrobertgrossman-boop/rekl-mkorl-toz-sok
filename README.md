# Óriásplakát-tilalom 2026 – interaktív térkép

Egyoldalas weboldal (`index.html`), amely Magyarország térképén mutatja az óriásplakát-szabályozás 2026. októberi változásának területi kategóriáit, és felugró ablakban a becsült plakátvesztést.

- **Budapest** és **az ország többi része (vidék)** külön-külön bejárható a kurzorral.
- A forrásdokumentum területi kategóriái külön rétegként jelennek meg: belterület általában, gazdasági és nagy kereskedelmi övezet, gyalogos aluljáró és metró üzemi területe, közút lakott területen kívüli szakasza mellett, védett területek.
- Három időállapot váltható: **Régen** (2026. szeptember 30-ig), **Most** (2026. október 1-jétől), **Tervezet szerint** (a kormányrendelet-tervezet kihirdetése esetén).

## Megnyitás

Az `index.html` önálló fájl, internetkapcsolat nélkül is megnyitható böngészőben.

## Számok

| | Érték | Forrás |
|---|---|---|
| Országos óriásplakát-állomány | ≈ 21 000 | Telex, 2026. június 23. (a Nemzeti Média- és Hírközlési Hatóság adatbázisa alapján) |
| Budapest | 8 393 | Infostart, 2026. június 25. (reklámkataszter) |
| Vidék | ≈ 12 600 | a kettő különbsége |
| Megszűnés a tervezet szerint | ≈ 19 600–20 000 (93–95%) | becslés, lásd alább |

A becslés lépései az oldal „Hogyan számoltunk?” részében szerepelnek. Röviden: Budapesten a fővárosi tilalom miatt a teljes nyilvántartott állomány érintett; vidéken a Magyar Reklámszövetség két közölt számításából (országosan ≈ 90%, illetve ≈ 95% csökkenés) ≈ 1 000–1 400 óriásplakát maradhat.

**Korlát:** a Nemzeti Média- és Hírközlési Hatóság reklámkataszterét a munka idején nem lehetett közvetlenül letölteni, a számok a kataszterre hivatkozó sajtóközlésekből származnak. A belterület általában és a külterületi útmenti sáv ezért csak együtt becsülhető. A kataszter koordinátás Excel-állományával a kategóriánkénti számok pontosan kiszámolhatók.

A jogi besorolás a „Óriásplakátok: mi változott és mi változik” című, 2026. október 13-i összefoglalóból származik. Az oldal jogszabályhelyet nem idéz.

## Újraépítés

```sh
pip install pyshp shapely pyproj
# Natural Earth 10m rétegek kicsomagolva, mindegyik a saját nevű almappában
python3 tools/build_geometry.py <natural_earth_mappa> data/geometry.json
python3 tools/build_page.py
```

- `src/template.html` – az oldal forrása (stílus, szövegek, számok, működés)
- `data/geometry.json` – a térkép rajzolata (Natural Earth, Egységes Országos Vetület)
- `tools/build_page.py` – a sablonból és a geometriából elkészíti az `index.html`-t

Térképalap: [Natural Earth](https://www.naturalearthdata.com/) (közkincs). A budapesti metróvonalak nyomvonala sematikus.
