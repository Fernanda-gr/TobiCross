import streamlit as st
from core.data import cargar_datos
from core.modelo import recomendar_anime, get_primera_temporada, _idx_posicional
import ast
import numpy as np
from collections import defaultdict
import faiss

st.set_page_config(page_title="Modo Dúo · TobiCross", page_icon="👥", layout="centered")

df_anime, df_pelser, index_scores, index_embed = cargar_datos()

def detectar_arquetipo(row):
    scores = {
        'errante':   float(row.get('dark_score', 0))    + float(row.get('crime_score', 0)),
        'romantico': float(row.get('romance', 0))        + float(row.get('music_score', 0)),
        'guerrero':  float(row.get('action_score', 0))   + float(row.get('adventure_score', 0)),
        'filosofo':  float(row.get('dystopia_score', 0)) + float(row.get('thriller_score', 0)),
        'libre':     float(row.get('feel_good_score', 0))+ float(row.get('comedy_score', 0)),
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

# ── UI ────────────────────────────────────────
st.markdown("""
<div style="text-align:center; margin-bottom:2rem;">
  <p style="font-size:13px; color:#7F77DD; letter-spacing:2px; margin:0 0 4px; font-weight:500;">MODO DÚO</p>
  <p style="font-size:24px; font-weight:600; margin:0 0 6px;">¿Qué anime los une?</p>
  <p style="font-size:14px; color:#888; margin:0;">Cada uno elige su película favorita y el universo hace el resto</p>
</div>
""", unsafe_allow_html=True)

col1, colv, col2 = st.columns([5, 1, 5])
with col1:
    st.markdown('<p style="font-size:11px; font-weight:500; color:#534AB7; letter-spacing:2px; margin:0 0 4px;">JUGADOR 1</p>', unsafe_allow_html=True)
    q1 = st.text_input("", placeholder="Tu película favorita...", key="duo_q1", label_visibility="collapsed")
with colv:
    st.markdown('<div style="display:flex; align-items:center; justify-content:center; height:100%; padding-top:20px;"><div style="width:40px;height:40px;border-radius:50%;background:#EEEDFE;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:600;color:#534AB7;">VS</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown('<p style="font-size:11px; font-weight:500; color:#993556; letter-spacing:2px; margin:0 0 4px;">JUGADOR 2</p>', unsafe_allow_html=True)
    q2 = st.text_input("", placeholder="Tu película favorita...", key="duo_q2", label_visibility="collapsed")

st.markdown("")
buscar = st.button("✨ Encontrar su anime en común", use_container_width=True)

if buscar and q1 and q2:
    r1 = df_pelser[df_pelser['título'].str.contains(q1, case=False, na=False)]
    r2 = df_pelser[df_pelser['título'].str.contains(q2, case=False, na=False)]

    if r1.empty:
        st.warning(f"No encontré '{q1}'")
    elif r2.empty:
        st.warning(f"No encontré '{q2}'")
    else:
        row1 = r1.iloc[0]
        row2 = r2.iloc[0]

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
        <div style="background:#f8f8f8; border-radius:12px; padding:16px; margin:1.5rem 0;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
            <span style="font-size:13px; font-weight:600; color:#111;">Compatibilidad animera</span>
            <span style="font-size:22px; font-weight:700; color:{info1['color']};">{pct}%</span>
          </div>
          <div style="height:6px; background:#eee; border-radius:3px; margin-bottom:8px;">
            <div style="width:{pct}%; height:100%; background:{info1['color']}; border-radius:3px;"></div>
          </div>
          <p style="font-size:12px; color:#888; margin:0;">{mensaje}</p>
        </div>
        """, unsafe_allow_html=True)

        with st.spinner("🎌 Fusionando universos..."):
            rrf1    = get_rrf(row1)
            rrf2    = get_rrf(row2)
            top_idx = fusionar(rrf1, rrf2, row1, row2)

        st.markdown('<p style="font-size:14px; font-weight:600; margin:0 0 12px;">🎌 Anime que los une</p>', unsafe_allow_html=True)

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
            genres = anime.get('genres_clean', [])
            if isinstance(genres, str):
                try:    genres = ast.literal_eval(genres)
                except: genres = [genres]

            badges = ''.join([
                f'<span style="font-size:10px; padding:2px 8px; border-radius:20px; {get_badge_style(g)}; margin-right:4px;">{g}</span>'
                for g in genres[:2]
            ])

            with cols[i]:
                st.markdown(f"""
                <div style="border-radius:12px; border:1px solid #eee; overflow:hidden;">
                  <div style="background:#f5f3ff; height:150px; display:flex;
                              align-items:center; justify-content:center;">
                    <img src="{anime['image_url']}" style="height:140px; width:auto; object-fit:contain;"/>
                  </div>
                  <div style="padding:10px;">
                    <p style="font-size:12px; font-weight:600; margin:0 0 5px;
                              color:#111; line-height:1.3;">{anime['title']}</p>
                    <div style="margin-bottom:5px;">{badges}</div>
                    <p style="font-size:11px; color:#888; margin:0;">⭐ {anime['score']}</p>
                  </div>
                </div>
                """, unsafe_allow_html=True)