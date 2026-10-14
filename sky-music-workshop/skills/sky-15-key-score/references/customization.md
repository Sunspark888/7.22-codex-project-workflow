# 可选外观配置 v1.13

## 默认与优先级

用户本次明确选择 > 项目已保存的 presentation > 本 Skill 默认。用户只说“做谱子”时直接用默认，不反复问风格。把选择存入 manifest，不临时改脚本常量。

默认：2160×1080、三条谱面行/页、54px 基准数字、82px 层距、浅蓝粉背景、1:1 2048px 封面、摄影优先。封面用 cinematic 文字布局。数字映射、时间槽、来源复核、快速横线和同按关系不随风格变化。

## 配置示例

在 manifest 顶层添加（不添加即用默认）：

```json
"presentation": {
  "preset": "fullhd",
  "palette": "mint",
  "cover": {
    "style": "fresh",
    "width": 1080,
    "height": 1440,
    "layout": "cinematic",
    "brief": "浅绿草地、云海，标题融入留白"
  }
}
```

| 项 | 可选值／行为 |
| --- | --- |
| preset | default=2160×1080；fullhd=1920×1080；uhd=3840×2160；portrait=1080×1920 |
| width + height | 同时提供时覆盖 preset；宽720–4096，高540–4096整数 |
| palette | default 浅蓝粉；mint 浅绿；paper 米白 |
| cover.style | photo 摄影优先（默认）；fresh 清新；illustration 插画；minimal 极简纯色；custom 按 brief |
| cover.width + height | 同时提供；默认2048×2048；支持横、竖、方封面 |
| cover.layout | cinematic 下方留白文字（默认）；center 居中 |
| cover.brief | 风格/颜色/意象等文字；custom 时必填 |

尺寸适配使用 canonical canvas=2160×1080，不改 `canvas`。仅 presentation 控制导出尺寸。所有数字、横线、点、间距一起等比缩放；不匹配2:1的比例会留浅色边，绝不压扁或切掉音符。四页合成=导出单页的2倍宽高，总谱按组纵排；不二次缩小。竖版当前是完整横谱留边，不是竖版重排，直接告诉用户这一点。想增加实际字大小优先横屏显示或分屏阅读，升高分辨率本身不增加手机上的相对字号。

封面 style/brief 是选图或图像生成的指令，不是脚本自动作画的模型。用户可给底图；否则按选择准备 `cover_art`，然后由 render_cover 排字。minimal 可无底图；其他风格正式输出缺图会报错。新建封面遵循相关图像工具规定。不要用生成模型绘制谱面。

中文封面同时提供 `cover_font_file` 和 `cover_font_family`，例如字体路径和 `Noto Sans CJK SC`。艺术标题另用 `cover_title_font_file` 和 `cover_title_font_family`；按实际字形核对。字体不随仓库分发，用户自行安装合法字体。任何尺寸下文本按图宽适配，极长标题仍须看图验收。

不支持任意改54px、单独拉伸数字、重排音符、插入第四行、关闭校验。遇到未知选项脚本报错；不要拼错参数后静默使用默认。

原谱作者署名不是可选装饰，不能通过个性化关闭。封面主标题保持视觉中心，`by:作者名`以约短边2%的小字号放在右下留白，距边约8%；字色与背景对比清楚。若按构图另行确定性排版，保留同样的清晰署名并目视核对。字体必须覆盖作者名中的实际字形。
