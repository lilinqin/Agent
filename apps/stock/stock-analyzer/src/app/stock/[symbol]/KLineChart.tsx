"use client";

import { useEffect, useRef, useCallback } from "react";
import {
  createChart,
  IChartApi,
  ISeriesApi,
  CandlestickData,
  HistogramData,
  ColorType,
  CrosshairMode,
  LineStyle,
  CandlestickSeries,
  HistogramSeries,
  LineSeries,
} from "lightweight-charts";

export interface KBar {
  date: string;
  open: number;
  close: number;
  high: number;
  low: number;
  volume: number;
  amount: number;
  change_pct: number;
}

interface Props {
  data: KBar[];
  period: "daily" | "weekly" | "monthly";
  ma: Record<number, number | null>;
}

const MA_COLORS: Record<number, string> = {
  5:   "#f59e0b",
  10:  "#3b82f6",
  20:  "#a855f7",
  30:  "#ec4899",
  60:  "#14b8a6",
  120: "#f97316",
  250: "#ef4444",
};

function toTimestamp(dateStr: string): number {
  // lightweight-charts 需要 UTC 时间戳（秒）
  return Math.floor(new Date(dateStr + "T00:00:00Z").getTime() / 1000);
}

export default function KLineChart({ data, period, ma }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef     = useRef<IChartApi | null>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const candleRef    = useRef<ISeriesApi<"Candlestick", any> | null>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const volumeRef    = useRef<ISeriesApi<"Histogram", any> | null>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const maRefs       = useRef<Record<number, ISeriesApi<"Line", any>>>({});

  // 初始化图表（只建一次）
  const initChart = useCallback(() => {
    if (!containerRef.current || chartRef.current) return;

    const chart = createChart(containerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "#6b7280",
        fontSize: 11,
      },
      grid: {
        vertLines: { color: "#f3f4f6", style: LineStyle.Dotted },
        horzLines: { color: "#f3f4f6", style: LineStyle.Dotted },
      },
      crosshair: { mode: CrosshairMode.Normal },
      rightPriceScale: { borderColor: "#e5e7eb" },
      timeScale: {
        borderColor: "#e5e7eb",
        timeVisible: true,
        secondsVisible: false,
      },
      handleScroll: true,
      handleScale: true,
    });

    // K线主图
    const candle = chart.addSeries(CandlestickSeries, {
      upColor:          "#ef4444",
      downColor:        "#22c55e",
      borderUpColor:    "#ef4444",
      borderDownColor:  "#22c55e",
      wickUpColor:      "#ef4444",
      wickDownColor:    "#22c55e",
    });

    // 成交量（副图，占 20% 高度）
    const volume = chart.addSeries(HistogramSeries, {
      color:    "#94a3b8",
      priceFormat:    { type: "volume" },
      priceScaleId:   "volume",
    } as any);
    chart.priceScale("volume").applyOptions({
      scaleMargins: { top: 0.82, bottom: 0 },
    });

    chartRef.current  = chart;
    candleRef.current = candle;
    volumeRef.current = volume;

    // 响应容器尺寸变化
    const ro = new ResizeObserver(() => {
      if (containerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width:  containerRef.current.clientWidth,
          height: containerRef.current.clientHeight,
        });
      }
    });
    ro.observe(containerRef.current);
    return () => ro.disconnect();
  }, []);

  // 数据变化时更新系列
  useEffect(() => {
    initChart();
    if (!chartRef.current || !candleRef.current || !volumeRef.current || !data.length) return;

    const sorted = [...data].sort((a, b) => a.date.localeCompare(b.date));

    const candleData: CandlestickData[] = sorted.map(k => ({
      time:  toTimestamp(k.date) as any,
      open:  k.open,
      high:  k.high,
      low:   k.low,
      close: k.close,
    }));

    const volumeData: HistogramData[] = sorted.map(k => ({
      time:  toTimestamp(k.date) as any,
      value: k.volume,
      color: k.close >= k.open ? "#fca5a5" : "#86efac",
    }));

    candleRef.current.setData(candleData);
    volumeRef.current.setData(volumeData);

    // MA 均线：只绘制 ma prop 中非 null 的周期
    // 先清除旧系列
    Object.values(maRefs.current).forEach(s => chartRef.current?.removeSeries(s));
    maRefs.current = {};

    const maPeriods = Object.keys(MA_COLORS).map(Number)
      .filter(p => p in ma && ma[p] !== null);

    for (const p of maPeriods) {
      // 从原始 bars 现场计算 MA 序列
      const line = chartRef.current.addSeries(LineSeries, {
        color:      MA_COLORS[p] ?? "#999",
        lineWidth:  1,
        priceLineVisible: false,
        lastValueVisible: false,
      });
      const maData = sorted
        .map((_, i) => {
          if (i < p - 1) return null;
          const slice = sorted.slice(i - p + 1, i + 1);
          const avg   = slice.reduce((s, k) => s + k.close, 0) / p;
          return { time: toTimestamp(sorted[i].date) as any, value: avg };
        })
        .filter(Boolean) as { time: any; value: number }[];

      line.setData(maData);
      maRefs.current[p] = line;
    }

    // 默认展示最近 120 根
    const visibleCount = Math.min(120, candleData.length);
    chartRef.current.timeScale().setVisibleRange({
      from: candleData[candleData.length - visibleCount].time,
      to:   candleData[candleData.length - 1].time,
    });
  }, [data, ma, initChart]);

  // 卸载时销毁
  useEffect(() => {
    return () => {
      Object.values(maRefs.current).forEach(s => chartRef.current?.removeSeries(s));
      chartRef.current?.remove();
      chartRef.current  = null;
      candleRef.current = null;
      volumeRef.current = null;
      maRefs.current    = {};
    };
  }, []);

  return (
    <div className="w-full flex flex-col gap-2">
      {/* 图例 */}
      <div className="flex flex-wrap gap-3 px-1 text-xs">
        {Object.entries(MA_COLORS)
          .filter(([p]) => Number(p) in ma && ma[Number(p)] !== null)
          .map(([p, color]) => (
            <span key={p} className="flex items-center gap-1">
              <span className="inline-block w-4 h-0.5 rounded" style={{ background: color }} />
              <span className="text-muted-foreground">MA{p}</span>
              <span className="font-mono">{ma[Number(p)]?.toFixed(2)}</span>
            </span>
          ))}
      </div>

      {/* 图表容器，支持拖拽/缩放 */}
      <div
        ref={containerRef}
        className="w-full rounded-lg overflow-hidden"
        style={{ height: 420 }}
      />

      <p className="text-xs text-muted-foreground text-right px-1">
        滚轮缩放 · 拖拽平移 · {data.length} 根{period === "daily" ? "日" : period === "weekly" ? "周" : "月"}K
      </p>
    </div>
  );
}
