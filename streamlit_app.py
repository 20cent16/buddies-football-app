import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px


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
    cur = conn.cursor()
    cur.execute(query_sql)
    rows = cur.fetchall()
    colnames = [desc[0] for desc in cur.description]
    df_series = pd.DataFrame(rows, columns=colnames)

    query_sql = 'SELECT * FROM public.combo_confrontations ORDER BY victoires DESC'
    cur = conn.cursor()
    cur.execute(query_sql)
    rows = cur.fetchall()
    colnames = [desc[0] for desc in cur.description]
    df_confrontations = pd.DataFrame(rows, columns=colnames)

    # 👉 Conversion des timestamps en format date lisible
    df_series['debut'] = pd.to_datetime(df_series['debut']).dt.strftime('%d/%m/%Y')
    df_series['fin'] = pd.to_datetime(df_series['fin']).dt.strftime('%d/%m/%Y')

    # Initialiser les états
    if 'nb_joueurs' not in st.session_state:
        st.session_state.nb_joueurs = []

    if 'nb_joueurs_opposant' not in st.session_state:
        st.session_state.nb_joueurs_opposant = []

    if 'matches' not in st.session_state:
        st.session_state.matches = (df['matches'].min(), df['matches'].max())

    if 'combo' not in st.session_state:
        st.session_state.combo = []

    # Titre
    st.markdown("### ⚽ Résultats par combinaison")

    # Filtres utilisateurs
    options_joueurs = [1, 2, 3, 4, 5]
    nb_joueurs_selectionnes = st.multiselect(
        "Sélectionnez le(s) nombre(s) de joueurs :", 
        options=options_joueurs, 
        default=options_joueurs
    )
    st.session_state.nb_joueurs = nb_joueurs_selectionnes

    st.markdown("<br>", unsafe_allow_html=True)
    slider_col, combo_col = st.columns([3, 1])

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

    # Application des filtres
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

    # Tri rapide
    sort_option = st.radio("Trier par :", ["victoires", "tx_victoires"], horizontal=True)
    df_filtered = df_filtered.sort_values(by=sort_option, ascending=False)

    # Tableau
    st.dataframe(df_filtered, use_container_width=True, hide_index=True)

    # Export CSV
    csv = df_filtered.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Télécharger les données filtrées (CSV)",
        data=csv,
        file_name='resultats_filtres.csv',
        mime='text/csv'
    )

    # 👉 Application des filtres à df_series
    df_series_filtered = df_series.copy()

    if 'nb_joueurs' in df_series.columns and st.session_state.nb_joueurs:
        df_series_filtered = df_series_filtered[df_series_filtered['nb_joueurs'].isin(st.session_state.nb_joueurs)]

    if st.session_state.combo:
        df_series_filtered = df_series_filtered[df_series_filtered['combo'].isin(st.session_state.combo)]

    # 🎯 Filtre "en cours" juste avant l'affichage de df_series
    st.markdown("### 📅 Séries de matchs")

    filtre_en_cours = st.radio(
        "Afficher uniquement les séries en cours ?",
        options=["Tous", "Oui", "Non"],
        horizontal=True
    )

    # 🔍 Appliquer le filtre "en_cours"
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

    # 🎛️ Filtre sur le nombre de joueurs pour les séries
    options_joueurs_series = sorted(df_series['nb_joueurs'].dropna().unique())
    nb_joueurs_series = st.multiselect(
        "Filtrer les séries par nombre de joueurs :",
        options=options_joueurs_series,
        default=options_joueurs_series
    )
    df_series_filtered = df_series_filtered[df_series_filtered['nb_joueurs'].isin(nb_joueurs_series)]

    # Affichage du tableau filtré
    st.dataframe(df_series_filtered, use_container_width=True, hide_index=True)



 # 👉 Application des filtres à df_confrontations
    df_confrontations_filtered = df_confrontations.copy()

    if 'nb_joueurs' in df_confrontations.columns and st.session_state.nb_joueurs:
        df_confrontations_filtered = df_confrontations_filtered[df_confrontations_filtered['nb_joueurs'].isin(st.session_state.nb_joueurs)]

    if 'nb_joueurs_opposant' in df_confrontations.columns and st.session_state.nb_joueurs_opposant:
        df_confrontations_filtered = df_confrontations_filtered[df_confrontations_filtered['nb_joueurs_opposant'].isin(st.session_state.nb_joueurs_opposant)]

    if st.session_state.combo:
        df_confrontations_filtered = df_confrontations_filtered[df_confrontations_filtered['combo'].isin(st.session_state.combo)]

    # 🎯 Filtre "en cours" juste avant l'affichage de df_confrontations
    st.markdown("### 📅 Confrontations")

    # 🎛️ Filtre sur le nombre de joueurs pour les confrontations
    options_joueurs_confrontations = sorted(df_confrontations['nb_joueurs'].dropna().unique())
    nb_joueurs_confrontations = st.multiselect(
        "Filtrer les confrontations par nombre de joueurs :",
        options=options_joueurs_confrontations,
        default=options_joueurs_confrontations
    )
    df_confrontations_filtered = df_confrontations_filtered[df_confrontations_filtered['nb_joueurs'].isin(nb_joueurs_confrontations)]

    # 🎛️ Filtre sur le nombre de joueurs opposant pour les confrontations
    options_joueurs_opposant_confrontations = sorted(df_confrontations['nb_joueurs_opposant'].dropna().unique())
    nb_joueurs_opposant_confrontations = st.multiselect(
        "Filtrer les confrontations par nombre de joueurs opposant :",
        options=options_joueurs_opposant_confrontations,
        default=options_joueurs_opposant_confrontations
    )

    # Nb Matches
    min_matches = int(df_confrontations['nb_matches'].min())
    max_matches = int(df_confrontations['nb_matches'].max())
    slider_col_nb_matches=selected_matches = st.slider(
            "Sélectionnez le nombre de matches minimum ou maximum", 
            min_value=min_matches, 
            max_value=max_matches, 
            value=st.session_state.matches
        )
    st.session_state.matches = selected_matches

    df_confrontations_filtered = df_confrontations_filtered[df_confrontations_filtered['nb_joueurs_opposant'].isin(nb_joueurs_opposant_confrontations)]


    # Affichage du tableau filtré
    st.dataframe(df_confrontations_filtered, hide_index=True)

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()