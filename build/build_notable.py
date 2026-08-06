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


def admissible_subject(s: str) -> bool:
    """Is this subject allowed to contribute an object at all?"""
    if not s.startswith("Category:"):
        return True                       # an authored query for a named artefact
    if _PEOPLE.search(s):
        return False                      # portraits and festivals
    if _WRITING.search(s):
        return True
    return bool(_LANGCAT.search(s))       # the grab-bag, audited by eye; a place category is not


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
        src = entry[3] if len(entry) > 3 else ""
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
            if admissible_subject(q):
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

    for b in bad:
        print("  SKIPPED " + b)
    d = os.path.join(ROOT, "web", "data")
    json.dump({"note": "Authored museum labels. `sources` carries a citation note for the "
                       "labels that have one — what the checkable claims rest on.",
               "expect": expect, "sources": sources, "by_glottocode": out},
              open(os.path.join(d, "notable.json"), "w"), ensure_ascii=False,
              separators=(",", ":"))
    json.dump(subjects, open(os.path.join(ROOT, "data", "gallery", "subjects.json"), "w"))
    print(f"   {len(sources)} labels carry a source note")
    print(f"{len(out)} labels resolved, {len(bad)} skipped · "
          f"{len(subjects)} gallery subjects queued "
          f"({nextra} of them measured Commons categories across "
          f"{len([1 for gc in out if extra_subjects(gc, cats)])} languages)")


if __name__ == "__main__":
    main()
