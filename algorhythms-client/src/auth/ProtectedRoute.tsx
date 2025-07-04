import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "./AuthProvider";

const ProtectedRoute = () => {
	const { user } = useAuth();
	if (!user) return <Navigate to='/login' />;
	return <Outlet />;
};

export default ProtectedRoute;
