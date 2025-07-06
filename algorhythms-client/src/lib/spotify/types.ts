export interface SpotifyUserProfile {
	country: string;
	display_name: string;
	email: string;
	explicit_content: {
		filter_enabled: boolean;
		filter_locked: boolean;
	};
	external_urls: { spotify: string };
	followers: { href: string; total: number };
	href: string;
	id: string;
	images: ImageObject[];
	product: string;
	type: string;
	uri: string;
}

interface ExternalUrlObject {
	spotify: string;
}

interface ImageObject {
	url: string;
	height: number | null;
	width: number | null;
}

interface SimplifiedArtistObject {
	external_urls: ExternalUrlObject;
	href: string;
	id: string;
	name: string;
	type: "artist";
	uri: string;
}

interface AlbumRestrictionObject {
	reason: "market" | "product" | "explicit" | string;
	type: "album";
}

interface SimplifiedAlbumObject {
	album_type: "album" | "single" | "compilation";
	total_tracks: number;
	available_markets: string[];
	external_urls: ExternalUrlObject;
	href: string;
	id: string;
	images: ImageObject[];
	name: string;
	release_date: string;
	release_date_precision: "year" | "month" | "day";
	restrictions?: AlbumRestrictionObject;
	type: "album";
	uri: string;
	artists: SimplifiedArtistObject[];
}

interface ExternalIdObject {
	isrc?: string;
	ean?: string;
	upc?: string;
}

interface TrackRestrictionObject {
	reason: "market" | "product" | "explicit" | string;
}

interface LinkedTrackObject {
	external_urls: ExternalUrlObject;
	href: string;
	id: string;
	type: "track";
	uri: string;
}

export interface TrackObject {
	album: SimplifiedAlbumObject;
	artists: SimplifiedArtistObject[];
	available_markets: string[];
	disc_number: number;
	duration_ms: number;
	explicit: boolean;
	external_ids: ExternalIdObject;
	external_urls: ExternalUrlObject;
	href: string;
	id: string;
	is_playable?: boolean;
	linked_from?: LinkedTrackObject;
	restrictions?: TrackRestrictionObject;
	name: string;
	popularity: number;
	preview_url: string | null;
	track_number: number;
	type: "track";
	uri: string;
	is_local: boolean;
}
