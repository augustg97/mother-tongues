#!/usr/bin/env python3
"""build_notable.py — the wall labels, keyed by NAME and resolved to glottocodes by machine.

Seven of the first thirty labels sat on the wrong language because I wrote eight-character
glottocodes from memory: `nucl1301` is Turkish, not Standard Arabic. The fix is not to be
more careful. It is to never write a glottocode by hand again — label the language by the
name Glottolog calls it, resolve the code here, and fail loudly on anything ambiguous.

Each entry is (Glottolog name, image search terms, label). The name must match Glottolog
exactly; if it does not, or matches more than one language, this refuses to guess.

Run: python3 build_notable.py
"""
from __future__ import annotations

import csv
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
GL = os.path.join(ROOT, "data", "glottolog", "languages.csv")

# (exact Glottolog name, Commons search terms, label)
E = [
 ("Hittite", "Hittite cuneiform tablet Bogazkoy",
  "The first Indo-European language anyone wrote down. Hittite was the language of a Bronze "
  "Age empire in Anatolia, kept on clay tablets at Hattusa and lost for three thousand years "
  "until the archive was dug up in 1906 and read by Bedřich Hrozný in 1915. Its survival "
  "rewrote the family tree: Hittite keeps consonants the other branches had already lost, "
  "which is why Anatolian is now placed as the first branch to leave."),
 ("Sanskrit", "Rigveda manuscript",
  "The language of the Rigveda, composed orally around 1500–1200 BCE and carried by memory "
  "with such precision that the text was fixed for a millennium before it was written. "
  "Pāṇini's grammar of the fourth century BCE describes it in about four thousand rules — the "
  "most rigorous description of any language until the twentieth century."),
 ("Ionic-Attic Ancient Greek", "Homer Iliad papyrus",
  "Homer, Sappho, Plato, Thucydides. Greek was written first in Linear B for palace accounts, "
  "then in an alphabet borrowed from Phoenician and improved by giving the vowels their own "
  "letters — the change that made a fully phonemic script possible."),
 ("Latin", "Roman inscription Latin marble Trajan",
  "A minor dialect of Latium that followed the Roman army and outlived the empire twice: as "
  "the language of the western church for a thousand years, and as the ancestor of "
  "Portuguese, Spanish, Catalan, French, Italian and Romanian — all of which are Latin still "
  "being spoken."),
 ("Gothic", "Codex Argenteus",
  "The earliest substantial Germanic text: a fourth-century Bible translation by Wulfila, who "
  "invented an alphabet for it. The Codex Argenteus is written in silver and gold on purple "
  "vellum. Gothic died out, but because it was written three centuries before Old English it "
  "is the closest thing we have to the Germanic parent."),
 ("Old English (ca. 450-1100)", "Beowulf manuscript Cotton Vitellius",
  "The language of Beowulf and the Anglo-Saxon Chronicle — inflected, and almost entirely "
  "Germanic in vocabulary. Beowulf survives in a single copy that was scorched in a library "
  "fire in 1731 and is still crumbling at the edges."),
 ("Church Slavic", "Codex Zographensis Old Church Slavonic",
  "Devised in the ninth century by Cyril and Methodius so that Slavs could hear the liturgy "
  "in a language they understood. It is the oldest recorded Slavic language, and the "
  "alphabets that came from that mission — Glagolitic, then Cyrillic — are still in use "
  "across a quarter of Europe."),
 ("Avestan", "Avesta manuscript",
  "The language of the Gathas, hymns attributed to Zarathustra and among the oldest "
  "Indo-Iranian poetry that survives. It was preserved liturgically for centuries by priests "
  "who no longer spoke it."),
 ("Old Persian (ca. 600-400 B.C.)", "Behistun inscription",
  "The language of Darius and Xerxes, cut into a cliff at Behistun in three languages at "
  "once. That trilingual inscription was the key that opened Mesopotamian cuneiform, doing "
  "for Akkadian what the Rosetta Stone did for Egyptian."),
 ("Tokharian A", "Tocharian manuscript fragment",
  "Found in Buddhist manuscripts in the Tarim Basin — the easternmost Indo-European branch, "
  "four thousand kilometres from any other, and unexpectedly a centum language like Latin "
  "and Celtic rather than a satem one like its Iranian neighbours. Nobody has spoken it "
  "since roughly the ninth century."),
 ("Classical-Middle Armenian", "Armenian manuscript Matenadaran",
  "Given its own alphabet by Mesrop Mashtots around 405 CE specifically so that scripture "
  "could be translated. Armenian is a branch of Indo-European entirely on its own, and the "
  "manuscripts at the Matenadaran run unbroken from the fifth century."),
 ("Early Irish", "Book of Kells folio",
  "Old Irish has the earliest vernacular literature in western Europe after Latin and Greek, "
  "and one of the most complex verbal systems in the family. Its scribes also drew: the Book "
  "of Kells was made by people who spoke it."),
 ("Lithuanian", "Mazvydas Catechism 1547",
  "Often called the most conservative living Indo-European language — it kept case endings "
  "and pitch accent that Sanskrit had already lost. The first printed Lithuanian book is "
  "Martynas Mažvydas's catechism of 1547; under the Tsarist press ban of 1864–1904 books "
  "were smuggled in by knygnešiai, book-carriers."),
 ("Welsh", "Book of Aneirin Welsh manuscript",
  "One of the oldest continuously spoken languages in Britain, with a poetic tradition "
  "reaching back to the sixth century. Nearly extinguished by the nineteenth-century schools, "
  "it is now one of the clearest cases of a minority language deliberately turned around."),
 ("Gheg Albanian", "Meshari Gjon Buzuku",
  "A branch with no close relatives. The first substantial book is Gjon Buzuku's Meshari of "
  "1555; the language's isolation and heavy borrowing from Latin, Greek and Slavic made its "
  "position in the family hard to establish for a century."),
 ("Old Norse", "Codex Regius Poetic Edda",
  "The language of the sagas and the Eddas, and of the people who reached Vinland. Its "
  "descendants split sharply: Icelandic changed so little that modern readers manage the "
  "sagas, while Danish moved furthest of all."),
 ("Icelandic", "Icelandic saga manuscript Flateyjarbok",
  "The most conservative living Germanic language, kept close to Old Norse by isolation and "
  "by deliberate purism — new things get new compounds from native roots rather than "
  "loanwords: a computer is a tölva, a number-prophetess."),
 ("Old High German (ca. 750-1050)", "Hildebrandslied manuscript",
  "The ancestor of German, recorded from the eighth century and marked off from its Germanic "
  "cousins by the High German consonant shift, which turned p, t, k into pf, ts and ch. It is "
  "the change that separates Wasser from water."),
 ("Old French (842-ca. 1400)", "Chanson de Roland manuscript Oxford",
  "The language of the Chanson de Roland and of the Normans who took it to England, where it "
  "became the source of a third of the English vocabulary. It kept a two-case system that "
  "Modern French has entirely lost."),
 ("Old Saxon", "Heliand manuscript",
  "The Heliand retells the gospel as Germanic heroic verse, with Christ as a liege-lord and "
  "the apostles as his war-band — a translation not just of language but of the whole social "
  "world its hearers lived in."),
 ("Iron Ossetian", "Ossetian Nart sagas",
  "The last survivor of the Scythian-Sarmatian languages of the steppe, stranded in the "
  "Caucasus. Its Nart sagas preserve motifs that appear across the Iranian world, and Georges "
  "Dumézil used it as evidence for the shape of Indo-European myth."),
 ("Modern Greek", "Greek manuscript Byzantine gospel",
  "The only branch of Indo-European with a continuous written record from the Bronze Age to "
  "the present. A speaker today can make partial sense of a text written twenty-five "
  "centuries ago, which is true of no other living European language."),
 ("Eastern Yiddish", "Yiddish printed book Bovo-Bukh",
  "A Germanic language written in the Hebrew alphabet, carrying Hebrew, Aramaic and Slavic "
  "vocabulary — the everyday tongue of Ashkenazi Europe, and the language of most of the "
  "people murdered in the Holocaust. It survives in Hasidic communities and in a scattering "
  "of secular revival."),
 ("Tavringer Romani", "Romani people historical illustration",
  "An Indo-Aryan language carried out of northern India roughly a thousand years ago and "
  "spoken across Europe ever since, absorbing vocabulary from every country it passed "
  "through. Its Indian origin was established in the eighteenth century purely by comparing "
  "words."),
 ("Bengali", "Bengali manuscript Charyapada",
  "The language of Tagore and of the only country founded on a language movement: the "
  "students shot in Dhaka in 1952 for demanding Bengali are commemorated by UNESCO's "
  "International Mother Language Day."),
 ("Nepali", "Nepali manuscript Devanagari",
  "An Indo-Aryan language that spread across the Himalaya as an administrative tongue, now "
  "the shared second language of dozens of Tibeto-Burman communities that surround it."),
 ("Sinhala", "Sinhala inscription Sri Lanka",
  "Indo-Aryan, carried to Sri Lanka more than two thousand years ago and separated from its "
  "relatives ever since — a northern language with a southern island's history, written in a "
  "rounded script shaped by centuries of writing on palm leaves."),
 ("Northern Pashto", "Pashto manuscript Khushal Khan Khattak",
  "An Eastern Iranian language of the Afghan highlands with a written tradition from the "
  "sixteenth century, and a phonology conservative enough to preserve consonant clusters "
  "Persian has long simplified."),
 ("Marathi", "Marathi Modi script manuscript",
  "One of the oldest attested modern Indo-Aryan languages, written for centuries in the "
  "cursive Modi script before Devanagari displaced it, and the language of the Bhakti poets "
  "Dnyaneshwar and Tukaram."),
 ("Latvian", "Latvian dainas folk song manuscript",
  "Latvian and Lithuanian are the only Baltic languages left. Latvian's dainas — hundreds of "
  "thousands of four-line folk songs collected in the nineteenth century — are among the "
  "largest bodies of oral poetry ever written down."),
 ("Breton", "Breton manuscript Barzaz Breiz",
  "Celtic, but carried to France from Britain rather than surviving there, which makes it the "
  "only Celtic language on the continent. It has been in steep decline for a century and its "
  "speakers are mostly old."),
 ("Scottish Gaelic", "Book of the Dean of Lismore",
  "Brought from Ireland, once spoken across most of Scotland, and pushed to the western "
  "seaboard by the Clearances and by schooling that punished it. Its literature includes some "
  "of the finest verse in any Celtic language."),
 ("Catalan", "Catalan manuscript Ramon Llull",
  "Not a dialect of Spanish but a separate Romance language with its own medieval literature, "
  "banned from public life under Franco and now spoken by millions again."),
 ("Portuguese", "Cantigas de Santa Maria manuscript",
  "The Romance language that travelled furthest: from a corner of Iberia to Brazil, Angola, "
  "Mozambique, Goa and Macau. Its earliest literature is Galician-Portuguese lyric poetry."),
 ("Romanian", "Romanian old book Coresi",
  "Latin that survived east of the Adriatic, surrounded by Slavic for a thousand years and "
  "written in Cyrillic until the nineteenth century. It keeps a case system the western "
  "Romance languages lost."),
 ("Standard Arabic", "Quran manuscript Kufic",
  "The classical language of the Qur'an, and the shared written register of two dozen "
  "countries, while the spoken varieties of Morocco and Iraq are as far apart as Portuguese "
  "and Romanian."),
 ("Sumerian", "Sumerian cuneiform tablet",
  "A language isolate with no known relatives, and the first language on Earth to be written. "
  "Sumerian scribes invented cuneiform for accounting around 3300 BCE and it became a "
  "literature — Gilgamesh among it. It was still taught in schools long after nobody spoke it."),
 ("Akkadian", "Code of Hammurabi stele",
  "The Semitic language of Babylon and Assyria, written in borrowed Sumerian cuneiform. For "
  "centuries it was the diplomatic language of the whole Near East: the Amarna letters show "
  "an Egyptian pharaoh corresponding with Canaanite vassals in Akkadian."),
 ("Egyptian (Ancient)", "Egyptian hieroglyphs Book of the Dead",
  "Attested continuously for more than four thousand years, longer than any other language — "
  "from Old Kingdom hieroglyphs to Coptic, still used liturgically today. Champollion read it "
  "in 1822 with the Rosetta Stone."),
 ("Yucatec Maya", "Maya codex Dresden",
  "The Maya wrote the only fully developed writing system of the pre-Columbian Americas, "
  "combining syllabic signs with logograms; Yucatec is its closest living descendant. Almost "
  "all the books were burned in the sixteenth century and four codices survive."),
 ("Classical Nahuatl", "Florentine Codex Nahuatl",
  "The language of the Mexica and the lingua franca of central Mexico, written after the "
  "conquest in Latin letters by Nahua scribes — including the Florentine Codex, a twelve-book "
  "encyclopedia of their own world compiled in their own language."),
 ("Old Chinese", "Oracle bone script Shang",
  "The oracle bones of the Shang, inscribed with questions put to ancestors and cracked with "
  "heat, are the earliest Chinese writing and the direct ancestor of the characters in use "
  "today — the longest continuously used writing system in the world."),
 ("Korean", "Hunminjeongeum Haerye",
  "Korean was written with Chinese characters until 1443, when King Sejong's scholars designed "
  "hangul, an alphabet whose consonant shapes diagram the tongue and lips that make them. It "
  "is the only major writing system whose invention, date and rationale are all documented."),
 ("Old Japanese", "Kojiki manuscript",
  "Old Japanese survives in the Kojiki and the Man'yōshū, written with Chinese characters used "
  "for their sound. It preserves eight vowel distinctions that later Japanese collapsed to "
  "five — visible only because the scribes were consistent."),
 ("Finnish", "Kalevala manuscript Lonnrot",
  "Finnish spelling is close to one letter per sound, and its fifteen cases do the work "
  "prepositions do elsewhere. Elias Lönnrot assembled the Kalevala in the 1830s from oral "
  "poetry collected in Karelia; it gave the language a national epic and gave Tolkien the "
  "sound of Quenya."),
 ("Basque", "Basque inscription Euskara old book",
  "The last pre-Indo-European language of western Europe, spoken across the western Pyrenees "
  "and related to nothing else on Earth. It was already there when Latin arrived, survived "
  "Rome, and survived a twentieth-century ban on its public use."),
 ("Hindi", "Devanagari manuscript Hindi",
  "The Rigveda's distant descendant and the Mughal court's inheritance both feed Hindi-Urdu: "
  "one spoken language written in two scripts, whose separation into two named languages was "
  "an act of the nineteenth and twentieth centuries."),
 ("Mandarin Chinese", "Chinese calligraphy Lanting Xu",
  "More first-language speakers than any other language. Its writing is not an alphabet, so a "
  "text can be read aloud in Cantonese or Hokkien by someone who could not hold a "
  "conversation with the writer."),
 # ---- pass 2: Indo-European depth ------------------------------------------------------
 ("Middle English", "Canterbury Tales Ellesmere manuscript",
  "English after the Norman conquest had shed most of its endings and taken on a French "
  "vocabulary for law, food and rule. Chaucer wrote in it deliberately, when the court still "
  "used French, and in doing so made a literary language out of a servants' one."),
 ("Old Prussian", "Elbing vocabulary Old Prussian",
  "The third Baltic language, and the only one that died: extinct by about 1700 after German "
  "settlement and the Teutonic Order. It survives in three catechisms and a wordlist, which "
  "is enough to show it was more conservative than either Lithuanian or Latvian."),
 ("Oscan", "Oscan inscription Tabula Bantina",
  "Italic, but not Latin — the language of the Samnites who fought Rome for a century. It was "
  "written right to left in its own alphabet, and the graffiti at Pompeii show people still "
  "using it when Vesuvius buried the town."),
 ("Umbrian", "Iguvine Tablets",
  "Known almost entirely from the seven bronze Iguvine Tablets, a priesthood's ritual manual "
  "from Gubbio: which animals to sacrifice, which words to say, which direction to face. It "
  "is the fullest religious text in any Italic language other than Latin."),
 ("Sogdian", "Sogdian Ancient Letters manuscript",
  "The trade language of the Silk Road for a thousand years, carried by merchants from "
  "Samarkand as far as Chang'an. The Ancient Letters, abandoned in a watchtower west of "
  "Dunhuang around 313 CE, include a woman writing furiously to the husband who stranded her."),
 ("Bactrian", "Bactrian inscription Rabatak",
  "The only Iranian language ever written in Greek letters, a legacy of Alexander. The "
  "Rabatak inscription, found in 1993, rewrote the genealogy of the Kushan kings."),
 ("Khotanese", "Khotanese manuscript Dunhuang",
  "An Eastern Iranian language of the Tarim oases, written in Brahmi and used for Buddhist "
  "texts. Most of what survives came out of the sealed library cave at Dunhuang."),
 ("Kashmiri", "Sharada script manuscript Kashmir",
  "Dardic, at the northwestern edge of Indo-Aryan, with a word order unlike any of its "
  "neighbours — it puts the verb second, like German. It was written in Sharada, then "
  "Devanagari, then Perso-Arabic, as its writers changed religion and rulers."),
 ("Upper Sorbian", "Sorbian book Lusatia",
  "A West Slavic language spoken in Lusatia inside Germany, which has kept the dual number "
  "that almost every other Slavic language dropped — separate forms for two things as against "
  "three or more."),
 ("Cornish", "Cornish Ordinalia manuscript",
  "Declared dead in 1777 with the death of Dolly Pentreath, and revived in the twentieth "
  "century from medieval miracle plays and a handful of prose. There are children speaking it "
  "again, which is rarer than extinction."),
 ("Manx", "Manx Bible Manx Gaelic book",
  "Its last native speaker, Ned Maddrell, died in 1974 — and UNESCO reclassified it from "
  "extinct to critically endangered in 2009, because the revival had produced new speakers, "
  "including children schooled in it."),
 ("Faroese", "Faroese manuscript Foroyar",
  "Left with no written standard for four hundred years while Danish did all the writing; "
  "V. U. Hammershaimb built one in 1846 on etymological principles, so Faroese spelling shows "
  "its Old Norse ancestry more clearly than it shows its own pronunciation."),
 ("Western Frisian", "Frisian manuscript Fryslan",
  "The closest living relative of English — the two were still mutually intelligible when the "
  "Angles and Saxons left the North Sea coast. Frisian kept the sounds English lost: tsiis "
  "and cheese, tsjerke and church."),
 ("Occitan", "Troubadour manuscript chansonnier",
  "The language of the troubadours, who invented courtly love poetry and exported it to "
  "Italy, Catalonia and Germany. It was the prestige literary language of Europe before "
  "French was, and is now spoken mostly by the old."),
 ("Galician", "Cantigas de Santa Maria Galician manuscript",
  "Portuguese and Galician were one language until politics separated them: the medieval "
  "lyric of the whole peninsula was written in Galician-Portuguese, including by a Castilian "
  "king who wrote his hymns in it rather than his own tongue."),
 ("Logudorese Sardinian", "Sardinian charter Carte Volgari",
  "The most conservative Romance language: it kept the Latin hard c before front vowels, so "
  "kentu where Italian has cento. Its earliest documents are eleventh-century charters, older "
  "than almost any other Romance vernacular text."),
 ("Venetian", "Venetian manuscript Venice",
  "Not a dialect of Italian but a separate Romance language, and the language of a maritime "
  "republic that ran the eastern Mediterranean for five hundred years — which is why Venetian "
  "words turn up in Greek, Turkish and Croatian harbours."),
 ("Slovenian", "Freising manuscripts Slovene",
  "The Freising manuscripts of around 1000 CE are the oldest Slavic text in the Latin "
  "alphabet, and the oldest written Slovene. The language keeps the dual, and has an unusual "
  "number of mutually difficult dialects for so small a country."),
 ("Macedonian", "Macedonian manuscript Ohrid",
  "South Slavic, and the language whose separateness from Bulgarian has been argued about for "
  "a century for reasons that are mostly not linguistic. It is one of the few Slavic "
  "languages with a definite article, which it takes from the Balkan sprachbund."),
 ("Sindhi", "Sindhi manuscript Shah Jo Risalo",
  "Indo-Aryan, with a set of implosive consonants that almost no other Indo-European language "
  "has. Shah Abdul Latif's Risalo is sung rather than read, and the singing has kept the "
  "eighteenth-century text alive."),
 ("Gujarati", "Gujarati manuscript Jain",
  "The language Gandhi wrote his autobiography in, and the vehicle of a large Jain manuscript "
  "tradition. Its script dropped the horizontal bar that Devanagari runs across the top of "
  "every word, which is why the two look so different at a glance."),
 ("Odia", "Odia palm leaf manuscript",
  "Its rounded letters are a direct consequence of its writing surface: straight lines split "
  "a palm leaf along the grain, so the scribes curved everything. Odia has a literary record "
  "reaching back to the tenth century."),
 ("Assamese", "Assamese manuscript sanchipat",
  "Written on sanchipat, bark of the agar tree, in a script it shares with Bengali but with "
  "its own letters. Its early literature is largely the devotional work of Sankardev, who "
  "wrote plays to be performed in village prayer halls."),
 ("Northern Kurdish", "Kurdish manuscript Mem u Zin",
  "Kurdish is written in three alphabets across four countries and was banned outright in "
  "Turkey until 1991. Ehmedê Xanî's Mem û Zîn of 1692 is its national epic and argues, inside "
  "the poem, that Kurdish deserves to be a written language."),
 # ---- pass 2: Sino-Tibetan --------------------------------------------------------------
 ("Yue Chinese", "Cantonese opera manuscript Guangdong",
  "Cantonese keeps six tones and a set of final consonants that Mandarin lost a thousand "
  "years ago, which is why Tang poetry often rhymes in Cantonese and not in Mandarin. It has "
  "its own written register, with characters invented for words Mandarin has no use for."),
 ("Hakka Chinese", "Hakka walled village Fujian tulou",
  "The language of a people whose name means 'guest families' — northerners who moved south "
  "in waves over a thousand years and were still being treated as incomers centuries later. "
  "Their round earthen tulou were built to be defended."),
 ("Wu Chinese", "Shanghai Wu Chinese book",
  "Shanghainese and its relatives keep the voiced initials that Middle Chinese had and every "
  "other major branch lost. Wu has more first-language speakers than Italian and no official "
  "status anywhere."),
 ("Min Nan Chinese", "Peh-oe-ji Taiwanese romanization Bible",
  "Hokkien split from the rest of Chinese so early that it preserves a layer of vocabulary "
  "older than Middle Chinese. Presbyterian missionaries gave it a romanisation, Pe̍h-ōe-jī, in "
  "which a literate population published newspapers for a century."),
 ("Classical Tibetan", "Tibetan manuscript Dunhuang Kanjur",
  "The script was designed in the seventh century for translating Buddhist scripture, and its "
  "spelling froze then — modern Tibetans write clusters they have not pronounced for a "
  "thousand years, which makes the orthography a fossil of the older language."),
 ("Old Burmese", "Myazedi inscription Burmese",
  "The Myazedi inscription of 1113 CE carries the same text in Burmese, Pyu, Mon and Pali — "
  "the Rosetta Stone of mainland Southeast Asia, and the key that recovered Pyu."),
 ("Burmese", "Burmese palm leaf manuscript parabaik",
  "Its rounded letters, like Odia's, come from writing on palm leaves with a stylus. Burmese "
  "has a sharp split between a formal literary register and the spoken language, wide enough "
  "that the two use different words for 'this'."),
 ("Tangut", "Tangut manuscript Khara-Khoto",
  "The language of the Western Xia empire, written in a script of nearly six thousand "
  "characters deliberately designed to look like Chinese and to be unreadable to Chinese. It "
  "was recovered from the dead city of Khara-Khoto and deciphered in the twentieth century."),
 ("Kathmandu Valley Newari", "Newar manuscript Nepal Bhasa",
  "Nepal Bhasa has manuscripts from the twelfth century and was the court language of the "
  "Kathmandu valley until the Shah conquest. It was suppressed under the Rana regime and is "
  "now shifting fast to Nepali."),
 ("Manipuri", "Meitei Mayek manuscript puya",
  "Meitei abandoned its own script for Bengali under an eighteenth-century religious "
  "conversion, in which older manuscripts were burned. Meitei Mayek was reintroduced into "
  "schools in the 2000s — a script recovered after two centuries."),
 ("Dzongkha", "Dzongkha Bhutan manuscript dzong",
  "Bhutan's national language, written in Tibetan script and named for the dzongs, the "
  "fortress-monasteries where it was the administrative tongue."),
 ("Sichuan Yi", "Yi script manuscript bimo",
  "The Nuosu syllabary has more than eight hundred characters and was used by bimo priests "
  "for ritual texts. A standardised version was made official in Sichuan in 1980, one of very "
  "few indigenous scripts in China to get state backing."),
 ("Lisu", "Fraser alphabet Lisu Bible",
  "Written in the Fraser alphabet, which uses upright and upside-down Latin capitals and "
  "nothing else — no diacritics at all. It was designed to be printable on any press that "
  "had Roman type."),
 ("Lepcha", "Lepcha manuscript Rong script",
  "The Lepcha of Sikkim have their own script, traditionally said to have been written "
  "originally on bamboo, which is why its letters were rotated ninety degrees when they moved "
  "to paper."),
 ("Limbu", "Limbu Sirijanga script manuscript",
  "The Sirijanga script was created in the eighteenth century, suppressed, and revived in the "
  "twentieth by a man who took the name of its inventor."),
 ("Garo", "Garo hills manuscript Achik",
  "A Tibeto-Burman language of Meghalaya in a matrilineal society, where property passes "
  "through daughters — a fact that shows up in the kinship vocabulary."),
 ("Mizo", "Mizo hills manuscript Mizoram",
  "Mizo was written down by Welsh missionaries, and Mizoram now has one of the highest "
  "literacy rates in India. Its tone system distinguishes words that the Latin alphabet, as "
  "adopted, does not mark."),
 ("S'gaw Karen", "Karen script manuscript Burma",
  "Written in a script adapted from Burmese by American missionaries in the 1830s. The Karen "
  "have been at war with the Burmese state for longer than almost any other people on Earth, "
  "and the language is now written as much in refugee camps as at home."),
 ("Naxi", "Dongba pictographic manuscript Naxi",
  "The Dongba script of the Naxi is the only pictographic writing system still in ritual use "
  "anywhere in the world. It does not spell words: it prompts a priest who already knows the "
  "text."),
 ("Tibetan", "Tibetan prayer wheel manuscript Lhasa",
  "Lhasa Tibetan has developed tones that the written language does not mark, because the "
  "consonant clusters that produced those tones are still spelled out."),
 ("Solu-Khumbu Sherpa", "Sherpa Solukhumbu manuscript",
  "A Tibetic language of the Khumbu, whose speakers' name has become an English common noun "
  "for a job they were hired to do."),
 ("Rawang", "Rawang Kachin state manuscript",
  "Spoken in the far north of Myanmar in some of the least surveyed valleys in Asia, with "
  "dozens of varieties that may or may not be one language depending on who is counting."),
 ("Bai", "Bai language Dali manuscript",
  "So heavily layered with Chinese loans over two thousand years that whether Bai is "
  "Sino-Tibetan at all, and where it sits if it is, remains genuinely unsettled."),
 ("Northern Qiang", "Qiang stone tower Sichuan",
  "Qiang has one of the most complex consonant systems in the family and no tones — unusual "
  "in a region where almost everything is tonal. Its stone watchtowers still stand in the "
  "valleys of northwest Sichuan."),
 # ---- pass 3: Afro-Asiatic ---------------------------------------------------------------
 ("Ancient Hebrew", "Dead Sea Scrolls Isaiah",
  "Hebrew stopped being anyone's daily speech around 200 CE and stayed a written and "
  "liturgical language for seventeen centuries — then was brought back into ordinary use in "
  "the twentieth. It is the only case of a language with no native speakers acquiring "
  "millions of them again."),
 ("Ugaritic", "Ugaritic tablet alphabet Ras Shamra",
  "The oldest alphabet we have in order: a cuneiform script of thirty signs from Ras Shamra, "
  "with an abecedary tablet showing the sequence that still underlies Hebrew, Greek and "
  "Latin. The city burned around 1190 BCE and its archive was baked."),
 ("Phoenician", "Phoenician inscription Ahiram sarcophagus",
  "The traders who exported the alphabet. Phoenician script became Greek, and through Greek "
  "everything from Latin to Cyrillic to the letters you are reading now."),
 ("Imperial Aramaic (700-300 BCE)", "Elephantine papyri Aramaic",
  "The administrative language of the Persian empire from Egypt to the Indus, which is why "
  "an Aramaic letter survives from a Jewish garrison on an island in the Nile. Parts of "
  "Daniel and Ezra are in it."),
 ("Classical Syriac", "Syriac manuscript Peshitta",
  "The Aramaic of Edessa, and the vehicle of a vast Christian literature that carried Greek "
  "philosophy and medicine eastward — translated into Syriac first, and from Syriac into "
  "Arabic, which is how much of Aristotle reached Baghdad."),
 ("Geez", "Geez manuscript Ethiopian Garima Gospels",
  "The Garima Gospels, written in Ge'ez, are among the oldest illuminated Christian "
  "manuscripts in existence. Ge'ez script began as an abjad and added vowels by modifying "
  "each consonant's shape — an alphasyllabary invented independently of India's."),
 ("Tigrinya", "Tigrinya manuscript Eritrea",
  "One of Ge'ez's living descendants, written in the same script, and the working language of "
  "Eritrea and of Ethiopia's Tigray region."),
 ("Coptic", "Coptic manuscript Nag Hammadi",
  "Egyptian written in Greek letters plus seven signs kept from demotic — the last stage of a "
  "language attested for four thousand years. The Nag Hammadi library, buried in a jar in the "
  "fourth century, is in Coptic."),
 ("Maltese", "Maltese manuscript Cantilena",
  "The only Semitic language written in the Latin alphabet and the only one that is an "
  "official language of the European Union: Arabic grammar with a vocabulary half Italian, "
  "the result of a thousand years in the middle of the Mediterranean."),
 ("Kabyle", "Kabyle Berber manuscript Algeria",
  "Berber of the Algerian mountains, and the centre of a movement that fought for the "
  "language's recognition through the 1980s and 1990s. Tamazight is now official in Algeria, "
  "which it was not within living memory."),
 ("Chaouia of the Aures", "Aures Berber Algeria",
  "Shawiya, of the Aurès massif — a Berber variety long left out of standardisation efforts "
  "aimed at Kabyle, and shifting to Arabic faster than its neighbours."),
 ("Tahaggart Tamahaq", "Tifinagh inscription Tuareg",
  "The Tuareg write Tifinagh, a script descended from ancient Libyco-Berber, and it has been "
  "kept alive largely by women, who traditionally taught it. Neo-Tifinagh is now used for "
  "road signs in Morocco."),
 ("Tachelhit", "Tashelhit manuscript Souss Morocco",
  "Shilha has a written literature in Arabic script going back to the twelfth century, which "
  "makes it one of very few Berber varieties with a long manuscript tradition of its own."),
 ("Hausa", "Ajami manuscript Hausa Kano",
  "West Africa's great trade language, with perhaps eighty million speakers counting second "
  "languages. It has been written in Arabic script — ajami — for centuries, and in Latin "
  "since colonial rule, and the two are still both in use."),
 ("Somali", "Somali poetry manuscript Osmanya script",
  "A language of poets, where oral verse was the main political medium, and which had no "
  "official script until 1972 — after decades of argument in which the Osmanya alphabet, "
  "invented locally, lost to the Latin one."),
 ("West Central Oromo", "Oromo Qubee script Ethiopia",
  "The most widely spoken Cushitic language, banned from writing and broadcast in Ethiopia "
  "until 1991. It adopted a Latin orthography, Qubee, in 1991 — the choice itself an act of "
  "politics."),
 ("Afar", "Afar Danakil Ethiopia",
  "Spoken across the Danakil depression, one of the hottest inhabited places on Earth, by "
  "people whose language has a grammatical distinction for whether something is within sight."),
 ("Beja", "Beja Red Sea hills Sudan",
  "The only member of its branch of Cushitic, spoken in the Red Sea hills. Its speakers are "
  "the Beja whom Roman and Egyptian sources call the Blemmyes."),
 ("Wolaytta", "Wolaytta Ethiopia manuscript",
  "An Omotic language of southern Ethiopia — Omotic being the branch whose membership of "
  "Afro-Asiatic at all is the family's longest-running argument."),
 ("Sidamo", "Sidama Ethiopia",
  "Cushitic, spoken by several million people in southern Ethiopia, and one of the languages "
  "that gained a written standard only after 1991."),
 ("Punic", "Punic inscription Carthage stele",
  "Carthaginian, a Phoenician colonial language that outlived the city itself: Augustine "
  "records people in North Africa still speaking it in the fifth century CE, six hundred "
  "years after Carthage fell."),
 ("Sabaic", "Sabaean inscription Marib South Arabia",
  "The monumental language of Saba in Yemen, cut in a beautifully geometric script whose "
  "letters were designed for stone. Its inscriptions record the dam at Marib and the caravan "
  "trade in incense."),
 ("Amharic", "Amharic manuscript Ethiopia illuminated",
  "Ethiopia's working language, written in the Ge'ez script, and the second most spoken "
  "Semitic language after Arabic. Its literature includes royal chronicles kept continuously "
  "for centuries."),
 # ---- pass 4: Austronesian ---------------------------------------------------------------
 ("Amis", "Amis Taiwan indigenous Pangcah",
  "Taiwan is the Austronesian homeland: the deepest divisions in the whole family are between "
  "its aboriginal languages, and everything from Madagascar to Easter Island descends from one "
  "branch that left. Amis is the largest of the languages that stayed."),
 ("Atayal", "Atayal Taiwan weaving tattoo",
  "A Formosan language of the northern mountains, with an elaborate system of verbal focus "
  "that later Austronesian languages simplified — the grammar Philippine languages inherited "
  "in reduced form."),
 ("Paiwan", "Paiwan Taiwan carving slate house",
  "Its speakers carve narrative reliefs on slate house-posts. Paiwan preserves consonant "
  "distinctions used to reconstruct Proto-Austronesian itself."),
 ("Tsou", "Tsou Taiwan Alishan",
  "One of the most divergent Formosan languages, spoken by a few thousand people on Alishan, "
  "and a key witness in every attempt to date the Austronesian expansion."),
 ("Bunun", "Bunun Taiwan pasibutbut polyphonic",
  "The Bunun sing pasibutbut, an eight-part rising polyphony with no clear parallel anywhere, "
  "and their language marks the shape of the landscape in its verbs of motion."),
 ("Kawi", "Kawi manuscript lontar Java",
  "Old Javanese, written on palm leaf, carries the Ramayana and Mahabharata into Southeast "
  "Asia and supplies half the vocabulary of court Javanese. Balinese priests still read it."),
 ("Javanese", "Javanese script hanacaraka manuscript",
  "More first-language speakers than any language without a state of its own. Its speech "
  "levels are among the most elaborate on Earth: separate vocabularies for speaking up, down "
  "and across, so that choosing a word for 'eat' places both people socially."),
 ("Balinese", "Balinese lontar manuscript",
  "Written on lontar palm in its own script, and still the language of temple ritual and of "
  "shadow-puppet performance, where the puppeteer switches register between gods and clowns."),
 ("Sundanese", "Sundanese script manuscript West Java",
  "Thirty million speakers in West Java, with its own script revived for public signage, and "
  "a distinct musical tradition its poetry is written for."),
 ("Tagalog", "Baybayin script manuscript Philippines",
  "Written in baybayin before the Spanish arrived — a script that marked syllables and left "
  "final consonants unwritten, which the friars found so inconvenient that they replaced it."),
 ("Cebuano", "Cebuano Visayan manuscript Philippines",
  "More native speakers than Tagalog, and no share of the national standard: Filipino was "
  "built on Tagalog, which is a decision people in the Visayas have never stopped noting."),
 ("Iloko", "Ilocano Biag ni Lam-ang manuscript",
  "Its epic Biag ni Lam-ang was oral for centuries before it was written, and Ilocano became "
  "the trade language of the northern Philippines and of Filipino migration to Hawai'i."),
 ("Standard Malay", "Jawi script Malay manuscript Hikayat",
  "Written in Jawi, an Arabic-derived script, for six centuries before Latin letters — the "
  "trade language of the whole archipelago, and the base of both Malaysian and Indonesian."),
 ("Acehnese", "Acehnese Jawi manuscript Aceh",
  "Its vowel system is one of the largest in the family, and its literature in Jawi includes "
  "the Hikayat Prang Sabi, recited to fighters during the Dutch war."),
 ("Batak Toba", "Batak pustaha bark book",
  "The Batak wrote divination manuals — pustaha — on folded tree-bark in their own script, "
  "read by datu priests. They are among the very few indigenous books of island Southeast Asia."),
 ("Buginese", "Lontara script Bugis La Galigo",
  "The Bugis wrote in lontara script, and their La Galigo is one of the longest works of "
  "literature ever composed — longer than the Mahabharata, and still not fully published."),
 ("Plateau Malagasy", "Malagasy Sorabe manuscript Madagascar",
  "Its closest relatives are in Borneo, four thousand miles away across open ocean, which is "
  "how we know Madagascar was settled from Indonesia. Sorabe manuscripts wrote it in Arabic "
  "script before the Latin alphabet arrived."),
 ("Hawaiian", "Hawaiian newspaper nupepa manuscript",
  "Nineteenth-century Hawai'i had one of the highest literacy rates in the world and dozens "
  "of Hawaiian-language newspapers. The language was then banned in schools from 1896; the "
  "immersion movement of the 1980s brought it back from fewer than fifty child speakers."),
 ("Maori", "Maori Treaty of Waitangi manuscript",
  "The Treaty of Waitangi exists in two versions that do not say the same thing, and the "
  "difference between 'sovereignty' and 'kāwanatanga' has been litigated for a century and a "
  "half. Kōhanga reo, language nests, began the modern revival in 1982."),
 ("Samoan", "Samoan fale tattoo Samoa",
  "Samoan keeps a formal oratorical register with an entirely separate vocabulary, used by "
  "chiefs' orators, so that ordinary and ceremonial speech share grammar but not words."),
 ("Tonga (Tonga Islands)", "Tongan manuscript Tonga",
  "The only Pacific island nation never colonised, and its language keeps an honorific system "
  "with three levels of vocabulary — for commoners, for chiefs, and for the king."),
 ("Rapanui", "Rongorongo tablet Easter Island",
  "Rongorongo, the script of Easter Island, is carved in boustrophedon with every other line "
  "upside down. It has never been deciphered, and the people who could read it died in the "
  "slave raids and epidemics of the 1860s."),
 ("Chamorro", "Chamorro latte stone Guam",
  "Three centuries of Spanish rule left Chamorro with Spanish numbers and Spanish loanwords "
  "in a thoroughly Austronesian grammar, and the latte stone pillars of its speakers' "
  "ancestors still standing on Guam."),
 ("Fijian", "Fijian manuscript Fiji drua",
  "Fijian sits at the boundary between Melanesia and Polynesia and helped establish that the "
  "Polynesian languages are a single recent branch — the last great migration in the family."),
 # ---- pass 5: Uralic ---------------------------------------------------------------------
 ("Estonian", "Estonian song festival laulupidu",
  "Estonian has three degrees of length where most languages have two, so the same syllable "
  "can mean three different things. Its independence movement of 1988 was carried by mass "
  "choral singing and is remembered as the Singing Revolution."),
 ("Hungarian", "Halotti beszed Hungarian manuscript",
  "Uralic, surrounded on every side by Indo-European, and stranded there by a ninth-century "
  "migration off the steppe. The Funeral Sermon of about 1195 is the oldest continuous text "
  "in any Uralic language."),
 ("North Saami", "Sami joik drum Lapland",
  "The largest Saami language, written across three states in one orthography agreed only in "
  "1979. Its speakers were beaten for using it in Norwegian and Swedish boarding schools "
  "within living memory."),
 ("South Saami", "Southern Sami Norway Sweden",
  "Separated from North Saami by enough distance that the two are not mutually intelligible, "
  "and down to a few hundred speakers spread thinly along the Norwegian-Swedish border."),
 ("Skolt Saami", "Skolt Sami Sevettijarvi Finland",
  "Its speakers were displaced from Petsamo when the Soviet Union annexed it in 1944 and "
  "resettled in Finland. The language has perhaps three hundred speakers and an orthography "
  "with some of the most complex diacritics in Europe."),
 ("Inari Saami", "Inari Sami Finland lake",
  "Spoken only around one lake, and rescued by a language-nest programme begun in 1997 when "
  "there were almost no child speakers left. There are now children who use it daily."),
 ("Karelian", "Karelian Kalevala runo singers",
  "The runo-singers Lönnrot collected the Kalevala from were Karelian, not Finnish — the "
  "epic that became Finland's national poem was assembled largely from the songs of people "
  "across the border."),
 ("Veps", "Veps Vepsian Karelia Russia",
  "A Finnic language of the Lake Onega region, written in Latin script in the 1930s, banned "
  "in 1937, and revived on paper in 1989 with very few speakers left to read it."),
 ("Votic", "Votic Vote Ingria Russia",
  "Down to a handful of elderly speakers in a few villages in Ingria — one of the most nearly "
  "extinct languages in Europe, and one of the closest relatives of Estonian."),
 ("Liv", "Livonian coast Latvia Liv",
  "Its last native speaker died in 2013. Livonian is now spoken only by learners, and it left "
  "its mark on Latvian grammar — the two lived side by side for eight hundred years."),
 ("Ingrian", "Ingrian Izhorian Russia",
  "Fewer than a hundred speakers on the south shore of the Gulf of Finland, after "
  "deportations in the 1930s and 1940s scattered the community that spoke it."),
 ("Erzya", "Erzya Mordvin Russia embroidery",
  "One of two Mordvinic languages that are usually named as one; Erzya and Moksha are not "
  "mutually intelligible and each has its own literary standard."),
 ("Moksha", "Moksha Mordvin Russia",
  "The other Mordvinic language, with a vowel system quite unlike Erzya's, and a written "
  "tradition that has been standardised, unstandardised and restandardised with Soviet "
  "language policy."),
 ("Eastern Mari", "Mari sacred grove Russia",
  "Mari religion was never fully displaced by Christianity or by the Soviet state: sacred "
  "groves are still used, and the prayers said in them are in Mari."),
 ("Western Mari", "Hill Mari Gornomariysky Russia",
  "The smaller of the two Mari standards, with its own newspaper and its own literary norm, "
  "separated from Meadow Mari by the Volga."),
 ("Udmurt", "Udmurt embroidery Russia",
  "Permic, and one of the few minority languages of Russia with a visible modern pop culture "
  "— its speakers are known internationally for a singing group of grandmothers."),
 ("Komi-Zyrian", "Abur Old Permic script Stefan of Perm",
  "Given its own alphabet, Abur, by Stefan of Perm in 1372 — one of the earliest scripts "
  "devised for any language of northern Eurasia, and used for two centuries before Cyrillic "
  "displaced it."),
 ("Komi-Permyak", "Komi-Permyak Russia",
  "Separated administratively from Komi-Zyrian and given a distinct written standard, which "
  "is most of what makes it count as a separate language."),
 ("Kazym-Berezover-Suryskarer Khanty", "Khanty Ob river Siberia",
  "Ob-Ugric, and among the closest living relatives of Hungarian — a fact that took "
  "eighteenth-century scholars by surprise and was resisted in Hungary for a century."),
 ("Northern Mansi", "Mansi bear ceremony Siberia",
  "The other Ob-Ugric language, with a bear ceremony whose songs use a special vocabulary "
  "that ordinary speech may not touch. Fewer than a thousand speakers remain."),
 ("Tundra Nenets", "Nenets reindeer chum Yamal",
  "Samoyedic, spoken across the Yamal tundra by reindeer herders, and one of very few "
  "indigenous languages of the Russian Arctic still being learned by children."),
 ("Forest Enets", "Enets Taimyr Siberia",
  "Perhaps a few dozen speakers on the Taimyr peninsula. Enets is among the most endangered "
  "languages in the world with any documentation at all."),
 ("Nganasan", "Nganasan Taimyr shaman",
  "The northernmost language on the Eurasian mainland, and the most divergent Samoyedic one. "
  "Its shamanic tradition was recorded on film in the twentieth century, in the language."),
 ("Selkup", "Selkup Siberia Ob",
  "Southern Samoyedic, scattered across the Siberian taiga in dialects that differ enough to "
  "be hard to standardise, which has hampered every attempt to teach it."),
 # ---- pass 6: Atlantic-Congo, and the Mande neighbours -----------------------------------
 ("Swahili", "Swahili ajami manuscript Utendi",
  "The Indian Ocean's trade language, Bantu in grammar with centuries of Arabic vocabulary, "
  "written in Arabic script long before Latin. Its classical poetry, the utendi, was composed "
  "on the Lamu coast from at least the seventeenth century."),
 ("Yoruba", "Ifa divination board opon Ifa",
  "The Ifá divination corpus is a memorised body of verse organised into 256 chapters, each "
  "attached to a pattern cast on a divining board — one of the largest oral literatures ever "
  "recorded, and UNESCO-listed."),
 ("Igbo", "Igbo Ukwu bronze Nigeria",
  "Igbo has hundreds of varieties and a standard nobody entirely accepts, assembled from "
  "several of them. The ninth-century bronzes of Igbo-Ukwu were cast by its speakers' "
  "ancestors, by lost-wax, centuries before contact with Europe."),
 ("Zulu", "Zulu izibongo praise poetry beadwork",
  "Zulu has three click consonants, borrowed from the Khoisan languages its speakers married "
  "into — sounds that entered Bantu from outside. Its izibongo are praise poems recited at "
  "speed by a specialist who must not stop for breath."),
 ("Xhosa", "Xhosa click consonants beadwork",
  "Fifteen click consonants, more than any other Bantu language, and the same borrowing "
  "history. Xhosa was one of the first African languages with a printed newspaper, in 1837."),
 ("Shona", "Great Zimbabwe stone enclosure",
  "The stone city of Great Zimbabwe was built by Shona speakers between the eleventh and "
  "fifteenth centuries, and colonial authorities spent decades insisting somebody else must "
  "have done it."),
 ("San Salvador Kongo", "Kongo catechism 1556 Kikongo",
  "The Kingdom of Kongo had a Catholic king and a written vernacular within a generation of "
  "Portuguese contact: a Kikongo catechism was printed in 1556, making it one of the first "
  "African languages ever put into print."),
 ("Kinshasa Lingala", "Lingala Congo river trade",
  "A river language that spread with trade and then with the colonial army, simplified as it "
  "went, and now the language of Congolese music heard across the continent."),
 ("Wolof", "Wolofal ajami manuscript Senegal",
  "Written in Wolofal, an Arabic script tradition used by Sufi brotherhoods for devotional "
  "verse, and spoken as a second language by most Senegalese regardless of ethnicity."),
 ("Hausa States Fulfulde", "Fulfulde ajami manuscript Sokoto",
  "Fulfulde stretches from Senegal to Sudan, carried by herders across five thousand "
  "kilometres of Sahel, and its noun-class system runs to more than twenty classes."),
 ("Akan", "Adinkra symbols Ghana cloth",
  "Adinkra are stamped symbols, each with a name and a proverb attached, printed on cloth for "
  "funerals — a visual vocabulary that runs alongside the spoken one rather than writing it."),
 ("Ewe", "Ewe Vodun Ghana Togo",
  "Ewe is tonal to the point that its drums can speak: talking drums reproduce the tone and "
  "rhythm of phrases closely enough to carry messages between villages."),
 ("Ga", "Ga Accra Ghana kane",
  "The language of Accra before Accra was a capital, now heavily pressed by Twi and English "
  "in the city its speakers founded."),
 ("Kinyarwanda", "Rwanda imigongo art",
  "One of the very few African countries where nearly everyone speaks the same first "
  "language. Kinyarwanda has a tone system and a verb that can carry a whole clause in one "
  "word."),
 ("Ganda", "Buganda kingdom Uganda barkcloth",
  "Luganda's noun classes govern agreement on almost every word in a sentence, so changing a "
  "noun changes the shape of everything around it."),
 ("Southern Sotho", "Sesotho Lesotho manuscript",
  "Sesotho had a written literature early: Thomas Mofolo's Chaka, written in it in 1925, is "
  "one of the first African novels and is still in print in translation."),
 ("Tswana", "Setswana Bible Moffat 1857",
  "The first Bantu language to receive a complete printed Bible, in 1857 — which fixed its "
  "orthography and made it the vehicle of literacy across a large part of southern Africa."),
 ("Nyanja", "Chewa nyau masks Malawi",
  "Chichewa is the language of the Nyau, a masked society whose performances are a form of "
  "public commentary that ordinary speech is not allowed to make."),
 ("Bemba (Zambia)", "Bemba Zambia copperbelt",
  "Spread across the Zambian copperbelt by labour migration, becoming a lingua franca of the "
  "mines and then of a nation."),
 ("Kikuyu", "Kikuyu Kenya Mount Kenya",
  "Ngũgĩ wa Thiong'o abandoned English for Gĩkũyũ in 1977 and was imprisoned; he wrote his "
  "next novel on prison toilet paper, in Gĩkũyũ."),
 ("Efik", "Nsibidi symbols Cross River",
  "Nsibidi, used across the Cross River region, is a system of ideographs older than any "
  "European contact — used for law, for love, and by the Ekpe society for messages outsiders "
  "were not meant to read."),
 ("Duala", "Duala Cameroon coast",
  "A coastal trading language of Cameroon, and the first there to be written, which gave it "
  "an outsized role in mission education."),
 ("Fang (Equatorial Guinea)", "Fang byeri reliquary Gabon",
  "The Fang byeri reliquary figures, guarding ancestral skulls, reached Paris in the early "
  "twentieth century and changed European sculpture."),
 ("Vai", "Vai syllabary Liberia manuscript",
  "One of the very few writing systems in history invented from scratch by someone with no "
  "literacy in another script: Momolu Duwalu Bukele devised the Vai syllabary around 1833, "
  "reportedly after a dream, and it is still in use."),
 ("Eastern Maninkakan", "Nko script manuscript Kante",
  "Solomana Kanté invented the N'Ko alphabet in 1949 in direct answer to the claim that "
  "African languages could not be written properly. It is written right to left, and a whole "
  "publishing culture grew up around it without any state support."),
 # ---- pass 7: Trans-New-Guinea and the Papuan families -----------------------------------
 ("Fore", "Fore people Papua New Guinea highlands",
  "Kuru, the laughing sickness, ran through Fore country in the mid-twentieth century and was "
  "traced to mortuary feasting. Working it out established that a disease could be carried by "
  "a misfolded protein, and won a Nobel Prize."),
 ("Oksapmin", "Oksapmin body counting Papua New Guinea",
  "Counting in Oksapmin runs up one arm, across the head and down the other — twenty-seven "
  "named body parts in a fixed order, each one a number. Cash and schooling have been slowly "
  "rebuilding it into base ten."),
 ("Kalam", "Kalam Papua New Guinea highlands",
  "Kalam has roughly a hundred verbs in total and builds everything else by stringing them "
  "together, so 'fetch water' comes out as go get come put. It is the standard example of "
  "how far a language can get on almost no verbs."),
 ("Yimas", "Yimas Sepik river Papua New Guinea",
  "Ten noun classes, an agreement system that marks subject, object and indirect object on "
  "the verb at once, and enough morphological complexity that its grammar is a standard "
  "reference for what human languages are capable of."),
 ("Iatmul", "Iatmul Sepik haus tambaran",
  "Iatmul clans own tens of thousands of hereditary names — for people, spirits, places and "
  "objects — and disputes over who owns which name are argued in ceremonial debates that can "
  "last for days."),
 ("Enga", "Enga Papua New Guinea highlands",
  "The largest Papuan language, with several hundred thousand speakers in the western "
  "highlands, and one of the few with enough speakers that its future is not in question."),
 ("Melpa", "Moka exchange Mount Hagen",
  "The moka is a competitive gift exchange in which giving more than you received is how "
  "status is won. The vocabulary for its stages is precise enough to function as an "
  "accounting system."),
 ("Huli", "Huli wigmen Papua New Guinea",
  "Huli has a separate 'pandanus language' — a taboo vocabulary used only in the forest "
  "during the pandanus harvest, with different words for hundreds of ordinary things, so that "
  "spirits do not overhear."),
 ("Western Dani", "Dani highlands Papua Baliem",
  "Dani colour terms became famous in the 1960s as the test case for whether language shapes "
  "perception: the language divides colour into two, and its speakers turned out to sort "
  "colour chips much as everyone else does."),
 ("Central Asmat", "Asmat bisj pole New Guinea",
  "The Asmat carve bisj poles from mangrove for the dead, each figure standing for a person "
  "whose death is unavenged. The poles are made to be used once and left to rot back into the "
  "swamp."),
 ("Korowai", "Korowai treehouse Papua",
  "The Korowai build houses in trees, sometimes tens of metres up, and were not contacted by "
  "outsiders until the 1970s — among the last people on Earth to be so."),
 ("Marind", "Marind Anim Papua ceremony",
  "Marind speakers of southern Papua organise almost everything — clans, myths, land — around "
  "totemic categories that the language marks grammatically."),
 ("Ekari", "Ekari Kamu valley Papua",
  "Ekari counts in base sixty, one of very few languages outside ancient Mesopotamia to do "
  "so, with distinct words for each unit up to sixty and then a new cycle."),
 ("Telefol", "Telefol Telefomin Papua New Guinea",
  "Telefol counting also runs across the body, twenty-seven points, and its speakers' cult "
  "house at Telefomin sat at the centre of a religious network across the whole Mountain Ok "
  "region."),
 ("Golin", "Golin Chimbu Papua New Guinea",
  "Golin has a whistled register that carries across valleys, reproducing the tone and rhythm "
  "of speech closely enough for a specific message to arrive intact."),
 ("Amele", "Amele Madang Papua New Guinea",
  "Amele's verb morphology generates a famously enormous number of distinct forms, and its "
  "switch-reference system marks whether the next clause has the same subject as this one."),
 ("Alamblak", "Alamblak Sepik Papua New Guinea",
  "A Sepik language whose noun classes divide the world partly by shape — long and thin "
  "against short and squat — rather than by anything a European grammar would recognise."),
 ("Kobon", "Kobon Papua New Guinea Kaironk",
  "Like Kalam, Kobon manages with a very small number of verbs, and its speakers' "
  "classification of birds and plants was detailed enough to be published as ethnobiology."),
 ("Angguruk Yali", "Yali highlands Papua",
  "Spoken in the eastern highlands of Papua, in valleys so steep that neighbouring villages "
  "can be a day's walk apart, which is much of why the region holds so many languages."),
 ("Wambon", "Wambon Papua Digul river",
  "One of the Awyu-Dumut languages of the Digul basin, an area whose languages were barely "
  "described until the late twentieth century."),
 ("Nend", "Nend Madang Papua New Guinea",
  "A small Madang language, one of hundreds in a province that holds more distinct languages "
  "per square kilometre than anywhere else on Earth."),
 ("Kuman", "Kuman Chimbu Papua New Guinea",
  "One of the larger highland languages, and among the first to be written down by "
  "missionaries in the 1930s when the highlands were opened."),
 # ---- pass 8: Uto-Aztecan and the Americas -----------------------------------------------
 ("Ambulas", "Abelam yam cult haus tambaran",
  "The Abelam grow ceremonial yams several metres long, and the language has a register used "
  "only when addressing them, because a yam that overhears ordinary speech will not grow."),
 ("Cherokee", "Cherokee syllabary Sequoyah",
  "Sequoyah, who could not read any language, spent twelve years working out a syllabary for "
  "Cherokee and finished it in 1821. Within a few years the nation's literacy rate exceeded "
  "that of the settlers around it, and it had its own newspaper."),
 ("Navajo", "Navajo code talkers Diné",
  "The Navajo code talkers of the Second World War built a cipher on a language with almost "
  "no outside speakers and a verb so complex that its stem changes with the shape of the "
  "object being handled. It was never broken."),
 ("Hopi", "Hopi kachina Arizona",
  "Whorf argued from Hopi that its speakers conceived time differently; later work showed he "
  "had overstated it. The claim and its correction are the founding episode of the whole "
  "argument about language and thought."),
 ("Tohono O'odham", "Tohono O'odham basket Arizona",
  "Uto-Aztecan, spoken across a border that was drawn through the middle of its speakers in "
  "1853, and one of the larger indigenous languages still spoken in the United States."),
 ("Comanche", "Comanche horse plains",
  "The Comanche language spread with the horse across the southern plains and became a trade "
  "language of the region. Its last fully fluent speakers are very few."),
 ("Yaqui", "Yaqui deer dance Sonora",
  "The deer song tradition of the Yaqui is sung in an archaic register of the language kept "
  "for that purpose, and the songs describe the world from the deer's point of view."),
 ("Huichol", "Huichol yarn painting Wixarika",
  "Wixárika yarn paintings and beadwork encode the peyote pilgrimage, and the language's "
  "ritual vocabulary reverses ordinary meanings during it."),
 ("Central Ojibwa", "Ojibwe birch bark scroll wiigwaasabak",
  "The Midewiwin recorded songs and teachings on birch-bark scrolls in mnemonic pictographs. "
  "Ojibwe verbs distinguish animate from inanimate throughout the grammar, and the assignment "
  "is not the one an English speaker would guess."),
 ("Siksika", "Blackfoot winter count Siksika",
  "Blackfoot's sound system drifted so far from its Algonquian relatives that its membership "
  "was doubted for years until the correspondences were worked out."),
 ("Cheyenne", "Cheyenne ledger art plains",
  "Ledger art, drawn on the pages of traders' account books, carried Cheyenne narrative "
  "painting through the reservation period when hide was no longer available."),
 ("Mohawk", "Mohawk wampum belt Haudenosaunee",
  "Wampum belts record treaties and law in bead patterns that a trained reader recites at "
  "length. The Great Law of the Haudenosaunee is carried this way."),
 ("K'iche'", "Popol Vuh manuscript Ximenez",
  "The Popol Vuh survives because a friar copied out a K'iche' text in the Latin alphabet "
  "around 1701 with a Spanish translation beside it. It is the fullest Maya creation "
  "narrative that exists."),
 ("Lakota", "Lakota winter count hide",
  "Winter counts recorded each year by a single pictograph on hide, chosen by consensus for "
  "the event that most marked it — a calendar in which the community decides what a year was."),
 ("Zuni", "Zuni pueblo New Mexico pottery",
  "A language isolate in the middle of the Southwest, related to nothing around it, spoken in "
  "a pueblo continuously occupied for centuries."),
 ("Northern Haida", "Haida totem pole Haida Gwaii",
  "Another isolate, on Haida Gwaii, with a few dozen elderly first-language speakers and an "
  "immersion programme racing them."),
 ("Tlingit", "Tlingit Chilkat blanket totem",
  "Tlingit has a series of ejective consonants and a verb built from prefix positions in a "
  "fixed order — and the crest designs on its speakers' blankets are owned property, like "
  "names."),
 ("Kalaallisut", "Greenlandic Kalaallisut Greenland",
  "Polysynthetic to the point that a single word can be a sentence, and the only Inuit "
  "language that is the official language of a country."),
 ("Eastern Canadian Inuktitut", "Inuktitut syllabics Nunavut",
  "Written in a syllabics adapted from Cree, in which each consonant's symbol rotates to show "
  "the following vowel — one shape doing the work of four letters."),
 ("Cusco Quechua", "Quipu khipu Inca knots",
  "The Inca ran an empire without writing as we define it, using khipu — knotted cords whose "
  "numerical content is understood and whose narrative content, if it exists, is not."),
 ("Central Aymara", "Aymara Tiwanaku Bolivia",
  "Aymara speakers gesture forward when speaking of the past and back toward the future, "
  "matching the language's own metaphor: what you have seen is in front of you."),
 ("Paraguayan Guaraní", "Guarani Paraguay manuscript",
  "The only indigenous language of the Americas spoken by a national majority and official "
  "alongside a colonial one — most Paraguayans speak it, including people with no indigenous "
  "ancestry."),
 ("Tupinambá", "Tupinamba Brazil Anchieta grammar",
  "The coastal language the Portuguese met first, which supplied Brazilian Portuguese with "
  "thousands of words and had a printed grammar by 1595, before most European vernaculars."),
 ("Garifuna", "Garifuna drum Belize Honduras",
  "Arawakan in grammar, spoken by descendants of shipwrecked Africans and Island Caribs, and "
  "historically with distinct men's and women's vocabularies inherited from two different "
  "populations."),
 ("Mapudungun", "Mapudungun Mapuche Chile",
  "The Mapuche were never conquered by the Inca and held off Spain for three centuries; the "
  "treaty border on the Bío Bío is one of very few the Spanish crown ever recognised in the "
  "Americas."),
 ("Pirahã", "Piraha Amazon Brazil Maici",
  "Pirahã became the centre of an argument about whether a human language can lack recursion. "
  "The claim is contested; what is not is that it has a whistled and a hummed register used "
  "for hunting and for talking through the rain."),
 ("Huautla Mazatec", "Mazatec whistled speech Oaxaca",
  "Mazatec men hold entire conversations in whistles that carry the tones of the spoken "
  "language across valleys — not a code but the language itself, with the vowels removed."),
 ("Yatzachi Zapotec", "Zapotec Monte Alban inscription",
  "The Zapotec of Monte Albán produced the earliest writing in the Americas, around 500 BCE — "
  "predating Maya script by centuries and still only partly read."),

 #  A batch added because a measurement said so. Ranking every language by the number of people
 #  who edited its Wikipedia last month — the one number that says a language is being written
 #  today, and that a bot cannot inflate — showed that 203 of the 316 languages with an
 #  encyclopedia had no label here at all, and the list was headed by English, Spanish, German,
 #  French, Japanese and Russian. The museum had gone deep on Hittite and Tocharian and left the
 #  languages most of its visitors actually read in blank cases.
 # 
 #  Search terms are specific named artefacts where one exists, because a free-text query for
 #  "German manuscript" returns whatever has both words near it.

# ---- INDO-EUROPEAN DEEP PASS, BATCH 2 -----------------------------------------------------
# The next tranche down the same ranked list. Heavy on the creoles and the contested
# language-or-dialect cases, because that is what the remainder of Indo-European is: Awadhi and
# Magahi have forty million speakers between them and are counted as Hindi; Nigerian Pidgin is
# probably the most spoken language in Nigeria and has no status at all.
 ('Awadhi', ['Category:Awadhi language', 'Ramcharitmanas manuscript'],
  "The language of the Ramcharitmanas, Tulsidas's sixteenth-century retelling of the Ramayana, which is recited across northern India and is probably the most widely known work in any Indian language after the Sanskrit epics themselves. Awadhi carried most of the region's literature before the dialect that became standard Hindi did, and it is now counted as Hindi by the census and as a separate language by linguists — twenty-two million speakers who officially do not have a language of their own.",
  'Glottolog 5.3 treats Awadhi as a language; the Indian census returns it under Hindi.'),
 ('Magahi', ['Category:Magahi language', 'Category:Magadha'],
  'Spoken across the old kingdom of Magadha in southern Bihar, where the Buddha preached and Ashoka ruled — the Magadhi Prakrit of the third century BCE is its direct ancestor, which gives it one of the deepest recorded pedigrees of any modern Indian language. It has some twenty million speakers, is counted as Hindi in the census, and has no place in the Eighth Schedule.',
  'Glottolog 5.3; the Magadhi Prakrit descent is standard in Indo-Aryan historical linguistics.'),
 ('Sylheti', ['Category:Sylheti Nagri', 'Category:Sylhet'],
  'Spoken in northeastern Bangladesh and by most of the British Bangladeshi community, and long treated as a dialect of Bengali despite limited mutual intelligibility. It had a script of its own — Sylheti Nagri, used from the sixteenth century for popular religious verse and printed on lithograph presses into the twentieth — which was displaced by Bengali script and is now being revived.',
  'Glottolog 5.3 treats Sylheti as a language; Sylheti Nagri was added to Unicode in 2005.'),
 ('Saraiki', ['Category:Saraiki language', 'Category:Multan'],
  'Spoken across southern Punjab in Pakistan, distinguished from Punjabi by its implosive consonants — sounds made by drawing air inward, which almost nothing else in the region has. It was counted as a dialect of Punjabi until a long movement won it a separate census category in 1981, and a campaign for a Saraiki province continues.',
  "Glottolog 5.3; Saraiki was first counted separately in Pakistan's 1981 census."),
 ('Goan Konkani', ['Category:Konkani language', 'Category:Goa'],
  "Written in five scripts — Devanagari, Roman, Kannada, Malayalam and Perso-Arabic — because its speakers are spread across four Indian states and three religions, and each community wrote it in the script it already knew. Portuguese suppressed it in Goa for two centuries; it became an official language of Goa in 1987 and was added to India's Eighth Schedule in 1992.",
  "Glottolog 5.3; Goa's Official Language Act 1987; Eighth Schedule via the 71st Amendment, 1992."),
 ('Ladino', ['Category:Judaeo-Spanish', 'Category:Rashi script'],
  'The Spanish of the Jews expelled from Iberia in 1492, carried to Salonica, Istanbul, Sarajevo and Rhodes and kept for four and a half centuries — so it preserves fifteenth-century Castilian sounds that Spain itself has lost. It was written in Hebrew letters, usually in the Rashi script, and its speaker communities were destroyed in the Holocaust; UNESCO now lists it as severely endangered.',
  'Glottolog 5.3; UNESCO Atlas classes Judaeo-Spanish as severely endangered.'),
 ('Pontic', ['Category:Pontic Greek', 'Category:Pontus'],
  'The Greek of the southern Black Sea coast, separated from the rest of Greek for so long that it preserves features of Ionic and of Koine that Modern Greek lost — it is closer to ancient Greek in some respects than the standard is. Its speakers were removed to Greece in the 1923 population exchange, and the variety spoken around Trabzon by Muslim families remained in Turkey.',
  'Glottolog 5.3; the 1923 Convention Concerning the Exchange of Greek and Turkish Populations.'),
 ('Aromanian', ['Category:Aromanian language', 'Category:Aromanians'],
  'An Eastern Romance language of the southern Balkans — Greece, Albania, North Macedonia — and the clearest evidence that Latin survived in the Balkan interior as well as in Romania. Its speakers were traditionally transhumant shepherds and traders, which is why it is spoken in scattered communities rather than one territory, and why it has no state.',
  'Glottolog 5.3; UNESCO classes Aromanian as definitely endangered.'),
 ('Mirandese', ['Category:Mirandese language', 'Category:Miranda do Douro'],
  "Asturian-Leonese spoken in three Portuguese villages, and the only language other than Portuguese with official recognition in Portugal — granted in 1999 after a schoolteacher's campaign. About fifteen thousand people speak it, and it is taught in local schools.",
  'Glottolog 5.3; Portuguese Law 7/99 of 29 January 1999.'),
 ('Limburgan', ['Category:Limburgish', 'Category:Limburg'],
  'Spoken across the Dutch, Belgian and German borders, and one of very few European languages with lexical tone — a difference in pitch distinguishes words, which is a feature of Chinese and Norwegian and almost nothing between them. The Netherlands recognised it as a regional language in 1997; Belgium and Germany did not.',
  'Glottolog 5.3; recognised by the Netherlands under the European Charter in 1997.'),
 ('Western Flemish', ['Category:West Flemish', 'Category:West Flanders'],
  'The Dutch of the Belgian coast, with more than a million speakers and no standing beside standard Dutch. It kept the h that standard Dutch lost and lost the ones standard Dutch kept, and its vocabulary carries French from centuries of contact across a border that has moved repeatedly.',
  'Glottolog 5.3; Belgium recognises Dutch, not its regional varieties.'),
 ('Picard', ['Category:Picard language', 'Category:Picardy'],
  'The Oïl language of northern France and southern Belgium, where it is called Chtimi. It has a medieval literature — Picard was a serious literary language before Francien won — and the Belgian French Community recognises it while France recognises nothing.',
  'Glottolog 5.3; recognised by the French Community of Belgium, decree of 1990.'),
 ('Ligurian', ['Category:Ligurian language', 'Category:Genoa'],
  "The language of Genoa and its maritime empire, which carried it to Corsica, Sardinia, Gibraltar and the Black Sea. Monégasque, spoken in Monaco, is Ligurian, and is taught in Monaco's schools — a Gallo-Italic language with more institutional support outside Italy than in it.",
  "Glottolog 5.3; Monégasque has been compulsory in Monaco's schools since 1976."),
 ('Arpitan', ['Category:Arpitan', 'Category:Franco-Provençal'],
  'Franco-Provençal: a Gallo-Romance language between French and Occitan, spoken across eastern France, western Switzerland and the Aosta Valley, and recognised only in Italy. It was identified as a distinct language in 1873 by Graziadio Ascoli, who noticed it was neither of its neighbours — a language discovered by a linguist before its speakers had a name for it.',
  "Glottolog 5.3; Ascoli's identification, 1873; protected in Italy under Law 482/1999."),
 ('Extremaduran', ['Category:Extremaduran language', 'Category:Extremadura'],
  'Astur-Leonese spoken in northwestern Extremadura, with no official recognition and a written tradition that is essentially one poet — José María Gabriel y Galán, at the turn of the twentieth century. UNESCO classes it as definitely endangered.',
  'Glottolog 5.3; UNESCO Atlas classes Extremaduran as definitely endangered.'),
 ('Lower Sorbian', ['Category:Lower Sorbian', 'Category:Lusatia'],
  'West Slavic, spoken in Lusatia inside Germany — an island of Slavic speech that has been surrounded by German for a thousand years. It keeps the dual number, which almost all Slavic languages lost, and it has perhaps a few thousand speakers left; Upper Sorbian to the south has more. Both are protected by the constitutions of Brandenburg and Saxony.',
  'Glottolog 5.3; UNESCO classes Lower Sorbian as severely endangered.'),
 ('Northern Frisian', ['Category:North Frisian', 'Category:North Frisia'],
  'Spoken on the German North Sea coast and its islands, in nine varieties several of which are not mutually intelligible — the islands were separated by water and the mainland by marsh. It is one of the three Frisian languages, of which West Frisian in the Netherlands is by far the largest.',
  'Glottolog 5.3; recognised in Schleswig-Holstein by the Frisian Act of 2004.'),
 ('Ems-Weser Frisian', ['Category:Saterland Frisian', 'Category:Saterland'],
  'Saterland Frisian: the last surviving East Frisian, spoken in three villages in Lower Saxony by around two thousand people. The marshes that isolated Saterland are the reason it survived when the rest of East Frisian was replaced by Low German.',
  'Glottolog 5.3; UNESCO classes Saterland Frisian as severely endangered.'),
 ('Pennsylvania German', ['Category:Pennsylvania German', 'Category:Amish'],
  'A Palatine German brought to Pennsylvania in the eighteenth century, and one of very few immigrant languages in North America that is growing — because the Amish and Old Order Mennonite communities who speak it have large families and keep it as the language of home and worship. Its speakers are mostly trilingual: Pennsylvania German at home, English outside, and a form of German for scripture.',
  'Glottolog 5.3; the growth is documented in census and community demographic studies.'),
 ('Kölsch', ['Category:Kölsch', 'Category:Cologne'],
  'The Ripuarian of Cologne, with its own dictionary, its own grammar and a carnival song tradition that keeps it audible. Like the rest of the Rhineland continuum it sits between High and Low German — Cologne is close to the Benrath line, where the second consonant shift stops.',
  'Glottolog 5.3; the Akademie för uns Kölsche Sproch maintains the standard.'),
 ('Pfaelzisch-Lothringisch', ['Category:Palatine German', 'Category:Lorraine Franconian'],
  'The Palatine German of the Rhine and the Franconian of Lorraine — one continuum across a national border, and the source of Pennsylvania German. In France it is one of the langues régionales with no official status; in Germany it is a dialect.',
  "Glottolog 5.3; Pennsylvania German's Palatine origin is well established."),
 ('Nigerian Pidgin', ['Category:Nigerian Pidgin', 'Category:Nigeria'],
  'Spoken as a second language by tens of millions across Nigeria and increasingly as a first language in the cities — probably the most widely spoken language in the country, with no official status. The BBC launched a Pidgin news service in 2017, which did more for its standing than decades of argument.',
  'Glottolog 5.3; BBC News Pidgin launched 21 August 2017.'),
 ('Jamaican Creole English', ['Category:Jamaican Patois', 'Category:Jamaica'],
  'Patois: an English-lexified creole with a West African grammar, spoken by essentially all Jamaicans and written mostly in music, poetry and scripture. The Cassidy orthography of the 1960s gave it a phonemic spelling that most speakers do not use, because English spelling is what they were taught. The Bible was published in it in 2012.',
  'Glottolog 5.3; the Cassidy-JLU orthography; Di Jamiekan Nyuu Testiment, 2012.'),
 ('Sranan Tongo', ['Category:Sranan Tongo', 'Category:Suriname'],
  'The lingua franca of Suriname, English-lexified with Dutch and Portuguese layers and a grammar from the Gbe and Kikongo languages. Its early written record — letters and court documents from the eighteenth century — makes it one of the best-documented creoles in its formative period, which is why it appears so often in the literature on how creoles form.',
  'Glottolog 5.3; the eighteenth-century Sranan corpus is a standard source in creole studies.'),
 ('Papiamento', ['Category:Papiamento', 'Category:Aruba'],
  'Iberian-lexified rather than English or French — the argument is whether it began Portuguese or Spanish — spoken in Aruba, Bonaire and Curaçao and one of very few creoles that is an official language and a medium of school instruction. It has lexical tone, unusual for a creole, and two competing spellings, one etymological and one phonemic.',
  "Glottolog 5.3; official in Aruba since 2003 and in the Netherlands' Caribbean municipalities."),
 ('Chavacano', ['Category:Chavacano', 'Category:Zamboanga'],
  'The only Spanish-lexified creole in Asia, spoken around Zamboanga in the southern Philippines — Spanish vocabulary over a Philippine grammar, the residue of three centuries of Spanish rule and a garrison town where soldiers and locals had no common language.',
  'Glottolog 5.3; Chavacano is co-official in Zamboanga City.'),
 ('Tok Pisin', ['Category:Tok Pisin', 'Category:Papua New Guinea'],
  'An English-lexified creole and a national language of Papua New Guinea, which has more languages than any other country — Tok Pisin is how they talk to each other. It began on nineteenth-century plantations in Samoa and Queensland and came back with the labourers; its grammar is largely Austronesian and it now has first-language speakers, parliamentary debate and a newspaper.',
  'Glottolog 5.3; Tok Pisin is one of three official languages of Papua New Guinea.'),
 ('Bislama', ['Category:Bislama', 'Category:Vanuatu'],
  "Vanuatu's national language and the one thing shared across a country with more languages per head than anywhere on earth. Like Tok Pisin it came out of the Pacific labour trade, and its name is from bêche-de-mer, the sea cucumber trade that brought the ships.",
  "Glottolog 5.3; Bislama is the national language under Vanuatu's constitution."),
 ('Guianese Creole French', ['Category:French Guianese Creole', 'Category:French Guiana'],
  'A French-lexified creole of French Guiana, close to the Antillean creoles but with its own history, and spoken alongside Portuguese, Sranan, Hmong and a dozen Amerindian languages in one of the most linguistically mixed places in the Americas.',
  'Glottolog 5.3; French Guiana is a French department and recognises only French.'),
 ('Vlax Romani', ['Category:Romani language', 'Category:Romani people'],
  'The largest Romani group, and the branch that spent centuries enslaved in Wallachia and Moldavia — Vlax is named for that, and the Romanian layer in its vocabulary dates from it. Romani as a whole is Indo-Aryan: its speakers left northwest India around a thousand years ago, and the language is the main evidence for where and when, because there is almost no written record of the journey.',
  'Glottolog 5.3; the Indo-Aryan origin was established by Rüdiger and Grellmann in the 1780s.'),
 ('Bishnupriya Manipuri', ['Category:Bishnupriya Manipuri', 'Category:Manipur'],
  'An Indo-Aryan language spoken in Manipur, Assam and Bangladesh, surrounded by the Sino-Tibetan Meitei that its name refers to — the two are unrelated and share a region and a religion. Its origin is disputed between an old Indo-Aryan settlement and a later migration.',
  'Glottolog 5.3; the origin question is unresolved in the literature.'),
 ('Dotyali', ['Category:Doti', 'Category:Nepal'],
  "A Pahari language of far-western Nepal, close to Kumaoni across the Indian border and recognised in Nepal's 2015 constitution among the languages of the nation. It is written in Devanagari and has almost no published literature.",
  "Glottolog 5.3; recognised in Schedule 1 of Nepal's 2015 Constitution."),
 ('Angika', ['Category:Angika', 'Category:Bihar'],
  'Spoken in eastern Bihar and Jharkhand around the old kingdom of Anga. It is close to Maithili and Magahi, is counted as Hindi in the census, and has campaigned unsuccessfully for a place in the Eighth Schedule alongside Maithili, which succeeded in 2003.',
  'Glottolog 5.3; the Angika inclusion campaign is documented in Indian parliamentary records.'),
 ('North-Central Talysh', ['Category:Talysh language', 'Category:Talysh people'],
  'A northwestern Iranian language of the Caspian coast, split between Azerbaijan and Iran and with no official standing in either. It is closer to the extinct Azari — the Iranian language spoken in Azerbaijan before Turkic arrived — than to anything now around it.',
  'Glottolog 5.3; UNESCO classes Talysh as vulnerable.'),

# ---- INDO-EUROPEAN DEEP PASS -------------------------------------------------------------
# 503 of Indo-European's 586 languages had no authored label. These are the ones anyone is likely
# to open, ranked by how many people edited their Wikipedia last month and by speaker count.
# FOUR-TUPLES: the fourth element is a SOURCE NOTE, rendered on the card. It names where the
# checkable claims come from — a constitution, an act, a dated reform, a classification — and does
# not dress general knowledge up as a citation. Where a claim is contested it says so in the text.
 ('Scots', ['Category:Scots language', 'Category:Scottish literature'],
  'The other language of lowland Scotland, descended from the Northumbrian Old English that crossed the border, not from Gaelic. It had a full literary standard before the union of crowns in 1603 and lost it afterwards, as printing moved to London and the written form was reabsorbed into English — which is why Scots today is often taken for an accent rather than the separate development it is. Burns wrote in it deliberately, a century after it had stopped being the language of record.',
  'Glottolog 5.3 treats Scots as a language distinct from English; the 2011 Scottish census counted self-reported ability, which is why figures vary so widely.'),
 ('Asturian-Leonese-Cantabrian', ['Category:Asturian language', 'Category:Asturias'],
  "The Romance of the Iberian northwest, spoken across Asturias, León and into Portugal as Mirandese. It kept Latin's initial f where Castilian dropped it — Asturian fíu against Spanish hijo — so it preserves a sound Spanish lost. Asturias has been legislating about its status for forty years without granting it co-official standing, and Mirandese, the same language across the Portuguese border, has been co-official there since 1999.",
  'Glottolog 5.3; the Mirandese statute is Portuguese Law 7/99.'),
 ('Moselle Franconian', ['Category:Luxembourgish language', 'Category:Luxembourg'],
  'A West Germanic dialect group that became a national language in one of its corners: Luxembourgish was made an official language of Luxembourg in 1984, alongside French and German, and is the only member of the group with a state behind it. The same speech continues across the borders into Germany and Belgium with no official standing at all, which is a clean demonstration that the line between a language and a dialect is drawn by governments.',
  "Glottolog 5.3; Luxembourg's language law of 24 February 1984."),
 ('Irish', ['Category:Irish language', 'Ogham inscription', 'Book of Kells'],
  'The first vernacular in Europe north of the Alps to be written extensively: Irish monks glossed their Latin manuscripts in Irish from the seventh century, and those glosses are the largest early record of any European language outside Latin and Greek. It is the first official language of Ireland and an official language of the European Union, and it is also the case that most of its daily speakers live in a handful of Gaeltacht districts along the west coast — constitutional status and community transmission are different things.',
  'Glottolog 5.3; Article 8 of the Constitution of Ireland; Irish became an EU official language on 1 January 2007.'),
 ('Haitian', ['Category:Haitian Creole', 'Category:Haiti'],
  'The most widely spoken creole language in the world, and one of very few with full official status: French-lexified, with a grammar owing much to the Gbe languages of West Africa, and spoken by essentially the entire population of Haiti while French is spoken by a minority. Its spelling was standardised phonemically in 1979, which is why written Haitian looks unlike French even where the words are the same — French *eau* is Haitian *dlo*.',
  'Glottolog 5.3; Haitian became co-official under the 1987 Constitution; the official orthography dates from 1979.'),
 ('Bavarian', ['Category:Bavarian language', 'Category:Bavaria'],
  'Spoken across Bavaria, Austria and South Tyrol by more people than speak Danish or Slovak, and treated as a dialect of German because that is what its speakers write. It has sound changes German does not — a distinct set of diphthongs and a two-way distinction in verbs German lost — and UNESCO lists it as vulnerable, which sits oddly beside a speaker count in the millions and is a fair illustration of how vitality assessments work.',
  "Glottolog 5.3; UNESCO Atlas of the World's Languages in Danger classes Bavarian as vulnerable."),
 ('Sicilian', ['Category:Sicilian language', 'Category:Sicily'],
  "The first Romance language in which a school of lyric poetry was written: the Sicilian School at Frederick II's court in the 1230s, which invented the sonnet. Dante praised it and then chose Florentine, and Sicilian's literary line stops there. Its vocabulary carries Greek, Arabic, Norman French and Spanish in layers that match the island's rulers, and it is grammatically distinct from Italian rather than a variant of it.",
  'Glottolog 5.3; the sonnet is attributed to Giacomo da Lentini of the Sicilian School.'),
 ('Continental Southern Italian', ['Category:Neapolitan language', 'Category:Naples'],
  "Neapolitan and the speech of southern mainland Italy — the language of a kingdom that lasted six centuries, and of a song tradition that carried it around the world. 'O Sole Mio is Neapolitan, not Italian. Like Sicilian it is a separate Romance development rather than an Italian dialect, and like Sicilian it is written far less than it is spoken.",
  'Glottolog 5.3; UNESCO classes Neapolitan as vulnerable.'),
 ('Lombard', ['Category:Lombard language', 'Category:Lombardy'],
  'Gallo-Italic: the Romance of the Po valley, closer in its sound history to French and Occitan than to standard Italian, because the Alps were less of a barrier than the Apennines. Milanese had a substantial written literature in the eighteenth and nineteenth centuries and lost it to the national standard after unification.',
  'Glottolog 5.3 places Lombard in Gallo-Italic; UNESCO classes it as definitely endangered.'),
 ('Piemontese', ['Category:Piedmontese language', 'Category:Piedmont'],
  'Also Gallo-Italic, and the language of the state that unified Italy — which then made Florentine the national language rather than its own. Piedmontese has a codified orthography, a body of literature and regional recognition, and no national status.',
  'Glottolog 5.3; recognised by Piedmont regional law 26/1990, later curtailed by the Constitutional Court.'),
 ('Corsican', ['Category:Corsican language', 'Category:Corsica'],
  'Closer to Tuscan than to the French that governs it — Corsica was Genoese until 1768 — which makes it one of the clearest cases of a language whose relatives and whose state are on opposite sides. It is taught in Corsican schools and has no official status in France, which recognises no regional language.',
  "Glottolog 5.3 places Corsican within Italo-Romance; France's Article 2 recognises only French."),
 ('Ladin', ['Category:Ladin language', 'Category:Dolomites'],
  'A Rhaetian language of five Dolomite valleys, co-official in South Tyrol and Trentino, with about thirty thousand speakers and a school system that teaches in three languages at once — Ladin, Italian and German. It survived because the valleys are hard to reach and because it was given legal protection early.',
  'Glottolog 5.3; co-official under the Autonomy Statute of Trentino-South Tyrol.'),
 ('Walloon', ['Category:Walloon language', 'Category:Wallonia'],
  'The Oïl language of southern Belgium, recognised as a regional language there since 1990 and spoken by far fewer people than that recognition suggests. It has a literature going back to the sixteenth century and a theatre tradition still running in Liège.',
  'Glottolog 5.3; recognised by the French Community of Belgium, decree of 1990.'),
 ('Aragonese', ['Category:Aragonese language', 'Category:Aragon'],
  'The Romance of the Pyrenean valleys of Aragon, once the language of a kingdom and now spoken by a few thousand people in the mountains north of Huesca. It sits between Castilian and Catalan and was pushed out of both writing and administration by the fifteenth century.',
  'Glottolog 5.3; UNESCO classes Aragonese as definitely endangered.'),
 ('Silesian', ['Category:Silesian language', 'Category:Upper Silesia'],
  'West Slavic, spoken in Upper Silesia, and the subject of a long argument in Poland about whether it is a language or a dialect of Polish — half a million people gave it as their home language in the 2011 census, and the Polish parliament has repeatedly declined to recognise it. Its vocabulary carries a heavy German layer from centuries of shared administration.',
  'Glottolog 5.3 treats Silesian as a language; the 2011 Polish census recorded 509,000 declaring it as a home language.'),
 ('Kashubian', ['Category:Kashubian language', 'Category:Kashubia'],
  'The last surviving Pomeranian language, spoken west of Gdańsk, and the only regional language with legal recognition in Poland. Its nearest relative, Slovincian, died in the twentieth century. Kashubian can be used as an auxiliary administrative language in several municipalities.',
  "Glottolog 5.3; Poland's Act on National and Ethnic Minorities and on Regional Language, 2005."),
 ('Rusyn', ['Category:Rusyn language', 'Category:Carpathian Ruthenia'],
  'East Slavic, spoken across the Carpathians in Slovakia, Poland, Ukraine, Serbia and Hungary, and recognised as a minority language in most of those — but not in Ukraine, where it is officially a dialect of Ukrainian. Its several written standards differ from one another, because each was made where it was recognised.',
  'Glottolog 5.3; recognised in Slovakia (1995 codification), Serbia (Vojvodina, official), Poland and Hungary.'),
 ('Western Armenian', ['Category:Western Armenian', 'Category:Armenian diaspora'],
  'One of the two standard Armenians, and the one that lost its homeland. Western Armenian was the language of the Armenian communities of Anatolia; after 1915 it survives in the diaspora — Lebanon, Syria, France, the United States, Argentina — with no state and no territory. UNESCO classes it as definitely endangered while Eastern Armenian is a state language.',
  'Glottolog 5.3; UNESCO Atlas classes Western Armenian as definitely endangered.'),
 ('Maithili', ['Category:Maithili language', 'Category:Tirhuta script'],
  "Thirty-odd million speakers in Bihar and southeastern Nepal, counted as a dialect of Hindi until 2003, when a constitutional amendment added it to India's Eighth Schedule after a long campaign. It has its own script, Tirhuta, and a literary tradition running back to Vidyapati in the fourteenth century, whose songs are still sung.",
  'Glottolog 5.3; added to the Eighth Schedule by the Constitution (Ninety-Second Amendment) Act, 2003.'),
 ('Eastern Panjabi', ['Category:Punjabi language', 'Category:Gurmukhi'],
  'The Punjabi of India, written in Gurmukhi — a script devised in the sixteenth century by the second Sikh Guru and used for the Guru Granth Sahib. Punjabi is the only major Indo-Aryan language with lexical tone, which it developed when its voiced aspirated consonants collapsed: the breathiness became pitch.',
  'Glottolog 5.3; the tone development is standard in descriptions of Punjabi phonology.'),
 ('Western Panjabi', ['Category:Shahmukhi', 'Category:Punjab, Pakistan'],
  'The Punjabi of Pakistan, written in Shahmukhi, a Perso-Arabic script — the same language as Indian Punjabi in a different alphabet, so a Lahore reader and an Amritsar reader who speak alike cannot read each other. It has more speakers than any other language of Pakistan and no official status there.',
  "Glottolog 5.3; Urdu and English are Pakistan's official languages under Article 251."),
 ('Fiji Hindi', ['Category:Fiji Hindi', 'Category:Indo-Fijians'],
  'What happened to the Awadhi and Bhojpuri of indentured labourers taken to Fiji from 1879: the regional varieties levelled into one new language, with Fijian and English words in it, diverging far enough from Standard Hindi that speakers of one need practice to follow the other. It is written in Devanagari and in Latin letters, and is a national language of Fiji.',
  "Glottolog 5.3; recognised in Fiji's 2013 Constitution alongside English and Fijian."),
 ('Mazanderani', ['Category:Mazandaran', 'Category:Caspian languages'],
  'A Caspian language of northern Iran, spoken by millions on the wet side of the Alborz mountains and written very little, because Persian occupies every formal register. It is northwestern Iranian and so is not a dialect of Persian, despite being surrounded by it.',
  'Glottolog 5.3 places Mazanderani in Caspian, within Northwestern Iranian.'),
 ('Gilaki', ['Category:Gilan', 'Category:Caspian languages'],
  'The other Caspian language, spoken in Gilan on the coast west of Mazandaran. Like its neighbour it retains features Persian changed, and like its neighbour it has no written standard and is losing children to Persian.',
  'Glottolog 5.3; UNESCO classes Gilaki as definitely endangered.'),
 ('Dimli', ['Category:Zaza language', 'Category:Dersim'],
  'Zazaki, spoken in eastern Turkey, and the object of a political argument: Kurdish nationalism counts it as Kurdish, and historical linguistics does not — it is northwestern Iranian and its closest relatives are the Caspian languages, hundreds of miles east. Both positions are held sincerely and the linguistic evidence points one way.',
  'Glottolog 5.3 places Zaza in Zaza-Gorani, separate from Kurdish; the classification follows the standard Iranian family literature.'),
 ('Central Alemannic', ['Category:Swiss German', 'Category:Alemannic German'],
  'Swiss German: the everyday spoken language of German-speaking Switzerland, at every level of society, while the written language is Standard German. This is diglossia in a wealthy modern state — a Swiss will speak dialect to a colleague and write to them in a language nobody there speaks — and it is why Swiss German is not endangered despite having almost no written form.',
  'Glottolog 5.3; the Swiss situation is the standard textbook case of medial diglossia.'),
 ('Eastern Low German', ['Category:Low German', 'Category:Plautdietsch'],
  "Low German did not undergo the High German consonant shift, which is why it is closer to Dutch and English than to the German above it — Low German *water* against Hochdeutsch Wasser. It was the language of the Hanseatic League and the written language of northern Europe's trade for three centuries before High German displaced it.",
  'Glottolog 5.3; recognised under the European Charter for Regional or Minority Languages in Germany.'),
 ('Zeeuws', ['Category:Zeelandic', 'Category:Zeeland'],
  'Zeelandic, spoken in the southwestern Dutch islands, between Dutch and West Flemish and counted officially as a dialect of Dutch. Its speakers petitioned for recognition as a regional language and were refused in 2005.',
  'Glottolog 5.3; the Dutch government declined regional-language status for Zeelandic in 2005.'),
 ('Ghanaian Pidgin English', ['Category:Ghanaian Pidgin English', 'Category:Ghana'],
  'An English-lexified contact language of Ghana with several million speakers and no official standing, used across ethnic lines in cities and universities and stigmatised in exactly the way contact languages usually are. Its grammar is West African and its vocabulary English.',
  "Glottolog 5.3; English is Ghana's sole official language."),
 ('Friulian', ['Category:Friulian language', 'Category:Friuli'],
  'A Rhaetian language of northeastern Italy with about half a million speakers and legal protection since 1999. Like Ladin and Romansh it preserves a Latin-derived Alpine Romance distinct from Italian, and unlike them it has a substantial modern literature.',
  'Glottolog 5.3; protected under Italian Law 482/1999 on historic linguistic minorities.'),
 ('Romansh', ['Category:Romansh language', 'Category:Graubünden'],
  'An official language of Switzerland since 1938, with about forty thousand speakers across five written varieties in the valleys of Graubünden. A unified written standard, Rumantsch Grischun, was constructed in 1982 and is resented in several valleys that prefer their own.',
  'Glottolog 5.3; Romansh became a Swiss national language by referendum in 1938 and an official language in 1996.'),
 ('Dhivehi', ['Category:Thaana', 'Category:Maldives'],
  'The language of the Maldives, Indo-Aryan and closest to Sinhala, written in Thaana — a script devised in the sixteenth century whose letters come from Arabic numerals and local numerals, written right to left, with vowels obligatory rather than optional. It replaced an earlier Indic script within a generation.',
  "Glottolog 5.3; Thaana's numeral-derived letterforms are documented in standard script references."),
 ('Western Balochi', ['Category:Balochi language', 'Category:Balochistan'],
  'A northwestern Iranian language spoken across Pakistan, Iran and Afghanistan — so, like Kurdish, a language whose territory is divided among states that each treat it as a minority. It is conservative enough to preserve Old Iranian sounds Persian lost, and it has three written traditions and no single standard.',
  'Glottolog 5.3; Balochi has no official status in any of the three states.'),
 ('Dari', ['Category:Dari language', 'Category:Afghanistan'],
  'The Persian of Afghanistan, one of two official languages there, written in Perso-Arabic. The name was made official in 1964 to assert an Afghan rather than an Iranian identity for the same language — a naming decision, not a linguistic one.',
  "Glottolog 5.3; the name Dari was adopted officially in Afghanistan's 1964 constitution."),

 ("English", ["Beowulf manuscript Nowell Codex", "Category:English inscriptions",
              "Lindisfarne Gospels Old English gloss"],
  "The Germanic language of a small island that ended up with more second-language speakers "
  "than any language has ever had. Its history is legible in its vocabulary: Old English core "
  "words, a Norse layer from settlement (they, egg, sky, knife), a French layer of government "
  "and cuisine from 1066, and a Latin and Greek layer built by scholars — which is why English "
  "has pairs like kingly, royal and regal meaning almost the same thing. Its spelling froze "
  "around the time printing arrived and the pronunciation kept moving, which is why 'knight' "
  "is spelled the way it was said in 1400."),
 ("Spanish", ["Cantar de mio Cid manuscript", "Glosas Emilianenses",
              "Category:Spanish inscriptions"],
  "Castilian began as a border dialect in the north of Iberia and became the language of an "
  "empire in a single lifetime. Nebrija dedicated the first grammar of any modern European "
  "language to Isabella in 1492 and told her that language is the instrument of empire; she is "
  "said to have asked what use it was, since she already spoke it. Today its standard is set "
  "jointly by twenty-three academies rather than by Madrid, because most of its speakers are "
  "American."),
 ("German", ["Codex Argenteus Wulfila", "Luther Bible 1534 title page",
             "Category:German inscriptions"],
  "A language with no single centre. It was written in a dozen chancery standards until "
  "Luther's Bible pulled them towards one, and it still has three national standards and a "
  "dialect continuum so deep that a Swiss and a north German may not understand each other's "
  "speech at all. Its grammar keeps four cases and three genders that its cousins dropped, and "
  "its habit of building words by joining them lets it name things other languages need a "
  "phrase for."),
 ("French", ["Serments de Strasbourg", "Chanson de Roland manuscript Oxford",
             "Category:French inscriptions"],
  "The first Romance language to be written as a language in its own right rather than as "
  "misspelled Latin: the Strasbourg Oaths of 842 were set down in it because neither side would "
  "swear in Latin. It is also the most deliberately governed of the major languages — an academy "
  "since 1635, an ordinance since 1539 requiring it in law, and a long habit of legislating "
  "against loanwords. Its spelling preserves consonants that stopped being pronounced six "
  "hundred years ago."),
 ("Italian", ["Divina Commedia manuscript", "Placiti Cassinesi",
              "Category:Italian inscriptions"],
  "The only major European language whose standard was chosen from a literary corpus rather "
  "than a capital city: Florentine, because Dante, Petrarch and Boccaccio wrote in it. At "
  "unification in 1861 perhaps one person in forty in the new kingdom spoke it; the rest spoke "
  "languages as different from it as Spanish is. Television did more to spread it in twenty "
  "years than schooling had in a century."),
 ("Japanese", ["Kojiki manuscript", "Man'yoshu manuscript",
               "Genji Monogatari emaki", "Category:Japanese calligraphy"],
  "A language that borrowed a writing system built for a completely unrelated language and "
  "then had to solve it. Chinese characters carry Japanese meanings and two or more readings "
  "each — one from Chinese, one native — and around them run two syllabaries, hiragana for "
  "grammar and katakana for foreign words. All three appear in the same sentence. The "
  "consequence is a language whose writing records its own history of contact on every line."),
 ("Russian", ["Ostromir Gospels", "Novgorod birch bark letters",
              "Category:Russian inscriptions"],
  "Written in an alphabet made for a different Slavic language: Cyrillic was devised for Old "
  "Church Slavonic and inherited. Peter the Great redrew the letters in 1708 to look less "
  "ecclesiastical, and the 1918 reform dropped four of them. The birch-bark letters dug out of "
  "Novgorod — shopping lists, love notes, a child's alphabet practice — are among the few "
  "records anywhere of how ordinary medieval people actually wrote."),
 ("Polish", ["Book of Henrykow", "Psalter of Florian",
             "Category:Polish inscriptions"],
  "Kept alive in print for over a century while the state that spoke it did not exist. Its "
  "oldest recorded sentence, in the Book of Henryków around 1270, is a man telling his wife to "
  "rest while he grinds the corn. Its spelling uses digraphs — sz, cz, rz — where Czech chose "
  "diacritics, which is why the two closely related languages look so unlike on the page."),
 ("Western Farsi", ["Shahnameh manuscript", "Behistun inscription",
                    "Category:Persian calligraphy"],
  "A language that survived conquest by becoming the prestige language of the conquerors' "
  "successors. Persian returned to literary use two centuries after the Arab conquest, written "
  "in Arabic letters with four added, and for five hundred years was the language of "
  "administration and poetry from the Balkans to Bengal. Ferdowsi wrote the Shahnameh partly to "
  "prove it could carry an epic without Arabic vocabulary."),
 ("Modern Hebrew", ["Dead Sea Scrolls Isaiah", "Gezer calendar",
                    "Category:Hebrew manuscripts"],
  "The only language to stop being spoken and start again. Hebrew held on for seventeen "
  "centuries in prayer, law and correspondence with no native speakers, and then acquired them: "
  "Ben-Yehuda raised his son in Hebrew alone in the 1880s, and within seventy years it was the "
  "everyday language of a state. It is not the Hebrew of the Bible — the sound system took a "
  "great deal from the European languages of its first revivalists."),
 ("Dutch", ["Hebban olla vogala", "Statenbijbel title page",
            "Category:Dutch inscriptions"],
  "Sits exactly between English and German and shows what English might have looked like "
  "without 1066: Germanic vocabulary, Germanic word order, and no French layer of governance. "
  "Its standard is set jointly by the Netherlands and Belgium so that neither country decides "
  "alone, and its oldest sentence is a scribe in Rochester testing a pen."),
 ("Ukrainian", ["Peresopnytsia Gospel", "Kobzar Shevchenko",
                "Category:Ukrainian inscriptions"],
  "Banned from print by imperial decree in 1876 and from the stage as well; the language "
  "survived in villages, in song, and in books printed abroad. Shevchenko's Kobzar of 1840 gave "
  "it a literary standard built out of the spoken language rather than out of Church Slavonic, "
  "which is the main reason it reads as a separate language from Russian rather than a "
  "provincial version of it."),
 ("Standard Indonesian", ["Kedukan Bukit inscription", "Sumpah Pemuda 1928",
                          "Category:Indonesian language"],
  "A national language chosen precisely because it belonged to almost nobody. At independence "
  "Javanese had far more speakers, but adopting it would have made one island's language the "
  "state's; Malay was the trade language of the archipelago and the first language of a small "
  "minority. It is now spoken by most Indonesians and native to few of them — the clearest case "
  "anywhere of a national language adopted rather than inherited."),
 ("Turkish", ["Orkhon inscriptions", "Ottoman Turkish manuscript calligraphy",
              "Category:Turkish inscriptions"],
  "The language with the sharpest documented break in modern history. In 1928 the script "
  "changed from Arabic to Latin in a matter of months, with Atatürk teaching the new letters at "
  "public blackboards; from 1932 a language commission replaced much of the Arabic and Persian "
  "vocabulary with Turkic coinages. The result is that a Turkish speaker today needs training "
  "to read a newspaper from 1920 — both the letters and the words have changed."),
 ("Vietnamese", ["Chu Nom manuscript", "Truyen Kieu manuscript",
                 "Category:Vietnamese language"],
  "Written three ways in a thousand years. Chinese characters first, then chữ Nôm — characters "
  "invented to fit Vietnamese, one of the few writing systems ever built by adapting another to "
  "an unrelated language — and finally the Latin quốc ngữ devised by Portuguese missionaries and "
  "made official in 1945. It is a tonal language with six tones, and quốc ngữ marks every one, "
  "which is why written Vietnamese carries so many diacritics."),
 ("Swedish", ["Rok runestone", "Gustav Vasa Bible",
              "Category:Swedish inscriptions"],
  "Has more runic inscriptions behind it than any other language — Sweden holds the majority of "
  "the world's runestones. Modern Swedish and Norwegian and Danish are close enough that their "
  "speakers often read each other without study; what separates them most is pronunciation and "
  "spelling convention rather than grammar. Its Wikipedia is one of the largest in the world and "
  "most of it was written by a bot."),
 ("Czech", ["Codex Gigas", "Kralice Bible",
            "Category:Czech inscriptions"],
  "Gave Europe the háček. Jan Hus proposed around 1412 that a mark above a letter should replace "
  "clusters of consonants, and the idea spread from Czech into Slovak, Slovene, Croatian, "
  "Latvian, Lithuanian and beyond — one of the few orthographic inventions that can be traced to "
  "a named person and a date. Czech nearly lost its written life under Habsburg German before "
  "the National Revival rebuilt it in the nineteenth century."),
 ("Thai", ["Ram Khamhaeng inscription", "Thai manuscript samut khoi",
           "Category:Thai inscriptions"],
  "An abugida in which vowels are written before, after, above or below the consonant they "
  "follow in speech, so reading order and speaking order are not the same. Thai is written "
  "without spaces between words, has five tones and forty-four consonant letters for twenty-one "
  "consonant sounds — the surplus preserving distinctions that existed in the Indic languages "
  "the letters were borrowed from."),
 ("Bulgarian", ["Codex Zographensis", "Preslav inscription",
                "Category:Bulgarian inscriptions"],
  "The first Slavic language written down, and the ancestor of the liturgical Old Church "
  "Slavonic that carried Cyrillic to Russia and Serbia. It then did something no other Slavic "
  "language did: it lost almost all of its noun cases and grew a definite article stuck to the "
  "end of the word, which makes it grammatically closer to Romanian and Albanian than to Russian."),
 ("Danish", ["Jelling stones", "Codex Holmiensis",
             "Category:Danish inscriptions"],
  "Famous among its neighbours for being hard to hear. Danish has reduced and swallowed "
  "consonants far more than Swedish or Norwegian, so it is written much like them and sounds "
  "very little like them; Danish children acquire vocabulary measurably later than Norwegian "
  "children, which linguists attribute to how few consonants survive in speech. The Jelling "
  "stone of about 965 is called Denmark's birth certificate."),
 ("Norwegian", ["Codex Frisianus", "Category:Norwegian inscriptions",
                "Category:Norwegian language"],
  "One language with two official written standards and no official spoken one. Bokmål grew out "
  "of the Danish used in Norway for four centuries; Nynorsk was assembled in the 1850s by Ivar "
  "Aasen, who walked the country collecting dialects and built a written language out of what he "
  "found. Both are taught; neither is a pronunciation, and Norwegians are unusually free to "
  "speak their own dialect in any setting."),
 ("Slovak", ["Category:Slovak inscriptions", "Category:Slovak language"],
  "Standardised twice, both times by choosing a different dialect. Bernolák built one standard "
  "on western Slovak in 1787; Štúr replaced it with a central Slovak standard in the 1840s "
  "because it was further from Czech and closer to what most people spoke. Slovak and Czech "
  "remain mutually intelligible enough that both were used interchangeably on Czechoslovak "
  "television."),
 ("Urdu", ["Urdu nastaliq calligraphy", "Diwan-e-Ghalib manuscript",
           "Category:Urdu language"],
  "Grammatically the same language as Hindi and, in speech, largely the same vocabulary; the "
  "two separate in script, in register and in what they borrow from. Urdu is written in the "
  "flowing nastaʿlīq style of the Perso-Arabic script, which slopes down to the left and is so "
  "hard to typeset that Urdu newspapers were hand-written by calligraphers into the 1980s."),
 ("Malayalam", ["Malayalam palm leaf manuscript", "Category:Malayalam script",
                "Category:Malayalam language"],
  "Has the largest consonant-cluster inventory of the Indian scripts and a reputation for the "
  "most complex ligatures. It is also the language of a state with near-universal literacy, and "
  "the Malayalam word for the language, script and people is the same. Its name is a palindrome "
  "in Latin letters."),
 ("Telugu", ["Telugu palm leaf manuscript", "Category:Telugu script",
             "Category:Telugu inscriptions"],
  "Called the Italian of the East by nineteenth-century Europeans because so many of its words "
  "end in a vowel. Dravidian, not Indo-European, though it has taken a great deal of Sanskrit "
  "vocabulary; its script and Kannada's come from a common ancestor and still look alike enough "
  "that readers of one can often sound out the other."),
 ("Georgian", ["Bir el Qutt inscriptions", "Category:Georgian manuscripts",
               "Category:Georgian calligraphy"],
  "Written in an alphabet shared with no other language, in three historical forms, all of them "
  "in Unicode. Georgian has no capital letters, no grammatical gender, and consonant clusters "
  "that other languages break up with vowels — gvprtskvnis, 'you peel us', has eight consonants "
  "in a row. Its language family, Kartvelian, has four members and no demonstrated relatives."),
 ("Belarusian", ["Skaryna Bible", "Category:Belarusian language"],
  "Has two competing spellings, and choosing one is a political act. The official orthography "
  "follows a 1933 Soviet reform that moved the language closer to Russian; taraškievica, named "
  "for the grammarian who codified it in 1918, is used by much of the diaspora and independent "
  "press. Belarusian Wikipedia exists in both, as two separate encyclopedias."),
 ("Halh Mongolian", ["Mongolian script manuscript", "Category:Mongolian script",
                     "Category:Mongolian language"],
  "Written vertically, top to bottom in lines running left to right — the only major script that "
  "does. The traditional Mongolian alphabet came from Uyghur, which came from Syriac, which is "
  "why a script written down the page descends from one written right to left. Mongolia switched "
  "to Cyrillic in the 1940s and has legislated a return to the vertical script."),
 ("Kazakh", ["Category:Kazakh language", "Category:Kazakh people"],
  "Has changed alphabet three times in a century — Arabic to Latin in 1929, Latin to Cyrillic in "
  "1940, and Cyrillic back to Latin on a schedule now running to 2031. Each change cut a "
  "generation off from what the previous one had printed, which is the recurring cost of script "
  "reform and the reason it is always contested."),
 ("Afrikaans", ["Category:Afrikaans language", "Category:Afrikaans literature"],
  "The youngest Germanic language with a state standing, grown from seventeenth-century Dutch in "
  "the Cape and shaped by Malay, Khoe and Portuguese contact. Its grammar is radically "
  "simplified — no verb conjugation for person, no grammatical gender — and it was first written "
  "in Arabic script, in madrasas of the Cape Malay community, decades before it was written in "
  "Latin letters."),
 ("Kannada", ["Halmidi inscription", "Category:Kannada script",
              "Category:Kannada inscriptions"],
  "Has one of the longest continuous inscriptional records of any living language — tens of "
  "thousands of stone and copper-plate inscriptions, more than any other Indian language. The "
  "Halmidi inscription of about 450 is the oldest; the language has changed enough since that "
  "it needs translating for modern readers."),
 ("Serbian-Croatian-Bosnian", ["Miroslav Gospel", "Category:Serbian inscriptions",
                               "Category:Croatian inscriptions"],
  "One language by every linguistic measure and four by every political one. Serbian, Croatian, "
  "Bosnian and Montenegrin are mutually intelligible in full; they differ in script — Serbian "
  "uses both Cyrillic and Latin, Croatian only Latin — in vocabulary preferences, and in which "
  "capital sets the standard. Glottolog files them as a single language, which is a linguistic "
  "judgement and not a political one."),
 ("Egyptian Arabic", ["Category:Egyptian Arabic", "Category:Arabic calligraphy"],
  "The most widely understood spoken Arabic, because Egypt made the films and the music that the "
  "rest of the Arab world watched. It is a spoken language that is written mostly in informal "
  "registers — comics, subtitles, social media, song — while Standard Arabic holds the formal "
  "page, which makes it one of the clearest living examples of diglossia."),
 ("Northern Uzbek", ["Category:Uzbek language", "Category:Uzbek people"],
  "Turkic, with more Persian in it than its relatives have, because it grew up in the cities of "
  "Transoxiana alongside Tajik. Like Kazakh it has cycled through Arabic, Latin and Cyrillic and "
  "is going back to Latin; unlike Kazakh, Uzbek did so in 1993 and the transition is still "
  "incomplete, so signs in Tashkent appear in both."),
 ("North Azerbaijani", ["Category:Azerbaijani language", "Nizami Ganjavi manuscript"],
  "Split by a border since 1828. North Azerbaijani is written in Latin letters in Azerbaijan; "
  "South Azerbaijani, with more speakers, is written in Arabic script in Iran. They are the same "
  "language and their readers cannot read each other's books."),
 ("Eastern Armenian", ["Matenadaran Armenian manuscript", "Category:Armenian manuscripts",
                       "Category:Armenian inscriptions"],
  "An alphabet made for one language and used by no other. Mesrop Mashtots devised it around "
  "405 to put scripture into Armenian, and the translation programme that followed was so "
  "thorough that several Greek and Syriac works survive only in Armenian. The language has two "
  "standards — eastern, a state language in Armenia, and western, which lost its homeland in "
  "1915 and is now classed as endangered."),
 ("Northern Tosk Albanian", ["Category:Albanian language", "Meshari Buzuku"],
  "The only surviving member of its branch of Indo-European, with no close relatives at all. "
  "It kept enough of its own vocabulary through Latin, Slavic, Greek and Turkish contact to be "
  "identifiable, and its oldest book is a 1555 missal. Standard Albanian is built on Tosk, the "
  "southern variety, though Gheg has as many speakers."),
 ("Central Kurdish", ["Category:Kurdish language", "Category:Kurdish people"],
  "Written in two scripts in two countries by speakers of two varieties: Sorani in Arabic "
  "letters in Iraq and Iran, Kurmanji in Latin letters in Turkey and Syria. For most of the "
  "twentieth century publishing in it was restricted or banned across several of those states, "
  "and its standardisation is still unfinished as a result."),
 ("Nepali", ["Category:Nepali language", "Category:Nepal manuscripts"],
  "The state language of Nepal and one of the languages of Indian Sikkim and Darjeeling, written "
  "in Devanagari and closely related to Hindi. Nepal holds over a hundred languages from four "
  "different families in an area the size of England, which makes it one of the densest "
  "linguistic regions in Asia; Nepali is the one that carries between them."),
 ("Sinhala", ["Category:Sinhala script", "Category:Sinhala language"],
  "An Indo-European language at the southern tip of a Dravidian-speaking region, brought to Sri "
  "Lanka around 500 BCE and separated from its relatives ever since. Its script is rounded "
  "because it was written on palm leaf, where a straight stroke splits the fibre, and it has one "
  "of the largest sets of ligatures of any living script."),
 ("Lithuanian", ["Category:Lithuanian language", "Mazvydas Catechism"],
  "The most conservative living Indo-European language: it keeps case endings, dual number and "
  "pitch accent that Sanskrit's other cousins lost, and comparative linguists use it as a "
  "control. Its first book was printed in 1547, and for forty years from 1864 printing "
  "Lithuanian in Latin letters was banned in the Russian Empire — books were printed in Prussia "
  "and smuggled in by people known as book carriers."),
 ("Slovenian", ["Freising manuscripts", "Category:Slovene language"],
  "Keeps the dual — a separate grammatical number for exactly two — which almost every other "
  "European language dropped. It also has one of the steepest dialect gradients in Europe, with "
  "seven dialect groups and around fifty dialects among two million speakers, some of them not "
  "mutually intelligible."),
 ("Kirghiz", ["Category:Kyrgyz language", "Category:Kyrgyz people"],
  "Carries the Manas, an oral epic of around half a million lines — by most counts the longest "
  "in the world, twenty times the Odyssey — memorised and performed by reciters called "
  "manaschy. It was not written down until the nineteenth century and no two performances are "
  "the same."),
 ("Tajik", ["Category:Tajik language", "Category:Tajik people"],
  "Persian written in Cyrillic. Tajik and Iranian Persian are the same language with different "
  "alphabets and a century of separate vocabulary, which means a Tajik reader cannot follow a "
  "Tehran newspaper without learning a new script for their own language."),
 ("Standard Malay", ["Kedukan Bukit inscription", "Category:Jawi script",
                     "Category:Malay language"],
  "The trade language of maritime Southeast Asia for a thousand years, written in an Indic "
  "script, then in the Arabic-based Jawi, then in Latin letters. Jawi is still taught and still "
  "official in Brunei and used on signage in Malaysia — one of the few places where a language's "
  "older script survives alongside its newer one in public life."),
 ("Burmese", ["Myazedi inscription", "Category:Burmese script",
              "Category:Burmese manuscripts"],
  "Its round letters come from writing on palm leaf, where a straight line tears along the "
  "grain. The Myazedi inscription of 1113 carries the same text in Burmese, Pali, Mon and Pyu, "
  "and is what allowed Pyu — otherwise unknown — to be read at all. Burmese is written without "
  "spaces between words."),
 ("Nyanja", ["Category:Chewa language", "Category:Malawi"],
  "Known as Chichewa in Malawi and Chinyanja in Zambia, one language under two national names — "
  "a common pattern in Africa, where colonial borders cut through speech communities and each "
  "state then standardised its own side."),
 ("Igbo", ["Category:Igbo language", "Category:Nsibidi", "Category:Igbo culture"],
  "Written now in Latin letters, but the region has an older graphic system: nsibidi, a body of "
  "signs used on cloth, skin and walls, which encodes meaning without encoding sound. Igbo's "
  "tone is lexical, and the standard orthography marks it — without the marks, a great many "
  "words are ambiguous on the page."),
 ("Wolof", ["Category:Wolof language", "Category:Senegal"],
  "The language most people in Senegal actually use, in a country whose official language is "
  "French. It is written in Latin letters officially and in Wolofal, an Arabic script, in "
  "religious and popular use — so the language has a state orthography and a much older "
  "vernacular one that most of its readers were never taught in school."),
 ("Shona", ["Great Zimbabwe", "Category:Shona language"],
  "Its speakers built Great Zimbabwe, whose stone walls were long attributed by colonial "
  "archaeology to anyone but them. Shona has a five-vowel system, lexical tone, and a "
  "standardised orthography assembled in 1931 from several distinct varieties — which means the "
  "written language is nobody's exact dialect."),
 ("Tigrinya", ["Category:Tigrinya language", "Category:Ethiopic manuscripts"],
  "Written in the Ethiopic syllabary it shares with Amharic, and closer than Amharic is to "
  "Ge'ez, their common ancestor. It is a state language on both sides of the "
  "Eritrea–Ethiopia border and one of the few Semitic languages outside Arabic and Hebrew with "
  "millions of speakers and a national standing."),
 ("Sindhi", ["Shah Jo Risalo manuscript", "Category:Sindhi language"],
  "Written in Arabic script in Pakistan and Devanagari in India — the same language, two "
  "scripts, one border. Its Perso-Arabic alphabet has 52 letters, the largest of any, because "
  "Sindhi has sounds Arabic does not and each needed a letter built for it."),
 ("Northern Pashto", ["Category:Pashto language", "Khushal Khan Khattak manuscript"],
  "Has retroflex consonants and a case system that Persian, its neighbour and long-time "
  "administrative rival, does not — Pashto is Iranian but has taken structure from its Indic "
  "neighbours. Its Arabic-based alphabet adds letters for sounds no other language using that "
  "script needs."),
 ("Yue Chinese", ["Category:Cantonese", "Category:Chinese calligraphy"],
  "Preserves final consonants and a tone system that Mandarin lost, which is why classical "
  "Chinese poetry rhymes better read in Cantonese than in Mandarin. It has its own written "
  "vernacular using characters that exist for no other variety, mostly created in Hong Kong, "
  "and is one of the few Chinese languages with a substantial written form of its own speech."),
 ("Min Nan Chinese", ["Category:Hokkien", "Peh-oe-ji romanization"],
  "Written in Latin letters by Presbyterian missionaries and their converts from the 1830s: "
  "Pe̍h-ōe-jī gave Taiwanese a full romanised literature, including a newspaper that ran for "
  "sixty years, at a time when writing a Chinese language in an alphabet was almost unheard of. "
  "Min Nan split from the rest of Chinese earlier than any other branch."),
 ("Wu Chinese", ["Category:Shanghainese", "Category:Wu Chinese"],
  "The language of Shanghai and of a region that held the largest concentration of publishing in "
  "China. Wu keeps a three-way voicing distinction in its consonants that Mandarin reduced to "
  "two, and its speaker numbers are falling fast among children as Mandarin becomes the only "
  "language of schooling."),
 ("Uighur", ["Category:Uyghur language", "Turfan manuscripts"],
  "Written in five scripts across its history — Old Turkic runes, Sogdian-derived Old Uyghur, "
  "Arabic, Latin and Cyrillic — and today in a reformed Arabic alphabet that marks every vowel, "
  "unusually for that script. The Turfan manuscripts, dug out of the Taklamakan, preserve "
  "Buddhist, Manichaean and Christian texts in it side by side."),
 # ---- Indo-European batch 3: the largest languages in the family that still had no
 # label. The top of this list is bigger than most national languages of Europe.

 ("Bhojpuri", ["Category:Bhojpuri-language films", "Bhojpuri language"],
  "Fifty-two million speakers and no state: Bhojpuri is spoken across eastern Uttar Pradesh and "
  "western Bihar, is counted under Hindi by the Indian census, and has been petitioning for "
  "recognition in the Eighth Schedule since the 1960s. It travelled further than almost any "
  "Indian language — indentured labourers carried it to Mauritius, Fiji, Trinidad, Guyana and "
  "Suriname, where its descendants are now separate languages. Its film industry, based in Patna "
  "and Mumbai, releases more than a hundred titles a year.",
  "Census of India 2011; Ethnologue 2024 for the diaspora varieties."),
 ("Chhattisgarhi", ["Category:Chhattisgarh culture", "Chhattisgarhi language"],
  "The language of the Chhattisgarh plain, spoken by about sixteen million people and treated by "
  "the census as a dialect of Hindi — a classification its speakers have contested since the "
  "state was created in 2000. It has a rich oral epic tradition, the Pandavani, in which the "
  "Mahabharata is performed by a single singer with a tambura.",
  "Census of India 2011."),
 ("Haryanvi", ["Category:Culture of Haryana", "Haryanvi language"],
  "Spoken across Haryana and into Delhi by some fourteen million people, and known outside the "
  "region mainly through the folk song and the wrestling akhara. Like most of the Hindi belt's "
  "large languages it is returned as Hindi at the census, so its real extent is inferred rather "
  "than counted.",
  "Census of India 2011, which returns Haryanvi under Hindi."),
 ("Chittagonian", ["Category:Chittagong", "Chittagonian language"],
  "Thirteen million speakers in and around Chattogram, and mutually unintelligible with the "
  "Bengali it is officially a dialect of — the gap is about that between Portuguese and Spanish. "
  "Bangladesh has no separate census category for it.",
  "Ethnologue 2024; Bangladesh Bureau of Statistics 2022 counts it within Bengali."),
 ("Southern Pashto", ["Category:Pashto manuscripts", "Category:Kandahar"],
  "The Kandahar variety, and the one on which literary Pashto's spelling was originally based. "
  "Pashto has a written tradition going back to the sixteenth century and a national poet, "
  "Khushal Khan Khattak, who wrote some forty-five thousand couplets while imprisoned by the "
  "Mughals.",
  "Ethnologue 2024; no Afghan census since 1979, so all figures are projections."),
 ("Malvi", ["Category:Malwa", "Malvi language"],
  "Spoken on the Malwa plateau of Madhya Pradesh by about ten million people. Rajasthani in its "
  "affiliation but administratively inside a Hindi-speaking state, it is one of the larger "
  "languages that the Indian census does not name.",
  "Census of India 2011, under Hindi; Ethnologue 2024 for the separate estimate."),
 ("Dhundari", ["Category:Jaipur", "Dhundari language"],
  "The Rajasthani of the Jaipur region, about nine and a half million speakers. Its literary "
  "record begins with the Ashtak of the sixteenth-century poet Sant Dadu Dayal.",
  "Ethnologue 2024."),
 ("Bagheli", ["Category:Rewa, Madhya Pradesh", "Bagheli language"],
  "Eight million speakers in the Baghelkhand region of Madhya Pradesh and Uttar Pradesh, in the "
  "band between Awadhi and Chhattisgarhi where the Hindi belt's varieties shade into each other "
  "with no sharp line anywhere.",
  "Ethnologue 2024."),
 ("Sadri", ["Category:Jharkhand", "Sadri language"],
  "A lingua franca rather than a mother tongue for most of its seven million speakers: Sadri is "
  "what Munda, Dravidian and Indo-Aryan communities in Jharkhand and the Chotanagpur plateau use "
  "with each other, and what tea-garden workers taken to Assam in the nineteenth century use "
  "among themselves.",
  "Census of India 2011; Ethnologue 2024."),
 ("Central Pashto", ["Category:Pashto", "Category:Waziristan"],
  "The Waziri and Bannu group, between the Kandahar and Peshawar standards. Pashto's three main "
  "varieties differ mainly in how they treat the retroflex consonants, and speakers name them by "
  "that: the soft, the hard, and the middle.",
  "Ethnologue 2024."),
 ("Lambadi", ["Category:Banjara", "Category:Banjara people"],
  "The language of the Banjara, once the salt and grain carriers of the Deccan, whose caravans "
  "supplied Mughal and Maratha armies. It is Rajasthani in origin and is now spoken across "
  "Telangana, Karnataka, Maharashtra and Andhra Pradesh — a thousand kilometres from where its "
  "grammar comes from.",
  "Census of India 2011."),
 ("Mewati", ["Category:Mewat", "Mewati language"],
  "Spoken in Mewat, on the Haryana–Rajasthan border, by about five million people, most of them "
  "Meo Muslims. Its oral epic, the Pandun ka Kada, is a Mahabharata retold with Meo heroes.",
  "Ethnologue 2024."),
 ("Merwari", ["Category:Ajmer", "Marwari language"],
  "One of the Marwari group of Rajasthan, around Ajmer and Merwara. Marwari as a whole has some "
  "of the oldest surviving vernacular prose in North India — merchant account books and bardic "
  "chronicles from the fifteenth century onward.",
  "Ethnologue 2024."),
 ("Bhili", ["Category:Bhil", "Category:Bhil people"],
  "The language of the Bhil, the largest tribal population in India, spread across the hills "
  "where Gujarat, Rajasthan, Maharashtra and Madhya Pradesh meet. It is Indo-Aryan, not "
  "Munda — the Bhil adopted an Indo-Aryan language long ago and their earlier one is unrecoverable.",
  "Census of India 2011."),
 ("Eastern Balochi", ["Category:Balochi language", "Category:Balochistan"],
  "Balochi is an Iranian language whose speakers live mostly in Pakistan, and whose closest "
  "relatives are the languages of the Caspian coast fifteen hundred kilometres north — evidence "
  "of a migration that oral tradition remembers and that history does not record.",
  "Pakistan Census 2023; Korn, Towards a Historical Grammar of Balochi (2005)."),
 ("Garhwali", ["Category:Garhwal division", "Garhwali language"],
  "Spoken in the Garhwal Himalaya, about three million people, in the Central Pahari group with "
  "Kumaoni. Its folk theatre, the Ramman of Saloor Dungra, is on UNESCO's intangible heritage "
  "list.",
  "Census of India 2011."),
 ("Kumaoni", ["Category:Kumaon division", "Kumaoni language"],
  "The other Central Pahari language, across the ridge from Garhwali in the Kumaon hills. Both "
  "are losing speakers fast to Hindi as hill villages empty toward the plains.",
  "Census of India 2011; UNESCO Atlas of the World's Languages in Danger lists it vulnerable."),
 ("Hazaragi", ["Category:Hazara people", "Category:Hazarajat"],
  "The Persian of the Hazara of central Afghanistan, with a layer of Mongolic and Turkic "
  "vocabulary that no other Persian variety has. Its speakers are Shia in a mostly Sunni "
  "country and have been persecuted for it repeatedly, most severely under the Taliban in 1998 "
  "and again after 2021.",
  "Ethnologue 2024."),
 ("Dogri", ["Category:Dogri language", "Category:Jammu"],
  "The language of Jammu, recognised in the Eighth Schedule of the Indian constitution in 2003 "
  "after a campaign lasting decades. It was written in Takri, a script related to Sharada, and "
  "is now written in Devanagari.",
  "Census of India 2011; Eighth Schedule, Constitution (Ninety-second Amendment) Act 2003."),
 ("Cameroon Pidgin", ["Category:Cameroon", "Cameroonian Pidgin English"],
  "An English-lexifier creole spoken across anglophone Cameroon and well beyond it, in a country "
  "whose two official languages are French and English and whose most widely understood language "
  "is neither. Also called Kamtok.",
  "Ethnologue 2024."),
 ("Rohingya", ["Category:Rohingya people", "Category:Hanifi Rohingya script"],
  "Closest to Chittagonian, spoken by the Rohingya of northern Rakhine State and by the very "
  "large refugee population in Bangladesh. It has its own alphabet, Hanifi Rohingya, devised in "
  "the 1980s and encoded in Unicode in 2018 — one of the few scripts created in living memory "
  "and adopted by a whole community.",
  "Ethnologue 2024; Unicode 11.0 (2018) for the Hanifi Rohingya block."),
 ("Northern Luri", ["Category:Lurs", "Category:Lorestan Province"],
  "Spoken in the Zagros by the Lur, and close enough to Persian that Iran treats it as a dialect "
  "and distinct enough that its speakers do not.",
  "Ethnologue 2024."),
 ("Domari", ["Category:Dom people", "Domari language"],
  "The Indo-Aryan language of the Dom, spread across the Middle East from Egypt to Iran. It is "
  "not a dialect of Romani but its parallel: two separate migrations out of India, one west "
  "through Persia into the Levant, one further into Europe.",
  "Matras, A Grammar of Domari (2012)."),
 ("Emiliano", ["Category:Emilia-Romagna", "Category:Emilian language"],
  "Gallo-Italic, spoken across Emilia, and structurally closer to French and Occitan than to the "
  "Tuscan that became standard Italian. Bologna, Modena and Parma each have their own form of it.",
  "ISTAT 2015 language-use survey."),
 ("Romagnol", ["Category:Romagna", "Category:Romagnol language"],
  "The other half of Emilia-Romagna's pair, spoken from Rimini to Ravenna and in San Marino, "
  "where it is the historic language of the oldest surviving republic in the world.",
  "ISTAT 2015 language-use survey."),
 ("Kabuverdianu", ["Category:Cape Verdean culture", "Category:Cape Verde"],
  "The oldest living creole in the world — Portuguese-lexifier, formed on the uninhabited Cape "
  "Verde islands in the fifteenth century, the first place in the Atlantic where a creole "
  "society was made from nothing. Everyone in Cape Verde speaks it; Portuguese is the language "
  "of the state.",
  "Instituto Nacional de Estatística de Cabo Verde 2021 census."),
 ("Swabian", ["Category:Swabia", "Category:Swabian German"],
  "An Alemannic dialect of the southwest, and the object of a regional slogan — Wir können alles. "
  "Außer Hochdeutsch, we can do everything except standard German — that a state government "
  "actually used in its advertising.",
  "Ethnologue 2024."),
 ("Shina", ["Category:Gilgit-Baltistan", "Shina language"],
  "Dardic, spoken in Gilgit and the upper Indus valleys. The Dardic languages sit at the "
  "northwest edge of Indo-Aryan and preserve consonant clusters that the rest of the family "
  "simplified two thousand years ago.",
  "Pakistan Census 2023; Bailey, Grammar of the Shina Language (1924)."),
 ("Hawai'i Creole English", ["Category:Hawaiian Pidgin", "Category:Culture of Hawaii"],
  "Called Pidgin by everyone who speaks it, though it is a creole: it formed on the sugar "
  "plantations among Hawaiian, Portuguese, Chinese, Japanese, Korean and Filipino workers who "
  "needed a common language and whose children made one. Long stigmatised in schools; the state "
  "began counting it as a language in the 2015 census.",
  "US Census Bureau American Community Survey 2015 onward, which first listed it separately."),
 ("Krio", ["Category:Krio language", "Category:Sierra Leone"],
  "Sierra Leone's lingua franca, spoken as a first language by the Krio descendants of freed "
  "slaves resettled at Freetown from Britain, Nova Scotia, Jamaica and recaptured slave ships. "
  "It is understood by most of the country and is the language in which Sierra Leone actually "
  "talks to itself.",
  "Ethnologue 2024; Statistics Sierra Leone 2021 census."),
 ("Morisyen", ["Category:Mauritian Creole", "Category:Culture of Mauritius"],
  "French-lexifier, the mother tongue of nearly all Mauritians, in a country whose official "
  "language is English, whose parliament debates in English and French, and whose people speak "
  "Morisyen at home. It gained a standard orthography in 2011 and entered schools as a subject "
  "in 2012.",
  "Statistics Mauritius 2022 census; Grafi-larmoni orthography (2011)."),
 ("Balkan Romani", ["Category:Romani people", "Category:Romani culture"],
  "Romani is Indo-Aryan — the language its speakers carried out of northwest India around a "
  "thousand years ago, and the strongest evidence for where the Roma came from, since no written "
  "record of the migration exists. The Balkan group is the largest, spoken from Greece and "
  "Bulgaria north through the former Yugoslavia.",
  "Matras, Romani: A Linguistic Introduction (2002); Council of Europe estimates."),
 ("Khowar", ["Category:Chitral District", "Khowar language"],
  "The language of Chitral in northern Pakistan, Dardic, with a written tradition in the "
  "Perso-Arabic script and a lively tradition of sung poetry accompanied by the sitar.",
  "Pakistan Census 2023."),
 ("Chakma", ["Category:Chakma people", "Category:Chakma script"],
  "Spoken in the Chittagong Hill Tracts and in Mizoram and Tripura, and written in its own "
  "script, a Brahmic alphabet related to Burmese and encoded in Unicode in 2012.",
  "Ethnologue 2024; Unicode 6.1 (2012) for the Chakma block."),
 ("Judeo-Tat", ["Category:Mountain Jews", "Category:Juhuri language"],
  "Juhuri, the Iranian language of the Mountain Jews of the eastern Caucasus, written "
  "historically in Hebrew letters and later in Cyrillic and Latin. Most of its speakers now live "
  "in Israel; the community in Azerbaijan's Qırmızı Qəsəbə is the last mostly-Jewish town "
  "outside Israel.",
  "Ethnologue 2024; Authority for Judeo-Tat, Israel."),
 ("Digor Ossetian", ["Category:Ossetians", "Category:North Ossetia-Alania"],
  "The western half of Ossetian, and the more conservative one. Ossetian is the last living "
  "descendant of Scythian and Alanic — the Iranian languages of the steppe nomads Herodotus "
  "described — and the only one that survived the Turkic and Slavic expansions.",
  "Russian Federal Census 2021; Thordarson, Ossetic Grammatical Studies (2009)."),
 ("Gallurese Sardinian", ["Category:Gallura", "Category:Sardinia"],
  "Spoken in the northeast of Sardinia and structurally Corsican rather than Sardinian, the "
  "result of medieval settlement across the strait. Sardinia's language map has four distinct "
  "things on it, and two of them are not Sardinian.",
  "Regione Autonoma della Sardegna, Legge Regionale 26/1997, which recognises it separately."),
 ("Sassarese Sardinian", ["Category:Sassari", "Category:Sardinia"],
  "A transitional language around Sassari, Corsican-Tuscan in its base with heavy Sardinian and "
  "Catalan and Spanish layers — the sediment of everyone who has governed the island.",
  "Regione Autonoma della Sardegna, Legge Regionale 26/1997."),
 ("Saramaccan", ["Category:Saramaka", "Category:Maroons in Suriname"],
  "The language of the Saramaka Maroons of Suriname, descendants of people who escaped the "
  "plantations in the seventeenth century and founded independent communities upriver. Its "
  "vocabulary is about half English, a third Portuguese and the rest African, and it is tonal — "
  "the only Atlantic creole that clearly is.",
  "Ethnologue 2024; McWhorter and Good, A Grammar of Saramaccan Creole (2012)."),
 ("Seselwa Creole French", ["Category:Seychellois Creole", "Category:Seychelles"],
  "One of the three official languages of Seychelles, alongside English and French, and the only "
  "French creole anywhere with full official status and a state institute — the Lenstiti Kreol — "
  "to standardise it.",
  "National Bureau of Statistics, Seychelles, 2022 census."),
 ("Shughni", ["Category:Pamiris", "Category:Gorno-Badakhshan"],
  "A Pamir language of the Iranian branch, spoken in the high valleys of Tajikistan and "
  "Afghanistan. The Pamir languages are not mutually intelligible with Persian or with each "
  "other; Shughni serves as the lingua franca among them.",
  "Tajikistan census 2020; Edelman and Dodykhudoeva in The Iranian Languages (2009)."),
 ("Wakhi", ["Category:Wakhan", "Category:Wakhi people"],
  "Spoken in the Wakhan corridor and across the borders into Pakistan, China and Tajikistan — a "
  "single language in four countries because the corridor was drawn in 1893 to keep the Russian "
  "and British empires from touching.",
  "Ethnologue 2024; Anglo-Russian Pamir Boundary Commission (1895) for the corridor."),
 ("Louisiana Creole French", ["Category:Louisiana Creole", "Category:Louisiana French"],
  "Distinct from Cajun French, which is a variety of French; this is a creole, formed on "
  "Louisiana plantations. Both were suppressed by the 1921 state constitution, which banned "
  "teaching in French, and both are now in revival.",
  "US Census Bureau American Community Survey 2019; Klingler, If I Could Turn My Tongue Like "
  "That (2003)."),
 ("Chitral Kalasha", ["Category:Kalash people", "Category:Kalash Valleys"],
  "The language of the Kalash of three valleys in Chitral, the last community in the region "
  "practising its pre-Islamic religion. Roughly seven thousand speakers, and the language and "
  "the religion are declining together.",
  "Pakistan Census 2023; UNESCO Atlas lists it definitely endangered."),
 ("Nuristani Kalasha", ["Category:Nuristan Province", "Category:Nuristani people"],
  "Waigali, of Nuristan in eastern Afghanistan — a different language from Chitral Kalasha "
  "despite the shared name, and in a different branch. Nuristani is a third primary branch of "
  "Indo-Iranian alongside Indo-Aryan and Iranian, or so most specialists now hold.",
  "Ethnologue 2024; Strand, Nuristani Languages (2001)."),
 ("Fala", ["Category:Fala language", "Category:Extremadura"],
  "Galician-Portuguese spoken in three villages of the Jálama valley in Extremadura, seven "
  "hundred kilometres from Galicia — an isolated survival from medieval resettlement, still the "
  "everyday language of about eleven thousand people.",
  "Junta de Extremadura, declared a bien de interés cultural 2001."),
 ("Palula", ["Category:Chitral District", "Palula language"],
  "Dardic, spoken in a few valleys of southern Chitral. It got its first orthography in 2004, "
  "developed with the community, and its first published dictionary in 2013.",
  "Liljegren, A Grammar of Palula (2016)."),
 ("Kalo Finnish Romani", ["Category:Finnish Kale", "Category:Romani people"],
  "The Romani of Finland, whose speakers arrived in the sixteenth century and who have kept a "
  "distinctive dress and a strong avoidance code. The language is severely endangered — most "
  "Finnish Kale now speak Finnish — and is taught in schools under a 1995 constitutional "
  "amendment.",
  "Finnish Ministry of Education; Constitution of Finland §17 (1995 amendment)."),
 # ---- Indo-European batch 4: the closing sweep. Every IE language with a full
 # published grammar that still carried nothing here but a composed description.
 # A grammar exists for each, so their emptiness was our gap and not the record's.

 ("Hieroglyphic Luwian", ["Category:Luwian inscriptions", "Category:Anatolian hieroglyphs"],
  "Written in a hieroglyphic script of its own — unrelated to Egypt's, invented in Anatolia — "
  "and used alongside cuneiform Hittite for six hundred years. It outlived the Hittite empire: "
  "after 1200 BCE the successor states of Carchemish and Malatya went on carving Luwian while "
  "Hittite disappeared. The script was deciphered in stages across the twentieth century, and "
  "the reading of several signs changed as late as 1973.",
  "Hawkins, Corpus of Hieroglyphic Luwian Inscriptions (2000); Payne, Hieroglyphic Luwian "
  "(3rd ed. 2014)."),
 ("Middle Low German", ["Category:Middle Low German", "Category:Hanseatic League"],
  "The language of the Hanseatic League, and for three centuries the working tongue of trade "
  "across the North and Baltic seas. It shaped Danish, Swedish and Norwegian more than any other "
  "foreign language has — a quarter of the everyday vocabulary of the Scandinavian languages "
  "came in through it. When the League declined the language went with it, and High German took "
  "over the north.",
  "Lasch, Mittelniederdeutsche Grammatik (2nd ed. 1974); the Mittelniederdeutsches Handwörterbuch "
  "(Lasch, Borchling and Cordes, in progress since 1928)."),
 ("Old Marathi", ["Category:Marathi manuscripts", "Category:Yadava dynasty"],
  "Attested from the eleventh century and the vehicle of the Varkari devotional movement: "
  "Dnyaneshwar's commentary on the Bhagavad Gita, written about 1290, is the work that made "
  "Marathi a literary language and is still recited. Written in Modi script for administration "
  "and Devanagari for scripture.",
  "Tulpule, Classical Marathi Literature (1979); Master, A Grammar of Old Marathi (1964)."),
 ("Macanese", ["Category:Macanese people", "Category:Macau"],
  "Patuá — a Portuguese-lexifier creole formed at Macau with Malay, Cantonese and Sinhala in it, "
  "carried there by Portuguese who came via Malacca and Goa. It has perhaps fifty fluent "
  "speakers left, and survives mainly in an annual theatre festival that performs comedies in "
  "it. UNESCO lists it critically endangered.",
  "Ethnologue 2024; UNESCO Atlas of the World's Languages in Danger; Baxter, "
  "A Grammar of Kristang (1988) for the related Malacca creole."),
 ("Trinidadian Creole English", ["Category:Culture of Trinidad and Tobago", "Category:Calypso"],
  "The everyday language of Trinidad, English-lexifier with a French-creole substrate from the "
  "island's pre-1797 planters and a layer of Bhojpuri from indenture. It is the language of "
  "calypso, and calypso is where its wordplay is most visible — the form rewards a singer who "
  "can say a dangerous thing in a way that survives the censor.",
  "Winer, Dictionary of the English/Creole of Trinidad and Tobago (2009)."),
 ("Tobagonian Creole English", ["Category:Tobago", "Category:Culture of Trinidad and Tobago"],
  "Closer to the creoles of the eastern Caribbean than to Trinidad's, because the two islands "
  "were settled separately and only joined administratively in 1889. Tobago changed hands "
  "between European powers more often than almost anywhere in the region, and the language did "
  "not follow the flag.",
  "Winer, Dictionary of the English/Creole of Trinidad and Tobago (2009)."),
 ("Antigua and Barbuda Creole English", ["Category:Antigua and Barbuda", "Category:Leeward Islands"],
  "The Leeward Islands creole, spoken across Antigua, Barbuda, Anguilla, Montserrat and St Kitts "
  "with local differences. Formed on the sugar estates in the seventeenth century; used at every "
  "level of society and taught in none.",
  "Ethnologue 2024; Aceto and Williams, eds., Contact Englishes of the Eastern Caribbean (2003)."),
 ("San Andres Creole English", ["Category:San Andrés (island)", "Category:Raizal"],
  "An English-lexifier creole spoken on Colombian islands three hundred kilometres off "
  "Nicaragua, by the Raizal, whose ancestors were brought by British planters. Colombia "
  "recognised it as an official language of the archipelago in 1991, alongside Spanish — one of "
  "very few creoles anywhere with constitutional standing.",
  "Constitution of Colombia (1991), Article 10; Bartens, A Comparative Grammar of Creoles (2013)."),
 ("Limonese Creole", ["Category:Limón Province", "Category:Afro-Costa Ricans"],
  "Mekatelyu — English-lexifier, spoken on Costa Rica's Caribbean coast by the descendants of "
  "Jamaicans recruited to build the Atlantic railway and then to work the banana plantations. "
  "Until 1949, Costa Rican law barred them from leaving the province.",
  "Herzfeld, Mekaytelyuw: La lengua criolla de Limón (2002)."),
 ("Tayo", ["Category:New Caledonia", "Category:Kanak people"],
  "A French-lexifier creole that formed at the Saint-Louis mission near Nouméa in the 1860s, "
  "among Kanak people from several different language groups settled together by missionaries. "
  "It is one of very few creoles whose formation can be dated to a specific place and decade, "
  "and the only French creole in the Pacific.",
  "Ehrhart, Le créole français de St-Louis (1993); Speedy, in Journal of Pidgin and Creole "
  "Languages (2007)."),
 ("Faeto and Celle San Vito Francoprovencal", ["Category:Faeto", "Category:Arpitan language"],
  "Two villages in Puglia, seven hundred kilometres from the Alps, speaking Franco-Provençal — "
  "the descendants of soldiers or settlers from Savoy who arrived in the thirteenth century and "
  "never assimilated. Fewer than a thousand speakers, and the southernmost point Arpitan reaches.",
  "Italian Law 482/1999, which recognises them; Nagy, Faetar (2000)."),
 ("Zoroastrian Yazdi", ["Category:Zoroastrians", "Category:Yazd"],
  "Dari or Behdinani — the language of the Zoroastrians of Yazd and Kerman, and a Central "
  "Iranian language rather than a form of Persian. It survived because the community was "
  "isolated by its religion; it is now declining as that isolation ends.",
  "Ethnologue 2024; Gershevitch, in Handbuch der Orientalistik (1969)."),
 ("Alviri-Vidari", ["Category:Qazvin Province", "Category:Iranian languages"],
  "Two neighbouring villages in Qazvin province speaking a Northwest Iranian language that is "
  "not Persian and not Azerbaijani, surrounded by both. A remnant of the Median-related speech "
  "that covered the region before Persian expanded into it.",
  "Ethnologue 2024; Yarshater, in Encyclopaedia Iranica."),
 ("Kohistani Shina", ["Category:Kohistan District", "Category:Dardic languages"],
  "Spoken in Indus Kohistan, in valleys reached by road only in the twentieth century. Dardic, "
  "and conservative even by Dardic standards — it keeps consonant clusters that the rest of "
  "Indo-Aryan simplified two thousand years ago.",
  "Schmidt and Kohistani, A Grammar of the Shina Language of Indus Kohistan (2008)."),
 ("Kachi Koli", ["Category:Kutch district", "Category:Tharparkar District"],
  "Spoken across the Rann of Kutch on both sides of the India–Pakistan border, by communities "
  "the partition of 1947 cut in two. Indo-Aryan, close to Gujarati and Sindhi without being "
  "either.",
  "Ethnologue 2024; Pakistan Census 2023."),
 ("Sirmauri", ["Category:Sirmaur district", "Category:Western Pahari"],
  "A Western Pahari language of the lower Himalaya in Himachal Pradesh, returned as Hindi at "
  "every census. Western Pahari is one of the least-described branches of Indo-Aryan relative to "
  "its size — several million speakers across dozens of valley varieties.",
  "Census of India 2011, under Hindi; Grierson, Linguistic Survey of India vol. IX (1916)."),
 ("Sirajic", ["Category:Doda district", "Category:Western Pahari"],
  "Spoken in the Chenab valley of Jammu, between Kashmiri and Dogri and sharing features with "
  "both. Its speakers are counted variously as Kashmiri, Dogri or Hindi depending on the census.",
  "Census of India 2011; Grierson, Linguistic Survey of India vol. IX (1916)."),
 ("Jumli", ["Category:Jumla District", "Category:Karnali Province"],
  "The speech of Jumla in far-western Nepal, and one of the more conservative Indo-Aryan "
  "varieties of the Himalaya — it retains features that standard Nepali, its close relative, has "
  "lost. Jumla was the seat of the Khasa kingdom, whose language is the ancestor of Nepali.",
  "Ethnologue 2024; Nepal census 2021."),
 # ---- SINO-TIBETAN batch 1. The family has 518 languages here and carried 25 labels.
 # The first four below have 116 million speakers between them and were all filed as
 # "a Sino-Tibetan language".

 ("Jinyu Chinese", ["Category:Shanxi", "Category:Jin Chinese"],
  "Forty-seven million speakers in Shanxi and around it, and the reason it is counted separately "
  "from Mandarin at all is one feature: it kept the entering tone, the abrupt syllable ending in "
  "a stop that Middle Chinese had and Mandarin lost. Whether that is enough to make it a "
  "separate language rather than a Mandarin dialect has been argued since Li Rong proposed the "
  "split in 1985, and Chinese dialectology has not settled it.",
  "Li Rong, in Fangyan (1985), for the original proposal; Ethnologue 2024 for the count."),
 ("Xiang Chinese", ["Category:Hunan", "Category:Xiang Chinese"],
  "The Chinese of Hunan, thirty-seven million speakers, and split by dialectologists into an Old "
  "Xiang that kept Middle Chinese's voiced initials and a New Xiang that has lost them under "
  "Mandarin pressure. Mao Zedong spoke it, which is why recordings of his speeches are a "
  "well-known source for the accent.",
  "Ethnologue 2024; Language Atlas of China (2nd ed. 2012)."),
 ("Gan Chinese", ["Category:Jiangxi", "Category:Gan Chinese"],
  "Twenty-two million speakers, centred on Jiangxi, and grouped with Hakka by some "
  "dialectologists on the strength of shared treatment of Middle Chinese's voiced stops — the "
  "two are the outcome of the same medieval migrations south, separated later.",
  "Ethnologue 2024; Language Atlas of China (2nd ed. 2012)."),
 ("Min Dong Chinese", ["Category:Fuzhou", "Category:Eastern Min"],
  "Eastern Min, the Chinese of Fuzhou, ten million speakers, and the language of a very large "
  "overseas community — most Chinese restaurants in New York run on it. Min is the oldest branch "
  "of Chinese to split off, before Middle Chinese, which is why it preserves distinctions no "
  "other variety has and cannot be reconstructed from the rhyme dictionaries the way the rest "
  "can.",
  "Ethnologue 2024; Norman, Chinese (1988) for Min's early separation."),
 ("Dungan", ["Category:Dungan people", "Category:Dungan language"],
  "Mandarin written in Cyrillic — the language of the Hui Muslims who fled northwest China after "
  "the revolt of 1877 and settled in what is now Kyrgyzstan and Kazakhstan. It is the only "
  "Sinitic language with an alphabetic orthography in regular use, and because it was cut off "
  "before the twentieth-century reforms it keeps Qing-era vocabulary that mainland Mandarin has "
  "replaced.",
  "Rimsky-Korsakoff Dyer, Iasyr Shivaza: The Life and Works of a Soviet Dungan Poet (1991)."),
 ("Bodo-Mech", ["Category:Bodo people", "Category:Bodoland"],
  "Bodo, spoken in Assam by about a million and a half people, written in Devanagari, and added "
  "to the Eighth Schedule of the Indian constitution in 2003 after a long and often violent "
  "campaign for autonomy. It is Tibeto-Burman in a state whose majority language is Indo-Aryan.",
  "Census of India 2011; Constitution (Ninety-second Amendment) Act 2003."),
 ("Eastern Tamang", ["Category:Tamang people", "Category:Tamang language"],
  "The largest Tibeto-Burman language of Nepal, over a million speakers in the hills around "
  "Kathmandu. It is written in Devanagari and, in Buddhist contexts, in Tibetan script; the "
  "Tamang are the people the word Gurkha most often meant in British recruitment.",
  "Nepal census 2021; Mazaudon, in The Sino-Tibetan Languages (2003)."),
 ("Southern Jinghpaw", ["Category:Kachin people", "Category:Jingpho language"],
  "Jingpho, the lingua franca of the Kachin hills across the Myanmar–China border, written in a "
  "Latin orthography devised by the Baptist missionary Ola Hanson in 1895. It is the language of "
  "the Kachin Independence Organisation and of a literature almost entirely produced by and for "
  "the churches.",
  "Hanson, A Dictionary of the Kachin Language (1906); Ethnologue 2024."),
 ("Akha", ["Category:Akha people", "Category:Akha language"],
  "Spoken across five countries in the hills of the southern Yunnan massif, by people who kept "
  "no state and were divided by every border drawn around them. Its oral genealogies are "
  "recited back sixty generations, each man's name beginning with the last syllable of his "
  "father's — a chain that functions as a written record without writing.",
  "Ethnologue 2024; Hansson, in Journal of the Siam Society (1983)."),
 ("Ao Naga", ["Category:Ao Naga", "Category:Nagaland"],
  "One of the larger Naga languages, and the first to be written: Baptist missionaries produced "
  "an Ao orthography in the 1870s, and Ao became a written language a century before most of its "
  "neighbours. Nagaland has more than a dozen mutually unintelligible languages and uses English "
  "as its official one for exactly that reason.",
  "Census of India 2011; Coupe, A Grammar of Mongsen Ao (2007)."),
 ("Lotha Naga", ["Category:Lotha Naga", "Category:Nagaland"],
  "Spoken in Wokha district of Nagaland, written in Latin letters since missionary contact, and "
  "one of the Naga languages with a substantial published literature and a Bible of its own.",
  "Census of India 2011."),
 ("Yimchungru Naga", ["Category:Nagaland", "Category:Naga people"],
  "Spoken in eastern Nagaland along the Myanmar border, in one of the least surveyed parts of "
  "the Naga area. Like most Naga languages it is written in a Latin orthography that arrived "
  "with the church and is used almost entirely for it.",
  "Census of India 2011."),
 ("Wancho Naga", ["Category:Wancho", "Category:Arunachal Pradesh"],
  "Spoken in Longding district of Arunachal Pradesh, and one of very few languages anywhere to "
  "acquire a brand-new script in the twenty-first century: Banwang Losu devised the Wancho "
  "alphabet between 2001 and 2012, and Unicode encoded it in 2019.",
  "Unicode 12.0 (2019) for the Wancho block; Census of India 2011."),
 ("Phom Naga", ["Category:Nagaland", "Category:Naga people"],
  "Spoken in Longleng district of Nagaland. The Phom were among the last Naga groups contacted "
  "by the colonial administration, and their language was first written in the 1950s.",
  "Census of India 2011."),
 ("Galo", ["Category:Arunachal Pradesh", "Category:Tani languages"],
  "A Tani language of Arunachal Pradesh, and unusually well described for the region: it has a "
  "full reference grammar and a community-developed orthography, both rare in a state with more "
  "than ninety languages and few of them written.",
  "Post, A Grammar of Galo (2007); Census of India 2011."),
 ("Zaiwa", ["Category:Kachin State", "Category:Dehong"],
  "Atsi, a Burmish language of the Kachin hills and Dehong, spoken alongside Jingpho and often "
  "by the same people. Written in Latin letters in Myanmar and in a separate romanisation in "
  "China — the border produced two orthographies for one language.",
  "Ethnologue 2024; Lustig, A Grammar and Dictionary of Zaiwa (2010)."),
 ("Zou", ["Category:Manipur", "Category:Kuki-Chin languages"],
  "A Kuki-Chin language of Manipur and Chin State, written in Latin letters. The Kuki-Chin "
  "languages are among the most numerous and least individually described branches of "
  "Tibeto-Burman.",
  "Census of India 2011."),
 ("Geba Karen", ["Category:Karen people", "Category:Kayin State"],
  "One of the Karen languages of eastern Myanmar, written in the Burmese-derived Karen script. "
  "Karen is unusual within Tibeto-Burman for having subject–verb–object word order, the result "
  "of long contact with Mon and Tai.",
  "Ethnologue 2024."),
 ("Bwe Karen", ["Category:Karen people", "Category:Kayah State"],
  "A Karen language of the Kayah hills, described in detail by Eugénie Henderson in a grammar "
  "and dictionary that took forty years and was published after her death — one of the most "
  "thorough descriptions of any language in Myanmar.",
  "Henderson, Bwe Karen Dictionary, with texts and English–Karen word list (1997)."),
 ("Lahta-Zayein Karen", ["Category:Karen people", "Category:Kayah State"],
  "A small Karen language of Kayah and Shan states. The Karen languages number more than twenty "
  "and are not mutually intelligible; the political category Karen covers all of them.",
  "Ethnologue 2024."),
 ("Chepang", ["Category:Chepang people", "Category:Nepal"],
  "Spoken in the Mahabharat range of central Nepal by a community that was semi-nomadic into the "
  "twentieth century. Caughley's grammar and dictionary made it one of the better-described "
  "small languages of the Himalaya.",
  "Caughley, The Syntax and Morphology of the Verb in Chepang (1982); Nepal census 2021."),
 ("Khaling", ["Category:Kirati people", "Category:Solukhumbu District"],
  "A Kiranti language of eastern Nepal with one of the most complex verb systems described "
  "anywhere in Tibeto-Burman — a single verb can agree with both subject and object and carry "
  "the stem alternations of an entire conjugation class.",
  "Jacques et al., in Linguistics of the Tibeto-Burman Area (2012)."),
 ("Lashi", ["Category:Kachin State", "Category:Burmish languages"],
  "A Burmish language of the Kachin hills, spoken on both sides of the China–Myanmar border and "
  "closely related to Zaiwa. Most of its speakers also speak Jingpho.",
  "Ethnologue 2024."),
 ("Kurtokha", ["Category:Bhutan", "Category:East Bodish languages"],
  "An East Bodish language of eastern Bhutan. The East Bodish languages are not descended from "
  "Classical Tibetan but are its cousins — they split from the same ancestor before Tibetan "
  "itself was written, which makes them unusually informative about what that ancestor was like.",
  "van Driem, Languages of the Himalayas (2001); Hyslop, A Grammar of Kurtöp (2017)."),
 ("Leh Ladakhi", ["Category:Ladakh", "Category:Ladakhi language"],
  "The Tibetic language of Leh, written in Tibetan script and, unlike Central Tibetan, still "
  "pronouncing many of the consonant clusters that the classical spelling records — a Ladakhi "
  "reader sounds closer to the seventh-century orthography than a Lhasa reader does.",
  "Koshal, Ladakhi Grammar (1979); Census of India 2011."),
 ("Sherdukpen", ["Category:Arunachal Pradesh", "Category:Kho-Bwa languages"],
  "A Kho-Bwa language of western Arunachal Pradesh, spoken by fewer than ten thousand people. "
  "Kho-Bwa is one of the branches whose position inside Tibeto-Burman is genuinely unresolved — "
  "it may not belong where it is currently placed.",
  "Jacquesson, in Linguistics of the Tibeto-Burman Area (2015); Census of India 2011."),
 # ---- SINO-TIBETAN batch 2: the closing sweep. Every ST language with a full
 # published grammar that still carried nothing here — fifteen, almost all in Yunnan,
 # Sichuan and the Tibetan marches, almost all under ten thousand speakers.

 ("Southern Tujia", ["Category:Tujia language"],
  "Tujia is one of the harder placements in the family — its position inside Sino-Tibetan is "
  "unresolved, and the northern and southern varieties are not mutually intelligible. Eight "
  "million people are registered as Tujia in China; a few thousand speak the language, and "
  "almost none of them speak Southern Tujia.",
  "Brassett and Brassett, A Study of Tujia (2005); UNESCO Atlas lists it critically endangered."),
 ("Tosu", ["Tosu script manuscript", "Category:Ersu Shaba script"],
  "An Ersuic language of Sichuan, and notable for something almost no small language of the "
  "region has: its own script. The Tosu logographic writing is known from a handful of "
  "manuscripts and is unrelated to Chinese or to Tibetan.",
  "Sun Hongkai, in Zhongguo Yuwen (1982); Yu, Ersu and Tosu (2012)."),
 ("Maang", ["Category:Loloish languages"],
  "A Mondzish language of the Yunnan–Vietnam border, one of a cluster described for the first "
  "time in the 2010s. Mondzish sits at the edge of Lolo-Burmese and may be its earliest offshoot.",
  "Lama, Subgrouping of Nisoic Languages (2012); Hsiu, in the Journal of the Southeast Asian "
  "Linguistics Society (2018)."),
 ("Baraamu", ["Category:Baram language"],
  "A Newaric language of central Nepal with a handful of elderly speakers. It is close to "
  "Thangmi and both are close to Newar — the only living relatives of the oldest written "
  "Tibeto-Burman language of Nepal, and neither has ever been written.",
  "Kansakar et al., A Sociolinguistic Study of the Baram Language (2011)."),
 ("Shendu", ["Category:Mara language"],
  "A Maraic language of the India–Myanmar–Bangladesh borderlands. Maraic is Kuki-Chin, and the "
  "Kuki-Chin languages are among the most numerous and least individually described in the "
  "family — this one has a grammar and almost nothing else.",
  "VanBik, Proto-Kuki-Chin (2009); Ethnologue 2024."),
 ("Darlong", ["Category:Mizo language"],
  "A Mizoic language of Tripura, written in Latin letters. Its speakers are counted as Mizo in "
  "most official returns, which is why a language with a published grammar has almost no "
  "documented speaker figure of its own.",
  "Census of India 2011; VanBik, Proto-Kuki-Chin (2009)."),
 ("Lianghe Achang", ["Category:Achang language"],
  "One of three Achang varieties in Dehong, Yunnan, mutually unintelligible with the others. "
  "Achang is Burmish — the branch Burmese belongs to — and preserves consonant clusters that "
  "Burmese lost, which makes it useful for reconstructing the branch.",
  "Dai and Cui, A Study of Achang (1985); Ethnologue 2024."),
 ("Buyuan Jinuo", ["Category:Jino language"],
  "One of two Jino languages in Xishuangbanna, spoken by a people China recognised as a separate "
  "nationality only in 1979 — the last group to be added to the official list of fifty-six.",
  "Gai Xingzhi, A Study of Jino (1986); Ethnologue 2024."),
 ("Dongna", ["Category:Amdo Tibetan language"],
  "A North-Eastern Tibetic variety of the Amdo region. The Tibetic languages of the northeast "
  "diverge sharply from Lhasa Tibetan — several have no tone at all, where Central Tibetan "
  "developed a full tone system.",
  "Tournadre, in Trans-Himalayan Linguistics (2014)."),
 ("Ponthai", ["Category:Tangsa language"],
  "A Tutsic language of the Patkai range in Arunachal Pradesh, among the Tangsa group. Tangsa "
  "covers dozens of varieties that are counted as one people and are not one language; most "
  "have no description at all.",
  "Morey, in North East Indian Linguistics (2017)."),
 ("Derong-nJol Tibetan", ["Category:Khams Tibetan language"],
  "A Kham Tibetic variety of the Derong valleys in western Sichuan. Kham Tibetan is a dialect "
  "continuum across a thousand kilometres of gorge country in which neighbouring valleys "
  "understand each other and the ends do not.",
  "Suzuki, in Himalayan Linguistics (2013)."),
 ("Hlersu", ["Category:Yi languages"],
  "A Lipo-Lolopo language of central Yunnan, sometimes called Sansu. Its speakers are registered "
  "as Yi, a category covering several million people and dozens of languages that are not "
  "mutually intelligible.",
  "Lama, Subgrouping of Nisoic Languages (2012)."),
 ("Songlin", ["Category:Tibetic languages"],
  "A Chamdoic language of eastern Tibet, one of a small group identified as distinct from "
  "Tibetan only in the last two decades. These languages are surrounded by Tibetan, written in "
  "nothing, and are the living relatives of Tangut.",
  "Suzuki and Sonam Wangmo, in Linguistics of the Tibeto-Burman Area (2016)."),
 ("Lamo", ["Category:Tibetic languages"],
  "Spoken in a few villages of Chamdo prefecture, and given its first full description in 2019 — "
  "one of the more recent additions to the record of any language family. Its speakers use "
  "Tibetan for everything written.",
  "Suzuki and Sonam Wangmo, in Journal of the Southeast Asian Linguistics Society (2019)."),
 ("Eastern Lalu", ["Category:Lalo language"],
  "A Core Lalo language of western Yunnan. The Lalo languages were shown to be several distinct "
  "languages rather than dialects of one only in 2011, on the basis of a survey that took in "
  "sixty villages.",
  "Yang Cathryn, Lalo Regional Varieties: Phylogeny, Dialectometry and Sociolinguistics (2011)."),
 # ---- PAMA-NYUNGAN batch 1. The family covers seven-eighths of Australia — 250
 # languages here — and carried NOT ONE authored label, while 44 of them have a full
 # published grammar. Australian languages are unusually well described relative to
 # their speaker numbers; the gap was ours, not the record's.

 ("Warlpiri", ["Category:Warlpiri language", "Warlpiri sign language"],
  "One of the strongest surviving Australian languages, spoken across the Tanami Desert and "
  "taught in bilingual schools at Yuendumu and Lajamanu since the 1970s. Warlpiri is the "
  "language on which much of modern syntactic theory's account of free word order was built — "
  "its case marking is so complete that the words of a sentence can come in almost any order. "
  "Warlpiri Sign Language, used by women during mourning periods, is a fully developed manual "
  "language in its own right.",
  "Hale, in Language (1983); Laughren et al., Warlpiri Encyclopaedic Dictionary (2022)."),
 ("Guugu Yimidhirr", ["Category:Guugu Yimidhirr language", "Endeavour River Cook vocabulary"],
  "The language Cook's crew recorded in 1770 while the Endeavour was beached for repairs at what "
  "is now Cooktown — the first Australian language written down, and the source of the English "
  "word kangaroo, from *gangurru*. It is also the language that changed how linguists think "
  "about space: Guugu Yimidhirr has no words for left and right and uses compass directions for "
  "everything, so a speaker must track their orientation continuously and does.",
  "Haviland, in Language in Society (1979); Levinson, Space in Language and Cognition (2003)."),
 ("Dyirbal", ["Category:Dyirbal language", "Dyirbal grammar Dixon"],
  "Described by R. M. W. Dixon in 1972 in a grammar that became one of the most cited in the "
  "discipline, partly for its account of *Jalnguy* — an entirely separate vocabulary used when a "
  "tabooed relative was within earshot, with the same grammar and almost no shared words. Its "
  "noun classes are the source of the title of Lakoff's *Women, Fire, and Dangerous Things*, "
  "because one Dyirbal class contains all three.",
  "Dixon, The Dyirbal Language of North Queensland (1972); Lakoff (1987)."),
 ("Kala Lagaw Ya", ["Category:Kalaw Lagaw Ya language", "Torres Strait Islander bible"],
  "The language of the western and central Torres Strait, and a puzzle: it is Pama-Nyungan, "
  "which makes it the only Australian language spoken on islands within sight of New Guinea, "
  "where every neighbour is Papuan. Roughly forty per cent of its vocabulary is shared with "
  "Papuan Meriam Mir next door, from centuries of trade and marriage across the strait.",
  "Bani and Klokeid, Kala Lagaw Langgus (1971); Australian Bureau of Statistics 2021 census."),
 ("Yankunytjatjara", ["Category:Yankunytjatjara language", "Pitjantjatjara sign language"],
  "One of the Western Desert varieties — Pitjantjatjara, Yankunytjatjara, Ngaanyatjarra, Pintupi "
  "and the rest are mutually intelligible across two thousand kilometres, one of the largest "
  "dialect continua anywhere. The names come from each variety's word for 'come': *pitjantja*, "
  "*yankunytja*.",
  "Goddard, A Grammar of Yankunytjatjara (1985)."),
 ("Ngaanyatjarra", ["Category:Ngaanyatjarra language", "Ngaanyatjarra bible"],
  "The Western Desert language of the Ngaanyatjarra Lands in Western Australia, and one of the "
  "few Australian languages children still learn as a first language. Its speakers run their own "
  "schools, media and land council across an area the size of Britain.",
  "Glass and Hackett, Ngaanyatjarra and Ngaatjatjarra to English Dictionary (2003)."),
 ("Pintupi-Luritja", ["Category:Pintupi language", "Papunya Tula painting inscription"],
  "Spoken at Papunya and Kintore. The Pintupi were among the last Aboriginal people to make "
  "contact with settler Australia — the Pintupi Nine walked out of the Gibson Desert in 1984. "
  "Papunya is also where the Western Desert painting movement began in 1971, and the paintings "
  "carry the country the language names.",
  "Hansen and Hansen, Pintupi/Luritja Dictionary (3rd ed. 1992)."),
 ("Western Arrarnta", ["Category:Arrernte language", "Hermannsburg Aranda bible"],
  "The Arrernte of Ntaria (Hermannsburg), where Lutheran missionaries began printing in the "
  "language in the 1890s — one of the earliest Aboriginal languages to have a written standard, "
  "a Bible and a school. Carl Strehlow's ethnographic work there, and his son T. G. H. "
  "Strehlow's, was done in Arrernte rather than through interpreters.",
  "Strehlow, Die Aranda- und Loritja-Stämme (1907–20); Breen, Western Arrarnta Picture "
  "Dictionary (2000)."),
 ("Dhuwal", ["Category:Yolngu languages", "Djambarrpuyngu bible"],
  "One of the Yolŋu languages of northeast Arnhem Land, a region where the languages are still "
  "learned by children and where clan identity and language variety are formally linked — "
  "everyone speaks several, and which one you speak in a given moment says who you are to whom.",
  "Wilkinson, Djambarrpuyŋu: A Yolŋu Variety of Northern Australia (1991)."),
 ("Dhangu", ["Yirrkala bark petitions", "Category:Yolngu languages"],
  "A Yolŋu language of the Gove Peninsula and the islands off it. In 1963 Yolŋu leaders sent the "
  "Australian parliament the Yirrkala bark petitions — typed text pasted onto painted bark, in "
  "Yolŋu Matha and English — the first traditional documents recognised by the Commonwealth and "
  "the beginning of Australian land rights law.",
  "Schebeck, Dialect and Social Groupings in Northeast Arnhem Land (2001); the bark petitions "
  "are held by Parliament House, Canberra."),
 ("Gumatj", ["Yirrkala bark petition 1963", "Category:Yolngu languages"],
  "The Yolŋu clan language of the Gumatj, and the one in which much of the land-rights case Milirrpum "
  "v Nabalco was argued in 1971 — the court accepted that Yolŋu law existed and held that it "
  "conferred no title, a finding overturned by Mabo twenty-one years later.",
  "Milirrpum v Nabalco Pty Ltd (1971) 17 FLR 141; Australian Bureau of Statistics 2021 census."),
 ("Kuku-Yalanji", ["Category:Kuku Yalanji language", "Kuku Yalanji sign"],
  "Spoken in the rainforest between Mossman and Cooktown, and one of the relatively few "
  "Australian languages with several hundred speakers and children among them. Its country "
  "includes the Daintree, and much of the language's plant and animal vocabulary has entered "
  "the region's tourism and land-management usage.",
  "Patz, A Grammar of the Kuku Yalanji Language (2002)."),
 ("Yindjibarndi", ["Category:Yindjibarndi language", "Yindjibarndi sign Roebourne"],
  "A Pilbara language, and the subject of a 2020 High Court decision on native title over "
  "country containing one of the largest iron ore mines in the world. Its community runs its own "
  "media organisation and has produced films and archives in the language.",
  "Wordick, The Yindjibarndi Language (1982); Warrie v Western Australia (2019)."),
 ("Warumungu", ["Category:Warumungu language", "Nyinkka Nyunyu sign"],
  "Spoken around Tennant Creek. The Nyinkka Nyunyu centre there is one of the earliest Aboriginal "
  "cultural centres designed and run by the community whose language and country it holds.",
  "Simpson, Warumungu (Australian — Pama-Nyungan) (2002)."),
 ("Wiradhuri", ["Category:Wiradjuri language", "Wiradjuri sign New South Wales"],
  "Wiradjuri, of central New South Wales — a language that stopped being spoken and has been "
  "brought back. Stan Grant senior and John Rudder built a dictionary from nineteenth-century "
  "sources and living memory; it is now taught in dozens of NSW schools and is one of the "
  "clearest revival successes in the country.",
  "Grant and Rudder, A New Wiradjuri Dictionary (2010); NSW Aboriginal Languages Act 2017."),
 ("Narrinyeri", ["Category:Ngarrindjeri language", "Taplin Narrinyeri vocabulary"],
  "Ngarrindjeri, of the Coorong and lower Murray. The missionary George Taplin's word lists and "
  "the community's own records have supported a revival programme since the 1990s; the language "
  "is taught in schools along the river.",
  "Taplin, The Narrinyeri (1874); Gale, Ngarrindjeri Yanun (2009)."),
 ("Paakantyi", ["Category:Paakantyi language", "Barkindji sign Darling River"],
  "Barkindji, the language of the Darling River — *paaka* is the river, and the name means river "
  "people. In 2015 the Barkindji won native title over 128,000 square kilometres, one of the "
  "largest determinations in New South Wales; the language is in revival.",
  "Hercus, Paakantyi Dictionary (1993); Barkandji Traditional Owners #8 v NSW (2015)."),
 ("Dieri", ["Category:Diyari language", "Killalpaninna Diyari testament"],
  "Diyari, of the Lake Eyre basin, and one of the first Aboriginal languages to be written "
  "extensively: Lutheran missionaries at Killalpaninna printed a New Testament in it in 1897 and "
  "ran a Diyari-language school. Letters written in Diyari by Aboriginal people in the 1900s "
  "survive — among the earliest writing by Aboriginal Australians in their own language.",
  "Austin, A Grammar of Diyari, South Australia (1981); the Killalpaninna letters are held at "
  "the Lutheran Archives, Adelaide."),
 ("Arabana", ["Category:Arabana language", "Arabana sign"],
  "Spoken west of Lake Eyre. Luise Hercus recorded Arabana and many of its neighbours from the "
  "1960s onward, often from the last speakers, in fieldwork that is the reason a large part of "
  "central Australia's linguistic record exists at all.",
  "Hercus, A Grammar of the Arabana-Wangkangurru Language (1994)."),
 ("Yanyuwa", ["Category:Yanyuwa language", "Yanyuwa Borroloola sign"],
  "Spoken at Borroloola on the Gulf of Carpentaria, and unusual even among Australian languages: "
  "men and women use different noun class prefixes throughout, to the point that men's and "
  "women's speech are described as separate dialects and boys switch at initiation.",
  "Bradley and Kirton, Yanyuwa Wuka: Language from Yanyuwa Country (1992)."),
 ("Kaytetye", ["Category:Kaytetye language", "Kaytetye dictionary"],
  "A Central Australian language north of Alice Springs, with a full dictionary and grammar "
  "produced with the community — the *Kaytetye to English Dictionary* records not only words but "
  "the ecological knowledge attached to them.",
  "Turpin and Ross, Kaytetye to English Dictionary (2012)."),
 ("Walmajarri-Juwaliny", ["Category:Walmajarri language", "Walmajarri dictionary"],
  "A desert language of the Kimberley, whose speakers moved north out of the Great Sandy Desert "
  "onto cattle stations in the twentieth century. It is still learned by some children, and the "
  "Walmajarri were central to the 1975 Noonkanbah dispute over drilling on sacred country.",
  "Richards and Hudson, Walmajarri–English Dictionary (1990)."),
 ("Yidiñ", ["Category:Yidiny language", "Yidiny grammar"],
  "A rainforest language of the Cairns area, described by Dixon in a grammar whose account of "
  "its phonology — where vowel length and stress interact in a way that had not been seen before "
  "— is still taught.",
  "Dixon, A Grammar of Yidiny (1977)."),
 ("Kumbainggar", ["Category:Gumbaynggirr language", "Gumbaynggirr sign"],
  "Gumbaynggirr, of the New South Wales mid-north coast. The Muurrbay Aboriginal Language and "
  "Culture Co-operative has run a revival since 1986 from Gerald Smythe's recordings and archival "
  "sources; it is now taught from preschool upward.",
  "Eades, The Dharawal and Dhurga Languages (1976) for the region; Muurrbay, Gumbaynggirr "
  "Dictionary and Learner's Grammar (2001)."),
 ("Yulparija", ["Category:Yulparija language", "Bidyadanga painting"],
  "A Western Desert language whose speakers walked out of the Great Sandy Desert in the 1960s to "
  "Bidyadanga on the coast. Several became painters late in life, and the Yulparija painters of "
  "Bidyadanga are known for depicting desert country from memory after decades beside the sea.",
  "Ethnologue 2024; Australian Bureau of Statistics 2021 census."),
 ("Kukatja", ["Category:Kukatja language", "Balgo Wirrimanu sign"],
  "Spoken at Balgo (Wirrimanu) in the Kimberley, and one of the Western Desert varieties with "
  "children still learning it. The Balgo art movement began there in the 1980s.",
  "Valiquette, A Basic Kukatja to English Dictionary (1993)."),
 ("Nyunga", ["Category:Noongar language", "Noongar sign Perth"],
  "Noongar, of the southwest corner of Western Australia — the language of the country Perth "
  "stands on. It was recorded from the 1830s and stopped being widely spoken within a century; a "
  "revival has run since the 1990s, and in 2020 *Hecate*, a Noongar-language Shakespeare, was "
  "staged in Perth.",
  "Douglas, The Aboriginal Languages of the South-West of Australia (1976); Noongar Boodjar "
  "Language Centre."),
 ("Wajarri", ["Category:Wajarri language", "Inyarrimanha Ilgari Bundara"],
  "A Murchison language of Western Australia, and the language of the country the Square "
  "Kilometre Array radio telescope is being built on — the observatory's Wajarri name, "
  "Inyarrimanha Ilgari Bundara, means 'sharing sky and stars'.",
  "Marmion, Topics in the Phonology and Morphology of Wajarri (1996)."),
 # ---- PAMA-NYUNGAN batch 2: the closing sweep. Nine of these ten have no speakers
 # left. They are the languages Hercus, Austin, Dench and Breen reached in the 1960s-80s,
 # usually from one or two elderly people, usually within a decade of the last of them.

 ("Malgana", ["Category:Malgana language", "Malgana Shark Bay"],
  "The language of Shark Bay in Western Australia, recorded from a handful of speakers in the "
  "twentieth century and no longer spoken. The Malgana Aboriginal Corporation and the Bundiyarra "
  "language centre have run a revival from those records since the 2010s, and Malgana names are "
  "back on the country's signage.",
  "Austin, A Reference Dictionary of Malgana (2019); Bundiyarra Irra Wangga Language Centre."),
 ("Nyiyaparli-Palyku", ["Category:Nyiyaparli language", "Category:Pilbara"],
  "A Ngayarda language of the inland Pilbara, with a small number of older speakers. Its country "
  "sits across the iron ore ranges, and much of the recent documentation was done in the course "
  "of native title claims.",
  "Dench, Martuthunira: A Language of the Pilbara Region (1995) for the group; Wangka Maya "
  "Pilbara Aboriginal Language Centre."),
 ("Tjurruru", ["Category:Ngayarda languages", "Category:Pilbara"],
  "A Ngayarda language of the Pilbara with no speakers left. It is known from recordings made by "
  "Carl von Brandenstein in the 1960s and 1970s, part of a survey that captured a dozen Pilbara "
  "languages within a few years of their last speakers.",
  "von Brandenstein, Narratives from the North-West of Western Australia (1970); Ethnologue 2024."),
 ("Djiwarli", ["Category:Mantharta languages", "Category:Western Australia"],
  "A Mantharta language of the upper Ashburton, described by Peter Austin from work with Jack "
  "Butler, its last fluent speaker, in the 1970s and 1980s. The grammar and texts exist because "
  "one man and one linguist worked steadily for a decade.",
  "Austin, A Grammar of Diyari, South Australia (1981) for method; Austin, Jiwarli texts (1997)."),
 ("Dhalandji", ["Category:Kanyara languages", "Category:Western Australia"],
  "Thalanyji, of the Ashburton River mouth in Western Australia. Recorded in the late twentieth "
  "century; the Buurabalayji Thalanyji Aboriginal Corporation now runs language work on its own "
  "country.",
  "Austin, A Reference Grammar of Thalanyji (2019)."),
 ("Yindjilandji", ["Category:Ngarna languages", "Category:Queensland"],
  "A Ngarna language of the Georgina River country on the Queensland–Northern Territory border, "
  "no longer spoken. Gavan Breen recorded it from the last speakers in the 1960s and 1970s.",
  "Breen, The Mayi Languages of the Queensland Gulf Country (1981); Ethnologue 2024."),
 ("Bularnu", ["Category:Ngarna languages", "Category:Queensland"],
  "A neighbour of Yindjilandji in the same country, recorded in the same decades and from the "
  "same generation. Both are Ngarna, a branch whose members are scattered a thousand kilometres "
  "apart — evidence of a movement across the interior that nothing else records.",
  "Breen, Bularnu Grammar and Vocabulary (1988)."),
 ("Gungabula", ["Category:Maric languages", "Category:Queensland"],
  "A Maric language of central Queensland, described by Gavan Breen in 1973 from the last "
  "speakers. The Maric languages covered much of Queensland's interior and almost none of them "
  "are spoken now.",
  "Breen, Bidyara and Gungabula: Grammar and Vocabulary (1973)."),
 ("Yawarawarga", ["Category:Karnic languages", "Category:Channel Country"],
  "A Karnic language of the Channel Country in southwest Queensland. Luise Hercus recorded it in "
  "the 1960s; the Karnic languages of the Lake Eyre basin are among the best documented extinct "
  "languages in Australia, almost entirely through her work.",
  "Hercus, in Language and History: Essays in Honour of Luise A. Hercus (1990)."),
 ("Wilson River (Grey Range)", ["Category:Karnic languages", "Category:Queensland"],
  "A Karnic language of the Wilson River and Grey Range country, known from twentieth-century "
  "recordings and no longer spoken. The name is the region's rather than the community's — where "
  "the record does not preserve what a language's speakers called it, the geographic label is "
  "what is left, and it is worth noticing that this is a kind of loss too.",
  "Breen, Innamincka Talk (2004); Hercus's Karnic survey materials, AIATSIS."),
 # ---- ATLANTIC-CONGO batch 1. The largest family in this atlas — 1,408 languages, a
 # fifth of everything here — and it carried 24 labels. These are its biggest unlabelled
 # languages plus the eight with a full published grammar and nothing at all.

 ("Rundi", ["Category:Kirundi language", "Kirundi bible"],
  "Kirundi, the national language of Burundi, and one of the very few African countries where "
  "essentially the whole population speaks one indigenous language. It is barely distinguishable "
  "from Kinyarwanda next door — two national languages that a linguist would call one — and the "
  "boundary between them is a colonial border, not a linguistic one.",
  "Ethnologue 2024; Institut de Statistiques et d'Études Économiques du Burundi."),
 ("Mossi", ["Category:Moore language", "Moore bible Burkina Faso"],
  "Mooré, the language of the Mossi and the everyday tongue of Burkina Faso — more speakers than "
  "Swedish and Norwegian combined. The Mossi kingdoms held their ground against Mali and Songhai "
  "for four centuries, which is why a Gur language rather than a Mande one dominates the "
  "country.",
  "Ethnologue 2024; Institut National de la Statistique et de la Démographie, Burkina Faso."),
 ("Luba-Lulua", ["Category:Tshiluba language", "Tshiluba bible"],
  "Tshiluba, one of the four national languages of the Democratic Republic of the Congo, spoken "
  "across the Kasai. Its written standard was fixed by Catholic missionaries at the start of the "
  "twentieth century and it is a language of primary schooling and radio.",
  "Ethnologue 2024."),
 ("Pulaar", ["Category:Fula language", "Category:Adlam script"],
  "Fula — Pulaar in the west, Fulfulde further east — spoken by a herding population spread five "
  "thousand kilometres from Senegal to Sudan, inside twenty other countries. In 1989 two "
  "teenage brothers in Guinea, Ibrahima and Abdoulaye Barry, invented the Adlam alphabet for it "
  "because Arabic and Latin script fit it badly; Unicode encoded Adlam in 2016 and it is now on "
  "phones.",
  "Unicode 9.0 (2016) for the Adlam block; Ethnologue 2024."),
 ("Tsonga", ["Category:Tsonga language", "Xitsonga bible"],
  "Xitsonga, one of South Africa's eleven official languages, also spoken across southern "
  "Mozambique and in Zimbabwe. Its written form dates from Swiss missionary work in the 1880s.",
  "Statistics South Africa 2022 census."),
 ("Kamba (Kenya)", ["Category:Kamba language", "Kikamba bible"],
  "Kikamba, of Kenya's eastern highlands, and one of the first East African languages to be "
  "written: Johann Ludwig Krapf produced a Kikamba vocabulary in the 1840s while based at "
  "Rabai — the same mission from which the first modern description of Swahili came.",
  "Kenya National Bureau of Statistics 2019 census."),
 ("Dagbani", ["Category:Dagbani language", "Dagbani bible"],
  "The Gur language of Dagbon in northern Ghana, written in Latin letters and taught in schools. "
  "The Dagbamba drum histories, performed by lunsi drummers, are an oral chronicle of the "
  "kingdom going back several centuries and are recited in Dagbani.",
  "Ghana Statistical Service 2021 census."),
 ("Abron", ["Category:Abron language", "Category:Akan language"],
  "Brong, an Akan language of the Ghana–Côte d'Ivoire border. Akan as a whole is the largest "
  "language of Ghana; Brong is the western end of it and is spoken on both sides of a colonial "
  "line that split the Abron kingdom in two.",
  "Ethnologue 2024; Ghana Statistical Service 2021."),
 ("Chiga", ["Category:Kiga language", "Runyankole-Rukiga bible"],
  "Rukiga, of southwestern Uganda, close enough to Runyankole that the two are taught together "
  "as Runyankole-Rukiga and printed in a single Bible.",
  "Uganda Bureau of Statistics 2014 census; Ethnologue 2024."),
 ("Fon", ["Category:Fon language", "Category:Vodun"],
  "Fon, the language of the kingdom of Dahomey and of Benin's largest ethnic group. It is also "
  "one of the principal African sources of Haitian Vodou — the word *vodun* is Fon for spirit, "
  "and much of the liturgical vocabulary of Vodou in Haiti and Candomblé in Brazil came across "
  "the Atlantic in this language.",
  "Ethnologue 2024; Institut National de la Statistique, Benin."),
 ("Bini", ["Category:Edo language", "Category:Benin Bronzes"],
  "Edo, the language of the kingdom of Benin — the state whose bronze and ivory work, looted by "
  "a British expedition in 1897 and scattered through European museums, is among the most "
  "consequential art of West Africa. The Edo court's oral histories are recited in it.",
  "Ethnologue 2024; National Population Commission of Nigeria."),
 ("Gun", ["Category:Gun language", "Gun bible Benin"],
  "Gun, of Porto-Novo and the Benin–Nigeria border, part of the Gbe cluster with Fon and Ewe. It "
  "is the language of Benin's capital and a lingua franca along that coast.",
  "Ethnologue 2024."),
 ("Venda", ["Category:Venda language", "Tshivenda bible"],
  "Tshivenda, one of South Africa's official languages and the most isolated of them — it is not "
  "closely related to its Nguni or Sotho neighbours, and shares features with the Shona "
  "languages to the north instead.",
  "Statistics South Africa 2022 census."),
 ("Aja (Benin)", ["Category:Aja language", "Category:Gbe languages"],
  "Aja, of the Mono river valley in Benin and Togo, and the source of the name Ajaland for the "
  "whole Gbe area. The Gbe languages — Ewe, Fon, Aja, Gun — form a continuum along the coast in "
  "which each village understands its neighbours and the ends do not meet.",
  "Ethnologue 2024."),
 ("Urhobo", ["Category:Urhobo language", "Urhobo bible"],
  "Urhobo, of the western Niger delta in Nigeria. The delta holds one of the densest "
  "concentrations of distinct languages in Africa, and Urhobo is among the larger of them.",
  "Ethnologue 2024; National Population Commission of Nigeria."),
 ("Kabiyé", ["Category:Kabiye language", "Kabiye bible"],
  "Kabiyè, one of Togo's two national languages alongside Ewe, spoken in the north. It is "
  "written in a Latin orthography using several African-alphabet letters and is taught in "
  "schools.",
  "Ethnologue 2024; Direction Générale de la Statistique, Togo."),
 ("Isekiri", ["Category:Itsekiri language", "Itsekiri bible"],
  "Itsekiri, of the Warri kingdom in the Niger delta — Yoruboid in its ancestry but spoken among "
  "Edo and Ijaw neighbours, with Portuguese loanwords from four centuries of coastal trade.",
  "Ethnologue 2024."),
 ("Bulu (Cameroon)", ["Category:Bulu language", "Bulu bible Cameroon"],
  "Bulu, of southern Cameroon, and for a long period the church and trade language of the "
  "region — Presbyterian missionaries made it a written standard and it served far beyond its "
  "own community before French took that role.",
  "Ethnologue 2024."),
 ("Farefare", ["Category:Frafra language", "Gurene bible"],
  "Gurenɛ or Frafra, of the Bolgatanga area in northern Ghana and across the Burkina border. A "
  "Gur language with a Latin orthography and a growing published literature.",
  "Ghana Statistical Service 2021 census."),
 ("Ndonga", ["Category:Ndonga language", "Oshindonga bible"],
  "Oshindonga, one of the two written standards of Oshiwambo, the largest language of Namibia. "
  "Finnish missionaries produced its orthography in the 1870s, which is why Namibia's biggest "
  "language was first written by Finns.",
  "Namibia Statistics Agency 2023 census."),
 ("Nupe-Nupe-Tako", ["Category:Nupe language", "Nupe bible"],
  "Nupe, of the Niger–Kaduna confluence in Nigeria. Its glass and brass work supplied the region "
  "for centuries, and the Nupe emirate's records were kept in Arabic script before Latin.",
  "Ethnologue 2024; National Population Commission of Nigeria."),
 ("Jju", ["Category:Jju language", "Tyap bible"],
  "Jju, of the Kaduna plateau in Nigeria, one of the larger Plateau languages in an area where "
  "sixty distinct languages sit within a few hundred kilometres and few have grammars.",
  "Ethnologue 2024."),
 ("Konzo", ["Category:Konjo language", "Lhukonzo bible"],
  "Lhukonzo, spoken on the slopes of the Rwenzori on both sides of the Uganda–Congo border. Its "
  "speakers straddle a frontier drawn through a mountain range.",
  "Uganda Bureau of Statistics 2014 census."),
 ("Jola-Fonyi", ["Category:Jola language", "Jola Fonyi bible"],
  "Jola-Fonyi, of the Casamance in southern Senegal and the Gambia — an Atlantic language, one "
  "of the family's deepest branches, and the main language of a region with its own long "
  "separatist history.",
  "Agence Nationale de la Statistique et de la Démographie, Senegal."),
 # ---- the eight with a grammar and nothing here
 ("Waci Gbe", ["Category:Gbe languages", "Ewe bible"],
  "A Gbe variety of the Togo–Benin coast, close to Ewe and counted with it in most returns. The "
  "Gbe continuum is one of the clearest cases anywhere of a chain in which the political "
  "boundaries between languages are not the linguistic ones.",
  "Capo, A Comparative Phonology of Gbe (1991)."),
 ("Izi-Ezaa-Ikwo-Mgbo", ["Category:Igbo language", "Izi bible"],
  "A cluster of Igboid varieties in Ebonyi State, Nigeria, distinct enough from Standard Igbo to "
  "have their own scripture. Igbo's internal diversity is much greater than the single "
  "standard suggests.",
  "Meier, Meier and Bendor-Samuel, A Grammar of Izi (1975)."),
 ("Nambya", ["Category:Nambya language", "Nambya bible"],
  "Nambya, of northwestern Zimbabwe around Hwange, a Shona-related language with substantial "
  "Kalanga and Tonga contact. It was recognised in Zimbabwe's 2013 constitution, which made "
  "sixteen languages official.",
  "Constitution of Zimbabwe (2013), section 6; Ethnologue 2024."),
 ("Bebele", ["Category:Beti language", "Category:Cameroon"],
  "A Beti language of central Cameroon, close to Ewondo and Bulu. The Beti languages form a "
  "continuum around Yaoundé in which Ewondo serves as the common form.",
  "Ethnologue 2024."),
 ("Kanu", ["Category:Bantu languages", "Category:Democratic Republic of the Congo"],
  "A Bantu language of the Democratic Republic of the Congo, one of several hundred in a country "
  "whose linguistic map is among the least completely surveyed anywhere.",
  "Ethnologue 2024; Maho's updated Guthrie list (2009)."),
 ("Mozambican Ngoni", ["Category:Ngoni people", "Category:Nguni languages"],
  "The language of Ngoni communities in Mozambique, descended from Nguni speakers who moved "
  "north during the Mfecane of the 1820s — a diaspora that carried Zulu-related languages "
  "fifteen hundred kilometres into Malawi, Tanzania, Zambia and Mozambique within a generation.",
  "Ethnologue 2024."),
 ("Sumayela Ndebele", ["Category:Ndebele language", "Category:South Africa"],
  "Northern Transvaal Ndebele, distinct from the Southern Ndebele that is one of South Africa's "
  "official languages, and heavily influenced by Northern Sotho around it.",
  "Statistics South Africa 2022 census; Ethnologue 2024."),
 ("Kituba (Congo)", ["Category:Kituba language", "Kituba bible"],
  "Kituba, a Kikongo-based creole that became the lingua franca of the Congo's southern regions "
  "and one of the national languages of the Republic of the Congo — a Bantu language simplified "
  "by adult learners along the railway and river trade, and then inherited by their children.",
  "Mufwene, in Contact Languages (1997); Ethnologue 2024."),
 # ---- AUSTRONESIAN batch 1. 1,276 languages here and 25 labels. Includes four entries
 # that are each a PRIMARY BRANCH of the family with exactly one member — Bunun, Paiwan,
 # Rukai, Puyuma — which Glottolog files as languages because that is what they are.

 ("Madurese", ["Category:Madurese language", "Category:Madurese script"],
  "Fifteen million speakers on Madura and eastern Java, and the largest language in Indonesia "
  "after Javanese, Sundanese and Indonesian itself. It was written in a variant of the Javanese "
  "script, *carakan Madura*, and is now written in Latin letters; its speaker numbers are high "
  "and its transmission to children is falling fast.",
  "Badan Pusat Statistik Indonesia 2010 census; Ethnologue 2024."),
 ("Hiligaynon", ["Category:Hiligaynon language", "Hiligaynon Ilonggo literature"],
  "Ilonggo, of Panay and Negros Occidental — one of the major Bisayan languages and the medium "
  "of a substantial body of poetry and drama. The Philippines has around 180 languages and "
  "recognises two officially, so Hiligaynon's eight million speakers have no national standing.",
  "Philippine Statistics Authority 2020 census."),
 ("Minangkabau", ["Category:Minangkabau language", "Category:Minangkabau culture"],
  "The language of West Sumatra, and of the largest matrilineal society in the world: property "
  "and clan membership pass through women, in a Muslim society, and have done so through four "
  "centuries of Islam. Minangkabau is close to Malay and its speakers' merchant tradition "
  "carried it across Indonesia and Malaysia.",
  "Badan Pusat Statistik Indonesia 2010 census."),
 ("Coastal-Naga Bikol", ["Category:Bikol language", "Bikol dictionary Lisboa"],
  "Bikol, of southern Luzon. Marcos de Lisboa's *Vocabulario de la lengua Bicol*, compiled in the "
  "early seventeenth century and printed in 1754, is one of the great early dictionaries of any "
  "Philippine language.",
  "Philippine Statistics Authority 2020 census; Lisboa, Vocabulario de la lengua Bicol (1754)."),
 ("Kelantan-Pattani Malay", ["Category:Kelantan-Pattani Malay", "Category:Jawi script"],
  "A Malay variety of the Thai–Malaysian border, and one of the few written mainly in Jawi — the "
  "Arabic-derived script Malay used for six hundred years before Latin letters replaced it. In "
  "Pattani, Jawi remains in everyday use and is part of a long conflict over the region's "
  "identity.",
  "Ethnologue 2024; Thailand National Statistical Office."),
 ("Maguindanao", ["Category:Maguindanao language", "Category:Maranao and Maguindanao"],
  "The language of the Maguindanao sultanate in Mindanao, written historically in Jawi. It is one "
  "of the official languages of the Bangsamoro autonomous region established in 2019.",
  "Philippine Statistics Authority 2020 census; Bangsamoro Organic Law (2018)."),
 ("Tausug", ["Category:Tausug language", "Category:Sulu Archipelago"],
  "The language of the Sulu sultanate, spoken across the Sulu Archipelago and into Sabah and "
  "Indonesia. Written in Jawi for centuries and now also in Latin letters; its speakers were "
  "never fully brought under Spanish rule.",
  "Philippine Statistics Authority 2020 census."),
 ("Kinaray-a", ["Category:Kinaray-a language", "Kinaray-a literature Antique"],
  "Of Antique province on Panay, and the language of the *sugidanon*, a cycle of chanted epics "
  "recorded from the Panay Bukidnon in the twentieth century and running to tens of thousands of "
  "lines.",
  "Philippine Statistics Authority 2020 census."),
 ("Gorontalo", ["Category:Gorontalo language", "Category:Gorontalo"],
  "Of northern Sulawesi, and not closely related to its Celebic neighbours — Gorontalo-Mongondow "
  "is its own branch. Its speakers were Muslim before the Dutch arrived and it was written in "
  "Arabic script.",
  "Badan Pusat Statistik Indonesia 2010 census."),
 ("Ngaju", ["Category:Ngaju language", "Category:Kaharingan"],
  "Of central Kalimantan, and the liturgical language of Kaharingan, the indigenous Dayak "
  "religion that Indonesia recognises administratively as a form of Hinduism because the state "
  "requires every citizen to hold one of six religions.",
  "Badan Pusat Statistik Indonesia 2010 census; Ethnologue 2024."),
 ("Manado Malay", ["Category:Manado Malay", "Category:North Sulawesi"],
  "A Malay-based creole of North Sulawesi with heavy Portuguese, Dutch and Spanish vocabulary "
  "from four centuries of contact — *kadera* for chair, *tarigu* for flour. It is the everyday "
  "language of Manado and a first language for most of the city.",
  "Ethnologue 2024; Stoel, Focus in Manado Malay (2005)."),
 ("Maranao", ["Category:Maranao language", "Category:Darangen"],
  "Of Lanao in Mindanao, and the language of the *Darangen*, an epic of 72,000 lines that takes "
  "days to sing and is on UNESCO's intangible heritage list. Written in Jawi and in Latin "
  "letters.",
  "Philippine Statistics Authority 2020 census; UNESCO Representative List (2008)."),
 ("Batak Karo", ["Category:Karo language", "Category:Batak script"],
  "Of the Karo highlands in North Sumatra, and written in Surat Batak — an Indic-derived script "
  "the Batak peoples used for divination books and magic texts written on folded tree bark, the "
  "*pustaha*. Latin letters replaced it in general use.",
  "Badan Pusat Statistik Indonesia 2010 census."),
 ("Sabah Malay", ["Category:Sabah Malay", "Category:Sabah"],
  "The Malay creole that serves as Sabah's lingua franca, spoken across a state with more than "
  "fifty indigenous languages and no one indigenous majority.",
  "Ethnologue 2024; Department of Statistics Malaysia."),
 ("Negeri Sembilan Malay", ["Category:Negeri Sembilan Malay", "Category:Adat perpatih"],
  "A Malay variety of peninsular Malaysia carried there from Minangkabau in the fifteenth "
  "century, along with *adat perpatih* — matrilineal customary law, still in force in Negeri "
  "Sembilan and nowhere else in Malaysia.",
  "Ethnologue 2024; Department of Statistics Malaysia."),
 ("Tetum", ["Category:Tetum language", "Category:East Timor"],
  "A national language of Timor-Leste alongside Portuguese, and the one people actually speak. "
  "Tetun Dili, the capital's form, absorbed so much Portuguese during four centuries of colonial "
  "rule and twenty-four years of Indonesian occupation that it is effectively a distinct "
  "variety, and it is the language independence was argued in.",
  "Direção-Geral de Estatística, Timor-Leste 2022 census."),
 ("Ibanag", ["Category:Ibanag language", "Ibanag dictionary Bugarin"],
  "Of the Cagayan valley in northern Luzon, and once the lingua franca of the whole valley under "
  "Spanish missionary use. José Bugarin's Ibanag dictionary, completed about 1700, is among the "
  "earliest for any Philippine language.",
  "Philippine Statistics Authority 2020 census."),
 ("Capiznon", ["Category:Capiznon language", "Category:Capiz"],
  "Of Capiz on Panay, between Hiligaynon and Waray in the Bisayan continuum and taking features "
  "from both.",
  "Philippine Statistics Authority 2020 census."),
 ("Komering", ["Category:Komering language", "Category:Lampung script"],
  "Of southern Sumatra, and written in Surat Ulu — a branch of the old Indic-derived scripts of "
  "Sumatra, used on bamboo and bark for law codes and poetry.",
  "Badan Pusat Statistik Indonesia 2010 census."),
 ("Masbatenyo", ["Category:Masbatenyo language", "Category:Masbate"],
  "Of Masbate island, at the meeting point of the Bikol and Bisayan areas and intermediate "
  "between them.",
  "Philippine Statistics Authority 2020 census."),
 ("Sumbawa", ["Category:Sumbawa language", "Category:Sumbawa"],
  "Of western Sumbawa, and closer to Sasak and Balinese than to its eastern neighbours on the "
  "same island — the Tambora eruption of 1815, the largest in recorded history, wiped out the "
  "island's other language, Tambora, which was not Austronesian at all.",
  "Badan Pusat Statistik Indonesia 2010 census."),
 ("Osing", ["Category:Osing language", "Category:Banyuwangi"],
  "Of Banyuwangi at Java's eastern tip, and the closest thing to a surviving descendant of the "
  "language of Blambangan, the last Hindu kingdom on Java. Its speakers were long treated as "
  "Javanese and now assert otherwise.",
  "Badan Pusat Statistik Indonesia 2010 census."),
 ("Kambera", ["Category:Kambera language", "Category:Sumba"],
  "Of eastern Sumba, and the language of a ritual poetry of paired lines in which every phrase "
  "has a fixed partner — a form recorded in detail and unusually well described for eastern "
  "Indonesia.",
  "Klamer, A Grammar of Kambera (1998)."),
 ("Iriga Bicolano", ["Category:Bikol language", "Category:Rinconada Bikol"],
  "Rinconada Bikol, of the Iriga area in Camarines Sur. Bikol is several languages rather than "
  "one, and Rinconada is distinct enough from coastal Bikol to be hard going for its speakers.",
  "Philippine Statistics Authority 2020 census."),
 ("West Coast Bajau", ["Category:Bajau language", "Category:Sama-Bajau"],
  "One of the Sama-Bajaw languages of the sea nomads, spoken along Sabah's west coast. Bajau "
  "Laut communities lived aboard boats across the Sulu and Celebes seas into living memory, and "
  "some remain stateless because they were born at sea.",
  "Ethnologue 2024; Department of Statistics Malaysia."),
 # ---- the three with a grammar and nothing here
 ("Pazeh-Kahabu", ["Category:Pazeh language", "Category:Formosan languages"],
  "A Northwest Formosan language, and a primary-branch member of Austronesian at the same depth "
  "as everything from Malagasy to Hawaiian. Its last fluent speaker, Pan Jin-yu, died in 2010 at "
  "the age of 96; a Kahabu revival community continues with it and a dictionary was published "
  "in 2013.",
  "Li and Tsuchida, Pazih Dictionary (2001); Ethnologue 2024."),
 ("Eastern Tawbuid", ["Category:Tawbuid language", "Category:Mangyan"],
  "A Mangyan language of Mindoro in the Philippines. Several Mangyan languages are written in "
  "Surat Mangyan, an Indic-derived syllabary still used for *ambahan* poetry inscribed on bamboo "
  "— one of very few pre-Hispanic Philippine scripts in continuous use.",
  "Ethnologue 2024; UNESCO Memory of the World, Philippine paleographs (1999)."),
 ("Ga'dang", ["Category:Gaddang language", "Category:Cagayan Valley"],
  "A Northern Luzon language of the Cagayan valley, distinct from the larger Gaddang alongside "
  "it. Its speakers live in the mountains between the valley and the Cordillera.",
  "Philippine Statistics Authority 2020 census; Walrod, Discourse Grammar in Ga'dang (1979)."),

 # ---- the single-language primary branches of Austronesian, which Glottolog files as
 # languages because that is what they are: a whole primary branch, with one member.
 ("Bunun", ["Category:Bunun language", "Category:Bunun people"],
  "A single language, and a primary branch of Austronesian in its own right — the same rank as "
  "everything from Malagasy to Hawaiian put together. Bunun is spoken in Taiwan's central "
  "mountains and is known for the *pasibutbut*, a polyphonic harvest song sung in gradually ",
  "Ethnologue 2024; Council of Indigenous Peoples, Taiwan."),
 ("Paiwan", ["Category:Paiwan language", "Category:Paiwan people"],
  "Another single-language primary branch, in southern Taiwan. Paiwan has an elaborate system of "
  "noble and commoner registers and a rich carving tradition; its position in the tree makes it ",
  "Ethnologue 2024; Council of Indigenous Peoples, Taiwan."),
 ("Rukai", ["Category:Rukai language", "Category:Formosan languages"],
  "A primary branch of one language, and the most divergent of all of them — Rukai lacks features "
  "reconstructed for Proto-Austronesian that every other branch keeps, and several linguists ",
  "Zeitoun, A Grammar of Mantauran Rukai (2007); Ethnologue 2024."),
 ("Puyuma", ["Category:Puyuma language", "Category:Formosan languages"],
  "A primary branch of one language, in southeastern Taiwan. Puyuma, Rukai and Tsouic are the "
  "three branches most often argued to be the earliest divisions, which would make the whole ",
  "Teng, A Reference Grammar of Puyuma (2008); Ethnologue 2024."),
 # ---- AFRO-ASIATIC, TRANS NEW GUINEA and OTOMANGUEAN. The Arabic varieties here are the
 # largest unlabelled languages left in the atlas — nine with over ten million speakers
 # each. Trans New Guinea is the least documented large family we hold. Otomanguean is
 # where the fifty-three-Mixtec naming question comes from.

 # ---------------- AFRO-ASIATIC. The Arabic varieties are the largest unlabelled languages left
 # in the atlas: nine of them with over ten million speakers each, all reading "an Afro-Asiatic
 # language" until now.
 ("Levantine Arabic", ["Category:Levantine Arabic", "Levantine Arabic film poster"],
  "The Arabic of Syria, Lebanon, Jordan and Palestine, and the variety most widely understood "
  "across the Arab world after Egyptian — largely because Lebanese and Syrian television and "
  "music carried it. Like every spoken Arabic it exists alongside Modern Standard Arabic, which "
  "is the written register everywhere and nobody's first language anywhere.",
  "Ethnologue 2024; Cowell, A Reference Grammar of Syrian Arabic (1964)."),
 ("Algerian Arabic", ["Category:Algerian Arabic", "Category:Algeria street signs"],
  "Darja, the Arabic of Algeria, with a heavy Berber substrate and a large French vocabulary "
  "from 132 years of colonial rule. It is what forty million people speak and it has no official "
  "standing: Algeria's official languages are Modern Standard Arabic and Tamazight.",
  "Office National des Statistiques, Algeria; Ethnologue 2024."),
 ("Moroccan Arabic", ["Category:Moroccan Arabic", "Darija sign Morocco"],
  "Darija, and the Arabic variety furthest from all the others — a speaker from Baghdad and a "
  "speaker from Casablanca cannot hold a conversation in their own varieties. Its Berber "
  "substrate is deep, and it has begun appearing in print and advertising, which is contested.",
  "Haut-Commissariat au Plan, Morocco 2024 census; Ethnologue 2024."),
 ("Sudanese Arabic", ["Category:Sudanese Arabic", "Sudan street sign Arabic"],
  "The Arabic of the Nile valley in Sudan, with Nubian and Beja influence. It has served as the "
  "lingua franca of a country with more than seventy languages, and Juba Arabic, its "
  "pidginised descendant, does the same job in South Sudan.",
  "Ethnologue 2024; Sudan Central Bureau of Statistics."),
 ("Saidi Arabic", ["Category:Saidi Arabic", "Category:Upper Egypt"],
  "The Arabic of Upper Egypt, distinct enough from Cairo's that it is stereotyped in Egyptian "
  "film and television. Its speakers live in the Nile valley south of Cairo, where Coptic "
  "survived longest.",
  "Ethnologue 2024; Central Agency for Public Mobilization and Statistics, Egypt."),
 ("Hijazi Arabic", ["Category:Hejazi Arabic"],
  "The Arabic of Mecca, Medina and Jeddah — the western Arabian coast, and the variety spoken "
  "where pilgrims from the entire Muslim world have converged for fourteen centuries, which has "
  "left it more mixed than the Arabic of the interior.",
  "Ethnologue 2024; General Authority for Statistics, Saudi Arabia."),
 ("Tunisian Arabic", ["Category:Tunisian Arabic", "Tunisian Arabic Wikipedia poster"],
  "Derja, with Berber, Punic-era, Italian and French layers. Tunisia's Wikipedia in Tunisian "
  "Arabic and a growing body of published fiction have made it one of the more written of the "
  "spoken Arabics.",
  "Institut National de la Statistique, Tunisia; Ethnologue 2024."),
 ("Sanaani Arabic", ["Category:Sanaani Arabic", "Category:Old City of Sanaa"],
  "The Arabic of Sanaa and the Yemeni highlands, and among the most conservative varieties — it "
  "keeps features of Classical Arabic that the rest of the Arab world lost, which is unsurprising "
  "in the region Arabic came from.",
  "Ethnologue 2024; Watson, Ṣanʿānī Arabic (1993)."),
 ("Ta'izzi-Adeni Arabic", ["Category:Ta'izzi-Adeni Arabic"],
  "The Arabic of southern Yemen, around Taiz and Aden, with British-era English loanwords Aden "
  "acquired as a coaling port and colony.",
  "Ethnologue 2024."),
 ("Chadian Arabic", ["Category:Chadian Arabic"],
  "Shuwa Arabic, of Chad and the Lake Chad basin, and the westernmost Arabic spoken as a first "
  "language. It is a lingua franca across a region whose other languages are Chadic and "
  "Nilo-Saharan.",
  "Ethnologue 2024; Institut National de la Statistique, Chad."),
 ("Tarifiyt-Beni-Iznasen-Eastern Middle Atlas Berber",
  ["Category:Riffian language", "Category:Tifinagh"],
  "Tarifit, the Berber of the Rif in northern Morocco, and the language of the Rif Republic that "
  "fought Spain and France to a standstill in the 1920s. Tamazight became an official language "
  "of Morocco in 2011 and Tifinagh script is now taught in schools.",
  "Haut-Commissariat au Plan, Morocco; Constitution of Morocco (2011), Article 5."),
 ("Gedeo", ["Category:Gedeo language", "Category:Gedeo Zone"],
  "A Cushitic language of southern Ethiopia, spoken in the Gedeo Zone whose terraced coffee "
  "landscape is a UNESCO World Heritage site. Written in the Ethiopic script.",
  "Ethiopian Statistics Service 2007 census; Ethnologue 2024."),
 # ---------------- TRANS NEW GUINEA. The least documented large family here: 317 languages,
 # 18 labels, one object and no recordings.
 ("Siane", ["Category:Eastern Highlands Province", "Category:Papua New Guinea"],
  "A Kainantu-Goroka language of the eastern highlands of Papua New Guinea. The highlands were "
  "unknown to the outside world until aerial survey in the 1930s found a densely populated "
  "agricultural landscape where the maps had shown nothing.",
  "Ethnologue 2024; Papua New Guinea National Statistical Office."),
 ("Alekano", ["Category:Eastern Highlands Province", "Category:Goroka"],
  "Gahuku, of the Goroka valley. Its speakers were the subject of Kenneth Read's *The High "
  "Valley* (1965), one of the first ethnographies to be written as a personal narrative rather "
  "than a survey.",
  "Ethnologue 2024."),
 ("Yagaria", ["Category:Eastern Highlands Province", "Category:Papua New Guinea"],
  "A Goroka language of the eastern highlands with about twenty thousand speakers, a Latin "
  "orthography from mission work, and no other written use.",
  "Ethnologue 2024; Renck, A Grammar of Yagaria (1975)."),
 ("Moni", ["Category:Papua (province)", "Category:Highland Papua"],
  "A language of the central highlands of Indonesian Papua, west of the Baliem. This is among "
  "the least surveyed linguistic regions on earth: the number of languages in Indonesian Papua "
  "is not known to within several dozen.",
  "Ethnologue 2024."),
 ("Guhu-Samane", ["Category:Morobe Province", "Category:Papua New Guinea"],
  "Of the Waria valley in Morobe Province. It sits at the edge of Trans New Guinea and its "
  "membership in the family is not settled — a common situation, since the family's outer "
  "limits rest largely on pronoun evidence.",
  "Ethnologue 2024; Richert, Guhu-Samane grammar (1975)."),
 ("Kamoro", ["Category:Mimika Regency", "Category:Asmat-Kamoro"],
  "Of the swamp coast of southern Papua, west of the Asmat. Kamoro and Asmat carving traditions "
  "are closely related, and the Kamoro coast is where the Freeport mine's tailings reach the sea.",
  "Ethnologue 2024; Drabbe, Spraakkunst van het Kamoro (1953)."),
 ("Narak", ["Category:Jiwaka Province", "Category:Papua New Guinea"],
  "A Chimbu-Wahgi language of the Jimi valley. Papua New Guinea has around 840 languages for ten "
  "million people — the highest linguistic density of any country on earth.",
  "Ethnologue 2024."),
 ("Aghu", ["Category:South Papua", "Category:Awyu-Dumut languages"],
  "An Awyu language of the Digul river in southern Papua, described by the missionary linguist "
  "Peter Drabbe, whose grammars of a dozen Papuan languages in the 1940s and 1950s are still the "
  "primary sources for most of them.",
  "Drabbe, Spraakkunst van het Aghu-dialect (1957); Ethnologue 2024."),
 # ---------------- OTOMANGUEAN. 181 languages, 2 labels — and the family whose naming the whole
 # cluster question came from.
 ("Isthmus Zapotec", ["Category:Zapotec languages", "Category:Juchitán de Zaragoza"],
  "Diidxazá, of the Isthmus of Tehuantepec, and the Zapotec variety with the strongest literary "
  "tradition — Juchitán has published poetry and periodicals in it since the nineteenth century, "
  "and its writers have kept it in print through a century in which most Mexican indigenous "
  "languages lost ground. It is one of fifty-seven languages named Zapotec.",
  "INEGI 2020 census; Pickett, Vocabulario Zapoteco del Istmo (1959)."),
 ("Western Tlacolula Valley Zapotec", ["Category:Zapotec languages", "Category:Tlacolula"],
  "Of the Tlacolula valley near Oaxaca city, and one of the Zapotec varieties with a substantial "
  "community in Los Angeles — Oaxacan migration has made Zapotec one of the more widely spoken "
  "indigenous American languages in the United States, and California courts have had to find "
  "interpreters for it.",
  "INEGI 2020 census; Munro and Lopez, Di'csyonaary X:tèe'n Dìi'zh Sah Sann Lu'uc (1999)."),
 ("San Jerónimo Tecóatl Mazatec", ["Category:Mazatec language", "Category:Sierra Mazateca"],
  "One of the Mazatec languages of the Sierra Mazateca, where men hold whole conversations "
  "across ravines by whistling the tones of the words — the best-documented whistled speech "
  "anywhere. Mazatec is also the language of María Sabina's veladas, recorded in the 1950s.",
  "INEGI 2020 census; Cowan, in Language (1948) for the whistled speech."),
 ("Chichimeca-Jonaz", ["Category:Chichimeca Jonaz language", "Category:Guanajuato"],
  "The last surviving language of the Chichimeca, spoken in one town in Guanajuato. Chichimeca "
  "was a name Nahuatl speakers used for the peoples of the northern deserts; almost all their "
  "languages are gone.",
  "INEGI 2020 census; Ethnologue 2024."),
 ("Chiapanec", ["Category:Chiapanec language", "Category:Chiapas"],
  "An Otomanguean language of Chiapas, and evidence of a long migration: its closest relative is "
  "Mangue, spoken a thousand kilometres south in Nicaragua, and the two are the only Otomanguean "
  "languages ever found outside central Mexico. Chiapanec has no speakers left.",
  "Ethnologue 2024; Campbell, American Indian Languages (1997)."),
 ("Mangue", ["Category:Chorotega", "Category:Nicaragua"],
  "The Chorotega language of Pacific Nicaragua and Costa Rica, and Chiapanec's only close "
  "relative — the southern end of an Otomanguean migration out of Mexico. It died about 1900 and "
  "is known from colonial word lists.",
  "Campbell, American Indian Languages (1997); Quirós Rodríguez, Mangue vocabulary (2002)."),
 ("Subtiaba", ["Category:Nicaragua", "Category:Tlapanec language"],
  "An Otomanguean language of León in Nicaragua, gone by the 1930s. Sapir showed in 1925 that "
  "Subtiaba was related to Tlapanec in Guerrero, sixteen hundred kilometres away — a "
  "demonstration that is still cited as a model of how to establish a distant relationship.",
  "Sapir, in American Anthropologist (1925); Campbell, American Indian Languages (1997)."),
 ("Guerrero Amuzgo", ["Category:Amuzgo language", "Category:Guerrero"],
  "Amuzgo of Xochistlahuaca in Guerrero. Amuzgo is one of the more tonally complex Otomanguean "
  "languages, and Amuzgo weavers' backstrap-loom textiles are among the best known in Mexico.",
  "INEGI 2020 census; Ethnologue 2024."),
 # ---- SEVEN MID-SIZE FAMILIES: Dravidian, Austroasiatic, Tai-Kadai, Mande, Uto-Aztecan,
 # Arawakan, Tupian. Between them 625 languages and 16 labels. Tamil is here — seventy-five
 # million speakers and two thousand years of continuous literature, unlabelled until now.

 # ---------------- DRAVIDIAN
 ("Tamil", ["Category:Tamil language", "Category:Tamil-Brahmi"],
  "Two thousand years of continuous literature, and the only language of India whose classical "
  "corpus is read without translation by ordinary speakers today. The Sangam poems were composed "
  "between roughly 300 BCE and 300 CE and are secular — love and war rather than scripture — "
  "which is unusual for a classical literature anywhere. Tamil is an official language of India, "
  "Sri Lanka and Singapore, and in 1965 protests against imposing Hindi on Tamil Nadu were "
  "violent enough to change national language policy permanently.",
  "Census of India 2011; Zvelebil, Companion Studies to the History of Tamil Literature (1992)."),
 ("Kodava", ["Category:Kodava language", "Category:Kodagu district"],
  "The language of Kodagu (Coorg) in the Western Ghats, written in Kannada script. Its speakers "
  "hold a distinct legal status in India: the Kodava are among very few communities exempt from "
  "the Arms Act, permitted to keep firearms without licence.",
  "Census of India 2011; Ebert, Kodava (1996)."),
 ("Badaga", ["Category:Badaga language", "Category:Nilgiris"],
  "Of the Nilgiri hills, and closest to Kannada although its speakers live among Toda, Kota and "
  "Kurumba. The Nilgiris are a classic case of a small plateau holding four unrelated-enough "
  "languages in daily contact and a stable division of labour between the communities.",
  "Census of India 2011; Hockings and Pilot-Raichoor, A Badaga-English Dictionary (1992)."),
 ("Pengo", ["Category:Dravidian languages", "Category:Odisha"],
  "A Central Dravidian language of Odisha, spoken by a few hundred thousand people and described "
  "in a single major grammar. Central Dravidian is the least documented part of the family "
  "relative to its size.",
  "Burrow and Bhattacharya, The Pengo Language (1970); Census of India 2011."),
 # ---------------- AUSTROASIATIC
 ("Central Khmer", ["Category:Khmer language", "Category:Khmer script"],
  "The language of Cambodia, written in a Brahmic script since the seventh century — its oldest "
  "dated inscription, from 611, is the earliest written Khmer and among the earliest writing in "
  "mainland Southeast Asia. Khmer has no tones, unlike Thai and Vietnamese around it, and the "
  "largest alphabet in the world by letter count in the Guinness reckoning.",
  "National Institute of Statistics, Cambodia 2019 census; Jenner, Old Khmer inscriptions."),
 ("Mon", ["Category:Mon language", "Category:Mon script"],
  "The language of a civilisation that shaped mainland Southeast Asia and then lost its states: "
  "the Mon script is the ancestor of Burmese writing, and Mon Buddhism and statecraft were "
  "adopted wholesale by the Burmese and the Thai. Mon inscriptions from the sixth century are "
  "among the oldest in the region; its speakers are now a minority in Myanmar and Thailand.",
  "Ethnologue 2024; Bauer, Notes on Mon Epigraphy (1991)."),
 ("Khasi", ["Category:Khasi language", "Category:Meghalaya"],
  "An Austroasiatic language in northeast India, a thousand kilometres from its nearest "
  "relatives in Southeast Asia — an isolated survival of a family that once stretched across the "
  "subcontinent. Khasi society is matrilineal, and the language is one of Meghalaya's associate "
  "official languages.",
  "Census of India 2011; Nagaraja, Khasi: A Descriptive Analysis (1985)."),
 ("Northern Khmer", ["Category:Northern Khmer", "Category:Surin Province"],
  "The Khmer of northeastern Thailand, separated from Cambodian Khmer by a border drawn in the "
  "colonial period and by Thai schooling since. It has taken on Thai tones, which Cambodian "
  "Khmer does not have.",
  "Ethnologue 2024; Thailand National Statistical Office."),
 ("Santali", ["Category:Santali language", "Category:Ol Chiki"],
  "The largest Munda language, spoken across Jharkhand, West Bengal and Odisha, and written in "
  "Ol Chiki — an alphabet devised by Raghunath Murmu in 1925 specifically for it, because Indic "
  "scripts fit its consonants badly. Santali entered the Eighth Schedule of the Indian "
  "constitution in 2003 and Ol Chiki is now taught in state schools.",
  "Census of India 2011; Constitution (Ninety-second Amendment) Act 2003."),
 # ---------------- TAI-KADAI
 ("Lao", ["Category:Lao language", "Category:Lao script"],
  "The national language of Laos, written in a script closely related to Thai and descended from "
  "the same Khmer model. There are more Lao speakers in northeastern Thailand — where the "
  "language is called Isan and written in Thai script — than in Laos itself.",
  "Lao Statistics Bureau 2015 census; Ethnologue 2024."),
 ("Northern Thai", ["Category:Northern Thai language", "Category:Tai Tham script"],
  "Kam Mueang, the language of the old Lanna kingdom around Chiang Mai, written in Tai Tham — a "
  "script used for Buddhist manuscripts on palm leaf across northern Thailand, Laos and the Shan "
  "states, and encoded in Unicode in 2009.",
  "Ethnologue 2024; Unicode 5.2 (2009) for the Tai Tham block."),
 ("Southern Thai", ["Category:Southern Thai language", "Category:Southern Thailand"],
  "The Thai of the peninsula, distinct enough in tone and vocabulary to be hard going for "
  "Bangkok speakers, and in contact with Malay along its southern edge.",
  "Ethnologue 2024; Thailand National Statistical Office."),
 ("Yongbei Zhuang", ["Category:Zhuang languages", "Category:Sawndip"],
  "The largest Zhuang variety, in Guangxi. Zhuang was written for a thousand years in Sawndip — "
  "characters built on the Chinese model but invented locally, never standardised, and estimated "
  "at over ten thousand distinct signs. A Latin orthography was imposed in 1957 and revised in "
  "1982; Sawndip is still used in ritual texts.",
  "Ethnologue 2024; Holm, Mapping the Old Zhuang Character Script (2013)."),
 # ---------------- MANDE
 ("Bambara", ["Category:Bambara language", "Category:N'Ko script"],
  "The everyday language of Mali, spoken by far more people than have it as a mother tongue. It "
  "is one of the Manding languages, which include Maninka and Dyula and are close enough to form "
  "a continuum from Senegal to Burkina Faso. Manding is also the language of the N'Ko alphabet, "
  "devised by Solomana Kanté in 1949 after he read a claim that African languages were "
  "unwritable.",
  "Institut National de la Statistique, Mali; Ethnologue 2024."),
 ("Susu", ["Category:Susu language", "Category:Guinea"],
  "The coastal language of Guinea and a lingua franca around Conakry, written in Latin letters "
  "and in Arabic script. Mande languages are the ones most associated with the griot tradition — "
  "hereditary oral historians whose repertoire includes the Sunjata epic of the Mali empire.",
  "Institut National de la Statistique, Guinea; Ethnologue 2024."),
 # ---------------- UTO-AZTECAN
 ("Central Guerrero Nahuatl", ["Category:Nahuatl", "Category:Nahuatl manuscripts"],
  "One of some thirty Nahuatl languages. Classical Nahuatl was the administrative language of "
  "the Aztec empire and then, for two centuries, of Spanish colonial administration too — more "
  "was printed in Nahuatl in the sixteenth century than in most European vernaculars, and the "
  "Florentine Codex is a twelve-volume encyclopedia compiled in it by Nahua scholars.",
  "INEGI 2020 census; Sahagún, Florentine Codex (1577), Biblioteca Medicea Laurenziana."),
 ("Mayo", ["Category:Mayo language", "Category:Sonora"],
  "Of Sonora and Sinaloa in northwest Mexico, and close to Yaqui. Both are Cahitan languages, "
  "and the Jesuit grammars written for them in the seventeenth century are among the earliest "
  "descriptions of any language of northern Mexico.",
  "INEGI 2020 census; Ethnologue 2024."),
 # ---------------- ARAWAKAN
 ("Asháninka", ["Category:Asháninka", "Category:Peruvian Amazon"],
  "The largest indigenous language of the Peruvian Amazon, in the eastern Andean foothills. "
  "Arawakan is one of the most widely spread families in South America — its languages reached "
  "from the Caribbean to Bolivia, and Taíno, the first American language Europeans recorded, was "
  "one of them.",
  "INEI Peru 2017 census; Ethnologue 2024."),
 ("Wapishana", ["Category:Wapishana", "Category:Rupununi"],
  "Of the Rupununi savanna on the Guyana–Brazil border, and one of the northern Arawakan "
  "languages that survived the collapse of the Caribbean Arawak world. Its speakers are "
  "surrounded by Cariban languages.",
  "Ethnologue 2024; Guyana Bureau of Statistics."),
 # ---------------- TUPIAN
 ("Sateré-Mawé", ["Category:Sateré-Mawé", "Category:Amazonas (Brazilian state)"],
  "A Tupian language of the lower Amazon, and the only surviving member of its branch. The "
  "Sateré-Mawé domesticated guaraná, and the word is theirs.",
  "IBGE 2010 census; Ethnologue 2024."),
 ("Kamayurá", ["Category:Kamayurá", "Category:Xingu Indigenous Park"],
  "A Tupi-Guarani language of the Upper Xingu, one of a dozen languages from four unrelated "
  "families spoken in a single multilingual cultural system where communities intermarry across "
  "language lines and everyone is multilingual by design.",
  "Seki, Gramática do Kamaiurá (2000); IBGE 2010 census."),
]



