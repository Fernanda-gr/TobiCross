import streamlit as st
from core.data import cargar_datos
from core.modelo import recomendar_anime, recomendar_desde_anime
import ast
import os
import requests
from dotenv import load_dotenv
import random 
load_dotenv()

st.set_page_config(page_title="Portal · TobiCross", page_icon="🗺️", layout="wide")

st.markdown("""
<style>
.block-container {
    padding-top: 2rem !important;
    padding-bottom: 2rem !important;
}
</style>
""", unsafe_allow_html=True)

df_anime, df_pelser, index_scores, index_embed, modelo_embed = cargar_datos()

TMDB_KEY = os.getenv("TMDB_API_KEY")
MAL_CLIENT_ID = os.getenv("MAL_CLIENT_ID")

#  Session state 
if 'portal_cadena'       not in st.session_state: st.session_state.portal_cadena   = []
if 'portal_opciones'     not in st.session_state: st.session_state.portal_opciones = []
if 'portal_query'        not in st.session_state: st.session_state.portal_query    = ''
if 'portal_frase_inicio' not in st.session_state: st.session_state.portal_frase_inicio = None
if 'portal_color_inicio' not in st.session_state: st.session_state.portal_color_inicio = None
if 'mal_cache'           not in st.session_state: st.session_state.mal_cache = {}

GENRE_COLORS = {
    'Horror':    {'bg':'#EEEDFE','color':'#3C3489'},
    'Crime':     {'bg':'#EEEDFE','color':'#3C3489'},
    'Romance':   {'bg':'#FBEAF0','color':'#72243E'},
    'Music':     {'bg':'#FBEAF0','color':'#72243E'},
    'Action':    {'bg':'#E6F1FB','color':'#0C447C'},
    'Fantasy':   {'bg':'#EEEDFE','color':'#3C3489'},
    'Sci-Fi':    {'bg':'#E6F1FB','color':'#0C447C'},
    'Comedy':    {'bg':'#FAEEDA','color':'#633806'},
    'Drama':     {'bg':'#F1EFE8','color':'#444441'},
    'Mystery':   {'bg':'#EAF3DE','color':'#27500A'},
    'Thriller':  {'bg':'#EAF3DE','color':'#27500A'},
    'Sports':    {'bg':'#E6F1FB','color':'#0C447C'},
    'Adventure': {'bg':'#E6F1FB','color':'#0C447C'},
    'Family':    {'bg':'#FAEEDA','color':'#633806'},
}

CONEXIONES = {
    'Horror': 'terror & oscuridad', 'Crime': 'crimen & poder',
    'Romance': 'amor & sentimientos', 'Music': 'música & alma',
    'Action': 'acción & adrenalina', 'Fantasy': 'magia & mundos',
    'Sci-Fi': 'futuro & ciencia', 'Comedy': 'humor & vida',
    'Drama': 'drama & emoción', 'Mystery': 'misterio & verdad',
    'Thriller': 'tensión & suspenso', 'Sports': 'deporte & superación',
    'Adventure': 'aventura & exploración', 'Family': 'calidez & familia',
}

FRASES_INICIO = {
    'Horror': '🌑 Adéntrate en las sombras. Lo que está por venir no es para todos.',
    'Crime': '🔪 El crimen tiene sus propias reglas. Estás a punto de aprenderlas.',
    'Romance': '🌸 Adéntrate en un mundo donde el amor lo cambia todo.',
    'Music': '🎵 La música está a punto de contarte una historia que no olvidarás.',
    'Action': '⚔️ Prepárate. Aquí no hay tiempo para el descanso.',
    'Fantasy': '🏰 Las puertas de otro mundo están abiertas. Solo tienes que cruzarlas.',
    'Sci-Fi': '🌌 El futuro te espera. No todas las respuestas son reconfortantes.',
    'Comedy': '✨ Deja ir todo por un momento. Es hora de reír.',
    'Drama': '🌊 Lo que estás a punto de sentir no tiene nombre. Solo se vive.',
    'Mystery': '🔭 Alguien sabe la verdad. Tendrás que encontrarlo.',
    'Thriller': '🕵️ La tensión ya empezó. Aunque todavía no lo sabes.',
    'Sports': '🏆 El esfuerzo tiene su recompensa. Pero primero hay que sudar.',
    'Adventure': '🗺️ El camino no tiene mapa. Esa es la mejor parte.',
    'Family': '🌟 Algunas historias calientan el alma. Esta es una de ellas.',
}

