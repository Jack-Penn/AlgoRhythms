import { Navigate } from "react-router-dom";
import { handleAuthCode } from "../lib/spotify-auth";
import { useAuth } from "../auth/AuthProvider";
import { useEffect, useRef } from "react";

const LoginCallback = () => {
	const params = new URLSearchParams(window.location.search);
	const code = params.get("code");

	const { loginAction } = useAuth();

	const isLoggingIn = useRef(false); // because React.StrictMode runs useEffect twice onMount
	useEffect(() => {
		if (code && !isLoggingIn.current) {
			handleAuthCode(code).then((res) => {
				loginAction(res);
			});
			isLoggingIn.current = true;
		}
	}, []);

	if (!code && !isLoggingIn) return <Navigate to='/login' />;

	// const user = useAuth();
	// if (user.token) return <Navigate to='/create-playlist' />;
	return <div>login callback</div>;
};

export default LoginCallback;
