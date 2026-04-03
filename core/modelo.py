# core/modelo.py
import numpy as np
import faiss
from collections import defaultdict, Counter

from core.scoring import (
    to_set, norm, limpiar_titulo_base, calcular_todos_los_scores,
    peso_genres, peso_demog, peso_embed,
    peso_dark, peso_crime, peso_family, peso_adventure, peso_feel_good,
    peso_horror, peso_scifi, peso_fantasy, peso_romance, peso_comedy,
    peso_meta, peso_thriller, peso_action, peso_drama,
    peso_dystopia, peso_power, peso_music
)


def get_primera_temporada(title, df_anime):
    """Dado un título, devuelve la primera temporada disponible en df_anime."""
    base = limpiar_titulo_base(title)
    candidatos = df_anime[df_anime['title'].apply(
        lambda t: limpiar_titulo_base(t) == base
    )]
    if candidatos.empty:
        return None
    return candidatos.loc[candidatos['title'].apply(len).idxmin()]


def _idx_posicional(df_anime, title):
    """Devuelve el índice posicional (iloc) de un título en df_anime."""
    match = df_anime[df_anime['title'] == title]
    if match.empty:
        return None
    return df_anime.index.get_loc(match.index[0])


def construir_vector_scores(row, GENRES_FINAL, DEMOG_FINAL):
    genres_vector = np.zeros(len(GENRES_FINAL))
    for i, g in enumerate(GENRES_FINAL):
        if g in row.get('genres_clean', []):
            genres_vector[i] = 1.0
    genres_vector = norm(genres_vector)
    demog_vector  = norm(np.zeros(len(DEMOG_FINAL)))
    n_genres = len(genres_vector)
    n_demog  = len(demog_vector)
    return np.concatenate([
        genres_vector * (peso_genres / n_genres),
        demog_vector  * (peso_demog  / n_demog),
        [row.get('dark_score',      0) * peso_dark],
        [row.get('crime_score',     0) * peso_crime],
        [row.get('family_score',    0) * peso_family],
        [row.get('adventure_score', 0) * peso_adventure],
        [row.get('feel_good_score', 0) * peso_feel_good],
        [row.get('horror_score',    0) * peso_horror],
        [row.get('scifi',           0) * peso_scifi],
        [row.get('fantasy',         0) * peso_fantasy],
        [row.get('romance',         0) * peso_romance],
        [row.get('comedy_score',    0) * peso_comedy],
        [row.get('meta_score',      0) * peso_meta],
        [row.get('thriller_score',  0) * peso_thriller],
        [row.get('action_score',    0) * peso_action],
        [row.get('drama_score',     0) * peso_drama],
        [row.get('dystopia_score',  0) * peso_dystopia],
        [row.get('power_score',     0) * peso_power],
        [row.get('music_score',     0) * peso_music],
    ]).astype('float32')


