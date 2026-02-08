import { useState, useEffect } from "react";
import { BarChart3, TrendingUp, Activity, Clock, PieChart, DollarSign, LineChart } from "lucide-react";

interface SymbolStats {
    symbol: string;
    total_orders: number;
    open_orders: number;
    closed_orders: number;
    win_count: number;
    loss_count: number;
    total_profit: number;
    win_rate: number | null;
}

interface DashboardData {
    total_profit_percentage: number;
    total_orders: number;
    open_orders: number;
    closed_orders: number;
    win_count: number;
    loss_count: number;
    win_rate: number | null;
    symbol_stats: SymbolStats[];
}

interface DailyProfit {
    date: string;
    total_profit: number;
    order_count: number;
    win_count: number;
}

interface IntervalStats {
    interval: string;
    tracking_count: number;
    avg_profit: number;
    avg_pnl_ratio: number;
    stop_loss_count: number;
    take_profit_count: number;
}

interface ProfitCurvePoint {
    date: string;
    daily_profit: number;
    daily_profit_amount: number;
    cumulative_profit: number;
    cumulative_profit_amount: number;
    order_count: number;
    win_count: number;
    position_value: number;
}

interface ProfitCurveData {
    symbol: string;
    days: number;
    data_points: number;
    total_profit_percentage: number;
    total_profit_amount: number;
    curve: ProfitCurvePoint[];
}

interface SymbolOption {
    symbol: string;
    order_count: number;
}

const API_BASE = "/api/orders";

