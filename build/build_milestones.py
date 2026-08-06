#!/usr/bin/env python3
"""build_milestones.py — dated events in the life of a language. Register D13.

WHY DATES. A museum label is prose and prose can be vague; a date can be checked. "Korean was
written in Chinese characters for centuries before it got its own alphabet" is a sentence.
"1443: Sejong's court completes hangul. 1446: it is published as Hunminjeongeum. 1504: it is
banned. 1894: it becomes the official script of Korea" is a life. The second form is denser,
harder to fudge, and it is what makes the difference between a card you read and a card you
learn something from.

WHAT COUNTS AS A MILESTONE, and the rule is deliberately narrow: an event in the life of the
*written or spoken language itself* — a first attestation, a script adopted or replaced, a
grammar or dictionary that fixed the standard, a translation that put it into print, a reform, a
ban, a revival, a last speaker. Not political history. "1066" is here because it took English
out of government for three hundred years, not because a battle happened.

DISCIPLINE, same as the labels. Keyed by EXACT GLOTTOLOG NAME and resolved by machine; a name
that matches nothing or matches twice stops the build. Glottocodes written from memory are how
a paragraph about the Qur'an ended up displayed on Turkish. Each entry carries a confidence:
`good` for a date the record fixes, `approx` for one scholarship brackets — rendered as "c." so
the card never states a contested date as a settled one.

Run: python3 build_milestones.py
"""
from __future__ import annotations

import csv
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
GL = os.path.join(ROOT, "data", "glottolog", "languages.csv")

