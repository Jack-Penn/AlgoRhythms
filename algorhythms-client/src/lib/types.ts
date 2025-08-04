import type { SpotifyUserProfile } from "./spotify/types";

export type Features = {
	acousticness: number;
	danceability: number;
	energy: number;
	instrumentalness: number;
	liveness: number;
	valence: number;
	speechiness: number;
	tempo: number; // 0 to 250
	loudness: number; // -60 to 0
};
export type Weights = {
	acousticness_weight: number;
	danceability_weight: number;
	energy_weight: number;
	instrumentalness_weight: number;
	liveness_weight: number;
	valence_weight: number;
	speechiness_weight: number;
	tempo_weight: number;
	loudness_weight: number;

	personalization_weight: number;
	cohesion_weight: number;
};

export type LoggedInUser = {
	display_name: string;
} & (
	| {
			is_guest: true;
			spotify_profile: null;
	  }
	| {
			is_guest: false;
			spotify_profile: SpotifyUserProfile;
	  }
);
