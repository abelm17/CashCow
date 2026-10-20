import { Button, Stack, Typography } from "@mui/material";
import { useAuth } from "../../context/AuthContext.jsx";
import ThemeToggle from "./ThemeToggle.jsx";

function AppHeader({ onNavigate }) {
    const { user, logout, hasPermission } = useAuth();


    return (
        <header>
            <Stack
                direction="row"
                
                sx={{ 
                    display: "flex",
                    justifyContent:"space-between",
                    alignItems: "center",
                    p: 1.5,
                    gap: 1 
                }}
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
                        {hasPermission("analytics:read") && (
                            <Button onClick={() => onNavigate("analytics")}>
                                Analytics
                            </Button>
                        )}

                        {/* Everyone */}
                        {hasPermission("atm:read") && <Button onClick={() => onNavigate("atms")}>
                            ATMs
                        </Button>}

                        {/* Admin + Auditor */}
                        {hasPermission("branch:read") && (
                            <Button onClick={() => onNavigate("branches")}>
                                Branches
                            </Button>
                        )}

                        {/* Everyone */}
                        {hasPermission("service_call:read") && <Button onClick={() => onNavigate("service-calls")}>
                            Service Calls
                        </Button>}

                        {/* Everyone */}
                        {hasPermission("report:read") && <Button
                            onClick={() =>
                                onNavigate("diagnostic-reports")
                            }
                        >
                            Diagnostic Reports
                        </Button>}

                        {/* Admin only */}
                        {hasPermission("user:manage") && (
                            <Button onClick={() => onNavigate("users")}>
                                Users
                            </Button>
                        )}

                        {hasPermission("user:manage") && (
                            <Button onClick={() => onNavigate("inactive-records")}>Inactive Records</Button>
                        )}

                        {/* Everyone */}
                        <ThemeToggle />

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