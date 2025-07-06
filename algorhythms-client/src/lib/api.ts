import type { Weights } from "./types";

const BASE_URL = "http://127.0.0.1:8000";

const fetchAPI = async (
	endpoint: string,
	params: any = {},
	options?: RequestInit,
) => {
	const apiURL = new URL(endpoint, BASE_URL);
	apiURL.search = new URLSearchParams(params).toString();

	const response = await fetch(apiURL, options);
	if (!response.ok) {
		throw new Error("Network response was not ok");
		console.error(response);
	}
	return response.json();
};

export const getGeneratedWeights = (input: {
	mood: string;
	activity: string;
}): Promise<Weights> => {
	return fetchAPI("generate-weights", input);
};
