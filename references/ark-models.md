# 方舟模型调用

`models.json` 是调用配置的唯一读取入口。名称是用户指定的部署说明；API 的 `model` 字段使用 endpoint ID，实际部署模型以方舟控制台为准。

| 用途 | 模型 | endpoint |
| --- | --- | --- |
| 语义理解、分句、构图和提示词规划 | 豆包 2.0 Lite | `ep-20260914174304-5d8v2` |
| 参考图驱动生图 | Seedream 5.0 Pro | `ep-20260914155654-cjmcd` |

默认地址为 `https://ark.cn-beijing.volces.com/api/v3`。凭据只从本地环境变量 `ARK_API_KEY` 读取，不写进 JSON、提示词或 GitHub。开源使用者需换成自己账户下可用的 endpoint；仅有 ID 无法获得调用权限。此配置不改变 Codex 宿主对话模型；`artifact-template.json` 中的 `galleryKind` 仅是展示元数据。

## 使用流程

以下命令在技能目录执行，脚本仅依赖 Python 3 标准库。先在运行环境安全配置 `ARK_API_KEY`；脚本不会自动加载 `.env`。

1. 将用户原文与明确的制作偏好写到工作目录的 `input.txt`，区分正文与偏好。
2. 调用文本模型：

```bash
python3 scripts/call_ark.py plan --input input.txt --out plan.txt
```

3. 阅读 `plan.txt`，按 `SKILL.md` 校对完整正文、区域比例、断句与构图规则；把修正后的完整生图提示词保存为 `prompt.txt`。本步骤由宿主执行校对，不再引入第二个文本 API 模型。规划输出是制作提示词，不是 `render_grid.py` 的 JSON。
4. 查看所选参考图，随后作为真实图片输入调用生图模型。例如选05时：

```bash
python3 scripts/call_ark.py image --input prompt.txt --reference assets/references/05-yellow-echo.png --out poster.png
```

`--reference` 可重复传入1–2次，图片会编码为 data URI 随请求发送。无需参考图时可省略。默认尺寸交给服务端，提示词明确约3:4竖版；要求具体尺寸时通过 `--size` 传入该 endpoint 支持的值。脚本请求单图与 base64 返回，不预设额外风格参数；按实际 PNG/JPEG 格式保存扩展名，以脚本打印的路径为准。

5. 查看成图并校对，不把调用成功等同于中文正确。需要再生成时使用新的输出文件名。

缺少密钥、权限不足、参数不支持或网络失败时停止并说明具体阶段，不自动更换模型，不自动重试计费请求。超时后先核对服务端状态。首次实际调用仍需验证部署可用性和参数支持；离线检查不证明线上可用。

## 不联网检查

在上述命令追加 `--dry-run` 并将 `--out` 指向新的 JSON 文件，只输出 URL 与请求体，不读取密钥、不发请求。请求体含用户正文及参考图数据，应留在工作目录，不提交到仓库。

## 接口依据

- [火山引擎官方 Python SDK 文本调用示例](https://github.com/volcengine/volcengine-python-sdk/blob/master/volcenginesdkexamples/volcenginesdkarkruntime/completions.py)
- [火山引擎官方 Python SDK 图像接口](https://github.com/volcengine/volcengine-python-sdk/blob/master/volcenginesdkarkruntime/resources/images/images.py)

SDK 接口定义用于核对请求格式，不构成特定部署模型支持所有可选参数的保证。
