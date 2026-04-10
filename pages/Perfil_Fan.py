import streamlit as st
from core.data import cargar_datos
from core.modelo import recomendar_anime, preferir_primera_temporada
import ast
import os
import requests
import numpy as np
from dotenv import load_dotenv
import random

load_dotenv()

st.set_page_config(page_title="Perfil de Fan · TobiCross", page_icon="📊", layout="wide")

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

if 'mal_cache' not in st.session_state:
    st.session_state.mal_cache = {}

ARQUETIPOS = {
    'errante': {
        'nombre': 'El Errante Oscuro', 'emoji': '😈', 'nivel': 'Maestro de las Sombras',
        'elemento': '🌑 Oscuridad', 'planeta': '🪐 Saturno', 'poder': '👁️ Ver la verdad',
        'debilidad': '💜 El amor',
        'descripcion': 'Caminas entre sombras con los ojos abiertos. Ves lo que otros evitan. Buscas historias que no teman mostrarte el lado oscuro del mundo — y de las personas.',
        'query': 'Breaking Bad',
    },
    'romantico': {
        'nombre': 'El Soñador Romántico', 'emoji': '🌸', 'nivel': 'Guardián del Corazón',
        'elemento': '🌸 Amor', 'planeta': '♀️ Venus', 'poder': '💞 Sentir todo',
        'debilidad': '🖤 La frialdad',
        'descripcion': 'Tu corazón late más fuerte con la música y el amor. Buscas historias que te recuerden que sentir es vivir — aunque duela.',
        'query': 'Diario de una pasión',
    },
    'guerrero': {
        'nombre': 'El Guerrero del Caos', 'emoji': '⚔️', 'nivel': 'Comandante de Batallas',
        'elemento': '🔥 Fuego', 'planeta': '♂️ Marte', 'poder': '⚡ Ser invencible',
        'debilidad': '😌 La calma',
        'descripcion': 'No naciste para quedarte quieto. Necesitas adrenalina, batallas y héroes que sangran pero no se rinden.',
        'query': 'Los juegos del hambre',
    },
    'filosofo': {
        'nombre': 'El Filósofo del Abismo', 'emoji': '🌀', 'nivel': 'Oráculo del Caos',
        'elemento': '🌌 Éter', 'planeta': '⛢ Urano', 'poder': '🔭 Ver el futuro',
        'debilidad': '😂 La simplicidad',
        'descripcion': 'Las grandes preguntas te persiguen. Buscas anime que te deje pensando días después de verlo — sin respuestas fáciles.',
        'query': 'Stranger Things',
    },
    'libre': {
        'nombre': 'El Alma Libre', 'emoji': '✨', 'nivel': 'Maestro del Presente',
        'elemento': '🌟 Luz', 'planeta': '🪐 Júpiter', 'poder': '😄 Contagiar alegría',
        'debilidad': '🌑 La oscuridad',
        'descripcion': 'Ríes fácil, amas fácil, vives fácil. Tu anime ideal es el que se siente como un abrazo — cálido, ligero y sin pretensiones.',
        'query': 'Friends',
    },
}

STAT_COLORS = {
    'Oscuridad':            '#534AB7',
    'Intensidad emocional': '#534AB7',
    'Tolerancia al caos':   '#534AB7',
    'Romance':              '#D4537E',
    'Feel good':            '#1D9E75',
}

TMDB_GENRE_MAP = {
    28: 'action_score', 12: 'adventure_score', 35: 'comedy_score', 80: 'crime_score',
    99: 'dark_score', 18: 'drama_score', 10751: 'family_score', 14: 'fantasy',
    27: 'horror_score', 10402: 'music_score', 9648: 'thriller_score', 10749: 'romance',
    878: 'scifi', 53: 'thriller_score', 10752: 'action_score',
}

#  MAL API 
def enriquecer_con_mal(mal_id):
    if not MAL_CLIENT_ID or not mal_id:
        return {}
    mal_id = str(mal_id)
    if mal_id in st.session_state.mal_cache:
        return st.session_state.mal_cache[mal_id]
    try:
        url = f"https://api.myanimelist.net/v2/anime/{mal_id}"
        params = {"fields": "id,title,synopsis,genres,mean,num_episodes,studios,main_picture"}
        headers = {"X-MAL-CLIENT-ID": MAL_CLIENT_ID}
        res = requests.get(url, params=params, headers=headers, timeout=5)
        if res.status_code != 200:
            return {}
        data = res.json()
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
def buscar_en_tmdb(titulo):
    if not TMDB_KEY:
        return None
    try:
        url = "https://api.themoviedb.org/3/search/multi"
        params = {"api_key": TMDB_KEY, "query": titulo, "language": "es-MX"}
        res = requests.get(url, params=params, timeout=5)
        data = res.json()
        if not data.get("results"):
            return None
        item = data["results"][0]
        genre_ids = item.get("genre_ids", [])
        row_falso = {
            'título': item.get("title") or item.get("name", titulo),
            'vector_scores': [], 'embedding': [],
        }
        for campo in ['horror_score','crime_score','family_score','adventure_score',
                      'feel_good_score','dark_score','fantasy','romance','scifi',
                      'comedy_score','thriller_score','action_score','drama_score',
                      'music_score','dystopia_score','power_score']:
            row_falso[campo] = 0.0
        for gid in genre_ids:
            campo = TMDB_GENRE_MAP.get(gid)
            if campo:
                row_falso[campo] = min(1.0, row_falso.get(campo, 0) + 0.6)
        row_falso['_tmdb'] = True
        return row_falso
    except:
        return None

