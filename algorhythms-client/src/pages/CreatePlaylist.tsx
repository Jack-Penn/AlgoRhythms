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
	getGeneratedTargetFeatures,
	getGenerateEmoji,
	searchTracks,
} from "../lib/api";
import useDebounce from "../lib/hooks/useDebounce";
import type { TrackObject } from "../lib/spotify/types";
import { useAuth } from "../auth/AuthProvider";
import type { Weights, Features } from "../lib/types";
import { lerpTailwindColor } from "../lib/color";
import Header from "../lib/components/Header";
import { usePlaylistGeneration } from "../lib/components/PlaylistGenerationContext";
import { useNavigate } from "react-router-dom";
import TrackItem from "../lib/components/TrackItem";

export default function CreatePlaylist() {
	const navigate = useNavigate();
	const { user, spotifyAuth } = useAuth();

	// Form states
	const [mood, setMood] = useState("");
	const [activity, setActivity] = useState("");
	const [playlistLength, setPlaylistLength] = useState(10);
	const [selectedTracks, setSelectedTracks] = useState<TrackObject[]>([]);

	const [activeTab, setActiveTab] = useState("features");

	// Feature states
	const [showAdvanced, setShowAdvanced] = useState(false);
	const [hasManualAdjustment, setHasManualAdjustment] = useState(false);
	const [isTargetFeaturesGenerated, setisTargetFeaturesGenerated] =
		useState(false);

	// Initialize weights at 0.5 for all features
	const [weights, setWeights] = useState<Weights>({
		acousticness_weight: 0.5,
		danceability_weight: 0.5,
		energy_weight: 0.5,
		instrumentalness_weight: 0.5,
		liveness_weight: 0.5,
		valence_weight: 0.5,
		speechiness_weight: 0.5,
		tempo_weight: 0.5,
		loudness_weight: 0.5,
		personalization_weight: 0.5,
		cohesion_weight: 0.5,
	});

	// Initialize target features with default values
	const [targetFeatures, settargetFeatures] = useState<Features>({
		acousticness: 0.5,
		danceability: 0.5,
		energy: 0.5,
		instrumentalness: 0.5,
		liveness: 0.5,
		valence: 0.5,
		speechiness: 0.5,
		tempo: 125,
		loudness: -30,
	});

	// Debounce inputs
	const debouncedMood = useDebounce(mood, 200).trim();
	const debouncedActivity = useDebounce(activity, 200).trim();

	// Fetch generated target features from Gemini
	const generatedTargetFeatures = useQuery({
		queryKey: ["generatedTargetFeatures", debouncedMood, debouncedActivity],
		queryFn: () => {
			if (!debouncedMood || !debouncedActivity) return null;
			return getGeneratedTargetFeatures({
				mood: debouncedMood,
				activity: debouncedActivity,
			});
		},
		enabled: !!debouncedMood && !!debouncedActivity,
	});

	useEffect(() => {
		if (generatedTargetFeatures.data) {
			settargetFeatures(generatedTargetFeatures.data);
			setisTargetFeaturesGenerated(true);
		}
	}, [generatedTargetFeatures.data]);

	// Emoji queries
	const moodEmoji = useQuery({
		queryKey: ["moodEmoji", debouncedMood],
		queryFn: () => {
			if (!debouncedMood) return null;
			return getGenerateEmoji(`mood: ${debouncedMood}`);
		},
		enabled: !!debouncedMood,
	});
	const activityEmoji = useQuery({
		queryKey: ["activityEmoji", debouncedActivity],
		queryFn: () => {
			if (!debouncedActivity) return null;
			return getGenerateEmoji(`activity: ${debouncedActivity}`);
		},
		enabled: !!debouncedActivity,
	});

	// Reset manual adjustment flag when inputs change
	useEffect(() => {
		setHasManualAdjustment(false);
	}, [mood, activity]);

	// Handle target features changes
	const handleTargetFeatureChange =
		(key: keyof Features) => (e: React.ChangeEvent<HTMLInputElement>) => {
			const value = parseFloat(e.target.value);
			settargetFeatures((prev) => ({ ...prev, [key]: value }));
			setHasManualAdjustment(true);
		};

	// Handle weight changes
	const handleWeightChange =
		(key: keyof Weights) => (e: React.ChangeEvent<HTMLInputElement>) => {
			const value = parseFloat(e.target.value);
			setWeights((prev) => ({ ...prev, [key]: value }));
			setHasManualAdjustment(true);
		};

	const { startGeneration } = usePlaylistGeneration();
	async function submitForm() {
		console.log("submitting");
		startGeneration({
			mood,
			activity,
			length: playlistLength,
			favorite_songs: selectedTracks.length
				? selectedTracks.map(({ uri }) => uri)
				: null,
			targetProfile: targetFeatures,
			weights,
			auth: spotifyAuth,
		});
		// Navigate to the loading page after initiating the stream
		navigate("/loading-playlist");
	}

	const Divider = () => <div className='border-t border-gray-200 my-6' />;

	return (
		<>
			<Header title='Create Playlist' />

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
										"blue-600",
										"purple-600",
										(playlistLength - 5) / 30,
									),
									backgroundColor: lerpTailwindColor(
										"blue-100",
										"purple-100",
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
									"blue-600",
									"purple-600",
									(playlistLength - 5) / 30,
								),
							}}
						/>
						<div className='flex justify-between text-sm text-gray-500 mt-1'>
							<span>Short</span>
							<span>Long</span>
						</div>
					</div>

					<Divider />

					{/* Favorite Songs Section */}
					{user?.is_guest && (
						<>
							<SongsSelector
								state={selectedTracks}
								setState={setSelectedTracks}
							/>

							<Divider />
						</>
					)}

					{/* Advanced Settings Toggle */}
					<div className='flex justify-between items-center'>
						<h3 className='text-xl font-bold text-gray-800'>
							Advanced Settings
						</h3>
						<button
							onClick={() => setShowAdvanced(!showAdvanced)}
							className='flex items-center gap-1 text-sm text-blue-600 cursor-pointer'
						>
							{showAdvanced ? "Hide" : "Show"}
							{showAdvanced ? (
								<EyeIcon className='w-4 h-4' />
							) : (
								<EyeSlashIcon className='w-4 h-4' />
							)}
						</button>
					</div>

					{showAdvanced && (
						<div className='bg-white rounded-lg border border-gray-200 overflow-hidden'>
							{/* Tab Navigation */}
							<div className='flex border-b border-gray-200'>
								<button
									className={`flex-1 py-3 font-medium text-center cursor-pointer ${
										activeTab === "features"
											? "text-blue-600 border-b-2 border-blue-600"
											: "text-gray-500"
									}`}
									onClick={() => setActiveTab("features")}
								>
									Target Features
								</button>
								<button
									className={`flex-1 py-3 font-medium text-center cursor-pointer ${
										activeTab === "weights"
											? "text-blue-600 border-b-2 border-blue-600"
											: "text-gray-500"
									}`}
									onClick={() => setActiveTab("weights")}
								>
									Feature Weights
								</button>
							</div>

							{/* Tab Content */}
							<div className='p-4'>
								{activeTab === "features" && (
									<div className='space-y-6'>
										<div className='text-sm text-gray-500 mb-4 flex items-center'>
											<SparklesIcon className='w-4 h-4 mr-1 text-purple-500' />
											{generatedTargetFeatures.isFetching
												? "Generating recommended features..."
												: "Adjust the ideal song characteristics"}
										</div>

										<FeatureGroup
											title='Mood & Energy ⚡'
											features={[
												{
													key: "valence",
													label: "Valence",
													description: "Musical positiveness (0=sad, 1=happy)",
													min: 0,
													max: 1,
													step: 0.01,
												},
												{
													key: "energy",
													label: "Energy",
													description:
														"Intensity and liveliness (0=calm, 1=energetic)",
													min: 0,
													max: 1,
													step: 0.01,
												},
												{
													key: "danceability",
													label: "Danceability",
													description:
														"Suitability for dancing (0=not danceable, 1=highly danceable)",
													min: 0,
													max: 1,
													step: 0.01,
												},
											]}
											targetFeatures={targetFeatures}
											onChange={handleTargetFeatureChange}
											disabled={!isTargetFeaturesGenerated}
										/>

										<FeatureGroup
											title='Sound Characteristics 🎵'
											features={[
												{
													key: "acousticness",
													label: "Acousticness",
													description:
														"Natural vs electronic sounds (0=electronic, 1=acoustic)",
													min: 0,
													max: 1,
													step: 0.01,
												},
												{
													key: "instrumentalness",
													label: "Instrumentalness",
													description:
														"Presence of vocals (0=vocal, 1=instrumental)",
													min: 0,
													max: 1,
													step: 0.01,
												},
											]}
											targetFeatures={targetFeatures}
											onChange={handleTargetFeatureChange}
											disabled={!isTargetFeaturesGenerated}
										/>

										<FeatureGroup
											title='Technical Properties ⚙️'
											features={[
												{
													key: "tempo",
													label: "Tempo",
													description: "Speed of the track (BPM)",
													min: 0,
													max: 250,
													step: 1,
													units: " BPM",
												},
												{
													key: "loudness",
													label: "Loudness",
													description: "Overall volume (dB)",
													min: -60,
													max: 0,
													step: 0.1,
													units: " dB",
												},
											]}
											targetFeatures={targetFeatures}
											onChange={handleTargetFeatureChange}
											disabled={!isTargetFeaturesGenerated}
										/>
									</div>
								)}

								{activeTab === "weights" && (
									<div className='space-y-6'>
										<div className='text-sm text-gray-500 mb-4'>
											🎚️Adjust how much each feature influences recommendations
										</div>

										<WeightGroup
											title='Audio Feature Importance'
											weights={[
												{ key: "valence_weight", label: "Valence" },
												{ key: "energy_weight", label: "Energy" },
												{ key: "danceability_weight", label: "Danceability" },
												{ key: "acousticness_weight", label: "Acousticness" },
												{
													key: "instrumentalness_weight",
													label: "Instrumentalness",
												},
												{ key: "tempo_weight", label: "Tempo" },
											]}
											currentWeights={weights}
											onChange={handleWeightChange}
										/>

										<WeightGroup
											title='Algorithm Parameters'
											weights={[
												{
													key: "personalization_weight",
													label: "Personalization",
												},
												{ key: "cohesion_weight", label: "Cohesion" },
											]}
											currentWeights={weights}
											onChange={handleWeightChange}
										/>
									</div>
								)}
							</div>
						</div>
					)}

					{/* Generate Button */}
					<button
						className='w-full bg-gradient-to-r from-blue-500 to-purple-600 text-white font-semibold py-4 rounded-lg hover:opacity-90 transition-opacity shadow-md text-lg cursor-pointer'
						onClick={submitForm}
					>
						Generate Playlist
					</button>
				</div>
			</div>
		</>
	);
}