def rerank(query_row, candidatos, faiss_scores, df_anime):
    gen_query = set(query_row.get('genres_clean', []))

    FAMILY_GENRES  = {'Family', 'Kids', 'Animation'}
    ROMANCE_GENRES = {'Romance', 'Drama'}

    is_horror = 'Horror' in gen_query
    if not is_horror and float(query_row.get('horror_score', 0)) > 0.2:
        is_horror = True
    is_crime     = 'Crime'     in gen_query
    is_family    = bool(gen_query & FAMILY_GENRES)
    is_romance   = bool(gen_query & ROMANCE_GENRES) and not is_horror and not is_crime
    is_action    = 'Action'    in gen_query
    is_adventure = 'Adventure' in gen_query
    is_scifi     = 'Sci-Fi'    in gen_query
    is_fantasy   = 'Fantasy'   in gen_query
    is_comedy    = 'Comedy'    in gen_query
    is_meta      = bool(gen_query & {'Parody', 'Gag Humor'})
    if not is_meta and float(query_row.get('meta_score', 0)) > 0.3:
        is_meta = True
    is_thriller  = bool(gen_query & {'Thriller', 'Mystery', 'Suspense'})
    is_dystopia  = float(query_row.get('dystopia_score', 0)) > 0.3
    is_power     = float(query_row.get('power_score',    0)) > 0.3
    is_music     = float(query_row.get('music_score',    0)) > 0.3

    is_drama = 'Drama' in gen_query and not is_romance and not is_horror
    if is_power: is_drama = False
    if is_music: is_drama = False

    is_infantil = is_family and (
        float(query_row.get('feel_good_score', 0)) > 0.5 or
        float(query_row.get('family_score',    0)) > 0.3
    )

    scores = []
    for idx, faiss_score in zip(candidatos, faiss_scores):
        anime     = df_anime.iloc[idx]
        gen_anime = (to_set(anime['genres_clean']) |
                     to_set(anime.get('themes'))   |
                     to_set(anime.get('demographic')))
        score = faiss_score * 15

        if is_horror:
            score += anime['horror_score'] * 20
            score += anime['dark_score']   * 5
            if 'Supernatural'  in gen_anime: score += 5
            if 'Psychological' in gen_anime: score += 3
            if 'Comedy' in gen_anime: score -= 10
            if 'Kids'   in gen_anime: score -= 20
            if 'Ecchi'  in gen_anime: score -= 10

        if is_crime:
            score += anime['crime_score'] * 10
            score += anime['dark_score']  * 5
            if 'Romance' in gen_anime: score -= 10
            if 'Kids'    in gen_anime: score -= 25
            if 'School'  in gen_anime: score -= 15
            if 'Ecchi'   in gen_anime: score -= 10

        if is_family:
            score += anime['feel_good_score'] * 10
            score += anime['adventure_score'] * 8
            score += anime['family_score']    * 6
            if is_infantil:
                if anime['family_score'] < 0.25:                                         score -= 40
                if anime.get('comedy_score', 0) > 0.5 and anime['family_score'] < 0.35: score -= 30
                if 'Seinen'        in gen_anime: score -= 20
                if 'Josei'         in gen_anime: score -= 20
                if 'Ecchi'         in gen_anime: score -= 50
                if 'Gore'          in gen_anime: score -= 50
                if 'Horror'        in gen_anime: score -= 40
                if 'Psychological' in gen_anime: score -= 30
                if 'Shounen' in gen_anime and anime['feel_good_score'] < 0.4: score -= 15
                if 'Action'  in gen_anime and anime['family_score']    < 0.20: score -= 20

        if is_romance:
            score += anime.get('romance', 0) * 8
            if 'Romance' in gen_anime: score += 15
            if 'Drama'   in gen_anime: score += 5
            if 'Horror'        in gen_anime: score -= 40
            if 'Gore'          in gen_anime: score -= 40
            if 'Psychological' in gen_anime: score -= 15
            if anime['horror_score'] > 0.3:  score -= 30

        if is_action or is_adventure or is_scifi or is_fantasy:
            score += anime['adventure_score'] * 10
            score += anime['dark_score']      * 5
            if 'Action'    in gen_anime: score += 5
            if 'Adventure' in gen_anime: score += 5
            if 'Sci-Fi'    in gen_anime: score += 5 + anime.get('scifi',   0) * 10
            if 'Fantasy'   in gen_anime: score += 3 + anime.get('fantasy', 0) * 8
            if anime['horror_score'] > 0.5 and anime.get('dystopia_score', 0) < 0.3: score -= 20
            if 'School'  in gen_anime: score -= 10
            if 'Romance' in gen_anime: score -= 5
            if 'Kids'    in gen_anime: score -= 10

        if is_comedy:
            score += anime.get('comedy_score',    0) * 12
            score += anime.get('feel_good_score', 0) * 6
            if 'Comedy'        in gen_anime: score += 10
            if 'Slice of Life' in gen_anime: score += 5
            if 'Gore'          in gen_anime: score -= 20
            if 'Horror'        in gen_anime: score -= 15
            if anime['dark_score'] > 0.6:    score -= 10
            if is_action and anime.get('meta_score', 0) >= 0.5:
                score += anime.get('meta_score', 0) * 15

        if is_meta:
            score += anime.get('meta_score',   0) * 15
            score += anime.get('comedy_score', 0) * 8
            if 'Parody'    in gen_anime: score += 20
            if 'Gag Humor' in gen_anime: score += 15
            if 'Comedy'    in gen_anime: score += 5
            if 'Kids'      in gen_anime: score -= 10
            if anime['dark_score'] > 0.7: score -= 15

        if is_thriller:
            score += anime.get('thriller_score', 0) * 15
            score += anime['dark_score']            * 8
            score += anime['crime_score']           * 5
            if 'Thriller'      in gen_anime: score += 10
            if 'Mystery'       in gen_anime: score += 10
            if 'Psychological' in gen_anime: score += 8
            if 'Comedy'        in gen_anime: score -= 10
            if 'Kids'          in gen_anime: score -= 25
            if 'Ecchi'         in gen_anime: score -= 15

        if is_drama:
            score += anime.get('drama_score',     0) * 12
            score += anime.get('feel_good_score', 0) * 4
            if 'Drama'         in gen_anime: score += 10
            if 'Slice of Life' in gen_anime: score += 5
            if 'Historical'    in gen_anime: score += 3
            if 'Gore'          in gen_anime: score -= 15
            if 'Ecchi'         in gen_anime: score -= 15
            if 'Kids'          in gen_anime: score -= 10

        if is_dystopia:
            score += anime.get('dystopia_score', 0) * 25
            score += anime['dark_score']            * 3
            score += anime['adventure_score']       * 5
            if 'Survival'      in gen_anime: score += 10
            if 'Psychological' in gen_anime: score += 5
            if 'Sci-Fi'        in gen_anime: score += 8
            if 'Military'      in gen_anime: score += 8
            if 'Action'        in gen_anime: score += 5
            if 'Super Power'   in gen_anime: score += 3
            if 'Kids'          in gen_anime: score -= 20
            if 'Comedy'        in gen_anime: score -= 10
            if anime['feel_good_score'] > 0.6: score -= 10

        if is_power:
            score += anime.get('power_score',  0) * 35
            score += anime['dark_score']           * 8
            score += anime.get('drama_score',  0) * 5
            if 'Psychological'   in gen_anime: score += 8
            if 'Historical'      in gen_anime: score += 5
            if 'Military'        in gen_anime: score += 5
            if 'Seinen'          in gen_anime: score += 5
            if 'Organized Crime' in gen_anime: score += 8
            if 'Kids'            in gen_anime: score -= 20
            if anime['feel_good_score'] > 0.6: score -= 15

        if is_music:
            score += anime.get('music_score',     0) * 20
            score += anime.get('feel_good_score', 0) * 5
            score += anime.get('drama_score',     0) * 3
            if 'Music'           in gen_anime: score += 10
            if 'Performing Arts' in gen_anime: score += 5
            if 'Drama'           in gen_anime: score += 3
            if 'Kids'            in gen_anime: score -= 10
            if anime['horror_score'] > 0.4: score -= 15

        scores.append((idx, score))

    scores.sort(key=lambda x: x[1], reverse=True)
    return [idx for idx, _ in scores]


