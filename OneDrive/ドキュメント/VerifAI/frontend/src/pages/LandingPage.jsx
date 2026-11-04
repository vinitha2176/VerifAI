import React from 'react';
import { Link } from 'react-router-dom';
import {
  Shield,
  FileSearch,
  CheckCircle,
  AlertTriangle,
  ArrowRight,
  Lock,
  Cpu,
  FileText,
  HelpCircle,
  Sparkles,
  Info
} from 'lucide-react';

export const LandingPage = () => {
  return (
    <div className="space-y-24 sm:space-y-32 py-6 sm:py-12">
      
      {/* Hero Section */}
      <section className="max-w-4xl mx-auto px-4 sm:px-6 text-center space-y-8">
        
        {/* Subtle pill banner */}
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-forest-50 border border-forest-200 text-forest-800 text-xs font-medium tracking-wide">
          <span className="w-2 h-2 rounded-full bg-forest-600 animate-pulse" />
          <span>VerifAI Platform • Neural Storm Hackathon</span>
        </div>

        {/* Hero Title */}
        <div className="space-y-4">
          <h1 className="font-serif text-4xl sm:text-6xl font-bold text-forest-950 tracking-tight leading-[1.15]">
            Verify opportunities. <br className="hidden sm:inline" />
            <span className="italic font-normal text-forest-700">Protect your future.</span>
          </h1>
          <p className="max-w-2xl mx-auto text-base sm:text-lg text-charcoal-600 leading-relaxed">
            Every year, thousands of students and job seekers fall victim to fake job advertisements,
            predatory training fees, and counterfeit offer letters. VerifAI provides transparent,
            explainable AI risk assessments to help you detect recruitment traps before sending money or private data.
          </p>
        </div>

        {/* Action CTAs */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-2">
          <Link
            to="/analyse"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl bg-forest-800 text-ivory-100 font-medium text-base hover:bg-forest-900 shadow-card hover:shadow-elevated transition-all"
          >
            <span>Analyse an Offer</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
          <a
            href="#how-it-works"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl bg-ivory-200 text-charcoal-800 font-medium text-base hover:bg-ivory-300 border border-ivory-300 transition-all"
          >
            <span>Explore How It Works</span>
          </a>
        </div>

        {/* Trust Badges */}
        <div className="pt-6 flex flex-wrap items-center justify-center gap-6 text-xs text-charcoal-500 font-medium">
          <div className="flex items-center gap-1.5">
            <CheckCircle className="w-4 h-4 text-forest-600" />
            <span>Trained on 15,849 EMSCAD Postings</span>
          </div>
          <div className="flex items-center gap-1.5">
            <CheckCircle className="w-4 h-4 text-forest-600" />
            <span>Context-Aware Negation Handling</span>
          </div>
          <div className="flex items-center gap-1.5">
            <CheckCircle className="w-4 h-4 text-forest-600" />
            <span>Privacy-Preserving SQLite Storage</span>
          </div>
        </div>

      </section>

      {/* 3-Step Process Section */}
      <section id="how-it-works" className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="text-center space-y-3 mb-16">
          <span className="text-xs font-semibold uppercase tracking-wider text-forest-700 font-sans">
            Methodology
          </span>
          <h2 className="font-serif text-3xl sm:text-4xl font-bold text-forest-950">
            How VerifAI Evaluates Recruitment Offers
          </h2>
          <p className="text-sm sm:text-base text-charcoal-600 max-w-xl mx-auto">
            A three-tier hybrid pipeline combining statistical machine learning with deterministic pattern audits.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          
          {/* Step 1 */}
          <div className="bg-white rounded-2xl p-7 border border-ivory-300 shadow-subtle hover:shadow-card transition-all space-y-4 relative">
            <div className="w-10 h-10 rounded-xl bg-forest-50 text-forest-800 font-serif font-bold text-lg flex items-center justify-center border border-forest-100">
              01
            </div>
            <h3 className="font-serif text-xl font-bold text-forest-950">
              Submit Offer Content
            </h3>
            <p className="text-sm text-charcoal-600 leading-relaxed">
              Paste the job description, internship email, or upload the recruitment document in PDF format.
              PyMuPDF parses digital documents safely in memory without permanent file retention.
            </p>
          </div>

          {/* Step 2 */}
          <div className="bg-white rounded-2xl p-7 border border-ivory-300 shadow-subtle hover:shadow-card transition-all space-y-4 relative">
            <div className="w-10 h-10 rounded-xl bg-forest-50 text-forest-800 font-serif font-bold text-lg flex items-center justify-center border border-forest-100">
              02
            </div>
            <h3 className="font-serif text-xl font-bold text-forest-950">
              Dual-Engine AI Inspection
            </h3>
            <p className="text-sm text-charcoal-600 leading-relaxed">
              Our Calibrated Linear SVM model computes an empirical scam risk probability, while an independent
              10-rule engine inspects the text for fee demands, security deposits, and interview skips.
            </p>
          </div>

          {/* Step 3 */}
          <div className="bg-white rounded-2xl p-7 border border-ivory-300 shadow-subtle hover:shadow-card transition-all space-y-4 relative">
            <div className="w-10 h-10 rounded-xl bg-forest-50 text-forest-800 font-serif font-bold text-lg flex items-center justify-center border border-forest-100">
              03
            </div>
            <h3 className="font-serif text-xl font-bold text-forest-950">
              Explainable Risk Report
            </h3>
            <p className="text-sm text-charcoal-600 leading-relaxed">
              Review a transparent risk classification (Low, Moderate, High) with exact matched evidence sentences,
              rule explanations, and practical verification steps before you take action.
            </p>
          </div>

        </div>
      </section>

      {/* Key Features Grid */}
      <section className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="text-center space-y-3 mb-16">
          <span className="text-xs font-semibold uppercase tracking-wider text-forest-700 font-sans">
            Capabilities
          </span>
          <h2 className="font-serif text-3xl sm:text-4xl font-bold text-forest-950">
            Engineered for Accuracy and Transparency
          </h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          
          <div className="bg-ivory-50 rounded-2xl p-6 border border-ivory-300 space-y-3">
            <div className="w-9 h-9 rounded-lg bg-forest-800 text-ivory-100 flex items-center justify-center">
              <Cpu className="w-4 h-4" />
            </div>
            <h4 className="font-serif text-lg font-bold text-forest-950">Genuine Machine Learning</h4>
            <p className="text-xs sm:text-sm text-charcoal-600 leading-relaxed">
              Powered by TF-IDF vectorization and a calibrated Support Vector Machine trained on thousands of authentic
              and fraudulent job notices. No mock scores or fabricated predictions.
            </p>
          </div>

          <div className="bg-ivory-50 rounded-2xl p-6 border border-ivory-300 space-y-3">
            <div className="w-9 h-9 rounded-lg bg-forest-800 text-ivory-100 flex items-center justify-center">
              <FileSearch className="w-4 h-4" />
            </div>
            <h4 className="font-serif text-lg font-bold text-forest-950">Context & Negation Handling</h4>
            <p className="text-xs sm:text-sm text-charcoal-600 leading-relaxed">
              Differentiates between predatory demands (&quot;pay ₹2,500 registration fee&quot;) and legitimate
              disclaimers (&quot;there is no registration fee&quot;) to avoid false alarms.
            </p>
          </div>

          <div className="bg-ivory-50 rounded-2xl p-6 border border-ivory-300 space-y-3">
            <div className="w-9 h-9 rounded-lg bg-forest-800 text-ivory-100 flex items-center justify-center">
              <FileText className="w-4 h-4" />
            </div>
            <h4 className="font-serif text-lg font-bold text-forest-950">Digital PDF Extraction</h4>
            <p className="text-xs sm:text-sm text-charcoal-600 leading-relaxed">
              Supports offer letters and PDF advertisements up to 10 MB. Validates magic file headers and notifies
              users if scanned documents require digital text conversion.
            </p>
          </div>

          <div className="bg-ivory-50 rounded-2xl p-6 border border-ivory-300 space-y-3">
            <div className="w-9 h-9 rounded-lg bg-forest-800 text-ivory-100 flex items-center justify-center">
              <Sparkles className="w-4 h-4" />
            </div>
            <h4 className="font-serif text-lg font-bold text-forest-950">Explainable Findings</h4>
            <p className="text-xs sm:text-sm text-charcoal-600 leading-relaxed">
              Every flag links to the exact sentence from your document with an explanation of why that behavior
              constitutes a high-risk employment practice.
            </p>
          </div>

          <div className="bg-ivory-50 rounded-2xl p-6 border border-ivory-300 space-y-3">
            <div className="w-9 h-9 rounded-lg bg-forest-800 text-ivory-100 flex items-center justify-center">
              <Lock className="w-4 h-4" />
            </div>
            <h4 className="font-serif text-lg font-bold text-forest-950">Privacy-First Architecture</h4>
            <p className="text-xs sm:text-sm text-charcoal-600 leading-relaxed">
              Submitted offers are saved only with a truncated preview and SHA-256 cryptographic digest. Uploaded PDF
              files are parsed in memory and never permanently written to server disks.
            </p>
          </div>

          <div className="bg-ivory-50 rounded-2xl p-6 border border-ivory-300 space-y-3">
            <div className="w-9 h-9 rounded-lg bg-forest-800 text-ivory-100 flex items-center justify-center">
              <Info className="w-4 h-4" />
            </div>
            <h4 className="font-serif text-lg font-bold text-forest-950">Actionable Guidance</h4>
            <p className="text-xs sm:text-sm text-charcoal-600 leading-relaxed">
              Provides tailored next steps—such as cross-referencing corporate domain records or contacting official HR
              portals—instead of simply returning an ambiguous percentage score.
            </p>
          </div>

        </div>
      </section>

      {/* Why Independent Verification Matters */}
      <section className="max-w-4xl mx-auto px-4 sm:px-6">
        <div className="bg-forest-900 text-ivory-100 rounded-3xl p-8 sm:p-12 shadow-elevated space-y-6">
          <span className="text-xs font-semibold uppercase tracking-widest text-forest-300">
            Advisory Insight
          </span>
          <h2 className="font-serif text-3xl sm:text-4xl font-bold leading-tight">
            Why Independent Verification Matters
          </h2>
          <p className="text-sm sm:text-base text-forest-100 leading-relaxed">
            Sophisticated recruitment scams often utilize genuine company logos, official-looking letterheads,
            and convincingly formatted offer templates. Many impersonate reputable multinational enterprises
            or emerging startups.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
            <div className="p-4 rounded-xl bg-forest-800/60 border border-forest-700/60 space-y-1.5">
              <h5 className="font-bold text-sm text-ivory-100">Never Pay to Work</h5>
              <p className="text-xs text-forest-200 leading-normal">
                Legitimate employers never demand application fees, onboarding deposits, or software kit purchases.
              </p>
            </div>
            <div className="p-4 rounded-xl bg-forest-800/60 border border-forest-700/60 space-y-1.5">
              <h5 className="font-bold text-sm text-ivory-100">Verify Official Domains</h5>
              <p className="text-xs text-forest-200 leading-normal">
                Watch out for recruiters communicating exclusively via personal Telegram handles or public free webmail.
              </p>
            </div>
          </div>
          <div className="pt-4">
            <Link
              to="/analyse"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-ivory-100 text-forest-950 font-semibold text-sm hover:bg-white transition-colors"
            >
              <span>Test an Offer Notice Now</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>

    </div>
  );
};

export default LandingPage;