// New FeatureGroup Component
type FeatureGroupProps = {
	title: string;
	features: Array<{
		key: keyof Features;
		label: string;
		description: string;
		min: number;
		max: number;
		step: number;
		units?: string;
	}>;
	targetFeatures: Features;
	onChange: (
		key: keyof Features,
	) => (e: React.ChangeEvent<HTMLInputElement>) => void;
	disabled?: boolean;
};

const FeatureGroup: React.FC<FeatureGroupProps> = ({
	title,
	features,
	targetFeatures,
	onChange,
	disabled = false,
}) => {
	return (
		<div className='feature-group'>
			<h4 className='text-gray-700 font-semibold mb-3'>{title}</h4>
			<div className='space-y-4'>
				{features.map((feature) => (
					<FeatureSlider
						key={feature.key}
						label={feature.label}
						description={feature.description}
						value={targetFeatures[feature.key]}
						onChange={onChange(feature.key)}
						min={feature.min}
						max={feature.max}
						step={feature.step}
						units={feature.units || ""}
						disabled={disabled}
					/>
				))}
			</div>
		</div>
	);
};

// New WeightGroup Component
type WeightGroupProps = {
	title: string;
	weights: Array<{
		key: keyof Weights;
		label: string;
	}>;
	currentWeights: Weights;
	onChange: (
		key: keyof Weights,
	) => (e: React.ChangeEvent<HTMLInputElement>) => void;
};

