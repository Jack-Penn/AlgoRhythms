import {
	useContext,
	createContext,
	useState,
	type PropsWithChildren,
} from "react";
import { useNavigate } from "react-router-dom";
import { fetchProfile } from "../lib/spotify-api";
import type { AccessTokenResponse } from "../lib/spotify-auth";
import type { LoggedInUser } from "../lib/types";

type ProviderProps = {
	user: null | LoggedInUser;
	token: null | string;
	guestLogin: () => void;
	spotifyLogin: (tokenResponse: AccessTokenResponse) => Promise<void>;
	logOut: () => void;
};
const AuthContext = createContext<ProviderProps>({
	user: null,
	token: null,
	guestLogin: () => {},
	spotifyLogin: () => Promise.resolve(),
	logOut: () => {},
});

const AuthProvider = ({ children }: PropsWithChildren) => {
	const [user, setUser] = useState<null | LoggedInUser>(null);
	const [token, setToken] = useState(localStorage.getItem("site") || null);
	const navigate = useNavigate();

	const guestLogin = () => {
		setUser({
			display_name: "guest",
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
				spotify_profile: spotifyProfile,
			});
			setToken(tokenResponse.access_token);
			localStorage.setItem("site", tokenResponse.access_token);
			return;
		}
	};

	const logOut = () => {
		setUser(null);
		setToken("");
		localStorage.removeItem("site");
		navigate("/login");
	};

	return (
		<AuthContext.Provider
			value={{ token, user, guestLogin, spotifyLogin, logOut }}
		>
			{children}
		</AuthContext.Provider>
	);
};

export default AuthProvider;

export const useAuth = () => {
	return useContext(AuthContext);
};
