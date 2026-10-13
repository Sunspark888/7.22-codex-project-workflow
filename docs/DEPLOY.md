# 部署说明

## Vercel

1. 新建 Project，导入 GitHub 公共仓库 `Sunspark888/7.22-codex-project-workflow`。
2. 在 Project Settings → Git → Production Branch 设为 `gh-pages`（该分支只含 PMR 产品站）。
3. 框架选择 Other，Build Command 留空，Output Directory 留空或 `.`。
4. Deploy 后使用 Vercel 给出的正式 URL，并验证首页与 `/demo/`。

## GitHub Pages（备用）

此仓库 `gh-pages` 分支仅包含网站，不影响 `main` 的现有工作流项目。

仓库 Settings → Pages → Build and deployment → Source = Deploy from a branch → Branch = `gh-pages`、目录 `/(root)` → Save。

站点通常对应 https://sunspark888.github.io/7.22-codex-project-workflow/ ，只有在托管平台报告已发布且实际访问成功后，才能称为 live。