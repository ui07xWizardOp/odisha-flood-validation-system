import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import MainLayout from './components/layout/MainLayout';
import Dashboard from './pages/Dashboard';
import MapPage from './pages/MapPage';
import SubmitReport from './pages/SubmitReport';
import PhotoUpload from './pages/PhotoUpload';
import AllReports from './pages/AllReports';

// Simple wrapper to inject props if needed, or pages can fetch their own data
// For this refactor, we'll let pages manage their data or pass simple props if we lift state.
// To keep it simple and scalable, we'll refactor pages to fetch data on mount.

const AppRoutes = ({ toggleTheme, isDarkMode }) => {
    return (
        <Routes>
            <Route path="/" element={<MainLayout toggleTheme={toggleTheme} isDarkMode={isDarkMode} />}>
                <Route index element={<Dashboard />} />
                <Route path="map" element={<MapPage />} />
                <Route path="submit" element={<SubmitReport />} />
                <Route path="photo-upload" element={<PhotoUpload />} />
                <Route path="reports" element={<AllReports />} />
                <Route path="*" element={<Navigate to="/" replace />} />
            </Route>
        </Routes>
    );
};

export default AppRoutes;
