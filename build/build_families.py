#!/usr/bin/env python3
"""build_families.py — a card for every family, and the reason its languages have the names
they do. Register D14.

WHY THIS EXISTS. Open Otomanguean and you get 181 languages, of which 56 end in "Zapotec" and 53
in "Mixtec": Juxtlahuaca Mixtec, Amoltepec Mixtec, Chazumba Mixtec, Silacayoapan Mixtec. Nothing
on screen explained that, and it is the single most confusing thing about the tree. The answer is
a real fact about the world rather than a quirk of our data: "Mixtec" is a cover term, the varieties
under it are not mutually intelligible, so Glottolog and ISO both treat them as separate languages
and name each one after the town it is spoken in.

SO THE PATTERN IS MEASURED, NOT AUTHORED. For every node in every family tree, count how many of
its descendant languages share the same final word in their name. 24 families show it over 789
languages — Quechuan 42 of 43, Otomanguean 155 of 181, Dogon 17 of 20, Sino-Tibetan's 42 Naga and
20 Chin. Authoring that per family would have covered Mixtec and missed the other twenty-three.

⚠ THE PARENTHETICAL MUST COME OFF FIRST. Glottolog disambiguates with a trailing bracket —
"Murik (Malaysia)", "Aja (Benin)" — and taking the last word of the raw name reported "Malaysia"
and "Indonesia" as though they were language clusters.

WHAT ELSE IS ON A FAMILY CARD, all of it measured from what this build already ships: how many
languages, dialects, extinct and endangered; where it is; its earliest attested member; its root
age where a dated phylogeny exists; and HOW MUCH OF THE MUSEUM IT HAS — labels, objects,
recordings, letters, prose. That last row is a coverage statement, so a thin family says it is thin
instead of looking complete.

The authored description is keyed by EXACT GLOTTOLOG NAME and resolved by machine, refusing
anything unmatched or ambiguous — the same discipline as build_notable.py, for the same reason.

Run AFTER build_notable.py: this appends its gallery subjects to the file that one writes.
    python3 build_notable.py && python3 build_families.py
"""
from __future__ import annotations

import csv
import json
import os
import re
import importlib.util as _ilu
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
WEB = os.path.join(ROOT, "web", "data")
GL = os.path.join(ROOT, "data", "glottolog", "languages.csv")

_spec = _ilu.spec_from_file_location("_bn", os.path.join(HERE, "build_notable.py"))
_bn = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_bn)

MIN_CLUSTER = 5        # below this a shared word is coincidence, not a naming convention
PAREN = re.compile(r"\s*\([^)]*\)\s*$")

