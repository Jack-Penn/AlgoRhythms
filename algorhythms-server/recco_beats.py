import asyncio
import json
from random import randint
from typing import Any, TypedDict
import httpx

class ReccoBeatsAPIError(Exception):
    """Custom exception for ReccoBeats API errors"""
    def __init__(self, status_code: int, error_message: str, response_data: dict):
        self.status_code = status_code
        self.error_message = error_message
        self.response_data = response_data
        super().__init__(f"API Error {status_code}: {error_message}")
async def make_request(endpoint: str, params: dict[str, str | int | list[str]] = {}) -> dict[str, Any]:
    BASE_API_URL = "https://api.reccobeats.com/v1"
    timeout = httpx.Timeout(10.0, connect=30.0)
    max_retries = 3
    backoff_factor = 0.5  # The base delay in seconds

    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                r = await client.get(
                    BASE_API_URL + endpoint,
                    params=params,
                    headers={'Accept': 'application/json'}
                )
                r.raise_for_status()  # Raises an exception for 4xx or 5xx status codes
                return r.json()
        except (httpx.ConnectError, httpx.ReadTimeout) as e:
            if attempt < max_retries - 1:
                # Calculate delay with exponential backoff (e.g., 0.5s, 1s, 2s)
                delay = backoff_factor * (2 ** attempt)
                print(f"Network error ({type(e).__name__}). Retrying in {delay:.1f}s...")
                await asyncio.sleep(delay)
            else:
                print("Network error failed after multiple retries.")
                raise Exception(f"Network request failed after {max_retries} attempts: {e}") from e
        except httpx.HTTPStatusError as e:
            # For server errors like 500 or 503, which might also be temporary
            if e.response.status_code >= 500 and attempt < max_retries - 1:
                delay = backoff_factor * (2 ** attempt)
                print(f"Server error ({e.response.status_code}). Retrying in {delay:.1f}s...")
                await asyncio.sleep(delay)
            else:
                print(f"HTTP error {e.response.status_code}: {e.response.text}")
                raise # Non-retriable client error (like 404) or final server error

    raise Exception("Request failed after all retries.") # Should not be reached, but for safety

async def get_track_features(spotify_ids: list[str]):
    tracks_res = await make_request("/track", {"ids": ",".join(spotify_ids)})

    # Create tasks to fetch audio features for each track concurrently
    tasks = []
    for track in tracks_res["content"]:
        spotify_id = track["href"].split("/")[-1]
        # Create task for fetching audio features (passing popularity for later use)
        task = make_request(f"/track/{track['id']}/audio-features")
        tasks.append((spotify_id, track["popularity"], task))

    # Run all feature requests in parallel
    features_responses = await asyncio.gather(*(task for _, _, task in tasks))

    # Build results dictionary
    feature_map: dict[str, dict | None] = {id: None for id in spotify_ids}
    for (spotify_id, popularity), features_data in zip(
        [(s_id, pop) for s_id, pop, _ in tasks], 
        features_responses
    ):
        features_data.pop("id", None)
        feature_map[spotify_id] = {**features_data, "popularity": popularity}
    
    return feature_map

class TargetFeatures(TypedDict, total=False):
    acousticness: float | str
    danceability: float | str
    energy: float | str
    instrumentalness: float | str
    liveness: float | str
    loudness: float | str
    speechiness: float | str
    tempo: float | str
    valence: float | str
    popularity: int | str
async def get_track_reccomendations(seed_ids: list[str], target_features: TargetFeatures, limit: int):
    params: dict[str, str | int | list[str]] = {
        "size": limit,
        "seeds": ",".join(seed_ids),
        **{feature: str(value) for feature, value in target_features.items()}
    }

    res = await make_request("/track/recommendation", params)
    return res["content"]

