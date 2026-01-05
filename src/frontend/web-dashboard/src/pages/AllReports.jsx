import React, { useState, useEffect } from 'react';
import {
    Box, Paper, Typography, Table, TableBody, TableCell, TableContainer,
    TableHead, TableRow, Chip, IconButton, Tooltip, CircularProgress
} from '@mui/material';
import { Refresh, CheckCircle, Warning, FilterList } from '@mui/icons-material';
import { getReports } from '../api';

const AllReports = () => {
    const [reports, setReports] = useState([]);
    const [loading, setLoading] = useState(true);

    const fetchData = async () => {
        setLoading(true);
        try {
            const data = await getReports();
            setReports(Array.isArray(data) ? data : []);
        } catch (error) {
            console.error("Failed to load reports", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    const getStatusChip = (status) => {
        if (status === 'validated') {
            return <Chip label="Validated" size="small" color="success" icon={<CheckCircle />} />;
        }
        return <Chip label="Flagged" size="small" color="error" icon={<Warning />} />;
    };

    const getScoreColor = (score) => {
        if (score >= 0.8) return '#4caf50';
        if (score >= 0.7) return '#8bc34a';
        if (score >= 0.5) return '#ff9800';
        return '#f44336';
    };

    return (
        <Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <Box>
                    <Typography variant="h4" fontWeight="bold">
                        📋 All Reports
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                        Comprehensive list of all submitted flood reports
                    </Typography>
                </Box>
                <Box>
                    <Tooltip title="Filter">
                        <IconButton>
                            <FilterList />
                        </IconButton>
                    </Tooltip>
                    <Tooltip title="Refresh">
                        <IconButton onClick={fetchData} color="primary">
                            <Refresh />
                        </IconButton>
                    </Tooltip>
                </Box>
            </Box>

            <Paper sx={{ borderRadius: 4, overflow: 'hidden', border: '1px solid rgba(0,0,0,0.08)' }}>
                <TableContainer>
                    <Table sx={{ minWidth: 800 }}>
                        <TableHead sx={{ bgcolor: 'action.hover' }}>
                            <TableRow>
                                <TableCell><strong>ID</strong></TableCell>
                                <TableCell><strong>User</strong></TableCell>
                                <TableCell><strong>Location</strong></TableCell>
                                <TableCell><strong>Depth</strong></TableCell>
                                <TableCell align="center"><strong>Status</strong></TableCell>
                                <TableCell align="center"><strong>Score</strong></TableCell>
                                <TableCell><strong>L1 Physical</strong></TableCell>
                                <TableCell><strong>L2 Statistical</strong></TableCell>
                                <TableCell><strong>L3 Reputation</strong></TableCell>
                                <TableCell><strong>L4 Social</strong></TableCell>
                                <TableCell><strong>L5 Visual</strong></TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {loading ? (
                                <TableRow>
                                    <TableCell colSpan={11} align="center" sx={{ py: 8 }}>
                                        <CircularProgress />
                                    </TableCell>
                                </TableRow>
                            ) : reports.length === 0 ? (
                                <TableRow>
                                    <TableCell colSpan={11} align="center" sx={{ py: 8 }}>
                                        <Typography color="text.secondary">
                                            No reports yet. Submit a flood report to get started!
                                        </Typography>
                                    </TableCell>
                                </TableRow>
                            ) : (
                                reports.map((report) => (
                                    <TableRow
                                        key={report.report_id}
                                        hover
                                        sx={{
                                            borderLeft: `4px solid ${getScoreColor(report.final_score)}`,
                                            transition: 'background-color 0.2s',
                                        }}
                                    >
                                        <TableCell>
                                            <Typography fontWeight="bold" color="primary">#{report.report_id}</Typography>
                                        </TableCell>
                                        <TableCell>
                                            <Typography variant="body2">User {report.user_id}</Typography>
                                            <Typography variant="caption" color="text.secondary">ID: {report.user_id}</Typography>
                                        </TableCell>
                                        <TableCell>
                                            <Typography variant="body2" fontWeight="medium">
                                                {report.latitude.toFixed(3)}°N
                                            </Typography>
                                            <Typography variant="caption" color="text.secondary">
                                                {report.longitude.toFixed(3)}°E
                                            </Typography>
                                        </TableCell>
                                        <TableCell>
                                            <Chip
                                                label={`${report.depth_meters?.toFixed(1) || 0}m`}
                                                size="small"
                                                variant="outlined"
                                                sx={{ borderColor: 'divider' }}
                                            />
                                        </TableCell>
                                        <TableCell align="center">
                                            {getStatusChip(report.validation_status)}
                                        </TableCell>
                                        <TableCell align="center">
                                            <Box sx={{ position: 'relative', display: 'inline-flex' }}>
                                                <CircularProgress
                                                    variant="determinate"
                                                    value={report.final_score * 100}
                                                    size={40}
                                                    thickness={4}
                                                    sx={{ color: getScoreColor(report.final_score) }}
                                                />
                                                <Box sx={{
                                                    top: 0,
                                                    left: 0,
                                                    bottom: 0,
                                                    right: 0,
                                                    position: 'absolute',
                                                    display: 'flex',
                                                    alignItems: 'center',
                                                    justifyContent: 'center',
                                                }}>
                                                    <Typography variant="caption" component="div" color="text.secondary" fontWeight="bold">
                                                        {(report.final_score * 100).toFixed(0)}
                                                    </Typography>
                                                </Box>
                                            </Box>
                                        </TableCell>
                                        <TableCell>
                                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                                <Box sx={{ width: '100%', mr: 1 }}>
                                                    <Box sx={{ height: 6, width: '100%', bgcolor: 'action.hover', borderRadius: 4, overflow: 'hidden' }}>
                                                        <Box sx={{ height: '100%', width: `${(report.physical_score || 0) * 100}%`, bgcolor: '#2196f3' }} />
                                                    </Box>
                                                </Box>
                                                <Typography variant="caption" color="text.secondary" sx={{ minWidth: 25 }}>
                                                    {((report.physical_score || 0) * 100).toFixed(0)}%
                                                </Typography>
                                            </Box>
                                        </TableCell>
                                        <TableCell>
                                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                                <Box sx={{ width: '100%', mr: 1 }}>
                                                    <Box sx={{ height: 6, width: '100%', bgcolor: 'action.hover', borderRadius: 4, overflow: 'hidden' }}>
                                                        <Box sx={{ height: '100%', width: `${(report.statistical_score || 0) * 100}%`, bgcolor: '#9c27b0' }} />
                                                    </Box>
                                                </Box>
                                                <Typography variant="caption" color="text.secondary" sx={{ minWidth: 25 }}>
                                                    {((report.statistical_score || 0) * 100).toFixed(0)}%
                                                </Typography>
                                            </Box>
                                        </TableCell>
                                        <TableCell>
                                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                                <Box sx={{ width: '100%', mr: 1 }}>
                                                    <Box sx={{ height: 6, width: '100%', bgcolor: 'action.hover', borderRadius: 4, overflow: 'hidden' }}>
                                                        <Box sx={{ height: '100%', width: `${(report.reputation_score || 0) * 100}%`, bgcolor: '#ff9800' }} />
                                                    </Box>
                                                </Box>
                                                <Typography variant="caption" color="text.secondary" sx={{ minWidth: 25 }}>
                                                    {((report.reputation_score || 0) * 100).toFixed(0)}%
                                                </Typography>
                                            </Box>
                                        </TableCell>
                                        <TableCell>
                                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                                <Box sx={{ width: '100%', mr: 1 }}>
                                                    <Box sx={{ height: 6, width: '100%', bgcolor: 'action.hover', borderRadius: 4, overflow: 'hidden' }}>
                                                        <Box sx={{ height: '100%', width: `${(report.social_score || 0) * 100}%`, bgcolor: '#00bcd4' }} />
                                                    </Box>
                                                </Box>
                                                <Typography variant="caption" color="text.secondary" sx={{ minWidth: 25 }}>
                                                    {((report.social_score || 0) * 100).toFixed(0)}%
                                                </Typography>
                                            </Box>
                                        </TableCell>
                                        <TableCell>
                                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                                <Box sx={{ width: '100%', mr: 1 }}>
                                                    <Box sx={{ height: 6, width: '100%', bgcolor: 'action.hover', borderRadius: 4, overflow: 'hidden' }}>
                                                        <Box sx={{ height: '100%', width: `${(report.cv_score || 0) * 100}%`, bgcolor: '#e91e63' }} />
                                                    </Box>
                                                </Box>
                                                <Typography variant="caption" color="text.secondary" sx={{ minWidth: 25 }}>
                                                    {((report.cv_score || 0) * 100).toFixed(0)}%
                                                </Typography>
                                            </Box>
                                        </TableCell>
                                    </TableRow>
                                ))
                            )}
                        </TableBody>
                    </Table>
                </TableContainer>
            </Paper>

            <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block', textAlign: 'center' }}>
                Showing {reports.length} report{reports.length !== 1 ? 's' : ''}
            </Typography>
        </Box>
    );
};

export default AllReports;