# (exact Glottolog family name) -> (commons search terms, description)
FAM: dict[str, tuple[list[str], str]] = {
 "Otomanguean": (["Codex Vindobonensis Mexicanus Mixtec", "Category:Mixtec culture",
                  "Monte Alban Zapotec inscription"],
  "The most internally divided family in the Americas, and the reason this tree looks the way it "
  "does. Its big groups — Zapotec, Mixtec, Chinantec, Mazatec, Otomi — are cover terms, not "
  "languages: the varieties inside each one are often no more mutually intelligible than Spanish "
  "and Portuguese, so each is counted separately and named after the town it is spoken in. "
  "Otomanguean is also tonal throughout, which is unusual in the Americas, and two of its members "
  "wrote: the Zapotec of Monte Albán produced the earliest writing anywhere in the Americas, and "
  "Mixtec kings kept painted genealogies on deerskin screenfold books, eight of which survived "
  "the conquest."),
 "Quechuan": (["Quechua Huarochiri manuscript", "Category:Quechua language", "Inca quipu"],
  "Spread by an empire and then by the church that replaced it. Quechua was the administrative "
  "language of the Inca state, which kept its records on knotted cords rather than in writing, "
  "and Spanish missionaries then standardised and printed it because it was the most efficient "
  "way to preach across the Andes. Nearly every name in this family ends in Quechua or Quichua "
  "and begins with a valley or a province: the family is a chain of local varieties, and the ones "
  "at either end cannot understand each other."),
 "Indo-European": (["Rigveda manuscript", "Behistun inscription",
                    "Category:Indo-European languages"],
  "The first family to be recognised as a family, and the one that created historical "
  "linguistics. William Jones told the Asiatic Society in 1786 that Sanskrit, Greek and Latin "
  "must share a common source; a century of work turned that into a reconstructed parent language "
  "with a sound system, a grammar and a vocabulary. Nobody wrote Proto-Indo-European down — "
  "everything known about it is recovered from its descendants by comparison, which is why the "
  "reconstruction is written with asterisks."),
 "Sino-Tibetan": (["Oracle bone script Shang", "Myazedi inscription",
                   "Category:Sino-Tibetan languages"],
  "Second only to Indo-European in speakers and far less agreed upon in shape. Chinese has 1.4 "
  "billion speakers and the rest of the family has a few hundred languages of a few thousand each, "
  "scattered through the Himalayas and Southeast Asia, many of them described only in the last "
  "fifty years. Naga and Chin are cover terms here, like Mixtec in Otomanguean — 42 and 20 "
  "separate languages named for the hills their speakers live in."),
 "Atlantic-Congo": (["Category:Yoruba culture", "Category:Igbo culture",
                     "Nsibidi", "Category:Bantu languages"],
  "The largest family on earth by number of languages, and the vehicle of the fastest documented "
  "language spread in prehistory: the Bantu expansion carried a few hundred related languages "
  "from Cameroon across a continent in about two thousand years, which is why Swahili in Kenya "
  "and Zulu in South Africa are recognisably relatives. Almost every member has noun classes — "
  "up to twenty grammatical genders, marked by prefixes that agree across the whole sentence."),
 "Austronesian": (["Kedukan Bukit inscription", "Category:Javanese script",
                   "Polynesian navigation", "Category:Austronesian languages"],
  "The family that crossed the most water. From Taiwan, its speakers reached Madagascar and Easter "
  "Island — half the circumference of the planet — in canoes, before anyone else attempted open "
  "ocean at that scale. Malagasy off the coast of Africa is closest to a language of Borneo, which "
  "is how the voyage was traced. The oldest and deepest divisions are all still in Taiwan; "
  "everything from the Philippines outward is one late branch."),
 "Afro-Asiatic": (["Rosetta Stone", "Category:Ethiopic manuscripts",
                   "Quran manuscript Kufic", "Category:Semitic languages"],
  "The family with the longest written record of any: Ancient Egyptian appears about 3200 BCE and "
  "Akkadian shortly after, so this family has been on the page for five thousand years. Its "
  "Semitic branch built the first alphabet, from which Greek, Latin, Arabic, Hebrew, Ethiopic and "
  "every script descended from them come. Its other branches — Cushitic, Chadic, Berber, Omotic — "
  "are mostly unwritten and mostly undescribed, and Omotic's membership is still argued about."),
 "Nuclear Trans New Guinea": (["Category:Papua New Guinea", "Category:New Guinea Highlands"],
  "The largest family of the world's most linguistically dense place. New Guinea holds around a "
  "fifth of all human languages on under a hundredth of its land, in valleys where a day's walk "
  "changes the language. Most members were first described after 1950, many have no written "
  "tradition at all, and the family's boundaries are still being revised — which is why the "
  "documentation field on this map reads thin here even though the language field reads dense."),
 "Pama-Nyungan": (["Category:Australian Aboriginal culture", "Category:Aboriginal Australians"],
  "One family covering seven-eighths of a continent, which is unusual: everywhere else, long "
  "occupation produces deep diversity, and Australia has been occupied for 65,000 years. The "
  "explanation is that Pama-Nyungan spread comparatively recently across ground that held "
  "something older. It is also the most damaged family in this atlas — 170 of its 250 languages "
  "are recorded here as extinct, almost all of them within the last two centuries."),
 "Austroasiatic": (["Category:Khmer inscriptions", "Category:Vietnamese language",
                    "Category:Munda people"],
  "Split in two by later arrivals. Its western branch is in India, its eastern in Southeast Asia, "
  "and the Tai and Burmese speakers who moved in between them are the reason. Two members carry "
  "long written traditions — Khmer has the longest continuous inscriptional record in Southeast "
  "Asia, from 611, and Vietnamese has been written three different ways — while most of the "
  "family has never been written at all."),
 "Tai-Kadai": (["Category:Thai inscriptions", "Category:Zhuang people",
                "Category:Tai peoples"],
  "A family that moved south out of what is now southern China within the last two thousand "
  "years, and whose largest member is now a national language of Thailand. Almost all members are "
  "tonal with heavy syllable structure, and the family was long misfiled as a branch of "
  "Sino-Tibetan because the vocabulary looks Chinese — it is borrowed, not inherited, which is "
  "the classic trap in language classification."),
 "Dravidian": (["Category:Tamil inscriptions", "Category:Tamil manuscripts",
                "Category:Telugu script"],
  "Older in India than Indo-European, and pushed south by it. Four of its members carry literary "
  "traditions over a thousand years old — Tamil's Sangam poems are the oldest surviving "
  "literature in any living Indian language — and Brahui, far to the northwest in Balochistan, "
  "sits a thousand miles from its nearest relative, which is either a remnant of a wider spread or "
  "a later migration and is still argued."),
 "Uto-Aztecan": (["Florentine Codex", "Category:Nahuatl", "Category:Hopi"],
  "Reaches from Oregon to Nicaragua, and its southern end wrote. Nahuatl was the language of the "
  "Aztec state and then, in Latin letters and by its own speakers, the language of the largest "
  "body of Indigenous-authored colonial documents anywhere in the Americas. Twenty-nine of the "
  "languages here end in Nahuatl: the cover term again, one name per region."),
 "Mayan": (["Dresden Codex Maya", "Category:Maya script", "Category:Maya inscriptions"],
  "The only family in the Americas whose ancient writing is now largely read. Maya script is "
  "logosyllabic — signs for words and signs for syllables in the same block — and its decipherment "
  "took most of the twentieth century, held up for decades by a scholar who insisted the signs "
  "were not phonetic. Its thirty-odd languages are all still spoken, several by hundreds of "
  "thousands of people, and Guatemala's Academy of Mayan Languages sets their orthographies."),
 "Uralic": (["Kalevala manuscript", "Category:Sami people",
             "Category:Hungarian language"],
  "Three national languages and thirty small ones, spread from Norway to Siberia. Hungarian's "
  "nearest relatives are two languages of the Ob river with a few thousand speakers, which is a "
  "distance of some 2,000 miles and about 2,500 years. Eleven names in this family end in Saami — "
  "nine or ten separate languages across four countries, several with fewer than a thousand "
  "speakers."),
 "Turkic": (["Orkhon inscriptions", "Category:Turkic languages", "Category:Uyghur language"],
  "Unusually uniform for its spread: a speaker of Turkish in Istanbul and a speaker of Uzbek in "
  "Tashkent are 3,000 miles apart and can make out a good deal of each other, because the family "
  "expanded fast and recently. Its oldest writing is the Orkhon inscriptions of 732 in a runic "
  "script of its own, and its modern members have changed alphabet more often than any other "
  "family's — Arabic to Latin to Cyrillic and back."),
 "Japonic": (["Kojiki manuscript", "Category:Japanese calligraphy",
              "Category:Ryukyuan languages"],
  "A family of two branches, one with 120 million speakers and one nearly gone. Japanese and the "
  "Ryukyuan languages of Okinawa separated perhaps 1,500 years ago and are not mutually "
  "intelligible; Japan treated the Ryukyuan languages as dialects and schooled children out of "
  "them, and every one is now listed as endangered. The family has no demonstrated relatives, "
  "Korean included, despite a century of attempts."),
 "Eskimo-Aleut": (["Category:Inuit culture", "Category:Canadian Aboriginal syllabics"],
  "One family stretched along five thousand miles of Arctic coast, from Siberia to Greenland, with "
  "so little internal division at its eastern end that Inuit from Alaska and Greenland can partly "
  "understand each other. Its languages build enormous single words out of stacked suffixes, and "
  "one of them — Greenlandic — is the only Indigenous language of the Americas that is the sole "
  "official language of a country."),
 "Athabaskan-Eyak-Tlingit": (["Category:Navajo language", "Category:Tlingit"],
  "A family with a hole in the middle of it. Most members are in Alaska and northwestern Canada; "
  "then there is a gap of 1,500 miles, and then Navajo and Apache in the American Southwest, "
  "which arrived perhaps 600 years ago. Its verbs are among the most complex described anywhere, "
  "and Navajo has more speakers than any other Indigenous language north of Mexico while still "
  "losing child speakers every year."),
 "Algic": (["Category:Cree syllabics", "Category:Ojibwe language"],
  "Covered most of the eastern half of North America at contact, which is why so much English "
  "place-name vocabulary comes from it. Two of its members are written in Canadian syllabics, a "
  "script devised in the 1840s in which a sign's orientation carries its vowel — rotate it and the "
  "vowel changes. Two more, Wiyot and Yurok in California, sit thousands of miles from the rest "
  "and were only shown to belong here in the twentieth century."),
 "Salishan": (["Category:Salishan languages", "Category:Coast Salish"],
  "Famous for words with no vowels in them. Nuxalk permits syllables — and whole words — built "
  "entirely of consonants, which was long held to be impossible. Thirteen of the family's "
  "twenty-five languages are recorded here as extinct and most of the rest have double-digit "
  "speaker counts, so the documentation made in the last century is in many cases all there will "
  "ever be."),
 "Siouan": (["Category:Lakota", "Category:Siouan languages"],
  "The languages of the Plains and of the Mississippi valley before it. Ten of eighteen are gone. "
  "Lakota has the largest remaining community and one of the most active revival programmes in "
  "North America, built on documentation made by speakers themselves rather than only by visiting "
  "linguists."),
 "Cariban": (["Category:Carib people", "Category:Indigenous peoples of the Amazon"],
  "The family that gave English the words canoe, hammock and hurricane, by way of Spanish, and "
  "gave Europe the word cannibal — a mangling of its own name applied by Columbus. Several of its "
  "languages mark whether the speaker witnessed what they are reporting, and one, Hixkaryana, is "
  "the first language ever described with object-verb-subject as its basic order, which had been "
  "assumed not to exist."),
 "Arawakan": (["Category:Arawak", "Category:Taíno"],
  "The most widely spread family in South America before contact, from the Caribbean to Paraguay, "
  "and the first American family Europeans met: Taíno gave Spanish canoa, hamaca, tabaco and "
  "maíz. Thirty-two of its seventy-seven languages here are extinct, most of them within a "
  "century of contact."),
 "Tupian": (["Category:Guaraní language", "Category:Tupi people"],
  "Its coastal member became the general language of colonial Brazil — spoken more widely in the "
  "interior than Portuguese until the crown banned it in 1758 — and its southern member is "
  "co-official with Spanish in Paraguay, the only Indigenous language of the Americas with that "
  "standing. Tupi supplied Portuguese with thousands of words and had a printed grammar by 1595, "
  "before most European vernaculars."),
 "Pano-Tacanan": (["Category:Indigenous peoples of the Amazon", "Category:Peru"],
  "Western Amazonian, and the source of some of the most-cited facts in linguistics: Matsés marks "
  "in its verbs how the speaker knows what they are saying and how long ago they learned it, and "
  "Shipibo-Konibo's designs on cloth and pottery are read by their makers as patterns with "
  "structure. Twenty of forty-five are extinct."),
 "Nuclear-Macro-Je": (["Category:Kayapo", "Category:Indigenous peoples of Brazil"],
  "The family of the Brazilian interior, and the one whose social organisation made anthropologists "
  "rethink kinship. Its speakers live in villages laid out as diagrams of their own moiety "
  "systems. Thirteen of twenty-nine languages here are extinct."),
 "Chibchan": (["Category:Kuna people", "Category:Costa Rica"],
  "Straddles the land bridge between the continents, from Honduras to Colombia, which puts it at "
  "the crossing point for every human movement between North and South America. One member, Kuna, "
  "records history on carved wooden picture-boards read by ritual specialists."),
 "Tucanoan": (["Category:Indigenous peoples of the Amazon", "Category:Vaupés"],
  "The family behind the best-documented case of institutional multilingualism anywhere. In the "
  "Vaupés basin a person must marry outside their own language group, so a household routinely "
  "holds three or four languages and children grow up fluent in all of them — and borrowing "
  "between them is deliberately resisted, because language is what marks who you are."),
 "Mixe-Zoque": (["Category:Olmec", "Category:Mexico"],
  "Small now, and probably very large once: the vocabulary the Olmec left in other Mesoamerican "
  "languages — words for maize, cacao, counting and ritual — looks Mixe-Zoquean, which would make "
  "this the family of Mesoamerica's first civilisation. Mixe and Zoque are both cover terms, seven "
  "and five languages."),
 "Totonacan": (["Category:El Tajín", "Category:Veracruz"],
  "Thirteen languages on the Gulf coast of Mexico, ten of them named Totonac after a town. Its "
  "speakers built El Tajín, and the family is one of the few in Mesoamerica with no established "
  "relatives at all."),
 "Hmong-Mien": (["Category:Hmong people", "Category:Nyiakeng Puachue Hmong"],
  "Mountain languages of southern China and Southeast Asia whose speakers were dispersed further "
  "by twentieth-century war. Written now in several competing systems, including one — Nyiakeng "
  "Puachue Hmong — devised in the 1980s by a Hmong pastor and now in Unicode, and another, Pahawh "
  "Hmong, produced in 1959 by a farmer who was illiterate when he began."),
 "Nakh-Daghestanian": (["Category:Dagestan", "Category:Caucasus"],
  "Thirty-six languages in an area the size of Scotland, several confined to a single village. "
  "Some have four dozen consonants; Tsez has been described with dozens of noun cases depending on "
  "how one counts. This is one of the two places on this map — the Caucasus and New Guinea — where "
  "the language field is genuinely granular rather than thinly surveyed."),
 "Mande": (["Category:N'Ko script", "Category:Mali", "Category:Mandinka people"],
  "West African, and the family that got its own alphabet from one man's decision: Solomana Kanté "
  "devised N'Ko in 1949 after reading a claim that African languages could not be written, and it "
  "is now taught, printed and in Unicode. Mande is also the family whose oral historians, the "
  "jeliw, keep genealogies and epics that are performed rather than written."),
 "Dogon": (["Category:Dogon people", "Category:Bandiagara"],
  "Twenty languages on and below one cliff in Mali, seventeen of them called Dogon after the "
  "village that speaks them. Their speakers are among the most studied peoples in anthropology and "
  "their languages among the least described, which is a common and instructive mismatch."),
 "Khoe-Kwadi": (["Category:Khoisan", "Category:San people"],
  "One of the families behind the click consonants of southern Africa — sounds made by suction "
  "rather than by breath, which occur as ordinary parts of words almost nowhere else on earth. "
  "The old label Khoisan lumped several unrelated families together on that shared trait; it is "
  "not a genealogical unit, and this is one of the pieces it was made of."),
 "Nilotic": (["Category:Maasai", "Category:Dinka people", "Category:Nuer"],
  "East African, and grammatically strange in a specific way: several members change a word's "
  "meaning by changing only the quality of its vowel or the length of it, so number and case are "
  "carried inside the syllable rather than on the end of the word. Dinka may have the most "
  "elaborate vowel system described anywhere."),
 "Central Sudanic": (["Category:Central African Republic", "Category:South Sudan"],
  "Sixty-three languages across the middle of the continent, from Chad to Uganda, and one of the "
  "least documented groups of that size anywhere. Its position in any larger grouping is "
  "unresolved: the old Nilo-Saharan label that contained it is not accepted as a demonstrated "
  "family."),
 "Kru": (["Category:Liberia", "Category:Côte d'Ivoire"],
  "Coastal West African, and the source of the English word Kroo for the sailors recruited from "
  "these communities into the Atlantic trade. Vai, spoken alongside them, carries a syllabary "
  "invented about 1833 by Momolu Duwalu Bukele, who said it came to him in a dream."),
 "Ta-Ne-Omotic": (["Category:Ethiopia", "Category:Omo valley"],
  "Nineteen languages in southwestern Ethiopia whose membership in Afro-Asiatic has been argued "
  "for fifty years and is still not settled — which is why they are listed here as their own "
  "family. The question is not trivial: if Omotic belongs, Afro-Asiatic's homeland moves."),
 "Nubian": (["Category:Nubia", "Category:Old Nubian language"],
  "The family of the Christian kingdoms of the middle Nile, and one of the very few African "
  "families with a medieval written record of its own: Old Nubian was written in a Coptic-derived "
  "alphabet from about the eighth century, which makes it the earliest written language of "
  "sub-Saharan Africa after Ge'ez."),
 "Mongolic-Khitan": (["Category:Mongolian script", "Category:Mongolia"],
  "The family of the largest contiguous land empire in history, and the only one whose main script "
  "is written in vertical lines running left to right. Khitan, its extinct outlier, was written in "
  "two scripts of its own that are still only partly read."),
 "Tungusic": (["Category:Manchu language", "Category:Evenks"],
  "Siberian and Manchurian, and the family with the sharpest fall in this atlas: Manchu was the "
  "language of the dynasty that ruled China for 268 years and produced a vast state archive, and "
  "it now has a handful of elderly speakers. Twelve of fifteen members are endangered."),
 "Sepik": (["Category:Sepik River", "Category:Papua New Guinea"],
  "Thirty-six languages along one river in northern New Guinea, thirty-three of them endangered. "
  "Several have grammatical gender assigned by shape and size rather than by anything animate — a "
  "long thin thing takes one agreement, a round thing another."),
 "Nuclear Torricelli": (["Category:Papua New Guinea", "Category:Sandaun Province"],
  "Fifty-five languages in the coastal hills of northwestern New Guinea, forty-nine endangered. "
  "One of them, called One, is a cluster of six separate languages all bearing that name."),
 "Ramu": (["Category:Papua New Guinea", "Category:Madang Province"],
  "Twenty-four languages on the Ramu river, every one of them endangered. Almost all were first "
  "described in the last fifty years and several are known from a single wordlist."),
 "Timor-Alor-Pantar": (["Category:Timor", "Category:Alor"],
  "The westernmost Papuan family, on islands otherwise entirely Austronesian — which makes it the "
  "trace of a population that was there before the canoes arrived."),
 "Lakes Plain": (["Category:Papua", "Category:New Guinea"],
  "Twenty languages in a swamp basin in Papua, notable for having lost almost all their nasal "
  "consonants — a change that happened across the whole group and is one of the clearest "
  "demonstrations anywhere of a sound shift running through a family."),
 "Yam": (["Category:Papua New Guinea", "Category:Western Province (Papua New Guinea)"],
  "Southern New Guinea, and the family with the most complicated verbs in the world by several "
  "measures: a single Nen verb form can require choosing among thousands of possibilities, and "
  "the paradigms have to be printed as tables rather than described in rules."),
 "Anim": (["Category:Papua New Guinea", "Category:Marind"],
  "Southern New Guinea. Marind, its largest member, was documented early and in detail by "
  "missionaries and anthropologists, which makes it a rare case of a Papuan language with a deep "
  "record."),
 "Border": (["Category:Papua New Guinea", "Category:Indonesia"],
  "Fifteen languages straddling the line between Papua New Guinea and Indonesia — a border drawn "
  "in Europe in 1895 that runs straight through the middle of a family."),
 "North Halmahera": (["Category:Halmahera", "Category:Maluku"],
  "Papuan languages on an Indonesian island a thousand miles from New Guinea, surrounded by "
  "Austronesian. Ternate and Tidore were the languages of the two sultanates that controlled the "
  "world's entire supply of cloves."),
 "Ndu": (["Category:Sepik River", "Category:Iatmul"],
  "A small family on the middle Sepik whose speakers built the ceremonial houses that made the "
  "region famous in art history. Ten of thirteen languages are endangered."),
 "Angan": (["Category:Papua New Guinea", "Category:Highlands Region"],
  "Highland New Guinea. Several members have systems of counting on the body — naming fingers, "
  "wrist, elbow, shoulder, ear, nose and back down the other side — so the number words are "
  "literally a map of a person."),
 "Tor-Orya": (["Category:Papua", "Category:Indonesia"],
  "Thirteen languages in northern Papua, nine endangered, most of them documented only in survey "
  "wordlists."),
 "Miwok-Costanoan": (["Category:Ohlone", "Category:California"],
  "Central California. Eleven of thirteen are extinct, all within about a century of the Gold "
  "Rush — one of the fastest and most complete language losses recorded anywhere. Several are "
  "known now only from recordings and notebooks made in the 1900s, and are being learned again "
  "from them."),
 "Pomoan": (["Category:Pomo people", "Category:California"],
  "Seven languages in a small part of northern California, six of them named Pomo by direction — "
  "Northern, Southern, Central, Eastern, Southeastern, Northeastern — which is a naming "
  "convention imposed by linguists rather than by their speakers."),
 "Kartvelian": (["Category:Georgian manuscripts", "Category:Georgian calligraphy"],
  "Four languages in the Caucasus with an alphabet of their own, no capital letters, no "
  "grammatical gender, and consonant clusters that other languages break up with vowels. No "
  "relationship to any other family has been demonstrated."),
 "Chukotko-Kamchatkan": (["Category:Chukchi people", "Category:Kamchatka"],
  "The far northeast of Siberia. Chukchi is one of the clearest cases anywhere of a language with "
  "systematically different speech for men and women — the same word, pronounced differently "
  "depending on who is saying it — and the women's forms are the older ones."),
 "Yeniseian": (["Category:Ket people", "Category:Siberia"],
  "Almost gone: Ket has a few dozen elderly speakers and the rest of the family is extinct. It "
  "matters far beyond its size because it is the only family with a proposed and seriously argued "
  "link to the Na-Dene languages of North America — which, if it holds, is the only demonstrated "
  "language connection across the Bering Strait."),
 "Ainu": (["Category:Ainu people", "Category:Hokkaido"],
  "One language, no relatives, and an oral literature of epic poems running to tens of thousands "
  "of lines. It was never written by its speakers; what exists was taken down in the 1920s, "
  "partly by Chiri Yukie, who wrote the yukar out in Latin letters with a Japanese translation at "
  "nineteen and died the year she finished."),
 "Basque": (["Category:Basque language", "Hand of Irulegi"],
  "The last pre-Indo-European language of western Europe, with no demonstrated relatives anywhere. "
  "Its survival is the fact: Latin, then Spanish and French, then a ban under Franco, and it is "
  "still spoken — by more children now than fifty years ago, because a unified written standard "
  "was agreed in 1968 and schools were built on it."),
 "Araucanian": (["Category:Mapuche", "Category:Chile"],
  "One language and its extinct relative, spoken by a people the Inca never conquered and Spain could not hold: the treaty "
  "border on the Bío Bío is one of very few the Spanish crown ever recognised in the Americas."),
 "Nivkh": (["Category:Nivkh people", "Category:Sakhalin"],
  "Sakhalin and the Amur estuary, no relatives, a few hundred speakers. Its counting words change "
  "shape according to what is being counted — one system for nets, another for boats, another for "
  "people."),
 "Burushaski": (["Category:Hunza", "Category:Gilgit-Baltistan"],
  "One language in the Karakoram mountains, surrounded by Indo-European and Sino-Tibetan and "
  "related to neither. Every attempt to attach it to something else has failed, which makes its "
  "valley one of the oldest linguistic situations in Asia."),
 "Sumerian": (["Category:Sumerian language", "Category:Cuneiform"],
  "The first language anyone wrote down, and it has no relatives. Cuneiform began as accounting "
  "at Uruk around 3300 BCE and became able to record connected speech within a few centuries. "
  "Sumerian stopped being spoken around 2000 BCE and was then studied and copied by scribes for "
  "another 1,500 years — the first dead language kept alive by scholarship."),
 "Elamite": (["Category:Elam", "Category:Susa"],
  "Southwestern Iran, written for over two thousand years, and still not fully understood. It is "
  "one of the three languages on Darius's inscription at Behistun, which is what let cuneiform be "
  "deciphered at all."),
 "Hurro-Urartian": (["Category:Urartu", "Category:Hurrians"],
  "Two related languages of the ancient Near East, both written in cuneiform, both with no "
  "demonstrated relatives. Hurrian preserves the oldest known piece of written music — a hymn on "
  "a tablet from Ugarit with its tuning instructions."),
 "Etruscan": (["Category:Etruscan language", "Category:Etruscan civilization"],
  "Etruscan and two relatives, in Italy before Rome. The script is Greek-derived and reads easily; "
  "the language behind it does not, because there is no relative to compare it to and almost "
  "nothing longer than an epitaph survives. Rome took its alphabet, some of its religion and "
  "several of its words, and then wrote its literature in Latin."),
# A SECOND BATCH, chosen by measurement: every family with five or more languages that still had
# no description. The first 70 covered the giants; these are the ones a visitor reaches by
# scrolling, and they were the last families in the list with a blank where their description goes.
 'Iroquoian': (['Category:Iroquois', 'Category:Cherokee syllabary'],
  'The family of the Haudenosaunee confederacy, whose constitution — the Great Law of Peace — was kept on wampum belts rather than paper and is still recited. Its southern outlier is Cherokee, which acquired a syllabary of its own in 1821 and had a printing press by 1828. The northern languages are mostly down to double-digit speaker counts, and Mohawk immersion schooling in Kahnawà:ke is one of the longest-running revival programmes in North America.'),
 'Cochimi-Yuman': (['Category:Yuman languages', 'Category:Baja California'],
  'The lower Colorado and Baja California. Several of its languages have accusative case marking and elaborate verb morphology that made them a testing ground for theories of switch reference — how a language marks whether the subject of the next clause is the same person. Cochimí, the southern branch, is extinct; most of the rest have fewer than a hundred speakers.'),
 'Gunwinyguan': (['Category:Arnhem Land', 'Category:Aboriginal Australians'],
  'Northern Australia, and grammatically among the most complex families described anywhere: a single Bininj Kunwok verb can carry subject, object, tense, mood, direction, body part and instrument in one word. These are non-Pama-Nyungan languages — the older layer of the continent, which is why Arnhem Land holds more distinct families than the rest of Australia put together.'),
 'Worrorran': (['Category:Kimberley Western Australia', 'Category:Aboriginal Australians'],
  'The Kimberley, and the family whose country holds the Gwion Gwion rock paintings. Its languages divide nouns into classes marked by prefixes, which is unusual in Australia and one of the reasons the non-Pama-Nyungan north is treated as a separate linguistic world.'),
 'Nyulnyulan': (['Category:Kimberley Western Australia', 'Category:Dampier Peninsula'],
  "Ten languages on the Dampier Peninsula in Western Australia, all of them severely endangered. Bardi's verb prefixes have been used to argue that this family and its neighbours preserve a grammatical pattern older than the Pama-Nyungan spread that covers the rest of the continent."),
 'Western Daly': (['Category:Northern Territory', 'Category:Daly River'],
  'The Daly River in the Northern Territory. Murrinh-Patha is one of very few Australian languages still being learned by children, and its verbs are built from two conjugating parts at once — a structure that took decades to describe and has no close parallel.'),
 'Sko': (['Category:Papua New Guinea', 'Category:Sandaun Province'],
  'Eleven languages on the north coast at the New Guinea border. Several have tone, which is rare for Papuan languages, and one — Skou — distinguishes words by whether the pitch rises or falls across the whole word rather than on a syllable.'),
 'South Bougainville': (['Category:Bougainville', 'Category:Papua New Guinea'],
  'Bougainville holds four unrelated families on one island, which is among the highest concentrations of deep linguistic diversity anywhere. This is the southern one. Nasioi and its relatives have some of the largest consonant inventories in the Pacific.'),
 'Chapacuran': (['Category:Rondônia', 'Category:Indigenous peoples of Brazil'],
  'The Guaporé river between Brazil and Bolivia. Nine of its twelve languages are extinct and the survivors have a few dozen speakers each; the family is known mostly from wordlists collected by rubber-boom travellers, which is why its internal structure is still argued about.'),
 'Surmic': (['Category:South Sudan', 'Category:Ethiopia'],
  'The Ethiopia–South Sudan borderlands. Several members mark plurality on nouns in three different directions at once — singular from plural, plural from singular, and both from a neutral base — which is one of the more unusual number systems described.'),
 'Heibanic': (['Category:Nuba Mountains', 'Category:Sudan'],
  "The Nuba Mountains of Sudan, and part of the argument about whether Niger-Congo extends this far east: these languages have noun-class prefixes like Bantu's, a thousand miles from the nearest Bantu language, and whether that is inheritance or convergence is unsettled."),
 'Songhay': (['Category:Timbuktu', 'Category:Mali', 'Category:Songhai Empire'],
  "The languages of the Niger bend and of the empire that controlled Timbuktu when it held the largest library in Africa. Songhay's classification is one of the open problems of African linguistics — it has been placed with Nilo-Saharan, with Mande, and on its own, and the evidence is genuinely thin in every direction."),
 'Saharan': (['Category:Kanem-Bornu Empire', 'Category:Lake Chad'],
  'Around Lake Chad. Kanuri was the language of the Kanem-Bornu empire, which lasted a thousand years — one of the longest-lived states in African history — and left a written tradition in Arabic script.'),
 'Maban': (['Category:Chad', 'Category:Darfur'],
  'The Chad–Sudan borderlands. Maba was the language of the Wadai sultanate; the family is small, poorly described, and its position in any wider grouping is unresolved.'),
 'Yanomamic': (['Category:Yanomami', 'Category:Amazon rainforest'],
  "Four languages in the forest between Venezuela and Brazil, spoken by people who had almost no contact with outsiders before the 1950s. The family has no demonstrated relatives, and its speakers' first sustained encounter with the state was an epidemic."),
 'Guaicuruan': (['Category:Gran Chaco', 'Category:Argentina'],
  'The Gran Chaco. Its speakers were among the few peoples of South America to take up horses and hold off colonial expansion for two centuries. Several members distinguish grammatical gender and mark it right through the sentence.'),
 'Mataguayan': (['Category:Gran Chaco', 'Category:Wichí'],
  'Also the Chaco, and unrelated to its neighbours there. Wichí has an unusually large set of verbal suffixes for direction and position — where the action goes and where the speaker is standing are both marked.'),
 'Zamucoan': (['Category:Gran Chaco', 'Category:Paraguay'],
  'Two surviving languages in the Paraguayan Chaco, and one of the strangest facts in the typological literature: Ayoreo and Chamacoco mark nouns for whether they are being used to address someone or to refer to something, a distinction most languages do not make at all.'),
 'Kadugli-Krongo': (['Category:Nuba Mountains', 'Category:Sudan'],
  'The Nuba Mountains again, and a different family from Heibanic despite the same hills — which is what makes this region one of the most linguistically layered in Africa.'),
 'Koman': (['Category:Ethiopia', 'Category:South Sudan'],
  'Five languages on the Ethiopia–Sudan border whose membership in Nilo-Saharan is asserted more often than it is demonstrated. All are endangered and none has a full grammar.'),
 'Katla-Tima': ([],
  'Two languages in the Nuba Mountains of Sudan, sometimes grouped with Niger-Congo and sometimes not. Both are endangered and neither has a published grammar.'),
 'Ijoid': (['Category:Niger Delta', 'Category:Ijaw people'],
  'The Niger Delta. Ijo has subject-object-verb word order, which almost nothing else in West Africa does, and that oddity is a large part of why its position in Niger-Congo is argued about.'),

 "Nihali": ([], "A single language in central India, and one of the clearest cases of a language "
                "that borrowed almost all of its vocabulary and kept its own grammar — which is "
                "why its classification has been argued for a century."),
}


