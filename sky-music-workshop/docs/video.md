# 演奏视频：从原录屏到发布包

[返回云间琴房](../README.md) · [完整 Skill](../skills/sky-score-social-video/SKILL.md)

## 录屏怎么给

一份连续录屏就能开始。弹错后留一段明显停顿，从完整乐句重新弹，保留上下文和自然尾音。停顿没有统一的必需秒数，也不是自动删除指令。已有额外补录可以一起交付，不要求重新拍成单文件。

同时提供已经确认的连续单页琴谱、封面或封面偏好；已有项目可复用已确认资产。没有谱面时先运行琴谱 Skill。

还需沿用或确认原谱作者，清单填`score_source.author`和`basis`。封面与视频内封面保留小号`by:作者名`；中文作者名提供`score_source.font_file`。未知先问，不把演奏者当成原谱作者。

AI需要核对哪个片段是错弹、哪个片段是重弹，区分歌曲本身的反复；不能仅凭静音或音符不同删内容。只录了错误、没有正确补弹时，需要补录或保留并标记问题。

## 运行条件

- Python 3，Pillow、NumPy；系统安装 ffmpeg、ffprobe。
- 代理能够检查视频帧、音频及源谱面。只有文字聊天能力不足以完成成片。
- 中文或特殊字体由用户提供合法字体；琴键字体可在清单设置 `key_font`。

```bash
python -m pip install Pillow numpy
ffmpeg -version
ffprobe -version
```

依赖未做跨全部操作系统的兼容认证；字体与设备录屏布局需要实际检查。

## 代理执行顺序

先完整读 Skill 及其引用的剪辑、游标、失败处理、封面和文案规则。以 `references/cursor-project-example.json` 建立本次项目；模板的时间与坐标不是实际歌曲数据。

1. 核对视频与图片，记录源尺寸、素材顺序和谱面身份。
2. 分析原演奏，建立经过核对的保留片段 `segments`，包括源文件及起止秒数。
3. 由同一清单制作剪后音轨，按成品时间建立页、行、位置锚点 `anchors`。
4. 合成琴谱、封面、演奏与彩色游标。
5. 查看编码后的换页与剪辑接点抽帧，听接点与密集段，再确认可交付状态。
6. 制作四平台封面及文案，一起交付。

```bash
python /path/to/sky-score-social-video/scripts/render_edit_audio.py /path/to/project.json
python /path/to/sky-score-social-video/scripts/render_cursor_video.py /path/to/project.json
python /path/to/sky-score-social-video/scripts/render_platform_covers.py /path/to/project.json
```

**这些命令执行已核对的清单，不会自行识别错音或补全锚点。** 参数、素材与剪辑判断由执行代理准备。默认1920×1080、30fps、H.264＋AAC，直接读取原录屏，尽量减少反复压缩；放大低清素材不能恢复原本不存在的细节。

## 个性化与适配

游标可改色，需与谱面保持明显对比；封面跟随作品情绪。不同设备录屏须先校准裁切和十五键位置。当前视频脚本使用2160×1080谱面坐标基准和固定行高；琴谱模块的自选尺寸不能不经坐标换算就直接套用视频锚点。

四平台各有封面文件，同一主视觉重新构图。包内比例是起始模板，不承诺平台永久不变；未进入App确认裁切时，交付记录须注明。用户检查发布预览后可继续适配。

## 交付清单

- 一份经过音画检查的跟弹MP4。
- 小红书、抖音、快手、视频号分别命名的封面。
- 各平台标题、正文、标签和置顶评论草稿，以及少量备选标题。
- 项目清单、剪辑依据、同步锚点、输出索引和仍存在的具体疑点。

`encoded_pending_visual_audio_review` 仅表示编码后等待音画检查，不能直接写“全部完成”。不存在逐音核对证据时，不宣称所有错音都已自动修正。发布素材不包括自动发帖。
