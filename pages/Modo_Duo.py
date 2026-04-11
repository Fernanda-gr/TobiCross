import streamlit as st
from core.data import cargar_datos
from core.modelo import recomendar_anime, get_primera_temporada, _idx_posicional
import ast
import os
import requests
import numpy as np
from collections import defaultdict
import faiss
from dotenv import load_dotenv
from openai import OpenAI
import random

load_dotenv()

st.set_page_config(page_title="Modo Dúo · TobiCross", page_icon="👥", layout="wide")

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

#  MAL API 
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

#  TMDB 
TMDB_GENRE_MAP = {
    28: 'action_score', 12: 'adventure_score', 16: 'feel_good_score',
    35: 'comedy_score', 80: 'crime_score', 99: 'dark_score',
    18: 'drama_score', 10751: 'family_score', 14: 'fantasy',
    36: 'dark_score', 27: 'horror_score', 10402: 'music_score',
    9648: 'thriller_score', 10749: 'romance', 878: 'scifi',
    53: 'thriller_score', 10752: 'action_score', 37: 'adventure_score',
}

def buscar_en_tmdb(titulo):
    if not TMDB_KEY:
        return None
    try:
        url    = "https://api.themoviedb.org/3/search/multi"
        params = {"api_key": TMDB_KEY, "query": titulo, "language": "es-MX"}
        res    = requests.get(url, params=params, timeout=5)
        data   = res.json()
        if not data.get("results"):
            return None
        item      = data["results"][0]
        genre_ids = item.get("genre_ids", [])
        row_falso = {
            'título': item.get("title") or item.get("name", titulo),
            'vector_scores': [], 'embedding': [],
        }
        for campo in ['horror_score','crime_score','family_score','adventure_score',
                      'feel_good_score','dark_score','fantasy','romance','scifi',
                      'comedy_score','thriller_score','action_score','drama_score',
                      'music_score','dystopia_score']:
            row_falso[campo] = 0.0
        for gid in genre_ids:
            campo = TMDB_GENRE_MAP.get(gid)
            if campo:
                row_falso[campo] = min(1.0, row_falso.get(campo, 0) + 0.6)
        row_falso['_tmdb'] = True
        row_falso['_nombre_tmdb'] = row_falso['título']
        return row_falso
    except:
        return None

def get_rrf_desde_scores(row_falso, k=60, top=200):
    campos = ['horror_score','crime_score','family_score','adventure_score',
              'feel_good_score','dark_score','fantasy','romance','scifi',
              'comedy_score','thriller_score','action_score','drama_score']
    scores      = np.array([float(row_falso.get(c, 0)) for c in campos], dtype='float32')
    scores_norm = scores / (np.linalg.norm(scores) + 1e-9)
    rrf = defaultdict(float)
    for idx in range(len(df_anime)):
        anime   = df_anime.iloc[idx]
        av      = np.array([float(anime.get(c, 0)) for c in campos], dtype='float32')
        av_norm = av / (np.linalg.norm(av) + 1e-9)
        rrf[idx] = float(np.dot(scores_norm, av_norm))
    return dict(sorted(rrf.items(), key=lambda x: x[1], reverse=True)[:top])

def detectar_arquetipo(row):
    scores = {
        'errante':   float(row.get('dark_score', 0))     + float(row.get('crime_score', 0)),
        'romantico': float(row.get('romance', 0))         + float(row.get('music_score', 0)),
        'guerrero':  float(row.get('action_score', 0))    + float(row.get('adventure_score', 0)),
        'filosofo':  float(row.get('dystopia_score', 0))  + float(row.get('thriller_score', 0)),
        'libre':     float(row.get('feel_good_score', 0)) + float(row.get('comedy_score', 0)),
    }
    return max(scores, key=scores.get)

ARQUETIPOS = {
    'errante':   {'emoji': '😈', 'nombre': 'El Errante Oscuro',      'color': '#534AB7', 'bg': '#EEEDFE'},
    'romantico': {'emoji': '🌸', 'nombre': 'El Soñador Romántico',   'color': '#993556', 'bg': '#FBEAF0'},
    'guerrero':  {'emoji': '⚔️', 'nombre': 'El Guerrero del Caos',  'color': '#185FA5', 'bg': '#E6F1FB'},
    'filosofo':  {'emoji': '🌀', 'nombre': 'El Filósofo del Abismo', 'color': '#0F6E56', 'bg': '#E1F5EE'},
    'libre':     {'emoji': '✨', 'nombre': 'El Alma Libre',           'color': '#854F0B', 'bg': '#FAEEDA'},
}

