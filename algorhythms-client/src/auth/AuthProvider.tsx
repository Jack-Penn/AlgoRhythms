import {
	useContext,
	createContext,
	useState,
	type PropsWithChildren,
} from "react";
import { useNavigate } from "react-router-dom";
import { fetchProfile } from "../lib/spotify/api";
import type { AccessTokenResponse } from "../lib/spotify/auth";
import type { LoggedInUser } from "../lib/types";

type ProviderProps = {
	user: null | LoggedInUser;
	spotifyAuth: null | AccessTokenResponse;
	guestLogin: () => void;
	spotifyLogin: (tokenResponse: AccessTokenResponse) => Promise<void>;
	logOut: () => void;
};
const AuthContext = createContext<ProviderProps>({
	user: null,
	spotifyAuth: null,
	guestLogin: () => {},
	spotifyLogin: () => Promise.resolve(),
	logOut: () => {},
});

export interface ExtendedTokenResponse extends AccessTokenResponse {
	expires_at: number;
}
const AuthProvider = ({ children }: PropsWithChildren) => {
	const [user, setUser] = useState<null | LoggedInUser>(null);
	const [spotifyAuth, setSpotifyAuth] = useState<ExtendedTokenResponse | null>(
		null,
	);
	const navigate = useNavigate();

	const guestLogin = () => {
		setUser({
			display_name: "guest",
			is_guest: true,
			spotify_profile: null,
		});
	};

	const spotifyLogin = async (tokenResponse: AccessTokenResponse) => {
		console.log(tokenResponse);
		// Get user's profile data
		const spotifyProfile = await fetchProfile(tokenResponse.access_token);
		if (spotifyProfile) {
			console.log(spotifyProfile);
			setUser({
				display_name: spotifyProfile.display_name,
				is_guest: false,
				spotify_profile: spotifyProfile,
			});
			console.log(
				"expires_at",
				Math.floor(new Date().getTime() / 1000 + tokenResponse.expires_in),
			);
			setSpotifyAuth({
				...tokenResponse,
				expires_at: Math.floor(
					new Date().getTime() / 1000 + tokenResponse.expires_in,
				),
			});
			return;
		}
	};

	const logOut = () => {
		setUser(null);
		setSpotifyAuth(null);
		navigate("/login");
	};

	return (
		<AuthContext.Provider
			value={{ spotifyAuth, user, guestLogin, spotifyLogin, logOut }}
		>
			{children}
		</AuthContext.Provider>
	);
};

export default AuthProvider;

export const useAuth = () => {
	return useContext(AuthContext);
};
