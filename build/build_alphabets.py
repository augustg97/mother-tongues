#!/usr/bin/env python3
"""build_alphabets.py — resolve the letters onto glottocodes, and describe what kind of
writing system each set actually is. Register D11.

THE PROBLEM WITH "HOW MANY LETTERS". CLDR's exemplar set for Korean has 11,172 members.
Printing "Korean: 11,172 letters" would be one of the worst sentences in the museum. Korean
has twenty-four letters; those letters compose into 11,172 syllable blocks, and CLDR lists the
blocks because that is what software needs to render. Japanese lists 2,311 — two syllabaries of
about ninety each plus the ~2,100 kanji taught in school. Amharic lists 282, and that number
IS right, because Ethiopic really has 282 distinct signs arranged as a consonant × vowel table.

Three different facts, one field. So the set is not counted — it is **taken apart**:

  1. SPLIT BY SCRIPT, from Unicode's own character names. `unicodedata.name('क')` is
     'DEVANAGARI LETTER KA'; the first token is the script. Nothing is authored: Japanese
     falls into Hiragana / Katakana / Han by itself, and a language written in two scripts
     reports both.

  2. SPLIT BY UNIT TYPE, from the same names. 'LETTER', 'SYLLABLE', 'IDEOGRAPH',
     'VOWEL SIGN', 'SIGN', 'MARK'. This is the difference between an alphabet and an abugida
     stated as a measurement rather than as a claim: Devanagari comes back as letters *and*
     vowel signs, Ethiopic as syllables, Han as ideographs.

  3. DECOMPOSE HANGUL. Every Hangul syllable is arithmetic:
     S = 0xAC00 + (L*21 + V)*28 + T. Running that backwards over the 11,172 blocks recovers
     19 initial consonants, 21 medial vowels and 27 finals — measured off the set, not looked
     up. The card can then say the true thing.

TIER 2, and why it is a different claim. For every language CLDR does not reach, the letters
actually used in the prose we already ship. The texts are HTML-escaped in storage, so they are
unescaped first — reading them raw would report the letters of `&#x00E7;` as the alphabet of
São Tomé creole, which is the exact shape of bug this project keeps finding. Labelled observed,
with the sample size, and it never calls itself the alphabet.

Run: python3 build_alphabets.py
"""
from __future__ import annotations

import html
import json
import os
import re
import unicodedata
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "data", "alphabets", "cldr_characters.json")
WEB = os.path.join(HERE, "..", "web", "data")

# How many units a card shows before it switches to "a sample of N". A 74-letter Khmer
# alphabet is a thing to look at; 2,210 Han ideographs is a wall.
SHOW_MAX = 130

ASCII_PUNCT = set("-‐‑–—,;:!?.…'‘’\"“”()[]§@*/#†‡′″&%+<>=_|~^$\\{}`")

SCRIPT_FIX = {"CJK": "Han", "IDEOGRAPHIC": "Han", "HANGUL": "Hangul",
              "KATAKANA-HIRAGANA": "Kana", "HALFWIDTH": "Latin", "FULLWIDTH": "Latin",
              "MODIFIER": None, "COMBINING": None, "ZERO": None, "NARROW": None,
              "LEFT": None, "RIGHT": None, "NO-BREAK": None, "SOFT": None,
              "ARABIC-INDIC": "Arabic", "EXTENDED": None, "VERTICAL": None,
              "IDEOGRAPHIC-": "Han", "VULGAR": None, "SUPERSCRIPT": None,
              "SUBSCRIPT": None, "DIGIT": None, "MASCULINE": "Latin",
              "FEMININE": "Latin", "MICRO": "Latin", "OHM": "Greek",
              "KELVIN": "Latin", "ANGSTROM": "Latin", "MIDDLE": None, "BULLET": None,
              "HYPHENATION": None, "GREEK-": "Greek"}

UNIT_ORDER = ["LETTER", "SYLLABLE", "IDEOGRAPH", "VOWEL SIGN", "SIGN", "MARK",
              "TONE", "CHARACTER", "DIGIT", "other"]

