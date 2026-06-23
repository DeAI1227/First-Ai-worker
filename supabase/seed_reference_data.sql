-- Production reference data seed for Investment Research Collector
--
-- Generated from collector/config/tracking_universe.py.
-- Re-run scripts/generate_reference_data_seed.py whenever the tracking universe changes.
-- This file seeds reference entities only. It does not create events.

-- SECTION: industries
insert into industries (
  industry_id,
  industry_name,
  enabled,
  keywords_zh,
  keywords_en
) values
  ('thermal', '散熱', true, '["散熱", "液冷", "熱管理", "AI 伺服器"]'::jsonb, '["thermal", "cooling", "liquid cooling", "data center cooling"]'::jsonb),
  ('power', '電力', true, '["電力", "電網", "儲能", "變壓器"]'::jsonb, '["power", "power grid", "energy storage", "transformer"]'::jsonb),
  ('autodrive', '自動駕駛', true, '["自動駕駛", "ADAS", "車用電子", "感測器"]'::jsonb, '["autonomous driving", "ADAS", "automotive electronics", "sensor"]'::jsonb),
  ('robot', '機器人', true, '["機器人", "工業自動化", "傳動", "伺服"]'::jsonb, '["robot", "industrial automation", "motion control", "servo"]'::jsonb),
  ('cpo', 'CPO 光通訊', true, '["CPO 光通訊", "共同封裝光學", "光通訊", "矽光子"]'::jsonb, '["CPO", "co-packaged optics", "optical communication", "silicon photonics"]'::jsonb),
  ('networking', '網通', true, '["網通", "路由器", "交換器", "WiFi"]'::jsonb, '["networking", "router", "switch", "Wi-Fi"]'::jsonb)
on conflict (industry_id) do update set
  industry_name = excluded.industry_name,
  enabled = excluded.enabled,
  keywords_zh = excluded.keywords_zh,
  keywords_en = excluded.keywords_en,
  updated_at = now();

