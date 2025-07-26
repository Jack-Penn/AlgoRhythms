import { Outlet } from "react-router-dom";
import "./layout.css";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const queryClient = new QueryClient();

export default function Layout() {
	return (
		<div className='min-h-screen bg-gradient-to-br from-indigo-900 to-purple-800 flex flex-col items-center justify-center p-4'>
				<QueryClientProvider client={queryClient}>
					<Outlet />
				</QueryClientProvider>
		</div>
	);
}
