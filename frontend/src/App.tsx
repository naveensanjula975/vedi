/**
 * Main Application Component
 */

import { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { Moon, Sun, LayoutGrid, List, AlertCircle, Sparkles, Zap } from 'lucide-react';

import { BirthDataForm } from './components/Forms/BirthDataForm';
import { SouthIndianChart } from './components/Chart/SouthIndianChart';
import { NorthIndianChart } from './components/Chart/NorthIndianChart';
import { PlanetTable } from './components/Chart/PlanetTable';
import { CurrentDasha } from './components/Dasha/CurrentDasha';
import { DashaTimeline } from './components/Dasha/DashaTimeline';
import { NakshatraInfo } from './components/Dasha/NakshatraInfo';
import { CurrentPrediction } from './components/Dasha/CurrentPrediction';
import { useGenerateChart, useDashaTimeline, useHealthCheck } from './hooks/useChart';
import type { BirthData, Chart } from './types/astrology';

// Create QueryClient
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

type ChartStyle = 'south' | 'north';
type ViewTab = 'chart' | 'dasha' | 'predictions';

function AppContent() {
  const [birthData, setBirthData] = useState<BirthData | null>(null);
  const [chartStyle, setChartStyle] = useState<ChartStyle>('south');
  const [activeTab, setActiveTab] = useState<ViewTab>('chart');
  const [chartData, setChartData] = useState<Chart | null>(null);

  // API hooks
  const generateChart = useGenerateChart();
  const { data: dashaTimeline, isLoading: isDashaLoading } = useDashaTimeline(
    birthData,
    80 // 80 years ahead
  );
  const { data: health, isError: isHealthError } = useHealthCheck();

  const handleSubmit = async (data: BirthData) => {
    setBirthData(data);
    try {
      const result = await generateChart.mutateAsync(data);
      setChartData(result);
    } catch (error) {
      console.error('Failed to generate chart:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-925 to-cyber-950 tech-grid">
      {/* Ambient glow effects */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-cyber-600/20 rounded-full blur-[100px]" />
        <div className="absolute top-1/2 -left-20 w-60 h-60 bg-neon-600/10 rounded-full blur-[80px]" />
        <div className="absolute -bottom-20 right-1/4 w-72 h-72 bg-accent-purple/10 rounded-full blur-[90px]" />
      </div>

      {/* Header */}
      <header className="relative z-10 border-b border-cyber-800/30 bg-slate-950/80 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyber-500 to-neon-500 flex items-center justify-center shadow-neon">
                <Zap className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-display font-bold tracking-tight text-white">VEDI</h1>
                <p className="text-xs text-cyber-400 font-mono uppercase tracking-wider">Astrology Engine</p>
              </div>
            </div>

            {/* API Status */}
            <div className="flex items-center gap-3">
              {isHealthError ? (
                <span className="flex items-center gap-2 text-xs px-3 py-1.5 rounded-full bg-red-500/10 border border-red-500/30 text-red-400">
                  <AlertCircle className="w-3 h-3" />
                  Offline
                </span>
              ) : health ? (
                <span className="flex items-center gap-2 text-xs px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  v{health.version}
                </span>
              ) : (
                <span className="text-xs text-slate-500">Connecting...</span>
              )}
            </div>
          </div>
        </div>
      </header>

      <main className="relative z-10 max-w-7xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Form */}
          <div className="lg:col-span-1">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="glass-card rounded-2xl p-6"
            >
              <h2 className="text-lg font-display font-semibold text-white mb-6 flex items-center gap-2">
                <Moon className="w-5 h-5 text-cyber-400" />
                Birth Details
              </h2>
              <BirthDataForm
                onSubmit={handleSubmit}
                isLoading={generateChart.isPending}
              />

              {generateChart.isError && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="mt-4 p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400 text-sm"
                >
                  <AlertCircle className="inline w-4 h-4 mr-2" />
                  {generateChart.error?.message || 'Failed to generate chart'}
                </motion.div>
              )}
            </motion.div>
          </div>

          {/* Right Column - Results */}
          <div className="lg:col-span-2">
            <AnimatePresence mode="wait">
              {chartData ? (
                <motion.div
                  key="results"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  className="space-y-6"
                >
                  {/* Tabs */}
                  <div className="flex gap-1 bg-slate-900/60 backdrop-blur-sm rounded-xl p-1.5 border border-cyber-800/30">
                    <button
                      onClick={() => setActiveTab('chart')}
                      className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg text-sm font-medium transition-all duration-300 ${activeTab === 'chart'
                          ? 'bg-cyber-600 text-white shadow-neon'
                          : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
                        }`}
                    >
                      <LayoutGrid className="w-4 h-4" />
                      Chart
                    </button>
                    <button
                      onClick={() => setActiveTab('dasha')}
                      className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg text-sm font-medium transition-all duration-300 ${activeTab === 'dasha'
                          ? 'bg-cyber-600 text-white shadow-neon'
                          : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
                        }`}
                    >
                      <List className="w-4 h-4" />
                      Timeline
                    </button>
                    <button
                      onClick={() => setActiveTab('predictions')}
                      className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg text-sm font-medium transition-all duration-300 ${activeTab === 'predictions'
                          ? 'bg-cyber-600 text-white shadow-neon'
                          : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
                        }`}
                    >
                      <Sparkles className="w-4 h-4" />
                      Insights
                    </button>
                  </div>

                  {activeTab === 'chart' && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="space-y-6"
                    >
                      {/* Chart Style Toggle */}
                      <div className="flex justify-center gap-2">
                        <button
                          onClick={() => setChartStyle('south')}
                          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-300 ${chartStyle === 'south'
                              ? 'bg-cyber-600 text-white shadow-neon'
                              : 'bg-slate-800/50 text-slate-400 hover:text-white border border-slate-700/50'
                            }`}
                        >
                          South Indian
                        </button>
                        <button
                          onClick={() => setChartStyle('north')}
                          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-300 ${chartStyle === 'north'
                              ? 'bg-cyber-600 text-white shadow-neon'
                              : 'bg-slate-800/50 text-slate-400 hover:text-white border border-slate-700/50'
                            }`}
                        >
                          North Indian
                        </button>
                      </div>

                      {/* Chart */}
                      <div className="glass-card rounded-2xl p-6">
                        {chartStyle === 'south' ? (
                          <SouthIndianChart
                            planets={chartData.planets}
                            ascendantRashi={chartData.ascendant.rashiIndex}
                          />
                        ) : (
                          <NorthIndianChart
                            planets={chartData.planets}
                            ascendantRashi={chartData.ascendant.rashiIndex}
                          />
                        )}
                      </div>

                      {/* Nakshatra Info */}
                      <NakshatraInfo nakshatra={chartData.moonNakshatra} />

                      {/* Planet Table */}
                      <div className="glass-card rounded-2xl p-6">
                        <h3 className="text-lg font-display font-semibold text-white mb-4 flex items-center gap-2">
                          <Sun className="w-5 h-5 text-amber-400" />
                          Planetary Positions
                        </h3>
                        <PlanetTable
                          planets={chartData.planets}
                          ascendant={chartData.ascendant}
                        />
                        <div className="mt-4 pt-3 border-t border-slate-700/50 flex justify-between items-center text-xs text-slate-500">
                          <span className="font-mono">Ayanamsa: {chartData.birthData.ayanamsa}</span>
                          <span className="font-mono">{chartData.ayanamsaValue.toFixed(4)}°</span>
                        </div>
                      </div>
                    </motion.div>
                  )}

                  {activeTab === 'dasha' && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="space-y-6"
                    >
                      {/* Current Dasha */}
                      <div className="glass-card rounded-2xl p-6">
                        <CurrentDasha currentDasha={chartData.currentDasha} />
                      </div>

                      {/* Dasha Timeline */}
                      <div className="glass-card rounded-2xl p-6">
                        {isDashaLoading ? (
                          <div className="text-center py-8 text-slate-500">
                            <div className="animate-spin w-8 h-8 border-2 border-cyber-500 border-t-transparent rounded-full mx-auto mb-3" />
                            <span className="font-mono text-sm">Loading timeline...</span>
                          </div>
                        ) : dashaTimeline ? (
                          <DashaTimeline timeline={dashaTimeline.timeline} birthData={birthData ?? undefined} />
                        ) : null}
                      </div>
                    </motion.div>
                  )}

                  {activeTab === 'predictions' && birthData && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="space-y-6"
                    >
                      <CurrentPrediction birthData={birthData} />
                    </motion.div>
                  )}
                </motion.div>
              ) : (
                <motion.div
                  key="empty"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="glass-card rounded-2xl p-12 text-center"
                >
                  <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-cyber-600/20 to-neon-600/20 flex items-center justify-center border border-cyber-500/30">
                    <Zap className="w-10 h-10 text-cyber-400" />
                  </div>
                  <h3 className="text-xl font-display font-semibold text-white mb-3">
                    Ready to Analyze
                  </h3>
                  <p className="text-slate-400 max-w-md mx-auto text-sm leading-relaxed">
                    Enter birth details to generate a comprehensive astrological chart
                    with Vimshottari Dasha timeline and personalized insights.
                  </p>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="relative z-10 mt-16 py-6 border-t border-cyber-800/30 bg-slate-950/50">
        <div className="max-w-7xl mx-auto px-4 flex items-center justify-between">
          <p className="text-slate-500 text-xs font-mono">
            VEDI • Powered by Swiss Ephemeris
          </p>
          <p className="text-slate-600 text-xs">
            Precision astronomical calculations
          </p>
        </div>
      </footer>
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  );
}
