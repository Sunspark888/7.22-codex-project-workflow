# PMR · 专注大项目治理｜公开产品站

这是 **Sunspark PMR 的公开展示版**，与私有科研项目的 L2H 原始图鉴分开维护。

- `index.html`：产品概念与设计原则
- `demo/`：脱敏、虚构的交互式示例图鉴
- `assets/`：静态样式与脚本，不引用第三方服务
- `.nojekyll`：静态部署时禁用 Jekyll

## 对外发布边界

不得上传私人项目中的 L1–L4 原始资料、实际历史聊天、完整决策总账、未发表实验结果、个人凭据或私有 Drive 链接。即使这些内容在本地已经成为图鉴中的公开 HTML，也不能由此推定获得对外发表许可。本网站仅使用明确标记的虚构演示记录。

## 本地运行

直接打开 `index.html`，或运行：

```sh
python -m http.server 8000 -d .
```

随后访问 `http://localhost:8000/`。站点无构建步骤、无后端、无用户数据收集。

## 部署

将目录发布到任何静态托管服务（Vercel、GitHub Pages 等）。GitHub Pages 可使用站点独立的 `gh-pages` 分支根目录；如未配置站点，管理员需要在 Settings → Pages 选择发布来源。

署名：Sunspark | https://github.com/Sunspark888