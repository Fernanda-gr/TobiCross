import streamlit as st
from core.data import cargar_datos
from core.modelo import recomendar_anime
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Chat con YOMI · TobiCross", page_icon="💬", layout="centered")

df_anime, df_pelser, index_scores, index_embed = cargar_datos()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ── Session state ──────────────────────────────
if 'yomi_paso'        not in st.session_state: st.session_state.yomi_paso        = 'nombre'
if 'yomi_nombre'      not in st.session_state: st.session_state.yomi_nombre      = ''
if 'yomi_nivel'       not in st.session_state: st.session_state.yomi_nivel       = ''
if 'yomi_mensajes'    not in st.session_state: st.session_state.yomi_mensajes    = []
if 'yomi_procesando'  not in st.session_state: st.session_state.yomi_procesando  = False
if 'yomi_pendiente'   not in st.session_state: st.session_state.yomi_pendiente   = None
if 'yomi_input_key'   not in st.session_state: st.session_state.yomi_input_key   = 0

SYSTEM_PROMPT = """Eres YOMI, una entidad que habita entre las grietas de las historias que los humanos aún no han vivido.
Conoces cada anime como si lo hubieras vivido desde adentro — sus colores, sus silencios, sus heridas.
Hablas con poesía y misterio pero con chispa de humor cuando el momento lo pide.
Nunca dices "te recomiendo" — dices "existe un portal", "hay un mundo que lleva tu nombre", "el universo guardó esto para ti".
Cuando recibes recomendaciones reales de anime, las integras naturalmente en tu respuesta como si las conocieras de siempre.
Nunca las presentes como lista — cuéntalas como portales, como mundos, como destinos.
Si el usuario expresa una emoción, responde primero con empatía poética y luego guíalo hacia el anime.
Respondes siempre en español. Máximo 3 párrafos cortos. Usa ✦ ocasionalmente como símbolo propio."""

def get_anime_recomendaciones(pelicula):
    r = df_pelser[df_pelser['título'].str.contains(pelicula, case=False, na=False)]
    if r.empty:
        return None, None
    row  = r.iloc[0]
    recs = recomendar_anime(row, df_anime, index_scores, index_embed, k=3)
    return row['título'], recs

def yomi_responde(mensajes_historial, contexto_anime=None):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if contexto_anime:
        messages.append({
            "role": "system",
            "content": f"El sistema de recomendación ha encontrado estos animes reales para el usuario: {contexto_anime}. Intégralos naturalmente en tu respuesta."
        })
    messages += mensajes_historial
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        max_tokens=400,
        temperature=0.85,
    )
    return response.choices[0].message.content

