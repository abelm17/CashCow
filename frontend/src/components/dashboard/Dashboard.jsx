// import { AppBar, Toolbar, Typography, Box, Button } from '@mui/material';
// import PrecisionManufacturingIcon from '@mui/icons-material/PrecisionManufacturing';
import AppHeader from "../layout/AppHeader";
import AtmDataGrid from "../atms/AtmDataGrid";
import { useState } from "react";
import { AppBar } from "@mui/material";
import AnalyticsDashboard from "../analytics/AnalyticsDashboard";
import BranchDataGrid from "../branches/BranchDataGrid";
import ServiceCallDataGrid from "../serviceCalls/ServiceCallDataGrid";
import DiagnosticReportDataGrid from "../diagnosticReports/DiagnosticReportDataGrid";
import UserDataGrid from "../users/UserDataGrid";

function Dashboard() {
    const [section, setSection] = useState("dashboard");
    return(
        <>
            <AppHeader onNavigate={setSection}/>
        
            <main>
                {section === "dashboard" && (
                    <h2>Welcome to CashCow, Meridian Bank's Branch Operations Command Center!</h2>
                )}

                {section === "analytics" && (
                    <AnalyticsDashboard />
                )}

                {section === "atms" && (
                    <AtmDataGrid/>
                )}  

                {section === "branches" && (
                    <BranchDataGrid />
                )}

                {section === "service-calls" && (
                    <ServiceCallDataGrid />
                )}

                {section === "diagnostic-reports" && (
                    <DiagnosticReportDataGrid />
                )}

                {section === "users" && (
                    <UserDataGrid />
                )}

                
            </main>
        </>
    );   
}

export default Dashboard;