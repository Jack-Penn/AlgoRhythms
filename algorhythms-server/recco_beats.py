import asyncio
from typing import Any, Dict, List, Optional
import httpx
from pydantic import BaseModel, ConfigDict, ValidationError
from _types import *

class ReccoTrackID(NamedStringType):
    """Explicit type representing a Recco Track ID."""

class ReccoArtist(BaseModel):
    """Artist information structure"""
    id: str
    name: str

class ReccoTrackDetails(BaseModel):
    """Track Details response structure"""
    id: ReccoTrackID
    trackTitle: str
    artists: List[ReccoArtist]
    durationMs: int
    href: str
    popularity: int
    isrc: Optional[str] = None
    ean: Optional[str] = None
    upc: Optional[str] = None
    availableCountries: Optional[str] = None
    model_config = ConfigDict(arbitrary_types_allowed=True)

    def extract_spotify_id(self) -> Optional[SpotifyTrackID]:
        """Extract and validate Spotify ID from track URL"""
        from urllib.parse import urlparse
        if not self.href:
            return None
        path_segment = urlparse(self.href).path.strip('/').split('/')[-1]
        clean_id = path_segment.split('?')[0].split('#')[0]
        return SpotifyTrackID(clean_id) if clean_id else None

class ReccoTrackFeatures(BaseModel):
    """Audio features structure for a recco track audio featuers"""
    acousticness: float
    danceability: float
    energy: float
    instrumentalness: float
    liveness: float
    loudness: float
    speechiness: float
    tempo: float
    valence: float

class ReccoBeatsAPIError(Exception):
            """Custom exception for API errors"""
            def __init__(self, status_code: int, error_message: str, response_data: Dict[str, Any]):
                self.status_code = status_code
                self.error_message = error_message
                self.response_data = response_data
                super().__init__(f"API Error {status_code}: {error_message}")