-- SECTION: stocks
insert into stocks (
  stock_code,
  stock_name,
  enabled,
  keywords_zh,
  keywords_en
) values
  ('6230', '尼得科超眾', true, '["尼得科超眾", "6230"]'::jsonb, '[]'::jsonb),
  ('1513', '中興電', true, '["中興電", "1513"]'::jsonb, '[]'::jsonb),
  ('1514', '亞力', true, '["亞力", "1514"]'::jsonb, '[]'::jsonb),
  ('6781', 'AES-KY', true, '["AES-KY", "6781"]'::jsonb, '[]'::jsonb),
  ('6121', '新普', true, '["新普", "6121"]'::jsonb, '[]'::jsonb),
  ('6412', '群電', true, '["群電", "6412"]'::jsonb, '[]'::jsonb),
  ('1504', '東元', true, '["東元", "1504"]'::jsonb, '[]'::jsonb),
  ('3015', '全漢', true, '["全漢", "3015"]'::jsonb, '[]'::jsonb),
  ('2371', '大同', true, '["大同", "2371"]'::jsonb, '[]'::jsonb),
  ('1609', '大亞', true, '["大亞", "1609"]'::jsonb, '[]'::jsonb),
  ('3227', '原相', true, '["原相", "3227"]'::jsonb, '[]'::jsonb),
  ('6279', '胡連', true, '["胡連", "6279"]'::jsonb, '[]'::jsonb),
  ('3552', '同致', true, '["同致", "3552"]'::jsonb, '[]'::jsonb),
  ('8255', '朋程', true, '["朋程", "8255"]'::jsonb, '[]'::jsonb),
  ('2497', '怡利電', true, '["怡利電", "2497"]'::jsonb, '[]'::jsonb),
  ('3019', '亞光', true, '["亞光", "3019"]'::jsonb, '[]'::jsonb),
  ('4976', '佳凌', true, '["佳凌", "4976"]'::jsonb, '[]'::jsonb),
  ('4952', '凌通', true, '["凌通", "4952"]'::jsonb, '[]'::jsonb),
  ('2049', '上銀', true, '["上銀", "2049"]'::jsonb, '[]'::jsonb),
  ('4583', '台灣精銳', true, '["台灣精銳", "4583"]'::jsonb, '[]'::jsonb),
  ('4576', '大銀微系統', true, '["大銀微系統", "4576"]'::jsonb, '[]'::jsonb),
  ('4571', '鈞興-KY', true, '["鈞興-KY", "4571"]'::jsonb, '[]'::jsonb),
  ('1597', '直得', true, '["直得", "1597"]'::jsonb, '[]'::jsonb),
  ('2233', '宇隆', true, '["宇隆", "2233"]'::jsonb, '[]'::jsonb),
  ('4540', '全球傳動', true, '["全球傳動", "4540"]'::jsonb, '[]'::jsonb),
  ('2359', '所羅門', true, '["所羅門", "2359"]'::jsonb, '[]'::jsonb),
  ('1536', '和大', true, '["和大", "1536"]'::jsonb, '[]'::jsonb),
  ('1583', '程泰', true, '["程泰", "1583"]'::jsonb, '[]'::jsonb),
  ('6215', '和椿', true, '["和椿", "6215"]'::jsonb, '[]'::jsonb),
  ('8016', '矽創', true, '["矽創", "8016"]'::jsonb, '[]'::jsonb),
  ('6732', '昇佳電子', true, '["昇佳電子", "6732"]'::jsonb, '[]'::jsonb),
  ('5484', '慧友', true, '["慧友", "5484"]'::jsonb, '[]'::jsonb),
  ('3059', '華晶科', true, '["華晶科", "3059"]'::jsonb, '[]'::jsonb),
  ('2328', '廣宇', true, '["廣宇", "2328"]'::jsonb, '[]'::jsonb),
  ('5388', '中磊', true, '["中磊", "5388"]'::jsonb, '[]'::jsonb),
  ('3596', '智易', true, '["智易", "3596"]'::jsonb, '[]'::jsonb),
  ('6285', '啟碁', true, '["啟碁", "6285"]'::jsonb, '[]'::jsonb),
  ('3380', '明泰', true, '["明泰", "3380"]'::jsonb, '[]'::jsonb),
  ('2314', '台揚', true, '["台揚", "2314"]'::jsonb, '[]'::jsonb),
  ('2312', '金寶', true, '["金寶", "2312"]'::jsonb, '[]'::jsonb),
  ('6546', '正基', true, '["正基", "6546"]'::jsonb, '[]'::jsonb),
  ('3665', '貿聯-KY', true, '["貿聯-KY", "3665"]'::jsonb, '[]'::jsonb),
  ('2330', '台積電', true, '["台積電", "2330"]'::jsonb, '[]'::jsonb),
  ('2454', '聯發科', true, '["聯發科", "2454"]'::jsonb, '[]'::jsonb),
  ('2308', '台達電', true, '["台達電", "2308"]'::jsonb, '[]'::jsonb)
on conflict (stock_code) do update set
  stock_name = excluded.stock_name,
  enabled = excluded.enabled,
  keywords_zh = excluded.keywords_zh,
  keywords_en = excluded.keywords_en,
  updated_at = now();

