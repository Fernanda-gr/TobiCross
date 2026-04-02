# core/data.py
import pandas as pd
import numpy as np
import faiss
import streamlit as st
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

@st.cache_resource
def cargar_datos():
    """Carga dataframes e índices FAISS — se cachea en memoria."""
    df_anime  = pd.read_parquet(DATA_DIR / "df_anime_final.parquet")
    df_pelser = pd.read_parquet(DATA_DIR / "df_pelser_final.parquet")

    index_scores = faiss.read_index(str(DATA_DIR / "index_scores.faiss"))
    index_embed  = faiss.read_index(str(DATA_DIR / "index_embed.faiss"))

    return df_anime, df_pelser, index_scores, index_embed

    