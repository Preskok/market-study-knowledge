# Outlook MCP Setup Guide

When configured, `ams-health` will query the last 12h of emails from:
- `graylogprod@b2b-carmarket.com` (Graylog alerts)
- `system@preskok.si` (AMS system notifications)

And show a grouped summary by subject pattern alongside the RMQ table.

## Recommended MCP: Softeria ms-365-mcp-server

GitHub: https://github.com/Softeria/ms-365-mcp-server
Requires: Microsoft 365 account + Azure AD app registration (Mail.Read permission)

## Setup steps

### 1. Register an Azure AD app (one-time, requires tenant admin)

1. Go to https://portal.azure.com → Azure Active Directory → App registrations → New registration
2. Name: `claude-ams-health`, Supported account types: "Accounts in this org only"
3. After creation: API permissions → Add permission → Microsoft Graph → Delegated → `Mail.Read` → Grant admin consent
4. Certificates & secrets → New client secret → copy the value (shown once)
5. Note your Application (client) ID and Directory (tenant) ID from the Overview page

### 2. Install the MCP server

```
npm install -g @softeria/ms-365-mcp-server
```

### 3. Add to Claude Code

```
claude mcp add ms365 -- npx @softeria/ms-365-mcp-server \
  --tenant-id YOUR_TENANT_ID \
  --client-id YOUR_CLIENT_ID \
  --client-secret YOUR_CLIENT_SECRET
```

### 4. Verify

Run `claude mcp list` — you should see `ms365` listed.
Then run `ams-health` — the email section will appear automatically.

## Detection at runtime

`ams-health` probes for MCP tools containing "mail", "message", or "outlook" in their name.
If found → queries last 12h filtered by the two senders above.
If not found → prints: "📧 Outlook MCP not configured — see references/outlook-mcp-setup.md"
