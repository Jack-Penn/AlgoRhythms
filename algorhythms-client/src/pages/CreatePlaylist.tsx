import { useState } from "react";

export default function CreatePlaylist() {
	// State for form values
	const [mood, setMood] = useState("");
	const [activity, setActivity] = useState("");
	const [playlistLength, setPlaylistLength] = useState(10);

	//weights
	const [showWeights, setShowWeights] = useState(false);
	const [energy, setEnergy] = useState(50);
	const [danceability, setDanceability] = useState(50);
	const [acousticness, setAcousticness] = useState(50);

	return (
		<div className='w-full max-w-md bg-white rounded-2xl shadow-xl overflow-hidden'>
			{/* Header Section */}
			<div className='bg-gradient-to-r from-blue-600 to-purple-600 p-8 text-center'>
				<div className='flex flex-row align-middle justify-center gap-4'>
					<div className='w-16 h-16 my-auto rounded-full border-dashed border border-white '>
						<div className='w-full h-full flex items-center justify-center'>
							<svg
								xmlns='http://www.w3.org/2000/svg'
								className='h-10 w-10 text-white'
								viewBox='0 0 20 20'
								fill='currentColor'
							>
								<path d='M18 3a1 1 0 00-1.196-.98l-10 2A1 1 0 006 5v9.114A4.369 4.369 0 005 14c-1.657 0-3 .895-3 2s1.343 2 3 2 3-.895 3-2V7.82l8-1.6v5.894A4.37 4.37 0 0015 12c-1.657 0-3 .895-3 2s1.343 2 3 2 3-.895 3-2V3z' />
							</svg>
						</div>
					</div>

					<h1 className='text-2xl font-bold text-white my-auto'>
						Create Playlist
					</h1>
				</div>
			</div>

			{/* Form Section */}
			<div className='p-8'>
				<div className='space-y-6'>
					{/* Current Mood Section */}
					<div>
						<label className='block text-gray-700 text-lg font-medium mb-3'>
							How are you feeling today?
						</label>
						<input
							type='text'
							value={mood}
							onChange={(e) => setMood(e.target.value)}
							className='w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
							placeholder='Describe your mood...'
						/>
					</div>

					{/* Activity Section */}
					<div>
						<label className='block text-gray-700 text-lg font-medium mb-3'>
							What activity do you need a playlist for?
						</label>
						<input
							type='text'
							value={mood}
							onChange={(e) => setActivity(e.target.value)}
							className='w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
							placeholder='Working, Studying, Exercising...'
						/>
					</div>

					{/* Playlist Length Section */}
					<div>
						<div className='flex justify-between items-center mb-3'>
							<label className='block text-gray-700 text-lg font-medium'>
								Playlist Length
							</label>
							<span className='text-xl font-bold text-purple-600 bg-purple-100 px-3 py-1 rounded-full'>
								{playlistLength} songs
							</span>
						</div>
						<input
							type='range'
							min='5'
							max='30'
							value={playlistLength}
							onChange={(e) => setPlaylistLength(parseInt(e.target.value))}
							className='w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-purple-600'
						/>
						<div className='flex justify-between text-sm text-gray-500 mt-1'>
							<span>Short</span>
							<span>Long</span>
						</div>
					</div>

					{/* Divider */}
					<div className='border-t border-gray-200 my-6'></div>

					{/* Weights Section */}
					<div>
						<div className='flex flex-row w-full justify-between align-middle mb-4'>
							<h3 className='text-xl font-bold text-gray-800'>
								Customize Weights
							</h3>
							<button>{showWeights ? "Hide" : "Show"}</button>
						</div>

						{/* Energy Slider */}
						<div className='mb-5'>
							<div className='flex justify-between mb-2'>
								<label className='block text-gray-700 font-medium'>
									Energy
								</label>
								<span className='text-sm font-medium text-purple-600'>
									{energy}%
								</span>
							</div>
							<input
								type='range'
								min='0'
								max='100'
								value={energy}
								onChange={(e) => setEnergy(parseInt(e.target.value))}
								className='w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-purple-600'
							/>
						</div>

						{/* Danceability Slider */}
						<div className='mb-5'>
							<div className='flex justify-between mb-2'>
								<label className='block text-gray-700 font-medium'>
									Danceability
								</label>
								<span className='text-sm font-medium text-purple-600'>
									{danceability}%
								</span>
							</div>
							<input
								type='range'
								min='0'
								max='100'
								value={danceability}
								onChange={(e) => setDanceability(parseInt(e.target.value))}
								className='w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-purple-600'
							/>
						</div>

						{/* Acousticness Slider */}
						<div className='mb-5'>
							<div className='flex justify-between mb-2'>
								<label className='block text-gray-700 font-medium'>
									Acousticness
								</label>
								<span className='text-sm font-medium text-purple-600'>
									{acousticness}%
								</span>
							</div>
							<input
								type='range'
								min='0'
								max='100'
								value={acousticness}
								onChange={(e) => setAcousticness(parseInt(e.target.value))}
								className='w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-purple-600'
							/>
						</div>
					</div>

					{/* Generate Button */}
					<button className='w-full bg-gradient-to-r from-blue-500 to-purple-600 text-white font-semibold py-4 rounded-lg hover:opacity-90 transition-opacity shadow-md text-lg'>
						Generate Playlist
					</button>
				</div>
			</div>
		</div>
	);
}