IE_BRANCH = {
 "Classical Indo-European":
  "Everything in Indo-European except Anatolian. Hittite and its relatives split off first and "
  "kept consonants — the laryngeals — that the rest had already lost, which is why their "
  "decipherment in 1915 forced the family tree to be redrawn with Anatolian outside everything "
  "else rather than inside it.",
 "Indo-Iranian":
  "The eastern half of the family, and the branch with the oldest continuous texts: the Rigveda "
  "in India and the Avesta in Iran are close enough in language that a line of one can often be "
  "converted into the other by regular sound rules. Its speakers called themselves *arya, which "
  "is where the name Iran comes from and which nineteenth-century Europe stole for a racial "
  "theory the languages have nothing to do with.",
 "Indo-Aryan":
  "From Sanskrit to Hindi, Bengali, Punjabi and two hundred others across northern India, "
  "Pakistan, Nepal, Bangladesh and Sri Lanka. The branch lost Sanskrit's elaborate case system "
  "and rebuilt grammar out of postpositions and auxiliaries, and it did so in the open: Prakrit "
  "and then Apabhramsha are written stages of that collapse, so the change can be read rather "
  "than reconstructed.",
 "Middle-Modern Indo-Aryan":
  "Everything after Sanskrit stopped being spoken. The Middle stage — the Prakrits — is the "
  "language of Ashoka's rock edicts and of the Buddhist and Jain canons, and is the reason the "
  "transition out of Old Indo-Aryan is one of the best-documented grammatical collapses in any "
  "family.",
 "Continental Indo-Aryan":
  "The mainland group, excluding Sinhala and Dhivehi, which went to sea early and developed "
  "apart for two thousand years.",
 "Iranian-Nuristani":
  "Iranian plus the Nuristani languages of the Hindu Kush, whose position is one of the family's "
  "long-running arguments: they share features with both Iranian and Indo-Aryan and are placed "
  "sometimes inside one, sometimes as a third branch of Indo-Iranian on their own.",
 "Iranian":
  "From Old Persian cut into the cliff at Behistun to Persian, Pashto, Kurdish, Balochi and "
  "Ossetian today. The branch is defined by a sound change anyone can hear: Indo-Iranian *s "
  "became h, so Sanskrit sindhu is Persian hind — which is how India got its name in Europe, by "
  "way of Persian.",
 "Germanic":
  "Defined by one sound shift, and it is the reason English *father* and Latin *pater* look "
  "alike but not identical: Grimm's Law turned every inherited p, t and k into f, th and h. "
  "Germanic also fixed stress on the first syllable, which eroded the endings that Latin and "
  "Greek kept, and it holds about a third of its vocabulary from no known source — words like "
  "sea, ship, sword and drink have no Indo-European etymology at all.",
 "Northwest Germanic":
  "Everything except Gothic and its lost East Germanic relatives. The split shows in one word: "
  "Gothic keeps *z* where the northwest turned it into *r* — Gothic maiza against Old Norse "
  "meiri, English more.",
 "West Germanic":
  "English, German, Dutch, Frisian, Afrikaans, Yiddish and the continuum between them. Whether "
  "it is a real branch or three parallel developments out of a dialect network is argued; what "
  "is not is that every member doubled its consonants before *j* and lost the old reflexive.",
 "North Sea Germanic":
  "The coastal group — English, Frisian, and the Saxon that stayed behind. Its members drop the "
  "nasal before a fricative, which is why English has *us*, *goose* and *five* where German has "
  "uns, Gans and fünf.",
 "Anglo-Frisian":
  "English and Frisian, the closest relatives English has. Both fronted Germanic long a to æ and "
  "both palatalised k before front vowels, which is why English has *cheese* and *church* where "
  "German has Käse and Kirche — and why the Frisian sentence 'bûter, brea en griene tsiis' is "
  "recognisable to an English speaker who has never studied it.",
 "Anglic":
  "English and Scots, plus the creoles and pidgins built on English across the Atlantic and "
  "Pacific. Glottolog counts 38 of them as separate languages, which is why this branch is so "
  "much larger than one language deep.",
 "Later Anglic":
  "English after the Norman conquest, and everything descended from it. The three hundred years "
  "in which French was the language of English government are the reason this stage looks so "
  "different from Old English.",
 "Macro-English":
  "English and the languages built out of it in the Atlantic and Pacific trade: Krio, Jamaican, "
  "Tok Pisin, Bislama, Gullah and two dozen more. Each has an English lexicon over a grammar "
  "that is not English, and each is a separate language rather than a dialect.",
 "Guinea Coast Creole English":
  "The West African creoles — Krio, Nigerian, Ghanaian, Cameroonian — which grew out of the "
  "trade forts of the Guinea coast and now have millions of speakers each. Krio carried back "
  "across the Atlantic in the resettlement of freed slaves in Sierra Leone, so its history runs "
  "in both directions.",
 "Caribbean English Creole":
  "Jamaican, Guyanese, Trinidadian, Bajan and their neighbours. The grammar came out of West "
  "African languages and the shipboard contact of the Middle Passage, and the vocabulary from "
  "English, which is why a written line looks familiar and a spoken one may not be.",
 "High German":
  "Named for the highlands, not for prestige. A second consonant shift ran through the south "
  "and turned p, t and k again — Low German *pund*, *water*, *maken* against High German Pfund, "
  "Wasser, machen — and the line it stopped at, the Benrath line, still divides German dialects.",
 "Italic":
  "Latin and its Italian neighbours — Oscan, Umbrian, Faliscan — most of which Rome absorbed. "
  "Whether Latin and Oscan-Umbrian descend from one Italic parent or converged in Italy is one "
  "of the family's open questions; the vocabulary agrees and some of the morphology does not.",
 "Latino-Faliscan":
  "Latin and Faliscan, its close neighbour fifty kilometres north of Rome, which was written for "
  "four centuries and then disappeared into Latin.",
 "Romance":
  "The only branch whose parent is not reconstructed but recorded. Latin is written down, so "
  "every Romance sound change can be checked rather than inferred, which makes this the "
  "laboratory in which comparative method was tested. Its members lost Latin's case system, "
  "invented articles out of demonstratives and built a future tense out of 'have to' — French "
  "*chanterai* is *cantare habeo*, sing I-have.",
 "Italo-Western Romance":
  "The main body of Romance, from Portugal to central Italy. It excludes Sardinian, which kept "
  "Latin's vowels almost unchanged and is the most conservative Romance language living.",
 "Western Romance":
  "Everything west of a line across northern Italy. Its members voiced Latin's intervocalic "
  "consonants — Latin *vita* to Spanish vida, French vie — and made plurals with -s where Italian "
  "and Romanian use a vowel.",
 "Gallo-Rhaetian":
  "French, Occitan's northern neighbours, Franco-Provençal and the Rhaetian languages of the "
  "Alps: Romansh, Ladin and Friulian. The group is a Celtic substrate and a Germanic superstrate "
  "on Latin, and the Alpine members survived because their valleys were hard to reach.",
 "Oil":
  "The northern French group — Picard, Norman, Walloon, Gallo, Champenois and standard French. "
  "Named for how each said yes: *oïl* in the north against *oc* in the south. Norman is the one "
  "that crossed to England in 1066 and put a third of its vocabulary into English.",
 "West Ibero-Romance":
  "Portuguese, Galician, Asturian, Leonese and Spanish. Its members lost Latin's initial f — "
  "Latin *filius* to Spanish hijo — and Portuguese and Galician were one language until a "
  "political border separated them in the twelfth century.",
 "Balto-Slavic":
  "Baltic and Slavic, and whether they are one branch or two that sat next to each other for a "
  "thousand years is among the oldest disputes in the field. The shared innovations are real but "
  "few; the shared vocabulary is large and could be contact. Lithuanian is the most "
  "conservative living Indo-European language by most measures, which makes this branch the "
  "control group for the whole family.",
 "Slavic":
  "The most recently diverged major branch: its members were still mutually intelligible around "
  "the ninth century, which is why Old Church Slavonic could serve as a liturgical language from "
  "Bulgaria to Novgorod. That late split is why Russian, Polish and Serbian remain far closer to "
  "one another than the Romance or Germanic languages are.",
 "Celtic":
  "Once spoken from Ireland to central Anatolia, now confined to the Atlantic fringe. Every "
  "Celtic language mutates the beginning of a word to mark grammar — Welsh *cath* a cat, *ei "
  "gath* his cat, *ei chath* her cat — a feature almost nothing else in Europe has, and one that "
  "makes the family instantly recognisable in writing.",
 "Indo-Aryan Eastern zone":
  "Bengali, Assamese, Odia, Bihari and their neighbours. The zone lost grammatical gender "
  "entirely, which sets it apart from Hindi and Gujarati to the west, and its scripts descend "
  "from a common eastern form of Brahmi.",
 "Bihari":
  "Bhojpuri, Magahi and Maithili — three languages with tens of millions of speakers each that "
  "were long counted as dialects of Hindi and are not. Maithili was given its own place in the "
  "Indian constitution in 2003 after a long campaign.",
 "Gauda-Kamrupa":
  "Bengali, Assamese and their close relatives around the Brahmaputra and the Ganges delta. "
  "Assamese and Bengali share a script with two letters' difference.",
 "Indo-Aryan Central zone":
  "The Hindi belt in the broad sense — Braj, Awadhi, Bundeli, Kanauji and the varieties that the "
  "census counts as Hindi and linguists do not. Braj and Awadhi carried most of the literature "
  "before the dialect that became standard Hindi did.",
 "Indo-Aryan Northwestern zone":
  "Punjabi, Sindhi, Lahnda and the Dardic borderlands. Punjabi is the only major Indo-Aryan "
  "language with lexical tone, which it developed when its voiced aspirates collapsed.",
 "Gujarati-Rajasthani":
  "Gujarati, Marwari, Mewari and the languages of the northwest desert. Gujarati dropped the "
  "line along the top of Devanagari, which is why its script looks lighter on the page.",
 "Rajasthani":
  "The languages of Rajasthan, counted by the Indian census as Hindi and by Glottolog as "
  "twenty-two separate languages — a disagreement about splitting that has real political weight, "
  "because census numbers decide what gets taught.",
 "Bhil":
  "The languages of the Bhil peoples across Gujarat, Rajasthan and Madhya Pradesh, sitting "
  "between the Gujarati and Marathi standards and absorbed into both by schooling.",
 "Himachali":
  "The Western Pahari languages of the Himalayan foothills, most counted as Hindi in the census "
  "and most with no written standard of their own.",
 "Sindhi-Lahnda":
  "Sindhi and the Lahnda group of western Punjab, including Saraiki. Sindhi's Perso-Arabic "
  "alphabet has 52 letters, the largest of any, because Sindhi has sounds Arabic does not.",
 "Oriya-Gauda-Kamrupa":
  "Odia and the eastern group. Odia has the longest unbroken literary record of the eastern "
  "Indo-Aryan languages and was the sixth language granted classical status in India.",
 "Apabhramsic":
  "The last Middle Indo-Aryan stage, and the immediate parent of most modern northern Indian "
  "languages. Apabhramsha literally means 'falling away' — the name grammarians gave the speech "
  "that had drifted from Sanskrit, and the stage in which the modern grammar took shape.",
 "Shaurasenic":
  "The Prakrit of the Mathura region and its descendants, which include the Hindi belt. In "
  "Sanskrit drama the high characters speak Sanskrit and the women and servants speak "
  "Shauraseni, which is how a spoken register got written down at all.",
 "Eastern Dardic":
  "Kashmiri, Shina, Khowar and the languages of the mountain valleys between Afghanistan and "
  "Kashmir. Whether Dardic is a branch or simply the Indo-Aryan languages that were left behind "
  "in the hills is unsettled — they are conservative rather than shared-innovative.",
 "Northwestern Iranian":
  "Kurdish, Balochi, Zaza, Gilaki, Mazanderani, Talysh and the Caspian languages. The group is "
  "defined against Persian by sounds Persian changed and these did not, which makes 'northwestern' "
  "a statement about conservatism rather than geography.",
 "Southwestern Iranian":
  "Persian and its close relatives — Dari, Tajik, Luri, Bakhtiari. The prestige of Persian from "
  "the tenth century onward drew the whole group toward it, so the boundaries here are unusually "
  "blurred.",
 "Modern Southwestern Iranian":
  "Persian in its three national forms — Iranian Persian, Dari and Tajik — plus Luri and the "
  "dialects of Fars. One language in three alphabets: Arabic script in Iran and Afghanistan, "
  "Cyrillic in Tajikistan.",
 "Middle-Modern Persian":
  "Persian after the Sasanians. Middle Persian was written in an Aramaic-derived script so "
  "ambiguous that scribes wrote Aramaic words and read them aloud in Persian; New Persian, in "
  "Arabic letters, is far easier to read and begins the literature.",
 "Central Iranian PBS":
  "Parthian, Bactrian, Sogdian and the Central Asian Iranian languages of the Silk Road. Sogdian "
  "was the trade language from Samarkand to Chang'an, and the letters found in a mailbag "
  "abandoned in a watchtower west of Dunhuang around 313 are among the oldest personal letters "
  "in any Iranian language.",
 "Tatic":
  "Tati, Talysh and the small Iranian languages of the Iranian-Azerbaijani borderland, several "
  "of them down to a few thousand speakers and none with an official standing.",
 "Shifted Western Romance":
  "The Romance languages that carried Latin's stress shift through — the main body of Iberian "
  "and Gallo-Romance.",
 "Southwestern Shifted Romance":
  "Spanish, Portuguese, Galician, Asturian and the languages of the Iberian peninsula, plus the "
  "creoles built on them in the Atlantic and the Pacific.",
 "Northwestern Shifted Romance":
  "French, Occitan and the Gallo-Romance group north of the Pyrenees.",
 "Galician Romance":
  "Galician and Portuguese and everything Portuguese became overseas — the creoles of Cape Verde, "
  "Guinea-Bissau, São Tomé and Macau. Galician and Portuguese were a single literary language in "
  "the thirteenth century, and Castilian kings wrote their lyric poetry in it.",
 "Macro-Portuguese":
  "Portuguese and the fifteen creoles built on it, from Cape Verde to Sri Lanka and Macau — the "
  "trace of the first European seaborne empire, and the reason Portuguese-lexified creoles are "
  "found on four continents.",
 "Central Oil":
  "The dialects around Paris out of which standard French was made — Francien and its neighbours. "
  "Standard French is not a dialect that won on merit; it is the speech of the region that held "
  "the court.",
 "Latinic":
  "Latin and everything descended from it, as against the Faliscan side of the branch.",
 "Imperial Latin":
  "Latin from the empire onward, and the Romance languages that grew out of the spoken form. The "
  "written standard barely moved for a thousand years while the speech underneath it became "
  "French, Spanish and Italian — which is why the Council of Tours in 813 had to order priests "
  "to preach in the local tongue.",
 "Nuclear Eastern Dardic":
  "The core Dardic group of the Chitral and Kashmir valleys, several of its members spoken in a "
  "single valley and none with more than a few thousand speakers except Kashmiri.",
 "Adharic":
  "A small group of central Iranian languages, most of them undescribed beyond a wordlist.",
 "Central Iranian PB":
  "Parthian and Bactrian: the languages of the Arsacid empire and of Kushan Afghanistan. "
  "Bactrian is the only Iranian language ever written in Greek letters, a legacy of Alexander.",
 "Midlands Indo-Aryan":
  "The great central block of northern India — the Hindi belt, Rajasthan and Gujarat — where the "
  "line between language and dialect is drawn by politics rather than by intelligibility.",
}

