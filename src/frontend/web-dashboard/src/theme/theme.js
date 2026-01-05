import { createTheme } from '@mui/material';

export const getTheme = (mode) => createTheme({
    palette: {
        mode,
        primary: {
            main: mode === 'dark' ? '#90caf9' : '#1e3c72',
            dark: '#152b52',
            light: '#64b5f6',
        },
        secondary: {
            main: mode === 'dark' ? '#f48fb1' : '#2a5298',
        },
        background: {
            default: mode === 'dark' ? '#0a1929' : '#f5f7fa',
            paper: mode === 'dark' ? '#1e293b' : '#ffffff',
        },
        text: {
            primary: mode === 'dark' ? '#e2e8f0' : '#1e293b',
            secondary: mode === 'dark' ? '#94a3b8' : '#64748b',
        },
    },
    typography: {
        fontFamily: '"Plus Jakarta Sans", "Inter", "Roboto", "Helvetica", "Arial", sans-serif',
        h4: { fontWeight: 700, letterSpacing: '-0.5px' },
        h5: { fontWeight: 600, letterSpacing: '-0.5px' },
        h6: { fontWeight: 600 },
        button: { textTransform: 'none', fontWeight: 600 },
    },
    shape: {
        borderRadius: 12,
    },
    components: {
        MuiCard: {
            styleOverrides: {
                root: {
                    backgroundImage: 'none',
                    backdropFilter: 'blur(20px)',
                    backgroundColor: mode === 'dark'
                        ? 'rgba(30, 41, 59, 0.7)'
                        : 'rgba(255, 255, 255, 0.8)',
                    boxShadow: mode === 'dark'
                        ? '0 4px 6px -1px rgba(0, 0, 0, 0.5)'
                        : '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                    border: mode === 'dark'
                        ? '1px solid rgba(255, 255, 255, 0.1)'
                        : '1px solid rgba(255, 255, 255, 0.3)',
                },
            },
        },
        MuiPaper: {
            styleOverrides: {
                root: {
                    backgroundImage: 'none',
                }
            }
        },
        MuiButton: {
            styleOverrides: {
                root: {
                    borderRadius: 8,
                    boxShadow: 'none',
                    '&:hover': {
                        boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
                        transform: 'translateY(-1px)',
                        transition: 'all 0.2s ease-in-out',
                    },
                },
                containedPrimary: {
                    background: 'linear-gradient(135deg, #1e3c72 0%, #2a5298 100%)',
                },
            },
        },
    },
});
