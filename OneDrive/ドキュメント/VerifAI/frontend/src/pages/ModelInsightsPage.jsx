import React, { useState, useEffect } from 'react';
import {
  Cpu,
  BarChart3,
  AlertTriangle,
  Info,
  CheckCircle2,
  ExternalLink,
  BookOpen,
  Loader2,
  ShieldAlert,
  Layers,
  Sparkles
} from 'lucide-react';
import { getModelMetrics } from '../services/api';

export const ModelInsightsPage = () => {
  const [metricsData, setMetricsData] = useState(null);
  const [status, setStatus] = useState('loading'); // 'loading', 'available', 'unavailable', 'error'
  const [errorMessage, setErrorMessage] = useState(null);

  useEffect(() => {
    let mounted = true;
    getModelMetrics()
      .then((res) => {
        if (mounted) {
          if (res.status === 'available' && res.metrics) {
            setMetricsData(res.metrics);
            setStatus('available');
          } else {
            setStatus('unavailable');
          }
        }
      })
      .catch((err) => {
        if (mounted) {
          setErrorMessage(err.message || 'Failed to fetch metrics from server.');
          setStatus('error');
        }
      });

    return () => {
      mounted = false;
    };
  }, []);

  // Reference fallbacks strictly for UI context if metrics file was deleted or loading
  const metrics = metricsData || {
    accuracy: 0.9836,
    precision: 0.9018,
    recall: 0.7113,
    f1_score: 0.7953,
    pr_auc: 0.8787,
    confusion_matrix: {
      true_negatives: 3017,
      false_positives: 11,
      false_negatives: 41,
      true_positives: 101,
    },
    total_test_samples: 3170,
    fraudulent_samples: 142,
    legitimate_samples: 3028,
    model_name: 'TF-IDF + CalibratedLinearSVM (Balanced)',
  };

  const cm = metrics.confusion_matrix || {
    true_negatives: 3017,
    false_positives: 11,
    false_negatives: 41,
    true_positives: 101,
  };

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8 space-y-12">
      
      {/* Page Header */}
      <div className="space-y-3 max-w-3xl">
        <span className="text-xs font-semibold uppercase tracking-wider text-forest-700 font-sans">
          Technical Transparency
        </span>
        <h1 className="font-serif text-3xl sm:text-4xl font-bold text-forest-950">
          Model Insights & Benchmark Metrics
        </h1>
        <p className="text-sm sm:text-base text-charcoal-600 leading-relaxed">
          VerifAI prioritizes empirical validation over black-box claims. The figures below reflect the genuine
          held-out test set performance of our serialized production pipeline evaluated against untouched samples.
        </p>

        {status === 'available' && (
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-50 text-emerald-800 text-xs font-medium border border-emerald-200">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            <span>Live metrics loaded directly from backend metrics.json</span>
          </div>
        )}

        {status === 'unavailable' && (
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-50 text-amber-800 text-xs font-medium border border-amber-200">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
            <span>Backend reported metrics file not found. Displaying documented validation baseline.</span>
          </div>
        )}
      </div>

      {/* Top Level Metric Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        
        <div className="bg-white rounded-2xl border border-ivory-300 p-5 shadow-subtle space-y-2">
          <span className="text-xs font-medium text-charcoal-500 uppercase tracking-wider block">
            Accuracy
          </span>
          <div className="font-serif text-3xl font-bold text-forest-950">
            {(metrics.accuracy * 100).toFixed(2)}%
          </div>
          <p className="text-[11px] text-charcoal-500 leading-normal">
            Overall correct predictions across both classes.
          </p>
        </div>

        <div className="bg-white rounded-2xl border border-ivory-300 p-5 shadow-subtle space-y-2">
          <span className="text-xs font-medium text-charcoal-500 uppercase tracking-wider block">
            Precision
          </span>
          <div className="font-serif text-3xl font-bold text-forest-950">
            {(metrics.precision * 100).toFixed(2)}%
          </div>
          <p className="text-[11px] text-charcoal-500 leading-normal">
            Low false-alarm rate when flagging suspicious jobs.
          </p>
        </div>

        <div className="bg-white rounded-2xl border border-ivory-300 p-5 shadow-subtle space-y-2">
          <span className="text-xs font-medium text-charcoal-500 uppercase tracking-wider block">
            Recall
          </span>
          <div className="font-serif text-3xl font-bold text-forest-950">
            {(metrics.recall * 100).toFixed(2)}%
          </div>
          <p className="text-[11px] text-charcoal-500 leading-normal">
            Percentage of actual scam offers captured.
          </p>
        </div>

        <div className="bg-white rounded-2xl border border-ivory-300 p-5 shadow-subtle space-y-2">
          <span className="text-xs font-medium text-charcoal-500 uppercase tracking-wider block">
            F1-Score
          </span>
          <div className="font-serif text-3xl font-bold text-forest-950">
            {(metrics.f1_score * 100).toFixed(2)}%
          </div>
          <p className="text-[11px] text-charcoal-500 leading-normal">
            Harmonic balance of precision and recall.
          </p>
        </div>

        <div className="col-span-2 md:col-span-1 bg-white rounded-2xl border border-ivory-300 p-5 shadow-subtle space-y-2">
          <span className="text-xs font-medium text-charcoal-500 uppercase tracking-wider block">
            PR-AUC
          </span>
          <div className="font-serif text-3xl font-bold text-forest-950">
            {(metrics.pr_auc * 100).toFixed(2)}%
          </div>
          <p className="text-[11px] text-charcoal-500 leading-normal">
            Area under Precision-Recall curve under class imbalance.
          </p>
        </div>

      </div>

      {/* Confusion Matrix & Breakdown Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
        
        {/* Confusion Matrix Card */}
        <div className="bg-white rounded-2xl border border-ivory-300 p-6 sm:p-8 shadow-card space-y-6">
          <div className="border-b border-ivory-200 pb-4">
            <h3 className="font-serif text-xl font-bold text-forest-950 flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-forest-700" />
              <span>Held-Out Confusion Matrix</span>
            </h3>
            <p className="text-xs text-charcoal-600 mt-1">
              Evaluated on 3,170 unseen test split samples (3,028 Legitimate, 142 Fraudulent).
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            
            {/* True Negatives */}
            <div className="p-4 rounded-xl bg-emerald-50/70 border border-emerald-200 space-y-1 text-center">
              <span className="text-xs font-semibold text-emerald-900 uppercase tracking-wider">
                True Negatives (TN)
              </span>
              <div className="font-mono text-3xl font-bold text-emerald-950">
                {cm.true_negatives.toLocaleString()}
              </div>
              <p className="text-[11px] text-emerald-800">
                Correctly identified legitimate jobs
              </p>
            </div>

            {/* False Positives */}
            <div className="p-4 rounded-xl bg-amber-50/70 border border-amber-200 space-y-1 text-center">
              <span className="text-xs font-semibold text-amber-900 uppercase tracking-wider">
                False Positives (FP)
              </span>
              <div className="font-mono text-3xl font-bold text-amber-950">
                {cm.false_positives.toLocaleString()}
              </div>
              <p className="text-[11px] text-amber-800">
                Legitimate jobs flagged as scam (0.36%)
              </p>
            </div>

            {/* False Negatives */}
            <div className="p-4 rounded-xl bg-rose-50/70 border border-rose-200 space-y-1 text-center">
              <span className="text-xs font-semibold text-rose-900 uppercase tracking-wider">
                False Negatives (FN)
              </span>
              <div className="font-mono text-3xl font-bold text-rose-950">
                {cm.false_negatives.toLocaleString()}
              </div>
              <p className="text-[11px] text-rose-800">
                Fraudulent jobs missed by ML model
              </p>
            </div>

            {/* True Positives */}
            <div className="p-4 rounded-xl bg-forest-50 border border-forest-200 space-y-1 text-center">
              <span className="text-xs font-semibold text-forest-900 uppercase tracking-wider">
                True Positives (TP)
              </span>
              <div className="font-mono text-3xl font-bold text-forest-950">
                {cm.true_positives.toLocaleString()}
              </div>
              <p className="text-[11px] text-forest-800">
                Correctly caught scam job offers
              </p>
            </div>

          </div>

          <div className="text-xs text-charcoal-600 bg-ivory-50 p-4 rounded-xl border border-ivory-200 space-y-1">
            <span className="font-semibold text-charcoal-800">Interpretation Note:</span>
            <p>
              The model produces remarkably few false positives (only 11 out of 3,028 legitimate jobs were misclassified),
              preventing excessive friction for candidates reviewing standard job ads.
            </p>
          </div>
        </div>

        {/* Dataset Information Card */}
        <div className="bg-white rounded-2xl border border-ivory-300 p-6 sm:p-8 shadow-card space-y-6">
          <div className="border-b border-ivory-200 pb-4">
            <h3 className="font-serif text-xl font-bold text-forest-950 flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-forest-700" />
              <span>Dataset Provenance</span>
            </h3>
            <p className="text-xs text-charcoal-600 mt-1">
              Employment Scam Aegean Dataset (EMSCAD).
            </p>
          </div>

          <div className="space-y-4 text-xs sm:text-sm text-charcoal-700 leading-relaxed">
            <p>
              VerifAI was trained using the published <strong>EMSCAD dataset</strong>, collected by researchers at the
              University of the Aegean. It contains genuine employment announcements with verified real-world ground truth.
            </p>

            <div className="grid grid-cols-2 gap-3 pt-1">
              <div className="p-3 rounded-lg bg-ivory-100 border border-ivory-200">
                <span className="text-[11px] font-semibold text-charcoal-500 uppercase block">Raw Postings</span>
                <span className="font-mono text-base font-bold text-charcoal-900">17,880 rows</span>
              </div>
              <div className="p-3 rounded-lg bg-ivory-100 border border-ivory-200">
                <span className="text-[11px] font-semibold text-charcoal-500 uppercase block">Deduplicated Corpus</span>
                <span className="font-mono text-base font-bold text-charcoal-900">15,849 unique</span>
              </div>
              <div className="p-3 rounded-lg bg-ivory-100 border border-ivory-200">
                <span className="text-[11px] font-semibold text-charcoal-500 uppercase block">Legitimate Samples</span>
                <span className="font-mono text-base font-bold text-charcoal-900">15,139 (95.5%)</span>
              </div>
              <div className="p-3 rounded-lg bg-ivory-100 border border-ivory-200">
                <span className="text-[11px] font-semibold text-charcoal-500 uppercase block">Fraudulent Samples</span>
                <span className="font-mono text-base font-bold text-charcoal-900">710 (4.5%)</span>
              </div>
            </div>

            <div className="pt-2">
              <a
                href="https://www.mdpi.com/1999-5903/9/1/6"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 text-forest-800 font-semibold hover:underline"
              >
                <span>Read the Research Paper: MDPI Future Internet (2017)</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            </div>
          </div>
        </div>

      </div>

      {/* Honest Limitations Section */}
      <div className="bg-ivory-200 rounded-3xl p-6 sm:p-10 border border-ivory-300 space-y-6">
        <div className="flex items-center gap-2.5 text-forest-900">
          <ShieldAlert className="w-6 h-6 text-forest-800" />
          <h2 className="font-serif text-2xl font-bold">Model Limitations & Boundary Conditions</h2>
        </div>

        <p className="text-xs sm:text-sm text-charcoal-700 leading-relaxed">
          VerifAI does not claim perfection. Understanding the boundaries of the machine learning classifier
          is essential for safe and responsible recruitment screening:
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          
          <div className="p-5 rounded-2xl bg-white border border-ivory-300 space-y-2">
            <h4 className="font-serif font-bold text-sm text-charcoal-950">
              Historical & International Origin
            </h4>
            <p className="text-xs text-charcoal-600 leading-relaxed">
              EMSCAD was constructed primarily from international job boards between 2012 and 2014. Contemporary
              recruitment fraud patterns in India (e.g. UPI QR code advances, Telegram assignment tasks, or
              fake internships) may employ phrasing differing from historical training patterns.
            </p>
          </div>

          <div className="p-5 rounded-2xl bg-white border border-ivory-300 space-y-2">
            <h4 className="font-serif font-bold text-charcoal-950 text-sm">
              Known False Negatives (Recall ~71%)
            </h4>
            <p className="text-xs text-charcoal-600 leading-relaxed">
              In test evaluation, 41 fraudulent offers out of 142 were not caught by the statistical model alone.
              This is precisely why VerifAI pairs ML with a deterministic rule engine and insists on human verification.
            </p>
          </div>

          <div className="p-5 rounded-2xl bg-white border border-ivory-300 space-y-2">
            <h4 className="font-serif font-bold text-charcoal-950 text-sm">
              Automated Analysis Is Not Proof
            </h4>
            <p className="text-xs text-charcoal-600 leading-relaxed">
              A high-risk score indicates structural patterns commonly associated with scams. It does not establish
              conclusive legal proof of fraud. Candidates should independently verify corporate registration.
            </p>
          </div>

        </div>
      </div>

    </div>
  );
};

export default ModelInsightsPage;

