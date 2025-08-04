import { useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { usePlaylistGeneration } from "../lib/components/PlaylistGenerationContext";
import SpotifyEmbedPlayer from "../lib/components/SpotifyEmbedPlayer";
import TrackItem from "../lib/components/TrackItem"; // Assuming this is now a shared component
import { ChartBarIcon, ClockIcon, TrophyIcon } from "@heroicons/react/16/solid";

// A small helper component for the chart legend
const LegendItem = ({ color, label }: { color: string; label: string }) => (
	<div className='flex items-center'>
		<div className={`w-3 h-3 rounded-sm mr-2 ${color}`} />
		<span className='text-sm text-gray-600'>{label}</span>
	</div>
);

export default function ResultsPage() {
	const navigate = useNavigate();
	const { finalData } = usePlaylistGeneration();

	const processedData = useMemo(() => {
		if (!finalData || !finalData.final_compiled_playlists) {
			return null;
		}
		const performance = Object.entries(finalData.final_compiled_playlists)
			.map(([key, value]) => ({
				name: key
					.replace(/_playlist/g, "")
					.replace(/_/g, " ")
					.replace(/\b\w/g, (l) => l.toUpperCase()),
				buildTime: value.build_time,
				searchTime: value.search_time,
				totalTime: value.build_time + value.search_time,
				tracks: value.tracks,
			}))
			.sort((a, b) => a.totalTime - b.totalTime);

		const tracks = performance.length > 0 ? performance[0].tracks : [];
		const playlistId = finalData.playlist_id;
		const playlistUri = playlistId ? `spotify:playlist:${playlistId}` : null;
		const maxTime = Math.max(...performance.map((p) => p.totalTime), 0);

		return { performance, tracks, playlistUri, maxTime };
	}, [finalData]);

	if (!processedData) {
		navigate("/create-playlist", { replace: true });
		return null;
	}

	const { performance, tracks, playlistUri, maxTime } = processedData;

	return (
		<div className='p-4 md:p-8'>
			<header className='text-center mb-10'>
				<h1 className='text-4xl md:text-5xl font-extrabold text-gray-800 mb-2 tracking-tight'>
					Your Playlist is Ready!
				</h1>
				<p className='text-lg text-gray-500'>
					Listen to the generated playlist and see how each algorithm performed.
				</p>
			</header>

			<section className='mb-12'>
				{playlistUri && <SpotifyEmbedPlayer uri={playlistUri} />}
			</section>

			<div>
				<section>
					<h2 className='flex items-center text-2xl font-bold mb-4 text-gray-700'>
						<ChartBarIcon className='mr-3 text-blue-500 size-7' />
						Performance Breakdown
					</h2>
					<div className='bg-white p-6 rounded-xl shadow-lg border border-gray-200'>
						<div className='flex justify-end space-x-4 mb-4'>
							<LegendItem color='bg-blue-400' label='Search Time' />
							<LegendItem color='bg-purple-500' label='Build Time' />
						</div>

						<div className='space-y-5'>
							{performance.map(
								({ name, buildTime, searchTime, totalTime }, index) => (
									<div key={name}>
										{/* Top section with name and total time */}
										<div className='flex justify-between items-center mb-1.5'>
											<span className='font-semibold text-gray-700'>
												{name}
											</span>
											<div className='flex items-center gap-2'>
												{index === 0 && (
													<TrophyIcon className='text-yellow-500 size-4' />
												)}
												<span className='text-sm font-mono text-gray-800'>
													{totalTime.toFixed(0)}ms
												</span>
											</div>
										</div>

										{/* Stacked Bar Chart */}
										<div className='w-full bg-gray-200 rounded-full h-4 flex overflow-hidden'>
											<div
												title={`Search Time: ${searchTime.toFixed(0)}ms`}
												className='bg-blue-400 transition-all duration-500'
												style={{ width: `${(searchTime / maxTime) * 100}%` }}
											/>
											<div
												title={`Build Time: ${buildTime.toFixed(0)}ms`}
												className='bg-purple-500 transition-all duration-500'
												style={{ width: `${(buildTime / maxTime) * 100}%` }}
											/>
										</div>

										{/* NEW: Detailed time labels below the bar */}
										<div className='flex justify-between text-xs text-gray-500 mt-1 px-1'>
											<span>Search: {searchTime.toFixed(0)}ms</span>
											{/* Only show build time if it's greater than 0 */}
											{buildTime > 0 && (
												<span>Build: {buildTime.toFixed(0)}ms</span>
											)}
										</div>
									</div>
								),
							)}
						</div>
					</div>
				</section>
			</div>
		</div>
	);
}
