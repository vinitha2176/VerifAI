import React from 'react';
import { Link } from 'react-router-dom';
import { Shield, ExternalLink, AlertCircle } from 'lucide-react';

export const Footer = () => {
  return (
    <footer className="bg-ivory-200 border-t border-ivory-300 mt-20 transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-10">
          
          {/* Brand Info */}
          <div className="md:col-span-2 space-y-4">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-forest-800 text-ivory-100 flex items-center justify-center">
                <Shield className="w-4 h-4" />
              </div>
              <span className="font-serif text-xl font-bold tracking-tight text-forest-950">
                Verif<span className="text-forest-600">AI</span>
              </span>
            </div>
            <p className="text-sm text-charcoal-600 max-w-md leading-relaxed">
              Verify opportunities. Protect your future. An AI-powered recruitment risk assessment
              platform designed to safeguard job seekers and students against employment scams,
              fraudulent training fees, and predatory placement schemes.
            </p>
            <div className="text-xs text-charcoal-500">
              Built with genuine ML (TF-IDF + Calibrated Linear SVM) trained on the EMSCAD research dataset.
            </div>
          </div>

          {/* Quick Links */}
          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-charcoal-900 mb-3 font-sans">
              Navigation
            </h4>
            <ul className="space-y-2 text-sm text-charcoal-600">
              <li>
                <Link to="/" className="hover:text-forest-800 transition-colors">
                  Home
                </Link>
              </li>
              <li>
                <Link to="/analyse" className="hover:text-forest-800 transition-colors">
                  Analyse Offer
                </Link>
              </li>
              <li>
                <Link to="/history" className="hover:text-forest-800 transition-colors">
                  Analysis History
                </Link>
              </li>
              <li>
                <Link to="/insights" className="hover:text-forest-800 transition-colors">
                  Model Insights
                </Link>
              </li>
            </ul>
          </div>

          {/* Developer & APIs */}
          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-charcoal-900 mb-3 font-sans">
              Documentation
            </h4>
            <ul className="space-y-2 text-sm text-charcoal-600">
              <li>
                <a
                  href="http://localhost:8000/docs"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 hover:text-forest-800 transition-colors"
                >
                  Swagger REST API <ExternalLink className="w-3.5 h-3.5" />
                </a>
              </li>
              <li>
                <a
                  href="http://localhost:8000/api/health"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 hover:text-forest-800 transition-colors"
                >
                  Health Endpoint <ExternalLink className="w-3.5 h-3.5" />
                </a>
              </li>
              <li>
                <a
                  href="https://www.mdpi.com/1999-5903/9/1/6"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 hover:text-forest-800 transition-colors"
                >
                  EMSCAD Paper <ExternalLink className="w-3.5 h-3.5" />
                </a>
              </li>
            </ul>
          </div>

        </div>

        {/* Legal Disclaimer Card */}
        <div className="bg-ivory-100 rounded-xl p-4 sm:p-5 border border-ivory-300 text-xs text-charcoal-600 leading-relaxed space-y-2">
          <div className="flex items-center gap-2 font-semibold text-charcoal-900">
            <AlertCircle className="w-4 h-4 text-forest-700" />
            <span>Important Advisory & Legal Disclaimer</span>
          </div>
          <p>
            VerifAI provides automated risk assessments based on submitted content. It does not verify employer
            identity or establish that an organisation is fraudulent. Always independently verify recruitment
            opportunities before sharing money or sensitive information.
          </p>
        </div>

        {/* Copyright */}
        <div className="mt-8 pt-6 border-t border-ivory-300 text-center text-xs text-charcoal-500 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p>© {new Date().getFullYear()} VerifAI Platform. Developed for the Neural Storm Hackathon.</p>
          <p className="text-charcoal-400">Strictly non-commercial research & risk prevention instrument.</p>
        </div>

      </div>
    </footer>
  );
};

export default Footer;

