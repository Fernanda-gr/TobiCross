import streamlit as st
from core.data import cargar_datos
from core.modelo import recomendar_anime
from core.tmdb_vector import construir_vector_desde_tmdb
from openai import OpenAI
import ast
import os
import requests
import numpy as np
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Recomendador · TobiCross", page_icon="🎯", layout="wide")

st.markdown("""
<style>
.block-container {
    padding-top: 2rem !important;
    padding-bottom: 2rem !important;
}
</style>
""", unsafe_allow_html=True)

df_anime, df_pelser, index_scores, index_embed, modelo_embed = cargar_datos()

TMDB_KEY      = os.getenv("TMDB_API_KEY")
MAL_CLIENT_ID = os.getenv("MAL_CLIENT_ID")
client        = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

if 'mal_cache' not in st.session_state:
    st.session_state.mal_cache = {}

# ─── MAL API ──────────────────────────────────────────────────────────────────
def enriquecer_con_mal(mal_id):
    if not MAL_CLIENT_ID or not mal_id:
        return {}
    mal_id = str(mal_id)
    if mal_id in st.session_state.mal_cache:
        return st.session_state.mal_cache[mal_id]
    try:
        url     = f"https://api.myanimelist.net/v2/anime/{mal_id}"
        params  = {"fields": "id,title,synopsis,genres,mean,num_episodes,studios,main_picture"}
        headers = {"X-MAL-CLIENT-ID": MAL_CLIENT_ID}
        res     = requests.get(url, params=params, headers=headers, timeout=5)
        if res.status_code != 200:
            return {}
        data   = res.json()
        result = {
            'title':    data.get('title', ''),
            'synopsis': data.get('synopsis', ''),
            'score':    data.get('mean', 0),
            'episodes': data.get('num_episodes', 0),
            'image':    data.get('main_picture', {}).get('large', ''),
            'studios':  [s['name'] for s in data.get('studios', [])],
            'genres':   [g['name'] for g in data.get('genres', [])],
        }
        st.session_state.mal_cache[mal_id] = result
        return result
    except:
        return {}

# ─── TMDB ─────────────────────────────────────────────────────────────────────
TMDB_GENRE_MAP = {
    28:    'Action',    12: 'Adventure', 16: 'Animation', 35: 'Comedy',
    80:    'Crime',     18: 'Drama',  10751: 'Kids',       14: 'Fantasy',
    36:    'Historical',27: 'Horror', 10402: 'Music',    9648: 'Mystery',
    10749: 'Romance',  878: 'Sci-Fi',   53: 'Suspense', 10752: 'Military',
}

def buscar_en_tmdb(titulo):
    if not TMDB_KEY:
        return None
    try:
        url    = "https://api.themoviedb.org/3/search/multi"
        params = {"api_key": TMDB_KEY, "query": titulo}
        res    = requests.get(url, params=params, timeout=5)
        data   = res.json()
        if not data.get("results"):
            return None
        item      = data["results"][0]
        genre_ids = item.get("genre_ids", [])
        genres    = [TMDB_GENRE_MAP[gid] for gid in genre_ids if gid in TMDB_GENRE_MAP]
        if not genres:
            genres = ['Drama']
        sinopsis = item.get("overview", "")

        row_falso = {
            'título':        item.get("title") or item.get("name", titulo),
            'year':          item.get("release_date", "")[:4],
            'genres_clean':  genres,
            'sinopsis':      sinopsis,
            'vector_scores': [],
            'embedding':     [],
            '_tmdb':         True,
        }

        score_map = {
            'Horror': 'horror_score', 'Crime': 'crime_score', 'Kids': 'family_score',
            'Adventure': 'adventure_score', 'Comedy': 'comedy_score', 'Drama': 'drama_score',
            'Fantasy': 'fantasy', 'Romance': 'romance', 'Sci-Fi': 'scifi',
            'Suspense': 'thriller_score', 'Action': 'action_score', 'Music': 'music_score',
            'Mystery': 'thriller_score', 'Military': 'action_score',
        }
        for campo in score_map.values():
            row_falso[campo] = 0.0
        for campo in ['dark_score', 'feel_good_score', 'dystopia_score', 'power_score', 'meta_score']:
            row_falso[campo] = 0.0
        for g in genres:
            if g in score_map:
                row_falso[score_map[g]] = min(1.0, row_falso.get(score_map[g], 0) + 0.6)

        if row_falso.get('romance', 0) > 0.3 and 'Action' not in genres:
            row_falso['action_score'] = 0.0
            row_falso['adventure_score'] = max(0.0, row_falso.get('adventure_score', 0) - 0.3)

        row_falso['vector_scores'] = construir_vector_desde_tmdb(row_falso, modelo_embed)
        row_falso['embedding']     = modelo_embed.encode(sinopsis, show_progress_bar=False) if sinopsis else np.zeros(384, dtype='float32')

        return row_falso
    except:
        return None

