import streamlit as st
from core.data import cargar_datos
from core.modelo import recomendar_anime, recomendar_desde_anime
import ast


st.set_page_config(page_title="Portal · TobiCross", page_icon="🗺️", layout="centered")

df_anime, df_pelser, index_scores, index_embed = cargar_datos()

# ── Session state ──────────────────────────────
if 'portal_cadena'       not in st.session_state: st.session_state.portal_cadena   = []
if 'portal_opciones'     not in st.session_state: st.session_state.portal_opciones = []
if 'portal_query'        not in st.session_state: st.session_state.portal_query    = ''
if 'portal_frase_inicio' not in st.session_state: st.session_state.portal_frase_inicio = None
if 'portal_color_inicio' not in st.session_state: st.session_state.portal_color_inicio = None

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
    'Horror':    'terror & oscuridad',
    'Crime':     'crimen & poder',
    'Romance':   'amor & sentimientos',
    'Music':     'música & alma',
    'Action':    'acción & adrenalina',
    'Fantasy':   'magia & mundos',
    'Sci-Fi':    'futuro & ciencia',
    'Comedy':    'humor & vida',
    'Drama':     'drama & emoción',
    'Mystery':   'misterio & verdad',
    'Thriller':  'tensión & suspenso',
    'Sports':    'deporte & superación',
    'Adventure': 'aventura & exploración',
    'Family':    'calidez & familia',
}

FRASES_INICIO = {
    'Horror':    '🌑 Adéntrate en las sombras. Lo que está por venir no es para todos.',
    'Crime':     '🔪 El crimen tiene sus propias reglas. Estás a punto de aprenderlas.',
    'Romance':   '🌸 Adéntrate en un mundo donde el amor lo cambia todo.',
    'Music':     '🎵 La música está a punto de contarte una historia que no olvidarás.',
    'Action':    '⚔️ Prepárate. Aquí no hay tiempo para el descanso.',
    'Fantasy':   '🏰 Las puertas de otro mundo están abiertas. Solo tienes que cruzarlas.',
    'Sci-Fi':    '🌌 El futuro te espera. No todas las respuestas son reconfortantes.',
    'Comedy':    '✨ Deja ir todo por un momento. Es hora de reír.',
    'Drama':     '🌊 Lo que estás a punto de sentir no tiene nombre. Solo se vive.',
    'Mystery':   '🔭 Alguien sabe la verdad. Tendrás que encontrarlo.',
    'Thriller':  '🕵️ La tensión ya empezó. Aunque todavía no lo sabes.',
    'Sports':    '🏆 El esfuerzo tiene su recompensa. Pero primero hay que sudar.',
    'Adventure': '🗺️ El camino no tiene mapa. Esa es la mejor parte.',
    'Family':    '🌟 Algunas historias calientan el alma. Esta es una de ellas.',
}

FRASES_PORTAL = {
    'Horror':    '🌑 Estás entrando a las sombras. No todo lo que encuentres querrá ser visto.',
    'Crime':     '🔪 El poder corrompe. La lealtad se compra. Bienvenido al lado oscuro.',
    'Romance':   '🌸 El corazón tiene sus propias reglas. Prepárate para sentir.',
    'Music':     '🎵 Donde las palabras fallan, la música habla. Escucha con el alma.',
    'Action':    '⚔️ No hay tiempo para dudar. Solo sobreviven los que se mueven primero.',
    'Fantasy':   '🏰 Las reglas del mundo real ya no aplican aquí. Todo es posible.',
    'Sci-Fi':    '🌌 La humanidad siempre pregunta qué hay más allá. Estás a punto de descubrirlo.',
    'Comedy':    '✨ La vida es demasiado corta para tomarse en serio. Ríe primero, piensa después.',
    'Drama':     '🌊 Las emociones más profundas no piden permiso para llegar.',
    'Mystery':   '🔭 Cada respuesta esconde una nueva pregunta. ¿Estás listo para buscar?',
    'Thriller':  '🕵️ La verdad está ahí. Alguien no quiere que la encuentres.',
    'Sports':    '🏆 El límite no es el cuerpo. Es la mente. Rompe el tuyo.',
    'Adventure': '🗺️ Cada paso revela un nuevo horizonte. No mires atrás.',
    'Family':    '🌟 Las mejores historias son las que se comparten. Entra.',
}