FRASES_PORTAL = {
    'Horror': '🌑 Estás entrando a las sombras. No todo lo que encuentres querrá ser visto.',
    'Crime': '🔪 El poder corrompe. La lealtad se compra. Bienvenido al lado oscuro.',
    'Romance': '🌸 El corazón tiene sus propias reglas. Prepárate para sentir.',
    'Music': '🎵 Donde las palabras fallan, la música habla. Escucha con el alma.',
    'Action': '⚔️ No hay tiempo para dudar. Solo sobreviven los que se mueven primero.',
    'Fantasy': '🏰 Las reglas del mundo real ya no aplican aquí. Todo es posible.',
    'Sci-Fi': '🌌 La humanidad siempre pregunta qué hay más allá. Estás a punto de descubrirlo.',
    'Comedy': '✨ La vida es demasiado corta para tomarse en serio. Ríe primero, piensa después.',
    'Drama': '🌊 Las emociones más profundas no piden permiso para llegar.',
    'Mystery': '🔭 Cada respuesta esconde una nueva pregunta. ¿Estás listo para buscar?',
    'Thriller': '🕵️ La verdad está ahí. Alguien no quiere que la encuentres.',
    'Sports': '🏆 El límite no es el cuerpo. Es la mente. Rompe el tuyo.',
    'Adventure': '🗺️ Cada paso revela un nuevo horizonte. No mires atrás.',
    'Family': '🌟 Las mejores historias son las que se comparten. Entra.',
}

