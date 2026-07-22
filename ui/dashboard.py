import streamlit as st
import requests
import pandas as pd
import time


st.set_page_config(page_title="MarketShift Bot", layout="wide")
st.title("🤖 MarketShift - Trading Dashboard")


API_URL = "http://127.0.0.1:8000/status"


# Conteneurs pour le rafraîchissement
metrics_placeholder = st.empty()
positions_placeholder = st.empty()


def fetch_data():
    try:
        response = requests.get(API_URL)
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.ConnectionError:
        return None
    return None


data = fetch_data()


if data and data.get("status") == "running":
    with metrics_placeholder.container():
        col1, col2, col3 = st.columns(3)
        col1.metric("Solde Virtuel", f"{data['balance']:.2f} $")
        col2.metric("Positions Ouvertes", data['open_positions_count'])
        col3.metric("Total Trades", data['total_trades'])


    with positions_placeholder.container():
        st.subheader("🟢 Positions Actuellement Ouvertes")
        if data['open_positions']:
            df_open = pd.DataFrame(data['open_positions'])
            st.dataframe(df_open, use_container_width=True)
        else:
            st.info("Aucune position ouverte pour le moment.")
            
        st.subheader("⚪ Derniers Trades Fermés")
        if data['closed_positions']:
            df_closed = pd.DataFrame(data['closed_positions'])
            st.dataframe(df_closed, use_container_width=True)
else:
    st.error("Impossible de se connecter à l'API du Bot. Vérifiez que main.py est en cours d'exécution.")


# Bouton de rafraîchissement manuel
if st.button("Rafraîchir les données"):
    st.rerun()
