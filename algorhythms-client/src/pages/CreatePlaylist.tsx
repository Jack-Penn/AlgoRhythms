import { EyeIcon, EyeSlashIcon, SparklesIcon } from "@heroicons/react/16/solid";
import { InformationCircleIcon } from "@heroicons/react/24/outline";
import { useQuery } from "@tanstack/react-query";
import React, { useEffect, useState } from "react";
import { getGeneratedWeights } from "../lib/api";
import useDebounce from "../lib/hooks/useDebounce";

export default function CreatePlaylist() {
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
	const { data, isFetching } = useQuery({
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

	// Update weights when new data comes in
	useEffect(() => {
		if (data && !hasManualAdjustment) {
			console.log("Weights", data);
			setAcousticness(data.acousticness * 100);
			setDanceability(data.danceability * 100);
			setEnergy(data.energy * 100);
			setInstrumentalness(data.instrumentalness * 100);
			setLiveness(data.liveness * 100);
			setValence(data.valence * 100);
			setSpeechiness(data.speechiness * 100);
			setTempo(data.tempo);
			setLoudeness(data.loudness);
		}
	}, [data]);

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

	const isLoadingWeights = isFetching;

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
							placeholder='Describe a mood for your playlist...'
						/>
					</div>

					{/* Activity Section */}
					<div>
						<label className='block text-gray-700 text-lg font-medium mb-3'>
							What activity do you need a playlist for?
						</label>
						<input
							type='text'
							value={activity}
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
					<div className='border-t border-gray-200 my-6'></div>

					{/* Weights Section */}
					<div>
						<div className='flex flex-row w-full justify-between items-center mb-4'>
							<h3 className='text-xl font-bold text-gray-800'>
								Customize Weights
							</h3>

							{isLoadingWeights && (
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
