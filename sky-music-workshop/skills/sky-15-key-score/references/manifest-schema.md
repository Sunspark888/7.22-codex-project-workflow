# 结构化谱面清单

随附脚本接收一个 JSON manifest。路径既可为绝对路径，也可相对 manifest 文件所在目录。

```json
{
  "schema_version": 2,
  "score_source": {
    "author": "sky荼苏",
    "basis": "示例：用户明确确认该截图的原谱作者；实际任务必须替换为真实依据"
  },
  "song": {
    "title": "Leave Me Alone",
    "subtitle": "寂寞作伴",
    "start_note": "A = E♭"
  },
  "output_dir": "./final",
  "score_background": "./score-bg.png",
  "cover_art": "./cover-art.png",
  "cover_font_file": "./NotoSansCJK-Regular.ttc",
  "cover_title_font_file": "./ArtisticTitle.otf",
  "cover_title_font_family": "Artistic Title",
  "canvas": {"width": 2160, "height": 1080},
  "slots_per_measure": 8,
  "audit": {
    "source_review": "./source-review.json",
    "event_transcription_verified": true,
    "rapid_candidates_verified": true,
    "source_page_count": 1,
    "source_system_count": 1,
    "source_note_count": 5,
    "source_dot_count": 2,
    "regression_checks": ["example-rapid-chain"]
  },
  "pages": [
    {
      "label": "P1",
      "systems": [
        {
          "source_system_id": "src1-row1",
          "measures": [
            [
              {"slot": 0, "notes": ["1", "4", "1'"], "rapid_to_next": false, "source_event_id": "src1-row1-t0"},
              {"slot": 2, "notes": ["5"], "rapid_to_next": true, "source_event_id": "src1-row1-t2"},
              {"slot": 3, "notes": ["3'"], "rapid_to_next": false, "source_event_id": "src1-row1-t3"}
            ],
            [], [], []
          ]
        }
      ]
    }
  ]
}
```

## 字段

