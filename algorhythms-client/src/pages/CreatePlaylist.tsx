import {
	EyeIcon,
	EyeSlashIcon,
	SparklesIcon,
	TrashIcon,
} from "@heroicons/react/16/solid";
import { InformationCircleIcon } from "@heroicons/react/24/outline";
import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import {
	getGeneratedWeights,
	getGenerateEmoji,
	searchTracks,
} from "../lib/api";
import useDebounce from "../lib/hooks/useDebounce";
import type { TrackObject } from "../lib/spotify/types";
import { useAuth } from "../auth/AuthProvider";

export default function CreatePlaylist() {
	const { user } = useAuth();

	// Form states
	const [mood, setMood] = useState("");
	const [activity, setActivity] = useState("");
	const [playlistLength, setPlaylistLength] = useState(10);

	// Weights state
	const [showWeights, setShowWeights] = useState(false);
	const [acousticness, setAcousticness] = useState(50);
	const [danceability, setDanceability] = useState(50);
	const [energy, setEnergy] = useState(50);
	const [instrumentalness, setInstrumentalness] = useState(50);
	const [liveness, setLiveness] = useState(50);
	const [valence, setValence] = useState(50);
	const [speechiness, setSpeechiness] = useState(50);
	const [tempo, setTempo] = useState(125);
	const [loudeness, setLoudeness] = useState(-30);
	const [hasManualAdjustment, setHasManualAdjustment] = useState(false);

	// Debounce mood and activity inputs
	const debouncedMood = useDebounce(mood, 1000).trim();
	const debouncedActivity = useDebounce(activity, 1000).trim();

	// React Query for fetching weights
	const generatedWeights = useQuery({
		queryKey: ["generatedWeights", debouncedMood, debouncedActivity],
		queryFn: () => {
			if (!debouncedMood || !debouncedActivity) return null;
			console.log("Fetching Weights");
			return getGeneratedWeights({
				mood: debouncedMood,
				activity: debouncedActivity,
			});
		},
		enabled: !!debouncedMood && !!debouncedActivity,
	});

	const moodEmoji = useQuery({
		queryKey: ["moodEmoji", debouncedMood],
		queryFn: () => {
			if (!debouncedMood) return null;
			return getGenerateEmoji(debouncedMood);
		},
		enabled: !!debouncedMood,
	});

	const activityEmoji = useQuery({
		queryKey: ["activityEmoji", debouncedActivity],
		queryFn: () => {
			if (!debouncedActivity) return null;
			return getGenerateEmoji(debouncedActivity);
		},
		enabled: !!debouncedActivity,
	});

	// Update weights when new data comes in
	useEffect(() => {
		if (generatedWeights.data && !hasManualAdjustment) {
			console.log("Weights", generatedWeights.data);
			setAcousticness(generatedWeights.data.acousticness * 100);
			setDanceability(generatedWeights.data.danceability * 100);
			setEnergy(generatedWeights.data.energy * 100);
			setInstrumentalness(generatedWeights.data.instrumentalness * 100);
			setLiveness(generatedWeights.data.liveness * 100);
			setValence(generatedWeights.data.valence * 100);
			setSpeechiness(generatedWeights.data.speechiness * 100);
			setTempo(generatedWeights.data.tempo);
			setLoudeness(generatedWeights.data.loudness);
		}
	}, [generatedWeights.data]);

	// Reset manual adjustment flag when inputs change
	useEffect(() => {
		setHasManualAdjustment(false);
	}, [mood, activity]);

	// Handle slider changes
	const handleSliderChange = (
		setter: React.Dispatch<React.SetStateAction<number>>,
	) => {
		return (e: React.ChangeEvent<HTMLInputElement>) => {
			const value = parseInt(e.target.value);
			setter(value);
			setHasManualAdjustment(true);
		};
	};

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
					{/* Mood Section */}
					<div className='mb-6'>
						<label className='block text-gray-700 text-lg font-medium mb-3'>
							How are you feeling today?
						</label>
						<div className='relative'>
							<input
								type='text'
								value={mood}
								onChange={(e) => setMood(e.target.value)}
								className='w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent pr-12' // Added pr-12 for right padding
								placeholder='Describe a mood for your playlist...'
							/>
							{moodEmoji.data?.emoji && (
								<div className='absolute inset-y-0 right-0 flex items-center px-4 pointer-events-none z-10'>
									<span className='text-2xl'>{moodEmoji.data.emoji}</span>
								</div>
							)}
						</div>
					</div>

					{/* Activity Section */}
					<div className='mb-6'>
						<label className='block text-gray-700 text-lg font-medium mb-3'>
							What activity do you need a playlist for?
						</label>
						<div className='relative'>
							<input
								type='text'
								value={activity}
								onChange={(e) => setActivity(e.target.value)}
								className='w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent pr-12' // Added pr-12 for right padding
								placeholder='Working, Studying, Exercising...'
							/>
							{activityEmoji.data?.emoji && (
								<div className='absolute inset-y-0 right-0 flex items-center px-4 pointer-events-none z-10'>
									<span className='text-2xl'>{activityEmoji.data?.emoji}</span>
								</div>
							)}
						</div>
					</div>

					{/* Playlist Length Section */}
					<div>
						<div className='flex justify-between items-center mb-3'>
							<label className='block text-gray-700 text-lg font-medium'>
								Playlist Length
							</label>
							<span
								className='text-xl font-bold px-3 py-1 rounded-full style'
								style={{
									color: lerpTailwindColor(
										"--color-blue-600",
										"--color-purple-600",
										(playlistLength - 5) / 30,
									),
									backgroundColor: lerpTailwindColor(
										"--color-blue-100",
										"--color-purple-100",
										(playlistLength - 5) / 30,
									),
								}}
							>
								{playlistLength} songs
							</span>
						</div>
						<input
							type='range'
							min='5'
							max='30'
							value={playlistLength}
							onChange={(e) => setPlaylistLength(parseInt(e.target.value))}
							className='w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer'
							style={{
								accentColor: lerpTailwindColor(
									"--color-blue-600",
									"--color-purple-600",
									(playlistLength - 5) / 30,
								),
							}}
						/>
						<div className='flex justify-between text-sm text-gray-500 mt-1'>
							<span>Short</span>
							<span>Long</span>
						</div>
					</div>

					{/* Divider */}
					<div className='border-t border-gray-200 my-6' />

					{user?.is_guest && (
						<>
							<SongsSelector />

							{/* Divider */}
							<div className='border-t border-gray-200 my-6' />
						</>
					)}

					{/* Weights Section */}
					<div>
						<div className='flex flex-row w-full justify-between items-center mb-4'>
							<h3 className='text-xl font-bold text-gray-800'>
								Customize Weights
							</h3>

							{generatedWeights.isFetching && (
								<div className=' animate-pulse flex flex-row gap-1'>
									<span className='bg-gradient-to-r from-blue-500 to-purple-500 text-transparent bg-clip-text text-sm'>
										Generating weights
									</span>
									<SparklesIcon className='size-4 text-purple-500' />
								</div>
							)}

							<button
								className=' cursor-pointer size-6.5'
								onClick={() => setShowWeights((showWeights) => !showWeights)}
							>
								{showWeights ? <EyeIcon /> : <EyeSlashIcon />}
							</button>
						</div>

						{showWeights && (
							<>
								{/* Mood & Energy Section */}
								<h4 className='text-gray-700 font-semibold mt-6 mb-3'>
									Mood & Energy ⚡
								</h4>
								<WeightSlider
									label='Energy'
									description='Intensity and liveliness (0=calm, 100=energetic)'
									value={energy}
									onChange={handleSliderChange(setEnergy)}
								/>
								<WeightSlider
									label='Valence'
									description='Musical positiveness (0=sad, 100=happy)'
									value={valence}
									onChange={handleSliderChange(setValence)}
								/>
								<WeightSlider
									label='Danceability'
									description='Suitability for dancing (0=not danceable, 100=highly danceable)'
									value={danceability}
									onChange={handleSliderChange(setDanceability)}
								/>

								{/* Sound Characteristics Section */}
								<h4 className='text-gray-700 font-semibold mt-8 mb-3'>
									Sound Characteristics 🎵
								</h4>
								<WeightSlider
									label='Acousticness'
									description='Natural vs electronic sounds (0=electronic, 100=acoustic)'
									value={acousticness}
									onChange={handleSliderChange(setAcousticness)}
								/>
								<WeightSlider
									label='Instrumentalness'
									description='Presence of vocals (0=vocal, 100=instrumental)'
									value={instrumentalness}
									onChange={handleSliderChange(setInstrumentalness)}
								/>
								<WeightSlider
									label='Speechiness'
									description='Spoken words content (0=music, 100=speech)'
									value={speechiness}
									onChange={handleSliderChange(setSpeechiness)}
								/>
								<WeightSlider
									label='Liveness'
									description='Audience presence (0=studio, 100=live)'
									value={liveness}
									onChange={handleSliderChange(setLiveness)}
								/>

								{/* Technical Properties Section */}
								<h4 className='text-gray-700 font-semibold mt-8 mb-3'>
									Technical Properties ⚙️
								</h4>
								<WeightSlider
									label='Tempo'
									description='Speed of the track (BPM)'
									value={tempo}
									onChange={handleSliderChange(setTempo)}
									min={0}
									max={250}
									units=' BPM'
								/>
								<WeightSlider
									label='Loudness'
									description='Overall volume (dB)'
									value={loudeness}
									onChange={handleSliderChange(setLoudeness)}
									min={-60}
									max={0}
									units=' db'
								/>
							</>
						)}
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

type WeightSliderProps = {
	label: string;
	description: string;
	value: number;
	onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
	units?: string;
	min?: number;
	max?: number;
};
const WeightSlider: React.FC<WeightSliderProps> = ({
	label,
	description,
	value,
	onChange,
	units = "%",
	min = 0,
	max = 100,
}) => {
	const lerpedGradientColor = lerpTailwindColor(
		"--color-blue-600",
		"--color-purple-600",
		(value - min) / (max - min),
	);

	return (
		<div className='mb-5'>
			<div className='flex justify-between mb-2'>
				<div className='flex items-center'>
					<label className='block text-gray-700 font-medium'>{label}</label>
					<div className='group relative ml-1'>
						<InformationCircleIcon className=' size-3.5 text-gray-400 cursor-help' />
						<div className='absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 hidden group-hover:block bg-black text-white text-xs rounded p-2 w-48 shadow-lg z-10'>
							{description}
						</div>
					</div>
				</div>
				<span
					className='text-sm font-medium'
					style={{ color: lerpedGradientColor }}
				>
					{value}
					{units}
				</span>
			</div>
			<input
				type='range'
				min={min}
				max={max}
				value={value}
				onChange={onChange}
				className='w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer'
				style={{
					accentColor: lerpedGradientColor,
				}}
			/>
		</div>
	);
};

function lerpTailwindColor(
	color1: string,
	color2: string,
	value: number,
	colorSpace: string = "oklch",
) {
	return `color-mix(in ${colorSpace}, var(${color1}), var(${color2}) ${
		value * 100
	}%)`;
}

const SongsSelector = () => {
	// States for song selection
	const [songQuery, setSongQuery] = useState("");
	const [selectedTracks, setSelectedTracks] = useState<TrackObject[]>([]);

	// Debounce the song search query
	const debouncedSongQuery = useDebounce(songQuery, 500);

	// React Query for fetching tracks
	const { data, isFetching } = useQuery({
		queryKey: ["searchTracks", debouncedSongQuery],
		queryFn: () => {
			if (!debouncedSongQuery) return [];
			return searchTracks(debouncedSongQuery);
		},
		enabled: !!debouncedSongQuery,
	});

	// Add track to selected list
	const addTrack = (track: TrackObject) => {
		if (!selectedTracks.some((t) => t.id === track.id)) {
			setSelectedTracks((prev) => [...prev, track]);
		}
		setSongQuery(""); // Clear search after selection
	};

	// Remove track from selected list
	const removeTrack = (trackId: string) => {
		setSelectedTracks((prev) => prev.filter((track) => track.id !== trackId));
	};

	return (
		<div className='space-y-4'>
			<div>
				<label className='block text-gray-700 text-lg font-medium mb-2'>
					Favorite Songs
				</label>
				<p className='text-xs text-gray-500 italic mb-3'>
					Help us understand your taste (songs may influence but not necessarily
					appear in playlist)
				</p>
			</div>

			{/* Search input with autocomplete */}
			<div className='relative mb-4'>
				<div className='relative'>
					<input
						type='text'
						value={songQuery}
						onChange={(e) => setSongQuery(e.target.value)}
						className='w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent pr-10'
						placeholder='Search for songs...'
					/>
					{isFetching && (
						<div className='absolute inset-y-0 right-0 flex items-center pr-3'>
							<svg
								className='animate-spin h-5 w-5 text-gray-400'
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
					)}
				</div>

				{/* Autocomplete dropdown */}
				{songQuery && (
					<div className='absolute z-10 mt-1 w-full bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto'>
						{isFetching ? (
							<div className='p-4 text-center text-gray-500'>
								<div className='flex justify-center'>
									<svg
										className='animate-spin h-5 w-5 text-purple-500'
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
						) : data?.length ? (
							data.map((track) => (
								<div
									key={track.id}
									onClick={() => addTrack(track)}
									className='flex items-center p-3 cursor-pointer hover:bg-blue-50 transition-colors'
								>
									<TrackItem track={track} />
								</div>
							))
						) : (
							<div className='p-4 text-center text-gray-500'>
								No results found
							</div>
						)}
					</div>
				)}
			</div>

			{/* Selected tracks */}
			<div>
				<div className='flex justify-between items-center mb-3'>
					<h4 className='font-medium text-gray-700'>Selected Songs</h4>
					<span
						className='text-sm font-medium bg-blue-100 text-blue-800 rounded-full px-2.5 py-0.5'
						style={{
							backgroundColor: lerpTailwindColor(
								"--color-blue-100",
								"--color-purple-100",
								selectedTracks.length / 5,
							),
							color: lerpTailwindColor(
								"--color-blue-800",
								"--color-purple-800",
								selectedTracks.length / 5,
							),
						}}
					>
						{selectedTracks.length}
					</span>
				</div>

				{selectedTracks.length === 0 ? (
					<div className='bg-gray-50 border-2 border-dashed border-gray-300 rounded-lg p-6 text-center'>
						<div className='flex flex-col items-center justify-center'>
							<svg
								xmlns='http://www.w3.org/2000/svg'
								className='h-10 w-10 text-gray-400'
								fill='none'
								viewBox='0 0 24 24'
								stroke='currentColor'
							>
								<path
									strokeLinecap='round'
									strokeLinejoin='round'
									strokeWidth={2}
									d='M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3'
								/>
							</svg>
							<p className='mt-2 text-sm text-gray-500'>
								No songs selected yet
							</p>
						</div>
					</div>
				) : (
					<div className='space-y-3 max-h-60 overflow-y-auto pr-1'>
						{selectedTracks.map((track) => (
							<div
								key={track.id}
								className='flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-200'
							>
								<TrackItem track={track} />
								<button
									onClick={() => removeTrack(track.id)}
									className='ml-3 text-gray-400 hover:text-red-500 transition-colors size-5 cursor-pointer '
								>
									<TrashIcon />
								</button>
							</div>
						))}
					</div>
				)}
			</div>
		</div>
	);
};

interface TrackItemProps {
	track: TrackObject;
}
const TrackItem: React.FC<TrackItemProps> = ({ track }) => {
	return (
		<div className='flex items-center w-full'>
			{track.album.images?.[0]?.url ? (
				<img
					src={track.album.images[0].url}
					alt={track.name}
					className='w-12 h-12 rounded-lg object-cover border border-gray-200'
				/>
			) : (
				<div className='bg-gray-200 border-2 border-dashed border-gray-300 rounded-lg w-12 h-12 flex items-center justify-center'>
					<svg
						xmlns='http://www.w3.org/2000/svg'
						className='h-6 w-6 text-gray-400'
						fill='none'
						viewBox='0 0 24 24'
						stroke='currentColor'
					>
						<path
							strokeLinecap='round'
							strokeLinejoin='round'
							strokeWidth={2}
							d='M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3'
						/>
					</svg>
				</div>
			)}
			<div className='ml-3 min-w-0 flex-1'>
				<p className='text-sm font-medium truncate'>{track.name}</p>
				<p className='text-xs text-gray-500 truncate'>
					{track.artists.map((artist) => artist.name).join(", ")}
				</p>
			</div>
		</div>
	);
};
