import asyncio
from typing import List, Optional, Set, Tuple, Coroutine
from spotify_api import SpotifyAPIClient, spotify_api_client, SpotifyTrack
from recco_beats import ReccoBeatsAPIClient, recco_api_client, ReccoTrackDetails, ReccoTrackFeatures, ReccoTrackID
from spotipy import Spotify
from _types import *
from gemini_api import generate_playlist_search_query
import producer_consumer as pc
from timing import Stopwatch

def _chunk_list(data: List, size: int) -> List[List]:
    """Helper to break a list into chunks of a specific size."""
    if not data:
        return []
    return [data[i:i + size] for i in range(0, len(data), size)]

class TrackListCompiler:
    """Compiles a master track list using a three-stage, concurrent pipeline architecture."""

    def __init__(self, spotify_user_access: Spotify, mood: Optional[str], activity: Optional[str], target_features: Optional[ReccoTrackFeatures], spotify_client: SpotifyAPIClient = spotify_api_client, recco_client: ReccoBeatsAPIClient = recco_api_client):
        self.sp = spotify_user_access
        self.mood = mood
        self.activity = activity
        self.target_features = target_features
        self.spotify_client = spotify_client
        self.recco_client = recco_client

        # Final data collection and state
        self.track_data_points: List[Tuple[SpotifyTrack, ReccoTrackFeatures]] = []
        self.seen_tracks: Set[str] = set()
        self.seen_tracks_lock = asyncio.Lock()

        # Pipeline 1: Processes primary tracks (e.g., top tracks, saved tracks)
        self.primary_tracks_pc = pc.ProducerConsumer(
            consumer_callback=self._consume_primary_tracks, batch_size=40
        )
        # Pipeline 2: Processes recommended tracks
        self.recco_details_pc = pc.ProducerConsumer(
            consumer_callback=self._consume_recco_details, batch_size=40
        )
        # Pipeline 3: Fetches final audio features for standardized items from the first two pipelines
        self.feature_fetch_pc = pc.ProducerConsumer(
            consumer_callback=self._consume_and_fetch_final_features, batch_size=40
        )

    async def _append_new_tracks_to_primary_pipeline(self, tracks: List[SpotifyTrack]) -> List[SpotifyTrack]:
        """Filters for unseen tracks and adds them to the primary processing pipeline."""
        new_tracks: List[SpotifyTrack] = []
        async with self.seen_tracks_lock:
            for track in tracks:
                track_key = f"{track.name}|{",".join(map(lambda a: a.name, track.artists))}"
                if track_key not in self.seen_tracks:
                    self.seen_tracks.add(track_key)
                    new_tracks.append(track)
        
        for track in new_tracks:
            await self.primary_tracks_pc.append_item(track)
        return new_tracks

    # --- Producer Definitions (Stage 1) ---

    def _create_primary_track_producer(self, track_fetch_coro: Coroutine, rec_batches: int) -> pc.ProduceBatchCallback:
        async def primary_track_producer():
            tracks: List[SpotifyTrack] = await track_fetch_coro
            added_tracks = await self._append_new_tracks_to_primary_pipeline(tracks)
            seed_ids = [SpotifyTrackID(t.id) for t in added_tracks]
            RECCO_SEED_LIMIT = 5
            seed_batches = _chunk_list(seed_ids, RECCO_SEED_LIMIT)[:rec_batches] # Limit seeds per source
            
            recco_producers = [self._create_recommended_track_producer(batch) for batch in seed_batches]
            await self.recco_details_pc.add_producers(recco_producers)
        return primary_track_producer

    def _create_recommended_track_producer(self, seed_ids: List[SpotifyTrackID]) -> pc.ProduceBatchCallback:
        async def recommended_track_producer():
            recco_tracks = await self.recco_client.get_spotify_track_recommendations(seed_ids, None, limit=40)
            async with self.seen_tracks_lock:
                unseen_recco_tracks = []
                for track in recco_tracks:
                    spotify_id = track.extract_spotify_id()
                    if spotify_id and spotify_id not in self.seen_tracks:
                        self.seen_tracks.add(spotify_id)
                        unseen_recco_tracks.append(track)
            
            for track in unseen_recco_tracks:
                await self.recco_details_pc.append_item(track)
        return recommended_track_producer

    def _create_playlists_tracks_producer(self, limit: int, track_limit: int = 50) -> pc.ProduceBatchCallback:
        async def playlists_producer():
            playlist_search_query = await generate_playlist_search_query(self.target_features, self.mood, self.activity)
            print("playlist_search_query", playlist_search_query)
            playlists = await self.spotify_client.search_playlist(self.sp, playlist_search_query, limit=10)
            producers = [self._create_single_playlist_tracks_producer(p.id, track_limit) for p in playlists[:limit]]
            await self.primary_tracks_pc.add_producers(producers)
        return playlists_producer

    def _create_single_playlist_tracks_producer(self, playlist_id: str, track_limit: int = 50) -> pc.ProduceBatchCallback:
        async def playlist_tracks_producer():
            tracks = await self.spotify_client.get_playlist_items(self.sp, playlist_id, limit=track_limit)
            await self._append_new_tracks_to_primary_pipeline(tracks)
        return playlist_tracks_producer

    # --- Consumers (Stage 2) ---

    async def _consume_primary_tracks(self, track_batch: List[SpotifyTrack]):
        """Consumes SpotifyTracks, finds their ReccoID, and produces items for the final pipeline."""
        spotify_ids = [SpotifyTrackID(track.id) for track in track_batch]
        recco_details_map = await self.recco_client.get_spotify_track_details_batch(spotify_ids)
        track_map = {SpotifyTrackID(t.id): t for t in track_batch}

        for spotify_id, details in recco_details_map.items():
            if details:
                original_track = track_map.get(spotify_id)
                if original_track:
                    await self.feature_fetch_pc.append_item((original_track, details.id))

    async def _consume_recco_details(self, recco_details_batch: List[ReccoTrackDetails]):
        """Consumes ReccoTrackDetails, finds their SpotifyTrack, and produces items for the final pipeline."""
        id_map = {details.extract_spotify_id(): details.id for details in recco_details_batch if details.extract_spotify_id()}
        
        id_chunks = _chunk_list(list(id_map.keys()), 50) # Spotify API limit
        tasks = [self.spotify_client.get_tracks_details(self.sp, chunk) for chunk in id_chunks]
        results = await asyncio.gather(*tasks)
        full_spotify_tracks: List[SpotifyTrack] = [t for sublist in results if sublist for t in sublist]

        for track in full_spotify_tracks:
            recco_id = id_map.get(SpotifyTrackID(track.id))
            if recco_id:
                # Optimized: We pass the known Recco ID directly to the next stage
                await self.feature_fetch_pc.append_item((track, recco_id))

    # --- Consumer (Stage 3) ---

    async def _consume_and_fetch_final_features(self, batch: List[Tuple[SpotifyTrack, ReccoTrackID]]):
        """Final consumer. Takes standardized items and fetches their audio features."""
        print(f"Processing final feature batch of size {len(batch)}")
        track_map = {recco_id: track for track, recco_id in batch}
        features_map = await self.recco_client.get_recco_track_features_batch(list(track_map.keys()))
        
        for recco_id, features in features_map.items():
            track = track_map.get(recco_id)
            if track and features:
                self.track_data_points.append((track, features))

    # --- Main Compile Method ---

    async def compile(self):
        print("Starting track compilation process...")
        
        # Start all three pipeline services
        await asyncio.gather(
            self.primary_tracks_pc.start(),
            self.recco_details_pc.start(),
            self.feature_fetch_pc.start()
        )
        
        # Used for small scale testing
        # initial_producers = [
        #     self._create_primary_track_producer(self.spotify_client.get_top_tracks(self.sp, limit=50, time_range="medium_term"), rec_batches=0),
        # ]
        
        # Add initial producers. They will dynamically add more producers to other pipelines.
        initial_producers = [
            self._create_primary_track_producer(self.spotify_client.get_top_tracks(self.sp, limit=100, time_range="long_term"), rec_batches=2),
            self._create_primary_track_producer(self.spotify_client.get_top_tracks(self.sp, limit=200, time_range="medium_term"), rec_batches=2),
            self._create_primary_track_producer(self.spotify_client.get_top_tracks(self.sp, limit=200, time_range="short_term"), rec_batches=2),
            self._create_primary_track_producer(self.spotify_client.get_saved_tracks(self.sp, limit=100), rec_batches=2),
            self._create_playlists_tracks_producer(limit=3, track_limit=30)
        ]
        await self.primary_tracks_pc.add_producers(initial_producers)
        
        # Graceful shutdown in sequence
        print("Waiting for primary track sources to finish...")
        await self.primary_tracks_pc.finish()
        
        print("Waiting for recommendation track sources to finish...")
        await self.recco_details_pc.finish()
        
        print("Waiting for final feature fetching to finish...")
        await self.feature_fetch_pc.finish()
        
        print(f"Final track count: {len(self.track_data_points)}")
        return self.track_data_points
    

async def test_track_compiler():
    from spotify_auth import get_spotify_clients
    _, algorhythms_account = await get_spotify_clients()
    track_compiler = TrackListCompiler(
        spotify_user_access=algorhythms_account,
        mood=None,
        activity=None,
        target_features=None
    )

    with Stopwatch() as stopwatch:
        await track_compiler.compile()
    print(f"compilation finished in {stopwatch.get_time()} s")

if __name__ == "__main__":
    asyncio.run(test_track_compiler())