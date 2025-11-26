#!/usr/bin/env python
# coding: utf-8

import streamlit as st
import pandas as pd
import numpy as np

# ---- ALAP BEÁLLÍTÁSOK ----
st.set_page_config(
    page_title="Magyar hosszútávfutás archívum",
    page_icon="🏃‍♂️",
    layout="wide",
)

# ---- STÍLUS ----
st.markdown("""
<style>
    body {
        background-color: #050816;
        color: #f9fafb;
    }
    .main {
        background-color: #050816;
    }

    .big-title {
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0.25rem;
    }
    .subtitle {
        font-size: 0.95rem;
        color: #9ca3af;
        margin-bottom: 1.5rem;
    }

    .event-title {
        font-size: 1.05rem;
        font-weight: 600;
        margin-bottom: 0.25rem;
        border-left: 4px solid #f05a28;
        padding-left: 0.5rem;
    }

    .small-label {
        font-size: 0.8rem;
        color: #9ca3af;
        margin-top: 0.4rem;
        margin-bottom: 0.2rem;
    }

    /* DataFrame kicsit kompaktabb sorokkal */
    [data-testid="stDataFrame"] table tbody tr td {
        padding-top: 0.15rem;
        padding-bottom: 0.15rem;
        font-size: 0.85rem;
    }
    [data-testid="stDataFrame"] table thead tr th {
        padding-top: 0.25rem;
        padding-bottom: 0.25rem;
        font-size: 0.8rem;
    }
    
    /* Világos kék infókártya */
.info-card {
    background: rgba(56, 189, 248, 0.15);  /* light blue */
    border: 1px solid rgba(56, 189, 248, 0.35);
    border-radius: 0.75rem;
    padding: 1rem 1.25rem;
    margin-bottom: 1rem;
}
.info-card-title {
    font-size: 1.6rem;
    font-weight: 600;
    color: #000000;
    margin-bottom: 0.25rem;
}
.info-card-text {
    font-size: 0.9rem;
    color: #000000;
    font-style: italic;
}



</style>
""", unsafe_allow_html=True)


# ---- ADAT BETÖLTÉS ----

event_group_distance = {
    "100 m": 100,
    "200 m": 200,
    "400 m": 400,
    "800 m": 800,
    "1500 m": 1500,
    "3000 m akadály": 3000,
    "5000m": 5000,
    "10 000 m": 10000,
    "félmaraton": 21097,
    "maraton": 42195,
    "100/110 m gát": 110,    # összevont gát
    "400 m gát": 400,
}

@st.cache_data
def load_data():
    df = pd.read_csv("futasok_tisztitott_nev_klub_kulon_smart.csv", encoding="utf-8")
    df["Év"] = df["Év"].astype(int)
    df["Helyezés"] = df["Helyezés"].astype(int)
    df["Eredmény_sec"] = df["Eredmény_sec"].astype(float)

    # Nemi normalizálás – nálad M és W:
    df["Nem_norm"] = df["Nem"]

    # Versenyszám csoportosítás: 100/110 gát egybe
    def normalize_event(ev: str) -> str:
        ev = str(ev).strip()
        if "gát" in ev and (ev.startswith("100") or ev.startswith("110")):
            return "100/110 m gát"
        return ev

    df["Event_group"] = df["Versenyszám"].apply(normalize_event)
    df["Event_group"] = df["Event_group"].astype(str).str.strip().str.lower()

    # Tav hozzárendelés event_group alapján
    df["Tav"] = df["Event_group"].map(event_group_distance)

    return df

df = load_data()