# (year, approximate?, event). Negative years are BCE.
M: dict[str, list] = {
    # ---- INDO-EUROPEAN DEEP PASS ----------------------------------------------------------
    # 90 Indo-European languages carried a museum label and no dated events. These are the 39
    # with the most active writing communities. The recurring shape of these timelines is worth
    # noticing on its own: a first attestation, then a long silence, then a printed Bible or a
    # dictionary that fixes a standard, then a ban, then a revival. Ukrainian, Lithuanian,
    # Breton, Belarusian and Silesian all have a ban in them.

 "Ukrainian": [
   (1056, False, "the Ostromir Gospels, in the Church Slavonic that Ukrainian and Russian both "
                 "grew out of"),
   (1556, True, "the Peresopnytsia Gospel, scripture put into a language close to the spoken "
                "one — Ukrainian presidents are sworn in on it"),
   (1798, False, "Kotliarevsky's Eneida, the first book written in the living vernacular rather "
                 "than a bookish register"),
   (1840, False, "Shevchenko's Kobzar builds a literary standard out of ordinary speech"),
   (1863, False, "the Valuev Circular declares that a separate Ukrainian language 'never "
                 "existed, does not exist and cannot exist', and bans most printing in it"),
   (1876, False, "the Ems Ukaz extends the ban to imports, to the stage and to sheet music"),
   (1928, False, "the Kharkiv orthography, agreed by a conference of both Soviet and western "
                 "Ukrainian scholars; it is abolished five years later"),
   (1991, False, "the state language of an independent Ukraine"),
 ],
 "Swedish": [
   (800, True, "the runic inscriptions begin; Sweden holds more runestones than anywhere else"),
   (1225, True, "the Västgötalagen, the oldest text in Swedish, a provincial law code"),
   (1541, False, "the Gustav Vasa Bible fixes a written standard and is the reason 1526 is "
                 "taken as the start of Modern Swedish"),
   (1786, False, "the Swedish Academy founded, to 'purity, strength and majesty' of the language"),
   (1906, False, "a spelling reform replaces hv- with v- and simplifies the verb"),
   (1974, True, "the du-reform: within a few years almost all formal address disappears and "
                "everyone is addressed as du"),
   (2009, False, "Swedish becomes the principal language of Sweden by statute — it had never "
                 "been declared one before"),
 ],
 "Romanian": [
   (1521, False, "Neacșu's letter, the oldest surviving text in Romanian, warning of an Ottoman "
                 "movement; written in Cyrillic"),
   (1582, False, "the Palia de la Orăștie, the first Romanian printing of scripture"),
   (1688, False, "the Bucharest Bible, the whole scripture in Romanian"),
   (1780, True, "the Transylvanian School argues Romanian's Latin descent and begins replacing "
                "Slavic vocabulary with Romance"),
   (1860, False, "the Latin alphabet replaces Cyrillic officially"),
   (1953, True, "Soviet Moldova keeps Cyrillic for the same language; it returns to Latin in 1989"),
   (1993, False, "a spelling reform restores â inside words, reversing a communist-era rule"),
 ],
 "Bulgarian": [
   (886, False, "Cyril and Methodius's pupils arrive in Bulgaria after being expelled from "
                "Moravia; the Preslav school develops Cyrillic out of Greek uncials"),
   (900, True, "Old Church Slavonic becomes the liturgical language of Slavic Christianity, and "
               "carries Cyrillic to Serbia and the Rus"),
   (1300, True, "Bulgarian loses almost all its noun cases and grows a definite article stuck to "
                "the end of the word — grammatically it moves toward its Balkan neighbours and "
                "away from its Slavic relatives"),
   (1762, False, "Paisius of Hilendar's history begins the national revival"),
   (1878, False, "an independent Bulgaria adopts the language of the eastern dialects"),
   (1945, False, "an orthographic reform drops the yat and the big yus"),
   (2007, False, "Cyrillic becomes the third official script of the European Union"),
 ],
 "Norwegian": [
   (1300, True, "Old Norwegian is written and then goes quiet: the Black Death and union with "
                "Denmark leave Danish as the written language for four centuries"),
   (1814, False, "independence from Denmark with no written Norwegian to return to"),
   (1848, False, "Ivar Aasen publishes a grammar built from dialects he collected on foot, "
                 "creating Landsmål — the ancestor of Nynorsk"),
   (1885, False, "parliament makes the two written forms equal"),
   (1907, True, "the Dano-Norwegian standard is reformed toward Norwegian speech, becoming "
                "Bokmål"),
   (1938, False, "a reform tries to merge the two into one Samnorsk; it is resisted and "
                 "eventually abandoned in 2002"),
 ],
 "Serbian-Croatian-Bosnian": [
   (1186, True, "the Miroslav Gospel, in Cyrillic, one of the great manuscripts of the Balkans"),
   (1483, False, "the Missale Romanum Glagolitice, the first book printed in Glagolitic"),
   (1818, False, "Vuk Karadžić's dictionary and his reformed Cyrillic: one letter per sound, "
                 "'write as you speak'"),
   (1850, False, "the Vienna Literary Agreement, in which Serb and Croat writers agree on one "
                 "literary language"),
   (1954, False, "the Novi Sad Agreement reaffirms it as a single language with two variants"),
   (1991, True, "the state breaks up and so does the name; the same language is now four"),
 ],
 "Danish": [
   (965, True, "the larger Jelling stone, called Denmark's birth certificate, in runes"),
   (1241, False, "the Code of Jutland, the oldest substantial Danish prose"),
   (1550, False, "the Christian III Bible, the first complete Danish scripture"),
   (1700, True, "Danish consonants weaken and are swallowed far beyond its neighbours' — the "
                "reason Danish is written like Norwegian and does not sound like it"),
   (1948, False, "a spelling reform ends the capitalisation of nouns and adds å for aa"),
 ],
 "Slovak": [
   (1787, False, "Bernolák codifies a standard on western Slovak; it does not hold"),
   (1843, False, "Ľudovít Štúr replaces it with a central Slovak standard, further from Czech "
                 "and closer to what most people speak"),
   (1918, False, "an official language of Czechoslovakia, in practice subordinate to Czech"),
   (1993, False, "the state language of an independent Slovakia"),
   (1995, False, "a state language law regulates its use in public life"),
 ],
 "Lithuanian": [
   (1503, True, "the earliest surviving Lithuanian writing, a handwritten prayer in a book"),
   (1547, False, "Mažvydas's Catechism, the first printed Lithuanian book"),
   (1864, False, "printing Lithuanian in Latin letters is banned in the Russian Empire; books "
                 "are printed in Prussia and smuggled by the knygnešiai, the book carriers"),
   (1904, False, "the ban is lifted after forty years"),
   (1918, False, "the state language of an independent Lithuania"),
   (1918, True, "comparative linguists adopt Lithuanian as a control for Indo-European, because "
                "it kept case endings, dual number and pitch accent that Sanskrit's other "
                "cousins lost"),
 ],
 "Latvian": [
   (1585, False, "the first Latvian book, a Catholic catechism"),
   (1685, False, "Glück's Bible translation, which fixes a written standard"),
   (1873, False, "the first Latvian Song Festival, which keeps the language in public voice "
                 "under German and then Russian administration"),
   (1908, True, "the modern orthography replaces the old German-based spelling"),
   (1918, False, "the state language of an independent Latvia"),
   (1988, False, "restored as the state language before independence itself"),
 ],
 "Slovenian": [
   (1000, True, "the Freising manuscripts, the oldest text in any Slavic language in Latin "
                "letters"),
   (1550, False, "Primož Trubar publishes the first printed Slovene book and coins the word "
                 "Slovenci for its readers"),
   (1584, False, "Dalmatin's Bible and Bohorič's grammar in the same year"),
   (1843, True, "the gajica alphabet, borrowed from Croatian, replaces the older bohoričica"),
   (1991, False, "the state language of an independent Slovenia"),
 ],
 "Macedonian": [
   (1903, True, "Krste Misirkov argues in print for a separate Macedonian literary language"),
   (1944, False, "codified as the official language of the Macedonian republic within Yugoslavia "
                 "— the last Slavic language to be standardised"),
   (1945, False, "its alphabet fixed, one letter per sound, with ѓ and ќ that no other Cyrillic "
                 "has"),
   (2018, False, "the Prespa Agreement records that the language is called Macedonian"),
 ],
 "Afrikaans": [
   (1830, True, "written first in Arabic script, in the madrasas of the Cape Malay community, "
                "decades before it was written in Latin letters"),
   (1875, False, "the Genootskap van Regte Afrikaners founded to promote it as a written "
                 "language in its own right"),
   (1925, False, "replaces Dutch as an official language of South Africa"),
   (1933, False, "the Bible in Afrikaans"),
   (1976, False, "the Soweto uprising begins against Afrikaans being made the medium of "
                 "instruction; the language's association with the state costs it dearly"),
   (1996, False, "one of eleven official languages of a democratic South Africa"),
 ],
 "Galician": [
   (1200, True, "Galician-Portuguese is the language of lyric poetry across Iberia; Castilian "
                "kings write their songs in it"),
   (1350, True, "the Séculos Escuros begin — four centuries in which Galician is spoken "
                "everywhere and written almost nowhere"),
   (1863, False, "Rosalía de Castro's Cantares gallegos reopens the written language"),
   (1906, False, "the Real Academia Galega founded"),
   (1981, False, "co-official in Galicia under its Statute of Autonomy"),
 ],
 "Northern Tosk Albanian": [
   (1462, True, "the Formula e pagëzimit, a baptismal formula, the oldest recorded Albanian"),
   (1555, False, "Buzuku's Meshari, the first Albanian book"),
   (1908, False, "the Congress of Manastir settles on a Latin alphabet, ending decades of "
                 "competing scripts"),
   (1972, False, "the Congress of Orthography fixes a unified standard built on Tosk"),
 ],
 "Occitan": [
   (1100, True, "the first troubadour lyrics; the form and its vocabulary spread to Italy, "
                "Catalonia and Germany"),
   (1323, False, "the Consistori del Gay Saber founded at Toulouse to regulate the poetry — "
                 "among the first language academies anywhere"),
   (1539, False, "the Ordinance of Villers-Cotterêts requires French in all legal acts, removing "
                 "Occitan from administration"),
   (1854, False, "Frédéric Mistral and the Félibrige begin a literary revival"),
   (1904, False, "Mistral takes the Nobel Prize for literature, written in Occitan"),
   (2010, False, "Aranese, the Occitan of the Val d'Aran, becomes co-official in Catalonia"),
 ],
 "Breton": [
   (800, True, "Old Breton glosses in Latin manuscripts, the earliest record"),
   (1499, False, "the Catholicon, a Breton-French-Latin dictionary and the first Breton "
                 "dictionary printed"),
   (1839, False, "La Villemarqué's Barzaz Breiz collects the ballads, and starts a long argument "
                 "about how much he rewrote"),
   (1902, True, "the Symbole: children caught speaking Breton at school are made to wear a "
                "token and pass it on to the next offender"),
   (1941, False, "a unified orthography agreed under occupation, which taints it for decades"),
   (1977, False, "the first Diwan immersion school opens"),
 ],
 "Gujarati": [
   (1592, True, "the earliest Gujarati prose"),
   (1797, False, "the first Gujarati printing type cut in Bombay"),
   (1909, False, "Gandhi writes Hind Swaraj in Gujarati; his autobiography follows in the same "
                 "language"),
   (1936, False, "the Gujarat Vidyapith standardises the spelling"),
 ],
 "Western Frisian": [
   (1200, True, "Old Frisian law texts, the closest recorded relative of Old English"),
   (1550, True, "Gysbert Japix begins writing literary Frisian, almost single-handedly reviving "
                "it as a written language"),
   (1937, False, "permitted as a subject in Dutch schools"),
   (1951, False, "Kneppelfreed — a riot over the refusal of Frisian in court — leads to its "
                 "admission there"),
   (1956, False, "recognised for use in the courts of Friesland"),
 ],
 "Central Kurdish": [
   (1600, True, "Ahmad Khani's Mem û Zîn, the Kurdish national epic, written in Kurmanji"),
   (1898, False, "Kurdistan, the first Kurdish newspaper, printed in Cairo"),
   (1932, False, "Celadet Bedirxan devises the Latin alphabet now used for Kurmanji"),
   (1938, True, "Sorani's Arabic-based alphabet is reformed to mark every vowel"),
   (2005, False, "Kurdish becomes an official language of Iraq alongside Arabic"),
 ],
 "Northern Kurdish": [
   (1596, False, "the Sharafnama, a history of the Kurds, though written in Persian"),
   (1695, True, "Mem û Zîn, in Kurmanji"),
   (1932, False, "Celadet Bedirxan's Latin alphabet, published in the journal Hawar"),
   (1983, False, "publishing and broadcasting in Kurdish banned in Turkey; the ban is lifted in "
                 "1991 and broadcasting permitted from 2002"),
 ],
 "Marathi": [
   (700, True, "the earliest Marathi inscription"),
   (1290, False, "the Dnyaneshwari, a commentary on the Gita, and the beginning of Marathi "
                 "devotional literature"),
   (1600, True, "Modi script comes into administrative use and stays for three centuries"),
   (1805, False, "the first Marathi book printed"),
   (1950, True, "Devanagari replaces Modi entirely; Modi is now read only by archivists"),
   (2024, False, "declared a classical language of India"),
 ],
 "Urdu": [
   (1300, True, "Amir Khusrau writes verse mixing Persian and the speech of Delhi"),
   (1611, True, "the Deccan sultanates produce the first substantial literature in the language"),
   (1780, True, "Mir and Sauda establish the ghazal in Urdu at Delhi and Lucknow"),
   (1837, False, "replaces Persian as the language of the lower courts in British India"),
   (1867, True, "the Hindi-Urdu controversy begins: the same speech, two scripts, two claimed "
                "identities"),
   (1947, False, "the national language of Pakistan, though the first language of a small "
                 "minority there"),
 ],
 "Assamese": [
   (1200, True, "the Kamarupa inscriptions in an early eastern Indo-Aryan"),
   (1450, True, "Sankardeva's Vaishnava writings and his one-act ankiya nat plays, still "
                "performed"),
   (1836, False, "Bengali is imposed as the language of Assam's courts and schools"),
   (1873, False, "Assamese restored, after a campaign led partly by American Baptist "
                 "missionaries who had printed in it"),
   (2024, False, "declared a classical language of India"),
 ],
 "Sinhala": [
   (-300, True, "Brahmi inscriptions in caves, the earliest Sinhala"),
   (900, True, "the graffiti on the Sigiriya mirror wall — verses scratched by visitors, the "
               "oldest Sinhala poetry and among the earliest casual writing anywhere"),
   (1200, True, "classical Sinhala literature at Polonnaruwa"),
   (1956, False, "the Sinhala Only Act makes it the sole official language, displacing English "
                 "and excluding Tamil; the consequences are severe and lasting"),
   (1987, False, "Tamil is made an official language alongside it"),
 ],
 "Nepali": [
   (1337, True, "the earliest dated Nepali inscription"),
   (1768, True, "the Gorkha conquest spreads it across the hills as an administrative language"),
   (1830, True, "Bhanubhakta Acharya translates the Ramayana into Nepali, giving it a literary "
                "standard"),
   (1958, False, "the official language of Nepal"),
   (1992, False, "a scheduled language of India, for Darjeeling and Sikkim"),
 ],
 "Odia": [
   (1051, True, "the earliest Odia inscription"),
   (1500, True, "Sarala Das's Mahabharata, the first great work in Odia"),
   (1870, True, "a campaign argues Odia is not a dialect of Bengali; a colonial commission "
                "agrees"),
   (1936, False, "Orissa becomes the first Indian province formed on linguistic lines"),
   (2014, False, "declared a classical language of India, the sixth"),
 ],
 "Eastern Panjabi": [
   (1539, True, "Guru Nanak's compositions, later collected in the Guru Granth Sahib"),
   (1550, True, "Guru Angad standardises Gurmukhi"),
   (1604, False, "the Adi Granth compiled at Amritsar"),
   (1966, False, "Punjab reorganised on linguistic lines after a long agitation"),
 ],
 "Tajik": [
   (1928, False, "the Perso-Arabic script replaced by Latin"),
   (1940, False, "Latin replaced by Cyrillic; two script changes in twelve years"),
   (1989, False, "made the state language of the Tajik SSR, with a stated intention to return "
                 "to Perso-Arabic that has not happened"),
   (1994, False, "the state language of independent Tajikistan"),
 ],
 "Belarusian": [
   (1517, False, "Francysk Skaryna prints the Bible in Prague, among the first printed books in "
                 "an East Slavic language"),
   (1588, False, "the Statutes of Lithuania, written in the Ruthenian chancery language"),
   (1918, False, "Branislaw Taraškievič codifies a grammar; the standard is named after him"),
   (1933, False, "a Soviet reform moves the orthography toward Russian; both standards remain "
                 "in use and the choice is political"),
   (1995, False, "a referendum makes Russian co-official, and Belarusian recedes from public "
                 "life"),
 ],
 "Bavarian": [
   (750, True, "Old Bavarian glosses and the Wessobrunn Prayer"),
   (1500, True, "Bavarian chancery writing gives way to the emerging High German standard"),
   (1970, True, "dialect literature and broadcasting revive, while transmission to children "
                "falls"),
   (2009, False, "UNESCO lists Bavarian as vulnerable"),
 ],
 "Scots": [
   (1375, False, "Barbour's Brus, the first major poem in Scots"),
   (1494, True, "Scots is the language of the Scottish parliament and courts"),
   (1603, False, "the union of crowns takes the court to London; printing follows and the "
                 "written standard is absorbed into English"),
   (1786, False, "Burns's Kilmarnock edition, written in Scots by choice"),
   (2001, False, "recognised under the European Charter for Regional or Minority Languages"),
 ],
 "Haitian": [
   (1700, True, "the language forms on the plantations of Saint-Domingue out of French and the "
                "Gbe languages of West Africa"),
   (1804, False, "independence, with French kept as the language of state and Creole spoken by "
                 "everyone"),
   (1940, True, "the first systematic orthography proposed by Ormonde McConnell"),
   (1979, False, "the official orthography adopted, phonemic rather than French-based"),
   (1987, False, "made co-official with French by the new constitution"),
 ],
 "Moselle Franconian": [
   (1829, False, "the first dictionary of the Luxembourg dialect"),
   (1946, True, "a first official orthography, revised in 1975 and 1999"),
   (1984, False, "Luxembourgish made a national language of Luxembourg alongside French and "
                 "German"),
   (2019, False, "a law establishes a commissioner and a twenty-year plan for the language"),
 ],
 "Central Alemannic": [
   (1900, True, "Standard German is the written language; Swiss German is not written and is "
                "spoken at every level of society"),
   (1938, True, "Swiss German broadcasting expands as a deliberate assertion of difference from "
                "Germany"),
   (2000, True, "text messaging and then social media put Swiss German into writing for the "
                "first time at scale, with no agreed spelling"),
 ],
 "Venetian": [
   (1250, True, "Venetian is written in commercial and diplomatic documents across the eastern "
                "Mediterranean"),
   (1516, True, "as the language of a trading empire it lends words to Greek, Turkish and "
                "Arabic — and gives English arsenal, ghetto, lagoon and regatta"),
   (1760, True, "Goldoni writes his comedies in Venetian"),
   (2007, False, "recognised by the Veneto region; not recognised by the Italian state"),
 ],
 "Silesian": [
   (1500, True, "Silesian written in German-language administrative contexts, with Polish and "
                "Czech features"),
   (2003, False, "given an ISO code, which is often the first formal recognition a contested "
                 "language gets"),
   (2011, False, "509,000 people declare it as a home language in the Polish census"),
   (2024, False, "the Polish parliament votes to recognise it as a regional language; the "
                 "president vetoes"),
 ],
 "Fiji Hindi": [
   (1879, False, "indentured labour begins from India to Fiji; Awadhi, Bhojpuri and other "
                 "varieties are carried together"),
   (1920, True, "the varieties level into one new language within two generations"),
   (1977, False, "a standard orthography proposed in Latin letters"),
   (2013, False, "recognised in Fiji's constitution alongside English and Fijian"),
 ],
 "Aragonese": [
   (1100, True, "the Glosas Emilianenses, whose Romance may be Aragonese rather than Castilian — "
                "the question is argued"),
   (1300, True, "Aragonese is the chancery language of the Crown of Aragon"),
   (1500, True, "Castilian displaces it from writing"),
   (1987, False, "a first modern orthography agreed at Huesca"),
   (2009, False, "given legal status in Aragon; the law is largely repealed in 2013"),
 ],

    "English": [
        (449, True, "Germanic-speaking Angles, Saxons and Jutes cross into Britain; the "
                    "language they bring has no name yet"),
        (731, False, "Bede finishes his history and reports that Britain holds five "
                     "languages — English, British, Irish, Pictish and Latin"),
        (1000, True, "the only surviving manuscript of Beowulf is copied"),
        (1066, False, "the Norman conquest; for the next three hundred years the language of "
                      "English government is French, and English is written far less"),
        (1362, False, "the Statute of Pleading orders court cases argued in English, because "
                      "French is no longer widely understood"),
        (1476, False, "Caxton sets up a printing press at Westminster and has to choose which "
                      "regional spelling to use; his choices are still in the language"),
        (1611, False, "the King James Bible"),
        (1755, False, "Johnson's Dictionary, 42,773 entries, written by one man in nine years"),
        (1928, False, "the Oxford English Dictionary is completed, seventy years after it was "
                      "begun and forty years late"),
    ],
    "Mandarin Chinese": [
        (-1200, True, "oracle-bone inscriptions at Anyang — the earliest Chinese writing, "
                      "already fully formed, with no simpler ancestor found"),
        (-221, False, "Qin Shi Huang standardises the script across the empire; the writing "
                      "unifies while the speech does not"),
        (105, True, "paper credited to Cai Lun"),
        (1040, True, "Bi Sheng makes movable type from fired clay, four centuries before "
                     "Gutenberg"),
        (1913, False, "a national commission fixes a standard pronunciation, based on Beijing"),
        (1935, False, "a first list of simplified characters is issued, then withdrawn"),
        (1956, False, "simplified characters promulgated in the mainland; Taiwan and Hong Kong "
                      "keep the traditional forms, so one language now has two scripts"),
        (1958, False, "Hanyu Pinyin adopted — a Latin spelling for teaching and typing, not "
                      "for replacing the characters"),
    ],
    "Standard Arabic": [
        (328, False, "the Namara inscription: Arabic, written in Nabataean letters"),
        (512, True, "the Zabad inscription, among the earliest in recognisably Arabic script"),
        (632, False, "the Qur'an is complete; it becomes the reference text for the grammar, "
                     "the vocabulary and the spelling of the language"),
        (650, True, "the Uthmanic codex fixes one written version"),
        (760, True, "al-Khalil ibn Ahmad devises the vowel and consonant pointing that makes "
                    "an unpointed abjad unambiguous, and writes the first Arabic dictionary"),
        (796, True, "Sibawayh's Kitab — a complete grammar of Arabic, still studied"),
        (1822, False, "the Bulaq press begins printing in Arabic in Egypt"),
        (1932, False, "the Academy of the Arabic Language founded in Cairo to coin modern "
                      "vocabulary"),
    ],
    "Korean": [
        (414, False, "the Gwanggaeto stele: Korean history written in Chinese characters, "
                     "because Korean has no script of its own"),
        (1443, False, "Sejong's court completes hangul, designed so that a letter's shape "
                      "shows how the mouth makes the sound"),
        (1446, False, "Hunminjeongeum published — 'the correct sounds for the instruction of "
                      "the people'; the preface says it exists so that the unlettered can "
                      "write"),
        (1504, False, "hangul banned by King Yeonsangun after it is used to criticise him"),
        (1894, False, "hangul becomes the official script of Korea, four and a half centuries "
                      "after it was invented"),
        (1938, False, "Korean-language teaching banned in schools under Japanese rule"),
        (1946, False, "Hangul Day made a national holiday"),
    ],
    "Japanese": [
        (57, True, "a gold seal given to a ruler in the Japanese islands, inscribed in "
                   "Chinese — the earliest writing connected with Japan"),
        (712, False, "the Kojiki: Japanese written with Chinese characters used for their "
                     "sound, a system so ambiguous it took a thousand years to decipher"),
        (759, True, "the Man'yōshū anthology, 4,500 poems"),
        (900, True, "hiragana and katakana develop out of cursive and abbreviated Chinese "
                    "characters; women of the court write in hiragana"),
        (1008, True, "Murasaki Shikibu writes The Tale of Genji in hiragana"),
        (1900, False, "the school system fixes one hiragana sign per syllable, ending "
                      "centuries of variant forms"),
        (1946, False, "post-war reform cuts the kanji taught in schools to 1,850 and "
                      "regularises spelling to match modern pronunciation"),
    ],
    "Hindi": [
        (-1500, True, "the Rigveda is composed in Vedic Sanskrit, an ancestor of this "
                      "language, and is transmitted by memory for a thousand years"),
        (1000, True, "the earliest verse in a language recognisably ancestral to Hindi"),
        (1600, True, "Braj and Awadhi carry most literature; the dialect that becomes "
                     "standard Hindi is not yet the literary one"),
        (1826, False, "Udant Martand, the first Hindi newspaper, printed in Calcutta"),
        (1873, False, "Bhartendu Harishchandra begins the prose that sets modern Hindi's "
                      "shape"),
        (1950, False, "Hindi in Devanagari made an official language of India, with English "
                      "kept alongside it 'for fifteen years' — a period repeatedly extended"),
    ],
    "Bengali": [
        (1000, True, "the Charyapada, Buddhist songs in an early form of the language, found "
                     "in a Nepalese palace library in 1907"),
        (1778, False, "Halhed's grammar, the first book printed with Bengali movable type"),
        (1801, False, "Fort William College makes Bengali a subject of formal study"),
        (1861, False, "Rabindranath Tagore born; he will write in Bengali and translate "
                      "himself into English"),
        (1913, False, "Tagore takes the Nobel Prize — the first for any Asian writer"),
        (1952, False, "police fire on students in Dhaka demonstrating for Bengali as a state "
                      "language of Pakistan; the deaths are commemorated by UNESCO as "
                      "International Mother Language Day"),
        (1971, False, "Bangladesh independent, with Bengali as its state language"),
    ],
    "Modern Greek": [
        (-1400, True, "Linear B tablets record Mycenaean Greek — the earliest Greek, five "
                      "centuries before the alphabet"),
        (-800, True, "Greek adapts the Phoenician abjad and turns unused consonants into "
                     "vowel letters, producing the first true alphabet"),
        (-250, True, "the Septuagint: Hebrew scripture translated into Greek at Alexandria"),
        (1453, False, "Constantinople falls; Greek learning disperses westward"),
        (1821, False, "the war of independence begins, and with it two centuries of argument "
                      "over which Greek the state should use"),
        (1976, False, "demotic Greek — the spoken language — replaces the archaising katharevousa "
                      "in schools and government"),
        (1982, False, "the polytonic accent system reduced to a single stress mark"),
    ],
    "Modern Hebrew": [
        (-1000, True, "the Gezer calendar, among the earliest Hebrew inscriptions"),
        (-700, True, "the Siloam tunnel inscription in Jerusalem"),
        (200, True, "Hebrew stops being an everyday spoken language; it continues in prayer, "
                    "law and letters for seventeen centuries"),
        (900, True, "the Masoretes add vowel points to fix the reading of a consonantal text"),
        (1881, False, "Eliezer Ben-Yehuda moves to Jerusalem and raises his son speaking only "
                      "Hebrew — the first native speaker in around 1,700 years"),
        (1922, False, "Hebrew made an official language of Mandatory Palestine"),
        (1948, False, "an official language of Israel; the only case of a language with no "
                      "native speakers becoming a national vernacular again"),
    ],
    "Irish": [
        (350, True, "Ogham inscriptions cut along the edges of standing stones — the earliest "
                    "Irish"),
        (600, True, "Old Irish glosses written between the lines of Latin manuscripts by "
                    "monks; they are the largest early record of any vernacular in Europe "
                    "north of the Alps"),
        (1571, False, "the first book printed in Irish"),
        (1831, False, "the national school system teaches only English; children are punished "
                      "for speaking Irish"),
        (1845, False, "the Famine begins, and falls hardest on the Irish-speaking west"),
        (1893, False, "the Gaelic League founded to revive the language"),
        (1937, False, "Irish named the first official language of the state"),
        (2007, False, "an official language of the European Union"),
    ],
    "Welsh": [
        (600, True, "Y Gododdin, a poem in early Welsh remembering a battle in what is now "
                    "Scotland"),
        (1588, False, "William Morgan's Bible in Welsh — the single most important reason the "
                      "language survived, because it gave it a printed standard"),
        (1847, False, "a government report blames Welsh for Welsh poverty; the 'Welsh Not' "
                      "punishes children for speaking it in school"),
        (1962, False, "Saunders Lewis's radio lecture 'Tynged yr Iaith' — the fate of the "
                      "language — starts the campaign that follows"),
        (1982, False, "S4C begins broadcasting television in Welsh"),
        (1993, False, "the Welsh Language Act gives it equal standing in public life in Wales"),
        (2011, False, "Welsh made an official language of Wales"),
    ],
    "Icelandic": [
        (874, True, "settlement of Iceland from Norway; the language carried there changes "
                    "less over the next thousand years than any of its relatives"),
        (1130, True, "the sagas begin to be written down in the vernacular, not Latin"),
        (1540, False, "the New Testament printed in Icelandic"),
        (1584, False, "the whole Bible; it fixes a written standard that modern readers can "
                      "still follow"),
        (1780, True, "a deliberate policy of coining new words from Icelandic roots rather "
                     "than borrowing begins — sími for telephone, tölva for computer"),
        (1944, False, "independence, with a language close enough to Old Norse that "
                      "schoolchildren read the sagas unaltered"),
    ],
    "Turkish": [
        (732, False, "the Orkhon inscriptions in Mongolia — the earliest Turkic writing, in "
                     "its own runic script"),
        (1071, True, "Turkish speakers enter Anatolia"),
        (1277, True, "Turkish begins to be used for court poetry alongside Persian"),
        (1729, False, "the first Turkish printing press in the Ottoman Empire"),
        (1928, False, "the alphabet reform: Arabic script replaced by Latin in a matter of "
                      "months, with Atatürk teaching the new letters at a blackboard in "
                      "public"),
        (1932, False, "the Turkish Language Association founded to replace Arabic and Persian "
                      "vocabulary with Turkic words; the change is large enough that 1920s "
                      "prose is hard for young readers"),
    ],
    "Russian": [
        (863, False, "Cyril and Methodius devise a script for Slavonic; the Cyrillic that "
                     "bears Cyril's name is the work of his successors"),
        (1056, True, "the Ostromir Gospels, the oldest dated East Slavic manuscript"),
        (1564, False, "the first printed book in Moscow"),
        (1708, False, "Peter the Great's civil script — the letters simplified and several "
                      "dropped, to look less ecclesiastical and more European"),
        (1755, False, "Lomonosov's grammar"),
        (1863, False, "Dahl's dictionary of the living language, 200,000 words collected by "
                      "one man"),
        (1918, False, "the orthographic reform drops four letters, including the hard sign at "
                      "the end of words"),
    ],
    "Spanish": [
        (950, True, "the Glosas Emilianenses — Romance words written between the lines of a "
                    "Latin manuscript to explain it, because Latin is no longer understood"),
        (1200, True, "Castilian used for royal documents in place of Latin"),
        (1492, False, "Nebrija publishes the first grammar of any modern European language, "
                      "and tells the queen that language is the instrument of empire"),
        (1605, False, "Don Quixote, part one"),
        (1713, False, "the Real Academia Española founded, with the motto 'it cleans, it "
                      "fixes, it gives splendour'"),
        (1951, False, "the academies of Spain and the Americas begin meeting jointly, so the "
                      "standard stops being set in Madrid alone"),
    ],
    "French": [
        (842, False, "the Strasbourg Oaths, sworn in a Romance vernacular and written down "
                     "because neither side would accept Latin"),
        (1100, True, "the Chanson de Roland"),
        (1539, False, "the Ordinance of Villers-Cotterêts requires French, not Latin, in all "
                      "legal acts — and by extension not Occitan, Breton or Basque either"),
        (1635, False, "the Académie française founded to regulate the language"),
        (1694, False, "its first dictionary, 59 years later"),
        (1794, False, "a revolutionary report finds that most citizens of France do not speak "
                      "French, and proposes to change that"),
        (1990, False, "a spelling reform proposed; three decades later both spellings are "
                      "still in use"),
    ],
    "German": [
        (750, True, "the Abrogans, a Latin-German glossary — the oldest German book"),
        (1522, False, "Luther's New Testament, written in a German he said he took from the "
                      "market and the home rather than from chancery clerks"),
        (1534, False, "the complete Bible; it pulls a dozen written dialects towards one "
                      "standard"),
        (1854, False, "the Grimm brothers begin their dictionary; it is finished in 1961, "
                      "107 years later"),
        (1901, False, "the Second Orthographic Conference fixes one spelling for the German "
                      "states"),
        (1996, False, "a spelling reform that takes a decade of argument to settle"),
    ],
    "Italian": [
        (960, False, "the Placiti Cassinesi, court testimony recorded in the vernacular"),
        (1320, True, "Dante finishes the Commedia in Florentine, having argued in Latin that "
                     "the vernacular deserved serious writing"),
        (1612, False, "the Accademia della Crusca's dictionary, the first of a modern "
                      "European language"),
        (1840, True, "Manzoni rewrites his novel in Florentine to give Italy one written "
                     "standard"),
        (1861, False, "unification; perhaps one in forty people in the new kingdom speaks "
                      "Italian rather than a regional language"),
        (1954, False, "television begins, and does more to spread spoken Italian than a "
                      "century of schooling"),
    ],
    "Portuguese": [
        (1175, True, "the earliest documents in Portuguese"),
        (1290, False, "Portuguese made the language of administration in place of Latin"),
        (1536, False, "the first grammar"),
        (1572, False, "Camões publishes Os Lusíadas"),
        (1990, False, "an orthographic agreement between Portugal, Brazil and five African "
                      "states, to bring two spellings together"),
    ],
    "Dutch": [
        (1100, True, "a line written in the margin of a Latin manuscript at Rochester — "
                     "'hebban olla vogala' — long treated as the oldest Dutch sentence"),
        (1637, False, "the Statenbijbel, a Bible translation that fixes a written standard"),
        (1804, False, "the first official spelling"),
        (1980, False, "the Dutch Language Union founded jointly by the Netherlands and "
                      "Belgium, so neither sets the standard alone"),
    ],
    "Swahili": [
        (1100, True, "Swahili-speaking trading towns along the East African coast"),
        (1711, False, "the oldest surviving Swahili letter, written in Arabic script"),
        (1728, False, "the Utendi wa Tambuka, an epic poem in Arabic script"),
        (1930, False, "a standard fixed on the Zanzibar dialect, in Latin letters"),
        (1961, False, "Tanzania adopts Swahili as a national language, and uses it to teach "
                      "primary school in an African language rather than English"),
        (2022, False, "UNESCO names 7 July World Kiswahili Language Day, the first for an "
                      "African language"),
    ],
    "Hausa": [
        (1500, True, "Hausa written in ajami, the Arabic script adapted for it"),
        (1804, True, "the Sokoto jihad; Hausa verse in ajami spreads widely"),
        (1912, True, "boko, a Latin orthography, introduced under colonial rule; the word "
                     "later comes to mean Western education"),
        (1930, False, "the standard Latin spelling settled"),
        (1957, False, "the BBC begins broadcasting in Hausa"),
    ],
    "Yoruba": [
        (1000, True, "Ife bronze casting; the language of the people who made it is an "
                     "ancestor of Yoruba"),
        (1843, False, "Samuel Ajayi Crowther, taken as a boy on a slave ship and returned, "
                      "publishes a Yoruba grammar and vocabulary — the first by a native "
                      "speaker of any West African language"),
        (1900, True, "tone marks standardised in the orthography, without which the writing "
                     "is ambiguous"),
        (1938, False, "Fagunwa's Ogboju Ode, the first novel in Yoruba"),
    ],
    "Amharic": [
        (330, True, "the Ezana inscriptions at Axum, in Ge'ez — Amharic's older relative and "
                    "the source of its script"),
        (1300, True, "the Royal Songs, the earliest Amharic verse"),
        (1513, True, "Ge'ez type cut in Europe; Ethiopic becomes one of the first non-European "
                     "scripts printed"),
        (1863, False, "the Bible printed in Amharic"),
        (1955, False, "Amharic named the official language of Ethiopia"),
        (2020, False, "four more languages given federal working status alongside it"),
    ],
    "Vietnamese": [
        (1000, True, "Vietnamese written in chữ Nôm, characters built out of Chinese ones to "
                     "fit a language Chinese characters do not suit"),
        (1651, False, "Alexandre de Rhodes prints a Vietnamese–Portuguese–Latin dictionary in "
                      "the Latin-based quốc ngữ, devised by Portuguese missionaries"),
        (1910, True, "the colonial administration promotes quốc ngữ over the characters"),
        (1945, False, "quốc ngữ made the official script; a literacy campaign follows, and "
                      "chữ Nôm passes out of general use within a generation"),
    ],
    "Thai": [
        (1283, True, "the Ram Khamhaeng inscription, traditionally the first Thai writing"),
        (1836, False, "the first Thai printing press, brought by missionaries"),
        (1942, False, "a wartime spelling reform simplifies the alphabet; it is reversed in "
                      "1944"),
    ],
    "Central Khmer": [
        (611, False, "the oldest dated Khmer inscription — the longest continuous written "
                     "record of any language in Southeast Asia"),
        (1200, True, "the Bayon and Angkor inscriptions"),
        (1915, True, "Khmer printing begins in earnest"),
        (1975, False, "under the Khmer Rouge, teachers, writers and printers are killed; the "
                      "written language loses most of the people who worked in it"),
    ],
    "Tamil": [
        (-300, True, "Tamil-Brahmi inscriptions in caves — the earliest Tamil"),
        (-100, True, "the Sangam poems, the oldest surviving literature in any living Indian "
                     "language"),
        (500, True, "the Tolkappiyam, a grammar of Tamil written in Tamil"),
        (1578, False, "the first book printed in an Indian language and script is Tamil"),
        (1956, False, "Tamil Nadu formed on linguistic lines after protests"),
        (2004, False, "declared a classical language of India"),
    ],
    "Basque": [
        (-100, True, "the Hand of Irulegi, a bronze plate bearing words that look ancestral "
                     "to Basque, found in 2021"),
        (1545, False, "Bernat Etxepare's poems — the first book printed in Basque"),
        (1571, False, "the New Testament in Basque"),
        (1937, False, "Basque banned in public under Franco; a generation is schooled only in "
                      "Spanish"),
        (1968, False, "euskara batua, a unified written standard, agreed — the language had "
                      "never had one"),
        (1979, False, "co-official in the Basque Autonomous Community; schooling in Basque "
                      "grows from almost nothing"),
    ],
    "Navajo": [
        (1868, False, "the Navajo return to their homeland after imprisonment at Bosque "
                      "Redondo"),
        (1910, True, "the Franciscans publish a Navajo dictionary and grammar"),
        (1939, False, "a practical Latin orthography settled"),
        (1942, False, "Navajo code talkers in the Pacific; the language is used as a cipher "
                      "because so few outsiders know it"),
        (1968, False, "Rough Rock, the first school run by a Native community, teaches in "
                      "Navajo"),
        (2005, True, "still the most widely spoken Indigenous language north of Mexico, and "
                     "still losing child speakers"),
    ],
    "Cherokee": [
        (1821, True, "Sequoyah completes a syllabary of 85 signs, having started unable to "
                     "read any script; Cherokee literacy overtakes that of white settlers "
                     "nearby within years"),
        (1828, False, "the Cherokee Phoenix begins printing in both Cherokee and English"),
        (1838, False, "the forced removal west; the press is destroyed"),
        (2010, True, "Cherokee added to Unicode-capable phones and computers by the Nation's "
                     "own translators"),
    ],
    "Maori": [
        (1300, True, "Polynesian voyagers reach New Zealand; the language they bring is "
                     "closest to those of the Cook Islands"),
        (1815, False, "the first book printed in Maori"),
        (1840, False, "the Treaty of Waitangi signed in two versions, Maori and English, "
                      "which do not say the same thing"),
        (1867, False, "the Native Schools Act; English-only teaching follows and children "
                      "are beaten for speaking Maori"),
        (1982, False, "the first kōhanga reo — a language nest where preschoolers hear only "
                      "Maori, staffed by elders"),
        (1987, False, "made an official language of New Zealand"),
    ],
    "Hawaiian": [
        (1822, False, "the first printing in Hawaiian; literacy spreads faster than almost "
                      "anywhere in the world at the time"),
        (1896, False, "English made the only language of instruction after the overthrow of "
                      "the kingdom; Hawaiian is pushed out of schools for most of a century"),
        (1983, True, "fewer than fifty children are estimated to speak it"),
        (1984, False, "Pūnana Leo immersion preschools open"),
        (1987, False, "Hawaiian-medium public schooling restarted"),
        (2016, True, "thousands of children now in Hawaiian-medium education"),
    ],
    "Nhengatu": [
        (1600, True, "Tupi coastal speech, learned by colonists and missionaries, becomes a "
                     "general language of the Brazilian interior"),
        (1750, True, "spoken far more widely in Amazonia than Portuguese"),
        (1758, False, "the Directorate bans the general language in favour of Portuguese"),
        (2002, False, "made co-official in São Gabriel da Cachoeira, alongside Portuguese"),
    ],
    "Classical Nahuatl": [
        (1325, True, "Tenochtitlan founded; Nahuatl is the language of its administration and "
                     "of a pictorial writing system"),
        (1547, True, "Nahuatl written in Latin letters by its own speakers; the Florentine "
                     "Codex is compiled with Nahua scholars"),
        (1770, False, "the crown orders Spanish only; Nahuatl loses its official standing"),
        (2003, False, "recognised as a national language of Mexico alongside 67 others"),
    ],
    "Paraguayan Guaraní": [
        (1639, False, "Montoya's grammar and dictionary of Guaraní"),
        (1870, True, "after the Paraguayan War the language survives as the everyday speech "
                     "of a mostly bilingual country"),
        (1992, False, "co-official with Spanish in Paraguay — the only Indigenous language of "
                      "the Americas with that standing in a national constitution"),
        (2006, False, "an official working language of Mercosur"),
    ],
    "Cusco Quechua": [
        (1400, True, "Quechua spread as the administrative language of the Inca state, which "
                     "kept records on knotted cords rather than in writing"),
        (1560, False, "Domingo de Santo Tomás publishes a grammar and dictionary"),
        (1780, False, "after the Túpac Amaru rebellion, Quechua is suppressed"),
        (1975, False, "made an official language of Peru"),
        (2021, True, "a Peruvian congress session opened in Quechua for the first time"),
    ],
    "Tibetan": [
        (650, True, "a script devised for Tibetan on an Indian model, to translate Buddhist "
                    "texts"),
        (783, False, "the Sino-Tibetan treaty pillar in Lhasa, inscribed in both languages"),
        (824, True, "a royal decree standardises the translation vocabulary — an early "
                    "language-planning document"),
        (1410, False, "the Kangyur printed from wooden blocks"),
    ],
    "Western Farsi": [
        (-520, True, "Old Persian cuneiform at Behistun, in three languages, which is what "
                     "let cuneiform be deciphered at all"),
        (900, True, "New Persian written in Arabic script; the language returns to literary "
                    "use two centuries after the conquest"),
        (1010, False, "Ferdowsi completes the Shahnameh, deliberately using Persian words "
                      "over Arabic ones"),
        (1500, True, "Persian is the language of administration from the Balkans to Bengal"),
        (1837, False, "English replaces Persian as the official language of British India"),
    ],
    "Standard Malay": [
        (683, False, "the Kedukan Bukit inscription in Old Malay, in an Indic script"),
        (1300, True, "Jawi, an Arabic script for Malay, comes into use with Islam"),
        (1612, True, "the Sejarah Melayu compiled"),
        (1901, True, "a Latin orthography introduced under colonial rule"),
        (1972, False, "Malaysia and Indonesia agree a common spelling, so two national "
                      "standards of one language write it the same way"),
    ],
    "Standard Indonesian": [
        (1928, False, "the Youth Pledge names Malay, renamed Indonesian, as the language of a "
                      "nation that does not yet exist"),
        (1945, False, "made the national language at independence — chosen over Javanese, "
                      "which had far more speakers, because it belonged to no dominant group"),
        (1972, False, "spelling unified with Malaysia"),
        (2010, True, "spoken by most Indonesians, but the first language of a minority: the "
                     "clearest case anywhere of a national language adopted rather than "
                     "inherited"),
    ],
    "Zulu": [
        (1850, True, "the first Zulu grammar and orthography, by missionaries"),
        (1930, False, "Vilakazi's poetry, the first Zulu verse in print by a Zulu writer"),
        (1959, False, "apartheid's Bantu Education uses mother-tongue schooling as a tool of "
                      "separation, which leaves African-language education distrusted for "
                      "decades"),
        (1996, False, "one of eleven official languages of South Africa; the most widely "
                      "spoken first language in the country"),
    ],
    "Somali": [
        (1300, True, "Somali written in Arabic script by scholars, alongside a strong oral "
                     "poetic tradition"),
        (1920, True, "Osman Yusuf Kenadid devises the Osmanya script for Somali"),
        (1972, False, "a Latin orthography made official after decades of argument between "
                      "three scripts; a mass literacy campaign follows"),
        (1974, False, "Somali replaces Italian and English in schools and government"),
    ],
    "Georgian": [
        (430, False, "the Bir el Qutt inscriptions in Palestine, the oldest Georgian writing"),
        (500, True, "the Martyrdom of Shushanik, the oldest surviving Georgian text"),
        (1629, False, "the first printed Georgian book, in Rome"),
        (1978, False, "protests in Tbilisi keep Georgian as the state language of the "
                      "republic when Moscow moves to remove it from the constitution"),
    ],
    "Eastern Armenian": [
        (405, True, "Mesrop Mashtots devises an alphabet for Armenian, with letters unlike "
                    "any other script's"),
        (450, True, "a translation programme puts scripture, philosophy and history into "
                    "Armenian within a generation"),
        (1512, False, "the first printed Armenian book, in Venice"),
        (1915, False, "the genocide; the western dialect loses most of its speakers and its "
                      "homeland"),
        (2010, True, "western Armenian listed by UNESCO as endangered while eastern Armenian "
                     "is a state language"),
    ],
    "Finnish": [
        (1200, True, "the Birch bark letter no. 292, a charm — the oldest known writing in "
                     "any Finnic language"),
        (1543, False, "Agricola's ABC book, the first printed Finnish"),
        (1548, False, "his New Testament, which invents much of written Finnish"),
        (1835, False, "Lönnrot publishes the Kalevala, assembled from oral poetry he collected "
                      "on foot"),
        (1863, False, "Finnish given equal status with Swedish in Finland"),
    ],
    "Estonian": [
        (1525, True, "the first printed book in Estonian, of which only fragments survive"),
        (1739, False, "the Bible in Estonian"),
        (1857, False, "Perno Postimees begins, and its editor addresses readers as 'good "
                      "Estonians' rather than as country people"),
        (1918, False, "an official language at independence"),
        (1991, False, "restored as the state language after fifty years of Russian in public "
                      "life"),
    ],
    "Hungarian": [
        (1055, False, "the Tihanyi foundation charter, Latin with Hungarian words in it"),
        (1192, True, "the Funeral Sermon and Prayer, the oldest continuous Hungarian text"),
        (1590, False, "the Vizsoly Bible"),
        (1800, True, "the language reform coins thousands of words to replace Latin and German "
                     "technical vocabulary"),
        (1844, False, "Hungarian replaces Latin as the language of the Diet"),
    ],
    "Polish": [
        (1270, True, "the Book of Henryków contains a sentence in Polish, a husband telling "
                     "his wife to rest while he grinds"),
        (1440, True, "Jakub Parkoszowic writes the first treatise on Polish spelling"),
        (1561, False, "the Bible in Polish"),
        (1795, False, "partition; for over a century Polish is taught and printed against "
                      "official policy in much of its territory"),
        (1918, False, "the state language of a restored Poland"),
    ],
    "Czech": [
        (1057, True, "Czech words in the Litoměřice charter"),
        (1412, True, "Jan Hus proposes diacritics — the háček above a letter — replacing "
                     "clusters of consonants; the idea spreads across Central Europe"),
        (1579, False, "the Kralice Bible fixes a literary standard"),
        (1780, True, "the National Revival rebuilds written Czech after generations in which "
                     "German dominated public life"),
        (1918, False, "an official language of Czechoslovakia"),
    ],
    "Catalan": [
        (1150, True, "the Homilies d'Organyà, the oldest Catalan literary text"),
        (1490, False, "Tirant lo Blanc printed"),
        (1716, False, "the Nueva Planta decrees remove Catalan from courts and administration"),
        (1913, False, "Pompeu Fabra's orthographic norms give the language one spelling"),
        (1939, False, "banned from public use under Franco"),
        (1983, False, "a normalisation law returns it to schools and government in Catalonia"),
    ],
    "Faroese": [
        (1298, True, "the Sheep Letter, the oldest Faroese document"),
        (1781, True, "the language survives mainly in ballads, with Danish in print and "
                     "church"),
        (1846, False, "Hammershaimb devises an orthography based on Old Norse rather than on "
                      "pronunciation, which makes the writing look older than the speech"),
        (1938, False, "allowed in schools"),
        (1948, False, "the principal language of the Faroes"),
    ],
    "Maltese": [
        (1470, True, "Il-Kantilena, the oldest text in Maltese"),
        (1750, True, "written with Latin letters for a language descended from Arabic — the "
                     "only such case in Europe"),
        (1924, False, "the alphabet standardised"),
        (1934, False, "an official language of Malta"),
        (2004, False, "an official language of the European Union, the smallest by speakers"),
    ],
    "Cornish": [
        (1000, True, "the Bodmin manumissions record Cornish names"),
        (1400, True, "the Ordinalia, a cycle of religious plays in Cornish"),
        (1777, False, "Dolly Pentreath dies at Mousehole, traditionally the last monolingual "
                      "speaker"),
        (1904, False, "Henry Jenner's handbook starts the revival"),
        (2010, False, "UNESCO reclassifies Cornish from extinct to critically endangered, "
                      "because there are children speaking it again"),
    ],
    "Manx": [
        (1610, True, "the Book of Common Prayer translated into Manx"),
        (1775, False, "the Bible in Manx"),
        (1974, False, "Ned Maddrell dies, the last native speaker"),
        (2001, False, "the first Manx-medium primary school opens"),
        (2009, False, "declared extinct by UNESCO; schoolchildren write in to point out that "
                      "they are speaking it, and the classification is revised"),
    ],
    "Hokkaido Ainu": [
        (1600, True, "Ainu recorded by Japanese officials in Hokkaido; the language has a vast "
                     "oral epic literature and no script of its own"),
        (1899, False, "assimilation law; Ainu children are schooled in Japanese and the "
                      "language stops being passed on"),
        (1923, False, "Chiri Yukie, aged nineteen, writes down the yukar epics in Latin "
                      "letters with a Japanese translation, then dies the year it is finished"),
        (2019, False, "Japan recognises the Ainu as an Indigenous people; the language has "
                      "almost no fluent speakers left"),
    ],
    "Eastern Yiddish": [
        (1272, True, "a blessing in Yiddish in the margin of a Hebrew prayer book, the oldest "
                     "dated line"),
        (1541, True, "printed Yiddish books circulate in Europe"),
        (1908, False, "the Czernowitz conference declares Yiddish a national language of the "
                      "Jewish people"),
        (1939, True, "around eleven million speakers"),
        (1945, False, "the Holocaust kills most of them; the centre of the language shifts to "
                      "Hasidic communities where it is now growing again"),
    ],
    "Egyptian (Ancient)": [
        (-3200, True, "hieroglyphs at Abydos — among the earliest writing anywhere"),
        (-2600, True, "hieratic, a cursive hand for papyrus, in use alongside the carved "
                      "signs"),
        (-1300, True, "the height of the written language under the New Kingdom"),
        (-700, True, "demotic, a third script, for everyday business"),
        (394, False, "the last dated hieroglyphic inscription, at Philae"),
        (1822, False, "Champollion reads the Rosetta Stone and recovers the language after "
                      "fourteen centuries"),
    ],
    "Latin": [
        (-600, True, "the Praeneste fibula, among the earliest Latin inscriptions"),
        (-450, True, "the Twelve Tables"),
        (-50, True, "Cicero and Caesar; the prose that later ages copy"),
        (405, True, "Jerome's Vulgate"),
        (813, False, "the Council of Tours orders preaching in the local tongue, because "
                     "congregations no longer understand Latin — the first official notice "
                     "that Romance and Latin have parted"),
        (1962, False, "the Second Vatican Council permits the Mass in vernacular languages"),
    ],
    "Sumerian": [
        (-3300, True, "clay tokens and tablets at Uruk; the writing begins as accounting"),
        (-2600, True, "the signs become able to record connected language"),
        (-2000, True, "Sumerian stops being spoken but is studied and copied for another "
                      "1,500 years — the first dead language kept alive by scholarship"),
        (-100, True, "the last cuneiform tablets"),
        (1905, True, "the language is well enough understood to be read"),
    ],
    "Sanskrit": [
        (-1500, True, "the Rigveda composed and then transmitted by exact memorisation for "
                      "over a millennium before being written"),
        (-400, True, "Panini's grammar describes the language in about 4,000 rules, with a "
                     "precision not matched until the twentieth century"),
        (200, True, "classical Sanskrit is the language of learning across South and "
                    "Southeast Asia"),
        (1786, False, "William Jones tells the Asiatic Society that Sanskrit, Greek and Latin "
                      "must share a common source — the beginning of comparative linguistics"),
    ],
    "Old Norse": [
        (150, True, "the earliest runic inscriptions in the older futhark"),
        (800, True, "the Viking expansion carries the language from Newfoundland to the "
                    "Volga"),
        (1220, True, "Snorri Sturluson writes the Prose Edda, partly to teach poets a "
                     "vocabulary going out of use"),
        (1350, True, "the language has separated into the Scandinavian languages"),
    ],
    "Gothic": [
        (350, True, "Wulfila devises an alphabet and translates the Bible into Gothic — the "
                    "oldest substantial text in any Germanic language"),
        (500, True, "the Codex Argenteus written in silver and gold ink on purple vellum"),
        (1600, True, "a few Gothic words recorded in the Crimea; then nothing"),
    ],
    "Coptic": [
        (100, True, "Egyptian written in Greek letters plus six kept from demotic — the last "
                    "stage of the language of the pharaohs"),
        (300, True, "monastic literature in Coptic"),
        (1000, True, "Arabic displaces it in daily speech"),
        (1600, True, "the last reports of Coptic spoken at home; it continues in the liturgy "
                     "of the Coptic Church to this day"),
    ],
 # ---- INDO-EUROPEAN BATCH 2: the 48 languages labelled in pass 4, for those whose
 # record fixes real dates. A creole has an unusually good timeline because its
 # beginning IS an event — a ship, a plantation, a settlement with a year on it. The
 # Indo-Aryan varieties of the Hindi belt have the opposite problem: continuous speech,
 # no founding moment, and a documentary record that opens with a British survey.

 "Bhojpuri": [
   (1789, False, "the earliest dated Bhojpuri manuscripts, in the Kaithi script that clerks "
                 "across Bihar used for everything"),
   (1834, False, "indenture begins; over eighty years Bhojpuri speakers are shipped to "
                 "Mauritius, Fiji, Trinidad, Guyana, Suriname and South Africa"),
   (1884, False, "Grierson's *Seven Grammars of the Dialects of the Bihari Language* — the first "
                 "systematic description"),
   (1903, False, "the Linguistic Survey of India records it as a language, not a Hindi dialect"),
   (1949, False, "the Kaithi script is dropped from official use in Bihar in favour of "
                 "Devanagari"),
   (1963, False, "*Ganga Maiya Tohe Piyari Chadhaibo*, the first Bhojpuri feature film"),
   (1969, False, "the first petition to add Bhojpuri to the Eighth Schedule of the Indian "
                 "constitution; it is still pending"),
   (2018, False, "Mauritius adds Bhojpuri to its intangible heritage, and it enters schools "
                 "there before it does in India"),
 ],
 "Chhattisgarhi": [
   (1885, False, "Hira Lal Kavyopadhyay's grammar, the first description of the language"),
   (1890, True, "the Pandavani begins to be recorded — the Mahabharata performed by one singer "
                "with a tambura"),
   (2000, False, "Chhattisgarh becomes a state, and the language acquires a political case"),
   (2007, False, "Chhattisgarhi is declared the state's official language alongside Hindi"),
   (2019, False, "the state announces primary schooling in it; implementation is partial"),
 ],
 "Dogri": [
   (1800, True, "Dogri is written in Takri, a script of the western Himalaya related to Sharada"),
   (1863, False, "the first printed Dogri book, from the Dogra court at Jammu"),
   (1944, False, "the Dogri Sanstha is founded at Jammu to standardise and publish"),
   (1969, False, "the Sahitya Akademi recognises Dogri as an independent literary language"),
   (2003, False, "added to the Eighth Schedule of the Indian constitution, after six decades of "
                 "campaigning"),
 ],
 "Kumaoni": [
   (989, False, "a copper-plate inscription in the language, in Devanagari — one of the oldest "
                "dated documents in any Pahari variety"),
   (1868, False, "Kumaoni appears in the first Census of the North-Western Provinces"),
   (1916, True, "Gumani Pant's verse establishes a written literary register"),
   (2010, False, "UNESCO's Atlas lists it vulnerable: hill villages are emptying toward the "
                 "plains and children arrive there speaking Hindi"),
 ],
 "Garhwali": [
   (1400, True, "Garhwali appears in temple inscriptions of the Garhwal kingdom"),
   (1913, False, "the Linguistic Survey of India describes it as Central Pahari"),
   (2009, False, "the Ramman of Saloor Dungra, a Garhwali ritual theatre, joins UNESCO's "
                 "intangible heritage list"),
   (2010, False, "UNESCO lists the language itself as vulnerable"),
 ],
 "Rohingya": [
   (1799, False, "Francis Buchanan-Hamilton records a Rohingya word list — the first "
                 "documentation of the language, and evidence of the community's presence in "
                 "Arakan two centuries before its citizenship was denied"),
   (1975, True, "Mohammed Hanif devises the Hanifi Rohingya alphabet, adapting Arabic letters "
                "to the language's vowels"),
   (1982, False, "Burma's citizenship law excludes the Rohingya, and with them any state "
                 "provision for the language"),
   (2018, False, "Unicode 11.0 encodes Hanifi Rohingya — a script created in living memory and "
                 "adopted by a whole community"),
   (2017, False, "over 700,000 people cross into Bangladesh; the largest concentration of "
                 "Rohingya speakers is now a refugee settlement"),
 ],
 "Chakma": [
   (1800, True, "the Chakma script, a Brahmic alphabet related to Burmese, is in use for "
                "religious and administrative texts"),
   (1963, False, "the Kaptai dam floods a large part of the Chittagong Hill Tracts and displaces "
                 "much of the Chakma population"),
   (2012, False, "Unicode 6.1 encodes the Chakma script"),
   (2017, False, "Bangladesh begins printing primary textbooks in Chakma"),
 ],
 "Kabuverdianu": [
   (1462, False, "settlement of Santiago begins; a Portuguese-lexifier creole forms on islands "
                 "that had no prior population — the first creole society in the Atlantic"),
   (1856, False, "slavery is abolished in the archipelago"),
   (1880, True, "Eugénio Tavares writes his *mornas*, giving the language a literature"),
   (1975, False, "independence from Portugal; Portuguese remains the language of the state"),
   (1998, False, "the ALUPEC alphabet is proposed as a standard orthography"),
   (2009, False, "ALUPEC is adopted officially, though Portuguese keeps its position"),
 ],
 "Krio": [
   (1787, False, "the Province of Freedom is settled at Freetown by formerly enslaved people "
                 "from Britain"),
   (1792, False, "the Nova Scotian settlers arrive, followed by the Jamaican Maroons in 1800"),
   (1808, True, "recaptured slave ships land tens of thousands of liberated Africans at "
                "Freetown; Krio forms among them as the common language"),
   (1980, False, "the New Testament appears in Krio"),
   (2013, False, "the full Bible in Krio"),
 ],
 "Morisyen": [
   (1721, False, "French settlement of Mauritius; the creole forms on the sugar estates"),
   (1810, False, "Britain takes the island but leaves French law and language in place, so the "
                 "creole keeps its French lexicon"),
   (1822, False, "Chrestien's *Les Essais d'un bobre africain*, the earliest printed Morisyen"),
   (2011, False, "the Grafi-larmoni orthography is adopted"),
   (2012, False, "Morisyen enters primary schools as an optional subject"),
   (2022, False, "it is used in the National Assembly for the first time"),
 ],
 "Saramaccan": [
   (1690, True, "enslaved people escape the Suriname plantations and establish independent "
                "communities upriver"),
   (1762, False, "the Dutch sign a peace treaty recognising Saramaka autonomy — a century before "
                 "abolition"),
   (1778, False, "Schumann's Saramaccan–German dictionary, compiled by Moravian missionaries — "
                 "one of the earliest dictionaries of any creole"),
   (2007, False, "the Inter-American Court rules for the Saramaka in a land-rights case, the "
                 "first such judgment for a Maroon people"),
 ],
 "Seselwa Creole French": [
   (1770, False, "French settlement of the Seychelles; the creole forms within a generation"),
   (1976, False, "independence from Britain"),
   (1981, False, "Seselwa becomes an official language and the medium of early schooling — the "
                 "only French creole anywhere to get both"),
   (1982, False, "the Lenstiti Kreol is founded to standardise it"),
 ],
 "Hawai'i Creole English": [
   (1835, False, "the first sugar plantation opens at Kōloa; labourers arrive from China, "
                 "Portugal, Japan, Korea and the Philippines"),
   (1900, True, "the children of the plantations turn the contact pidgin into a creole — a "
                "first language with a grammar of its own"),
   (1987, False, "the Board of Education attempts to ban it in schools; the attempt fails after "
                 "public opposition"),
   (2000, False, "*Da Jesus Book*, the New Testament in Pidgin"),
   (2015, False, "the US Census Bureau lists it as a language of the home for the first time"),
 ],
 "Louisiana Creole French": [
   (1719, False, "the first slave ships reach Louisiana from Senegambia; the creole forms on the "
                 "plantations"),
   (1803, False, "the Louisiana Purchase brings the territory into an English-speaking country"),
   (1921, False, "the state constitution bans teaching in French, and both Louisiana Creole and "
                 "Cajun French begin to collapse"),
   (1968, False, "CODOFIL is created to promote French; it initially promotes Parisian French "
                 "rather than either local variety"),
   (2018, False, "Louisiana joins the Organisation internationale de la Francophonie, and the "
                 "revival turns toward the local languages"),
 ],
 "Cameroon Pidgin": [
   (1840, True, "an English-lexifier pidgin is in use on the Cameroon coast through the palm-oil "
                "trade"),
   (1884, False, "Germany annexes Kamerun; the pidgin survives German rule and outlives it"),
   (1961, False, "the British Southern Cameroons joins Cameroon; Kamtok is the everyday language "
                 "of the anglophone regions"),
   (2016, False, "the anglophone crisis begins, and the language becomes a marker in it"),
 ],
 "Domari": [
   (1000, True, "the Dom leave northwest India, taking an Indo-Aryan language west through "
                "Persia into the Levant — a separate migration from the one that produced Romani"),
   (1913, False, "Macalister's *The Language of the Nawar*, the first grammar, from Jerusalem"),
   (2012, False, "Matras publishes *A Grammar of Domari*, describing the Jerusalem variety, "
                 "then spoken fluently by fewer than ten people"),
 ],
 "Balkan Romani": [
   (1000, True, "the Roma leave northwest India; the language is the strongest evidence for "
                "where they came from, since no written record of the migration survives"),
   (1542, False, "Andrew Borde prints thirteen Romani sentences in England — the earliest "
                 "recorded Romani anywhere"),
   (1782, False, "Rüdiger demonstrates that Romani is an Indian language"),
   (1971, False, "the first World Romani Congress adopts a flag, an anthem and the name Roma"),
   (2008, False, "Romani becomes a recognised minority language in several Balkan states under "
                 "the European Charter"),
 ],
 "Kalo Finnish Romani": [
   (1559, False, "the Finnish Kale are first recorded in Finland, arriving via Sweden"),
   (1971, False, "Finland ends the last of the assimilation policies aimed at the Kale"),
   (1995, False, "a constitutional amendment gives Romani the right to be maintained and "
                 "developed; it enters schools"),
   (2010, True, "surveys find most Finnish Kale no longer speak it; it is severely endangered"),
 ],
 "Judeo-Tat": [
   (1700, True, "Juhuri is written in Hebrew letters by the Mountain Jews of the eastern "
                "Caucasus"),
   (1929, False, "the Soviet state switches the language to Latin script"),
   (1938, False, "and then to Cyrillic, nine years later"),
   (1990, True, "most speakers emigrate to Israel after the Soviet collapse"),
   (2010, False, "UNESCO lists Juhuri as endangered"),
 ],
 "Digor Ossetian": [
   (1798, False, "the first printed book in Ossetian, a catechism in Cyrillic"),
   (1844, False, "Sjögren's grammar establishes the modern Cyrillic orthography"),
   (1937, False, "Digor is declared a dialect of Iron and its separate literary use is "
                 "suppressed"),
   (1957, False, "Digor publishing resumes"),
   (2009, True, "Ossetian is the last living descendant of the Scythian and Alanic languages of "
                "the steppe, and the only one to survive the Turkic and Slavic expansions"),
 ],
 "Shina": [
   (1880, True, "Leitner records Shina during the Gilgit surveys"),
   (1924, False, "Bailey's *Grammar of the Shina Language*"),
   (1974, True, "Perso-Arabic orthographies for Shina are developed in Gilgit"),
   (2010, True, "Shina is one of the few Dardic languages with a growing published literature"),
 ],
 "Khowar": [
   (1880, True, "Khowar is recorded during the British surveys of Chitral"),
   (1919, False, "the first Khowar poetry appears in print"),
   (1958, False, "Khowar broadcasting begins on Radio Pakistan Peshawar"),
   (2003, True, "a standard Perso-Arabic orthography is agreed"),
 ],
 "Palula": [
   (1900, True, "Palula is noted in the Linguistic Survey of India as a Dardic language of "
                "southern Chitral"),
   (2004, False, "an orthography is developed with the community — the language's first"),
   (2013, False, "the first Palula dictionary is published"),
   (2016, False, "Liljegren's *A Grammar of Palula*, the full description"),
 ],
 "Chitral Kalasha": [
   (1896, False, "the Durand Line divides the Kalash from Nuristan, whose people are converted "
                 "by force the same year; the Chitral Kalash, on the British side, are not"),
   (1970, True, "anthropologists begin recording the language and the ritual calendar together"),
   (2003, False, "an orthography is agreed at a community conference in Chitral"),
   (2010, False, "UNESCO lists Kalasha as definitely endangered; the religion and the language "
                 "are declining together"),
 ],
 "Wakhi": [
   (1876, False, "Shaw's account of Wakhi, from the first European crossings of the corridor"),
   (1895, False, "the Anglo-Russian boundary commission fixes the Wakhan corridor, splitting one "
                 "language across four countries so two empires would not touch"),
   (1984, True, "Wakhi begins to be written in Cyrillic in Tajikistan and in Perso-Arabic in "
                "Pakistan"),
 ],
 "Shughni": [
   (1895, False, "the Pamir boundary settlement divides Shughni speakers between Russian "
                 "Bukhara and Afghanistan"),
   (1931, False, "Shughni is given a Latin alphabet and used in Soviet schools"),
   (1937, False, "the experiment is ended and Tajik replaces it"),
   (1990, True, "Cyrillic-based Shughni publishing resumes in Gorno-Badakhshan"),
 ],
 "Fala": [
   (1200, True, "Galician-Portuguese speakers are resettled in the Jálama valley, seven hundred "
                "kilometres from Galicia"),
   (1910, False, "Fala is first described in print, and identified as Galician-Portuguese rather "
                 "than a Spanish dialect"),
   (2001, False, "declared a *bien de interés cultural* by the Junta de Extremadura"),
 ],
 "Emiliano": [
   (1200, True, "Gallo-Italic speech is written in Emilia in notarial and devotional texts"),
   (1901, False, "the *Vocabolario bolognese-italiano* fixes a written form for the Bologna "
                 "variety"),
   (1999, False, "Italy's Law 482 recognises twelve minority languages and does not include "
                 "Emilian, which is classed as an Italian dialect"),
   (2015, True, "ISTAT finds it still spoken at home by a substantial minority in the region"),
 ],
 "Romagnol": [
   (1300, True, "Romagnol appears in verse and in notarial documents"),
   (1840, True, "a Romagnol theatre tradition establishes itself around Ravenna and Forlì"),
   (1979, False, "Tonino Guerra, who wrote in Romagnol, scripts *Amarcord*'s successors and "
                 "brings the language to a national audience"),
   (2014, False, "Emilia-Romagna passes a regional law to protect and promote its dialects"),
 ],
 "Gallurese Sardinian": [
   (1400, True, "Corsican settlement of northeastern Sardinia brings a Corsican-based speech "
                "across the strait"),
   (1770, True, "Gallurese poetry is established in written form"),
   (1997, False, "Sardinian regional law 26 recognises Gallurese separately from Sardinian"),
 ],
 "Sassarese Sardinian": [
   (1235, False, "Sassari's statutes are written in a language already distinct from both "
                 "Sardinian and Tuscan"),
   (1500, True, "Catalan and then Spanish rule leave their layers on it"),
   (1997, False, "recognised separately under Sardinian regional law 26"),
 ],
 "Swabian": [
   (1800, True, "Swabian is the everyday speech of a region whose written language is standard "
                "German"),
   (1904, False, "Fischer's *Schwäbisches Wörterbuch* begins publication, running to six volumes"),
   (1999, False, "Baden-Württemberg adopts the slogan *Wir können alles. Außer Hochdeutsch* — a "
                 "state government advertising its own dialect"),
 ],
 "Hazaragi": [
   (1880, True, "the Hazara wars; Abdur Rahman Khan's campaigns kill or displace a large part of "
                "the population"),
   (1962, False, "the first linguistic description of Hazaragi is published"),
   (1998, False, "the Taliban massacre at Mazar-i-Sharif"),
   (2021, False, "the Taliban return; Hazara speakers again leave in large numbers"),
 ],
 "Southern Pashto": [
   (1651, True, "Khushal Khan Khattak begins writing; he leaves some forty-five thousand "
                "couplets, much of it composed in Mughal prisons"),
   (1936, False, "Pashto is declared a national language of Afghanistan"),
   (1964, False, "the constitution makes Pashto and Dari the two official languages"),
   (1978, True, "the Pashto Academy at Kabul standardises orthography on the Kandahar variety"),
 ],
 "Eastern Balochi": [
   (1838, False, "Leech publishes the first Balochi vocabulary"),
   (1877, True, "Balochi is written in Perso-Arabic script for the first time in any quantity"),
   (1951, False, "the Balochi Academy is founded at Quetta"),
   (2005, True, "Korn's historical grammar shows Balochi's closest relatives are the languages "
                "of the Caspian coast, fifteen hundred kilometres north"),
 ],
 "Northern Luri": [
   (1300, True, "Luri appears in the poetry of the Lur dynasties of the Zagros"),
   (1963, False, "the first modern linguistic description of Luri"),
   (2010, True, "Iran counts Luri as a dialect of Persian; its speakers do not"),
 ],
 "Nuristani Kalasha": [
   (1896, False, "Abdur Rahman Khan conquers Kafiristan and converts it by force; the region is "
                 "renamed Nuristan, the land of light"),
   (1954, True, "Morgenstierne's surveys establish Nuristani as a third branch of Indo-Iranian, "
                "alongside Indo-Aryan and Iranian"),
   (2001, False, "Strand publishes the fullest modern account of the Nuristani languages"),
 ],
 "Chittagonian": [
   (1799, False, "Buchanan-Hamilton records Chittagonian alongside Rohingya, noting the two are "
                 "close"),
   (1903, False, "the Linguistic Survey of India treats it as a dialect of Bengali, a "
                 "classification that has held administratively ever since"),
   (2010, True, "linguists put the distance between Chittagonian and standard Bengali at about "
                "that between Portuguese and Spanish"),
 ],
 "Sadri": [
   (1900, True, "Sadri spreads as a lingua franca on the Chotanagpur plateau, used between Munda, "
                "Dravidian and Indo-Aryan communities"),
   (1860, True, "tea-garden recruitment carries Sadri speakers to Assam, where their descendants "
                "speak it still"),
   (2003, False, "Jharkhand recognises Sadri as a second official language of the state"),
 ],
 "Lambadi": [
   (1600, True, "the Banjara carry salt and grain for Mughal and Maratha armies across the "
                "Deccan, taking a Rajasthani language a thousand kilometres south"),
   (1871, False, "the Criminal Tribes Act designates the Banjara a criminal tribe; the "
                 "designation is not lifted until 1952"),
   (1952, False, "the Act is repealed and the community is denotified"),
 ],
}