def buscar_pelicula(query):
    r = df_pelser[df_pelser['título'].str.contains(query, case=False, na=False)]
    if not r.empty:
        return r.iloc[0]
    return buscar_en_tmdb(query)

# ─── COLORES ──────────────────────────────────────────────────────────────────
GENRE_COLORS = {
    'Horror':    ('#EEEDFE', '#3C3489'), 'Romance':   ('#FBEAF0', '#72243E'),
    'Action':    ('#E6F1FB', '#0C447C'), 'Adventure': ('#E6F1FB', '#0C447C'),
    'Comedy':    ('#FAEEDA', '#633806'), 'Drama':     ('#F1EFE8', '#444441'),
    'Mystery':   ('#EAF3DE', '#27500A'), 'Thriller':  ('#EAF3DE', '#27500A'),
    'Sci-Fi':    ('#E6F1FB', '#0C447C'), 'Fantasy':   ('#EEEDFE', '#3C3489'),
    'Music':     ('#FBEAF0', '#72243E'),
}

def get_badge_style(genre):
    if genre in GENRE_COLORS:
        bg, color = GENRE_COLORS[genre]
        return f"background:{bg}; color:{color}"
    return "background:#F1EFE8; color:#444441"

def get_bg_color(genres):
    for g in genres:
        if g in GENRE_COLORS:
            return GENRE_COLORS[g][0]
    return '#F5F5F5'