MENSAJES_COMPAT = {
    (90, 100): "¡Son almas gemelas animeras! El universo los tenía planeados. 💫",
    (70,  89): "Comparten el amor por historias intensas con corazón. Raro pero poderoso. 🔥",
    (50,  69): "Gustos distintos pero complementarios. Van a descubrir algo nuevo juntos. 🌊",
    (30,  49): "Mundos opuestos que se atraen. Este anime los va a sorprender a los dos. ⚡",
    ( 0,  29): "Son de galaxias diferentes... pero eso hace la recomendación más interesante. 🌌",
}

def get_mensaje(pct):
    for (lo, hi), msg in MENSAJES_COMPAT.items():
        if lo <= pct <= hi:
            return msg
    return ""

def calcular_compatibilidad(row1, row2):
    campos = ['horror_score','crime_score','family_score','adventure_score',
              'feel_good_score','dark_score','fantasy','romance','scifi',
              'comedy_score','thriller_score','action_score','drama_score']
    v1 = np.array([float(row1.get(s, 0)) for s in campos])
    v2 = np.array([float(row2.get(s, 0)) for s in campos])
    n1, n2 = np.linalg.norm(v1), np.linalg.norm(v2)
    if n1 == 0 or n2 == 0:
        return 50
    return int(np.dot(v1, v2) / (n1 * n2) * 100)

def get_rrf(row, k=60, top=200):
    if row.get('_tmdb'):
        return get_rrf_desde_scores(row, k, top)
    vec_s = np.array(row['vector_scores'], dtype='float32').reshape(1, -1)
    faiss.normalize_L2(vec_s)
    vec_e = np.array(row['embedding'], dtype='float32').reshape(1, -1)
    faiss.normalize_L2(vec_e)
    _, is_ = index_scores.search(vec_s, top)
    _, ie_ = index_embed.search(vec_e, top)
    rrf = defaultdict(float)
    for rank, idx in enumerate(is_[0]):
        rrf[idx] += 0.5 / (k + rank + 1)
    for rank, idx in enumerate(ie_[0]):
        rrf[idx] += 0.5 / (k + rank + 1)
    return rrf

def scores_dominantes(row, umbral=0.3):
    campos = ['fantasy','romance','adventure_score','feel_good_score',
              'dark_score','drama_score','horror_score','action_score',
              'comedy_score','music_score','scifi']
    return {c for c in campos if float(row.get(c, 0)) > umbral}

def fusionar(rrf1, rrf2, row1, row2):
    dom1 = scores_dominantes(row1)
    dom2 = scores_dominantes(row2)
    fusion = defaultdict(float)
    for idx in set(rrf1) | set(rrf2):
        anime  = df_anime.iloc[idx]
        base   = rrf1.get(idx, 0) + rrf2.get(idx, 0)
        bonus1 = sum(float(anime.get(s, 0)) for s in dom1) / max(len(dom1), 1)
        bonus2 = sum(float(anime.get(s, 0)) for s in dom2) / max(len(dom2), 1)
        fusion[idx] = base + bonus1 * 0.3 + bonus2 * 0.3
    return sorted(fusion.keys(), key=lambda x: fusion[x], reverse=True)

def get_badge_style(genre):
    GENRE_COLORS = {
        'Horror':   ('background:#EEEDFE', 'color:#3C3489'),
        'Romance':  ('background:#FBEAF0', 'color:#72243E'),
        'Action':   ('background:#E6F1FB', 'color:#0C447C'),
        'Drama':    ('background:#F1EFE8', 'color:#444441'),
        'Mystery':  ('background:#EAF3DE', 'color:#27500A'),
        'Thriller': ('background:#EAF3DE', 'color:#27500A'),
        'Comedy':   ('background:#FAEEDA', 'color:#633806'),
        'Fantasy':  ('background:#EEEDFE', 'color:#3C3489'),
        'Music':    ('background:#FBEAF0', 'color:#72243E'),
        'Sci-Fi':   ('background:#E6F1FB', 'color:#0C447C'),
    }
    if genre in GENRE_COLORS:
        bg, color = GENRE_COLORS[genre]
        return f"{bg}; {color}"
    return "background:#F1EFE8; color:#444441"

