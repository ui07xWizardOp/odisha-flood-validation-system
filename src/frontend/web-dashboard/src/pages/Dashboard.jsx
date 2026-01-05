import React, { useState, useEffect, useRef } from 'react';
import { useGSAP } from '@gsap/react';
import gsap from 'gsap';
import {
    Box, Grid, Paper, Typography, Card, CardContent,
    LinearProgress, CircularProgress
} from '@mui/material';
import {
    CheckCircle, Warning, Assessment, People, TrendingUp
} from '@mui/icons-material';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Legend } from 'recharts';
import { getStats, getReports } from '../api';

const StatCard = ({ title, value, subtitle, icon: Icon, color, progress }) => (
    <Card sx={{
        height: '100%',
        background: `linear-gradient(135deg, ${color}15 0%, ${color}05 100%)`,
        borderLeft: `4px solid ${color}`,
        position: 'relative',
        overflow: 'visible'
    }}>
        <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <Box>
                    <Typography variant="body2" color="text.secondary" gutterBottom fontWeight="medium">
                        {title}
                    </Typography>
                    <Typography variant="h3" fontWeight="bold" sx={{ color, my: 1 }}>
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
                    borderRadius: '12px',
                    p: 1.5,
                    display: 'flex',
                    boxShadow: `0 4px 12px ${color}30`
                }}>
                    <Icon sx={{ fontSize: 32, color }} />
                </Box>
            </Box>
            {progress !== undefined && (
                <Box sx={{ mt: 3 }}>
                    <LinearProgress
                        variant="determinate"
                        value={progress}
                        sx={{
                            height: 6,
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

const Dashboard = () => {
    const [stats, setStats] = useState(null);
    const [reports, setReports] = useState([]);
    const [loading, setLoading] = useState(true);
    const containerRef = useRef();

    useGSAP(() => {
        if (!loading && stats) {
            gsap.from('.gsap-stagger', {
                y: 50,
                opacity: 0,
                duration: 0.8,
                stagger: 0.1,
                ease: "power3.out"
            });
        }
    }, { scope: containerRef, dependencies: [loading] });

    useEffect(() => {
        const loadData = async () => {
            try {
                const [statsData, reportsData] = await Promise.all([
                    getStats(),
                    getReports()
                ]);
                setStats(statsData);
                setReports(reportsData);
            } catch (error) {
                console.error("Failed to load dashboard data", error);
            } finally {
                setLoading(false);
            }
        };
        loadData();
    }, []);

    if (loading) {
        return (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 8 }}>
                <CircularProgress />
            </Box>
        );
    }

    if (!stats) return <Typography color="error">Failed to load statistics</Typography>;

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
        <Box ref={containerRef}>
            <Typography variant="h4" fontWeight="700" gutterBottom sx={{ mb: 1 }}>
                System Overview
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
                Real-time validation metrics for Mahanadi Delta
            </Typography>

            {/* Stats Cards */}
            <Grid container spacing={3} sx={{ mb: 4 }}>
                <Grid item xs={12} sm={6} md={3} className="gsap-stagger">
                    <StatCard
                        title="Total Reports"
                        value={stats.total_reports}
                        subtitle="All time submissions"
                        icon={Assessment}
                        color="#2196f3"
                    />
                </Grid>
                <Grid item xs={12} sm={6} md={3} className="gsap-stagger">
                    <StatCard
                        title="Validated"
                        value={stats.validated_reports}
                        subtitle={`${validationRate}% validation rate`}
                        icon={CheckCircle}
                        color="#4caf50"
                        progress={parseFloat(validationRate)}
                    />
                </Grid>
                <Grid item xs={12} sm={6} md={3} className="gsap-stagger">
                    <StatCard
                        title="Flagged"
                        value={stats.flagged_reports}
                        subtitle="Requires review"
                        icon={Warning}
                        color="#f44336"
                    />
                </Grid>
                <Grid item xs={12} sm={6} md={3} className="gsap-stagger">
                    <StatCard
                        title="Active Users"
                        value={stats.total_users}
                        subtitle="Registered reporters"
                        icon={People}
                        color="#9c27b0"
                    />
                </Grid>
            </Grid>

            {/* Charts */}
            <Grid container spacing={3}>
                <Grid item xs={12} md={4} className="gsap-stagger">
                    <Paper sx={{ p: 3, height: { xs: 320, md: 380 }, borderRadius: 4 }}>
                        <Typography variant="h6" fontWeight="bold" gutterBottom>
                            Validation Status
                        </Typography>

                        <ResponsiveContainer width="100%" height="90%">
                            <PieChart>
                                <Pie
                                    data={pieData}
                                    cx="50%"
                                    cy="50%"
                                    innerRadius={60}
                                    outerRadius={80}
                                    paddingAngle={5}
                                    dataKey="value"
                                >
                                    {pieData.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={entry.color} />
                                    ))}
                                </Pie>
                                <Tooltip
                                    contentStyle={{ borderRadius: 8, border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
                                />
                                <Legend verticalAlign="bottom" height={36} />
                            </PieChart>
                        </ResponsiveContainer>
                    </Paper>
                </Grid>

                <Grid item xs={12} md={8} className="gsap-stagger">
                    <Paper sx={{ p: 3, height: { xs: 320, md: 380 }, borderRadius: 4 }}>
                        <Typography variant="h6" fontWeight="bold" gutterBottom>
                            Trust Score Distribution
                        </Typography>
                        <ResponsiveContainer width="100%" height="90%">
                            <BarChart data={scoreDistribution}>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e0e0e0" />
                                <XAxis dataKey="range" axisLine={false} tickLine={false} />
                                <YAxis axisLine={false} tickLine={false} />
                                <Tooltip
                                    cursor={{ fill: 'rgba(0,0,0,0.05)' }}
                                    contentStyle={{ borderRadius: 8, border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
                                />
                                <Bar dataKey="count" fill="#3f51b5" radius={[6, 6, 0, 0]} barSize={50} />
                            </BarChart>
                        </ResponsiveContainer>
                    </Paper>
                </Grid>
            </Grid>

            {/* Additional Stats: Depth Analysis */}
            <Grid container spacing={3} sx={{ mt: 1 }}>
                <Grid item xs={12} sm={6} className="gsap-stagger">
                    <StatCard
                        title="Maximum Flood Depth"
                        value={`${Math.max(...reports.map(r => r.depth_meters || 0), 0).toFixed(1)}m`}
                        subtitle="Highest recorded status"
                        icon={Warning}
                        color="#d32f2f"
                    />
                </Grid>
                <Grid item xs={12} sm={6} className="gsap-stagger">
                    <StatCard
                        title="Average Flood Depth"
                        value={`${(reports.reduce((acc, curr) => acc + (curr.depth_meters || 0), 0) / (reports.length || 1)).toFixed(1)}m`}
                        subtitle="Across all active reports"
                        icon={Assessment}
                        color="#0288d1"
                    />
                </Grid>
                {/* Layer Performance Radar */}
                <Grid item xs={12} className="gsap-stagger">
                    <Paper sx={{ p: 3, borderRadius: 4 }}>
                        <Typography variant="h6" fontWeight="bold" gutterBottom>
                            Validation Logic Performance
                        </Typography>
                        <Box sx={{ height: 300, width: '100%' }}>
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart
                                    layout="vertical"
                                    data={[
                                        { name: 'Physical (L1)', score: (reports.reduce((acc, r) => acc + (r.physical_score || 0), 0) / (reports.length || 1)) * 100 },
                                        { name: 'Statistical (L2)', score: (reports.reduce((acc, r) => acc + (r.statistical_score || 0), 0) / (reports.length || 1)) * 100 },
                                        { name: 'Reputation (L3)', score: (reports.reduce((acc, r) => acc + (r.reputation_score || 0), 0) / (reports.length || 1)) * 100 },
                                        { name: 'Social (L4)', score: (reports.reduce((acc, r) => acc + (r.social_score || 0), 0) / (reports.length || 1)) * 100 },
                                        { name: 'Visual (L5)', score: (reports.reduce((acc, r) => acc + (r.cv_score || 0), 0) / (reports.length || 1)) * 100 },
                                    ]}
                                    margin={{ top: 20, right: 30, left: 40, bottom: 5 }}
                                >
                                    <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                                    <XAxis type="number" domain={[0, 100]} />
                                    <YAxis dataKey="name" type="category" width={100} />
                                    <Tooltip
                                        cursor={{ fill: 'rgba(0,0,0,0.05)' }}
                                        contentStyle={{ borderRadius: 8, border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
                                    />
                                    <Bar dataKey="score" fill="#673ab7" radius={[0, 4, 4, 0]} barSize={20} label={{ position: 'right', fill: '#666', fontSize: 12, formatter: (val) => `${val.toFixed(0)}%` }} />
                                </BarChart>
                            </ResponsiveContainer>
                        </Box>
                        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', textAlign: 'center', mt: 2 }}>
                            Average confidence score contribution by each validation layer
                        </Typography>
                    </Paper>
                </Grid>
            </Grid>

            {/* Overall System Score Section */}
            <Paper sx={{ p: 3, mt: 3, borderRadius: 4, background: 'linear-gradient(135deg, #fff3e0 0%, #ffffff 100%)' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 3 }}>
                    <Box sx={{ p: 2, bgcolor: '#ff9800', borderRadius: '50%', color: 'white' }}>
                        <TrendingUp sx={{ fontSize: 32 }} />
                    </Box>
                    <Box>
                        <Typography variant="body2" color="text.secondary">
                            System Average Score
                        </Typography>
                        <Typography variant="h4" fontWeight="bold" color="#e65100">
                            {(stats.average_score * 100).toFixed(1)}%
                        </Typography>
                    </Box>
                    <Box sx={{ flexGrow: 1, ml: 4 }}>
                        <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
                            Overall confidence in crowd reports
                        </Typography>
                        <LinearProgress
                            variant="determinate"
                            value={stats.average_score * 100}
                            sx={{
                                height: 12,
                                borderRadius: 10,
                                bgcolor: 'rgba(255, 152, 0, 0.2)',
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

export default Dashboard;
