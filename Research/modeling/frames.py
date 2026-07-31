#!/usr/bin/env python3
"""frames.py — the canonical frame for Mother Tongues, as tested code.

Register: A1 (identity + naming + counts), A2 (Mollweide <-> WGS84).
Contract: SCOPE.md §6. Nothing in this project may join two sources until this module
can convert between them.

Why this file exists at all
--------------------------
The most expensive class of bug in this kind of project is two sources silently in
different frames — different identity keys, different name conventions, different
projections. This module is the single place those differences are resolved, and its
selftest is the gate.

Five things it settles
----------------------
1.  **Identity is the glottocode.** ISO 639-3 is an *alias*, never a key. ISO has no
    "ancient" type, so Latin, Sumerian and Akkadian are all coded `H`istorical and a
    bucket-by-extinct returns almost nothing; its coverage also differs from Glottolog's
    by hundreds of entries.
2.  **Names are autonym-first**, in the language's own script, exonym second, historical
    exonyms flagged. Display order is decided *here*, in code, not left to data entry —
    many exonyms are colonial or slurs. (CLAUDE.md rule 11.)
3.  **A speaker count is a triple** — (value, year, source). A bare number is not a datum
    in this subject, because sources copy each other's decades-old figures forward.
4.  **Mollweide <-> WGS84**, closed-form inverse plus Newton forward, because the
    population raster ships in Mollweide and there is no pyproj here. Hand-rolled and
    tested beats an opaque call: the residual is measured, not assumed.
5.  **"Unknown" is a legitimate return** — with confidence `none`, never an invention.

stdlib only, so `build/` can import it without a new dependency.
"""
from __future__ import annotations

import math
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Iterable, Optional

# ---------------------------------------------------------------------------
# 0. Confidence — a field on the data, not a footnote in prose (rule 9)
# ---------------------------------------------------------------------------

CONFIDENCE = ("good", "moderate", "contested", "none")


def valid_confidence(c: str) -> bool:
    return c in CONFIDENCE


# ---------------------------------------------------------------------------
# 1. Identity
# ---------------------------------------------------------------------------

_GLOTTOCODE = re.compile(r"^[a-z0-9]{4}\d{4}$")
_ISO639P3 = re.compile(r"^[a-z]{3}$")


def is_glottocode(s: object) -> bool:
    """Glottocodes are four lowercase alphanumerics then four digits: `stan1293`."""
    return isinstance(s, str) and bool(_GLOTTOCODE.match(s))


def is_iso639p3(s: object) -> bool:
    return isinstance(s, str) and bool(_ISO639P3.match(s))


class FrameError(ValueError):
    """Raised when a caller tries to use a non-canonical key as the key."""


@dataclass(frozen=True)
class Languoid:
    """One node of the canonical spine. `glottocode` is the only identity."""

    glottocode: str
    name: str                       # Glottolog's English reference name
    level: str                      # language | dialect | family
    iso639p3: Optional[str] = None  # ALIAS ONLY
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    family_id: Optional[str] = None
    is_isolate: bool = False
    first_year: Optional[int] = None
    last_year: Optional[int] = None

    def __post_init__(self) -> None:
        if not is_glottocode(self.glottocode):
            raise FrameError(f"not a glottocode: {self.glottocode!r}")
        if self.iso639p3 is not None and not is_iso639p3(self.iso639p3):
            raise FrameError(f"not an ISO 639-3 code: {self.iso639p3!r}")
        if self.level not in ("language", "dialect", "family"):
            raise FrameError(f"unknown level: {self.level!r}")


class Registry:
    """Glottocode -> Languoid, with ISO used only as a lookup convenience.

    `by_iso()` deliberately returns a *list*: the mapping is not 1:1, and code that
    assumes it is will be wrong somewhere it never looks.
    """

    def __init__(self, languoids: Iterable[Languoid] = ()) -> None:
        self._by_code: dict[str, Languoid] = {}
        self._by_iso: dict[str, list[str]] = {}
        for l in languoids:
            self.add(l)

    def add(self, l: Languoid) -> None:
        if l.glottocode in self._by_code:
            raise FrameError(f"duplicate glottocode: {l.glottocode}")
        self._by_code[l.glottocode] = l
        if l.iso639p3:
            self._by_iso.setdefault(l.iso639p3, []).append(l.glottocode)

    def __len__(self) -> int:
        return len(self._by_code)

    def __contains__(self, code: object) -> bool:
        return code in self._by_code

    def get(self, glottocode: str) -> Optional[Languoid]:
        if not is_glottocode(glottocode):
            raise FrameError(
                f"{glottocode!r} is not a glottocode. ISO codes are aliases — "
                f"resolve with by_iso() and handle the list."
            )
        return self._by_code.get(glottocode)

    def by_iso(self, iso: str) -> list[str]:
        if not is_iso639p3(iso):
            raise FrameError(f"not an ISO 639-3 code: {iso!r}")
        return list(self._by_iso.get(iso, []))

    def ambiguous_iso(self) -> dict[str, list[str]]:
        """ISO codes that map to more than one glottocode — the reason ISO is not a key."""
        return {k: v for k, v in self._by_iso.items() if len(v) > 1}


