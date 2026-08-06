#!/usr/bin/env python3
"""D16 — authored words and phrases, for the languages ASJP cannot reach.

ASJP samples living speech from fieldwork, so it is empty for every language that stopped being
spoken before a linguist could record it, and thin for several that are spoken but small. This
file is the authored tier: a short note saying what the writing is and how to read it, then
twelve-odd forms with a transliteration and a gloss.

NAME-RESOLVED, like every other authored tier here. Entries are keyed by EXACT Glottolog name and
resolved to a glottocode by machine, refusing anything that matches zero or more than one
language. Seven of thirty labels once sat on the wrong language because a human typed the code.

FORM SHAPE: (form, transliteration, gloss). An empty transliteration means the form IS the
transliteration — which is the honest answer for the languages whose own letterforms could not be
set with confidence (Oscan and Umbrian in Old Italic, Sogdian in the Sogdian script, Khotanese in
Brahmi). Their notes say so. A wrong glyph presented as a language's own writing is worse than no
glyph; a secure transliteration labelled as one is better than an empty card.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
WEB = os.path.join(ROOT, "web", "data")

PHRASES = {
 "Egyptian (Ancient)": (
  "Hieroglyphs with Egyptological transliteration. Vowels are not written, so the readings are conventional rather than reconstructed pronunciation.",
  [("𓂋𓈖𓆎𓅓𓏏𓊖", "r n km.t", "the speech of Egypt — the language's own name"),
   ("𓋹", "ꜥnḥ", "life — the ankh"),
   ("𓊹", "nṯr", "god"),
   ("𓇳", "rꜥ", "sun; the god Ra"),
   ("𓉐", "pr", "house"),
   ("𓉐𓉻", "pr-ꜥꜣ", "the great house — the word English took as pharaoh"),
   ("𓄤", "nfr", "good, beautiful, complete — the nefer of Nefertiti"),
   ("𓋞", "nbw", "gold"),
   ("𓁹", "jrt", "eye"),
   ("𓈗", "mw", "water"),
   ("𓏏𓄿", "tꜣ", "land"),
   ("𓆓𓂧", "ḏd", "to say"),
   ("𓋴𓈖", "sn", "brother"),
   ("𓋹𓍑𓋴", "ꜥnḥ wḏꜣ snb", "may he live, be prosperous and healthy — written after a king's name")]),
 "Middle English": (
  "Spelling was not standardised; these are common forms.",
  [("water", "water", "water"),
   ("fyr", "fyr", "fire"),
   ("sonne", "sonne", "sun"),
   ("mone", "mone", "moon"),
   ("sterre", "sterre", "star"),
   ("ston", "ston", "stone"),
   ("tree", "tree", "tree"),
   ("hond", "hond", "hand"),
   ("eye", "eye", "eye"),
   ("nyght", "nyght", "night"),
   ("oon", "oon", "one"),
   ("two", "two", "two"),
   ("Whan that Aprille with his shoures soote", "", "when April with its sweet showers — the opening of the Canterbury Tales")]),
 "Old French (842-ca. 1400)": (
  "Two-case Old French; forms vary by region and date.",
  [("aigue", "aigue", "water"),
   ("feu", "feu", "fire"),
   ("soleil", "soleil", "sun"),
   ("lune", "lune", "moon"),
   ("estoile", "estoile", "star"),
   ("pierre", "pierre", "stone"),
   ("arbre", "arbre", "tree"),
   ("main", "main", "hand"),
   ("oil", "oil", "eye"),
   ("nuit", "nuit", "night"),
   ("un", "un", "one"),
   ("dui", "dui", "two"),
   ("Carles li reis, nostre emperere magnes", "", "Charles the king, our great emperor — the opening of the Chanson de Roland")]),
 "Latvian": (
  "Latvian is living; ASJP simply never sampled it.",
  [("ūdens", "ūdens", "water"),
   ("uguns", "uguns", "fire"),
   ("saule", "saule", "sun"),
   ("mēness", "mēness", "moon"),
   ("zvaigzne", "zvaigzne", "star"),
   ("akmens", "akmens", "stone"),
   ("koks", "koks", "tree"),
   ("roka", "roka", "hand"),
   ("acs", "acs", "eye"),
   ("nakts", "nakts", "night"),
   ("viens", "viens", "one"),
   ("divi", "divi", "two"),
   ("valoda", "valoda", "language")]),
 "Venetian": (
  "",
  [("aqua", "aqua", "water"),
   ("fogo", "fogo", "fire"),
   ("sol", "sol", "sun"),
   ("luna", "luna", "moon"),
   ("stéla", "stéla", "star"),
   ("piera", "piera", "stone"),
   ("àlbaro", "àlbaro", "tree"),
   ("man", "man", "hand"),
   ("ocio", "ocio", "eye"),
   ("note", "note", "night"),
   ("un", "un", "one"),
   ("do", "do", "two")]),
 "Classical Tibetan": (
  "Wylie transliteration beside the Tibetan script. The spelling froze in the seventh century, so written clusters are no longer pronounced.",
  [("ཆུ", "chu", "water"),
   ("མེ", "me", "fire"),
   ("ཉི་མ", "nyi ma", "sun"),
   ("ཟླ་བ", "zla ba", "moon"),
   ("སྐར་མ", "skar ma", "star"),
   ("རྡོ", "rdo", "stone"),
   ("ཤིང", "shing", "tree"),
   ("ལག་པ", "lag pa", "hand"),
   ("མིག", "mig", "eye"),
   ("མཚན", "mtshan", "night"),
   ("གཅིག", "gcig", "one"),
   ("གཉིས", "gnyis", "two"),
   ("སངས་རྒྱས", "sangs rgyas", "awakened one — the word used for Buddha")]),
 "Imperial Aramaic (700-300 BCE)": (
  "Given in square script, the form most Aramaic was later copied in.",
  [("מיא", "mayyā", "water"),
   ("נורא", "nūrā", "fire"),
   ("שמשא", "šimšā", "sun"),
   ("ארעא", "arʿā", "earth, land"),
   ("אבן", "ʾeben", "stone"),
   ("ידא", "yadā", "hand"),
   ("עינא", "ʿaynā", "eye"),
   ("מלכא", "malkā", "king"),
   ("חד", "ḥad", "one"),
   ("תרין", "tərēn", "two"),
   ("שלם", "šəlām", "peace")]),

 "Bactrian": (
  "Bactrian is the only Iranian language ever written in the Greek alphabet — a legacy of "
  "Alexander that outlasted Greek rule by seven hundred years. The letter þ (sho) was added for "
  "a sound Greek did not have.",
  [("αριαο", "ariao", "Aryan — what its speakers called their own language"),
   ("βαγο", "bago", "god"),
   ("þαο", "shao", "king; the title of the Kushan rulers"),
   ("οαβαρο", "wabaro", "father"),
   ("μαλο", "malo", "mother"),
   ("κιρδο", "kirdo", "made — the word that opens most Bactrian inscriptions"),
   ("νοβικτο", "nobikhto", "new"),
   ("λρωγο", "lrogo", "long"),
   ("ναμο", "namo", "name"),
   ("βωλο", "bolo", "high"),
   ("οαρδο", "wardo", "town"),
   ("þαοναναοþαο", "shaonanoshao", "king of kings — the Kushan imperial title on the Rabatak "
                                   "inscription")]),
 "Oscan": (
  "Written in an alphabet of its own, derived from Etruscan and read right to left. That script "
  "is not reproduced here: the transliteration below is the scholarly convention, printed in "
  "every edition of the inscriptions, and the letterforms are the part that could not be set "
  "with confidence.",
  [("touto", "", "the people, the community — cognate with German Deutsch and Irish tuath"),
   ("meddíss", "", "the chief magistrate of an Oscan town"),
   ("meddíss túvtíks", "", "magistrate of the people — the highest office"),
   ("aíttíum", "", "share, portion"),
   ("húrz", "", "sacred grove"),
   ("kúmbennieís", "", "of the assembly"),
   ("víteliú", "", "land of calves — one proposed origin of the name Italy"),
   ("níp", "", "not"),
   ("famel", "", "household slave — Latin borrowed it as familia"),
   ("aasas", "", "altars"),
   ("deívaí", "", "to the goddess"),
   ("eítuns", "", "let them go — the word that opens the Pompeii wall notices directing "
                  "defenders to their posts")]),
 "Umbrian": (
  "Recorded almost entirely on the Iguvine Tables, seven bronze plates found at Gubbio in 1444 "
  "which set out the ritual duties of a priestly brotherhood — the fullest surviving account of "
  "any Italic religion outside Rome. Three tables are in the native Umbrian alphabet, four in "
  "Latin letters; the transliteration below is the convention used in every edition.",
  [("ikuvins", "", "of Iguvium, the town — modern Gubbio"),
   ("atiieřiate", "", "the priestly brotherhood whose rites the tables record"),
   ("ute", "", "or"),
   ("pople", "", "the people under arms — Latin populus"),
   ("totar", "", "of the community"),
   ("fetu", "", "let him make, let him sacrifice — the commonest verb on the tables"),
   ("persklu", "", "supplication"),
   ("vitlu", "", "calf"),
   ("erietu", "", "ram"),
   ("purtitu", "", "let him offer"),
   ("subocau", "", "I invoke"),
   ("teřte", "", "let him give")]),
 "Sogdian": (
  "The trade language of the Silk Road, written in a script descended from Aramaic. Those "
  "letterforms are not reproduced here; the transliteration is the standard one. The best-known "
  "Sogdian texts are the Ancient Letters, a mailbag abandoned in a watchtower west of Dunhuang "
  "around 313 and never delivered.",
  [("swγδyk", "soghdik", "Sogdian — the language's own name"),
   ("βγy", "baghi", "god, lord"),
   ("xwtʼw", "khutaw", "lord, ruler"),
   ("nʼm", "nam", "name"),
   ("ptskwʼn", "patskwan", "letter, message"),
   ("myδ", "mith", "day"),
   ("ʼspʼδ", "spadh", "army"),
   ("wʼnʼkw", "wanaku", "thus, so"),
   ("δβr", "dhbar", "give"),
   ("ʼʼpw", "apu", "water"),
   ("prm", "param", "until"),
   ("nwkr", "nokar", "now")]),
 "Khotanese": (
  "An Iranian language of the Silk Road oasis of Khotan, written in Brahmi and preserved almost "
  "entirely in Buddhist manuscripts recovered from the Taklamakan. The Brahmi letterforms are "
  "not reproduced here; the transliteration is the standard scholarly one.",
  [("hvatana", "", "Khotanese — the language's own name, from the name of the kingdom"),
   ("balysa", "", "the Buddha"),
   ("ttīra", "", "three"),
   ("gyasta", "", "god"),
   ("pharu", "", "many"),
   ("kṣīra", "", "land, kingdom"),
   ("hīvī", "", "own"),
   ("aysu", "", "I"),
   ("tta", "", "so, thus"),
   ("padauśśa", "", "teaching"),
   ("uysānaa", "", "living being"),
   ("hauda", "", "seven")]),
 "Silesian": (
  "Written in Latin letters with a Polish-derived orthography agreed in 2010, the ślabikŏrzowy "
  "szrajbōnek, which added ō and ŏ for vowels Polish does not have.",
  [("ślōnskŏ gŏdka", "", "the Silesian language — what its speakers call it"),
   ("dziyń dobry", "", "good day"),
   ("pōn", "", "sir, mister"),
   ("chopiec", "", "boy"),
   ("dzioucha", "", "girl"),
   ("bajtel", "", "child — from German Beutel, and unlike anything in Polish"),
   ("gruba", "", "coal mine — the word a whole region's working life turned on"),
   ("szkoła", "", "school"),
   ("woda", "", "water"),
   ("chleba", "", "bread"),
   ("ôgyń", "", "fire"),
   ("nikiej", "", "never")]),
 "Pontic": (
  "Greek that left the rest of Greek early enough to keep sounds the standard lost — the "
  "infinitive survives, and so does the ancient ē where Modern Greek has i. Written in the Greek "
  "alphabet, and in Turkey by Muslim speakers in Latin letters.",
  [("ρωμαίικα", "romeyka", "the language's own name — Roman, as in Eastern Roman"),
   ("νερόν", "neron", "water"),
   ("ψωμίν", "psomin", "bread — the -ν that Modern Greek dropped is still there"),
   ("μάνα", "mana", "mother"),
   ("έρθαν", "erthan", "they came"),
   ("καλατζεύω", "kalatzevo", "I speak"),
   ("τ' εμόν", "t' emon", "mine"),
   ("ελέπω", "elepo", "I see — from ancient βλέπω, with a vowel Modern Greek lost"),
   ("πουλίν", "poulin", "bird"),
   ("κ' εξέρω", "k' eksero", "I do not know"),
   ("χάριν", "kharin", "thanks"),
   ("τη θάλασσας", "ti thalassas", "of the sea")]),
 "Picard": (
  "Written in Latin letters with several competing spellings, the Feller-Carton system being the "
  "most used. Its speakers in France call it chtimi, from the way northern French renders 'c'est "
  "toi, c'est moi'.",
  [("ch'ti", "", "a northerner, and the language — from ch'est ti, ch'est mi"),
   ("bojour", "", "good day"),
   ("ker", "", "heart"),
   ("kien", "", "dog — Picard keeps the k where French palatalised it to chien"),
   ("cat", "", "cat — likewise, against French chat; English took its cat from the same "
               "Norman-Picard side"),
   ("caud", "", "hot, against French chaud"),
   ("mi", "", "me"),
   ("acater", "", "to buy, against French acheter"),
   ("berlafe", "", "a slap"),
   ("drache", "", "a downpour — the word Belgian French borrowed"),
   ("min", "", "my"),
   ("ravisher", "", "to look at")]),
 "Extremaduran": (
  "Astur-Leonese written in Latin letters, with almost no standard: its written tradition is "
  "essentially the poems of José María Gabriel y Galán at the turn of the twentieth century.",
  [("estremeñu", "", "Extremaduran — the language's own name"),
   ("ehti", "", "this"),
   ("jacel", "", "to do, to make — with the j where Castilian has h and Latin had f"),
   ("jueu", "", "fire"),
   ("águа", "", "water"),
   ("muyel", "", "woman"),
   ("ombri", "", "man"),
   ("cielu", "", "sky"),
   ("tierra", "", "earth"),
   ("palabra", "", "word"),
   ("nueva", "", "new"),
   ("dos", "", "two")]),
 "Fiji Hindi": (
  "Written in Devanagari and in Latin letters. Its vocabulary is Awadhi and Bhojpuri levelled "
  "together, with Fijian and English words that no Indian variety has.",
  [("फ़िजी हिंदी", "Fiji Hindi", "the language's own name"),
   ("हम", "hum", "I — where Standard Hindi uses this for we"),
   ("तुम", "tum", "you"),
   ("काहे", "kaahe", "why"),
   ("खाना", "khana", "food"),
   ("पानी", "paani", "water"),
   ("घर", "ghar", "house"),
   ("कालो", "kaalo", "black"),
   ("बाबा", "baba", "father"),
   ("दादा", "daada", "elder brother"),
   ("सलाम", "salaam", "a greeting, used across religions in Fiji"),
   ("ठीक हai", "thiik hai", "all right")]),
 "Pfaelzisch-Lothringisch": (
  "Palatine German, written in Latin letters with no fixed standard. It is the ancestor of "
  "Pennsylvania German, which is why the two look alike on the page.",
  [("Pälzisch", "", "Palatine — the language's own name"),
   ("Guude", "", "hello — from guten Tag, worn down"),
   ("Bub", "", "boy"),
   ("Mädel", "", "girl"),
   ("Haus", "", "house"),
   ("Woi", "", "wine, against High German Wein"),
   ("Grumbeer", "", "potato — literally ground-pear"),
   ("schaffe", "", "to work"),
   ("Bach", "", "stream"),
   ("Kerwe", "", "the village fair"),
   ("Dubbeglas", "", "the dimpled half-litre wine glass of the Palatinate"),
   ("Ei jo", "", "yes indeed")]),
}

def main():
    L = json.load(open(os.path.join(WEB, "languages.json")))
    F = {k: i for i, k in enumerate(L["fields"])}
    by_name = {}
    for r in L["rows"]:
        by_name.setdefault(r[F["name"]], []).append(r[F["code"]])

    out, bad = {}, []
    for name, (note, items) in PHRASES.items():
        hit = by_name.get(name) or []
        if len(hit) != 1:
            bad.append(f"  {name!r} matched {len(hit)} languages")
            continue
        rec = {"items": [list(i) for i in items]}
        if note:
            rec["note"] = note
        out[hit[0]] = rec
    if bad:
        sys.exit("build_phrases: unresolved names\n" + "\n".join(bad))

    # Every form must be non-empty and every gloss must say something. An entry that renders as a
    # blank row is a defect the card cannot show you.
    for g, rec in out.items():
        for f, t, gl in rec["items"]:
            if not f.strip() or not gl.strip():
                sys.exit(f"build_phrases: empty form or gloss in {g}")

    json.dump({"by_glottocode": out}, open(os.path.join(WEB, "phrases.json"), "w"),
              ensure_ascii=False, separators=(",", ":"))
    n = sum(len(r["items"]) for r in out.values())
    print(f"phrases: {len(out)} languages, {n} forms")

if __name__ == "__main__":
    main()
