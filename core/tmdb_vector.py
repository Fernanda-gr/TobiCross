import numpy as np
from core.scoring import (
    calcular_todos_los_scores,
    norm,
    peso_genres, peso_demog,
    peso_dark, peso_crime, peso_family, peso_adventure, peso_feel_good,
    peso_horror, peso_scifi, peso_fantasy, peso_romance, peso_comedy,
    peso_meta, peso_thriller, peso_action, peso_drama,
    peso_dystopia, peso_power, peso_music
)

GENRES_FINAL = [
    "Action", "Adventure", "Comedy", "Drama", "Romance",
    "Fantasy", "Sci-Fi", "Horror", "Mystery", "Suspense",
    "Psychological", "Slice of Life",
    "Historical", "Music",
    "Supernatural", "Military", "Crime", "Kids", "Sports", "Animation"
]

DEMOGRAPHIC_COLS = ['Shounen', 'Seinen', 'Shoujo', 'Josei', 'Kids']


def construir_vector_desde_tmdb(row_falso, modelo_embed=None):
    """
    Construye un vector_scores de 43 dimensiones compatible con FAISS
    usando los géneros Y la sinopsis de TMDB para calcular scores narrativos reales.
    Si se pasa modelo_embed, calcula el embedding real de la sinopsis.
    """
    import ast

    genres_list = row_falso.get('genres_clean', [])
    if isinstance(genres_list, str):
        try: genres_list = ast.literal_eval(genres_list)
        except: genres_list = []

    synopsis = row_falso.get('sinopsis', '') or row_falso.get('synopsis', '') or ''

    # ── Scores narrativos reales ───────────────────────────────────────────────
    scores = calcular_todos_los_scores(
        genres_clean=genres_list,
        themes=None,
        demographic=None,
        synopsis=synopsis
    )

    # ── Embedding real o ceros ─────────────────────────────────────────────────
    if modelo_embed is not None and synopsis:
        embedding = modelo_embed.encode(synopsis, show_progress_bar=False)
    else:
        embedding = np.zeros(384, dtype='float32')
    row_falso['embedding'] = embedding

    # ── genres_vector (20 dims, one-hot) ──────────────────────────────────────
    genres_vec = np.zeros(len(GENRES_FINAL), dtype=float)
    for g in genres_list:
        if g in GENRES_FINAL:
            genres_vec[GENRES_FINAL.index(g)] = 1.0
    genres_vec_norm = norm(genres_vec)
    n_genres = len(genres_vec_norm)

    # ── demog_vector (5 dims, cero para TMDB) ─────────────────────────────────
    demog_vec      = np.zeros(len(DEMOGRAPHIC_COLS), dtype=float)
    demog_vec_norm = demog_vec
    n_demog        = len(demog_vec_norm)

    # ── Vector final ───────────────────────────────────────────────────────────
    vector = np.concatenate([
        genres_vec_norm * (peso_genres / max(n_genres, 1)),
        demog_vec_norm  * (peso_demog  / max(n_demog,  1)),
        [scores['dark_score']      * peso_dark],
        [scores['crime_score']     * peso_crime],
        [scores['family_score']    * peso_family],
        [scores['adventure_score'] * peso_adventure],
        [scores['feel_good_score'] * peso_feel_good],
        [scores['horror_score']    * peso_horror],
        [scores['scifi']           * peso_scifi],
        [scores['fantasy']         * peso_fantasy],
        [scores['romance']         * peso_romance],
        [scores['comedy_score']    * peso_comedy],
        [scores['meta_score']      * peso_meta],
        [scores['thriller_score']  * peso_thriller],
        [scores['action_score']    * peso_action],
        [scores['drama_score']     * peso_drama],
        [scores['dystopia_score']  * peso_dystopia],
        [scores['power_score']     * peso_power],
        [scores['music_score']     * peso_music],
    ])

    return vector.astype('float32')