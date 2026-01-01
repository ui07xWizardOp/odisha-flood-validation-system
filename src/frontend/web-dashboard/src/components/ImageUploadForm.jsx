import React, { useState, useCallback } from 'react';
import {
    Box, Paper, Typography, Button, Grid, Alert, CircularProgress,
    Card, CardContent, LinearProgress, Chip, TextField
} from '@mui/material';
import { CloudUpload, PhotoCamera, LocationOn, CheckCircle, Error } from '@mui/icons-material';

const ImageUploadForm = ({ onSubmitImage }) => {
    const [file, setFile] = useState(null);
    const [preview, setPreview] = useState(null);
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);
    const [depthMeters, setDepthMeters] = useState(1.0);
    const [description, setDescription] = useState('');

    const handleFileChange = useCallback((e) => {
        const selectedFile = e.target.files?.[0];
        if (selectedFile) {
            // Validate file type
            if (!selectedFile.type.startsWith('image/')) {
                setError('Please select an image file (JPEG, PNG)');
                return;
            }

            setFile(selectedFile);
            setError(null);
            setResult(null);

            // Create preview
            const reader = new FileReader();
            reader.onloadend = () => setPreview(reader.result);
            reader.readAsDataURL(selectedFile);
        }
    }, []);

    const handleDrop = useCallback((e) => {
        e.preventDefault();
        const droppedFile = e.dataTransfer.files?.[0];
        if (droppedFile && droppedFile.type.startsWith('image/')) {
            setFile(droppedFile);
            setError(null);

            const reader = new FileReader();
            reader.onloadend = () => setPreview(reader.result);
            reader.readAsDataURL(droppedFile);
        }
    }, []);

    const handleDragOver = (e) => e.preventDefault();

    const handleSubmit = async () => {
        if (!file) {
            setError('Please select an image first');
            return;
        }

        setLoading(true);
        setError(null);
        setResult(null);

        try {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('user_id', '1');
            formData.append('depth_meters', depthMeters.toString());
            formData.append('description', description);

            const response = await fetch('http://localhost:8000/reports/from-image', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Upload failed');
            }

            setResult(data);
            if (onSubmitImage) onSubmitImage(data);
        } catch (err) {
            setError(err.message || 'Failed to upload image');
        } finally {
            setLoading(false);
        }
    };

    const resetForm = () => {
        setFile(null);
        setPreview(null);
        setResult(null);
        setError(null);
    };

    return (
        <Box>
            <Typography variant="h4" fontWeight="600" gutterBottom sx={{ mb: 3 }}>
                📸 One-Shot Photo Report
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Upload a geotagged photo and we'll automatically extract the location and validate the flood.
            </Typography>

            <Grid container spacing={4}>
                {/* Upload Area */}
                <Grid item xs={12} md={7}>
                    <Paper sx={{ p: 3 }}>
                        {/* Drop Zone */}
                        <Box
                            onDrop={handleDrop}
                            onDragOver={handleDragOver}
                            sx={{
                                border: '2px dashed',
                                borderColor: preview ? 'success.main' : 'grey.400',
                                borderRadius: 2,
                                p: 4,
                                textAlign: 'center',
                                cursor: 'pointer',
                                bgcolor: preview ? 'success.50' : 'grey.50',
                                transition: 'all 0.3s ease',
                                '&:hover': { borderColor: 'primary.main', bgcolor: 'primary.50' }
                            }}
                            onClick={() => document.getElementById('image-upload').click()}
                        >
                            <input
                                id="image-upload"
                                type="file"
                                accept="image/jpeg,image/png"
                                onChange={handleFileChange}
                                style={{ display: 'none' }}
                            />

                            {preview ? (
                                <Box>
                                    <img
                                        src={preview}
                                        alt="Preview"
                                        style={{
                                            maxWidth: '100%',
                                            maxHeight: 300,
                                            borderRadius: 8
                                        }}
                                    />
                                    <Typography variant="body2" sx={{ mt: 2 }}>
                                        {file?.name}
                                    </Typography>
                                </Box>
                            ) : (
                                <Box>
                                    <CloudUpload sx={{ fontSize: 64, color: 'grey.400', mb: 2 }} />
                                    <Typography variant="h6" color="text.secondary">
                                        Drag & drop a geotagged image
                                    </Typography>
                                    <Typography variant="body2" color="text.secondary">
                                        or click to browse
                                    </Typography>
                                    <Button
                                        variant="outlined"
                                        startIcon={<PhotoCamera />}
                                        sx={{ mt: 2 }}
                                    >
                                        Select Photo
                                    </Button>
                                </Box>
                            )}
                        </Box>

                        {/* Additional Fields */}
                        <Grid container spacing={2} sx={{ mt: 2 }}>
                            <Grid item xs={6}>
                                <TextField
                                    fullWidth
                                    type="number"
                                    label="Water Depth (meters)"
                                    value={depthMeters}
                                    onChange={(e) => setDepthMeters(parseFloat(e.target.value) || 1.0)}
                                    inputProps={{ min: 0, max: 10, step: 0.1 }}
                                    size="small"
                                />
                            </Grid>
                            <Grid item xs={6}>
                                <TextField
                                    fullWidth
                                    label="Description (optional)"
                                    value={description}
                                    onChange={(e) => setDescription(e.target.value)}
                                    size="small"
                                />
                            </Grid>
                        </Grid>

                        {/* Submit Button */}
                        <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
                            <Button
                                variant="contained"
                                size="large"
                                onClick={handleSubmit}
                                disabled={!file || loading}
                                startIcon={loading ? <CircularProgress size={20} /> : <CloudUpload />}
                                sx={{
                                    flexGrow: 1,
                                    py: 1.5,
                                    background: 'linear-gradient(135deg, #1e3c72 0%, #2a5298 100%)'
                                }}
                            >
                                {loading ? 'Processing...' : 'Submit Photo Report'}
                            </Button>
                            {preview && (
                                <Button variant="outlined" onClick={resetForm}>
                                    Clear
                                </Button>
                            )}
                        </Box>

                        {error && (
                            <Alert severity="error" sx={{ mt: 2 }} icon={<Error />}>
                                {error}
                            </Alert>
                        )}
                    </Paper>
                </Grid>

                {/* Result Panel */}
                <Grid item xs={12} md={5}>
                    <Paper sx={{ p: 3, bgcolor: '#f8f9fa', height: '100%' }}>
                        <Typography variant="h6" gutterBottom>
                            📍 Extraction Result
                        </Typography>

                        {!result && !loading && (
                            <Box sx={{
                                display: 'flex', flexDirection: 'column',
                                alignItems: 'center', justifyContent: 'center',
                                height: 250, color: 'text.secondary'
                            }}>
                                <LocationOn sx={{ fontSize: 48, opacity: 0.3 }} />
                                <Typography>GPS will be extracted from photo</Typography>
                            </Box>
                        )}

                        {loading && (
                            <Box sx={{ py: 4 }}>
                                <Typography variant="body2" sx={{ mb: 2 }}>
                                    Extracting GPS & validating...
                                </Typography>
                                <LinearProgress />
                            </Box>
                        )}

                        {result && (
                            <Box>
                                <Card sx={{
                                    mb: 2,
                                    bgcolor: result.validation_status === 'validated'
                                        ? '#e8f5e9' : '#fff3e0'
                                }}>
                                    <CardContent>
                                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                                            <CheckCircle color="success" />
                                            <Typography variant="h6">
                                                Report #{result.report_id} Created
                                            </Typography>
                                        </Box>
                                        <Chip
                                            label={result.validation_status?.toUpperCase()}
                                            color={result.validation_status === 'validated' ? 'success' : 'warning'}
                                            size="small"
                                        />
                                        <Typography variant="h4" sx={{ mt: 2 }}>
                                            {(result.final_score * 100).toFixed(1)}%
                                        </Typography>
                                    </CardContent>
                                </Card>

                                {/* Extracted Location */}
                                <Typography variant="subtitle2" gutterBottom>
                                    📍 Extracted Location
                                </Typography>
                                <Box sx={{ mb: 2, pl: 2 }}>
                                    <Typography variant="body2">
                                        Lat: {result.extracted_location?.latitude?.toFixed(4)}°
                                    </Typography>
                                    <Typography variant="body2">
                                        Lon: {result.extracted_location?.longitude?.toFixed(4)}°
                                    </Typography>
                                    {result.extracted_location?.in_odisha_bounds && (
                                        <Chip label="Within Odisha" color="success" size="small" sx={{ mt: 1 }} />
                                    )}
                                </Box>

                                {/* CV Result */}
                                <Typography variant="subtitle2" gutterBottom>
                                    🔍 CV Analysis
                                </Typography>
                                <Box sx={{ pl: 2 }}>
                                    <Typography variant="body2">
                                        Flood Detected: {result.cv_result?.is_flood ? '✅ Yes' : '❌ No'}
                                    </Typography>
                                    <Typography variant="body2">
                                        Confidence: {((result.cv_result?.confidence || 0) * 100).toFixed(0)}%
                                    </Typography>
                                </Box>
                            </Box>
                        )}
                    </Paper>
                </Grid>
            </Grid>
        </Box>
    );
};

export default ImageUploadForm;
