import pandas as pd

R = []
RP_APR = ("RugbyPass injury-list audit","2026-04-26","https://www.rugbypass.com/news/the-mind-blowing-injury-lists-mounting-up-across-prem-and-urc/")
IRFU = ("IRFU squad announcement via RTE/Irish Times","2026-06-20","https://www.rte.ie/sport/rugby/2026/0620/1579488-blow-for-ireland-as-doris-and-obrien-ruled-out-of-tour/")
WRU = ("Wales 33-man Nations Championship squad via Nation.Cymru/PA","2026-06-30","https://nation.cymru/sport/dafydd-jenkins-out-of-wales-nations-championship-matches-due-to-shoulder-injury/")

STATUS_LABELS = {
    "healthy": "Healthy",
    "injured": "Injured",
    "unknown_potentially_injured": "Potential Injury",
    "international_duty": "International Duty",
    "retired_medical": "Retired (Medical)",
    "unavailable_other": "Unavailable (Other)",
    "suspended": "Suspended",
    "coverage_gap": "",
    "review_item": "",
}

def row(comp, team, player, status, inj_date, date_type, inj_type, body, ret, conf, verified, src, internal_note,
        user_status=None, user_note=""):
    R.append(dict(
        competition=comp, team=team, player_name=player,
        user_status=user_status if user_status is not None else STATUS_LABELS.get(status, status),
        user_notes=user_note,
        expected_return=ret, injury_date=inj_date, injury_date_type=date_type,
        injury_type=inj_type, body_part=body, confidence=conf, last_verified=verified,
        internal_status=status, source_name=src[0], source_date=src[1], source_url=src[2],
        internal_notes=internal_note,
    ))

STALE_GENERIC = ("Was reported unavailable due to injury in late April 2026. No specific injury details were "
                  "given and there's been no more recent update, so the current status can't be confirmed - "
                  "treat as uncertain rather than assume they're still out.")

def stale(comp, team, players, internal_extra="", user_note=None, overrides=None):
    overrides = overrides or {}
    for p in players:
        un, ust = overrides.get(p, (user_note or STALE_GENERIC, None))
        row(comp, team, p, "unknown_potentially_injured", "2026-04-26", "first_reported", "unspecified", "unspecified",
            "unknown", "low", "2026-04-26", RP_APR,
            (f"On club unavailable-for-selection list 26 Apr 2026; not re-verified since (stale >6 weeks) - "
             f"pre-season re-check required. {internal_extra}").strip(),
            user_status=ust, user_note=un)

def wales_note(extra=""):
    return (f"Named in Wales's squad for the summer internationals (through 18 July). Fit and away on "
            f"international duty, not injured. {extra}").strip()

def ireland_note(extra=""):
    return (f"Named in Ireland's squad for the summer tour to Australia, Japan and New Zealand (through 18 July). "
            f"Fit and away on international duty, not injured. {extra}").strip()

def scotland_note(extra=""):
    return (f"Named in Scotland's squad for the summer internationals. Fit and away on international duty, "
            f"not injured. {extra}").strip()

def ireland_injured_note(extra=""):
    return (f"Listed as unavailable due to injury in Ireland's squad announcement (17 June). The specific "
            f"injury wasn't disclosed publicly. {extra}").strip()

# ---------------- GALLAGHER PREM ----------------
# Bath
row("PREM","Bath","Finn Russell","unknown_potentially_injured","2026-06-08","first_reported","soft tissue","calf","unknown","medium","2026-06-08",
    ("Planet Rugby (Bath press conf)","2026-06-08","https://www.planetrugby.com/news/bath-boss-reveals-extent-of-finn-russells-injury-and-pays-respect-to-family-man-leaving-the-club-in-the-summer"),
    "Rested from final regular-round win with calf issue, described as risk management; unclear whether he featured in play-offs - verify",
    user_note="Rested from Bath's final regular-season game with a calf issue, which the club described as risk management rather than a serious injury. It isn't confirmed whether he went on to play in the play-offs.")

# Bristol (Apr list)
stale("PREM","Bristol Bears",["Jimmy Halliwell","Paddy Pearce","Pedro Rubiolo","Steele Barker","Kenzie Jenkins","Santiago Grondona","Luka Ivanishvili","Steven Luatua","Viliame Mata","Kieran Marmion","AJ MacGinty","Victor Worsnip","Aidan Boshoff","Josh Carrington","Benjamin Elizalde","Evan Morris"])
row("PREM","Bristol Bears","Louis Rees-Zammit","international_duty","","","","","after Wales window (Jul 18 last Test)","high","2026-06-30",WRU,
    "Was on Apr injury list (missed Newcastle trip per Pat Lam) but named in Wales 33-man squad 30 Jun - injury resolved",
    user_note="Missed a game in April with an injury concern, but has since recovered and been named in Wales's squad for the summer internationals (through 18 July).")

