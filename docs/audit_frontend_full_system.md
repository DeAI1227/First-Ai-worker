# 新前端與全系統整合邊界全面巡檢

## 1. 整體結論：warning

新前端的資料邊界大致正確，已經做到：

- 只讀 Supabase anon key
- 不讀 Python 程式
- 不讀 `output/` JSON
- 不直接呼叫 Collector
- 頁面資料來源對應到 production views

我也沒有看到 service_role key 被放進前端程式的風險。

但有兩個需要標示成警示的地方：

- `Industry Detail` 沒有獨立 route，現在只有 `Industries` 總覽頁
- `python -m unittest discover -s tests -p "test_*.py" -v` 這次重新執行時沒有在 audit 時間內收尾，因此我不能把它寫成這一輪「已完成通過」

另外，`npm run lint` 在前端專案中沒有定義，這不是錯誤，但需要在報告裡如實記錄。

---

## 2. 前端是否只讀 Supabase

**是。**

我確認到前端使用的是：

- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY`

前端 Supabase client 位置：

- [frontend/src/lib/supabase.ts](../frontend/src/lib/supabase.ts)

它會直接從 `import.meta.env` 讀取前端變數，並在缺值時明確報錯。

### 沒有看到前端使用的敏感後端變數

前端程式中沒有看到：

- `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_SERVICE_KEY`
- `API_AUTH_TOKEN`
- Python output JSON
- local output folder
- collector files

---

## 3. 是否發現 service_role key 外洩風險

**沒有發現前端外洩風險。**

我掃到的結果顯示：

- 前端只用 `VITE_SUPABASE_URL`
- 前端只用 `VITE_SUPABASE_ANON_KEY`
- 沒有把 `SUPABASE_SERVICE_ROLE_KEY` 放進前端程式

後端文件有提到 service_role key，但那是正確位置，屬於後端與寫入流程，不是前端。

---

## 4. 每個頁面對應的 Supabase view

### 已確認的頁面 / route

`frontend/src/App.tsx` 目前的 routes：

- Dashboard
- Industries
- Stocks
- Stock Detail
- Macro
- Institution Watch
- Reports
- Settings / System

### 對應 view

- 總覽頁 → `view_dashboard_events`
- 產業追蹤頁 → `view_industry_cards`
- 股票清單頁 → `view_stock_cards`
- 股票詳情頁 → `view_stock_detail_events`
- 大環境頁 → `view_macro_events`
- 大行關注頁 → `view_institution_watch_events`
- 研究報告頁 → `view_recent_reports`
- 未讀統計 → `view_unread_counts`

### 文件 / 實作佐證

- [frontend/src/lib/queries.ts](../frontend/src/lib/queries.ts)
- [frontend/src/pages/DashboardPage.tsx](../frontend/src/pages/DashboardPage.tsx)
- [frontend/src/pages/IndustriesPage.tsx](../frontend/src/pages/IndustriesPage.tsx)
- [frontend/src/pages/StocksPage.tsx](../frontend/src/pages/StocksPage.tsx)
- [frontend/src/pages/StockDetailPage.tsx](../frontend/src/pages/StockDetailPage.tsx)
- [frontend/src/pages/MacroPage.tsx](../frontend/src/pages/MacroPage.tsx)
- [frontend/src/pages/InstitutionWatchPage.tsx](../frontend/src/pages/InstitutionWatchPage.tsx)
- [frontend/src/pages/ReportsPage.tsx](../frontend/src/pages/ReportsPage.tsx)
- [frontend/src/pages/SettingsPage.tsx](../frontend/src/pages/SettingsPage.tsx)

### 需要特別說明

- `Industry Detail` 目前沒有獨立 route
  - 現狀只有 `Industries` 總覽頁
  - 若未來要拆出詳細頁，現在還沒有對應 route

---

## 5. 是否有 mock data 需要移除

**沒有發現需要移除的前端 mock data。**

我掃到的頁面都已經在用 `frontend/src/lib/queries.ts` 的 Supabase 查詢函式，而不是硬編造前端資料。

目前看到的本機狀態資料只有：

- `userId` 存在 local storage

這是用來測試 unread count 與 read status，不是事件假資料。

---

## 6. 股票清單是否依賴 reference data

**是。**

股票清單頁使用：

- `getStockCards()`
- 來源 view：`view_stock_cards`

這代表股票清單來自 reference data，不依賴當天事件。

### 這件事很重要，因為：

- 45 檔股票應該一直存在
- 沒事件的股票也要出現在清單
- 不需要後端硬生生製造「無重大更新」假事件

我在以下檔案也看到了同樣的定位：

- [frontend/src/pages/StocksPage.tsx](../frontend/src/pages/StocksPage.tsx)
- [frontend/src/components/domain/StockRow.tsx](../frontend/src/components/domain/StockRow.tsx)

---

## 7. 股票詳情 empty state 是否正確

**是。**

股票詳情頁使用：

- `getStockDetailEvents(stockCode)`
- 來源 view：`view_stock_detail_events`

當沒有事件時：

- 前端顯示 `EmptyState`
- 不會自己產生假資料

相關檔案：

- [frontend/src/pages/StockDetailPage.tsx](../frontend/src/pages/StockDetailPage.tsx)

---

## 8. 是否出現禁止的股價 / 技術分析 / 買賣建議功能

**沒有看到功能層面的違規。**

我沒有看到前端有：

- 即時股價
- 今日漲跌
- 漲跌幅
- K 線
- 成交量
- 技術分析
- 買進
- 賣出
- 目標價
- 報酬率預測
- 飆股
- 喊單

### 但有兩點要分清楚

1. 有些文件 / 說明文字會反覆提到「不要做」這些東西  
   - 這是正確的約束，不是功能

2. 有些頁面文案因為終端機編碼顯示成亂碼  
   - 這看起來像字元編碼顯示問題，不像是功能性風險
   - 在 build / typecheck 上沒有反映成錯誤

---

## 9. UI / UX 狀態

### 已具備的 UI 狀態

- 深色主題
- 卡片式布局
- 高資訊密度但不亂
- loading state
- error state
- empty state
- critical / important / general 標籤
- quality_summary 顯示區塊
- unread count 顯示

### 已看到的設計位置

- `DashboardPage` 有：
  - 重要度統計
  - `QualitySummaryMini`
  - unread counts
  - 近期事件 / 報告摘要
- `EventItem` 有：
  - importance badge
  - quality summary
  - source urls
- `SettingsPage` 有：
  - `user_read_status` 的說明
  - `view_unread_counts` 的顯示

### 整體感受

風格方向是符合「金融研究終端」的：

- 深色
- 卡片
- 資訊分層清楚

---

## 10. 前端 build / lint / typecheck 結果

### build

- 指令：`npm run build`
- 結果：**pass**

### typecheck

- 指令：`npm run check`
- 結果：**pass**

### lint

- 指令：`npm run lint`
- 結果：**script 不存在**

這不是前端錯誤，但代表目前沒有 lint 流程可跑。

---

## 11. 後端測試結果

### compileall

- 指令：`python -m compileall .`
- 結果：**pass**

### unittest

- 指令：`python -m unittest discover -s tests -p "test_*.py" -v`
- 這一輪 audit 時間內**沒有完成收尾**

我能確認的是：

- 這次 `unittest` 已經跑到很後面
- 但沒有在這次稽核窗口內回傳最終結果

### 補充

在這次之前，整套 unittest 曾經在先前驗證中通過過。  
但就這次的巡檢而言，我不能把這輪重新執行結果硬寫成 pass。

---

## 12. 必須人工處理的事項

1. `Industry Detail` 若未來需要獨立頁，現在還沒有 route

2. `npm run lint` 尚未定義
   - 若團隊需要 lint，需後續補 script

3. `python -m unittest discover -s tests -p "test_*.py" -v`
   - 這次未在稽核時間內收尾
   - 若你要完全確定整體綠燈，建議再單獨重跑一次並等完整結束

4. 前端文案目前有終端顯示亂碼的情況
   - 需要在真實編輯器與瀏覽器中再看一次
   - 這比較像字元編碼顯示問題，不是資料流問題

---

## 13. 建議下一步

1. 保持新前端只讀 Supabase views，不回頭接 Python / output JSON
2. 若需要完整品質保證，補跑一次 unittest 到最後
3. 若團隊想要 lint，補上 frontend 的 `lint` script
4. 若真的需要 `Industry Detail`，再新增獨立 route 與對應 view
5. 進入正式部署時，只把環境變數填給前端 anon key 與 Supabase URL，service_role 僅留後端