# ---------------------------------------------------------------------------
# 2. Names — autonym first, always
# ---------------------------------------------------------------------------

NAME_KINDS = ("autonym", "exonym", "historical-exonym", "reference")


@dataclass(frozen=True)
class Name:
    text: str
    kind: str
    script: Optional[str] = None    # ISO 15924, e.g. "Cyrl"
    lang: Optional[str] = None      # BCP-47 of the name itself
    note: Optional[str] = None      # e.g. "pejorative"
    confidence: str = "moderate"

    def __post_init__(self) -> None:
        if self.kind not in NAME_KINDS:
            raise FrameError(f"unknown name kind: {self.kind!r}")
        if not valid_confidence(self.confidence):
            raise FrameError(f"bad confidence: {self.confidence!r}")
        if not self.text or not self.text.strip():
            raise FrameError("empty name")


@dataclass
class NameSet:
    """Every attested name for one languoid, with display order decided in code."""

    glottocode: str
    names: list[Name] = field(default_factory=list)

    # Display precedence. Rule 11: the autonym is first because of what the
    # alternative means, not because it looks better.
    ORDER = {"autonym": 0, "reference": 1, "exonym": 2, "historical-exonym": 3}

    def ordered(self) -> list[Name]:
        return sorted(self.names, key=lambda n: (self.ORDER[n.kind], n.text))

    def display(self) -> str:
        """The card's title line: autonym (exonym). Never the exonym alone."""
        o = self.ordered()
        if not o:
            return "(unnamed)"
        primary = o[0]
        second = next(
            (n for n in o[1:] if n.kind in ("reference", "exonym")
             and _fold(n.text) != _fold(primary.text)),
            None,
        )
        return f"{primary.text} ({second.text})" if second else primary.text

    def historical(self) -> list[Name]:
        """Shown only in the historical-names row, marked. Never in the title."""
        return [n for n in self.ordered() if n.kind == "historical-exonym"]

    def has_autonym(self) -> bool:
        return any(n.kind == "autonym" for n in self.names)


def _fold(s: str) -> str:
    """Casefold + strip diacritics, for comparing names across sources."""
    d = unicodedata.normalize("NFD", s)
    return "".join(c for c in d if unicodedata.category(c) != "Mn").casefold().strip()


# ---------------------------------------------------------------------------
# 3. Speaker counts — always the triple
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SpeakerCount:
    """(value, year, source) or nothing. A bare integer is rejected by construction."""

    value: Optional[int]
    year: Optional[int]
    source: Optional[str]
    confidence: str = "moderate"
    note: Optional[str] = None

    def __post_init__(self) -> None:
        if not valid_confidence(self.confidence):
            raise FrameError(f"bad confidence: {self.confidence!r}")
        if self.value is None:
            if self.confidence != "none":
                raise FrameError("a count with no value must have confidence 'none'")
            return
        if self.value < 0:
            raise FrameError(f"negative speakers: {self.value}")
        if self.year is None or self.source is None:
            raise FrameError(
                "a speaker count needs value AND year AND source — a bare number is "
                "not a datum in this subject (SCOPE §6)"
            )
        if not (1500 <= self.year <= 2100):
            raise FrameError(f"implausible estimate year: {self.year}")

    @classmethod
    def unknown(cls, note: str = "no published estimate found") -> "SpeakerCount":
        """'Unknown' is a legitimate return (rule 10)."""
        return cls(None, None, None, confidence="none", note=note)

    @property
    def known(self) -> bool:
        return self.value is not None

    def staleness(self, as_of: int) -> Optional[int]:
        """Years between the estimate and now — rendered on the card, not hidden."""
        return None if self.year is None else as_of - self.year

    def display(self, as_of: int = 2026) -> str:
        if not self.known:
            return "no published estimate"
        age = self.staleness(as_of)
        stale = f", {age} years old" if age is not None and age >= 20 else ""
        return f"{self.value:,} speakers ({self.year}, {self.source}{stale})"


