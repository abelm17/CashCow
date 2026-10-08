import { Box } from "@mui/material";
import { useAuth } from "./context/AuthContext.jsx";
import Login from "./components/auth/LoginForm";
import Dashboard from "./components/dashboard/Dashboard";
import ThemeToggle from "./components/layout/ThemeToggle.jsx";
import "./App.css";

function App() {
    const { user } = useAuth();

    if (!user) {
        return (
            <>
                <Box component="header" sx={{ display: "flex", justifyContent: "flex-end", p: 2 }}>
                    <ThemeToggle />
                </Box>
                <Login />
            </>
        );
    }

    return <Dashboard />;
}

export default App;