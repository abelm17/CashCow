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
    const { user } = useAuth();

    const [atms, setAtms] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const [dialogOpen, setDialogOpen] = useState(false);
    const [updateDialogOpen, setUpdateDialogOpen] = useState(false);
    const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

    const [updateAtmId, setUpdateAtmId] = useState("");
    const [deleteAtmId, setDeleteAtmId] = useState("");
    const [formValues, setFormValues] = useState(emptyForm);

    const isAdmin = user?.role === ADMIN;
    const canView = [ADMIN, TECHNICIAN, AUDITOR].includes(user?.role);

    async function fetchAtms() {
        setLoading(true);

        try {
            const response = await apiClient.get("/atms");
            setAtms(response.data);
            setError(null);
        } catch {
            setError("Could not load ATM data");
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        if (canView) {
            fetchAtms();
        } else {
            setLoading(false);
        }
    }, [canView]);

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

            <Box sx={{ height: 400, width: "100%" }}>
                <AppDataGrid
                    rows={atms}
                    columns={columns}
                    getRowId={(row) => row.id}
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
        </Box>
    );
}

export default AtmDataGrid;