# Exeter
EX_JUN = ("DevonLive via Yahoo (Baxter press conf)","2026-06-04","https://uk.sports.yahoo.com/news/exeter-chiefs-injury-latest-ahead-104939314.html")
for p in ["Jack Yeandle","Ross Vintcent","Tommy Wyatt"]:
    row("PREM","Exeter Chiefs",p,"injured","2026-06-04","first_reported","unspecified","unspecified","unknown (was ruled out for remainder of 2025-26)","medium","2026-06-04",EX_JUN,
        "Named by Baxter as out for the rest of the season on 4 Jun; 2026-27 pre-season status unconfirmed",
        user_note="Ruled out for the remainder of the 2025-26 season (confirmed 4 June). The specific injury wasn't disclosed, and fitness for pre-season hasn't yet been confirmed.")
row("PREM","Exeter Chiefs","Immanuel Feyi-Waboso","injured","2026-05-31","occurred","fracture (surgery)","face","unknown","high","2026-06-05",
    ("RugbyPass","2026-06-05","https://www.rugbypass.com/news/exeter-chiefs-suffer-massive-double-injury-blow-as-team-named-for-sarries/"),
    "Facial injury vs Leicester 31 May; operation agreed with England medics",
    user_note="Suffered a facial injury against Leicester on 31 May and had surgery on it. No return date has been confirmed.")
row("PREM","Exeter Chiefs","Greg Fisilau","unknown_potentially_injured","2026-05-31","occurred","unspecified","face","unknown","medium","2026-06-05",
    ("RugbyPass","2026-06-05","https://www.rugbypass.com/news/exeter-chiefs-suffer-massive-double-injury-blow-as-team-named-for-sarries/"),
    "Facial injury vs Leicester 31 May, missed Saracens game; unclear if he featured in play-offs/final - verify",
    user_note="Also picked up a facial injury in the same match on 31 May and missed the next game. It's not confirmed whether he returned for the play-offs.")
row("PREM","Exeter Chiefs","Dafydd Jenkins","injured","2026-06-20","occurred","unspecified","shoulder","unknown (ruled out of Wales Jul window)","high","2026-06-30",WRU,
    "Shoulder injury in Prem final vs Northampton 20 Jun; ruled out of Wales Nations Championship matches",
    user_note="Suffered a shoulder injury in the Premiership final (20 June) and has been ruled out of Wales's summer Test matches. No return date confirmed yet.")
row("PREM","Exeter Chiefs","Kane James","international_duty","","","","","after Wales window (Jul 18 last Test)","high","2026-06-30",WRU,
    "Returned from Jan ankle injury in June and named in Wales 33-man squad - fit",
    user_note="Recovered from an ankle injury sustained back in January and has been named in Wales's squad for the summer internationals.")

# Gloucester (Apr list)
stale("PREM","Gloucester",["Seb Blake","Jack Singleton","Jack Mann","Callum Braley","Josh Hathaway","Ben Redshaw","Rob Russell","Jack Cotgreave","Jamal Ford-Robinson","Ciaran Knight","Olly Allport","Harry Taylor"])
for p in ["Max Llewellyn","Tomos Williams"]:
    row("PREM","Gloucester",p,"international_duty","","","","","after Wales window (Jul 18 last Test)","high","2026-06-30",WRU,
        "Named in Wales 33-man squad 30 Jun - fit", user_note=wales_note())

# Harlequins (Apr list)
stale("PREM","Harlequins",["Harry Browne","Pedro Delgado","Jonny Green","Harry Williams","Boris Wenger","Cameron Doak","James Chisholm","Tate Williams","Fin Baxter","Titi Lamositele","Tom Lawday","Jordan Els","Simon Kerrod","Lucas Schmid","Jamie Benson","Josh Bellamy","Rodrigo Isgro","Ludo Kolade","Will Porter","Oscar Beard","Frank McMillan","Sean Sharp","Ben Waghorn","Tyrone Green","Cassius Cleaves"],
      internal_extra="Quins had 26 unavailable in Apr - highest in Prem.")
row("PREM","Harlequins","Stephan Lewies","unknown_potentially_injured","2026-04-26","first_reported","unspecified","unspecified","unknown","low","2026-04-26",RP_APR,
    "On club unavailable list 26 Apr; also reported joining Sharks (SA) for 2026-27",
    user_note="Was reported unavailable due to injury in late April, with no further update since. Separately, he's been reported as joining the Sharks in South Africa for next season.")

