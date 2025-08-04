from math import sqrt
from typing import List, Tuple, Dict
import heapq
class Adj_Matrix:
    def __init__(self,data):
        self.feature_keys =  list(data[0][1].keys())
        self.matrix = self.build_adjacency_matrix(data)

    def build_adjacency_matrix(self,master_list: List[Tuple[dict, Dict[str, float]]]) -> List[List[float]]:
        n = len(master_list)
        matrix = [[0.0] * n for _ in range(n)]

        vectors = [self.song_to_vector(trackfeatures, self.feature_keys) for _, trackfeatures in master_list]

        for i in range(n):
            for j in range(i + 1, n):  # matrix is symmetric
                dist = self.euclidean_distance(vectors[i], vectors[j])
                matrix[i][j] = dist
                matrix[j][i] = dist

        return matrix
    def song_to_vector(self,trackfeatures: dict, feature_keys: list[str]) -> list[float]:
        return [trackfeatures[key] for key in feature_keys]

    def euclidean_distance(self,vec1: list[float], vec2: list[float]) -> float:
        return sqrt(sum((a - b) ** 2 for a, b in zip(vec1, vec2)))

    def find_closest_song(self,
            master_list: List[Tuple[dict, Dict[str, float]]],
            ideal_vector: List[float],
            feature_keys: List[str]
    ) -> int:
        min_dist = float("inf")
        closest_index = -1

        for i, (_, features) in enumerate(master_list):
            vec = self.song_to_vector(features, feature_keys)
            dist = self.euclidean_distance(vec, ideal_vector)
            if dist < min_dist:
                min_dist = dist
                closest_index = i

        return closest_index

    def get_k_closest_songs(self, source_index: int, k: int) -> List[int]:
        distances = [(dist, i) for i, dist in enumerate(self.matrix[source_index]) if i != source_index]
        closest = heapq.nsmallest(k, distances, key= lambda n: n[0])
        return [i for _, i in closest]