import streamlit as st
from core.data import cargar_datos

st.set_page_config(
    page_title="TobiCross",
    page_icon="🎌",
    layout="wide"
)

df_anime, df_pelser, index_scores, index_embed = cargar_datos()

st.title("🎌 TobiCross")
st.caption("Recomendador de anime para principiantes")

query = st.text_input("¿Qué película o serie te gusta?", placeholder="Ej: Breaking Bad, El Conjuro...")

# ── Colores por género dominante ──────────────
GENRE_COLORS = {
    'Horror':     ('bg:#EEEDFE', 'color:#3C3489'),
    'Romance':    ('bg:#FBEAF0', 'color:#72243E'),
    'Action':     ('bg:#E6F1FB', 'color:#0C447C'),
    'Adventure':  ('bg:#E6F1FB', 'color:#0C447C'),
    'Comedy':     ('bg:#FAEEDA', 'color:#633806'),
    'Drama':      ('bg:#F1EFE8', 'color:#444441'),
    'Mystery':    ('bg:#EAF3DE', 'color:#27500A'),
    'Thriller':   ('bg:#EAF3DE', 'color:#27500A'),
    'Sci-Fi':     ('bg:#E6F1FB', 'color:#0C447C'),
    'Fantasy':    ('bg:#EEEDFE', 'color:#3C3489'),
    'Music':      ('bg:#FBEAF0', 'color:#72243E'),
}

def get_badge_style(genre):
    if genre in GENRE_COLORS:
        bg, color = GENRE_COLORS[genre]
        bg_val    = bg.replace('bg:', '')
        color_val = color.replace('color:', '')
        return f"background:{bg_val}; color:{color_val}"
    return "background:#F1EFE8; color:#444441"
GENRE_BG = {
    'Horror':    '#EEEDFE',
    'Romance':   '#FBEAF0',
    'Action':    '#E6F1FB',
    'Adventure': '#E6F1FB',
    'Comedy':    '#FAEEDA',
    'Drama':     '#F1EFE8',
    'Mystery':   '#EAF3DE',
    'Fantasy':   '#EEEDFE',
    'Music':     '#FBEAF0',
    'Sci-Fi':    '#E6F1FB',
    'Thriller':  '#EAF3DE',
}

def get_bg_color(genres):
    for g in genres:
        if g in GENRE_BG:
            return GENRE_BG[g]
    return '#F5F5F5'


def render_carta(anime):
    genres = anime.get('genres_clean', [])
    if isinstance(genres, str):
        import ast
        try:
            genres = ast.literal_eval(genres)
        except:
            genres = [genres]

    title    = anime.get('title', '')
    score    = anime.get('score', 0)
    episodes = anime.get('episodes', '?')
    synopsis = str(anime.get('synopsis', ''))[:120] + '...'
    image    = anime.get('image_url', '')
    mal_id   = anime.get('mal_id', '')
    mal_url  = f"https://myanimelist.net/anime/{mal_id}" if mal_id else '#'
    bg_color = get_bg_color(genres)

    badges = ''
    for g in genres[:2]:
        style = get_badge_style(g)
        badges += f'<span style="font-size:10px; padding:2px 8px; border-radius:20px; {style}; margin-right:4px;">{g}</span>'

    return f"""
    <div style="width:100%; background:#fff; border-radius:16px;
                border:1px solid rgba(0,0,0,0.1); overflow:hidden; font-family:sans-serif;">
      <div style="width:100%; background:{bg_color}; display:flex; align-items:center;
                  justify-content:center; padding:8px 0; min-height:240px;">
        <img src="{image}" style="height:240px; width:auto; object-fit:contain; display:block;"
             onerror="this.src='https://via.placeholder.com/170x240?text=No+image'"/>
      </div>
      <div style="padding:10px 12px 14px;">
        <p style="font-size:13px; font-weight:600; margin:0 0 5px;
                  color:#111; line-height:1.3;">{title}</p>
        <div style="margin-bottom:7px;">{badges}</div>
        <p style="font-size:11px; color:#888; margin:0 0 7px; line-height:1.5;">{synopsis}</p>
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <span style="font-size:11px; color:#888;">⭐ {score} · {episodes} eps</span>
          <a href="{mal_url}" target="_blank"
             style="font-size:10px; color:#534AB7; text-decoration:none;">Ver en MAL →</a>
        </div>
      </div>
    </div>
    """

if query:
    from core.modelo import recomendar_anime

    resultados = df_pelser[df_pelser['título'].str.contains(query, case=False, na=False)]

    if resultados.empty:
        st.warning(f"No encontré '{query}' en la base de datos.")
    else:
        row = resultados.iloc[0]
        st.success(f"Encontrado: **{row['título']}** ({row['year']})")

        with st.spinner("Buscando anime similar..."):
            recomendaciones = recomendar_anime(
                row, df_anime, index_scores, index_embed, k=5
            )

        st.subheader("🎌 Animes recomendados")
        cols = st.columns(5)
        for i, anime in enumerate(recomendaciones):
            with cols[i]:
                st.markdown(render_carta(anime), unsafe_allow_html=True)

st.markdown("---")
st.markdown("© 2026 Fer | Anime Recommender 🔮")
st.markdown("Datos obtenidos de APIs públicas. Uso educativo.")