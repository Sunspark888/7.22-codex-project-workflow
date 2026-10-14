---
name: sky-15-key-score
description: 将光遇十五键琴谱截图转为统一音区、同时音和节奏间距的高清数字谱，输出封面、单页、四页合成及总谱；支持自选琴谱尺寸、配色和封面风格，默认保留原标准。用于“做谱子”“整理光遇琴谱”“按之前规则排版”；不用于音频扒谱、普通五线谱或视频剪辑。
---

# 光遇十五键琴谱整理

规范 v1.12.0。目标：同一套读谱习惯，换曲不换规则。不要依赖过去聊天或未随包提供的“黄金样图”。本目录的代码、配置与文档就是执行依据。

## 必须先读

1. [score-rules.md](references/score-rules.md)：音符、时间与排版事实。
2. [execution-contract.md](references/execution-contract.md)：命令、恢复和交付。
3. [manifest-schema.md](references/manifest-schema.md) 与 [source-review.md](references/source-review.md)：转录及独立复读格式。
4. 用户选择外观时读 [customization.md](references/customization.md)；默认直接执行，不反复问偏好。
5. 修复错误时查 [failure-cases.md](references/failure-cases.md)，按实际证据更新对应检查。

## 最短执行流程

1. 将当前 Skill 所在目录作为唯一代码根目录。环境需 Node.js >=20、sharp、DejaVu Sans及fontconfig；中文封面需中文字体。普通电脑在本目录 `npm install`，已有依赖可直接运行。
2. 收齐原图，确认歌曲、页序和每条谱面边界；未知起始音省略。保留来源，不把 UI 和账号读成音符。
3. 第一遍按时间记录事件与来源 ID；第二遍独立复读原图生成 source-review.json。不能从第一遍复制账本。差异回看原图，不能按熟悉旋律补音。
4. 四小节一条谱面行，按音乐顺序每三行一页，最后一页可少于三行。使用 manifest schema_version=2；见随附 `examples/demo` 的完整格式，但不要把合成样例当真实读谱证据。
5. 将用户选择存入 `presentation`；省略即2160×1080原版及摄影优先方形封面。准备封面底图、文字字体；插画/清新风格仅在用户选择时覆盖默认摄影偏好。
6. 运行唯一全套入口：

```bash
node "$SKILL_ROOT/scripts/build.mjs" /absolute/path/to/project/manifest.json
```

修谱且复用已确认封面，加 `--reuse-cover`。纯演示用 `npm run demo`；demo不能代替真实来源。

7. 检查 `final/build-report.json`：status=rendered只表示文件生成与检查完成，仍需看成图核对字形、原图疑点及可读性。脚本失败先按具体位置修数据，不删除校验、不覆盖账本迎合错误数据。
8. 保存可恢复项目及全部结果，按封面→全部单页→四页合成→总谱交付。四拼按列阅读：左上P1、左下P2、右上P3、右下P4。不默认发ZIP。

## 不随个性化改变的约束

- 琴键三排：1–5；6、7、1'–3'；4'–7'、1''。单引号是音高点，不能丢。
- 同按事件共享横向中心；同排数字中心距0.50em；连续快音是不同事件。
- 最小时间槽决定1×/2×/3×关系；跨小节、行、页照常连接。用全谱时间轴校验，不能在小节末默认断开。
- 谱面只允许确定性代码渲染；禁止用生成模型重画数字、点或线。
- 54px字号、82px层距是2160×1080基准；自选尺寸只整体等比例适配，不能改音符或压扁。全套输出共享同一配置。
- 模糊来源停在具体疑点。轻量模型可执行已核对数据的渲染；难图转录需要具备视觉识别能力并复核的执行者，不承诺所有模型读任意截图都零错误。

## 文件入口

- `scripts/build.mjs`：全套渲染、合成与结果清单；失败写出实际错误。
- `scripts/settings.mjs`：外观唯一配置解析器，拒绝未知选项。
- `scripts/render_score.mjs`：谱面渲染，强制来源与时间轴校验。
- `scripts/render_cover.mjs`：封面排字，支持独立尺寸。
- `scripts/compose_outputs.mjs`：四拼、总谱，检查单页尺寸一致。
- `scripts/validate_source_review.mjs` / `rapid_timeline.mjs`：来源比较、全谱连接校验。
- `examples/demo/`：无真实歌曲的完整可执行样例。
- `tests/`：历史错误与尺寸适配回归；维护时 `npm test`。

下游视频制作可使用 sky-score-social-video；它不是做谱的必需依赖。
