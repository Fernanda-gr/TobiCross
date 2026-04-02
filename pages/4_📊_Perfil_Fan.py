import streamlit as st
from core.data import cargar_datos
from core.modelo import recomendar_anime
import ast
import numpy as np

st.set_page_config(page_title="Perfil de Fan · TobiCross", page_icon="📊", layout="centered")

df_anime, df_pelser, index_scores, index_embed = cargar_datos()

ARQUETIPOS = {
    'errante': {
        'nombre':    'El Errante Oscuro',
        'emoji':     '😈',
        'nivel':     'Maestro de las Sombras',
        'elemento':  '🌑 Oscuridad',
        'planeta':   '🪐 Saturno',
        'poder':     '👁️ Ver la verdad',
        'debilidad': '💜 El amor',
        'descripcion': 'Caminas entre sombras con los ojos abiertos. Ves lo que otros evitan. Buscas historias que no teman mostrarte el lado oscuro del mundo — y de las personas.',
        'query':     'Breaking Bad',
        'color':     '#534AB7',
        'bg':        '#EEEDFE',
    },
    'romantico': {
        'nombre':    'El Soñador Romántico',
        'emoji':     '🌸',
        'nivel':     'Guardián del Corazón',
        'elemento':  '🌸 Amor',
        'planeta':   '♀️ Venus',
        'poder':     '💞 Sentir todo',
        'debilidad': '🖤 La frialdad',
        'descripcion': 'Tu corazón late más fuerte con la música y el amor. Buscas historias que te recuerden que sentir es vivir — aunque duela.',
        'query':     'Diario de una pasión',
        'color':     '#993556',
        'bg':        '#FBEAF0',
    },
    'guerrero': {
        'nombre':    'El Guerrero del Caos',
        'emoji':     '⚔️',
        'nivel':     'Comandante de Batallas',
        'elemento':  '🔥 Fuego',
        'planeta':   '♂️ Marte',
        'poder':     '⚡ Ser invencible',
        'debilidad': '😌 La calma',
        'descripcion': 'No naciste para quedarte quieto. Necesitas adrenalina, batallas y héroes que sangran pero no se rinden.',
        'query':     'Los juegos del hambre',
        'color':     '#185FA5',
        'bg':        '#E6F1FB',
    },
    'filosofo': {
        'nombre':    'El Filósofo del Abismo',
        'emoji':     '🌀',
        'nivel':     'Oráculo del Caos',
        'elemento':  '🌌 Éter',
        'planeta':   '⛢ Urano',
        'poder':     '🔭 Ver el futuro',
        'debilidad': '😂 La simplicidad',
        'descripcion': 'Las grandes preguntas te persiguen. Buscas anime que te deje pensando días después de verlo — sin respuestas fáciles.',
        'query':     'Stranger Things',
        'color':     '#0F6E56',
        'bg':        '#E1F5EE',
    },
    'libre': {
        'nombre':    'El Alma Libre',
        'emoji':     '✨',
        'nivel':     'Maestro del Presente',
        'elemento':  '🌟 Luz',
        'planeta':   '☀️ Sol',
        'poder':     '😄 Contagiar alegría',
        'debilidad': '🌑 La oscuridad',
        'descripcion': 'Ríes fácil, amas fácil, vives fácil. Tu anime ideal es el que se siente como un abrazo — cálido, ligero y sin pretensiones.',
        'query':     'Friends',
        'color':     '#854F0B',
        'bg':        '#FAEEDA',
    },
}

def get_genero_dominante(genres):
    if isinstance(genres, str):
        try: genres = ast.literal_eval(genres)
        except: genres = [genres]
    ORDEN = ['Horror','Crime','Romance','Music','Action','Fantasy','Sci-Fi',
             'Comedy','Drama','Mystery','Thriller','Sports']
    for g in ORDEN:
        if g in genres:
            return g
    return genres[0] if genres else 'Drama'

