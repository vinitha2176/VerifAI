import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FileText,
  Upload,
  AlertCircle,
  Loader2,
  Trash2,
  ArrowRight,
  Sparkles,
  CheckCircle2,
  HelpCircle,
  FileUp,
  X
} from 'lucide-react';
import { analyzeText, analyzeFile } from '../services/api';

export const AnalysePage = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('text'); // 'text' or 'pdf'
  
  // Text state
  const [textInput, setTextInput] = useState('');
  
  // File state
  const [selectedFile, setSelectedFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);

  // Submission & error state
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);
  const [errorCode, setErrorCode] = useState(null);

  // Character limits
  const MIN_CHARS = 15;
  const MAX_CHARS = 50000;
  const currentLength = textInput.length;
  const isTextValid = currentLength >= MIN_CHARS && currentLength <= MAX_CHARS;
  const isFileError = activeTab === 'pdf' && Boolean(errorMessage) && !selectedFile;
  const isUnrelatedError =
    errorCode === 'UNRELATED_DOCUMENT' ||
    errorCode === 'INSUFFICIENT_CONTENT' ||
    Boolean(errorMessage && errorMessage.includes("doesn't appear to be a job posting"));

  // Sample presets for quick testing
  const sampleLegitimate = `Senior Backend Engineer
Company: CloudScale Systems Inc.
Location: Remote / Bengaluru, India
Job Description:
We are seeking an experienced Backend Software Engineer with at least 4 years of experience in Python, FastAPI, and PostgreSQL. You will design reliable microservices, build robust REST APIs, and collaborate with our distributed engineering team.
Requirements:
- Bachelor's degree in Computer Science or equivalent practical experience.
- Strong proficiency in Python, concurrency, and database design.
- Familiarity with Docker and AWS/GCP cloud environments.
Benefits:
- Competitive base salary with annual performance review.
- Comprehensive medical insurance for candidate and dependents.
- Flexible hybrid working arrangements.
Application: Apply directly through our career portal with your resume and GitHub profile.`;

  const sampleSuspicious = `URGENT APPOINTMENT NOTIFICATION – DIRECT SELECTION
Congratulations! You have been shortlisted and appointed for the position of Home-Based Data Entry Specialist without any interview or preliminary technical screening.
Salary: Earn ₹45,000 per week working 2 hours daily from home.
Mandatory Requirements:
To confirm your seat and receive the company training laptop and formal appointment letter, all candidates are required to remit a mandatory registration fee and refundable security deposit of ₹2,500 immediately within 24 hours.
Payment must be remitted via UPI or wire transfer to our recruitment coordinator. Failure to deposit within 24 hours will result in automatic offer cancellation.`;

  const handlePasteSample = (sample) => {
    setTextInput(sample);
    setErrorMessage(null);
    setErrorCode(null);
    setActiveTab('text');
  };

  const handleClear = () => {
    setTextInput('');
    setSelectedFile(null);
    setErrorMessage(null);
    setErrorCode(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Drag and drop handlers
  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const validateAndSetFile = (file) => {
    setErrorMessage(null);
    setErrorCode(null);
    if (!file) return;

    const fileName = file.name || '';
    const hasPdfExtension = fileName.toLowerCase().endsWith('.pdf');
    const hasPdfMimeType = Boolean(file.type && file.type.toLowerCase() === 'application/pdf');

    if (!hasPdfExtension) {
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
      setErrorMessage('Unsupported file format. Please upload a standard PDF document (.pdf).');
      return;
    }

    if (!hasPdfMimeType) {
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
      setErrorMessage(
        'Invalid file type. The selected file has a .pdf extension but is not recognized as a valid PDF document (MIME type must be application/pdf).'
      );
      return;
    }

    if (file.size === 0) {
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
      setErrorMessage('The selected file is empty (0 bytes). Please upload a valid PDF document.');
      return;
    }

    const MAX_SIZE = 10 * 1024 * 1024; // 10 MB
    if (file.size > MAX_SIZE) {
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
      const mb = (file.size / (1024 * 1024)).toFixed(1);
      setErrorMessage(`File size (${mb} MB) exceeds the maximum allowed limit of 10 MB.`);
      return;
    }

    setSelectedFile(file);
    setErrorMessage(null);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    } else {
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
      setErrorMessage('No file detected. Please drag & drop a standard PDF document (.pdf).');
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  // Form submit
  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage(null);
    setErrorCode(null);

    if (activeTab === 'text') {
      if (!textInput.trim()) {
        setErrorMessage('Please paste or type the recruitment text to analyze.');
        setErrorCode(null);
        return;
      }
      if (currentLength < MIN_CHARS) {
        setErrorMessage(`Input is too short. Please provide at least ${MIN_CHARS} characters of job content.`);
        setErrorCode(null);
        return;
      }
      if (currentLength > MAX_CHARS) {
        setErrorMessage(`Input exceeds the maximum limit of ${MAX_CHARS.toLocaleString()} characters.`);
        setErrorCode(null);
        return;
      }

      setIsSubmitting(true);
      try {
        const result = await analyzeText(textInput);
        navigate(`/results/${result.id}`, { state: { result } });
      } catch (err) {
        setErrorMessage(err.message || 'Analysis failed. Please check the backend connection.');
        setErrorCode(err.code || (err.message && err.message.includes("doesn't appear to be a job posting") ? 'UNRELATED_DOCUMENT' : null));
      } finally {
        setIsSubmitting(false);
      }
    } else {
      if (!selectedFile) {
        setErrorMessage('Please select or drop a valid PDF document first.');
        setErrorCode(null);
        return;
      }

      const hasPdfExtension = Boolean(selectedFile.name && selectedFile.name.toLowerCase().endsWith('.pdf'));
      const hasPdfMimeType = Boolean(selectedFile.type && selectedFile.type.toLowerCase() === 'application/pdf');

      if (!hasPdfExtension || !hasPdfMimeType) {
        setSelectedFile(null);
        if (fileInputRef.current) fileInputRef.current.value = '';
        setErrorMessage('Invalid file type. Please upload a genuine PDF document (.pdf with MIME type application/pdf).');
        setErrorCode(null);
        return;
      }

      setIsSubmitting(true);
      try {
        const result = await analyzeFile(selectedFile);
        navigate(`/results/${result.id}`, { state: { result } });
      } catch (err) {
        setErrorMessage(err.message || 'PDF extraction and analysis failed.');
        setErrorCode(err.code || (err.message && err.message.includes("doesn't appear to be a job posting") ? 'UNRELATED_DOCUMENT' : null));
      } finally {
        setIsSubmitting(false);
      }
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8 space-y-8">
      
      {/* Header */}
      <div className="space-y-2">
        <span className="text-xs font-semibold uppercase tracking-wider text-forest-700 font-sans">
          Risk Evaluation
        </span>
        <h1 className="font-serif text-3xl sm:text-4xl font-bold text-forest-950">
          Analyse Recruitment Opportunity
        </h1>
        <p className="text-sm sm:text-base text-charcoal-600">
          Paste the job description, internship email, or upload a recruitment offer letter.
          Our dual-engine pipeline will screen for scam markers and uncalibrated risk signals.
        </p>
      </div>

      {/* Main Analysis Card */}
      <div className="bg-white rounded-2xl border border-ivory-300 shadow-card p-6 sm:p-8 space-y-6">
        
        {/* Method Toggle Tabs */}
        <div className="flex items-center gap-2 border-b border-ivory-200 pb-4">
          <button
            type="button"
            onClick={() => { setActiveTab('text'); setErrorMessage(null); setErrorCode(null); }}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeTab === 'text'
                ? 'bg-forest-800 text-ivory-100 shadow-sm'
                : 'text-charcoal-600 hover:text-charcoal-900 hover:bg-ivory-100'
            }`}
          >
            <FileText className="w-4 h-4" />
            <span>Paste Offer Text</span>
          </button>

          <button
            type="button"
            onClick={() => { setActiveTab('pdf'); setErrorMessage(null); setErrorCode(null); }}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeTab === 'pdf'
                ? 'bg-forest-800 text-ivory-100 shadow-sm'
                : 'text-charcoal-600 hover:text-charcoal-900 hover:bg-ivory-100'
            }`}
          >
            <Upload className="w-4 h-4" />
            <span>Upload PDF Document</span>
          </button>
        </div>

        {/* Input Areas */}
        <form onSubmit={handleSubmit} className="space-y-6">
          
          {activeTab === 'text' ? (
            <div className="space-y-3">
              <div className="flex items-center justify-between text-xs text-charcoal-500">
                <label htmlFor="offer-text" className="font-medium text-charcoal-800">
                  Recruitment Announcement, Email, or Offer Text
                </label>
                <span className={currentLength > MAX_CHARS ? 'text-rose-600 font-bold' : ''}>
                  {currentLength.toLocaleString()} / {MAX_CHARS.toLocaleString()} characters
                </span>
              </div>

              <textarea
                id="offer-text"
                rows={12}
                value={textInput}
                onChange={(e) => {
                  setTextInput(e.target.value);
                  if (errorMessage) {
                    setErrorMessage(null);
                    setErrorCode(null);
                  }
                }}
                placeholder="Paste the complete job description, internship announcement, or offer email here... (e.g. title, responsibilities, compensation, registration instructions)"
                className="w-full rounded-xl border border-ivory-300 bg-ivory-50/50 p-4 text-sm text-charcoal-900 placeholder:text-charcoal-400 focus:outline-none focus:ring-2 focus:ring-forest-600/20 focus:border-forest-700 transition-all font-mono leading-relaxed"
                disabled={isSubmitting}
              />

              {/* Sample loader helper buttons */}
              <div className="flex flex-wrap items-center justify-between gap-3 pt-1 text-xs">
                <span className="text-charcoal-500">Need an example to test?</span>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => handlePasteSample(sampleLegitimate)}
                    className="px-2.5 py-1 rounded-md bg-ivory-100 hover:bg-ivory-200 text-charcoal-700 border border-ivory-300 font-medium transition-colors"
                  >
                    Load Safe Example
                  </button>
                  <button
                    type="button"
                    onClick={() => handlePasteSample(sampleSuspicious)}
                    className="px-2.5 py-1 rounded-md bg-rose-50 hover:bg-rose-100 text-rose-800 border border-rose-200 font-medium transition-colors"
                  >
                    Load Scam Example
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              
              {/* PDF Dropzone */}
              <div
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all duration-150 ${
                  dragActive
                    ? 'border-forest-600 bg-forest-50/60'
                    : selectedFile
                    ? 'border-forest-400 bg-ivory-50'
                    : isFileError
                    ? 'border-rose-300 bg-rose-50/40 hover:border-rose-400 hover:bg-rose-50/60'
                    : 'border-ivory-300 bg-ivory-50/50 hover:border-forest-400 hover:bg-ivory-100/50'
                }`}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="application/pdf,.pdf"
                  onChange={handleFileChange}
                  className="hidden"
                  disabled={isSubmitting}
                />

                <div className="flex flex-col items-center justify-center space-y-3">
                  <div
                    className={`w-12 h-12 rounded-2xl flex items-center justify-center transition-colors ${
                      isFileError
                        ? 'bg-rose-100 text-rose-700'
                        : 'bg-forest-100 text-forest-800'
                    }`}
                  >
                    {isFileError ? (
                      <AlertCircle className="w-6 h-6 text-rose-600" />
                    ) : (
                      <FileUp className="w-6 h-6" />
                    )}
                  </div>
                  <div>
                    <p
                      className={`text-sm font-semibold ${
                        isFileError ? 'text-rose-900' : 'text-charcoal-900'
                      }`}
                    >
                      {selectedFile
                        ? selectedFile.name
                        : isFileError
                        ? 'Invalid File Selection'
                        : 'Click to select or drag & drop PDF document'}
                    </p>
                    <p
                      className={`text-xs mt-1 max-w-md mx-auto ${
                        isFileError ? 'text-rose-700 font-medium leading-relaxed' : 'text-charcoal-500'
                      }`}
                    >
                      {selectedFile
                        ? `${(selectedFile.size / 1024).toFixed(1)} KB • Digital PDF ready for analysis`
                        : isFileError
                        ? errorMessage
                        : 'Supports PDF offer letters or advertisements up to 10 MB'}
                    </p>
                    {isFileError && (
                      <p className="text-xs text-charcoal-500 mt-2 font-medium">
                        Click or drag &amp; drop to select a valid PDF document
                      </p>
                    )}
                  </div>
                  {selectedFile && (
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedFile(null);
                        setErrorMessage(null);
                        if (fileInputRef.current) fileInputRef.current.value = '';
                      }}
                      className="inline-flex items-center gap-1 text-xs text-rose-700 hover:text-rose-900 pt-2 font-medium"
                    >
                      <X className="w-3.5 h-3.5" /> Remove file
                    </button>
                  )}
                </div>
              </div>

              {/* PDF advisory notes */}
              <div className="rounded-xl p-3.5 bg-ivory-100 border border-ivory-300 text-xs text-charcoal-600 space-y-1">
                <p className="font-semibold text-charcoal-800 flex items-center gap-1.5">
                  <HelpCircle className="w-3.5 h-3.5 text-forest-700" />
                  PDF Requirements & Limitations
                </p>
                <p>
                  Documents must contain digital, selectable text. Scanned or image-only PDFs require OCR, which is not
                  supported in this phase.
                </p>
              </div>

            </div>
          )}

          {/* Error Message Box */}
          {errorMessage && (
            <div
              className={`rounded-xl p-4 border text-xs sm:text-sm flex items-start gap-3 animate-fade-in ${
                isUnrelatedError
                  ? 'bg-amber-50 border-amber-200 text-amber-900'
                  : 'bg-rose-50 border-rose-200 text-rose-800'
              }`}
            >
              <AlertCircle
                className={`w-5 h-5 shrink-0 mt-0.5 ${
                  isUnrelatedError ? 'text-amber-600' : 'text-rose-600'
                }`}
              />
              <div className="space-y-1">
                <span className="font-semibold">
                  {isFileError
                    ? 'PDF Validation Error'
                    : isUnrelatedError
                    ? 'Content Relevance Notice'
                    : 'Analysis Failed'}
                </span>
                <p className="leading-relaxed">{errorMessage}</p>
              </div>
            </div>
          )}

          {/* Form Actions */}
          <div className="pt-2 flex flex-col-reverse sm:flex-row items-center justify-between gap-4">
            
            <button
              type="button"
              onClick={handleClear}
              disabled={isSubmitting || (!textInput && !selectedFile)}
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium text-charcoal-600 hover:text-charcoal-900 hover:bg-ivory-100 border border-ivory-300 transition-colors disabled:opacity-40 disabled:pointer-events-none"
            >
              <Trash2 className="w-4 h-4" />
              <span>Clear Input</span>
            </button>

            <button
              type="submit"
              disabled={isSubmitting || (activeTab === 'text' && !isTextValid) || (activeTab === 'pdf' && !selectedFile)}
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-7 py-3 rounded-xl bg-forest-800 text-ivory-100 font-medium text-sm hover:bg-forest-900 shadow-card hover:shadow-elevated transition-all disabled:opacity-50 disabled:pointer-events-none"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Screening Content...</span>
                </>
              ) : (
                <>
                  <span>Analyse Offer</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>

          </div>

        </form>

      </div>

    </div>
  );
};

export default AnalysePage;

