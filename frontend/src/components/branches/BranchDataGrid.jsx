
import { useCallback, useEffect, useState } from "react";
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
const AUDITOR = "Auditor";

const columns = [
    { field: "id", headerName: "ID" },
    { field: "name", headerName: "Branch" },
    { field: "location_region", headerName: "Region" },
    { field: "capacity", headerName: "Capacity", type: "number" },
    {
        field: "supervisor_id",
        headerName: "Supervisor ID",
        type: "number",
    },
];

const emptyForm = {
    name: "",
    location_region: "",
    capacity: "",
    supervisor_id: "",
};

const emptyUpdateForm = {
    name: "",
    location_region: "",
    capacity: "",
    supervisor_id: "",
};

function BranchDataGrid({ onSuccess }) {
    const { user } = useAuth();

    const isAdmin = user?.role === ADMIN;
    const canView = [ADMIN, AUDITOR].includes(user?.role);

    const [branches, setBranches] = useState([]);
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

    const [searchInput, setSearchInput] = useState("");
    const [search, setSearch] = useState("");
    const [regionFilter, setRegionFilter] = useState("");
    const [supervisorFilter, setSupervisorFilter] = useState("");

    const [dialogOpen, setDialogOpen] = useState(false);
    const [updateDialogOpen, setUpdateDialogOpen] = useState(false);
    const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

    const [updateBranchId, setUpdateBranchId] = useState("");
    const [deleteBranchId, setDeleteBranchId] = useState("");
    const [formValues, setFormValues] = useState(emptyForm);
    const [updateValues, setUpdateValues] = useState(emptyUpdateForm);

    const fetchBranches = useCallback(async () => {
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

            if (search) params.search = search;
            if (regionFilter) params.region = regionFilter;

            if (supervisorFilter !== "") {
                params.supervisor_id = Number(supervisorFilter);
            }

            const response = await apiClient.get("/branches", { params });

            setBranches(response.data.items);
            setRowCount(response.data.total);
            setError(null);
        } catch (error) {
            console.error("Could not load branches:", error);
            setError("Could not load branch data");
        } finally {
            setLoading(false);
        }
    }, [
        paginationModel,
        sortModel,
        search,
        regionFilter,
        supervisorFilter,
    ]);

    useEffect(() => {
        if (canView) {
            fetchBranches();
        } else {
            setLoading(false);
        }
    }, [canView, fetchBranches]);

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

    const handleUpdateFieldChange = (field) => (event) => {
        setUpdateValues((previous) => ({
            ...previous,
            [field]: event.target.value,
        }));
    };

    const resetForm = () => {
        setFormValues({ ...emptyForm });
    };

    const resetUpdateForm = () => {
        setUpdateValues({ ...emptyUpdateForm });
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

            if (updateValues.name !== "") {
                data.name = updateValues.name;
            }

            if (updateValues.location_region !== "") {
                data.location_region = updateValues.location_region;
            }

            if (updateValues.capacity !== "") {
                data.capacity = Number(updateValues.capacity);
            }

            if (updateValues.supervisor_id !== "") {
                data.supervisor_id = Number(updateValues.supervisor_id);
            }

            if (Object.keys(data).length === 0) {
                setError("Enter at least one field to update.");
                return;
            }

            await apiClient.patch(
                `/branches/${updateBranchId}`,
                data
            );

            const id = updateBranchId;

            setUpdateDialogOpen(false);
            setUpdateBranchId("");
            resetUpdateForm();

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

    if (!canView) return null;

    if (loading) {
        return (
            <Box sx={{ display: "flex", justifyContent: "center", p: 4 }}>
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

            {isAdmin && (
                <Stack
                    direction={{ xs: "column", sm: "row" }}
                    spacing={1}
                    sx={{ mb: 2 }}
                >
                    <Button variant="outlined" onClick={() => {
                        resetForm();
                        setDialogOpen(true);
                    }}>
                        Add Branch
                    </Button>

                    <Button variant="outlined" onClick={() => {
                        resetUpdateForm();
                        setUpdateBranchId("");
                        setUpdateDialogOpen(true);
                    }}>
                        Update Branch
                    </Button>

                    <Button
                        variant="outlined"
                        color="error"
                        onClick={() => setDeleteDialogOpen(true)}
                    >
                        Delete Branch
                    </Button>
                </Stack>
            )}

            <Stack
                direction={{ xs: "column", md: "row" }}
                spacing={2}
                sx={{ mb: 2 }}
            >
                <TextField
                    label="Search branch or region"
                    value={searchInput}
                    onChange={(event) => setSearchInput(event.target.value)}
                    size="small"
                />

                <TextField
                    label="Region filter"
                    value={regionFilter}
                    onChange={(event) => {
                        setRegionFilter(event.target.value);
                        setPaginationModel((previous) => ({
                            ...previous,
                            page: 0,
                        }));
                    }}
                    size="small"
                />

                <TextField
                    label="Supervisor ID"
                    type="number"
                    value={supervisorFilter}
                    onChange={(event) => {
                        setSupervisorFilter(event.target.value);
                        setPaginationModel((previous) => ({
                            ...previous,
                            page: 0,
                        }));
                    }}
                    size="small"
                />
            </Stack>

            <AppDataGrid
                rows={branches}
                columns={columns}
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
                        newModel.length
                            ? newModel
                            : [{ field: "id", sort: "asc" }]
                    );
                    setPaginationModel((previous) => ({
                        ...previous,
                        page: 0,
                    }));
                }}
                disableColumnFilter
            />

            {/* CREATE BRANCH */}
            <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)}>
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
                            onChange={handleFieldChange("location_region")}
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
                            onChange={handleFieldChange("supervisor_id")}
                        />
                    </Stack>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
                    <Button
                        variant="contained"
                        onClick={handleCreate}
                        disabled={
                            !formValues.name.trim() ||
                            !formValues.location_region.trim() ||
                            formValues.capacity === "" ||
                            formValues.supervisor_id === ""
                        }
                    >
                        Create
                    </Button>
                </DialogActions>
            </Dialog>

            {/* UPDATE BRANCH */}
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
                            onChange={(event) => setUpdateBranchId(event.target.value)}
                        />
                        <TextField
                            label="Name"
                            value={updateValues.name}
                            onChange={handleUpdateFieldChange("name")}
                        />
                        <TextField
                            label="Region"
                            value={updateValues.location_region}
                            onChange={handleUpdateFieldChange("location_region")}
                        />
                        <TextField
                            label="Capacity"
                            type="number"
                            value={updateValues.capacity}
                            onChange={handleUpdateFieldChange("capacity")}
                        />
                        <TextField
                            label="Supervisor ID"
                            type="number"
                            value={updateValues.supervisor_id}
                            onChange={handleUpdateFieldChange("supervisor_id")}
                        />
                    </Stack>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setUpdateDialogOpen(false)}>Cancel</Button>
                    <Button
                        variant="contained"
                        disabled={!updateBranchId}
                        onClick={handleUpdate}
                    >
                        Update
                    </Button>
                </DialogActions>
            </Dialog>

            {/* DELETE BRANCH */}
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
                        onChange={(event) => setDeleteBranchId(event.target.value)}
                    />
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
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
