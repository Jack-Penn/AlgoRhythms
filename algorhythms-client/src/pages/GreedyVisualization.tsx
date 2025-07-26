import React, { useState, useEffect, useRef, useMemo } from "react";
import * as d3 from "d3";
import type { Features, Weights } from "../lib/types";
import { InformationCircleIcon, SparklesIcon } from "@heroicons/react/16/solid";

interface SongCandidate {
	id: string;
	name: string;
	artist: string;
	score: number;
	weightedFeatures: Features;
	features: Features;
}

// Constants for test data generation
const artists = [
	"Arctic Monkeys",
	"Tame Impala",
	"Glass Animals",
	"MGMT",
	"Florence + The Machine",
	"The Strokes",
	"Billie Eilish",
	"Dua Lipa",
	"Kendrick Lamar",
	"Lana Del Rey",
];

const songNames = [
	"Do I Wanna Know?",
	"The Less I Know The Better",
	"Heat Waves",
	"Electric Feel",
	"Dog Days Are Over",
	"Last Nite",
	"bad guy",
	"Levitating",
	"HUMBLE.",
	"Summertime Sadness",
];

// Generate constant test data
const generateSongs = (count: number): SongCandidate[] => {
	const generateRandomFeature = (low = 0, high = 1) => {
		return Math.random() * (high - low) + low;
	};

	const weights: Weights = {
		acousticness_weight: 0.1,
		danceability_weight: 0.15,
		energy_weight: 0.18,
		instrumentalness_weight: 0.08,
		liveness_weight: 0.07,
		valence_weight: 0.12,
		speechiness_weight: 0.05,
		tempo_weight: 0.1,
		loudness_weight: 0.15,
		personalization_weight: 0.5,
		cohesion_weight: 0.5,
	};

	return Array.from({ length: count }, (_, i) => {
		// Generate normalized features
		const features: Features = {
			acousticness: generateRandomFeature(),
			danceability: generateRandomFeature(),
			energy: generateRandomFeature(),
			instrumentalness: generateRandomFeature(),
			liveness: generateRandomFeature(),
			valence: generateRandomFeature(),
			speechiness: generateRandomFeature(),
			tempo: generateRandomFeature(), // Normalized to [0,1]
			loudness: generateRandomFeature(), // Normalized to [0,1]
		};

		// Calculate weighted features
		const weightedFeatures: Features = Object.fromEntries(
			Object.entries(features).map(([key, value]) => [
				key,
				value * weights[`${key}_weight` as keyof Weights] * 100,
			]),
		) as Features;

		const score = Object.values(weightedFeatures).reduce(
			(sum, val) => sum + val,
			0,
		);

		return {
			id: `song-${i}`,
			name: songNames[i % songNames.length],
			artist: artists[i % artists.length],
			score,
			weightedFeatures,
			features,
		};
	}).sort((a, b) => b.score - a.score);
};
const initialSongs = generateSongs(15); // Constant test data

// Feature label mapping
const featureLabels: Record<keyof Features, string> = {
	acousticness: "Acousticness",
	danceability: "Danceability",
	energy: "Energy",
	instrumentalness: "Instrumentalness",
	liveness: "Liveness",
	valence: "Valence",
	speechiness: "Speechiness",
	tempo: "Tempo",
	loudness: "Loudness",
};

// Feature colors
const featureColors = {
	acousticness: "#4C78A8",
	danceability: "#54A24B",
	energy: "#F58518",
	instrumentalness: "#B279A2",
	liveness: "#72B7B2",
	valence: "#EECA3B",
	speechiness: "#FF9DA6",
	tempo: "#9D755D",
	loudness: "#BAB0AC",
};

// Features in order for stacking
const featuresOrder = Object.keys(
	featureLabels,
) as (keyof typeof featureLabels)[];

// Color scale for features
const colorScale = d3
	.scaleOrdinal<string>()
	.domain(featuresOrder)
	.range(featuresOrder.map((key) => featureColors[key]));

