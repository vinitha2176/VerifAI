import React from 'react';
import { ShieldCheck, AlertTriangle, AlertOctagon, CheckCircle2 } from 'lucide-react';

export const RiskBadge = ({ level, size = 'md', showIcon = true }) => {
  const normLevel = (level || 'LOW').toUpperCase();

  const configs = {
    LOW: {
      label: 'Low Risk',
      bg: 'bg-emerald-50 text-emerald-800 border-emerald-200',
      icon: ShieldCheck,
      iconColor: 'text-emerald-600',
    },
    MODERATE: {
      label: 'Moderate Risk',
      bg: 'bg-amber-50 text-amber-900 border-amber-200',
      icon: AlertTriangle,
      iconColor: 'text-amber-600',
    },
    HIGH: {
      label: 'High Risk',
      bg: 'bg-rose-50 text-rose-900 border-rose-200',
      icon: AlertOctagon,
      iconColor: 'text-rose-600',
    },
  };

  const current = configs[normLevel] || configs.LOW;
  const IconComponent = current.icon;

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5 font-medium',
    md: 'text-xs px-2.5 py-1 font-semibold tracking-wide',
    lg: 'text-sm px-3.5 py-1.5 font-semibold tracking-wide',
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border ${current.bg} ${sizeClasses[size] || sizeClasses.md}`}
    >
      {showIcon && <IconComponent className={`w-3.5 h-3.5 ${current.iconColor}`} />}
      <span>{current.label}</span>
    </span>
  );
};

export const PredictionBadge = ({ prediction }) => {
  const isSuspicious = (prediction || '').toUpperCase() === 'SUSPICIOUS';

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold uppercase tracking-wider border ${
        isSuspicious
          ? 'bg-rose-50 text-rose-800 border-rose-200'
          : 'bg-forest-50 text-forest-800 border-forest-200'
      }`}
    >
      {isSuspicious ? (
        <AlertTriangle className="w-3.5 h-3.5 text-rose-600" />
      ) : (
        <CheckCircle2 className="w-3.5 h-3.5 text-forest-600" />
      )}
      <span>{prediction}</span>
    </span>
  );
};

export default RiskBadge;

