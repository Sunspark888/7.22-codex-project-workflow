# PMR 公开静态网站部署

## 静态目录

根目录包含 `index.html`，站内 `demo/` 与 `assets/` 为相对路径。不要移动这三个目录的位置，除非同步改 HTML 路径。

## GitHub Pages

现有公开仓库：`Sunspark888/7.22-codex-project-workflow`，专用分支：`gh-pages`。

1. 打开仓库的 **Settings → Pages**。
2. Build and deployment 下选 **Deploy from a branch**。
3. 选 `gh-pages` 和 `/(root)`，点 **Save**。
4. 等 GitHub 提供访问 URL，再检查主页和 `/demo/` 六区导航。

该分支与主分支隔离，旧公开代码可通过 Git 提交历史回滚。未来可以转移到独立 PMR 专用仓库和自定义域名。

## Vercel

连接 Vercel 后可用静态项目：Framework Preset = Other；Root Directory = 根目录；Build Command 留空；Output Directory 保持根目录。可沿用 `vercel.json` 的安全响应头。部署后再实际访问核对。

## 上线最小验收

- 主页样式、文字正常；演示 `demo/` 有布局而非裸 HTML。
- 六区切换、图表、筛选和 CSV 导出正常；移动端没有横向溢出。
- 合成数据明确标为虚构；未公开任何私有原文、Drive 链接或未经授权的科研图表。
- 公开 URL 能通过未登录的普通浏览器打开，才可声明 `LIVE`。