# Leicester
LT = ("Leicester Tigers official","2026-06-11","https://www.leicestertigers.com/news")
row("PREM","Leicester Tigers","Freddie Steward","healthy","2026-05-16","occurred","surgery","thumb","returned 2026-06-11","high","2026-06-11",LT,
    "Thumb surgery after Sale game (club statement 21 May); club TEAM NEWS confirmed return for play-off 11 Jun - resolved",
    user_note="Had thumb surgery in May after an injury against Sale, but recovered in time to return for the play-off game on 11 June.")
row("PREM","Leicester Tigers","Billy Searle","healthy","2026-05-01","first_reported","unspecified","unspecified","returned 2026-06-11","high","2026-06-11",LT,
    "One of two sidelined fly-halves in May; club TEAM NEWS confirmed return 11 Jun - resolved",
    user_note="Was sidelined earlier in the season, but returned for the 11 June play-off game.")
row("PREM","Leicester Tigers","James O'Connor","unknown_potentially_injured","2026-05-01","first_reported","unspecified","unspecified","unknown","medium","2026-06-03",
    ("RugbyPass (Parling press conf)","2026-06-03","https://www.rugbypass.com/news/leicester-injury-news/"),
    "Parling said one of Steward/Searle/O'Connor would be lucky to return before season end; Searle and Steward returned - O'Connor return unconfirmed; contract reportedly ending",
    user_status="Unclear",
    user_note="Was one of two fly-halves sidelined alongside Billy Searle, who has since returned. It isn't clear whether O'Connor has also recovered, and there have been reports his contract may be ending, which adds to the uncertainty.")

# Newcastle (Apr list)
stale("PREM","Newcastle Red Bulls",["Sammy Arnold","Eduardo Bello","Max Clark","Luan de Bruin","Connor Doherty","Ethan Grayson","Joel Grayson","Callum Hancock","Connor Hancock","Elvis Kitenge-Fuki","Freddie Lockwood","Amanaki Mafi","George McGuigan","Cameron Neild","Oli Spencer","Oscar Usher"])

# Northampton (Apr list)
stale("PREM","Northampton Saints",["Alex Coles","Trevor Davison","George Furbank","Tom James","Curtis Langdon","Henry Lumley","Tom Pearson","James Ramm","Freddie St John","Edoardo Todaro","JJ van der Mescht","Charlie Ulcoq"],
      internal_extra="Saints won the Prem final 20 Jun - some of these likely returned during the run-in; check final team sheets.",
      user_note="Was reported unavailable due to injury in late April. Northampton went on to win the Premiership final on 20 June, so it's possible some players in this group returned during that run-in, but we don't have a confirmed individual update.")

# Sale
SS = ("Sale Sharks official team news","2026-05-15","https://www.salesharks.com/2026/05/15/team-news-sharks-v-leicester-tigers/")
row("PREM","Sale Sharks","Tom Curry","healthy","2026-01-24","occurred","soft tissue","calf","returned 2026-05-17","high","2026-05-15",SS,
    "Club team news: fit again, first start since Jan - resolved",
    user_note="Recovered from a calf injury and made his first start since January on 15 May.")
row("PREM","Sale Sharks","Raffi Quirke","healthy","2026-04-01","first_reported","soft tissue","hamstring","returned 2026-05-17","high","2026-05-15",SS,
    "Club team news: recovered from hamstring - resolved",
    user_note="Recovered from a hamstring injury in time to start on 15 May.")
stale("PREM","Sale Sharks",["Ben Curry","Bevan Rodd","Luke Cowan-Dickie","Rob du Preez"])

# Saracens
row("PREM","Saracens","(no players identified)","coverage_gap","","","","","","","2026-07-02",
    ("Sweep note","2026-07-02",""),
    "No current injury data captured for Saracens in this sweep despite the club running per-match SQUAD UPDATE posts - fill from saracens.com archive before publishing",
    user_status="", user_note="")
row("PREM","Saracens","Rhys Carre","international_duty","","","","","after Wales window (Jul 18 last Test)","high","2026-06-30",WRU,
    "Named in Wales 33-man squad 30 Jun", user_note=wales_note())
for p in ["Nicky Smith","Tommy Reffell","Olly Cracknell"]:
    row("PREM","Leicester Tigers",p,"international_duty","","","","","after Wales window (Jul 18 last Test)","high","2026-06-30",WRU,
        "Named in Wales 33-man squad 30 Jun", user_note=wales_note())

