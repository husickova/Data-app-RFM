import streamlit as st
import pandas as pd

# Titulek aplikace
st.title("RFM for Keboola by Bytegarden")

# Načtení CSV souboru
csv_path = "rfm-data.csv"  # relativní cesta, pokud je skript ve stejné složce
try:
    df = pd.read_csv(csv_path)
    # Zobrazení tabulky
    st.dataframe(df)
except FileNotFoundError:
    st.error(f"Soubor na cestě {csv_path} nebyl nalezen.")
except Exception as e:
    st.error(f"Došlo k chybě při načítání souboru: {e}")

if __name__ == "__main__":
    st.run()