ST_BRANCH = {
 "Sinitic":
  "Chinese, and the count depends entirely on who is asking. Ten to fifteen mutually "
  "unintelligible languages by any criterion applied to Europe; one language with dialects by "
  "the criterion China uses, which is a shared writing system and a shared literary tradition "
  "reaching back three thousand years. Both statements describe the same facts. The branch split "
  "early — Min separated before Middle Chinese and cannot be reconstructed from the rhyme "
  "dictionaries the way the rest can — and its modern spread is the record of a millennium of "
  "migration southward out of the north China plain.",
 "Classical-Middle-Modern Sinitic":
  "Everything descended from the language of the Han and Tang, which is all of Chinese except "
  "the earliest layer. The rhyme dictionaries of the sixth and eleventh centuries — the Qieyun "
  "and the Guangyun — were written to standardise poetry and turned out to be a phonological "
  "record of Middle Chinese precise enough to reconstruct from, which is why Chinese historical "
  "linguistics rests on evidence no other language family in Asia has.",
 "Burmo-Qiangic":
  "A large grouping across Yunnan, Sichuan and northern Myanmar joining Lolo-Burmese to the "
  "Qiangic languages of the Sichuan highlands. It is one of the more contested nodes in the "
  "family: the Qiangic languages are agreed to be a group, and whether they belong here rather "
  "than nearer Tibetan is not.",
 "Lolo-Burmese":
  "Burmese and the hundred-odd Ngwi (Loloish) languages of the Yunnan massif — one of the "
  "best-established branches of the family, and the one with the deepest split between a "
  "national language with a thousand-year written record and a hundred hill languages with "
  "almost none. Tone did most of the work here: the branch's history is largely the story of "
  "what happened to Proto-Lolo-Burmese's initial consonants after they turned into tones.",
 "Loloish":
  "The Ngwi languages: over a hundred of them across Yunnan, Sichuan, Myanmar, Thailand, Laos "
  "and Vietnam, spoken by peoples the Chinese state groups as Yi, Hani, Lisu, Lahu and Naxi. "
  "Several have scripts of their own — the Yi syllabary, standardised in 1974 with 819 "
  "characters, and Naxi's dongba, the only pictographic writing still in ritual use anywhere.",
 "Burmish":
  "Burmese and its close relatives in the Kachin and Dehong hills — Zaiwa, Lashi, Achang. "
  "Burmese has been written since the Myazedi inscription of 1113 and the rest have been written "
  "for about a century, in Latin orthographies that stop at the China–Myanmar border and change "
  "on the other side of it.",
 "Kuki-Chin-Naga":
  "Ninety-odd languages across Nagaland, Manipur, Mizoram, Chin State and the Chittagong Hill "
  "Tracts. The grouping is geographic as much as genealogical: Naga is a colonial category that "
  "covers several branches which may not be each other's closest relatives, and the Kuki-Chin "
  "languages are a real group inside it. This is the least individually described part of "
  "Sino-Tibetan relative to its size.",
 "Kuki-Chin":
  "Mizo, Thado, Hmar, Zou, Tedim and some fifty others across the India–Myanmar border. A "
  "well-established group with an unusual amount of internal regularity, and a written tradition "
  "that arrived with Baptist missionaries in the 1890s and produced literacy rates among the "
  "highest in either country.",
 "Angami-Ao":
  "The central Naga languages of Nagaland — Angami, Ao, Lotha, Sema, Rengma. Mutually "
  "unintelligible enough that Nagaland made English its official language rather than choose "
  "among them, and the state is now one of the few places in India where English is the everyday "
  "written language of ordinary administration.",
 "Patkaian":
  "The Konyak, Wancho, Phom and Chang languages of the Patkai range on the Myanmar border — the "
  "last part of the Naga area contacted by the colonial administration, and the least described. "
  "Wancho acquired a brand-new alphabet in 2012, one of very few scripts invented anywhere in "
  "this century and encoded in Unicode.",
 "Bodic":
  "Tibetan and its relatives, plus the Himalayish languages of Nepal and the western Himalaya. "
  "A large and only partly settled grouping: Bodish proper is secure, and whether West "
  "Himalayish and the Kiranti languages belong under the same node is argued.",
 "Bodish":
  "The Tibetic languages and their nearest cousins. Everything written in Tibetan script "
  "descends from the language of the seventh-century Tibetan empire, and the orthography was "
  "fixed then — which means a modern Lhasa speaker's spelling records a pronunciation thirteen "
  "hundred years old, and a Ladakhi or Balti speaker still says many of the consonant clusters "
  "the spelling shows.",
 "Central Tibetan":
  "The Tibetan of Lhasa and Ü-Tsang, the prestige variety and the basis of the standard. It has "
  "developed tone, which Classical Tibetan did not have; the tones arose from the initial "
  "clusters the script still faithfully writes and the mouth no longer pronounces.",
 "South-Western Tibetic":
  "The Tibetic languages of Nepal, Sikkim and Bhutan — Sherpa, Jirel, Lhomi, Dzongkha's "
  "neighbours. Spoken across a border that is also a religious and administrative boundary, and "
  "written in Tibetan script wherever they are written at all.",
 "Early Old Tibetan":
  "The language of the Tibetan empire's first inscriptions and of the Dunhuang manuscripts "
  "sealed in a cave library about 1000 and not reopened until 1900. Those documents are the "
  "oldest substantial record of any Tibeto-Burman language and the reason Tibetan anchors the "
  "family's historical reconstruction.",
 "West Himalayish":
  "Kinnauri, Bunan, Darma and their relatives in Himachal Pradesh, Uttarakhand and western "
  "Nepal — languages that are not Tibetan and are surrounded by it and by Indo-Aryan. Several "
  "preserve archaic features and none has a written tradition of its own.",
 "Himalayish":
  "The languages of the Nepal Himalaya and the ranges west of it, taken together. A large "
  "grouping of small languages, most with a few thousand speakers, many described only in the "
  "last forty years, and a good number not described at all.",
 "Mahakiranti":
  "A proposed grouping joining the Kiranti languages to the Newar and Magar languages of central "
  "Nepal. Whether it is a real clade is disputed — the shared features may be contact rather "
  "than descent — and the card says so because the tree cannot.",
 "Kiranti":
  "The languages of eastern Nepal's Rai and Limbu peoples, about thirty of them, and "
  "collectively the holders of some of the most complex verb morphology described anywhere in "
  "the world. A single Kiranti verb can agree with subject and object simultaneously and select "
  "among several stems to do it; Khaling's system took decades to work out.",
 "Eastern Kiranti":
  "Limbu and its neighbours, in the hills between the Arun and the Mechi. Limbu has its own "
  "script, Sirijanga, revived in the eighteenth century from a tradition said to be far older, "
  "and encoded in Unicode in 2002.",
 "Brahmaputran":
  "The Bodo-Garo, Konyak and Kachin languages of Assam, Meghalaya and the Brahmaputra valley — "
  "a grouping van Driem proposed and not everyone accepts. Bodo and Garo are among the few "
  "Tibeto-Burman languages of India with official status in a state.",
 "Bodo-Garo":
  "Bodo, Garo, Rabha, Tiwa and their relatives across Assam and Meghalaya. Bodo entered the "
  "Eighth Schedule of the Indian constitution in 2003 after a long and violent campaign; Garo is "
  "the majority language of the Garo Hills and is written in Latin letters.",
 "Karenic":
  "Twenty-odd languages of eastern Myanmar and western Thailand, and the odd one out in the "
  "whole family: Karen puts the verb before the object, where nearly every other Tibeto-Burman "
  "language puts it after. That is almost certainly the result of a thousand years of contact "
  "with Mon and Tai rather than inheritance. Written in a Burmese-derived script.",
 "Na-Qiangic":
  "The Qiangic and Naic languages of the Sichuan–Yunnan highlands, including Naxi and the "
  "languages of the Mosuo. Structurally among the most complex in the family — Gyalrongic verbs "
  "carry directional prefixes and person marking of a kind found nowhere else in Sino-Tibetan.",
 "Qiangic":
  "The languages of the Sichuan highland corridor: Qiang, Prinmi, Ersu, Tangut's living "
  "relatives. Tangut itself, the language of the Xi Xia empire destroyed by the Mongols in 1227, "
  "was written in a script of six thousand characters invented in 1036 and deciphered only in "
  "the twentieth century.",
 "Gyalrongic":
  "A dozen languages of western Sichuan with the most elaborate verbal morphology in the family "
  "and, unusually for the region, consonant clusters that look like what Proto-Sino-Tibetan is "
  "reconstructed to have had. They are heavily used in reconstruction for that reason.",
 "Hani-Jino":
  "The Hani, Akha and Jino languages of southern Yunnan and the hills across the Burmese, Lao "
  "and Thai borders. Akha's oral genealogies chain each man's name to the last syllable of his "
  "father's and are recited back sixty generations — a record kept without writing.",
 "Lisoid":
  "Lisu, Lipo, Lolopo and their relatives in Yunnan and northern Myanmar. Lisu is written in the "
  "Fraser alphabet, invented about 1915 using only upright and rotated Latin capitals so it "
  "could be set on any press — one of the most ingenious missionary scripts ever devised, and "
  "still the standard.",
 "Nisoid":
  "The Nisu and Nasu languages of Yunnan, written where they are written in the Yi syllabary — "
  "a script of over a thousand traditional characters, standardised to 819 in 1974 and used for "
  "ritual texts by the bimo priests for centuries before that.",
 "Highland Phula":
  "Fifteen small Ngwi languages of southeastern Yunnan, most of them documented for the first "
  "time in a single survey published in 2012 — an unusually clear case of a whole subgroup "
  "entering the record at once.",
}

