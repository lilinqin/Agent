"""
HTML 日报渲染器（单页聚合版 · 日期下拉选择）
- 每次运行把当天数据持久化到 output/data/YYYY-MM-DD.json
- index.html 是唯一入口，顶部日期下拉，切换时动态渲染对应日期内容
- 支持 2 级分类：category 格式 "parent" 或 "parent/sub"
- 每个内容区支持按来源（source）筛选
"""
import json
from datetime import datetime
from pathlib import Path

from models import Article

# ── 一级分类配置 ──────────────────────────────────────────────────
PARENT_CONFIG = {
    "github":        ("GitHub Trending", 0),
    "hackernews":    ("Hacker News",     1),
    "official_blog": ("官方博客",         2),
    "tech_blog":     ("技术博客",         3),
    "cn_media":      ("国内媒体",         4),
    "tech_media":    ("技术媒体",         5),
    "rss":           ("其他",            6),
}

# Tab 图标 SVG（inline，来自 Heroicons）
PARENT_ICONS = {
    "github": '<svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"/></svg>',
    "hackernews": '<svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M0 24V0h24v24H0zM6.951 5.896l4.112 7.708v5.064h1.583v-4.972l4.148-7.799h-1.749l-2.457 4.875c-.372.745-.688 1.434-.688 1.434s-.297-.708-.651-1.434L8.831 5.896H6.951z"/></svg>',
    "official_blog": '<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M12 21a9.004 9.004 0 008.716-6.747M12 21a9.004 9.004 0 01-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m0 0a8.997 8.997 0 017.843 4.582M12 3a8.997 8.997 0 00-7.843 4.582m15.686 0A11.953 11.953 0 0112 10.5c-2.998 0-5.74-1.1-7.843-2.918m15.686 0A8.959 8.959 0 0121 12c0 .778-.099 1.533-.284 2.253m0 0A17.919 17.919 0 0112 16.5c-3.162 0-6.133-.815-8.716-2.247m0 0A9.015 9.015 0 013 12c0-1.605.42-3.113 1.157-4.418"/></svg>',
    "tech_blog": '<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25"/></svg>',
    "cn_media": '<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M12 7.5h1.5m-1.5 3h1.5m-7.5 3h7.5m-7.5 3h7.5m3-9h3.375c.621 0 1.125.504 1.125 1.125V18a2.25 2.25 0 01-2.25 2.25M16.5 7.5V18a2.25 2.25 0 002.25 2.25M16.5 7.5V4.875c0-.621-.504-1.125-1.125-1.125H4.125C3.504 3.75 3 4.254 3 4.875V18a2.25 2.25 0 002.25 2.25h13.5M6 7.5h3v3H6v-3z"/></svg>',
    "tech_media": '<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M12 7.5h1.5m-1.5 3h1.5m-7.5 3h7.5m-7.5 3h7.5m3-9h3.375c.621 0 1.125.504 1.125 1.125V18a2.25 2.25 0 01-2.25 2.25M16.5 7.5V18a2.25 2.25 0 002.25 2.25M16.5 7.5V4.875c0-.621-.504-1.125-1.125-1.125H4.125C3.504 3.75 3 4.254 3 4.875V18a2.25 2.25 0 002.25 2.25h13.5M6 7.5h3v3H6v-3z"/></svg>',
    "rss": '<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M12.75 19.5v-.75a7.5 7.5 0 00-7.5-7.5H4.5m0-6.75h.75c7.87 0 14.25 6.38 14.25 14.25v.75M6 18.75a.75.75 0 11-1.5 0 .75.75 0 011.5 0z"/></svg>',
}

SUB_CONFIG = {
    "official_blog/intl": "国际大厂",
    "official_blog/cn":   "国内大模型",
    "tech_blog/framework":"框架与工具",
}

IMPORTANCE_CONFIG = {
    5: {"label": "重大突破", "dot": "bg-red-500",    "badge": "bg-red-50 text-red-700 ring-red-200"},
    4: {"label": "重要进展", "dot": "bg-orange-400", "badge": "bg-orange-50 text-orange-700 ring-orange-200"},
    3: {"label": "值得关注", "dot": "bg-blue-400",   "badge": "bg-blue-50 text-blue-700 ring-blue-200"},
    2: {"label": "一般资讯", "dot": "bg-gray-300",   "badge": "bg-gray-50 text-gray-500 ring-gray-200"},
    1: {"label": "参考信息", "dot": "bg-gray-200",   "badge": "bg-gray-50 text-gray-400 ring-gray-100"},
}


