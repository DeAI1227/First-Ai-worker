# GitHub Pages Frontend Deployment

這份文件說明如何把 `frontend/` 部署成真正可瀏覽的靜態網址。

## 目標

- 前端只讀 Supabase production views
- 前端不讀 Python 程式
- 前端不讀 `output/` JSON
- 前端不直接呼叫 Collector

## 部署流程

```text
GitHub Actions
→ build frontend
→ deploy to GitHub Pages
→ browser opens the public URL
```

部署 workflow 位於：

- [`.github/workflows/frontend-pages.yml`](../.github/workflows/frontend-pages.yml)

## GitHub Pages 公開網址

實際網址會是：

```text
https://<your-github-username>.github.io/First-Ai-worker/
```

如果 repository 名稱改變，網址路徑也會跟著變。

## 為什麼要用 HashRouter

GitHub Pages 是靜態站，直接刷新深層路由容易 404。  
前端改用 `HashRouter` 後，網址在 GitHub Pages 上比較穩定，例如：

```text
https://<your-github-username>.github.io/First-Ai-worker/#/stocks/6230
```

## 建置設定

前端 build 會吃 `VITE_BASE_PATH`：

```text
VITE_BASE_PATH=/<repo-name>/
```

GitHub Actions workflow 會自動把它設成 repository name。

## 前端環境變數

前端只需要：

```env
VITE_SUPABASE_URL=
VITE_SUPABASE_ANON_KEY=
```

不要把 `SUPABASE_SERVICE_ROLE_KEY` 放到前端。

## 手動檢查

1. 到 GitHub repository settings
2. 開啟 Pages
3. 確認 workflow 已成功部署
4. 打開 Pages URL
