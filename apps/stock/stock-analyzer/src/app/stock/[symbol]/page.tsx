"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, BarChart2, Tag, Building2 } from "lucide-react";
import KLineChart from "./KLineChart";

// ─── Types ───────────────────────────────────────────────
interface KlineData {
  date: string;
  open: number;
  close: number;
  high: number;
  low: number;
  volume: number;
  amount: number;
  change_pct: number;
}

interface Indicators {
  daily:   { ma: Record<number, number | null>; kdj: { k: number | null; d: number | null; j: number | null } };
  weekly:  { ma: Record<number, number | null>; kdj: { k: number | null; d: number | null; j: number | null } };
  monthly: { ma: Record<number, number | null>; kdj: { k: number | null; d: number | null; j: number | null } };
}

interface StockDetail {
  symbol: string;
  name: string;
  listed_date: string;
  industries: string[];
  concepts: string[];
  klines: {
    daily:   KlineData[];
    weekly:  KlineData[];
    monthly: KlineData[];
  };
  indicators: Indicators;
  updated_at: string;
}

// ─── Helpers ─────────────────────────────────────────────
function changeColor(v: number) {
  if (v > 0) return "text-red-500";
  if (v < 0) return "text-green-600";
  return "text-gray-500";
}

function formatVolume(v: number) {
  if (v >= 100000000) return (v / 100000000).toFixed(2) + "亿";
  if (v >= 10000) return (v / 10000).toFixed(2) + "万";
  return v?.toLocaleString() || "0";
}

