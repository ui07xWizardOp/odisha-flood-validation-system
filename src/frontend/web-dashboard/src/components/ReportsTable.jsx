import React from 'react';
import {
    Box, Paper, Typography, Table, TableBody, TableCell, TableContainer,
    TableHead, TableRow, Chip, IconButton, Tooltip
} from '@mui/material';
import { Refresh, CheckCircle, Warning } from '@mui/icons-material';

const ReportsTable = ({ reports, onRefresh }) => {
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
                <Typography variant="h4" fontWeight="600">
                    📋 All Reports
                </Typography>
                <Tooltip title="Refresh">
                    <IconButton onClick={onRefresh} color="primary">
                        <Refresh />
                    </IconButton>
                </Tooltip>
            </Box>

            <TableContainer component={Paper} sx={{ borderRadius: 2 }}>
                <Table>
                    <TableHead sx={{ bgcolor: '#f5f5f5' }}>
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
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {reports.length === 0 ? (
                            <TableRow>
                                <TableCell colSpan={9} align="center" sx={{ py: 6 }}>
                                    <Typography color="text.secondary">
                                        No reports yet. Submit a flood report to get started!
                                    </Typography>
                                </TableCell>
                            </TableRow>
                        ) : (
                            reports.map((report) => (
                                <TableRow
                                    key={report.report_id}
                                    sx={{
                                        '&:hover': { bgcolor: '#f5f5f5' },
                                        borderLeft: `4px solid ${getScoreColor(report.final_score)}`
                                    }}
                                >
                                    <TableCell>
                                        <Typography fontWeight="bold">#{report.report_id}</Typography>
                                    </TableCell>
                                    <TableCell>User {report.user_id}</TableCell>
                                    <TableCell>
                                        <Typography variant="body2">
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
                                        />
                                    </TableCell>
                                    <TableCell align="center">
                                        {getStatusChip(report.validation_status)}
                                    </TableCell>
                                    <TableCell align="center">
                                        <Typography
                                            fontWeight="bold"
                                            sx={{ color: getScoreColor(report.final_score) }}
                                        >
                                            {(report.final_score * 100).toFixed(1)}%
                                        </Typography>
                                    </TableCell>
                                    <TableCell>
                                        <Box sx={{
                                            height: 8,
                                            width: 60,
                                            bgcolor: '#e0e0e0',
                                            borderRadius: 4
                                        }}>
                                            <Box sx={{
                                                height: '100%',
                                                width: `${(report.L1_physical || 0) * 100}%`,
                                                bgcolor: '#2196f3',
                                                borderRadius: 4
                                            }} />
                                        </Box>
                                        <Typography variant="caption">
                                            {((report.L1_physical || 0) * 100).toFixed(0)}%
                                        </Typography>
                                    </TableCell>
                                    <TableCell>
                                        <Box sx={{
                                            height: 8,
                                            width: 60,
                                            bgcolor: '#e0e0e0',
                                            borderRadius: 4
                                        }}>
                                            <Box sx={{
                                                height: '100%',
                                                width: `${(report.L2_statistical || 0) * 100}%`,
                                                bgcolor: '#9c27b0',
                                                borderRadius: 4
                                            }} />
                                        </Box>
                                        <Typography variant="caption">
                                            {((report.L2_statistical || 0) * 100).toFixed(0)}%
                                        </Typography>
                                    </TableCell>
                                    <TableCell>
                                        <Box sx={{
                                            height: 8,
                                            width: 60,
                                            bgcolor: '#e0e0e0',
                                            borderRadius: 4
                                        }}>
                                            <Box sx={{
                                                height: '100%',
                                                width: `${(report.L3_reputation || 0) * 100}%`,
                                                bgcolor: '#ff9800',
                                                borderRadius: 4
                                            }} />
                                        </Box>
                                        <Typography variant="caption">
                                            {((report.L3_reputation || 0) * 100).toFixed(0)}%
                                        </Typography>
                                    </TableCell>
                                </TableRow>
                            ))
                        )}
                    </TableBody>
                </Table>
            </TableContainer>

            <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
                Showing {reports.length} report{reports.length !== 1 ? 's' : ''}
            </Typography>
        </Box>
    );
};

export default ReportsTable;
