import { Card, CardContent, Typography } from "@mui/material";
import { useAuth } from "../../context/AuthContext.jsx";

const ADMIN = "Operations Admin";

function UserCard({ user: userData }) {
    const { user } = useAuth();

    if (!user || user.role !== ADMIN) {
        return null;
    }

    return (
        <Card>
            <CardContent>
                <Typography variant="h6">
                    {userData.name}
                </Typography>

                <Typography color="text.secondary">
                    Username: {userData.username}
                </Typography>

                <Typography color="text.secondary">
                    Role: {userData.role}
                </Typography>

                <Typography color="text.secondary">
                    User ID: {userData.id}
                </Typography>
            </CardContent>
        </Card>
    );
}

export default UserCard;
