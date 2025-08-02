from math import sqrt
from typing import List, Tuple, Dict
import heapq

FEATURE_KEYS = ["acousticness", "danceability", "energy", "instrumentalness",
                "liveness", "loudness", "speechiness", "tempo", "valence"]

def song_to_vector(trackfeatures: dict, feature_keys: list[str]) -> list[float]:
    return [trackfeatures[key] for key in feature_keys]

def euclidean_distance(vec1: list[float], vec2: list[float]) -> float:
    return sqrt(sum((a - b) ** 2 for a, b in zip(vec1, vec2)))


def build_adjacency_matrix(master_list: List[Tuple[dict, Dict[str, float]]],
                           feature_keys: List[str]) -> List[List[float]]:
    n = len(master_list)
    matrix = [[0.0] * n for _ in range(n)]

    vectors = [song_to_vector(trackfeatures, feature_keys)
               for _, trackfeatures in master_list]

    for i in range(n):
        for j in range(i + 1, n):  # matrix is symmetric
            dist = euclidean_distance(vectors[i], vectors[j])
            matrix[i][j] = dist
            matrix[j][i] = dist

    return matrix

#use to normalize features
def normalize_features(master_list: List[Tuple[dict, Dict[str, float]]],
                       feature_keys: List[str]) -> None:
    # Modify in-place: scale each feature to [0, 1]
    min_max = {key: [float("inf"), float("-inf")] for key in feature_keys}

    for _, features in master_list:
        for key in feature_keys:
            val = features[key]
            min_max[key][0] = min(min_max[key][0], val)
            min_max[key][1] = max(min_max[key][1], val)

    for _, features in master_list:
        for key in feature_keys:
            min_val, max_val = min_max[key]
            if max_val != min_val:
                features[key] = (features[key] - min_val) / (max_val - min_val)
            else:
                features[key] = 0.0  # or 1.0 — your call

def average_feature_vector(top_songs: List[Tuple[dict, Dict[str, float]]],
                           feature_keys: List[str]) -> List[float]:
    total = [0.0] * len(feature_keys)
    for _, features in top_songs:
        for i, key in enumerate(feature_keys):
            total[i] += features[key]
    count = len(top_songs)
    return [x / count for x in total]

def find_closest_song(master_list: List[Tuple[dict, Dict[str, float]]],
                      ideal_vector: List[float],
                      feature_keys: List[str]) -> int:
    min_dist = float("inf")
    closest_index = -1

    for i, (_, features) in enumerate(master_list):
        vec = song_to_vector(features, feature_keys)
        dist = euclidean_distance(vec, ideal_vector)
        if dist < min_dist:
            min_dist = dist
            closest_index = i

    return closest_index

def get_k_closest_songs(adj_matrix: List[List[float]], source_index: int, k: int) -> List[int]:
    distances = [(dist, i) for i, dist in enumerate(adj_matrix[source_index]) if i != source_index]
    closest = heapq.nsmallest(k, distances)
    return [i for _, i in closest]


def recommend_playlist(master_list: List[Tuple[dict, Dict[str, float]]],
                       top_100: List[Tuple[dict, Dict[str, float]]],
                       feature_keys: List[str],
                       adj_matrix: List[List[float]],
                       k: int = 20) -> List[dict]:
    # Step 1: average vector
    ideal_vector = average_feature_vector(top_100, feature_keys)

    # Step 2: find song closest to user profile
    center_index = find_closest_song(master_list, ideal_vector, feature_keys)

    # Step 3: get k closest songs to that
    neighbor_indices = get_k_closest_songs(adj_matrix, center_index, k)

    # Step 4: build playlist (just return trackdata)
    return [master_list[i][0] for i in neighbor_indices]


#example use

normalize_features(master_list, FEATURE_KEYS)
normalize_features(top_100, FEATURE_KEYS)
adj_matrix = build_adjacency_matrix(master_list, FEATURE_KEYS)

playlist = recommend_playlist(master_list, top_100, FEATURE_KEYS, adj_matrix, k=20)
