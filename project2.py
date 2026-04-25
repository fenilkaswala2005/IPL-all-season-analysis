import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

# =========================
# CHANGEABLE LABELS
# =========================
APP_TITLE = "🏏 Indian Premier League Dashboard (2008–2025)"


st.set_page_config(page_title="IPL Dashboard", page_icon="🏏", layout="wide")

TEAM_ALIASES = {
    "Rising Pune Supergiant": "RPS",
    "Rising Pune Supergiants": "RPS",
    "Pune Warriors": "PW",
    "Deccan Chargers": "DCG",
    "Delhi Daredevils": "DD",
    "Delhi Capitals": "DC",
    "Kings XI Punjab": "KXIP",
    "Punjab Kings": "PBKS",
    "Gujarat Lions": "GL",
    "Lucknow Super Giants": "LSG",
    "Royal Challengers Bangalore": "RCB",
    "Royal Challengers Bengaluru": "RCB",
    "Sunrisers Hyderabad": "SRH",
    "Chennai Super Kings": "CSK",
    "Mumbai Indians": "MI",
    "Kolkata Knight Riders": "KKR",
    "Rajasthan Royals": "RR",
    "Gujarat Titans": "GT",
    "Kochi Tuskers Kerala": "KTK",
}

MONTH_ORDER = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

def canonical(text):
    return str(text).strip().lower().replace("_", " ").replace("-", " ")

def find_col(df, options):
    canon_map = {canonical(col): col for col in df.columns}
    for opt in options:
        if canonical(opt) in canon_map:
            return canon_map[canonical(opt)]
    for col in df.columns:
        c = canonical(col)
        for opt in options:
            if canonical(opt) in c:
                return col
    return None

def team_short(name):
    if pd.isna(name):
        return name
    name = str(name).strip()
    return TEAM_ALIASES.get(name, name)

@st.cache_data(show_spinner=False)
def load_data():
    df = pd.read_csv("ipl.csv")
    df.columns = [c.strip() for c in df.columns]

    col_date = find_col(df, ["date", "match_date", "start_date"])
    col_season = find_col(df, ["season", "year"])
    col_team1 = find_col(df, ["team1", "team 1", "home_team"])
    col_team2 = find_col(df, ["team2", "team 2", "away_team"])
    col_winner = find_col(df, ["winner", "winning_team"])
    col_toss_winner = find_col(df, ["toss_winner", "toss winner"])
    col_toss_decision = find_col(df, ["toss_decision", "toss decision"])
    col_venue = find_col(df, ["venue", "ground"])
    col_city = find_col(df, ["city", "host_city"])
    col_player = find_col(df, ["player_of_match", "player of match", "pom"])
    col_margin_runs = find_col(df, ["win_by_runs", "runs_margin", "margin_runs"])
    col_margin_wkts = find_col(df, ["win_by_wickets", "wickets_margin", "margin_wickets"])
    col_result = find_col(df, ["result", "result_type", "outcome"])

    if col_date:
        df[col_date] = pd.to_datetime(df[col_date], errors="coerce")
        df["match_date"] = df[col_date]
        df["year"] = df[col_date].dt.year
        df["month"] = df[col_date].dt.month_name().str[:3]
    elif col_season:
        df["year"] = pd.to_numeric(df[col_season], errors="coerce")
        df["match_date"] = pd.NaT
        df["month"] = None
    else:
        st.error("Date or season column not found in CSV.")
        st.stop()

    if col_team1 is None or col_team2 is None:
        st.error("team1/team2 columns not found in CSV.")
        st.stop()

    df["team1_clean"] = df[col_team1].map(team_short)
    df["team2_clean"] = df[col_team2].map(team_short)
    df["winner_clean"] = df[col_winner].map(team_short) if col_winner else np.nan
    df["toss_winner_clean"] = df[col_toss_winner].map(team_short) if col_toss_winner else np.nan
    df["venue_clean"] = df[col_venue].fillna("Unknown") if col_venue else "Unknown"
    df["city_clean"] = df[col_city].fillna("Unknown") if col_city else "Unknown"
    df["player_of_match_clean"] = df[col_player].fillna("Unknown") if col_player else "Unknown"
    df["toss_decision_clean"] = df[col_toss_decision].fillna("Unknown") if col_toss_decision else "Unknown"
    df["result_clean"] = df[col_result].fillna("Completed") if col_result else "Completed"
    df["win_by_runs_clean"] = pd.to_numeric(df[col_margin_runs], errors="coerce").fillna(0) if col_margin_runs else 0
    df["win_by_wickets_clean"] = pd.to_numeric(df[col_margin_wkts], errors="coerce").fillna(0) if col_margin_wkts else 0

    return df

