import streamlit as st
import psycopg2
import pandas as pd


def main():

     # Configurer la page Streamlit pour occuper toute la largeur
    st.set_page_config(page_title="Tableau interactif", layout="wide")  # 'wide' pour maximiser la largeur

    conn = psycopg2.connect('postgres://'+st.secrets["DB_USERNAME"]+':'+st.secrets["DB_PASSWORD"]+'@'+st.secrets["DB_HOST"]+':21552/buddies?sslmode=require')
        # Requête SQL pour récupérer les données
    query_sql = 'SELECT * FROM public.combo_stats'

    # Exécution de la requête
    cur = conn.cursor()
    cur.execute(query_sql)

    # Récupérer toutes les lignes de la table
    rows = cur.fetchall()

    # Récupérer les noms de colonnes
    colnames = [desc[0] for desc in cur.description]

    # Convertir les résultats en DataFrame pour un affichage dans Streamlit
    df = pd.DataFrame(rows, columns=colnames)

   # Initialiser les variables dans le session_state si ce n'est pas déjà fait
    if 'nb_joueurs' not in st.session_state:
        st.session_state.nb_joueurs = []

    if 'total_matchs' not in st.session_state:
        st.session_state.total_matchs = (df['total_matchs'].min(), df['total_matchs'].max())

    if 'combo' not in st.session_state:
        st.session_state.combo = ""

    # Placer les cases à cocher côte à côte au-dessus du tableau
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        checkbox_1 = st.checkbox("1 joueur")
        if checkbox_1:
            st.session_state.nb_joueurs.append(1)
        else:
            if 1 in st.session_state.nb_joueurs:
                st.session_state.nb_joueurs.remove(1)

    with col2:
        checkbox_2 = st.checkbox("2 joueurs")
        if checkbox_2:
            st.session_state.nb_joueurs.append(2)
        else:
            if 2 in st.session_state.nb_joueurs:
                st.session_state.nb_joueurs.remove(2)

    with col3:
        checkbox_3 = st.checkbox("3 joueurs")
        if checkbox_3:
            st.session_state.nb_joueurs.append(3)
        else:
            if 3 in st.session_state.nb_joueurs:
                st.session_state.nb_joueurs.remove(3)

    with col4:
        checkbox_4 = st.checkbox("4 joueurs")
        if checkbox_4:
            st.session_state.nb_joueurs.append(4)
        else:
            if 4 in st.session_state.nb_joueurs:
                st.session_state.nb_joueurs.remove(4)

    with col5:
        checkbox_5 = st.checkbox("5 joueurs")
        if checkbox_5:
            st.session_state.nb_joueurs.append(5)
        else:
            if 5 in st.session_state.nb_joueurs:
                st.session_state.nb_joueurs.remove(5)

    # Ajouter un espace ici pour séparer les cases à cocher du reste de la page
    st.markdown("<br>", unsafe_allow_html=True)

    # Placer le slider et le champ de texte pour le combo en dessous des cases à cocher
    slider_col, combo_col = st.columns([3, 1])  # 3 parties pour le slider, 1 pour le champ de texte

    with slider_col:
        # Définir les valeurs minimales et maximales pour le slider du total de matchs
        min_total_matchs = int(df['total_matchs'].min())
        max_total_matchs = int(df['total_matchs'].max())

        # Slider pour sélectionner une plage de total de matchs
        selected_total_matchs = st.slider(
            "Sélectionnez une plage de total de matchs", 
            min_value=min_total_matchs, 
            max_value=max_total_matchs, 
            value=st.session_state.total_matchs
        )
        
        # Enregistrer la plage sélectionnée dans session_state
        st.session_state.total_matchs = selected_total_matchs

    with combo_col:
        # Champ de texte pour filtrer par combinaison (combo)
        combo_input = st.text_input("Filtrer par combinaison (combo)", "")
        st.session_state.combo = combo_input

    # Appliquer les filtres basés sur l'état de session
    df_filtered = df.copy()

    # Filtrer selon le nombre de joueurs sélectionnés
    if st.session_state.nb_joueurs:
        df_filtered = df_filtered[df_filtered['nb_joueurs'].isin(st.session_state.nb_joueurs)]

    # Filtrer selon la plage de total de matchs
    df_filtered = df_filtered[
        (df_filtered['total_matchs'] >= st.session_state.total_matchs[0]) & 
        (df_filtered['total_matchs'] <= st.session_state.total_matchs[1])
    ]

    # Filtrer par combinaison (combo)
    if st.session_state.combo:
        df_filtered = df_filtered[df_filtered['combo'].str.contains(st.session_state.combo, case=False, na=False)]

    # Enlever la colonne d'index (numéro de ligne) et masquer l'index
    df_filtered = df_filtered.reset_index(drop=True)

    # Afficher le titre avec une taille réduite, un ballon devant et centré
    st.markdown("<h3 style='text-align: center;'>⚽ Résultats par combinaison, total de matchs et combo</h3>", unsafe_allow_html=True)

    # Afficher le DataFrame filtré et permettre le tri par les colonnes
    st.dataframe(df_filtered, use_container_width=True, hide_index=True)

    # Fermer la connexion
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
