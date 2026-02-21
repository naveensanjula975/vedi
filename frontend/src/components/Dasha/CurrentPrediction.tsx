/**
 * Current Period Prediction component - displays predictions for the running Dasha period
 */

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { getCurrentPrediction } from '../../services/api';
import type { BirthData } from '../../types/astrology';
import DashaPrediction from './DashaPrediction';
import { Loader2, Calendar, Moon, Star } from 'lucide-react';

interface Props {
  birthData: BirthData;
}

export const CurrentPrediction: React.FC<Props> = ({ birthData }) => {
  const { data: prediction, isLoading, error } = useQuery({
    queryKey: ['currentPrediction', birthData],
    queryFn: () => getCurrentPrediction(birthData),
    enabled: !!birthData.date,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-12 glass-card rounded-xl">
        <Loader2 className="w-8 h-8 animate-spin text-cyber-500" />
        <span className="ml-3 text-slate-400 font-mono text-sm">Loading predictions...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400">
        <p>Failed to load predictions. Please try again.</p>
      </div>
    );
  }

  if (!prediction) return null;

  // Transform the API response to match the component's expected format
  const formattedPrediction = {
    dasha_lord: prediction.dashaLord,
    period_type: prediction.periodType,
    overall_theme: prediction.overallTheme,
    overall_rating: prediction.overallRating,
    predictions: {
      health: prediction.predictions.health,
      wealth: prediction.predictions.wealth,
      career: prediction.predictions.career,
      relationships: prediction.predictions.relationships,
      general: prediction.predictions.general,
    },
    favorable_activities: prediction.favorableActivities,
    unfavorable_activities: prediction.unfavorableActivities,
    remedies: prediction.remedies,
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-4"
    >
      {/* Current Period Header */}
      {prediction.currentPeriods && (
        <div className="glass-card rounded-xl p-4 border border-cyber-600/30">
          <h3 className="text-lg font-display font-semibold mb-4 flex items-center gap-2 text-white">
            <Calendar className="w-5 h-5 text-cyber-400" />
            Currently Running Periods
          </h3>

          <div className="grid md:grid-cols-3 gap-4">
            {/* Mahadasha */}
            <div className="bg-slate-800/50 rounded-lg p-3 border border-slate-700/50">
              <div className="flex items-center gap-2 mb-2">
                <Star className="w-4 h-4 text-amber-400" />
                <span className="text-sm text-slate-400">Mahadasha</span>
              </div>
              <div className="text-xl font-bold text-white">
                {prediction.currentPeriods.mahadasha?.lord}
              </div>
              <div className="text-xs text-slate-500 mt-1 font-mono">
                {prediction.currentPeriods.mahadasha?.start?.split('T')[0]} to{' '}
                {prediction.currentPeriods.mahadasha?.end?.split('T')[0]}
              </div>
            </div>

            {/* Antardasha */}
            {prediction.currentPeriods.antardasha && (
              <div className="bg-slate-800/50 rounded-lg p-3 border border-slate-700/50">
                <div className="flex items-center gap-2 mb-2">
                  <Moon className="w-4 h-4 text-cyber-400" />
                  <span className="text-sm text-slate-400">Antardasha</span>
                </div>
                <div className="text-xl font-bold text-white">
                  {prediction.currentPeriods.antardasha?.lord}
                </div>
                <div className="text-xs text-slate-500 mt-1 font-mono">
                  {prediction.currentPeriods.antardasha?.start?.split('T')[0]} to{' '}
                  {prediction.currentPeriods.antardasha?.end?.split('T')[0]}
                </div>
              </div>
            )}

            {/* Pratyantardasha */}
            {prediction.currentPeriods.pratyantardasha && (
              <div className="bg-slate-800/50 rounded-lg p-3 border border-slate-700/50">
                <div className="flex items-center gap-2 mb-2">
                  <Star className="w-4 h-4 text-neon-400" />
                  <span className="text-sm text-slate-400">Pratyantardasha</span>
                </div>
                <div className="text-xl font-bold text-white">
                  {prediction.currentPeriods.pratyantardasha?.lord}
                </div>
                <div className="text-xs text-slate-500 mt-1 font-mono">
                  {prediction.currentPeriods.pratyantardasha?.start?.split('T')[0]} to{' '}
                  {prediction.currentPeriods.pratyantardasha?.end?.split('T')[0]}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Detailed Prediction */}
      <DashaPrediction prediction={formattedPrediction} />
    </motion.div>
  );
};

export default CurrentPrediction;