# What the unit type means for a reader, in one clause. Authored prose, keyed by a MEASURED
# category — so it can never sit on the wrong language.
SCRIPT_KIND = {
    "Latin": ("alphabet", "one sign per consonant or vowel, written in a line"),
    "Greek": ("alphabet", "one sign per consonant or vowel — the first script to write "
                          "vowels as letters in their own right"),
    "Cyrillic": ("alphabet", "one sign per consonant or vowel, built from Greek in the "
                             "ninth century for Slavonic"),
    "Armenian": ("alphabet", "one sign per sound, devised about 405 for this language alone"),
    "Georgian": ("alphabet", "one sign per sound, and no capital letters"),
    "Hebrew": ("abjad", "consonants are written; vowels are marks, usually left off"),
    "Arabic": ("abjad", "consonants are written and joined; vowels are marks, usually "
                        "left off"),
    "Syriac": ("abjad", "consonants written and joined, vowels marked with dots"),
    "Thaana": ("alphabet", "consonants and obligatory vowel marks, written right to left"),
    "Adlam": ("alphabet", "devised in the 1980s by two teenage brothers for their own "
                          "language"),
    "Tifinagh": ("alphabet", "a consonantal script of the Sahara, in use for two thousand "
                             "years and revived as an official script"),
    "N'Ko": ("alphabet", "devised in 1949 by Solomana Kanté for the Manding languages of "
                         "West Africa, written right to left"),
    "Devanagari": ("abugida", "each consonant carries a built-in a; other vowels are "
                              "written as marks hung on it"),
    "Bengali": ("abugida", "each consonant carries a built-in vowel, changed by marks"),
    "Gurmukhi": ("abugida", "each consonant carries a built-in vowel, changed by marks"),
    "Gujarati": ("abugida", "as Devanagari, without the line along the top"),
    "Oriya": ("abugida", "each consonant carries a built-in vowel; the rounded tops come "
                         "from writing on palm leaf"),
    "Tamil": ("abugida", "with far fewer consonants than its neighbours — no separate "
                         "letters for voiced stops at all"),
    "Telugu": ("abugida", "each consonant carries a built-in vowel, changed by marks"),
    "Kannada": ("abugida", "each consonant carries a built-in vowel, changed by marks"),
    "Malayalam": ("abugida", "each consonant carries a built-in vowel; famous for its "
                             "consonant clusters"),
    "Sinhala": ("abugida", "each consonant carries a built-in vowel, changed by marks"),
    "Thai": ("abugida", "vowels are written before, after, above or below the consonant "
                        "they follow in speech"),
    "Lao": ("abugida", "vowels written around the consonant; no spaces between words"),
    "Khmer": ("abugida", "two series of consonants, each carrying a different built-in "
                         "vowel — so the same mark reads two ways"),
    "Myanmar": ("abugida", "each consonant carries a built-in vowel; the round shapes "
                           "come from writing on palm leaf"),
    "Tibetan": ("abugida", "consonants stack vertically, and the written form preserves "
                           "sounds that stopped being pronounced centuries ago"),
    "Balinese": ("abugida", "each consonant carries a built-in vowel, changed by marks"),
    "Javanese": ("abugida", "each consonant carries a built-in vowel, changed by marks"),
    "Ethiopic": ("syllabary", "a grid: each consonant appears in seven shapes, one per "
                              "vowel, so the sign is the whole syllable"),
    "Vai": ("syllabary", "one sign per syllable, invented about 1833 by Momolu Duwalu "
                         "Bukele, who said it came to him in a dream"),
    "Cherokee": ("syllabary", "one sign per syllable, devised by Sequoyah, who could not "
                              "read any script when he began"),
    "Yi": ("syllabary", "one sign per syllable, standardised in 1974 from a much older "
                        "and much larger set"),
    "Hiragana": ("syllabary", "one sign per syllable, used for grammar and native words"),
    "Katakana": ("syllabary", "one sign per syllable, used for foreign words and emphasis"),
    "Kana": ("syllabary", "one sign per syllable"),
    "Canadian syllabics": ("syllabary", "a sign's orientation carries its vowel — rotate it "
                                        "and the vowel changes"),
    "Han": ("logography", "one character per word or per part of a word, not per sound"),
    "Hangul": ("featural alphabet", "letters are grouped into square syllable blocks, and "
                                    "each letter's shape shows how the mouth makes it"),
    "Bopomofo": ("phonetic notation", "a sound-spelling system used to teach reading, "
                                      "not to write the language in full"),
    "Ol": ("alphabet", "devised in 1925 for Santali, its letter shapes drawn from objects"),
    "Meetei": ("abugida", "each consonant carries a built-in vowel; letters are named "
                          "after parts of the body"),
    "Hanifi": ("alphabet", "devised in the 1980s for Rohingya, written right to left"),
    "Osage": ("alphabet", "devised in the 2000s by the Osage Nation to replace a Latin "
                          "spelling that fitted the language badly"),
    "Mongolian": ("alphabet", "written in vertical lines, top to bottom, left to right"),
    "Bamum": ("syllabary", "devised about 1896 by King Njoya, who reduced it from "
                           "pictographs to syllables over six revisions"),
    "Coptic": ("alphabet", "Greek letters plus six kept from demotic Egyptian"),
    "Runic": ("alphabet", "cut into wood and stone, which is why it has so few curves"),
}

UNIT_GLOSS = {
    "LETTER": ["letters", ""],
    "SYLLABLE": ["syllable signs", "each one is a consonant with its vowel built in"],
    "IDEOGRAPH": ["characters", "each standing for a word or part of one"],
    "VOWEL SIGN": ["vowel marks", "written onto a consonant rather than beside it"],
    "SIGN": ["signs", ""],
    "DIGIT": ["digits", ""],
    "other": ["signs", ""],
    "SYLLABLE_AS_LETTER": ["syllable signs", "one sign for a whole syllable"],
}

# A script whose SCRIPT_KIND is a syllabary but whose characters Unicode names LETTER — the
# Cherokee case. "85 letters" under a heading that says syllabary contradicts itself.
KIND_LETTER = {"syllabary": ["syllable signs", "one sign for a whole syllable"],
               "logography": ["characters", "each standing for a word or part of one"]}

# Where a language uses several systems at once, naming only the biggest is false: Japanese is
# not "a logography". Keyed by the sorted set of scripts, so it cannot land on the wrong one.
MIXED = {
    ("Han", "Hiragana", "Katakana"): (
        "mixed",
        "three systems in the same sentence — Chinese characters for word stems, hiragana "
        "for the grammar around them, katakana for foreign words"),
    ("Han", "Hiragana", "Kana", "Katakana"): (
        "mixed",
        "three systems in the same sentence — Chinese characters for word stems, hiragana "
        "for the grammar around them, katakana for foreign words"),
    ("Bopomofo", "Han"): (
        "mixed",
        "characters for the language itself, with a sound-spelling alphabet used to teach "
        "them"),
    ("Han", "Hangul"): (
        "mixed", "an alphabet, with Chinese characters still used for some roots"),
}

# The script subtag of a CLDR locale, as a label a visitor can read.
SUBTAG = {"Latn": "Latin", "Cyrl": "Cyrillic", "Arab": "Arabic", "Deva": "Devanagari",
          "Hans": "simplified characters", "Hant": "traditional characters",
          "Adlm": "Adlam", "Mong": "Mongolian script", "Tfng": "Tifinagh",
          "Vaii": "Vai", "Nkoo": "N'Ko", "Cans": "Canadian syllabics", "Ethi": "Ethiopic",
          "Beng": "Bengali", "Guru": "Gurmukhi", "Olck": "Ol Chiki", "Rohg": "Hanifi",
          "Java": "Javanese", "Thaa": "Thaana", "Syrc": "Syriac", "Hebr": "Hebrew",
          "Grek": "Greek", "Armn": "Armenian", "Geor": "Georgian", "Mtei": "Meitei Mayek",
          "Tibt": "Tibetan", "Mymr": "Myanmar", "Khmr": "Khmer", "Taml": "Tamil",
          "Telu": "Telugu", "Knda": "Kannada", "Mlym": "Malayalam", "Sinh": "Sinhala",
          "Gujr": "Gujarati", "Orya": "Odia", "Bugi": "Buginese", "Cham": "Cham",
          "Yiii": "Yi", "Plrd": "Miao", "Bamu": "Bamum", "Osge": "Osage", "Cher": "Cherokee"}