def get_genero_dominante(genres):
    if isinstance(genres, str):
        try: genres = ast.literal_eval(genres)
        except: genres = [genres]
    # 🔥 convertir array numpy a lista
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
    genero = get_genero_dominante(genres)
    color  = GENRE_COLORS.get(genero, GENRE_COLORS['Drama'])
    return {
        'title':    anime['title'],
        'genres':   ', '.join(genres[:2]),
        'genero':   genero,
        'image':    anime.get('image_url', ''),
        'score':    float(anime.get('score', 0)),
        'synopsis': str(anime.get('synopsis', ''))[:160] + '...',
        'mal_id':   str(anime.get('mal_id', '')),
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
    frase = FRASES_PORTAL.get(anime['genero'], '🌀 Estás cruzando a otro universo narrativo.')
    st.markdown(f"""
    <div style="border-radius:16px;overflow:hidden;border:1px solid #e8e6f5;">
      <div style="position:relative;width:100%;height:190px;overflow:hidden;">
        <img src="{anime['image']}" style="width:100%;height:100%;object-fit:cover;display:block;"
             onerror="this.src='https://via.placeholder.com/560x190'"/>
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
          <span style="font-size:11px;color:rgba(255,255,255,0.6);">{anime['genres']}</span>
        </div>
      </div>
      <div style="padding:12px 14px 6px;background:#fff;">
        <p style="font-size:12px;color:#666;line-height:1.6;margin-bottom:8px;">{anime['synopsis']}</p>
        <p style="font-size:10px;color:#aaa;font-style:italic;margin-bottom:10px;">
          Portal {num} — {anime['conexion']}
        </p>
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

# ── UI ────────────────────────────────────────
st.markdown("""
<div style="text-align:center; margin-bottom:1.5rem;">
  <p style="font-size:13px; color:#7F77DD; letter-spacing:2px; margin:0 0 4px; font-weight:500;">PORTAL ENTRE HISTORIAS</p>
  <p style="font-size:24px; font-weight:600; margin:0 0 6px;">Explora el multiverso anime</p>
  <p style="font-size:14px; color:#888; margin:0;">Elige un anime y sigue la cadena</p>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([4, 1])
with col1:
    query = st.text_input("", placeholder="¿Qué película o serie te gusta?",
                          label_visibility="collapsed", key="portal_input")
with col2:
    buscar = st.button("Explorar →", use_container_width=True)

if buscar and query:
    resultados = df_pelser[df_pelser['título'].str.contains(query, case=False, na=False)]
    if resultados.empty:
        st.warning(f"No encontré '{query}'")
    else:
        row = resultados.iloc[0]

        genres_pelser = row.get('genres_clean', [])
        if isinstance(genres_pelser, str):
            try: genres_pelser = ast.literal_eval(genres_pelser)
            except: genres_pelser = []
        genero_inicio = get_genero_dominante(genres_pelser)
        frase_inicio  = FRASES_INICIO.get(genero_inicio, '🌀 Un nuevo universo te espera.')
        color_inicio  = GENRE_COLORS.get(genero_inicio, GENRE_COLORS['Drama'])

        st.session_state.portal_frase_inicio = frase_inicio
        st.session_state.portal_color_inicio = color_inicio

        with st.spinner("🗺️ Abriendo portales..."):
            recs = recomendar_anime(row, df_anime, index_scores, index_embed, k=4)

        st.session_state.portal_cadena   = []
        st.session_state.portal_opciones = [anime_to_dict(a) for a in recs]
        st.session_state.portal_query    = query

# ── Frase de inicio ───────────────────────────
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

# ── Cadena elegida ────────────────────────────
for i, anime in enumerate(st.session_state.portal_cadena):
    render_card(anime, i + 1)
    render_conector()

# ── Opciones actuales ─────────────────────────
if st.session_state.portal_opciones:
    titulos_vistos = {a['title'] for a in st.session_state.portal_cadena}
    opciones = [o for o in st.session_state.portal_opciones if o['title'] not in titulos_vistos]

    st.markdown("""
    <p style="font-size:13px;font-weight:500;color:#534AB7;text-align:center;
              letter-spacing:1px;margin:12px 0 16px;">¿A cuál portal entras?</p>
    """, unsafe_allow_html=True)

    for opcion in opciones:
        col_img, col_info, col_btn = st.columns([1, 3, 1])
        with col_img:
            st.image(opcion['image'], use_container_width=True)
        with col_info:
            st.markdown(f"**{opcion['title']}**")
            st.caption(f"⭐ {opcion['score']:.1f} · {opcion['genres']}")
            st.caption(opcion['synopsis'][:80] + '...')
        with col_btn:
            if st.button("Entrar →", key=f"opt_{opcion['title']}_{len(st.session_state.portal_cadena)}"):
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

        st.markdown("<hr style='border:none;border-top:1px solid #f0f0f0;margin:8px 0;'/>",
                    unsafe_allow_html=True)

# ── Reset ─────────────────────────────────────
if st.session_state.portal_cadena:
    st.markdown("")
    if st.button("🔄 Empezar de nuevo", use_container_width=True):
        st.session_state.portal_cadena       = []
        st.session_state.portal_opciones     = []
        st.session_state.portal_query        = ''
        st.session_state.portal_frase_inicio = None
        st.session_state.portal_color_inicio = None
        st.rerun()