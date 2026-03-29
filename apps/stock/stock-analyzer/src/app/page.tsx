"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { RefreshCw, TrendingUp, TrendingDown, Minus, ChevronDown, ChevronUp, BarChart2, Zap, Clock, AlertCircle, Search, Layers, Tag, ArrowRight } from "lucide-react";

// ─── Types ───────────────────────────────────────────────
interface Stock {
  symbol: string;
  name: string;
  close: number;
  change_pct: number;
  volume: number;
  turnover: number;
  industry: string;
}

interface Group {
  name: string;
  total_stocks: number;
  hit_stocks: number;
  avg_change: number;
  up_count: number;
  down_count: number;
  strength: string;
  strength_score: number;
  summary: string;
  stocks: Stock[];
}

interface ResultData {
  status: string;
  updated_at: string | null;
  total_hit: number;
  groups: Group[];
  type: "industry" | "concept";
}

// ─── Helpers ─────────────────────────────────────────────
function strengthColor(s: string) {
  if (s === "强势") return "text-red-500 bg-red-50";
  if (s === "偏强") return "text-orange-500 bg-orange-50";
  if (s === "偏弱") return "text-blue-500 bg-blue-50";
  if (s === "弱势") return "text-green-600 bg-green-50";
  return "text-gray-500 bg-gray-100";
}

function changeColor(v: number) {
  if (v > 0) return "text-red-500";
  if (v < 0) return "text-green-600";
  return "text-gray-500";
}

// ─── Mock data for demo ──────────────────────────────────
const MOCK_INDUSTRY: ResultData = {
  status: "demo",
  updated_at: new Date().toLocaleString("zh-CN"),
  total_hit: 12,
  type: "industry",
  groups: [
    {
      name: "医药生物",
      total_stocks: 186,
      hit_stocks: 4,
      avg_change: -1.32,
      up_count: 54,
      down_count: 112,
      strength: "偏弱",
      strength_score: 35,
      summary: "医药生物行业今日偏弱，平均涨跌幅↓1.32%，共186只成分股。",
      stocks: [
        { symbol: "600276", name: "恒瑞医药", close: 42.1, change_pct: -0.8, volume: 3567800, turnover: 2.3, industry: "医药生物" },
        { symbol: "300015", name: "爱尔眼科", close: 18.6, change_pct: -1.1, volume: 2134500, turnover: 1.8, industry: "医药生物" },
        { symbol: "000661", name: "长春高新", close: 88.4, change_pct: -2.1, volume: 987600, turnover: 3.1, industry: "医药生物" },
        { symbol: "603259", name: "药明康德", close: 56.7, change_pct: -0.5, volume: 1823400, turnover: 1.5, industry: "医药生物" },
      ],
    },
    {
      name: "电子",
      total_stocks: 312,
      hit_stocks: 3,
      avg_change: 0.45,
      up_count: 178,
      down_count: 102,
      strength: "偏强",
      strength_score: 65,
      summary: "电子行业今日偏强，平均涨跌幅↑0.45%，共312只成分股。",
      stocks: [
        { symbol: "002230", name: "科大讯飞", close: 38.9, change_pct: 1.2, volume: 4567800, turnover: 4.2, industry: "电子" },
        { symbol: "603501", name: "韦尔股份", close: 72.3, change_pct: 0.8, volume: 1234500, turnover: 2.1, industry: "电子" },
        { symbol: "688012", name: "中微公司", close: 61.2, change_pct: -0.3, volume: 987600, turnover: 1.8, industry: "电子" },
      ],
    },
    {
      name: "银行",
      total_stocks: 42,
      hit_stocks: 2,
      avg_change: -0.21,
      up_count: 18,
      down_count: 22,
      strength: "中性",
      strength_score: 50,
      summary: "银行行业今日中性，平均涨跌幅↓0.21%，共42只成分股。",
      stocks: [
        { symbol: "601328", name: "交通银行", close: 6.84, change_pct: -0.1, volume: 2345600, turnover: 0.8, industry: "银行" },
        { symbol: "600015", name: "华夏银行", close: 7.21, change_pct: -0.4, volume: 1876400, turnover: 0.9, industry: "银行" },
      ],
    },
  ],
};