export default function Dashboard() {
    const [data, setData] = useState<DashboardData | null>(null);
    const [dailyProfits, setDailyProfits] = useState<DailyProfit[]>([]);
    const [intervalStats, setIntervalStats] = useState<IntervalStats[]>([]);
    const [profitCurve, setProfitCurve] = useState<ProfitCurveData | null>(null);
    const [availableSymbols, setAvailableSymbols] = useState<SymbolOption[]>([]);
    const [selectedSymbol, setSelectedSymbol] = useState<string>("");
    const [curveDays, setCurveDays] = useState<number>(90);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchDashboardData();
        fetchDailyProfits();
        fetchIntervalStats();
        fetchAvailableSymbols();
    }, []);

    useEffect(() => {
        fetchProfitCurve();
    }, [selectedSymbol, curveDays]);

    const fetchDashboardData = async () => {
        try {
            setLoading(true);
            const response = await fetch(`${API_BASE}/dashboard`);
            if (response.ok) {
                const result = await response.json();
                setData(result);
            }
        } catch (err) {
            console.error("Failed to fetch dashboard data", err);
        } finally {
            setLoading(false);
        }
    };

    const fetchDailyProfits = async () => {
        try {
            const response = await fetch(`${API_BASE}/dashboard/daily-profit?days=30`);
            if (response.ok) {
                const result = await response.json();
                setDailyProfits(result);
            }
        } catch (err) {
            console.error("Failed to fetch daily profits", err);
        }
    };

    const fetchIntervalStats = async () => {
        try {
            const response = await fetch(`${API_BASE}/dashboard/interval-stats`);
            if (response.ok) {
                const result = await response.json();
                setIntervalStats(result);
            }
        } catch (err) {
            console.error("Failed to fetch interval stats", err);
        }
    };

    const fetchProfitCurve = async () => {
        try {
            const symbolParam = selectedSymbol ? `&symbol=${selectedSymbol}` : "";
            const response = await fetch(`${API_BASE}/dashboard/profit-curve?days=${curveDays}${symbolParam}`);
            if (response.ok) {
                const result = await response.json();
                setProfitCurve(result);
            }
        } catch (err) {
            console.error("Failed to fetch profit curve", err);
        }
    };

    const fetchAvailableSymbols = async () => {
        try {
            const response = await fetch(`${API_BASE}/dashboard/available-symbols`);
            if (response.ok) {
                const result = await response.json();
                setAvailableSymbols(result);
            }
        } catch (err) {
            console.error("Failed to fetch available symbols", err);
        }
    };

    if (loading) {
        return <div className="flex h-screen w-full items-center justify-center bg-slate-900 text-slate-500">Loading dashboard...</div>;
    }

    if (!data) {
        return <div className="flex h-screen w-full items-center justify-center bg-slate-900 text-slate-500">Failed to load data</div>;
    }

    return (
        <div className="flex h-screen w-full bg-slate-900 text-slate-200 overflow-y-auto font-sans">
            <main className="flex-1 p-8 max-w-7xl mx-auto w-full">
                <header className="mb-8 flex justify-between items-center">
                    <div>
                        <h1 className="text-3xl font-bold text-white flex items-center gap-3">
                            <Activity className="text-blue-500" /> Trading Dashboard
                        </h1>
                        <p className="text-slate-400 mt-1">Overview of trading performance and statistics</p>
                    </div>
                    <button
                        onClick={fetchDashboardData}
                        className="bg-slate-800 hover:bg-slate-700 text-slate-300 px-4 py-2 rounded border border-slate-700 flex items-center gap-2 text-sm"
                    >
                        <Clock size={14} /> Refresh
                    </button>
                </header>

                {/* Key Metrics Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                    {/* Total Profit */}
                    <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
                        <div className="flex justify-between items-start mb-4">
                            <div>
                                <h3 className="text-slate-400 text-sm font-medium uppercase tracking-wider">Total Profit</h3>
                                <div className={`text-3xl font-bold mt-2 ${data.total_profit_percentage >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                                    {data.total_profit_percentage >= 0 ? '+' : ''}{data.total_profit_percentage.toFixed(2)}%
                                </div>
                            </div>
                            <div className={`p-3 rounded-lg ${data.total_profit_percentage >= 0 ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>
                                <DollarSign size={24} />
                            </div>
                        </div>
                        <div className="text-xs text-slate-500">
                            Aggregate PnL across all closed orders
                        </div>
                    </div>

                    {/* Win Rate */}
                    <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
                        <div className="flex justify-between items-start mb-4">
                            <div>
                                <h3 className="text-slate-400 text-sm font-medium uppercase tracking-wider">Win Rate</h3>
                                <div className="text-3xl font-bold mt-2 text-blue-400">
                                    {data.win_rate ? data.win_rate.toFixed(1) : 0}%
                                </div>
                            </div>
                            <div className="p-3 rounded-lg bg-blue-500/10 text-blue-400">
                                <PieChart size={24} />
                            </div>
                        </div>
                        <div className="flex gap-4 text-xs">
                            <span className="text-emerald-400">{data.win_count} Wins</span>
                            <span className="text-red-400">{data.loss_count} Losses</span>
                        </div>
                    </div>

                    {/* Total Orders */}
                    <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
                        <div className="flex justify-between items-start mb-4">
                            <div>
                                <h3 className="text-slate-400 text-sm font-medium uppercase tracking-wider">Total Orders</h3>
                                <div className="text-3xl font-bold mt-2 text-white">
                                    {data.total_orders}
                                </div>
                            </div>
                            <div className="p-3 rounded-lg bg-purple-500/10 text-purple-400">
                                <BarChart3 size={24} />
                            </div>
                        </div>
                        <div className="text-xs text-slate-500">
                            {data.closed_orders} closed, {data.open_orders} open
                        </div>
                    </div>

                    {/* Active Activity */}
                    <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
                        <div className="flex justify-between items-start mb-4">
                            <div>
                                <h3 className="text-slate-400 text-sm font-medium uppercase tracking-wider">Active</h3>
                                <div className="text-3xl font-bold mt-2 text-amber-400">
                                    {data.open_orders}
                                </div>
                            </div>
                            <div className="p-3 rounded-lg bg-amber-500/10 text-amber-400">
                                <Activity size={24} />
                            </div>
                        </div>
                        <div className="text-xs text-slate-500">
                            Currently running orders
                        </div>
                    </div>
                </div>

                {/* Performance by Symbol Table */}
                <div className="bg-slate-800/50 border border-slate-700 rounded-xl overflow-hidden">
                    <div className="p-6 border-b border-slate-700 flex justify-between items-center">
                        <h3 className="font-bold text-white flex items-center gap-2">
                            <TrendingUp size={18} className="text-blue-500" /> Performance by Symbol
                        </h3>
                    </div>
                    <div className="overflow-x-auto">
                        <table className="w-full text-left text-sm text-slate-400">
                            <thead className="bg-slate-800 text-xs uppercase font-medium text-slate-500">
                                <tr>
                                    <th className="px-6 py-4">Symbol</th>
                                    <th className="px-6 py-4 text-center">Orders</th>
                                    <th className="px-6 py-4 text-center">Win/Loss</th>
                                    <th className="px-6 py-4 text-right">Win Rate</th>
                                    <th className="px-6 py-4 text-right">Total Profit</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-700">
                                {data.symbol_stats.map((stat) => (
                                    <tr key={stat.symbol} className="hover:bg-slate-800/50 transition-colors">
                                        <td className="px-6 py-4 font-bold text-white">{stat.symbol}</td>
                                        <td className="px-6 py-4 text-center">
                                            <span className="text-slate-300">{stat.total_orders}</span>
                                            <span className="text-xs text-slate-600 ml-1">({stat.open_orders} open)</span>
                                        </td>
                                        <td className="px-6 py-4 text-center">
                                            <span className="text-emerald-400">{stat.win_count}W</span>
                                            <span className="text-slate-600 mx-1">/</span>
                                            <span className="text-red-400">{stat.loss_count}L</span>
                                        </td>
                                        <td className="px-6 py-4 text-right">
                                            <div className="flex items-center justify-end gap-2">
                                                <div className="w-16 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                                                    <div
                                                        className="h-full bg-blue-500"
                                                        style={{ width: `${stat.win_rate || 0}%` }}
                                                    ></div>
                                                </div>
                                                <span className="text-blue-400 font-mono">
                                                    {stat.win_rate ? stat.win_rate.toFixed(1) : 0}%
                                                </span>
                                            </div>
                                        </td>
                                        <td className={`px-6 py-4 text-right font-bold ${stat.total_profit >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                                            {stat.total_profit >= 0 ? '+' : ''}{stat.total_profit.toFixed(2)}%
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                    {data.symbol_stats.length === 0 && (
                        <div className="p-8 text-center text-slate-500">
                            No trading data available yet.
                        </div>
                    )}
                </div>

                {/* Profit Curve Chart */}
                <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6 mt-6">
                    <div className="flex justify-between items-center mb-4">
                        <h3 className="font-bold text-white flex items-center gap-2">
                            <LineChart size={18} className="text-cyan-500" /> 收益曲线
                        </h3>
                        <div className="flex items-center gap-4">
                            <select
                                value={curveDays}
                                onChange={(e) => setCurveDays(Number(e.target.value))}
                                className="bg-slate-900 border border-slate-700 rounded px-3 py-1.5 text-sm text-slate-300 focus:outline-none focus:border-cyan-500"
                            >
                                <option value={30}>30天</option>
                                <option value={60}>60天</option>
                                <option value={90}>90天</option>
                                <option value={180}>180天</option>
                                <option value={365}>365天</option>
                            </select>
                            <select
                                value={selectedSymbol}
                                onChange={(e) => setSelectedSymbol(e.target.value)}
                                className="bg-slate-900 border border-slate-700 rounded px-3 py-1.5 text-sm text-slate-300 focus:outline-none focus:border-cyan-500"
                            >
                                <option value="">全部币种</option>
                                {availableSymbols.map((s) => (
                                    <option key={s.symbol} value={s.symbol}>
                                        {s.symbol} ({s.order_count})
                                    </option>
                                ))}
                            </select>
                        </div>
                    </div>

                    {profitCurve && profitCurve.curve.length > 0 ? (
                        <div>
                            {/* Summary Stats */}
                            <div className="grid grid-cols-4 gap-4 mb-4">
                                <div className="bg-slate-900/50 rounded-lg p-3 text-center">
                                    <div className="text-slate-500 text-xs mb-1">累计收益率</div>
                                    <div className={`text-xl font-bold ${(profitCurve.total_profit_percentage || 0) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                                        {(profitCurve.total_profit_percentage || 0) >= 0 ? '+' : ''}
                                        {(profitCurve.total_profit_percentage || 0).toFixed(2)}%
                                    </div>
                                </div>
                                <div className="bg-slate-900/50 rounded-lg p-3 text-center">
                                    <div className="text-slate-500 text-xs mb-1">累计收益金额</div>
                                    <div className={`text-xl font-bold ${(profitCurve.total_profit_amount || 0) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                                        {(profitCurve.total_profit_amount || 0) >= 0 ? '+' : ''}
                                        ${(profitCurve.total_profit_amount || 0).toFixed(2)}
                                    </div>
                                </div>
                                <div className="bg-slate-900/50 rounded-lg p-3 text-center">
                                    <div className="text-slate-500 text-xs mb-1">数据点</div>
                                    <div className="text-xl font-bold text-cyan-400">{profitCurve.data_points}</div>
                                </div>
                                <div className="bg-slate-900/50 rounded-lg p-3 text-center">
                                    <div className="text-slate-500 text-xs mb-1">筛选币种</div>
                                    <div className="text-xl font-bold text-purple-400">{profitCurve.symbol}</div>
                                </div>
                            </div>

                            {/* Simple Bar Chart */}
                            <div className="h-48 flex items-end gap-1 bg-slate-900/30 rounded-lg p-4">
                                {profitCurve.curve.slice(-30).map((point, idx) => {
                                    const maxAbs = Math.max(
                                        ...profitCurve.curve.slice(-30).map(p => Math.abs(p.cumulative_profit)),
                                        1
                                    );
                                    const heightPercent = Math.min(Math.abs(point.cumulative_profit) / maxAbs * 100, 100);
                                    const isPositive = point.cumulative_profit >= 0;
                                    return (
                                        <div
                                            key={idx}
                                            className="flex-1 flex flex-col items-center justify-end h-full relative group"
                                        >
                                            <div
                                                className={`w-full rounded-t transition-all duration-300 ${isPositive ? 'bg-emerald-500/70 hover:bg-emerald-400' : 'bg-red-500/70 hover:bg-red-400'}`}
                                                style={{ height: `${heightPercent}%`, minHeight: '2px' }}
                                            ></div>
                                            <div className="absolute bottom-full mb-2 hidden group-hover:block bg-slate-800 border border-slate-600 rounded px-2 py-1 text-xs whitespace-nowrap z-10">
                                                <div className="text-slate-400 font-bold">{point.date}</div>
                                                <div className={isPositive ? 'text-emerald-400' : 'text-red-400'}>
                                                    累计: {point.cumulative_profit.toFixed(2)}% (${point.cumulative_profit_amount?.toFixed(2) || '0.00'})
                                                </div>
                                                <div className="text-slate-500">
                                                    日: {point.daily_profit.toFixed(2)}% (${point.daily_profit_amount?.toFixed(2) || '0.00'})
                                                </div>
                                                <div className="text-slate-600 text-[10px]">{point.order_count} 单</div>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                            <div className="flex justify-between text-xs text-slate-500 mt-2 px-4">
                                <span>{profitCurve.curve[Math.max(0, profitCurve.curve.length - 30)]?.date || ''}</span>
                                <span>{profitCurve.curve[profitCurve.curve.length - 1]?.date || ''}</span>
                            </div>
                        </div>
                    ) : (
                        <div className="text-center text-slate-500 py-12">暂无收益曲线数据</div>
                    )}
                </div>

                {/* Daily Profit & Interval Stats Row */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">

                    {/* Daily Profit Chart */}
                    <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
                        <h3 className="font-bold text-white flex items-center gap-2 mb-4">
                            <BarChart3 size={18} className="text-emerald-500" /> 每日盈亏 (30天)
                        </h3>
                        {dailyProfits.length > 0 ? (
                            <div className="space-y-2 max-h-64 overflow-y-auto">
                                {dailyProfits.map((day) => (
                                    <div key={day.date} className="flex justify-between items-center text-sm">
                                        <span className="text-slate-400">{day.date}</span>
                                        <div className="flex items-center gap-4">
                                            <span className="text-slate-500 text-xs">{day.order_count} 单</span>
                                            <span className={`font-mono ${day.total_profit >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                                                {day.total_profit >= 0 ? '+' : ''}{day.total_profit.toFixed(2)}%
                                            </span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="text-center text-slate-500 py-8">暂无数据</div>
                        )}
                    </div>

                    {/* Interval Stats */}
                    <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
                        <h3 className="font-bold text-white flex items-center gap-2 mb-4">
                            <Clock size={18} className="text-blue-500" /> 周期盈亏追踪
                        </h3>
                        {intervalStats.length > 0 ? (
                            <div className="space-y-3">
                                {intervalStats.map((stat) => (
                                    <div key={stat.interval} className="bg-slate-900/50 rounded-lg p-3">
                                        <div className="flex justify-between items-center mb-2">
                                            <span className="text-white font-bold">{stat.interval}</span>
                                            <span className={`font-mono ${stat.avg_profit >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                                                {stat.avg_profit >= 0 ? '+' : ''}{stat.avg_profit.toFixed(2)}%
                                            </span>
                                        </div>
                                        <div className="flex justify-between text-xs text-slate-500">
                                            <span>{stat.tracking_count} 次追踪</span>
                                            <span className="text-emerald-400">{stat.take_profit_count} 止盈</span>
                                            <span className="text-red-400">{stat.stop_loss_count} 止损</span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="text-center text-slate-500 py-8">暂无追踪数据</div>
                        )}
                    </div>
                </div>
            </main>
        </div>
    );
}
