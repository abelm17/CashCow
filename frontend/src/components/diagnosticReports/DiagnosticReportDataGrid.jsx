import { useEffect, useState } from "react";
import { DataGrid } from "@mui/x-data-grid";
import {
    Alert,
    Box,
    CircularProgress,
    Button,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    Stack,
    TextField,
} from "@mui/material";
import apiClient from "../../api/client";
import { useAuth } from "../../context/AuthContext.jsx";

const ADMIN = "Operations Admin";
const TECHNICIAN = "Field Technician";
const AUDITOR = "Auditor";

const columns = [
    { field: "id", headerName: "ID", width: 70 },
    { field: "file_url", headerName: "File", width: 220 },
    { field: "notes", headerName: "Notes", width: 300 },
    {
        field: "service_call_id",
        headerName: "Service Call ID",
        width: 140,
        type: "number",
    },
    {
        field: "technician_id",
        headerName: "Technician ID",
        width: 130,
        type: "number",
    },
];

const emptyForm = {
    file_url: "",
    notes: "",
    service_call_id: "",
    technician_id: "",
};

function DiagnosticReportDataGrid({ onSuccess }) {
    const { user } = useAuth();

    const isAdmin = user?.role === ADMIN;
    const isTechnician = user?.role === TECHNICIAN;
    const isAuditor = user?.role === AUDITOR;

    const canView = isAdmin || isTechnician || isAuditor;

    const [reports, setReports] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const [dialogOpen, setDialogOpen] = useState(false);
    const [updateDialogOpen, setUpdateDialogOpen] = useState(false);
    const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

    const [updateId, setUpdateId] = useState("");
    const [deleteId, setDeleteId] = useState("");

    const [formValues, setFormValues] = useState(emptyForm);

    async function fetchReports() {
        setLoading(true);

        try {
            const response = await apiClient.get(
                "/diagnostic_reports"
            );

            setReports(response.data);
            setError(null);
        } catch (error) {
            console.error(
                "Could not load diagnostic reports:",
                error
            );

            setError("Could not load diagnostic reports");
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        if (canView) {
            fetchReports();
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
            await apiClient.post("/diagnostic_reports", {
                ...formValues,
                service_call_id: Number(
                    formValues.service_call_id
                ),
                technician_id: Number(
                    formValues.technician_id
                ),
            });

            setDialogOpen(false);
            resetForm();

            onSuccess?.("Diagnostic report created.");

            await fetchReports();
        } catch (error) {
            console.error(
                "Could not create diagnostic report:",
                error
            );

            setError("Could not create diagnostic report");
        }
    };

    const handleUpdate = async () => {
        try {
            const data = {};

            if (formValues.file_url !== "") {
                data.file_url = formValues.file_url;
            }

            if (formValues.notes !== "") {
                data.notes = formValues.notes;
            }

            await apiClient.patch(
                `/diagnostic_reports/${updateId}`,
                data
            );

            const id = updateId;

            setUpdateDialogOpen(false);
            setUpdateId("");
            resetForm();

            onSuccess?.(`Diagnostic report ${id} updated.`);

            await fetchReports();
        } catch (error) {
            console.error(
                "Could not update diagnostic report:",
                error
            );

            setError(
                `Could not update diagnostic report ${updateId}`
            );
        }
    };

    const handleDelete = async () => {
        try {
            const id = deleteId;

            await apiClient.delete(
                `/diagnostic_reports/${id}`
            );

            setDeleteDialogOpen(false);
            setDeleteId("");

            onSuccess?.(`Diagnostic report ${id} deleted.`);

            await fetchReports();
        } catch (error) {
            console.error(
                "Could not delete diagnostic report:",
                error
            );

            setError(
                `Could not delete diagnostic report ${deleteId}`
            );
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
                        Add Report
                    </Button>

                    <Button
                        variant="outlined"
                        sx={{ mb: 2, mr: 1 }}
                        onClick={() => setUpdateDialogOpen(true)}
                    >
                        Update Report
                    </Button>

                    <Button
                        variant="outlined"
                        color="error"
                        sx={{ mb: 2 }}
                        onClick={() => setDeleteDialogOpen(true)}
                    >
                        Delete Report
                    </Button>
                </>
            )}

            {isTechnician && (
                <Button
                    variant="outlined"
                    sx={{ mb: 2 }}
                    onClick={() => setDialogOpen(true)}
                >
                    Attach Diagnostic Report
                </Button>
            )}

            <Box sx={{ height: 450, width: "100%" }}>
                <DataGrid
                    rows={reports}
                    columns={columns}
                    getRowId={(row) => row.id}
                />
            </Box>

            {/* CREATE / ATTACH */}
            <Dialog
                open={dialogOpen}
                onClose={() => setDialogOpen(false)}
            >
                <DialogTitle>
                    {isTechnician
                        ? "Attach Diagnostic Report"
                        : "Add Diagnostic Report"}
                </DialogTitle>

                <DialogContent>
                    <Stack spacing={2} sx={{ mt: 1, minWidth: 300 }}>
                        <TextField
                            label="File URL"
                            value={formValues.file_url}
                            onChange={handleFieldChange("file_url")}
                        />

                        <TextField
                            label="Notes"
                            multiline
                            rows={3}
                            value={formValues.notes}
                            onChange={handleFieldChange("notes")}
                        />

                        <TextField
                            label="Service Call ID"
                            type="number"
                            value={formValues.service_call_id}
                            onChange={handleFieldChange(
                                "service_call_id"
                            )}
                        />

                        {isAdmin && (
                            <TextField
                                label="Technician ID"
                                type="number"
                                value={formValues.technician_id}
                                onChange={handleFieldChange(
                                    "technician_id"
                                )}
                            />
                        )}
                    </Stack>
                </DialogContent>

                <DialogActions>
                    <Button
                        onClick={() => setDialogOpen(false)}
                    >
                        Cancel
                    </Button>

                    <Button
                        variant="contained"
                        onClick={handleCreate}
                    >
                        {isTechnician ? "Attach" : "Create"}
                    </Button>
                </DialogActions>
            </Dialog>

            {/* ADMIN UPDATE */}
            <Dialog
                open={updateDialogOpen}
                onClose={() => setUpdateDialogOpen(false)}
            >
                <DialogTitle>
                    Update Diagnostic Report
                </DialogTitle>

                <DialogContent>
                    <Stack spacing={2} sx={{ mt: 1, minWidth: 300 }}>
                        <TextField
                            label="Report ID"
                            type="number"
                            value={updateId}
                            onChange={(event) =>
                                setUpdateId(event.target.value)
                            }
                        />

                        <TextField
                            label="File URL"
                            value={formValues.file_url}
                            onChange={handleFieldChange("file_url")}
                        />

                        <TextField
                            label="Notes"
                            multiline
                            rows={3}
                            value={formValues.notes}
                            onChange={handleFieldChange("notes")}
                        />
                    </Stack>
                </DialogContent>

                <DialogActions>
                    <Button
                        onClick={() => setUpdateDialogOpen(false)}
                    >
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

            {/* ADMIN DELETE */}
            <Dialog
                open={deleteDialogOpen}
                onClose={() => setDeleteDialogOpen(false)}
            >
                <DialogTitle>
                    Delete Diagnostic Report
                </DialogTitle>

                <DialogContent>
                    <TextField
                        autoFocus
                        margin="dense"
                        label="Report ID"
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

export default DiagnosticReportDataGrid;
