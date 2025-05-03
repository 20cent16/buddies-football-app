import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px


def paginate_dataframe(df, page_size=20):
    total_rows = len(df)
    total_pages = (total_rows - 1) // page_size + 1
    page_number = st.number_input("Page", min_value=1, max_value=total_pages, value=1)
    start = (page_number - 1) * page_size
    end = start + page_size
    return df.iloc[start:end]


def main():
    st.set_page_config(page_title="Tableau interactif", layout="wide")

    # Connexion à la base de données
    conn = psycopg2.connect(
        'postgres://' + st.secrets["DB_USERNAME"] + ':' + st.secrets["DB_PASSWORD"] +
        '@' + st.secrets["DB_HOST"] + ':21552/buddies?sslmode=require'
    )

    # Récupération des données
    query_sql = 'SELECT * FROM public.combo_stats ORDER BY victoires DESC'
    cur = conn.cursor()
    cur.execute(query_sql)
    rows = cur.fetchall()
    colnames = [desc[0] for desc in cur.description]
    df = pd.DataFrame(rows, columns=colnames)

    query_sql = 'SELECT * FROM public.series ORDER BY debut'
    cur.execute(query_sql)
    rows = cur.fetchall()
    colnames = [desc[0] for desc in cur.description]
    df_series = pd.DataFrame(rows, columns=colnames)

    query_sql = 'SELECT * FROM public.combo_confrontations ORDER BY victoires DESC'
    cur.execute(query_sql)
    rows = cur.fetchall()
    colnames = [desc[0] for desc in cur.description]
    df_confrontations = pd.DataFrame(rows, columns=colnames)

    df_series['debut'] = pd.to_datetime(df_series['debut']).dt.strftime('%d/%m/%Y')
    df_series['fin'] = pd.to_datetime(df_series['fin']).dt.strftime('%d/%m/%Y')

    if 'nb_joueurs' not in st.session_state:
        st.session_state.nb_joueurs = []

    if 'nb_joueurs_opposant' not in st.session_state:
        st.session_state.nb_joueurs_opposant = []

    if 'matches' not in st.session_state:
        st.session_state.matches = (df['matches'].min(), df['matches'].max())

    if 'combo' not in st.session_state:
        st.session_state.combo = []

    st.markdown("### ⚽ Résultats par combinaison")

    options_joueurs = [1, 2, 3, 4, 5]
    nb_joueurs_selectionnes = st.multiselect(
        "Sélectionnez le(s) nombre(s) de joueurs :", 
        options=options_joueurs, 
        default=options_joueurs
    )
    st.session_state.nb_joueurs = nb_joueurs_selectionnes

    combo_col, slider_col = st.columns([1, 3])

    with slider_col:
        min_matches = int(df['matches'].min())
        max_matches = int(df['matches'].max())
        selected_matches = st.slider(
            "Sélectionnez le nombre de matches minimum ou maximum", 
            min_value=min_matches, 
            max_value=max_matches, 
            value=st.session_state.matches
        )
        st.session_state.matches = selected_matches

    with combo_col:
        combo_options = sorted(df['combo'].dropna().unique())
        selected_combos = st.multiselect(
            "Filtrer par combinaison",
            combo_options,
            default=[],
            help="Laissez vide pour tout afficher"
        )
        st.session_state.combo = selected_combos

    df_filtered = df.copy()

    if st.session_state.nb_joueurs:
        df_filtered = df_filtered[df_filtered['nb_joueurs'].isin(st.session_state.nb_joueurs)]

    df_filtered = df_filtered[
        (df_filtered['matches'] >= st.session_state.matches[0]) & 
        (df_filtered['matches'] <= st.session_state.matches[1])
    ]

    if st.session_state.combo:
        df_filtered = df_filtered[df_filtered['combo'].isin(st.session_state.combo)]

    df_filtered = df_filtered.reset_index(drop=True)

    sort_option = st.radio("Trier par :", ["victoires", "tx_victoires"], horizontal=True)
    df_filtered = df_filtered.sort_values(by=sort_option, ascending=False)

    st.dataframe(paginate_dataframe(df_filtered), use_container_width=True, hide_index=True)

    if not df_filtered.empty:
        st.markdown("### 📊 Graphique : Victoires par combinaison")
        fig = px.bar(
            df_filtered,
            x="combo",
            y="victoires",
            color="nb_joueurs",
            title="Nombre de victoires par combinaison",
            labels={"victoires": "Victoires", "combo": "Combinaison"},
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)

    csv = df_filtered.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Télécharger les données filtrées (CSV)",
        data=csv,
        file_name='resultats_filtres.csv',
        mime='text/csv'
    )

    df_series_filtered = df_series.copy()
    if 'nb_joueurs' in df_series.columns and st.session_state.nb_joueurs:
        df_series_filtered = df_series_filtered[df_series_filtered['nb_joueurs'].isin(st.session_state.nb_joueurs)]
    if st.session_state.combo:
        df_series_filtered = df_series_filtered[df_series_filtered['combo'].isin(st.session_state.combo)]

    st.markdown("### 🗕️ Séries de matchs")

    filtre_en_cours = st.radio(
        "Afficher uniquement les séries en cours ?",
        options=["Tous", "Oui", "Non"],
        horizontal=True
    )
    if filtre_en_cours != "Tous":
        valeur_texte = "Oui" if filtre_en_cours == "Oui" else "Non"
        df_series_filtered = df_series_filtered[df_series_filtered['en_cours'] == valeur_texte]

    filtre_type_serie = st.radio(
        "Type de série à afficher :",
        options=["Toutes", "Séries de victoires", "Séries de défaites"],
        horizontal=True
    )
    if filtre_type_serie != "Toutes":
        if filtre_type_serie == "Séries de victoires":
            df_series_filtered = df_series_filtered[df_series_filtered['resultat'].str.lower() == 'victoires']
        else:
            df_series_filtered = df_series_filtered[df_series_filtered['resultat'].str.lower() == 'défaites']

    options_joueurs_series = sorted(df_series['nb_joueurs'].dropna().unique())
    nb_joueurs_series = st.multiselect(
        "Filtrer les séries par nombre de joueurs :",
        options=options_joueurs_series,
        default=options_joueurs_series
    )
    df_series_filtered = df_series_filtered[df_series_filtered['nb_joueurs'].isin(nb_joueurs_series)]

    st.dataframe(paginate_dataframe(df_series_filtered), use_container_width=True, hide_index=True)

    df_confrontations_filtered = df_confrontations.copy()

    if 'nb_joueurs' in df_confrontations.columns and st.session_state.nb_joueurs:
        df_confrontations_filtered = df_confrontations_filtered[df_confrontations_filtered['nb_joueurs'].isin(st.session_state.nb_joueurs)]

    if 'nb_joueurs_opposant' in df_confrontations.columns and st.session_state.nb_joueurs_opposant:
        df_confrontations_filtered = df_confrontations_filtered[df_confrontations_filtered['nb_joueurs_opposant'].isin(st.session_state.nb_joueurs_opposant)]

    st.markdown("### ⚔️ Confrontations (NE PAS UTILISER, FAUX)")

    options_joueurs_confrontations = sorted(df_confrontations['nb_joueurs'].dropna().unique())
    nb_joueurs_confrontations = st.multiselect(
        "Filtrer les confrontations par nombre de joueurs :",
        options=options_joueurs_confrontations,
        default=options_joueurs_confrontations
    )
    df_confrontations_filtered = df_confrontations_filtered[df_confrontations_filtered['nb_joueurs'].isin(nb_joueurs_confrontations)]

    options_joueurs_opposant_confrontations = sorted(df_confrontations['nb_joueurs_opposant'].dropna().unique())
    nb_joueurs_opposant_confrontations = st.multiselect(
        "Filtrer les confrontations par nombre de joueurs opposant :",
        options=options_joueurs_opposant_confrontations,
        default=options_joueurs_opposant_confrontations
    )
    df_confrontations_filtered = df_confrontations_filtered[df_confrontations_filtered['nb_joueurs_opposant'].isin(nb_joueurs_opposant_confrontations)]

    selected_combos_confrontations = st.multiselect(
        "Filtrer confrontations par combinaison",
        combo_options,
        default=[],
        help="Laissez vide pour tout afficher"
    )
    st.session_state.combo = selected_combos_confrontations

    if st.session_state.combo:
        df_confrontations_filtered = df_confrontations_filtered[df_confrontations_filtered['combo'].isin(st.session_state.combo)]

    min_matches = int(df_confrontations['nb_matches'].min())
    max_matches = int(df_confrontations['nb_matches'].max())
    selected_nb_matches = st.slider(
        "Sélectionnez le nombre de matches minimum ou maximum", 
        min_value=min_matches, 
        max_value=max_matches, 
        value=st.session_state.matches
    )
    st.session_state.matches = selected_nb_matches

    df_confrontations_filtered = df_confrontations_filtered[
        (df_confrontations_filtered['nb_matches'] >= st.session_state.matches[0]) & 
        (df_confrontations_filtered['nb_matches'] <= st.session_state.matches[1])
    ]

    st.dataframe(paginate_dataframe(df_confrontations_filtered), hide_index=True)

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
