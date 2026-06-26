type IndustryReference = {
  key: string;
  name: string;
  rawNames: string[];
};

type StockReference = {
  stockCode: string;
  stockName: string;
  industries: string[];
};

export const INDUSTRY_REFERENCE: IndustryReference[] = [
  { key: "thermal", name: "散熱", rawNames: ["散熱"] },
  { key: "power", name: "電力", rawNames: ["電力"] },
  { key: "autonomous-driving", name: "自動駕駛", rawNames: ["自動駕駛"] },
  { key: "robotics", name: "機器人", rawNames: ["機器人"] },
  { key: "cpo", name: "CPO 光通訊", rawNames: ["CPO 光通訊", "CPO光通訊"] },
  { key: "networking", name: "網通", rawNames: ["網通"] },
];

export const STOCK_REFERENCE: StockReference[] = [
  { stockCode: "6230", stockName: "尼得科超眾", industries: ["散熱"] },
  { stockCode: "1513", stockName: "中興電", industries: ["電力"] },
  { stockCode: "1514", stockName: "亞力", industries: ["電力"] },
  { stockCode: "6781", stockName: "AES-KY", industries: ["電力"] },
  { stockCode: "6121", stockName: "新普", industries: ["電力"] },
  { stockCode: "6412", stockName: "群電", industries: ["電力"] },
  { stockCode: "1504", stockName: "東元", industries: ["電力"] },
  { stockCode: "3015", stockName: "全漢", industries: ["電力"] },
  { stockCode: "2371", stockName: "大同", industries: ["電力"] },
  { stockCode: "1609", stockName: "大亞", industries: ["電力"] },
  { stockCode: "3227", stockName: "原相", industries: ["自動駕駛", "機器人"] },
  { stockCode: "6279", stockName: "胡連", industries: ["自動駕駛"] },
  { stockCode: "3552", stockName: "同致", industries: ["自動駕駛"] },
  { stockCode: "8255", stockName: "朋程", industries: ["自動駕駛"] },
  { stockCode: "2497", stockName: "怡利電", industries: ["自動駕駛"] },
  { stockCode: "3019", stockName: "亞光", industries: ["自動駕駛"] },
  { stockCode: "4976", stockName: "佳凌", industries: ["自動駕駛"] },
  { stockCode: "4952", stockName: "凌通", industries: ["自動駕駛"] },
  { stockCode: "2049", stockName: "上銀", industries: ["機器人"] },
  { stockCode: "4583", stockName: "台灣精銳", industries: ["機器人"] },
  { stockCode: "4576", stockName: "大銀微系統", industries: ["機器人"] },
  { stockCode: "4571", stockName: "鈞興-KY", industries: ["機器人"] },
  { stockCode: "1597", stockName: "直得", industries: ["機器人"] },
  { stockCode: "2233", stockName: "宇隆", industries: ["機器人"] },
  { stockCode: "4540", stockName: "全球傳動", industries: ["機器人"] },
  { stockCode: "2359", stockName: "所羅門", industries: ["機器人"] },
  { stockCode: "1536", stockName: "和大", industries: ["機器人"] },
  { stockCode: "1583", stockName: "程泰", industries: ["機器人"] },
  { stockCode: "6215", stockName: "和椿", industries: ["機器人"] },
  { stockCode: "8016", stockName: "矽創", industries: ["機器人"] },
  { stockCode: "6732", stockName: "昇佳電子", industries: ["機器人"] },
  { stockCode: "5484", stockName: "慧友", industries: ["機器人"] },
  { stockCode: "3059", stockName: "華晶科", industries: ["機器人"] },
  { stockCode: "2328", stockName: "廣宇", industries: ["機器人"] },
  { stockCode: "5388", stockName: "中磊", industries: ["網通"] },
  { stockCode: "3596", stockName: "智易", industries: ["網通"] },
  { stockCode: "6285", stockName: "啟碁", industries: ["網通"] },
  { stockCode: "3380", stockName: "明泰", industries: ["網通"] },
  { stockCode: "2314", stockName: "台揚", industries: ["網通"] },
  { stockCode: "2312", stockName: "金寶", industries: ["網通"] },
  { stockCode: "6546", stockName: "正基", industries: ["網通"] },
  { stockCode: "3665", stockName: "貿聯-KY", industries: [] },
  { stockCode: "2330", stockName: "台積電", industries: [] },
  { stockCode: "2454", stockName: "聯發科", industries: [] },
  { stockCode: "2308", stockName: "台達電", industries: [] },
];

const STOCK_REFERENCE_BY_CODE = new Map<string, StockReference>(
  STOCK_REFERENCE.map((item) => [item.stockCode, item]),
);

const INDUSTRY_NAME_BY_RAW = new Map<string, string>(
  INDUSTRY_REFERENCE.flatMap((item) => item.rawNames.map((rawName) => [rawName, item.name] as [string, string])),
);

const INDUSTRY_KEY_BY_NAME = new Map<string, string>(
  INDUSTRY_REFERENCE.map((item) => [item.name, item.key] as [string, string]),
);

const INDUSTRY_NAME_BY_KEY = new Map<string, string>(
  INDUSTRY_REFERENCE.map((item) => [item.key, item.name] as [string, string]),
);

export function normalizeIndustryName(value: string | null | undefined): string {
  if (!value) {
    return "未分類產業";
  }
  return INDUSTRY_NAME_BY_RAW.get(value) ?? value;
}

export function getIndustryKeyByName(industryName: string): string {
  return INDUSTRY_KEY_BY_NAME.get(industryName) ?? encodeURIComponent(industryName);
}

export function getIndustryNameByKey(industryKey: string): string {
  return INDUSTRY_NAME_BY_KEY.get(industryKey) ?? decodeURIComponent(industryKey);
}

export function normalizeStockName(stockCode: string, value: string | null | undefined): string {
  return STOCK_REFERENCE_BY_CODE.get(stockCode)?.stockName ?? value ?? stockCode;
}

export function getReferenceIndustriesByStockCode(stockCode: string): string[] {
  return [...(STOCK_REFERENCE_BY_CODE.get(stockCode)?.industries ?? [])];
}

export function normalizeScopeName(
  value: string | null | undefined,
  scope?: string | null,
  stockCode?: string | null,
): string {
  if (scope === "industry") {
    return normalizeIndustryName(value);
  }
  if (scope === "stock" && stockCode) {
    return normalizeStockName(stockCode, value);
  }
  if (scope === "institution_watch" || scope === "institution") {
    return "大行關注";
  }
  if (scope === "macro") {
    return value || "大環境";
  }
  return value || "研究事件";
}

export function isPlaceholderUrl(value: string): boolean {
  return value.includes("example.com") || value.includes("/mock/");
}

export function isPlaceholderContent(summary: string, sourceUrls: string[]): boolean {
  const lowerSummary = summary.toLowerCase();
  const joinedUrls = sourceUrls.join(" ").toLowerCase();
  return (
    sourceUrls.length > 0 &&
    sourceUrls.every(isPlaceholderUrl) &&
    (lowerSummary.includes("english technology coverage") || joinedUrls.includes("/mock/"))
  );
}

export function cleanSourceUrls(sourceUrls: string[] | null | undefined): string[] {
  return (sourceUrls ?? []).filter((url) => !isPlaceholderUrl(url));
}

export function buildDigestTitle(label: string): string {
  return `${label} 研究摘要`;
}