PN_BRANCH = {
 "Paman":
  "The languages of Cape York, and the northern half of the family's name — *pama* is the word "
  "for 'person' there, as *nyunga* is in the southwest, and the family was named for the two ends "
  "of the continent it spans. Paman is where Australian phonology gets strange: several of these "
  "languages underwent drastic initial-consonant loss, so words that elsewhere begin with a "
  "consonant here begin with a vowel or nothing, and the family's usual look breaks down.",
 "Wik":
  "The Wik languages of western Cape York, around Aurukun. Wik-Mungkan is one of the stronger "
  "Australian languages, still learned by children. The Wik peoples' 1996 High Court case "
  "established that native title and pastoral leases can coexist, which changed Australian "
  "property law.",
 "Northern Pama":
  "The languages of the top of Cape York, several of them with the initial-dropping that makes "
  "Paman distinctive. Most have no speakers left; the documentation is largely Bruce Sommer's and "
  "Terry Crowley's fieldwork of the 1960s and 1970s.",
 "Yuulngu":
  "The Yolŋu languages of northeast Arnhem Land — the strongest surviving group in the family, "
  "and the one where language and clan identity are formally bound together. A Yolŋu person "
  "belongs to a clan and to that clan's variety, speaks several others, and chooses among them "
  "by who is present. They are Pama-Nyungan surrounded by non-Pama-Nyungan languages, which is "
  "one of the family's unsolved geographic puzzles.",
 "Desert Nyungic":
  "The Western Desert languages: Pitjantjatjara, Yankunytjatjara, Ngaanyatjarra, Pintupi, "
  "Kukatja, Manyjilyjarra and the rest, mutually intelligible across two thousand kilometres of "
  "desert — one of the largest dialect continua on earth. Its varieties are named for their word "
  "for 'come' or 'this', because that is the audible difference between neighbours.",
 "Wati":
  "The Wati group inside the Western Desert, and the part of the family with the best prospects: "
  "several of these languages are still learned by children, taught in schools their communities "
  "run, and used in media and land administration across an area larger than most countries.",
 "Ngayarda":
  "The languages of the inland Pilbara. Most have few or no speakers, and much of what is known "
  "was recorded by Carl von Brandenstein and Alan Dench within a decade of the last fluent "
  "generation. Martuthunira's grammar was written from work with Algy Paterson, its last speaker.",
 "Pilbara":
  "The Pilbara languages taken together — Ngayarda, Kanyara, Mantharta and their neighbours. "
  "Colonised late and hard: the region's pastoral industry ran on Aboriginal labour under "
  "conditions that ended only with the 1946 Pilbara strike, the longest strike in Australian "
  "history, and the language shift followed the same timeline.",
 "Karnic":
  "The languages of the Lake Eyre basin and the Channel Country. Almost none is spoken, and yet "
  "they are among the best-documented extinct languages anywhere, because Luise Hercus spent "
  "forty years recording them from the last speakers. Diyari is the exception in another "
  "direction: Lutheran missionaries printed a New Testament in it in 1897.",
 "Arandic-Thura-Yura":
  "Arandic and Thura-Yura, from central Australia down to the Adelaide plains. Arandic phonology "
  "is unlike anything else in the family — Arrernte has been analysed as having syllables that "
  "run vowel-consonant rather than consonant-vowel, which almost no language does.",
 "Thura-Yura":
  "The languages of the Flinders Ranges, Eyre Peninsula and the Adelaide plains — Adnyamathanha, "
  "Nukunu, Narungga, Kaurna. Kaurna, the language of Adelaide, stopped being spoken in the "
  "nineteenth century and has been reconstructed from two German missionaries' 1840 records into "
  "a taught, spoken language again.",
 "Maric":
  "The languages of interior Queensland, covering an enormous area and almost entirely silent "
  "now. Gavan Breen's grammars of Bidyara, Gungabula and their neighbours, written in the 1970s "
  "from the last speakers, are most of what survives.",
 "Greater Maric":
  "Maric and its nearest relatives across central and southern Queensland. The group is held "
  "together by shared pronoun and case morphology rather than by sound changes, which is the "
  "usual situation in this family and the reason its higher nodes stay provisional.",
 "New South Wales Pama-Nyungan":
  "Wiradjuri, Gamilaraay, Ngiyambaa, Gumbaynggirr, Dharug and their neighbours — the languages of "
  "the country colonised first and hardest, all of which stopped being spoken. Nearly all of them "
  "are now in revival, taught from archival records and community memory; New South Wales passed "
  "an Aboriginal Languages Act in 2017, the first law in Australia to recognise Aboriginal "
  "languages as belonging to the people whose languages they are.",
 "Victorian Pama-Nyungan":
  "The languages of Victoria, none of them spoken continuously into the present and several now "
  "in revival — Woiwurrung, Boonwurrung, Wergaia, Gunditjmara. The Victorian Aboriginal "
  "Corporation for Languages has run reclamation from archival sources since 1994.",
 "Southeastern Pama-Nyungan":
  "The whole southeastern quarter of the family, from the Murray to the coast. Its languages were "
  "the first to meet the frontier and the first to fall silent, which means their record is "
  "mostly nineteenth-century word lists written by settlers, missionaries and police — and that "
  "those lists are now the raw material of a dozen revivals.",
 "South-West Pama-Nyungan":
  "The languages of southwestern Western Australia, Noongar chief among them. Noongar covers a "
  "dialect continuum from Perth around to Esperance; its revival has produced dictionaries, "
  "school programmes, place-name restorations and, in 2020, a Noongar-language Shakespeare.",
 "Compromise Middle Pama":
  "A middle-Cape York grouping whose name records an argument: the branch was proposed as a "
  "compromise between competing classifications of the Paman languages, and Glottolog keeps the "
  "name. It is a good reminder that a node in this tree can be a negotiated position rather than "
  "a finding.",
 "Guwa-Maric":
  "Maric together with Guwa and Yanda of the Queensland interior. Like most higher nodes in this "
  "family it rests on shared morphology and on computational phylogeny rather than on classical "
  "sound-change reconstruction, and it is not universally accepted.",
 "Kartu":
  "The languages of the Murchison and Shark Bay coast of Western Australia — Nhanda, Malgana, "
  "Wajarri, Badimaya. Nhanda is another of the family's phonological outliers: it lost initial "
  "consonants, like the Paman languages three thousand kilometres away, and did it independently.",
}

