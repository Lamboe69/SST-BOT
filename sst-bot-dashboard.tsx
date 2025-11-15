import React, { useState, useEffect } from 'react';
import { Activity, TrendingUp, TrendingDown, Settings, Play, Pause, DollarSign, Target, AlertCircle, CheckCircle, Clock, BarChart3, Bell } from 'lucide-react';

const TradingBotDashboard = () => {
  const [botActive, setBotActive] = useState(false);
  const [riskPercentage, setRiskPercentage] = useState(2);
  const [balanceMethod, setBalanceMethod] = useState('current');
  const [newsFilter, setNewsFilter] = useState(false);
  const [dailyTradeLimit, setDailyTradeLimit] = useState(3);
  
  // Mock data - will be replaced with real data from backend
  const [accountBalance, setAccountBalance] = useState(1000);
  const [initialBalance] = useState(1000);
  const [todayPnL, setTodayPnL] = useState(45.50);
  const [tradesRemaining, setTradesRemaining] = useState(2);
  const [openTrades, setOpenTrades] = useState([
    {
      id: 1,
      instrument: 'NAS100',
      direction: 'BUY',
      entryPrice: 25466.32,
      currentPrice: 25512.80,
      stopLoss: 25440.00,
      takeProfit: 25571.28,
      unrealizedPnL: 46.48,
      setupType: 'CHOCH',
      entryTime: '2024-11-13 08:45:23'
    }
  ]);
  
  const [tradeHistory, setTradeHistory] = useState([
    {
      id: 1,
      instrument: 'USDJPY',
      direction: 'SELL',
      entryPrice: 149.850,
      exitPrice: 149.450,
      pnl: 40.00,
      setupType: 'BOS',
      exitReason: 'TP',
      exitTime: '2024-11-13 06:30:15'
    },
    {
      id: 2,
      instrument: 'USDCAD',
      direction: 'BUY',
      entryPrice: 1.3820,
      exitPrice: 1.3800,
      pnl: -20.00,
      setupType: 'CHOCH',
      exitReason: 'SL',
      exitTime: '2024-11-13 05:15:42'
    }
  ]);

  const winRate = 50;
  const avgRR = 3.2;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white p-6">
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-8">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-3">
            <div className="bg-blue-500 p-3 rounded-xl">
              <Activity className="w-8 h-8" />
            </div>
            <div>
              <h1 className="text-3xl font-bold">Smart Structure Trading Bot</h1>
              <p className="text-slate-400">Automated CHOCH & BOS Trading System</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className={`flex items-center gap-2 px-4 py-2 rounded-lg ${botActive ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
              <div className={`w-3 h-3 rounded-full ${botActive ? 'bg-green-400 animate-pulse' : 'bg-red-400'}`}></div>
              <span className="font-semibold">{botActive ? 'ACTIVE' : 'INACTIVE'}</span>
            </div>
            <button
              onClick={() => setBotActive(!botActive)}
              className={`flex items-center gap-2 px-6 py-3 rounded-lg font-semibold transition-all ${
                botActive 
                  ? 'bg-red-500 hover:bg-red-600' 
                  : 'bg-green-500 hover:bg-green-600'
              }`}
            >
              {botActive ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5" />}
              {botActive ? 'Stop Bot' : 'Start Bot'}
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto space-y-6">
        {/* Overview Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-slate-400 text-sm">Account Balance</span>
              <DollarSign className="w-5 h-5 text-blue-400" />
            </div>
            <div className="text-3xl font-bold">${accountBalance.toFixed(2)}</div>
            <div className="text-xs text-slate-500 mt-1">Initial: ${initialBalance.toFixed(2)}</div>
          </div>

          <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-slate-400 text-sm">Today's P&L</span>
              {todayPnL >= 0 ? <TrendingUp className="w-5 h-5 text-green-400" /> : <TrendingDown className="w-5 h-5 text-red-400" />}
            </div>
            <div className={`text-3xl font-bold ${todayPnL >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {todayPnL >= 0 ? '+' : ''}{todayPnL.toFixed(2)}
            </div>
            <div className="text-xs text-slate-500 mt-1">{((todayPnL / accountBalance) * 100).toFixed(2)}% of balance</div>
          </div>

          <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-slate-400 text-sm">Open Trades</span>
              <Target className="w-5 h-5 text-purple-400" />
            </div>
            <div className="text-3xl font-bold">{openTrades.length}</div>
            <div className="text-xs text-slate-500 mt-1">Active positions</div>
          </div>

          <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-slate-400 text-sm">Trades Remaining</span>
              <Clock className="w-5 h-5 text-orange-400" />
            </div>
            <div className="text-3xl font-bold">{tradesRemaining}/{dailyTradeLimit}</div>
            <div className="text-xs text-slate-500 mt-1">Today's limit</div>
          </div>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Active Trades Panel */}
          <div className="lg:col-span-2 bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold flex items-center gap-2">
                <Activity className="w-6 h-6 text-blue-400" />
                Active Trades
              </h2>
              <span className="text-sm text-slate-400">{openTrades.length} position(s)</span>
            </div>
            
            <div className="space-y-4">
              {openTrades.length === 0 ? (
                <div className="text-center py-12 text-slate-500">
                  <Target className="w-12 h-12 mx-auto mb-3 opacity-50" />
                  <p>No active trades</p>
                  <p className="text-sm mt-1">Bot is monitoring for setups...</p>
                </div>
              ) : (
                openTrades.map(trade => (
                  <div key={trade.id} className="bg-slate-900/50 border border-slate-700 rounded-lg p-4">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <div className={`px-3 py-1 rounded-lg text-sm font-semibold ${
                          trade.direction === 'BUY' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                        }`}>
                          {trade.direction}
                        </div>
                        <div>
                          <div className="font-bold text-lg">{trade.instrument}</div>
                          <div className="text-xs text-slate-500">{trade.setupType} Setup</div>
                        </div>
                      </div>
                      <div className={`text-xl font-bold ${trade.unrealizedPnL >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {trade.unrealizedPnL >= 0 ? '+' : ''}{trade.unrealizedPnL.toFixed(2)}
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-slate-500">Entry:</span>
                        <span className="ml-2 font-semibold">{trade.entryPrice.toFixed(2)}</span>
                      </div>
                      <div>
                        <span className="text-slate-500">Current:</span>
                        <span className="ml-2 font-semibold">{trade.currentPrice.toFixed(2)}</span>
                      </div>
                      <div>
                        <span className="text-slate-500">Stop Loss:</span>
                        <span className="ml-2 font-semibold text-red-400">{trade.stopLoss.toFixed(2)}</span>
                      </div>
                      <div>
                        <span className="text-slate-500">Take Profit:</span>
                        <span className="ml-2 font-semibold text-green-400">{trade.takeProfit.toFixed(2)}</span>
                      </div>
                    </div>
                    
                    <div className="flex gap-2 mt-4">
                      <button className="flex-1 bg-slate-700 hover:bg-slate-600 px-4 py-2 rounded-lg text-sm font-semibold transition-colors">
                        Modify SL/TP
                      </button>
                      <button className="flex-1 bg-red-500/20 hover:bg-red-500/30 text-red-400 px-4 py-2 rounded-lg text-sm font-semibold transition-colors">
                        Close Trade
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Settings Panel */}
          <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6">
            <h2 className="text-xl font-bold flex items-center gap-2 mb-6">
              <Settings className="w-6 h-6 text-blue-400" />
              Bot Settings
            </h2>
            
            <div className="space-y-6">
              {/* Risk Percentage */}
              <div>
                <label className="block text-sm font-semibold mb-3 text-slate-300">Risk Per Trade</label>
                <div className="grid grid-cols-4 gap-2">
                  {[1, 2, 3, 4].map(value => (
                    <button
                      key={value}
                      onClick={() => setRiskPercentage(value)}
                      className={`py-2 rounded-lg font-semibold transition-all ${
                        riskPercentage === value
                          ? 'bg-blue-500 text-white'
                          : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                      }`}
                    >
                      {value}%
                    </button>
                  ))}
                </div>
              </div>

              {/* Balance Method */}
              <div>
                <label className="block text-sm font-semibold mb-3 text-slate-300">Balance Calculation</label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    onClick={() => setBalanceMethod('initial')}
                    className={`py-2 px-3 rounded-lg font-semibold text-sm transition-all ${
                      balanceMethod === 'initial'
                        ? 'bg-blue-500 text-white'
                        : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                    }`}
                  >
                    Initial
                  </button>
                  <button
                    onClick={() => setBalanceMethod('current')}
                    className={`py-2 px-3 rounded-lg font-semibold text-sm transition-all ${
                      balanceMethod === 'current'
                        ? 'bg-blue-500 text-white'
                        : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                    }`}
                  >
                    Current
                  </button>
                </div>
              </div>

              {/* News Filter */}
              <div>
                <label className="flex items-center justify-between cursor-pointer">
                  <span className="text-sm font-semibold text-slate-300">High-Impact News Filter</span>
                  <div
                    onClick={() => setNewsFilter(!newsFilter)}
                    className={`relative w-12 h-6 rounded-full transition-colors ${
                      newsFilter ? 'bg-blue-500' : 'bg-slate-700'
                    }`}
                  >
                    <div
                      className={`absolute top-1 left-1 w-4 h-4 rounded-full bg-white transition-transform ${
                        newsFilter ? 'transform translate-x-6' : ''
                      }`}
                    />
                  </div>
                </label>
              </div>

              {/* Daily Trade Limit */}
              <div>
                <label className="block text-sm font-semibold mb-3 text-slate-300">Daily Trade Limit</label>
                <input
                  type="number"
                  value={dailyTradeLimit}
                  onChange={(e) => setDailyTradeLimit(parseInt(e.target.value) || 3)}
                  min="1"
                  max="10"
                  className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Apply Button */}
              <button className="w-full bg-blue-500 hover:bg-blue-600 py-3 rounded-lg font-semibold transition-colors">
                Apply Settings
              </button>

              {/* Performance Stats */}
              <div className="pt-6 border-t border-slate-700">
                <h3 className="text-sm font-semibold mb-3 text-slate-300">Performance Metrics</h3>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-400">Win Rate:</span>
                    <span className="font-semibold text-green-400">{winRate}%</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-400">Avg R:R:</span>
                    <span className="font-semibold">1:{avgRR}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-400">Total Trades:</span>
                    <span className="font-semibold">{tradeHistory.length}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Trade History */}
        <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold flex items-center gap-2">
              <BarChart3 className="w-6 h-6 text-blue-400" />
              Trade History
            </h2>
            <button className="text-sm text-blue-400 hover:text-blue-300 font-semibold">
              View All →
            </button>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="text-left text-sm text-slate-400 border-b border-slate-700">
                  <th className="pb-3">Instrument</th>
                  <th className="pb-3">Direction</th>
                  <th className="pb-3">Setup</th>
                  <th className="pb-3">Entry</th>
                  <th className="pb-3">Exit</th>
                  <th className="pb-3">P&L</th>
                  <th className="pb-3">Exit Reason</th>
                  <th className="pb-3">Time</th>
                </tr>
              </thead>
              <tbody className="text-sm">
                {tradeHistory.map(trade => (
                  <tr key={trade.id} className="border-b border-slate-800 hover:bg-slate-800/30">
                    <td className="py-3 font-semibold">{trade.instrument}</td>
                    <td className="py-3">
                      <span className={`px-2 py-1 rounded text-xs font-semibold ${
                        trade.direction === 'BUY' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                      }`}>
                        {trade.direction}
                      </span>
                    </td>
                    <td className="py-3 text-slate-400">{trade.setupType}</td>
                    <td className="py-3">{trade.entryPrice.toFixed(trade.instrument.includes('JPY') ? 3 : 4)}</td>
                    <td className="py-3">{trade.exitPrice.toFixed(trade.instrument.includes('JPY') ? 3 : 4)}</td>
                    <td className={`py-3 font-bold ${trade.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {trade.pnl >= 0 ? '+' : ''}{trade.pnl.toFixed(2)}
                    </td>
                    <td className="py-3">
                      <span className={`px-2 py-1 rounded text-xs font-semibold ${
                        trade.exitReason === 'TP' ? 'bg-green-500/20 text-green-400' : 
                        trade.exitReason === 'SL' ? 'bg-red-500/20 text-red-400' : 
                        'bg-slate-500/20 text-slate-400'
                      }`}>
                        {trade.exitReason}
                      </span>
                    </td>
                    <td className="py-3 text-slate-400">{trade.exitTime}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Monitoring Status */}
        <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6">
          <h2 className="text-xl font-bold flex items-center gap-2 mb-6">
            <Bell className="w-6 h-6 text-blue-400" />
            Instruments Monitoring
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            {['NAS100', 'EU50', 'JP225', 'USDCAD', 'USDJPY'].map(instrument => (
              <div key={instrument} className="bg-slate-900/50 border border-slate-700 rounded-lg p-4 text-center">
                <div className="font-bold mb-2">{instrument}</div>
                <div className="flex items-center justify-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse"></div>
                  <span className="text-xs text-slate-400">Monitoring</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TradingBotDashboard;