# ---------------- URC ----------------
# Leinster
for p, bp, d, extra in [("Caelan Doris","foot","2026-06-19"," He'd also been managing a knee issue going into that game."),
                          ("Tommy O'Brien","groin","2026-06-19","")]:
    row("URC","Leinster",p,"injured",d,"occurred","unspecified",bp,"unknown (ruled out of Ireland Jul Tests)","high","2026-06-20",IRFU,
        "Injured in URC final win over Bulls 19 Jun; withdrawn from Ireland tour squad. Doris also carried a knee issue into the final",
        user_note=f"Suffered a {bp} injury early in Leinster's URC final win over the Bulls (19 June) and was withdrawn from Ireland's squad for the summer Tests against Australia, Japan and New Zealand.{extra} No return date confirmed.")
for p in ["Andrew Porter","Ryan Baird","Jack Boyle","Paddy McCarthy"]:
    row("URC","Leinster",p,"injured","2026-06-17","first_reported","unspecified","unspecified","unknown (unavailable for Ireland Jul Tests)","high","2026-06-17",IRFU,
        "Listed as unavailable due to injury in IRFU squad announcement 17 Jun; also on club unavailable list 26 Apr - injury type not disclosed",
        user_note=ireland_injured_note())
stale("URC","Leinster",["Jordan Larmour","Diarmuid Mangan","RG Snyman","Alex Usanov"])
row("URC","Leinster","James Lowe","unavailable_other","2026-04-26","first_reported","","","permanent (international retirement)","high","2026-06-01",
    RP_APR, "Was on Apr club list; has since announced international retirement (not an injury signal) - not a Test player going forward, club status unclear",
    user_note="Was reported unavailable in April, but has since announced his retirement from international rugby - this is a career decision, not an injury. His club availability for Leinster isn't affected by this.")
row("URC","Leinster","Dan Sheehan","international_duty","","","","","after Ireland Jul Tests (Jul 18 last Test)","high","2026-06-20",IRFU,
    "Captains Ireland tour in Doris absence - fit",
    user_note="Fit and captaining Ireland's summer tour to Australia and New Zealand (through 18 July) in Caelan Doris's absence.")

# Munster
row("URC","Munster","Oli Jager","retired_medical","2026-06-20","first_reported","concussion history","head","permanent","high","2026-06-20",
    ("Munster Rugby official / RTE","2026-06-20","https://www.munsterrugby.ie/2026/06/20/oli-jager-to-retire-on-medical-grounds/oli-jager-30-9-2025-2/"),
    "Medically retired with immediate effect after concussion-related issues; remove from active player pool",
    user_note="Announced his retirement from professional rugby on medical grounds on 20 June, following a history of concussions. No longer an active player.")
row("URC","Munster","Roman Salanoa","injured","2026-04-01","first_reported","unspecified","unspecified","unknown","medium","2026-06-21",
    ("Irish Examiner","2026-06-21","https://www.irishexaminer.com/sport/rugby/arid-41866182.html"),
    "Described as continuing to endure injury torment - long-term absentee, exact injury and return not disclosed",
    user_status="Potential Injury",
    user_note="Described as having continued to struggle with injury through the 2025-26 season, but the specific issue and an expected return date haven't been reported.")
for p in ["Jack Crowley","Edwin Edogbo","Tom Farrell","Calvin Nash"]:
    row("URC","Munster",p,"injured","2026-06-17","first_reported","unspecified","unspecified","unknown (unavailable for Ireland Jul Tests)","high","2026-06-17",IRFU,
        "Listed as unavailable due to injury in IRFU squad announcement 17 Jun - injury type not disclosed",
        user_note=ireland_injured_note())
row("URC","Munster","John Ryan","unavailable_other","2026-06-21","first_reported","","","permanent (retiring)","high","2026-06-21",
    ("Irish Examiner","2026-06-21","https://www.irishexaminer.com/sport/rugby/arid-41866182.html"),"Retiring after 16 years (age, not medical)",
    user_note="Retiring from professional rugby after 16 years at Munster. This is a career decision, not an injury.")

# Ulster
row("URC","Ulster","Bryn Ward","international_duty","","","","","after Ireland Jul Tests (Jul 18 last Test)","high","2026-06-20",IRFU,
    "Was on Apr unavailable list but called up to Ireland tour 20 Jun - fit; resolves Apr entry",
    user_note="Was reported unavailable in April, but has since recovered and been called into Ireland's squad for the summer tour as an uncapped player in contention for a debut.")
