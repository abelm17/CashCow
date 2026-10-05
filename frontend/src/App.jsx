import { useAuth } from "./context/AuthContext.jsx";
import Login from "./components/auth/LoginForm";
import Dashboard from "./components/dashboard/Dashboard";
import "./App.css";

function App() {
    const { user } = useAuth();

    if (!user) {
        return <Login />;
    }

    return <Dashboard />;
}

export default App;