const MOCK_CONCEPT: ResultData = {
  status: "demo",
  updated_at: new Date().toLocaleString("zh-CN"),
  total_hit: 8,
  type: "concept",
  groups: [
    {
      name: "人工智能",
      total_stocks: 156,
      hit_stocks: 3,
      avg_change: 2.35,
      up_count: 98,
      down_count: 45,
      strength: "强势",
      strength_score: 85,
      summary: "人工智能概念今日强势，平均涨跌幅↑2.35%，共156只成分股。",
      stocks: [
        { symbol: "002230", name: "科大讯飞", close: 38.9, change_pct: 3.2, volume: 5678900, turnover: 5.1, industry: "人工智能" },
        { symbol: "688981", name: "寒武纪", close: 156.7, change_pct: 2.8, volume: 1234000, turnover: 6.3, industry: "人工智能" },
        { symbol: "300750", name: "宁德时代", close: 182.3, change_pct: 1.5, volume: 3456700, turnover: 2.8, industry: "人工智能" },
      ],
    },
    {
      name: "新能源汽车",
      total_stocks: 234,
      hit_stocks: 2,
      avg_change: -0.85,
      up_count: 87,
      down_count: 132,
      strength: "偏弱",
      strength_score: 38,
      summary: "新能源汽车概念今日偏弱，平均涨跌幅↓0.85%，共234只成分股。",
      stocks: [
        { symbol: "002594", name: "比亚迪", close: 267.8, change_pct: -1.2, volume: 4567800, turnover: 3.2, industry: "新能源汽车" },
        { symbol: "300124", name: "汇川技术", close: 78.9, change_pct: -0.5, volume: 1234500, turnover: 2.1, industry: "新能源汽车" },
      ],
    },
    {
      name: "芯片",
      total_stocks: 89,
      hit_stocks: 3,
      avg_change: 1.56,
      up_count: 56,
      down_count: 28,
      strength: "偏强",
      strength_score: 68,
      summary: "芯片概念今日偏强，平均涨跌幅↑1.56%，共89只成分股。",
      stocks: [
        { symbol: "688012", name: "中微公司", close: 61.2, change_pct: 2.1, volume: 987600, turnover: 3.5, industry: "芯片" },
        { symbol: "603501", name: "韦尔股份", close: 72.3, change_pct: 1.8, volume: 1234500, turnover: 2.9, industry: "芯片" },
        { symbol: "688008", name: "澜起科技", close: 45.6, change_pct: 0.9, volume: 765400, turnover: 2.2, industry: "芯片" },
      ],
    },
  ],
};

