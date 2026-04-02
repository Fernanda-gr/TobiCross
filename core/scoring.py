# scoring.py
import re
import numpy as np


def to_set(val):
    if val is None:           return set()
    if isinstance(val, set):  return val
    if isinstance(val, list): return set(val)
    if isinstance(val, str):  return {val}
    try:
        if len(val) == 0:     return set()
        return set(val)
    except:
        return set()


def norm(v):
    n = np.linalg.norm(v)
    return v / n if n > 0 else v


# ── PESOS ─────────────────────────────────────
peso_genres    = 0.50
peso_demog     = 0.20
peso_embed     = 0.20
peso_dark      = 0.3
peso_crime     = 0.6
peso_family    = 0.7
peso_adventure = 0.6
peso_feel_good = 0.3
peso_horror    = 0.8
peso_scifi     = 0.6
peso_fantasy   = 0.7
peso_romance   = 0.5
peso_comedy    = 0.5
peso_meta      = 0.6
peso_thriller  = 0.6
peso_action    = 0.5
peso_drama     = 0.4
peso_dystopia  = 0.6
peso_power     = 0.6
peso_music     = 0.6


# ── SCORES ────────────────────────────────────
def calcular_horror_score(genres, themes=None, demographic=None, synopsis=''):
    genres_set = to_set(genres) | to_set(themes) | to_set(demographic)
    synopsis   = str(synopsis).lower()
    score      = 0.0
    if 'Horror'        in genres_set: score += 0.3
    if 'Supernatural'  in genres_set: score += 0.2
    if 'Psychological' in genres_set: score += 0.2
    if 'Mystery'       in genres_set: score += 0.1
    if 'Thriller'      in genres_set: score += 0.1
    if 'Suspense'      in genres_set: score += 0.1
    if 'Gore'          in genres_set: score += 0.15
    if 'Guro'          in genres_set: score += 0.10
    keywords = [
        'ghost', 'demon', 'curse', 'haunted', 'spirit', 'paranormal',
        'possessed', 'exorcism', 'conjuring', 'supernatural', 'witch',
        'fantasma', 'demonio', 'maldición', 'espíritu', 'exorcismo',
        'sobrenatural', 'experimentos secretos', 'fuerzas oscuras',
        'criatura', 'monstruo', 'terror', 'aterrador', 'pesadilla',
        'dimension', 'dimensión', 'portal', 'anomalía', 'fenómeno',
        'creature', 'monster', 'nightmare', 'sinister', 'evil',
        'darkness', 'forbidden', 'experiment', 'laboratory',
    ]
    hits = sum(1 for kw in keywords if kw in synopsis)
    score += min(hits * 0.05, 0.3)
    return min(score, 1.0)


def calcular_crime_score(genres, themes=None, demographic=None):
    genres_set = to_set(genres) | to_set(themes) | to_set(demographic)
    score = 0.0
    if 'Crime'         in genres_set: score += 0.4
    if 'Thriller'      in genres_set: score += 0.2
    if 'Mystery'       in genres_set: score += 0.15
    if 'Psychological' in genres_set: score += 0.15
    if 'Suspense'      in genres_set: score += 0.1
    if 'Detective'     in genres_set: score += 0.1
    if 'Gore'          in genres_set: score += 0.05
    return min(score, 1.0)


def calcular_family_score(genres, themes=None, demographic=None):
    genres_set = to_set(genres) | to_set(themes) | to_set(demographic)
    score = 0.0
    if 'Family'        in genres_set: score += 0.5
    if 'Kids'          in genres_set: score += 0.4
    if 'Animation'     in genres_set: score += 0.3
    if 'Comedy'        in genres_set: score += 0.15
    if 'Fantasy'       in genres_set: score += 0.10
    if 'Adventure'     in genres_set: score += 0.10
    if 'Slice of Life' in genres_set: score += 0.10
    if 'School'        in genres_set: score += 0.05
    if 'Shounen' in genres_set and 'Ecchi' not in genres_set and 'Gore' not in genres_set:
        score += 0.05
    if 'Gore'          in genres_set: score -= 0.40
    if 'Ecchi'         in genres_set: score -= 0.40
    if 'Horror'        in genres_set: score -= 0.30
    if 'Hentai'        in genres_set: score -= 0.50
    if 'Seinen'        in genres_set: score -= 0.20
    if 'Josei'         in genres_set: score -= 0.10
    if 'Violence'      in genres_set: score -= 0.20
    if 'Psychological' in genres_set: score -= 0.10
    return max(0.0, min(score, 1.0))