row("URC","Ulster","Zac Ward","international_duty","","","","","after Ireland Jul Tests (Jul 18 last Test)","high","2026-06-20",IRFU,
    "Called up to Ireland tour 20 Jun",
    user_note="Called into Ireland's squad for the summer tour (through 18 July) as an uncapped player in contention for a debut.")
stale("URC","Ulster",["Angus Bell","Scott Wilson","Tom O'Toole","James Hume","Jude Postlethwaite","Nick Timoney","James McNabney","Rob Herring","Robert Baloucoune","Rory McGuire","Stewart Moore"])

# Connacht
for p in ["Mack Hansen","Shayne Bolton"]:
    row("URC","Connacht",p,"injured","2026-06-17","first_reported","unspecified","unspecified","unknown (unavailable for Ireland Jul Tests)","high","2026-06-17",IRFU,
        "Listed as unavailable due to injury in IRFU squad announcement 17 Jun (Hansen also on club Apr list)",
        user_note=ireland_injured_note())
stale("URC","Connacht",["Josh Ioane","Oisin McCormack","Temi Lasisi","Oisin Dowling","Caolin Blade","David Hawkshaw","Byron Ralston","Finn Treacy"])

# Glasgow
row("URC","Glasgow Warriors","George Horne","unknown_potentially_injured","2026-06-06","occurred","unspecified","unspecified","unknown","medium","2026-06-06",
    ("Planet Rugby","2026-06-06","https://www.planetrugby.com/news/glasgow-warriors-suffer-critical-injury-blow-ahead-of-urc-semi-final-as-scotland-international-ruled-out"),
    "Failed late fitness test hours before URC semi-final - severity undisclosed; check Scotland squad involvement to resolve",
    user_note="Failed a late fitness test hours before Glasgow's URC semi-final (6 June) and was withdrawn from the starting line-up. The nature and severity of the issue weren't disclosed.")
row("URC","Glasgow Warriors","Huw Jones","injured","2026-04-25","occurred","unspecified","foot","unknown","medium","2026-05-21",
    ("The Scotsman (Glasgow media session)","2026-05-21","https://www.scotsman.com/sport/rugby-union/glasgow-warriors-injury-update-as-scotland-duo-back-in-the-mix-for-urc-quarter-final-8639954"),
    "Foot injury, last played 25 Apr; had not returned to training by late May, season-end return was in doubt",
    user_note="Has a foot injury and, as of late May, hadn't returned to training. His return before the end of the season was in doubt at that point.")
row("URC","Glasgow Warriors","Gregor Brown","unknown_potentially_injured","2026-03-07","occurred","soft tissue","hamstring then calf","unknown","medium","2026-05-21",
    ("The Scotsman (Glasgow media session)","2026-05-21","https://www.scotsman.com/sport/rugby-union/glasgow-warriors-injury-update-as-scotland-duo-back-in-the-mix-for-urc-quarter-final-8639954"),
    "Hamstring injury in Six Nations; lasted 14 min on comeback vs Ulster after tweaking calf - final status unresolved",
    user_note="Returned from a hamstring injury in May but only lasted 14 minutes before feeling his calf. His status since hasn't been confirmed.")
row("URC","Glasgow Warriors","Jamie Dobie","healthy","2026-02-14","occurred","surgery","shoulder","returned 2026-06-06","high","2026-06-06",
    ("The Scotsman","2026-06-06","https://www.scotsman.com/sport/rugby-union/glasgow-warriors-injury-news-rugby-bulls-urc-semi-final-george-horne-jamie-dobbie-8661659"),
    "Shoulder surgery after Calcutta Cup; started URC semi-final - resolved",
    user_note="Had shoulder surgery after the Calcutta Cup in February, but returned to start Glasgow's URC semi-final on 6 June.")
row("URC","Glasgow Warriors","Scott Cummings","healthy","2026-03-07","occurred","soft tissue","calf","returned by 2026-06-06","high","2026-06-06",
    ("Planet Rugby semi-final team news","2026-06-06","https://www.planetrugby.com/news/glasgow-warriors-suffer-critical-injury-blow-ahead-of-urc-semi-final-as-scotland-international-ruled-out"),
    "Calf injury in Six Nations; started URC semi-final - resolved",
    user_note="Missed several months with a calf injury from the Six Nations, but returned to start Glasgow's URC semi-final.")