def main() -> None:
    names: dict[str, list] = {}
    with open(GL, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["Level"] == "language":
                names.setdefault(r["Name"], []).append(r["ID"])
    out: dict[str, list] = {}
    expect: dict[str, str] = {}
    bad = []
    for nm, rows in M.items():
        hit = names.get(nm)
        if not hit:
            bad.append(f"{nm!r}: no language of that name in Glottolog")
            continue
        if len(hit) > 1:
            bad.append(f"{nm!r}: ambiguous, {len(hit)} languages share the name")
            continue
        gc = hit[0]
        # sorted, so a card reads forwards no matter what order they were written in
        out[gc] = [[y, bool(ap), t] for y, ap, t in sorted(rows, key=lambda r: r[0])]
        expect[gc] = max(nm.replace("(", " ").replace(")", " ").split(), key=len)
    for b in bad:
        print("  SKIPPED " + b)
    d = os.path.join(ROOT, "web", "data")
    json.dump({"note": "Dated events in the life of each language. Authored, keyed by exact "
                       "Glottolog name and resolved by machine. A true flag on an entry means "
                       "the date is approximate and the card shows it as c.",
               "expect": expect, "by_glottocode": out},
              open(os.path.join(d, "milestones.json"), "w"), ensure_ascii=False,
              separators=(",", ":"))
    n = sum(len(v) for v in out.values())
    ap = sum(1 for v in out.values() for r in v if r[1])
    print(f"{len(out)} languages, {n} dated events "
          f"({ap} approximate, {n-ap} fixed by the record), {len(bad)} skipped")
    if out:
        span = [r[0] for v in out.values() for r in v]
        print(f"   earliest {min(span)} · latest {max(span)}")


if __name__ == "__main__":
    main()
