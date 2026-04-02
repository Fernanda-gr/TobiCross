import streamlit as st
from core.data import cargar_datos
from core.modelo import recomendar_anime
import ast

st.set_page_config(page_title="Modo Destino · TobiCross", page_icon="🔮", layout="centered")

df_anime, df_pelser, index_scores, index_embed = cargar_datos()

# ── Session state ──────────────────────────────
if 'destino_paso' not in st.session_state:
    st.session_state.destino_paso = 0
if 'destino_respuestas' not in st.session_state:
    st.session_state.destino_respuestas = {}

PREGUNTAS = [
    {
        'num': 'I',
        'texto': '¿Si pudieras abrir una puerta a cualquier mundo, cuál elegiría tu corazón?',
        'opciones': [
            ('🏰', 'Un reino de magia y criaturas antiguas',    'guerrero'),
            ('🌆', 'Una ciudad cyberpunk bajo lluvia eterna',    'filosofo'),
            ('🌿', 'Un pueblo pequeño donde todos se conocen',  'libre'),
            ('⚔️', 'Un mundo en guerra donde los héroes caen',  'guerrero'),
            ('🌀', 'Una dimensión donde el tiempo no existe',   'filosofo'),
        ]
    },
    {
        'num': 'II',
        'texto': '¿Qué parte de ti nadie ve?',
        'opciones': [
            ('🎵', 'La que llora con música a medianoche',              'romantico'),
            ('🕵️', 'La que planea en silencio y espera',                'errante'),
            ('🔥', 'La que quiere destruirlo todo y empezar de nuevo',  'guerrero'),
            ('💜', 'La que ama tan profundo que asusta',                 'romantico'),
            ('😂', 'La que ríe de todo porque si no, llora',            'libre'),
        ]
    },
    {
        'num': 'III',
        'texto': 'Un extraño te dice que conoce tu historia. ¿Cómo termina?',
        'opciones': [
            ('🔥', 'En llamas, pero glorioso',                  'guerrero'),
            ('🌸', 'En paz, rodeado de los que amas',           'romantico'),
            ('🔭', 'Solo, pero habiendo entendido todo',        'filosofo'),
            ('🌊', 'En medio de algo que nunca terminó',        'errante'),
            ('😄', 'Riéndote de lo absurdo que fue todo',       'libre'),
        ]
    },
    {
        'num': 'IV',
        'texto': 'Te ofrecen un poder. ¿Cuál tomas?',
        'opciones': [
            ('👁️', 'Ver la verdad detrás de las mentiras', 'errante'),
            ('💞', 'Sentir lo que sienten los demás',       'romantico'),
            ('⚡', 'Ser invencible en batalla',             'guerrero'),
            ('⏳', 'Reescribir el pasado',                  'filosofo'),
            ('👻', 'Desaparecer cuando quieras',            'libre'),
        ]
    },
    {
        'num': 'V',
        'texto': '¿Qué frase vivirías?',
        'opciones': [
            ('🌑', 'El caos es el único orden verdadero',       'filosofo'),
            ('💗', 'Amar es el acto más valiente',              'romantico'),
            ('🖤', 'La oscuridad también tiene su belleza',     'errante'),
            ('⚔️', 'Lucho porque no tengo otra opción',         'guerrero'),
            ('✨', 'La vida es demasiado corta para ser seria', 'libre'),
        ]
    },
]

ARQUETIPOS = {
    'errante': {
        'nombre':      '🌑 El Errante Oscuro',
        'descripcion': 'Caminas entre sombras con los ojos abiertos. Ves lo que otros evitan. Tu anime vive en los márgenes del mundo.',
        'query':       'Breaking Bad',
        'color':       '#534AB7',
        'bg':          '#EEEDFE',
    },
    'romantico': {
        'nombre':      '🌸 El Soñador Romántico',
        'descripcion': 'Tu corazón late más fuerte con la música y el amor. Buscas historias que te recuerden que sentir es vivir.',
        'query':       'Diario de una pasión',
        'color':       '#993556',
        'bg':          '#FBEAF0',
    },
    'guerrero': {
        'nombre':      '⚔️ El Guerrero del Caos',
        'descripcion': 'No naciste para quedarte quieto. Necesitas adrenalina, batallas y héroes que sangran pero no se rinden.',
        'query':       'Los juegos del hambre',
        'color':       '#185FA5',
        'bg':          '#E6F1FB',
    },
    'filosofo': {
        'nombre':      '🌀 El Filósofo del Abismo',
        'descripcion': 'Las grandes preguntas te persiguen. Buscas anime que te deje pensando días después de verlo.',
        'query':       'Stranger Things',
        'color':       '#0F6E56',
        'bg':          '#E1F5EE',
    },
    'libre': {
        'nombre':      '✨ El Alma Libre',
        'descripcion': 'Ríes fácil, amas fácil, vives fácil. Tu anime ideal es el que se siente como un abrazo.',
        'query':       'Friends',
        'color':       '#854F0B',
        'bg':          '#FAEEDA',
    },
}