def calcular_adventure_score(genres, themes=None, demographic=None):
    genres_set = to_set(genres) | to_set(themes) | to_set(demographic)
    score = 0.0
    if 'Adventure'     in genres_set: score += 0.5
    if 'Action'        in genres_set: score += 0.2
    if 'Fantasy'       in genres_set: score += 0.1
    if 'Sci-Fi'        in genres_set: score += 0.1
    if 'Shounen'       in genres_set: score += 0.1
    if 'Isekai'        in genres_set: score += 0.1
    if 'Military'      in genres_set: score += 0.1
    if 'Slice of Life' in genres_set: score -= 0.1
    if 'Romance'       in genres_set: score -= 0.1
    return max(0.0, min(score, 1.0))


def calcular_feel_good(genres, themes=None, demographic=None):
    genres_set = to_set(genres) | to_set(themes) | to_set(demographic)
    score = 0.0
    if 'Comedy'        in genres_set: score += 0.3
    if 'Slice of Life' in genres_set: score += 0.3
    if 'Family'        in genres_set: score += 0.2
    if 'Kids'          in genres_set: score += 0.15
    if 'Romance'       in genres_set: score += 0.1
    if 'Music'         in genres_set: score += 0.1
    if 'Sports'        in genres_set: score += 0.1
    if 'Iyashikei'     in genres_set: score += 0.2
    if 'Cute Girls Doing Cute Things' in genres_set: score += 0.15
    if 'Horror'        in genres_set: score -= 0.3
    if 'Gore'          in genres_set: score -= 0.4
    if 'Psychological' in genres_set: score -= 0.2
    if 'Drama'         in genres_set: score -= 0.1
    if 'Thriller'      in genres_set: score -= 0.2
    if 'Guro'          in genres_set: score -= 0.4
    if 'Violence'      in genres_set: score -= 0.2
    return max(0.0, min(score, 1.0))


def calcular_dark_score(genres, themes=None, demographic=None, synopsis=''):
    genres_set = to_set(genres) | to_set(themes) | to_set(demographic)
    synopsis   = str(synopsis).lower()
    score      = 0.0
    if 'Psychological' in genres_set: score += 0.3
    if 'Horror'        in genres_set: score += 0.3
    if 'Gore'          in genres_set: score += 0.3
    if 'Thriller'      in genres_set: score += 0.2
    if 'Mystery'       in genres_set: score += 0.15
    if 'Drama'         in genres_set: score += 0.1
    if 'Suspense'      in genres_set: score += 0.15
    if 'Crime'         in genres_set: score += 0.15
    if 'Dementia'      in genres_set: score += 0.2
    if 'Guro'          in genres_set: score += 0.25
    if 'Violence'      in genres_set: score += 0.15
    keywords = [
        'betrayal', 'manipulation', 'corruption', 'murder', 'conspiracy',
        'traición', 'manipulación', 'corrupción', 'asesinato', 'conspiración',
        'poder', 'dynasty', 'dinasti', 'venganza', 'revenge', 'greed',
        'ambición', 'ambicion', 'oscuro', 'dark', 'twisted', 'morally',
    ]
    hits = sum(1 for kw in keywords if kw in synopsis)
    score += min(hits * 0.1, 0.4)
    if 'Comedy'        in genres_set: score -= 0.2
    if 'Kids'          in genres_set: score -= 0.4
    if 'Family'        in genres_set: score -= 0.3
    if 'Slice of Life' in genres_set: score -= 0.15
    if 'Sports'        in genres_set: score -= 0.1
    if 'Iyashikei'     in genres_set: score -= 0.2
    return max(0.0, min(score, 1.0))


