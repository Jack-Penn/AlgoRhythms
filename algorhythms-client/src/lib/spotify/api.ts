import type { SpotifyUserProfile, TrackObject } from "./types";

async function fetchSpotifyEndpoint(
	token: string,
	endpoint: string,
	params = {},
) {
	const url = new URL(endpoint, "https://api.spotify.com/v1/");
	url.search = new URLSearchParams(params).toString();

	try {
		const response = await fetch(url, {
			method: "GET",
			headers: { Authorization: `Bearer ${token}` },
		});

		if (!response.ok) {
			// Handle HTTP errors (4xx/5xx responses)
			throw new Error(`HTTP error! Status: ${response.status}`);
		}

		return await response.json();
	} catch (error) {
		// Handle both network errors and API errors
		console.error("Fetch profile failed:", error);
		return null;
	}
}

export async function fetchProfile(
	token: string,
): Promise<SpotifyUserProfile | null> {
	return fetchSpotifyEndpoint(token, "me");
}

// export async function searchTracks(
// 	token: string,
// 	query: string,
// ): Promise<TrackObject[] | null> {
// 	const data = await fetchSpotifyEndpoint(token, "search", {
// 		q: query,
// 		type: "track",
// 	});

// 	console.log(data);

// 	// Helper function to deduplicate tracks
// 	function deduplicateTracks(tracks: TrackObject[]): TrackObject[] {
// 		const seen = new Set<string>();
// 		const uniqueTracks: TrackObject[] = [];

// 		for (const track of tracks) {
// 			// Create a normalized key: lowercase track name + sorted lowercase artist names
// 			const artistKey = track.artists
// 				.map((a) => a.name.toLowerCase())
// 				.sort()
// 				.join(",");
// 			const trackKey = `${track.name.toLowerCase()}|${artistKey}`;

// 			// If we haven't seen this combination, add to results
// 			if (!seen.has(trackKey)) {
// 				seen.add(trackKey);
// 				uniqueTracks.push(track);
// 			}
// 		}

// 		return uniqueTracks;
// 	}
// 	return deduplicateTracks(data.tracks.items);
// }