// ─── Main Page ────────────────────────────────────────────
export default function StockDetailPage() {
  const params = useParams();
  const router = useRouter();
  const symbol = params.symbol as string;

  const [stock, setStock] = useState<StockDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [period, setPeriod] = useState<"daily" | "weekly" | "monthly">("daily");

  useEffect(() => {
    const fetchStock = async () => {
      try {
        const res = await fetch(`/api/stock/${symbol}`);
        if (!res.ok) {
          setError("股票数据未找到");
          return;
        }
        const data = await res.json();
        setStock(data);
      } catch {
        setError("加载失败");
      } finally {
        setLoading(false);
      }
    };
    fetchStock();
  }, [symbol]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-10 h-10 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (error || !stock) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-muted-foreground mb-4">{error || "数据未找到"}</p>
          <button onClick={() => router.back()} className="text-primary hover:underline">
            返回
          </button>
        </div>
      </div>
    );
  }

  // 使用最后一根日K作为当日行情
  const dailyBars = stock.klines?.daily || [];
  const lastBar = dailyBars[dailyBars.length - 1];
  const changePct = lastBar?.change_pct || 0;
  const isUp = changePct >= 0;

  const currentBars = stock.klines?.[period] || [];
  const currentMa   = stock.indicators?.[period]?.ma || {};
  const currentKdj  = stock.indicators?.[period]?.kdj;

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-10 bg-background/90 backdrop-blur border-b border-border">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center gap-4">
          <button
            onClick={() => router.back()}
            className="flex items-center gap-1 text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft size={20} />
          </button>
          <div>
            <h1 className="font-bold text-lg">{stock.name}</h1>
            <span className="text-sm text-muted-foreground font-mono">{stock.symbol}</span>
          </div>
          <div className="flex-1" />
          {lastBar && (
            <div className="text-right">
              <div className={`text-2xl font-bold ${changeColor(changePct)}`}>
                {lastBar.close.toFixed(2)}
              </div>
              <div className={`text-sm ${changeColor(changePct)}`}>
                {isUp ? "+" : ""}{changePct.toFixed(2)}%
              </div>
            </div>
          )}
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-6 space-y-6">
        {/* 最新K线数据 */}
        {lastBar && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-muted/50 rounded-xl p-4">
              <div className="text-xs text-muted-foreground">今开</div>
              <div className={`font-semibold ${changeColor(lastBar.open - (lastBar.close / (1 + changePct / 100)))}`}>
                {lastBar.open.toFixed(2)}
              </div>
            </div>
            <div className="bg-muted/50 rounded-xl p-4">
              <div className="text-xs text-muted-foreground">最高</div>
              <div className="font-semibold text-red-500">{lastBar.high.toFixed(2)}</div>
            </div>
            <div className="bg-muted/50 rounded-xl p-4">
              <div className="text-xs text-muted-foreground">最低</div>
              <div className="font-semibold text-green-600">{lastBar.low.toFixed(2)}</div>
            </div>
            <div className="bg-muted/50 rounded-xl p-4">
              <div className="text-xs text-muted-foreground">成交量</div>
              <div className="font-semibold">{formatVolume(lastBar.volume)}</div>
            </div>
          </div>
        )}

        {/* 行业概念标签 */}
        <div className="bg-muted/50 rounded-xl p-4 space-y-3">
          <div className="flex items-center gap-2 text-sm font-medium">
            <Building2 size={16} className="text-blue-400" />
            <span>行业</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {(stock.industries || []).map((ind, i) => (
              <span key={i} className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm">
                {ind}
              </span>
            ))}
            {(!stock.industries || stock.industries.length === 0) && (
              <span className="text-muted-foreground text-sm">暂无数据</span>
            )}
          </div>

          <div className="flex items-center gap-2 text-sm font-medium mt-4">
            <Tag size={16} className="text-purple-400" />
            <span>概念板块</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {(stock.concepts || []).map((con, i) => (
              <span key={i} className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-sm">
                {con}
              </span>
            ))}
            {(!stock.concepts || stock.concepts.length === 0) && (
              <span className="text-muted-foreground text-sm">暂无数据</span>
            )}
          </div>
        </div>

        {/* K线图 */}
        <div className="bg-muted/50 rounded-xl p-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2 text-sm font-medium">
              <BarChart2 size={16} className="text-orange-400" />
              <span>K线图</span>
              <span className="text-xs text-muted-foreground ml-2">
                ({currentBars.length}根
                {period === "daily" ? "日" : period === "weekly" ? "周" : "月"}K)
              </span>
            </div>

            {/* 周期选择器 */}
            <div className="flex items-center gap-1 bg-background rounded-lg p-0.5">
              {(["daily", "weekly", "monthly"] as const).map((p) => (
                <button
                  key={p}
                  onClick={() => setPeriod(p)}
                  className={`px-3 py-1 rounded-md text-xs font-medium transition-colors ${
                    period === p
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  {p === "daily" ? "日线" : p === "weekly" ? "周线" : "月线"}
                </button>
              ))}
            </div>
          </div>

          {currentBars.length > 0 ? (
            <KLineChart data={currentBars} period={period} ma={currentMa} />
          ) : (
            <div className="text-center py-10 text-muted-foreground">暂无K线数据</div>
          )}
        </div>

        {/* KDJ 指标 */}
        {currentKdj && (
          <div className="bg-muted/50 rounded-xl p-4">
            <div className="text-xs text-muted-foreground mb-3">
              KDJ 指标（{period === "daily" ? "日线" : period === "weekly" ? "周线" : "月线"}）
            </div>
            <div className="flex gap-6">
              {(["k", "d", "j"] as const).map((key) => {
                const val = currentKdj[key];
                let color = "text-muted-foreground";
                if (val !== null && val !== undefined) {
                  if (val > 80) color = "text-red-500";
                  else if (val < 20) color = "text-green-600";
                  else color = "text-orange-500";
                }
                return (
                  <div key={key} className="flex items-center gap-1">
                    <span className="text-xs text-muted-foreground">{key.toUpperCase()}:</span>
                    <span className={`text-sm font-mono font-semibold ${color}`}>
                      {val !== null && val !== undefined ? val.toFixed(2) : "-"}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}


        {/* 数据更新时间 */}
        <div className="text-center text-xs text-muted-foreground py-4">
          数据更新于 {stock.updated_at || "未知"}
          {stock.listed_date && ` · 上市日期 ${stock.listed_date}`}
        </div>
      </main>
    </div>
  );
}
