import heapq
import itertools
import math
from typing import Generic, List, Mapping, Optional, Sequence, Tuple, TypeVar, Dict, cast
from brute_force import brute_force_nearest

Number = int | float
Data = TypeVar('Data')
Point = TypeVar('Point', bound=Mapping[str, Number])
DataPoint = Tuple[Data, Point]
PointKey = str

def euclidean_squared(p1: Point, p2: Point) -> float:
    return sum((p1[k] - p2[k]) ** 2 for k in p1)

class BallNode(Generic[Data, Point]):
    def __init__(self, data: Data, point: Point, center: Point, radius: float, 
        left: Optional['BallNode[Data, Point]'] = None, 
        right: Optional['BallNode[Data, Point]'] = None
    ):
        self.data: Data = data
        self.point: Point = point
        self.center: Point = center
        self.radius: float = radius
        self.left: Optional[BallNode[Data, Point]] = left
        self.right: Optional[BallNode[Data, Point]] = right

    def lower_bound_sq(self, target: Point) -> float:
        d_center_sq = euclidean_squared(target, self.center)
        d_center = math.sqrt(d_center_sq)
        lb = max(0.0, d_center - self.radius)
        return lb * lb

class BallTree(Generic[Data, Point]):
    root: Optional[BallNode[Data, Point]]
    n: int

    def __init__(self, data_points: Sequence[Tuple[Data, Point]]) -> None:
        if not data_points:
            self.root = None
            self.n = 0
            return
        
        self.n = len(data_points)
        
        def compute_ball_properties(points: List[DataPoint[Data, Point]]) -> Tuple[Point, float]:
            keys = list(points[0][1].keys())
            centroid: Dict[str, float] = {k: 0.0 for k in keys}
            for _, point in points:
                for k in keys:
                    centroid[k] += point[k]
            for k in keys:
                centroid[k] /= len(points)
            
            max_radius = 0.0
            for _, point in points:
                dist_sq = 0.0
                for k in keys:
                    diff = point[k] - centroid[k]
                    dist_sq += diff * diff
                dist = math.sqrt(dist_sq)
                if dist > max_radius:
                    max_radius = dist
            return cast(Point, centroid), max_radius

        def build_tree(points: List[DataPoint[Data, Point]]) -> Optional[BallNode[Data, Point]]:
            if not points:
                return None
            if len(points) == 1:
                data, point = points[0]
                return BallNode(data, point, center=point, radius=0.0, left=None, right=None)
            
            centroid, radius = compute_ball_properties(points)
            
            p1_index = 0
            max_dist_sq = -1.0
            for i, (_, p) in enumerate(points):
                dist_sq = euclidean_squared(p, centroid)
                if dist_sq > max_dist_sq:
                    max_dist_sq = dist_sq
                    p1_index = i
            data1, point1 = points[p1_index]
            
            remaining_points = points.copy()
            del remaining_points[p1_index]
            
            if not remaining_points:
                return BallNode(data1, point1, center=centroid, radius=radius, left=None, right=None)
            
            p2_index = 0
            max_dist_sq = -1.0
            for i, (_, p) in enumerate(remaining_points):
                dist_sq = euclidean_squared(p, point1)
                if dist_sq > max_dist_sq:
                    max_dist_sq = dist_sq
                    p2_index = i
            data2, point2 = remaining_points[p2_index]
            
            set1 = []
            set2 = []
            for dp in remaining_points:
                data_p, point_p = dp
                d1 = euclidean_squared(point_p, point1)
                d2 = euclidean_squared(point_p, point2)
                if d1 <= d2:
                    set1.append(dp)
                else:
                    set2.append(dp)
            
            left_child = build_tree(set1)
            right_child = build_tree(set2)
            
            return BallNode(data1, point1, center=centroid, radius=radius, left=left_child, right=right_child)

        self.root = build_tree(list(data_points))
    
    def nearest_neighbors(self, target: Point, limit: int = 1) -> List[Optional[Data]]:
        if self.root is None or limit <= 0:
            return [None] * limit
            
        tie_breaker = itertools.count()
        best_candidates: List[Tuple[float, int, Data]] = []
        
        def process_node(node: BallNode[Data, Point]) -> None:
            dist_sq = euclidean_squared(target, node.point)
            heap_item = (-dist_sq, next(tie_breaker), node.data)
            
            if len(best_candidates) < limit:
                heapq.heappush(best_candidates, heap_item)
            elif dist_sq < -best_candidates[0][0]:
                heapq.heapreplace(best_candidates, heap_item)
            
            current_max_sq = -best_candidates[0][0] if len(best_candidates) == limit else float('inf')
            
            children = []
            if node.left is not None:
                lb_sq = node.left.lower_bound_sq(target)
                children.append((lb_sq, node.left))
            if node.right is not None:
                lb_sq = node.right.lower_bound_sq(target)
                children.append((lb_sq, node.right))
            
            children.sort(key=lambda x: x[0])
            
            for lb_sq, child in children:
                if len(best_candidates) < limit or lb_sq <= current_max_sq:
                    process_node(child)
                    if len(best_candidates) == limit:
                        current_max_sq = -best_candidates[0][0]
                    else:
                        current_max_sq = float('inf')
        
        process_node(self.root)
        
        sorted_candidates = sorted(best_candidates, key=lambda item: -item[0])
        # Create list with Optional[Data] type from the start
        sorted_data: List[Optional[Data]] = [data for _, _, data in sorted_candidates]
        
        if len(sorted_data) < limit:
            # Pad with None values
            sorted_data.extend([None] * (limit - len(sorted_data)))
            
        return sorted_data

    def calc_height(self) -> int:
        def _height(node: Optional[BallNode[Data, Point]]) -> int:
            if node is None:
                return 0
            return 1 + max(_height(node.left), _height(node.right))
        return _height(self.root)

    def calc_density(self) -> float:
        if self.n == 0:
            return 0.0
        h = self.calc_height()
        if h == 0:
            return 0.0
        max_nodes = (2 ** h) - 1
        return self.n / max_nodes

def run_tests():
    data_points_2d = [
        ('a', {'x': 2, 'y': 3}), ('b', {'x': 5, 'y': 4}), ('c', {'x': 9, 'y': 6}),
        ('d', {'x': 4, 'y': 7}), ('e', {'x': 8, 'y': 1}), ('f', {'x': 7, 'y': 2})
    ]
    limit = 3
    target_2d = {'x': 8, 'y': 5}
    
    print("\n--- Testing BallTree ---")
    ball_tree = BallTree(data_points_2d)
    balltree_result = ball_tree.nearest_neighbors(target_2d, limit)
    print(f"BallTree result (limit={limit}): {balltree_result}")
    
    print("\n--- Brute-force verification ---")
    brute_force_result = brute_force_nearest(data_points_2d, target_2d, limit)
    print(f"Brute-force result (limit={limit}): {brute_force_result}")
    
    set_balltree = set(p for p in balltree_result if p is not None)
    set_brute = set(p for p in brute_force_result if p is not None)
    print(f"\nAre results correct? {set_balltree == set_brute}")

if __name__ == "__main__":
    run_tests()