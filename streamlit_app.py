import streamlit as st
import psycopg2
import pandas as pd


# 📦 Chargement des données avec cache
@st.cache_data(ttl=600)
def load_data(query):
    with psycopg2.connect(
        'postgres://' + st.secrets["DB_USERNAME"] + ':' + st.secrets["DB_PASSWORD"] +
        '@' + st.secrets["DB_HOST"] + ':21552/buddies?sslmode=require'
    ) as conn:
        df = pd.read_sql_query(query, conn)
    return df


def main():
    st.set_page_config(page_title="Tableau interactif", layout="wide")

    # 🔄 Chargement des données
    df = load_data('SELECT * FROM public.combo_stats ORDER BY victoires DESC')
    df_series = load_data('SELECT * FROM public.series ORDER BY debut')
    df_confrontations = load_data('SELECT * FROM public.combo_confrontations ORDER BY victoires DESC')

    # 🔧 Optimisation des types
    for col in ['nb_joueurs', 'nb_joueurs_opposant', 'nb_matches']:
        if col in df_confrontations.columns:
            df_confrontations[col] = pd.to_numeric(df_confrontations[col], errors='coerce').astype('Int16')

    # 👉 Conversion des timestamps
    df_series['debut'] = pd.to_datetime(df_series['debut'], errors='coerce').dt.normalize()
    df_series['fin'] = pd.to_datetime(df_series['fin'], errors='coerce').dt.normalize()

    # Initialisation des états
    if 'matches' not in st.session_state:
        st.session_state.matches = (df['matches'].min(), df['matches'].max())

    st.markdown("### ⚽ Résultats par combinaison")

    options_joueurs = [1, 2, 3, 4, 5]
    nb_joueurs_selectionnes = st.multiselect(
        "Sélectionnez le(s) nombre(s) de joueurs :",
        options=options_joueurs,
        default=options_joueurs
    )

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

    # Filtrage des résultats
    df_filtered = df.copy()
    df_filtered = df_filtered[df_filtered['nb_joueurs'].isin(nb_joueurs_selectionnes)]
    df_filtered = df_filtered[
        (df_filtered['matches'] >= selected_matches[0]) &
        (df_filtered['matches'] <= selected_matches[1])
    ]
    if selected_combos:
        df_filtered = df_filtered[df_filtered['combo'].isin(selected_combos)]
    df_filtered = df_filtered.reset_index(drop=True)

    sort_option = st.radio("Trier par :", ["victoires", "tx_victoires"], horizontal=True)
    df_filtered = df_filtered.sort_values(by=sort_option, ascending=False)

    st.dataframe(df_filtered, use_container_width=True, hide_index=True)

    csv = df_filtered.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Télécharger les données filtrées (CSV)",
        data=csv,
        file_name='resultats_filtres.csv',
        mime='text/csv'
    )

    # 🎯 Séries de matchs
    st.markdown("### 📅 Séries de matchs")

    df_series_filtered = df_series.copy()
    if 'nb_joueurs' in df_series.columns:
        df_series_filtered = df_series_filtered[df_series_filtered['nb_joueurs'].isin(nb_joueurs_selectionnes)]

    if selected_combos:
        df_series_filtered = df_series_filtered[df_series_filtered['combo'].isin(selected_combos)]

    filtre_en_cours = st.radio(
        "Afficher uniquement les séries en cours ?",
        options=["Tous", "Oui", "Non"],
        horizontal=True
    )
    if filtre_en_cours != "Tous":
        df_series_filtered = df_series_filtered[df_series_filtered['en_cours'] == filtre_en_cours]

    filtre_type_serie = st.radio(
        "Type de série à afficher :",
        options=["Toutes", "Séries de victoires", "Séries de défaites"],
        horizontal=True
    )
    if filtre_type_serie != "Toutes":
        condition = 'victoires' if filtre_type_serie == "Séries de victoires" else 'défaites'
        df_series_filtered = df_series_filtered[df_series_filtered['resultat'].str.lower() == condition]

    options_joueurs_series = sorted(df_series['nb_joueurs'].dropna().unique())
    nb_joueurs_series = st.multiselect(
        "Filtrer les séries par nombre de joueurs :",
        options=options_joueurs_series,
        default=options_joueurs_series
    )
    df_series_filtered = df_series_filtered[df_series_filtered['nb_joueurs'].isin(nb_joueurs_series)]

    # 🛠️ Assurez-vous de trier avant le formatage
    df_series_filtered = df_series_filtered.sort_values(by='debut', ascending=False)

    st.dataframe(df_series_filtered, use_container_width=True, hide_index=True)

    # ⚔️ Confrontations optimisées
    st.markdown("### ⚔️ Confrontations")

    df_confrontations_filtered = df_confrontations.copy()

    options_joueurs_confrontations = sorted(df_confrontations['nb_joueurs'].dropna().unique())
    selected_nb_joueurs_confrontations = st.multiselect(
        "Filtrer les confrontations par nombre de joueurs :",
        options=options_joueurs_confrontations,
        default=options_joueurs_confrontations
    )
    df_confrontations_filtered = df_confrontations_filtered[
        df_confrontations_filtered['nb_joueurs'].isin(selected_nb_joueurs_confrontations)
    ]

    options_joueurs_opposant_confrontations = sorted(df_confrontations['nb_joueurs_opposant'].dropna().unique())
    selected_nb_joueurs_opposant_confrontations = st.multiselect(
        "Filtrer les confrontations par nombre de joueurs opposant :",
        options=options_joueurs_opposant_confrontations,
        default=options_joueurs_opposant_confrontations
    )
    df_confrontations_filtered = df_confrontations_filtered[
        df_confrontations_filtered['nb_joueurs_opposant'].isin(selected_nb_joueurs_opposant_confrontations)
    ]

    selected_combos_confrontations = st.multiselect(
        "Filtrer confrontations par combinaison",
        sorted(df_confrontations['combo'].dropna().unique()),
        default=[],
        help="Laissez vide pour tout afficher"
    )
    if selected_combos_confrontations:
        df_confrontations_filtered = df_confrontations_filtered[
            df_confrontations_filtered['combo'].isin(selected_combos_confrontations)
        ]

    min_matches = int(df_confrontations['nb_matches'].min())
    max_matches = int(df_confrontations['nb_matches'].max())
    selected_nb_matches = st.slider(
        "Sélectionnez le nombre de matches minimum ou maximum",
        min_value=min_matches,
        max_value=max_matches,
        value=(min_matches, max_matches)
    )
    df_confrontations_filtered = df_confrontations_filtered[
        (df_confrontations_filtered['nb_matches'] >= selected_nb_matches[0]) &
        (df_confrontations_filtered['nb_matches'] <= selected_nb_matches[1])
    ]

    st.dataframe(df_confrontations_filtered, hide_index=True)


if __name__ == "__main__":
    main()
