import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App.jsx";
import { AuthProvider } from "./context/AuthContext.jsx";
import { ThemeModeProvider } from "./context/ThemeModeContext.jsx";

createRoot(document.getElementById("root")).render(
    <StrictMode>
        <ThemeModeProvider>
            <AuthProvider>
                <App />
            </AuthProvider>
        </ThemeModeProvider>
    </StrictMode>
);