# ── 公开接口 ──────────────────────────────────────────────────────

def render_daily(articles: list[Article], output_dir: str, date: datetime) -> str:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    data_dir = out / "data"
    data_dir.mkdir(exist_ok=True)

    date_str = date.strftime("%Y-%m-%d")

    # 持久化当天数据
    records = [_to_dict(a) for a in articles]
    (data_dir / f"{date_str}.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[Renderer] 已保存数据: data/{date_str}.json ({len(articles)} 条)")

    # 重建 index.html
    _rebuild_index(out, data_dir)
    return str(out / "index.html")


def _rebuild_index(out: Path, data_dir: Path):
    date_files = sorted(data_dir.glob("????-??-??.json"), reverse=True)
    all_days: list[tuple[str, list[dict]]] = []
    for f in date_files:
        records = json.loads(f.read_text(encoding="utf-8"))
        all_days.append((f.stem, records))

    html = _build_page(all_days)
    (out / "index.html").write_text(html, encoding="utf-8")
    print(f"[Renderer] 已更新 index.html，共 {len(all_days)} 天")


# ── 数据序列化 ────────────────────────────────────────────────────

def _to_dict(a: Article) -> dict:
    return {
        "id": a.id,
        "title": a.title or "",
        "zh_title": a.zh_title or "",
        "zh_summary": a.zh_summary or "",
        "content": (a.content or "")[:500],
        "url": a.url or "#",
        "source": a.source or "",
        "category": a.category or "rss",
        "importance": a.importance or 3,
        "score": a.score or 0,
        "authors": a.authors or [],
        "published_at": a.published_at.isoformat() if a.published_at else None,
    }


# ── 分组 ──────────────────────────────────────────────────────────

def _build_structure(records: list[dict]) -> list[dict]:
    parents: dict[str, dict] = {}
    for a in records:
        cat = a.get("category", "rss")
        if "/" in cat:
            parent, sub = cat.split("/", 1)
        else:
            parent, sub = cat, None
        cfg = PARENT_CONFIG.get(parent, (parent, 99))
        if parent not in parents:
            parents[parent] = {
                "parent": parent, "name": cfg[0],
                "order": cfg[1], "total": 0, "subs": {}, "articles": [],
            }
        parents[parent]["total"] += 1
        if sub:
            parents[parent]["subs"].setdefault(sub, []).append(a)
        else:
            parents[parent]["articles"].append(a)

    result = []
    for p in sorted(parents.values(), key=lambda x: x["order"]):
        for lst in p["subs"].values():
            lst.sort(key=lambda a: (a.get("importance", 3), a.get("score", 0)), reverse=True)
        p["articles"].sort(key=lambda a: (a.get("importance", 3), a.get("score", 0)), reverse=True)
        result.append(p)
    return result


def _sources_of(records: list[dict]) -> list[str]:
    seen, out = set(), []
    for a in records:
        s = a.get("source", "")
        if s and s not in seen:
            seen.add(s); out.append(s)
    return out


# ── 页面构建 ──────────────────────────────────────────────────────

