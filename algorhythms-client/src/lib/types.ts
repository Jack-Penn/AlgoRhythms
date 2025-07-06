import type { SpotifyUserProfile } from "./spotify/types";

export type Weights = {
	acousticness: number;
	danceability: number;
	energy: number;
	instrumentalness: number;
	liveness: number;
	valence: number;
	speechiness: number;
	tempo: number;
	loudness: number;
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
