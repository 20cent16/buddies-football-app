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
        st.session_state.nb_joueurs = None

    if 'total_matches' not in st.session_state:
        st.session_state.total_matches = (df['total_matchs'].min(), df['total_matchs'].max())

    if 'combo' not in st.session_state:
        st.session_state.combo = ""

    # Créer une disposition en 2 colonnes
    col1, col2 = st.columns([1, 3])  # 1 partie pour les boutons, 3 parties pour le tableau
    
    # Placer les boutons dans la première colonne
    with col1:
        button_1 = st.button("1 joueur")
        button_2 = st.button("2 joueurs")
        button_3 = st.button("3 joueurs")
        button_4 = st.button("4 joueurs")
        button_5 = st.button("5 joueurs")

        # Appliquer le filtre selon le bouton cliqué
        if button_1:
            st.session_state.nb_joueurs = 1
        elif button_2:
            st.session_state.nb_joueurs = 2
        elif button_3:
            st.session_state.nb_joueurs = 3
        elif button_4:
            st.session_state.nb_joueurs = 4
        elif button_5:
            st.session_state.nb_joueurs = 5

    # Placer le slider pour le total de matches dans la deuxième colonne
    with col2:
        # Définir les valeurs minimales et maximales pour le slider du total de matches
        min_total_matches = int(df['total_matchs'].min())
        max_total_matches = int(df['total_matchs'].max())

        # Slider pour sélectionner une plage de total de matches
        selected_total_matches = st.slider(
            "Sélectionnez une plage de total de matches", 
            min_value=min_total_matches, 
            max_value=max_total_matches, 
            value=st.session_state.total_matches
        )
        
        # Enregistrer la plage sélectionnée dans session_state
        st.session_state.total_matches = selected_total_matches

        # Champ de texte pour filtrer par nom de joueur
        joueur_input = st.text_input("Filtrer par nom de joueur", "")
        st.session_state.joueur = joueur_input

    # Appliquer les filtres basés sur l'état de session
    df_filtered = df.copy()

    # Filtrer selon le nombre de joueurs
    if st.session_state.nb_joueurs is not None:
        df_filtered = df_filtered[df_filtered['nb_joueurs'] == st.session_state.nb_joueurs]

    # Filtrer selon la plage de total de matches
    df_filtered = df_filtered[
        (df_filtered['total_matchs'] >= st.session_state.total_matches[0]) & 
        (df_filtered['total_matchs'] <= st.session_state.total_matches[1])
    ]

    # Filtrer par nom de joueur
    if st.session_state.joueur:
        df_filtered = df_filtered[df_filtered['combo'].str.contains(st.session_state.joueur, case=False, na=False)]

    # Enlever la colonne d'index (numéro de ligne) et masquer l'index
    df_filtered = df_filtered.reset_index(drop=True)

    # Afficher le DataFrame filtré sans la colonne d'index
    st.title("Résultats par combinaison de joueurs, total de matches et nom de joueur")
    st.dataframe(df_filtered, use_container_width=True, hide_index=True)

    # Fermer la connexion
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
