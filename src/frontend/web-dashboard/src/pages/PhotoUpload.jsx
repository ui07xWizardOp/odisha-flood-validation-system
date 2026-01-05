import React, { useState, useCallback } from 'react';
import {
    Box, Paper, Typography, Button, Grid, Alert, CircularProgress,
    Card, CardContent, LinearProgress, Chip, TextField, Stack, IconButton
} from '@mui/material';
import { CloudUpload, PhotoCamera, LocationOn, CheckCircle, Error, Close, QrCodeScanner } from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { submitImageReport, createUser, getUser } from '../api';

const ScannerOverlay = () => (
    <Box
        sx={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            overflow: 'hidden',
            borderRadius: 2,
            zIndex: 10,
            pointerEvents: 'none'
        }}
    >
        <motion.div
            initial={{ top: '0%' }}
            animate={{ top: '100%' }}
            transition={{
                duration: 2,
                repeat: Infinity,
                ease: "linear",
                repeatType: "reverse"
            }}
            style={{
                position: 'absolute',
                left: 0,
                right: 0,
                height: '4px',
                background: 'linear-gradient(90deg, transparent, #00ff00, transparent)',
                boxShadow: '0 0 15px #00ff00'
            }}
        />
        <Box sx={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            bgcolor: 'rgba(0,0,0,0.6)',
            px: 2,
            py: 1,
            borderRadius: 8,
            color: '#00ff00',
            display: 'flex',
            alignItems: 'center',
            gap: 1
        }}>
            <QrCodeScanner sx={{ animation: 'pulse 2s infinite' }} />
            <Typography variant="caption" fontWeight="bold">ANALYZING EXIF & CV</Typography>
        </Box>
    </Box>
);

