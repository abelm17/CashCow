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
    "Pending",
    "In-Progress",
    "Completed",
    "Failed",
];

const PRIORITY_OPTIONS = [
    "Low",
    "Medium",
    "Critical",
];

const columns = [
    { field: "id", headerName: "ID" },
    { field: "title", headerName: "Title" },
    { field: "priority", headerName: "Priority" },
    { field: "status", headerName: "Status" },
    { field: "atm_id", headerName: "ATM ID", type: "number" },
    { field: "technician_id", headerName: "Technician ID", type: "number" },
];

const emptyForm = {
    title: "",
    priority: "Low",
    status: "Pending",
    atm_id: "",
    technician_id: "",
};

function ServiceCallDataGrid({ onSuccess }) {
    const { hasPermission } = useAuth();
    const [historyId, setHistoryId] = useState(null);

    const canView = hasPermission("service_call:read");
    const canWrite = hasPermission("service_call:write");
    const canChangeStatus = hasPermission("service_call:status");

    const [serviceCalls, setServiceCalls] = useState([]);
    const [rowCount, setRowCount] = useState(0);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const [paginationModel, setPaginationModel] = useState({
        page: 0,
        pageSize: 25,
    });

    const [sortModel, setSortModel] = useState([
        { field: "id", sort: "asc" },
    ]);

    const [statusFilter, setStatusFilter] = useState("");
    const [priorityFilter, setPriorityFilter] = useState("");
    const [atmFilter, setAtmFilter] = useState("");
    const [technicianFilter, setTechnicianFilter] = useState("");
    const [searchInput, setSearchInput] = useState("");
    const [search, setSearch] = useState("");

    const [dialogOpen, setDialogOpen] = useState(false);
    const [updateDialogOpen, setUpdateDialogOpen] = useState(false);
    const [statusDialogOpen, setStatusDialogOpen] = useState(false);
    const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

    const [updateId, setUpdateId] = useState("");
    const [statusId, setStatusId] = useState("");
    const [deleteId, setDeleteId] = useState("");

    const [formValues, setFormValues] = useState(emptyForm);
    const [newStatus, setNewStatus] = useState("Pending");

    const fetchServiceCalls = useCallback(async () => {
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

            if (priorityFilter) {
                params.priority = priorityFilter;
            }

            if (atmFilter !== "") {
                params.atm_id = Number(atmFilter);
            }

            if (technicianFilter !== "") {
                params.technician_id = Number(technicianFilter);
            }

            if (search) {
                params.search = search;
            }

            const response = await apiClient.get("/service_calls", {
                params,
            });

            setServiceCalls(response.data.items);
            setRowCount(response.data.total);
            setError(null);
        } catch (error) {
            console.error("Could not load service calls:", error);
            setError("Could not load service calls");
        } finally {
            setLoading(false);
        }
    }, [
        paginationModel,
        sortModel,
        statusFilter,
        priorityFilter,
        atmFilter,
        technicianFilter,
        search,
    ]);

    useEffect(() => {
        if (canView) {
            fetchServiceCalls();
        } else {
            setLoading(false);
        }
    }, [canView, fetchServiceCalls]);

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

    const resetPage = () => {
        setPaginationModel((previous) => ({
            ...previous,
            page: 0,
        }));
    };

    const handleCreate = async () => {
        try {
            await apiClient.post("/service_calls", {
                ...formValues,
                atm_id: Number(formValues.atm_id),
                technician_id: Number(formValues.technician_id),
            });

            setDialogOpen(false);
            resetForm();
            resetPage();

            onSuccess?.("Service call created.");

            await fetchServiceCalls();
        } catch (error) {
            console.error("Could not create service call:", error);
            setError("Could not create service call");
        }
    };

    const handleUpdate = async () => {
        try {
            const data = {};

            if (formValues.title !== "") {
                data.title = formValues.title;
            }

            if (formValues.priority !== "") {
                data.priority = formValues.priority;
            }

            if (formValues.status !== "") {
                data.status = formValues.status;
            }

            if (formValues.atm_id !== "") {
                data.atm_id = Number(formValues.atm_id);
            }

            if (formValues.technician_id !== "") {
                data.technician_id = Number(formValues.technician_id);
            }

            await apiClient.patch(`/service_calls/${updateId}`, data);

            const id = updateId;

            setUpdateDialogOpen(false);
            setUpdateId("");
            resetForm();
            resetPage();

            onSuccess?.(`Service call ${id} updated.`);

            await fetchServiceCalls();
        } catch (error) {
            console.error("Could not update service call:", error);
            setError(`Could not update service call ${updateId}`);
        }
    };

    const handleStatusUpdate = async () => {
        try {
            await apiClient.patch(`/service_calls/${statusId}/status`, {
                status: newStatus,
            });

            const id = statusId;

            setStatusDialogOpen(false);
            setStatusId("");
            setNewStatus("Pending");
            resetPage();

            onSuccess?.(`Service call ${id} status updated.`);

            await fetchServiceCalls();
        } catch (error) {
            console.error("Could not update service call status:", error);
            setError(`Could not update service call ${statusId}`);
        }
    };

    const handleDelete = async () => {
        try {
            const id = deleteId;

            await apiClient.delete(`/service_calls/${id}`);

            setDeleteDialogOpen(false);
            setDeleteId("");
            resetPage();

            onSuccess?.(`Service call ${id} deleted.`);

            await fetchServiceCalls();
        } catch (error) {
            console.error("Could not delete service call:", error);
            setError(`Could not delete service call ${deleteId}`);
        }
    };

    if (!canView) {
        return (
            <Alert severity="error">
                You do not have permission to view service calls.
            </Alert>
        );
    }

    if (loading && serviceCalls.length === 0) {
        return (
            <Box
                sx={{
                    display: "flex",
                    justifyContent: "center",
                    alignItems: "center",
                    minHeight: 200,
                }}
            >
                <CircularProgress />
            </Box>
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
                        Add Service Call
                    </Button>

                    <Button
                        variant="outlined"
                        sx={{ mb: 2, mr: 1 }}
                        onClick={() => setUpdateDialogOpen(true)}
                    >
                        Update Service Call
                    </Button>

                    <Button
                        variant="outlined"
                        color="error"
                        sx={{ mb: 2 }}
                        onClick={() => setDeleteDialogOpen(true)}
                    >
                        Delete Service Call
                    </Button>
                </>
            )}

            {canChangeStatus && (
                <Button
                    variant="outlined"
                    sx={{ mb: 2 }}
                    onClick={() => setStatusDialogOpen(true)}
                >
                    Update My Service Call Status
                </Button>
            )}

            <Stack
                direction={{ xs: "column", sm: "row" }}
                spacing={2}
                sx={{ mb: 2 }}
            >
                <TextField
                    label="Search title"
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
                        resetPage();
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
                    select
                    label="Priority"
                    value={priorityFilter}
                    onChange={(event) => {
                        setPriorityFilter(event.target.value);
                        resetPage();
                    }}
                    size="small"
                >
                    <MenuItem value="">All priorities</MenuItem>
                    {PRIORITY_OPTIONS.map((option) => (
                        <MenuItem key={option} value={option}>
                            {option}
                        </MenuItem>
                    ))}
                </TextField>

                <TextField
                    label="ATM ID"
                    type="number"
                    value={atmFilter}
                    onChange={(event) => {
                        setAtmFilter(event.target.value);
                        resetPage();
                    }}
                    size="small"
                />

                <TextField
                    label="Technician ID"
                    type="number"
                    value={technicianFilter}
                    onChange={(event) => {
                        setTechnicianFilter(event.target.value);
                        resetPage();
                    }}
                    size="small"
                />
            </Stack>

            <Box sx={{ height: 450, width: "100%" }}>
                <AppDataGrid
                    rows={serviceCalls}
                    columns={[...columns, {
                        field: "historyAction", headerName: "History", width: 125, sortable: false, filterable: false,
                        renderCell: (params) => <Button size="small" onClick={() => setHistoryId(params.row.id)}>History</Button>,
                    }]}
                    getRowId={(row) => row.id}
                    loading={loading}
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
                        resetPage();
                    }}
                    filterMode="server"
                />
            </Box>

            {/* CREATE */}
            <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)}>
                <DialogTitle>Add Service Call</DialogTitle>
                <DialogContent>
                    <Stack spacing={2} sx={{ mt: 1, minWidth: 300 }}>
                        <TextField
                            label="Title"
                            value={formValues.title}
                            onChange={handleFieldChange("title")}
                        />

                        <TextField
                            select
                            label="Priority"
                            value={formValues.priority}
                            onChange={handleFieldChange("priority")}
                        >
                            {PRIORITY_OPTIONS.map((option) => (
                                <MenuItem key={option} value={option}>
                                    {option}
                                </MenuItem>
                            ))}
                        </TextField>

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

                        <TextField
                            label="ATM ID"
                            type="number"
                            value={formValues.atm_id}
                            onChange={handleFieldChange("atm_id")}
                        />

                        <TextField
                            label="Technician ID"
                            type="number"
                            value={formValues.technician_id}
                            onChange={handleFieldChange("technician_id")}
                        />
                    </Stack>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
                    <Button variant="contained" onClick={handleCreate}>
                        Create
                    </Button>
                </DialogActions>
            </Dialog>

            {/* ADMIN UPDATE */}
            <Dialog
                open={updateDialogOpen}
                onClose={() => setUpdateDialogOpen(false)}
            >
                <DialogTitle>Update Service Call</DialogTitle>
                <DialogContent>
                    <Stack spacing={2} sx={{ mt: 1, minWidth: 300 }}>
                        <TextField
                            label="Service Call ID"
                            type="number"
                            value={updateId}
                            onChange={(event) => setUpdateId(event.target.value)}
                        />

                        <TextField
                            label="Title"
                            value={formValues.title}
                            onChange={handleFieldChange("title")}
                        />

                        <TextField
                            select
                            label="Priority"
                            value={formValues.priority}
                            onChange={handleFieldChange("priority")}
                        >
                            {PRIORITY_OPTIONS.map((option) => (
                                <MenuItem key={option} value={option}>
                                    {option}
                                </MenuItem>
                            ))}
                        </TextField>

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

                        <TextField
                            label="ATM ID"
                            type="number"
                            value={formValues.atm_id}
                            onChange={handleFieldChange("atm_id")}
                        />

                        <TextField
                            label="Technician ID"
                            type="number"
                            value={formValues.technician_id}
                            onChange={handleFieldChange("technician_id")}
                        />
                    </Stack>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setUpdateDialogOpen(false)}>
                        Cancel
                    </Button>
                    <Button
                        variant="contained"
                        disabled={!updateId}
                        onClick={handleUpdate}
                    >
                        Update
                    </Button>
                </DialogActions>
            </Dialog>

            {/* TECHNICIAN STATUS UPDATE */}
            <Dialog
                open={statusDialogOpen}
                onClose={() => setStatusDialogOpen(false)}
            >
                <DialogTitle>Update Service Call Status</DialogTitle>
                <DialogContent>
                    <Stack spacing={2} sx={{ mt: 1, minWidth: 300 }}>
                        <TextField
                            label="Service Call ID"
                            type="number"
                            value={statusId}
                            onChange={(event) => setStatusId(event.target.value)}
                        />

                        <TextField
                            select
                            label="Status"
                            value={newStatus}
                            onChange={(event) => setNewStatus(event.target.value)}
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
                    <Button onClick={() => setStatusDialogOpen(false)}>
                        Cancel
                    </Button>
                    <Button
                        variant="contained"
                        disabled={!statusId}
                        onClick={handleStatusUpdate}
                    >
                        Update
                    </Button>
                </DialogActions>
            </Dialog>

            {/* DELETE */}
            <Dialog
                open={deleteDialogOpen}
                onClose={() => setDeleteDialogOpen(false)}
            >
                <DialogTitle>Delete Service Call</DialogTitle>
                <DialogContent>
                    <TextField
                        autoFocus
                        margin="dense"
                        label="Service Call ID"
                        type="number"
                        fullWidth
                        value={deleteId}
                        onChange={(event) => setDeleteId(event.target.value)}
                    />
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setDeleteDialogOpen(false)}>
                        Cancel
                    </Button>
                    <Button
                        variant="contained"
                        color="error"
                        disabled={!deleteId}
                        onClick={handleDelete}
                    >
                        Delete
                    </Button>
                </DialogActions>
            </Dialog>
            <RecordHistoryDialog type="service_call" recordId={historyId} onClose={() => setHistoryId(null)} />
        </Box>
    );
}

export default ServiceCallDataGrid;