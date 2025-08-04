import heapq
from typing import Generic, List, Mapping, Optional, Sequence, Tuple, TypeVar

# --- Type Aliases ---
Number = int | float
Data = TypeVar('Data')
Point = TypeVar('Point', bound=Mapping[str, Number])
DataPoint = Tuple[Data, Point]
PointKey = str

# https://medium.com/@isurangawarnasooriya/exploring-kd-trees-a-comprehensive-guide-to-implementation-and-applications-in-python-3385fd56a246
class KDNode(Generic[Data, Point]):
    def __init__(self, data_point: DataPoint, key: PointKey, left=None, right=None):
        self.data: Data = data_point[0]
        self.point: Point = data_point[1]  # k-dimensional point
        self.key: PointKey = key  # axis of comparison
        self.left: Optional[KDNode[Data, Point]] = left  # left subtree
        self.right: Optional[KDNode[Data, Point]] = right  # right subtree

class KDTree(Generic[Data, Point]):
    root: Optional[KDNode[Data, Point]]
    k: int

    def __init__(self, data_points: Sequence[Tuple[Data, Point]]) -> None:
        if not data_points:
            self.root = None
            self.k = 0
            return
        
        # Get all possible keys from the first point.
        all_keys = [PointKey(k) for k in data_points[0][1]]
        self.k = len(all_keys)

        def build_tree(current_points: Sequence[DataPoint[Data, Point]], depth: int = 0) -> Optional[KDNode[Data, Point]]:
            if not current_points:
                return None
            
            # --- Dynamic Axis Selection by Variance ---
            # Calculate variance for each axis for the current set of points.
            variances: List[Tuple[PointKey, float]] = []
            for key in all_keys:
                values: List[Number] = [p[key] for _, p in current_points]
                mean: float = sum(values) / len(values)
                variance: float = sum((v - mean) ** 2 for v in values) / len(values)
                variances.append((key, variance))
            
            # Select the axis (key) with the highest variance.
            axis, _ = max(variances, key=lambda item: item[1])
            
            # Sort points along the chosen axis and find the median.
            sorted_points = sorted(current_points, key=lambda dp: dp[1][axis])
            median_index = len(sorted_points) // 2
            median_data_point = sorted_points[median_index]
            
            # Create node and recurse.
            node = KDNode(median_data_point, key=axis)
            node.left = build_tree(sorted_points[:median_index], depth + 1)
            node.right = build_tree(sorted_points[median_index + 1:], depth + 1)
            return node

        self.root = build_tree(data_points)
    
    def nearest_neighbors(self, target: Point, limit: int = 1) -> List[Optional[Data]]:
        if self.root is None or limit <= 0:
            return [None] * limit
            
        def euclidean_squared(p1: Point, p2: Point):
            return sum((p1[k] - p2[k])**2 for k in p1)
        
        # We use a max-heap to keep track of the `limit` closest points.
        # Since Python's heapq is a min-heap, we store (-distance, point) tuples.
        # The smallest negative distance is the largest distance.
        best_candidates: List[Tuple[float, Data]] = []

        def process_branch(node: Optional[KDNode]) -> None:
            if node is None:
                return
            
            axis: PointKey = node.key
            # Check current node against the candidates
            dist = euclidean_squared(target, node.point)
            
            # If the heap isn't full, add the new point.
            if len(best_candidates) < limit:
                heapq.heappush(best_candidates, (-dist, node.data))
            # If the heap is full, and this point is closer than the farthest candidate, replace it.
            elif dist <= -best_candidates[0][0]: # best_candidates[0] is the largest distance
                # heapreplace pops the top element and inserts the new element into the heap
                heapq.heapreplace(best_candidates, (-dist, node.data))

            # Determine which branch to search first
            if target[axis] < node.point[axis]:
                next_branch, other_branch = node.left, node.right
            else:
                next_branch, other_branch = node.right, node.left
            
            # Recursively search down the more promising branch
            process_branch(next_branch)
            
            # Check if the other branch could have a closer point (the pruning step)
            # The radius of our search sphere is the distance to the farthest candidate.
            farthest_dist = -best_candidates[0][0]
            dist_to_plane = (target[axis] - node.point[axis])**2

            # We must explore the other branch if our search sphere crosses the dividing plane,
            # or if we haven't even found `limit` candidates yet.
            if len(best_candidates) < limit or farthest_dist >= dist_to_plane:
                process_branch(other_branch)

        process_branch(self.root)
        
        # Extract points from the heap and sort them by distance (closest first)
        sorted_candidates = sorted(best_candidates, key=lambda item: -item[0])
        sorted_points: List[Optional[Data]] = [data for neg_dist, data in sorted_candidates]
        
        # Pad the list with None if fewer than `limit` points were found
        if len(sorted_points) < limit:
            sorted_points.extend([None] * (limit - len(sorted_points)))
            
        return sorted_points

def brute_force_nearest(data_points: List[DataPoint[Data, Point]], target: Point, limit: int) -> List[Data]:
    """Calculates nearest neighbors by checking every point."""
    def euclidean_squared(p1: Point, p2: Point):
        return sum((p1[k] - p2[k])**2 for k in p1)
    
    # Calculate distance for all points
    distances: List[Tuple[Number, Data]] = [(euclidean_squared(point, target), data) for data, point in data_points]
    
    # Sort by distance
    distances.sort(key=lambda x: x[0])
    
    # Return the top `limit` points
    return [data for dist, data in distances[:limit]]

# --- Test execution ---
def run_tests():
    """Runs tests for the KD-Tree implementation."""
    # Sample data for testing
    data_points_2d = [
        ('a', {'x': 2, 'y': 3}), ('b', {'x': 5, 'y': 4}), ('c', {'x': 9, 'y': 6}),
        ('d', {'x': 4, 'y': 7}), ('e', {'x': 8, 'y': 1}), ('f', {'x': 7, 'y': 2})
    ]
    limit = 3
    target_2d = {'x': 8, 'y': 5}
    
    # --- Test 1: Verify the corrected code works ---
    print("\n--- Testing Corrected Code ---")
    kd_tree = KDTree(data_points_2d)
    kdtree_result = kd_tree.nearest_neighbors(target_2d, limit)
    print(f"Corrected KD-Tree result (limit={limit}): {kdtree_result}")
    
    # --- Test 2: Compare corrected code against brute-force ---
    print("\n--- Brute-force verification ---")
    brute_force_result = brute_force_nearest(data_points_2d, target_2d, limit)
    print(f"Brute-force result (limit={limit}): {brute_force_result}")
    
    # We will compare the sets of points to avoid issues with ordering
    set_kdtree = set(p for p in kdtree_result if p is not None)
    set_brute = set(p for p in brute_force_result if p is not None)
    print(f"\nAre results correct? {set_kdtree == set_brute}")

if __name__ == "__main__":
    run_tests()