# ---- SEGÉDFÜGGVÉNYEK ----
def format_time(sec: float) -> str:
    if pd.isna(sec):
        return ""
    sec = float(sec)

    # 1) Ha hosszabb mint 1 óra → óó:pp:mm
    if sec >= 3600:
        hours = int(sec // 3600)
        rem = sec - hours * 3600
        minutes = int(rem // 60)
        seconds = int(rem - minutes * 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    # 2) Ha kevesebb, mint 1 perc → ss.ss
    if sec < 60:
        return f"{sec:05.2f}"

    # 3) Egyébként → pp:mm.ss (kétjegyű perc)
    minutes = int(sec // 60)
    seconds = sec - minutes * 60
    return f"{minutes:02d}:{seconds:05.2f}"


def winner_table_for_year(year_df: pd.DataFrame) -> pd.DataFrame:
    year_df = year_df.sort_values(["Event_group", "Nem_norm", "Helyezés"])

    top3 = (
        year_df
        .groupby(["Event_group", "Nem_norm"], group_keys=False)
        .apply(lambda g: g.nsmallest(3, "Helyezés"))
    )

    top3 = top3.copy()
    top3["Idő"] = top3["Eredmény_sec"].apply(format_time)

    return top3[[
        "Event_group",
        "Versenyszám",
        "Nem_norm",
        "Év",
        "Helyezés",
        "Futó_név",
        "Klub",
        "Idő",
        "Tav",
    ]]


# ---- OLDAL FEJLÉC ----
st.markdown('<div class="big-title"> Atlétika országos bajnokság archívum böngésző</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Évek, versenyszámok és futók szerint böngészhető adatbázis - egyelőre futószámokra '
    'Keresés sportolóra, versenyszámra, top3 listák, győztesek időgrafikonja.</div>',
    unsafe_allow_html=True
)
# --- Header nézetválasztó ---
header_view = st.radio(
    "Navigáció",
    ["Éves nézet", "Sportoló kereső", "Versenyszám nézet"],
    horizontal=True,
    label_visibility="collapsed"
)

# A két választó (sidebar + header) legyen szinkronban → a header legyen az elsődleges
view = header_view

st.markdown("---")  # egy egyszerű, vékony horizontális választó a kártya helyett

# ---- OLDALSÁV: NÉZET VÁLASZTÓ ----
# OLDALSÁV (meghagyjuk, de csak vizuális opció)
_ = st.sidebar.radio(
    "Nézet:",
    ["Éves nézet", "Sportoló kereső", "Versenyszám nézet"],
    index=["Éves nézet", "Sportoló kereső", "Versenyszám nézet"].index(view)
)

st.sidebar.markdown("---")
st.sidebar.write("Szűrők és keresés az aktuális nézetnek megfelelően.")


# ======================================================
# 1) ÉVES NÉZET
# ======================================================
if view == "Éves nézet":
    st.markdown("### Éves bontás")
    st.markdown("""
        <div class="info-card">
            <div class="info-card-text">
                Az év választása után a versenyszámok szerint rendezett dobogókat találjuk.
            </div>
        </div>
        """, unsafe_allow_html=True)
    col1, col2 = st.columns([1, 2])

    with col1:
        years = sorted(df["Év"].unique())
        selected_year = st.selectbox("Év kiválasztása", years, index=len(years) - 1)


    year_df = df[df["Év"] == selected_year]
    top3 = winner_table_for_year(year_df)

    st.markdown(f"### 🗓️ {selected_year}. évi dobogósok")

    event_groups_sorted = (
        top3[["Event_group", "Tav"]]
        .drop_duplicates()
        .sort_values("Tav")
    )

    for event_group in event_groups_sorted["Event_group"]:
        ev_df = top3[top3["Event_group"] == event_group]

        # Versenyszám cím (szép, bal oldali narancs csíkkal)
        pretty_name = ev_df["Event_group"].iloc[0]
        st.markdown(f'<div class="event-title">{pretty_name}</div>', unsafe_allow_html=True)

        c1, c2 = st.columns(2)

        for gender_label, col_obj in [("M", c1), ("W", c2)]:
            with col_obj:
                st.markdown(
                    f'<div class="small-label">'
                    f'{"Férfi" if gender_label == "M" else "Női"} dobogó</div>',
                    unsafe_allow_html=True
                )
                g = ev_df[ev_df["Nem_norm"] == gender_label]
                if g.empty:
                    st.write("–")
                else:
                    display = g[["Helyezés", "Futó_név", "Klub", "Idő"]]
                    display = display.rename(columns={
                        "Helyezés": "Hely.",
                        "Futó_név": "Név",
                    })
                    st.dataframe(display, use_container_width=True, hide_index=True)

        st.markdown("---")  # egy egyszerű, vékony horizontális választó a kártya helyett


# ======================================================
# 2) SPORTOLÓ KERESŐ
# ======================================================
elif view == "Sportoló kereső":
    st.markdown("### Sportoló keresése név alapján")

    all_names = sorted(df["Futó_név"].dropna().unique())

    search_text = st.text_input(
        "Írj be egy nevet (vagy részletet):",
        value="",
        placeholder="pl. Szegedi Ferenc"
    )

    if search_text:
        matches = [n for n in all_names if search_text.lower() in n.lower()]
    else:
        matches = all_names

    selected_runner = st.selectbox(
        "Válaszd ki a sportolót:",
        matches if matches else ["Nincs találat"],
        index=0
    )

    if matches and selected_runner in matches:
        r_df = df[df["Futó_név"] == selected_runner].copy()
        r_df["Idő"] = r_df["Eredmény_sec"].apply(format_time)

        wins = (r_df["Helyezés"] == 1).sum()
        podiums = (r_df["Helyezés"] <= 3).sum()
        years_span = f'{r_df["Év"].min()}–{r_df["Év"].max()}'

        st.markdown(f"#### {selected_runner}")
        c1, c2, c3 = st.columns(3)
        c1.metric("🏅 Bajnoki címek (1. hely)", wins)
        c2.metric("🥉 Dobogós helyezések (1–3.)", podiums)
        c3.metric("Aktív évek", years_span)

        st.markdown("#### Összes eredménye")
        show_cols = ["Év", "Versenyszám", "Helyezés", "Idő", "Klub"]
        r_df_sorted = r_df.sort_values(["Év", "Versenyszám", "Helyezés"])

        display_df = r_df_sorted[show_cols].copy()
        display_df["Év"] = display_df["Év"].astype(str)

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )

        won_df = r_df[r_df["Helyezés"] == 1]
        if not won_df.empty:
            st.markdown("#### Megnyert bajnokságok")
            wins_grouped = (
                won_df
                .groupby("Versenyszám")["Év"]
                .apply(lambda s: ", ".join(str(x) for x in sorted(s)))
                .reset_index(name="Évek")
            )
            st.dataframe(wins_grouped, use_container_width=True, hide_index=True)
        else:
            st.info("Ennél a sportolónál nincs 1. helyezés az adatbázisban.")


# ======================================================
# 3) VERSENYSZÁM NÉZET
# ======================================================
elif view == "Versenyszám nézet":
    st.markdown("### Versenyszám nézet")
    st.markdown("""
    <div class="info-card">
        <div class="info-card-text">
            Ebben a nézetben megnézheted, hogy egy adott versenyszámban hogyan alakultak 
            a győztes idők az évek során, ki tartja a legjobb eredményt, 
            és kik nyerték a legtöbb bajnoki címet.
        </div>
    </div>
    """, unsafe_allow_html=True)

    event_df_unique = df[["Versenyszám", "Tav"]].drop_duplicates()
    event_df_unique = event_df_unique.sort_values("Tav")  # rendezzük táv szerint
    events = event_df_unique["Versenyszám"].tolist()
    col1, col2 = st.columns([2, 1])

    with col1:
        selected_event = st.selectbox("Válassz versenyszámot", events)

    with col2:
        gender = st.radio("Nemi kategória", ["M", "W"],
                          format_func=lambda x: "Férfi" if x == "M" else "Női")


    ev_df = df[(df["Versenyszám"] == selected_event) & (df["Nem"] == gender)]

    if ev_df.empty:
        st.warning("Ehhez a kombinációhoz nincs adat.")
    else:
        winners = ev_df[ev_df["Helyezés"] == 1].copy()
        winners = winners.sort_values("Év")
        winners["Idő"] = winners["Eredmény_sec"].apply(format_time)

        best_idx = winners["Eredmény_sec"].idxmin()
        best_row = winners.loc[best_idx]

        wins_by_runner = (
            winners
            .groupby("Futó_név")["Év"]
            .count()
            .sort_values(ascending=False)
        )
        top3_winners = wins_by_runner.head(3)

        st.markdown(
            f"#### {selected_event} – {'Férfi' if gender == 'M' else 'Női'} kategória"
        )
        c1, c2, c3 = st.columns(3)
        c1.metric("📈 Évek száma", len(winners["Év"].unique()))
        c2.metric(
            "⏱️ Valaha futott legjobb idő",
            format_time(best_row["Eredmény_sec"]),
            help=f'{int(best_row["Év"])} – {best_row["Futó_név"]}'
        )
        c3.metric(
            "🏆 Legtöbb bajnoki cím",
            f"{top3_winners.index[0]} ({top3_winners.iloc[0]}×)"
        )

        st.markdown("#### Győztes idők alakulása az évek során")
        chart_df = winners[["Év", "Eredmény_sec"]].copy()
        chart_df = chart_df.set_index("Év")
        st.line_chart(chart_df, use_container_width=True)

        tab1, tab2 = st.tabs(["Győztesek év szerint", "Legtöbbet nyerők"])

        with tab1:
            winners_display = winners[["Év", "Futó_név", "Klub", "Idő"]].copy()
            winners_display = winners_display.sort_values("Év")
            winners_display["Év"] = winners_display["Év"].astype(str)
            st.dataframe(winners_display, use_container_width=True, hide_index=True)

        with tab2:
            top3_df = (
                wins_by_runner
                .reset_index()
                .rename(columns={"Futó_név": "Név", "Év": "Győzelmek száma"})
            )
            st.dataframe(top3_df, use_container_width=True, hide_index=True)