# ---------------------------------------------------------------------------
# THE MACROLANGUAGE BRIDGE.
#
# CLDR is keyed by locale and its locales are frequently ISO 639-3 *macrolanguages*: `ar` is
# `ara`, which is not a language but a bag of thirty. `zh` is `zho`. `fa` is `fas`. Glottolog
# has no macrolanguages, so the plain ISO join drops Arabic, Persian, Chinese, Malay, Uzbek,
# Azerbaijani, Kurdish, Mongolian, Swahili, Oromo, Nepali, Pashto, Estonian, Serbian, Croatian,
# Bosnian, Norwegian, Inuktitut, Konkani, Yiddish, Malagasy, Guarani and Albanian on the floor —
# 72 locales, and Chinese silently fell back to a 212-character sample of its own UDHR.
#
# So the bridge is authored, and it is keyed by EXACT GLOTTOLOG NAME and resolved by machine,
# the same discipline as build_notable.py: a name that does not match, or matches twice, stops
# the build rather than landing the wrong alphabet on the wrong language.
#
# Where CLDR's letters describe one standardised variety rather than the whole macrolanguage,
# the note says which — because "the Persian alphabet" and "the alphabet CLDR records for
# Iranian Persian" are different claims.
#
# WHAT IS DELIBERATELY REFUSED is listed in DECLINED below, with the reason. A macrolanguage
# with several equal members and no single standard has no correct target, and guessing one
# would put a real alphabet on a language that does not use it.
# ---------------------------------------------------------------------------
BRIDGE: dict[str, tuple[str, str]] = {
    "ar": ("Standard Arabic", ""),
    "fa": ("Western Farsi", "CLDR's Persian is the Iranian standard"),
    "zh": ("Mandarin Chinese", ""),
    "zh-Hans": ("Mandarin Chinese", ""),
    "zh-Hant": ("Mandarin Chinese", ""),
    "zh-Latn": ("Mandarin Chinese", "Pinyin — a Latin spelling of Mandarin, not a script "
                                    "it is normally written in"),
    "ms": ("Standard Malay", ""),
    "ms-Arab": ("Standard Malay", "Jawi, the Arabic script Malay was written in before "
                                  "the Latin one"),
    "uz": ("Northern Uzbek", ""),
    "uz-Arab": ("Northern Uzbek", ""),
    "uz-Cyrl": ("Northern Uzbek", ""),
    "uz-Latn": ("Northern Uzbek", ""),
    "az": ("North Azerbaijani", ""),
    "az-Arab": ("North Azerbaijani", ""),
    "az-Cyrl": ("North Azerbaijani", ""),
    "az-Latn": ("North Azerbaijani", ""),
    "ku": ("Northern Kurdish", "CLDR's Kurdish is Kurmanji"),
    "ku-Arab": ("Northern Kurdish", ""),
    "ku-Latn": ("Northern Kurdish", ""),
    "mn": ("Halh Mongolian", ""),
    "mn-Mong": ("Halh Mongolian", ""),
    "sw": ("Swahili", ""),
    "om": ("West Central Oromo", ""),
    "ne": ("Nepali", ""),
    "ps": ("Northern Pashto", "the letters of the Kabul and Peshawar standard"),
    "et": ("Estonian", ""),
    "hr": ("Serbian-Croatian-Bosnian", "the Croatian standard"),
    "bs": ("Serbian-Croatian-Bosnian", "the Bosnian standard"),
    "bs-Cyrl": ("Serbian-Croatian-Bosnian", "the Bosnian standard in Cyrillic"),
    "bs-Latn": ("Serbian-Croatian-Bosnian", "the Bosnian standard in Latin"),
    "sr": ("Serbian-Croatian-Bosnian", "the Serbian standard"),
    "sr-Cyrl": ("Serbian-Croatian-Bosnian", "the Serbian standard in Cyrillic"),
    "sr-Latn": ("Serbian-Croatian-Bosnian", "the Serbian standard in Latin"),
    "nb": ("Norwegian", "Bokmål"),
    "nn": ("Norwegian", "Nynorsk"),
    "iu": ("Eastern Canadian Inuktitut", ""),
    "iu-Latn": ("Eastern Canadian Inuktitut", ""),
    "kok": ("Goan Konkani", ""),
    "kok-Deva": ("Goan Konkani", ""),
    "kok-Latn": ("Goan Konkani", ""),
    "doi": ("Dogri", ""),
    "yi": ("Eastern Yiddish", ""),
    "mg": ("Plateau Malagasy", "the Merina standard, which is the written language"),
    "gn": ("Paraguayan Guaraní", ""),
    "syr": ("Classical Syriac", ""),
    "sq": ("Northern Tosk Albanian", "standard Albanian is built on Tosk"),
    "qu": ("Cusco Quechua", "the three-vowel Southern Quechua standard"),
    "za": ("Yongbei Zhuang", "Standard Zhuang is built on this variety"),
    "bua": ("Russia Buriat", "the Cyrillic standard"),
    "ff-Adlm": ("Pular", "Adlam was devised for this language"),
}

DECLINED: dict[str, str] = {
    "ff": "Fula's Latin orthography is shared across a dozen separate Glottolog languages; "
          "there is no single one to attach it to",
    "ff-Latn": "same as ff",
    "bal": "Balochi is a macrolanguage of three members with no single written standard",
    "bal-Arab": "same as bal", "bal-Latn": "same as bal",
    "sc": "Sardinian is a macrolanguage of four members; the common written norm spans "
          "Logudorese and Campidanese and matches neither",
    "raj": "Rajasthani has no language-level node in Glottolog",
    "nr": "ISO nbl (South Ndebele) has no matching language-level Glottolog node here",
    "kln": "Kalenjin is a macrolanguage",
    "luy": "Luyia is a macrolanguage",
    "ltg": "Glottolog files Latgalian as a variety of Latvian, which has its own letters",
    "sgs": "Glottolog files Samogitian as a variety of Lithuanian, which has its own letters",
    "kpe": "Kpelle is a macrolanguage of two members",
    "zgh": "Standard Moroccan Tamazight is a composite standard over three languages; "
           "Tachelhit and Central Moroccan Berber carry the Tifinagh letters instead",
    "und": "the undetermined-language locale; not a language",
    "nqo": "ISO nqo is the literary Manding standard written in N'Ko rather than a spoken "
           "language; Glottolog has no node for it, and the N'Ko letters belong to the "
           "Manding languages that use them",
    "eo": "constructed; this build holds languages with first-language speaker communities",
    "ia": "constructed", "ie": "constructed", "io": "constructed", "jbo": "constructed",
    "vo": "constructed", "tok": "constructed",
}