# ---------------------------------------------------------------------------
# 4. Time — the two snapshots, and the earlier one is NOT a year
# ---------------------------------------------------------------------------

SNAPSHOTS = ("before-contact", "today")


class SnapshotError(ValueError):
    pass


def snapshot_label(snapshot: str, contact_year: Optional[int] = None) -> str:
    """Label for the timeline.

    `before-contact` is a per-region *state*, not a date: contact ranges from the 1490s
    to the 20th century and never happened in some places. Printing one year on that
    snapshot would be the frame error of this project (SCOPE §6), so this function
    refuses to. A per-region contact year may appear on a *card*, never on the axis.
    """
    if snapshot not in SNAPSHOTS:
        raise SnapshotError(f"unknown snapshot: {snapshot!r}")
    if snapshot == "today":
        return "today"
    return "before contact"


def contact_note(contact_year: Optional[int], region: str) -> str:
    """Card-level text for the contact date, where one is known."""
    if contact_year is None:
        return f"Sustained outside contact in {region}: date not established."
    return f"Sustained outside contact in {region}: from about {contact_year}."


# ---------------------------------------------------------------------------
# 5. Projections — Mollweide <-> WGS84  (register A2)
# ---------------------------------------------------------------------------
# The population raster (GHS-POP) ships in Mollweide on a sphere of R = 6371007.181 m.
# Forward has no closed form: solve  2*theta + sin(2*theta) = pi*sin(phi)  by Newton,
# which converges in a handful of iterations everywhere except exactly at the poles,
# where the derivative vanishes and we clamp.

R_GHSL = 6371007.181            # m, the authalic sphere GHSL uses
_SQRT2 = math.sqrt(2.0)


def _mollweide_theta(phi: float, tol: float = 1e-12, itmax: int = 60) -> float:
    """Auxiliary angle theta for latitude phi (radians)."""
    if abs(abs(phi) - math.pi / 2) < 1e-12:
        return math.copysign(math.pi / 2, phi)      # pole: derivative is zero
    target = math.pi * math.sin(phi)
    theta = phi if phi else 0.0                      # good enough to start
    for _ in range(itmax):
        f = 2.0 * theta + math.sin(2.0 * theta) - target
        d = 2.0 + 2.0 * math.cos(2.0 * theta)
        if abs(d) < 1e-15:
            break
        step = f / d
        theta -= step
        if abs(step) < tol:
            break
    return theta


def wgs84_to_mollweide(lon_deg: float, lat_deg: float, R: float = R_GHSL,
                       lon0_deg: float = 0.0) -> tuple[float, float]:
    """(lon, lat) in degrees -> (x, y) in metres."""
    if not (-90.0 - 1e-9 <= lat_deg <= 90.0 + 1e-9):
        raise FrameError(f"latitude out of range: {lat_deg}")
    phi = math.radians(max(-90.0, min(90.0, lat_deg)))
    lam = math.radians(_wrap180(lon_deg - lon0_deg))
    theta = _mollweide_theta(phi)
    x = (2.0 * _SQRT2 / math.pi) * R * lam * math.cos(theta)
    y = _SQRT2 * R * math.sin(theta)
    return x, y


def mollweide_to_wgs84(x: float, y: float, R: float = R_GHSL,
                       lon0_deg: float = 0.0) -> tuple[float, float]:
    """(x, y) in metres -> (lon, lat) in degrees. Closed form.

    Raises FrameError outside the ellipse, rather than returning a plausible lie —
    a library that extrapolates instead of refusing is how a whole field gets invented
    (TRAPS §D6).
    """
    s = y / (_SQRT2 * R)
    if abs(s) > 1.0 + 1e-9:
        raise FrameError(f"y={y} is outside the Mollweide ellipse")
    s = max(-1.0, min(1.0, s))
    theta = math.asin(s)
    sin_phi = (2.0 * theta + math.sin(2.0 * theta)) / math.pi
    if abs(sin_phi) > 1.0 + 1e-9:
        raise FrameError(f"y={y} maps outside valid latitude")
    lat = math.degrees(math.asin(max(-1.0, min(1.0, sin_phi))))
    c = math.cos(theta)
    if abs(c) < 1e-12:
        return _wrap180(lon0_deg), lat                # at a pole longitude is undefined
    lam = (math.pi * x) / (2.0 * _SQRT2 * R * c)
    lon = math.degrees(lam) + lon0_deg
    if abs(lon - lon0_deg) > 180.0 + 1e-6:
        raise FrameError(f"x={x} is outside the Mollweide ellipse at lat {lat:.4f}")
    return _wrap180(lon), lat


