import heapq
from typing import Callable, Generic, List, Mapping, Optional, Sequence, TypeVar

Number = int | float
Point = TypeVar('Point', bound=Mapping[str, Number])
DistFunc = Callable[[Number, Number], Number]

class PointKeys(str):
    pass

# https://medium.com/@isurangawarnasooriya/exploring-kd-trees-a-comprehensive-guide-to-implementation-and-applications-in-python-3385fd56a246
class KDNode(Generic[Point]):
    def __init__(self, point: Point, k, left=None, right=None):
        self.point: Point = point  # k-dimensional point
        self.k: PointKeys = k  # axis of comparison
        self.left: Optional[KDNode] = left  # left subtree
        self.right: Optional[KDNode] = right  # right subtree

class KDTree(Generic[Point]):
    root: Optional[KDNode[Point]]
    k: int
    key_order: List[PointKeys]

    def __init__(self, points: Sequence[Point]) -> None:
        if not points:
            self.root = None
            self.k = 0
            return

        # Get all possible keys from the first point.
        all_keys = list(points[0].keys())
        self.k = len(all_keys)

        def build_tree(current_points: Sequence[Point], depth: int = 0) -> Optional[KDNode[Point]]:
            if not current_points:
                return None
            
            # --- Dynamic Axis Selection by Variance ---
            # Calculate variance for each axis for the current set of points.
            variances = []
            for key in all_keys:
                # Extract all values for the current key
                values = [p[key] for p in current_points]
                # Calculate mean
                mean = sum(values) / len(values)
                # Calculate variance
                variance = sum((v - mean) ** 2 for v in values) / len(values)
                variances.append((key, variance))
            
            # Select the axis (key) with the highest variance.
            axis, _ = max(variances, key=lambda item: item[1])
            
            # Sort points along the chosen axis and find the median.
            sorted_points = sorted(current_points, key=lambda p: p[axis])
            median_index = len(sorted_points) // 2
            median_point = sorted_points[median_index]

            # Create node and recurse.
            node = KDNode(median_point, axis)
            node.left = build_tree(sorted_points[:median_index], depth+1)
            node.right = build_tree(sorted_points[median_index+1:], depth+1)
            return node

        self.root = build_tree(points)
    
    def nearest_neighbor(self, target: Point, limit: int = 1) -> List[Optional[Point]]:
        if self.root is None or limit <= 0:
            return [None] * limit

        def euclidean_squared(x1: Number, x2: Number):
            return (x1 - x2)**2
        cumulative_dist_func = lambda p1, p2: sum(euclidean_squared(p1[k], p2[k]) for k in p1)
        
        # We use a max-heap to keep track of the `limit` closest points.
        # Since Python's heapq is a min-heap, we store (-distance, point) tuples.
        # The smallest negative distance is the largest distance.
        best_candidates: List[tuple[float, Point]] = []

        def process_branch(root: Optional[KDNode]) -> None:
            if root is None:
                return

            axis: PointKeys = root.k
            
            # Check current node against the candidates
            dist = cumulative_dist_func(target, root.point)
            
            # If the heap isn't full, add the new point.
            if len(best_candidates) < limit:
                heapq.heappush(best_candidates, (-dist, root.point))
            # If the heap is full, and this point is closer than the farthest candidate, replace it.
            elif dist <= -best_candidates[0][0]: # best_candidates[0] is the largest distance
                # heapreplace pops the top element and inserts the new element into the heap
                heapq.heapreplace(best_candidates, (-dist, root.point))

            # Determine which branch to search first
            if target[axis] < root.point[axis]:
                next_branch, other_branch = root.left, root.right
            else:
                next_branch, other_branch = root.right, root.left
            
            # Recursively search down the more promising branch
            process_branch(next_branch)

            # Check if the other branch could have a closer point (the pruning step)
            # The radius of our search sphere is the distance to the farthest candidate.
            farthest_dist = -best_candidates[0][0]
            dist_to_plane = euclidean_squared(target[axis], root.point[axis])

            # We must explore the other branch if our search sphere crosses the dividing plane,
            # or if we haven't even found `limit` candidates yet.
            if len(best_candidates) <= limit or farthest_dist > dist_to_plane:
                process_branch(other_branch)

        process_branch(self.root)
        
        # Extract points from the heap and sort them by distance (closest first)
        sorted_points: List[Optional[Point]] = [point for neg_dist, point in sorted(best_candidates, key=lambda item: -item[0])]
        
        # Pad the list with None if fewer than `limit` points were found
        num_found = len(sorted_points)
        if num_found < limit:
            sorted_points.extend([None] * (limit - num_found))
            
        return sorted_points

# for test verificaton
def brute_force_nearest(points: List[Point], target: Point, limit: int) -> List[Point]:
    """Calculates nearest neighbors by checking every point."""

    def euclidean_squared(x1: Number, x2: Number):
            return (x1 - x2)**2
    cumulative_dist_func = lambda p1, p2: sum(euclidean_squared(p1[k], p2[k]) for k in p1)
    
    # Calculate distance for all points
    distances = [(cumulative_dist_func(p, target), p) for p in points]
    
    # Sort by distance
    distances.sort(key=lambda x: x[0])
    
    # Return the top `limit` points
    return [point for dist, point in distances[:limit]]

# --- Test execution ---
def run_tests():
    """Runs tests for both buggy and corrected KD-Tree implementations."""
    # Sample data for testing
    points_2d = [
        {'x': 2, 'y': 3}, {'x': 5, 'y': 4}, {'x': 9, 'y': 6},
        {'x': 4, 'y': 7}, {'x': 8, 'y': 1}, {'x': 7, 'y': 2}
    ]
    target_2d = {'x': 8, 'y': 5}
    k = 2

    # --- Test 2: Verify the corrected code works ---
    print("\n--- Testing Corrected Code ---")
    corrected_tree = KDTree(points_2d)
    kdtree_result = corrected_tree.nearest_neighbor(target_2d, limit=k)
    print(f"Corrected KD-Tree result (k={k}): {kdtree_result}")

    # --- Test 3: Compare corrected code against brute-force ---
    print("\n--- Brute-force verification ---")
    brute_force_result = brute_force_nearest(points_2d, target_2d, limit=k)
    print(f"Brute-force result (k={k}): {brute_force_result}")
    
    # We will compare the sets of points to avoid issues with ordering
    set_kdtree = set(tuple(p.items()) for p in kdtree_result if p is not None)
    set_brute = set(tuple(p.items()) for p in brute_force_result if p is not None)

    print(f"\nAre results correct? {set_kdtree == set_brute}")


if __name__ == "__main__":
    run_tests()
