import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Shield, Menu, X, Activity, CheckCircle, AlertCircle } from 'lucide-react';
import { getHealth } from '../services/api';

export const Navbar = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [healthStatus, setHealthStatus] = useState({ status: 'checking', ml: 'unknown' });
  const location = useLocation();

  useEffect(() => {
    let mounted = true;
    const checkSystemHealth = async () => {
      try {
        const data = await getHealth();
        if (mounted) {
          setHealthStatus({
            status: data.status === 'healthy' ? 'healthy' : 'degraded',
            ml: data.ml_model === 'loaded' ? 'ML Ready' : 'ML Unavailable',
          });
        }
      } catch (err) {
        if (mounted) {
          setHealthStatus({ status: 'offline', ml: 'Backend Offline' });
        }
      }
    };

    checkSystemHealth();
    const interval = setInterval(checkSystemHealth, 30000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  const navLinks = [
    { name: 'Home', path: '/' },
    { name: 'Analyse Offer', path: '/analyse' },
    { name: 'Analysis History', path: '/history' },
    { name: 'Model Insights', path: '/insights' },
  ];

  const isActive = (path) => {
    if (path === '/' && location.pathname === '/') return true;
    if (path !== '/' && location.pathname.startsWith(path)) return true;
    return false;
  };

  return (
    <header className="sticky top-0 z-40 bg-ivory-100/90 backdrop-blur-md border-b border-ivory-300 transition-all duration-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-20">
          
          {/* Logo & Tagline */}
          <Link to="/" className="flex items-center gap-3 group">
            <div className="w-10 h-10 rounded-xl bg-forest-800 text-ivory-100 flex items-center justify-center shadow-subtle group-hover:bg-forest-900 transition-colors">
              <Shield className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-serif text-2xl font-bold tracking-tight text-forest-950">
                  Verif<span className="text-forest-600">AI</span>
                </span>
                <span className="hidden sm:inline-block text-[11px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded bg-ivory-200 text-charcoal-700 border border-ivory-300">
                  v1.0
                </span>
              </div>
              <p className="hidden md:block text-xs text-charcoal-500 font-sans tracking-normal">
                Verify opportunities. Protect your future.
              </p>
            </div>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center gap-1 lg:gap-2">
            {navLinks.map((link) => {
              const active = isActive(link.path);
              return (
                <Link
                  key={link.path}
                  to={link.path}
                  className={`px-3.5 py-2 rounded-lg text-sm font-medium transition-all duration-150 ${
                    active
                      ? 'bg-forest-800 text-ivory-100 shadow-sm'
                      : 'text-charcoal-700 hover:text-forest-900 hover:bg-ivory-200'
                  }`}
                >
                  {link.name}
                </Link>
              );
            })}
          </nav>

          {/* System Health Status & Primary CTA */}
          <div className="hidden sm:flex items-center gap-3">
            <div
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${
                healthStatus.status === 'healthy'
                  ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                  : healthStatus.status === 'checking'
                  ? 'bg-amber-50 text-amber-800 border-amber-200'
                  : 'bg-rose-50 text-rose-800 border-rose-200'
              }`}
              title={`API Backend: ${healthStatus.status} | ML Pipeline: ${healthStatus.ml}`}
            >
              <span
                className={`w-2 h-2 rounded-full ${
                  healthStatus.status === 'healthy'
                    ? 'bg-emerald-500 animate-pulse'
                    : healthStatus.status === 'checking'
                    ? 'bg-amber-500'
                    : 'bg-rose-500'
                }`}
              />
              <span className="hidden lg:inline">{healthStatus.ml}</span>
              <span className="lg:hidden">Ready</span>
            </div>

            <Link
              to="/analyse"
              className="inline-flex items-center justify-center px-4 py-2 rounded-lg text-sm font-medium bg-forest-800 text-ivory-100 hover:bg-forest-900 shadow-sm transition-all"
            >
              Analyse Offer
            </Link>
          </div>

          {/* Mobile menu button */}
          <div className="flex md:hidden items-center">
            <button
              type="button"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-lg text-charcoal-700 hover:text-charcoal-900 hover:bg-ivory-200 focus:outline-none"
              aria-label="Toggle mobile menu"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>

        </div>
      </div>

      {/* Mobile menu dropdown */}
      {mobileMenuOpen && (
        <div className="md:hidden border-b border-ivory-300 bg-ivory-100 px-4 pt-3 pb-6 space-y-2">
          {navLinks.map((link) => {
            const active = isActive(link.path);
            return (
              <Link
                key={link.path}
                to={link.path}
                onClick={() => setMobileMenuOpen(false)}
                className={`block px-3 py-2.5 rounded-lg text-base font-medium transition-colors ${
                  active
                    ? 'bg-forest-800 text-ivory-100'
                    : 'text-charcoal-800 hover:bg-ivory-200'
                }`}
              >
                {link.name}
              </Link>
            );
          })}
          <div className="pt-3 border-t border-ivory-300 flex items-center justify-between">
            <span className="text-xs text-charcoal-500 flex items-center gap-1.5">
              <span
                className={`w-2 h-2 rounded-full ${
                  healthStatus.status === 'healthy' ? 'bg-emerald-500' : 'bg-rose-500'
                }`}
              />
              System: {healthStatus.ml}
            </span>
            <Link
              to="/analyse"
              onClick={() => setMobileMenuOpen(false)}
              className="px-4 py-2 rounded-lg text-sm font-medium bg-forest-800 text-ivory-100"
            >
              Start Analysis
            </Link>
          </div>
        </div>
      )}
    </header>
  );
};

export default Navbar;

