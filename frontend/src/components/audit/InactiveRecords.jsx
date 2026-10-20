import { useCallback, useEffect, useState } from "react";
import { Alert, Box, Button, CircularProgress, Stack, Tab, Tabs, Typography } from "@mui/material";
import apiClient from "../../api/client";
import { useAuth } from "../../context/AuthContext.jsx";

const resources = {
    atm: { label: "ATMs", base: "/atms", description: (r) => `${r.serial_number} — ${r.model}` },
    service_call: { label: "Service Calls", base: "/service_calls", description: (r) => r.title },
};
export default function InactiveRecords() {
    const { hasPermission } = useAuth();
    const [type, setType] = useState("atm");
    const [items, setItems] = useState([]);
    const [loading, setLoading] = useState(false);
    const [workingId, setWorkingId] = useState(null);
    const [error, setError] = useState("");
    const [notice, setNotice] = useState("");
    const load = useCallback(async () => {
        setLoading(true); setError("");
        try { const { data } = await apiClient.get(`${resources[type].base}/inactive`); setItems(data); }
        catch (err) { setError(err.response?.data?.detail ?? "Unable to load inactive records"); }
        finally { setLoading(false); }
    }, [type]);
    useEffect(() => { if (hasPermission("user:manage")) load(); }, [load, hasPermission]);
    if (!hasPermission("user:manage")) return <Alert severity="error">Access denied.</Alert>;
    const restore = async (id) => {
        setWorkingId(id); setError(""); setNotice("");
        try {
            await apiClient.post(`${resources[type].base}/${id}/restore`);
            setNotice(`${resources[type].label} record #${id} restored.`);
            await load();
        } catch (err) { setError(err.response?.data?.detail ?? "Restore failed"); }
        finally { setWorkingId(null); }
    };
    return <Box sx={{ p: 3 }}>
        <Typography variant="h5" gutterBottom>Inactive Records</Typography>
        <Tabs value={type} onChange={(_, next) => { setType(next); setNotice(""); }}>
            <Tab label="ATMs" value="atm" /><Tab label="Service Calls" value="service_call" />
        </Tabs>
        {error && <Alert severity="error" sx={{ mt: 2 }}>{String(error)}</Alert>}
        {notice && <Alert severity="success" sx={{ mt: 2 }}>{notice}</Alert>}
        {loading ? <CircularProgress sx={{ mt: 3 }} /> : (
            <Stack spacing={1} sx={{ mt: 2 }}>
                {items.length === 0 && <Typography>No inactive records.</Typography>}
                {items.map((record) => <Box key={record.id} sx={{ p: 2, border: 1, borderColor: "divider", borderRadius: 1, display: "flex", alignItems: "center", justifyContent: "space-between", gap: 2 }}>
                    <Box>
                        <Typography fontWeight={600}>#{record.id} — {resources[type].description(record)}</Typography>
                        <Typography variant="body2" color="text.secondary">
                            Deleted {record.deleted_at ? new Date(record.deleted_at).toLocaleString() : "at unknown time"} · By user ID {record.deleted_by ?? "Unknown"}
                        </Typography>
                    </Box>
                    <Button variant="outlined" disabled={workingId !== null} onClick={() => restore(record.id)}>
                        {workingId === record.id ? "Restoring…" : "Restore"}
                    </Button>
                </Box>)}
            </Stack>
        )}
    </Box>;
}