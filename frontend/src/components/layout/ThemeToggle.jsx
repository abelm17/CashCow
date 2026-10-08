import { Button } from "@mui/material";
import { useThemeMode } from "../../context/ThemeModeContext.jsx";

export default function ThemeToggle() {
    const { mode, toggleMode } = useThemeMode();
    const label = `Switch to ${mode === "light" ? "dark" : "light"} mode`;
    return (
        <Button type="button" variant="outlined" onClick={toggleMode} aria-label={label}>
            {label}
        </Button>
    );
}