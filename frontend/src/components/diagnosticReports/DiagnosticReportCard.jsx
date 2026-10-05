import { Card, CardContent, Typography } from "@mui/material";

function DiagnosticReportCard({ report }) {
    return (
        <Card>
            <CardContent>
                <Typography variant="h6">Report #{report.id}</Typography>
                <Typography>Service Call: {report.service_call_id}</Typography>
                <Typography>Technician: {report.technician_id}</Typography>
                <Typography sx={{ mt: 1 }}>{report.notes}</Typography>
                <Typography color="text.secondary" sx={{ mt: 1 }}>
                    {report.file_url}
                </Typography>
            </CardContent>
        </Card>
    );
}

export default DiagnosticReportCard;
