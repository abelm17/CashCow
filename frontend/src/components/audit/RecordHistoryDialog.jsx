import { useEffect, useState } from "react";
import { Alert, Box, CircularProgress, Dialog, DialogActions, DialogContent, DialogTitle, Button, Stack, Typography } from "@mui/material";
import apiClient from "../../api/client";

export default function RecordHistoryDialog({ type, recordId, onClose }) {
    const [entries, setEntries] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    useEffect(() => {
        if (recordId == null) return;
        let active = true;
        setLoading(true);
        setError("");
        const base = type === "atm" ? "/atms" : "/service_calls";
        apiClient.get(`${base}/${recordId}/history`)
            .then(({ data }) => { if (active) setEntries(data); })
            .catch((err) => { if (active) setError(err.response?.data?.detail ?? "Unable to load history"); })
            .finally(() => { if (active) setLoading(false); });
        return () => { active = false; };
    }, [type, recordId]);
    return (
        <Dialog open={recordId != null} onClose={onClose} fullWidth maxWidth="md">
            <DialogTitle>History — {type === "atm" ? "ATM" : "Service Call"} #{recordId}</DialogTitle>
            <DialogContent dividers>
                {loading && <CircularProgress size={24} />}
                {error && <Alert severity="error">{error}</Alert>}
                {!loading && !error && entries.length === 0 && <Typography>No history recorded.</Typography>}
                {!loading && !error && <Stack spacing={2}>
                    {entries.map((entry) => (
                        <Box key={entry.id} sx={{ borderBottom: 1, borderColor: "divider", pb: 1 }}>
                            <Typography variant="subtitle2">{entry.action} · Actor ID {entry.actor_id ?? "Unknown"}</Typography>
                            <Typography variant="caption" color="text.secondary">
                                {entry.created_at ? new Date(entry.created_at).toLocaleString() : "Unknown time"}
                            </Typography>
                            <Box component="pre" sx={{ whiteSpace: "pre-wrap", overflowWrap: "anywhere", fontSize: 12, m: 0, mt: 1 }}>
                                {JSON.stringify(entry.changes ?? {}, null, 2)}
                            </Box>
                        </Box>
                    ))}
                </Stack>}
            </DialogContent>
            <DialogActions><Button onClick={onClose}>Close</Button></DialogActions>
        </Dialog>
    );
}