# ── UI ────────────────────────────────────────
st.title("🔮 Modo Destino")
st.caption("Cinco preguntas. Un destino. Tu anime perfecto.")

paso = st.session_state.destino_paso

if paso < 5:
    # ── Barra de progreso ──
    progreso = paso / 5
    st.markdown(f"""
    <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
      <span style="font-size:12px; color:#888;">Pregunta {paso+1} de 5</span>
      <span style="font-size:12px; color:#888;">{int(progreso*100)}%</span>
    </div>
    <div style="height:3px; background:#eee; border-radius:2px; margin-bottom:2rem;">
      <div style="width:{int(progreso*100)}%; height:100%; background:#534AB7; border-radius:2px;"></div>
    </div>
    """, unsafe_allow_html=True)

    # ── Pregunta actual ──
    p = PREGUNTAS[paso]
    st.markdown(f"**{p['num']}. {p['texto']}**")
    st.markdown("")

    respuesta_actual = st.session_state.destino_respuestas.get(paso)
    opciones_texto   = [f"{e}  {t}" for e, t, _ in p['opciones']]
    idx_actual       = None
    if respuesta_actual is not None:
        idx_actual = respuesta_actual

    seleccion = st.radio("", opciones_texto, index=idx_actual, key=f"radio_{paso}")

    # Guardar índice seleccionado
    if seleccion:
        idx = opciones_texto.index(seleccion)
        st.session_state.destino_respuestas[paso] = idx

    st.markdown("")
    col1, col2 = st.columns([1, 2])

    with col1:
        if paso > 0:
            if st.button("← Anterior", use_container_width=True):
                st.session_state.destino_paso -= 1
                st.rerun()

    with col2:
        hay_respuesta = paso in st.session_state.destino_respuestas
        label = "Siguiente →" if paso < 4 else "🔮 Revelar mi destino"
        if st.button(label, use_container_width=True, disabled=not hay_respuesta):
            st.session_state.destino_paso += 1
            st.rerun()

else:
    # ── Calcular arquetipo ──
    puntos = {'errante': 0, 'romantico': 0, 'guerrero': 0, 'filosofo': 0, 'libre': 0}
    for paso_idx, opcion_idx in st.session_state.destino_respuestas.items():
        _, _, arquetipo_key = PREGUNTAS[paso_idx]['opciones'][opcion_idx]
        puntos[arquetipo_key] += 1

    arquetipo = max(puntos, key=puntos.get)
    info      = ARQUETIPOS[arquetipo]

    # ── Mostrar arquetipo ──
    st.markdown(f"""
    <div style="border-radius:16px; border:1px solid {info['color']}40;
                background:{info['bg']}; padding:28px; text-align:center; margin:1rem 0;">
      <p style="font-size:32px; margin:0 0 10px;">{info['nombre'].split()[0]}</p>
      <p style="font-size:22px; font-weight:600; color:{info['color']}; margin:0 0 10px;">
        {' '.join(info['nombre'].split()[1:])}
      </p>
      <p style="font-size:15px; color:{info['color']}; margin:0; line-height:1.6;">
        {info['descripcion']}
      </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Animes ──
    with st.spinner("✨ Invocando tu destino..."):
        resultados = df_pelser[df_pelser['título'].str.contains(info['query'], case=False, na=False)]
        if not resultados.empty:
            row = resultados.iloc[0]
            recomendaciones = recomendar_anime(row, df_anime, index_scores, index_embed, k=3)

            st.subheader("✨ Tu anime del destino")
            cols = st.columns(3)
            for i, anime in enumerate(recomendaciones):
                genres = anime.get('genres_clean', [])
                if isinstance(genres, str):
                    try: genres = ast.literal_eval(genres)
                    except: genres = [genres]
                with cols[i]:
                    st.markdown(f"""
                    <div style="border-radius:12px; border:1px solid #eee; overflow:hidden;">
                      <div style="background:{info['bg']}; height:160px; display:flex;
                                  align-items:center; justify-content:center;">
                        <img src="{anime['image_url']}" style="height:150px; width:auto; object-fit:contain;"/>
                      </div>
                      <div style="padding:10px;">
                        <p style="font-size:13px; font-weight:600; margin:0 0 3px;
                                  color:#111; line-height:1.3;">{anime['title']}</p>
                        <p style="font-size:11px; color:#888; margin:0;">
                          ⭐ {anime['score']} · {', '.join(genres[:2])}
                        </p>
                      </div>
                    </div>
                    """, unsafe_allow_html=True)

    st.markdown("")
    if st.button("🔄 Volver a intentarlo", use_container_width=True):
        st.session_state.destino_paso = 0
        st.session_state.destino_respuestas = {}
        st.rerun()