def _build_page(all_days: list[tuple[str, list[dict]]]) -> str:
    if not all_days:
        return "<html><body class='p-8 text-gray-400'>暂无数据</body></html>"

    js_data_parts = []
    for date_str, records in all_days:
        js_data_parts.append(f'"{date_str}": {json.dumps(records, ensure_ascii=False)}')
    js_all_data = "{" + ",\n".join(js_data_parts) + "}"

    dates_js = json.dumps([d for d, _ in all_days])
    latest_date = all_days[0][0]
    total_articles = sum(len(r) for _, r in all_days)

    imp_config_js = json.dumps({
        str(k): v for k, v in IMPORTANCE_CONFIG.items()
    })
    parent_config_js = json.dumps({
        k: {"name": v[0], "order": v[1]}
        for k, v in PARENT_CONFIG.items()
    })
    parent_icons_js = json.dumps({k: v for k, v in PARENT_ICONS.items()})
    sub_config_js = json.dumps(SUB_CONFIG)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Agent 每日情报</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Sans+SC:wght@400;500;700&display=swap" rel="stylesheet">
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdn.jsdelivr.net/npm/alpinejs@3.14.1/dist/cdn.min.js" defer></script>
<style>
  * {{ font-family: 'Inter', 'Noto Sans SC', system-ui, sans-serif; }}
  [x-cloak] {{ display: none !important; }}

  /* 主题变量 */
  :root {{
    --bg: #F8F9FB;
    --surface: #FFFFFF;
    --surface-2: #F3F4F6;
    --border: #E5E7EB;
    --border-subtle: #F0F1F3;
    --text-primary: #0F172A;
    --text-secondary: #475569;
    --text-muted: #94A3B8;
    --accent: #4F46E5;
    --accent-light: #EEF2FF;
    --accent-hover: #4338CA;
    --radius: 12px;
  }}

  body {{ background: var(--bg); color: var(--text-primary); }}

  /* 动画 */
  .fade-in {{ animation: fadeUp 0.2s cubic-bezier(0.16,1,0.3,1) both; }}
  @keyframes fadeUp {{
    from {{ opacity: 0; transform: translateY(6px); }}
    to   {{ opacity: 1; transform: translateY(0); }}
  }}
  @media (prefers-reduced-motion: reduce) {{
    .fade-in {{ animation: none; }}
  }}

  /* 滚动条 */
  .scrollbar-hide {{ -ms-overflow-style: none; scrollbar-width: none; }}
  .scrollbar-hide::-webkit-scrollbar {{ display: none; }}

  /* 自定义 select */
  select {{ -webkit-appearance: none; appearance: none; }}

  /* 卡片悬浮 */
  .card-hover {{ transition: box-shadow 0.2s ease, transform 0.2s ease; }}
  .card-hover:hover {{ box-shadow: 0 4px 24px rgba(0,0,0,0.08); transform: translateY(-1px); }}

  /* 来源标签点击效果 */
  .source-btn {{ transition: all 0.15s ease; }}

  /* Tab 下划线动画 */
  .sub-tab-active {{ position: relative; }}
  .sub-tab-active::after {{
    content: '';
    position: absolute;
    bottom: -1px;
    left: 0; right: 0;
    height: 2px;
    background: var(--accent);
    border-radius: 2px 2px 0 0;
  }}
</style>
</head>
<body x-data="app()" x-init="init()">

<!-- ── 顶部导航 ─────────────────────────────────────────────── -->
<header class="sticky top-0 z-50 bg-white/90 backdrop-blur-md border-b border-gray-100">
  <div class="max-w-4xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between gap-4">

    <!-- Logo -->
    <div class="flex items-center gap-2.5 shrink-0">
      <div class="w-7 h-7 rounded-lg bg-indigo-600 flex items-center justify-center">
        <svg class="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z"/>
        </svg>
      </div>
      <span class="font-semibold text-gray-900 text-sm hidden sm:block tracking-tight">Agent 每日情报</span>
    </div>

    <!-- 日期选择区 -->
    <div class="flex items-center gap-2">
      <!-- 前一天 -->
      <button @click="prevDate()" :disabled="currentDateIdx >= dates.length - 1"
              :class="currentDateIdx >= dates.length - 1 ? 'opacity-25 cursor-not-allowed' : 'hover:bg-gray-100 cursor-pointer'"
              class="w-8 h-8 flex items-center justify-center rounded-lg transition-colors"
              aria-label="前一天">
        <svg class="w-4 h-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5"/>
        </svg>
      </button>

      <!-- 日期下拉 -->
      <div class="relative">
        <select x-model="currentDate" @change="switchDate()"
                class="h-8 pl-3 pr-8 bg-white border border-gray-200 rounded-lg text-sm font-medium text-gray-700 cursor-pointer hover:border-indigo-300 focus:outline-none focus:ring-2 focus:ring-indigo-300/50 transition-all">
          <template x-for="d in dates" :key="d">
            <option :value="d" x-text="formatDateLabel(d)"></option>
          </template>
        </select>
        <div class="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 text-gray-400">
          <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7"/>
          </svg>
        </div>
      </div>

      <!-- 后一天 -->
      <button @click="nextDate()" :disabled="currentDateIdx <= 0"
              :class="currentDateIdx <= 0 ? 'opacity-25 cursor-not-allowed' : 'hover:bg-gray-100 cursor-pointer'"
              class="w-8 h-8 flex items-center justify-center rounded-lg transition-colors"
              aria-label="后一天">
        <svg class="w-4 h-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5"/>
        </svg>
      </button>
    </div>

    <!-- 统计 -->
    <div class="text-xs text-gray-400 shrink-0 hidden sm:flex items-center gap-1.5">
      <span x-text="(dayData[currentDate] || []).length" class="font-medium text-gray-600"></span>
      <span>条 ·</span>
      <span>{len(all_days)} 天</span>
      <span class="mx-1 text-gray-300">|</span>
      <!-- 访问计数 -->
      <svg class="w-3.5 h-3.5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.964-7.178z"/>
        <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
      </svg>
      <span x-text="pageviews !== null ? pageviews.toLocaleString() : '…'" class="font-medium text-gray-600"></span>
    </div>
  </div>