def recomendar_anime(row, df_anime, index_scores, index_embed, k=5):
    gen_query     = set(row.get('genres_clean', []))
    FAMILY_GENRES = {'Family', 'Kids', 'Animation'}

    is_horror = 'Horror' in gen_query
    if not is_horror and float(row.get('horror_score', 0)) > 0.2:
        is_horror = True

    is_crime  = 'Crime' in gen_query

    is_family = bool(gen_query & FAMILY_GENRES)
    if is_family and 'Family' not in gen_query and 'Kids' not in gen_query:
        if float(row.get('dark_score', 0)) > 0.1 or float(row.get('drama_score', 0)) > 0.4:
            is_family = False

    is_action    = 'Action'    in gen_query
    is_adventure = 'Adventure' in gen_query
    is_scifi     = 'Sci-Fi'    in gen_query
    is_fantasy   = 'Fantasy'   in gen_query
    is_meta      = bool(gen_query & {'Parody', 'Gag Humor'})
    if not is_meta and float(row.get('meta_score', 0)) > 0.3:
        is_meta = True
    is_thriller  = bool(gen_query & {'Thriller', 'Mystery', 'Suspense'})
    is_dystopia  = float(row.get('dystopia_score', 0)) > 0.3
    is_power     = float(row.get('power_score',    0)) > 0.35
    is_music     = float(row.get('music_score',    0)) > 0.3

    is_romance = bool(gen_query & {'Romance', 'Drama'}) and not is_horror and not is_crime
    if is_romance and 'Romance' not in gen_query and float(row.get('romance', 0)) < 0.5:
        is_romance = False
    if not is_romance and float(row.get('romance', 0)) > 0.4:
        is_romance = True

    is_drama = 'Drama' in gen_query and float(row.get('drama_score', 0)) > 0.4 and not is_romance and not is_horror
    if is_power and float(row.get('power_score', 0)) > float(row.get('drama_score', 0)) * 0.8:
        is_drama = False
    if is_music:
        is_drama = False

    is_comedy = 'Comedy' in gen_query and float(row.get('comedy_score', 0)) > 0.3
    if is_drama and float(row.get('drama_score', 0)) > float(row.get('comedy_score', 0)):
        is_comedy = False

    is_infantil = is_family and (
        float(row.get('feel_good_score', 0)) > 0.5 or
        float(row.get('family_score',    0)) > 0.3
    )

    if is_horror or is_crime:
        peso_s, peso_e = 0.70, 0.30
    elif is_meta or is_thriller:
        peso_s, peso_e = 0.65, 0.35
    elif is_dystopia:
        peso_s, peso_e = 0.60, 0.40
    elif is_power:
        peso_s, peso_e = 0.55, 0.45
    elif is_music:
        peso_s, peso_e = 0.55, 0.45
    elif is_action or is_adventure or is_scifi or is_fantasy:
        peso_s, peso_e = 0.50, 0.50
    elif is_comedy or is_drama or is_romance:
        peso_s, peso_e = 0.40, 0.60
    else:
        peso_s, peso_e = 0.20, 0.80

    vec_scores = np.array(row['vector_scores'], dtype='float32').reshape(1, -1)
    faiss.normalize_L2(vec_scores)
    vec_embed = np.array(row['embedding'], dtype='float32').reshape(1, -1)
    faiss.normalize_L2(vec_embed)

    top_k = 400 if (is_dystopia or is_power or is_music or is_horror) else 200
    _, i_scores = index_scores.search(vec_scores, top_k)
    _, i_embed  = index_embed.search(vec_embed,   top_k)

    rrf_scores = defaultdict(float)
    k_rrf = 60
    for rank, idx in enumerate(i_scores[0]):
        rrf_scores[idx] += peso_s / (k_rrf + rank + 1)
    for rank, idx in enumerate(i_embed[0]):
        rrf_scores[idx] += peso_e / (k_rrf + rank + 1)

    if is_dystopia:
        for ai in df_anime[df_anime['dystopia_score'] >= 0.4].index:
            rrf_scores[ai] += 0.015
    if is_power:
        for ai in df_anime[df_anime['power_score'] >= 0.3].index:
            rrf_scores[ai] += 0.010
    if is_music:
        for ai in df_anime[df_anime['music_score'] >= 0.5].index:
            rrf_scores[ai] += 0.012
    if is_horror and float(row.get('horror_score', 0)) < 0.5:
        for ai in df_anime[df_anime['horror_score'] >= 0.5].index:
            rrf_scores[ai] += 0.010
    if is_fantasy and float(row.get('fantasy', 0)) > 0.6:
        for ai in df_anime[
            (df_anime['fantasy'] >= 0.7) &
            (df_anime['adventure_score'] >= 0.5)
        ].index:
            rrf_scores[ai] += 0.012
    if is_action and is_comedy:
        for ai in df_anime[
            (df_anime['meta_score'] >= 0.5) &
            (df_anime['action_score'] >= 0.5)
        ].index:
            rrf_scores[ai] += 0.015

    candidatos = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
    rrf_vals   = [rrf_scores[idx] for idx in candidatos]

    umbral_family = 0.30
    for _ in range(3):
        candidatos_f, scores_f = [], []
        for idx, fscore in zip(candidatos, rrf_vals):
            anime     = df_anime.iloc[idx]
            gen_anime = (to_set(anime['genres_clean']) |
                         to_set(anime.get('themes'))   |
                         to_set(anime.get('demographic')))

            if is_family   and any(g in gen_anime for g in ['Ecchi', 'Hentai', 'Gore']): continue
            if is_horror   and 'Kids' in gen_anime:                                       continue
            if is_romance  and anime['horror_score'] > 0.5:                               continue
            if (is_action or is_adventure) and not is_horror and anime['horror_score'] > 0.6: continue
            if is_meta     and anime.get('comedy_score', 0) < 0.1:                        continue
            if is_thriller and 'Kids' in gen_anime:                                       continue
            if is_comedy   and not is_family and anime['family_score'] > 0.8:             continue
            if is_infantil and anime['family_score'] < umbral_family:                     continue
            if is_infantil and any(g in gen_anime for g in ['Seinen', 'Josei']):          continue
            if is_crime    and anime['crime_score'] < 0.15 and anime['dark_score'] < 0.2: continue
            if is_power    and anime.get('power_score', 0) < 0.35:                        continue
            if is_power    and anime['crime_score'] > 0.5 and anime['dark_score'] < 0.2: continue
            if is_music    and anime.get('music_score', 0) < 0.5:                         continue
            if is_drama    and not is_romance and anime.get('romance', 0) > 0.8 and anime.get('drama_score', 0) < 0.4: continue
            if is_action   and is_comedy and not is_family and anime.get('comedy_score', 0) < 0.3: continue

            candidatos_f.append(idx)
            scores_f.append(fscore)
            if len(candidatos_f) >= k * 10:
                break

        if len(candidatos_f) >= k:
            break
        umbral_family -= 0.10

    reranked = rerank(row, candidatos_f, scores_f, df_anime)

    MAX_POR_CLUSTER = 3 if (is_dystopia or is_power or is_music) else 2
    vistos_titulos  = set()
    cluster_counts  = Counter()
    recomendaciones = []

    for idx in reranked:
        anime   = df_anime.iloc[idx]
        base    = limpiar_titulo_base(anime['title'])
        cluster = int(anime.get('cluster', -1))

        if base in vistos_titulos:
            continue
        if cluster != -1 and cluster_counts[cluster] >= MAX_POR_CLUSTER:
            continue

        vistos_titulos.add(base)
        cluster_counts[cluster] += 1

        # 🔥 Siempre mostrar la primera temporada
        primera = get_primera_temporada(anime['title'], df_anime)
        if primera is not None:
            idx_p = _idx_posicional(df_anime, primera['title'])
            recomendaciones.append(idx_p if idx_p is not None else idx)
        else:
            recomendaciones.append(idx)

        if len(recomendaciones) >= k:
            break

    return [df_anime.iloc[idx] for idx in recomendaciones]


