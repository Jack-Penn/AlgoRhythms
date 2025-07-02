import { useState } from "react";

const DarkGlassLogin = () => {
	const [username, setUsername] = useState("");
	const [password, setPassword] = useState("");
	const [isFocused, setIsFocused] = useState(false);

	return (
		<div className=' flex items-center justify-center bg-gradient-to-br from-gray-900 via-indigo-900 to-purple-900 p-4 overflow-hidden'>
			{/* Liquid Glass Background Elements */}
			<div className='absolute top-1/4 -left-20 w-96 h-96 bg-indigo-700/30 rounded-full blur-[100px] animate-morph'></div>
			<div className='absolute bottom-1/3 -right-20 w-80 h-80 bg-purple-700/40 rounded-full blur-[90px] animate-morph-delay'></div>
			<div className='absolute top-1/3 right-1/4 w-72 h-72 bg-blue-700/20 rounded-full blur-[80px] animate-morph-delay-2'></div>

			{/* Floating bubbles for liquid effect */}
			<div className='absolute top-1/4 right-10 w-8 h-8 bg-indigo-500/40 rounded-full blur-md animate-float'></div>
			<div className='absolute bottom-1/3 left-12 w-10 h-10 bg-purple-500/30 rounded-full blur-[10px] animate-float-delay'></div>
			<div className='absolute top-1/3 right-1/4 w-12 h-12 bg-blue-500/20 rounded-full blur-lg animate-float-delay-2'></div>

			{/* Main Glass Card */}
			<div className='relative w-full max-w-md z-10'>
				{/* Liquid Glass Effect Container */}
				<div className='absolute -inset-3 rounded-3xl bg-gradient-to-br from-indigo-700/20 via-purple-700/15 to-blue-700/25 backdrop-blur-3xl shadow-2xl shadow-indigo-900/30 animate-pulse-slow'></div>

				{/* Liquid Glass Effect Overlay */}
				<div className='absolute inset-0 rounded-3xl bg-gradient-to-br from-gray-800/30 to-gray-900/40 backdrop-blur-[120px] border border-indigo-500/30'></div>

				{/* Content Container */}
				<div className='relative w-full max-w-md bg-gray-900/20 backdrop-blur-[100px] rounded-3xl border border-indigo-500/30 shadow-2xl shadow-purple-900/20 overflow-hidden'>
					{/* Header Section */}
					<div className='p-8 text-center relative overflow-hidden'>
						{/* Header Liquid Glass Effect */}
						<div className='absolute inset-0 bg-gradient-to-r from-indigo-600/15 to-purple-700/15 backdrop-blur-[60px] z-0'></div>

						<div className='relative z-10 flex flex-col items-center gap-4'>
							{/* Logo with Liquid Glass Effect */}
							<div className='w-24 h-24 rounded-full bg-gradient-to-br from-gray-800/40 to-gray-900/10 backdrop-blur-sm border-2 border-indigo-500/30 flex items-center justify-center shadow-lg shadow-purple-900/10'>
								<div className='bg-gradient-to-r from-indigo-600 to-purple-700 w-16 h-16 rounded-full flex items-center justify-center shadow-inner shadow-indigo-400/30'>
									<svg
										xmlns='http://www.w3.org/2000/svg'
										className='h-10 w-10 text-indigo-200'
										viewBox='0 0 20 20'
										fill='currentColor'
									>
										<path d='M18 3a1 1 0 00-1.196-.98l-10 2A1 1 0 006 5v9.114A4.369 4.369 0 005 14c-1.657 0-3 .895-3 2s1.343 2 3 2 3-.895 3-2V7.82l8-1.6v5.894A4.37 4.37 0 0015 12c-1.657 0-3 .895-3 2s1.343 2 3 2 3-.895 3-2V3z' />
									</svg>
								</div>
							</div>

							<div className='space-y-2'>
								<h1 className='text-4xl font-bold bg-gradient-to-r from-indigo-300 to-purple-300 bg-clip-text text-transparent drop-shadow-lg'>
									AlgoRhythms
								</h1>
								<p className='text-indigo-200/80 font-medium text-lg'>
									Get a playlist tailored to your mood
								</p>
							</div>
						</div>
					</div>

					{/* Form Section */}
					<div className='p-8 relative'>
						<div className='space-y-6'>
							<div>
								<div className='relative'>
									<input
										type='text'
										value={username}
										onChange={(e) => setUsername(e.target.value)}
										onFocus={() => setIsFocused(true)}
										onBlur={() => setIsFocused(false)}
										className='w-full px-4 py-3.5 bg-gray-800/40 backdrop-blur-lg border border-indigo-500/30 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500/30 placeholder:text-indigo-200/60 text-indigo-100 font-medium shadow-inner shadow-indigo-900/20'
										placeholder='Username / Email'
									/>
									<div className='absolute inset-0 rounded-xl bg-gradient-to-r from-transparent via-indigo-500/20 to-transparent opacity-0 hover:opacity-100 transition-opacity pointer-events-none'></div>
								</div>
							</div>

							<div>
								<div className='relative'>
									<input
										type='password'
										value={password}
										onChange={(e) => setPassword(e.target.value)}
										onFocus={() => setIsFocused(true)}
										onBlur={() => setIsFocused(false)}
										className='w-full px-4 py-3.5 bg-gray-800/40 backdrop-blur-lg border border-indigo-500/30 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500/30 placeholder:text-indigo-200/60 text-indigo-100 font-medium shadow-inner shadow-indigo-900/20'
										placeholder='Enter your password'
									/>
									<div className='absolute inset-0 rounded-xl bg-gradient-to-r from-transparent via-indigo-500/20 to-transparent opacity-0 hover:opacity-100 transition-opacity pointer-events-none'></div>
								</div>
							</div>

							<button className='w-full bg-gradient-to-r from-indigo-600/90 to-purple-700/90 text-indigo-50 font-semibold py-4 rounded-xl hover:shadow-xl hover:shadow-indigo-700/40 transition-all duration-300 transform hover:-translate-y-0.5 active:translate-y-0 shadow-lg shadow-indigo-900/30 relative overflow-hidden group'>
								<span className='relative z-10'>Login</span>
								<div className='absolute inset-0 bg-gradient-to-r from-indigo-400/30 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300'></div>
								<div className='absolute inset-0 bg-gradient-to-r from-indigo-700 to-purple-800 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300'></div>
							</button>
						</div>

						<div className='mt-8 pt-6 border-t border-indigo-500/20'>
							<button className='w-full bg-gray-800/30 backdrop-blur-lg text-indigo-200 font-semibold py-3.5 rounded-xl hover:bg-gray-800/40 transition-all duration-300 border border-indigo-500/30 shadow-sm shadow-indigo-900/10 relative overflow-hidden'>
								<span className='relative z-10'>Continue as Guest</span>
								<div className='absolute inset-0 bg-gradient-to-r from-transparent via-indigo-500/20 to-transparent opacity-0 hover:opacity-100 transition-opacity'></div>
							</button>
						</div>
					</div>
				</div>
			</div>
		</div>
	);
};

export default DarkGlassLogin;
