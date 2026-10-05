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
const AUDITOR = "Auditor";

const columns = [
    { field: "id", headerName: "ID", width: 70 },
    { field: "name", headerName: "Branch", width: 180 },
    {
        field: "location_region",
        headerName: "Region",
        width: 180,
    },
    {
        field: "capacity",
        headerName: "Capacity",
        width: 110,
        type: "number",
    },
    {
        field: "supervisor_id",
        headerName: "Supervisor ID",
        width: 130,
        type: "number",
    },
];

const emptyForm = {
    name: "",
    location_region: "",
    capacity: "",
    supervisor_id: "",
};

function BranchDataGrid({ onSuccess }) {
    const { user } = useAuth();

    const isAdmin = user?.role === ADMIN;
    const isAuditor = user?.role === AUDITOR;

    const canView = isAdmin || isAuditor;

    const [branches, setBranches] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const [dialogOpen, setDialogOpen] = useState(false);
    const [updateDialogOpen, setUpdateDialogOpen] = useState(false);
    const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

    const [updateBranchId, setUpdateBranchId] = useState("");
    const [deleteBranchId, setDeleteBranchId] = useState("");

    const [formValues, setFormValues] = useState(emptyForm);

    async function fetchBranches() {
        setLoading(true);

        try {
            const response = await apiClient.get("/branches");

            setBranches(response.data);
            setError(null);
        } catch (error) {
            console.error("Could not load branches:", error);
            setError("Could not load branch data");
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        if (canView) {
            fetchBranches();
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
            await apiClient.post("/branches", {
                ...formValues,
                capacity: Number(formValues.capacity),
                supervisor_id: Number(formValues.supervisor_id),
            });

            setDialogOpen(false);
            resetForm();

            onSuccess?.("Branch created successfully.");

            await fetchBranches();
        } catch (error) {
            console.error("Could not create branch:", error);
            setError("Could not create branch");
        }
    };

    const handleUpdate = async () => {
        try {
            const data = {};

            if (formValues.name !== "") {
                data.name = formValues.name;
            }

            if (formValues.location_region !== "") {
                data.location_region = formValues.location_region;
            }

            if (formValues.capacity !== "") {
                data.capacity = Number(formValues.capacity);
            }

            if (formValues.supervisor_id !== "") {
                data.supervisor_id = Number(
                    formValues.supervisor_id
                );
            }

            await apiClient.patch(
                `/branches/${updateBranchId}`,
                data
            );

            const id = updateBranchId;

            setUpdateDialogOpen(false);
            setUpdateBranchId("");
            resetForm();

            onSuccess?.(`Branch ${id} was updated.`);

            await fetchBranches();
        } catch (error) {
            console.error("Could not update branch:", error);
            setError(`Could not update branch ${updateBranchId}`);
        }
    };

    const handleDelete = async () => {
        try {
            const id = deleteBranchId;

            await apiClient.delete(`/branches/${id}`);

            setDeleteDialogOpen(false);
            setDeleteBranchId("");

            onSuccess?.(`Branch ${id} was deleted.`);

            await fetchBranches();
        } catch (error) {
            console.error("Could not delete branch:", error);
            setError(`Could not delete branch ${deleteBranchId}`);
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
                        Add Branch
                    </Button>

                    <Button
                        variant="outlined"
                        sx={{ mb: 2, mr: 1 }}
                        onClick={() => setUpdateDialogOpen(true)}
                    >
                        Update Branch
                    </Button>

                    <Button
                        variant="outlined"
                        color="error"
                        sx={{ mb: 2 }}
                        onClick={() => setDeleteDialogOpen(true)}
                    >
                        Delete Branch
                    </Button>
                </>
            )}

            <Box sx={{ height: 400, width: "100%" }}>
                <DataGrid
                    rows={branches}
                    columns={columns}
                    getRowId={(row) => row.id}
                />
            </Box>

            <Dialog
                open={dialogOpen}
                onClose={() => setDialogOpen(false)}
            >
                <DialogTitle>Add Branch</DialogTitle>

                <DialogContent>
                    <Stack spacing={2} sx={{ mt: 1, minWidth: 300 }}>
                        <TextField
                            label="Name"
                            value={formValues.name}
                            onChange={handleFieldChange("name")}
                        />

                        <TextField
                            label="Region"
                            value={formValues.location_region}
                            onChange={handleFieldChange(
                                "location_region"
                            )}
                        />

                        <TextField
                            label="Capacity"
                            type="number"
                            value={formValues.capacity}
                            onChange={handleFieldChange("capacity")}
                        />

                        <TextField
                            label="Supervisor ID"
                            type="number"
                            value={formValues.supervisor_id}
                            onChange={handleFieldChange(
                                "supervisor_id"
                            )}
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

            <Dialog
                open={updateDialogOpen}
                onClose={() => setUpdateDialogOpen(false)}
            >
                <DialogTitle>Update Branch</DialogTitle>

                <DialogContent>
                    <Stack spacing={2} sx={{ mt: 1, minWidth: 300 }}>
                        <TextField
                            label="Branch ID"
                            type="number"
                            value={updateBranchId}
                            onChange={(event) =>
                                setUpdateBranchId(event.target.value)
                            }
                        />

                        <TextField
                            label="Name"
                            value={formValues.name}
                            onChange={handleFieldChange("name")}
                        />

                        <TextField
                            label="Region"
                            value={formValues.location_region}
                            onChange={handleFieldChange(
                                "location_region"
                            )}
                        />

                        <TextField
                            label="Capacity"
                            type="number"
                            value={formValues.capacity}
                            onChange={handleFieldChange("capacity")}
                        />

                        <TextField
                            label="Supervisor ID"
                            type="number"
                            value={formValues.supervisor_id}
                            onChange={handleFieldChange(
                                "supervisor_id"
                            )}
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
                        disabled={!updateBranchId}
                        onClick={handleUpdate}
                    >
                        Update
                    </Button>
                </DialogActions>
            </Dialog>

            <Dialog
                open={deleteDialogOpen}
                onClose={() => setDeleteDialogOpen(false)}
            >
                <DialogTitle>Delete Branch</DialogTitle>

                <DialogContent>
                    <TextField
                        autoFocus
                        margin="dense"
                        label="Branch ID"
                        type="number"
                        fullWidth
                        value={deleteBranchId}
                        onChange={(event) =>
                            setDeleteBranchId(event.target.value)
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
                        disabled={!deleteBranchId}
                        onClick={handleDelete}
                    >
                        Delete
                    </Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
}

export default BranchDataGrid;
