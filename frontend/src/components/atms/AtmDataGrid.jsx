import RecordHistoryDialog from "../audit/RecordHistoryDialog.jsx";
import { useEffect, useState, useCallback } from "react";
import AppDataGrid from "../common/AppDataGrid.jsx";
import {
    Alert,
    Box,
    CircularProgress,
    Button,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    MenuItem,
    Stack,
    TextField,
} from "@mui/material";
import apiClient from "../../api/client";
import { useAuth } from "../../context/AuthContext.jsx";

const STATUS_OPTIONS = [
    "Operational",
    "In-Transport",
    "Maintenance",
    "Offline",
];

const columns = [
    { field: "id", headerName: "ID", width: 70 },
    { field: "serial_number", headerName: "Serial Number", width: 160 },
    { field: "model", headerName: "Model", width: 140 },
    { field: "status", headerName: "Status", width: 140 },
    { field: "cash_level", headerName: "Cash Level", width: 120, type: "number" },
    { field: "branch_id", headerName: "Branch ID", width: 100, type: "number" },
];

const emptyForm = {
    serial_number: "",
    model: "",
    status: "Offline",
    cash_level: "",
    branch_id: "",
};

function AtmDataGrid({ onSuccess }) {
    const { hasPermission } = useAuth();
    const [historyId, setHistoryId] = useState(null);

    const [atms, setAtms] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const [dialogOpen, setDialogOpen] = useState(false);
    const [updateDialogOpen, setUpdateDialogOpen] = useState(false);
    const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

    const [updateAtmId, setUpdateAtmId] = useState("");
    const [deleteAtmId, setDeleteAtmId] = useState("");
    const [formValues, setFormValues] = useState(emptyForm);

    const [rowCount, setRowCount] = useState(0);
    const [paginationModel, setPaginationModel] = useState({
        page: 0,
        pageSize: 25,
    });

    const [sortModel, setSortModel] = useState([
        { field: "id", sort: "asc" },
    ]);

    const [statusFilter, setStatusFilter] = useState("");
    const [branchFilter, setBranchFilter] = useState("");
    const [searchInput, setSearchInput] = useState("");
    const [search, setSearch] = useState("");

    const canView = hasPermission("atm:read");
    const canWrite = hasPermission("atm:write");

    const fetchAtms = useCallback(async () => {
        setLoading(true);

        try {
            const currentSort = sortModel[0] ?? {
                field: "id",
                sort: "asc",
            };

            const params = {
                page: paginationModel.page + 1,
                size: paginationModel.pageSize,
                sort_by: currentSort.field,
                sort_dir: currentSort.sort ?? "asc",
            };

            if (statusFilter) {
                params.status = statusFilter;
            }

            if (branchFilter !== "") {
                params.branch_id = Number(branchFilter);
            }

            if (search) {
                params.search = search;
            }

            const response = await apiClient.get("/atms", { params });

            setAtms(response.data.items);
            setRowCount(response.data.total);
            setError(null);
        } catch {
            setError("Could not load ATM data");
        } finally {
            setLoading(false);
        }
    }, [
        paginationModel,
        sortModel,
        statusFilter,
        branchFilter,
        search,
    ]);

    useEffect(() => {
        if (canView) {
            fetchAtms();
        } else {
            setLoading(false);
        }
    }, [canView, fetchAtms]);

    useEffect(() => {
        const timer = setTimeout(() => {
            setSearch(searchInput.trim());
            setPaginationModel((previous) => ({
                ...previous,
                page: 0,
            }));
        }, 350);

        return () => clearTimeout(timer);
    }, [searchInput]);

    const handleFieldChange = (field) => (event) => {
        setFormValues((previous) => ({
            ...previous,
            [field]: event.target.value,
        }));
    };

    const resetForm = () => {
        setFormValues(emptyForm);
    };

    const handleCreate = async () => {
        try {
            await apiClient.post("/atms", {
                ...formValues,
                cash_level: Number(formValues.cash_level),
                branch_id: Number(formValues.branch_id),
            });

            const serialNumber = formValues.serial_number;

            setDialogOpen(false);
            resetForm();

            onSuccess?.(`ATM ${serialNumber} was created.`);

            await fetchAtms();
        } catch {
            setError("Could not create ATM");
        }
    };

    const handleUpdate = async () => {
        try {
            const updateData = {};

            if (formValues.status !== "") {
                updateData.status = formValues.status;
            }

            if (formValues.cash_level !== "") {
                updateData.cash_level = Number(formValues.cash_level);
            }

            if (formValues.branch_id !== "") {
                updateData.branch_id = Number(formValues.branch_id);
            }

            await apiClient.patch(`/atms/${updateAtmId}`, updateData);

            const id = updateAtmId;

            setUpdateDialogOpen(false);
            setUpdateAtmId("");
            resetForm();

            onSuccess?.(`ATM ${id} was updated.`);

            await fetchAtms();
        } catch {
            setError(`Could not update ATM ${updateAtmId}`);
        }
    };

    const handleDelete = async () => {
        try {
            const id = deleteAtmId;

            await apiClient.delete(`/atms/${id}`);

            setDeleteDialogOpen(false);
            setDeleteAtmId("");

            onSuccess?.(`ATM ${id} was deleted.`);

            await fetchAtms();
        } catch {
            setError(`Could not delete ATM ${deleteAtmId}`);
        }
    };

    if (!canView) {
        return (
            <Alert severity="error">
                You do not have permission to view ATMs.
            </Alert>
        );
    }


    return (
        <Box>
            {error && (
                <Alert
                    severity="error"
                    onClose={() => setError(null)}
                    sx={{ mb: 2 }}
                >
                    {error}
                </Alert>
            )}

            {canWrite && (
                <>
                    <Button
                        variant="outlined"
                        sx={{ mb: 2, mr: 1 }}
                        onClick={() => setDialogOpen(true)}
                    >
                        Add ATM
                    </Button>

                    <Button
                        variant="outlined"
                        sx={{ mb: 2, mr: 1 }}
                        onClick={() => setUpdateDialogOpen(true)}
                    >
                        Update ATM
                    </Button>

                    <Button
                        variant="outlined"
                        color="error"
                        sx={{ mb: 2 }}
                        onClick={() => setDeleteDialogOpen(true)}
                    >
                        Delete ATM
                    </Button>
                </>
            )}

            <Stack
                direction={{ xs: "column", sm: "row" }}
                spacing={2}
                sx={{ mb: 2 }}
            >
                <TextField
                    label="Search model or serial number"
                    value={searchInput}
                    onChange={(event) => setSearchInput(event.target.value)}
                    size="small"
                />

                <TextField
                    select
                    label="Status"
                    value={statusFilter}
                    onChange={(event) => {
                        setStatusFilter(event.target.value);
                        setPaginationModel((previous) => ({
                            ...previous,
                            page: 0,
                        }));
                    }}
                    size="small"
                >
                    <MenuItem value="">All statuses</MenuItem>
                    {STATUS_OPTIONS.map((option) => (
                        <MenuItem key={option} value={option}>
                            {option}
                        </MenuItem>
                    ))}
                </TextField>

                <TextField
                    label="Branch ID"
                    type="number"
                    value={branchFilter}
                    onChange={(event) => {
                        setBranchFilter(event.target.value);
                        setPaginationModel((previous) => ({
                            ...previous,
                            page: 0,
                        }));
                    }}
                    size="small"
                />
            </Stack>

            <Box sx={{ height: 400, width: "100%" }}>
                {loading && (
                <Box
                    sx={{
                        display: "flex",
                        justifyContent: "center",
                        py: 1,
                    }}
                >
                    <CircularProgress size={28} />
                </Box>
                )}
                <AppDataGrid
                    rows={atms}
                    columns={[...columns, {
                        field: "historyAction", headerName: "History", width: 125, sortable: false, filterable: false,
                        renderCell: (params) => <Button size="small" onClick={() => setHistoryId(params.row.id)}>History</Button>,
                    }]}
                    getRowId={(row) => row.id}

                    // loading={loading}
                    rowCount={rowCount}

                    pagination
                    paginationMode="server"
                    paginationModel={paginationModel}
                    onPaginationModelChange={setPaginationModel}
                    pageSizeOptions={[10, 25, 50, 100]}

                    sortingMode="server"
                    sortModel={sortModel}
                    onSortModelChange={(newModel) => {
                        setSortModel(
                            newModel.length > 0
                                ? newModel
                                : [{ field: "id", sort: "asc" }]
                        );

                        setPaginationModel((previous) => ({
                            ...previous,
                            page: 0,
                        }));
                    }}

                    filterMode="server"
                />
            </Box>

            {/* CREATE ATM */}

            <Dialog
                open={dialogOpen}
                onClose={() => setDialogOpen(false)}
            >
                <DialogTitle>Add New ATM</DialogTitle>

                <DialogContent>
                    <Stack
                        spacing={2}
                        sx={{ mt: 1, minWidth: 300 }}
                    >
                        <TextField
                            label="Serial Number"
                            value={formValues.serial_number}
                            onChange={handleFieldChange("serial_number")}
                        />

                        <TextField
                            label="Model"
                            value={formValues.model}
                            onChange={handleFieldChange("model")}
                        />

                        <TextField
                            label="Cash Level"
                            type="number"
                            value={formValues.cash_level}
                            onChange={handleFieldChange("cash_level")}
                        />

                        <TextField
                            label="Branch ID"
                            type="number"
                            value={formValues.branch_id}
                            onChange={handleFieldChange("branch_id")}
                        />

                        <TextField
                            select
                            label="Status"
                            value={formValues.status}
                            onChange={handleFieldChange("status")}
                        >
                            {STATUS_OPTIONS.map((option) => (
                                <MenuItem key={option} value={option}>
                                    {option}
                                </MenuItem>
                            ))}
                        </TextField>
                    </Stack>
                </DialogContent>

                <DialogActions>
                    <Button onClick={() => setDialogOpen(false)}>
                        Cancel
                    </Button>

                    <Button
                        variant="contained"
                        onClick={handleCreate}
                    >
                        Create
                    </Button>
                </DialogActions>
            </Dialog>

            {/* UPDATE ATM */}

            <Dialog
                open={updateDialogOpen}
                onClose={() => setUpdateDialogOpen(false)}
            >
                <DialogTitle>Update ATM</DialogTitle>

                <DialogContent>
                    <Stack
                        spacing={2}
                        sx={{ mt: 1, minWidth: 300 }}
                    >
                        <TextField
                            label="ATM ID"
                            type="number"
                            value={updateAtmId}
                            onChange={(event) =>
                                setUpdateAtmId(event.target.value)
                            }
                        />

                        <TextField
                            label="Cash Level"
                            type="number"
                            value={formValues.cash_level}
                            onChange={handleFieldChange("cash_level")}
                        />

                        <TextField
                            label="Branch ID"
                            type="number"
                            value={formValues.branch_id}
                            onChange={handleFieldChange("branch_id")}
                        />

                        <TextField
                            select
                            label="Status"
                            value={formValues.status}
                            onChange={handleFieldChange("status")}
                        >
                            {STATUS_OPTIONS.map((option) => (
                                <MenuItem key={option} value={option}>
                                    {option}
                                </MenuItem>
                            ))}
                        </TextField>
                    </Stack>
                </DialogContent>

                <DialogActions>
                    <Button onClick={() => setUpdateDialogOpen(false)}>
                        Cancel
                    </Button>

                    <Button
                        variant="contained"
                        disabled={!updateAtmId}
                        onClick={handleUpdate}
                    >
                        Update
                    </Button>
                </DialogActions>
            </Dialog>

            {/* DELETE ATM */}

            <Dialog
                open={deleteDialogOpen}
                onClose={() => setDeleteDialogOpen(false)}
            >
                <DialogTitle>Delete ATM</DialogTitle>

                <DialogContent>
                    <TextField
                        autoFocus
                        margin="dense"
                        label="ATM ID"
                        type="number"
                        fullWidth
                        value={deleteAtmId}
                        onChange={(event) =>
                            setDeleteAtmId(event.target.value)
                        }
                    />
                </DialogContent>

                <DialogActions>
                    <Button onClick={() => setDeleteDialogOpen(false)}>
                        Cancel
                    </Button>

                    <Button
                        variant="contained"
                        color="error"
                        disabled={!deleteAtmId}
                        onClick={handleDelete}
                    >
                        Delete
                    </Button>
                </DialogActions>
            </Dialog>
            <RecordHistoryDialog type="atm" recordId={historyId} onClose={() => setHistoryId(null)} />
        </Box>
    );
}

export default AtmDataGrid;
