import streamlit as st
from core.data import cargar_datos
from core.modelo import recomendar_anime
import ast

st.set_page_config(page_title="Modo Destino · TobiCross", page_icon="🎭", layout="wide")

st.markdown("""
<style>
.block-container {
    padding-top: 2rem !important;
    padding-bottom: 2rem !important;
}

/* Contenedor del radio */
div[data-testid="stRadio"] > div {
    gap: 10px !important;
    display: flex !important;
    flex-direction: column !important;
}

/* Cada opción como card */
div[data-testid="stRadio"] div[data-testid="stMarkdownContainer"] p,
div[data-testid="stRadio"] label {
    font-size: 18px !important;
    padding: 8px 20px !important;
    border-radius: 14px !important;
    border: 2px solid #e0e0e0 !important;
    background: #ffffff !important;
    color: #333 !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
    margin: 0 !important;
    width: 100% !important;
    display: block !important;
}

div[data-testid="stRadio"] label:hover {
    border-color: #534AB7 !important;
    background: #EEEDFE !important;
    color: #534AB7 !important;
}

/* Opción seleccionada */
div[data-testid="stRadio"] label:has(input:checked) {
    border-color: #534AB7 !important;
    background: #EEEDFE !important;
    color: #534AB7 !important;
    font-weight: 600 !important;
}

/* Oculta el radio button circular */
div[data-testid="stRadio"] input[type="radio"] {
    display: none !important;
}

/* Oculta el label vacío del radio */
div[data-testid="stRadio"] > label {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

df_anime, df_pelser, index_scores, index_embed, modelo_embed = cargar_datos()

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
    'errante':   {'nombre':'🌑 El Errante Oscuro','descripcion':'Caminas entre sombras con los ojos abiertos. Ves lo que otros evitan. Tu anime vive en los márgenes del mundo.','query':'Breaking Bad','color':'#534AB7','bg':'#EEEDFE'},
    'romantico': {'nombre':'🌸 El Soñador Romántico','descripcion':'Tu corazón late más fuerte con la música y el amor. Buscas historias que te recuerden que sentir es vivir.','query':'Diario de una pasión','color':'#993556','bg':'#FBEAF0'},
    'guerrero':  {'nombre':'⚔️ El Guerrero del Caos','descripcion':'No naciste para quedarte quieto. Necesitas adrenalina, batallas y héroes que sangran pero no se rinden.','query':'Los juegos del hambre','color':'#185FA5','bg':'#E6F1FB'},
    'filosofo':  {'nombre':'🌀 El Filósofo del Abismo','descripcion':'Las grandes preguntas te persiguen. Buscas anime que te deje pensando días después de verlo.','query':'Stranger Things','color':'#0F6E56','bg':'#E1F5EE'},
    'libre':     {'nombre':'✨ El Alma Libre','descripcion':'Ríes fácil, amas fácil, vives fácil. Tu anime ideal es el que se siente como un abrazo.','query':'Friends','color':'#854F0B','bg':'#FAEEDA'},
}

# ─── HEADER ───────────────────────────────────────────────────────────────────
col_back, col_title, _ = st.columns([1, 5, 1])
with col_back:
    st.markdown("<div style='padding-top:36px'>", unsafe_allow_html=True)
    if st.button("← Inicio", key="btn_inicio"):
        st.switch_page("main.py")
    st.markdown("</div>", unsafe_allow_html=True)
with col_title:
    st.markdown(
        '<div style="text-align:center;margin-bottom:2rem;">'
        '<p style="font-size:11px;color:#534AB7;letter-spacing:3px;margin-bottom:8px;">MODO DESTINO</p>'
        '<p style="font-size:60px;font-weight:700;margin:0 0 8px;">🎭 Modo Destino</p>'
        '<p style="font-size:16px;color:#888;margin:0;">Cinco preguntas. Un destino. Tu anime perfecto.</p>'
        '</div>',
        unsafe_allow_html=True
    )

paso = st.session_state.destino_paso

# ─── PREGUNTAS ────────────────────────────────────────────────────────────────
if paso < 5:
    _, col, _ = st.columns([1, 3, 1])
    with col:
        progreso = paso / 5
        st.markdown(f"""
        <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
            <span style="font-size:13px; color:#888;">Pregunta {paso+1} de 5</span>
            <span style="font-size:13px; color:#534AB7; font-weight:600;">{int(progreso*100)}%</span>
        </div>
        <div style="position:relative; height:8px; background:#eee; border-radius:4px; margin-bottom:2.5rem;">
            <div style="width:{int(progreso*100)}%; height:100%;
                        background:linear-gradient(90deg, #534AB7, #185FA5);
                        border-radius:4px;"></div>
            <div style="position:absolute; top:-10px;
                        left:calc({int(progreso*100)}% - 12px);
                        font-size:20px;">🍿</div>
        </div>
        """, unsafe_allow_html=True)

        p = PREGUNTAS[paso]
        st.markdown(
            f"<p style='font-size:22px;font-weight:600;margin-bottom:1.5rem;line-height:1.4;'>"
            f"{p['num']}. {p['texto']}</p>",
            unsafe_allow_html=True
        )

        opciones_texto   = [f"{e}  {t}" for e, t, _ in p['opciones']]
        idx_actual       = st.session_state.destino_respuestas.get(paso)
        seleccion        = st.radio("\u200b", opciones_texto, index=idx_actual, key=f"radio_{paso}")

        if seleccion:
            idx = opciones_texto.index(seleccion)
            st.session_state.destino_respuestas[paso] = idx

        st.markdown("<div style='margin-top:2rem;'>", unsafe_allow_html=True)
        col1, col2 = st.columns([1, 2])
        with col1:
            if paso > 0:
                if st.button("← Anterior", key="btn_anterior", use_container_width=True):
                    st.session_state.destino_paso -= 1
                    st.rerun()
        with col2:
            hay_respuesta = paso in st.session_state.destino_respuestas
            label = "Siguiente →" if paso < 4 else "🔮 Revelar mi destino"
            if st.button(label, key="btn_siguiente", use_container_width=True, disabled=not hay_respuesta):
                st.session_state.destino_paso += 1
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# ─── RESULTADO ────────────────────────────────────────────────────────────────
else:
    puntos = {'errante': 0, 'romantico': 0, 'guerrero': 0, 'filosofo': 0, 'libre': 0}
    for paso_idx, opcion_idx in st.session_state.destino_respuestas.items():
        _, _, arquetipo_key = PREGUNTAS[paso_idx]['opciones'][opcion_idx]
        puntos[arquetipo_key] += 1

    arquetipo = max(puntos, key=puntos.get)
    info      = ARQUETIPOS[arquetipo]

    _, col, _ = st.columns([1, 3, 1])
    with col:
        st.markdown(f"""
        <div style="border-radius:20px; border:2px solid {info['color']}60;
                    background:{info['bg']}; padding:36px; text-align:center; margin:1rem 0 2rem;">
            <p style="font-size:48px; margin:0 0 12px;">{info['nombre'].split()[0]}</p>
            <p style="font-size:28px; font-weight:700; color:{info['color']}; margin:0 0 12px;">
                {' '.join(info['nombre'].split()[1:])}
            </p>
            <p style="font-size:16px; color:{info['color']}; margin:0; line-height:1.7;">
                {info['descripcion']}
            </p>
        </div>
        """, unsafe_allow_html=True)

        with st.spinner("✨ Invocando tu destino..."):
            resultados = df_pelser[df_pelser['título'].str.contains(info['query'], case=False, na=False)]
            if not resultados.empty:
                row = resultados.iloc[0]
                recomendaciones = recomendar_anime(row, df_anime, index_scores, index_embed, k=3)

                st.markdown(
                    "<p style='font-size:20px;font-weight:600;margin:1rem 0;'>✨ Tu anime del destino</p>",
                    unsafe_allow_html=True
                )
                cols = st.columns(min(len(recomendaciones), 3))
                for i, anime in enumerate(recomendaciones[:3]):
                    genres = anime.get('genres_clean', [])
                    if isinstance(genres, str):
                        try: genres = ast.literal_eval(genres)
                        except: genres = [genres]
                    with cols[i]:
                        st.markdown(
                            f'<div style="border-radius:14px;border:1px solid #eee;overflow:hidden;">'
                            f'<div style="background:{info["bg"]};height:160px;display:flex;align-items:center;justify-content:center;">'
                            f'<img src="{anime["image_url"]}" style="height:190px;width:auto;object-fit:contain;"/>'
                            f'</div>'
                            f'<div style="padding:14px;">'
                            f'<p style="font-size:15px;font-weight:600;margin:0 0 4px;color:#111;line-height:1.3;">{anime["title"]}</p>'
                            f'<p style="font-size:12px;color:#888;margin:0 0 8px;">⭐ {anime["score"]} · {", ".join(genres[:2])}</p>'
                            f'<a href="https://myanimelist.net/anime/{anime["mal_id"]}" '
                            f'target="_blank" style="font-size:12px;color:#534AB7;text-decoration:none;">Ver en MAL →</a>'
                            f'</div></div>',
                            unsafe_allow_html=True
                        )

        st.markdown("<div style='margin-top:2rem;'>", unsafe_allow_html=True)
        if st.button("🔄 Volver a intentarlo", use_container_width=True, key="btn_reiniciar"):
            st.session_state.destino_paso = 0
            st.session_state.destino_respuestas = {}
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)