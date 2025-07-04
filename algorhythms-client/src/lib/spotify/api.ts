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
	images: Image[];
	product: string;
	type: string;
	uri: string;
}
interface Image {
	url: string;
	height: number;
	width: number;
}

export async function fetchProfile(
	token: string,
): Promise<SpotifyUserProfile | null> {
	try {
		const response = await fetch("https://api.spotify.com/v1/me", {
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