def calcular_fantasy(genres, themes=None, demographic=None):
    genres_set = to_set(genres) | to_set(themes) | to_set(demographic)
    score = 0.0
    if 'Fantasy'       in genres_set: score += 0.6
    if 'Magic'         in genres_set: score += 0.4
    if 'Supernatural'  in genres_set: score += 0.3
    if 'Isekai'        in genres_set: score += 0.4
    if 'Adventure'     in genres_set: score += 0.2
    if 'Mythology'     in genres_set: score += 0.2
    if 'Demons'        in genres_set: score += 0.15
    if 'Vampire'       in genres_set: score += 0.15
    if 'Sci-Fi'        in genres_set: score -= 0.3
    if 'Mecha'         in genres_set: score -= 0.3
    return max(0.0, min(score, 1.0))


def calcular_romance(genres, themes=None, demographic=None, synopsis=''):
    genres_set = to_set(genres) | to_set(themes) | to_set(demographic)
    synopsis   = str(synopsis).lower()
    score      = 0.0
    if 'Romance'       in genres_set: score += 0.6
    if 'Drama'         in genres_set: score += 0.2
    if 'Slice of Life' in genres_set: score += 0.2
    if 'Shoujo'        in genres_set: score += 0.15
    if 'Josei'         in genres_set: score += 0.10
    if 'Harem'         in genres_set: score += 0.10
    if 'Reverse Harem' in genres_set: score += 0.10
    if 'Horror'        in genres_set: score -= 0.4
    if 'Action'        in genres_set: score -= 0.1
    if 'Mecha'         in genres_set: score -= 0.2
    if 'Gore'          in genres_set: score -= 0.3
    keywords = ['love', 'amor', 'romance', 'fall in love', 'relationship',
                'enamorado', 'enamorada', 'romantic', 'lover', 'sweetheart',
                'passionate', 'affection', 'beloved', 'devotion', 'pareja']
    hits = sum(1 for kw in keywords if kw in synopsis)
    score += min(hits * 0.08, 0.4)
    return max(0.0, min(score, 1.0))


def calcular_scifi(genres, themes=None, demographic=None):
    genres_set = to_set(genres) | to_set(themes) | to_set(demographic)
    score = 0.0
    if 'Sci-Fi'        in genres_set: score += 0.6
    if 'Space'         in genres_set: score += 0.3
    if 'Mecha'         in genres_set: score += 0.3
    if 'Cyberpunk'     in genres_set: score += 0.4
    if 'Super Power'   in genres_set: score += 0.2
    if 'Military'      in genres_set: score += 0.1
    if 'Psychological' in genres_set: score += 0.1
    if 'Action'        in genres_set: score += 0.1
    if 'Adventure'     in genres_set: score += 0.1
    if 'Mystery'       in genres_set: score += 0.1
    if 'Historical'    in genres_set: score -= 0.3
    if 'Samurai'       in genres_set: score -= 0.3
    if 'Kids'          in genres_set: score -= 0.1
    if 'Fantasy'       in genres_set: score -= 0.2
    return max(0.0, min(score, 1.0))


def calcular_comedy_score(genres, themes=None, demographic=None):
    genres_set = to_set(genres) | to_set(themes) | to_set(demographic)
    score = 0.0
    if 'Comedy'        in genres_set: score += 0.5
    if 'Parody'        in genres_set: score += 0.3
    if 'Gag Humor'     in genres_set: score += 0.2
    if 'Slice of Life' in genres_set: score += 0.1
    if 'Slapstick'     in genres_set: score += 0.15
    if 'Drama'         in genres_set: score -= 0.1
    if 'Horror'        in genres_set: score -= 0.2
    if 'Psychological' in genres_set: score -= 0.1
    return max(0.0, min(score, 1.0))


def calcular_meta_score(genres, themes=None, demographic=None):
    genres_set = to_set(genres) | to_set(themes) | to_set(demographic)
    score = 0.0
    if 'Parody'    in genres_set: score += 0.5
    if 'Gag Humor' in genres_set: score += 0.3
    if 'Comedy'    in genres_set: score += 0.1
    if 'Drama'     in genres_set: score -= 0.2
    if 'Horror'    in genres_set: score -= 0.3
    return max(0.0, min(score, 1.0))


