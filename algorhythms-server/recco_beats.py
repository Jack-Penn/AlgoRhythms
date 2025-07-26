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

    timeout = httpx.Timeout(10.0, connect=30.0)  # 30 seconds connection timeout
    
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            r = await client.get(BASE_API_URL + endpoint, params=params, headers={'Accept': 'application/json'})
            r.raise_for_status()  # Raises HTTPStatusError for 4xx/5xx responses
            
            response_data = r.json()
            
            # Check for API-specific error format
            if "error" in response_data and "status" in response_data:
                raise ReccoBeatsAPIError(
                    status_code=response_data["status"],
                    error_message=response_data["error"],
                    response_data=response_data
                )
            
            return response_data
            
        except httpx.HTTPStatusError as e:
            print(f"HTTP error {e.response.status_code}: {e.response.text}")
            raise
        except httpx.RequestError as e:
            print(f"Network error: {str(e)}")
            # Suggest network diagnostics
            raise Exception(f"Network request failed: {e}")

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
async def get_track_reccomendations(count: int, seed_ids: list[str], target_features: TargetFeatures):
    params: dict[str, str | int | list[str]] = {
        "size": count,
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
        count=10,
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
        count=5,
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
        count=15,
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
        count=20,
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
        count=8,
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