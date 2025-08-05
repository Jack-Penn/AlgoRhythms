import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthProvider";
import "../lib/spotify/auth";
import { handleSpotifyLogin } from "../lib/spotify/auth";

const Login = () => {
	const { guestLogin } = useAuth();

	const navigate = useNavigate();

	return (
		<>
			{/* Header Section */}
			<div className='bg-gradient-to-r from-blue-600 to-purple-600 p-8 text-center'>
				<div className='flex flex-row align-middle justify-center gap-4 pb-5'>
					<div className='w-16 h-16 my-auto rounded-full border-dashed border border-white '>
						<img
							src='logo.png'
							alt='Logo'
							className='p-3 brightness-200 contrast-200 invert'
						/>
					</div>

					<h1 className='text-4xl font-bold text-white my-auto'>AlgoRhythms</h1>
				</div>
				<p className='text-blue-100 font-medium text-lg'>
					Get a playlist tailored to your mood
				</p>
			</div>

			{/* Form Section */}
			<div className='p-8'>
				<div className='space-y-5'>
					<button
						className='flex flex-row justify-center items-center gap-2 cursor-pointer w-full bg-gradient-to-r from-blue-500 to-purple-600 text-white font-semibold py-3 rounded-lg hover:opacity-90 transition-opacity shadow-md'
						onClick={handleSpotifyLogin}
					>
						<img src='spotify-logo.svg' className='w-8 h-8 invert' />
						<span>Login with Spotify</span>
					</button>
				</div>

				{/* <div className='mt-8 pt-5 border-t border-gray-200'>
					<button
						className='cursor-pointer w-full bg-gradient-to-r from-blue-500 to-purple-600 text-white font-semibold py-3 rounded-lg hover:opacity-90 transition-opacity shadow-md'
						onClick={() => {
							guestLogin();
							navigate("/create-playlist");
						}}
					>
						Continue as Guest
					</button>
				</div> */}
			</div>
		</>
	);
};

export default Login;
