import type { TrackObject } from "../spotify/types";

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
export default TrackItem;
