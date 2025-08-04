import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Login from "./pages/Login";
import CreatePlaylist from "./pages/CreatePlaylist";
import AuthProvider from "./auth/AuthProvider";
import Home from "./pages/Home";
import ProtectedRoute from "./auth/ProtectedRoute";
import "./index.css";
import LoginCallback from "./pages/LoginCallback";
import ViewPlaylist from "./pages/ViewPlaylist";
import LoadingPlaylist from "./pages/LoadingPlaylist";
import GreedyVisualization from "./pages/GreedyVisualization";
import Layout from "./pages/Layout";
import FormLayout from "./pages/FormLayout";

createRoot(document.getElementById("root")!).render(
	<StrictMode>
		<BrowserRouter>
			<AuthProvider>
				<Routes>
					<Route path='/' element={<Layout />}>
						<Route path='/home' element={<Home />} />
						<Route path='/test' element={<GreedyVisualization />} />
						<Route path='/login/callback' element={<LoginCallback />} />
						<Route path='/' element={<FormLayout />}>
							<Route index element={<Navigate to='/home' />} />
							<Route path='/login' element={<Login />} />
							<Route path='/view-playlist' element={<ViewPlaylist />} />
							<Route path='/loading-playlist' element={<LoadingPlaylist />} />
							<Route element={<ProtectedRoute />}>
								<Route path='/create-playlist' element={<CreatePlaylist />} />
							</Route>
						</Route>
					</Route>
				</Routes>
			</AuthProvider>
		</BrowserRouter>
	</StrictMode>,
);
