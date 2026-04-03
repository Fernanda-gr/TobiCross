import streamlit as st

st.set_page_config(page_title="TobiCross", page_icon="🎌", layout="wide")

st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)

col_esp1, col_logo, col_titulo, col_esp2 = st.columns([0.3, 2, 4, 0.3])

with col_logo:
    st.image("assets/logo.png", use_container_width=True)

with col_titulo:
    st.markdown("""
    <div style="display:flex;flex-direction:column;justify-content:center;
                height:100%;padding-left:30px;padding-top:20px;">
      <p style="font-size:11px;color:#534AB7;letter-spacing:5px;font-weight:500;
                margin:0 0 16px;">DESCUBRE TU ANIME</p>
      <p style="font-size:80px;font-weight:900;color:#1A1635;margin:0 0 20px;
                line-height:1;letter-spacing:-2px;white-space:nowrap;">TobiCross</p>
      <p style="font-size:18px;color:#888;margin:0;line-height:1.7;max-width:460px;">
        Dinos qué películas te gustan y encontraremos el anime perfecto para ti.
      </p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)

FEATURES = [
    ('🎯', 'Recomendador',    'Busca tu película favorita.',        'pages/0_🎯_Recomendador.py',  '#1A1635', '#CECBF6', '#534AB7'),
    ('🔮', 'Modo Destino',    '5 preguntas, un destino.',           'pages/1_🔮_Modo_Destino.py',  '#26215C', '#AFA9EC', '#7F77DD'),
    ('👥', 'Modo Dúo',        'Un anime para los dos.',             'pages/2_👥_Modo_Duo.py',      '#4B1528', '#F4C0D1', '#993556'),
    ('🗺️', 'Portal',          'Explora mundos conectados.',         'pages/3_🗺️_Portal.py',        '#04342C', '#9FE1CB', '#0F6E56'),
    ('📊', 'Perfil de Fan',   'Descubre tu arquetipo.',             'pages/4_📊_Perfil_Fan.py',    '#412402', '#FAC775', '#854F0B'),
    ('💬', 'Chat con YOMI',   'Tu guía entre mundos.',              'pages/5_💬_Chat_YOMI.py',     '#042C53', '#B5D4F4', '#185FA5'),
    ('🎴', 'Carta Astral',    'Deja que el universo elija.',        'pages/6_🎴_Carta_Astral.py',  '#0A0820', '#CECBF6', '#534AB7'),
]

def render_card(emoji, titulo, desc, bg, text, accent):
    st.markdown(f"""
    <div style="border-radius:20px;background:{bg};padding:28px 24px 24px;
                border:1px solid {accent}40;margin-bottom:8px;min-height:170px;">
      <div style="font-size:36px;margin-bottom:14px;">{emoji}</div>
      <p style="font-size:17px;font-weight:700;color:{text};margin:0 0 6px;">{titulo}</p>
      <p style="font-size:13px;color:{text};opacity:0.7;line-height:1.5;margin:0;">{desc}</p>
    </div>
    """, unsafe_allow_html=True)

cols1 = st.columns(4)
for i in range(4):
    emoji, titulo, desc, pagina, bg, text, accent = FEATURES[i]
    with cols1[i]:
        render_card(emoji, titulo, desc, bg, text, accent)
        if st.button("→", key=f"btn_{i}", use_container_width=True):
            st.switch_page(pagina)

st.markdown("<div style='margin-bottom:16px;'></div>", unsafe_allow_html=True)

_, col1, col2, col3, _ = st.columns([0.5, 1, 1, 1, 0.5])
for j, col in enumerate([col1, col2, col3]):
    emoji, titulo, desc, pagina, bg, text, accent = FEATURES[4 + j]
    with col:
        render_card(emoji, titulo, desc, bg, text, accent)
        if st.button("→", key=f"btn_{4+j}", use_container_width=True):
            st.switch_page(pagina)