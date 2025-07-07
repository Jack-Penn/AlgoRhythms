const CLIENT_ID = import.meta.env.VITE_SPOTIFY_CLIENT_ID;

const REDIRECT_URI = "http://[::1]:5173/login/callback";

export function handleSpotifyLogin() {
	redirectToAuthCodeFlow(CLIENT_ID);
}

export async function handleAuthCode(code: string) {
	return await getAccessToken(CLIENT_ID, code);
}

async function redirectToAuthCodeFlow(CLIENT_ID: string) {
	const verifier = generateCodeVerifier(128);
	const challenge = await generateCodeChallenge(verifier);

	localStorage.setItem("verifier", verifier);

	const authUrl = new URL("https://accounts.spotify.com/authorize");

	const params = {
		client_id: CLIENT_ID,
		response_type: "code",
		redirect_uri: REDIRECT_URI,
		// state: "" //TODO:  Prevent CSRF attack
		scope:
			"user-read-private user-read-email playlist-modify-public playlist-modify-private",
		code_challenge_method: "S256",
		code_challenge: challenge,
	};

	authUrl.search = new URLSearchParams(params).toString();
	document.location = authUrl.toString();
}

function generateCodeVerifier(length: number) {
	// generates cryptographic random string
	const possible =
		"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
	const values = crypto.getRandomValues(new Uint8Array(length));
	return values.reduce((acc, x) => acc + possible[x % possible.length], "");
}

async function generateCodeChallenge(codeVerifier: string) {
	// performs SHA256 hash on verifier
	const data = new TextEncoder().encode(codeVerifier);
	const digest = await crypto.subtle.digest("SHA-256", data);
	// base64 encodes the hash
	return btoa(String.fromCharCode.apply(null, [...new Uint8Array(digest)]))
		.replace(/\+/g, "-")
		.replace(/\//g, "_")
		.replace(/=+$/, "");
}

export type AccessTokenResponse = {
	access_token: string;
	token_type: "Bearer";
	scope: string;
	expires_in: number;
	refresh_token: string;
};
async function getAccessToken(
	CLIENT_ID: string,
	code: string,
): Promise<AccessTokenResponse> {
	const verifier = localStorage.getItem("verifier")!;

	const params = {
		client_id: CLIENT_ID,
		grant_type: "authorization_code",
		code,
		redirect_uri: REDIRECT_URI, // used for validation
		code_verifier: verifier,
	};

	const result = await fetch("https://accounts.spotify.com/api/token", {
		method: "POST",
		headers: { "Content-Type": "application/x-www-form-urlencoded" },
		body: new URLSearchParams(params),
	});

	return await result.json();
}
