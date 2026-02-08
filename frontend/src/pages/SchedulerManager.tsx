import { useState, useEffect } from "react";
import { Play, Pause, Trash2, Plus, Clock, Activity, Zap } from "lucide-react";

interface Job {
    job_id: string;
    symbol: string;
    interval: string;
    schedule_type: string;
    schedule_value: number;
    next_run_time: string | null;
    status: string;
    // Trader config fields
    service?: string;
    model?: string;
    klines_count?: number;
    temperature?: number;
    enable_thinking?: boolean;
    is_trader?: boolean;
}

// 平台模型选项配置
const PLATFORM_MODELS: Record<string, string[]> = {
    guiji: [
        "deepseek-ai/DeepSeek-V3",
        "deepseek-ai/DeepSeek-V3.1-Terminus",
        "deepseek-ai/DeepSeek-R1",
        "Qwen/Qwen2.5-72B-Instruct"
    ],
    qiniu: [
        "deepseek-ai/DeepSeek-V3",
        "deepseek-ai/DeepSeek-V3.2",
        "deepseek-ai/DeepSeek-R1",
        "deepseek-ai/DeepSeek-R1-0528",
        "openai/gpt-4o",
        "openai/gpt-5",
        "openai/gpt-5.2",
        "anthropic/claude-3.5-sonnet",
        "anthropic/claude-4.0-sonnet",
        "anthropic/claude-4.5-sonnet",
        "google/gemini-2.0-flash",
        "google/gemini-2.5-flash",
        "google/gemini-2.5-pro",
        "qwen/qwen3-max",
        "kimi/kimi-k2",
        "x-ai/grok-4-fast"
    ],
    deepseek: [
        "deepseek-chat",
        "deepseek-coder",
        "deepseek-reasoner"
    ],
    kimi: [
        "moonshot-v1-8k",
        "moonshot-v1-32k",
        "moonshot-v1-128k"
    ]
};

const API_BASE = "/api/scheduler";

