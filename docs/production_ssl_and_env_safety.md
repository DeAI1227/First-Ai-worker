# Production SSL and Environment Safety

這份文件說明 Supabase 寫入流程在 production 與 development 的 SSL 安全規則。

## 為什麼 production 不能使用 `verify=False`

`verify=False` 會跳過 TLS 憑證驗證。對 production 來說，這代表：

- 可能被中間人攔截
- `SUPABASE_SERVICE_ROLE_KEY` 可能外洩
- 寫入資料可能被偽造或竄改

因此 production-safe 模式下，SSL 驗證失敗就必須直接失敗，不能自動退回 `verify=False`。

## 環境變數

### 正式環境必填

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`

### 開發環境預設

- `ENVIRONMENT=development`
- `ALLOW_INSECURE_SSL=false`

## 如果本機有 HTTPS / TLS 檢查

如果 Windows、防毒軟體或公司網路會做 HTTPS/TLS 檢查，請不要改成 `verify=False`。  
請改用檢查用根憑證，並設定以下任一環境變數：

- `SUPABASE_CA_BUNDLE`
- `REQUESTS_CA_BUNDLE`
- `SSL_CERT_FILE`

程式會優先使用你指定的 CA bundle，仍然保持 SSL 驗證開啟。這是 production-safe 的做法。

## `ALLOW_INSECURE_SSL` 的用途

只有在下列條件同時成立時，才允許 insecure fallback：

- `ENVIRONMENT=development`
- `ALLOW_INSECURE_SSL=true`

這只適合本機 debug。正式環境不得設定 `ALLOW_INSECURE_SSL=true`。

## `wrote_to_supabase` 的判斷

`wrote_to_supabase=true` 的前提是：

1. 真的走到 Supabase write path
2. 寫入成功
3. 不是 dry-run
4. 沒有 SSL / env / write error

如果只是本地產出 packet、dry-run，或寫入流程失敗，`wrote_to_supabase` 必須是 `false`。

## 常見錯誤訊息

- `SUPABASE_SSL_VERIFICATION_FAILED`
- `ALLOW_INSECURE_SSL is false`
- `Refusing to retry with verify=False in production-safe mode`

若 development 允許 insecure fallback，會看到：

- `WARNING: insecure SSL fallback enabled by ALLOW_INSECURE_SSL=true`

## service role key

`SUPABASE_SERVICE_ROLE_KEY` 只能放後端 `.env`。
前端只用 `VITE_SUPABASE_URL` 和 `VITE_SUPABASE_ANON_KEY`，讀 production views，不碰 service role key。
