import { useEffect, useState } from "react";
import { DataGrid } from "@mui/x-data-grid";
import {
    Alert,
    Box,
    Button,
    CircularProgress,
    Divider,
    FormControl,
    InputLabel,
    MenuItem,
    Select,
    Stack,
    Typography,
} from "@mui/material";
import apiClient from "../../api/client";
import { useAuth } from "../../context/AuthContext.jsx";

const ADMIN = "Operations Admin";
const AUDITOR = "Auditor";

const lowCashColumns = [
    { field: "atm_id", headerName: "ATM ID", width: 90 },
    { field: "serial_number", headerName: "Serial Number", width: 160 },
    { field: "model", headerName: "Model", width: 130 },
    { field: "cash_level", headerName: "Cash Level", width: 120 },
    { field: "branch_id", headerName: "Branch ID", width: 100 },
    { field: "branch_name", headerName: "Branch", width: 180 },
];

const discrepancyColumns = [
    { field: "service_call_id", headerName: "Service Call ID", width: 130 },
    { field: "title", headerName: "Service Call", width: 220 },
    { field: "atm_id", headerName: "ATM ID", width: 90 },
    { field: "atm_branch_id", headerName: "ATM Branch", width: 110 },
    { field: "technician_id", headerName: "Technician ID", width: 120 },
    { field: "technician_name", headerName: "Technician", width: 170 },
    { field: "technician_branch_id", headerName: "Technician Branch", width: 150 },
];

const reliabilityColumns = [
    { field: "model", headerName: "ATM Model", width: 160 },
    { field: "total_service_calls", headerName: "Total Calls", width: 120 },
    { field: "completed_count", headerName: "Completed", width: 120 },
    { field: "failed_count", headerName: "Failed", width: 100 },
    {
        field: "completion_failure_ratio",
        headerName: "Completion / Failure",
        width: 180,
        valueFormatter: (value) =>
            value == null ? "N/A" : Number(value).toFixed(2),
    },
];

const maintenanceColumns = [
    { field: "branch_id", headerName: "Branch ID", width: 100 },
    { field: "branch_name", headerName: "Branch", width: 180 },
    { field: "total_atms", headerName: "Total ATMs", width: 120 },
    { field: "maintenance_count", headerName: "Maintenance", width: 130 },
    {
        field: "maintenance_percentage",
        headerName: "Maintenance %",
        width: 150,
        valueFormatter: (value) =>
            `${Number(value).toFixed(1)}%`,
    },
];

const technicianColumns = [
    { field: "technician_id", headerName: "Technician ID", width: 120 },
    { field: "technician_name", headerName: "Technician", width: 180 },
    {
        field: "active_service_call_count",
        headerName: "Active Service Calls",
        width: 170,
    },
];