# ---------------------------------------------------------------------------
# UnicodeSet parsing. CLDR writes exemplars in UnicodeSet notation:
#     [a b c-e {ch} ‌ \- é]
# Elements are space-separated; `X-Y` is an inclusive codepoint range; `{seq}` is a
# multi-character unit the language treats as one letter (Dutch {ij}, Hungarian {dzs});
# a backslash escapes a literal. Getting the range syntax wrong silently turns
# "the 26 letters of English" into "three letters and two hyphens", so this is parsed
# rather than split, and the parser has a selftest.
# ---------------------------------------------------------------------------
def _unescape(s: str) -> str:
    out, i = [], 0
    while i < len(s):
        c = s[i]
        if c == "\\" and i + 1 < len(s):
            n = s[i + 1]
            if n == "u" and i + 5 < len(s) + 1:
                try:
                    out.append(chr(int(s[i + 2:i + 6], 16)))
                    i += 6
                    continue
                except ValueError:
                    pass
            if n == "U" and i + 9 < len(s) + 1:
                try:
                    out.append(chr(int(s[i + 2:i + 10], 16)))
                    i += 10
                    continue
                except ValueError:
                    pass
            out.append(n)
            i += 2
            continue
        out.append(c)
        i += 1
    return "".join(out)


def parse_set(spec: str) -> list[str]:
    """UnicodeSet string -> the list of units, in CLDR's own order.

    Order matters and is not sorted: CLDR lists Hindi's independent vowels before its
    consonants before its vowel signs, which is the order a reader learns them in.
    """
    if not spec:
        return []
    s = spec.strip()
    if not (s.startswith("[") and s.endswith("]")):
        return []
    s = s[1:-1]
    # The guard below must look for an UNESCAPED bracket. Testing `"[" in s` refused every
    # CLDR punctuation set, because they all contain `\[` and `\]` as literal characters —
    # which silently removed the marks row from every language in the museum.
    if re.search(r"(?<!\\)\[", s):
        return []
    units: list[str] = []
    i, n = 0, len(s)
    pending: str | None = None          # last single unit, eligible to start a range

    def flush():
        nonlocal pending
        if pending is not None:
            units.append(pending)
            pending = None

    while i < n:
        c = s[i]
        if c in " \t\n":
            i += 1
            continue
        if c == "{":                     # multi-character letter
            j = s.find("}", i)
            if j < 0:
                break
            flush()
            units.append(_unescape(s[i + 1:j]))
            i = j + 1
            continue
        if c == "-" and pending is not None:
            # a range: pending is the low end, next unit is the high end
            i += 1
            while i < n and s[i] in " \t\n":
                i += 1
            if i >= n:
                units.append("-")
                pending = None
                break
            if s[i] == "\\":
                m = re.match(r"\\(?:u[0-9A-Fa-f]{4}|U[0-9A-Fa-f]{8}|.)", s[i:])
                adv = len(m.group(0)) if m else 2
                hi = _unescape(s[i:i + adv])
                i += adv
            else:
                hi = s[i]
                i += 1
            lo = pending
            pending = None
            if len(lo) == 1 and len(hi) == 1 and ord(hi) >= ord(lo):
                units.extend(chr(k) for k in range(ord(lo), ord(hi) + 1))
            else:
                units.extend([lo, hi])
            continue
        if c == "\\":
            m = re.match(r"\\(?:u[0-9A-Fa-f]{4}|U[0-9A-Fa-f]{8}|.)", s[i:])
            tok = m.group(0) if m else s[i:i + 2]
            flush()
            pending = _unescape(tok)
            i += len(tok)
            continue
        # a plain character, possibly followed by combining marks that belong to it
        j = i + 1
        while j < n and unicodedata.combining(s[j]):
            j += 1
        flush()
        pending = s[i:j]
        i = j
    flush()
    seen, out = set(), []
    for u in units:
        if u and u not in seen:
            seen.add(u)
            out.append(u)
    return out


def _parse_selftest() -> None:
    a = parse_set("[a-c x {ch} \\u200C]")
    assert a == ["a", "b", "c", "x", "ch", "‌"], a
    b = parse_set("[a-z]")
    assert len(b) == 26 and b[0] == "a" and b[-1] == "z", len(b)
    c = parse_set("[\\- , .]")
    assert c == ["-", ",", "."], c
    d = parse_set("[0० 1१]")   # CLDR pairs ASCII with native digits, no space
    assert d == ["0०", "1१"] or d == ["0", "०", "1", "१"], d
    e = parse_set("[[a-z]-[q]]")         # a difference set is refused, not mangled
    assert e == [], e
    f = parse_set("[ъ ь ѣ]")
    assert f == ["ъ", "ь", "ѣ"], f
    g = parse_set("[e é]")          # a combining mark stays attached to its base
    assert len(g) == 2, g
    # the bug that removed every marks row: an escaped bracket is a literal, not a subset
    h = parse_set("[\\- , . … । ॥ \\[ \\] ॰]")
    assert "।" in h and "[" in h and "]" in h, h
    print("parse_set selftest OK")


# Unicode character names are the source for both the script and the unit type, but a name's
# script part is not always one token. `CANADIAN SYLLABICS E` truncated to "Canadian", and
# because `unit_of` had no keyword for SYLLABICS either, all 206 syllabics characters fell
# through into an unnamed bucket which then labelled itself Latin — Inuktitut, Swampy Cree and
# Ojibwa each showed a Latin alphabet they do not use. Both halves are fixed here.
SCRIPT_PREFIX = [
    ("CANADIAN SYLLABICS", "Canadian syllabics"),
    ("NYIAKENG PUACHUE HMONG", "Nyiakeng Puachue Hmong"),
    ("HANIFI ROHINGYA", "Hanifi Rohingya"),
    ("MEETEI MAYEK", "Meetei Mayek"),
    ("MASARAM GONDI", "Masaram Gondi"),
    ("GUNJALA GONDI", "Gunjala Gondi"),
    ("MENDE KIKAKUI", "Mende Kikakui"),
    ("SYLOTI NAGRI", "Syloti Nagri"),
    ("PAHAWH HMONG", "Pahawh Hmong"),
    ("NEW TAI LUE", "New Tai Lue"),
    ("TAI THAM", "Tai Tham"),
    ("TAI VIET", "Tai Viet"),
    ("TAI LE", "Tai Le"),
    ("KAYAH LI", "Kayah Li"),
    ("OL CHIKI", "Ol Chiki"),
    ("NKO", "N'Ko"),
    ("OL ONAL", "Ol Onal"),
    ("EXTENDED ARABIC-INDIC", "Arabic"),
    ("ARABIC-INDIC", "Arabic"),
    ("KIRAT RAI", "Kirat Rai"),
    ("PHAGS-PA", "Phags-pa"),
]

