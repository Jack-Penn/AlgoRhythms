import { Navigate, useNavigate } from "react-router-dom";
import { handleAuthCode } from "../lib/spotify-auth";
import { useAuth } from "../auth/AuthProvider";
import { useEffect, useRef, useState } from "react";

const LoginCallback = () => {
	const params = new URLSearchParams(window.location.search);
	const code = params.get("code");

	const { spotifyLogin, user } = useAuth();
	const navigate = useNavigate();
	const [status, setStatus] = useState<"loggingIn" | "welcome" | "error">(
		"loggingIn",
	);
	const [errorMessage, setErrorMessage] = useState("");
	const isLoggingIn = useRef(false);

	useEffect(() => {
		if (code && !isLoggingIn.current) {
			setStatus("loggingIn");
			isLoggingIn.current = true;

			handleAuthCode(code)
				.then(async (res) => {
					await spotifyLogin(res);
					setStatus("welcome");

					// Wait before navigating
					setTimeout(() => {
						navigate("/create-playlist");
					}, 1500);
				})
				.catch((error) => {
					console.error("Login failed:", error);
					setStatus("error");
					setErrorMessage(
						error.message || "Failed to authenticate with Spotify",
					);
				});
		}
	}, []);

	if (!code && !isLoggingIn.current) return <Navigate to='/login' />;

	return (
		<div className='bg-white/10 backdrop-blur-lg rounded-3xl shadow-xl p-8 max-w-md w-full text-center transition-all duration-500'>
			{status === "loggingIn" && (
				<div className='animate-fadeIn'>
					<div className='flex justify-center mb-6'>
						<div className='relative'>
							<div className='w-24 h-24 rounded-full bg-gradient-to-r from-indigo-500 to-purple-600 animate-pulse' />
							<div className='absolute inset-0 flex items-center justify-center'>
								<svg
									className='w-12 h-12 text-white animate-spin'
									xmlns='http://www.w3.org/2000/svg'
									fill='none'
									viewBox='0 0 24 24'
								>
									<circle
										className='opacity-25'
										cx='12'
										cy='12'
										r='10'
										stroke='currentColor'
										strokeWidth='4'
									></circle>
									<path
										className='opacity-75'
										fill='currentColor'
										d='M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z'
									></path>
								</svg>
							</div>
						</div>
					</div>

					<h1 className='text-3xl font-bold text-white mb-2'>
						Connecting to Spotify
					</h1>
					<p className='text-purple-200 mb-8'>
						Securely authenticating your account...
					</p>
					<div className='w-48 h-1.5 bg-white/20 rounded-full mx-auto overflow-hidden'>
						<div className='h-full bg-indigo-300 rounded-full animate-progress' />
					</div>
				</div>
			)}

			{status === "welcome" && user && (
				<div className='animate-fadeIn'>
					<div className='flex justify-center mb-6'>
						<div className='bg-gradient-to-br from-green-400 to-emerald-500 rounded-full size-24 flex'>
							<span className='m-auto font-medium text-5xl'>
								{user.display_name[0]}
							</span>
						</div>
					</div>

					<h1 className='text-3xl font-bold text-white mb-2 animate-pulse'>
						Welcome!
					</h1>
					<p className='text-2xl text-emerald-200 font-semibold mb-4'>
						Hello {user.display_name}!
					</p>
					<p className='text-purple-200'>
						Taking you to the playlist creator...
					</p>
				</div>
			)}

			{status === "error" && (
				<div className='animate-fadeIn'>
					<div className='flex justify-center mb-6'>
						<div className='bg-gradient-to-br from-red-500 to-rose-700 p-2 rounded-full'>
							<svg
								className='w-16 h-16 text-white'
								fill='none'
								stroke='currentColor'
								viewBox='0 0 24 24'
								xmlns='http://www.w3.org/2000/svg'
							>
								<path
									strokeLinecap='round'
									strokeLinejoin='round'
									strokeWidth='2'
									d='M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z'
								></path>
							</svg>
						</div>
					</div>

					<h1 className='text-3xl font-bold text-white mb-4'>Login Failed</h1>
					<p className='text-rose-200 mb-6'>{errorMessage}</p>

					<button
						onClick={() => window.location.reload()}
						className='px-6 py-3 bg-rose-600 hover:bg-rose-700 text-white font-medium rounded-full transition duration-300'
					>
						Try Again
					</button>

					<div className='mt-6'>
						<a
							href='/login'
							className='text-indigo-300 hover:text-indigo-100 transition duration-300'
						>
							← Return to Login
						</a>
					</div>
				</div>
			)}
		</div>
	);
};

export default LoginCallback;