def matches_played_by_team(filtered_df):
    all_teams = pd.concat([
        filtered_df["team1_clean"].rename("team"),
        filtered_df["team2_clean"].rename("team")
    ])
    return all_teams.value_counts().rename_axis("team").reset_index(name="matches")

def wins_by_team(filtered_df):
    valid = filtered_df[
        filtered_df["winner_clean"].notna() &
        (filtered_df["winner_clean"] != "")
    ]
    return valid["winner_clean"].value_counts().rename_axis("team").reset_index(name="wins")

def team_summary(filtered_df):
    played = matches_played_by_team(filtered_df)
    wins = wins_by_team(filtered_df)
    summary = played.merge(wins, how="left", on="team").fillna({"wins": 0})
    summary["wins"] = summary["wins"].astype(int)
    summary["losses"] = summary["matches"] - summary["wins"]
    summary["win_pct"] = (summary["wins"] / summary["matches"]) * 100
    return summary.sort_values(["wins", "win_pct"], ascending=[False, False])

try:
    df = load_data()
except FileNotFoundError:
    st.error("ipl.csv file not found. Keep ipl.csv in the same folder as app.py")
    st.stop()

# =========================
# HEADER
# =========================
st.title(APP_TITLE)




# =========================
# FILTERS
# =========================
all_years = sorted([int(y) for y in pd.Series(df["year"]).dropna().unique()])
all_teams = sorted(set(pd.concat([df["team1_clean"], df["team2_clean"]]).dropna().unique()))
all_venues = sorted(df["venue_clean"].dropna().unique().tolist())

st.sidebar.header("Filters")
selected_years = st.sidebar.multiselect("Season", all_years, default=all_years)
selected_teams = st.sidebar.multiselect("Team", all_teams, default=[])
selected_venues = st.sidebar.multiselect("Venue", all_venues, default=[])
selected_toss = st.sidebar.multiselect(
    "Toss Decision",
    sorted(df["toss_decision_clean"].dropna().unique().tolist()),
    default=[]
)

filtered = df.copy()

if selected_years:
    filtered = filtered[filtered["year"].isin(selected_years)]

if selected_teams:
    filtered = filtered[
        (filtered["team1_clean"].isin(selected_teams)) |
        (filtered["team2_clean"].isin(selected_teams))
    ]

if selected_venues:
    filtered = filtered[filtered["venue_clean"].isin(selected_venues)]

if selected_toss:
    filtered = filtered[filtered["toss_decision_clean"].isin(selected_toss)]

if filtered.empty:
    st.warning("No records found for selected filters.")
    st.stop()

team_stats = team_summary(filtered)
completed_matches = filtered[
    filtered["winner_clean"].notna() &
    (filtered["winner_clean"] != "")
]

# =========================
# METRICS
# =========================
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Matches", len(filtered))
col2.metric("Seasons", filtered["year"].nunique())
col3.metric("Teams", len(set(pd.concat([filtered["team1_clean"], filtered["team2_clean"]]).dropna().unique())))
col4.metric("Venues", filtered["venue_clean"].nunique())

col5, col6, col7, col8 = st.columns(4)
col5.metric("Completed Matches", len(completed_matches))
col6.metric("Tied / NR / Other", len(filtered) - len(completed_matches))
col7.metric("Top Winner", team_stats.iloc[0]["team"])
col8.metric("Best Win %", f"{team_stats['win_pct'].max():.1f}%")