# Unicode's general category, which every character has. This is the backstop that makes
# classification total: 400-odd characters carry no keyword in their name at all — every
# Arabic haraka, every Syriac vowel point, DEVANAGARI OM — and a keyword list can only ever
# be a list of the cases someone thought of.
CAT_UNIT = {"Lu": "LETTER", "Ll": "LETTER", "Lt": "LETTER", "Lm": "LETTER", "Lo": "LETTER",
            "Mn": "MARK", "Mc": "MARK", "Me": "MARK",
            "Nd": "DIGIT", "Nl": "DIGIT", "No": "DIGIT",
            "Pc": "SIGN", "Pd": "SIGN", "Ps": "SIGN", "Pe": "SIGN", "Pi": "SIGN",
            "Pf": "SIGN", "Po": "SIGN", "Sm": "SIGN", "Sc": "SIGN", "Sk": "SIGN",
            "So": "SIGN", "Cf": "SIGN"}


# ISO 15924, so the alphabet can be scored against an INDEPENDENT witness: the script code
# recorded for the UDHR translation we ship. The two come from different places — CLDR's
# survey process and the UN's translators — and where they disagree that is either a bug here
# or a language with two orthographies. Both are worth knowing; the first three times this ran
# it found a bug (206 Canadian syllabics characters reported as a Latin alphabet).
ISO15924 = {
    "Latin": "Latn", "Cyrillic": "Cyrl", "Arabic": "Arab", "Devanagari": "Deva",
    "Greek": "Grek", "Hebrew": "Hebr", "Bengali": "Beng", "Gurmukhi": "Guru",
    "Gujarati": "Gujr", "Oriya": "Orya", "Tamil": "Taml", "Telugu": "Telu",
    "Kannada": "Knda", "Malayalam": "Mlym", "Sinhala": "Sinh", "Thai": "Thai",
    "Lao": "Laoo", "Tibetan": "Tibt", "Myanmar": "Mymr", "Khmer": "Khmr",
    "Ethiopic": "Ethi", "Armenian": "Armn", "Georgian": "Geor", "Hangul": "Hang",
    "Han": "Hani", "Hiragana": "Hira", "Katakana": "Kana", "Kana": "Jpan",
    "Adlam": "Adlm", "Vai": "Vaii", "N'Ko": "Nkoo", "Cherokee": "Cher",
    "Canadian syllabics": "Cans", "Ol Chiki": "Olck", "Tifinagh": "Tfng",
    "Thaana": "Thaa", "Syriac": "Syrc", "Javanese": "Java", "Balinese": "Bali",
    "Buginese": "Bugi", "Cham": "Cham", "Tai Le": "Tale", "New Tai Lue": "Talu",
    "Tai Tham": "Lana", "Meetei Mayek": "Mtei", "Saurashtra": "Saur",
    "Sundanese": "Sund", "Hanifi Rohingya": "Rohg", "Yi": "Yiii", "Miao": "Plrd",
    "Bamum": "Bamu", "Osage": "Osge", "Masaram Gondi": "Gonm", "Kayah Li": "Kali",
    "Lisu": "Lisu", "Newa": "Newa", "Chakma": "Cakm", "Coptic": "Copt",
    "Runic": "Runr", "Mongolian": "Mong", "Bopomofo": "Bopo", "Deseret": "Dsrt",
    "Shavian": "Shaw", "Nyiakeng Puachue Hmong": "Hmnp", "Limbu": "Limb",
    "Lepcha": "Lepc", "Batak": "Batk", "Rejang": "Rjng", "Tagalog": "Tglg",
}
CODE_NAME = {v: k for k, v in ISO15924.items()}
# Codes that name the same writing in a different grain: Jpan IS Han+Hiragana+Katakana.
SCRIPT_SAME = {("Hani", "Jpan"), ("Hira", "Jpan"), ("Kana", "Jpan"), ("Hani", "Hans"),
               ("Hani", "Hant"), ("Hani", "Kore"), ("Hang", "Kore"), ("Hani", "Zyyy")}


def witness_check(out: dict, texts: dict, names: dict) -> dict:
    """Score every alphabet's script against the script of the prose we ship for it."""
    agree = dis = nowit = unmapped = 0
    bad = []
    for gc, v in out.items():
        t = texts.get(gc)
        wit = (t or {}).get("s")
        if not wit:
            nowit += 1
            continue
        ours = [g["script"] for g in v.get("groups", [])]
        ours += [a["groups"][0]["script"] for a in v.get("also", []) if a.get("groups")]
        codes = {ISO15924[o] for o in ours if o in ISO15924}
        if not codes:
            unmapped += 1
            continue
        if wit in codes or any((c, wit) in SCRIPT_SAME or (wit, c) in SCRIPT_SAME
                               for c in codes):
            agree += 1
        else:
            dis += 1
            bad.append((names.get(gc, gc), v["tier"], wit, sorted(codes)))
            # A language with two orthographies: say so on the card rather than hide it.
            v["prose_script"] = CODE_NAME.get(wit, wit)
    tot = agree + dis
    return {"agree": agree, "disagree": dis, "no_witness": nowit,
            "unmapped": unmapped, "rate": (agree / tot if tot else 0.0), "bad": bad}


def script_of(ch: str) -> str | None:
    """The script a character belongs to, from Unicode's own name for it."""
    try:
        nm = unicodedata.name(ch)
    except ValueError:
        return None
    for pre, label in SCRIPT_PREFIX:
        if nm.startswith(pre):
            return label
    tok = nm.split(" ")[0]
    if tok.startswith("CJK"):
        return "Han"
    if tok in SCRIPT_FIX:
        return SCRIPT_FIX[tok]
    if "-" in tok and tok.split("-")[0] in SCRIPT_FIX:
        return SCRIPT_FIX[tok.split("-")[0]]
    return tok.title().replace("_", " ")


def unit_of(ch: str) -> str:
    """What kind of unit this is — the difference between an alphabet and an abugida."""
    try:
        nm = unicodedata.name(ch)
    except ValueError:
        nm = ""
    if "VOWEL SIGN" in nm:
        return "VOWEL SIGN"
    if "INDEPENDENT VOWEL" in nm:
        return "LETTER"          # Khmer's independent vowels are letters, not marks
    if "SYLLABICS" in nm or "SYLLABLE" in nm:
        return "SYLLABLE"
    if "IDEOGRAPH" in nm:
        return "IDEOGRAPH"
    for k in ("LETTER", "TONE", "DIGIT", "MARK", "SIGN", "CHARACTER"):
        if k in nm:
            return k
    return CAT_UNIT.get(unicodedata.category(ch), "SIGN")


