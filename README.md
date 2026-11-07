# 朋域科技 IG 自動宣傳系統｜PENGYU DIGITAL

開始：直接雙擊 [`START_HERE.html`](START_HERE.html) 預覽 25 則素材。

## 功能與部署

- IG 有機貼文排程：每週一、三、五 09:00（Asia/Taipei）。
- GitHub Actions 無需持續開啟個人電腦。
- 使用 Meta 官方 Instagram API with Instagram Login，不使用密碼模擬登入。
- 首發 30 秒 Reel，後續 24 則圖文；僅素材庫內已核准內容會發布。
- `state.json` 追蹤 reserved / published / needs_review，避免故障時重複上傳。
- 所有媒體放在 `docs/media/` 以 GitHub Pages 對外公開。
- 開始前請閱讀 [`SETUP_GUIDE.txt`](SETUP_GUIDE.txt)。

## 資安與注意事項

IG `IG_ACCESS_TOKEN`、`IG_USER_ID` 使用 GitHub Actions Secrets（請不要直接編輯程式碼填入）；公開儲存庫只放對外素材與文案。系統預設 `ENABLE_AUTO_PUBLISH=false`，未設定官方授權與 GitHub Pages 不會自動發布。每次執行會先做帳號與公開素材檢查。Meta token 可能約 60 天過期，需定期維護。本版不會發送大量 DM、刷讚、買粉或購買廣告。

## 本地預覽與測試

```bash
python publisher.py --phase preview
python -m unittest discover -s tests -v
```

## 主要檔案

- `queue.json`：已審核貼文清單與文案，直接改了要 commit 到 GitHub。
- `state.json`：發文進度，請勿手動清空。
- `publisher.py`：Meta 官方內容發布程式。
- `.github/workflows/instagram-auto.yml`：GitHub 雲端排程。
- `docs/media`：圖片／影片公共素材。

## 重要限制

目前版本可自動發布 25 則「預先核准」內容，不是無限 AI 產文；IG 自動排程發布 ≠ Meta 付費廣告。要擴展智能內容生成、每日素材產製、影片與 IG Insights 分析，應在下一版本另行接入並先建立審稿防護。
