import { Card, CardContent, Typography } from "@mui/material";

function ServiceCallCard({ serviceCall }) {
    return (
        <Card>
            <CardContent>
                <Typography variant="h6">{serviceCall.title}</Typography>
                <Typography>Priority: {serviceCall.priority}</Typography>
                <Typography>Status: {serviceCall.status}</Typography>
                <Typography>ATM ID: {serviceCall.atm_id}</Typography>
                <Typography>Technician ID: {serviceCall.technician_id}</Typography>
            </CardContent>
        </Card>
    );
}

export default ServiceCallCard;
