import { createContext, useState, useContext, useCallback } from "react";
import { generatePlaylistStream } from "../api";
import type { AccessTokenResponse } from "../spotify/auth";
import type { Features, Weights } from "../types";

// Types for the stream data chunks
type Task = {
	id: string;
	label: string;
	description: string;
	status: "pending" | "running" | "completed";
	duration?: string;
	additionalData?: Record<string, any>;
};

type TaskMap = { [key: string]: Task };

type InitialData = {
	type: "initial";
	tasks: (Omit<Task, "status"> & { status: "pending" })[];
};

interface UpdateDataBase {
	type: "update";
	task_id: string;
	duration?: string;
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
	data: {
		// Assuming the final data contains the playlist ID
		kd_tree_playlist?: { tracks: any[]; generation_time: number };
	};
};

type ChunkData = InitialData | UpdateData | FinalData;

// Define the shape of our context state
interface PlaylistGenerationState {
	tasks: TaskMap;
	status: "idle" | "streaming" | "completed" | "error";
	finalData: FinalData["data"] | null;
	startGeneration: (params: StartGenerationParams) => Promise<void>;
}

// Define the parameters needed to start the generation
interface StartGenerationParams {
	mood: string;
	activity: string;
	length: number;
	favorite_songs: string[] | null;
	targetProfile: Features;
	weights: Weights;
	auth: AccessTokenResponse | null;
}

// Create the context
const PlaylistGenerationContext = createContext<
	PlaylistGenerationState | undefined
>(undefined);

// Create the Provider component
export const PlaylistGenerationProvider = ({
	children,
}: {
	children: React.ReactNode;
}) => {
	const [tasks, setTasks] = useState<TaskMap>({});
	const [status, setStatus] =
		useState<PlaylistGenerationState["status"]>("idle");
	const [finalData, setFinalData] = useState<FinalData["data"] | null>(null);

	const handleStreamUpdate = (chunk: ChunkData) => {
		console.log("Received chunk:", chunk);

		switch (chunk.type) {
			case "initial":
				const initialTasks: TaskMap = chunk.tasks.reduce(
					(obj, task) => ({ ...obj, [task.id]: task }),
					{},
				);
				setTasks(initialTasks);
				break;
			case "update":
				setTasks((prev) => {
					const updatedTask: Task = {
						...prev[chunk.task_id],
						status: chunk.status,
						...(chunk.duration && { duration: chunk.duration }),
					};
					if (chunk.status === "completed" && "data" in chunk) {
						updatedTask.additionalData = chunk.data;
					}
					return { ...prev, [chunk.task_id]: updatedTask };
				});
				break;
			case "final":
				setFinalData(chunk.data);
				setStatus("completed");
				break;
		}
	};

	const startGeneration = useCallback(async (params: StartGenerationParams) => {
		setTasks({});
		setFinalData(null);
		setStatus("streaming");
		console.log("starting generation");
		try {
			await generatePlaylistStream(params, handleStreamUpdate);
		} catch (error) {
			console.error("Playlist generation failed:", error);
			setStatus("error");
		}
	}, []);

	const value = { tasks, status, finalData, startGeneration };

	return (
		<PlaylistGenerationContext.Provider value={value}>
			{children}
		</PlaylistGenerationContext.Provider>
	);
};

// Create a custom hook for easy consumption
export const usePlaylistGeneration = () => {
	const context = useContext(PlaylistGenerationContext);
	if (context === undefined) {
		throw new Error(
			"usePlaylistGeneration must be used within a PlaylistGenerationProvider",
		);
	}
	return context;
};