st.markdown("---")

# =========================
# CHARTS
# =========================
year_counts = filtered.groupby("year").size().reset_index(name="matches")
fig_year = px.bar(year_counts, x="year", y="matches", text="matches",
                  title="Matches by Season")
st.plotly_chart(fig_year, use_container_width=True)

left, right = st.columns(2)

with left:
    fig_wins = px.bar(team_stats.head(10), x="team", y="wins", text="wins",
                      title="Top 10 Teams by Wins")
    st.plotly_chart(fig_wins, use_container_width=True)

with right:
    venue_counts = filtered["venue_clean"].value_counts().head(10).rename_axis("venue").reset_index(name="matches")
    fig_venues = px.bar(venue_counts, x="matches", y="venue", orientation="h",
                         text="matches", title="Top 10 Venues by Match Count")
    st.plotly_chart(fig_venues, use_container_width=True)

left, right = st.columns(2)

with left:
    toss_counts = filtered["toss_decision_clean"].value_counts().rename_axis("decision").reset_index(name="count")
    fig_toss = px.pie(toss_counts, names="decision", values="count",
                      title="Toss Decision Distribution")
    st.plotly_chart(fig_toss, use_container_width=True)

with right:
    pom = filtered["player_of_match_clean"].replace("Unknown", np.nan).dropna().value_counts().head(10)

    if len(pom) > 0:
        fig_pom = px.bar(
            pom.rename_axis("player").reset_index(name="awards"),
            x="awards",
            y="player",
            orientation="h",
            text="awards",
            title="Top 10 Player of the Match Winners"
        )
        st.plotly_chart(fig_pom, use_container_width=True)

if filtered["month"].notna().any() and filtered["match_date"].notna().any():
    monthly = (
        filtered.dropna(subset=["month", "year"])
        .groupby(["year", "month"])
        .size()
        .reset_index(name="matches")
    )
    monthly["month"] = pd.Categorical(monthly["month"], categories=MONTH_ORDER, ordered=True)
    monthly = monthly.sort_values(["year", "month"])

    fig_month = px.line(monthly, x="month", y="matches", color="year",
                        markers=True, title="Monthly Match Trend by Season")
    st.plotly_chart(fig_month, use_container_width=True)

# =========================
# TABLES
# =========================
st.subheader("Team Performance Summary")
summary_show = team_stats.copy()
summary_show["win_pct"] = summary_show["win_pct"].round(2)
st.dataframe(summary_show, use_container_width=True)

# =========================
# HEAD TO HEAD
# =========================
st.subheader("Head-to-Head Analyzer")

col_a, col_b = st.columns(2)
team_a = col_a.selectbox("Select Team A", options=all_teams, index=0)
team_b_candidates = [t for t in all_teams if t != team_a]
team_b = col_b.selectbox("Select Team B", options=team_b_candidates, index=0)

h2h = filtered[
    ((filtered["team1_clean"] == team_a) & (filtered["team2_clean"] == team_b)) |
    ((filtered["team1_clean"] == team_b) & (filtered["team2_clean"] == team_a))
]

if not h2h.empty:
    h2h_result = h2h["winner_clean"].value_counts().rename_axis("team").reset_index(name="wins")
    fig_h2h = px.bar(h2h_result, x="team", y="wins", text="wins",
                     title=f"{team_a} vs {team_b} - Win Comparison")
    st.plotly_chart(fig_h2h, use_container_width=True)
    st.caption(f"Total matches between {team_a} and {team_b}: {len(h2h)}")
else:
    st.info("No head-to-head matches available for selected teams.")

# =========================
# RAW DATA
# =========================
st.subheader("Filtered Data")
st.dataframe(filtered, use_container_width=True)

st.download_button(
    label="Download Filtered Data as CSV",
    data=filtered.to_csv(index=False).encode("utf-8"),
    file_name="ipl_filtered_data.csv",
    mime="text/csv"
)

st.markdown("---")