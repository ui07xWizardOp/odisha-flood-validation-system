import React, { useState, useEffect } from 'react';
import {
    Box, Container, AppBar, Toolbar, Typography, Tabs, Tab,
    Snackbar, Alert, CircularProgress
} from '@mui/material';
import WaterDropIcon from '@mui/icons-material/WaterDrop';
import StatsDashboard from './components/StatsDashboard';
import FloodMap from './components/FloodMap';
import ReportForm from './components/ReportForm';
import ReportsTable from './components/ReportsTable';
import { getStats, getReports, submitReport, createUser } from './api';

function App() {
    const [tabValue, setTabValue] = useState(0);
    const [stats, setStats] = useState(null);
    const [reports, setReports] = useState([]);
    const [loading, setLoading] = useState(true);
    const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });

    // Fetch data on load
    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        setLoading(true);
        try {
            const [statsData, reportsData] = await Promise.all([
                getStats(),
                getReports()
            ]);
            setStats(statsData);
            setReports(reportsData);
        } catch (error) {
            showSnackbar('Failed to load data. Is the API running?', 'error');
        }
        setLoading(false);
    };

    const handleSubmitReport = async (reportData) => {
        try {
            // First ensure user exists (create if needed)
            try {
                await createUser({
                    username: `user_${reportData.user_id}`,
                    email: `user${reportData.user_id}@floodreport.local`
                });
            } catch (e) {
                // User might already exist (400 error), which is fine
                console.log('User creation skipped (may already exist):', e.message);
            }

            const result = await submitReport(reportData);
            // API returns flat structure: validation_status, final_score (not nested)
            const status = result.validation_status || 'submitted';
            const score = result.final_score || 0;
            showSnackbar(
                `Report ${status}! Score: ${(score * 100).toFixed(1)}%`,
                status === 'validated' ? 'success' : 'warning'
            );
            loadData(); // Refresh
            // Return in format expected by ReportForm
            return {
                report_id: result.report_id,
                validation: {
                    status: status,
                    final_score: score,
                    layer_scores: {
                        L1_physical: result.physical_score || 0,
                        L2_statistical: result.statistical_score || 0,
                        L3_reputation: result.reputation_score || 0
                    }
                }
            };
        } catch (error) {
            showSnackbar('Failed to submit report', 'error');
            throw error;
        }
    };

    const showSnackbar = (message, severity) => {
        setSnackbar({ open: true, message, severity });
    };

    const handleCloseSnackbar = () => {
        setSnackbar({ ...snackbar, open: false });
    };

    if (loading) {
        return (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
                <CircularProgress size={60} />
            </Box>
        );
    }

    return (
        <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', bgcolor: '#f5f7fa' }}>
            {/* Header */}
            <AppBar position="static" sx={{
                background: 'linear-gradient(135deg, #1e3c72 0%, #2a5298 100%)',
                boxShadow: '0 4px 20px rgba(0,0,0,0.15)'
            }}>
                <Toolbar>
                    <WaterDropIcon sx={{ mr: 2, fontSize: 32 }} />
                    <Typography variant="h5" component="div" sx={{ flexGrow: 1, fontWeight: 600 }}>
                        Odisha Flood Validation System
                    </Typography>
                    <Typography variant="body2" sx={{
                        bgcolor: 'rgba(255,255,255,0.15)',
                        px: 2, py: 0.5,
                        borderRadius: 2
                    }}>
                        Mahanadi Delta • Live Dashboard
                    </Typography>
                </Toolbar>
                <Tabs
                    value={tabValue}
                    onChange={(e, v) => setTabValue(v)}
                    textColor="inherit"
                    indicatorColor="secondary"
                    sx={{ px: 2, bgcolor: 'rgba(0,0,0,0.1)' }}
                >
                    <Tab label="📊 Dashboard" />
                    <Tab label="🗺️ Flood Map" />
                    <Tab label="📝 Submit Report" />
                    <Tab label="📋 All Reports" />
                </Tabs>
            </AppBar>

            {/* Main Content */}
            <Container maxWidth="xl" sx={{ flexGrow: 1, py: 4 }}>
                {tabValue === 0 && <StatsDashboard stats={stats} reports={reports} />}
                {tabValue === 1 && <FloodMap reports={reports} />}
                {tabValue === 2 && <ReportForm onSubmit={handleSubmitReport} />}
                {tabValue === 3 && <ReportsTable reports={reports} onRefresh={loadData} />}
            </Container>

            {/* Footer */}
            <Box component="footer" sx={{
                py: 2, px: 2,
                bgcolor: '#1e3c72',
                color: 'white',
                textAlign: 'center'
            }}>
                <Typography variant="body2">
                    🌊 AI/ML-Enhanced Crowdsourced Flood Validation System © 2026 | Odisha Disaster Management
                </Typography>
            </Box>

            {/* Snackbar for notifications */}
            <Snackbar
                open={snackbar.open}
                autoHideDuration={5000}
                onClose={handleCloseSnackbar}
                anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
            >
                <Alert onClose={handleCloseSnackbar} severity={snackbar.severity} sx={{ width: '100%' }}>
                    {snackbar.message}
                </Alert>
            </Snackbar>
        </Box>
    );
}

export default App;