AC_BRANCH = {
 "Volta-Congo":
  "Almost the whole family — some 1,343 of its languages, from Senegal to South Africa. The name "
  "is geographic, for the two rivers between which its oldest divisions sit, and that is the "
  "point: the deep splits are all in West Africa, in a strip a few hundred kilometres wide, "
  "while a single sub-branch of one sub-branch covers everything south of the equator.",
 "Benue-Congo":
  "A thousand languages, named for the Benue river in Nigeria, and containing both the "
  "extraordinary density of southeastern Nigeria — where mutually unintelligible languages "
  "change every few dozen kilometres — and, inside it, the whole Bantu expansion.",
 "Bantoid":
  "The branch that contains Bantu and its nearest relatives. Its non-Bantu members are "
  "concentrated in the Nigeria–Cameroon borderlands, in the Grassfields and the Mambila plateau, "
  "and that concentration is the main evidence for where the Bantu expansion started.",
 "Southern Bantoid":
  "Narrow Bantu together with the Grassfields, Tivoid, Ekoid and Mambiloid languages of the "
  "Cameroon highlands. Seven hundred languages, of which five hundred and sixty are Bantu and "
  "the rest sit in an area smaller than Scotland.",
 "Narrow Bantu":
  "Five hundred and sixty languages across a third of Africa — Swahili, Zulu, Shona, Kikongo, "
  "Lingala, Kinyarwanda, Luganda, Xhosa, Sotho — and all of them descended from one language "
  "spoken in the Cameroon–Nigeria borderlands perhaps three thousand years ago. They share a "
  "noun-class system of a dozen or more genders marked by prefixes, which is why a Bantu "
  "language is recognisable as one on sight. The expansion that produced them is among the "
  "largest and fastest known for any language family.",
 "East Bantu":
  "The eastern half of the Bantu spread: Swahili, Kikuyu, Chichewa, Shona, Zulu, Xhosa, Sotho, "
  "Tswana. This is where Bantu languages met Khoisan ones, and several of them took click "
  "consonants from that contact — Zulu and Xhosa have three series of clicks, which no other "
  "branch of the family has.",
 "Great Lakes Bantu":
  "Kinyarwanda, Kirundi, Luganda, Runyankole, Haya, Chiga and their neighbours around Lakes "
  "Victoria, Kivu and Tanganyika — one of the most densely populated language areas in Africa "
  "and the one with the tightest chain of mutual intelligibility: Kinyarwanda and Kirundi are "
  "the national languages of two different countries and are barely different languages.",
 "Central-Western Bantu":
  "The Bantu languages of the Congo basin and the Atlantic coast — Kikongo, Lingala, Luba, "
  "Mongo, Tetela. Lingala is the youngest major one, formed in the nineteenth century as a "
  "trade language along the river and now spoken by tens of millions who did not inherit it.",
 "West-Coastal Bantu":
  "The Bantu languages of the Atlantic coast from Gabon to Angola, Kikongo chief among them. "
  "Kikongo was the language of the kingdom of Kongo, which corresponded with Portugal in writing "
  "from 1491, and the one enslaved people carried to Brazil, Cuba and Haiti in the largest "
  "numbers — its words survive in Palenquero, in Cuban Palo and in Haitian Vodou.",
 "Northeast Savanna Bantu":
  "The Bantu languages of the northern savanna belt, from the Great Lakes westward. Their "
  "internal relationships are among the least settled in Bantu, because the expansion moved fast "
  "here and left a chain of varieties rather than clean splits.",
 "North Volta-Congo":
  "The Gur, Adamawa and Ubangi languages of the northern belt, from Burkina Faso to South Sudan. "
  "The grouping is not universally accepted, and Ubangi's membership in the family at all has "
  "been argued over for decades.",
 "Gur":
  "Ninety-odd languages across Burkina Faso, Mali, Ghana, Togo and Côte d'Ivoire — Mooré, "
  "Dagbani, Gurma, Lobi, Kabiyé. Mooré alone has more speakers than most European languages. Gur "
  "languages use noun-class suffixes where Bantu uses prefixes, which is one of the family's "
  "oldest internal divisions.",
 "Central Gur":
  "The core of Gur: Mooré and the Mossi languages of Burkina Faso, Dagbani and its relatives in "
  "northern Ghana. The Mossi kingdoms held out against the Mali and Songhai empires for four "
  "hundred years, and Mooré is the everyday language of Burkina Faso today.",
 "Kwa Volta-Congo":
  "The languages of the Gulf of Guinea coast — Akan, Ewe, Fon, Ga, Baoulé. Kwa languages are "
  "tonal and largely isolating, having lost the noun-class prefixes the rest of the family "
  "keeps, and several are national lingua francas: Akan in Ghana, Ewe and Fon across Togo and "
  "Benin.",
 "Nyo":
  "Akan, Baoulé, Anyi, Ga, Guang and their relatives in Ghana and Côte d'Ivoire. Akan is the "
  "vehicle of the Adinkra symbols and of the Asante state, and it gave English *chimpanzee*, "
  "and the day-names — Kofi, Kwame, Akosua — that mark which day of the week a person was born.",
 "Ubangi":
  "The languages of the Central African Republic and northern Congo — Zande, Banda, Ngbaka, and "
  "Sango, which became the national language of the CAR. Whether Ubangi belongs in this family "
  "at all is genuinely contested; Greenberg placed it here and several later scholars have "
  "argued it out again.",
 "North-Central Atlantic":
  "The Atlantic languages of Senegal, Gambia and Guinea — Wolof, Pulaar (Fula), Serer, Jola. "
  "These are among the deepest divisions in the whole family, and Fula is remarkable in another "
  "way: its speakers are spread from Senegal to Sudan, five thousand kilometres, as a herding "
  "population inside twenty other countries' languages.",
 "Delta Cross":
  "The languages of the Niger delta and the Cross River — Efik, Ibibio, Anaang, Ogoni. Efik "
  "carries the Nsibidi ideographic system, a body of signs used for law, trade and the Ekpe "
  "society that is one of very few indigenous West African writing traditions.",
 "Kainji":
  "Fifty-odd languages of the Niger's middle reaches in Nigeria, most with a few thousand "
  "speakers and few with any description. Central Nigeria holds one of the densest "
  "concentrations of distinct languages anywhere and one of the thinnest documentary records.",
 "Benue-Congo Plateau":
  "The Plateau languages of central Nigeria — Berom, Tarok, Jju, Eggon and sixty others around "
  "Jos. Like Kainji, this is an area of extreme linguistic density and almost no published "
  "grammars.",
 "Wide Grassfields":
  "The Grassfields languages of western Cameroon, seventy of them in a highland area a few "
  "hundred kilometres across — and the closest known relatives of Bantu. Their diversity in so "
  "small a space, next to Bantu's uniformity across a continent, is the argument for the Bantu "
  "homeland being here.",
 "Narrow Grassfields":
  "The core Grassfields group — Bamileke, Bamun, Nkambe, Ngemba. Bamun is the language for which "
  "Sultan Njoya invented a script about 1896, developing it through six revisions from a "
  "pictographic system into a syllabary: one of the very few writing systems in history whose "
  "invention is documented step by step.",
}

AN_BRANCH = {
 "Malayo-Polynesian":
  "One of Austronesian's ten primary branches, and the one that left: 1,255 languages from "
  "Madagascar to Rapa Nui, across two oceans and 210 degrees of longitude. The other nine "
  "branches are all on Taiwan. Everything below this node happened after a crossing of the "
  "Bashi Channel around 2000 BCE, and it is the largest area any language family reached before "
  "the age of European empires.",
 "Atayalic":
  "One of the nine primary branches of Austronesian confined to Taiwan — Atayal and Truku, in "
  "the northern mountains. A branch of the family at the same depth as Malayo-Polynesian's "
  "1,255 languages, with two.",
 "Tsouic":
  "Tsou and its relatives in Taiwan's central mountains. A primary branch whose internal unity "
  "is itself questioned — the languages placed in it may not be each other's closest relatives.",
 "East Formosan":
  "Kavalan, Basay, Amis and their relatives along Taiwan's eastern coast and northern tip. Amis "
  "is the largest surviving Formosan language; Basay and several others are gone.",
 "Northwest Formosan":
  "Saisiyat and Kulon-Pazeh, in northwestern Taiwan. Pazeh's last fluent speaker died in 2010; "
  "Kahabu speakers and a revival community continue with it.",
 "Western Plains Austronesian":
  "The languages of Taiwan's western plains — Thao, Papora, Hoanya, Siraya. These were the first "
  "Formosan peoples to meet Dutch, Chinese and Japanese settlement, and almost all their "
  "languages are gone. Siraya is being revived from a seventeenth-century Dutch gospel "
  "translation.",
 "Eastern Malayo-Polynesian":
  "The eastern half of the great expansion — the languages of Halmahera, New Guinea's coasts and "
  "everything in the Pacific beyond. Its Oceanic subgroup is one of the best-reconstructed "
  "subgroups of any family anywhere.",
 "Oceanic":
  "Five hundred and twenty-three languages across the Pacific, all descended from one language "
  "spoken in the Bismarck Archipelago around 1200 BCE — the language of the people who made "
  "Lapita pottery. The archaeological trail and the linguistic tree agree with each other "
  "closely enough that Oceanic is the standard example of the two disciplines confirming a "
  "single migration.",
 "Western Oceanic linkage":
  "The Oceanic languages of New Guinea's north coast, New Britain, New Ireland and the western "
  "Solomons. Called a linkage rather than a subgroup on purpose: these languages did not descend "
  "from one ancestor by clean splits but diverged in place, in continuous contact, so the "
  "boundaries between them run in overlapping bands rather than branching lines.",
 "Meso Melanesian linkage":
  "The Oceanic languages of New Ireland, the Solomons and northwest New Britain. Another linkage, "
  "and one where centuries of trade and intermarriage make the family tree a poor picture of "
  "what actually happened.",
 "Papuan Tip linkage":
  "The Oceanic languages of the southeastern tail of New Guinea and the islands off it, "
  "including the Trobriands — where Malinowski's fieldwork in Kilivila between 1915 and 1918 "
  "effectively invented modern ethnography.",
 "North and Central Vanuatu":
  "Vanuatu has more languages per head of population than anywhere on earth: about 130 languages "
  "for 300,000 people, most of them Oceanic and most with a few hundred speakers. Bislama, an "
  "English-lexifier creole, is what the country actually uses in common.",
 "Central Pacific linkage":
  "Fijian, Rotuman and the Polynesian languages together. Polynesian is a subgroup inside Fijian's "
  "immediate neighbourhood, which is the linguistic form of the fact that the settlement of the "
  "remote Pacific set out from there.",
 "Polynesian":
  "Thirty-nine languages spread over ten million square kilometres of ocean — Hawaiian, Māori, "
  "Samoan, Tongan, Tahitian, Rapa Nui — and so closely related that a Tongan and a Samoan can "
  "find their way through each other's speech. That combination, enormous distance and small "
  "difference, is the signature of a fast deliberate migration by people who knew how to sail "
  "and how to come back.",
 "East Polynesian":
  "Hawaiian, Māori, Tahitian, Rapa Nui, Marquesan and their relatives — the last major "
  "settlement of empty land anywhere on earth, completed between about 900 and 1300. New Zealand "
  "was the final large landmass on the planet to be reached by people, and Māori is what they "
  "brought.",
 "Micronesian":
  "The languages of the Carolines, Marshalls, Kiribati and Nauru, spread over a scattering of "
  "atolls across an area the size of the continental United States. Marshallese and Kiribati "
  "navigators mapped that ocean with stick charts recording swell patterns rather than "
  "coastlines.",
 "Greater Central Philippine":
  "Tagalog, Bikol, the Bisayan languages, Maranao, Maguindanao and their relatives — the "
  "majority of the Philippines' population. Tagalog became Filipino, the national language, "
  "which is one reason Cebuano has more native speakers than Tagalog and less standing.",
 "Central Philippine":
  "Tagalog, Bikol and Bisayan proper. The Philippines was written before Spanish contact in "
  "Baybayin, an Indic-derived script; Spanish printing displaced it within a century, and it has "
  "been revived as a cultural marker rather than an everyday orthography.",
 "Bisayan":
  "Cebuano, Hiligaynon, Waray, Kinaray-a and their relatives across the central Philippines. "
  "Cebuano has more first-language speakers than Tagalog and no official status of its own, "
  "which is a live political question rather than a historical one.",
 "Northern Luzon":
  "Ilocano, Pangasinan, Ibanag, Kalinga, Ifugao and their neighbours. The Ifugao *hudhud* chants, "
  "which take days to perform and are sung at harvest and at wakes, are on UNESCO's intangible "
  "heritage list.",
 "Malayo-Chamic":
  "Malay, Indonesian, Minangkabau and the Chamic languages of Vietnam and Cambodia. Chamic is the "
  "branch that went to the mainland: Cham was the language of a Hindu-Buddhist kingdom in "
  "central Vietnam, and its earliest inscription of about 350 CE is the oldest written "
  "Austronesian anywhere.",
 "Malayic":
  "Malay and its close relatives across Sumatra, Borneo and the peninsula. Malay's history is "
  "unusual: it was a trade language of the Straits for a thousand years before it was anyone's "
  "national language, which is why Indonesia adopted it in 1928 over Javanese, spoken by far "
  "more people — a lingua franca belongs to nobody, which was the point.",
 "Chamic":
  "The Austronesian languages of Vietnam and Cambodia — Cham, Jarai, Rade, Chru. Long contact "
  "with Mon-Khmer has restructured them so heavily that they have taken on the shape of "
  "mainland Southeast Asian languages while remaining Austronesian by descent.",
 "Celebic":
  "The languages of central and eastern Sulawesi — Bugis's neighbours, Mori, Tolaki, Bungku. "
  "Sulawesi's shape gives it an unusual linguistic map: four long peninsulas meeting at a "
  "mountainous centre, with distinct languages up each one.",
 "North Borneo Malayo-Polynesian":
  "The languages of Sabah, Brunei and northern Kalimantan — Dusun, Kadazan, Murut, and the "
  "Sama-Bajaw languages of the sea nomads, whose speakers lived on boats across the Sulu and "
  "Celebes seas and are among the last maritime nomadic peoples anywhere.",
 "Greater Barito linkage":
  "The languages of southeastern Borneo — and the origin of Malagasy. Malagasy's closest "
  "relatives are here, seven thousand kilometres away across the Indian Ocean, which is how we "
  "know Madagascar was settled from Borneo around 700 CE. It is the longest prehistoric ocean "
  "migration attested by language.",
 "Timor-Babar":
  "The Austronesian languages of Timor and the islands east of it, including Tetum, a national "
  "language of Timor-Leste alongside Portuguese. They sit alongside Papuan languages on the same "
  "islands, and the two families have been exchanging structure for millennia.",
}