def buscar_pelicula(query):
    r = df_pelser[df_pelser['título'].str.contains(query, case=False, na=False)]
    if not r.empty:
        return r.iloc[0]
    return buscar_en_tmdb(query)

def calcular_perfil(rows):
    campos = ['dark_score','crime_score','romance','music_score','action_score',
              'adventure_score','fantasy','scifi','comedy_score','feel_good_score',
              'drama_score','thriller_score','dystopia_score','power_score','horror_score']
    promedios = {}
    for c in campos:
        vals = []
        for r in rows:
            try:
                val = float(r[c]) if c in r else 0.0
            except:
                val = 0.0
            vals.append(val)
        promedios[c] = np.mean(vals)
    return promedios

def detectar_arquetipo(promedios):
    scores = {
        'errante':   promedios['dark_score']     + promedios['crime_score'],
        'romantico': promedios['romance']         + promedios['music_score'],
        'guerrero':  promedios['action_score']    + promedios['adventure_score'],
        'filosofo':  promedios['dystopia_score']  + promedios['thriller_score'],
        'libre':     promedios['feel_good_score'] + promedios['comedy_score'],
    }
    return max(scores, key=scores.get)

def calcular_stats(promedios):
    return {
        'Oscuridad':            int(min((promedios['dark_score']      + promedios['horror_score'])  * 80, 100)),
        'Intensidad emocional': int(min((promedios['drama_score']     + promedios['romance'])       * 60, 100)),
        'Tolerancia al caos':   int(min((promedios['action_score']    + promedios['dystopia_score'])* 70, 100)),
        'Romance':              int(min( promedios['romance']          * 100, 100)),
        'Feel good':            int(min( promedios['feel_good_score']  * 100, 100)),
    }

def build_stats_html(stats):
    html = ''
    for nombre, valor in stats.items():
        color = STAT_COLORS.get(nombre, '#534AB7')
        html += f'<div style="display:flex;justify-content:space-between;font-size:11px;color:#7F77DD;margin-bottom:5px;"><span>{nombre}</span><span style="color:#CECBF6;">{valor}</span></div>'
        html += f'<div style="height:6px;background:rgba(83,74,183,0.2);border-radius:3px;margin-bottom:12px;"><div style="width:{valor}%;height:100%;border-radius:3px;background:{color};"></div></div>'
    return html

