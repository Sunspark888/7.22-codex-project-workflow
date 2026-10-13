# PMR — 专注大项目治理

**一个专注长期复杂项目决策连续性的原型。** 公开版提供产品说明和完全虚构的交互演示，不包含任何私人科研记忆。

## 本仓库站点文件

| 路径 | 内容 |
|---|---|
| `index.html` | 产品主页，面向访客 |
| `demo/index.html` | 六个页面的交互图鉴（演示数据） |
| `assets/styles.css` / `assets/site.js` | 主页样式与脚本 |
| `assets/demo.css` / `assets/demo.js` | 演示交互、实验表格及 CSV 导出 |
| `docs/PUBLIC_STANDARD.md` | **公开版与私人版的不可越界维护规范** |
| `.nojekyll` | GitHub Pages 静态发布支持 |

## 本地体验

```bash
python -m http.server 8000
```

打开 `http://127.0.0.1:8000/`。也可直接双击 `index.html`。无需数据库、服务器、API key 或构建工具。

## 部署状态与公开链接

代码分支为 `gh-pages`。如 Pages 尚未启用，仓库维护者在 **Settings → Pages → Deploy from a branch → gh-pages / (root) → Save** 激活发布。实际可访问 URL 以 Pages 设置显示为准，不能仅凭代码上传就宣称网站已上线。

## 隐私与准确性

- 合成演示的数值不代表任何真实科研成果，亦不是 PMR 的准确率/召回率。
- 不上传任何私人 L1–L4、聊天原文、真实决策目录、私有附件、未公开研究结果或 Drive 访问路径。
- 本项目不默认安装分析追踪脚本；任何公开真实案例都须单独确认权属与许可。

维护准则见 [`docs/PUBLIC_STANDARD.md`](docs/PUBLIC_STANDARD.md)。

作者 **Sunspark** | [GitHub](https://github.com/Sunspark888)