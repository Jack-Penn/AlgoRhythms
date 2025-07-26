import type { AccessTokenResponse } from "./spotify/auth";
import type { TrackObject } from "./spotify/types";
import type { Features, Weights } from "./types";

const BASE_URL = "http://127.0.0.1:8000";

const fetchAPI = async (
	endpoint: string,
	params: any = {},
	options?: RequestInit,
) => {
	const apiURL = new URL(endpoint, BASE_URL);
	apiURL.search = new URLSearchParams(params).toString();

	const response = await fetch(apiURL, options);
	if (!response.ok) {
		throw new Error("Network response was not ok");
		console.error(response);
	}
	return response.json();
};

export const getGeneratedTargetFeatures = (input: {
	mood: string;
	activity: string;
}): Promise<Features> => {
	return fetchAPI("generate-target-features", input);
};

export const getGenerateEmoji = (term: string): Promise<{ emoji: string }> => {
	return fetchAPI("generate-emoji", { term });
};

export const searchTracks = (query: string): Promise<TrackObject[] | null> => {
	return fetchAPI("search-tracks", {
		query,
	});
};

export const generatePlaylist = (
	mood: string,
	activity: string,
	length: number,
	favorite_songs: string[] | null,
	targetProfile: Features,
	weights: Weights,
	auth: AccessTokenResponse | null,
) => {
	return fetchAPI(
		"create-playlist",
		{
			mood,
			activity,
			length,
			favorite_songs: favorite_songs ? favorite_songs.join(",") : undefined,
		},
		{
			method: "POST",
			headers: {
				"Content-Type": "application/json",
			},
			body: JSON.stringify({
				weights,
				auth,
			}),
		},
	);
};