def _compat_jamo() -> dict[str, str]:
    """suffix of a Unicode jamo name -> the standalone form of that letter.

    U+1100 CHOSEONG KIYEOK, U+11A8 JONGSEONG KIYEOK and U+3131 HANGUL LETTER KIYEOK are three
    encodings of one letter. The first two are *conjoining* — they render with a gap where the
    rest of the syllable should be, which in a chart of letters looks like a font error. The
    HANGUL LETTER block is the standalone form, and Unicode's own names are what connect them,
    so no table is authored here.
    """
    m: dict[str, str] = {}
    for c in range(0x3131, 0x3190):
        try:
            nm = unicodedata.name(chr(c))
        except ValueError:
            continue
        if nm.startswith("HANGUL LETTER "):
            m[nm[len("HANGUL LETTER "):]] = chr(c)
    return m


def _standalone(cp: int, compat: dict[str, str]) -> str:
    try:
        nm = unicodedata.name(chr(cp))
    except ValueError:
        return chr(cp)
    for pre in ("HANGUL CHOSEONG ", "HANGUL JUNGSEONG ", "HANGUL JONGSEONG "):
        if nm.startswith(pre):
            return compat.get(nm[len(pre):], chr(cp))
    return chr(cp)


def hangul_parts(units: list[str]) -> dict | None:
    """Recover Korean's real letters from the syllable blocks, by arithmetic.

    S = 0xAC00 + (L*21 + V)*28 + T, so L, V and T fall straight out of any block. This is a
    measurement of the shipped set, which is why the resulting counts can be trusted — and
    each recovered jamo is then converted to its standalone form so a chart of them reads as
    letters rather than as a row of broken glyphs.
    """
    compat = _compat_jamo()
    li, vi, ti = set(), set(), set()
    n = 0
    for u in units:
        if len(u) != 1:
            continue
        c = ord(u)
        if not (0xAC00 <= c <= 0xD7A3):
            continue
        n += 1
        s = c - 0xAC00
        li.add(s // 588)
        vi.add((s % 588) // 28)
        t = s % 28
        if t:
            ti.add(t - 1)
    if n < 100:
        return None
    init = [_standalone(0x1100 + i, compat) for i in sorted(li)]
    med = [_standalone(0x1161 + i, compat) for i in sorted(vi)]
    fin = [_standalone(0x11A8 + i, compat) for i in sorted(ti)]
    # NOT DERIVED, and the difference matters. 19 initials, 21 medials, 27 finals and 11,172
    # blocks are all MEASURED off the set above. "24 letters" is not: it is the 한글 자모, the
    # alphabet Korean children are taught, and the other shapes here are doubles (ㄲ from ㄱ)
    # and compounds (ㅘ from ㅗ and ㅏ) built out of those 24. No Unicode property separates
    # them — the jamo blocks carry no decompositions at all, which was checked — so the number
    # is stated as an authored fact with its reason, rather than counted and presented as one.
    return {"blocks": n, "initial": init, "medial": med, "final": fin,
            "letters": 24,
            "letters_note": "the alphabet Korean children learn is 24 letters; the rest of "
                            "the shapes here are doubles and compounds built out of those"}


def describe(units: list[str]) -> list[dict]:
    """The exemplar set, taken apart into (script, unit type) groups, largest first.

    Every SIGN, MARK and unnamed character folds into ONE trailing "signs" row, whatever
    script it came from. Japanese otherwise produced three separate rows holding two, two and
    one iteration mark, which reads as a taxonomy rather than as an alphabet.
    """
    groups: dict[tuple[str, str], list[str]] = {}
    extras: list[str] = []
    for u in units:
        # Prefer a real base character; fall back to a combining mark, because in an abugida
        # a lone vowel sign IS the unit (Devanagari ि, Khmer ា) and dropping marks here
        # deleted the vowel-mark row from every abugida in the museum. Only whitespace,
        # which belongs to no script, is skipped.
        base = next((c for c in u if unicodedata.category(c)[0] not in ("M", "Z")), None)
        if base is None:
            base = next((c for c in u if unicodedata.category(c)[0] == "M"), None)
        if base is None:
            continue
        sc = script_of(base)
        if not sc or sc == "Space":
            continue
        ut = unit_of(base)
        if ut in ("SIGN", "MARK", "other"):
            extras.append(u)
            continue
        groups.setdefault((sc, ut), []).append(u)
    out = []
    for (sc, ut), us in groups.items():
        out.append({"script": sc, "unit": ut, "n": len(us),
                    "show": us[:SHOW_MAX], "truncated": len(us) > SHOW_MAX})
    out.sort(key=lambda g: (-g["n"], g["script"]))
    if extras:
        # Measured, not defaulted. `if out else "Latin"` invented a Latin alphabet for every
        # language whose whole character set fell through the classifier.
        ec = Counter(s for s in (script_of(next((c for c in u
                                                 if unicodedata.category(c)[0] != "Z"), u[0]))
                                 for u in extras) if s)
        sc0 = (ec.most_common(1)[0][0] if ec else
               (out[0]["script"] if out else "unrecorded"))
        out.append({"script": sc0, "unit": "SIGN", "n": len(extras), "any": True,
                    "show": extras[:SHOW_MAX], "truncated": len(extras) > SHOW_MAX})
    return out


def set_kind(e: dict, groups: list[dict]) -> None:
    """Name the writing system, and refuse to name it after only its largest part."""
    if not groups:
        return
    # Ignore the trailing signs row when deciding what the system IS.
    real = [g for g in groups if g["unit"] != "SIGN"] or groups
    scripts = tuple(sorted({g["script"] for g in real}))
    if len(scripts) > 1:
        mk = MIXED.get(scripts)
        if mk:
            e["kind"], e["kind_note"] = mk
            return
        kinds = {SCRIPT_KIND[s][0] for s in scripts if s in SCRIPT_KIND}
        if len(kinds) > 1:
            e["kind"] = "mixed"
            e["kind_note"] = ("written with more than one system at once — "
                              + ", ".join(scripts))
            return
    k = SCRIPT_KIND.get(real[0]["script"])
    if not k:
        return
    e["kind"], e["kind_note"] = k
    # Cherokee's characters are named LETTER by Unicode but the script is a syllabary.
    for g in groups:
        if g["unit"] == "LETTER" and k[0] in KIND_LETTER:
            g["unit"] = "SYLLABLE_AS_LETTER"


def observed(text: str) -> tuple[list[str], int, int]:
    freq: Counter = Counter()
    total = 0
    for ch in text:
        cat = unicodedata.category(ch)
        if cat[0] == "L" or cat in ("Mn", "Mc"):
            total += 1
            freq[ch] += 1
    order = [c for c, _ in freq.most_common()]
    return order, total, len(freq)


def _selftest() -> None:
    assert script_of("क") == "Devanagari", script_of("क")
    assert script_of("一") == "Han", script_of("一")
    assert script_of("가") == "Hangul", script_of("가")
    assert script_of("ሀ") == "Ethiopic", script_of("ሀ")
    assert script_of("a") == "Latin"
    # the class that made three languages show an alphabet they do not use
    assert script_of("\u1401") == "Canadian syllabics", script_of("\u1401")
    assert unit_of("\u1401") == "SYLLABLE", unit_of("\u1401")
    assert unit_of("\u064e") == "MARK", unit_of("\u064e")     # ARABIC FATHA, no keyword
    # DEVANAGARI OM carries no keyword in its name; Unicode's category for it is Lo, so the
    # backstop returns LETTER. That is Unicode's own classification and we follow it.
    assert unit_of("\u0950") == "LETTER", unit_of("\u0950")
    assert unit_of("\u0903") == "SIGN", unit_of("\u0903")     # DEVANAGARI SIGN VISARGA
    assert unit_of("\u17a3") == "LETTER", unit_of("\u17a3")   # KHMER INDEPENDENT VOWEL
    d2 = describe([chr(c) for c in range(0x1401, 0x1420)])
    assert d2 and d2[0]["script"] == "Canadian syllabics", d2
    assert script_of("α") == "Greek"
    assert unit_of("ሀ") == "SYLLABLE", unit_of("ሀ")
    assert unit_of("ि") == "VOWEL SIGN", unit_of("ि")
    assert unit_of("क") == "LETTER"
    assert unit_of("一") == "IDEOGRAPH"
    # Hangul arithmetic must recover exactly the real inventory from the full block range
    hp = hangul_parts([chr(c) for c in range(0xAC00, 0xD7A4)])
    assert hp and hp["blocks"] == 11172, hp
    assert len(hp["initial"]) == 19 and len(hp["medial"]) == 21, hp
    assert len(hp["final"]) == 27, hp
    # the standalone forms, not the conjoining ones: ㄱ (U+3131), never ᄀ (U+1100)
    assert hp["initial"][0] == "\u3131" and hp["medial"][0] == "\u314f", hp
    assert hp["final"][0] == "\u3131", hp
    assert hp["letters"] == 24 and hp["letters_note"], hp
    # HTML-escaped prose must not report the letters of the escape sequence
    o, n, d = observed(html.unescape("Direi&#x0074;u"))
    assert "&" not in o and "x" not in o and o and n == len("Direitu"), (o, n)
    print("build_alphabets selftest OK")


if __name__ == "__main__":
    _parse_selftest()
    _selftest()
    src = json.load(open(SRC))
    cldr, i1to3 = src["cldr"], src["iso1_to_iso3"]
    langs = json.load(open(os.path.join(WEB, "languages.json")))
    F = {k: i for i, k in enumerate(langs["fields"])}
    by_iso: dict[str, str] = {}
    names: dict[str, str] = {}
    by_name: dict[str, list[str]] = {}
    for r in langs["rows"]:
        names[r[F["code"]]] = r[F["name"]]
        by_name.setdefault(r[F["name"]], []).append(r[F["code"]])
        iso = r[F["iso"]]
        if iso:
            by_iso.setdefault(iso, r[F["code"]])

    # Resolve the authored bridge by machine. An unmatched or ambiguous name is a build
    # error, not a warning — that is the whole reason the bridge is keyed by name.
    bridge: dict[str, tuple[str, str]] = {}
    for loc, (nm, note) in BRIDGE.items():
        hit = by_name.get(nm) or []
        if len(hit) != 1:
            raise SystemExit(f"bridge entry {loc!r} -> {nm!r} matched {len(hit)} languages; "
                             f"fix the name in BRIDGE")
        bridge[loc] = (hit[0], note)

    def entry_for(loc: str, rec: dict) -> dict:
        # rec holds RAW UnicodeSet strings; interpreting them is this file's job.
        ex = parse_set(rec.get("exemplarCharacters", ""))
        idx = parse_set(rec.get("index", ""))
        groups = describe(ex)
        e: dict = {"locale": loc, "groups": groups, "n": len(ex),
                   "index": idx[:SHOW_MAX], "index_n": len(idx), "tier": "curated"}
        hp = hangul_parts(ex)
        if hp:
            e["hangul"] = hp
        native: list[str] = []
        for u in parse_set(rec.get("numbers", "")):
            native.extend(c for c in u
                          if unicodedata.category(c) == "Nd" and not c.isascii())
        if native:
            e["digits"] = native[:20]
        pu = [u for u in parse_set(rec.get("punctuation", ""))
              if u and not all(c in ASCII_PUNCT or c.isspace() for c in u)]
        if pu:
            e["punctuation"] = pu[:14]
        set_kind(e, groups)
        return e

    # Gather every locale that lands on each glottocode, then dedupe: `sr`, `sr-Cyrl` and
    # `bs-Cyrl` are the same thirty letters, and printing them three times would suggest
    # three alphabets where there is one.
    per_gc: dict[str, list[tuple[str, dict, str]]] = {}
    unresolved, declined = [], []
    for loc, rec in sorted(cldr.items()):
        base = loc.split("-")[0]
        if loc in bridge:
            gc, note = bridge[loc]
        elif base in bridge and loc not in DECLINED:
            gc, note = bridge[base]
        elif loc in DECLINED or base in DECLINED:
            declined.append(loc)
            continue
        else:
            iso3 = base if len(base) == 3 else i1to3.get(base)
            gc = by_iso.get(iso3) if iso3 else None
            note = ""
            if not gc:
                unresolved.append(loc)
                continue
        per_gc.setdefault(gc, []).append((loc, rec, note))

    out: dict[str, dict] = {}
    multi = 0
    empty_cldr: list[str] = []
    for gc, items in per_gc.items():
        # shortest locale tag first — the base language is the primary alphabet
        items.sort(key=lambda t: (len(t[0]), t[0]))
        seen_sig: dict[tuple, dict] = {}
        ordered: list[dict] = []
        for loc, rec, note in items:
            sig = rec.get("exemplarCharacters", "")
            if not parse_set(sig):
                empty_cldr.append(loc)   # falls through to the observed tier below
                continue
            if sig in seen_sig:
                # same letters, different locale: keep the note if the kept one had none
                if note and not seen_sig[sig].get("note"):
                    seen_sig[sig]["note"] = note
                continue
            e = entry_for(loc, rec)
            if note:
                e["note"] = note
            seen_sig[sig] = e
            ordered.append(e)
        if not ordered:
            continue
        head = ordered[0]
        prime = (head["groups"][0]["script"] if head.get("groups") else None)
        for e in ordered[1:]:
            sub = e["locale"].split("-")[1] if "-" in e["locale"] else ""
            e["label"] = SUBTAG.get(sub) or (e["groups"][0]["script"]
                                             if e.get("groups") else "another script")
            sc = e["groups"][0]["script"] if e.get("groups") else None
            if sc == "Latin" and prime and prime != "Latin" and not e.get("note"):
                e["note"] = ("a Latin spelling, used for typing and for transliteration — "
                             "not a script this language is normally written in")
        if len(ordered) > 1:
            head["also"] = ordered[1:]
            multi += 1
        out[gc] = head

    curated = len(out)
    print(f"tier 1 — curated: {curated} languages ({multi} written in more than one script)")
    print(f"   bridge resolved {len(BRIDGE)} macrolanguage/variety locales by name, "
          f"all matched exactly one Glottolog language")
    if declined:
        print(f"   {len(declined)} locales deliberately refused a target:")
        for loc in sorted(set(declined)):
            r = DECLINED.get(loc) or DECLINED.get(loc.split("-")[0], "")
            if not r.startswith("same as") and r != "constructed":
                print(f"      {loc:9s} {r}")
        cons = sorted(l for l in set(declined) if DECLINED.get(l) == "constructed")
        if cons:
            print(f"      {' '.join(cons)}: constructed languages, no L1 community")
    if empty_cldr:
        print(f"   {len(empty_cldr)} locales CLDR lists with no letters filled in "
              f"({' '.join(sorted(empty_cldr))}) — these fall through to the observed tier")
    if unresolved:
        print(f"   {len(unresolved)} locales still unresolved: {' '.join(unresolved)}")

    # ---- tier 2: observed ------------------------------------------------
    texts = json.load(open(os.path.join(WEB, "texts.json")))["by_glottocode"]
    sources = {gc: " ".join(html.unescape(v) for _, v in (rec.get("b") or []))
               for gc, rec in texts.items()}
    origin = {gc: "the UDHR translation held here" for gc in sources}
    # A THIRD SOURCE, for the languages neither CLDR nor our own prose reaches. 316 languages
    # have their own Wikipedia and 75 of those had no letters, with three or more active editors
    # so the articles are written rather than bot-generated. Same footing as the UDHR tier: a
    # measurement of a document, labelled as one, with its sample size.
    wtp = os.path.join(ROOT, "data", "wikipedia", "wikitext.json") \
        if (ROOT := os.path.join(HERE, "..")) else ""
    if os.path.exists(wtp):
        for gc, v in json.load(open(wtp, encoding="utf-8"))["by_glottocode"].items():
            if gc not in sources:
                sources[gc] = v["text"]
                origin[gc] = "articles in this language's own Wikipedia"
    added = 0
    thin = 0
    for gc, body in sources.items():
        if gc in out or gc not in names:
            continue
        chars, total, distinct = observed(body)
        if total < 400:               # too little prose to say anything about an inventory
            thin += 1
            continue
        groups = describe(chars)
        rec2 = {"groups": groups, "n": distinct, "tier": "observed",
                "sample": total, "index": [], "index_n": 0,
                "from": origin.get(gc, "prose held here")}
        set_kind(rec2, groups)
        out[gc] = rec2
        added += 1
    nwiki = sum(1 for gc, v in out.items()
                if v.get("from", "").startswith("articles"))
    print(f"tier 2 — observed from prose: {added} languages "
          f"({nwiki} of them from their own Wikipedia rather than the UDHR; "
          f"{thin} had under 400 characters, too thin to state an inventory)")

    wc = witness_check(out, texts, names)
    print(f"\nindependent witness — the script of the prose we ship for each language")
    print(f"   agree {wc['agree']}  ·  disagree {wc['disagree']}  ·  no witness "
          f"{wc['no_witness']}  ·  script not in the ISO table {wc['unmapped']}")
    print(f"   agreement where a witness exists: {wc['rate']*100:.1f}%")
    for b in sorted(wc["bad"]):
        print(f"      {b[0]:30s} {b[1]:9s} prose in {b[2]}, letters in {'/'.join(b[3])}")
    if wc["bad"]:
        print("   These are languages written in two scripts. The card now says so.")

    meta = {
        "source": "Unicode CLDR exemplarCharacters (curated); character inventory measured "
                  "from the UDHR prose in this build (observed)",
        "licence": "Unicode-3.0",
        "unit_gloss": UNIT_GLOSS,
        "kinds": sorted({v["kind"] for v in out.values() if v.get("kind")}),
        "show_max": SHOW_MAX,
        "curated": curated,
        "observed": added,
        "witness": {k: wc[k] for k in ("agree", "disagree", "no_witness", "rate")},
        "by_glottocode": out,
    }
    json.dump(meta, open(os.path.join(WEB, "alphabets.json"), "w"), ensure_ascii=False)
    kb = os.path.getsize(os.path.join(WEB, "alphabets.json")) / 1024
    print(f"\nwrote web/data/alphabets.json — {len(out)} languages, {kb:.0f} KB")

    # a worked demonstration, so the numbers can be checked by eye
    for gc in ("stan1293", "kore1280", "nucl1643", "hind1269", "amha1245", "cent1989",
               "mand1415", "khme1253", "geor1249"):
        v = out.get(gc)
        if not v:
            continue
        g = ", ".join(f"{x['n']} {x['script']} "
                      f"{UNIT_GLOSS.get(x['unit'], [x['unit'], ''])[0]}"
                      for x in v["groups"][:3])
        extra = "  " + (v.get("kind") or "")
        if v.get("hangul"):
            h = v["hangul"]
            extra = (f"  [{len(h['initial'])} initial + {len(h['medial'])} medial "
                     f"+ {len(h['final'])} final jamo -> {h['blocks']:,} blocks]")
        print(f"  {names.get(gc, gc):22s} {v['tier']:8s} {g}{extra}")
