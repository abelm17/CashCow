import { Button, Stack, Typography } from "@mui/material";
import { useAuth } from "../../context/AuthContext.jsx";

const ADMIN = "Operations Admin";
const TECHNICIAN = "Field Technician";
const AUDITOR = "Auditor";

function AppHeader({ onNavigate }) {
    const { user, logout } = useAuth();

    const isAdmin = user?.role === ADMIN;
    const isTechnician = user?.role === TECHNICIAN;
    const isAuditor = user?.role === AUDITOR;

    return (
        <header>
            <Stack
                direction="row"
                justifyContent="space-between"
                alignItems="center"
                sx={{ p: 2 }}
            >
                <Typography variant="h4">
                    CashCow
                </Typography>

                <nav>
                    <Stack direction="row" spacing={1}>

                        {/* Everyone */}
                        <Button onClick={() => onNavigate("dashboard")}>
                            Dashboard
                        </Button>

                        {/* Admin + Auditor */}
                        {(isAdmin || isAuditor) && (
                            <Button onClick={() => onNavigate("analytics")}>
                                Analytics
                            </Button>
                        )}

                        {/* Everyone */}
                        <Button onClick={() => onNavigate("atms")}>
                            ATMs
                        </Button>

                        {/* Admin + Auditor */}
                        {(isAdmin || isAuditor) && (
                            <Button onClick={() => onNavigate("branches")}>
                                Branches
                            </Button>
                        )}

                        {/* Everyone */}
                        <Button onClick={() => onNavigate("service-calls")}>
                            Service Calls
                        </Button>

                        {/* Everyone */}
                        <Button
                            onClick={() =>
                                onNavigate("diagnostic-reports")
                            }
                        >
                            Diagnostic Reports
                        </Button>

                        {/* Admin only */}
                        {isAdmin && (
                            <Button onClick={() => onNavigate("users")}>
                                Users
                            </Button>
                        )}

                        {/* Everyone */}
                        <Button
                            color="error"
                            onClick={logout}
                        >
                            Log Out
                        </Button>

                    </Stack>
                </nav>
            </Stack>

            {user && (
                <Typography
                    variant="body2"
                    sx={{ px: 2, pb: 1 }}
                >
                    Logged in as: {user.username} ({user.role})
                </Typography>
            )}
        </header>
    );
}

export default AppHeader;