def calcular_perfil(rows):
    campos = ['dark_score','crime_score','romance','music_score','action_score',
              'adventure_score','fantasy','scifi','comedy_score','feel_good_score',
              'drama_score','thriller_score','dystopia_score','power_score','horror_score']
    promedios = {}
    for c in campos:
        vals = []
        for r in rows:
            try:
                val = float(r[c]) if c in r.index else 0.0
            except:
                val = 0.0
            vals.append(val)
        promedios[c] = np.mean(vals)
    return promedios

def detectar_arquetipo(promedios):
    scores = {
        'errante':   promedios['dark_score']    + promedios['crime_score'],
        'romantico': promedios['romance']        + promedios['music_score'],
        'guerrero':  promedios['action_score']   + promedios['adventure_score'],
        'filosofo':  promedios['dystopia_score'] + promedios['thriller_score'],
        'libre':     promedios['feel_good_score']+ promedios['comedy_score'],
    }
    return max(scores, key=scores.get)

def calcular_stats(promedios):
    return {
        'Oscuridad':            int(min((promedios['dark_score']     + promedios['horror_score']) * 80, 100)),
        'Intensidad emocional': int(min((promedios['drama_score']    + promedios['romance'])      * 60, 100)),
        'Tolerancia al caos':   int(min((promedios['action_score']   + promedios['dystopia_score'])* 70, 100)),
        'Romance':              int(min( promedios['romance']         * 100, 100)),
        'Feel good':            int(min( promedios['feel_good_score'] * 100, 100)),
    }

STAT_COLORS = {
    'Oscuridad':            '#534AB7',
    'Intensidad emocional': '#534AB7',
    'Tolerancia al caos':   '#534AB7',
    'Romance':              '#D4537E',
    'Feel good':            '#1D9E75',
}

# ── UI ────────────────────────────────────────
st.markdown("""
<div style="text-align:center; margin-bottom:1.5rem;">
  <p style="font-size:13px; color:#7F77DD; letter-spacing:2px; margin:0 0 4px; font-weight:500;">PERFIL DE FAN</p>
  <p style="font-size:24px; font-weight:600; margin:0 0 6px;">Descubre tu arquetipo animero</p>
  <p style="font-size:14px; color:#888; margin:0;">Ingresa 3 a 5 películas que te encanten</p>
</div>
""", unsafe_allow_html=True)

st.markdown('<p style="font-size:13px; color:#7F77DD; letter-spacing:2px; margin-bottom:8px; font-weight:500;">TUS PELÍCULAS FAVORITAS</p>', unsafe_allow_html=True)

