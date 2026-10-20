import { useMemo } from "react";
import { Box } from "@mui/material";
import { DataGrid } from "@mui/x-data-grid";

const COLUMN_WIDTH = 175;

function AppDataGrid({
    columns,
    height = 400,
    columnWidth = COLUMN_WIDTH,
    ...gridProps
}) {
    const equalColumns = useMemo(
        () => columns.map((column) => ({
            ...column,
            width: columnWidth,
            minWidth: columnWidth,
            maxWidth: columnWidth,
            flex: undefined,
            resizable: false,
        })),
        [columns, columnWidth]
    );

    return (
        <Box
            sx={{
                height,
                width: equalColumns.length * columnWidth + 20,
                maxWidth: "100%",
                mx: "auto",
            }}
        >
            <DataGrid
                {...gridProps}
                columns={equalColumns}
                sortingMode={gridProps.sortingMode ?? "client"}
            />
        </Box>
    );
}

export default AppDataGrid;