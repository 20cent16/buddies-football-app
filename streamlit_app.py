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
    query_sql = 'SELECT * FROM public.combo_stats ORDER BY victoire DESC'
    cur = conn.cursor()
    cur.execute(query_sql)
    rows = cur.fetchall()
    colnames = [desc[0] for desc in cur.description]
    df = pd.DataFrame(rows, columns=colnames)

    # Initialiser les états
    if 'nb_joueurs' not in st.session_state:
        st.session_state.nb_joueurs = []

    if 'total_matchs' not in st.session_state:
        st.session_state.total_matchs = (df['total_matchs'].min(), df['total_matchs'].max())

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
        min_total_matchs = int(df['total_matchs'].min())
        max_total_matchs = int(df['total_matchs'].max())
        selected_total_matchs = st.slider(
            "Sélectionnez le nombre de matches minimum ou maximum", 
            min_value=min_total_matchs, 
            max_value=max_total_matchs, 
            value=st.session_state.total_matchs
        )
        st.session_state.total_matchs = selected_total_matchs

    with combo_col:
        combo_options = sorted(df['combo'].dropna().unique())
        selected_combos = st.multiselect("Filtrer par combinaison", combo_options, default=combo_options)
        st.session_state.combo = selected_combos

    # Application des filtres
    df_filtered = df.copy()
    if st.session_state.nb_joueurs:
        df_filtered = df_filtered[df_filtered['nb_joueurs'].isin(st.session_state.nb_joueurs)]

    df_filtered = df_filtered[
        (df_filtered['total_matchs'] >= st.session_state.total_matchs[0]) & 
        (df_filtered['total_matchs'] <= st.session_state.total_matchs[1])
    ]

    if st.session_state.combo:
        df_filtered = df_filtered[df_filtered['combo'].isin(st.session_state.combo)]

    df_filtered = df_filtered.reset_index(drop=True)

    # Tri rapide
    sort_option = st.radio("Trier par :", ["victoire", "taux_victoire"], horizontal=True)
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
    fig = px.bar(
        df_filtered.sort_values(by="victoire", ascending=False).head(20),
        x="combo",
        y="victoire",
        title="Top 20 des combos par nombre de victoires",
        labels={"combo": "Combinaison", "victoire": "Nombre de victoires"},
        text_auto=True
    )
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

    # Fermeture connexion
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()