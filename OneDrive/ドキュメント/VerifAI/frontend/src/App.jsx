import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import LandingPage from './pages/LandingPage';
import AnalysePage from './pages/AnalysePage';
import ResultsPage from './pages/ResultsPage';
import HistoryPage from './pages/HistoryPage';
import ModelInsightsPage from './pages/ModelInsightsPage';

export function App() {
  return (
    <Router>
      <div className="flex flex-col min-h-screen bg-ivory-100 text-charcoal-900 font-sans selection:bg-forest-100 selection:text-forest-900">
        <Navbar />
        <main className="flex-grow">
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/analyse" element={<AnalysePage />} />
            <Route path="/results/:id" element={<ResultsPage />} />
            <Route path="/history" element={<HistoryPage />} />
            <Route path="/insights" element={<ModelInsightsPage />} />
            {/* Fallback to Home */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
        <Footer />
      </div>
    </Router>
  );
}

export default App;