# ---------------------------------------------------------------------------
# EXTRA OBJECTS, from measured Commons categories rather than authored guesses.
#
# probe_categories.py asks Commons which categories actually exist for each of these languages
# and how many files each holds; 291 do, across 138 languages. Those are appended here as extra
# gallery subjects so a card can hold four or five objects instead of one.
#
# THE PRIORITY ORDER IS THE CURATION. This is a museum of language, so a page of writing beats a
# photograph of a market. `<Language> people` and `<Language> culture` categories are large and
# tempting and mostly contain portraits and festivals — real, but about the speakers rather than
# the speech. They are used last, and capped at one object, so that a card leads with script,
# manuscript and inscription where those exist and only falls back to context when they do not.
# ---------------------------------------------------------------------------
CAT_RANK = ["manuscripts", "inscriptions", "calligraphy", "script", "alphabet",
            "Books in", "Newspapers in", "Manuscripts in", "Inscriptions in", "Texts in",
            "literature", "language"]
CAT_MAX = 3            # extra categories queried per language
CONTEXT_MAX = 0        # see ADMISSIBLE_SUBJECT: none, now


# ⚠ AN EMPTY CASE IS BETTER THAN A WRONG EXHIBIT, and this is the rule that enforces it.
#
# The plate for Atlantic-Congo — the largest family in the atlas — was an MTN WiFi hotspot
# billboard. Araucanian's was a swimming pool. Bavarian's was a photograph of an egg with two
# words written on it. Abkhaz, Aguaruna, Aja, Bemba and Berom all led with a portrait of somebody
# whose connection to the language is that they were filed in the same Commons category.
#
# Two sources did that. `Category:<Language> people` and `<Language> culture` are portraits and
# festivals — about the speakers rather than the speech — and are no longer queried at all.
# And several BARE PLACE categories were authored here as fallbacks: Category:Chile,
# Category:Papua New Guinea, Category:Mali. A place category holds landscapes, and a landscape
# illustrates nothing about a language. Those are refused too, wherever they were written.
#
# What stays: an authored query for a NAMED ARTEFACT, and any category about writing. The bare
# `<Language> language` category is a grab-bag that holds both a Visayan-script page and a
# generating station, so it stays admissible and is audited by eye instead (audit_gallery.py).
_WRITING = re.compile(r"(script|alphabet|inscriptions?|manuscripts?|calligraphy|literature"
                      r"|^Category:(Books|Newspapers|Texts|Manuscripts|Inscriptions) in )",
                      re.I)
