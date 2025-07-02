// import { useQuery } from "@tanstack/react-query";
import {
	useContext,
	createContext,
	useState,
	type PropsWithChildren,
} from "react";
import { useNavigate } from "react-router-dom";
import { fetchProfile, type SpotifyUserProfile } from "../lib/spotify-api";
import type { AccessTokenResponse } from "../lib/spotify-auth";

type ProviderProps = {
	user: null | SpotifyUserProfile;
	token: null | string;
	loginAction: (tokenResponse: AccessTokenResponse) => void;
	logOut: () => void;
};
const AuthContext = createContext<ProviderProps>({
	user: null,
	token: null,
	loginAction: () => {},
	logOut: () => {},
});

const AuthProvider = ({ children }: PropsWithChildren) => {
	const [user, setUser] = useState<null | SpotifyUserProfile>(null);
	const [token, setToken] = useState(localStorage.getItem("site") || null);
	const navigate = useNavigate();

	// const testQuery = useQuery({ queryKey: ["test"], queryFn: testapi });
	// console.log(testQuery.data);

	const loginAction = async (tokenResponse: AccessTokenResponse) => {
		console.log(tokenResponse);
		// Get user's profile data
		const res = await fetchProfile(tokenResponse.access_token);
		if (res) {
			console.log(res);
			setUser(res);
			setToken(tokenResponse.access_token);
			localStorage.setItem("site", tokenResponse.access_token);
			navigate("/create-playlist");
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
		<AuthContext.Provider value={{ token, user, loginAction, logOut }}>
			{children}
		</AuthContext.Provider>
	);
};

export default AuthProvider;

export const useAuth = () => {
	return useContext(AuthContext);
};
