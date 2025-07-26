import asyncio
from typing import Any
import httpx

class ReccoBeatsAPIError(Exception):
    """Custom exception for ReccoBeats API errors"""
    def __init__(self, status_code: int, error_message: str, response_data: dict):
        self.status_code = status_code
        self.error_message = error_message
        self.response_data = response_data
        super().__init__(f"API Error {status_code}: {error_message}")

async def make_request(endpoint: str, params: dict[str, str | list[str]] = {}) -> dict[str, Any]:
    BASE_API_URL = "https://api.reccobeats.com/v1"
    
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(BASE_API_URL + endpoint, params=params)
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
            # Handle HTTP errors (4xx, 5xx)
            try:
                error_data = e.response.json()
                if "error" in error_data:
                    raise ReccoBeatsAPIError(
                        status_code=error_data.get("status", e.response.status_code),
                        error_message=error_data["error"],
                        response_data=error_data
                    )
            except ValueError:
                # Response isn't JSON
                pass
            raise  # Re-raise the original HTTP error
            
        except httpx.RequestError as e:
            # Handle network/connection errors
            raise Exception(f"Network error occurred: {e}")

async def get_track_features(spotify_ids: list[str]):
    tracks_res = await make_request("/track", {"ids": spotify_ids})

    feature_map: dict[str, dict | None] = {id: None for id in spotify_ids}

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
        # Remove internal id from features and add popularity
        features_data.pop("id", None)
        feature_map[spotify_id] = {**features_data, "popularity": popularity}
    
    return feature_map


async def main():
    features = await get_track_features(["21B4gaTWnTkuSh77iWEXdS", "102YUQbYmwdBXS7jwamI90", "42UBPzRMh5yyz0EDPr6fr1", "2ipIPsgrgd0j2beDf4Ki70"])
    print(features)

if __name__ == "__main__":
    asyncio.run(main())