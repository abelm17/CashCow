import { useEffect, useState } from "react";
import { DataGrid } from "@mui/x-data-grid";
import {
    Alert,
    Box,
    CircularProgress,
    Typography,
} from "@mui/material";
import apiClient from "../../api/client";
import { useAuth } from "../../context/AuthContext.jsx";

const ADMIN = "Operations Admin";

const columns = [
    {
        field: "id",
        headerName: "ID",
        width: 70,
    },
    {
        field: "name",
        headerName: "Name",
        width: 200,
    },
    {
        field: "username",
        headerName: "Username",
        width: 180,
    },
    {
        field: "role",
        headerName: "Role",
        width: 180,
    },
];

function UserDataGrid() {
    const { user } = useAuth();

    const isAdmin = user?.role === ADMIN;

    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    async function fetchUsers() {
        setLoading(true);

        try {
            const response = await apiClient.get("/users");

            setUsers(response.data);
            setError(null);
        } catch (error) {
            console.error("Could not load users:", error);
            setError("Could not load users");
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        if (isAdmin) {
            fetchUsers();
        } else {
            setLoading(false);
        }
    }, [isAdmin]);

    if (!isAdmin) {
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

            <Typography variant="h6" sx={{ mb: 2 }}>
                Users
            </Typography>

            <Box sx={{ height: 450, width: "100%" }}>
                <DataGrid
                    rows={users}
                    columns={columns}
                    getRowId={(row) => row.id}
                />
            </Box>
        </Box>
    );
}

export default UserDataGrid;
