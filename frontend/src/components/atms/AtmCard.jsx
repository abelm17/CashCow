import { Card, CardContent, Typography } from "@mui/material";

function AtmCard ({atm}){
    return(
        <Card>
            <CardContent>
                <Typography>
                    Serial Number: {atm.serial_number}
                </Typography>

                <Typography>
                    Model: {atm.model}
                </Typography>

                <Typography>
                    Status: {atm.status}
                </Typography>

                <Typography>
                    Cash Level: ${atm.cash_level}
                </Typography>

                <Typography>
                    Branch ID: {atm.branch_id}
                </Typography>
            </CardContent>
        </Card>
    );
}

export default AtmCard;