import { NextRequest, NextResponse } from "next/server";

const PYTHON_API = process.env.PYTHON_API_URL || "http://localhost:5000";

export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ symbol: string }> }
) {
  const { symbol } = await params;

  try {
    const response = await fetch(`${PYTHON_API}/api/stock/${symbol}`, {
      next: { revalidate: 60 }
    });
    
    if (!response.ok) {
      return NextResponse.json(
        { status: "error", message: `获取股票 ${symbol} 失败` },
        { status: response.status }
      );
    }
    
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Stock API error:', error);
    return NextResponse.json(
      { status: "error", message: "获取股票详情失败" },
      { status: 500 }
    );
  }
}