async def test_get_track_recommendation():
    seeds =  [
        "21B4gaTWnTkuSh77iWEXdS", "102YUQbYmwdBXS7jwamI90", 
        "1kuGVB7EU95pJObxwvfwKS", "6HU7h9RYOaPRFeh0R3UeAr", "1zhvxTuSha22nsUT5Nw8gE", "6nrSo5ZWhsai0oeX257rRF", 
        "0b0Dz0Gi86SVdBxYeiQcCP", "2LU2CYKUZUc1iAErxJb1dK", "2OyX4SHk1oVRBP2dBOqRqC", "0lTDxglypMd8e8Q5hnmDnI"
    ]
    def random_seed_subset():
        length = randint(1, min(5, len(seeds)))
        subset: set[str] = set(seeds)
        while(len(subset) > length):
            subset.pop()
        return list(subset)

    # Test 1: High energy, danceable tracks   
    recommendations_1 = await get_track_reccomendations(
        limit=10,
        seed_ids=random_seed_subset(),
        target_features= {
            "energy": 0.8,
            "danceability": 0.7,
            "valence": 0.6,
            "tempo": 120
        }
    )
    print("High energy recommendations:", json.dumps(recommendations_1, indent=4))
    
    # Test 2: Acoustic, mellow tracks
    recommendations_2 = await get_track_reccomendations(
        limit=5,
        seed_ids=random_seed_subset(),
        target_features={
            "acousticness": 0.9,
            "energy": 0.3,
            "valence": 0.4,
            "instrumentalness": 0.2,
            "loudness": -20
        }
    )
    print("Acoustic recommendations:", json.dumps(recommendations_2, indent=4))
    
    # Test 3: Instrumental, ambient music   
    recommendations_3 = await get_track_reccomendations(
        limit=15,
        seed_ids=random_seed_subset(),
        target_features={
            "instrumentalness": 0.8,
            "energy": 0.2,
            "speechiness": 0.1,
            "tempo": 80,
        }
    )
    print("Instrumental recommendations:", json.dumps(recommendations_3, indent=4))
    
    # Test 4: Popular, upbeat tracks   
    recommendations_4 = await get_track_reccomendations(
        limit=20,
        seed_ids=random_seed_subset(),
            target_features= {
            "popularity": 80,
            "valence": 0.8,
            "danceability": 0.6,
        }
    )
    print("Popular upbeat recommendations:", json.dumps(recommendations_4, indent=4))
    
    # Test 5: Live performance feel   
    recommendations_5 = await get_track_reccomendations(
        limit=8,
        seed_ids=random_seed_subset(),
        target_features={
            "liveness": 0.9,
            "energy": 0.7,
            "loudness": -5,
            "acousticness": 0.6
        }
    )
    print("Live performance recommendations:",json.dumps(recommendations_5, indent=4))

async def test_get_track_features():
    spotify_track_ids = [
        "21B4gaTWnTkuSh77iWEXdS", "102YUQbYmwdBXS7jwamI90", "42UBPzRMh5yyz0EDPr6fr1", "2ipIPsgrgd0j2beDf4Ki70", 
        "1kuGVB7EU95pJObxwvfwKS", "6HU7h9RYOaPRFeh0R3UeAr", "1zhvxTuSha22nsUT5Nw8gE", "6nrSo5ZWhsai0oeX257rRF", 
        "0b0Dz0Gi86SVdBxYeiQcCP", "2LU2CYKUZUc1iAErxJb1dK", "2OyX4SHk1oVRBP2dBOqRqC", "0lTDxglypMd8e8Q5hnmDnI"
    ]
    data = await get_track_features(spotify_track_ids)

    features = {id: features for id, features in data.items() if features is not None}
    print(json.dumps(features, indent=4))

    found = [id for id, features in data.items() if features is not  None]
    print("Found: ", found)
    not_found = [id for id, features in data.items() if features is None]
    print("Not Found: ", not_found)

async def main():
    await test_get_track_recommendation()

if __name__ == "__main__":
    asyncio.run(main())