function AnalyticsDashboard() {
    const { user } = useAuth();

    const [lowCash, setLowCash] = useState([]);
    const [discrepancies, setDiscrepancies] = useState([]);
    const [reliability, setReliability] = useState([]);
    const [maintenance, setMaintenance] = useState([]);
    
    const [supervisors, setSupervisors] = useState([]);
    const [selectedSupervisor, setSelectedSupervisor] = useState("");
    const [reportingLine, setReportingLine] = useState(null);
    const [loading, setLoading] = useState(true);
    const [reportingLoading, setReportingLoading] = useState(false);
    const [error, setError] = useState(null);

    const canView = user?.role === ADMIN || user?.role === AUDITOR;

    useEffect(() => {
        if (!canView) {
            setLoading(false);
            return;
        }

        async function fetchAnalytics() {
            try {
                setLoading(true);
                setError(null);

                const [
                    lowCashResponse,
                    discrepancyResponse,
                    reliabilityResponse,
                    maintenanceResponse,
                    supervisorsResponse,
                ] = await Promise.all([
                    apiClient.get("/analytics/low-cash"),
                    apiClient.get("/analytics/co-location-discrepancy"),
                    apiClient.get("/analytics/reliability"),
                    apiClient.get("/analytics/maintenance-flags"),
                    apiClient.get("/analytics/supervisors"),
                ]);

                setLowCash(lowCashResponse.data);
                setDiscrepancies(discrepancyResponse.data);
                setReliability(reliabilityResponse.data);
                setMaintenance(maintenanceResponse.data);
                setSupervisors(supervisorsResponse.data);
            } catch {
                setError("Could not load analytics data.");
            } finally {
                setLoading(false);
            }
        }

        fetchAnalytics();
    }, [canView]);

    const fetchReportingLine = async () => {
        if (!supervisorId) return;

        try {
            setReportingLoading(true);
            setError(null);

            const response = await apiClient.get(
                `/analytics/reporting-lines/${supervisorId}`
            );

            setReportingLine(response.data);
        } catch {
            setReportingLine(null);
            setError("Could not load reporting line data.");
        } finally {
            setReportingLoading(false);
        }
    };

    if (!canView) return null;

    if (loading) {
        return <CircularProgress />;
    }

    return (
        <Box sx={{ p: 3 }}>
            <Typography variant="h4" gutterBottom>
                Analytics Dashboard
            </Typography>

            <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
                Operational analytics for CashCow ATMs, service calls, branches,
                and field technicians.
            </Typography>

            {error && (
                <Alert
                    severity="error"
                    onClose={() => setError(null)}
                    sx={{ mb: 3 }}
                >
                    {error}
                </Alert>
            )}

            <Stack spacing={4}>
                <Box>
                    <Typography variant="h6" gutterBottom>
                        1. Low Cash Alert
                    </Typography>

                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        Active ATMs operating below 20% of the $50,000 cash
                        capacity ($10,000).
                    </Typography>

                    <Box sx={{ height: 400, width: "100%" }}>
                        <DataGrid
                            rows={lowCash}
                            columns={lowCashColumns}
                            getRowId={(row) => row.atm_id}
                            disableRowSelectionOnClick
                        />
                    </Box>
                </Box>

                <Divider />

                <Box>
                    <Typography variant="h6" gutterBottom>
                        2. Co-Location Discrepancy
                    </Typography>

                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        Service calls where the assigned technician is based at
                        a different branch from the ATM.
                    </Typography>

                    <Box sx={{ height: 400, width: "100%" }}>
                        <DataGrid
                            rows={discrepancies}
                            columns={discrepancyColumns}
                            getRowId={(row) => row.service_call_id}
                            disableRowSelectionOnClick
                        />
                    </Box>
                </Box>

                <Divider />

                <Box>
                    <Typography variant="h6" gutterBottom>
                        3. Reliability Metrics
                    </Typography>

                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        Service call completion and failure counts broken down
                        by ATM model.
                    </Typography>

                    <Box sx={{ height: 350, width: "100%" }}>
                        <DataGrid
                            rows={reliability}
                            columns={reliabilityColumns}
                            getRowId={(row) => row.model}
                            disableRowSelectionOnClick
                        />
                    </Box>
                </Box>

                <Divider />

                <Box>
                    <Typography variant="h6" gutterBottom>
                        4. Maintenance Flags
                    </Typography>

                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        Branches where more than 30% of ATMs are currently in
                        maintenance.
                    </Typography>

                    <Box sx={{ height: 350, width: "100%" }}>
                        <DataGrid
                            rows={maintenance}
                            columns={maintenanceColumns}
                            getRowId={(row) => row.branch_id}
                            disableRowSelectionOnClick
                        />
                    </Box>
                </Box>

                <Divider />

                <Box>
                    <Typography variant="h6" gutterBottom>
                        5. Reporting Lines
                    </Typography>

                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        Select an Operations Supervisor to see the technicians
                        reporting to them and their active service calls.
                    </Typography>

                    <FormControl sx={{ minWidth: 300, mb: 3 }}>
                        <InputLabel id="supervisor-select-label">
                            Operations Supervisor
                        </InputLabel>

                        <Select
                            labelId="supervisor-select-label"
                            value={selectedSupervisor}
                            label="Operations Supervisor"
                            onChange={async (event) => {
                                const supervisorId = event.target.value;

                                setSelectedSupervisor(supervisorId);
                                setReportingLine(null);

                                try {
                                    setReportingLoading(true);
                                    setError(null);

                                    const response = await apiClient.get(
                                        `/analytics/reporting-lines/${supervisorId}`
                                    );

                                    setReportingLine(response.data);
                                } catch {
                                    setError("Could not load reporting line data.");
                                } finally {
                                    setReportingLoading(false);
                                }
                            }}
                        >
                            {supervisors.map((supervisor) => (
                                <MenuItem key={supervisor.id} value={supervisor.id}>
                                    {supervisor.name}
                                </MenuItem>
                            ))}
                        </Select>
                    </FormControl>

                    {reportingLoading && <CircularProgress sx={{ ml: 2 }} />}

                    {reportingLine && (
                        <>
                            <Typography variant="body1" sx={{ mb: 2 }}>
                                <strong>Supervisor:</strong>{" "}
                                {reportingLine.supervisor_name}
                                {" — "}
                                <strong>Technicians:</strong>{" "}
                                {reportingLine.technician_count}
                            </Typography>

                            <Box sx={{ height: 350, width: "100%" }}>
                                <DataGrid
                                    rows={reportingLine.technicians}
                                    columns={technicianColumns}
                                    getRowId={(row) => row.technician_id}
                                    disableRowSelectionOnClick
                                />
                            </Box>
                        </>
                    )}
                </Box>
            </Stack>
        </Box>
    );
}

export default AnalyticsDashboard;
