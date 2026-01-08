import React, { useState, useCallback } from 'react';
import {
    Box, Paper, Typography, TextField, Button, Grid, Slider,
    Alert, CircularProgress, Card, CardContent, Snackbar, IconButton
} from '@mui/material';
import { Send, LocationOn, Water, Person, CloudUpload, PhotoCamera, Close } from '@mui/icons-material';
import { submitReport, submitImageReport, createUser, validatePhoto } from '../api';
import { motion, AnimatePresence } from 'framer-motion';

const SubmitReport = () => {
    const [formData, setFormData] = useState({
        user_id: 1,
        latitude: 20.46,
        longitude: 85.88,
        depth_meters: 1.0,
        description: ''
    });

    // Image Upload State
    const [imageFile, setImageFile] = useState(null);
    const [preview, setPreview] = useState(null);

    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);
    const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });

    const handleChange = (field) => (e) => {
        setFormData({ ...formData, [field]: e.target.value });
    };

    const handleSliderChange = (field) => (e, value) => {
        setFormData({ ...formData, [field]: value });
    };

    // Drag & Drop Handlers
    const handleFileChange = (e) => {
        const file = e.target.files[0];
        if (file) handleFile(file);
    };

    const handleDrop = useCallback((e) => {
        e.preventDefault();
        e.stopPropagation();
        const file = e.dataTransfer.files[0];
        if (file && file.type.startsWith('image/')) {
            handleFile(file);
        }
    }, []);

    const handleDragOver = useCallback((e) => {
        e.preventDefault();
        e.stopPropagation();
    }, []);

    const handleFile = async (file) => {
        setImageFile(file);
        const reader = new FileReader();
        reader.onloadend = () => setPreview(reader.result);
        reader.readAsDataURL(file);
        setResult(null); // Clear previous result

        // Auto-extract location from photo (Visual Validation + GPS)
        try {
            const validation = await validatePhoto(file);
            console.log("Photo validation:", validation);

            if (validation.location && validation.location.latitude) {
                setFormData(prev => ({
                    ...prev,
                    latitude: validation.location.latitude,
                    longitude: validation.location.longitude
                }));
                setSnackbar({ open: true, message: '📍 Location updated from photo!', severity: 'success' });
            }
        } catch (e) {
            console.error("Photo validation failed", e);
        }
    };


    const removeImage = () => {
        setImageFile(null);
        setPreview(null);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        setResult(null);

        try {
            // First ensure user exists (create if needed)
            try {
                await createUser({
                    username: `user_${formData.user_id}`,
                    email: `user${formData.user_id}@floodreport.local`
                });
            } catch (e) {
                // User might already exist (400 error), which is fine
                console.log('User creation skipped (may already exist):', e.message);
            }

            let response;

            if (imageFile) {
                // Use Visual Validation Path (L5)
                // Pass manual coordinates to override EXIF if needed
                response = await submitImageReport(imageFile, {
                    ...formData,
                    user_id: parseInt(formData.user_id),
                    latitude: parseFloat(formData.latitude),
                    longitude: parseFloat(formData.longitude),
                    depth_meters: parseFloat(formData.depth_meters)
                });

                // image report response structure is slightly different, need to align
                // api.py -> /reports/from-image returns ImageReportResponse
                // which has: report_id, extracted_location, cv_result, validation_status, final_score
            } else {
                // Use Standard Path
                response = await submitReport({
                    ...formData,
                    user_id: parseInt(formData.user_id),
                    latitude: parseFloat(formData.latitude),
                    longitude: parseFloat(formData.longitude),
                    depth_meters: parseFloat(formData.depth_meters),
                    timestamp: new Date().toISOString()
                });
            }

            // Format result for display
            // Standardize response for the UI
            // Check if response has 'validation' object (standard) or flat structure (image)

            // Standard submitReport returns full DB object which has attributes
            // Image submitReport return ImageReportResponse schema

            // Let's normalize safely
            // For standard: response.physical_score etc exist
            // For image: response.cv_result might have details

            // Actually, based on my recent memory of standard submit, it returns FloodReportResponse
            // which has detailed scores.

            const formattedResult = {
                report_id: response.report_id,
                validation: {
                    status: response.validation_status || 'submitted',
                    final_score: response.final_score || 0,
                    layer_scores: {
                        L1_physical: response.physical_score || 0,
                        L2_statistical: response.statistical_score || 0,
                        L3_reputation: response.reputation_score || 0,
                        L4_social: response.social_score || 0,  // Now available!
                        L5_visual: response.cv_score || 0       // Now available!
                    }
                }
            };

            // If image upload, we might want to ensure L5 is visible
            if (imageFile && formattedResult.validation.layer_scores.L5_visual === 0) {
                // Fallback if API didn't map it directly yet (though it should)
                if (response.cv_result && response.cv_result.score) {
                    formattedResult.validation.layer_scores.L5_visual = response.cv_result.score;
                }
            }

            setResult(formattedResult);
            setSnackbar({ open: true, message: 'Report submitted successfully!', severity: 'success' });

        } catch (err) {
            console.error(err);
            setError('Failed to submit report. Please try again.');
            setSnackbar({ open: true, message: 'Submission failed', severity: 'error' });
        }
        setLoading(false);
    };

    return (
        <Box maxWidth="lg" sx={{ mx: 'auto' }}>
            <Typography variant="h4" fontWeight="600" gutterBottom sx={{ mb: 3 }}>
                📝 Submit Flood Report
            </Typography>

            <Grid container spacing={4}>
                {/* Form */}
                <Grid item xs={12} md={7}>
                    <Paper sx={{ p: 4, borderRadius: 4 }}>
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

                                {/* Photo Upload (L5 Visual Validation) */}
                                <Grid item xs={12}>
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                                        <PhotoCamera color="secondary" />
                                        <Typography variant="subtitle1" fontWeight="500">
                                            Add Photo for Visual Validation (L5)
                                        </Typography>
                                        <Typography variant="caption" color="text.secondary" sx={{ ml: 1 }}>
                                            (Optional - Drag & Drop)
                                        </Typography>
                                    </Box>

                                    <Box
                                        onDrop={handleDrop}
                                        onDragOver={handleDragOver}
                                        onClick={() => !preview && document.getElementById('image-upload').click()}
                                        sx={{
                                            border: '2px dashed',
                                            borderColor: preview ? 'transparent' : 'grey.400',
                                            borderRadius: 2,
                                            height: 200,
                                            position: 'relative',
                                            display: 'flex',
                                            flexDirection: 'column',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            cursor: preview ? 'default' : 'pointer',
                                            bgcolor: preview ? 'black' : 'action.hover',
                                            transition: 'all 0.3s ease',
                                            '&:hover': { borderColor: preview ? 'transparent' : 'primary.main', bgcolor: preview ? 'black' : 'action.selected' },
                                            overflow: 'hidden'
                                        }}
                                    >
                                        <input
                                            id="image-upload"
                                            type="file"
                                            accept="image/jpeg,image/png"
                                            onChange={handleFileChange}
                                            style={{ display: 'none' }}
                                        />

                                        <AnimatePresence>
                                            {preview ? (
                                                <motion.div
                                                    initial={{ opacity: 0 }}
                                                    animate={{ opacity: 1 }}
                                                    exit={{ opacity: 0 }}
                                                    style={{ width: '100%', height: '100%', position: 'relative' }}
                                                >
                                                    <img
                                                        src={preview}
                                                        alt="Preview"
                                                        style={{
                                                            width: '100%',
                                                            height: '100%',
                                                            objectFit: 'contain',
                                                        }}
                                                    />
                                                    <IconButton
                                                        onClick={(e) => { e.stopPropagation(); removeImage(); }}
                                                        sx={{ position: 'absolute', top: 5, right: 5, bgcolor: 'rgba(0,0,0,0.5)', color: 'white', '&:hover': { bgcolor: 'rgba(0,0,0,0.8)' } }}
                                                        size="small"
                                                    >
                                                        <Close fontSize="small" />
                                                    </IconButton>
                                                </motion.div>
                                            ) : (
                                                <Box textAlign="center">
                                                    <CloudUpload sx={{ fontSize: 40, color: 'text.secondary', mb: 1 }} />
                                                    <Typography variant="body2" color="text.primary">
                                                        Drag & drop or click to upload
                                                    </Typography>
                                                </Box>
                                            )}
                                        </AnimatePresence>
                                    </Box>
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
                                        startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <Send />}
                                        sx={{
                                            py: 1.5,
                                            borderRadius: 2,
                                            background: 'linear-gradient(135deg, #1e3c72 0%, #2a5298 100%)'
                                        }}
                                    >
                                        {loading ? 'Submitting...' : 'Submit Report'}
                                    </Button>
                                </Grid>
                            </Grid>
                        </form>

                        {error && (
                            <Alert severity="error" sx={{ mt: 3, borderRadius: 2 }}>
                                {error}
                            </Alert>
                        )}
                    </Paper>
                </Grid>

                {/* Result Panel */}
                <Grid item xs={12} md={5}>
                    <Paper sx={{ p: 3, bgcolor: 'background.paper', height: '100%', borderRadius: 4 }}>
                        <Typography variant="h6" gutterBottom fontWeight="bold">
                            🔍 Validation Result
                        </Typography>

                        {!result ? (
                            <Box sx={{
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                height: 300,
                                color: 'text.secondary',
                                border: '2px dashed rgba(0,0,0,0.1)',
                                borderRadius: 2
                            }}>
                                <Typography>Submit a report to see validation results</Typography>
                            </Box>
                        ) : (
                            <Box>
                                <Card sx={{
                                    mb: 2,
                                    bgcolor: result.validation.status === 'validated' ? 'rgba(76, 175, 80, 0.1)' : 'rgba(244, 67, 54, 0.1)',
                                    backgroundImage: 'none',
                                    border: `1px solid ${result.validation.status === 'validated' ? '#4caf50' : '#f44336'}`
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

                                <Typography variant="subtitle2" gutterBottom sx={{ mt: 3 }}>
                                    Layer Breakdown:
                                </Typography>

                                {Object.entries(result.validation.layer_scores).map(([layer, score]) => (
                                    <Box key={layer} sx={{ mb: 2 }}>
                                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                                            <Typography variant="caption" color="text.secondary">
                                                {layer.replace(/_/g, ' ').replace('L', 'Layer ')}
                                            </Typography>
                                            <Typography variant="caption" fontWeight="bold">
                                                {(score * 100).toFixed(0)}%
                                            </Typography>
                                        </Box>
                                        <Box sx={{
                                            height: 6,
                                            bgcolor: 'action.hover',
                                            borderRadius: 4,
                                            overflow: 'hidden'
                                        }}>
                                            <Box sx={{
                                                height: '100%',
                                                width: `${score * 100}%`,
                                                bgcolor: score >= 0.7 ? '#4caf50' : score >= 0.5 ? '#ff9800' : '#f44336',
                                                borderRadius: 4,
                                                transition: 'width 1s ease-in-out'
                                            }} />
                                        </Box>
                                    </Box>
                                ))}

                                <Alert severity="info" sx={{ mt: 3, borderRadius: 2 }}>
                                    Report ID: <strong>#{result.report_id}</strong>
                                </Alert>
                            </Box>
                        )}
                    </Paper>
                </Grid>
            </Grid>

            <Snackbar
                open={snackbar.open}
                autoHideDuration={6000}
                onClose={() => setSnackbar({ ...snackbar, open: false })}
                anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
            >
                <Alert severity={snackbar.severity} onClose={() => setSnackbar({ ...snackbar, open: false })}>
                    {snackbar.message}
                </Alert>
            </Snackbar>
        </Box>
    );
};

export default SubmitReport;