def render_carta(anime, explicacion=''):
    mal_id = str(anime.get('mal_id', ''))
    mal    = enriquecer_con_mal(mal_id)

    title    = mal.get('title')    or anime.get('title', '')
    image    = mal.get('image')    or anime.get('image_url', '')
    score    = mal.get('score')    or float(anime.get('score', 0))
    episodes = mal.get('episodes') or anime.get('episodes', '?')
    synopsis = (mal.get('synopsis') or str(anime.get('synopsis', '')))[:120] + '...'
    studios  = ', '.join(mal['studios'][:1]) if mal.get('studios') else ''
    genres   = mal.get('genres') or anime.get('genres_clean', [])

    if isinstance(genres, str):
        try: genres = ast.literal_eval(genres)
        except: genres = [genres]

    mal_url  = f"https://myanimelist.net/anime/{mal_id}" if mal_id else '#'
    bg_color = get_bg_color(genres)

    badges = ''.join([
        f'<span style="font-size:10px; padding:2px 8px; border-radius:20px; {get_badge_style(g)}; margin-right:4px;">{g}</span>'
        for g in genres[:2]
    ])

    studios_html     = f'<p style="font-size:10px;color:#aaa;margin:0 0 5px;">{studios}</p>' if studios else ''
    explicacion_html = f'<p style="font-size:11px;color:#534AB7;font-style:italic;margin-top:8px;line-height:1.5;">{explicacion}</p>' if explicacion else ''
    score_str        = f"{score:.1f}" if isinstance(score, float) else str(score)

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
        {studios_html}
        <p style="font-size:11px; color:#888; margin:0 0 7px; line-height:1.5;">{synopsis}</p>
        {explicacion_html}
        <div style="display:flex; justify-content:space-between; align-items:center; margin-top:8px;">
          <span style="font-size:11px; color:#888;">⭐ {score_str} · {episodes} eps</span>
          <a href="{mal_url}" target="_blank"
             style="font-size:10px; color:#534AB7; text-decoration:none;">Ver en MAL →</a>
        </div>
      </div>
    </div>
    """


# ─── HEADER ───────────────────────────────────────────────────────────────────
col_back, col_title, _ = st.columns([1, 5, 1])
with col_back:
    st.markdown("<div style='padding-top:36px'>", unsafe_allow_html=True)
    if st.button("← Inicio", key="btn_inicio"):
        st.switch_page("main.py")
    st.markdown("</div>", unsafe_allow_html=True)
with col_title:
    st.markdown("""
    <div style="text-align:center; margin-bottom:2rem;">
      <p style="font-size:11px; color:#7F77DD; letter-spacing:3px; margin:0 0 8px; font-weight:500;">RECOMENDADOR</p>
      <p style="font-size:60px; font-weight:700; margin:0 0 8px;">🎯 Recomendador</p>
      <p style="font-size:16px; color:#888; margin:0;">Busca tu película favorita y encuentra tu anime perfecto</p>
    </div>
    """, unsafe_allow_html=True)

# ─── BÚSQUEDA ─────────────────────────────────────────────────────────────────
_, col, _ = st.columns([1, 4, 1])
with col:
    col1, col2 = st.columns([5, 1])
    with col1:
        query = st.text_input("", placeholder="¿Qué película o serie te gusta? Ej: Breaking Bad, El Conjuro...",
                              label_visibility="collapsed", key="rec_query")
    with col2:
        buscar = st.button("Buscar →", use_container_width=True)

    if buscar and query:
        row = buscar_pelicula(query)

        if row is None:
            st.warning(f"No encontré '{query}'. Intenta con otro título.")
        else:
            nombre   = row.get('título', query)
            year     = row.get('year', '')
            year_str = f" ({year})" if year else ""

            st.markdown(f"""
            <div style="background:#EEEDFE; border-radius:12px; padding:12px 16px;
                        margin-bottom:1.5rem; display:flex; align-items:center; gap:10px;">
              <span style="font-size:20px;">🎬</span>
              <div>
                <p style="font-size:13px; color:#534AB7; margin:0; font-weight:600;">{nombre}{year_str}</p>
                <p style="font-size:11px; color:#7F77DD; margin:0;">Buscando anime similar...</p>
              </div>
            </div>
            """, unsafe_allow_html=True)

            with st.spinner("🎌 Buscando anime similar..."):
                recomendaciones = recomendar_anime(row, df_anime, index_scores, index_embed, k=5)

            st.markdown('<p style="font-size:16px; font-weight:600; margin:0 0 12px;">🎌 Animes recomendados</p>', unsafe_allow_html=True)

            cols = st.columns(5)
            for i, anime in enumerate(recomendaciones):
                mal_id = str(anime.get('mal_id', ''))
                mal    = enriquecer_con_mal(mal_id)
                title  = mal.get('title') or anime.get('title', '')

                with st.spinner(""):
                    prompt = f"""En máximo 2 oraciones cortas con el estilo poético de YOMI,
                    explica por qué '{title}' conecta con alguien que amó '{nombre}'.
                    Sin saludos, directo a la explicación."""
                    resp = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "Eres YOMI, hablas con poesía y misterio."},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=80,
                        temperature=0.85,
                    )
                    explicacion = resp.choices[0].message.content

                with cols[i]:
                    st.markdown(render_carta(anime, explicacion), unsafe_allow_html=True)