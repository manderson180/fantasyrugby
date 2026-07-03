#!/usr/bin/env python3
"""
build_international_squads.py — the international-duty half of the injury scan.

Encodes the researched summer-2026 international squads (the 2026 Nations Championship
July window) as data and writes injury/international_squads.csv. build_injury.py then
folds these in as "International Duty" for any of our URC/PREM players named in a squad
(a club injury/suspension always takes precedence).

To refresh: update the SQUADS below from the latest squad announcements and re-run:
    python3 injury/build_international_squads.py
    python3 injury/build_injury.py

Scope note: the July 2026 window is the Nations Championship. Wales and Ireland are already
covered in player_availability.csv. France and New Zealand have no URC/PREM players. Japan's
squad has no URC/PREM players either (not ingested). Samoa, Tonga and Georgia are not in this
window (their tests fall later), so their league players are not away in July.
"""

import csv
from pathlib import Path

HERE = Path(__file__).resolve().parent
WINDOW = "the 2026 Nations Championship (July window)"

# nation -> (source_name, source_url, source_date, [players])
SQUADS = {
    "England": (
        "England squad for the 2026 Nations Championship",
        "https://www.englandrugby.com/follow/news-and-media/england-squad-named-nations-championship-2026",
        "2026-06-19",
        ["Ollie Chessum", "Arthur Clark", "Alex Coles", "Luke Cowan-Dickie", "Tom Curry",
         "Theo Dan", "Ben Earl", "Charlie Ewels", "Greg Fisilau", "Ellis Genge", "Jamie George",
         "Joe Heyes", "Ted Hill", "George Kloska", "George Martin", "Beno Obano",
         "Asher Opoku-Fordjour", "Guy Pepper", "Henry Pollock", "Vilikesa Sela", "Seb Atkinson",
         "Noah Caluori", "Immanuel Feyi-Waboso", "George Ford", "Tommy Freeman", "George Furbank",
         "Benhard Janse van Rensburg", "Alex Mitchell", "Cadan Murley", "Max Ojomoh", "Henry Slade",
         "Fin Smith", "Marcus Smith", "Ben Spencer", "Freddie Steward", "Jack van Poortvliet"],
    ),
    "Scotland": (
        "Scotland squad for the 2026 Nations Championship",
        "https://www.theoffsideline.com/scotland-2026-summer-nations-championship-series-squad-announced/",
        "2026-06-18",
        ["Ewan Ashman", "Josh Bayliss", "Magnus Bradbury", "Gregor Brown", "Scott Cummings",
         "Rory Darge", "Jack Dempsey", "Freddy Douglas", "Matt Fagerson", "Zander Fagerson",
         "Jonny Gray", "Gregor Hiddleston", "Will Hurd", "Nathan McBeth", "Liam McConnell",
         "Elliot Millar Mills", "D'arcy Rae", "Alex Samuel", "Pierre Schoeman", "Seb Stephen",
         "Rory Sutherland", "Max Williamson", "Fergus Burke", "Jamie Dobie", "Darcy Graham",
         "George Horne", "Rory Hutchinson", "Tom Jordan", "Stafford McDowall", "Kyle Rowe",
         "Finn Russell", "Ollie Smith", "Kyle Steyn", "Sione Tuipulotu", "Duhan van der Merwe",
         "Ben White"],
    ),
    "Italy": (
        "Italy squad for the 2026 Nations Championship",
        "https://www.rugbypass.com/news/gonzalo-quesada-announces-italy-squad-and-explains-ange-capuozzos-absence-nations-championship/",
        "2026-06-17",
        ["Lorenzo Cannone", "Niccolò Cannone", "Tommaso Di Bartolomeo", "Pablo Dimcheff",
         "Riccardo Favretto", "Danilo Fischetti", "Muhamed Hasa", "Michele Lamaro",
         "Gianmarco Lucchesi", "Giulio Marini", "Ion Neculai", "David Odiase", "Alessandro Ortombina",
         "Marco Riccioni", "Federico Ruzza", "Mirco Spagnolo", "Ross Vintcent", "Andrea Zambonin",
         "Tommaso Allan", "Giulio Bertaccini", "Juan Ignacio Brex", "Giacomo Da Re", "Malik Faissal",
         "Alessandro Fusco", "Alessandro Garbisi", "Paolo Garbisi", "Monty Ioane", "Louis Lynagh",
         "Leonardo Marin", "Tommaso Menoncello", "Paolo Odogwu", "Lorenzo Pani", "Stephen Varney"],
    ),
    "South Africa": (
        "South Africa (Springboks) squad for the 2026 Nations Championship",
        "https://springboks.rugby/news-features/articles/2026/6/20/bok-squad",
        "2026-06-20",
        ["Thomas du Toit", "Wilco Louw", "Ntuthuko Mchunu", "Ox Nche", "Zachary Porthen",
         "Carlu Sadie", "Gerhard Steenekamp", "Boan Venter", "Johan Grobbelaar", "Malcolm Marx",
         "Andre-Hugo Venter", "Lood de Jager", "Eben Etzebeth", "Ruan Nortje", "Ruben van Heerden",
         "Paul de Villiers", "Ben-Jason Dixon", "Cameron Hanekom", "Siya Kolisi", "Evan Roos",
         "Vincent Tshituka", "Jasper Wiese", "Elrigh Louw", "Pieter-Steph du Toit", "Franco Mostert",
         "Marco van Staden", "Jan-Hendrik Wessels", "Cobus Wiese", "Embrose Papier",
         "Herschel Jantjies", "Cobus Reinach", "Grant Williams", "Manie Libbok", "Vusi Moyo",
         "Handre Pollard", "Damian de Allende", "Andre Esterhuizen", "Jesse Kriel", "Kurt-Lee Arendse",
         "Aphelele Fassi", "Quan Horn", "Cheslin Kolbe", "Canan Moodie", "Edwill van der Merwe",
         "Jaco Williams", "Damian Willemse", "Ethan Hooker"],
    ),
    "Argentina": (
        "Argentina (Los Pumas) squad for the 2026 Nations Championship",
        "https://www.planetrugby.com/news/argentina-squad-felipe-contepomi-names-five-uncapped-men-in-nations-championship-group",
        "2026-06-19",
        ["Matías Alemanno", "Luciano Asevedo", "Francisco Coria Machetti", "Pedro Delgado",
         "Santiago Grondona", "Marcos Kremer", "Pablo Matera", "Franco Molina", "Julián Montoya",
         "Joaquín Moro", "Joaquín Oviedo", "Leonel Oviedo", "Juan Penoucos", "Guido Petti",
         "Tomás Rapetti", "Ignacio Ruiz", "Mayco Vivas", "Boris Wenger", "Tomás Albornoz",
         "Simón Benítez Cruz", "Mateo Carreras", "Santiago Carreras", "Lucio Cinti", "Bautista Delguy",
         "Agustín Fraga", "Gonzalo García", "Rodrigo Isgro", "Ignacio Mendy", "Matías Moroni",
         "Agustín Moyano", "Gerónimo Prisciantelli", "Nicolás Roger", "Faustino Sánchez Valarolo",
         "Mateo Soler"],
    ),
    "Australia": (
        "Australia (Wallabies) squad for the 2026 Nations Championship",
        "https://wallabies.rugby/news/wallabies-squad-confirmed-for-july-nations-championship-tests-2026618",
        "2026-06-18",
        ["Allan Alaalatoa", "Miles Amatosero", "Angus Bell", "Charlie Cale", "Josh Canham",
         "Nick Champion De Crespigny", "Tom Hooper", "Fraser McReight", "Josh Nasser", "Zane Nonggorr",
         "Brandon Paenga-Amosa", "Billy Pollard", "Aidan Ross", "Lachlan Shaw", "James Slipper",
         "Carlo Tizzano", "Taniela Tupou", "Rob Valetini", "Jeremy Williams", "Harry Wilson",
         "Jock Campbell", "Filipo Daugunu", "Ben Donaldson", "Josh Flook", "Carter Gordon",
         "Len Ikitau", "Max Jorgensen", "Ryan Lonergan", "Tate McDermott", "Declan Meredith",
         "Hunter Paisami", "Dylan Pietsch", "Harry Potter", "Joseph-Aukuso Suaalii", "Kalani Thomas",
         "Corey Toole", "Tom Wright"],
    ),
    "Fiji": (
        "Fiji (Flying Fijians) squad for the 2026 Nations Championship",
        "https://www.planetrugby.com/news/ex-france-and-england-regulars-named-in-fijis-star-studded-nations-championship-squad",
        "2026-06-15",
        ["Eroni Mawi", "Atunaisa Sokobale", "Peni Ravai", "Livai Natave", "Haereiti Hetet",
         "Luke Tagi", "Tim Hoyt", "Vilikesa Nairau", "Mesake Doge", "Tevita Ikanivere",
         "Kavaia Tagivetaua", "Zuriel Togiatama", "Sam Matavesi", "Isoa Nasilasila", "Mesake Vocevoce",
         "Albert Tuisue", "Temo Mayanavanua", "Tevita Ratuva", "Joseva Tamani", "Lekima Tagitagivalu",
         "Etonia Waqa", "Isoa Tuwai", "Elia Canakaivata", "Levani Botia", "Kitione Salawa",
         "Pita-Gus Sowakula", "Peceli Yato", "Nathan Hughes", "Frank Lomani", "Simione Kuruvoli",
         "Sam Wye", "Philip Baselala", "Caleb Muntz", "Isaia Armstrong-Ravula", "Kemu Valetini",
         "Josua Tuisova", "Filimoni Botitu", "Isikeli Rabitu", "Virimi Vakatawa", "Iosefo Masi",
         "Semi Radradra", "Seta Tamanivalu", "Sireli Maqala", "Jiuta Wainiqolo",
         "Selestino Ravutaumada", "Kalaveti Ravouvou", "Vinaya Habosi", "Manasa Mataele",
         "Salesi Rayasi", "Vuate Karawalevu"],
    ),
}


def main():
    rows = []
    for nation, (sname, surl, sdate, players) in SQUADS.items():
        for p in players:
            rows.append({"nation": nation, "player_name": p, "window": WINDOW,
                         "source_name": sname, "source_url": surl, "source_date": sdate})
    out = HERE / "international_squads.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["nation", "player_name", "window",
                                          "source_name", "source_url", "source_date"])
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {len(rows)} squad rows across {len(SQUADS)} nations -> {out.name}")


if __name__ == "__main__":
    main()
