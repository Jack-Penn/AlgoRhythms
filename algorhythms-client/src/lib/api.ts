const BASE_URL = "http://127.0.0.1:8000";

const fetchAPI = async (endpoint: string, options?: RequestInit) => {
	const response = await fetch(`${BASE_URL}/${endpoint}`, options);
	if (!response.ok) {
		throw new Error("Network response was not ok");
	}
	return response.json();
};

export const testapi = (): Promise<{ Hello: string }> => {
	return fetchAPI("");
};