row("URC","Glasgow Warriors","Kyle Steyn","healthy","2026-03-14","occurred","fracture","foot (stress fracture)","returned by 2026-05-08","high","2026-06-06",
    ("RugbyPass / semi-final team sheet","2026-06-06","https://www.rugbypass.com/news/urc-leaders-glasgow-dealt-major-setback-with-damaging-injury-list-from-six-nations/"),
    "Foot stress fracture from Six Nations; captained side in May/June - resolved",
    user_note="Played through a foot stress fracture and captained Glasgow through the URC play-offs in May and June.")
for p in ["Gregor Hiddleston","Seb Stephen"]:
    row("URC","Glasgow Warriors",p,"international_duty","","","","","after Scotland Jul window","high","2026-06-09",
        ("Glasgow Warriors official","2026-06-09","https://glasgowwarriors.org/news-and-features/"),
        "Among 19 Glasgow players in Scotland Nations Championship squad (9 Jun); full 19-name list not yet ingested - gap",
        user_note=scotland_note("Uncapped and in contention for a Test debut."))

# Edinburgh (Apr list)
stale("URC","Edinburgh Rugby",["Charlie McCaig","Rhys Litterick","Rob Carmichael","Luke Crosbie","Sam Skinner","Paddy Harrison","Conor McAlpine","Wes Goosen","Duhan van der Merwe","Harry Paterson","Magnus Bradbury","Matt Currie","Mikey Jones","Ben Muncaster","James Lang","D'arcy Rae","Liam McConnell","Connor Boyle","Ben Vellacott"],
      internal_extra="19 unavailable in Apr - second-worst in URC.")
row("URC","Edinburgh Rugby","Hamish Watson","healthy","2026-01-01","first_reported","unspecified","unspecified","returned 2026-05-17 (on loan at Leicester)","medium","2026-05-18",
    ("The Scotsman","2026-05-18","https://www.scotsman.com/sport/rugby-union/leicester-tigers-gallagher-premiership-hamish-watson-sale-sharks-edinburgh-scottish-rugby-play-offs-8550854"),
    "Returned from injury for loan club Leicester in May; contracted to Edinburgh - confirm 2026-27 club",
    user_note="Recovered from injury and made appearances on loan at Leicester Tigers in May. He remains contracted to Edinburgh, but his club for 2026-27 should be confirmed.")

# Cardiff
row("URC","Cardiff Rugby","(no players identified)","coverage_gap","","","","","","","2026-07-02",("Sweep note","2026-07-02",""),
    "No current injury data captured for Cardiff this sweep - fill via WalesOnline archive before publishing",
    user_status="", user_note="")
for p in ["Josh Adams","Ben Thomas","James Botham","Mason Grady","Evan Lloyd","Alex Mann","Keiron Assiratti","Seb Wainwright","Teddy Williams"]:
    row("URC","Cardiff Rugby",p,"international_duty","","","","","after Wales window (Jul 18 last Test)","high","2026-06-30",WRU,
        "Named in Wales 33-man squad 30 Jun - fit", user_note=wales_note())

# Dragons
row("URC","Dragons RFC","(no players identified)","coverage_gap","","","","","","","2026-07-02",("Sweep note","2026-07-02",""),
    "No current injury data captured for Dragons this sweep - fill via WalesOnline/South Wales Argus before publishing",
    user_status="", user_note="")
for p, extra in [("Ben Carter",""),("Dillon Lewis",""),("Aaron Wainwright","He's reported to be transferring to Leicester Tigers for the 2026-27 season.")]:
    row("URC","Dragons RFC",p,"international_duty","","","","","after Wales window (Jul 18 last Test)","high","2026-06-30",WRU,
        ("Named in Wales 33-man squad 30 Jun - fit. "+extra).strip(), user_note=wales_note(extra))

# Ospreys
for p, extra in [("Dewi Lake","He's captaining Wales for this window."),("Gareth Thomas",""),
                  ("Jac Morgan","He's reported to be leaving Ospreys this summer."),("Ben Warren",""),
                  ("Dan Edwards",""),("Kieran Hardy",""),("Reuben Morgan-Williams","")]:
    row("URC","Ospreys",p,"international_duty","","","","","after Wales window (Jul 18 last Test)","high","2026-06-30",WRU,
        ("Named in Wales 33-man squad 30 Jun - fit. "+extra).strip(), user_note=wales_note(extra))

# Scarlets
for p in ["Ellis Mee","Sam Costelow"]:
    row("URC","Scarlets",p,"international_duty","","","","","after Wales window (Jul 18 last Test)","high","2026-06-30",WRU,
        "Was on club unavailable list 26 Apr but named in Wales 33-man squad 30 Jun - injury resolved",
        user_note="Was reported unavailable due to injury in late April, but has since recovered and been named in Wales's squad for the summer internationals.")