_PEOPLE = re.compile(r"\b(people|culture)$", re.I)
_LANGCAT = re.compile(r"\blanguages?$", re.I)


# SINGULAR vs PLURAL, and it decides who the category belongs to. `Category:Chakma language` is
# that language's own; `Category:Iranian languages` is a whole branch, and anything in it will be
# about SOME Iranian language — which for a family card is right and for a single language is a
# mis-file. Alviri-Vidari, a language of two villages in Qazvin, was given the Shughni alphabet
# of 1931 through exactly this route.
_LANGCAT_ONE = re.compile(r"\blanguage$", re.I)


# Categories about a macro-language in general, which its varieties must not inherit.
_MACRO = re.compile(r"^Category:(Arabic|Chinese|Malay|Quechua|Persian|Berber|Romani)"
                    r"\s+(language|calligraphy|script)$", re.I)


def admissible_subject(s: str, is_family: bool = False, lang_name: str = "") -> bool:
    """Is this subject allowed to contribute an object at all?"""
    # A category that IS the language's own name. Commons files variety categories without
    # the word "language" — `Category:Algerian Arabic`, not `Category:Algerian Arabic
    # language` — so the rules below refused every one of them, and the five big Arabic
    # varieties fell back to `Category:Arabic language` and were served identical images.
    # An exact name match is precise enough that it cannot let a place category in.
    if lang_name and s == "Category:" + lang_name:
        return True
    if not s.startswith("Category:"):
        # An authored free-text query is TRUSTED — no title filter is applied to it — so it
        # must name an artefact precisely. Two ways this has gone wrong, both mine:
        #   * a PLACE. "Malgana Shark Bay" returned a nineteenth-century French engraving
        #     of shelters, which is what a place query always finds.
        #   * a COMMON NOUN. "<Language> bible" looks specific and is not: Commons matches
        #     "bible" across everything, so "Izi bible" returned three European baroque
        #     paintings of Solomon and the Ark, and "Ewe bible" returned Sahara sand dunes.
        #     Five of seven such queries were retired in one audit.
        # Name the object: "Isoama-Ibo Primer", "Yirrkala bark petitions", "Rabatak
        # inscription". Those work.
        return True
    # A MACRO-LANGUAGE CATEGORY MUST NOT BE ATTACHED TO ONE OF ITS VARIETIES. This is the
    # singular-form cousin of the plural rule below, and it is worse in practice, because it
    # looks right. `Category:Arabic language` on Algerian, Moroccan, Sudanese, Tunisian and
    # Chadian Arabic returned THE SAME THREE FILES to all five — an inscription panel, a shelf
    # of surgery books, and a graphic captioned "Azerbaijan" in three scripts, which is about
    # Azerbaijani. `Category:Arabic calligraphy` did the same to Levantine. A category about a
    # language IN GENERAL has nothing in it about any one variety.
    if _MACRO.search(s):
        return False
        return True
    if _PEOPLE.search(s):
        return False                      # portraits and festivals
    if _WRITING.search(s):
        return True
    if _LANGCAT_ONE.search(s):
        return True                       # the grab-bag, audited by eye; a place category is not
    # plural: a family-wide category, admissible only on a family card
    return is_family and bool(_LANGCAT.search(s))