def buscar_pelicula(query):
    r = df_pelser[df_pelser['título'].str.contains(query, case=False, na=False)]
    if not r.empty:
        return r.iloc[0], None
    tmdb = buscar_en_tmdb(query)
    if tmdb:
        return tmdb, None
    return None, f"No encontré '{query}' en ninguna parte."


#  HEADER 
col_back, col_title, _ = st.columns([1, 5, 1])
with col_back:
    st.markdown("<div style='padding-top:36px'>", unsafe_allow_html=True)
    if st.button("← Inicio", key="btn_inicio"):
        st.switch_page("main.py")
    st.markdown("</div>", unsafe_allow_html=True)
with col_title:
    st.markdown("""
    <div style="text-align:center; margin-bottom:2rem;">
      <p style="font-size:11px; color:#7F77DD; letter-spacing:3px; margin:0 0 8px; font-weight:500;">MODO DÚO</p>
      <p style="font-size:clamp(32px, 6vw, 60px); font-weight:700; margin:0 0 8px;">👥 Modo Dúo</p>
      <p style="font-size:clamp(13px, 2vw, 16px); color:#888; margin:0;">Cada uno elige su película-serie favorita y el universo hace el resto</p>
    </div>
    """, unsafe_allow_html=True)

#  CONTENIDO 
_, col, _ = st.columns([1, 4, 1])
with col:
    col1, colv, col2 = st.columns([5, 1, 5])
    with col1:
        st.markdown('<p style="font-size:11px; font-weight:500; color:#534AB7; letter-spacing:2px; margin:0 0 4px;">PERSONA 1</p>', unsafe_allow_html=True)
        q1 = st.text_input("", placeholder="Tu película-serie favorita...", key="duo_q1", label_visibility="collapsed")
    with colv:
        st.markdown('<div style="display:flex; align-items:center; justify-content:center; height:100%; padding-top:20px;"><div style="width:40px;height:40px;border-radius:50%;background:#EEEDFE;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:600;color:#534AB7;">VS</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<p style="font-size:11px; font-weight:500; color:#993556; letter-spacing:2px; margin:0 0 4px;">PERSONA 2</p>', unsafe_allow_html=True)
        q2 = st.text_input("", placeholder="Tu película-serie favorita...", key="duo_q2", label_visibility="collapsed")

    st.markdown("")
    buscar = st.button("✨ Encontrar su anime en común", use_container_width=True)

    if buscar and q1 and q2:
        row1, msg1 = buscar_pelicula(q1)
        row2, msg2 = buscar_pelicula(q2)

        if row1 is None:
            st.warning(msg1)
        elif row2 is None:
            st.warning(msg2)
        else:
            arq1  = detectar_arquetipo(row1)
            arq2  = detectar_arquetipo(row2)
            info1 = ARQUETIPOS[arq1]
            info2 = ARQUETIPOS[arq2]

            c1, _, c2 = st.columns([5, 1, 5])
            with c1:
                st.markdown(f"""
                <div style="background:{info1['bg']}; border-radius:12px; padding:12px 14px;
                            display:flex; align-items:center; gap:10px; margin-top:8px;">
                  <span style="font-size:20px;">{info1['emoji']}</span>
                  <div>
                    <p style="font-size:10px; color:{info1['color']}; margin:0; font-weight:500;">{row1['título'][:28]}</p>
                    <p style="font-size:13px; font-weight:600; color:{info1['color']}; margin:0;">{info1['nombre']}</p>
                  </div>
                </div>
                """, unsafe_allow_html=True)
            with c2:
                st.markdown(f"""
                <div style="background:{info2['bg']}; border-radius:12px; padding:12px 14px;
                            display:flex; align-items:center; gap:10px; margin-top:8px;">
                  <span style="font-size:20px;">{info2['emoji']}</span>
                  <div>
                    <p style="font-size:10px; color:{info2['color']}; margin:0; font-weight:500;">{row2['título'][:28]}</p>
                    <p style="font-size:13px; font-weight:600; color:{info2['color']}; margin:0;">{info2['nombre']}</p>
                  </div>
                </div>
                """, unsafe_allow_html=True)

            pct     = calcular_compatibilidad(row1, row2)
            mensaje = get_mensaje(pct)

            st.markdown(f"""
            <div style="background:#f8f8f8; border-radius:12px; padding:20px; margin:1.5rem 0;">
              <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                <span style="font-size:14px; font-weight:600; color:#111;">Compatibilidad animera</span>
                <span style="font-size:26px; font-weight:700; color:{info1['color']};">{pct}%</span>
              </div>
              <div style="height:8px; background:#eee; border-radius:4px; margin-bottom:10px;">
                <div style="width:{pct}%; height:100%;
                            background:linear-gradient(90deg, {info1['color']}, {info2['color']});
                            border-radius:4px;"></div>
              </div>
              <p style="font-size:13px; color:#888; margin:0;">{mensaje}</p>
            </div>
            """, unsafe_allow_html=True)

            with st.spinner("🎌 Fusionando universos..."):
                rrf1    = get_rrf(row1)
                rrf2    = get_rrf(row2)
                top_idx = fusionar(rrf1, rrf2, row1, row2)
                top_idx = list(top_idx)
                pool    = top_idx[:20]
                random.shuffle(pool)
                top_idx = pool + top_idx[20:]

            st.markdown('<p style="font-size:16px; font-weight:600; margin:1rem 0 12px;">🎌 Anime que los une</p>', unsafe_allow_html=True)

            from core.scoring import limpiar_titulo_base
            vistos  = set()
            mostrar = []
            for idx in top_idx:
                anime = df_anime.iloc[idx]
                base  = limpiar_titulo_base(anime['title'])
                if base not in vistos:
                    vistos.add(base)
                    primera = get_primera_temporada(anime['title'], df_anime)
                    if primera is not None:
                        idx_p = _idx_posicional(df_anime, primera['title'])
                        mostrar.append(idx_p if idx_p is not None else idx)
                    else:
                        mostrar.append(idx)
                if len(mostrar) >= 3:
                    break

            cols = st.columns(3)
            for i, idx in enumerate(mostrar):
                anime  = df_anime.iloc[idx]
                mal_id = str(anime.get('mal_id', ''))
                mal    = enriquecer_con_mal(mal_id)

                # Datos enriquecidos con MAL
                title    = mal.get('title')    or anime['title']
                image    = mal.get('image')    or anime.get('image_url', '')
                score    = mal.get('score')    or float(anime.get('score', 0))
                episodes = f" · {mal['episodes']} eps" if mal.get('episodes') else ''
                studios  = ', '.join(mal['studios'][:2]) if mal.get('studios') else ''
                genres   = mal.get('genres') or anime.get('genres_clean', [])

                if isinstance(genres, str):
                    try:    genres = ast.literal_eval(genres)
                    except: genres = [genres]

                badges = ''.join([
                    f'<span style="font-size:10px; padding:2px 8px; border-radius:20px; {get_badge_style(g)}; margin-right:4px;">{g}</span>'
                    for g in genres[:2]
                ])

                with st.spinner(""):
                    prompt = f"""En máximo 2 oraciones cortas y con el estilo poético de YOMI,
                    explica por qué '{title}' conecta con alguien que amó '{row1['título']}'
                    y '{row2['título']}'. Sin saludos, directo a la explicación."""
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
                    st.markdown(f"""
                    <div style="border-radius:14px; border:1px solid #eee; overflow:hidden;">
                      <div style="background:#f5f3ff; height:180px; display:flex;
                                  align-items:center; justify-content:center;">
                        <img src="{image}" style="height:170px; width:auto; object-fit:contain;"/>
                      </div>
                      <div style="padding:12px;">
                        <p style="font-size:13px; font-weight:600; margin:0 0 4px;
                                  color:#111; line-height:1.3;">{title}</p>
                        <div style="margin-bottom:4px;">{badges}</div>
                        <p style="font-size:11px; color:#888; margin:0;">⭐ {score:.1f}{episodes}</p>
                        {f'<p style="font-size:10px;color:#aaa;margin:2px 0;">{studios}</p>' if studios else ''}
                        <p style="font-size:11px; color:#534AB7; font-style:italic;
                                  margin-top:8px; line-height:1.5;">{explicacion}</p>
                        <a href="https://myanimelist.net/anime/{mal_id}"
                           target="_blank"
                           style="font-size:12px; color:#534AB7; text-decoration:none; display:block; margin-top:6px;">
                           Ver en MAL →
                        </a>
                      </div>
                    </div>
                    """, unsafe_allow_html=True)

st.markdown("""
<style>
/* Ocultar sidebar y botón de abrir sidebar */
[data-testid="stSidebar"] {
    display: none !important;
}
[data-testid="collapsedControl"] {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)