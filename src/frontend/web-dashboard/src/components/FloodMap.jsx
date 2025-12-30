import React, { useEffect, useRef } from 'react';
import { Box, Paper, Typography, Chip, Stack } from '@mui/material';
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

// Legend component
const Legend = () => (
    <Paper sx={{
        position: 'absolute',
        bottom: 20,
        right: 20,
        zIndex: 1000,
        p: 2,
        bgcolor: 'rgba(255,255,255,0.95)'
    }}>
        <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
            Report Status
        </Typography>
        <Stack spacing={1}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Box sx={{ width: 16, height: 16, borderRadius: '50%', bgcolor: '#4caf50' }} />
                <Typography variant="body2">Validated</Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Box sx={{ width: 16, height: 16, borderRadius: '50%', bgcolor: '#f44336' }} />
                <Typography variant="body2">Flagged</Typography>
            </Box>
        </Stack>
    </Paper>
);

// Fit map to bounds when reports change
const FitBounds = ({ reports }) => {
    const map = useMap();

    useEffect(() => {
        if (reports.length > 0) {
            const bounds = reports.map(r => [r.latitude, r.longitude]);
            map.fitBounds(bounds, { padding: [50, 50] });
        }
    }, [reports, map]);

    return null;
};

const FloodMap = ({ reports }) => {
    // Mahanadi Delta center
    const center = [20.46, 85.88];

    const getMarkerColor = (status) => {
        return status === 'validated' ? '#4caf50' : '#f44336';
    };

    const getMarkerRadius = (depth) => {
        return Math.max(8, Math.min(20, depth * 5 + 8));
    };

    return (
        <Box>
            <Typography variant="h4" fontWeight="600" gutterBottom sx={{ mb: 3 }}>
                🗺️ Live Flood Map
            </Typography>

            {/* Stats bar */}
            <Stack direction="row" spacing={2} sx={{ mb: 2 }}>
                <Chip
                    label={`${reports.length} Total Reports`}
                    color="primary"
                    variant="outlined"
                />
                <Chip
                    label={`${reports.filter(r => r.validation_status === 'validated').length} Validated`}
                    sx={{ bgcolor: '#e8f5e9', color: '#2e7d32' }}
                />
                <Chip
                    label={`${reports.filter(r => r.validation_status === 'flagged').length} Flagged`}
                    sx={{ bgcolor: '#ffebee', color: '#c62828' }}
                />
            </Stack>

            {/* Map */}
            <Paper sx={{ height: 550, position: 'relative', overflow: 'hidden', borderRadius: 2 }}>
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
                                fillOpacity: 0.7,
                                color: '#fff',
                                weight: 2
                            }}
                        >
                            <Popup>
                                <Box sx={{ minWidth: 200 }}>
                                    <Typography variant="subtitle2" fontWeight="bold">
                                        Report #{report.report_id}
                                    </Typography>
                                    <Typography variant="body2">
                                        <strong>Status:</strong>{' '}
                                        <Chip
                                            label={report.validation_status}
                                            size="small"
                                            color={report.validation_status === 'validated' ? 'success' : 'error'}
                                        />
                                    </Typography>
                                    <Typography variant="body2">
                                        <strong>Score:</strong> {(report.final_score * 100).toFixed(1)}%
                                    </Typography>
                                    <Typography variant="body2">
                                        <strong>Depth:</strong> {report.depth_meters?.toFixed(1) || 'N/A'}m
                                    </Typography>
                                    <Typography variant="body2">
                                        <strong>Location:</strong> {report.latitude.toFixed(4)}°N, {report.longitude.toFixed(4)}°E
                                    </Typography>
                                    <Box sx={{ mt: 1, pt: 1, borderTop: '1px solid #eee' }}>
                                        <Typography variant="caption" color="text.secondary">
                                            L1: {(report.L1_physical * 100).toFixed(0)}% |
                                            L2: {(report.L2_statistical * 100).toFixed(0)}% |
                                            L3: {(report.L3_reputation * 100).toFixed(0)}%
                                        </Typography>
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

export default FloodMap;
