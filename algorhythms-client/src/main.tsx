import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Login from "./pages/Login";
import CreatePlaylist from "./pages/CreatePlaylist";
import Layout from "./pages/Layout";
import AuthProvider from "./auth/AuthProvider";
import Home from "./pages/Home";
import ProtectedRoute from "./auth/ProtectedRoute";
import "./index.css";
import LoginCallback from "./pages/LoginCallback";
import ViewPlaylist from "./pages/ViewPlaylist";

createRoot(document.getElementById("root")!).render(
	<StrictMode>
		<BrowserRouter>
			<AuthProvider>
				<Routes>
					<Route path='/' element={<Layout />}>
						<Route index element={<Navigate to='/home' />} />
						<Route path='/home' element={<Home />} />
						<Route path='/login' element={<Login />} />
						<Route path='/login/callback' element={<LoginCallback />} />
						<Route path='/view-playlist' element={<ViewPlaylist />} />
						<Route element={<ProtectedRoute />}>
							<Route path='/create-playlist' element={<CreatePlaylist />} />
						</Route>
					</Route>
				</Routes>
			</AuthProvider>
		</BrowserRouter>
	</StrictMode>,
);