const PhotoUpload = () => {
    const [file, setFile] = useState(null);
    const [preview, setPreview] = useState(null);
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);
    const [depthMeters, setDepthMeters] = useState(1.0);
    const [description, setDescription] = useState('');

    const handleFileChange = useCallback((e) => {
        const selectedFile = e.target.files?.[0];
        processFile(selectedFile);
    }, []);

    const processFile = (selectedFile) => {
        if (selectedFile) {
            if (!selectedFile.type.startsWith('image/')) {
                setError('Please select an image file (JPEG, PNG)');
                return;
            }

            setFile(selectedFile);
            setError(null);
            setResult(null);

            const reader = new FileReader();
            reader.onloadend = () => setPreview(reader.result);
            reader.readAsDataURL(selectedFile);
        }
    };

    const handleDrop = useCallback((e) => {
        e.preventDefault();
        const droppedFile = e.dataTransfer.files?.[0];
        processFile(droppedFile);
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
            // First ensure user exists (create if needed)
            try {
                // Check if user exists first to promote cleaner console logs
                try {
                    await getUser(1);
                } catch (notFound) {
                    await createUser({
                        username: `user_1`,
                        email: `user1@floodreport.local`
                    });
                }
            } catch (e) {
                // Ignore exist error
            }

            const response = await submitImageReport(file, {
                user_id: 1,
                depth_meters: depthMeters,
                description: description
            });

            setResult(response);

        } catch (err) {
            setError(err.message || 'Failed to upload image. Please try again.');
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
        <Box maxWidth="lg" sx={{ mx: 'auto' }}>
            <Typography variant="h4" fontWeight="600" gutterBottom sx={{ mb: 1 }}>
                📸 Magic Photo Upload
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
                One-shot report submission: Geo-tag extraction, CV flood detection, and auto-validation.
            </Typography>

            <Grid container spacing={4}>
                {/* Upload Area */}
                <Grid item xs={12} md={7}>
                    <Paper sx={{ p: 0, overflow: 'hidden', borderRadius: 4, bgcolor: 'background.paper', border: '1px solid rgba(0,0,0,0.1)' }}>
                        <Box sx={{ p: 3 }}>
                            {/* Drop Zone */}
                            <Box
                                onDrop={handleDrop}
                                onDragOver={handleDragOver}
                                onClick={() => !preview && document.getElementById('image-upload').click()}
                                sx={{
                                    border: '2px dashed',
                                    borderColor: preview ? 'transparent' : 'grey.400',
                                    borderRadius: 3,
                                    height: { xs: 250, md: 400 },
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
                                                onClick={(e) => { e.stopPropagation(); resetForm(); }}
                                                sx={{ position: 'absolute', top: 10, right: 10, bgcolor: 'rgba(0,0,0,0.5)', color: 'white', '&:hover': { bgcolor: 'rgba(0,0,0,0.8)' } }}
                                            >
                                                <Close />
                                            </IconButton>
                                            {loading && <ScannerOverlay />}
                                        </motion.div>
                                    ) : (
                                        <Box textAlign="center">
                                            <CloudUpload sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                                            <Typography variant="h6" color="text.primary">
                                                Drag & drop a geotagged image
                                            </Typography>
                                            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                                                or click to browse checks
                                            </Typography>
                                            <Button
                                                variant="outlined"
                                                startIcon={<PhotoCamera />}
                                                sx={{ borderRadius: 8 }}
                                            >
                                                Select Photo
                                            </Button>
                                        </Box>
                                    )}
                                </AnimatePresence>
                            </Box>
                        </Box>

                        {/* Controls */}
                        <Box sx={{ px: 3, pb: 3, pt: 1 }}>
                            <Grid container spacing={2}>
                                <Grid item xs={6}>
                                    <TextField
                                        fullWidth
                                        type="number"
                                        label="Estimated Depth (m)"
                                        value={depthMeters}
                                        onChange={(e) => setDepthMeters(parseFloat(e.target.value) || 1.0)}
                                        inputProps={{ min: 0, max: 10, step: 0.1 }}
                                        size="small"
                                        disabled={loading}
                                    />
                                </Grid>
                                <Grid item xs={6}>
                                    <TextField
                                        fullWidth
                                        label="Description"
                                        value={description}
                                        onChange={(e) => setDescription(e.target.value)}
                                        size="small"
                                        disabled={loading}
                                    />
                                </Grid>
                                <Grid item xs={12}>
                                    <Button
                                        fullWidth
                                        variant="contained"
                                        size="large"
                                        onClick={handleSubmit}
                                        disabled={!file || loading}
                                        sx={{
                                            py: 1.5,
                                            borderRadius: 2,
                                            background: 'linear-gradient(135deg, #1e3c72 0%, #2a5298 100%)',
                                            boxShadow: '0 4px 12px rgba(30, 60, 114, 0.3)'
                                        }}
                                    >
                                        {loading ? 'Processing...' : 'Analyze & Submit'}
                                    </Button>
                                </Grid>
                            </Grid>

                            {error && (
                                <Alert severity="error" sx={{ mt: 2, borderRadius: 2 }} icon={<Error />}>
                                    {error}
                                </Alert>
                            )}
                        </Box>
                    </Paper>
                </Grid>

                {/* Result Panel */}
                <Grid item xs={12} md={5}>
                    <Paper sx={{ p: 4, bgcolor: 'background.paper', height: '100%', borderRadius: 4 }}>
                        <Typography variant="h6" gutterBottom fontWeight="bold">
                            Analysis Results
                        </Typography>

                        {!result && !loading && (
                            <Box sx={{
                                display: 'flex', flexDirection: 'column',
                                alignItems: 'center', justifyContent: 'center',
                                height: 300, color: 'text.secondary',
                                opacity: 0.7
                            }}>
                                <LocationOn sx={{ fontSize: 64, mb: 1, color: 'text.disabled' }} />
                                <Typography align="center" variant="body2">
                                    Upload a photo to detect flood severity,<br />location, and validate report.
                                </Typography>
                            </Box>
                        )}

                        {loading && (
                            <Box sx={{ py: 8 }}>
                                <Typography variant="body2" sx={{ mb: 2 }} align="center">
                                    Running MobileNetV2 Analysis...
                                </Typography>
                                <LinearProgress sx={{ borderRadius: 4, height: 8 }} />
                                <Stack spacing={1} sx={{ mt: 2 }}>
                                    <Typography variant="caption" color="text.secondary">➤ Extracting EXIF Data...</Typography>
                                    <Typography variant="caption" color="text.secondary">➤ Verifying Coordinates...</Typography>
                                    <Typography variant="caption" color="text.secondary">➤ Checking Flood Hazards...</Typography>
                                </Stack>
                            </Box>
                        )}

                        {result && (
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                            >
                                <Card sx={{
                                    mb: 3,
                                    bgcolor: result.validation_status === 'validated'
                                        ? 'rgba(76, 175, 80, 0.1)' : 'rgba(255, 152, 0, 0.1)',
                                    backgroundImage: 'none',
                                    border: `1px solid ${result.validation_status === 'validated' ? '#4caf50' : '#ff9800'}`
                                }}>
                                    <CardContent>
                                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                                            {result.validation_status === 'validated' ? <CheckCircle color="success" /> : <Error color="warning" />}
                                            <Typography variant="h6">
                                                Verification Complete
                                            </Typography>
                                        </Box>
                                        <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 1 }}>
                                            <Typography variant="h3" fontWeight="bold">
                                                {(result.final_score * 100).toFixed(1)}%
                                            </Typography>
                                            <Typography variant="subtitle1" color="text.secondary">
                                                Confidence
                                            </Typography>
                                        </Box>
                                        <Chip
                                            label={result.validation_status?.toUpperCase()}
                                            color={result.validation_status === 'validated' ? 'success' : 'warning'}
                                            size="small"
                                            sx={{ mt: 1 }}
                                        />
                                    </CardContent>
                                </Card>

                                <Stack spacing={2}>
                                    <Box>
                                        <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                                            📍 Geolocation
                                        </Typography>
                                        <Paper variant="outlined" sx={{ p: 2, bgcolor: 'background.default' }}>
                                            <Typography variant="body2" fontWeight="bold">
                                                {result.extracted_location?.latitude != null
                                                    ? `${result.extracted_location.latitude.toFixed(5)}°N, ${result.extracted_location.longitude.toFixed(5)}°E`
                                                    : "N/A (Geo-tag unavailable)"}
                                            </Typography>
                                            {result.extracted_location?.in_odisha_bounds && (
                                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mt: 0.5 }}>
                                                    <CheckCircle fontSize="small" color="success" />
                                                    <Typography variant="caption" color="success.main">Verified Location (Odisha)</Typography>
                                                </Box>
                                            )}
                                        </Paper>
                                    </Box>

                                    <Box>
                                        <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                                            🖼️ CV Analysis
                                        </Typography>
                                        <Paper variant="outlined" sx={{ p: 2, bgcolor: 'background.default' }}>
                                            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                                                <Typography variant="body2">Flood Detected</Typography>
                                                <Typography variant="body2" fontWeight="bold" color={result.cv_result?.is_flood ? 'error.main' : 'text.primary'}>
                                                    {result.cv_result?.is_flood ? 'POSITIVE' : 'NEGATIVE'}
                                                </Typography>
                                            </Box>
                                            <Box sx={{ mt: 1 }}>
                                                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                                                    <Typography variant="caption">Model Confidence</Typography>
                                                    <Typography variant="caption">{((result.cv_result?.confidence || 0) * 100).toFixed(0)}%</Typography>
                                                </Box>
                                                <LinearProgress variant="determinate" value={(result.cv_result?.confidence || 0) * 100} sx={{ height: 6, borderRadius: 3 }} />
                                            </Box>
                                        </Paper>
                                    </Box>
                                </Stack>
                            </motion.div>
                        )}
                    </Paper>
                </Grid>
            </Grid>
        </Box>
    );
};

export default PhotoUpload;
