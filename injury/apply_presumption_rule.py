import pandas as pd
from pathlib import Path

HERE = Path(__file__).resolve().parent
CSV_PATH = HERE / "player_availability.csv"

df = pd.read_csv(CSV_PATH)

qualifies = ((df.internal_status == "unknown_potentially_injured") &
             (df.source_name == "RugbyPass injury-list audit") &
             (df.injury_type == "unspecified"))

BASE = ("Was reported unavailable due to injury in late April 2026, with no specific details given about what "
        "the injury was. Since the season has since finished with no further update, and nothing on record "
        "suggested a long-term issue, they're presumed to have recovered by now under our default assumption "
        "for undetailed, non-serious reports - but this hasn't been individually confirmed, so treat it as a "
        "reasonable working assumption rather than a certainty. Best checked against recent squad appearances.")

SUFFIX = {
    ("Northampton Saints",): " Northampton went on to win the Premiership final on 20 June, so some of this group may well have featured in that run-in.",
    ("Hollywoodbets Sharks",): " Several Sharks players in this group are Springboks, so it's also worth checking South Africa's July squad announcement for confirmation of fitness.",
}
PLAYER_SUFFIX = {
    "Stephan Lewies": " He's also been reported as joining the Sharks in South Africa for 2026-27, so double-check which club any future appearance is actually for.",
}

df.loc[qualifies, "user_status"] = "Likely Healthy (Unconfirmed)"

def build_note(row):
    if not qualifies.loc[row.name]:
        return row.user_notes
    note = BASE
    for teams, suf in SUFFIX.items():
        if row.team in teams:
            note += suf
    if row.player_name in PLAYER_SUFFIX:
        note += PLAYER_SUFFIX[row.player_name]
    return note

df["user_notes"] = df.apply(build_note, axis=1)
df["presumption_rule_applied"] = qualifies.map({True: "yes", False: "no"})

cols = ["competition","team","player_name","user_status","user_notes","expected_return","injury_date",
        "injury_type","body_part","confidence","last_verified","internal_status","presumption_rule_applied",
        "source_name","source_date","source_url","internal_notes"]
df = df[cols]
df.to_csv(CSV_PATH, index=False)

print(df.groupby("user_status").size().to_string())
print("\npresumption applied:", (df.presumption_rule_applied=="yes").sum())
