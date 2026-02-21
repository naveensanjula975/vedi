/**
 * Dasha Timeline component - shows Mahadashas with expandable Antardashas and predictions
 */

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import {
  ChevronDown,
  ChevronUp,
  Eye,
  Heart,
  Wallet,
  Briefcase,
  Users,
  Sparkles,
  Loader2,
  Star,
  CheckCircle,
  AlertTriangle,
  MinusCircle,
  Gem
} from 'lucide-react';
import type { DashaWithAntardashas, BirthData } from '../../types/astrology';
import { DASHA_COLORS } from '../../types/astrology';
import { formatDate, formatYears, formatDays } from '../../utils/dateUtils';
import { parseISO, isWithinInterval } from 'date-fns';
import { getAntardashaPrediction, type DashaPredictionData } from '../../services/api';

interface Props {
  timeline: DashaWithAntardashas[];
  birthData?: BirthData;
  currentDate?: Date;
}

const TREND_CONFIG = {
  positive: { icon: CheckCircle, color: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/30', label: 'Favorable' },
  negative: { icon: AlertTriangle, color: 'text-rose-400', bg: 'bg-rose-500/10', border: 'border-rose-500/30', label: 'Challenging' },
  mixed: { icon: MinusCircle, color: 'text-amber-400', bg: 'bg-amber-500/10', border: 'border-amber-500/30', label: 'Mixed' },
  neutral: { icon: MinusCircle, color: 'text-slate-400', bg: 'bg-slate-500/10', border: 'border-slate-500/30', label: 'Neutral' },
};

const AREA_CONFIG = {
  health: { icon: Heart, color: 'text-rose-400', bgColor: 'bg-rose-500/10', label: 'Health' },
  wealth: { icon: Wallet, color: 'text-emerald-400', bgColor: 'bg-emerald-500/10', label: 'Wealth' },
  career: { icon: Briefcase, color: 'text-cyber-400', bgColor: 'bg-cyber-500/10', label: 'Career' },
  relationships: { icon: Users, color: 'text-pink-400', bgColor: 'bg-pink-500/10', label: 'Relationships' },
  general: { icon: Sparkles, color: 'text-purple-400', bgColor: 'bg-purple-500/10', label: 'General' },
};

interface PredictionDisplayProps {
  prediction: DashaPredictionData;
  mahadashaLord: string;
  antardashaLord: string;
}

const PredictionDisplay: React.FC<PredictionDisplayProps> = ({ prediction, mahadashaLord, antardashaLord }) => {
  const [expandedArea, setExpandedArea] = useState<string | null>(null);
  const [showActivities, setShowActivities] = useState(false);

  const renderTrendBadge = (trend: string) => {
    const config = TREND_CONFIG[trend as keyof typeof TREND_CONFIG] || TREND_CONFIG.neutral;
    const Icon = config.icon;
    return (
      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${config.bg} ${config.color} border ${config.border}`}>
        <Icon className="w-3 h-3" />
        {config.label}
      </span>
    );
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className="mt-3 glass-card rounded-lg overflow-hidden"
    >
      {/* Header */}
      <div className="p-4 bg-gradient-to-r from-cyber-700 to-neon-700">
        <div className="flex items-center justify-between">
          <div>
            <h4 className="font-display font-semibold text-lg text-white">
              {mahadashaLord} - {antardashaLord} Predictions
            </h4>
            <p className="text-cyber-200 text-sm mt-1 line-clamp-2">
              {prediction.overallTheme}
            </p>
          </div>
          <div className="text-right">
            <div className="text-cyber-200 text-xs">Rating</div>
            <div className="flex items-center gap-1">
              <Star className="w-4 h-4 text-amber-400 fill-amber-400" />
              <span className="font-bold text-lg text-white">{prediction.overallRating}/10</span>
            </div>
          </div>
        </div>
      </div>

      {/* Life Areas Grid */}
      <div className="p-4 space-y-2">
        <h5 className="text-sm font-semibold text-slate-300 mb-3">Life Area Outlook</h5>

        {Object.entries(prediction.predictions).map(([area, data]) => {
          const config = AREA_CONFIG[area as keyof typeof AREA_CONFIG];
          if (!config) return null;

          const Icon = config.icon;
          const isExpanded = expandedArea === area;

          return (
            <div key={area} className="rounded-lg border border-slate-700/50 overflow-hidden bg-slate-800/30">
              <button
                onClick={() => setExpandedArea(isExpanded ? null : area)}
                className="w-full p-3 flex items-center justify-between hover:bg-slate-700/30 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className={`p-1.5 rounded-lg ${config.bgColor} border border-slate-600/30`}>
                    <Icon className={`w-4 h-4 ${config.color}`} />
                  </div>
                  <div className="text-left">
                    <div className="font-medium text-white text-sm">{config.label}</div>
                    <div className="text-xs text-slate-400 line-clamp-1 max-w-xs">{data.summary}</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {renderTrendBadge(data.trend)}
                  {isExpanded ? (
                    <ChevronUp className="w-4 h-4 text-slate-500" />
                  ) : (
                    <ChevronDown className="w-4 h-4 text-slate-500" />
                  )}
                </div>
              </button>

              <AnimatePresence>
                {isExpanded && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="border-t border-slate-700/50"
                  >
                    <div className="p-4 bg-slate-800/50 space-y-4">
                      {/* Details */}
                      <div>
                        <h6 className="font-medium text-slate-300 text-sm mb-2">Details</h6>
                        <ul className="space-y-1">
                          {data.details.slice(0, 5).map((detail, i) => (
                            <li key={i} className="flex items-start gap-2 text-xs text-slate-400">
                              <span className="text-cyber-400 mt-0.5">•</span>
                              <span>{detail}</span>
                            </li>
                          ))}
                        </ul>
                      </div>

                      {/* Remedies */}
                      {data.remedies.length > 0 && (
                        <div>
                          <h6 className="font-medium text-slate-300 text-sm mb-2">Remedies</h6>
                          <ul className="space-y-1">
                            {data.remedies.slice(0, 3).map((remedy, i) => (
                              <li key={i} className="flex items-start gap-2 text-xs text-slate-400">
                                <span className="text-emerald-400">✓</span>
                                <span>{remedy}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          );
        })}
      </div>

      {/* Remedies & Activities */}
      <div className="px-4 pb-4 space-y-3">
        {/* Main Remedies */}
        <div className="p-3 bg-slate-800/50 rounded-lg border border-slate-700/50">
          <h5 className="text-sm font-semibold text-slate-300 mb-2 flex items-center gap-2">
            <Gem className="w-4 h-4 text-purple-400" />
            Recommended Remedies
          </h5>
          <div className="grid grid-cols-3 gap-2 text-xs">
            {prediction.remedies.gemstone && (
              <div className="p-2 bg-purple-500/10 rounded-lg border border-purple-500/20">
                <div className="text-purple-400 font-medium">Gemstone</div>
                <div className="text-slate-300">{prediction.remedies.gemstone}</div>
              </div>
            )}
            {prediction.remedies.mantra && (
              <div className="p-2 bg-cyber-500/10 rounded-lg border border-cyber-500/20">
                <div className="text-cyber-400 font-medium">Mantra</div>
                <div className="text-slate-300 truncate">{prediction.remedies.mantra}</div>
              </div>
            )}
            {prediction.remedies.deity && (
              <div className="p-2 bg-amber-500/10 rounded-lg border border-amber-500/20">
                <div className="text-amber-400 font-medium">Deity</div>
                <div className="text-slate-300">{prediction.remedies.deity}</div>
              </div>
            )}
          </div>
        </div>

        {/* Activities */}
        <button
          onClick={() => setShowActivities(!showActivities)}
          className="w-full p-3 flex items-center justify-between bg-slate-800/50 rounded-lg border border-slate-700/50 hover:bg-slate-700/40 transition-colors"
        >
          <span className="text-sm font-semibold text-slate-300 flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-emerald-400" />
            Activities Guide
          </span>
          {showActivities ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
        </button>

        <AnimatePresence>
          {showActivities && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="grid grid-cols-2 gap-3"
            >
              <div className="p-3 bg-emerald-500/10 rounded-lg border border-emerald-500/30">
                <h6 className="font-medium text-emerald-400 text-xs mb-2 flex items-center gap-1">
                  <CheckCircle className="w-3 h-3" /> Favorable
                </h6>
                <ul className="space-y-1">
                  {prediction.favorableActivities.slice(0, 4).map((activity, i) => (
                    <li key={i} className="text-xs text-slate-300 flex items-start gap-1">
                      <span className="text-emerald-400">✓</span>
                      <span>{activity}</span>
                    </li>
                  ))}
                </ul>
              </div>
              <div className="p-3 bg-rose-500/10 rounded-lg border border-rose-500/30">
                <h6 className="font-medium text-rose-400 text-xs mb-2 flex items-center gap-1">
                  <AlertTriangle className="w-3 h-3" /> Avoid
                </h6>
                <ul className="space-y-1">
                  {prediction.unfavorableActivities.slice(0, 4).map((activity, i) => (
                    <li key={i} className="text-xs text-slate-300 flex items-start gap-1">
                      <span className="text-rose-400">✗</span>
                      <span>{activity}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
};

export const DashaTimeline: React.FC<Props> = ({ timeline, birthData, currentDate = new Date() }) => {
  const [expandedDasha, setExpandedDasha] = useState<string | null>(null);
  const [selectedAntardasha, setSelectedAntardasha] = useState<{
    mahadasha: string;
    antardasha: string;
    key: string;
  } | null>(null);

  // Fetch prediction for selected Antardasha
  const { data: prediction, isLoading: isPredictionLoading } = useQuery({
    queryKey: ['antardashaPrediction', selectedAntardasha?.mahadasha, selectedAntardasha?.antardasha, birthData],
    queryFn: () => {
      if (!birthData || !selectedAntardasha) return null;
      return getAntardashaPrediction(birthData, selectedAntardasha.mahadasha, selectedAntardasha.antardasha);
    },
    enabled: !!birthData && !!selectedAntardasha,
    staleTime: 10 * 60 * 1000, // 10 minutes cache
  });

  // Check if a period contains the current date
  const isCurrent = (start: string, end: string): boolean => {
    try {
      return isWithinInterval(currentDate, {
        start: parseISO(start),
        end: parseISO(end),
      });
    } catch {
      return false;
    }
  };

  // Toggle expansion
  const toggleExpand = (lord: string, index: number) => {
    const key = `${lord}-${index}`;
    if (expandedDasha === key) {
      setExpandedDasha(null);
      setSelectedAntardasha(null);
    } else {
      setExpandedDasha(key);
      setSelectedAntardasha(null);
    }
  };

  // Handle Antardasha click
  const handleAntardashaClick = (mahadasha: string, antardasha: string, mdIdx: number, adIdx: number) => {
    const key = `${mahadasha}-${antardasha}-${mdIdx}-${adIdx}`;
    if (selectedAntardasha?.key === key) {
      setSelectedAntardasha(null);
    } else {
      setSelectedAntardasha({ mahadasha, antardasha, key });
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-display font-semibold text-white">
          Mahadasha Timeline
        </h3>
        <p className="text-xs text-slate-500 font-mono">Click any period to view predictions</p>
      </div>

      {timeline.map((item, idx) => {
        const { mahadasha, antardashas } = item;
        const key = `${mahadasha.lord}-${idx}`;
        const isExpanded = expandedDasha === key;
        const isMdCurrent = isCurrent(mahadasha.start, mahadasha.end);

        return (
          <motion.div
            key={key}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: idx * 0.05 }}
            className="rounded-xl overflow-hidden border border-slate-700/50"
          >
            {/* Mahadasha header */}
            <div
              onClick={() => toggleExpand(mahadasha.lord, idx)}
              className={`
                p-4 cursor-pointer flex items-center justify-between
                transition-all hover:brightness-110
                ${DASHA_COLORS[mahadasha.lord] || 'bg-slate-600'}
                ${isMdCurrent ? 'ring-2 ring-cyber-400 ring-offset-2 ring-offset-slate-900' : ''}
              `}
            >
              <div className="flex items-center gap-3">
                <span className="text-white font-bold text-lg">
                  {mahadasha.lord}
                </span>
                {mahadasha.isBirthDasha && (
                  <span className="px-2 py-0.5 bg-white/20 rounded text-xs text-white font-mono">
                    Birth
                  </span>
                )}
                {isMdCurrent && (
                  <span className="px-2 py-0.5 bg-cyber-500 rounded text-xs text-white font-semibold">
                    Current
                  </span>
                )}
              </div>

              <div className="flex items-center gap-4 text-white">
                <div className="text-right text-sm">
                  <div className="opacity-80 font-mono text-xs">
                    {formatDate(mahadasha.start)} – {formatDate(mahadasha.end)}
                  </div>
                  <div className="font-semibold">
                    {formatYears(mahadasha.durationYears)}
                  </div>
                </div>
                {isExpanded ? (
                  <ChevronUp className="w-5 h-5" />
                ) : (
                  <ChevronDown className="w-5 h-5" />
                )}
              </div>
            </div>

            {/* Antardashas */}
            <AnimatePresence>
              {isExpanded && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.2 }}
                  className="bg-slate-900/50"
                >
                  <div className="p-3 space-y-2">
                    {antardashas.map((ad, adIdx) => {
                      const isAdCurrent = isCurrent(ad.start, ad.end);
                      const adKey = `${mahadasha.lord}-${ad.lord}-${idx}-${adIdx}`;
                      const isSelected = selectedAntardasha?.key === adKey;

                      return (
                        <div key={`${ad.lord}-${adIdx}`}>
                          <motion.div
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: adIdx * 0.03 }}
                            onClick={() => birthData && handleAntardashaClick(mahadasha.lord, ad.lord, idx, adIdx)}
                            className={`
                              p-3 rounded-lg flex items-center justify-between
                              bg-slate-800/50 border
                              ${isAdCurrent ? 'border-cyber-400' : 'border-slate-700/50'}
                              ${birthData ? 'cursor-pointer hover:bg-slate-700/50 transition-all' : ''}
                              ${isSelected ? 'ring-2 ring-cyber-500 bg-slate-700/50' : ''}
                            `}
                          >
                            <div className="flex items-center gap-2">
                              <span
                                className={`
                                  w-3 h-3 rounded-full
                                  ${DASHA_COLORS[ad.lord] || 'bg-slate-500'}
                                `}
                              />
                              <span className="font-medium text-white">
                                {mahadasha.lord} - {ad.lord}
                              </span>
                              {isAdCurrent && (
                                <span className="px-2 py-0.5 bg-cyber-500 rounded text-xs text-white">
                                  Now
                                </span>
                              )}
                              {birthData && (
                                <Eye className={`w-4 h-4 ${isSelected ? 'text-cyber-400' : 'text-slate-500'}`} />
                              )}
                            </div>

                            <div className="text-right text-sm text-slate-400">
                              <div className="font-mono text-xs">{formatDate(ad.start)} – {formatDate(ad.end)}</div>
                              <div className="font-medium text-slate-300">{formatDays(ad.durationDays)}</div>
                            </div>
                          </motion.div>

                          {/* Inline Prediction Display */}
                          <AnimatePresence>
                            {isSelected && (
                              <motion.div
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: 'auto' }}
                                exit={{ opacity: 0, height: 0 }}
                              >
                                {isPredictionLoading ? (
                                  <div className="mt-3 p-6 glass-card rounded-lg flex items-center justify-center">
                                    <Loader2 className="w-5 h-5 animate-spin text-cyber-500 mr-2" />
                                    <span className="text-sm text-slate-400 font-mono">Loading predictions...</span>
                                  </div>
                                ) : prediction ? (
                                  <PredictionDisplay
                                    prediction={prediction}
                                    mahadashaLord={mahadasha.lord}
                                    antardashaLord={ad.lord}
                                  />
                                ) : null}
                              </motion.div>
                            )}
                          </AnimatePresence>
                        </div>
                      );
                    })}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        );
      })}
    </div>
  );
};