const WeightGroup: React.FC<WeightGroupProps> = ({
	title,
	weights,
	currentWeights,
	onChange,
}) => {
	return (
		<div className='weight-group'>
			<h4 className='text-gray-700 font-semibold mb-3'>{title}</h4>
			<div className='space-y-4'>
				{weights.map((weight) => (
					<WeightSlider
						key={weight.key}
						label={weight.label}
						value={currentWeights[weight.key]}
						onChange={onChange(weight.key)}
					/>
				))}
			</div>
		</div>
	);
};

// Feature Slider Component (for Target Features)
type FeatureSliderProps = {
	label: string;
	description: string;
	value: number;
	onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
	min: number;
	max: number;
	step: number;
	units?: string;
	disabled?: boolean;
};

const FeatureSlider: React.FC<FeatureSliderProps> = ({
	label,
	description,
	value,
	onChange,
	min,
	max,
	step,
	units = "",
	disabled = false,
}) => {
	const progress = ((value - min) / (max - min)) * 100;

	return (
		<div className='mb-5'>
			<div className='flex justify-between items-center mb-2'>
				<div className='flex items-center'>
					<label className='block text-gray-700 font-medium'>{label}</label>
					<div className='group relative ml-1'>
						<InformationCircleIcon className='size-4 text-gray-400 cursor-help' />
						<div className='absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 hidden group-hover:block bg-black text-white text-xs rounded p-2 w-48 shadow-lg z-10'>
							{description}
						</div>
					</div>
				</div>
				<span className='text-sm font-medium text-blue-600'>
					{value.toFixed(units ? 0 : 2)}
					{units}
				</span>
			</div>

			<div className='relative'>
				<input
					type='range'
					min={min}
					max={max}
					step={step}
					value={value}
					onChange={onChange}
					className={`w-full h-2 bg-blue-100 rounded-lg appearance-none ${
						disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer"
					}`}
					style={{
						background: `linear-gradient(to right, #3b82f6 0%, #3b82f6 ${progress}%, #e5e7eb ${progress}%, #e5e7eb 100%)`,
					}}
					disabled={disabled}
				/>
			</div>

			<div className='flex justify-between text-xs text-gray-500 mt-1'>
				<span>
					{min}
					{units}
				</span>
				<span>
					{max}
					{units}
				</span>
			</div>
		</div>
	);
};

