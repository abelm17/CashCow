import { createContext, useCallback, useContext, useMemo, useState } from "react";
import { CssBaseline, useMediaQuery } from "@mui/material";
import { ThemeProvider } from "@mui/material/styles";
import getAppTheme from "../theme.js";
import { readStoredValue, writeStoredValue } from "../utils/storage.js";

const ThemeModeContext = createContext(null);
const STORAGE_KEY = "cashcow-theme-mode";

export function ThemeModeProvider({ children }) {
    const systemPrefersDark = useMediaQuery("(prefers-color-scheme: dark)", {
        noSsr: true,
    });
    const [chosenMode, setChosenMode] = useState(() => {
        const stored = readStoredValue(STORAGE_KEY);
        return stored === "light" || stored === "dark" ? stored : null;
    });

    const mode = chosenMode ?? (systemPrefersDark ? "dark" : "light");
    const theme = useMemo(() => getAppTheme(mode), [mode]);
    const toggleMode = useCallback(() => {
        const nextMode = mode === "light" ? "dark" : "light";
        setChosenMode(nextMode);
        writeStoredValue(STORAGE_KEY, nextMode);
    }, [mode]);
    const value = useMemo(() => ({ mode, toggleMode }), [mode, toggleMode]);

    return (
        <ThemeModeContext.Provider value={value}>
            <ThemeProvider theme={theme}>
                <CssBaseline enableColorScheme />
                {children}
            </ThemeProvider>
        </ThemeModeContext.Provider>
    );
}

export function useThemeMode() {
    const context = useContext(ThemeModeContext);
    if (!context) throw new Error("useThemeMode must be used inside ThemeModeProvider");
    return context;
}
