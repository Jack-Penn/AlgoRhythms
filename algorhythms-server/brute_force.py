from typing import List, Mapping, Tuple, TypeVar

Number = int | float
Data = TypeVar('Data')
Point = TypeVar('Point', bound=Mapping[str, Number])
DataPoint = Tuple[Data, Point]
PointKey = str


def brute_force_nearest(data_points: List[Tuple[Data, Point]], target: Point, limit: int) -> List[Data]:
    """Calculates nearest neighbors by checking every point."""
    def euclidean_squared(p1: Point, p2: Point):
        return sum((p1[k] - p2[k])**2 for k in p1)
    
    # Calculate distance for all points
    distances: List[Tuple[Number, Data]] = [(euclidean_squared(point, target), data) for data, point in data_points]
    
    # Sort by distance
    distances.sort(key=lambda x: x[0])
    
    # Return the top `limit` points
    return [data for dist, data in distances[:limit]]
