import { NextRequest, NextResponse } from "next/server";

// 东财接口：个股所属概念标签
// secid 前缀：0=深市 1=沪市 北交所=0
function getSecid(symbol: string): string {
  const code = symbol.replace(/^[A-Z]+/, "");
  // 沪市：60xxxx, 68xxxx
  if (/^(60|68)/.test(code)) return `1.${code}`;
  // 深市/创业板/北交所
  return `0.${code}`;
}

export async function GET(req: NextRequest) {
  const symbol = req.nextUrl.searchParams.get("symbol");
  if (!symbol) {
    return NextResponse.json({ error: "symbol required" }, { status: 400 });
  }

  try {
    const secid = getSecid(symbol);
    const url = `https://push2.eastmoney.com/api/qt/stock/get?secid=${secid}&fields=f14,f57,f100,f127,f128,f129`;

    const res = await fetch(url, {
      headers: { "User-Agent": "Mozilla/5.0" },
      next: { revalidate: 300 }, // 5分钟缓存
    });

    const json = await res.json();
    const data = json?.data ?? {};

    // f129: 概念标签，逗号分隔的字符串
    const conceptsRaw: string = data.f129 ?? "";
    const concepts: string[] = conceptsRaw
      ? conceptsRaw.split(",").map((s: string) => s.trim()).filter(Boolean)
      : [];

    return NextResponse.json({
      symbol,
      name: data.f14 ?? "",
      industry: data.f127 ?? "",   // 所属行业
      region: data.f128 ?? "",     // 地域板块
      concepts,                    // 概念标签列表
    });
  } catch (e) {
    return NextResponse.json({ symbol, concepts: [], error: String(e) }, { status: 500 });
  }
}