def calcular_thriller_score(genres, themes=None, demographic=None):
    genres_set = to_set(genres) | to_set(themes) | to_set(demographic)
    score = 0.0
    if 'Thriller'      in genres_set: score += 0.5
    if 'Mystery'       in genres_set: score += 0.3
    if 'Suspense'      in genres_set: score += 0.3
    if 'Psychological' in genres_set: score += 0.2
    if 'Detective'     in genres_set: score += 0.15
    if 'Comedy'        in genres_set: score -= 0.1
    if 'Slice of Life' in genres_set: score -= 0.1
    return max(0.0, min(score, 1.0))


def calcular_action_score(genres, themes=None, demographic=None):
    genres_set = to_set(genres) | to_set(themes) | to_set(demographic)
    score = 0.0
    if 'Action'        in genres_set: score += 0.5
    if 'Martial Arts'  in genres_set: score += 0.3
    if 'Military'      in genres_set: score += 0.2
    if 'Super Power'   in genres_set: score += 0.2
    if 'Shounen'       in genres_set: score += 0.1
    if 'Combat Sports' in genres_set: score += 0.2
    if 'Slice of Life' in genres_set: score -= 0.2
    if 'Romance'       in genres_set: score -= 0.1
    return max(0.0, min(score, 1.0))


def calcular_drama_score(genres, themes=None, demographic=None):
    genres_set = to_set(genres) | to_set(themes) | to_set(demographic)
    score = 0.0
    if 'Drama'         in genres_set: score += 0.5
    if 'Psychological' in genres_set: score += 0.2
    if 'Historical'    in genres_set: score += 0.1
    if 'Josei'         in genres_set: score += 0.1
    if 'Seinen'        in genres_set: score += 0.1
    if 'Tragedy'       in genres_set: score += 0.15
    if 'Comedy'        in genres_set: score -= 0.1
    if 'Gag Humor'     in genres_set: score -= 0.2
    return max(0.0, min(score, 1.0))


def calcular_dystopia_score(genres, themes=None, demographic=None, synopsis=''):
    genres_set = to_set(genres) | to_set(themes) | to_set(demographic)
    synopsis   = str(synopsis).lower()
    score      = 0.0
    if 'Sci-Fi'        in genres_set: score += 0.2
    if 'Psychological' in genres_set: score += 0.2
    if 'Military'      in genres_set: score += 0.1
    if 'Survival'      in genres_set: score += 0.3
    if 'Gore'          in genres_set: score += 0.1
    keywords = [
        'dystopia', 'dystopian', 'totalitarian', 'rebellion', 'uprising',
        'resistance', 'authoritarian', 'post-apocalyptic', 'survival',
        'arena', 'battle royale', 'oppressive regime',
        'rebelión', 'rebelde', 'rebeldes', 'capitolio', 'tributo', 'tributos',
        'distrito', 'distritos', 'supervivencia', 'sobrevivir', 'régimen',
        'totalitario', 'opresión', 'vasallaje', 'levantamiento',
        'bajo control', 'presidente', 'distopía', 'distópico',
    ]
    hits = sum(1 for kw in keywords if kw in synopsis)
    score += min(hits * 0.1, 0.5)
    if 'Comedy'        in genres_set: score -= 0.2
    if 'Slice of Life' in genres_set: score -= 0.3
    if 'Kids'          in genres_set: score -= 0.3
    return max(0.0, min(score, 1.0))


def calcular_power_score(genres, themes=None, demographic=None, synopsis=''):
    genres_set = to_set(genres) | to_set(themes) | to_set(demographic)
    synopsis   = str(synopsis).lower()
    score      = 0.0
    if 'Drama'   in genres_set: score += 0.2
    if 'Crime'   in genres_set: score += 0.2
    if 'History' in genres_set: score += 0.1
    keywords = [
        'poder', 'político', 'política', 'corporaci', 'riqueza',
        'herencia', 'sucesión', 'ambición', 'traición', 'manipulaci',
        'familia', 'dynasty', 'dinasti', 'multimillonario', 'empresa',
        'negocios', 'dominio', 'control', 'influencia', 'corrupci',
    ]
    hits = sum(1 for kw in keywords if kw in synopsis)
    score += min(hits * 0.1, 0.5)
    if 'Comedy'        in genres_set: score -= 0.1
    if 'Slice of Life' in genres_set: score -= 0.2
    if 'Kids'          in genres_set: score -= 0.3
    if 'Horror'        in genres_set: score -= 0.1
    return max(0.0, min(score, 1.0))


