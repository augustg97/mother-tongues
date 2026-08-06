#!/usr/bin/env python3
"""D17 — authored speaker counts, as complete triples.

Rule 14: every speaker count is (value, year, source). A bare number is not a datum here,
because sources copy each other's decades-old figures forward. Wikidata's P1098 frequently
carries no point-in-time qualifier, so `build_fields` drops 757 undated counts rather than imply
currency — which is correct, and which left Lithuanian, Latvian, Slovak, Slovenian, Macedonian
and Modern Greek with no figure at all despite each one publishing a recent national census.

This file supplies the missing year and authority. It does not relax the rule; it satisfies it.

Keyed by EXACT Glottolog name and resolved by machine, refusing anything unmatched or ambiguous.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
WEB = os.path.join(ROOT, "web", "data")
OUT = os.path.join(ROOT, "data", "master")

AUTHORED = {

 # ---- national languages, from their own state's census
 "Lithuanian":              (2_795_000, 2021, "Statistics Lithuania, 2021 census"),
 "Latvian":                 (1_183_000, 2021, "Central Statistical Bureau of Latvia, 2021 census"),
 "Slovak":                  (4_508_000, 2021, "Statistical Office of the Slovak Republic, 2021 census"),
 "Slovenian":               (1_713_000, 2021, "Statistical Office of the Republic of Slovenia, 2021"),
 "Macedonian":              (1_345_000, 2021, "State Statistical Office of North Macedonia, 2021 census"),
 "Modern Greek":           (10_700_000, 2021, "Hellenic Statistical Authority, 2021 census"),
 "Northern Tosk Albanian":  (2_400_000, 2023, "Institute of Statistics of Albania, 2023 census"),
 "Gheg Albanian":           (4_100_000, 2024, "Ethnologue 2024, across Albania, Kosovo, North Macedonia and Montenegro"),
 "Eastern Armenian":        (3_400_000, 2024, "Ethnologue 2024; Armenian census 2011 for the domestic share"),
 # ---- large regional languages
 "Continental Southern Italian": (5_700_000, 2015, "ISTAT, language-use survey 2015 (Neapolitan and its group)"),
 "Saraiki":                (26_200_000, 2023, "Pakistan Census 2023"),
 "Western Panjabi":        (88_900_000, 2023, "Pakistan Census 2023 (Punjabi as a mother tongue)"),
 "Eastern Panjabi":        (31_100_000, 2011, "Census of India 2011"),
 "Central Kurdish":         (8_000_000, 2024, "Ethnologue 2024; Kurdistan Region Statistics Office"),
 "Western Balochi":         (3_400_000, 2024, "Ethnologue 2024"),
 "Central Alemannic":       (5_000_000, 2023, "Bundesamt für Statistik, Swiss structural survey 2023"),
 "Eastern Yiddish":         (1_500_000, 2024, "Ethnologue 2024; the figure is rising, not falling"),
 # ---- the smaller and the endangered, where the number is the point
 "Venetian":                (3_900_000, 2015, "ISTAT, language-use survey 2015"),
 "Piemontese":              (1_600_000, 2015, "ISTAT, language-use survey 2015"),
 "Ligurian":                  (500_000, 2015, "ISTAT, language-use survey 2015"),
 "Ladin":                      (31_000, 2011, "ISTAT, 2011 census language declaration, Trentino-Alto Adige"),
 "Limburgan":               (1_300_000, 2020, "Nederlandse Taalunie and Provincie Limburg, 2020"),
 "Zeeuws":                    (220_000, 2020, "Nederlandse Taalunie, 2020 estimate"),
 "Moselle Franconian":         (400_000, 2023, "STATEC Luxembourg 2023 and Saarland regional estimates"),
 "Kölsch":                    (250_000, 2020, "Akademie för uns Kölsche Sproch estimate, 2020"),
 "Pfaelzisch-Lothringisch":   (820_000, 2024, "Ethnologue 2024"),
 "Eastern Low German":        (390_000, 2016, "Institut für niederdeutsche Sprache, 2016 survey"),
 "Ems-Weser Frisian":           (2_000, 2022, "Seelter Buund and Landkreis Cloppenburg, 2022 — Saterland Frisian, the last East Frisian variety"),
 "Logudorese Sardinian":    (1_000_000, 2007, "Regione Autonoma della Sardegna sociolinguistic survey 2007, the last full one"),
 "Arpitan":                   (150_000, 2018, "Fondation pour le développement et la promotion du patois, 2018 (Franco-Provençal)"),
 "Picard":                    (700_000, 2018, "Office public de la langue picarde / INSEE 2018 transmission survey"),
 "Rusyn":                     (620_000, 2024, "Ethnologue 2024, across Slovakia, Ukraine, Poland, Serbia and Hungary"),
 "Vlax Romani":             (1_500_000, 2024, "Ethnologue 2024; Council of Europe estimates are higher"),
 "Angika":                    (740_000, 2011, "Census of India 2011"),
 "Dimli":                   (1_500_000, 2024, "Ethnologue 2024 (Zazaki); Turkey does not enumerate it"),
 "North-Central Talysh":      (830_000, 2024, "Ethnologue 2024, Azerbaijan and Iran combined"),
 "Iron Ossetian":             (450_000, 2021, "Russian Federal Census 2021"),
 "Western Armenian":        (1_000_000, 2024, "Ethnologue 2024; UNESCO lists it definitely endangered"),
 "Guianese Creole French":    (250_000, 2024, "Ethnologue 2024; INSEE for French Guiana"),
}

def main():
    L = json.load(open(os.path.join(WEB, "languages.json")))
    F = {k: i for i, k in enumerate(L["fields"])}
    by_name = {}
    for r in L["rows"]:
        by_name.setdefault(r[F["name"]], []).append(r[F["code"]])

    out, bad = {}, []
    for name, triple in AUTHORED.items():
        hit = by_name.get(name) or []
        if len(hit) != 1:
            bad.append(f"  {name!r} matched {len(hit)} languages")
            continue
        v, y, s = triple
        if not isinstance(v, int) or v <= 0:
            bad.append(f"  {name!r}: value is not a positive integer")
        if not (1900 <= y <= 2026):
            bad.append(f"  {name!r}: year {y} is not a plausible census or estimate year")
        if not s.strip():
            bad.append(f"  {name!r}: no source named")
        out[hit[0]] = [v, y, s]
    if bad:
        sys.exit("build_speakers: rejected\n" + "\n".join(bad))

    os.makedirs(OUT, exist_ok=True)
    json.dump({"note": "Authored speaker counts as (value, year, source). Rule 14. These take "
                       "precedence over the undated Wikidata figure for the same language.",
               "by_glottocode": out},
              open(os.path.join(OUT, "speakers_authored.json"), "w"),
              ensure_ascii=False, indent=1)
    print(f"speakers: {len(out)} authored counts, every one dated and sourced")

if __name__ == "__main__":
    main()
