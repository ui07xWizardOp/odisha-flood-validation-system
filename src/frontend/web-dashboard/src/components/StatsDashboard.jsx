import React from 'react';
import {
    Box, Grid, Paper, Typography, Card, CardContent,
    LinearProgress
} from '@mui/material';
import {
    CheckCircle, Warning, Assessment, People, TrendingUp
} from '@mui/icons-material';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip } from 'recharts';

const StatCard = ({ title, value, subtitle, icon: Icon, color, progress }) => (
    <Card sx={{
        height: '100%',
        background: `linear-gradient(135deg, ${color}15 0%, ${color}05 100%)`,
        borderLeft: `4px solid ${color}`,
        transition: 'transform 0.2s, box-shadow 0.2s',
        '&:hover': {
            transform: 'translateY(-4px)',
            boxShadow: '0 8px 25px rgba(0,0,0,0.1)'
        }
    }}>
        <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <Box>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                        {title}
                    </Typography>
                    <Typography variant="h3" fontWeight="bold" sx={{ color }}>
                        {value}
                    </Typography>
                    {subtitle && (
                        <Typography variant="caption" color="text.secondary">
                            {subtitle}
                        </Typography>
                    )}
                </Box>
                <Box sx={{
                    bgcolor: `${color}20`,
                    borderRadius: '50%',
                    p: 1.5,
                    display: 'flex'
                }}>
                    <Icon sx={{ fontSize: 32, color }} />
                </Box>
            </Box>
            {progress !== undefined && (
                <Box sx={{ mt: 2 }}>
                    <LinearProgress
                        variant="determinate"
                        value={progress}
                        sx={{
                            height: 8,
                            borderRadius: 4,
                            bgcolor: `${color}20`,
                            '& .MuiLinearProgress-bar': { bgcolor: color }
                        }}
                    />
                </Box>
            )}
        </CardContent>
    </Card>
);

const StatsDashboard = ({ stats, reports }) => {
    if (!stats) {
        return <Typography>Loading statistics...</Typography>;
    }

    const validationRate = stats.total_reports > 0
        ? ((stats.validated_reports / stats.total_reports) * 100).toFixed(1)
        : 0;

    // Pie chart data
    const pieData = [
        { name: 'Validated', value: stats.validated_reports, color: '#4caf50' },
        { name: 'Flagged', value: stats.flagged_reports, color: '#f44336' }
    ];

    // Recent reports by score range
    const scoreDistribution = [
        { range: '90-100%', count: reports.filter(r => r.final_score >= 0.9).length },
        { range: '70-90%', count: reports.filter(r => r.final_score >= 0.7 && r.final_score < 0.9).length },
        { range: '50-70%', count: reports.filter(r => r.final_score >= 0.5 && r.final_score < 0.7).length },
        { range: '<50%', count: reports.filter(r => r.final_score < 0.5).length }
    ];

    return (
        <Box>
            <Typography variant="h4" fontWeight="600" gutterBottom sx={{ mb: 3 }}>
                📊 System Dashboard
            </Typography>

            {/* Stats Cards */}
            <Grid container spacing={3} sx={{ mb: 4 }}>
                <Grid item xs={12} sm={6} md={3}>
                    <StatCard
                        title="Total Reports"
                        value={stats.total_reports}
                        subtitle="All submitted reports"
                        icon={Assessment}
                        color="#2196f3"
                    />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <StatCard
                        title="Validated"
                        value={stats.validated_reports}
                        subtitle={`${validationRate}% validation rate`}
                        icon={CheckCircle}
                        color="#4caf50"
                        progress={parseFloat(validationRate)}
                    />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <StatCard
                        title="Flagged"
                        value={stats.flagged_reports}
                        subtitle="Requires review"
                        icon={Warning}
                        color="#f44336"
                    />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <StatCard
                        title="Users"
                        value={stats.total_users}
                        subtitle="Registered reporters"
                        icon={People}
                        color="#9c27b0"
                    />
                </Grid>
            </Grid>

            {/* Charts */}
            <Grid container spacing={3}>
                <Grid item xs={12} md={4}>
                    <Paper sx={{ p: 3, height: 300 }}>
                        <Typography variant="h6" gutterBottom>
                            Validation Distribution
                        </Typography>
                        <ResponsiveContainer width="100%" height="85%">
                            <PieChart>
                                <Pie
                                    data={pieData}
                                    cx="50%"
                                    cy="50%"
                                    innerRadius={60}
                                    outerRadius={90}
                                    paddingAngle={5}
                                    dataKey="value"
                                    label={({ name, value }) => `${name}: ${value}`}
                                >
                                    {pieData.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={entry.color} />
                                    ))}
                                </Pie>
                                <Tooltip />
                            </PieChart>
                        </ResponsiveContainer>
                    </Paper>
                </Grid>

                <Grid item xs={12} md={8}>
                    <Paper sx={{ p: 3, height: 300 }}>
                        <Typography variant="h6" gutterBottom>
                            Score Distribution
                        </Typography>
                        <ResponsiveContainer width="100%" height="85%">
                            <BarChart data={scoreDistribution}>
                                <XAxis dataKey="range" />
                                <YAxis />
                                <Tooltip />
                                <Bar dataKey="count" fill="#2196f3" radius={[8, 8, 0, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    </Paper>
                </Grid>
            </Grid>

            {/* Average Score */}
            <Paper sx={{ p: 3, mt: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <TrendingUp sx={{ fontSize: 40, color: '#ff9800' }} />
                    <Box>
                        <Typography variant="body2" color="text.secondary">
                            Average Validation Score
                        </Typography>
                        <Typography variant="h4" fontWeight="bold" color="#ff9800">
                            {(stats.average_score * 100).toFixed(1)}%
                        </Typography>
                    </Box>
                    <Box sx={{ flexGrow: 1, ml: 4 }}>
                        <LinearProgress
                            variant="determinate"
                            value={stats.average_score * 100}
                            sx={{
                                height: 20,
                                borderRadius: 10,
                                bgcolor: '#fff3e0',
                                '& .MuiLinearProgress-bar': {
                                    bgcolor: '#ff9800',
                                    borderRadius: 10
                                }
                            }}
                        />
                    </Box>
                </Box>
            </Paper>
        </Box>
    );
};

export default StatsDashboard;
