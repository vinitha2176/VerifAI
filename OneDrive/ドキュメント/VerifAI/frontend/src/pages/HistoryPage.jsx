import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  History,
  Trash2,
  ExternalLink,
  RefreshCw,
  Loader2,
  AlertCircle,
  FileText,
  Clock,
  ArrowRight,
  Shield,
  Layers
} from 'lucide-react';
import { getHistory, deleteAnalysis } from '../services/api';
import { RiskBadge, PredictionBadge } from '../components/RiskBadge';

export const HistoryPage = () => {
  const [historyItems, setHistoryItems] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [limit] = useState(15);
  const [offset, setOffset] = useState(0);
  
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  // Deletion modal state
  const [recordToDelete, setRecordToDelete] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState(null);

  const fetchHistory = async (currentOffset = offset, isBackground = false) => {
    if (!isBackground) setLoading(true);
    else setRefreshing(true);
    setError(null);

    try {
      const data = await getHistory(limit, currentOffset);
      setHistoryItems(data.items || []);
      setTotalCount(data.total || 0);
    } catch (err) {
      setError(err.message || 'Failed to load analysis history.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchHistory(offset);
  }, [offset]);

  const handleDeleteConfirm = async () => {
    if (!recordToDelete) return;
    setIsDeleting(true);
    setDeleteError(null);

    try {
      await deleteAnalysis(recordToDelete.id);
      setRecordToDelete(null);
      // Reload history
      await fetchHistory(offset, true);
    } catch (err) {
      setDeleteError(err.message || 'Failed to delete record.');
    } finally {
      setIsDeleting(false);
    }
  };

  const totalPages = Math.ceil(totalCount / limit);
  const currentPage = Math.floor(offset / limit) + 1;

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8 space-y-8">
      
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-ivory-300 pb-6">
        <div className="space-y-1">
          <span className="text-xs font-semibold uppercase tracking-wider text-forest-700 font-sans">
            Audit Ledger
          </span>
          <h1 className="font-serif text-3xl sm:text-4xl font-bold text-forest-950">
            Analysis History
          </h1>
          <p className="text-xs sm:text-sm text-charcoal-600">
            All previously evaluated recruitment offers and offer letters stored in SQLite.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => fetchHistory(offset, true)}
            disabled={refreshing || loading}
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-ivory-200 hover:bg-ivory-300 text-charcoal-800 text-xs font-medium border border-ivory-300 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
          <Link
            to="/analyse"
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-forest-800 hover:bg-forest-900 text-ivory-100 text-xs font-medium transition-colors shadow-sm"
          >
            <span>New Analysis</span>
          </Link>
        </div>
      </div>

      {/* Loading state */}
      {loading ? (
        <div className="py-24 text-center space-y-4">
          <Loader2 className="w-8 h-8 text-forest-700 animate-spin mx-auto" />
          <h3 className="font-serif text-lg font-bold text-forest-950">Loading History Records...</h3>
          <p className="text-xs text-charcoal-500">Querying SQLite database...</p>
        </div>
      ) : error ? (
        <div className="p-8 rounded-2xl bg-rose-50 border border-rose-200 text-center space-y-4 max-w-xl mx-auto">
          <AlertCircle className="w-8 h-8 text-rose-600 mx-auto" />
          <div className="space-y-1">
            <h3 className="font-serif text-lg font-bold text-rose-950">Could Not Load History</h3>
            <p className="text-xs text-rose-800">{error}</p>
          </div>
          <button
            type="button"
            onClick={() => fetchHistory(offset)}
            className="px-4 py-2 rounded-lg bg-rose-700 text-white text-xs font-medium hover:bg-rose-800"
          >
            Try Again
          </button>
        </div>
      ) : historyItems.length === 0 ? (
        <div className="bg-white rounded-2xl border border-ivory-300 p-12 text-center space-y-5 max-w-lg mx-auto shadow-subtle">
          <div className="w-12 h-12 rounded-2xl bg-ivory-200 text-charcoal-600 flex items-center justify-center mx-auto">
            <History className="w-6 h-6" />
          </div>
          <div className="space-y-2">
            <h3 className="font-serif text-xl font-bold text-forest-950">No Analyses Recorded Yet</h3>
            <p className="text-xs text-charcoal-600 leading-relaxed">
              When you evaluate job advertisements or offer letters, your assessment results and evidence
              will appear here for future reference.
            </p>
          </div>
          <Link
            to="/analyse"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-forest-800 text-ivory-100 text-sm font-medium hover:bg-forest-900 transition-colors"
          >
            <span>Analyse Your First Offer</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          
          {/* Table Container */}
          <div className="bg-white rounded-2xl border border-ivory-300 shadow-card overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs sm:text-sm">
                
                <thead className="bg-ivory-50 border-b border-ivory-300 text-charcoal-700 font-semibold uppercase tracking-wider text-[11px]">
                  <tr>
                    <th scope="col" className="px-6 py-3.5">ID / Date</th>
                    <th scope="col" className="px-6 py-3.5">Type & Preview</th>
                    <th scope="col" className="px-6 py-3.5">Risk Level</th>
                    <th scope="col" className="px-6 py-3.5">ML Prediction</th>
                    <th scope="col" className="px-6 py-3.5 text-center">Indicators</th>
                    <th scope="col" className="px-6 py-3.5 text-right">Actions</th>
                  </tr>
                </thead>

                <tbody className="divide-y divide-ivory-200 text-charcoal-800">
                  {historyItems.map((item) => {
                    const formattedDate = new Date(item.created_at).toLocaleDateString('en-US', {
                      month: 'short',
                      day: 'numeric',
                      year: 'numeric',
                    });
                    const formattedTime = new Date(item.created_at).toLocaleTimeString('en-US', {
                      hour: '2-digit',
                      minute: '2-digit',
                    });

                    return (
                      <tr key={item.id} className="hover:bg-ivory-50/60 transition-colors">
                        
                        {/* ID and Date */}
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="font-mono font-semibold text-charcoal-900">#{item.id}</div>
                          <div className="text-xs text-charcoal-500 flex items-center gap-1 mt-0.5">
                            <Clock className="w-3 h-3" />
                            <span>{formattedDate} {formattedTime}</span>
                          </div>
                        </td>

                        {/* Text Preview */}
                        <td className="px-6 py-4 max-w-xs">
                          <div className="flex items-center gap-1.5 text-xs text-forest-800 font-medium mb-1">
                            <span className="uppercase tracking-wider px-1.5 py-0.5 bg-ivory-200 rounded text-[10px]">
                              {item.submission_type}
                            </span>
                          </div>
                          <p className="text-xs text-charcoal-600 line-clamp-2 font-mono">
                            {item.submitted_text_preview}
                          </p>
                        </td>

                        {/* Risk Level */}
                        <td className="px-6 py-4 whitespace-nowrap">
                          <RiskBadge level={item.risk_level} size="sm" />
                        </td>

                        {/* ML Prediction */}
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="space-y-1">
                            <PredictionBadge prediction={item.prediction} />
                            <div className="text-[11px] text-charcoal-500 font-mono">
                              Score: {(item.model_score * 100).toFixed(0)}%
                            </div>
                          </div>
                        </td>

                        {/* Indicators count */}
                        <td className="px-6 py-4 whitespace-nowrap text-center">
                          <span
                            className={`inline-block px-2.5 py-1 rounded-full text-xs font-semibold ${
                              item.indicator_count > 0
                                ? 'bg-amber-100 text-amber-900 border border-amber-200'
                                : 'bg-ivory-100 text-charcoal-600'
                            }`}
                          >
                            {item.indicator_count}
                          </span>
                        </td>

                        {/* Actions */}
                        <td className="px-6 py-4 whitespace-nowrap text-right space-x-2">
                          <Link
                            to={`/results/${item.id}`}
                            className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-ivory-100 hover:bg-forest-800 hover:text-ivory-100 text-charcoal-800 font-medium text-xs border border-ivory-300 transition-colors"
                          >
                            <span>View</span>
                            <ExternalLink className="w-3 h-3" />
                          </Link>

                          <button
                            type="button"
                            onClick={() => setRecordToDelete(item)}
                            className="inline-flex items-center justify-center p-1.5 rounded-lg text-charcoal-400 hover:text-rose-700 hover:bg-rose-50 transition-colors"
                            title="Delete this analysis record"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </td>

                      </tr>
                    );
                  })}
                </tbody>

              </table>
            </div>

            {/* Pagination Controls */}
            {totalPages > 1 && (
              <div className="px-6 py-4 border-t border-ivory-300 bg-ivory-50 flex items-center justify-between text-xs text-charcoal-600">
                <span>
                  Showing {offset + 1}–{Math.min(offset + limit, totalCount)} of {totalCount} records
                </span>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    disabled={offset === 0}
                    onClick={() => setOffset(Math.max(0, offset - limit))}
                    className="px-3 py-1.5 rounded-md bg-white border border-ivory-300 font-medium disabled:opacity-40 disabled:pointer-events-none hover:bg-ivory-100 transition-colors"
                  >
                    Previous
                  </button>
                  <span className="font-semibold text-charcoal-900">
                    Page {currentPage} of {totalPages}
                  </span>
                  <button
                    type="button"
                    disabled={offset + limit >= totalCount}
                    onClick={() => setOffset(offset + limit)}
                    className="px-3 py-1.5 rounded-md bg-white border border-ivory-300 font-medium disabled:opacity-40 disabled:pointer-events-none hover:bg-ivory-100 transition-colors"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}

          </div>

        </div>
      )}

      {/* Delete Confirmation Modal */}
      {recordToDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-charcoal-950/40 backdrop-blur-sm animate-fade-in">
          <div className="bg-white rounded-2xl border border-ivory-300 p-6 max-w-md w-full shadow-elevated space-y-4">
            <div className="flex items-center gap-3 text-rose-700">
              <div className="w-10 h-10 rounded-xl bg-rose-50 flex items-center justify-center border border-rose-200">
                <Trash2 className="w-5 h-5" />
              </div>
              <h3 className="font-serif text-lg font-bold text-charcoal-950">
                Delete Analysis #{recordToDelete.id}?
              </h3>
            </div>

            <p className="text-xs sm:text-sm text-charcoal-600 leading-relaxed">
              Are you sure you want to permanently delete this analysis record from SQLite history?
              This action cannot be undone.
            </p>

            {deleteError && (
              <div className="p-3 rounded-lg bg-rose-50 text-rose-800 text-xs">
                {deleteError}
              </div>
            )}

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setRecordToDelete(null)}
                disabled={isDeleting}
                className="px-4 py-2 rounded-lg bg-ivory-100 text-charcoal-700 hover:bg-ivory-200 text-xs font-medium border border-ivory-300"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleDeleteConfirm}
                disabled={isDeleting}
                className="px-4 py-2 rounded-lg bg-rose-700 hover:bg-rose-800 text-white text-xs font-medium flex items-center gap-1.5"
              >
                {isDeleting ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Deleting...</span>
                  </>
                ) : (
                  <span>Delete Record</span>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};

export default HistoryPage;