</header>

<!-- ── 主体 ────────────────────────────────────────────────────── -->
<main class="max-w-4xl mx-auto px-4 sm:px-6 py-6">

  <!-- 页面标题 -->
  <div class="mb-5" x-cloak>
    <div class="flex items-baseline gap-3">
      <h1 class="text-xl font-bold text-gray-900 tracking-tight" x-text="currentDate"></h1>
      <span class="text-sm text-gray-400"
            x-text="(dayData[currentDate] || []).length + ' 条情报'"></span>
    </div>
  </div>

  <!-- ── 一级分类 Tab ──────────────────────────────────────────── -->
  <div class="flex gap-1 mb-5 overflow-x-auto scrollbar-hide" x-cloak>
    <template x-for="p in structure" :key="p.parent">
      <button
        @click="activeTab = p.parent; activeSubTab = p.firstSub; activeSource = 'all'"
        :class="activeTab === p.parent
          ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-200'
          : 'bg-white text-gray-600 border border-gray-200 hover:border-indigo-200 hover:text-indigo-600'"
        class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all whitespace-nowrap cursor-pointer">
        <!-- SVG 图标 -->
        <span x-html="PARENT_ICONS[p.parent] || ''"></span>
        <span x-text="p.name"></span>
        <span class="px-1.5 py-0.5 rounded-md text-xs font-semibold"
              :class="activeTab === p.parent ? 'bg-white/20 text-white' : 'bg-gray-100 text-gray-500'"
              x-text="p.total"></span>
      </button>
    </template>
  </div>

  <!-- ── 二级分类 Tab ──────────────────────────────────────────── -->
  <template x-for="p in structure" :key="'sub-'+p.parent">
    <div x-show="activeTab === p.parent && p.subs.length > 0" x-cloak class="mb-4">
      <div class="flex gap-0 border-b border-gray-200 overflow-x-auto scrollbar-hide">
        <template x-for="s in p.subs" :key="s.key">
          <button
            @click="activeSubTab = s.key; activeSource = 'all'"
            :class="activeSubTab === s.key
              ? 'sub-tab-active text-indigo-600 font-semibold'
              : 'text-gray-500 hover:text-gray-700'"
            class="px-4 py-2.5 text-sm transition-colors whitespace-nowrap cursor-pointer relative">
            <span x-text="s.label"></span>
            <span class="ml-1.5 text-xs"
                  :class="activeSubTab === s.key ? 'text-indigo-400' : 'text-gray-400'"
                  x-text="'(' + s.articles.length + ')'"></span>
          </button>
        </template>
      </div>
    </div>
  </template>

  <!-- ── 来源筛选 ───────────────────────────────────────────────── -->
  <div x-show="currentSources.length > 1" class="flex items-center gap-2 mb-4 flex-wrap" x-cloak>
    <span class="text-xs text-gray-400 font-medium shrink-0">来源</span>
    <button @click="activeSource = 'all'" cursor-pointer
            :class="activeSource === 'all'
              ? 'bg-indigo-600 text-white border-transparent'
              : 'bg-white text-gray-600 border-gray-200 hover:border-indigo-300 hover:text-indigo-600'"
            class="source-btn px-2.5 py-1 rounded-full text-xs border font-medium cursor-pointer">
      全部
    </button>
    <template x-for="s in currentSources" :key="s">
      <button @click="activeSource = activeSource === s ? 'all' : s"
              :class="activeSource === s
                ? 'bg-indigo-600 text-white border-transparent'
                : 'bg-white text-gray-600 border-gray-200 hover:border-indigo-300 hover:text-indigo-600'"
              class="source-btn px-2.5 py-1 rounded-full text-xs border font-medium whitespace-nowrap cursor-pointer"
              x-text="s"></button>
    </template>
  </div>

  <!-- ── 文章卡片列表 ───────────────────────────────────────────── -->
  <div class="space-y-3 fade-in" x-cloak>
    <template x-for="a in filteredArticles" :key="a.id || a.url">
      <article class="card-hover bg-white rounded-xl border border-gray-100 overflow-hidden cursor-pointer"
               @click.self="window.open(a.url, '_blank')">
        <div class="p-4 sm:p-5">

          <!-- 头部：标题 + 重要性 -->
          <div class="flex items-start gap-3 mb-2.5">
            <!-- 重要性指示点 -->
            <div class="mt-1.5 shrink-0">
              <div class="w-2 h-2 rounded-full"
                   :class="IMP_CFG[String(a.importance || 3)]?.dot || 'bg-gray-300'"></div>
            </div>

            <div class="flex-1 min-w-0">
              <h3 class="font-semibold text-gray-900 text-sm sm:text-base leading-snug">
                <a :href="a.url" target="_blank" rel="noopener"
                   class="hover:text-indigo-600 transition-colors"
                   x-text="a.zh_title || a.title || '（无标题）'"></a>
              </h3>
            </div>

            <!-- 重要性 Badge -->
            <span class="shrink-0 text-xs px-2 py-0.5 rounded-full ring-1 font-medium"
                  :class="IMP_CFG[String(a.importance || 3)]?.badge || 'bg-gray-50 text-gray-500 ring-gray-200'"
                  x-text="IMP_CFG[String(a.importance || 3)]?.label || ''"></span>
          </div>

          <!-- 摘要 -->
          <p class="text-gray-500 text-sm leading-relaxed ml-5 mb-3 line-clamp-3"
             x-text="a.zh_summary || a.content || '（暂无摘要）'"></p>

          <!-- 底部元信息 -->
          <div class="flex items-center justify-between ml-5">
            <div class="flex items-center gap-2 flex-wrap">
              <!-- 来源标签 -->
              <button @click.stop="activeSource = activeSource === a.source ? 'all' : a.source"
                      :class="activeSource === a.source
                        ? 'bg-indigo-50 text-indigo-700 ring-1 ring-indigo-200'
                        : 'bg-gray-100 text-gray-500 hover:bg-indigo-50 hover:text-indigo-600'"
                      class="source-btn px-2 py-0.5 rounded-md text-xs font-medium cursor-pointer"
                      x-text="a.source"></button>
              <!-- 时间 -->
              <span class="text-xs text-gray-400" x-text="formatTime(a.published_at)"></span>
            </div>
            <!-- 查看原文 -->
            <a :href="a.url" target="_blank" rel="noopener"
               class="flex items-center gap-1 text-xs text-indigo-500 hover:text-indigo-700 font-medium transition-colors shrink-0"
               @click.stop>
              查看原文
              <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 19.5l15-15m0 0H8.25m11.25 0v11.25"/>
              </svg>
            </a>
          </div>
        </div>
      </article>
    </template>

    <!-- 空状态 -->
    <div x-show="filteredArticles.length === 0"
         class="text-center py-20">
      <div class="w-16 h-16 rounded-2xl bg-gray-100 flex items-center justify-center mx-auto mb-4">
        <svg class="w-8 h-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"/>
        </svg>
      </div>
      <p class="text-gray-400 text-sm">暂无数据</p>
    </div>
  </div>

