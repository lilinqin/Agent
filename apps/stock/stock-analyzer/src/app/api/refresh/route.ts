import { NextRequest, NextResponse } from "next/server";
import { exec } from "child_process";
import path from "path";

export async function POST(req: NextRequest) {
  const type = req.nextUrl.searchParams.get("type") || "industry";
  
  const scriptPath = path.join(process.cwd(), "..", "stock_screener", "stock_screener.py");
  const dataDir = path.join(process.cwd(), "data");
  const outFile = path.join(dataDir, type === "concept" ? "result_concept.json" : "result.json");
  const mode = type === "concept" ? "concept" : "industry";

  const fs = await import("fs");
  if (!fs.existsSync(scriptPath)) {
    return NextResponse.json({ status: "error", message: "采集脚本不存在" }, { status: 404 });
  }

  exec(`python3 "${scriptPath}" --mode ${mode} --output "${outFile}"`, (err) => {
    if (err) console.error("采集脚本错误:", err.message);
  });

  return NextResponse.json({ status: "started", message: `${type === "concept" ? "概念" : "行业"}板块数据采集已启动` });
}
