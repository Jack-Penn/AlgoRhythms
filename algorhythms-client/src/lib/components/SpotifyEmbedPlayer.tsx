import { useEffect, useRef, useState } from "react";

// Extend Window interface to include Spotify API callback
declare global {
	interface Window {
		onSpotifyIframeApiReady?: (SpotifyIframeApi: SpotifyIframeApi) => void;
	}
}

// ... Interfaces for SpotifyIframeApi, etc. remain the same ...
interface SpotifyIframeApi {
	createController: (
		element: HTMLElement,
		options: { uri: string; width?: string; height?: string },
		callback: (controller: SpotifyEmbedController) => void,
	) => void;
}
interface SpotifyEmbedController {
	addListener: (event: string, callback: (event: any) => void) => void;
	removeListener: (event: string, callback: (event: any) => void) => void;
	loadUri: (uri: string) => void;
	// ... other methods
}

// The component now accepts a URI as a prop
interface SpotifyEmbedPlayerProps {
	uri: string;
}

export default function SpotifyEmbedPlayer({ uri }: SpotifyEmbedPlayerProps) {
	const embedRef = useRef<HTMLDivElement>(null);
	const spotifyControllerRef = useRef<SpotifyEmbedController | null>(null);
	const [isPlayerLoaded, setPlayerLoaded] = useState(false);

	// Effect to load the IFrame API script once
	useEffect(() => {
		const script = document.createElement("script");
		script.src = "https://open.spotify.com/embed/iframe-api/v1";
		script.async = true;
		document.body.appendChild(script);

		window.onSpotifyIframeApiReady = (IFrameAPI) => {
			if (!embedRef.current) return;

			const options = { width: "400", height: "600", uri };
			IFrameAPI.createController(embedRef.current, options, (controller) => {
				spotifyControllerRef.current = controller;
				controller.addListener("ready", () => setPlayerLoaded(true));
			});
		};

		return () => {
			document.body.removeChild(script);
			delete window.onSpotifyIframeApiReady;
		};
	}, []); // Empty dependency array ensures this runs only once

	// Effect to load a new URI when the prop changes
	useEffect(() => {
		if (spotifyControllerRef.current) {
			spotifyControllerRef.current.loadUri(uri);
		}
	}, [uri]); // This runs whenever the uri prop changes

	return (
		<div className='relative mb-2 rounded-xl bg-black/20'>
			<div ref={embedRef} />
			{!isPlayerLoaded && (
				<div className='absolute inset-0 flex items-center justify-center bg-black/20 rounded-xl'>
					{/* ... Your loading spinner JSX ... */}
					<p className='text-purple-200'>Loading player...</p>
				</div>
			)}
		</div>
	);
}
