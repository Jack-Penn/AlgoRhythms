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

export const generatePlaylistStream = async (
	params: {
		mood: string;
		activity: string;
		length: number;
		favorite_songs: string[] | null;
		targetProfile: Features;
		weights: Weights;
		auth: AccessTokenResponse | null;
	},
	onUpdate: (chunk: any) => void,
) => {
	const {
		mood,
		activity,
		length,
		favorite_songs,
		targetProfile,
		weights,
		auth,
	} = params;

	const apiURL = new URL("generate-playlist", BASE_URL);
	apiURL.search = new URLSearchParams({
		mood,
		activity,
		length: String(length),
		...(favorite_songs && { favorite_songs: favorite_songs.join(",") }),
	}).toString();

	const response = await fetch(apiURL, {
		method: "POST",
		headers: {
			"Content-Type": "application/json",
		},
		body: JSON.stringify({
			target_features: targetProfile,
			weights,
			auth,
		}),
	});

	if (!response.body) {
		throw new Error("Response has no body");
	}

	const reader = response.body.getReader();
	const decoder = new TextDecoder();

	while (true) {
		const { value, done } = await reader.read();
		if (done) break;

		const chunkString = decoder.decode(value);
		// The server sends chunks separated by double newlines
		const chunks = chunkString.split("\n\n").filter(Boolean);
		for (const chunk of chunks) {
			try {
				const data = JSON.parse(chunk);
				onUpdate(data);
			} catch (error) {
				console.error("Error parsing stream chunk:", chunk, error);
			}
		}
	}
};
