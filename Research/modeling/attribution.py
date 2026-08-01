#!/usr/bin/env python3
"""attribution.py — the attribution ledger, and the machine that keeps it honest.

Register item A5. SCOPE §12 D3 permits ShareAlike, which has a consequence most projects
discover late: **ShareAlike obligations are only dischargeable if you know what you took.**
So the ledger is not prose in an About panel — prose drifts from the ingest silently. It is
this module, and `build_site.py` refuses to publish unless the shipped JSON is byte-identical
to what this module generates.

Each row is a source that is IN THE SHIPPED BUILD. Not a source we might use, not one the
survey found: one whose bytes reached `web/`. `ingested=False` rows are carried so that a
future round adding them has the row already written and checked.

Why `verified` is a field: a licence I have read at the source is a different kind of fact
from a licence I remember. The selftest refuses to let an ingested source ship unverified —
which is what forced the Ecoregions licence to be read at source rather than assumed.

stdlib only. Run: python3 attribution.py
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import List

# Licences that SCOPE §12 D3 excludes outright. Matched as substrings of the licence id,
# so "CC-BY-NC-SA-3.0" is caught by "NC" without needing every permutation enumerated.
FORBIDDEN_TOKENS = ("-NC", "NONCOMMERCIAL", "-ND", "NODERIV")
SA_TOKENS = ("-SA", "SHAREALIKE")

# ShareAlike sources whose obligation has been worked out and recorded, with the reasoning
# in that source's own `note`. Adding a key here is the deliberate act; the selftest below
# will not let an SA source ship without one.
SA_DISCLOSED = {"commons"}


@dataclass
class Source:
    key: str
    title: str
    creators: str
    year: str
    licence: str
    licence_url: str
    source_url: str
    attribution: str          # the exact string the licence requires us to display
    layer: str                # which field of the model it becomes
    ingested: bool
    verified: bool            # has the licence been read at the source, this project?
    note: str = ""

    @property
    def share_alike(self) -> bool:
        u = self.licence.upper()
        return any(t in u for t in SA_TOKENS)


# ---------------------------------------------------------------------------------------
# The ledger. Order is display order in the About panel.
# ---------------------------------------------------------------------------------------
LEDGER: List[Source] = [
    Source(
        key="glottolog",
        title="Glottolog 5.3",
        creators="Hammarström, Harald; Forkel, Robert; Haspelmath, Martin; Bank, Sebastian",
        year="2026",
        licence="CC-BY-4.0",
        licence_url="https://creativecommons.org/licenses/by/4.0/",
        source_url="https://doi.org/10.5281/zenodo.18840967",
        attribution=("Glottolog 5.3 — Hammarström, Forkel, Haspelmath & Bank (2026), "
                     "Max Planck Institute for Evolutionary Anthropology. CC-BY-4.0."),
        layer="the language spine: glottocode, family, coordinates, vitality, attestation",
        ingested=True, verified=True,
        note=("7,674 spoken-L1 languages of 8,618 language-level languoids; 7,672 with "
              "coordinates. Filtered on `category`, never on `Level` — see A6."),
    ),
    Source(
        key="glottography",
        title="Glottography",
        creators=("Ranacher, Peter; Forkel, Robert; Efrat-Kowalsky, Nour; Urban, Matthias; "
                  "and the Glottography contributors"),
        year="2025",
        licence="CC-BY-4.0",
        licence_url="https://creativecommons.org/licenses/by/4.0/",
        source_url="https://doi.org/10.1038/s41597-025-05828-6",
        attribution=("Glottography — Ranacher, Forkel, Efrat-Kowalsky, Urban et al., "
                     "Scientific Data 12:1466 (2025). CC-BY-4.0, 26 component datasets."),
        layer="language areas — the polygons the language field is rasterised from",
        ingested=True, verified=True,
        note=("26 of 29 dataset repositories. THREE ARE CC-BY-NC AND EXCLUDED — "
              "bowern2021australia, haynie2019modern, wurm1981pacific — against the "
              "collection paper's own blanket CC-BY claim. The gate reads licence text, "
              "because GitHub's licence API returns NOASSERTION for all three."),
    ),
    Source(
        key="etopo1",
        title="ETOPO1 Ice Surface, 1 arc-minute",
        creators="Amante, Christopher; Eakins, Barry W. — NOAA NGDC",
        year="2009",
        licence="public-domain",
        licence_url="https://www.ngdc.noaa.gov/mgg/global/",
        source_url="https://doi.org/10.7289/V5C8276M",
        attribution=("ETOPO1 1 Arc-Minute Global Relief Model — Amante & Eakins (2009), "
                     "NOAA National Geophysical Data Center. Public domain."),
        layer="elevation and bathymetry — the substrate the whole surface is lit from",
        ingested=True, verified=True,
        note="US federal work, no licence required. 10800×21600 int16, ice surface.",
    ),
    Source(
        key="ghspop",
        title="GHS-POP R2023A, 2020 epoch, 30 arcsec",
        creators="Schiavina, Marcello; Freire, Sergio; MacManus, Kytt — European Commission JRC",
        year="2023",
        licence="CC-BY-4.0",
        licence_url="https://creativecommons.org/licenses/by/4.0/",
        source_url="https://doi.org/10.2905/2FF68A52-5B5B-4A22-8F40-C41DA8332CFE",
        attribution=("GHS-POP R2023A — Schiavina, Freire & MacManus (2023), European "
                     "Commission Joint Research Centre. CC-BY-4.0."),
        layer="speaker density — the luminance channel of the language field",
        ingested=True, verified=True,
        note=("The WGS84 (EPSG:4326) product, NOT the Mollweide one — which is why no "
              "reprojection is exercised in this build. Placed by its own geotransform: it "
              "spans 178.20° of latitude, not 180, and assuming 180 put 70 people/km² on "
              "Everest's summit and lost 340 million people."),
    ),
    Source(
        key="ecoregions",
        title="Ecoregions 2017",
        creators=("Dinerstein, Eric; Olson, David; Joshi, Anup; Vynne, Carly; Burgess, "
                  "Neil D.; et al. — RESOLVE"),
        year="2017",
        licence="CC-BY-4.0",
        licence_url="https://creativecommons.org/licenses/by/4.0/",
        source_url="https://ecoregions.appspot.com/",
        attribution=("Ecoregions 2017 © RESOLVE — Dinerstein et al., \"An Ecoregion-Based "
                     "Approach to Protecting Half the Terrestrial Realm\", BioScience 67(6): "
                     "534–545 (2017). CC-BY-4.0."),
        layer="biome — the land material, and the project's current proxy for growing season",
        ingested=True, verified=True,
        note=("847 ecoregions, 14 biomes + rock/ice. Keyed on the shapefile's own BIOME_NUM, "
              "never on a re-derived index — a remap disagreeing with its own label array is "
              "how the Sahara came to report itself as 'ice, rock or water'. ⚠ Biome is a "
              "PROXY for growing season, not growing season: register item C3."),
    ),
    Source(
        key="modis_ndvi",
        title="MOD13C2 NDVI, monthly CMG, 2024",
        creators="Didan, Kamel — NASA LP DAAC / MODIS Land Science Team",
        year="2024",
        licence="public-domain",
        licence_url="https://www.earthdata.nasa.gov/engage/open-data-services-software-policies",
        source_url="https://neo.gsfc.nasa.gov/view.php?datasetId=MOD_NDVI_M",
        attribution=("MOD13C2 Vegetation Indices — Didan (2024), NASA LP DAAC, via NASA "
                     "Earth Observations. Public domain."),
        layer="greenness — PEAK NDVI over the year, the land's tone",
        ingested=True, verified=True,
        note=("Peak, not annual mean: the mean is dominated by the months boreal forest is "
              "under snow, so taiga scored like semi-desert. ⚠ NOT the AVHRR_CLIM_M product, "
              "which reads like a vegetation climatology and is sea surface temperature — it "
              "was wired in first and saturated the whole land surface."),
    ),
    Source(
        key="modis_snow",
        title="MOD10C1 snow cover, monthly, 2020",
        creators="Hall, Dorothy K.; Riggs, George A. — NASA NSIDC DAAC",
        year="2020",
        licence="public-domain",
        licence_url="https://www.earthdata.nasa.gov/engage/open-data-services-software-policies",
        source_url="https://neo.gsfc.nasa.gov/view.php?datasetId=MOD10C1_M_SNOW",
        attribution=("MOD10C1 Snow Cover — Hall & Riggs (2020), NASA NSIDC DAAC, via NASA "
                     "Earth Observations. Public domain."),
        layer="snow cover — a measured snowline rather than an invented height threshold",
        ingested=True, verified=True,
        note="Annual mean, not peak: peak snow is 100% anywhere it ever snows, which would "
             "put permanent ice on Warsaw.",
    ),
    Source(
        key="wikidata",
        title="Wikidata native labels (P1705) and writing systems (P282)",
        creators="Wikidata contributors",
        year="2026",
        licence="CC0-1.0",
        licence_url="https://creativecommons.org/publicdomain/zero/1.0/",
        source_url="https://query.wikidata.org/",
        attribution="Wikidata (CC0), properties P1394, P1705, P282, P218, P220.",
        layer="AUTONYMS — what a language's own speakers call it, in its own script",
        ingested=True, verified=True,
        note=("Register D6. Joined on P1394 (glottocode, our own key) with P220 (ISO 639-3) "
              "as the alias fallback. Covers 1,089 of 7,672 languages — partial, and the "
              "card says so rather than passing an exonym off as an autonym."),
    ),
    # ---- carried, not yet ingested: the row exists before the bytes do -------------------
    Source(
        key="udhr",
        title="UDHR in XML",
        creators="Muller, Eric (ed.), from UN translations",
        year="2026",
        licence="NO-LICENCE-STATEMENT",
        licence_url="",
        source_url="https://github.com/eric-muller/udhr",
        attribution="Universal Declaration of Human Rights translations, UDHR in XML (E. Muller).",
        layer="parallel prose — Article 1 of the UDHR in 432 languages and 38 scripts",
        ingested=True, verified=True,
        note=("446 distinct languages, 49 scripts. HAS NO LICENCE FILE. Ships only under the "
              "user's recorded decision SCOPE §12 D2, behind a single feature flag so it is "
              "removable in one commit, with per-block provenance and a takedown path. "
              "An email to the maintainer is register item F1."),
    ),
    Source(
        key="asjp",
        title="ASJP — Automated Similarity Judgment Program",
        creators="Wichmann, Søren; Holman, Eric W.; Brown, Cecil H. (eds.)",
        year="2022",
        licence="CC-BY-4.0",
        licence_url="https://creativecommons.org/licenses/by/4.0/",
        source_url="https://github.com/lexibank/asjp",
        attribution=("ASJP — Wichmann, Holman & Brown (eds.), Automated Similarity Judgment "
                     "Program, via the Lexibank CLDF edition. CC-BY-4.0."),
        layer="the word tier — ASJP's core 40 concepts for 6,110 languages",
        ingested=True, verified=True,
        note=("380,912 forms. Joined on Glottocode, which is ASJP's own key. Forms are in "
              "**ASJPcode**, a deliberately coarse ASCII transcription for cross-language "
              "comparison — NOT the language's own orthography, and the card says so. ASJP "
              "marks its core 40 with a leading asterisk in the concept name; matching "
              "without stripping it found 4 concepts of 100 and produced an empty file."),
    ),
    Source(
        key="cldr",
        title="Unicode CLDR — locale display names",
        creators="Unicode Consortium and CLDR contributors",
        year="2026",
        licence="Unicode-3.0",
        licence_url="https://www.unicode.org/license.txt",
        source_url="https://github.com/unicode-org/cldr-json",
        attribution="Unicode Common Locale Data Repository (CLDR), Unicode Licence v3.",
        layer="autonyms for the world's widely-spoken languages",
        ingested=True, verified=True,
        note=("A locale's name for ITSELF — suomi, русский, 日本語 — which is exactly where "
              "Wikidata's P1705 is thinnest. 296 self-names, 138 of them new to us, joined by "
              "ISO 639-3 directly or through an ISO 639-1 bridge. ⚠ CLDR's `availableLocales` "
              "has an EMPTY \"modern\" list in the current release; the populated one is "
              "\"full\", and reading the wrong key returned zero locales and looked like a "
              "coverage problem rather than a bug."),
    ),
    Source(
        key="commons",
        title="Wikimedia Commons — manuscripts, inscriptions and objects",
        creators="Wikimedia Commons contributors and the holding institutions",
        year="2026",
        licence="mixed-open (public domain, CC0, CC-BY, CC-BY-SA; per file)",
        licence_url="https://commons.wikimedia.org/wiki/Commons:Licensing",
        source_url="https://commons.wikimedia.org/",
        attribution=("Wikimedia Commons — each image carries its own licence, title and "
                     "author, shown on the exhibit beside it."),
        layer="the gallery (26 objects) and the spoken recordings (15, Lingua Libre)",
        ingested=True, verified=True,
        note=("Admitted by MACHINE, per file, on the licence Commons reports for that file: "
              "public domain, CC0, CC-BY and CC-BY-SA pass; NonCommercial, NoDerivatives and "
              "fair-use fail. A public-domain manuscript can carry a restrictively licensed "
              "photograph, so the object's age is never the test. This is the same per-file "
              "gate register D3 specifies for audio, built for images first."),
    ),
    Source(
        key="phlorest",
        title="Phlorest — dated language phylogenies",
        creators="Forkel, Robert; Greenhill, Simon J.; and the original study authors",
        year="2022",
        licence="CC-BY-4.0",
        licence_url="https://creativecommons.org/licenses/by/4.0/",
        source_url="https://github.com/phlorest",
        attribution=("Phlorest — Forkel & Greenhill (eds.), a CLDF collection of published "
                     "Bayesian language phylogenies. CC-BY-4.0, per-study citations in each "
                     "dataset."),
        layer="root ages — the only real time depth in the genealogy view",
        ingested=True, verified=True,
        note=("19 families dated of 30 datasets; 11 rejected. **Do not trust the scaling "
              "field**: one tree's stated unit gives a 613,594-year root, and four are scaled "
              "in substitutions or 'change', which are not time at all. Every age is bounded "
              "to 300-12,000 years and two have an inferred unit, marked as such in the app."),
    ),
    Source(
        key="phoible",
        title="PHOIBLE 2.0",
        creators="Moran, Steven; McCloy, Daniel (eds.)",
        year="2019",
        licence="CC-BY-SA-3.0",
        licence_url="https://creativecommons.org/licenses/by-sa/3.0/",
        source_url="https://phoible.org/",
        attribution=("PHOIBLE 2.0 — Moran & McCloy (eds.), 2019, Max Planck Institute for "
                     "the Science of Human History. CC-BY-SA-3.0."),
        layer="phonology (v2+)",
        ingested=False, verified=True,
        note=("ShareAlike, and therefore the first source that makes SCOPE §12 D3 bite: the "
              "moment this is ingested, our emitted phonology data inherits SA."),
    ),
]


def ingested() -> List[Source]:
    return [s for s in LEDGER if s.ingested]


def share_alike_ingested() -> List[Source]:
    return [s for s in ingested() if s.share_alike]


def to_json() -> str:
    """The exact bytes the app ships. `build_site.py` compares against this."""
    rows = [{k: v for k, v in asdict(s).items() if k != "note"} | {"note": s.note,
             "share_alike": s.share_alike} for s in LEDGER]
    return json.dumps({"ledger": rows,
                       "sa_ingested": [s.key for s in share_alike_ingested()]},
                      indent=1, ensure_ascii=False, sort_keys=False)


def _selftest() -> None:
    keys = [s.key for s in LEDGER]
    assert len(keys) == len(set(keys)), "duplicate ledger key"

    for s in LEDGER:
        u = s.licence.upper()
        # 1. the policy, enforced rather than remembered.
        bad = [t for t in FORBIDDEN_TOKENS if t in u]
        assert not bad, f"{s.key}: SCOPE §12 D3 excludes {bad} — {s.licence}"
        # 2. an attribution string that is a string, not a placeholder.
        assert len(s.attribution) > 30, f"{s.key}: attribution too short to discharge CC-BY"
        assert "to be filled" not in s.attribution.lower(), f"{s.key}: placeholder attribution"
        assert s.creators and s.year, f"{s.key}: CC-BY needs a creator and a date"
        # 3. anything whose bytes are in the build must have a licence read at the source.
        if s.ingested:
            assert s.verified, f"{s.key} is INGESTED but its licence is unverified"
            assert s.licence_url or s.licence in ("public-domain", "CC0-1.0",
                                                  "NO-LICENCE-STATEMENT"), \
                f"{s.key}: no licence URL"
            # The one source with no licence at all ships under SCOPE §12 D2, a decision of
            # record. It is named here explicitly so that a SECOND unlicensed source cannot
            # slip in behind it on the same reasoning.
            assert "NO-LICENCE" not in u or s.key == "udhr", \
                f"{s.key} has no licence statement and cannot be ingested without a §12 decision"
        # 4. the attribution must actually name the thing it attributes.
        assert s.title.split()[0].rstrip(",") in s.attribution, \
            f"{s.key}: attribution does not name the source"

    # 5. the five fields the shipped build actually reads. If a sixth source reaches web/,
    #    this fails and forces a row — which is the whole point of the ledger.
    assert sorted(s.key for s in ingested()) == \
        ["asjp", "cldr", "commons", "ecoregions", "etopo1", "ghspop", "glottography", "glottolog",
         "modis_ndvi", "modis_snow", "phlorest", "udhr", "wikidata"], \
        "the ingested set changed without a ledger row"

    # 6. SA discipline. An SA source may ship only once the consequence has been worked out
    #    and written down HERE, not once someone remembers it. `commons` qualifies because
    #    the images are redistributed unmodified, each beside its own licence and author, so
    #    the obligation is discharged per file and nothing we generate is a derivative of
    #    them. A source that we DID build on would have to say so and would make our emitted
    #    data ShareAlike in turn.
    for src in share_alike_ingested():
        assert src.key in SA_DISCLOSED, (
            f"{src.key} is ShareAlike and not in SA_DISCLOSED: work out what it obliges us "
            f"to do and record it before shipping it")

    json.loads(to_json())
    print("attribution.py selftest OK")


if __name__ == "__main__":
    _selftest()
    print(f"\n{len(LEDGER)} sources · {len(ingested())} ingested · "
          f"{len(share_alike_ingested())} ShareAlike in the build")
    for s in LEDGER:
        flag = "SHIPPED " if s.ingested else "carried "
        sa = " [SA]" if s.share_alike else ""
        print(f"  {flag}{s.key:14s} {s.licence:22s}{sa} {s.layer[:52]}")