for p in ["Ryan Elias","Taine Plumtree","Eddie James","Joe Hawkins","Blair Murray"]:
    row("URC","Scarlets",p,"international_duty","","","","","after Wales window (Jul 18 last Test)","high","2026-06-30",WRU,
        "Named in Wales 33-man squad 30 Jun - fit", user_note=wales_note())
stale("URC","Scarlets",["Tom Rogers","Archer Holz","Josh Macleod","Jake Ball","Alec Hepburn","Will Evans","Dom Kossuth"])

# Benetton
row("URC","Benetton Rugby","Simone Ferrari","injured","2026-03-14","occurred","surgery (cervical spine stabilisation)","neck","unknown","high","2026-03-24",
    ("Rugbymeet / Benetton medical bulletin","2026-03-24","https://www.rugbymeet.com/news/111603518982/benetton-rugby-perde-due-piloni-per-infortunio-nel-6-nazioni"),
    "Neck injury in Six Nations vs England; cervical stabilisation surgery 19 Mar - serious, availability for 2026-27 must be re-verified",
    user_note="Suffered a neck injury playing for Italy in the Six Nations in March and underwent surgery to stabilise his cervical spine. This is a serious injury, and his availability for the 2026-27 season needs confirming.")
row("URC","Benetton Rugby","Mirco Spagnolo","healthy","2026-03-07","occurred","muscle lesion","calf (right medial gastrocnemius)","returned (featured in late-season URC match)","medium","2026-05-01",
    ("Benetton medical bulletin + match data","2026-05-01","https://www.rugbymeet.com/news/111603518982/benetton-rugby-perde-due-piloni-per-infortunio-nel-6-nazioni"),
    "One-month calf lesion from Six Nations; appeared in subsequent URC fixture - resolved",
    user_note="Had a calf injury from the Six Nations in March expected to last about a month, and returned to action for Benetton before the end of the season.")

# Zebre
row("URC","Zebre Parma","(no players identified)","coverage_gap","","","","","","","2026-07-02",("Sweep note","2026-07-02",""),
    "No injury data captured for Zebre this sweep - weakest coverage in the league; fill via OnRugby.it before publishing",
    user_status="", user_note="")

# Sharks
row("URC","Hollywoodbets Sharks","Siya Kolisi","healthy","2026-02-15","first_reported","soft tissue","calf","returned 2026-04-24","high","2026-04-23",
    ("RugbyPass","2026-04-23","https://www.rugbypass.com/news/siya-kolisi-makes-timely-return-as-sharks-reel-from-catastrophic-injury-list/"),
    "Returned to matchday squad vs Edinburgh 24 Apr after calf injury - resolved",
    user_note="Recovered from a calf injury and returned to the matchday squad on 24 April.")
stale("URC","Hollywoodbets Sharks",["Aphelele Fassi","Bongi Mbonambi","Bryce Calvert","Coetzee le Roux","Eben Etzebeth","Ethan Bester","Ethan Hooker","Francois Venter","Grant Williams","Hakeem Kunene","Jaco Williams","Jordan Hendrikse","Jurenzo Julius","Le Roux Malan","Luan Giliomee","Marvin Orie","Matt Romao","Ruan Dreyer","Simphiwe Matanzima","Tom Dyer","Trevor Nyakane","Yaw Penxe"],
      internal_extra="Worst list in either league in Apr (22 out). Several are Springboks and may since have entered the national squad - cross-check Bok 51-man list.",
      user_note="Was reported unavailable due to injury in late April 2026. No specific injury details were given and there's been no update since. Some Sharks players are Springboks who may since have been called into South Africa's squad for the July internationals, though we haven't been able to confirm each individually.")

# Stormers
SRM = ("SA Rugby magazine (semi-final team news)","2026-06-05","https://www.sarugbymag.co.za/injury-hit-stormers-suffer-another-blow/")
row("URC","DHL Stormers","Sacha Feinberg-Mngomezulu","injured","2026-05-30","first_reported","unspecified","ankle","unknown","high","2026-06-05",SRM,
    "Ruled out of URC semi-final vs Leinster with ankle injury; Springbok involvement in July window unconfirmed",
    user_note="Ruled out of the Stormers' URC semi-final (30 May) with an ankle injury. No return date has been confirmed, and it's unclear whether he'll be available for the Springboks' July internationals.")
