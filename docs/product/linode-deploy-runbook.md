# Linode 部署 Runbook（Step 1）

**伺服器**：`root@172.233.67.244`  
**應用 URL**：https://app.kakusinn.com  
**API Health**：https://app.kakusinn.com/health  
**程式目錄**：`/opt/exposureflow`  
**Compose**：`/opt/exposureflow/infra/docker/docker-compose.prod.yml`  
**Secrets**：`/opt/exposureflow/infra/docker/.env`（首次 bootstrap 自動產生，勿 commit）

## 現階段設定（依 gtm-deployment-scope.md）

- `APP_ENV=staging` — 顧問可用 dev 登入，直到 Step 2 Clerk
- `NEXT_PUBLIC_ENABLE_DEV_AUTH=true`
- 未接 Stripe / 公開註冊 / Client Portal

## 常用指令（SSH 登入後）

```bash
cd /opt/exposureflow/infra/docker
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f api
docker compose -f docker-compose.prod.yml restart api worker web
```

## 重新部署（本機更新後）

```powershell
cd C:\Users\User\Desktop\Exposureflow
tar -czf $env:TEMP\exposureflow-deploy.tgz --exclude=node_modules --exclude=.next --exclude=.git --exclude=apps/web/.next .
scp $env:TEMP\exposureflow-deploy.tgz root@172.233.67.244:/opt/exposureflow-deploy.tgz
```

```bash
ssh root@172.233.67.244 'tar -xzf /opt/exposureflow-deploy.tgz -C /opt/exposureflow && cd /opt/exposureflow/infra/docker && docker compose -f docker-compose.prod.yml build && docker compose -f docker-compose.prod.yml up -d'
```

## 顧問登入（現階段）

1. 開啟 https://app.kakusinn.com/app-entry  
2. 點「登入」→ dev-token 流程（staging）  
3. 或 `/dev/login` 切換 RBAC 角色（僅 staging）

## 下一步

- **Step 2**：Clerk 邀請制 + `APP_ENV=production` + 關 dev-token  
- **Step 3**：GSC OAuth（顧問 Integrations）  
- **新案接入**：[`consultant-site-onboarding-playbook.md`](../product/consultant-site-onboarding-playbook.md)  
- **可選**：綁定網域 + HTTPS（Caddy 443）— 已完成 `app.kakusinn.com`