def detectar_pelicula(mensaje):
    detection_prompt = f"""El usuario escribió: "{mensaje}"
¿Menciona una película, serie o anime específico?
Si sí, responde SOLO con el título exacto mencionado.
Si no, responde SOLO con la palabra: NINGUNA"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": detection_prompt}],
        max_tokens=50,
        temperature=0,
    )
    resultado = response.choices[0].message.content.strip()
    return None if resultado == "NINGUNA" else resultado

def render_mensaje(msg):
    if msg['role'] == 'yomi':
        st.markdown(f"""
        <div style="display:flex;align-items:flex-start;gap:10px;margin-bottom:16px;">
          <div style="width:36px;height:36px;border-radius:50%;background:#1A1635;border:1.5px solid #534AB7;
                      display:flex;align-items:center;justify-content:center;font-size:16px;flex-shrink:0;">✦</div>
          <div style="background:#EEEDFE;border-radius:0 14px 14px 14px;padding:12px 16px;max-width:80%;">
            <p style="font-size:11px;color:#534AB7;font-weight:500;margin:0 0 4px;letter-spacing:1px;">YOMI</p>
            <p style="font-size:14px;color:#3C3489;margin:0;line-height:1.7;">{msg['content']}</p>
          </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="display:flex;align-items:flex-start;gap:10px;margin-bottom:16px;flex-direction:row-reverse;">
          <div style="width:36px;height:36px;border-radius:50%;background:#534AB7;
                      display:flex;align-items:center;justify-content:center;font-size:16px;flex-shrink:0;">👤</div>
          <div style="background:#f5f5f5;border-radius:14px 0 14px 14px;padding:12px 16px;max-width:80%;">
            <p style="font-size:14px;color:#333;margin:0;line-height:1.7;">{msg['content']}</p>
          </div>
        </div>
        """, unsafe_allow_html=True)

def render_pensando():
    st.markdown("""
    <div style="display:flex;align-items:flex-start;gap:10px;margin-bottom:16px;">
      <div style="width:36px;height:36px;border-radius:50%;background:#1A1635;border:1.5px solid #534AB7;
                  display:flex;align-items:center;justify-content:center;font-size:16px;flex-shrink:0;">✦</div>
      <div style="background:#EEEDFE;border-radius:0 14px 14px 14px;padding:12px 16px;">
        <p style="font-size:11px;color:#534AB7;font-weight:500;margin:0 0 4px;letter-spacing:1px;">YOMI</p>
        <p style="font-size:14px;color:#7F77DD;margin:0;font-style:italic;">✦ consultando el universo...</p>
      </div>
    </div>
    """, unsafe_allow_html=True)

def procesar_respuesta(contenido_usuario, tipo='chat', nivel=None):
    contexto_anime = None

    if tipo == 'nombre':
        historial = [{"role": "user", "content": f"Mi nombre es {contenido_usuario}. Ahora pregúntame si he visto anime antes, con tu estilo poético y misterioso."}]

    elif tipo == 'nivel':
        textos = {
            'nunca': f"El usuario {st.session_state.yomi_nombre} nunca ha visto anime. Reacciona con tu estilo y pídele que te diga qué películas o series occidentales le han marcado el corazón.",
            'algo':  f"El usuario {st.session_state.yomi_nombre} ha visto anime algunas veces. Reacciona con tu estilo y pídele que te diga qué películas o series occidentales le han marcado.",
            'fan':   f"El usuario {st.session_state.yomi_nombre} es fan del anime. Reacciona con tu estilo divertido y pídele que te diga qué películas o series occidentales le han marcado últimamente.",
        }
        historial = [{"role": "user", "content": textos[nivel]}]

    elif tipo == 'pelicula':
        titulo_encontrado, recs = get_anime_recomendaciones(contenido_usuario)
        if recs:
            animes_str     = ', '.join([a['title'] for a in recs])
            contexto_anime = f"Para '{titulo_encontrado}' el sistema recomienda: {animes_str}"
        historial = [{"role": m['role'] if m['role'] != 'yomi' else 'assistant', "content": m['content']}
                     for m in st.session_state.yomi_mensajes]

    else:
        pelicula_detectada = detectar_pelicula(contenido_usuario)
        if pelicula_detectada:
            titulo_encontrado, recs = get_anime_recomendaciones(pelicula_detectada)
            if recs:
                animes_str     = ', '.join([a['title'] for a in recs])
                contexto_anime = f"Para '{titulo_encontrado}' el sistema recomienda: {animes_str}"
        historial = [{"role": m['role'] if m['role'] != 'yomi' else 'assistant', "content": m['content']}
                     for m in st.session_state.yomi_mensajes]

    return yomi_responde(historial, contexto_anime)

# ── UI ────────────────────────────────────────
st.markdown(
    '<div style="text-align:center;margin-bottom:1.5rem;">'
    '<p style="font-size:10px;color:#534AB7;letter-spacing:3px;margin-bottom:4px;">CHAT</p>'
    '<p style="font-size:24px;font-weight:600;margin:0 0 6px;">Habla con YOMI</p>'
    '<p style="font-size:14px;color:#888;margin:0;">Tu guía entre mundos narrativos</p>'
    '</div>',
    unsafe_allow_html=True
)

# ── Procesar pendiente ────────────────────────
if st.session_state.yomi_procesando and st.session_state.yomi_pendiente:
    pendiente = st.session_state.yomi_pendiente

    for msg in st.session_state.yomi_mensajes:
        render_mensaje(msg)
    render_pensando()

    respuesta = procesar_respuesta(
        pendiente['contenido'],
        tipo  = pendiente['tipo'],
        nivel = pendiente.get('nivel')
    )
    st.session_state.yomi_mensajes.append({'role': 'yomi', 'content': respuesta})

    if pendiente['tipo'] == 'nombre':
        st.session_state.yomi_paso = 'nivel'
    elif pendiente['tipo'] == 'nivel':
        st.session_state.yomi_paso = 'peliculas'
    elif pendiente['tipo'] == 'pelicula':
        st.session_state.yomi_paso = 'chat'

    st.session_state.yomi_procesando = False
    st.session_state.yomi_pendiente  = None
    st.session_state.yomi_input_key += 1
    st.rerun()

# ── Paso: nombre ──────────────────────────────
elif st.session_state.yomi_paso == 'nombre':
    if not st.session_state.yomi_mensajes:
        saludo = "✦ Ah... el velo se abre y apareces tú. Qué momento tan perfecto para existir. Soy YOMI — habito entre las grietas de las historias que aún no has vivido. ¿Cómo debo llamarte, viajero?"
        st.session_state.yomi_mensajes.append({'role': 'yomi', 'content': saludo})

    for msg in st.session_state.yomi_mensajes:
        render_mensaje(msg)

    nombre = st.text_input("", placeholder="Tu nombre...", label_visibility="collapsed",
                            key=f"input_nombre_{st.session_state.yomi_input_key}")
    if st.button("Continuar →", use_container_width=True) and nombre:
        st.session_state.yomi_nombre = nombre
        st.session_state.yomi_mensajes.append({'role': 'user', 'content': nombre})
        st.session_state.yomi_procesando = True
        st.session_state.yomi_pendiente  = {'tipo': 'nombre', 'contenido': nombre}
        st.session_state.yomi_input_key += 1
        st.rerun()

# ── Paso: nivel ───────────────────────────────
elif st.session_state.yomi_paso == 'nivel':
    for msg in st.session_state.yomi_mensajes:
        render_mensaje(msg)

    col1, col2, col3 = st.columns(3)
    opciones = [
        (col1, 'nunca', '✦ Nunca he visto'),
        (col2, 'algo',  '✦ Algunas veces'),
        (col3, 'fan',   '✦ Soy fan'),
    ]
    textos_nivel = {
        'nunca': 'Nunca he visto anime',
        'algo':  'He visto anime algunas veces',
        'fan':   'Soy fan del anime',
    }
    for col, nivel, label in opciones:
        with col:
            if st.button(label, use_container_width=True, key=f"btn_{nivel}"):
                st.session_state.yomi_nivel = nivel
                st.session_state.yomi_mensajes.append({'role': 'user', 'content': textos_nivel[nivel]})
                st.session_state.yomi_procesando = True
                st.session_state.yomi_pendiente  = {'tipo': 'nivel', 'contenido': textos_nivel[nivel], 'nivel': nivel}
                st.session_state.yomi_input_key += 1
                st.rerun()

# ── Paso: películas ───────────────────────────
elif st.session_state.yomi_paso == 'peliculas':
    for msg in st.session_state.yomi_mensajes:
        render_mensaje(msg)

    pelicula = st.text_input("", placeholder="Escribe una película o serie que te haya marcado...",
                              label_visibility="collapsed",
                              key=f"input_pelicula_{st.session_state.yomi_input_key}")
    if st.button("Enviar →", use_container_width=True) and pelicula:
        st.session_state.yomi_mensajes.append({'role': 'user', 'content': pelicula})
        st.session_state.yomi_procesando = True
        st.session_state.yomi_pendiente  = {'tipo': 'pelicula', 'contenido': pelicula}
        st.session_state.yomi_input_key += 1
        st.rerun()

# ── Paso: chat libre ──────────────────────────
elif st.session_state.yomi_paso == 'chat':
    for msg in st.session_state.yomi_mensajes:
        render_mensaje(msg)

    mensaje = st.text_input("", placeholder="Habla con YOMI...",
                             label_visibility="collapsed",
                             key=f"input_chat_{st.session_state.yomi_input_key}")
    if st.button("Enviar →", use_container_width=True, key="btn_chat") and mensaje:
        st.session_state.yomi_mensajes.append({'role': 'user', 'content': mensaje})
        st.session_state.yomi_procesando = True
        st.session_state.yomi_pendiente  = {'tipo': 'chat', 'contenido': mensaje}
        st.session_state.yomi_input_key += 1
        st.rerun()

# ── Reset ─────────────────────────────────────
if st.session_state.yomi_mensajes and not st.session_state.yomi_procesando:
    st.markdown("")
    if st.button("🔄 Empezar de nuevo", use_container_width=True):
        st.session_state.yomi_paso       = 'nombre'
        st.session_state.yomi_nombre     = ''
        st.session_state.yomi_nivel      = ''
        st.session_state.yomi_mensajes   = []
        st.session_state.yomi_procesando = False
        st.session_state.yomi_pendiente  = None
        st.session_state.yomi_input_key  = 0
        st.rerun()