// Weight Slider Component
type WeightSliderProps = {
	label: string;
	value: number;
	onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
};

const WeightSlider: React.FC<WeightSliderProps> = ({
	label,
	value,
	onChange,
}) => {
	const percentage = value * 100;
	const lerpedColor = lerpTailwindColor("blue-600", "purple-600", value);

	return (
		<div className='mb-5'>
			<div className='flex justify-between items-center mb-2'>
				<label className='block text-gray-700 font-medium'>{label}</label>
				<span className='text-sm font-medium' style={{ color: lerpedColor }}>
					{percentage.toFixed(0)}%
				</span>
			</div>

			<div className='relative'>
				<input
					type='range'
					min='0'
					max='1'
					step='0.01'
					value={value}
					onChange={onChange}
					className='w-full h-2 bg-purple-100 rounded-lg appearance-none cursor-pointer'
					style={{
						background: `linear-gradient(to right, var(--color-blue-400) 0%, ${lerpTailwindColor(
							"blue-400",
							"purple-500",
							value,
						)} ${percentage}%, #e5e7eb ${percentage}%, #e5e7eb 100%)`,
						accentColor: lerpedColor,
					}}
				/>
			</div>
		</div>
	);
};

type SongsSelectorProps = {
	state: TrackObject[];
	setState: React.Dispatch<React.SetStateAction<TrackObject[]>>;
};
const SongsSelector: React.FC<SongsSelectorProps> = ({ state, setState }) => {
	// States for song selection
	const [songQuery, setSongQuery] = useState("");

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
		if (!state.some((t) => t.id === track.id)) {
			setState((prev) => [...prev, track]);
		}
		setSongQuery(""); // Clear search after selection
	};

	// Remove track from selected list
	const removeTrack = (trackId: string) => {
		setState((prev) => prev.filter((track) => track.id !== trackId));
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
								"blue-100",
								"purple-100",
								state.length / 5,
							),
							color: lerpTailwindColor(
								"blue-600",
								"purple-600",
								state.length / 5,
							),
						}}
					>
						{state.length}
					</span>
				</div>

				{state.length === 0 ? (
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
						{state.map((track) => (
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
