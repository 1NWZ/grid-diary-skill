#!/usr/bin/env python3
"""按语义计划渲染方格日记；语言理解由调用者完成。"""
import argparse
import json
import math
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageColor


def compact(s):
    return ''.join(s.split())


def font_path(given):
    candidates = [given] if given else [
        '/System/Library/Fonts/Supplemental/Songti.ttc',
        '/System/Library/Fonts/PingFang.ttc',
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
        'C:/Windows/Fonts/msyh.ttc',
    ]
    for p in candidates:
        if p and Path(p).is_file():
            return p
    raise ValueError('未找到中文字体，请通过 --font 指定本地字体。')


def intersects(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def render(plan, output, given_font=None, index=0):
    pages = plan['pages']
    if not pages or not compact(plan['source']):
        raise ValueError('正文与页面不能为空。')
    actual = ''.join(run['text'] for page in pages for run in page['runs'])
    if compact(actual) != compact(plan['source']):
        raise ValueError('排版文字与原文不一致：请检查漏字、重复、标点及顺序。')
    fp = font_path(given_font)
    probe = ImageFont.truetype(fp, 64, index=index)
    def signature(ch):
        mask = probe.getmask(ch)
        return (mask.size, bytes(mask))
    absent = signature(chr(0x10FFFF))
    missing = sorted({c for c in actual if not c.isspace() and signature(c) == absent})
    if missing:
        raise ValueError('疑似字体缺字：' + ''.join(missing))
    cols, rows = plan.get('cols', 14), plan.get('rows', 20)
    if not (4 <= cols <= 32 and 4 <= rows <= 40):
        raise ValueError('格数应在合理范围内：列 4–32，行 4–40。')
    w, h = 1200, 1600
    cell = min(w * .8 / cols, h * .84 / rows)
    x0, y0 = (w-cols*cell)/2, (h-rows*cell)/2
    paper, ink, accent = (plan.get(k, v) for k,v in [
        ('paper','#FAF3DE'), ('ink','#555CA1'), ('accent','#4B72CB')])
    rendered = []
    for pi, page in enumerate(pages):
        rng = random.Random(plan.get('seed', 7) + pi)
        im = Image.new('RGB', (w,h), paper)
        d = ImageDraw.Draw(im)
        def rect(c,r,cw,rh):
            if not all(math.isfinite(v) for v in (c,r,cw,rh)) or c < 0 or r < 0 or cw <= 0 or rh <= 0 or c+cw > cols+1e-6 or r+rh > rows+1e-6:
                raise ValueError(f'第 {pi+1} 页格位越界。')
            return (x0+c*cell, y0+r*cell, x0+(c+cw)*cell, y0+(r+rh)*cell)
        if 'field' in page:
            d.rectangle(rect(*page['field']), fill=accent)
        tiles=[]
        glyphs=[]
        occupied=[]
        for run in page['runs']:
            c, r = run['col'], run['row']
            size, step = run.get('size', .8), run.get('step',1)
            if not (.3 <= size <= 2 and .3 <= step <= 3):
                raise ValueError('字号或字距超出支持范围。')
            n=len(run['text'])
            if not n:
                raise ValueError('不能使用空文字单元。')
            box=rect(c,r,(n-1)*step+max(1,size), max(1,size))
            if run.get('tile',False):
                tiles.append(box)
            f=ImageFont.truetype(fp, round(cell*size), index=index)
            for j,ch in enumerate(run['text']):
                if ch.isspace():
                    continue
                bounds=f.getbbox(ch)
                gw,gh=bounds[2]-bounds[0],bounds[3]-bounds[1]
                patch=Image.new('RGBA',(gw+4,gh+4))
                ImageDraw.Draw(patch).text((2-bounds[0],2-bounds[1]), ch, font=f, fill=run.get('color',ink))
                patch=patch.rotate(rng.uniform(-1.2,1.2),resample=Image.Resampling.BICUBIC,expand=True)
                px=round(x0+(c+j*step+.5*max(1,size))*cell-patch.width/2)
                py=round(y0+(r+.5*max(1,size))*cell-patch.height/2+rng.uniform(-.015,.015)*cell)
                bb=(px,py,px+patch.width,py+patch.height)
                if bb[0]<x0 or bb[1]<y0 or bb[2]>x0+cols*cell or bb[3]>y0+rows*cell:
                    raise ValueError('实际字形越界，请留出更多边距。')
                if any(intersects(bb,b) for b in occupied):
                    raise ValueError('文字发生碰撞，请增加字距或移动文字单元。')
                occupied.append(bb)
                glyphs.append((patch,(px,py)))
        for b in tiles:
            d.rectangle(b,fill=paper)
        grid=Image.new('RGBA',im.size)
        gd=ImageDraw.Draw(grid)
        grid_ink=ImageColor.getrgb(ink)+(85,)
        for c in range(cols+1):
            gd.line((x0+c*cell,y0,x0+c*cell,y0+rows*cell),fill=grid_ink,width=1)
        for r in range(rows+1):
            gd.line((x0,y0+r*cell,x0+cols*cell,y0+r*cell),fill=grid_ink,width=1)
        im=Image.alpha_composite(im.convert('RGBA'),grid)
        for mark in page.get('marks',[]):
            pts=mark['points']
            if len(pts)<2 or any(not(0<=c<=cols and 0<=r<=rows) for c,r in pts):
                raise ValueError('装饰线格位无效。')
            ImageDraw.Draw(im).line([(x0+c*cell,y0+r*cell) for c,r in pts],fill=mark.get('color',ink),width=mark.get('width',3))
        for patch,pos in glyphs:
            im.alpha_composite(patch,pos)
        # 只加入轻量纸纤维颗粒，不改变正文或读取外部图片。
        texture=Image.new('RGBA',im.size)
        td=ImageDraw.Draw(texture)
        for _ in range(45000):
            x,y=rng.randrange(w),rng.randrange(h)
            td.point((x,y),fill=(95,75,50,rng.randrange(3,16)))
        im=Image.alpha_composite(im,texture).convert('RGB')
        target=output if len(pages)==1 else output.with_name(f'{output.stem}-{pi+1:02}{output.suffix}')
        rendered.append((target,im))
    # 全部页面验证通过后才写入，避免前页成功而后页失败。
    targets=[p for p,_ in rendered]
    record=output.with_suffix('.layout.json')
    if any(p.exists() for p in targets+[record]):
        raise ValueError('输出已存在，请改用新文件名以保留旧版本。')
    output.parent.mkdir(parents=True,exist_ok=True)
    for target,im in rendered:
        im.save(target,format='PNG')
    record.write_text(json.dumps({'font':fp,'font_index':index,'plan':plan,'reading_text':actual,'outputs':[str(p) for p in targets]},ensure_ascii=False,indent=2),encoding='utf-8')
    return [str(p) for p in targets]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--plan',required=True,type=Path)
    p.add_argument('--out',required=True,type=Path)
    p.add_argument('--font')
    p.add_argument('--font-index',type=int,default=0)
    args=p.parse_args()
    try:
        result=render(json.loads(args.plan.read_text(encoding='utf-8')),args.out,args.font,args.font_index)
    except (ValueError,KeyError,OSError) as exc:
        p.exit(1,str(exc)+'\n')
    print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':
    main()
