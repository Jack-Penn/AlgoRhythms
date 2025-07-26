import { Outlet } from "react-router-dom";
import "./layout.css";

export default function FormLayout() {
	return (
		<div className='w-full max-w-md bg-white rounded-2xl shadow-xl overflow-hidden'>
			<Outlet />
		</div>
	);
}
