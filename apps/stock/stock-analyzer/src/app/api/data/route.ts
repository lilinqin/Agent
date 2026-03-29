import { NextRequest, NextResponse } from "next/server";

const PYTHON_API = process.env.PYTHON_API_URL || "http://localhost:5000";

export async function GET(req: NextRequest) {
  const type  = req.nextUrl.searchParams.get("type")  || "industry";
  const board = req.nextUrl.searchParams.get("board");

  try {
    if (board) {
      // 单个板块详情
      const res = await fetch(
        `${PYTHON_API}/api/boards/${type}/${encodeURIComponent(board)}`,
        { next: { revalidate: 60 } }
      );
      if (!res.ok) {
        return NextResponse.json({ status: "not_found" }, { status: 404 });
      }
      const data = await res.json();
      // 适配前端期望的字段名
      return NextResponse.json({
        status: "ok",
        name: data.name,
        type,
        total_stocks: data.total_stocks,
        hit_stocks: data.total_stocks,
        avg_change: data.avg_change,
        up_count: data.up_count,
        down_count: data.down_count,
        strength: data.strength,
        strength_score: data.strength_score,
        summary: `${data.name}板块今日${data.strength}，平均涨跌${data.avg_change >= 0 ? "+" : ""}${data.avg_change?.toFixed(2)}%，共${data.total_stocks}只成分股。`,
        stocks: data.stocks,
      });
    }

    // 板块列表
    const res = await fetch(
      `${PYTHON_API}/api/boards?type=${type}`,
      { next: { revalidate: 60 } }
    );
    if (!res.ok) {
      return NextResponse.json({ status: "no_data", groups: [], updated_at: null, type });
    }
    const data = await res.json();

    if (!data.items?.length) {
      return NextResponse.json({ status: "no_data", groups: [], updated_at: null, type });
    }

    const groups = data.items.map((item: Record<string, unknown>) => ({
      name: item.name,
      total_stocks: item.total_stocks || 0,
      hit_stocks: item.total_stocks || 0,
      avg_change: item.avg_change || 0,
      up_count: item.up_count || 0,
      down_count: item.down_count || 0,
      strength: item.strength || "中性",
      strength_score: item.strength_score || 50,
      summary: `${item.name}板块今日${item.strength || "中性"}，共${item.total_stocks || 0}只成分股。`,
      stocks: [],
    }));

    return NextResponse.json({
      status: "ok",
      type,
      updated_at: data.updated_at,
      total_hit: groups.reduce((s: number, g: { total_stocks: number }) => s + g.total_stocks, 0),
      groups,
    });
  } catch (e) {
    return NextResponse.json({ status: "error", groups: [], updated_at: null, type }, { status: 500 });
  }
}
