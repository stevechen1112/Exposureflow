# ExposureFlow 上線與部署 Scope（GTM 決策紀錄）

**生效日期**：2026-06-14  
**決策者**：Product / 營運（使用者確認）  
**狀態**：**現階段有效 — Agent 部署與上線工作必須優先遵循本文件**

> **重要**：本文件針對 **Production 部署、上線驗收、整合優先序** 的 scope 決策。  
> 與 `pre-launch-audit.md`、`launch-checklist.md` 中「全自助 SaaS」假設衝突時，**以本文件為準**。  
> Phase 0–14 **工程開發**仍依 `exposureflow-development-plan.md` 與 `AGENTS.md` 憲章。

---

## 1. 商業模式（已確認）

| 項目 | 決策 |
|------|------|
| 目標用戶 | **SEO 顧問／代理商**（非終端企業 DIY） |
| 簽約 | **人工線下簽約** |
| 收款 | **人工線下收款**（非系統內自助結帳） |
| 自助註冊 | **不開放** |
| 自助計費 / Stripe Checkout | **現階段不需要** |
| 服務交付 | 顧問 **線下＋線上代操**（onboarding、GSC、decision、報表等） |
| 終端客戶 | **現階段不進系統**；報表可先 **PDF 線下交付** |

本產品主軸與 `exposureflow-development-plan.md` §7（顧問面談、關鍵字金字塔、agency 代管 client workspace）一致；**不是**「企業客戶自助 DIY SEO 平台」。

---

## 2. 現階段 Phase（Consultant-Only）

**現階段 = 僅顧問團隊使用後台**，不包含 Client Portal 對外上線。

### 2.1 顧問現階段流程

```text
人工簽約（線下）
  → 平台／營運開通顧問帳號（Clerk 邀請制）
  → 建立 client workspace + site
  → 顧問完成 strategy / onboarding
  → 顧問連 GSC → 觸發 sync
  → opportunity → decision 核准 → 產生／匯出報表
  → （可選）PDF 線下交給客戶
```

### 2.2 角色重點

| 角色 | 現階段 |
|------|--------|
| owner / admin / strategist / editor / analyst | ✅ 使用 |
| client_viewer | ❌ **現階段不上線**（Client Portal 延後） |
| billing_admin（自助 Stripe） | ❌ 現階段不需要 |

---

## 3. Production 最小集合（現階段必做）

| 優先 | 項目 | 說明 |
|------|------|------|
| **P0** | Linode（或同等 VPS）部署 | API + Web + Celery Worker + Postgres(pgvector) + Redis + HTTPS |
| **P0** | Secrets | `DATABASE_URL`、`ENCRYPTION_KEY`、Clerk keys、Google OAuth 等；禁止 commit |
| **P0** | Clerk **邀請制** | 關閉公開註冊；僅受邀顧問 email 登入；Production **禁用** `dev-token` |
| **P0** | GSC OAuth（**顧問端**） | owner/admin 在 Integrations 代客戶連線；非客戶 DIY |
| **P1** | 簽約後開通 SOP | 誰建 workspace、誰是 owner、如何發 Clerk 邀請 |
| **P1** | Postgres 備份 | 每日 backup + 還原程序至少文件化 |

### 3.1 現階段驗收標準（4 條）

1. 顧問以 Clerk 登入（非 dev-token）
2. 可建立 workspace / site、完成 onboarding
3. GSC 連線成功且 sync 有資料
4. opportunity → decision → report 匯出可用

**以上四條通過 = 現階段可給顧問實際接案使用。**

---

## 4. 現階段明確不做（勿擅自擴 scope）

以下項目存在於產品能力或 `launch-checklist.md`，但 **現階段 GTM 不要求**。Agent **不得**因 audit / checklist 而默認必做：

| 不做 | 原因 |
|------|------|
| 公開自助註冊 | 人工簽約後開通 |
| Stripe Checkout / Portal / Webhook 演練 | 線下收款 |
| Launch checklist「自助客戶七步」E2E | 非本階段商業模式 |
| Client Portal / 邀請 client_viewer | 第二階段 |
| 客戶 DIY 連 GSC | 由顧問代連 |
| 完整 Email 通知（SendGrid/SES） | 可第二波；sync 失敗可先後台查看 |
| Staging 第二套環境 | 可選；小團隊可先單一 Linode 環境謹慎發版 |
| EF-0206 Brand Web Presence | 維持 DEFERRED，除非 Product 另決 |

---

## 5. 與其他文件的關係

| 文件 | 用途 | 與本文件關係 |
|------|------|--------------|
| `exposureflow-development-plan.md` | Phase 工程規格 | 工程能力依計畫；**部署優先序**依本文件 |
| `pre-launch-audit.md` | 全自助 SaaS GA audit | BLOCKER 清單參考，但 **scope 以本文件縮減** |
| `launch-checklist.md` | 通用上線檢查 | 「顧問客戶旅程」適用；「自助客戶旅程」**現階段不適用** |
| `GET /api/v1/launch/readiness` | 工程健康儀表板 | **不能**替代本文件的 GTM scope |

---

## 6. 建議實作順序（部署工作）

1. Dockerfile + Linode `docker-compose`（或同等）— 服務跑起來  
2. Clerk 邀請制 + Production 關閉 dev-token — 顧問安全登入  
3. GSC OAuth — Integrations 顧問端連線  
4. 簽約後開通 SOP — 營運文件（見 [`consultant-site-onboarding-playbook.md`](./consultant-site-onboarding-playbook.md)）  

---

## 7. 第二階段（未來，現階段不啟動）

待顧問後台穩定後，Product 可另決是否啟動：

- Client Portal + `client_viewer` 邀請  
- Email 通知  
- Stripe（若改為線上訂閱）  
- Staging 環境 + 完整 E2E  

**第二階段需 Product 明確確認後才可開始，Agent 勿自動擴展。**

---

## 8. 修訂紀錄

| 日期 | 變更 |
|------|------|
| 2026-06-14 | 初版：顧問優先、無自助註冊／計費、Consultant-Only 現階段、Linode 部署最小集合 |