const GreedyAlgorithmVisualization: React.FC = () => {
	const containerRef = useRef<HTMLDivElement>(null);
	const [dimensions, setDimensions] = useState({ width: 800, height: 500 });
	const [cutoff, setCutoff] = useState<number>(75);
	const [tooltip, setTooltip] = useState<{
		content: string;
		x: number;
		y: number;
		type: "song" | "feature";
	} | null>(null);
	const [containerOffset, setContainerOffset] = useState({ top: 0, left: 0 });

	// Use constant test data
	const songs = initialSongs;

	// Handle window resize and get container position
	useEffect(() => {
		const handleResize = () => {
			if (containerRef.current) {
				const rect = containerRef.current.getBoundingClientRect();
				setDimensions({
					width: containerRef.current.clientWidth,
					height: 500,
				});
				setContainerOffset({
					top: rect.top + window.scrollY,
					left: rect.left + window.scrollX,
				});
			}
		};

		handleResize();
		window.addEventListener("resize", handleResize);
		return () => window.removeEventListener("resize", handleResize);
	}, []);

	// Dimensions calculations
	const margin = useMemo(
		() => ({ top: 40, right: 20, bottom: 80, left: 60 }),
		[],
	);
	const boundedWidth = dimensions.width - margin.left - margin.right;
	const boundedHeight = dimensions.height - margin.top - margin.bottom;

	// Create scales
	const xScale = useMemo(() => {
		return d3
			.scaleBand()
			.domain(songs.map((d) => d.id))
			.range([0, boundedWidth])
			.padding(0.2);
	}, [songs, boundedWidth]);

	const yScale = useMemo(() => {
		const maxScore = d3.max(songs, (d) => d.score) || 100;
		return d3
			.scaleLinear()
			.domain([0, maxScore])
			.range([boundedHeight, 0])
			.nice();
	}, [songs, boundedHeight]);

	// Calculate cumulative heights for segments
	const calculateSegments = (song: SongCandidate) => {
		const segments: { feature: keyof Features; start: number; end: number }[] =
			[];
		let currentHeight = 0;

		for (const feature of [...featuresOrder].reverse()) {
			const value = song.weightedFeatures[feature];
			segments.push({
				feature,
				start: currentHeight,
				end: currentHeight + value,
			});
			currentHeight += value;
		}

		return segments;
	};

	// Handle tooltip for segments
	const handleSegmentHover = (
		event: React.MouseEvent<SVGRectElement>,
		song: SongCandidate,
		feature: keyof Features,
	) => {
		const featureName = featureLabels[feature];
		const value = (song.features[feature] * 100).toFixed(1);
		const contribution = song.weightedFeatures[feature].toFixed(1);

		setTooltip({
			content: `
        <div class="font-bold">${song.name}</div>
        <div class="text-sm">${song.artist}</div>
        <div class="mt-2">Feature: <span class="font-semibold">${featureName}</span></div>
        <div>Value: <span class="font-semibold">${value}%</span></div>
        <div>Contribution: <span class="font-semibold">${contribution} pts</span></div>
      `,
			x: event.clientX,
			y: event.clientY,
			type: "feature",
		});
	};

	// Handle tooltip for song bars
	const handleSongHover = (
		event: React.MouseEvent<SVGRectElement>,
		song: SongCandidate,
	) => {
		setTooltip({
			content: `
        <div class="font-bold">${song.name}</div>
        <div class="text-sm">${song.artist}</div>
        <div class="mt-1">Score: <span class="font-semibold">${song.score.toFixed(
					1,
				)}</span></div>
      `,
			x: event.clientX,
			y: event.clientY,
			type: "song",
		});
	};

	// Handle mouse leave
	const handleMouseLeave = () => {
		setTooltip(null);
	};

	// Render X axis ticks
	const renderXAxis = () => {
		if (!xScale) return null;

		return songs.map((song) => {
			const x = (xScale(song.id) || 0) + xScale.bandwidth() / 2;
			const y = boundedHeight + 35; // Position below the bars
			const truncatedName =
				song.name.length > 12 ? `${song.name.substring(0, 9)}...` : song.name;

			return (
				<g
					key={`tick-${song.id}`}
					transform={`translate(${x}, ${y})`}
					className='text-xs'
				>
					<text
						textAnchor='end'
						fill='#666'
						transform='rotate(-60)'
						dy='-1em'
						dx='2em'
					>
						{truncatedName}
					</text>
				</g>
			);
		});
	};

	// Render Y axis ticks
	const renderYAxis = () => {
		if (!yScale) return null;

		const ticks = yScale.ticks(5);
		return ticks.map((tick) => {
			const y = yScale(tick);
			return (
				<g key={`tick-${tick}`} transform={`translate(0, ${y})`}>
					<line x2={boundedWidth} stroke='#eee' />
					<text
						x={-10}
						dy='0.32em'
						textAnchor='end'
						fill='#666'
						className='text-xs'
					>
						{tick}
					</text>
				</g>
			);
		});
	};

	return (
		<div className='max-w-6xl mx-auto p-6 bg-gradient-to-br from-blue-50 to-purple-50 rounded-2xl shadow-xl'>
			<div className='mb-8 text-center'>
				<div className='inline-flex items-center gap-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white py-2 px-6 rounded-full mb-4'>
					<SparklesIcon className='w-5 h-5' />
					<h1 className='text-2xl font-bold'>Playlist Generation Algorithm</h1>
				</div>
				<p className='text-gray-600 max-w-2xl mx-auto'>
					This visualization shows how a greedy algorithm selects songs for a
					playlist based on weighted feature contributions. Each bar represents
					a song candidate, with segments showing how each audio feature
					contributes to the overall match score.
				</p>
			</div>

			<div className='flex flex-col lg:flex-row gap-6'>
				<div className='lg:w-3/4'>
					<div className='bg-white p-5 rounded-xl border border-gray-200 shadow-sm'>
						<div className='mb-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3'>
							<h2 className='text-xl font-semibold text-gray-800 flex items-center gap-2'>
								<InformationCircleIcon className='w-5 h-5 text-indigo-600' />
								Song Selection Visualization
							</h2>
							<div className='flex items-center space-x-3'>
								<span className='text-sm font-medium text-gray-700'>
									Cutoff Threshold:
								</span>
								<div className='flex items-center bg-gray-100 rounded-lg px-3 py-1'>
									<input
										type='range'
										min='0'
										max='100'
										value={cutoff}
										onChange={(e) => setCutoff(Number(e.target.value))}
										className='w-24'
									/>
									<span className='w-10 text-center font-medium text-indigo-700 ml-2'>
										{cutoff}
									</span>
								</div>
							</div>
						</div>

						<div className='relative' ref={containerRef}>
							<svg
								width={dimensions.width}
								height={dimensions.height}
								className='bg-white rounded border border-gray-200'
							>
								{/* Main chart area */}
								<g transform={`translate(${margin.left}, ${margin.top})`}>
									{/* Background grid */}
									{renderYAxis()}

									{/* Bars */}
									{songs.map((song) => {
										const segments = calculateSegments(song);
										const x = xScale(song.id) || 0;
										const width = xScale.bandwidth();

										return (
											<g
												key={song.id}
												transform={`translate(${x}, 0)`}
												className='cursor-pointer'
											>
												{/* Add full-height background for song tooltip */}
												<rect
													x={0}
													y={yScale(song.score)}
													width={width}
													height={boundedHeight - yScale(song.score)}
													fill='transparent'
													onMouseEnter={(e) => handleSongHover(e, song)}
													onMouseMove={(e) => handleSongHover(e, song)}
													onMouseLeave={handleMouseLeave}
												/>

												{/* Feature segments */}
												{segments.map((segment) => (
													<rect
														key={`${song.id}-${segment.feature}`}
														x={0}
														y={yScale(segment.end)}
														width={width}
														height={yScale(segment.start) - yScale(segment.end)}
														fill={colorScale(segment.feature)}
														onMouseEnter={(e) =>
															handleSegmentHover(e, song, segment.feature)
														}
														onMouseMove={(e) =>
															handleSegmentHover(e, song, segment.feature)
														}
														onMouseLeave={handleMouseLeave}
													/>
												))}
											</g>
										);
									})}

									{/* Cutoff line */}
									<line
										key='cutoff-line'
										x1={0}
										x2={boundedWidth}
										y1={yScale(cutoff)}
										y2={yScale(cutoff)}
										stroke='#E64C66'
										strokeWidth={2}
										strokeDasharray='5,5'
									/>

									{/* Cutoff label */}
									<text
										key='cutoff-label'
										x={boundedWidth - 5}
										y={yScale(cutoff) - 10}
										textAnchor='end'
										fill='#E64C66'
										className='text-sm font-medium'
									>
										{`Cutoff: ${cutoff}`}
									</text>

									{/* X Axis */}
									{renderXAxis()}

									{/* Y Axis label */}
									<text
										key='y-axis-label'
										transform={`rotate(-90) translate(${
											-boundedHeight / 2
										}, -40)`}
										textAnchor='middle'
										fill='#666'
										className='text-sm font-medium'
									>
										Match Score
									</text>
								</g>

								{/* Title */}
								<text
									key='title'
									x={dimensions.width / 2}
									y={20}
									textAnchor='middle'
									className='text-base font-bold'
									fill='#333'
								>
									Greedy Algorithm Song Selection
								</text>

								{/* Subtitle */}
								<text
									key='subtitle'
									x={dimensions.width / 2}
									y={40}
									textAnchor='middle'
									className='text-sm'
									fill='#666'
								>
									Songs sorted by overall match score with feature contributions
								</text>
							</svg>

							{/* Tooltip - positioned relative to container */}
							{tooltip && (
								<div
									className='absolute bg-white border border-gray-300 rounded-lg shadow-lg p-3 text-sm max-w-xs pointer-events-none'
									style={{
										left: `${tooltip.x - containerOffset.left + 15}px`,
										top: `${tooltip.y - containerOffset.top - 60}px`,
										opacity: 1,
										transition: "opacity 0.2s",
										zIndex: 10,
									}}
									dangerouslySetInnerHTML={{ __html: tooltip.content }}
								/>
							)}
						</div>

						<div className='mt-6 bg-gradient-to-r from-indigo-50 to-purple-50 p-4 rounded-xl border border-indigo-100'>
							<h3 className='font-semibold text-indigo-800 mb-2 flex items-center gap-2'>
								<InformationCircleIcon className='w-5 h-5 text-indigo-600' />
								Algorithm Explanation
							</h3>
							<ul className='text-gray-700 text-sm space-y-2 pl-2'>
								<li className='flex items-start'>
									<div className='bg-indigo-600 w-1.5 h-1.5 rounded-full mt-1.5 mr-2'></div>
									Songs are sorted by overall match score (highest first)
								</li>
								<li className='flex items-start'>
									<div className='bg-indigo-600 w-1.5 h-1.5 rounded-full mt-1.5 mr-2'></div>
									The algorithm selects songs above the cutoff line until
									playlist duration is reached
								</li>
								<li className='flex items-start'>
									<div className='bg-indigo-600 w-1.5 h-1.5 rounded-full mt-1.5 mr-2'></div>
									Each feature contributes to the score based on its weight and
									song's feature value
								</li>
								<li className='flex items-start'>
									<div className='bg-indigo-600 w-1.5 h-1.5 rounded-full mt-1.5 mr-2'></div>
									This greedy approach ensures we get the best matches first
								</li>
							</ul>
						</div>
					</div>
				</div>

				<div className='lg:w-1/4'>
					<div className='bg-white p-5 rounded-xl border border-gray-200 shadow-sm'>
						<h3 className='font-bold text-gray-800 mb-4 text-center pb-2 border-b border-gray-200'>
							Feature Legend
						</h3>
						<div className='space-y-3'>
							{featuresOrder.map((key) => (
								<div key={`legend-${key}`} className='flex items-center'>
									<div
										className='w-4 h-4 rounded-sm mr-3'
										style={{ backgroundColor: featureColors[key] }}
									></div>
									<span className='text-sm text-gray-700'>
										{featureLabels[key]}
									</span>
								</div>
							))}
						</div>

						<div className='mt-6 pt-4 border-t border-gray-200'>
							<h3 className='font-bold text-gray-800 mb-2'>Playlist Summary</h3>
							<div className='text-sm space-y-3'>
								<div className='flex justify-between items-center p-2 bg-blue-50 rounded-lg'>
									<span className='text-gray-600'>Songs selected:</span>
									<span className='font-medium bg-indigo-600 text-white rounded-full px-2.5 py-0.5'>
										{songs.filter((song) => song.score >= cutoff).length} of{" "}
										{songs.length}
									</span>
								</div>
								<div className='flex justify-between items-center p-2 bg-purple-50 rounded-lg'>
									<span className='text-gray-600'>Avg. match score:</span>
									<span className='font-medium bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-full px-2.5 py-0.5'>
										{(
											songs.reduce((sum, song) => sum + song.score, 0) /
											songs.length
										).toFixed(1)}
									</span>
								</div>
								<div className='flex justify-between items-center p-2 bg-indigo-50 rounded-lg'>
									<span className='text-gray-600'>Top features:</span>
									<span className='font-medium text-indigo-700'>
										Energy, Danceability
									</span>
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>
		</div>
	);
};

export default GreedyAlgorithmVisualization;