- `song.title`：必填，封面和页眉标题。
- `score_source.author`：强制，已确认的原谱作者显示名，只填姓名/账号，不带 `by:`。上面的 sky荼苏仅示范格式，不是默认作者；未知先询问，不能填“未知/待确认”后交付。
- `score_source.basis`：强制，原图可见署名、原始来源链接或用户确认等实际依据。多来源先分别确认作者，涉及不同作者时完整列出，不只署排版者或演奏者。
- 封面生成器自动排入 `by:作者名`。复用已有封面前实看当前署名，记入 `audit.cover_credit_verified=true`；缺此核对不得用 `--reuse-cover` 跳过署名。
- `song.subtitle`：可选，中文名或副标题。
- `song.start_note`：可选；原谱或用户明确提供时填写。缺失时封面自动省略，不能填默认值。
- `output_dir`：输出目录。
- `score_background`：浅色谱面背景，可选；省略时使用内置浅色渐变。
- `cover_art`：按所选封面比例裁切的底图。默认摄影优先；其他风格按 presentation.cover.style / brief；minimal可用纯色无底图。
- `cover_font_file`：封面包含中文或其他非拉丁文字时必填，必须指向支持这些字形的 TTF/OTF/TTC 字体；缺失时脚本会停止，防止输出方框乱码。
- `cover_title_font_file`：可选，只用于封面主标题的艺术字体；按歌曲选择自然、有表现力的字形，不把缺省字体当作所有歌曲的固定模板。副标题和起始音仍使用 `cover_font_file`，避免艺术字降低调号或说明文字的清晰度。缺失时标题沿用 `cover_font_file`，仍须通过实际字形与画面融合验收。
- `cover_title_font_family`：可选；当运行环境已安装标题字体时填字体族名，用于确保 SVG 渲染器正确选中艺术字。应与 `cover_title_font_file` 的实际字体族一致。
- `schema_version`：新版结构化谱面固定为 `2`。
- `canvas`：内部基准固定2160×1080。导出尺寸只用新增 `presentation`；完整选项见 [customization.md](customization.md)。默认四拼4320×2160，自定义四拼为单页宽高各乘2。
- `slots_per_measure`：每小节最小时间槽数，默认 8。
- `audit.event_transcription_verified`：逐事件对照来源后填 `true`；不得仅凭 OCR 通过。
- `audit.source_review`：必填，独立复读原图得到的来源账本路径；完整格式和执行要求见 [source-review.md](source-review.md)。不能从待验 manifest 反向生成这一账本。
- `systems[].source_system_id` / `event.source_event_id`：必填，对应来源账本中的稳定行／事件 ID。
- `audit.rapid_candidates_verified`：已逐个检查所有紧密相邻候选、跨小节、跨行和跨页连续关系后填 `true`。
- `audit.source_page_count`：来源谱面页数，用来检查漏页。
- `audit.source_system_count`：来源中实际可见的谱面行总数；必须等于 manifest 内的 `systems` 总数，分页顺延不改变它。
- `audit.source_note_count`：来源中实际可见的数字总数；必须等于 manifest 所有事件的 `notes` 元素总数。禁止用集合去重相同数字。
- `audit.source_dot_count`：来源中实际可见、已归属数字的附点总数；必须等于 manifest 音符字符串中的单引号总数。
- `audit.regression_checks`：用户指出过的具体错误或本曲高风险位置；修正后保留为可重复检查项。
- `pages[].label`：P1、P2……。
- `systems[].measures`：一行中的小节数组；标准为四小节。转录后先展平全部 `systems`，再按原顺序每三项组成一个输出页；除最后一页外，每个 `pages[].systems` 必须恰好三项。禁止保留来源旧分页、缩字或压缩行距容纳第四行。
- `event.slot`：事件在当前小节中的整数时间槽，从 0 开始。
- `event.notes`：同一时刻按下的全部键。
- `event.rapid_to_next`：该事件是否与下一个全局事件组成连续快速关系。可跨小节、谱面行和页面。

## 音符写法

- 第一排：`1`–`5`
- 第二排低音：`6`、`7`
- 第二排高音：`1'`、`2'`、`3'`
- 第三排：`4'`–`7'`、`1''`

单引号数量控制附点/高音标记，渲染时必须逐个保留。

## 转录约束

- 先确定事件时间，再填写音符；不要按视觉均匀分布反推节奏。
- 同次按键的音全部放进一个 `notes` 数组。
- 不同事件即使数字相同，也必须分成不同对象。
- 同一个 `notes` 数组不得包含重复键；若同一 x 分组出现两个相同数字，优先怀疑相邻事件被误并，不能用 `Set`、字典键或其他去重操作静默删掉一个。
- 快速关系优先显式填写 `rapid_to_next`，不要依赖脚本猜测。
- 每个事件必须显式填写布尔值 `rapid_to_next`。渲染器不会用最终横向距离替你猜快速关系。
- 默认渲染器每条谱面行严格四小节；来源不同需显式扩展几何与校验后执行，不得静默误排。
- 像素裁切、OCR、连通域和聚类只能生成候选；逐事件对照完成并写入 `audit` 后才可最终渲染。

## 全谱连接

rapid_to_next 描述下一个全谱事件，不是当前小节数组的下一个元素。使用 scripts/rapid_timeline.mjs 校验已确认槽位；不要在逐小节 map 中把末音默认设为 false。来源账本的 systems 顺序就是音乐顺序，重新分页不能重新排序。

## v1.12 补充

`cover_font_family` 必须与 `cover_font_file` 实际字族一致；独立标题文件需 `cover_title_font_family`。`demo: true` 仅用于合成样例，账本method=synthetic_fixture；真实任务不能设置demo。全套运行用 build.mjs，输出清单包括实际尺寸。
