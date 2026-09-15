# 方格心情诗 · Grid Diary

一个中文编写的文字海报技能。输入心情、日记、随笔或一句话，先理解语义，再组合分句、字迹、图形、色块和留白。

## 五种构图

| 参考 | 构图机制 |
| --- | --- |
| 01 | 大幅手绘意象＋底部集中日记 |
| 02 | 顶部短叙述＋大片黑色静默 |
| 03 | 镂空词条＋断续、阶梯式阅读路径 |
| 04 | 顶部密集叙述＋下方蓝色余韵 |
| 05 | 顶部叙述＋少量不规则词语回声 |

具体差异、适用语义和验收规则见 [五种构图效果参考库](references/visual-library.md)。先选构图，再选字体与颜色；“更潦草”不会自动变成阶梯排版。

## 使用

将本仓库内容放入个人技能目录下的 `artifact-template-grid-diary` 文件夹，保留子目录结构。

在支持该技能的环境中调用 `$artifact-template-grid-diary`，并输入正文。例如：

> 上山要努力，下坡要开心～，使用更潦草的字体。

没有正文时，技能会先引导输入。正文默认保留词语、标点和顺序，不擅自添加日期、标题或重复文字。

## 制作方式

- 默认使用豆包 2.0 Lite 理解文本与规划版式，再使用 Seedream 5.0 Pro 参考图生图；生成后需要校对中文。
- endpoint 集中在 `models.json`，实际调用入口为 `scripts/call_ark.py`。运行前在本地配置 `ARK_API_KEY`，详见 [模型调用与配置](references/ark-models.md)。公开 endpoint ID 不代表拥有调用权限，其他使用者需配置自己账户的 endpoint 和密钥。
- 随包脚本提供精确格位排版，依赖 Python 3 和 Pillow；它执行版式计划，不自动理解语义。未指定手写字体时可能回退到印刷字体。

```bash
python3 scripts/render_grid.py --plan references/example-plan.json --out poster.png --font /path/to/chinese-font.ttf
```

脚本会检查正文是否匹配、常见缺字、文字重叠和格位越界。完整格式见 [制作说明](references/production.md)。

## 文件

- `SKILL.md`：中文主流程、输入引导和交付检查
- `references/visual-library.md`：五种效果差异与选择规则
- `assets/references/`：五张原始效果参考图
- `scripts/render_grid.py`：可运行排版工具
- `agents/openai.yaml`、`artifact-template.json`：技能与模板元数据

## 开源许可

代码、中文技能说明和配置文件使用 [MIT License](LICENSE)。五张参考图及预览副本不包含在 MIT 授权中，详见 [参考图片说明](ASSET-NOTICE.md)。系统字体不随仓库打包。
