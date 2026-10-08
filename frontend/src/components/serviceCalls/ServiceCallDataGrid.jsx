import { useEffect, useState } from "react";
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

const ADMIN = "Operations Admin";
const TECHNICIAN = "Field Technician";
const AUDITOR = "Auditor";

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
    { field: "id", headerName: "ID", width: 70 },
    { field: "title", headerName: "Title", width: 240 },
    { field: "priority", headerName: "Priority", width: 120 },
    { field: "status", headerName: "Status", width: 130 },
    { field: "atm_id", headerName: "ATM ID", width: 90, type: "number" },
    {
        field: "technician_id",
        headerName: "Technician ID",
        width: 130,
        type: "number",
    },
];

const emptyForm = {
    title: "",
    priority: "Low",
    status: "Pending",
    atm_id: "",
    technician_id: "",
};

function ServiceCallDataGrid({ onSuccess }) {
    const { user } = useAuth();

    const isAdmin = user?.role === ADMIN;
    const isTechnician = user?.role === TECHNICIAN;
    const isAuditor = user?.role === AUDITOR;

    const canView = isAdmin || isTechnician || isAuditor;

    const [serviceCalls, setServiceCalls] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const [dialogOpen, setDialogOpen] = useState(false);
    const [updateDialogOpen, setUpdateDialogOpen] = useState(false);
    const [statusDialogOpen, setStatusDialogOpen] = useState(false);
    const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

    const [updateId, setUpdateId] = useState("");
    const [statusId, setStatusId] = useState("");
    const [deleteId, setDeleteId] = useState("");

    const [formValues, setFormValues] = useState(emptyForm);
    const [newStatus, setNewStatus] = useState("Pending");

    async function fetchServiceCalls() {
        setLoading(true);

        try {
            const response = await apiClient.get("/service_calls");

            setServiceCalls(response.data);
            setError(null);
        } catch (error) {
            console.error("Could not load service calls:", error);
            setError("Could not load service calls");
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        if (canView) {
            fetchServiceCalls();
        } else {
            setLoading(false);
        }
    }, [canView]);

    const handleFieldChange = (field) => (event) => {
        setFormValues((prev) => ({
            ...prev,
            [field]: event.target.value,
        }));
    };

    const resetForm = () => {
        setFormValues(emptyForm);
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

            await apiClient.patch(
                `/service_calls/${updateId}`,
                data
            );

            const id = updateId;

            setUpdateDialogOpen(false);
            setUpdateId("");
            resetForm();

            onSuccess?.(`Service call ${id} updated.`);

            await fetchServiceCalls();
        } catch (error) {
            console.error("Could not update service call:", error);
            setError(`Could not update service call ${updateId}`);
        }
    };

    const handleStatusUpdate = async () => {
        try {
            await apiClient.patch(
                `/service_calls/${statusId}/status`,
                {
                    status: newStatus,
                }
            );

            const id = statusId;

            setStatusDialogOpen(false);
            setStatusId("");
            setNewStatus("Pending");

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

            onSuccess?.(`Service call ${id} deleted.`);

            await fetchServiceCalls();
        } catch (error) {
            console.error("Could not delete service call:", error);
            setError(`Could not delete service call ${deleteId}`);
        }
    };

    if (!canView) {
        return null;
    }

    if (loading) {
        return <CircularProgress />;
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

            {isAdmin && (
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

            {isTechnician && (
                <Button
                    variant="outlined"
                    sx={{ mb: 2 }}
                    onClick={() => setStatusDialogOpen(true)}
                >
                    Update My Service Call Status
                </Button>
            )}

            <Box sx={{ height: 450, width: "100%" }}>
                <AppDataGrid
                    rows={serviceCalls}
                    columns={columns}
                    getRowId={(row) => row.id}
                />
            </Box>

            {/* ADMIN CREATE */}
            <Dialog
                open={dialogOpen}
                onClose={() => setDialogOpen(false)}
            >
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
                            onChange={(event) =>
                                setUpdateId(event.target.value)
                            }
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

            {/* TECHNICIAN STATUS */}
            <Dialog
                open={statusDialogOpen}
                onClose={() => setStatusDialogOpen(false)}
            >
                <DialogTitle>
                    Update Service Call Status
                </DialogTitle>

                <DialogContent>
                    <Stack spacing={2} sx={{ mt: 1, minWidth: 300 }}>
                        <TextField
                            label="Service Call ID"
                            type="number"
                            value={statusId}
                            onChange={(event) =>
                                setStatusId(event.target.value)
                            }
                        />

                        <TextField
                            select
                            label="Status"
                            value={newStatus}
                            onChange={(event) =>
                                setNewStatus(event.target.value)
                            }
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
                    <Button
                        onClick={() => setStatusDialogOpen(false)}
                    >
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

            {/* ADMIN DELETE */}
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
                        onChange={(event) =>
                            setDeleteId(event.target.value)
                        }
                    />
                </DialogContent>

                <DialogActions>
                    <Button
                        onClick={() => setDeleteDialogOpen(false)}
                    >
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
        </Box>
    );
}

export default ServiceCallDataGrid;