def build_guardian_html(guardian):
    if guardian is None:
        return ''
    mal_id = str(guardian.get('mal_id', ''))
    mal    = enriquecer_con_mal(mal_id)

    image    = mal.get('image')    or guardian.get('image_url', '')
    score    = mal.get('score')    or float(guardian.get('score', 0))
    title    = mal.get('title')    or guardian['title']
    episodes = f" · {mal['episodes']} eps" if mal.get('episodes') else ''
    studios  = f"<p style='font-size:10px;color:#7F77DD;margin:2px 0;'>{', '.join(mal['studios'][:2])}</p>" if mal.get('studios') else ''

    genres_g = mal.get('genres') or guardian.get('genres_clean', [])
    if isinstance(genres_g, str):
        try: genres_g = ast.literal_eval(genres_g)
        except: genres_g = []
    genres_str = ', '.join(genres_g[:2]) if genres_g else ''

    return (
        f'<div style="background:rgba(83,74,183,0.1);border-radius:10px;padding:14px;border:1px solid #2A2550;margin-top:16px;">'
        f'<p style="font-size:10px;color:#534AB7;letter-spacing:2px;margin-bottom:10px;">ANIME GUARDIÁN</p>'
        f'<div style="display:flex;align-items:center;gap:12px;">'
        f'<img src="{image}" style="width:60px;height:60px;border-radius:10px;object-fit:cover;flex-shrink:0;"/>'
        f'<div>'
        f'<p style="font-size:14px;font-weight:600;color:#CECBF6;margin-bottom:2px;">{title}</p>'
        f'<p style="font-size:11px;color:#7F77DD;margin:0;">Tu espejo en otro universo</p>'
        f'{studios}'
        f'<p style="font-size:10px;color:#534AB7;margin:3px 0;">⭐ {score:.1f} · {genres_str}{episodes}</p>'
        f'<a href="https://myanimelist.net/anime/{mal_id}" target="_blank" '
        f'style="font-size:10px;color:#7F77DD;text-decoration:none;">Ver en MAL →</a>'
        f'</div></div></div>'
    )


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
      <p style="font-size:11px; color:#7F77DD; letter-spacing:3px; margin:0 0 8px; font-weight:500;">PERFIL DE FAN</p>
      <p style="font-size:60px; font-weight:700; margin:0 0 8px;">📊 Perfil de Fan</p>
      <p style="font-size:16px; color:#888; margin:0;">Descubre tu arquetipo animero</p>
    </div>
    """, unsafe_allow_html=True)

#  CONTENIDO 
_, col, _ = st.columns([1, 3, 1])
with col:
    st.markdown('<p style="font-size:13px;color:#7F77DD;letter-spacing:2px;margin-bottom:8px;font-weight:500;">TUS PELÍCULAS FAVORITAS</p>', unsafe_allow_html=True)

    peliculas = []
    for i in range(5):
        p = st.text_input("", placeholder=f"Película {i+1}...", label_visibility="collapsed", key=f"perfil_p{i}")
        if p:
            peliculas.append(p)

    st.markdown("")
    generar = st.button("✨ Revelar mi perfil animero", use_container_width=True)

    if generar:
        if len(peliculas) < 3:
            st.warning("Ingresa al menos 3 películas para generar tu perfil.")
        else:
            rows = []
            no_encontradas = []
            for p in peliculas:
                row = buscar_pelicula(p)
                if row is None:
                    no_encontradas.append(p)
                else:
                    rows.append(row)

            if no_encontradas:
                st.warning(f"No encontré: {', '.join(no_encontradas)}")

            if len(rows) < 2:
                st.error("Necesito encontrar al menos 2 películas para calcular tu perfil.")
            else:
                with st.spinner("✨ Calculando tu arquetipo..."):
                    promedios = calcular_perfil(rows)
                    arq_key   = detectar_arquetipo(promedios)
                    arq       = ARQUETIPOS[arq_key]
                    stats     = calcular_stats(promedios)

                    guardian = None
                    r_query  = df_pelser[df_pelser['título'].str.contains(arq['query'], case=False, na=False)]
                    if not r_query.empty:
                        recs     = recomendar_anime(r_query.iloc[0], df_anime, index_scores, index_embed, k=10)
                        random.shuffle(recs)
                        guardian = preferir_primera_temporada(recs)     

                nivel         = int(min(sum(stats.values()) / len(stats), 99))
                stats_html    = build_stats_html(stats)
                guardian_html = build_guardian_html(guardian)

                st.markdown(
                    f'<div style="background:#0D0B1A;border-radius:20px;padding:28px;border:1px solid #2A2550;margin-top:1rem;">'
                    f'<p style="font-size:10px;color:#534AB7;letter-spacing:3px;text-align:center;margin-bottom:20px;">PERFIL ANIMERO</p>'
                    f'<div style="text-align:center;margin-bottom:24px;">'
                    f'<div style="font-size:52px;margin-bottom:10px;">{arq["emoji"]}</div>'
                    f'<p style="font-size:26px;font-weight:700;color:#CECBF6;margin-bottom:4px;">{arq["nombre"]}</p>'
                    f'<p style="font-size:12px;color:#534AB7;font-style:italic;">{arq["nivel"]} · Nivel {nivel}</p>'
                    f'</div>'
                    f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:20px;">'
                    f'<div style="background:rgba(83,74,183,0.15);border-radius:10px;padding:12px;text-align:center;border:1px solid #2A2550;"><p style="font-size:10px;color:#534AB7;margin-bottom:4px;letter-spacing:1px;">ELEMENTO</p><p style="font-size:15px;color:#CECBF6;font-weight:600;">{arq["elemento"]}</p></div>'
                    f'<div style="background:rgba(83,74,183,0.15);border-radius:10px;padding:12px;text-align:center;border:1px solid #2A2550;"><p style="font-size:10px;color:#534AB7;margin-bottom:4px;letter-spacing:1px;">PLANETA</p><p style="font-size:15px;color:#CECBF6;font-weight:600;">{arq["planeta"]}</p></div>'
                    f'<div style="background:rgba(83,74,183,0.15);border-radius:10px;padding:12px;text-align:center;border:1px solid #2A2550;"><p style="font-size:10px;color:#534AB7;margin-bottom:4px;letter-spacing:1px;">PODER</p><p style="font-size:15px;color:#CECBF6;font-weight:600;">{arq["poder"]}</p></div>'
                    f'<div style="background:rgba(83,74,183,0.15);border-radius:10px;padding:12px;text-align:center;border:1px solid #2A2550;"><p style="font-size:10px;color:#534AB7;margin-bottom:4px;letter-spacing:1px;">DEBILIDAD</p><p style="font-size:15px;color:#CECBF6;font-weight:600;">{arq["debilidad"]}</p></div>'
                    f'</div>'
                    f'<div style="margin-bottom:20px;"><p style="font-size:10px;color:#534AB7;letter-spacing:2px;margin-bottom:12px;">ESTADÍSTICAS</p>{stats_html}</div>'
                    f'<div style="background:rgba(83,74,183,0.1);border-radius:10px;padding:14px;border:1px solid #2A2550;">'
                    f'<p style="font-size:12px;color:#AFA9EC;line-height:1.7;font-style:italic;">"{arq["descripcion"]}"</p>'
                    f'</div>'
                    f'{guardian_html}'
                    f'</div>',
                    unsafe_allow_html=True
                )
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