export default function SchedulerManager() {
    const [jobs, setJobs] = useState<Job[]>([]);
    const [schedulerStatus, setSchedulerStatus] = useState<{ running: boolean, jobs_count: number } | null>(null);
    const [loading, setLoading] = useState(true);

    // Form state
    const [newSymbol, setNewSymbol] = useState("BTCUSDT");
    const [newInterval, setNewInterval] = useState("15m");
    const [newScheduleValue, setNewScheduleValue] = useState(15);
    const [isAdding, setIsAdding] = useState(false);

    // Trader config form state
    const [newService, setNewService] = useState("guiji");
    const [newModel, setNewModel] = useState("");
    const [newKlinesCount, setNewKlinesCount] = useState(100);
    const [newTemperature, setNewTemperature] = useState(0.7);
    const [newEnableThinking, setNewEnableThinking] = useState(false);

    useEffect(() => {
        fetchJobs();
        fetchStatus();
    }, []);

    const fetchJobs = async () => {
        try {
            setLoading(true);
            const response = await fetch(`${API_BASE}/jobs`);
            if (response.ok) {
                const data = await response.json();
                setJobs(data);
            }
        } catch (err) {
            console.error("Failed to fetch jobs", err);
        } finally {
            setLoading(false);
        }
    };

    const fetchStatus = async () => {
        try {
            const response = await fetch(`${API_BASE}/status`);
            if (response.ok) {
                const data = await response.json();
                setSchedulerStatus(data);
            }
        } catch (err) {
            console.error("Failed to fetch status", err);
        }
    };

    const handleStartScheduler = async () => {
        try {
            await fetch(`${API_BASE}/start`, { method: "POST" });
            fetchStatus();
        } catch (err) {
            console.error("Failed to start scheduler", err);
        }
    };

    const handleStopScheduler = async () => {
        try {
            await fetch(`${API_BASE}/stop`, { method: "POST" });
            fetchStatus();
        } catch (err) {
            console.error("Failed to stop scheduler", err);
        }
    };

    const handleAddJob = async () => {
        try {
            setIsAdding(true);
            const payload = {
                symbol: newSymbol,
                interval: newInterval,
                schedule_type: "m",
                schedule_value: newScheduleValue,
                service: newService,
                model: newModel || null,
                klines_count: newKlinesCount,
                temperature: newTemperature,
                enable_thinking: newEnableThinking,
                is_trader: true
            };

            const response = await fetch(`${API_BASE}/jobs`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            if (response.ok) {
                await fetchJobs();
                await fetchStatus();
            } else {
                const error = await response.json();
                alert(`Failed to add job: ${error.detail}`);
            }
        } catch (err) {
            console.error("Failed to add job", err);
        } finally {
            setIsAdding(false);
        }
    };

    const handleRemoveJob = async (jobId: string) => {
        if (!confirm(`Are you sure you want to remove job ${jobId}?`)) return;

        try {
            const response = await fetch(`${API_BASE}/jobs/${jobId}`, { method: "DELETE" });
            if (response.ok) {
                fetchJobs();
                fetchStatus();
            }
        } catch (err) {
            console.error("Failed to remove job", err);
        }
    };

    const handlePauseJob = async (jobId: string) => {
        try {
            const response = await fetch(`${API_BASE}/jobs/${jobId}/pause`, { method: "POST" });
            if (response.ok) {
                fetchJobs();
            } else {
                const error = await response.json();
                alert(`暂停失败: ${error.detail}`);
            }
        } catch (err) {
            console.error("Failed to pause job", err);
        }
    };

    const handleResumeJob = async (jobId: string) => {
        try {
            const response = await fetch(`${API_BASE}/jobs/${jobId}/resume`, { method: "POST" });
            if (response.ok) {
                fetchJobs();
            } else {
                const error = await response.json();
                alert(`恢复失败: ${error.detail}`);
            }
        } catch (err) {
            console.error("Failed to resume job", err);
        }
    };

    const handleRunNow = async (jobId: string) => {
        try {
            const response = await fetch(`${API_BASE}/jobs/${jobId}/run`, { method: "POST" });
            if (response.ok) {
                alert("任务已开始执行");
            } else {
                const error = await response.json();
                alert(`执行失败: ${error.detail}`);
            }
        } catch (err) {
            console.error("Failed to run job", err);
        }
    };

    const formatDate = (dateStr: string | null) => {
        if (!dateStr) return "Pending...";
        return new Date(dateStr).toLocaleString();
    };

    return (
        <div className="flex h-screen w-full bg-slate-900 text-slate-200 overflow-y-auto font-sans">
            <main className="flex-1 p-8 max-w-6xl mx-auto w-full">
                <header className="mb-8 flex justify-between items-center">
                    <div>
                        <h1 className="text-3xl font-bold text-white flex items-center gap-3">
                            <Clock className="text-purple-500" /> Scheduler Manager
                        </h1>
                        <p className="text-slate-400 mt-1">Manage automated AI trading analysis jobs</p>
                    </div>

                    <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2 px-4 py-2 bg-slate-800 rounded-lg border border-slate-700">
                            <div className={`w-3 h-3 rounded-full ${schedulerStatus?.running ? 'bg-emerald-500 animate-pulse' : 'bg-red-500'}`}></div>
                            <span className="text-sm font-medium">
                                {schedulerStatus?.running ? 'Running' : 'Stopped'}
                            </span>
                        </div>

                        {schedulerStatus?.running ? (
                            <button
                                onClick={handleStopScheduler}
                                className="bg-red-500/10 hover:bg-red-500/20 text-red-500 border border-red-500/50 px-4 py-2 rounded flex items-center gap-2"
                            >
                                <Pause size={16} /> Stop Scheduler
                            </button>
                        ) : (
                            <button
                                onClick={handleStartScheduler}
                                className="bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-500 border border-emerald-500/50 px-4 py-2 rounded flex items-center gap-2"
                            >
                                <Play size={16} /> Start Scheduler
                            </button>
                        )}
                    </div>
                </header>

                {/* Add New Job Panel */}
                <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6 mb-8">
                    <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                        <Plus size={18} className="text-blue-500" /> Add New Job
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
                        <div>
                            <label className="block text-xs text-slate-400 mb-1">Symbol</label>
                            <select
                                value={newSymbol}
                                onChange={(e) => setNewSymbol(e.target.value)}
                                className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm text-white focus:outline-none focus:border-blue-500"
                            >
                                <option value="BTCUSDT">BTCUSDT</option>
                                <option value="ETHUSDT">ETHUSDT</option>
                                <option value="BNBUSDT">BNBUSDT</option>
                                <option value="SOLUSDT">SOLUSDT</option>
                                <option value="XRPUSDT">XRPUSDT</option>
                                <option value="DOGEUSDT">DOGEUSDT</option>
                                <option value="ADAUSDT">ADAUSDT</option>
                                <option value="MATICUSDT">MATICUSDT</option>
                                <option value="DOTUSDT">DOTUSDT</option>
                                <option value="LTCUSDT">LTCUSDT</option>
                            </select>
                        </div>
                        <div>
                            <label className="block text-xs text-slate-400 mb-1">K-Line Interval</label>
                            <select
                                value={newInterval}
                                onChange={(e) => setNewInterval(e.target.value)}
                                className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm text-white focus:outline-none focus:border-blue-500"
                            >
                                <option value="15m">15 Minutes</option>
                                <option value="30m">30 Minutes</option>
                                <option value="1h">1 Hour</option>
                                <option value="4h">4 Hours</option>
                                <option value="1d">1 Day</option>
                            </select>
                        </div>
                        <div>
                            <label className="block text-xs text-slate-400 mb-1">Schedule (Minutes)</label>
                            <input
                                type="number"
                                min="1"
                                value={newScheduleValue}
                                onChange={(e) => setNewScheduleValue(parseInt(e.target.value))}
                                className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm text-white focus:outline-none focus:border-blue-500"
                            />
                        </div>
                    </div>

                    {/* Trader Configuration Row */}
                    <div className="grid grid-cols-1 md:grid-cols-5 gap-4 items-end mt-4">
                        <div>
                            <label className="block text-xs text-slate-400 mb-1">AI Service</label>
                            <select
                                value={newService}
                                onChange={(e) => {
                                    setNewService(e.target.value);
                                    setNewModel(""); // 切换平台时重置模型
                                }}
                                className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm text-white focus:outline-none focus:border-blue-500"
                            >
                                <option value="guiji">硅基流动</option>
                                <option value="qiniu">七牛云</option>
                                <option value="deepseek">DeepSeek</option>
                                <option value="kimi">Kimi</option>
                            </select>
                        </div>
                        <div className="col-span-2">
                            <label className="block text-xs text-slate-400 mb-1">AI Model (可输入或选择)</label>
                            <input
                                type="text"
                                list="model-options"
                                placeholder="选择或输入模型名称..."
                                value={newModel}
                                onChange={(e) => setNewModel(e.target.value)}
                                className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm text-white focus:outline-none focus:border-blue-500"
                            />
                            <datalist id="model-options">
                                {(PLATFORM_MODELS[newService] || []).map((model) => (
                                    <option key={model} value={model}>{model}</option>
                                ))}
                            </datalist>
                        </div>
                        <div>
                            <label className="block text-xs text-slate-400 mb-1">K-Lines Count</label>
                            <input
                                type="number"
                                min="50"
                                max="500"
                                value={newKlinesCount}
                                onChange={(e) => setNewKlinesCount(parseInt(e.target.value))}
                                className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm text-white focus:outline-none focus:border-blue-500"
                            />
                        </div>
                        <div>
                            <label className="block text-xs text-slate-400 mb-1">Temperature</label>
                            <input
                                type="number"
                                min="0"
                                max="2"
                                step="0.1"
                                value={newTemperature}
                                onChange={(e) => setNewTemperature(parseFloat(e.target.value))}
                                className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm text-white focus:outline-none focus:border-blue-500"
                            />
                        </div>
                        <div className="flex items-center gap-2 pt-4">
                            <input
                                type="checkbox"
                                id="enableThinking"
                                checked={newEnableThinking}
                                onChange={(e) => setNewEnableThinking(e.target.checked)}
                                className="w-4 h-4 rounded border-slate-700 bg-slate-900 text-blue-500 focus:ring-blue-500"
                            />
                            <label htmlFor="enableThinking" className="text-xs text-slate-400">Enable Thinking</label>
                        </div>
                        <button
                            onClick={handleAddJob}
                            disabled={isAdding}
                            className="bg-blue-600 hover:bg-blue-500 text-white font-medium p-2 rounded flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {isAdding ? "Adding..." : "Add Schedule"}
                        </button>
                    </div>
                </div>

                {/* Jobs List */}
                <div className="bg-slate-800/50 border border-slate-700 rounded-xl overflow-hidden">
                    <div className="p-6 border-b border-slate-700">
                        <h3 className="font-bold text-white">Scheduled Jobs ({jobs.length})</h3>
                    </div>

                    {loading ? (
                        <div className="p-8 text-center text-slate-500">Loading jobs...</div>
                    ) : jobs.length === 0 ? (
                        <div className="p-8 text-center text-slate-500">
                            No jobs scheduled. Add a job to start automated trading analysis.
                        </div>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="w-full text-left text-sm text-slate-400">
                                <thead className="bg-slate-800 text-xs uppercase font-medium text-slate-500">
                                    <tr>
                                        <th className="px-6 py-4">Symbol</th>
                                        <th className="px-6 py-4">Interval</th>
                                        <th className="px-6 py-4">Schedule</th>
                                        <th className="px-6 py-4">Next Run</th>
                                        <th className="px-6 py-4 text-center">Status</th>
                                        <th className="px-6 py-4 text-right">Actions</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-700">
                                    {jobs.map((job) => (
                                        <tr key={job.job_id} className="hover:bg-slate-800/50 transition-colors">
                                            <td className="px-6 py-4 font-bold text-white flex items-center gap-2">
                                                <Activity size={14} className="text-blue-500" />
                                                {job.symbol}
                                            </td>
                                            <td className="px-6 py-4">
                                                <span className="px-2 py-1 bg-slate-700 rounded text-xs text-slate-300">
                                                    {job.interval}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4">
                                                Every {job.schedule_value} {job.schedule_type === 'm' ? 'minutes' : 'hours'}
                                            </td>
                                            <td className="px-6 py-4 font-mono text-xs">
                                                {formatDate(job.next_run_time)}
                                            </td>
                                            <td className="px-6 py-4 text-center">
                                                <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${job.status === 'paused'
                                                    ? 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/20'
                                                    : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                                                    }`}>
                                                    {job.status === 'paused' ? '暂停中' : '运行中'}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 text-right flex justify-end gap-1">
                                                {job.status === 'paused' ? (
                                                    <button
                                                        onClick={() => handleResumeJob(job.job_id)}
                                                        className="text-slate-500 hover:text-emerald-400 transition-colors p-2 hover:bg-emerald-500/10 rounded"
                                                        title="恢复任务"
                                                    >
                                                        <Play size={16} />
                                                    </button>
                                                ) : (
                                                    <button
                                                        onClick={() => handlePauseJob(job.job_id)}
                                                        className="text-slate-500 hover:text-yellow-400 transition-colors p-2 hover:bg-yellow-500/10 rounded"
                                                        title="暂停任务"
                                                    >
                                                        <Pause size={16} />
                                                    </button>
                                                )}
                                                <button
                                                    onClick={() => handleRunNow(job.job_id)}
                                                    className="text-slate-500 hover:text-blue-400 transition-colors p-2 hover:bg-blue-500/10 rounded"
                                                    title="立即执行"
                                                >
                                                    <Zap size={16} />
                                                </button>
                                                <button
                                                    onClick={() => handleRemoveJob(job.job_id)}
                                                    className="text-slate-500 hover:text-red-400 transition-colors p-2 hover:bg-red-500/10 rounded"
                                                    title="删除任务"
                                                >
                                                    <Trash2 size={16} />
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
}
