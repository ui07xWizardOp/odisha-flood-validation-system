import React, { useEffect, useState } from 'react';
import { Box, Paper, Typography, Chip, Stack, CircularProgress } from '@mui/material';
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { getReports } from '../api';

// Legend component
const Legend = () => (
    <Paper sx={{
        position: 'absolute',
        bottom: 20,
        right: 20,
        zIndex: 1000,
        p: 2,
        bgcolor: 'rgba(255,255,255,0.95)',
        backdropFilter: 'blur(10px)',
        borderRadius: 2
    }}>
        <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
            Status
        </Typography>
        <Stack spacing={1}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: '#4caf50', boxShadow: '0 0 8px #4caf50' }} />
                <Typography variant="body2" fontWeight="medium">Validated</Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: '#f44336', boxShadow: '0 0 8px #f44336' }} />
                <Typography variant="body2" fontWeight="medium">Flagged</Typography>
            </Box>
        </Stack>
    </Paper>
);

// Fit map to bounds when reports change
const FitBounds = ({ reports }) => {
    const map = useMap();

    useEffect(() => {
        if (reports && reports.length > 0) {
            try {
                const bounds = reports.map(r => [r.latitude, r.longitude]);
                map.fitBounds(bounds, { padding: [50, 50] });
            } catch (e) {
                console.warn("Invalid bounds", e);
            }
        }
    }, [reports, map]);

    return null;
};

const MapPage = () => {
    const [reports, setReports] = useState([]);
    const [loading, setLoading] = useState(true);

    // Mahanadi Delta center
    const center = [20.46, 85.88];

    useEffect(() => {
        const fetchReports = async () => {
            try {
                const data = await getReports();
                setReports(Array.isArray(data) ? data : []);
            } catch (error) {
                console.error("Failed to fetch reports for map", error);
            } finally {
                setLoading(false);
            }
        };
        fetchReports();
    }, []);

    const getMarkerColor = (status) => {
        return status === 'validated' ? '#4caf50' : '#f44336';
    };

    const getMarkerRadius = (depth) => {
        return Math.max(8, Math.min(20, depth * 5 + 8));
    };

    if (loading) return <Box p={4} display="flex" justifyContent="center"><CircularProgress /></Box>;

    return (
        <Box sx={{ height: 'calc(100vh - 100px)', display: 'flex', flexDirection: 'column' }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h4" fontWeight="700">
                    Live Flood Map
                </Typography>
                <Stack direction="row" spacing={1}>
                    <Chip
                        label={`${reports.length} Total`}
                        color="primary"
                        variant="outlined"
                        size="small"
                    />
                    <Chip
                        label={`${reports.filter(r => r.validation_status === 'validated').length} Verified`}
                        sx={{ bgcolor: '#e8f5e9', color: '#2e7d32', fontWeight: 'bold' }}
                        size="small"
                    />
                </Stack>
            </Box>

            {/* Map */}
            <Paper sx={{
                flexGrow: 1,
                position: 'relative',
                overflow: 'hidden',
                borderRadius: 4,
                border: '1px solid rgba(0,0,0,0.1)'
            }}>
                <MapContainer
                    center={center}
                    zoom={9}
                    style={{ height: '100%', width: '100%' }}
                >
                    <TileLayer
                        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    />

                    {reports.length > 0 && <FitBounds reports={reports} />}

                    {reports.map((report) => (
                        <CircleMarker
                            key={report.report_id}
                            center={[report.latitude, report.longitude]}
                            radius={getMarkerRadius(report.depth_meters || 1)}
                            pathOptions={{
                                fillColor: getMarkerColor(report.validation_status),
                                fillOpacity: 0.8,
                                color: '#fff',
                                weight: 2
                            }}
                        >
                            <Popup>
                                <Box sx={{ minWidth: 200 }}>
                                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                                        <Typography variant="subtitle2" fontWeight="bold">
                                            Report #{report.report_id}
                                        </Typography>
                                        <Chip
                                            label={report.validation_status}
                                            size="small"
                                            sx={{
                                                height: 20,
                                                fontSize: '0.65rem',
                                                bgcolor: report.validation_status === 'validated' ? '#4caf50' : '#f44336',
                                                color: 'white'
                                            }}
                                        />
                                    </Box>

                                    <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1, mb: 1 }}>
                                        <Box>
                                            <Typography variant="caption" color="text.secondary">Score</Typography>
                                            <Typography variant="body2" fontWeight="bold">{(report.final_score * 100).toFixed(0)}%</Typography>
                                        </Box>
                                        <Box>
                                            <Typography variant="caption" color="text.secondary">Depth</Typography>
                                            <Typography variant="body2" fontWeight="bold">{report.depth_meters?.toFixed(1) || 'N/A'}m</Typography>
                                        </Box>
                                    </Box>

                                    <Typography variant="caption" display="block" color="text.secondary" gutterBottom>
                                        📍 {report.latitude.toFixed(4)}, {report.longitude.toFixed(4)}
                                    </Typography>

                                    <Box sx={{ mt: 1, pt: 1, borderTop: '1px solid #eee' }}>
                                        <Typography variant="caption" sx={{ display: 'block', mb: 0.5 }}>Validation Scores:</Typography>
                                        <Stack direction="row" spacing={0.5} flexWrap="wrap">
                                            <Chip label={`L1: ${(report.L1_physical * 100).toFixed(0)}`} size="small" variant="outlined" sx={{ height: 20, fontSize: '0.6rem' }} />
                                            <Chip label={`L2: ${(report.L2_statistical * 100).toFixed(0)}`} size="small" variant="outlined" sx={{ height: 20, fontSize: '0.6rem' }} />
                                            <Chip label={`L3: ${(report.L3_reputation * 100).toFixed(0)}`} size="small" variant="outlined" sx={{ height: 20, fontSize: '0.6rem' }} />
                                        </Stack>
                                    </Box>
                                </Box>
                            </Popup>
                        </CircleMarker>
                    ))}
                </MapContainer>

                <Legend />
            </Paper>
        </Box>
    );
};

export default MapPage;