-- SECTION: stock_industries
insert into stock_industries (
  stock_code,
  industry_name
) values
  ('6230', '散熱'),
  ('1513', '電力'),
  ('1514', '電力'),
  ('6781', '電力'),
  ('6121', '電力'),
  ('6412', '電力'),
  ('1504', '電力'),
  ('3015', '電力'),
  ('2371', '電力'),
  ('1609', '電力'),
  ('3227', '自動駕駛'),
  ('3227', '機器人'),
  ('6279', '自動駕駛'),
  ('3552', '自動駕駛'),
  ('8255', '自動駕駛'),
  ('2497', '自動駕駛'),
  ('3019', '自動駕駛'),
  ('4976', '自動駕駛'),
  ('4952', '自動駕駛'),
  ('2049', '機器人'),
  ('4583', '機器人'),
  ('4576', '機器人'),
  ('4571', '機器人'),
  ('1597', '機器人'),
  ('2233', '機器人'),
  ('4540', '機器人'),
  ('2359', '機器人'),
  ('1536', '機器人'),
  ('1583', '機器人'),
  ('6215', '機器人'),
  ('8016', '機器人'),
  ('6732', '機器人'),
  ('5484', '機器人'),
  ('3059', '機器人'),
  ('2328', '機器人'),
  ('5388', '網通'),
  ('3596', '網通'),
  ('6285', '網通'),
  ('3380', '網通'),
  ('2314', '網通'),
  ('2312', '網通'),
  ('6546', '網通')
on conflict (stock_code, industry_name) do update set
  stock_code = excluded.stock_code,
  industry_name = excluded.industry_name;

-- SECTION: macro_topics
insert into macro_topics (
  topic_id,
  topic_name,
  enabled,
  keywords_zh,
  keywords_en
) values
  ('fed_rate', 'FED 利率', true, '["聯準會", "利率政策", "降息", "升息"]'::jsonb, '["Fed", "interest rate", "rate cut", "rate hike"]'::jsonb),
  ('us_cpi', '美國 CPI', true, '["美國 CPI", "CPI", "通膨"]'::jsonb, '["US CPI", "inflation"]'::jsonb),
  ('us_ppi', '美國 PPI', true, '["美國 PPI", "PPI", "生產者物價"]'::jsonb, '["US PPI", "producer price index"]'::jsonb),
  ('us_jobs', '美國就業數據', true, '["就業數據", "非農", "失業率"]'::jsonb, '["employment", "nonfarm payrolls", "unemployment rate"]'::jsonb),
  ('us_10y_yield', '十年期美債殖利率', true, '["十年期美債殖利率", "美債殖利率", "公債殖利率"]'::jsonb, '["10Y Treasury yield", "yield"]'::jsonb),
  ('usd_index', '美元指數', true, '["美元指數", "DXY"]'::jsonb, '["USD index", "DXY"]'::jsonb),
  ('taiwan_weighted_index', '台股加權指數環境', true, '["台股加權指數", "加權指數", "台股環境"]'::jsonb, '["Taiwan Weighted Index", "Taiwan market"]'::jsonb),
  ('foreign_investor_flows', '外資動向', true, '["外資", "買賣超", "資金流向"]'::jsonb, '["foreign investor", "capital flow"]'::jsonb),
  ('ai_capex', 'AI 資本支出', true, '["AI 資本支出", "AI 伺服器", "資本支出"]'::jsonb, '["AI capex", "AI server", "capex"]'::jsonb),
  ('data_center_demand', '資料中心需求', true, '["資料中心", "雲端", "液冷"]'::jsonb, '["data center", "cloud", "liquid cooling"]'::jsonb)
on conflict (topic_id) do update set
  topic_name = excluded.topic_name,
  enabled = excluded.enabled,
  keywords_zh = excluded.keywords_zh,
  keywords_en = excluded.keywords_en,
  updated_at = now();

-- SECTION: institution_watch_stocks
insert into institution_watch_stocks (
  stock_code,
  stock_name,
  enabled,
  watch_reason
) values
  ('3665', '貿聯-KY', true, 'institution_watch'),
  ('2330', '台積電', true, 'institution_watch'),
  ('2454', '聯發科', true, 'institution_watch'),
  ('2308', '台達電', true, 'institution_watch')
on conflict (stock_code) do update set
  stock_name = excluded.stock_name,
  enabled = excluded.enabled,
  watch_reason = excluded.watch_reason,
  updated_at = now();