MID_BRANCH = {
 # ---------------- AFRO-ASIATIC (381 languages, 0 branch cards)
 "Semitic":
  "Arabic, Hebrew, Amharic, Tigrinya, Aramaic, Maltese — and, through Akkadian, the oldest "
  "written language of any family: cuneiform tablets from about 2500 BCE. Semitic's defining "
  "trick is the root: most words are built from three consonants carrying the meaning, with "
  "vowels slotted between them carrying the grammar, so *k-t-b* gives write, book, writer, "
  "office and library. That is why an Arabic or Hebrew script can leave the vowels out.",
 "West Semitic":
  "Everything except Akkadian — Arabic, the Ethiopian languages, Hebrew, Aramaic, and the "
  "extinct Canaanite and South Arabian languages. The alphabet was invented here: every "
  "alphabetic script on earth, Latin and Cyrillic and Greek and Devanagari and Hangul's "
  "inspiration alike, descends from a West Semitic writing system of about 1800 BCE.",
 "Central Semitic":
  "Arabic, Hebrew and Aramaic together with the extinct Canaanite languages. Aramaic was the "
  "administrative language of the Persian empire, and its script is the ancestor of Hebrew "
  "square script, Arabic, Syriac, Mongolian and — through Brahmi's likely Aramaic model — much "
  "of South and Southeast Asian writing.",
 "Arabic":
  "Thirty-seven varieties here, and the count is the point: Moroccan and Iraqi Arabic are as "
  "different as Portuguese and Romanian, and no Arabic speaker calls them separate languages. "
  "Modern Standard Arabic is the written and formal register everywhere and nobody's mother "
  "tongue anywhere — a diglossia a thousand years deep, held together by the Qur'an.",
 "Cushitic":
  "Oromo, Somali, Afar, Beja and their relatives across the Horn of Africa. Somali is one of "
  "very few African languages to be made a national medium of government and schooling — in "
  "1972, with a Latin orthography chosen after a decade of argument, followed by a mass literacy "
  "campaign.",
 "Chadic":
  "Two hundred and ten languages around Lake Chad, and Hausa among them — one of Africa's great "
  "lingua francas, with tens of millions of second-language speakers across the Sahel. Chadic is "
  "the largest branch of Afro-Asiatic by language count and the least described.",
 "Berber":
  "Tamazight and its relatives across North Africa, from Morocco to the Siwa oasis in Egypt. "
  "They survived twelve centuries of Arabic as the languages of mountains and desert, and are "
  "written in Tifinagh — a script descended from ancient Libyco-Berber, kept alive by Tuareg "
  "women, and made official in Morocco in 2003 after being banned for decades.",
 "Ta-Ne-Omotic":
  "The larger half of Omotic, in southwestern Ethiopia — Wolaytta, Gamo, Kafa and their "
  "relatives. Omotic's membership in Afro-Asiatic is the least secure of any branch: several "
  "specialists argue it is not Afro-Asiatic at all. Glottolog does not even keep it as one "
  "node, splitting it into this and South Omotic — which is the doubt made structural.",
 "South Omotic":
  "Aari, Hamer-Banna and Dime, in the lower Omo valley. Held apart from the rest of Omotic here "
  "because the two groups may not be each other's closest relatives, and possibly not related "
  "at all — one of the genuinely open questions in African historical linguistics.",
 # ---------------- TRANS NEW GUINEA (317 languages, 0 branch cards)
 "Madang":
  "A hundred and eight languages in one province of Papua New Guinea, an area smaller than "
  "Denmark. New Guinea holds about a fifth of the world's languages on under one per cent of its "
  "land, and Madang is the densest part of it: valleys a day's walk apart speak languages that "
  "share no vocabulary.",
 "Finisterre-Huon":
  "Sixty-one languages in the mountains behind the Huon Gulf. This is where Trans New Guinea was "
  "first argued for as a family, in the 1970s, on the strength of shared pronouns — and pronouns "
  "remain most of the evidence, which is why the family's outer limits are still disputed.",
 "Kainantu-Goroka":
  "The languages of the eastern highlands, including several with a few tens of thousands of "
  "speakers and no writing. The highlands were unknown to the outside world until aerial survey "
  "in the 1930s revealed a densely populated agricultural landscape where the maps said nothing.",
 "Asmat-Awyu-Ok":
  "The languages of the southern lowlands and the Ok mountains, spread across the Indonesian "
  "border. Ok languages are among the better-described in the family; Asmat is known outside it "
  "chiefly for wood carving.",
 "Rai Coast":
  "The languages of the coast southeast of Madang, where Miklouho-Maclay lived from 1871 and "
  "wrote the first sustained European description of any New Guinea community — and collected "
  "word lists that are still the earliest record of several of these languages.",
 # ---------------- OTOMANGUEAN (181 languages, 0 branch cards)
 "Eastern Otomanguean":
  "Mixtec, Zapotec, Mazatec, Amuzgo, Chatino and their relatives — a hundred and forty-five "
  "languages, most in Oaxaca. Oaxaca is the most linguistically diverse state in Mexico and one "
  "of the most diverse comparable areas anywhere.",
 "Mixtec":
  "Fifty-three languages, all called Mixtec. That is not a naming quirk but a fact about the "
  "record: they occupy a continuous mountain region, neighbouring valleys understand each other "
  "and distant ones do not, and no standard variety ever won out — so each is named for its town. "
  "Ñuu Savi, the People of the Rain, wrote pre-conquest codices in a pictorial system that "
  "recorded genealogy and conquest, and eight of those codices survive.",
 "Mixtecan":
  "Mixtec with Cuicatec and Trique. Otomanguean is a tonal family — most of its languages use "
  "pitch to distinguish words, and several Mixtec varieties have a whistled register that "
  "carries the tones across a valley without the words.",
 "Zapotecan":
  "Zapotec and Chatino, sixty-four languages. The Zapotec state at Monte Albán produced the "
  "earliest writing in the Americas outside the Maya area — inscriptions from about 500 BCE that "
  "are still only partly read.",
 "Zapotec":
  "Fifty-seven languages named Zapotec, for the same reason as Mixtec: a mountain landscape, no "
  "single standard, and a name applied from outside to everyone who spoke something like it. "
  "Isthmus Zapotec has the strongest literary tradition and Juchitán has published in it since "
  "the nineteenth century.",
 "Popolocan-Mazatecan":
  "Mazatec, Popoloca, Ixcatec and Chocho. Mazatec is the language of the whistled speech of the "
  "Sierra Mazateca, in which men hold entire conversations across ravines by whistling the tones "
  "of the words — the best-documented whistled register anywhere.",
 "Otopamean":
  "Otomí, Mazahua, Matlatzinca and Pame, in central Mexico. Otomí was written in a pictorial "
  "system before the conquest and in Latin letters from the 1550s, and it is one of the larger "
  "indigenous languages of Mexico still spoken near the capital.",
 "Western Otomanguean":
  "Otomí, Mazahua, Chinantec, Mazatec and their relatives, north and west of the Zapotec-Mixtec "
  "block. Chinantec, like Mazatec, has a whistled form; Otomanguean's tone systems are what make "
  "that possible.",
}

