import pandas as pd

# audit_status: verified = checked in this sweep; provisional = based on known landscape, to verify in phase 1 completion
rows = [
# PREM
("PREM","Bath","Official injury update articles (Head of Medical) posted irregularly under club news; no maintained page (the /content/injury-updates page is a dead 8-year-old stub)","https://www.bathrugby.com/news","Bath Chronicle / Somerset Live; RugbyPass Bath feed","partial","verified","Club posts pre-season and in-season medical updates as news articles; monitor news feed not the stub page"),
("PREM","Bristol Bears","Club news; injuries mainly via Pat Lam press conferences","https://www.bristolbearsrugby.com/news/","Bristol Post / BristolLive; RugbyPass","no","provisional","Lam gives detailed injury info in pressers; April 2026 RugbyPass audit listed 17 unavailable"),
("PREM","Exeter Chiefs","Club news; injuries via Rob Baxter press conferences","https://www.exeterchiefs.co.uk/news","DevonLive; Yahoo/PA syndication; RugbyPass","no","verified","Baxter pressers reliably transcribed by DevonLive; confirmed season-enders named in June coverage"),
("PREM","Gloucester","Club news; injuries via press conferences","https://www.gloucesterrugby.co.uk/news","Gloucestershire Live (dedicated beat reporter)","no","provisional","Gloucestershire Live is the strongest single Prem beat source"),
("PREM","Harlequins","Club news; occasional injury statements","https://www.quins.co.uk/news/","Standard/talkSPORT; RugbyPass","no","provisional","Worst-affected club in Apr 2026 (26 unavailable); club rarely publishes structured lists"),
("PREM","Leicester Tigers","Official 'Injury Update: <player>' articles per significant injury","https://www.leicestertigers.com/news","Leicester Mercury; RugbyPass","partial","verified","Club posts named injury updates (e.g. Steward 21 May 2026) and TEAM NEWS return notes - good Tier 1"),
("PREM","Newcastle Red Bulls","Club news","https://www.newcastle-redbulls.co.uk/","Chronicle Live (dedicated beat reporter)","no","provisional","Chronicle Live is primary source; 16 unavailable in Apr 2026 audit"),
("PREM","Northampton Saints","Club news; injuries via Phil Dowson pressers","https://www.northamptonsaints.co.uk/news","Northampton Chronicle & Echo; BBC Northampton","no","provisional","12 unavailable in Apr 2026 audit"),
("PREM","Sale Sharks","Official TEAM NEWS articles note injury returns with body part","https://www.salesharks.com/news/","Manchester Evening News; RugbyPass","partial","verified","Team news articles state returns explicitly (e.g. Curry calf / Quirke hamstring, 15 May 2026)"),
("PREM","Saracens","Official 'SQUAD UPDATE' player availability articles per match","https://saracens.com/news/","Standard; RugbyPass","yes","verified","Best structured Tier 1 in the Prem: per-match squad updates listing each injury with body part; no June 2026 update captured in this sweep - gap to fill"),
# URC - Ireland
("URC","Leinster","Weekly official squad updates in-season; IRFU squad announcements fill gaps","https://www.leinsterrugby.ie/news/","The42; Irish Times; Irish Independent; RTE","yes","verified","IRFU 17-20 Jun 2026 announcements confirmed 8 Leinster players out injured - Irish provinces have the best injury transparency"),
("URC","Munster","Weekly official squad updates in-season","https://www.munsterrugby.ie/news/","Irish Examiner; The42; RTE","yes","verified","Club statements (e.g. Jager medical retirement 20 Jun) plus IRFU announcements"),
("URC","Ulster","Weekly official squad updates in-season","https://www.ulster.rugby/news","Belfast Telegraph; BBC Sport NI; The42","yes","provisional","12 unavailable in Apr 2026 audit"),
("URC","Connacht","Weekly official squad updates in-season","https://www.connachtrugby.ie/news/","Connacht Tribune; The42; RTE","yes","provisional","Hansen and Bolton confirmed injured via IRFU 17 Jun"),
# URC - Scotland
("URC","Glasgow Warriors","Official 'Squad Update' articles; injuries also via Franco Smith pressers","https://glasgowwarriors.org/news-and-features/","The Scotsman (dedicated); The Herald; Scotland Rugby News","partial","verified","Scotsman carries detailed weekly injury updates from assistant-coach media sessions"),
("URC","Edinburgh Rugby","Club news; injuries via Sean Everitt pressers","https://www.edinburghrugby.org/news","The Scotsman; Edinburgh Evening News; The Offside Line","no","provisional","19 unavailable in Apr 2026 audit; club publishes little - beat press essential"),
# URC - Wales
("URC","Cardiff Rugby","Club news","https://www.cardiffrugby.wales/news/","WalesOnline (covers all four regions)","no","provisional","WalesOnline is the single indispensable Welsh source"),
("URC","Dragons RFC","Club news","https://dragonsrugby.wales/news/","WalesOnline; South Wales Argus","no","provisional","No injury data captured this sweep - gap"),
("URC","Ospreys","Club news","https://www.ospreysrugby.com/news","WalesOnline; South Wales Evening Post","no","verified","Club posts Wales squad news; injury info via pressers"),
("URC","Scarlets","Club news","https://scarlets.wales/news/","WalesOnline; Llanelli Star","no","provisional","9 unavailable in Apr 2026 audit; Mee and Costelow since confirmed fit via Wales squad"),
# URC - Italy
("URC","Benetton Rugby","Official 'INFORTUNIO <player>' medical bulletins with diagnosis detail","https://benettonrugby.it/news/","OnRugby.it; Rugbymeet","yes","verified","Publishes named medical bulletins incl. surgery details (e.g. Ferrari cervical surgery Mar 2026) - strong Tier 1, Italian language"),
("URC","Zebre Parma","Club news","https://zebreparma.it/","OnRugby.it; Gazzetta dello Sport","no","provisional","No injury data captured this sweep - weakest coverage in URC alongside Dragons - gap"),
# URC - South Africa
("URC","Vodacom Bulls","Injuries via Johan Ackermann pressers; occasional club updates","https://bullsrugby.co.za/","Rugby365; SA Rugby magazine; Netwerk24 (paywalled Afrikaans)","no","verified","Ackermann discloses HIA/injury detail in post-match pressers carried by Rugby365"),
("URC","DHL Stormers","Occasional official injury updates (historically detailed); pressers via John Dobson","https://thestormers.com/","SA Rugby magazine; Rugby365; Daily Maverick","partial","verified","SA Rugby mag carries named injury changes per team announcement"),
("URC","Hollywoodbets Sharks","Club news; injuries mostly inferred","https://sharksrugby.co.za/","Rugby365; SA Rugby magazine; IOL","no","provisional","Worst URC injury list in Apr 2026 (22 players); club publishes little - team-sheet inference critical"),
("URC","Emirates Lions","Club news; pressers","https://lionsrugbyco.co.za/","Rugby365; SA Rugby magazine; Kickoff","no","provisional","No current injury data captured - gap; suspensions well covered by URC disciplinary releases"),
# Cross-cutting
("BOTH","(All clubs) Suspensions","URC Disciplinary Press Releases; RFU disciplinary decisions page; EPCR judicial notices","https://www.unitedrugby.com/latest/ and https://www.englandrugby.com/run/rules-governance/discipline/disciplinary-decisions","Planet Rugby / RugbyPass disciplinary reports","yes","verified","Only centrally standardised availability data in rugby; URC posted a Disciplinary Press Release 12 Jun 2026 - content not yet reviewed"),
("BOTH","(All clubs) International duty","Official national squad announcements: IRFU, WRU, SRU, RFU, FIR, SA Rugby","national union websites","RugbyPass; Planet Rugby","yes","verified","Wales 33-man (30 Jun) and Ireland tour changes (17-20 Jun) captured; England / full Scotland / Springbok 51-man / Italy squads not yet ingested - gap"),
("BOTH","(All clubs) Team sheets","League match centres publish matchday 23s ~24-48h pre-kickoff","https://www.premiershiprugby.com/ and https://www.unitedrugby.com/","RugbyPass live match pages","yes","verified","Primary inference source for unexplained absences once 2026-27 season starts"),
]

cols = ["competition","team","tier1_official_source","tier1_url","tier2_beat_outlets","publishes_structured_injury_info","audit_status","notes"]
pd.DataFrame(rows, columns=cols).to_csv("/home/claude/rugby/club_injury_sources.csv", index=False)
print("sources csv written:", len(rows), "rows")
