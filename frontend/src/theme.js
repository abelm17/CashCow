import { createTheme } from "@mui/material/styles";

export default function getAppTheme(mode) {
    return createTheme({
        palette: {
            mode,
        },
    });
}