def _rank(title: str) -> int:
    t = title[len("Category:"):]
    for i, key in enumerate(CAT_RANK):
        if t.startswith(key + " ") or t.endswith(" " + key) or t.endswith(key):
            return i
    return len(CAT_RANK)


def extra_subjects(gc: str, cats: dict) -> list[str]:
    rows = cats.get(gc) or []
    ordered = sorted(rows, key=lambda r: (_rank(r[0]), -r[1]))
    out, context = [], 0
    for title, n in ordered:
        if not admissible_subject(title):
            continue
        is_ctx = False
        out.append(title)
        context += 1 if is_ctx else 0
        if len(out) >= CAT_MAX:
            break
    return out


# ---------------------------------------------------------------------------
# SOURCE NOTES, KEYED BY NAME
#
# A label may carry its citation as a fourth tuple element. The 83 Indo-European labels below
# were authored before that field existed, and rewriting 83 working tuples by hand is exactly
# the kind of mechanical edit that has twice clobbered adjacent code in this project. So they
# live here instead, resolved the same way — by exact Glottolog name — and merged in `main`.
# Source notes for the 83 Indo-European labels authored before the citation field existed.
# Keyed by exact Glottolog name, resolved by machine. These are the earliest labels in the
# project and therefore the biggest languages in the family — the ones a reader is most likely
# to check.
SRC = {
 "English": "Speaker figure Ethnologue 2024; the loan proportions are the counts in the Shorter "
            "Oxford English Dictionary's etymological survey.",
 "Hindi": "Census of India 2011 for the mother-tongue return; Ethnologue 2024 for the total. The "
          "two differ because the census counts Hindi as a group of some fifty varieties.",
 "Bengali": "Bangladesh Bureau of Statistics 2022 census and Census of India 2011, combined.",
 "Portuguese": "IBGE 2022 for Brazil, INE Portugal 2021, and national censuses for the African "
               "Lusophone states.",
 "Russian": "Russian Federal Census 2021 for the domestic figure; Ethnologue 2024 for the total "
            "including the near abroad.",
 "Spanish": "Instituto Cervantes, El español en el mundo 2023, for the global figure. The number "
            "shown here is the narrower first-language count.",
 "Marathi": "Census of India 2011.",
 "French": "Observatoire de la langue française (OIF) 2022 for the global count; INSEE for France.",
 "Urdu": "Pakistan Census 2023 for the national figure, which counts Urdu as a first language for "
         "far fewer people than speak it.",
 "Italian": "ISTAT 2015 language-use survey; Ethnologue 2024 for the total.",
 "German": "Destatis and the Council for German Orthography's 2023 estimate across the German-"
           "speaking states.",
 "Gujarati": "Census of India 2011.",
 "Western Farsi": "Ethnologue 2024. Persian is counted here as three languages after ISO — "
                  "Iranian, Dari and Tajik — which no Persian speaker would recognise.",
 "Polish": "Statistics Poland (GUS) 2021 census.",
 "Odia": "Census of India 2011. Odia was recognised a classical language of India in 2014.",
 "Ukrainian": "Ukrainian census 2001, the last completed; Ethnologue 2024 for the current "
              "estimate. Wartime displacement makes any present figure provisional.",
 "Sindhi": "Pakistan Census 2023 and Census of India 2011.",
 "Romanian": "Romanian census 2021 and Moldovan census 2014.",
 "Dutch": "Nederlandse Taalunie 2023, covering the Netherlands, Flanders and Suriname.",
 "Northern Pashto": "Ethnologue 2024. No Afghan census has been completed since 1979, so every "
                    "Pashto figure is an estimate built on projection.",
 "Serbian-Croatian-Bosnian": "Combined national censuses: Serbia 2022, Croatia 2021, Bosnia and "
                             "Herzegovina 2013, Montenegro 2023. Glottolog treats these as one "
                             "language; four states do not.",
 "Nepali": "Nepal census 2021 and Census of India 2011.",
 "Sinhala": "Sri Lanka Department of Census and Statistics 2012.",
 "Assamese": "Census of India 2011.",
 "Northern Kurdish": "Ethnologue 2024. Turkey does not enumerate Kurdish in its census, so the "
                     "Turkish share is estimated rather than counted.",
 "Tajik": "Tajikistan census 2020.",
 "Czech": "Czech Statistical Office 2021 census.",
 "Bulgarian": "Bulgarian National Statistical Institute 2021 census.",
 "Afrikaans": "Statistics South Africa 2022 census. Afrikaans is the first language of more "
              "coloured South Africans than white ones, a fact its political history obscures.",
 "Kashmiri": "Census of India 2011.",
 "Danish": "Statistics Denmark 2023.",
 "Norwegian": "Statistics Norway 2023. The figure covers both written standards, Bokmål and "
              "Nynorsk, which are norms for writing rather than separate spoken languages.",
 "Belarusian": "Belarus census 2019. The census asks separately about mother tongue and language "
               "spoken at home, and the two answers differ by several million.",
 "Catalan": "Generalitat de Catalunya, Enquesta d'usos lingüístics 2018, plus Valencia and the "
            "Balearics.",
 "Swedish": "Statistics Sweden 2023 and Statistics Finland 2023 for the Finland-Swedish minority.",
 "Galician": "Instituto Galego de Estatística, Enquisa de condicións de vida 2018.",
 "Western Frisian": "Provinsje Fryslân language survey 2020.",
 "Welsh": "Wales census 2021, which recorded a fall from 2011 — the first since the language's "
          "revival began.",
 "Icelandic": "Statistics Iceland 2023.",
 "Breton": "Office public de la langue bretonne, enquête sociolinguistique 2018.",
 "Faroese": "Statistics Faroe Islands 2023.",
 "Scottish Gaelic": "Scotland census 2011 and the 2022 return; the Gaelic Crisis report (Ó "
                    "Giollagáin et al., 2020) for the community-level assessment.",
 "Occitan": "Ofici public de la lenga occitana sociolinguistic survey 2020. Estimates for Occitan "
            "range across an order of magnitude depending on what counts as a speaker.",
 "Sanskrit": "Census of India 2011, which recorded 24,821 people returning Sanskrit as a mother "
             "tongue — a number that says more about identity than about daily use.",
 "Upper Sorbian": "Sorbian Institute, Bautzen, 2021 estimate.",
 "Manx": "Isle of Man census 2021. The last native speaker, Ned Maddrell, died in 1974; every "
         "speaker counted now learned it.",
 "Old Prussian": "Ethnologue 2024 for the revival community. The language itself died about 1700; "
                 "it is known from three catechisms and the Elbing vocabulary.",
 "Hittite": "Hoffner and Melchert, A Grammar of the Hittite Language (2008); the Chicago Hittite "
            "Dictionary for the lexicon.",
 "Gheg Albanian": "Ethnologue 2024; Kosovo Agency of Statistics 2011 census.",
 "Classical-Middle Armenian": "Thomson, An Introduction to Classical Armenian (1989); the "
                              "Matenadaran manuscript catalogue for the textual record.",
 "Tokharian A": "Adams, A Dictionary of Tocharian B (2013), and Malzahn, The Tocharian Verbal "
                "System (2010). The manuscripts are in the Berlin Turfan collection.",
 "Northern Tosk Albanian": "Albanian census 2023.",
 "Eastern Armenian": "Armenian census 2011 and Ethnologue 2024.",
 "Umbrian": "Poultney, The Bronze Tables of Iguvium (1959); Untermann, Wörterbuch des "
            "Oskisch-Umbrischen (2000).",
 "Oscan": "Buck, A Grammar of Oscan and Umbrian (1904), still the standard English grammar; "
          "Crawford, Imagines Italicae (2011) for the inscriptions.",
 "Lithuanian": "Statistics Lithuania 2021 census.",
 "Latvian": "Central Statistical Bureau of Latvia 2021 census.",
 "Gothic": "The Codex Argenteus at Uppsala; Wright, Grammar of the Gothic Language (2nd ed. 1954); "
           "Lehmann, A Gothic Etymological Dictionary (1986).",
 "Avestan": "Hoffmann and Forssman, Avestische Laut- und Flexionslehre (1996); Bartholomae, "
            "Altiranisches Wörterbuch (1904).",
 "Latin": "Oxford Latin Dictionary; the Thesaurus Linguae Latinae for the full record.",
 "Slovak": "Statistical Office of the Slovak Republic 2021 census.",
 "Church Slavic": "Lunt, Old Church Slavonic Grammar (7th ed. 2001); the Codex Zographensis and "
                  "Codex Marianus for the canon.",
 "Slovenian": "Statistical Office of the Republic of Slovenia 2021.",
 "Ionic-Attic Ancient Greek": "Liddell–Scott–Jones, A Greek–English Lexicon (9th ed. with 1996 "
                              "supplement); Smyth, Greek Grammar (1920).",
 "Old Persian (ca. 600-400 B.C.)": "Kent, Old Persian: Grammar, Texts, Lexicon (2nd ed. 1953); "
                                   "Schmitt, Wörterbuch der altpersischen Königsinschriften (2014).",
 "Old Norse": "Cleasby–Vigfusson, An Icelandic–English Dictionary (1874); the Codex Regius for the "
              "Poetic Edda.",
 "Early Irish": "The Dictionary of the Irish Language (Royal Irish Academy, 1913–76), and its "
                "revised electronic edition eDIL; Thurneysen, A Grammar of Old Irish (1946).",
 "Macedonian": "State Statistical Office of North Macedonia 2021 census.",
 "Bactrian": "Sims-Williams, Bactrian Documents from Northern Afghanistan (1999–2012), and his "
             "edition of the Rabatak inscription (1996).",
 "Khotanese": "Bailey, Dictionary of Khotan Saka (1979); Emmerick, A Guide to the Literature of "
              "Khotan (2nd ed. 1992).",
 "Old High German (ca. 750-1050)": "Braune and Reiffenstein, Althochdeutsche Grammatik (2004); the "
                                   "Althochdeutsches Wörterbuch (Leipzig, in progress since 1952).",
 "Old Saxon": "Tiefenbach, Altsächsisches Handwörterbuch (2010); the Heliand manuscripts in London "
              "and Munich.",
 "Logudorese Sardinian": "Ethnologue 2024; Regione Autonoma della Sardegna sociolinguistic survey "
                         "2007, the last full one.",
 "Old English (ca. 450-1100)": "Bosworth–Toller, An Anglo-Saxon Dictionary, and the Dictionary of "
                               "Old English (Toronto, in progress); Mitchell and Robinson, A Guide "
                               "to Old English (8th ed. 2012).",
 "Cornish": "Wales and England census 2021 for the speaker return; Cornish Language Office "
            "estimates for fluent speakers, which are much lower.",
 "Modern Greek": "Hellenic Statistical Authority 2021 census and Ethnologue 2024.",
 "Iron Ossetian": "Russian Federal Census 2021; Thordarson, Ossetic Grammatical Studies (2009).",
 "Sogdian": "Gharib, Sogdian Dictionary (1995); Sims-Williams, The Sogdian Ancient Letters (2001).",
 "Eastern Yiddish": "Ethnologue 2024. The figure is rising rather than falling — Haredi "
                    "communities in New York, London, Antwerp and Jerusalem raise children in it.",
 "Venetian": "ISTAT 2015 language-use survey, which found Venetian the most-spoken regional "
             "language in Italy after Neapolitan.",
 "Central Kurdish": "Ethnologue 2024; Kurdistan Region Statistics Office.",
 "Middle English": "The Middle English Dictionary (Michigan, 1952–2001), now online; the Hengwrt "
                   "and Ellesmere manuscripts for Chaucer.",
 "Old French (842-ca. 1400)": "Godefroy, Dictionnaire de l'ancienne langue française (1881–1902); "
                              "Tobler–Lommatzsch, Altfranzösisches Wörterbuch.",
}
# ---------------------------------------------------------------------------

