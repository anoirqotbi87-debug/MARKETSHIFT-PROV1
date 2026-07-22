import streamlit as st
import requests
import pandas as pd


st.set_page_config(page_title="MarketShift Bot", layout="wide")
st.title("🤖 MarketShift - Control Center")


API_URL = "http://127.0.0.1:8000"


def fetch_data(endpoint="/status"):
    try: return requests.get(f"{API_URL}{endpoint}").json()
    except: return None


def send_command(action):
    try: requests.post(f"{API_URL}/control", json={"action": action})
    except Exception as e: st.error(f"Erreur de communication : {e}")


# --- BARRE LATÉRALE (CONTRÔLE) ---
with st.sidebar:
    st.header("🎛️ Panneau de Contrôle")
    data = fetch_data()
    
    if data:
        status_color = "🔴 En Pause" if data.get("status") == "paused" else "🟢 Actif"
        st.subheader(f"Statut Moteur : {status_color}")
        
        col1, col2 = st.columns(2)
        if col1.button("▶️ Start"):
            send_command("resume")
            st.rerun()
        if col2.button("⏸️ Pause"):
            send_command("pause")
            st.rerun()
            
        st.divider()
        st.subheader("📊 Backtesting")
        if st.button("Lancer Backtest XGBoost"):
            with st.spinner("Simulation en cours..."):
                res = requests.post(f"{API_URL}/backtest").json()
                if res.get("success"):
                    st.success("Backtest terminé !")
                    st.metric("Capital Final", f"{res['final_balance']} $")
                    st.metric("Win Rate", f"{res['win_rate']} %")
                    st.metric("Total Trades", res['total_trades'])
                else:
                    st.error(res.get("error", "Erreur inconnue"))
    else:
        st.error("API hors ligne.")


# --- ZONE PRINCIPALE (MONITORING) ---
if data and data.get("status") != "error":
    col1, col2, col3 = st.columns(3)
    col1.metric("Solde Virtuel", f"{data['balance']:.2f} $")
    col2.metric("Positions Ouvertes", data['open_positions_count'])
    col3.metric("Total Trades Historique", data['total_trades'])


    st.subheader("🟢 Positions Ouvertes")
    if data['open_positions']:
        st.dataframe(pd.DataFrame(data['open_positions']), use_container_width=True)
    else:
        st.info("Aucune position en cours.")
        
    st.subheader("⚪ Derniers Trades Fermés")
    if data['closed_positions']:
        st.dataframe(pd.DataFrame(data['closed_positions']), use_container_width=True)