TMDB_GENRE_MAP = {
    28: 'Action', 12: 'Adventure', 16: 'Comedy', 35: 'Comedy',
    80: 'Crime', 18: 'Drama', 10751: 'Family', 14: 'Fantasy',
    27: 'Horror', 10402: 'Music', 9648: 'Mystery', 10749: 'Romance',
    878: 'Sci-Fi', 53: 'Thriller', 37: 'Adventure',
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
        params = {"fields": "id,title,synopsis,genres,mean,num_episodes,studios,main_picture,status"}
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
            'status':   data.get('status', ''),
            'image':    data.get('main_picture', {}).get('large', ''),
            'genres':   [g['name'] for g in data.get('genres', [])],
            'studios':  [s['name'] for s in data.get('studios', [])],
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
        genres = [TMDB_GENRE_MAP[gid] for gid in genre_ids if gid in TMDB_GENRE_MAP]
        if not genres:
            genres = ['Drama']
        score_map = {
            'Horror': 'horror_score', 'Crime': 'crime_score', 'Family': 'family_score',
            'Adventure': 'adventure_score', 'Comedy': 'comedy_score', 'Drama': 'drama_score',
            'Fantasy': 'fantasy', 'Romance': 'romance', 'Sci-Fi': 'scifi',
            'Thriller': 'thriller_score', 'Action': 'action_score', 'Music': 'music_score',
        }
        row_falso = {
            'título': item.get("title") or item.get("name", titulo),
            'genres_clean': genres, 'vector_scores': [], 'embedding': [],
        }
        for campo in score_map.values():
            row_falso[campo] = 0.0
        for g in genres:
            if g in score_map:
                row_falso[score_map[g]] = min(1.0, row_falso.get(score_map[g], 0) + 0.6)
        for campo in ['dark_score','feel_good_score','dystopia_score','music_score','crime_score']:
            if campo not in row_falso:
                row_falso[campo] = 0.0
        row_falso['_tmdb'] = True
        return row_falso
    except:
        return None

def buscar_pelicula(query):
    r = df_pelser[df_pelser['título'].str.contains(query, case=False, na=False)]
    if not r.empty:
        return r.iloc[0]
    return buscar_en_tmdb(query)

def get_genero_dominante(genres):
    if isinstance(genres, str):
        try: genres = ast.literal_eval(genres)
        except: genres = [genres]
    if hasattr(genres, 'tolist'):
        genres = genres.tolist()
    if not genres:
        return 'Drama'
    ORDEN = ['Horror','Crime','Romance','Music','Action','Fantasy','Sci-Fi',
             'Comedy','Drama','Mystery','Thriller','Sports','Adventure','Family']
    for g in ORDEN:
        if g in genres:
            return g
    return genres[0] if genres else 'Drama'

def anime_to_dict(anime):
    genres = anime.get('genres_clean', [])
    if isinstance(genres, str):
        try: genres = ast.literal_eval(genres)
        except: genres = []
    mal_id = str(anime.get('mal_id', ''))

    # Enriquecer con MAL
    mal = enriquecer_con_mal(mal_id)

    title    = mal.get('title') or anime['title']
    synopsis = mal.get('synopsis') or str(anime.get('synopsis', ''))
    score    = mal.get('score') or float(anime.get('score', 0))
    image    = mal.get('image') or anime.get('image_url', '')
    episodes = mal.get('episodes', 0)
    studios  = ', '.join(mal.get('studios', [])[:2]) if mal.get('studios') else ''
    mal_genres = mal.get('genres', genres)

    genero = get_genero_dominante(mal_genres if mal_genres else genres)
    color  = GENRE_COLORS.get(genero, GENRE_COLORS['Drama'])

    return {
        'title':    title,
        'genres':   ', '.join((mal_genres if mal_genres else genres)[:2]),
        'genero':   genero,
        'image':    image,
        'score':    score,
        'synopsis': synopsis[:160] + '...',
        'mal_id':   mal_id,
        'episodes': episodes,
        'studios':  studios,
        'bg':       color['bg'],
        'color':    color['color'],
        'conexion': CONEXIONES.get(genero, 'conexión narrativa'),
    }

def render_conector():
    st.markdown("""
    <div style="display:flex;flex-direction:column;align-items:center;height:48px;">
      <div style="width:1.5px;flex:1;background:#CECBF6;"></div>
      <div style="width:22px;height:22px;border-radius:50%;background:#EEEDFE;
                  border:1.5px solid #534AB7;display:flex;align-items:center;
                  justify-content:center;font-size:11px;color:#534AB7;flex-shrink:0;">↓</div>
      <div style="width:1.5px;flex:1;background:#CECBF6;"></div>
    </div>
    """, unsafe_allow_html=True)

def render_card(anime, num):
    frase    = FRASES_PORTAL.get(anime['genero'], '🌀 Estás cruzando a otro universo narrativo.')
    episodes = f" · {anime['episodes']} eps" if anime.get('episodes') else ''
    studios  = f"<p style='font-size:11px;color:#aaa;margin:0 0 6px;'>{anime['studios']}</p>" if anime.get('studios') else ''

    st.markdown(f"""
    <div style="border-radius:16px;overflow:hidden;border:1px solid #e8e6f5;">
      <div style="position:relative;width:100%;height:190px;overflow:hidden;">
        <img src="{anime['image']}" style="width:100%;height:100%;object-fit:cover;display:block;"/>
        <div style="position:absolute;top:0;left:0;right:0;bottom:0;
                    background:linear-gradient(to bottom,transparent 35%,rgba(0,0,0,0.82));"></div>
        <div style="position:absolute;top:12px;left:12px;font-size:10px;font-weight:500;
                    padding:3px 10px;border-radius:20px;background:{anime['bg']};color:{anime['color']};">
          {anime['genero']}
        </div>
        <div style="position:absolute;top:12px;right:12px;font-size:11px;color:#fff;font-weight:500;">
          ⭐ {anime['score']:.1f}
        </div>
        <div style="position:absolute;bottom:0;left:0;right:0;padding:10px 14px 14px;">
          <p style="font-size:17px;font-weight:600;color:#fff;margin:0 0 3px;line-height:1.3;">
            {anime['title']}
          </p>
          <span style="font-size:11px;color:rgba(255,255,255,0.6);">{anime['genres']}{episodes}</span>
        </div>
      </div>
      <div style="padding:12px 14px 6px;background:#fff;">
        {studios}
        <p style="font-size:12px;color:#666;line-height:1.6;margin-bottom:8px;">{anime['synopsis']}</p>
        <p style="font-size:10px;color:#aaa;font-style:italic;margin-bottom:10px;">
          Portal {num} — {anime['conexion']}
        </p>
        <a href="https://myanimelist.net/anime/{anime['mal_id']}" target="_blank"
           style="font-size:12px;color:#534AB7;text-decoration:none;">Ver en MAL →</a>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="background:{anime['bg']};border-left:3px solid {anime['color']};
                border-radius:0 8px 8px 0;padding:10px 14px;margin:10px 0;
                font-size:13px;color:{anime['color']};font-style:italic;line-height:1.6;">
      {frase}
    </div>
    """, unsafe_allow_html=True)


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
      <p style="font-size:11px; color:#7F77DD; letter-spacing:3px; margin:0 0 8px; font-weight:500;">PORTAL ENTRE HISTORIAS</p>
      <p style="font-size:clamp(32px, 6vw, 60px); font-weight:700; margin:0 0 8px;">🗺️ Portal entre historias</p>
      <p style="font-size:clamp(13px, 2vw, 16px); color:#888; margin:0;">Busca una pelicula-serie, elige un anime y sigue la cadena</p>
    </div>
    """, unsafe_allow_html=True)

#  CONTENIDO 
_, col, _ = st.columns([1, 3, 1])
with col:
    col1, col2 = st.columns([4, 1])
    with col1:
        query = st.text_input("", placeholder="¿Qué película o serie te gusta?",
                              label_visibility="collapsed", key="portal_input")
    with col2:
        buscar = st.button("Explorar →", use_container_width=True)

    if buscar and query:
        row = buscar_pelicula(query)
        if row is None:
            st.warning(f"No encontré '{query}'")
        else:
            genres_pelser = row.get('genres_clean', [])
            if isinstance(genres_pelser, str):
                try: genres_pelser = ast.literal_eval(genres_pelser)
                except: genres_pelser = []
            genero_inicio = get_genero_dominante(genres_pelser)
            frase_inicio  = FRASES_INICIO.get(genero_inicio, '🌀 Un nuevo universo te espera.')
            color_inicio  = GENRE_COLORS.get(genero_inicio, GENRE_COLORS['Drama'])

            st.session_state.portal_frase_inicio = frase_inicio
            st.session_state.portal_color_inicio = color_inicio

            if row.get('_tmdb'):
                import numpy as np
                campos = ['horror_score','crime_score','family_score','adventure_score',
                          'feel_good_score','dark_score','fantasy','romance','scifi',
                          'comedy_score','thriller_score','action_score','drama_score']
                scores = __import__('numpy').array([float(row.get(c, 0)) for c in campos], dtype='float32')
                import numpy as np
                scores_norm = scores / (np.linalg.norm(scores) + 1e-9)
                sims = []
                for idx in range(len(df_anime)):
                    anime = df_anime.iloc[idx]
                    av = np.array([float(anime.get(c, 0)) for c in campos], dtype='float32')
                    av_norm = av / (np.linalg.norm(av) + 1e-9)
                    sims.append((idx, float(np.dot(scores_norm, av_norm))))
                top = sorted(sims, key=lambda x: x[1], reverse=True)[:4]
                recs = [df_anime.iloc[idx] for idx, _ in top]
            else:
                with st.spinner("🗺️ Abriendo portales..."):
                    recs = recomendar_anime(row, df_anime, index_scores, index_embed, k=4)

            st.session_state.portal_cadena   = []
            st.session_state.portal_opciones = [anime_to_dict(a) for a in recs]
            st.session_state.portal_query    = query

    if st.session_state.portal_frase_inicio and st.session_state.portal_color_inicio:
        fi = st.session_state.portal_frase_inicio
        ci = st.session_state.portal_color_inicio
        st.markdown(f"""
        <div style="background:{ci['bg']};border-left:3px solid {ci['color']};
                    border-radius:0 12px 12px 0;padding:14px 18px;margin:12px 0 20px;
                    font-size:15px;color:{ci['color']};font-style:italic;line-height:1.7;">
          {fi}
        </div>
        """, unsafe_allow_html=True)

    for i, anime in enumerate(st.session_state.portal_cadena):
        render_card(anime, i + 1)
        render_conector()

    if st.session_state.portal_opciones:
        titulos_vistos = {a['title'] for a in st.session_state.portal_cadena}
        opciones = [o for o in st.session_state.portal_opciones if o['title'] not in titulos_vistos]

        st.markdown("""
        <p style="font-size:13px;font-weight:500;color:#534AB7;text-align:center;
                  letter-spacing:1px;margin:12px 0 16px;">¿A cuál portal entras?</p>
        """, unsafe_allow_html=True)

        for opcion in opciones:
            col_card, col_btn = st.columns([5, 1])
            with col_card:
                episodes_str = f" · {opcion['episodes']} eps" if opcion.get('episodes') else ''
                st.markdown(f"""
                <div style="border-radius:16px;overflow:hidden;border:1px solid #e8e6f5;
                            display:flex;gap:0;margin-bottom:4px;">
                  <div style="width:120px;min-width:120px;height:140px;overflow:hidden;flex-shrink:0;">
                    <img src="{opcion['image']}" style="width:100%;height:100%;object-fit:cover;"/>
                  </div>
                  <div style="padding:14px 16px;flex:1;">
                    <span style="font-size:10px;padding:2px 8px;border-radius:20px;
                                 background:{opcion['bg']};color:{opcion['color']};font-weight:500;">
                      {opcion['genero']}
                    </span>
                    <p style="font-size:15px;font-weight:600;color:#111;margin:6px 0 4px;line-height:1.3;">
                      {opcion['title']}
                    </p>
                    <p style="font-size:11px;color:#888;margin:0 0 4px;">⭐ {opcion['score']:.1f} · {opcion['genres']}{episodes_str}</p>
                    {f'<p style="font-size:10px;color:#aaa;margin:0 0 4px;">{opcion["studios"]}</p>' if opcion.get('studios') else ''}
                    <p style="font-size:12px;color:#555;margin:0;line-height:1.5;">
                      {opcion['synopsis'][:90]}...
                    </p>
                    <a href="https://myanimelist.net/anime/{opcion['mal_id']}" target="_blank"
                       style="font-size:11px;color:#534AB7;text-decoration:none;">Ver en MAL →</a>
                  </div>
                </div>
                """, unsafe_allow_html=True)
            with col_btn:
                st.markdown("<div style='padding-top:48px'>", unsafe_allow_html=True)
                if st.button("Entrar →", key=f"opt_{opcion['title']}_{len(st.session_state.portal_cadena)}", use_container_width=True):
                    st.session_state.portal_cadena.append(opcion)
                    matches = df_anime[df_anime['title'] == opcion['title']]
                    if not matches.empty:
                        anime_row = matches.iloc[0]
                        todos     = {a['title'] for a in st.session_state.portal_cadena}
                        with st.spinner("🗺️ Descubriendo nuevos portales..."):
                            nuevos = recomendar_desde_anime(
                                anime_row, df_anime, index_scores, index_embed, k=6
                            )
                        filtrados = [n for n in nuevos if n['title'] not in todos][:4]
                        st.session_state.portal_opciones = [anime_to_dict(n) for n in filtrados]
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.portal_cadena:
        st.markdown("")
        if st.button("🔄 Empezar de nuevo", use_container_width=True, key="btn_reset"):
            st.session_state.portal_cadena       = []
            st.session_state.portal_opciones     = []
            st.session_state.portal_query        = ''
            st.session_state.portal_frase_inicio = None
            st.session_state.portal_color_inicio = None
            st.rerun()

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