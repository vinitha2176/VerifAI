import React, { useState, useEffect } from 'react';
import { useParams, useLocation, Link, useNavigate } from 'react-router-dom';
import {
  ShieldCheck,
  AlertTriangle,
  AlertOctagon,
  FileText,
  Clock,
  ArrowLeft,
  CheckCircle2,
  ExternalLink,
  Info,
  Quote,
  Loader2,
  Cpu,
  Layers,
  History,
  WifiOff,
  RefreshCw
} from 'lucide-react';
import { getAnalysisDetail } from '../services/api';
import { RiskBadge, PredictionBadge } from '../components/RiskBadge';

/**
 * Helper to distinguish network/server errors from genuine 404 / record not found responses
 */
const isNetworkOrServerError = (err) => {
  if (!err) return false;

  // Check explicit HTTP status if present on error object
  if (err.status === 404 || err.response?.status === 404) {
    return false;
  }
  if (err.status >= 500 || err.response?.status >= 500) {
    return true;
  }

  const msg = (typeof err === 'string' ? err : err.message || '').toLowerCase();

  // Explicit network connection, timeout, or server error patterns
  if (
    msg.includes('unable to connect') ||
    msg.includes('network error') ||
    msg.includes('failed to fetch') ||
    msg.includes('connection refused') ||
    msg.includes('connection') ||
    msg.includes('econnrefused') ||
    msg.includes('timeout') ||
    msg.includes('server returned error (5') ||
    msg.includes('internal server error') ||
    msg.includes('bad gateway') ||
    msg.includes('service unavailable') ||
    msg.includes('gateway timeout')
  ) {
    return true;
  }

  // Explicit 404 / record not found patterns
  if (
    msg.includes('not found') ||
    msg.includes('404') ||
    msg.includes('no analysis record id')
  ) {
    return false;
  }

  // Treat any other unexpected communication/retrieval error as retryable
  return true;
};

