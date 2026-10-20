import InactiveRecords from "../audit/InactiveRecords.jsx";
// import { AppBar, Toolbar, Typography, Box, Button } from '@mui/material';
// import PrecisionManufacturingIcon from '@mui/icons-material/PrecisionManufacturing';
import AppHeader from "../layout/AppHeader";
import AtmDataGrid from "../atms/AtmDataGrid";
import { useState } from "react";
import { useAuth } from "../../context/AuthContext.jsx";
import { AppBar } from "@mui/material";
import AnalyticsDashboard from "../analytics/AnalyticsDashboard";
import BranchDataGrid from "../branches/BranchDataGrid";
import ServiceCallDataGrid from "../serviceCalls/ServiceCallDataGrid";
import DiagnosticReportDataGrid from "../diagnosticReports/DiagnosticReportDataGrid";
import UserDataGrid from "../users/UserDataGrid";

function Dashboard() {
    const [section, setSection] = useState("dashboard");
    const { hasPermission } = useAuth();
    return(
        <>
            <AppHeader onNavigate={setSection}/>
        
            <main>
                {section === "dashboard" && (
                    <h2>Welcome to CashCow, Meridian Bank's Branch Operations Command Center!</h2>
                )}

                {section === "analytics" && hasPermission("analytics:read") && (
                    <AnalyticsDashboard />
                )}

                {section === "atms" && hasPermission("atm:read") && (
                    <AtmDataGrid/>
                )}  

                {section === "branches" && hasPermission("branch:read") && (
                    <BranchDataGrid />
                )}

                {section === "service-calls" && hasPermission("service_call:read") && (
                    <ServiceCallDataGrid />
                )}

                {section === "diagnostic-reports" && hasPermission("report:read") && (
                    <DiagnosticReportDataGrid />
                )}

                {section === "inactive-records" && hasPermission("user:manage") && (
                    <InactiveRecords />
                )}

                {section === "users" && hasPermission("user:manage") && (
                    <UserDataGrid />
                )}

                
            </main>
        </>
    );   
}

export default Dashboard;