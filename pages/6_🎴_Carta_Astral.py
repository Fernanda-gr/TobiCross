import streamlit as st
from core.data import cargar_datos
from core.modelo import recomendar_anime
import ast
import random

st.set_page_config(page_title="Carta Astral · TobiCross", page_icon="🎴", layout="centered")

df_anime, df_pelser, index_scores, index_embed = cargar_datos()

CARTAS = [
    {
        'nombre':    'El Errante Oscuro',
        'subtitulo': 'SOMBRA · CRIMEN · VERDAD',
        'simbolo':   '😈',
        'header':    'LA CARTA DE LAS SOMBRAS',
        'descripcion': 'Caminas donde otros no se atreven. Tu anime vive en los márgenes del mundo, donde la moral se dobla y los héroes sangran.',
        'query':     'Breaking Bad',
        'color':     '#534AB7',
        'bg':        '#EEEDFE',
    },
    {
        'nombre':    'El Soñador Romántico',
        'subtitulo': 'AMOR · MÚSICA · ALMA',
        'simbolo':   '🌸',
        'header':    'LA CARTA DEL CORAZÓN',
        'descripcion': 'Sientes más profundo que los demás. Tu anime te hará llorar de la manera más hermosa posible.',
        'query':     'Diario de una pasión',
        'color':     '#993556',
        'bg':        '#FBEAF0',
    },
    {
        'nombre':    'El Guerrero del Caos',
        'subtitulo': 'FUEGO · BATALLA · GLORIA',
        'simbolo':   '⚔️',
        'header':    'LA CARTA DEL CAOS',
        'descripcion': 'No naciste para quedarte quieto. Tu anime tiene batallas épicas y héroes que no se rinden aunque el mundo caiga.',
        'query':     'Los juegos del hambre',
        'color':     '#185FA5',
        'bg':        '#E6F1FB',
    },
    {
        'nombre':    'El Filósofo del Abismo',
        'subtitulo': 'MISTERIO · ÉTER · COSMOS',
        'simbolo':   '🌀',
        'header':    'LA CARTA DEL ABISMO',
        'descripcion': 'Las grandes preguntas te persiguen. Tu anime te dejará pensando días después de verlo — sin respuestas fáciles.',
        'query':     'Stranger Things',
        'color':     '#0F6E56',
        'bg':        '#E1F5EE',
    },
    {
        'nombre':    'El Alma Libre',
        'subtitulo': 'LUZ · RISA · PRESENTE',
        'simbolo':   '✨',
        'header':    'LA CARTA DE LA LUZ',
        'descripcion': 'Vives el momento. Tu anime es el que se siente como un abrazo — cálido, ligero y sin pretensiones.',
        'query':     'Friends',
        'color':     '#854F0B',
        'bg':        '#FAEEDA',
    },
    {
        'nombre':    'El Maestro del Horror',
        'subtitulo': 'OSCURIDAD · TERROR · VISIÓN',
        'simbolo':   '👁️',
        'header':    'LA CARTA DEL TERROR',
        'descripcion': 'Ves lo que otros no pueden ver. Tu anime te mostrará los rincones más oscuros de la existencia.',
        'query':     'El Conjuro',
        'color':     '#3C3489',
        'bg':        '#EEEDFE',
    },
    {
        'nombre':    'El Viajero del Cosmos',
        'subtitulo': 'DISTOPÍA · FUTURO · CAOS',
        'simbolo':   '🌌',
        'header':    'LA CARTA DEL FUTURO',
        'descripcion': 'Ves el mundo como podría ser, no como es. Tu anime existe en mundos que aún no existen.',
        'query':     'Interestelar',
        'color':     '#0F6E56',
        'bg':        '#E1F5EE',
    },
    {
        'nombre':    'El Alma Musical',
        'subtitulo': 'MELODÍA · PASIÓN · ESCENARIO',
        'simbolo':   '🎵',
        'header':    'LA CARTA DE LA MELODÍA',
        'descripcion': 'Donde las palabras fallan, tú escuchas. Tu anime habla el idioma universal de la música.',
        'query':     'Whiplash',
        'color':     '#993556',
        'bg':        '#FBEAF0',
    },
]

CARTA_BG_OSCURO = {
    '#534AB7': '#ffffff',
    '#993556': '#ffffff',
    '#185FA5': '#ffffff',
    '#0F6E56': '#ffffff',
    '#854F0B': '#ffffff',
    '#3C3489': '#ffffff',
}

CARTA_BORDER_OSCURO = {
    '#534AB7': '#EEEDFE',
    '#993556': '#FBEAF0',
    '#185FA5': '#E6F1FB',
    '#0F6E56': '#E1F5EE',
    '#854F0B': '#FAEEDA',
    '#3C3489': '#EEEDFE',
}

CARTA_TEXT_OSCURO = {
    '#534AB7': '#3C3489',
    '#993556': '#72243E',
    '#185FA5': '#0C447C',
    '#0F6E56': '#085041',
    '#854F0B': '#633806',
    '#3C3489': '#26215C',
}

if 'carta_revelada' not in st.session_state: st.session_state.carta_revelada = None
if 'carta_anime'    not in st.session_state: st.session_state.carta_anime    = None
if 'carta_generada' not in st.session_state: st.session_state.carta_generada = False

