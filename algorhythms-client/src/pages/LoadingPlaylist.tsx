import { InformationCircleIcon } from "@heroicons/react/16/solid";
import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";

type Task = {
	id: string;
	label: string;
	description: string;
	status: "pending" | "running" | "completed";
	duration?: string;
	additionalData?: Record<string, any>;
};
type TaskMap = {
	[key: string]: Task;
};
type InitialData = {
	type: "initial";
	timestamp: number;
	tasks: (Omit<Task, "status"> & { status: "pending" })[];
};
interface UpdateDataBase {
	type: "update";
	timestamp: number;
	task_id: string;
	duration: string;
}
interface RunningUpdate extends UpdateDataBase {
	status: "running";
}
interface CompletedUpdate extends UpdateDataBase {
	status: "completed";
	data: any;
}
type UpdateData = RunningUpdate | CompletedUpdate;
type FinalData = {
	type: "final";
	timestamp: number;
	playlist_id: string;
};

type ChunkData = InitialData | UpdateData | FinalData;

const LoadingPlaylist = () => {
	const navigate = useNavigate();

	const isInitalized = useRef(false);
	const [tasks, setTasks] = useState<TaskMap>({});

	useEffect(() => {
		const processStream = async () => {
			const response = await fetch("http://127.0.0.1:8000/generate-playlist");
			if (!response.body) {
				console.error("Could not fetch generate-playlist", response);
				return;
			}
			const reader = response.body.getReader();
			const decoder = new TextDecoder();

			while (true) {
				const { value, done } = await reader.read();
				if (done) break;

				// represents newest received chunks from server connection
				const chunks = decoder.decode(value).split("\n\n");
				for (const chunk of chunks) {
					if (!chunk.trim()) continue;

					try {
						const data: ChunkData = JSON.parse(chunk);

						switch (data.type) {
							case "initial":
								// Initialize tasks with definitions
								const initialTasks: TaskMap = data.tasks.reduce(
									(obj, task) => ({ ...obj, [task.id]: task }),
									{},
								);
								setTasks(initialTasks);
								break;
							case "update":
								// Update specific task
								setTasks((prev) => {
									const updatedTask = {
										...prev[data.task_id],
										status: data.status,
										...(data.duration && { duration: data.duration }),
									};
									// Add this block to handle additional data
									if (data.status === "completed" && "data" in data) {
										updatedTask.additionalData = data.data;
									}
									return {
										...prev,
										[data.task_id]: updatedTask,
									};
								});
								break;
							case "final":
								// setTimeout(() => {
								// 	// Navigate to view-playlist route with playlist ID
								// 	navigate(`/view-playlist`);
								// }, 1000);
								break; // Exit the loop after navigation
						}
						if (data.type === "initial") {
						} else if (data.type === "update") {
						}
					} catch (error) {
						console.error("Error parsing chunk:", error);
					}
				}
			}
		};

		if (!isInitalized.current) {
			isInitalized.current = true;
			processStream();
		}
	}, []);

	// Calculate progress percentage
	const taskList = Object.values(tasks);
	const completed = taskList.filter((t) => t.status === "completed").length;
	const progress =
		taskList.length != 0 ? (completed / taskList.length) * 100 : 0;

	return (
		<div className='w-full max-w-md bg-white rounded-2xl shadow-xl overflow-hidden'>
			{/* Header Section */}
			<div className='bg-gradient-to-r from-blue-600 to-purple-600 p-8 text-center'>
				<div className='flex flex-row align-middle justify-center gap-4'>
					<div className='w-16 h-16 my-auto rounded-full border-dashed border border-white'>
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
					<h1 className='text-2xl font-bold text-white my-auto'>AlgoRhythms</h1>
				</div>
			</div>

			{/* Content Section */}
			<div className='p-8'>
				<p className='text-center text-gray-700 mb-6'>
					Finding the perfect songs for you...
				</p>

				{/* Progress Bar */}
				<div className='mb-8'>
					<div className='flex justify-between items-center mb-2'>
						<span className='text-sm font-medium text-gray-700'>Progress</span>
						<span className='text-sm font-medium text-gray-700'>
							{Math.round(progress)}%
						</span>
					</div>
					<div className='w-full h-2 bg-gray-200 rounded-full overflow-hidden'>
						<div
							className='h-full bg-gradient-to-r from-blue-500 to-purple-500 rounded-full transition-all duration-300'
							style={{ width: `${progress}%` }}
						/>
					</div>
				</div>

				{/* Algorithm Status */}
				<div>
					<h3 className='text-lg font-bold text-gray-800 mb-4'>
						Algorithm Status
					</h3>
					<ul className='space-y-4'>
						{taskList.map((task, index) => (
							<li key={index} className='flex flex-col items-start'>
								<div className='flex'>
									<div className='flex-shrink-0 mt-1 mr-3'>
										{/* Status Indicator */}
										<div
											className={`w-3 h-3 rounded-full ${
												task.status === "completed"
													? "bg-green-500"
													: task.status === "running"
													? "bg-blue-500 animate-pulse"
													: "bg-gray-300"
											}`}
										/>
									</div>
									<div>
										<div className='flex items-baseline'>
											<strong className='font-medium text-gray-800'>
												{task.label}
											</strong>
											{task.duration && (
												<span className='text-gray-500 text-sm ml-2'>
													({task.duration})
												</span>
											)}
										</div>
										<div className='text-gray-500 text-sm mt-1'>
											{task.description}
										</div>
									</div>
								</div>

								{/* Add this block for additional data */}
								{task.status === "completed" && task.additionalData && (
									<AdditionalDataDisplay data={task.additionalData} />
								)}
							</li>
						))}
					</ul>
				</div>
			</div>
		</div>
	);
};

export default LoadingPlaylist;

const AdditionalDataDisplay = ({ data }: { data: Record<string, any> }) => (
	<div className='mt-2 ml-4 px-3 py-2 bg-gradient-to-br from-blue-50 to-purple-50 rounded-lg border border-purple-200 shadow-sm transform transition-all duration-300 hover:scale-[1.01] hover:shadow-md'>
		<div className='flex flex-start'>
			<InformationCircleIcon className='size-4 text-purple-700 mt-0.5 flex-shrink-0' />

			<div className='ml-2 flex-1 min-w-0'>
				{Object.entries(data).map(([key, value]) => (
					<div key={key} className='text-xs mb-1 last:mb-0 animate-fadeIn'>
						{key === "message" ? (
							<div className='font-medium text-purple-700 italic'>
								"{value}"
							</div>
						) : (
							<div className='flex'>
								<span className='font-semibold text-purple-800 capitalize mr-1.5'>
									{key}:
								</span>
								<span className='text-gray-700 truncate' title={String(value)}>
									{value}
								</span>
							</div>
						)}
					</div>
				))}
			</div>
		</div>
	</div>
);