def _wrap180(lon: float) -> float:
    return (lon + 180.0) % 360.0 - 180.0


def roundtrip_residual_m(lon: float, lat: float, R: float = R_GHSL) -> float:
    """Great-circle metres between (lon,lat) and its Mollweide round trip.

    This is the number A2 requires be *recorded* rather than assumed.
    """
    x, y = wgs84_to_mollweide(lon, lat, R)
    lon2, lat2 = mollweide_to_wgs84(x, y, R)
    return _haversine_m(lon, lat, lon2, lat2, R)


def _haversine_m(lon1: float, lat1: float, lon2: float, lat2: float, R: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(_wrap180(lon2 - lon1))
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(min(1.0, math.sqrt(a)))


# ---------------------------------------------------------------------------
# 6. Selftest — the module's contract
# ---------------------------------------------------------------------------

def _selftest() -> None:
    # --- identity ---------------------------------------------------------
    assert is_glottocode("stan1293") and is_glottocode("nucl1643")
    assert not is_glottocode("STAN1293") and not is_glottocode("stan129")
    assert not is_glottocode("eng") and not is_glottocode(None)
    assert is_iso639p3("eng") and not is_iso639p3("english")

    eng = Languoid("stan1293", "Standard German", "language", iso639p3="deu",
                   latitude=48.6, longitude=12.5, family_id="indo1319")
    reg = Registry([eng])
    assert len(reg) == 1 and "stan1293" in reg
    assert reg.get("stan1293") is eng
    assert reg.by_iso("deu") == ["stan1293"]
    # ISO must not be usable as a key
    try:
        reg.get("deu")
        raise AssertionError("ISO code was accepted as a key")
    except FrameError:
        pass
    # a bad level, a bad code and a duplicate all refuse
    for bad in (lambda: Languoid("stan1293", "x", "planet"),
                lambda: Languoid("nope", "x", "language"),
                lambda: Languoid("stan1293", "x", "language", iso639p3="deutsch")):
        try:
            bad(); raise AssertionError("bad Languoid accepted")
        except FrameError:
            pass
    try:
        reg.add(eng); raise AssertionError("duplicate accepted")
    except FrameError:
        pass

    # --- names: autonym first, always ------------------------------------
    ns = NameSet("stan1293", [
        Name("German", "reference"),
        Name("Deutsch", "autonym", script="Latn", lang="de", confidence="good"),
        Name("Alemán", "exonym", lang="es"),
        Name("Dutch", "historical-exonym", note="obsolete English usage"),
    ])
    assert ns.ordered()[0].kind == "autonym"
    assert ns.display() == "Deutsch (German)", ns.display()
    assert [n.text for n in ns.historical()] == ["Dutch"]
    assert ns.has_autonym()

    # a languoid with no autonym still renders, and never promotes a slur
    ns2 = NameSet("test1234", [
        Name("Reference Name", "reference"),
        Name("Slur", "historical-exonym", note="pejorative"),
    ])
    assert not ns2.has_autonym()
    assert ns2.display() == "Reference Name", ns2.display()
    assert "Slur" not in ns2.display()

    # duplicate autonym/reference must not render as "X (X)"
    ns3 = NameSet("test1234", [Name("Nuosu", "autonym"), Name("nuosu", "reference")])
    assert ns3.display() == "Nuosu", ns3.display()

    for bad in (lambda: Name("x", "nickname"), lambda: Name("", "autonym"),
                lambda: Name("x", "autonym", confidence="probably")):
        try:
            bad(); raise AssertionError("bad Name accepted")
        except FrameError:
            pass

    # --- speaker counts: the triple --------------------------------------
    c = SpeakerCount(75_000_000, 2016, "Ethnologue 19")
    assert c.known and c.staleness(2026) == 10
    assert "75,000,000" in c.display(2026)
    old = SpeakerCount(1200, 1987, "SIL survey")
    assert "39 years old" in old.display(2026), old.display(2026)

    u = SpeakerCount.unknown()
    assert not u.known and u.confidence == "none"
    assert u.display() == "no published estimate"

    for bad in (lambda: SpeakerCount(1000, None, "x"),          # no year
                lambda: SpeakerCount(1000, 2020, None),         # no source
                lambda: SpeakerCount(-5, 2020, "x"),            # negative
                lambda: SpeakerCount(1000, 1200, "x"),          # implausible year
                lambda: SpeakerCount(None, None, None)):        # unknown w/o confidence
        try:
            bad(); raise AssertionError("bad SpeakerCount accepted")
        except FrameError:
            pass

    # --- time: the earlier snapshot is not a year ------------------------
    assert snapshot_label("today") == "today"
    assert snapshot_label("before-contact") == "before contact"
    # even given a year, the axis label must not print it
    assert "1788" not in snapshot_label("before-contact", contact_year=1788)
    assert "1788" in contact_note(1788, "eastern Australia")
    assert "not established" in contact_note(None, "interior New Guinea")
    try:
        snapshot_label("1492"); raise AssertionError("bogus snapshot accepted")
    except SnapshotError:
        pass

    # --- projection: Mollweide <-> WGS84 --------------------------------
    # origin
    x, y = wgs84_to_mollweide(0.0, 0.0)
    assert abs(x) < 1e-6 and abs(y) < 1e-6, (x, y)
    # equator: x is linear in longitude
    x90, _ = wgs84_to_mollweide(90.0, 0.0)
    x45, _ = wgs84_to_mollweide(45.0, 0.0)
    assert abs(x90 / x45 - 2.0) < 1e-9
    # poles: y = +/- sqrt(2) R, x collapses to 0
    xp, yp = wgs84_to_mollweide(37.0, 90.0)
    assert abs(yp - _SQRT2 * R_GHSL) < 1e-3 and abs(xp) < 1e-6, (xp, yp)
    # round trip is sub-millimetre over a global sample
    worst, worst_at = 0.0, None
    for lat in range(-89, 90, 1):
        for lon in range(-179, 180, 7):
            r = roundtrip_residual_m(float(lon), float(lat))
            if r > worst:
                worst, worst_at = r, (lon, lat)
    assert worst < 1e-3, f"round-trip residual {worst:.3e} m at {worst_at}"
    # outside the ellipse must RAISE, not extrapolate (TRAPS D6)
    for bad in (lambda: mollweide_to_wgs84(0.0, 3.0 * R_GHSL),
                lambda: mollweide_to_wgs84(3.0 * R_GHSL, 0.0)):
        try:
            bad(); raise AssertionError("out-of-domain point accepted")
        except FrameError:
            pass
    # a known Mollweide property: the map is twice as wide as it is tall
    xe, _ = wgs84_to_mollweide(180.0, 0.0)
    _, yn = wgs84_to_mollweide(0.0, 90.0)
    assert abs((abs(xe) / yn) - 2.0) < 1e-9, abs(xe) / yn

    # The antimeridian, pinned deliberately because a raster ingest will hit it:
    # lon +180 and lon -180 are the same meridian, and _wrap180 canonicalises to -180.
    # So x is NEGATIVE at +180. Code that assumes a positive right edge will place the
    # last column of a global raster on the wrong side of the map.
    assert _wrap180(180.0) == -180.0
    assert _wrap180(-180.0) == -180.0
    assert xe < 0.0, "expected +180 to canonicalise to the -180 meridian"
    xw, _ = wgs84_to_mollweide(-180.0, 0.0)
    assert abs(xe - xw) < 1e-9, "the two antimeridian spellings must agree"

    print("frames.py selftest: OK")
    return worst


if __name__ == "__main__":
    worst = _selftest()
    print()
    print("A2 — Mollweide <-> WGS84 residual, recorded as the register requires:")
    print(f"  worst round-trip over a 180x52 global lattice: {worst:.3e} m")
    print(f"  sphere: R = {R_GHSL} m (GHSL authalic)")
    print()
    print("A1 — worked demonstration:")
    ns = NameSet("stan1293", [
        Name("Deutsch", "autonym", script="Latn", lang="de", confidence="good"),
        Name("German", "reference"),
        Name("Alemán", "exonym", lang="es"),
    ])
    print("  title line          :", ns.display())
    print("  count, fresh        :", SpeakerCount(75_000_000, 2016, "Ethnologue 19").display())
    print("  count, stale        :", SpeakerCount(1200, 1987, "SIL survey").display())
    print("  count, absent       :", SpeakerCount.unknown().display())
    print("  timeline label      :", snapshot_label("before-contact"))
    print("  contact, known      :", contact_note(1788, "eastern Australia"))
    print("  contact, unknown    :", contact_note(None, "interior New Guinea"))
