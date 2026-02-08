import { useState, useEffect } from "react";
import { Database, Clock, Activity, StopCircle, Zap, Plus, X } from "lucide-react";

// --- Types ---
interface AIOrder {
    id: number;
    symbol: string;
    interval: string;
    recommendation: "BUY" | "SELL" | "HOLD";
    risk_level: "LOW" | "MEDIUM" | "HIGH";
    trend_status: string | null;
    momentum: string | null;
    entry_price: number | null;
    stop_loss: number | null;
    target_t1: number | null;
    target_t2: number | null;
    target_t3: number | null;
    status: string;
    created_at: string;
    closed_at: string | null;
    final_profit_percentage: number | null;
    reasoning?: string; // Added field if available
}

interface ProfitTracking {
    id: number;
    current_price: number;
    profit_percentage: number;
    tracking_interval: string;
    tracked_at: string;
}

interface TrackerStatus {
    is_running: boolean;
}

interface ProfitAnalytics {
    stats: {
        total_orders: number;
        closed_orders: number;
        open_orders: number;
        win_count: number;
        loss_count: number;
        total_profit_percentage: number;
        win_rate: number | null;
    };
}

interface RealtimeConfig {
    id: number;
    order_id: number;
    is_enabled: boolean;
    tracking_interval: string;
}

const API_BASE = "/api/orders";
const REALTIME_API_BASE = "/api/realtime";

