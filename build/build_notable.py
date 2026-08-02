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
]


def main() -> None:
    names: dict[str, list] = {}
    with open(GL, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["Level"] == "language":
                names.setdefault(r["Name"], []).append(r["ID"])
    out, expect, subjects, bad = {}, {}, [], []
    for nm, terms, text in E:
        hit = names.get(nm)
        if not hit:
            bad.append(f"{nm!r}: no language of that name in Glottolog")
            continue
        if len(hit) > 1:
            bad.append(f"{nm!r}: ambiguous, {len(hit)} languages share the name")
            continue
        gc = hit[0]
        out[gc] = text
        # the gate's keyword: the most distinctive word of the Glottolog name itself
        expect[gc] = max(nm.replace("(", " ").replace(")", " ").split(), key=len)
        subjects.append((gc, terms))
    for b in bad:
        print("  SKIPPED " + b)
    d = os.path.join(ROOT, "web", "data")
    json.dump({"note": "Authored museum labels.", "expect": expect, "by_glottocode": out},
              open(os.path.join(d, "notable.json"), "w"), ensure_ascii=False,
              separators=(",", ":"))
    json.dump(subjects, open(os.path.join(ROOT, "data", "gallery", "subjects.json"), "w"))
    print(f"{len(out)} labels resolved, {len(bad)} skipped · "
          f"{len(subjects)} gallery subjects queued")


if __name__ == "__main__":
    main()