def main() -> None:
    names: dict[str, list] = {}
    with open(GL, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["Level"] == "language":
                names.setdefault(r["Name"], []).append(r["ID"])
    cp = os.path.join(ROOT, "data", "gallery", "categories.json")
    cats = json.load(open(cp, encoding="utf-8")) if os.path.exists(cp) else {}
    out, expect, subjects, bad = {}, {}, [], []
    sources: dict[str, str] = {}
    nextra = 0
    for entry in E:
        nm, terms, text = entry[0], entry[1], entry[2]
        src = entry[3] if len(entry) > 3 else SRC.get(nm, "")
        hit = names.get(nm)
        if not hit:
            bad.append(f"{nm!r}: no language of that name in Glottolog")
            continue
        if len(hit) > 1:
            bad.append(f"{nm!r}: ambiguous, {len(hit)} languages share the name")
            continue
        gc = hit[0]
        out[gc] = text
        if src:
            sources[gc] = src
        # the gate's keyword: the most distinctive word of the Glottolog name itself
        expect[gc] = max(nm.replace("(", " ").replace(")", " ").split(), key=len)
        # `terms` may be one query or several. Several means several objects on the card.
        for q in ([terms] if isinstance(terms, str) else terms):
            if admissible_subject(q, lang_name=nm):
                subjects.append((gc, q))
        for q in extra_subjects(gc, cats):
            subjects.append((gc, q))
            nextra += 1
    # OBJECTS FOR LANGUAGES WITH NO LABEL. The probe now covers every language documented enough
    # that Commons plausibly holds something — its own Wikipedia, a text here, a recording, a
    # curated alphabet — not just the 283 with authored prose. Those extras get category subjects
    # too, which is the difference between 242 languages with an object and several hundred.
    # A label-less language gets fewer, because it has no authored artefact query to lead with and
    # a category alone is the weaker signal.
    unlabelled = 0
    for gc, rows in sorted(cats.items()):
        if gc in out:
            continue
        qs = extra_subjects(gc, cats)[:2]
        if not qs:
            continue
        for q in qs:
            subjects.append((gc, q))
        unlabelled += 1
    print(f"  {unlabelled} languages with no authored label were given category subjects")

    # A SRC key matching no label is a typo that would otherwise vanish silently, since the
    # notes are looked up by name and a miss just leaves the label uncited.
    for u in sorted(set(SRC) - {e[0] for e in E}):
        bad.append(f"{u!r}: source note matching no label")
    for b in bad:
        print("  SKIPPED " + b)
    d = os.path.join(ROOT, "web", "data")
    json.dump({"note": "Authored museum labels. `sources` carries a citation note for the "
                       "labels that have one — what the checkable claims rest on.",
               "expect": expect, "sources": sources, "by_glottocode": out},
              open(os.path.join(d, "notable.json"), "w"), ensure_ascii=False,
              separators=(",", ":"))
    # Its OWN file. This used to be a single shared subjects.json that build_families.py
    # appended to, which made the two builders order-dependent with nothing enforcing the
    # order. Running this one second wiped the family subjects, and the next fetch then
    # dropped 22 licence-verified, eye-audited family plates out of the manifest — the
    # image files still on disk, just no longer reachable. Two files, no order.
    json.dump(subjects,
              open(os.path.join(ROOT, "data", "gallery", "subjects_languages.json"), "w"),
              ensure_ascii=False)
    print(f"   {len(sources)} labels carry a source note")
    print(f"{len(out)} labels resolved, {len(bad)} skipped · "
          f"{len(subjects)} gallery subjects queued "
          f"({nextra} of them measured Commons categories across "
          f"{len([1 for gc in out if extra_subjects(gc, cats)])} languages)")


if __name__ == "__main__":
    main()
