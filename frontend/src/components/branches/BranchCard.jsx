import { Card, CardContent, Typography } from "@mui/material";

function BranchCard({ branch }) {
    return (
        <Card>
            <CardContent>
                <Typography variant="h6">{branch.name}</Typography>
                <Typography color="text.secondary">
                    Region: {branch.location_region}
                </Typography>
                <Typography>
                    Capacity: {branch.capacity}
                </Typography>
                <Typography>
                    Supervisor ID: {branch.supervisor_id}
                </Typography>
            </CardContent>
        </Card>
    );
}

export default BranchCard;