def calcular_music_score(genres, themes=None, demographic=None, synopsis=''):
    genres_set = to_set(genres) | to_set(themes) | to_set(demographic)
    synopsis   = str(synopsis).lower()
    score      = 0.0
    if 'Music'           in genres_set: score += 0.6
    if 'Performing Arts' in genres_set: score += 0.3
    if 'Idols (Female)'  in genres_set: score += 0.2
    if 'Idols (Male)'    in genres_set: score += 0.2
    if 'Drama'           in genres_set: score += 0.1
    if 'Slice of Life'   in genres_set: score += 0.1
    keywords = [
        'música', 'musical', 'músico', 'cantante', 'canción', 'canciones',
        'banda', 'concierto', 'jazz', 'piano', 'guitarra', 'violín',
        'compositor', 'melodía', 'ritmo', 'actuación', 'escenario',
        'pianista', 'baterista', 'instrumentista', 'conservatorio',
        'music', 'musician', 'singer', 'song', 'band', 'concert',
        'orchestra', 'instrument', 'dance', 'baile', 'bailar',
        'pianist', 'drummer', 'performer',
    ]
    hits = sum(1 for kw in keywords if kw in synopsis)
    score += min(hits * 0.15, 0.4)
    if 'Horror' in genres_set: score -= 0.3
    if 'Mecha'  in genres_set: score -= 0.2
    return max(0.0, min(score, 1.0))


# ── FUNCIÓN PRINCIPAL: calcular todos los scores ──
def calcular_todos_los_scores(genres_clean, themes=None, demographic=None, synopsis=''):
    """Calcula todos los scores para una película/serie nueva en tiempo real."""
    return {
        'horror_score':    calcular_horror_score(genres_clean, themes, demographic, synopsis),
        'crime_score':     calcular_crime_score(genres_clean, themes, demographic),
        'family_score':    calcular_family_score(genres_clean, themes, demographic),
        'adventure_score': calcular_adventure_score(genres_clean, themes, demographic),
        'feel_good_score': calcular_feel_good(genres_clean, themes, demographic),
        'dark_score':      calcular_dark_score(genres_clean, themes, demographic, synopsis),
        'fantasy':         calcular_fantasy(genres_clean, themes, demographic),
        'romance':         calcular_romance(genres_clean, themes, demographic, synopsis),
        'scifi':           calcular_scifi(genres_clean, themes, demographic),
        'comedy_score':    calcular_comedy_score(genres_clean, themes, demographic),
        'meta_score':      calcular_meta_score(genres_clean, themes, demographic),
        'thriller_score':  calcular_thriller_score(genres_clean, themes, demographic),
        'action_score':    calcular_action_score(genres_clean, themes, demographic),
        'drama_score':     calcular_drama_score(genres_clean, themes, demographic),
        'dystopia_score':  calcular_dystopia_score(genres_clean, themes, demographic, synopsis),
        'power_score':     calcular_power_score(genres_clean, themes, demographic, synopsis),
        'music_score':     calcular_music_score(genres_clean, themes, demographic, synopsis),
    }


# ── LIMPIEZA DE TÍTULOS ───────────────────────
def limpiar_titulo_base(titulo):
    titulo = titulo.lower()
    titulo = re.sub(r'[\(\[].*?[\)\]]', '', titulo)
    basura = ['movie', 'ova', 'ona', 'special', 'specials',
              'season', 'part', 'episode', 'tv', 'movies', 'the', 'a', 'an']
    for b in basura:
        titulo = re.sub(rf'\b{b}\b', '', titulo, flags=re.IGNORECASE)
    titulo = re.sub(r'\b\d+\b', '', titulo)
    titulo = re.sub(r'[:\-\.]\s+.*', '', titulo)
    titulo = re.sub(r'[^a-z0-9 ]', '', titulo)
    titulo = re.sub(r'\s+', ' ', titulo).strip()
    return " ".join(titulo.split()[:2])