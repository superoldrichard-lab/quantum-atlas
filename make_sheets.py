# -*- coding: utf-8 -*-
"""把全部节点照片拼成网格大图供快速目检：12 列网格，格内 96px 图 + id 标注。"""
import json, base64, io, math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).parent
DATA = json.loads((BASE / "quantum_network.json").read_text(encoding="utf-8"))
photos = json.loads((BASE / "photos.json").read_text(encoding="utf-8"))

CELL_W, CELL_H, COLS = 108, 122, 12
try:
    font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 11)
except Exception:
    font = ImageFont.load_default()

nodes = DATA["nodes"]
pages = math.ceil(len(nodes) / (COLS * 8))  # 每页 8 行
for p in range(pages):
    chunk = nodes[p * COLS * 8:(p + 1) * COLS * 8]
    rows = math.ceil(len(chunk) / COLS)
    sheet = Image.new("RGB", (COLS * CELL_W, rows * CELL_H), "white")
    dr = ImageDraw.Draw(sheet)
    for i, n in enumerate(chunk):
        x, y = (i % COLS) * CELL_W, (i // COLS) * CELL_H
        if n["id"] in photos:
            im = Image.open(io.BytesIO(base64.b64decode(photos[n["id"]].split(",", 1)[1]))).convert("RGB")
            sheet.paste(im, (x + 6, y + 2))
        dr.rectangle([x, y, x + CELL_W - 2, y + CELL_H - 2], outline="#cccccc")
        dr.text((x + 3, y + 100), f"{p*96+i}:{n['id'][:13]}", fill="#333333", font=font)
    out = BASE / f".tmp_photo_check/sheet_{p}.png"
    sheet.save(out)
    print(out.name, sheet.size)
print("total nodes:", len(nodes), "with photos:", len(photos))
