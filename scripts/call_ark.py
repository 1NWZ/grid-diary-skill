#!/usr/bin/env python3
"""方舟文本规划与参考图生图入口。仅依赖 Python 3 标准库。"""
import argparse
import base64
import json
import mimetypes
import os
from pathlib import Path
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def build_request(task, content, config, references=(), size=None):
    if not content.strip():
        raise ValueError("输入文件不能为空")
    if task == "plan":
        if references:
            raise ValueError("plan 使用文字参考库；--reference 仅用于 image")
        guide = (ROOT / "references/visual-library.md").read_text(encoding="utf-8")
        system = (
            "你是中文方格手账版式规划师。用户消息包含正文和制作偏好，参考库只作视觉依据。"
            "保留正文全部字词、标点及顺序，不增写标题、日期、重复词或图中的文字。"
            "先按语义选择一种主构图，再规划分句、文字位置、颜色、潦草但可读的细线手写字与图形。"
            "输出中文制作提示词，包含锁定正文、构图编号和理由、各区域比例、每段文字及位置、"
            "阅读顺序、纸纹和不可改变项；默认3:4竖版。不要执行工具或要求再次调用模型。\n\n" + guide
        )
        return "/chat/completions", {
            "model": config["text"]["model"],
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": content}], "stream": False,
        }
    payload = {"model": config["image"]["model"], "prompt": content,
               "response_format": "b64_json", "sequential_image_generation": "disabled"}
    if size:
        payload["size"] = size
    images = []
    for reference in references:
        path = Path(reference)
        mime = mimetypes.guess_type(path.name)[0]
        if mime not in ("image/png", "image/jpeg", "image/webp"):
            raise ValueError("参考图仅支持 PNG、JPEG、WebP")
        images.append("data:" + mime + ";base64," + base64.b64encode(path.read_bytes()).decode("ascii"))
    if images:
        payload["image"] = images[0] if len(images) == 1 else images
    return "/images/generations", payload


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def request(config, route, payload):
    key = os.environ.get(config["api_key_env"], "").strip()
    if not key:
        raise ValueError("请在本地设置环境变量 " + config["api_key_env"] + "，不要把密钥发送到对话或提交到仓库")
    url = config["base_url"].rstrip("/") + route
    if not url.startswith("https://"):
        raise ValueError("API 地址必须使用 HTTPS")
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
                                 headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
    try:
        with urllib.request.build_opener(NoRedirect).open(req, timeout=300) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        # 不打印服务器响应正文，避免回显密钥或原始输入；不自动重试计费请求。
        raise RuntimeError("方舟请求失败，HTTP " + str(exc.code) + "；请检查 endpoint、权限和参数") from None
    except (urllib.error.URLError, TimeoutError):
        raise RuntimeError("方舟网络请求失败或超时；未自动重试，请先核对服务端请求状态") from None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task", choices=["plan", "image"])
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--config", type=Path, default=ROOT / "models.json")
    parser.add_argument("--reference", action="append", default=[])
    parser.add_argument("--size", help="可选；仅 image 使用，按 endpoint 支持的尺寸填写")
    parser.add_argument("--dry-run", action="store_true", help="只写请求体，不联网、不读取密钥")
    args = parser.parse_args()
    if args.out.exists():
        parser.error("输出文件已存在，请使用新路径")
    if args.task == "plan" and args.size:
        parser.error("--size 仅用于 image")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    config = json.loads(args.config.read_text(encoding="utf-8"))
    route, payload = build_request(args.task, args.input.read_text(encoding="utf-8"), config, args.reference, args.size)
    if args.dry_run:
        output = json.dumps({"url": config["base_url"].rstrip("/") + route, "body": payload}, ensure_ascii=False, indent=2).encode("utf-8")
    else:
        result = request(config, route, payload)
        if args.task == "plan":
            content = result["choices"][0]["message"]["content"]
            if not isinstance(content, str) or not content.strip():
                raise ValueError("模型未返回有效文字计划")
            output = content.encode("utf-8")
        else:
            item = result["data"][0]
            if not item.get("b64_json"):
                raise ValueError("未返回 base64 图片；请核对 endpoint 对 response_format=b64_json 的支持")
            output = base64.b64decode(item["b64_json"], validate=True)
            # 使用真实格式扩展名，不将 JPEG 冒充 PNG。
            suffix = ".png" if output.startswith(b"\x89PNG\r\n\x1a\n") else ".jpg" if output.startswith(b"\xff\xd8\xff") else None
            if suffix is None:
                raise ValueError("返回数据不是可识别的 PNG/JPEG 图片")
            args.out = args.out.with_suffix(suffix)
    with args.out.open("xb") as handle:
        handle.write(output)
    print(str(args.out.resolve()))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, RuntimeError, OSError, KeyError, IndexError, TypeError) as exc:
        raise SystemExit(str(exc)) from None