// ─── Group Card ──────────────────────────────────────────
function GroupCard({ group, activeTab, onNavigate }: { group: Group, activeTab: string, onNavigate: (type: string, name: string) => void }) {
  const handleClick = () => {
    // Navigate to board detail
    onNavigate(activeTab, group.name);
  };

  return (
    <div className="border border-border rounded-xl overflow-hidden bg-background shadow-sm hover:shadow-md transition-shadow">
      {/* Header - click to navigate */}
      <button
        onClick={handleClick}
        className="w-full text-left px-5 py-4 flex items-center gap-4 hover:bg-muted/40 transition-colors"
      >
        {/* 名称 + 强弱 */}
        <div className="flex items-center gap-2 min-w-0 flex-1">
          <span className="font-semibold text-base truncate">{group.name}</span>
          <span className={`text-xs px-2 py-0.5 rounded-full font-medium flex-shrink-0 ${strengthColor(group.strength)}`}>
            {group.strength}
          </span>
        </div>

        {/* 今日涨跌 */}
        <div className={`text-sm font-mono font-medium flex-shrink-0 ${changeColor(group.avg_change)}`}>
          {group.avg_change >= 0 ? "+" : ""}{group.avg_change.toFixed(2)}%
        </div>

        {/* 上涨/下跌比 */}
        <div className="hidden sm:flex items-center gap-1 text-xs flex-shrink-0">
          <span className="text-red-500">↑{group.up_count}</span>
          <span className="text-gray-300">/</span>
          <span className="text-green-600">↓{group.down_count}</span>
        </div>

        {/* 命中股数 */}
        <div className="flex items-center gap-1 flex-shrink-0">
          <Zap size={13} className="text-orange-400" />
          <span className="text-sm font-semibold text-orange-500">{group.hit_stocks}</span>
          <span className="text-xs text-muted-foreground">只</span>
        </div>

        <ArrowRight size={16} className="text-muted-foreground flex-shrink-0" />
      </button>

      {/* 摘要 */}
      <div className="px-5 pb-3 text-xs text-muted-foreground border-t border-border/50 pt-2.5">
        {group.summary}
      </div>
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────
export default function Home() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<"industry" | "concept">("industry");
  const [data, setData] = useState<ResultData | null>(null);
  const [boardData, setBoardData] = useState<Group | null>(null);
  const [boardLoading, setBoardLoading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [search, setSearch] = useState("");
  const [sortBy, setSortBy] = useState<"hit" | "change" | "strength">("hit");
  const [filterStrength, setFilterStrength] = useState<string>("全部");

  const handleNavigate = async (type: string, boardName: string) => {
    setBoardLoading(true);
    try {
      const res = await fetch(`/api/data?type=${type}&board=${encodeURIComponent(boardName)}`);
      if (res.ok) {
        const json = await res.json();
        setBoardData(json);
      }
    } catch (e) {
      console.error('Failed to load board:', e);
    }
    setBoardLoading(false);
  };

  const handleBack = () => {
    setBoardData(null);
  };

  const fetchData = useCallback(async () => {
    try {
      const type = activeTab;
      const res = await fetch(`/api/data?type=${type}`);
      if (!res.ok) throw new Error("fetch failed");
      const json = await res.json();
      if (json.status === "no_data" || !json.groups?.length) {
        setData(type === "industry" ? MOCK_INDUSTRY : MOCK_CONCEPT);
      } else {
        setData(json);
      }
    } catch {
      setData(activeTab === "industry" ? MOCK_INDUSTRY : MOCK_CONCEPT);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [activeTab]);

  useEffect(() => { 
    setLoading(true);
    fetchData(); 
  }, [fetchData]);

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await fetch(`/api/refresh?type=${activeTab}`, { method: "POST" });
    } catch {}
    await fetchData();
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-10 h-10 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-sm text-muted-foreground">加载中...</p>
        </div>
      </div>
    );
  }

  const groups = data?.groups || [];

  // 过滤 + 搜索 + 排序
  let filtered = groups.filter((g) => {
    const matchSearch = search
      ? g.name.includes(search) ||
        g.stocks.some((s) => s.name.includes(search) || s.symbol.includes(search))
      : true;
    const matchStrength = filterStrength === "全部" ? true : g.strength === filterStrength;
    return matchSearch && matchStrength;
  });

  filtered = [...filtered].sort((a, b) => {
    if (sortBy === "hit") return b.hit_stocks - a.hit_stocks;
    if (sortBy === "change") return a.avg_change - b.avg_change;
    if (sortBy === "strength") return a.strength_score - b.strength_score;
    return 0;
  });

  const isDemo = data?.status === "demo";
  const totalStocks = groups.reduce((s, g) => s + g.hit_stocks, 0);
  const totalGroups = groups.length;

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-10 bg-background/90 backdrop-blur border-b border-border">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center gap-4">
          <div className="flex items-center gap-2">
            <BarChart2 size={20} className="text-primary" />
            <h1 className="font-bold text-lg tracking-tight">A股板块雷达</h1>
          </div>
          
          {/* Tab切换 */}
          <div className="flex items-center gap-1 bg-muted rounded-lg p-0.5">
            <button
              onClick={() => setActiveTab("industry")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                activeTab === "industry"
                  ? "bg-background text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <Layers size={14} />
              <span className="hidden sm:inline">行业板块</span>
            </button>
            <button
              onClick={() => setActiveTab("concept")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                activeTab === "concept"
                  ? "bg-background text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <Tag size={14} />
              <span className="hidden sm:inline">概念板块</span>
            </button>
          </div>

          <div className="flex-1" />
          {isDemo && (
            <div className="flex items-center gap-1 text-xs text-orange-500 bg-orange-50 px-2 py-1 rounded-full">
              <AlertCircle size={12} />
              <span>演示数据</span>
            </div>
          )}
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <Clock size={12} />
            <span>{data?.updated_at || "—"}</span>
          </div>
          {(() => {
            const now = new Date();
            const day = now.getDay();
            const isWeekday = day >= 1 && day <= 5;
            return isWeekday ? (
              <button
                onClick={handleRefresh}
                disabled={refreshing}
                className="flex items-center gap-1.5 text-xs bg-primary text-primary-foreground px-3 py-1.5 rounded-lg hover:opacity-90 disabled:opacity-50 transition-opacity"
              >
                <RefreshCw size={12} className={refreshing ? "animate-spin" : ""} />
                {refreshing ? "采集中..." : "刷新数据"}
              </button>
            ) : (
              <span className="flex items-center gap-1.5 text-xs bg-muted text-muted-foreground px-3 py-1.5 rounded-lg">
                周末休息，周一自动更新
              </span>
            );
          })()}
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-6 space-y-6">
        {/* 统计卡片 */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { label: "涉及股票", value: totalStocks, unit: "只", icon: <Zap size={16} className="text-orange-400" /> },
            { label: activeTab === "industry" ? "行业板块" : "概念板块", value: totalGroups, unit: "个", icon: <BarChart2 size={16} className="text-blue-400" /> },
            { label: "今日上涨", value: groups.filter(g => g.avg_change > 0).length, unit: "个", icon: <TrendingUp size={16} className="text-red-400" /> },
            { label: "今日下跌", value: groups.filter(g => g.avg_change < 0).length, unit: "个", icon: <TrendingDown size={16} className="text-green-500" /> },
          ].map((c) => (
            <div key={c.label} className="bg-muted/50 border border-border rounded-xl px-4 py-3 flex items-center gap-3">
              <div className="bg-background rounded-lg p-1.5 shadow-sm">{c.icon}</div>
              <div>
                <div className="text-xs text-muted-foreground">{c.label}</div>
                <div className="font-bold text-lg leading-tight">
                  {c.value}<span className="text-xs font-normal text-muted-foreground ml-0.5">{c.unit}</span>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* 过滤工具栏 */}
        <div className="flex flex-wrap items-center gap-3">
          {/* 搜索 */}
          <div className="relative">
            <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="搜索行业/股票..."
              className="pl-8 pr-3 py-1.5 text-sm border border-border rounded-lg bg-background focus:outline-none focus:ring-1 focus:ring-ring w-44"
            />
          </div>

          {/* 强弱过滤 */}
          <div className="flex items-center gap-1.5">
            {["全部", "强势", "偏强", "中性", "偏弱", "弱势"].map((s) => (
              <button
                key={s}
                onClick={() => setFilterStrength(s)}
                className={`text-xs px-2.5 py-1 rounded-lg border transition-colors ${
                  filterStrength === s
                    ? "bg-primary text-primary-foreground border-primary"
                    : "border-border text-muted-foreground hover:border-foreground/30"
                }`}
              >
                {s}
              </button>
            ))}
          </div>

          <div className="flex-1" />

          {/* 排序 */}
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            <span>排序：</span>
            {[["hit", "命中数"], ["change", "跌幅优先"], ["strength", "弱势优先"]].map(([k, label]) => (
              <button
                key={k}
                onClick={() => setSortBy(k as typeof sortBy)}
                className={`px-2 py-1 rounded border transition-colors ${
                  sortBy === k
                    ? "bg-foreground text-background border-foreground"
                    : "border-border hover:border-foreground/30"
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        {/* 板块列表 */}
        {filtered.length === 0 ? (
          <div className="text-center py-20 text-muted-foreground">
            <Minus size={32} className="mx-auto mb-3 opacity-30" />
            <p>暂无符合条件的结果</p>
          </div>
        ) : (
          <div className="space-y-3">
            {filtered.map((g) => (
              <GroupCard key={g.name} group={g} activeTab={activeTab} onNavigate={handleNavigate} />
            ))}
          </div>
        )}

        {/* 板块详情 */}
        {boardData && (
          <div className="fixed inset-0 z-50 bg-background overflow-auto">
            <div className="max-w-6xl mx-auto p-4">
              <button
                onClick={handleBack}
                className="mb-4 flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
              >
                <ChevronDown size={16} className="rotate-90" />
                返回板块列表
              </button>
              
              <div className="bg-muted/50 rounded-xl p-4">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h2 className="text-xl font-bold">{boardData.name}</h2>
                    <p className="text-sm text-muted-foreground">{activeTab === 'industry' ? '行业板块' : '概念板块'}</p>
                  </div>
                  <div className="text-right">
                    <div className={`text-2xl font-bold ${changeColor(boardData.avg_change)}`}>
                      {boardData.avg_change >= 0 ? "+" : ""}{boardData.avg_change.toFixed(2)}%
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {boardData.up_count}↑ / {boardData.down_count}↓
                    </div>
                  </div>
                </div>
                
                <p className="text-sm text-muted-foreground mb-4">{boardData.summary}</p>
                
                {boardLoading ? (
                  <div className="py-10 text-center">
                    <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto" />
                  </div>
                ) : (
                  <div className="border-t border-border">
                    <div className="grid grid-cols-[2fr_1fr_1fr_1fr_1fr] gap-2 px-5 py-2 bg-muted/50 text-xs text-muted-foreground font-medium">
                      <span>股票</span>
                      <span className="text-right">现价</span>
                      <span className="text-right">涨跌</span>
                      <span className="text-right">成交量</span>
                      <span className="text-right">换手率</span>
                    </div>
                    {boardData.stocks?.map((s: Stock) => (
                      <div
                        key={s.symbol}
                        onClick={() => router.push(`/stock/${s.symbol}`)}
                        className="grid grid-cols-[2fr_1fr_1fr_1fr_1fr] gap-2 px-5 py-3 border-t border-border/40 hover:bg-muted/30 cursor-pointer"
                      >
                        <div>
                          <div className="text-sm font-medium">{s.name}</div>
                          <div className="text-xs text-muted-foreground font-mono">{s.symbol}</div>
                        </div>
                        <div className="text-right text-sm font-mono font-semibold">{s.close?.toFixed(2) || "-"}</div>
                        <div className={`text-right text-sm font-mono ${changeColor(s.change_pct)}`}>
                          {s.change_pct >= 0 ? "+" : ""}{s.change_pct?.toFixed(2) || 0}%
                        </div>
                        <div className="text-right text-xs text-muted-foreground font-mono">
                          {s.volume ? (s.volume / 10000).toFixed(1) + "万" : "-"}
                        </div>
                        <div className="text-right text-xs text-muted-foreground font-mono">
                          {s.turnover?.toFixed(1) || 0}%
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* 说明 */}
        <div className="text-xs text-muted-foreground border border-border rounded-xl p-4 space-y-1.5">
          <p className="font-medium text-foreground mb-2">📖 板块强弱说明</p>
          <p>• <b>强势</b>：平均涨幅 ≥2% 或上涨股占比 ≥70%</p>
          <p>• <b>偏强</b>：平均涨幅 0.5%~2% 或上涨股占比 55%~70%</p>
          <p>• <b>中性</b>：平均涨幅 -0.5%~0.5% 或上涨股占比 45%~55%</p>
          <p>• <b>偏弱</b>：平均跌幅 0.5%~2% 或上涨股占比 30%~45%</p>
          <p>• <b>弱势</b>：平均跌幅 ≥2% 或上涨股占比 ≤30%</p>
          <p className="text-orange-500 pt-1">⚠️ 本工具仅供市场参考，不构成投资建议</p>
        </div>
      </main>
    </div>
  );
}
