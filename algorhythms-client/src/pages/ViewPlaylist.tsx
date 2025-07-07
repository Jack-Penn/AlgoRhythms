import { useEffect, useRef, useState } from "react";

// Extend Window interface to include Spotify API callback
declare global {
	interface Window {
		onSpotifyIframeApiReady?: (SpotifyIframeApi: SpotifyIframeApi) => void;
	}
}

interface SpotifyIframeApi {
	createController: (
		element: HTMLElement,
		options: { uri: string; width?: string; height?: string },
		callback: (controller: SpotifyEmbedController) => void,
	) => void;
}

interface SpotifyEmbedController {
	addListener: (event: string, callback: (event: any) => void) => void;
	removeListener: (event: string) => void;
	pause: () => void;
	play: () => void;
	loadUri: (uri: string) => void;
}

interface SpotifyEmbedControllerOptions {
	width: string;
	height: string;
	uri: string;
	theme?: "dark";
}

export default function ViewPlaylist() {
	const embedRef = useRef<HTMLDivElement>(null);
	const containerRef = useRef<HTMLDivElement>(null);
	const spotifyEmbedControllerRef = useRef<SpotifyEmbedController | null>(null);
	const [iFrameAPI, setIFrameAPI] = useState<SpotifyIframeApi | undefined>(
		undefined,
	);
	const [playerLoaded, setPlayerLoaded] = useState(false);

	const uri = "spotify:playlist:4huCkxRKajE7Vs0HsNmyLF";

	const isInitialized = useRef(false);
	useEffect(() => {
		if (isInitialized.current) return;
		isInitialized.current = true;

		const script = document.createElement("script");
		script.src = "https://open.spotify.com/embed/iframe-api/v1";
		script.async = true;
		document.body.appendChild(script);

		return () => {
			document.body.removeChild(script);
			delete window.onSpotifyIframeApiReady;
		};
	}, []);

	useEffect(() => {
		if (iFrameAPI) return;

		window.onSpotifyIframeApiReady = (SpotifyIframeApi) => {
			setIFrameAPI(SpotifyIframeApi);
		};

		return () => {
			delete window.onSpotifyIframeApiReady;
		};
	}, [iFrameAPI]);

	useEffect(() => {
		if (playerLoaded || !iFrameAPI || !embedRef.current) {
			return;
		}

		// Set dimensions based on calculated height
		const options: SpotifyEmbedControllerOptions = {
			width: "100%",
			height: "475",
			uri: uri,
			// theme: "dark",
		};

		iFrameAPI.createController(
			embedRef.current,
			options,
			(spotifyEmbedController) => {
				spotifyEmbedControllerRef.current = spotifyEmbedController;

				const handleReady = () => setPlayerLoaded(true);
				const handlePlaybackStarted = (e: any) => {
					console.log(`Playback started: ${e.data.playingURI}`);
				};

				spotifyEmbedController.addListener("ready", handleReady);
				spotifyEmbedController.addListener(
					"playback_started",
					handlePlaybackStarted,
				);
			},
		);

		return () => {
			spotifyEmbedControllerRef.current = null;
		};
	}, [playerLoaded, iFrameAPI, uri]);

	return (
		<div
			className='bg-white/10 backdrop-blur-lg rounded-3xl shadow-xl p-8 max-w-md w-full transition-all duration-500'
			ref={containerRef}
		>
			{/* Header with gradient background */}
			<div className='bg-gradient-to-r from-blue-600 to-purple-600 p-4 -mx-8 -mt-8 mb-6 rounded-t-3xl'>
				<div className='flex items-center justify-center gap-3'>
					<div className='w-10 h-10 rounded-full border-2 border-white/50 flex items-center justify-center'>
						<svg
							xmlns='http://www.w3.org/2000/svg'
							className='h-6 w-6 text-white'
							viewBox='0 0 20 20'
							fill='currentColor'
						>
							<path d='M18 3a1 1 0 00-1.196-.98l-10 2A1 1 0 006 5v9.114A4.369 4.369 0 005 14c-1.657 0-3 .895-3 2s1.343 2 3 2 3-.895 3-2V7.82l8-1.6v5.894A4.37 4.37 0 0015 12c-1.657 0-3 .895-3 2s1.343 2 3 2 3-.895 3-2V3z' />
						</svg>
					</div>
					<h1 className='text-xl font-bold text-white'>Playlist Player</h1>
				</div>
			</div>

			{/* Player container - dynamic height */}
			<div className='relative mb-2 rounded-xl bg-black/20'>
				<div className=''>
					<div ref={embedRef} />
				</div>
				{!playerLoaded && (
					<div className='absolute inset-0 flex items-center justify-center bg-black/20'>
						<div className='text-center'>
							<div className='flex justify-center mb-3'>
								<div className='relative'>
									<div className='w-16 h-16 rounded-full bg-gradient-to-r from-indigo-500 to-purple-600 animate-pulse' />
									<div className='absolute inset-0 flex items-center justify-center'>
										<svg
											className='w-8 h-8 text-white animate-spin'
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
							<p className='text-purple-200'>Loading player...</p>
						</div>
					</div>
				)}
			</div>
		</div>
	);
}