def recomendar_desde_anime(anime_row, df_anime, index_scores, index_embed, k=2):
    vec_scores = np.array(anime_row['vector_scores'], dtype='float32').reshape(1, -1)
    faiss.normalize_L2(vec_scores)
    vec_embed = np.array(anime_row['embedding'], dtype='float32').reshape(1, -1)
    faiss.normalize_L2(vec_embed)

    _, i_scores = index_scores.search(vec_scores, 50)
    _, i_embed  = index_embed.search(vec_embed,   50)

    rrf_scores = defaultdict(float)
    k_rrf = 60
    for rank, idx in enumerate(i_scores[0]):
        rrf_scores[idx] += 0.5 / (k_rrf + rank + 1)
    for rank, idx in enumerate(i_embed[0]):
        rrf_scores[idx] += 0.5 / (k_rrf + rank + 1)

    candidatos = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)

    vistos_titulos = set()
    vistos_titulos.add(limpiar_titulo_base(anime_row['title']))
    cluster_counts  = Counter()
    recomendaciones = []

    for idx in candidatos:
        anime   = df_anime.iloc[idx]
        base    = limpiar_titulo_base(anime['title'])
        cluster = int(anime.get('cluster', -1))

        if base in vistos_titulos:
            continue
        if cluster != -1 and cluster_counts[cluster] >= 2:
            continue

        vistos_titulos.add(base)
        cluster_counts[cluster] += 1

        # 🔥 Siempre mostrar la primera temporada
        primera = get_primera_temporada(anime['title'], df_anime)
        if primera is not None:
            idx_p = _idx_posicional(df_anime, primera['title'])
            recomendaciones.append(df_anime.iloc[idx_p] if idx_p is not None else df_anime.iloc[idx])
        else:
            recomendaciones.append(df_anime.iloc[idx])

        if len(recomendaciones) >= k:
            break

    return recomendaciones


def preferir_primera_temporada(animes):
    """De una lista de animes, prefiere el título más corto."""
    if not animes:
        return None
    return min(animes, key=lambda a: len(str(a.get('title', ''))))