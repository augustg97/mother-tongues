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
                if _bn.admissible_subject(q):
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
               "by_glottocode": out, "clusters_by_node": allclusters},
              open(os.path.join(WEB, "families.json"), "w"), ensure_ascii=False,
              separators=(",", ":"))

    # append the family subjects to the queue build_notable.py wrote
    sp = os.path.join(ROOT, "data", "gallery", "subjects.json")
    existing = json.load(open(sp, encoding="utf-8")) if os.path.exists(sp) else []
    existing = [x for x in existing if x[0] not in out or x[0] in
                {r[F["code"]] for r in rows}]        # drop a previous family run's rows
    json.dump([list(x) for x in existing] + subjects, open(sp, "w"), ensure_ascii=False)

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