</main>

<!-- ── 底部 ─────────────────────────────────────────────────────── -->
<footer class="max-w-4xl mx-auto px-6 py-6 mt-4">
  <div class="border-t border-gray-100 pt-6 flex items-center justify-between">
    <p class="text-xs text-gray-400">由 Agent 每日情报系统自动生成 · AWS Bedrock Claude Sonnet 摘要</p>
    <p class="text-xs text-gray-400">每日 08:00 自动更新</p>
  </div>
</footer>

<script>
const ALL_DATA   = {js_all_data};
const IMP_CFG    = {imp_config_js};
const PARENT_CFG = {parent_config_js};
const PARENT_ICONS = {parent_icons_js};
const SUB_CFG    = {sub_config_js};

function app() {{
  return {{
    dates: {dates_js},
    currentDate: '{latest_date}',
    currentDateIdx: 0,
    dayData: ALL_DATA,
    structure: [],
    activeTab: '',
    activeSubTab: null,
    activeSource: 'all',
    pageviews: null,
    IMP_CFG,
    PARENT_ICONS,

    init() {{
      this.currentDateIdx = 0;
      this.switchDate();
      // 访问计数：同一 tab 内只计一次
      if (!sessionStorage.getItem('_counted')) {{
        sessionStorage.setItem('_counted', '1');
        fetch('https://api.counterapi.dev/v1/agent-daily/pageviews/up')
          .then(r => r.json())
          .then(d => {{ this.pageviews = d.count; }})
          .catch(() => {{ this.pageviews = null; }});
      }} else {{
        fetch('https://api.counterapi.dev/v1/agent-daily/pageviews/')
          .then(r => r.json())
          .then(d => {{ this.pageviews = d.count; }})
          .catch(() => {{ this.pageviews = null; }});
      }}
    }},

    switchDate() {{
      this.currentDateIdx = this.dates.indexOf(this.currentDate);
      this.activeSource = 'all';
      this.buildStructure();
    }},

    prevDate() {{
      if (this.currentDateIdx < this.dates.length - 1) {{
        this.currentDateIdx++;
        this.currentDate = this.dates[this.currentDateIdx];
        this.activeSource = 'all';
        this.buildStructure();
      }}
    }},

    nextDate() {{
      if (this.currentDateIdx > 0) {{
        this.currentDateIdx--;
        this.currentDate = this.dates[this.currentDateIdx];
        this.activeSource = 'all';
        this.buildStructure();
      }}
    }},

    buildStructure() {{
      const records = this.dayData[this.currentDate] || [];
      const parents = {{}};
      for (const a of records) {{
        const cat = a.category || 'rss';
        let parent, sub;
        if (cat.includes('/')) {{ [parent, sub] = cat.split('/', 2); }}
        else {{ parent = cat; sub = null; }}
        const cfg = PARENT_CFG[parent] || {{ name: parent, order: 99 }};
        if (!parents[parent]) {{
          parents[parent] = {{ parent, name: cfg.name, order: cfg.order,
                               total: 0, subsMap: {{}}, articles: [] }};
        }}
        parents[parent].total++;
        if (sub) {{ (parents[parent].subsMap[sub] = parents[parent].subsMap[sub] || []).push(a); }}
        else {{ parents[parent].articles.push(a); }}
      }}
      const sortFn = (a, b) => (b.importance||3) - (a.importance||3) || (b.score||0) - (a.score||0);
      this.structure = Object.values(parents)
        .sort((a, b) => a.order - b.order)
        .map(p => {{
          const subs = Object.entries(p.subsMap).map(([key, arts]) => {{
            const fullKey = p.parent + '/' + key;
            arts.sort(sortFn);
            return {{ key, label: SUB_CFG[fullKey] || key, articles: arts }};
          }});
          p.articles.sort(sortFn);
          const firstSub = subs.length ? subs[0].key : null;
          return {{ ...p, subs, firstSub }};
        }});

      if (this.structure.length) {{
        const first = this.structure[0];
        this.activeTab = first.parent;
        this.activeSubTab = first.firstSub;
      }}
    }},

    get currentArticles() {{
      const p = this.structure.find(p => p.parent === this.activeTab);
      if (!p) return [];
      if (p.subs.length) {{
        const s = p.subs.find(s => s.key === this.activeSubTab);
        return s ? s.articles : (p.subs[0]?.articles || []);
      }}
      return p.articles;
    }},

    get currentSources() {{
      const seen = new Set(), out = [];
      for (const a of this.currentArticles) {{
        if (a.source && !seen.has(a.source)) {{ seen.add(a.source); out.push(a.source); }}
      }}
      return out;
    }},

    get filteredArticles() {{
      if (this.activeSource === 'all') return this.currentArticles;
      return this.currentArticles.filter(a => a.source === this.activeSource);
    }},

    formatDateLabel(d) {{
      const now = new Date();
      const today = now.toISOString().slice(0, 10);
      const yesterday = new Date(now - 86400000).toISOString().slice(0, 10);
      if (d === today) return d + ' 今天';
      if (d === yesterday) return d + ' 昨天';
      return d;
    }},

    formatTime(iso) {{
      if (!iso) return '';
      try {{
        const d = new Date(iso);
        const m = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        const h = String(d.getHours()).padStart(2, '0');
        const min = String(d.getMinutes()).padStart(2, '0');
        return m + '-' + day + ' ' + h + ':' + min;
      }} catch(e) {{ return ''; }}
    }},
  }}
}}
</script>
</body>
</html>"""