export const ResultsPage = () => {
  const { id } = useParams();
  const location = useLocation();
  const navigate = useNavigate();

  // If state was passed via navigate from AnalysePage, use it immediately
  const [analysis, setAnalysis] = useState(location.state?.result || null);
  const [loading, setLoading] = useState(!location.state?.result);
  const [isRetrying, setIsRetrying] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    let mounted = true;

    // If analysis was passed via navigation state and matches current ID (or no ID in route)
    if (analysis && (!id || String(analysis.id) === String(id))) {
      setLoading(false);
      return;
    }

    if (!id) {
      setLoading(false);
      setError('No analysis record ID was provided.');
      return;
    }

    setLoading(true);
    setError(null);

    getAnalysisDetail(id)
      .then((data) => {
        if (mounted) {
          setAnalysis(data);
          setError(null);
        }
      })
      .catch((err) => {
        if (mounted) {
          setError(err.message || 'Unable to retrieve analysis details.');
        }
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, [id]);

  const handleRetry = async () => {
    if (isRetrying || !id) return;
    setIsRetrying(true);
    try {
      const data = await getAnalysisDetail(id);
      setAnalysis(data);
      setError(null);
    } catch (err) {
      setError(err.message || 'Unable to retrieve analysis details.');
    } finally {
      setIsRetrying(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-20 text-center space-y-4">
        <Loader2 className="w-8 h-8 text-forest-700 animate-spin mx-auto" />
        <h2 className="font-serif text-xl font-bold text-forest-950">Loading Risk Assessment...</h2>
        <p className="text-sm text-charcoal-500">Retrieving evaluation record from database storage.</p>
      </div>
    );
  }

  if (error || !analysis) {
    const isNetworkError = isNetworkOrServerError(error);

    if (isNetworkError) {
      return (
        <div className="max-w-2xl mx-auto px-4 py-16 text-center space-y-6">
          <div className="w-12 h-12 rounded-2xl bg-amber-50 text-amber-700 border border-amber-200 flex items-center justify-center mx-auto">
            <WifiOff className="w-6 h-6" />
          </div>
          <div className="space-y-2">
            <h2 className="font-serif text-2xl font-bold text-charcoal-900">
              Connection or Server Error
            </h2>
            <p className="text-sm text-charcoal-600 max-w-md mx-auto">
              {error || 'Unable to connect to the VerifAI backend server. Please verify the server is running.'}
            </p>
          </div>
          <div className="flex flex-wrap items-center justify-center gap-3">
            <button
              type="button"
              onClick={handleRetry}
              disabled={isRetrying}
              className="px-4 py-2 rounded-lg bg-forest-800 text-ivory-100 text-sm font-medium hover:bg-forest-900 transition-colors inline-flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
            >
              {isRetrying ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Retrying...</span>
                </>
              ) : (
                <>
                  <RefreshCw className="w-4 h-4" />
                  <span>Retry Analysis</span>
                </>
              )}
            </button>
            <Link
              to="/history"
              className="px-4 py-2 rounded-lg bg-ivory-200 text-charcoal-800 text-sm font-medium hover:bg-ivory-300 transition-colors"
            >
              View History
            </Link>
            <Link
              to="/analyse"
              className="px-4 py-2 rounded-lg bg-ivory-200 text-charcoal-800 text-sm font-medium hover:bg-ivory-300 transition-colors"
            >
              Analyse New Offer
            </Link>
          </div>
        </div>
      );
    }

    return (
      <div className="max-w-2xl mx-auto px-4 py-16 text-center space-y-6">
        <div className="w-12 h-12 rounded-2xl bg-rose-50 text-rose-700 border border-rose-200 flex items-center justify-center mx-auto">
          <AlertOctagon className="w-6 h-6" />
        </div>
        <div className="space-y-2">
          <h2 className="font-serif text-2xl font-bold text-charcoal-900">Record Not Found</h2>
          <p className="text-sm text-charcoal-600">
            {error || `Analysis record with ID ${id} could not be retrieved.`}
          </p>
        </div>
        <div className="flex items-center justify-center gap-3">
          <Link
            to="/analyse"
            className="px-4 py-2 rounded-lg bg-forest-800 text-ivory-100 text-sm font-medium hover:bg-forest-900 transition-colors"
          >
            Analyse New Offer
          </Link>
          <Link
            to="/history"
            className="px-4 py-2 rounded-lg bg-ivory-200 text-charcoal-800 text-sm font-medium hover:bg-ivory-300 transition-colors"
          >
            View History
          </Link>
        </div>
      </div>
    );
  }

  const {
    risk_level,
    prediction,
    model_score,
    rule_risk_score,
    detected_indicators = [],
    recommendations = [],
    disclaimer,
    submission_type,
    created_at,
    submitted_text_preview
  } = analysis;

  const formattedDate = new Date(created_at).toLocaleString('en-US', {
    dateStyle: 'medium',
    timeStyle: 'short',
  });

  // Risk presentation themes
  const riskStyles = {
    LOW: {
      bg: 'bg-emerald-50/70 border-emerald-200',
      badge: 'bg-emerald-100 text-emerald-800 border-emerald-300',
      title: 'text-emerald-950',
      desc: 'No acute predatory recruitment signals were flagged. Standard professional verification is still recommended.',
      icon: ShieldCheck,
      iconColor: 'text-emerald-700',
    },
    MODERATE: {
      bg: 'bg-amber-50/80 border-amber-200',
      badge: 'bg-amber-100 text-amber-900 border-amber-300',
      title: 'text-amber-950',
      desc: 'Ambiguous or elevated risk indicators detected. We strongly suggest thorough verification before proceeding.',
      icon: AlertTriangle,
      iconColor: 'text-amber-700',
    },
    HIGH: {
      bg: 'bg-rose-50/80 border-rose-200',
      badge: 'bg-rose-100 text-rose-900 border-rose-300',
      title: 'text-rose-950',
      desc: 'High-risk predatory patterns (e.g. upfront fee requests or guaranteed direct hiring) were identified.',
      icon: AlertOctagon,
      iconColor: 'text-rose-700',
    },
  };

  const currentRisk = riskStyles[risk_level] || riskStyles.LOW;
  const RiskIcon = currentRisk.icon;

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8 space-y-8">
      
      {/* Navigation Top Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <Link
          to="/analyse"
          className="inline-flex items-center gap-1.5 text-xs sm:text-sm font-medium text-charcoal-600 hover:text-forest-900 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Analyse Another Offer</span>
        </Link>
        <div className="flex items-center gap-2">
          <Link
            to="/history"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-ivory-200 hover:bg-ivory-300 text-charcoal-700 text-xs font-medium transition-colors border border-ivory-300"
          >
            <History className="w-3.5 h-3.5" />
            <span>Analysis History</span>
          </Link>
        </div>
      </div>

      {/* Main Banner: Overall Risk Classification */}
      <div className={`rounded-2xl border p-6 sm:p-8 ${currentRisk.bg} space-y-4 shadow-card transition-all`}>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3.5">
            <div className="w-12 h-12 rounded-2xl bg-white/90 shadow-subtle flex items-center justify-center shrink-0">
              <RiskIcon className={`w-7 h-7 ${currentRisk.iconColor}`} />
            </div>
            <div>
              <span className="text-xs uppercase tracking-wider font-semibold text-charcoal-500 font-sans">
                Composite Risk Assessment
              </span>
              <h1 className={`font-serif text-3xl font-bold ${currentRisk.title}`}>
                {risk_level} RISK OPPORTUNITY
              </h1>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <RiskBadge level={risk_level} size="lg" />
          </div>
        </div>

        <p className="text-sm sm:text-base text-charcoal-700 leading-relaxed max-w-2xl">
          {currentRisk.desc}
        </p>

        {/* Evaluation Metadata Bar */}
        <div className="pt-3 border-t border-charcoal-200/40 flex flex-wrap items-center gap-6 text-xs text-charcoal-600 font-medium">
          <div className="flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5 text-charcoal-500" />
            <span>Evaluated: {formattedDate}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <FileText className="w-3.5 h-3.5 text-charcoal-500" />
            <span>Format: {submission_type.toUpperCase()} Submission</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="font-semibold text-charcoal-800">Record ID: #{analysis.id}</span>
          </div>
        </div>
      </div>

      {/* Dual Engine Metrics Breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* ML Engine Card */}
        <div className="bg-white rounded-2xl border border-ivory-300 p-6 shadow-subtle space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-forest-50 text-forest-800 flex items-center justify-center">
                <Cpu className="w-4 h-4" />
              </div>
              <h3 className="font-serif text-lg font-bold text-forest-950">Machine Learning Classifier</h3>
            </div>
            <PredictionBadge prediction={prediction} />
          </div>

          <div className="space-y-2 pt-2">
            <div className="flex items-baseline justify-between">
              <span className="text-xs font-medium text-charcoal-600">Model Calibrated Score:</span>
              <span className="font-mono text-base font-bold text-charcoal-900">
                {(model_score * 100).toFixed(1)}%
              </span>
            </div>
            <div className="w-full bg-ivory-200 rounded-full h-2 overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-500 ${
                  model_score > 0.6 ? 'bg-rose-500' : model_score > 0.3 ? 'bg-amber-500' : 'bg-emerald-500'
                }`}
                style={{ width: `${Math.max(model_score * 100, 3)}%` }}
              />
            </div>
            <p className="text-xs text-charcoal-500 pt-1 leading-relaxed">
              Calculated by Calibrated Linear SVM (EMSCAD). Reflects empirical similarity to documented recruitment fraud patterns.
            </p>
          </div>
        </div>

        {/* Rule Engine Card */}
        <div className="bg-white rounded-2xl border border-ivory-300 p-6 shadow-subtle space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-forest-50 text-forest-800 flex items-center justify-center">
                <Layers className="w-4 h-4" />
              </div>
              <h3 className="font-serif text-lg font-bold text-forest-950">Contextual Rule Engine</h3>
            </div>
            <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-ivory-200 text-charcoal-800 border border-ivory-300">
              {detected_indicators.length} {detected_indicators.length === 1 ? 'Indicator' : 'Indicators'}
            </span>
          </div>

          <div className="space-y-2 pt-2">
            <div className="flex items-baseline justify-between">
              <span className="text-xs font-medium text-charcoal-600">Rule Risk Index:</span>
              <span className="font-mono text-base font-bold text-charcoal-900">
                {(rule_risk_score * 100).toFixed(1)}%
              </span>
            </div>
            <div className="w-full bg-ivory-200 rounded-full h-2 overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-500 ${
                  rule_risk_score > 0.5 ? 'bg-rose-500' : rule_risk_score > 0.2 ? 'bg-amber-500' : 'bg-emerald-500'
                }`}
                style={{ width: `${Math.max(rule_risk_score * 100, 3)}%` }}
              />
            </div>
            <p className="text-xs text-charcoal-500 pt-1 leading-relaxed">
              Screens for specific extortion schemes, deposits, and fee demands while suppressing legitimate disclaimers.
            </p>
          </div>
        </div>

      </div>

      {/* Identified Suspicious Indicators Section */}
      <div className="bg-white rounded-2xl border border-ivory-300 p-6 sm:p-8 shadow-card space-y-6">
        <div className="border-b border-ivory-200 pb-4">
          <h2 className="font-serif text-2xl font-bold text-forest-950">
            Detected Suspicious Indicators
          </h2>
          <p className="text-xs sm:text-sm text-charcoal-600 mt-1">
            Exact phrases and behavioral patterns extracted from the submitted material.
          </p>
        </div>

        {detected_indicators.length === 0 ? (
          <div className="py-6 px-4 rounded-xl bg-forest-50/50 border border-forest-100 flex items-start gap-3">
            <CheckCircle2 className="w-5 h-5 text-forest-600 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <h4 className="text-sm font-semibold text-forest-950">No Specific Red Flags Identified</h4>
              <p className="text-xs text-charcoal-600 leading-relaxed">
                The contextual rule engine did not detect overt upfront fee demands, deposit mandates, or interview bypasses.
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-5">
            {detected_indicators.map((ind, idx) => (
              <div
                key={idx}
                className="p-5 rounded-xl border border-ivory-300 bg-ivory-50/40 space-y-3 hover:border-forest-200 transition-colors"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="w-6 h-6 rounded-full bg-forest-100 text-forest-800 text-xs font-bold flex items-center justify-center">
                      {idx + 1}
                    </span>
                    <h4 className="font-serif font-bold text-base text-forest-950">
                      {ind.indicator_name}
                    </h4>
                  </div>
                  <span
                    className={`px-2 py-0.5 rounded text-xs font-semibold uppercase tracking-wider ${
                      ind.severity === 'CRITICAL'
                        ? 'bg-rose-100 text-rose-800 border border-rose-200'
                        : ind.severity === 'HIGH'
                        ? 'bg-amber-100 text-amber-900 border border-amber-200'
                        : 'bg-ivory-200 text-charcoal-700'
                    }`}
                  >
                    {ind.severity} Severity
                  </span>
                </div>

                <p className="text-xs sm:text-sm text-charcoal-700 leading-relaxed">
                  {ind.explanation}
                </p>

                {ind.matched_evidence && (
                  <div className="rounded-lg p-3 bg-white border border-ivory-300 text-xs text-charcoal-800 flex items-start gap-2.5">
                    <Quote className="w-4 h-4 text-forest-700 shrink-0 mt-0.5" />
                    <div>
                      <span className="font-semibold text-charcoal-900 block mb-0.5">Matched Evidence in Text:</span>
                      <span className="italic font-mono text-charcoal-700">&quot;{ind.matched_evidence}&quot;</span>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Recommended Verification Actions */}
      <div className="bg-white rounded-2xl border border-ivory-300 p-6 sm:p-8 shadow-card space-y-5">
        <div className="border-b border-ivory-200 pb-4">
          <h2 className="font-serif text-2xl font-bold text-forest-950">
            Recommended Verification Steps
          </h2>
          <p className="text-xs sm:text-sm text-charcoal-600 mt-1">
            Actionable diligence steps recommended before sharing documents or accepting the position.
          </p>
        </div>

        <ul className="space-y-3">
          {recommendations.map((rec, idx) => (
            <li key={idx} className="flex items-start gap-3 text-xs sm:text-sm text-charcoal-700">
              <span className="w-5 h-5 rounded-full bg-forest-800 text-ivory-100 text-xs font-semibold flex items-center justify-center shrink-0 mt-0.5">
                {idx + 1}
              </span>
              <span className="leading-relaxed">{rec}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Submitted Content Preview */}
      {submitted_text_preview && (
        <div className="bg-ivory-50 rounded-2xl border border-ivory-300 p-6 space-y-3">
          <h3 className="font-serif text-lg font-bold text-forest-950">Submitted Text Excerpt</h3>
          <p className="text-xs font-mono text-charcoal-700 bg-white p-4 rounded-xl border border-ivory-200 leading-relaxed whitespace-pre-wrap">
            {submitted_text_preview}
          </p>
        </div>
      )}

      {/* Mandatory Legal Disclaimer */}
      <div className="rounded-2xl p-5 bg-ivory-200 border border-ivory-300 text-xs text-charcoal-600 leading-relaxed space-y-2">
        <div className="flex items-center gap-2 font-semibold text-charcoal-900">
          <Info className="w-4 h-4 text-forest-800" />
          <span>Automated Assessment Notice</span>
        </div>
        <p>{disclaimer}</p>
      </div>

    </div>
  );
};

export default ResultsPage;

