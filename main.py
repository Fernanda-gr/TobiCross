import streamlit as st
from streamlit_card import card

st.set_page_config(page_title="TobiCross", page_icon="🎌", layout="wide")

st.markdown("""
<style>
* { box-sizing: border-box; }

.block-container {
    padding-top: 1rem !important;
    padding-bottom: 1rem !important;
}

div[data-testid="stHorizontalBlock"] {
    gap: 4px !important;
}

div[data-testid="stHorizontalBlock"] > div {
    padding: 0 !important;
}

/* Junta los dos grids */
div[data-testid="stVerticalBlockBorderWrapper"] {
    margin-top: 0 !important;
    margin-bottom: 0 !important;
}

div[data-testid="stVerticalBlock"] > div {
    margin-bottom: 0 !important;
}
</style>
""", unsafe_allow_html=True)


# ─── HEADER ───────────────────────────────────────────────────────────────────
_, col_logo, col_titulo, _ = st.columns([0.3, 2, 4, 0.3])

with col_logo:
    st.image("assets/logo.png", use_container_width=True)

with col_titulo:
    st.markdown("""
    <div style="display:flex; flex-direction:column; justify-content:center;
                height:100%; padding-left:30px; padding-top:10px;">
       <p style="font-size:11px; color:#534AB7 !important; letter-spacing:5px;
          font-weight:600; margin:0 0 8px; text-transform:uppercase;">
    Descubre tu anime
</p>
            Descubre tu anime
        </p>
        <p style="font-size:120px; font-weight:900; color:#1A1635;
                  margin:0 0 10px; line-height:1; letter-spacing:-4px;
                  font-family: 'Georgia', serif;">
            TobiCross
        </p>
        <p style="font-size:16px; color:#888; margin:0; line-height:1.5;">
            Cruza tus gustos. Encuentra tu anime.
        </p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ─── FEATURES ─────────────────────────────────────────────────────────────────
FEATURES = [
    ("🎯", "RECOMENDADOR",  "Busca tu película favorita.",   "pages/Recomendador.py", "linear-gradient(135deg, #6B2737, #C0394F)"),
    ("🔮", "MODO DESTINO",  "5 preguntas, un destino.",      "pages/Modo_Destino.py", "linear-gradient(135deg, #1B3A6B, #2E6DB4)"),
    ("👥", "MODO DÚO",      "Un anime para los dos.",        "pages/Modo_Duo.py",     "linear-gradient(135deg, #2D5A3D, #4A9463)"),
    ("🗺️", "PORTAL",        "Explora mundos conectados.",    "pages/Portal.py",       "linear-gradient(135deg, #5C3A1E, #A0622A)"),
    ("📊", "PERFIL DE FAN", "Descubre tu arquetipo.",        "pages/Perfil_Fan.py",   "linear-gradient(135deg, #3B1F6B, #6B3DB5)"),
    ("💬", "CHAT CON YOMI", "Tu guía entre mundos.",         "pages/Chat.py",         "linear-gradient(135deg, #1A4A5A, #2A7A8A)"),
    ("🎴", "CARTA ASTRAL",  "Deja que el universo elija.",   "pages/Carta_Astral.py", "linear-gradient(135deg, #4A2040, #8B3A72)"),
]


def anime_card(emoji, titulo, desc, pagina, color, key):
    clicked = card(
        title=f"{emoji}  {titulo}",
        text=desc,
        image=None,
        key=key,
        styles={
            "card": {
                "width": "100%",
                "height": "180px",
                "border-radius": "20px",
                "background": color,
                "border": "none",
                "box-shadow": "0 4px 20px rgba(0,0,0,0.2)",
                "cursor": "pointer",
                "margin": "0",
            },
            "title": {
                "font-size": "20px",
                "font-weight": "900",
                "letter-spacing": "0.1em",
                "color": "#FFFFFF",
                "text-shadow": "0 1px 4px rgba(0,0,0,0.4)",
            },
            "text": {
                "font-size": "12px",
                "color": "rgba(255,255,255,0.85)",
                "font-weight": "400",
            },
            "filter": {
                "background-color": "rgba(0,0,0,0)",
            },
        },
    )
    if clicked:
        st.switch_page(pagina)


# ─── GRID 1 ───────────────────────────────────────────────────────────────────
cols1 = st.columns(4)
for i in range(4):
    emoji, titulo, desc, pagina, color = FEATURES[i]
    with cols1[i]:
        anime_card(emoji, titulo, desc, pagina, color, key=f"card_{i}")

# ─── GRID 2 ───────────────────────────────────────────────────────────────────
_, c1, c2, c3, _ = st.columns([0.1, 1, 1, 1, 0.1])
for j, col in enumerate([c1, c2, c3]):
    emoji, titulo, desc, pagina, color = FEATURES[4 + j]
    with col:
        anime_card(emoji, titulo, desc, pagina, color, key=f"card_{4+j}")



st.markdown("---")
st.markdown("© 2026 Fernanda García | Recomendador de Anime")
st.markdown("Datos obtenidos de APIs públicas (MAL/TMDB). Uso educativo.")