export default function TradingOrders() {
    const [orders, setOrders] = useState<AIOrder[]>([]);
    const [selectedId, setSelectedId] = useState<number | null>(null);
    const [profitHistory, setProfitHistory] = useState<ProfitTracking[]>([]);
    const [trackerStatus, setTrackerStatus] = useState<TrackerStatus | null>(null);
    const [profitAnalytics, setProfitAnalytics] = useState<ProfitAnalytics | null>(null);
    const [realtimeConfig, setRealtimeConfig] = useState<RealtimeConfig | null>(null);
    const [loading, setLoading] = useState(true);
    const [updatingRealtime, setUpdatingRealtime] = useState(false);

    // Filters
    const [filterSymbol, setFilterSymbol] = useState("");
    const [filterStatus, setFilterStatus] = useState("");
    const [filterRecommendation, setFilterRecommendation] = useState("");
    const [filterRiskLevel, setFilterRiskLevel] = useState("");
    const [filterStartDate, setFilterStartDate] = useState("");
    const [filterEndDate, setFilterEndDate] = useState("");
    const [calculatingProfit, setCalculatingProfit] = useState(false);
    const [availableSymbols, setAvailableSymbols] = useState<{ symbol: string, order_count: number }[]>([]);

    // Create Order Modal State
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [creatingOrder, setCreatingOrder] = useState(false);
    const [newOrder, setNewOrder] = useState({
        symbol: "BTCUSDT",
        interval: "4h",
        recommendation: "BUY" as "BUY" | "SELL",
        risk_level: "MEDIUM" as "LOW" | "MEDIUM" | "HIGH",
        entry_price: 0,
        stop_loss: 0,
        target_t1: 0,
        target_t2: 0,
        target_t3: 0,
        leverage: 1,
        quantity: 0,
        open_amount: 0,
        analysis_summary: ""
    });

    const selectedOrder = orders.find(o => o.id === selectedId);

    useEffect(() => {
        fetchOrders();
        fetchTrackerStatus();
        fetchProfitAnalytics();
        fetchAvailableSymbols();
    }, [filterSymbol, filterStatus, filterRecommendation, filterRiskLevel, filterStartDate, filterEndDate]);

    useEffect(() => {
        if (selectedId) {
            fetchProfitHistory(selectedId);
            fetchRealtimeConfig(selectedId);
        }
    }, [selectedId]);

    // --- API Calls ---
    const fetchOrders = async () => {
        try {
            setLoading(true);
            const queryParams = new URLSearchParams({
                page_size: "50",
                page: "1",
                ...(filterSymbol && { symbol: filterSymbol }),
                ...(filterStatus && { status: filterStatus }),
                ...(filterRecommendation && { recommendation: filterRecommendation }),
                ...(filterRiskLevel && { risk_level: filterRiskLevel }),
                ...(filterStartDate && { start_date: filterStartDate }),
                ...(filterEndDate && { end_date: filterEndDate }),
            });
            const response = await fetch(`${API_BASE}?${queryParams}`);
            const data = await response.json();
            const fetchedOrders = data.orders || [];
            setOrders(fetchedOrders);
            if (fetchedOrders.length > 0 && !selectedId) {
                setSelectedId(fetchedOrders[0].id);
            }
        } catch (err) {
            console.error("Failed to fetch orders", err);
        } finally {
            setLoading(false);
        }
    };

    const fetchAvailableSymbols = async () => {
        try {
            const response = await fetch(`${API_BASE}/dashboard/available-symbols`);
            if (response.ok) {
                const data = await response.json();
                setAvailableSymbols(data);
            }
        } catch (err) {
            console.error("Failed to fetch available symbols", err);
        }
    };

    const calculateOrderProfit = async (orderId: number) => {
        try {
            setCalculatingProfit(true);
            const response = await fetch(`${API_BASE}/${orderId}/calculate-profit`, { method: "POST" });
            if (response.ok) {
                const data = await response.json();
                console.log("Profit calculated:", data);
                // Refresh profit history after calculation
                await fetchProfitHistory(orderId);
                await fetchOrders();
            }
        } catch (err) {
            console.error("Failed to calculate profit", err);
        } finally {
            setCalculatingProfit(false);
        }
    };

    const calculateAllProfits = async () => {
        try {
            setCalculatingProfit(true);
            const response = await fetch(`${API_BASE}/calculate-all-profits`, { method: "POST" });
            if (response.ok) {
                const data = await response.json();
                console.log("All profits calculated:", data);
                await fetchOrders();
                if (selectedId) {
                    await fetchProfitHistory(selectedId);
                }
            }
        } catch (err) {
            console.error("Failed to calculate all profits", err);
        } finally {
            setCalculatingProfit(false);
        }
    };

    const fetchTrackerStatus = async () => {
        try {
            const response = await fetch(`${API_BASE}/profit-tracker/status`);
            if (response.ok) {
                const data = await response.json();
                setTrackerStatus(data);
            }
        } catch (err) {
            console.error("Tracker status error", err);
        }
    };

    const fetchProfitAnalytics = async () => {
        try {
            const response = await fetch(`${API_BASE}/profit-analytics?period=all`);
            if (response.ok) {
                const data = await response.json();
                setProfitAnalytics(data);
            }
        } catch (err) {
            console.error("Analytics error", err);
        }
    };

    const fetchProfitHistory = async (orderId: number) => {
        try {
            const response = await fetch(`${API_BASE}/${orderId}/profits`);
            if (response.ok) {
                const data = await response.json();
                setProfitHistory(data.history || []);
            }
        } catch (err) {
            console.error("History error", err);
        }
    };

    const fetchRealtimeConfig = async (orderId: number) => {
        try {
            const response = await fetch(`${REALTIME_API_BASE}/orders/${orderId}`);
            if (response.ok) {
                const data = await response.json();
                setRealtimeConfig(data);
            } else {
                setRealtimeConfig(null);
            }
        } catch (err) {
            console.error("Failed to fetch realtime config", err);
            setRealtimeConfig(null);
        }
    };

    const toggleRealtime = async () => {
        if (!selectedId) return;
        try {
            setUpdatingRealtime(true);
            const endpoint = realtimeConfig?.is_enabled ? "disable" : "enable";
            const response = await fetch(`${REALTIME_API_BASE}/orders/${selectedId}/${endpoint}`, { method: "POST" });
            if (response.ok) {
                const data = await response.json();
                setRealtimeConfig(data);
            }
        } catch (err) {
            console.error("Failed to toggle realtime", err);
        } finally {
            setUpdatingRealtime(false);
        }
    };

    const updateRealtimeInterval = async (interval: string) => {
        if (!selectedId) return;
        try {
            setUpdatingRealtime(true);
            const response = await fetch(`${REALTIME_API_BASE}/orders/${selectedId}`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ tracking_interval: interval })
            });
            if (response.ok) {
                const data = await response.json();
                setRealtimeConfig(data);
            }
        } catch (err) {
            console.error("Failed to update interval", err);
        } finally {
            setUpdatingRealtime(false);
        }
    };

    const createOrder = async () => {
        try {
            setCreatingOrder(true);
            const response = await fetch(`${API_BASE}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(newOrder)
            });
            if (response.ok) {
                const created = await response.json();
                setShowCreateModal(false);
                setNewOrder({
                    symbol: "BTCUSDT",
                    interval: "4h",
                    recommendation: "BUY",
                    risk_level: "MEDIUM",
                    entry_price: 0,
                    stop_loss: 0,
                    target_t1: 0,
                    target_t2: 0,
                    target_t3: 0,
                    leverage: 1,
                    quantity: 0,
                    open_amount: 0,
                    analysis_summary: ""
                });
                await fetchOrders();
                setSelectedId(created.id);
            } else {
                const error = await response.json();
                alert(`创建失败: ${error.detail}`);
            }
        } catch (err) {
            console.error("Failed to create order", err);
        } finally {
            setCreatingOrder(false);
        }
    };

    const toggleTracker = async () => {
        const endpoint = trackerStatus?.is_running ? "stop" : "start";
        await fetch(`${API_BASE}/profit-tracker/${endpoint}`, { method: "POST" });
        fetchTrackerStatus();
    };

    // --- Helpers ---
    const formatTime = (isoString: string) => {
        const date = new Date(isoString);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };

    const formatDate = (isoString: string) => {
        const date = new Date(isoString);
        return date.toLocaleDateString(); // e.g., "10/25/2023"
    };

    return (
        <div className="flex h-screen w-full bg-slate-900 text-slate-200 overflow-hidden font-sans">

            {/* --- LEFT SIDEBAR: SIGNAL FEED --- */}
            <aside className="w-1/3 min-w-[350px] border-r border-slate-700 flex flex-col bg-slate-900">
                {/* Analytics Header */}
                <div className="p-4 border-b border-slate-700 bg-slate-900 z-10">
                    <div className="flex justify-between items-center mb-2">
                        <h2 className="text-sm font-bold text-slate-400 uppercase tracking-wider">Signal Feed</h2>
                        <div className="flex items-center gap-2">
                            <button
                                onClick={() => setShowCreateModal(true)}
                                className="text-xs px-2 py-1 rounded flex items-center gap-1 bg-blue-500/20 text-blue-400 hover:bg-blue-500/30"
                            >
                                <Plus size={12} /> 创建订单
                            </button>
                            <button onClick={toggleTracker} className={`text-xs px-2 py-1 rounded flex items-center gap-1 ${trackerStatus?.is_running ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'}`}>
                                {trackerStatus?.is_running ? <Activity size={12} /> : <StopCircle size={12} />}
                                {trackerStatus?.is_running ? 'LIVE' : 'STOPPED'}
                            </button>
                        </div>
                    </div>

                    {/* Quick Stats */}
                    {profitAnalytics && (
                        <div className="grid grid-cols-2 gap-2 text-xs">
                            <div className="bg-slate-800 p-2 rounded border border-slate-700">
                                <span className="text-slate-500 block">Total PnL</span>
                                <span className={`font-bold text-sm ${profitAnalytics.stats.total_profit_percentage >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                                    {profitAnalytics.stats.total_profit_percentage >= 0 ? '+' : ''}
                                    {profitAnalytics.stats.total_profit_percentage.toFixed(2)}%
                                </span>
                            </div>
                            <div className="bg-slate-800 p-2 rounded border border-slate-700">
                                <span className="text-slate-500 block">Win Rate</span>
                                <span className="font-bold text-sm text-blue-400">
                                    {profitAnalytics.stats.win_rate ? profitAnalytics.stats.win_rate.toFixed(1) : 0}%
                                </span>
                            </div>
                        </div>
                    )}
                </div>

                {/* Filters */}
                <div className="px-4 pb-2 space-y-2">
                    <div className="flex gap-2">
                        <div className="relative flex-1">
                            <input
                                type="text"
                                list="symbol-options"
                                placeholder="输入或选择币种..."
                                value={filterSymbol}
                                onChange={(e) => setFilterSymbol(e.target.value.toUpperCase())}
                                className="w-full bg-slate-800 text-xs text-white p-2 rounded border border-slate-700 focus:outline-none focus:border-blue-500"
                            />
                            <datalist id="symbol-options">
                                <option value="">全部币种</option>
                                {availableSymbols.map((s) => (
                                    <option key={s.symbol} value={s.symbol}>
                                        {s.symbol} ({s.order_count}单)
                                    </option>
                                ))}
                            </datalist>
                        </div>
                        <select
                            value={filterStatus}
                            onChange={(e) => setFilterStatus(e.target.value)}
                            className="bg-slate-800 text-xs text-white p-2 rounded border border-slate-700 flex-1 focus:outline-none focus:border-blue-500"
                        >
                            <option value="">All Status</option>
                            <option value="OPEN">Open</option>
                            <option value="CLOSED">Closed</option>
                            <option value="STOP_LOSS">Stop Loss</option>
                            <option value="TAKE_PROFIT_T1">TP T1</option>
                            <option value="TAKE_PROFIT_T2">TP T2</option>
                            <option value="TAKE_PROFIT_T3">TP T3</option>
                        </select>
                    </div>
                    <div className="flex gap-2">
                        <select
                            value={filterRecommendation}
                            onChange={(e) => setFilterRecommendation(e.target.value)}
                            className="bg-slate-800 text-xs text-white p-2 rounded border border-slate-700 flex-1 focus:outline-none focus:border-blue-500"
                        >
                            <option value="">All Direction</option>
                            <option value="BUY">BUY</option>
                            <option value="SELL">SELL</option>
                            <option value="HOLD">HOLD</option>
                        </select>
                        <select
                            value={filterRiskLevel}
                            onChange={(e) => setFilterRiskLevel(e.target.value)}
                            className="bg-slate-800 text-xs text-white p-2 rounded border border-slate-700 flex-1 focus:outline-none focus:border-blue-500"
                        >
                            <option value="">All Risk</option>
                            <option value="LOW">Low Risk</option>
                            <option value="MEDIUM">Medium Risk</option>
                            <option value="HIGH">High Risk</option>
                        </select>
                    </div>
                    <div className="flex gap-2">
                        <input
                            type="date"
                            value={filterStartDate}
                            onChange={(e) => setFilterStartDate(e.target.value)}
                            className="bg-slate-800 text-xs text-white p-2 rounded border border-slate-700 flex-1 focus:outline-none focus:border-blue-500"
                        />
                        <input
                            type="date"
                            value={filterEndDate}
                            onChange={(e) => setFilterEndDate(e.target.value)}
                            className="bg-slate-800 text-xs text-white p-2 rounded border border-slate-700 flex-1 focus:outline-none focus:border-blue-500"
                        />
                    </div>
                    <button
                        onClick={calculateAllProfits}
                        disabled={calculatingProfit}
                        className="w-full bg-blue-600 hover:bg-blue-500 text-white text-xs py-2 rounded flex items-center justify-center gap-2 disabled:opacity-50"
                    >
                        {calculatingProfit ? "Calculating..." : "Refresh All Profits"}
                    </button>
                </div>

                {/* Signals List */}
                <div className="overflow-y-auto scroll-hide flex-1 p-2 space-y-2">
                    {loading ? (
                        <div className="text-center text-slate-500 py-8">Loading signals...</div>
                    ) : (
                        orders.map(order => (
                            <div
                                key={order.id}
                                onClick={() => setSelectedId(order.id)}
                                className={`signal-card ${selectedId === order.id ? 'active' : ''}`}
                            >
                                <div className="flex justify-between items-start">
                                    <div className="flex items-center gap-2">
                                        <span className="font-bold text-white text-lg">{order.symbol}</span>
                                        <span className={`badge ${order.recommendation === 'BUY' ? 'badge-long' : 'badge-short'}`}>
                                            {order.recommendation}
                                        </span>
                                    </div>
                                    <span className="text-xs text-slate-400 flex flex-col items-end">
                                        <span>{formatTime(order.created_at)}</span>
                                        <span className="text-[10px] opacity-60">{formatDate(order.created_at)}</span>
                                    </span>
                                </div>
                                <div className="flex justify-between items-end mt-1">
                                    <div className="flex gap-2 text-xs">
                                        <span className={`badge ${order.risk_level === 'LOW' ? 'badge-risk-low' :
                                            order.risk_level === 'MEDIUM' ? 'badge-risk-med' : 'badge-risk-high'
                                            }`}>
                                            {order.risk_level} Risk
                                        </span>
                                    </div>
                                    <div className="text-right">
                                        {order.final_profit_percentage !== null ? (
                                            <span className={`text-sm font-bold ${order.final_profit_percentage >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                                                {order.final_profit_percentage >= 0 ? '+' : ''}{order.final_profit_percentage.toFixed(2)}%
                                            </span>
                                        ) : (
                                            <span className="text-xs text-amber-500">Active</span>
                                        )}
                                    </div>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </aside>

            {/* --- MAIN PANEL: DETAILS --- */}
            <main className="flex-1 flex flex-col bg-slate-900 overflow-y-auto w-full">
                {selectedOrder ? (
                    <>
                        {/* Header */}
                        <header className="p-6 border-b border-slate-700 flex justify-between items-start bg-slate-800/30">
                            <div>
                                <h1 className="text-2xl font-bold text-white flex items-center gap-3">
                                    {selectedOrder.symbol}
                                    <span className="text-xs font-normal text-slate-400 px-2 py-1 bg-slate-700 rounded border border-slate-600">ID: #{selectedOrder.id}</span>
                                </h1>
                                <div className="mt-2 text-sm text-slate-400 flex gap-4">
                                    <span>Signal ID: <span className="text-blue-400 font-mono">#{selectedOrder.id}</span></span>
                                    <span>State: <span className="text-blue-400">{selectedOrder.status}</span></span>
                                </div>
                            </div>
                            <div className="text-right flex flex-col items-end gap-2">
                                <div className={`text-3xl font-bold ${(selectedOrder.final_profit_percentage || 0) >= 0 ? 'text-emerald-400' : 'text-red-400'
                                    }`}>
                                    {(selectedOrder.final_profit_percentage || 0) >= 0 ? '+' : ''}
                                    {(selectedOrder.final_profit_percentage || 0).toFixed(2)}%
                                </div>
                                <div className="text-xs text-slate-400 uppercase tracking-wider">Current PnL</div>
                                {selectedOrder.status === 'OPEN' && (
                                    <button
                                        onClick={() => calculateOrderProfit(selectedOrder.id)}
                                        disabled={calculatingProfit}
                                        className="mt-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs px-3 py-1.5 rounded disabled:opacity-50"
                                    >
                                        {calculatingProfit ? "Calculating..." : "Calculate Profit"}
                                    </button>
                                )}
                            </div>
                        </header>

                        <div className="flex flex-1 overflow-hidden">
                            {/* Left Column: Performance Timeline */}
                            <div className="w-1/2 p-6 overflow-y-auto border-r border-slate-700">
                                {/* Real-time Configuration */}
                                <div className="mb-8 bg-slate-800/50 rounded-lg p-4 border border-slate-700">
                                    <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
                                        <Zap size={16} className="text-yellow-400" /> Real-time Execution
                                    </h3>

                                    <div className="flex items-center justify-between mb-4">
                                        <div className="flex items-center gap-3">
                                            <div className={`w-10 h-5 rounded-full relative cursor-pointer transition-colors ${realtimeConfig?.is_enabled ? 'bg-emerald-500' : 'bg-slate-600'}`} onClick={toggleRealtime}>
                                                <div className={`absolute top-1 left-1 w-3 h-3 bg-white rounded-full transition-transform ${realtimeConfig?.is_enabled ? 'translate-x-5' : 'translate-x-0'}`}></div>
                                            </div>
                                            <span className="text-sm text-slate-300">
                                                {realtimeConfig?.is_enabled ? 'Enabled' : 'Disabled'}
                                            </span>
                                        </div>
                                        {updatingRealtime && <span className="text-xs text-slate-500 animate-pulse">Updating...</span>}
                                    </div>

                                    {realtimeConfig?.is_enabled && (
                                        <div>
                                            <label className="block text-xs text-slate-400 mb-2">Tracking Interval</label>
                                            <div className="flex gap-2">
                                                {['1m', '5m', '15m'].map(interval => (
                                                    <button
                                                        key={interval}
                                                        onClick={() => updateRealtimeInterval(interval)}
                                                        className={`px-3 py-1 text-xs rounded border transition-colors ${realtimeConfig.tracking_interval === interval
                                                            ? 'bg-blue-600 border-blue-500 text-white'
                                                            : 'bg-slate-800 border-slate-600 text-slate-400 hover:bg-slate-700'
                                                            }`}
                                                    >
                                                        {interval}
                                                    </button>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </div>

                                <h3 className="text-sm font-bold text-slate-300 mb-6 flex items-center gap-2">
                                    <Clock size={16} /> Performance Tracking (Scheduled Tasks)
                                </h3>

                                <div className="pl-2">
                                    {/* Entry Point */}
                                    <div className="timeline-container">
                                        <div className="timeline-dot bg-blue-500"></div>
                                        <div className="flex justify-between items-center mb-1">
                                            <span className="text-xs font-bold text-blue-400">Signal Generated</span>
                                            <span className="text-xs text-slate-500">{formatTime(selectedOrder.created_at)}</span>
                                        </div>
                                        <div className="p-3 bg-slate-800 rounded border border-slate-700 text-xs text-slate-300">
                                            <span>Entry Price: <span className="text-white font-bold">{selectedOrder.entry_price}</span></span><br />
                                            <span className="text-slate-400 mt-1 block">Targets: TP1 {selectedOrder.target_t1} / SL {selectedOrder.stop_loss}</span>
                                        </div>
                                    </div>

                                    {/* Profit History Points */}
                                    {profitHistory.map((history, idx) => (
                                        <div key={history.id} className="timeline-container">
                                            <div className={`timeline-dot ${history.profit_percentage >= 0 ? 'profit' : 'loss'}`}></div>
                                            <div className="flex justify-between items-center mb-1">
                                                <span className={`text-xs font-bold ${history.profit_percentage >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                                                    Check {idx + 1} ({history.tracking_interval})
                                                </span>
                                                <span className="text-xs text-slate-500">{formatTime(history.tracked_at)}</span>
                                            </div>
                                            <div className={`p-3 rounded border text-xs ${history.profit_percentage >= 0
                                                ? 'bg-emerald-500/10 border-emerald-500/20'
                                                : 'bg-red-500/10 border-red-500/20'
                                                }`}>
                                                <div className="flex justify-between">
                                                    <span className="text-slate-300">Price: {history.current_price}</span>
                                                    <span className={`font-bold ${history.profit_percentage >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                                                        {history.profit_percentage >= 0 ? '+' : ''}{history.profit_percentage.toFixed(2)}%
                                                    </span>
                                                </div>
                                            </div>
                                        </div>
                                    ))}

                                    {/* Future/Pending */}
                                    {selectedOrder.status === 'OPEN' && (
                                        <div className="timeline-container">
                                            <div className="timeline-dot pending"></div>
                                            <div className="flex justify-between items-center mb-1">
                                                <span className="text-xs font-bold text-slate-500">Next Check</span>
                                                <span className="text-xs text-slate-600">Pending...</span>
                                            </div>
                                            <div className="p-3 bg-slate-800/30 rounded border border-slate-700/50 text-xs text-slate-600 border-dashed">
                                                Monitoring price action...
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </div>

                            {/* Right Column: Signal Details (Replaces JSON) */}
                            <div className="w-1/2 p-6 overflow-y-auto bg-[#1e293b]"> {/* Slightly lighter background for contrast */}
                                <h3 className="text-sm font-bold text-slate-300 mb-4 flex items-center gap-2">
                                    <Database size={16} /> Signal Analysis
                                </h3>

                                <div className="space-y-6">
                                    {/* Key Metrics Grid */}
                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="p-3 bg-slate-900/50 rounded border border-slate-700">
                                            <span className="text-xs text-slate-500 uppercase">Confidence</span>
                                            <div className="text-lg font-bold text-white">High</div>
                                        </div>
                                        <div className="p-3 bg-slate-900/50 rounded border border-slate-700">
                                            <span className="text-xs text-slate-500 uppercase">Risk/Reward</span>
                                            <div className="text-lg font-bold text-white">1:2.5</div>
                                        </div>
                                    </div>

                                    {/* Technical Targets */}
                                    <div className="p-4 bg-slate-900/50 rounded border border-slate-700">
                                        <h4 className="text-xs font-bold text-slate-400 uppercase mb-3">Technical Targets</h4>
                                        <div className="space-y-2 text-sm">
                                            <div className="flex justify-between">
                                                <span className="text-slate-400">Stop Loss</span>
                                                <span className="text-red-400 font-mono">{selectedOrder.stop_loss}</span>
                                            </div>
                                            <div className="flex justify-between">
                                                <span className="text-slate-400">Take Profit 1</span>
                                                <span className="text-emerald-400 font-mono">{selectedOrder.target_t1}</span>
                                            </div>
                                            <div className="flex justify-between">
                                                <span className="text-slate-400">Take Profit 2</span>
                                                <span className="text-emerald-400 font-mono">{selectedOrder.target_t2}</span>
                                            </div>
                                            <div className="flex justify-between">
                                                <span className="text-slate-400">Take Profit 3</span>
                                                <span className="text-emerald-400 font-mono">{selectedOrder.target_t3}</span>
                                            </div>
                                        </div>
                                    </div>

                                    {/* AI Reasoning (If available) */}
                                    <div>
                                        <h4 className="text-xs font-bold text-slate-400 uppercase mb-2">AI Reasoning</h4>
                                        <div className="p-4 bg-slate-800 rounded border border-slate-600 text-sm text-slate-300 leading-relaxed italic">
                                            {selectedOrder.reasoning ? (
                                                `"${selectedOrder.reasoning}"`
                                            ) : (
                                                <span className="text-slate-500 not-italic">No detailed reasoning available for this signal.</span>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </>
                ) : (
                    <div className="flex flex-col items-center justify-center h-full text-slate-500">
                        <Activity size={48} className="mb-4 opacity-20" />
                        <p>Select a signal from the feed to view details</p>
                    </div>
                )}
            </main>

            {/* Create Order Modal */}
            {showCreateModal && (
                <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
                    <div className="bg-slate-800 rounded-xl border border-slate-700 w-full max-w-lg p-6 max-h-[90vh] overflow-y-auto">
                        <div className="flex justify-between items-center mb-6">
                            <h3 className="text-lg font-bold text-white">创建新订单</h3>
                            <button onClick={() => setShowCreateModal(false)} className="text-slate-400 hover:text-white">
                                <X size={20} />
                            </button>
                        </div>

                        <div className="space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-xs text-slate-400 mb-1">交易对</label>
                                    <select value={newOrder.symbol} onChange={e => setNewOrder({ ...newOrder, symbol: e.target.value })} className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm text-white">
                                        <option value="BTCUSDT">BTCUSDT</option>
                                        <option value="ETHUSDT">ETHUSDT</option>
                                        <option value="BNBUSDT">BNBUSDT</option>
                                        <option value="SOLUSDT">SOLUSDT</option>
                                        <option value="XRPUSDT">XRPUSDT</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-xs text-slate-400 mb-1">方向</label>
                                    <select value={newOrder.recommendation} onChange={e => setNewOrder({ ...newOrder, recommendation: e.target.value as "BUY" | "SELL" })} className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm text-white">
                                        <option value="BUY">买入做多</option>
                                        <option value="SELL">卖出做空</option>
                                    </select>
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-xs text-slate-400 mb-1">风险等级</label>
                                    <select value={newOrder.risk_level} onChange={e => setNewOrder({ ...newOrder, risk_level: e.target.value as "LOW" | "MEDIUM" | "HIGH" })} className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm text-white">
                                        <option value="LOW">低风险</option>
                                        <option value="MEDIUM">中等风险</option>
                                        <option value="HIGH">高风险</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-xs text-slate-400 mb-1">杠杆倍数</label>
                                    <input type="number" value={newOrder.leverage} onChange={e => setNewOrder({ ...newOrder, leverage: parseFloat(e.target.value) || 1 })} className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm text-white" min="1" max="125" />
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-xs text-slate-400 mb-1">入场价格 *</label>
                                    <input type="number" step="0.01" value={newOrder.entry_price || ""} onChange={e => setNewOrder({ ...newOrder, entry_price: parseFloat(e.target.value) || 0 })} className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm text-white" placeholder="0.00" />
                                </div>
                                <div>
                                    <label className="block text-xs text-slate-400 mb-1">止损价格 *</label>
                                    <input type="number" step="0.01" value={newOrder.stop_loss || ""} onChange={e => setNewOrder({ ...newOrder, stop_loss: parseFloat(e.target.value) || 0 })} className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm text-white" placeholder="0.00" />
                                </div>
                            </div>

                            <div className="grid grid-cols-3 gap-4">
                                <div>
                                    <label className="block text-xs text-slate-400 mb-1">目标价 T1</label>
                                    <input type="number" step="0.01" value={newOrder.target_t1 || ""} onChange={e => setNewOrder({ ...newOrder, target_t1: parseFloat(e.target.value) || 0 })} className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm text-white" placeholder="0.00" />
                                </div>
                                <div>
                                    <label className="block text-xs text-slate-400 mb-1">目标价 T2</label>
                                    <input type="number" step="0.01" value={newOrder.target_t2 || ""} onChange={e => setNewOrder({ ...newOrder, target_t2: parseFloat(e.target.value) || 0 })} className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm text-white" placeholder="0.00" />
                                </div>
                                <div>
                                    <label className="block text-xs text-slate-400 mb-1">目标价 T3</label>
                                    <input type="number" step="0.01" value={newOrder.target_t3 || ""} onChange={e => setNewOrder({ ...newOrder, target_t3: parseFloat(e.target.value) || 0 })} className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm text-white" placeholder="0.00" />
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-xs text-slate-400 mb-1">开仓数量</label>
                                    <input type="number" step="0.001" value={newOrder.quantity || ""} onChange={e => setNewOrder({ ...newOrder, quantity: parseFloat(e.target.value) || 0 })} className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm text-white" placeholder="0.00" />
                                </div>
                                <div>
                                    <label className="block text-xs text-slate-400 mb-1">开仓金额</label>
                                    <input type="number" step="0.01" value={newOrder.open_amount || ""} onChange={e => setNewOrder({ ...newOrder, open_amount: parseFloat(e.target.value) || 0 })} className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm text-white" placeholder="0.00" />
                                </div>
                            </div>

                            <div>
                                <label className="block text-xs text-slate-400 mb-1">备注</label>
                                <textarea value={newOrder.analysis_summary} onChange={e => setNewOrder({ ...newOrder, analysis_summary: e.target.value })} className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm text-white h-20" placeholder="订单备注信息..." />
                            </div>
                        </div>

                        <div className="mt-6 flex justify-end gap-3">
                            <button onClick={() => setShowCreateModal(false)} className="px-4 py-2 bg-slate-700 text-slate-300 rounded hover:bg-slate-600">取消</button>
                            <button onClick={createOrder} disabled={creatingOrder || !newOrder.entry_price || !newOrder.stop_loss} className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed">
                                {creatingOrder ? "创建中..." : "确认创建"}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
