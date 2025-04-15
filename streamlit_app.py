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

    # 👉 Conversion des timestamps en format date lisible
    df_series['debut'] = pd.to_datetime(df_series['debut']).dt.strftime('%d/%m/%Y')
    df_series['fin'] = pd.to_datetime(df_series['fin']).dt.strftime('%d/%m/%Y')

    # Initialiser les états
    if 'nb_joueurs' not in st.session_state:
        st.session_state.nb_joueurs = []

    if 'matches' not in st.session_state:
        st.session_state.matches = (df['matches'].min(), df['matches'].max())

    if 'combo' not in st.session_state:
        st.session_state.combo = []

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

    # Titre
    st.markdown("<h3 style='text-align: center;'>⚽ Résultats par combinaison</h3>", unsafe_allow_html=True)

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

    # Graphique interactif
    st.markdown("### Visualisation des combos (victoires)")
    if not df_filtered.empty:
        fig = px.bar(
            df_filtered.sort_values(by="victoires", ascending=False).head(20),
            x="combo",
            y="victoires",
            title="Top 20 des combos par nombre de victoires",
            labels={"combo": "Combinaison", "victoires": "Nombre de victoires"},
            text_auto=True
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Aucune donnée à afficher pour ce filtre.")

    # 👉 Application des filtres à df_series
    df_series_filtered = df_series.copy()

    if 'nb_joueurs' in df_series.columns and st.session_state.nb_joueurs:
        df_series_filtered = df_series_filtered[df_series_filtered['nb_joueurs'].isin(st.session_state.nb_joueurs)]

    if st.session_state.combo:
        df_series_filtered = df_series_filtered[df_series_filtered['combo'].isin(st.session_state.combo)]

    # 🎯 Filtre "en cours" juste avant l'affichage de df_series
    st.markdown("### 📅 Séries de matchs (filtrées)")

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

    # Affichage du tableau filtré
    st.dataframe(df_series_filtered, use_container_width=True, hide_index=True)

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()