row("URC","DHL Stormers","Seabelo Senatla","unknown_potentially_injured","2026-05-30","first_reported","concussion/HIA","head","estimated mid-Jun (12-day protocol) - unverified","medium","2026-06-05",SRM,
    "Concussion ruled him out of semi-final; standard return-to-play window has since elapsed but return not confirmed",
    user_note="Missed the URC semi-final with concussion. The standard return-to-play window has likely passed by now, but his actual return hasn't been confirmed.")
row("URC","DHL Stormers","Ruben van Heerden","unknown_potentially_injured","2026-06-01","occurred","concussion/HIA","head","estimated mid-Jun (12-day protocol) - unverified","medium","2026-06-05",SRM,
    "Failed to recover from head knock before semi-final; return not confirmed",
    user_note="Failed to recover from a head knock in time for the URC semi-final in early June. His return hasn't yet been confirmed.")
row("URC","DHL Stormers","Damian Willemse","healthy","2026-05-15","first_reported","soft tissue","hamstring","returned by 2026-06-06 (started semi-final)","high","2026-06-05",SRM,
    "Named at 15 in semi-final XV after hamstring layoff - resolved",
    user_note="Missed time with a hamstring injury but returned to start the Stormers' URC semi-final.")

# Bulls
row("URC","Vodacom Bulls","Sebastian de Klerk","unknown_potentially_injured","2026-03-14","occurred","fracture (suspected, repeat injury)","foot","unknown","medium","2026-03-15",
    ("Rugby365 (Ackermann press conf)","2026-03-15","https://rugby365.com/tournaments/united-rugby-championship/bulls-count-injury-toll-after-stormers-defeat/"),
    "Suspected broken bone in foot (repeat of previous fracture) in Mar; not seen in Jun semi-final team sheet - status unresolved",
    user_status="Potential Injury",
    user_note="Suspected a repeat foot fracture in March and hasn't appeared in a reported matchday squad since. It's unclear whether he's still sidelined or simply been out of the selection picture for other reasons.")
row("URC","Vodacom Bulls","Harold Vorster","healthy","2026-03-14","occurred","concussion/HIA","head","returned (started URC semi-final 6 Jun)","high","2026-06-06",
    ("Planet Rugby semi-final team sheet","2026-06-06","https://www.planetrugby.com/news/glasgow-warriors-suffer-critical-injury-blow-ahead-of-urc-semi-final-as-scotland-international-ruled-out"),
    "Failed HIA in March; started semi-final vs Glasgow - resolved",
    user_note="Failed a concussion test in March but returned to start the URC semi-final in June.")

# Lions
row("URC","Emirates Lions","Conraad van Vuuren","healthy","2026-02-28","occurred","suspension (served)","","ban completed (4 matches from early Mar)","high","2026-03-07",
    ("Kickoff.com / URC disciplinary","2026-03-07","https://www.kickoff.com/rugby/urc/lions-prop-conraad-van-vuuren-banned-4-matches-after-red-card-in-urc"),
    "4-match ban (red card vs Stormers) fully served during 2025-26 - no carryover",
    user_note="Served a four-match suspension for a red card earlier in the season. The ban is fully complete, with nothing carrying over.")
row("URC","Emirates Lions","(no players identified)","coverage_gap","","","","","","","2026-07-02",("Sweep note","2026-07-02",""),
    "No current injury data captured for Lions this sweep - fill via Rugby365/SA Rugby magazine before publishing",
    user_status="", user_note="")

# Cross-league notes
row("BOTH","(league-wide)","(suspensions)","review_item","","","","","","","2026-07-02",
    ("URC news index","2026-06-12","https://www.unitedrugby.com/latest/"),
    "URC posted a Disciplinary Press Release dated 12 Jun 2026 whose content was not reviewed in this sweep - check for any ban carrying into 2026-27. No active carryover suspensions otherwise identified in either league",
    user_status="", user_note="")
row("BOTH","(league-wide)","(international squads)","review_item","","","","","","","2026-07-02",
    ("Sweep note","2026-07-02",""),
    "Full England, Scotland (19 Glasgow players), Ireland (36-man), Springbok (51-man) and Italy squads not yet ingested - Wales 33 and named Irish call-ups only. July window ends before 2026-27 club season so fantasy impact is nil, but ingest for completeness",
    user_status="", user_note="")

df = pd.DataFrame(R)
cols = ["competition","team","player_name","user_status","user_notes","expected_return","injury_date",
        "injury_type","body_part","confidence","last_verified","internal_status","source_name","source_date",
        "source_url","internal_notes"]
df = df[cols]
df.to_csv("/home/claude/rugby/player_availability_first_sweep.csv", index=False)
print(len(df), "rows")
print(df.groupby("user_status").size().to_string())