# --- Client Functions ---
class ReccoBeatsAPIClient:
    """Client for interacting with ReccoBeats API"""
    def __init__(self, concurrent_request_limit: int = 10):
        self.semaphore = asyncio.Semaphore(concurrent_request_limit)
        self.timeout = httpx.Timeout(10.0, connect=15.0)
    
    async def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make request to Recco Beats API with retry logic"""
        BASE_API_URL = "https://api.reccobeats.com/v1"
        max_retries = 3
        backoff_factor = 0.5

        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    async with self.semaphore:
                        response = await client.get(
                            f"{BASE_API_URL}{endpoint}",
                            params=params or {},
                            headers={'Accept': 'application/json'}
                        )
                        print("Fetching URL: ", response.url)
                    response.raise_for_status()
                    return response.json()
            except (httpx.ConnectError, httpx.ReadTimeout) as e:
                if attempt < max_retries - 1:
                    delay = backoff_factor * (2 ** attempt)
                    print(f"Network error ({type(e).__name__}). Retrying in {delay:.1f}s...")
                    await asyncio.sleep(delay)
                else:
                    raise ReccoBeatsAPIError(
                        status_code=0,
                        error_message=f"Network failure after {max_retries} attempts: {e}",
                        response_data={}
                    ) from e
            except httpx.HTTPStatusError as e:
                # Handle 429 Rate Limiting with Retry-After header
                if e.response.status_code == 429 and attempt < max_retries - 1:
                    retry_after = e.response.headers.get('Retry-After')
                    if retry_after:
                        try:
                            # Parse Retry-After as seconds (integer)
                            delay = float(retry_after)
                        except ValueError:
                            # Fallback to exponential backoff if header is invalid
                            delay = backoff_factor * (2 ** attempt)
                    else:
                        delay = backoff_factor * (2 ** attempt)
                    
                    print(f"Rate limit exceeded (429). Retrying after {delay:.1f}s...")
                    await asyncio.sleep(delay)
                    continue  # Proceed to next retry attempt
                
                # Handle 5xx server errors
                if e.response.status_code >= 500 and attempt < max_retries - 1:
                    delay = backoff_factor * (2 ** attempt)
                    print(f"Server error ({e.response.status_code}). Retrying in {delay:.1f}s...")
                    await asyncio.sleep(delay)
                else:
                    # Raise exception for non-retryable errors or final attempt failure
                    try:
                        response_data = e.response.json()
                    except Exception:
                        response_data = {}
                    
                    raise ReccoBeatsAPIError(
                        status_code=e.response.status_code,
                        error_message=f"HTTP error {e.response.status_code}: {e.response.text}",
                        response_data=response_data
                    ) from e

        raise ReccoBeatsAPIError(
            status_code=0,
            error_message="Request failed after all retries",
            response_data={}
        )
    
    async def get_spotify_track_details_batch(
        self, 
        track_ids: List[SpotifyTrackID]
    ) -> Dict[SpotifyTrackID, Optional[ReccoTrackDetails]]:
        """
        Get track details for a batch of Spotify Track IDs
        Returns dict mapping the ID to Track Details (or None if not found)
        """
        response = await self._make_request( "/track", {"ids": ",".join(track_ids)})

        track_details_map: Dict[SpotifyTrackID, Optional[ReccoTrackDetails]] = {id:None for id in track_ids}
        for item in response.get("content", []):
            try:
                track_details = ReccoTrackDetails(**item)
                spotify_id = track_details.extract_spotify_id()
                if spotify_id:
                    track_details_map[spotify_id] = track_details
            except Exception as e:
                print(e)
                pass
        return track_details_map

    async def get_recco_track_features_batch(
        self, 
        track_ids: List[ReccoTrackID]
    ) -> Dict[ReccoTrackID, ReccoTrackFeatures]:
        """
        Fetch audio features for a list of Recco track IDs
        Returns dict mapping Recco track ID to features
        """
        response = await self._make_request("/audio-features", {"ids": ",".join(track_ids)})

        track_features_map: Dict[ReccoTrackID, ReccoTrackFeatures] = {}
        for item in response.get("content", []):
            try:
                recco_id =ReccoTrackID(item["id"])
                features = ReccoTrackFeatures(**item)
                # feature normalization
                features.loudness = features.loudness / -60
                features.tempo = features.tempo / 250
                track_features_map[recco_id] = features
            except ValidationError:
                # We will skip this track instead of crashing.
                pass 
            except Exception as e:
                # Catch any other unexpected errors during parsing
                print(f"An unexpected error occurred while parsing item {item.get('id')}: {e}")
                pass
        return track_features_map

    async def get_spotify_track_recommendations(
        self,
        seed_ids: List[SpotifyTrackID],
        target_features: Optional[ReccoTrackFeatures],
        limit: int = 40
    ) -> List[ReccoTrackDetails]:
        """Get track recommendations based on seed tracks and target features"""
        params = {
            "size": limit,
            "seeds": ",".join(seed_ids),
            **{feature: str(value) for feature, value in (target_features.__dict__.items() if target_features else {})}
        }
        response = await self._make_request("/track/recommendation", params)
        
        recommendations: List[ReccoTrackDetails] = []
        for item in response.get("content", []):
            try:
                recommendations.append(ReccoTrackDetails(**item))
            except Exception as e:
                print(f"Error parsing recommendation: {e}")
        return recommendations


recco_api_client = ReccoBeatsAPIClient() # exported shared client instance

# --- Test Functions ---

async def test_get_spotify_track_details_batch(client: ReccoBeatsAPIClient):
    print("--- Testing get_spotify_track_details_batch ---")
    spotify_ids_to_test = [SpotifyTrackID("1kuGVB7EU95pJObxwvfwKS"), SpotifyTrackID("6HU7h9RYOaPRFeh0R3UeAr")]
    details_map = await client.get_spotify_track_details_batch(spotify_ids_to_test)

    print("\n--- Results for get_spotify_track_details_batch ---")
    assert len(details_map) == 2
    for track_id, details in details_map.items():
        print(f"\n> Spotify ID: {track_id}")
        if details:
            print(details.model_dump_json(indent=2))
        else:
            print("  Details not found.")
    print("-------------------------------------------------\n")

async def test_get_recco_track_features_batch(client: ReccoBeatsAPIClient):
    print("--- Testing get_recco_track_features_batch ---")
    recco_ids_to_test = [ReccoTrackID("52234343-6e15-4625-8492-9f76f3e1da7e"), ReccoTrackID("a5bc31b2-e181-43df-b281-4bae469325ba")]
    features_map = await client.get_recco_track_features_batch(recco_ids_to_test)
    
    print("\n--- Results for get_recco_track_features_batch ---")
    assert len(features_map) > 0
    for track_id, features in features_map.items():
        print(f"\n> Recco ID: {track_id}")
        if features:
            print(features.model_dump_json(indent=2))
        else:
            print("  Features not found.")
    print("------------------------------------------------\n")

async def test_get_spotify_track_recommendations(client: ReccoBeatsAPIClient):
    print("--- Testing get_spotify_track_recommendations ---")
    seed_track_ids = [SpotifyTrackID("21B4gaTWnTkuSh77iWEXdS")]
    target_features = ReccoTrackFeatures(acousticness=0.1, danceability=0.8, energy=0.9, instrumentalness=0.0, liveness=0.2, loudness=-5.0, speechiness=0.1, tempo=128.0, valence=0.7)
    limit = 3
        
    recommendations = await client.get_spotify_track_recommendations(seed_ids=seed_track_ids, target_features=target_features, limit=limit)
    
    print("\n--- Results for get_spotify_track_recommendations ---")
    if recommendations:
        for i, track in enumerate(recommendations):
            print(f"\n> Recommendation #{i+1}:")
            print(track.model_dump_json(indent=2))
    else:
        print("No recommendations found.")
    print("---------------------------------------------------\n")

async def main():
    recco_client = ReccoBeatsAPIClient()
    # Running all tests including the new helper tests
    # await test_get_spotify_track_details_batch(recco_client)
    # await test_get_recco_track_features_batch(recco_client)
    # await test_get_spotify_track_features(recco_client)
    # await test_get_spotify_track_recommendations(recco_client)

if __name__ == "__main__":
    asyncio.run(main())