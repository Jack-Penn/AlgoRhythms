import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Home from "./pages/Home2";
import CreatePlaylist from "./pages/CreatePlaylist";
import Layout from "./pages/Layout";
import "./index.css";

createRoot(document.getElementById("root")!).render(
	<StrictMode>
		<BrowserRouter>
			<Routes>
				<Route path='/' element={<Layout />}>
					<Route index element={<Home />} />
					<Route path='/create-playlist' element={<CreatePlaylist />} />
				</Route>
			</Routes>
		</BrowserRouter>
	</StrictMode>,
);