st.markdown(
    '<div style="text-align:center;margin-bottom:1.5rem;">'
    '<p style="font-size:10px;color:#534AB7;letter-spacing:3px;margin-bottom:4px;">CARTA ASTRAL</p>'
    '<p style="font-size:24px;font-weight:600;margin:0 0 6px;">El Tarot Animero</p>'
    '<p style="font-size:14px;color:#888;margin:0;">El universo tiene un anime esperándote</p>'
    '</div>',
    unsafe_allow_html=True
)

CARTA_HTML = """
<div style="width:100%;aspect-ratio:2/3;border-radius:14px;background:#0D0B1A;
            border:1.5px solid #534AB7;display:flex;align-items:center;
            justify-content:center;flex-direction:column;gap:8px;
            position:relative;overflow:hidden;margin-bottom:8px;
            box-shadow:0 2px 12px rgba(83,74,183,0.2);">
  <div style="position:absolute;top:6px;left:6px;right:6px;bottom:6px;
              border:1px solid #2A2550;border-radius:10px;"></div>
  <div style="position:absolute;top:12px;left:12px;right:12px;bottom:12px;
              border:1px solid #1E1A3A;border-radius:8px;"></div>
  <div style="font-size:26px;position:relative;z-index:1;">✦</div>
  <div style="font-size:7px;color:#534AB7;letter-spacing:3px;position:relative;z-index:1;">TOBICROSS</div>
</div>
"""

def elegir_carta(i):
    carta = random.choice(CARTAS)
    st.session_state.carta_revelada = carta
    r_query = df_pelser[df_pelser['título'].str.contains(carta['query'], case=False, na=False)]
    if not r_query.empty:
        recs = recomendar_anime(r_query.iloc[0], df_anime, index_scores, index_embed, k=1)
        st.session_state.carta_anime    = recs[0] if recs else None
        st.session_state.carta_generada = True

if not st.session_state.carta_generada:
    st.markdown('<p style="font-size:13px;color:#888;text-align:center;font-style:italic;margin:1rem 0 1.5rem;">Elige la carta que te llame</p>', unsafe_allow_html=True)

    cols1 = st.columns(4)
    for i in range(4):
        with cols1[i]:
            st.markdown(CARTA_HTML, unsafe_allow_html=True)
            if st.button("Elegir", key=f"carta_{i}", use_container_width=True):
                with st.spinner("🎴 El universo está eligiendo..."):
                    elegir_carta(i)
                st.rerun()

    cols2 = st.columns(4)
    for i in range(4, 8):
        with cols2[i-4]:
            st.markdown(CARTA_HTML, unsafe_allow_html=True)
            if st.button("Elegir", key=f"carta_{i}", use_container_width=True):
                with st.spinner("🎴 El universo está eligiendo..."):
                    elegir_carta(i)
                st.rerun()

if st.session_state.carta_generada and st.session_state.carta_revelada:
    carta         = st.session_state.carta_revelada
    anime         = st.session_state.carta_anime
    bg_oscuro     = CARTA_BG_OSCURO.get(carta['color'], '#ffffff')
    border_oscuro = CARTA_BORDER_OSCURO.get(carta['color'], '#EEEDFE')
    text_color    = CARTA_TEXT_OSCURO.get(carta['color'], '#3C3489')

    anime_html = ''
    img_html   = ''
    if anime is not None:
        genres_a = anime.get('genres_clean', [])
        if isinstance(genres_a, str):
            try: genres_a = ast.literal_eval(genres_a)
            except: genres_a = []
        img_html = f'<img src="{anime.get("image_url","")}" style="height:210px;width:auto;object-fit:contain;"/>'
        anime_html = (
            f'<div style="display:flex;align-items:center;gap:10px;border-top:1px solid {border_oscuro};padding-top:12px;margin-top:4px;">'
            f'<img src="{anime.get("image_url","")}" style="width:44px;height:44px;border-radius:8px;object-fit:cover;flex-shrink:0;"/>'
            f'<div>'
            f'<p style="font-size:13px;font-weight:600;color:{text_color};margin:0 0 2px;">{anime["title"]}</p>'
            f'<span style="font-size:10px;color:{carta["color"]};">⭐ {float(anime.get("score",0)):.1f} · {", ".join(genres_a[:2])}</span>'
            f'</div></div>'
        )

    st.markdown(
        f'<div style="max-width:280px;margin:2rem auto 0;">'
        f'<div style="border-radius:16px;overflow:hidden;border:2px solid {carta["color"]};background:{bg_oscuro};">'
        f'<div style="background:{carta["color"]};padding:10px 14px;text-align:center;">'
        f'<p style="font-size:9px;color:#fff;letter-spacing:3px;margin:0;">{carta["header"]}</p>'
        f'</div>'
        f'<div style="background:{carta["bg"]};height:220px;display:flex;align-items:center;justify-content:center;position:relative;">'
        f'{img_html}'
        
        f'</div>'
        f'<div style="padding:14px;background:{bg_oscuro};">'
        f'<p style="font-size:17px;font-weight:700;color:{text_color};margin:0 0 3px;">{carta["nombre"]}</p>'
        f'<p style="font-size:9px;color:{carta["color"]};letter-spacing:2px;margin:0 0 10px;">{carta["subtitulo"]}</p>'
        f'<p style="font-size:11px;color:{text_color};line-height:1.6;font-style:italic;margin-bottom:12px;">"{carta["descripcion"]}"</p>'
        f'{anime_html}'
        f'</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True
    )

    st.markdown("")
    if st.button("🔄 Sacar otra carta", use_container_width=True):
        st.session_state.carta_revelada = None
        st.session_state.carta_anime    = None
        st.session_state.carta_generada = False
        st.rerun()