SEVEN_BRANCH = {
 # ---------------- AUSTROASIATIC
 "Mundaic":
  "The Munda languages of eastern India — Santali, Mundari, Ho, Sora — a thousand kilometres "
  "from every other Austroasiatic language and structurally unlike them: Munda is heavily "
  "suffixing and polysynthetic where Khmer and Vietnamese are isolating. That divergence is the "
  "clearest evidence that Austroasiatic once covered ground it no longer holds, and that Munda "
  "restructured under long contact with Indo-Aryan and Dravidian neighbours.",
 "Khasi-Palaung":
  "Khasi in Meghalaya and the Palaungic languages of Myanmar and Yunnan — another Austroasiatic "
  "outlier group, stranded either side of a gap now filled by Tibeto-Burman and Indo-Aryan.",
 "Palaungic":
  "The languages of the Shan hills and southern Yunnan, including Wa, Blang and Palaung. Wa was "
  "unwritten until the twentieth century and now has competing Latin orthographies on either "
  "side of the China–Myanmar border.",
 "Bahnaric":
  "Thirty-six languages of the Central Highlands of Vietnam, Laos and Cambodia — Bahnar, Sedang, "
  "Koho, Stieng. Most were written for the first time by French missionaries and then by "
  "American linguists during the war; several communities have been displaced since.",
 "Aslian":
  "The Austroasiatic languages of the Malay peninsula, spoken by Orang Asli communities and "
  "surrounded entirely by Austronesian Malay. They are the southernmost Austroasiatic languages "
  "and the last trace of the family's presence there before Malay arrived.",
 # ---------------- TAI-KADAI
 "Kam-Tai":
  "Thai, Lao, Shan, Zhuang and their relatives — the bulk of the family. Tai-Kadai's homeland is "
  "in southern China, not Thailand: its deepest diversity is in Guangxi, Guizhou and Hainan, and "
  "the Tai peoples moved south into mainland Southeast Asia only in the last thousand years, "
  "which is recent enough that the Thai and Lao languages are still very close.",
 "Southwestern Tai":
  "Thai, Lao, Shan, Northern Thai, Isan, Tai Dam — a group that spread across mainland Southeast "
  "Asia within a few centuries and remains largely mutually intelligible. Their scripts all "
  "descend from the Khmer adaptation of Indic writing, which is why Thai and Lao letters look "
  "related and Chinese characters play no part.",
 "Daic":
  "The wider grouping including the Kam-Sui languages of Guizhou and the Hlai languages of "
  "Hainan. Hlai is the most divergent branch and the strongest argument for the family's "
  "southern-Chinese origin.",
 # ---------------- DRAVIDIAN
 "South Dravidian":
  "Tamil, Malayalam, Kannada, Tulu, Kodava and the small languages of the Nilgiris — the branch "
  "with the literary languages. Tamil's record begins around 300 BCE, Kannada's around 450 CE, "
  "and Malayalam split off from Tamil late enough that the two share most of their classical "
  "inheritance.",
 "Tamil-Kannada":
  "The core of South Dravidian. Kannada and Tamil both have classical status in India and "
  "literary traditions well over a thousand years old; Malayalam separated from Tamil around the "
  "ninth century, largely through heavy Sanskrit borrowing that Tamil resisted.",
 # ---------------- MANDE
 "Western Mande":
  "Bambara, Maninka, Dyula, Soninke, Susu, Mende, Vai and their relatives across West Africa. "
  "The Manding languages within this group form a continuum from Senegal to Burkina Faso and "
  "carry the griot tradition — hereditary oral historians whose repertoire includes the Sunjata "
  "epic of the thirteenth-century Mali empire, still performed.",
 "Manding-Vai":
  "Manding together with Vai and Kono. Two indigenous scripts came out of this group: the Vai "
  "syllabary of about 1833, and N'Ko, devised for Manding by Solomana Kanté in 1949 after he "
  "read a Lebanese writer's claim that African languages could not be written. N'Ko is written "
  "right to left and is in use across Guinea, Mali and Côte d'Ivoire.",
 "Eastern Mande":
  "The Mande languages of Côte d'Ivoire, Burkina Faso and Nigeria — Dan, Mano, Bisa, Busa. Mande "
  "as a whole is one of the branches whose place inside Niger-Congo is least settled; several "
  "specialists treat it as a separate family.",
 # ---------------- UTO-AZTECAN
 "Southern Uto-Aztecan":
  "The languages of northwest Mexico and Mesoamerica — Nahuatl, Cora, Huichol, Yaqui, Mayo, "
  "Tarahumara, O'odham. Uto-Aztecan is one of very few families to span the Mexico–United States "
  "divide, reaching from Oregon to El Salvador.",
 "Aztec":
  "About thirty Nahuatl languages, from Durango to Veracruz. Classical Nahuatl was the "
  "administrative language of the Aztec empire and remained an administrative language under "
  "Spanish rule for two centuries: more was printed in Nahuatl in the sixteenth century than in "
  "most European vernaculars, and Nahua scholars compiled the twelve-volume Florentine Codex in "
  "it. Nahuatl gave English chocolate, tomato, avocado, coyote and chilli.",
 "Northern Uto-Aztecan":
  "Hopi, Shoshone, Comanche, Paiute, Ute, Luiseño and their relatives across the Great Basin and "
  "the Southwest. Comanche was the basis of a code-talker programme in the Second World War, as "
  "Navajo was.",
 # ---------------- ARAWAKAN
 "Southern Maipuran":
  "The Arawakan languages of the southwestern Amazon and the Andean foothills — Asháninka, "
  "Machiguenga, Piro, Terena. Arawakan is among the most widely spread families in South "
  "America; its speakers were the first Americans Europeans met, since Taíno in the Caribbean "
  "was Arawakan and gave English canoe, hammock, hurricane, tobacco and barbecue.",
 "Caribbean Arawakan":
  "Lokono, Garifuna and the extinct Taíno and Island Carib. Garifuna is the odd one: its "
  "speakers are the descendants of Africans and Island Caribs deported from St Vincent to "
  "Central America in 1797, and the language is Arawakan with a Cariban men's vocabulary layered "
  "over it.",
 # ---------------- TUPIAN
 "Tupi-Guarani":
  "Guaraní, Tupinambá, Kamayurá, Kaiowá and forty others across Brazil, Paraguay, Bolivia and "
  "Argentina. Tupinambá became the *língua geral* of colonial Brazil — the working language of "
  "the whole colony until Portuguese was imposed by decree in 1758 — and Paraguayan Guaraní is "
  "the only indigenous American language that is the majority language of a country.",
 "Eastern Tupian":
  "Tupi-Guarani together with the Aweti and Mawé branches. Tupian's deepest diversity is in "
  "Rondônia in the southwestern Amazon, which places the family's homeland there rather than on "
  "the Atlantic coast where Europeans first met it.",
}


def strip_paren(name: str) -> str:
    # ⚠ Glottolog disambiguates with a trailing bracket — "Murik (Malaysia)", "Aja (Benin)".
    # Taking the last word of the raw name reported "Malaysia" and "Indonesia" as clusters.
    return PAREN.sub("", name).strip()


def clusters_of(names: list[str]) -> list[list]:
    """Shared final words in a set of language names, largest first."""
    c = Counter(strip_paren(n).split()[-1] for n in names if strip_paren(n))
    out = [[w, n] for w, n in c.items() if n >= MIN_CLUSTER and len(w) > 2]
    out.sort(key=lambda t: -t[1])
    return out


def node_clusters(tree: dict) -> dict[str, list]:
    """Clusters at EVERY node, so a branch card can explain its own naming too."""
    found: dict[str, list] = {}

    def walk(n) -> list[str]:
        # ⚠ A LANGUAGE STOPS THE WALK, whether or not it has children. Glottolog gives most
        # languages dialect children, and testing `if not kids` first meant a language with
        # dialects returned its DIALECTS' names instead of its own — so the Mixtec node reported
        # 40 where the family reported 53, and the two numbers disagreed on screen.
        if n.get("lv") == 1:
            return [n.get("n", "")]
        kids = n.get("c") or []
        if not kids:
            return []
        names: list[str] = []
        for k in kids:
            names.extend(walk(k))
        if n.get("lv") == 0 and len(names) >= MIN_CLUSTER:
            cl = clusters_of(names)
            if cl:
                found[n["g"]] = cl
        return names

    walk(tree)
    return found


def main() -> None:
    # A true ISOLATE has Level='language' and no family: the language is its own top node, so
    # there is no family row to match "Basque" or "Sumerian" against. Both levels are indexed,
    # family first, and an ambiguous name is still refused.
    names: dict[str, list] = {}
    isolate_names: dict[str, list] = {}
    with open(GL, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["Level"] == "family":
                names.setdefault(r["Name"], []).append(r["ID"])
            elif r["Level"] == "language" and not r["Family_ID"]:
                isolate_names.setdefault(r["Name"], []).append(r["ID"])

    idx = json.load(open(os.path.join(WEB, "tree", "index.json"), encoding="utf-8"))
    langs = json.load(open(os.path.join(WEB, "languages.json"), encoding="utf-8"))
    F = {k: i for i, k in enumerate(langs["fields"])}
    rows = langs["rows"]

    # what the museum already holds, per language, so a family can state its own coverage
    def keys(path, sub=None):
        if not os.path.exists(os.path.join(WEB, path)):
            return set()
        d = json.load(open(os.path.join(WEB, path), encoding="utf-8"))
        return set((d.get(sub) or d) if sub else d)
    have = {
        "label": keys("notable.json", "by_glottocode"),
        "object": keys("gallery.json"),
        "prose": keys("texts.json", "by_glottocode"),
        "words": keys("words.json", "by_glottocode"),
        "letters": keys("alphabets.json", "by_glottocode"),
        "heard": keys("audio.json", "by_glottocode"),
        "dated": keys("milestones.json", "by_glottocode"),
    }

    fam_langs: dict[str, list] = {}
    for r in rows:
        fam_langs.setdefault(r[F["famid"]], []).append(r)

    # resolve the authored table by name, refusing anything that does not match exactly one
    authored: dict[str, tuple[list[str], str]] = {}
    for nm, (terms, text) in FAM.items():
        hit = names.get(nm) or isolate_names.get(nm) or []
        if len(hit) != 1:
            print(f"  SKIPPED {nm!r}: matched {len(hit)} families or isolates in Glottolog")
            continue
        authored[hit[0]] = (terms, text)

    # BRANCH DESCRIPTIONS. Internal nodes are Level='family' in Glottolog, so they resolve
    # through exactly the same name gate as the top-level families — a name that matches nothing
    # or matches twice stops the build. These replace "branch of the Indo-European language
    # family", which passed the old substantive() test while restating the tree.
    branch_text: dict[str, str] = {}
    for src in (IE_BRANCH, ST_BRANCH, PN_BRANCH, AC_BRANCH, AN_BRANCH,
                MID_BRANCH, SEVEN_BRANCH):
        for nm, txt in src.items():
            hit = names.get(nm) or []
            if len(hit) != 1:
                raise SystemExit(f"branch {nm!r} matched {len(hit)} Glottolog families")
            branch_text[hit[0]] = txt

    out: dict[str, dict] = {}
    allclusters: dict[str, list] = {}
    subjects: list[list] = []
    for f in idx["families"]:
        gc = f["g"]
        if f.get("pseudo"):
            continue
        mine = fam_langs.get(gc) or []
        rec: dict = {"n": f["n"], "lang": f.get("lang", 0), "dial": f.get("dial", 0),
                     "extinct": f.get("extinct", 0), "endangered": f.get("endangered", 0),
                     "ma": f.get("ma", ""), "isolate": bool(f.get("isolate"))}
        if f.get("age"):
            rec["age"] = f["age"]
            rec["ageExplicit"] = bool(f.get("ageExplicit"))
        cl = clusters_of([r[F["name"]] for r in mine])
        if cl:
            rec["clusters"] = cl
        # earliest attested member
        att = [(r[F["first"]], r[F["name"]]) for r in mine if r[F["first"]]]
        if att:
            y, nm2 = min(att)
            rec["earliest"] = [y, nm2]
        # countries the family is spoken in
        # ⚠ SEMICOLONS, not spaces. Glottolog writes "ER;ET;SD"; splitting on whitespace
        # returned one token per language and the count was meaningless even once the column
        # had a name.
        cs = sorted({c for r in mine for c in (r[F["cc"]] or "").split(";") if c}) \
            if "cc" in F else []
        if cs:
            rec["countries"] = len(cs)
        # coverage: what this museum holds for this family
        cov = {k: sum(1 for r in mine if r[F["code"]] in s) for k, s in have.items()}
        rec["coverage"] = cov
        if gc in authored:
            terms, text = authored[gc]
            rec["text"] = text
            for q in terms:
                # ONE predicate, imported rather than copied: a place category holds landscapes
                # and several were authored in this very file as fallbacks (Category:Chile,
                # Category:Mali). See build_notable.admissible_subject for why.
                # is_family: a plural, branch-wide category IS this card's subject.
                if _bn.admissible_subject(q, is_family=True):
                    subjects.append([gc, q])
        out[gc] = rec

        # per-node clusters, so branch cards can explain themselves
        tp = os.path.join(WEB, "tree", gc + ".json")
        if os.path.exists(tp) and (cl or f.get("lang", 0) >= MIN_CLUSTER):
            try:
                allclusters.update(node_clusters(json.load(open(tp, encoding="utf-8"))))
            except Exception as e:                           # noqa: BLE001
                print(f"  could not read the tree for {gc}: {e}")

    json.dump({"note": "One card per family. Counts, clusters, earliest attestation and coverage "
                       "are measured from this build; the description is authored and keyed by "
                       "exact Glottolog name.",
               "min_cluster": MIN_CLUSTER,
               "by_glottocode": out, "clusters_by_node": allclusters,
               "branch_text": branch_text},
              open(os.path.join(WEB, "families.json"), "w"), ensure_ascii=False,
              separators=(",", ":"))

    # The FAMILY half of the gallery queue, in its own file. It used to be appended to the
    # single subjects.json build_notable.py writes, which meant the two had to run in one
    # specific order and nothing said so. They no longer touch each other's file.
    json.dump([list(x) for x in subjects],
              open(os.path.join(ROOT, "data", "gallery", "subjects_families.json"), "w"),
              ensure_ascii=False)

    print(f"   {len(branch_text)} branch nodes carry an authored description")
    described = sum(1 for v in out.values() if v.get("text"))
    withcl = sum(1 for v in out.values() if v.get("clusters"))
    print(f"{len(out)} families · {described} with an authored description · "
          f"{withcl} whose languages fall into name clusters · "
          f"{len(allclusters)} nodes carry a cluster explanation")
    print(f"   {len(subjects)} family gallery subjects appended to the queue")
    big = sorted(out.items(), key=lambda kv: -sum(c[1] for c in kv[1].get("clusters", [])))[:6]
    for gc, v in big:
        cl = ", ".join(f"{w} {n}" for w, n in v.get("clusters", [])[:4])
        print(f"   {v['n'][:24]:26s} {sum(c[1] for c in v.get('clusters', [])):4d} of "
              f"{v['lang']:4d} in clusters — {cl}")


if __name__ == "__main__":
    main()
