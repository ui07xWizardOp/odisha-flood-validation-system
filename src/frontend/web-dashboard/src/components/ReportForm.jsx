import React, { useState } from 'react';
import {
    Box, Paper, Typography, TextField, Button, Grid, Slider,
    Alert, CircularProgress, Card, CardContent
} from '@mui/material';
import { Send, LocationOn, Water, Person } from '@mui/icons-material';

const ReportForm = ({ onSubmit }) => {
    const [formData, setFormData] = useState({
        user_id: 1,
        latitude: 20.46,
        longitude: 85.88,
        depth_meters: 1.0,
        description: ''
    });
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);

    const handleChange = (field) => (e) => {
        setFormData({ ...formData, [field]: e.target.value });
    };

    const handleSliderChange = (field) => (e, value) => {
        setFormData({ ...formData, [field]: value });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        setResult(null);

        try {
            const response = await onSubmit({
                ...formData,
                user_id: parseInt(formData.user_id),
                latitude: parseFloat(formData.latitude),
                longitude: parseFloat(formData.longitude),
                depth_meters: parseFloat(formData.depth_meters),
                timestamp: new Date().toISOString()  // Add required timestamp
            });
            setResult(response);
        } catch (err) {
            setError('Failed to submit report. Please try again.');
        }
        setLoading(false);
    };

    return (
        <Box>
            <Typography variant="h4" fontWeight="600" gutterBottom sx={{ mb: 3 }}>
                📝 Submit Flood Report
            </Typography>

            <Grid container spacing={4}>
                {/* Form */}
                <Grid item xs={12} md={7}>
                    <Paper sx={{ p: 4 }}>
                        <form onSubmit={handleSubmit}>
                            <Grid container spacing={3}>
                                {/* User ID */}
                                <Grid item xs={12}>
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                                        <Person color="primary" />
                                        <Typography variant="subtitle1" fontWeight="500">
                                            Reporter ID
                                        </Typography>
                                    </Box>
                                    <TextField
                                        fullWidth
                                        type="number"
                                        value={formData.user_id}
                                        onChange={handleChange('user_id')}
                                        inputProps={{ min: 1 }}
                                        helperText="Your unique user ID"
                                    />
                                </Grid>

                                {/* Location */}
                                <Grid item xs={12}>
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                                        <LocationOn color="error" />
                                        <Typography variant="subtitle1" fontWeight="500">
                                            Location (Mahanadi Delta)
                                        </Typography>
                                    </Box>
                                </Grid>
                                <Grid item xs={6}>
                                    <Typography variant="caption" color="text.secondary">
                                        Latitude: {formData.latitude}°N
                                    </Typography>
                                    <Slider
                                        value={formData.latitude}
                                        onChange={handleSliderChange('latitude')}
                                        min={19.5}
                                        max={21.5}
                                        step={0.01}
                                        valueLabelDisplay="auto"
                                    />
                                </Grid>
                                <Grid item xs={6}>
                                    <Typography variant="caption" color="text.secondary">
                                        Longitude: {formData.longitude}°E
                                    </Typography>
                                    <Slider
                                        value={formData.longitude}
                                        onChange={handleSliderChange('longitude')}
                                        min={84.5}
                                        max={87.0}
                                        step={0.01}
                                        valueLabelDisplay="auto"
                                    />
                                </Grid>

                                {/* Depth */}
                                <Grid item xs={12}>
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                                        <Water color="primary" />
                                        <Typography variant="subtitle1" fontWeight="500">
                                            Water Depth: {formData.depth_meters.toFixed(1)} meters
                                        </Typography>
                                    </Box>
                                    <Slider
                                        value={formData.depth_meters}
                                        onChange={handleSliderChange('depth_meters')}
                                        min={0}
                                        max={5}
                                        step={0.1}
                                        valueLabelDisplay="auto"
                                        marks={[
                                            { value: 0, label: '0m' },
                                            { value: 1, label: '1m' },
                                            { value: 2, label: '2m' },
                                            { value: 3, label: '3m' },
                                            { value: 5, label: '5m' }
                                        ]}
                                    />
                                </Grid>

                                {/* Description */}
                                <Grid item xs={12}>
                                    <TextField
                                        fullWidth
                                        multiline
                                        rows={3}
                                        label="Description (optional)"
                                        value={formData.description}
                                        onChange={handleChange('description')}
                                        placeholder="Describe the flooding situation..."
                                    />
                                </Grid>

                                {/* Submit */}
                                <Grid item xs={12}>
                                    <Button
                                        type="submit"
                                        variant="contained"
                                        size="large"
                                        fullWidth
                                        disabled={loading}
                                        startIcon={loading ? <CircularProgress size={20} /> : <Send />}
                                        sx={{
                                            py: 1.5,
                                            background: 'linear-gradient(135deg, #1e3c72 0%, #2a5298 100%)'
                                        }}
                                    >
                                        {loading ? 'Submitting...' : 'Submit Report'}
                                    </Button>
                                </Grid>
                            </Grid>
                        </form>

                        {error && (
                            <Alert severity="error" sx={{ mt: 3 }}>
                                {error}
                            </Alert>
                        )}
                    </Paper>
                </Grid>

                {/* Result Panel */}
                <Grid item xs={12} md={5}>
                    <Paper sx={{ p: 3, bgcolor: '#f8f9fa', height: '100%' }}>
                        <Typography variant="h6" gutterBottom>
                            🔍 Validation Result
                        </Typography>

                        {!result ? (
                            <Box sx={{
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                height: 300,
                                color: 'text.secondary'
                            }}>
                                <Typography>Submit a report to see validation results</Typography>
                            </Box>
                        ) : (
                            <Box>
                                <Card sx={{
                                    mb: 2,
                                    bgcolor: result.validation.status === 'validated' ? '#e8f5e9' : '#ffebee'
                                }}>
                                    <CardContent>
                                        <Typography variant="h4" fontWeight="bold" align="center"
                                            color={result.validation.status === 'validated' ? 'success.main' : 'error.main'}
                                        >
                                            {result.validation.status.toUpperCase()}
                                        </Typography>
                                        <Typography variant="h3" align="center" sx={{ my: 2 }}>
                                            {(result.validation.final_score * 100).toFixed(1)}%
                                        </Typography>
                                        <Typography variant="body2" align="center" color="text.secondary">
                                            Final Validation Score
                                        </Typography>
                                    </CardContent>
                                </Card>

                                <Typography variant="subtitle2" gutterBottom>
                                    Layer Breakdown:
                                </Typography>

                                {Object.entries(result.validation.layer_scores).map(([layer, score]) => (
                                    <Box key={layer} sx={{ mb: 1 }}>
                                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                                            <Typography variant="body2">{layer}</Typography>
                                            <Typography variant="body2" fontWeight="bold">
                                                {(score * 100).toFixed(1)}%
                                            </Typography>
                                        </Box>
                                        <Box sx={{
                                            height: 8,
                                            bgcolor: '#e0e0e0',
                                            borderRadius: 4,
                                            overflow: 'hidden'
                                        }}>
                                            <Box sx={{
                                                height: '100%',
                                                width: `${score * 100}%`,
                                                bgcolor: score >= 0.7 ? '#4caf50' : score >= 0.5 ? '#ff9800' : '#f44336',
                                                borderRadius: 4
                                            }} />
                                        </Box>
                                    </Box>
                                ))}

                                <Alert severity="info" sx={{ mt: 2 }}>
                                    Report ID: <strong>#{result.report_id}</strong>
                                </Alert>
                            </Box>
                        )}
                    </Paper>
                </Grid>
            </Grid>
        </Box>
    );
};

export default ReportForm;