peliculas = []
for i in range(5):
    p = st.text_input("", placeholder=f"Película {i+1}...",
                      label_visibility="collapsed", key=f"perfil_p{i}")
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
            r = df_pelser[df_pelser['título'].str.contains(p, case=False, na=False)]
            if r.empty:
                no_encontradas.append(p)
            else:
                rows.append(r.iloc[0])

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

                # Anime guardián
                guardian = None
                r_query  = df_pelser[df_pelser['título'].str.contains(arq['query'], case=False, na=False)]
                if not r_query.empty:
                    recs = recomendar_anime(r_query.iloc[0], df_anime, index_scores, index_embed, k=1)
                    if recs and len(recs) > 0:
                        guardian = recs[0]

            nivel = int(min(sum(stats.values()) / len(stats), 99))

            # Barras de stats
            stats_html = ''
            for nombre, valor in stats.items():
                color = STAT_COLORS.get(nombre, '#534AB7')
                stats_html += f"""
                <div style="display:flex;justify-content:space-between;font-size:11px;
                            color:#7F77DD;margin-bottom:5px;">
                  <span>{nombre}</span><span style="color:#CECBF6;">{valor}</span>
                </div>
                <div style="height:6px;background:rgba(83,74,183,0.2);border-radius:3px;margin-bottom:12px;">
                  <div style="width:{valor}%;height:100%;border-radius:3px;background:{color};"></div>
                </div>
                """

            # Anime guardián
            guardian_html = ''
            if guardian is not None:
                genres_g = guardian.get('genres_clean', [])
                if isinstance(genres_g, str):
                    try: genres_g = ast.literal_eval(genres_g)
                    except: genres_g = []
                guardian_html = f"""
                <div style="background:rgba(83,74,183,0.1);border-radius:10px;padding:14px;
                            border:1px solid #2A2550;margin-top:16px;">
                  <p style="font-size:10px;color:#534AB7;letter-spacing:2px;margin-bottom:10px;">ANIME GUARDIÁN</p>
                  <div style="display:flex;align-items:center;gap:12px;">
                    <img src="{guardian.get('image_url','')}" style="width:52px;height:52px;
                         border-radius:10px;object-fit:cover;flex-shrink:0;"/>
                    <div>
                      <p style="font-size:14px;font-weight:600;color:#CECBF6;margin-bottom:2px;">
                        {guardian['title']}
                      </p>
                      <p style="font-size:11px;color:#7F77DD;">Tu espejo en otro universo</p>
                      <p style="font-size:10px;color:#534AB7;margin-top:3px;">
                        ⭐ {float(guardian.get('score', 0)):.1f} · {', '.join(genres_g[:2])}
                      </p>
                    </div>
                  </div>
                </div>
                """

            st.markdown(f"""
            <div style="background:#0D0B1A;border-radius:20px;padding:28px;border:1px solid #2A2550;margin-top:1rem;">

              <p style="font-size:10px;color:#534AB7;letter-spacing:3px;text-align:center;margin-bottom:20px;">PERFIL ANIMERO</p>

              <div style="text-align:center;margin-bottom:24px;">
                <div style="font-size:52px;margin-bottom:10px;">{arq['emoji']}</div>
                <p style="font-size:26px;font-weight:700;color:#CECBF6;margin-bottom:4px;">{arq['nombre']}</p>
                <p style="font-size:12px;color:#534AB7;font-style:italic;">{arq['nivel']} · Nivel {nivel}</p>
              </div>

              <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:20px;">
                <div style="background:rgba(83,74,183,0.15);border-radius:10px;padding:12px;text-align:center;border:1px solid #2A2550;">
                  <p style="font-size:10px;color:#534AB7;margin-bottom:4px;letter-spacing:1px;">ELEMENTO</p>
                  <p style="font-size:15px;color:#CECBF6;font-weight:600;">{arq['elemento']}</p>
                </div>
                <div style="background:rgba(83,74,183,0.15);border-radius:10px;padding:12px;text-align:center;border:1px solid #2A2550;">
                  <p style="font-size:10px;color:#534AB7;margin-bottom:4px;letter-spacing:1px;">PLANETA</p>
                  <p style="font-size:15px;color:#CECBF6;font-weight:600;">{arq['planeta']}</p>
                </div>
                <div style="background:rgba(83,74,183,0.15);border-radius:10px;padding:12px;text-align:center;border:1px solid #2A2550;">
                  <p style="font-size:10px;color:#534AB7;margin-bottom:4px;letter-spacing:1px;">PODER</p>
                  <p style="font-size:15px;color:#CECBF6;font-weight:600;">{arq['poder']}</p>
                </div>
                <div style="background:rgba(83,74,183,0.15);border-radius:10px;padding:12px;text-align:center;border:1px solid #2A2550;">
                  <p style="font-size:10px;color:#534AB7;margin-bottom:4px;letter-spacing:1px;">DEBILIDAD</p>
                  <p style="font-size:15px;color:#CECBF6;font-weight:600;">{arq['debilidad']}</p>
                </div>
              </div>

              <div style="margin-bottom:20px;">
                <p style="font-size:10px;color:#534AB7;letter-spacing:2px;margin-bottom:12px;">ESTADÍSTICAS</p>
                {stats_html}
              </div>

              <div style="background:rgba(83,74,183,0.1);border-radius:10px;padding:14px;border:1px solid #2A2550;">
                <p style="font-size:12px;color:#AFA9EC;line-height:1.7;font-style:italic;">
                  "{arq['descripcion']}"
                </p>
              </div>

              {guardian_html}

            </div>
            """, unsafe_allow_html=True)