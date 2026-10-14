#!/usr/bin/env python3
"""Deterministic builder and boundary verifier for Sky 15-key play-along videos."""

from __future__ import annotations

import argparse
import copy
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from source_credit import score_credit, credit_cover


CANVAS = (1920, 1080)
SCORE_BOX = (20, 114, 1240, 852)
COVER_BOX = (1343, 32, 530, 530)
PERFORMANCE_BOX = (1268, 614, 640, 454)
KEY_LABELS = ["1", "2", "3", "4", "5", "6", "7", "1̇", "2̇", "3̇", "4̇", "5̇", "6̇", "7̇", "1̈"]
DEFAULT_CENTERS = [
    (220 / 736, 88 / 512), (294 / 736, 88 / 512), (368 / 736, 88 / 512), (442 / 736, 88 / 512), (516 / 736, 88 / 512),
    (220 / 736, 159 / 512), (294 / 736, 159 / 512), (368 / 736, 159 / 512), (442 / 736, 159 / 512), (516 / 736, 159 / 512),
    (220 / 736, 230 / 512), (294 / 736, 230 / 512), (368 / 736, 230 / 512), (442 / 736, 230 / 512), (516 / 736, 230 / 512),
]


def fail(message: str) -> None:
    raise ValueError(message)


def atomic_json(data: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".rendering")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def atomic_png(image: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.stem + ".rendering.png")
    image.save(tmp, format="PNG", compress_level=6)
    with Image.open(tmp) as check:
        check.load()
        if check.size != image.size:
            fail(f"PNG size mismatch: {tmp}")
    os.replace(tmp, path)


def run(command: list[str], capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=True, text=True, capture_output=capture)


def resolve(base: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (base / path).resolve()


def load_manifest(path: Path) -> tuple[dict[str, Any], Path]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data, path.resolve().parent


def ffprobe(path: Path) -> dict[str, Any]:
    result = run([
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration:stream=codec_type,codec_name,width,height,r_frame_rate",
        "-of", "json", str(path),
    ], capture=True)
    return json.loads(result.stdout)


def image_info(path: Path) -> dict[str, Any]:
    with Image.open(path) as image:
        image.load()
        return {"width": image.width, "height": image.height, "mode": image.mode}


def video_stream(probe: dict[str, Any]) -> dict[str, Any]:
    streams = [s for s in probe.get("streams", []) if s.get("codec_type") == "video"]
    if not streams:
        fail("Performance video has no video stream")
    return streams[0]


def validate_manifest(data: dict[str, Any], base: Path) -> dict[str, Any]:
    score_credit(data)
    for binary in ("ffmpeg", "ffprobe"):
        if not shutil.which(binary):
            fail(f"Required binary not found: {binary}")

    assets = data.get("assets") or {}
    video_cfg = data.get("video") or {}
    output_cfg = data.get("output") or {}
    pages = assets.get("pages") or []
    if not pages:
        fail("assets.pages must contain at least one page")

    performance = resolve(base, assets.get("performance_video", ""))
    cover = resolve(base, assets.get("cover", ""))
    if not performance.is_file():
        fail(f"Performance video missing: {performance}")
    if not cover.is_file():
        fail(f"Cover missing: {cover}")

    probe = ffprobe(performance)
    stream = video_stream(probe)
    source_duration = float(probe["format"]["duration"])
    duration = float(video_cfg.get("duration", source_duration))
    if duration <= 0 or duration > source_duration + 0.05:
        fail(f"video.duration must be >0 and no longer than source ({source_duration:.3f}s)")

    page_records = []
    previous_end = 0.0
    fps = int(video_cfg.get("fps", 30))
    tolerance = 1.0 / fps + 1e-4

    for expected, page in enumerate(pages, start=1):
        number = int(page.get("page", -1))
        if number != expected:
            fail(f"Page numbers must be continuous: expected P{expected}, got P{number}")
        path = resolve(base, page.get("path", ""))
        if not path.is_file():
            fail(f"P{number} missing: {path}")
        info = image_info(path)
        start, end = float(page["start"]), float(page["end"])
        if end <= start:
            fail(f"P{number} end must be later than start")
        if abs(start - previous_end) > tolerance:
            fail(f"Timeline gap/overlap before P{number}: {previous_end:.3f} -> {start:.3f}")
        page_records.append({"page": number, "path": str(path), "start": start, "end": end, **info})
        previous_end = end

    if abs(previous_end - duration) > tolerance:
        fail(f"Last page must end at video.duration ({duration:.3f}s), got {previous_end:.3f}s")

    rows = data.get("row_timeline") or []
    for i, item in enumerate(rows, start=1):
        page, row = int(item["page"]), int(item["row"])
        start, end = float(item["start"]), float(item["end"])
        if not 1 <= page <= len(pages) or row not in (1, 2, 3):
            fail(f"row_timeline[{i}] has invalid page/row")
        p = page_records[page - 1]
        if start < p["start"] - tolerance or end > p["end"] + tolerance or end <= start:
            fail(f"row_timeline[{i}] must stay within P{page}'s interval")

    end_card_start = video_cfg.get("end_card_start")
    if end_card_start is not None and not 0 <= float(end_card_start) < duration:
        fail("video.end_card_start must be inside video.duration")

    crop = (data.get("performance") or {}).get("crop_normalized", [0, 0, 1, 1])
    if len(crop) != 4 or any(float(v) < 0 or float(v) > 1 for v in crop):
        fail("performance.crop_normalized must contain four values in [0,1]")
    if float(crop[2]) <= 0 or float(crop[3]) <= 0 or float(crop[0]) + float(crop[2]) > 1.0001 or float(crop[1]) + float(crop[3]) > 1.0001:
        fail("performance.crop_normalized must be [x,y,width,height] inside the frame")

    centers = (data.get("performance") or {}).get("key_centers_normalized", DEFAULT_CENTERS)
    if len(centers) != 15 or any(len(point) != 2 for point in centers):
        fail("Exactly 15 key centers are required")
    if any(not (0 <= float(v) <= 1) for point in centers for v in point):
        fail("Key centers must be normalized to [0,1]")

    known_issues = data.get("known_issues") or []
    for i, issue in enumerate(known_issues, start=1):
        if not all(str(issue.get(key, "")).strip() for key in ("id", "scope", "description")):
            fail(f"known_issues[{i}] requires id, scope and description")
        if issue.get("decision") != "deferred":
            fail(f"known_issues[{i}].decision must be 'deferred'")

    output = resolve(base, output_cfg.get("path", "output.mp4"))
    if output.exists() and not bool(output_cfg.get("overwrite", False)):
        fail(f"Output exists and overwrite is false: {output}")

    return {
        "performance": str(performance),
        "manifest_root": str(base),
        "cover": str(cover),
        "output": str(output),
        "duration": duration,
        "source_duration": source_duration,
        "fps": fps,
        "source_width": int(stream["width"]),
        "source_height": int(stream["height"]),
        "source_probe": probe,
        "pages": page_records,
        "cover_info": image_info(cover),
        "known_issues": known_issues,
    }


def cover_fill(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    image = image.convert("RGB")
    scale = max(size[0] / image.width, size[1] / image.height)
    resized = image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS)
    left = (resized.width - size[0]) // 2
    top = (resized.height - size[1]) // 2
    return resized.crop((left, top, left + size[0], top + size[1]))


def contain(image: Image.Image, size: tuple[int, int], color=(244, 246, 248)) -> tuple[Image.Image, tuple[int, int, int, int]]:
    image = image.convert("RGB")
    scale = min(size[0] / image.width, size[1] / image.height)
    resized = image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", size, color)
    x, y = (size[0] - resized.width) // 2, (size[1] - resized.height) // 2
    canvas.paste(resized, (x, y))
    return canvas, (x, y, resized.width, resized.height)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc" if bold else "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            pass
    return ImageFont.load_default()


def base_background(cover: Image.Image) -> Image.Image:
    bg = cover_fill(cover, CANVAS).filter(ImageFilter.GaussianBlur(36))
    bg = ImageEnhance.Color(bg).enhance(0.65)
    dark = Image.new("RGBA", CANVAS, (4, 13, 24, 164))
    return Image.alpha_composite(bg.convert("RGBA"), dark).convert("RGB")


def render_layouts(data: dict[str, Any], validated: dict[str, Any], build_dir: Path) -> tuple[list[Path], Path | None, dict[str, Any]]:
    layouts = build_dir / "layouts"
    layouts.mkdir(parents=True, exist_ok=True)
    cover = Image.open(validated["cover"])
    bg = base_background(cover)
    cover_tile = credit_cover(cover_fill(cover, (COVER_BOX[2], COVER_BOX[3])), data, validated["manifest_root"])
    song = str((data.get("project") or {}).get("song", "SKY PLAY ALONG"))
    title_font = font(28, bold=True)
    geometry: dict[str, Any] = {}
    results: list[Path] = []

    for record in validated["pages"]:
        page_no = record["page"]
        canvas = bg.copy()
        with Image.open(record["path"]) as source:
            source.load()
            page_tile, inner = contain(source, (SCORE_BOX[2], SCORE_BOX[3]))
        canvas.paste(page_tile, (SCORE_BOX[0], SCORE_BOX[1]))
        canvas.paste(cover_tile, (COVER_BOX[0], COVER_BOX[1]))
        draw = ImageDraw.Draw(canvas, "RGBA")
        draw.rectangle((12, 106, 1268, 974), outline=(216, 236, 255, 150), width=3)
        draw.rectangle((1333, 22, 1883, 572), outline=(216, 236, 255, 145), width=3)
        x, y, w, h = PERFORMANCE_BOX
        draw.rectangle((x, y, x + w, y + h), fill=(4, 13, 24, 105), outline=(216, 236, 255, 145), width=3)
        title = f"{song}  ·  PLAY ALONG"
        box = draw.textbbox((0, 0), title, font=title_font)
        tx = x + w / 2 - (box[2] - box[0]) / 2
        draw.text((tx + 2, 578), title, font=title_font, fill=(0, 0, 0, 150))
        draw.text((tx, 576), title, font=title_font, fill=(255, 255, 255, 235))
        output = layouts / f"layout_p{page_no:02d}.png"
        atomic_png(canvas, output)
        results.append(output)
        geometry[str(page_no)] = {
            "score_content": [SCORE_BOX[0] + inner[0], SCORE_BOX[1] + inner[1], inner[2], inner[3]],
        }

    end_path: Path | None = None
    start = (data.get("video") or {}).get("end_card_start")
    if start is not None:
        end = bg.copy()
        tile = credit_cover(cover_fill(cover, (720, 720)), data, validated["manifest_root"])
        end.paste(tile, (600, 70))
        draw = ImageDraw.Draw(end, "RGBA")
        draw.rectangle((586, 56, 1334, 804), outline=(216, 236, 255, 165), width=4)
        cfg = data.get("video") or {}
        lines = [
            (str(cfg.get("end_card_title", "收藏 · 下次直接跟弹")), 850, font(38, bold=True)),
            (str(cfg.get("end_card_subtitle", "关注我，继续更新新手友好谱")), 918, font(28)),
        ]
        for text, y, typeface in lines:
            box = draw.textbbox((0, 0), text, font=typeface)
            tx = (CANVAS[0] - (box[2] - box[0])) / 2
            draw.text((tx + 2, y + 2), text, font=typeface, fill=(0, 0, 0, 160))
            draw.text((tx, y), text, font=typeface, fill=(255, 255, 255, 240))
        end_path = layouts / "layout_end.png"
        atomic_png(end, end_path)
    cover.close()
    return results, end_path, geometry


def render_key_labels(data: dict[str, Any], validated: dict[str, Any], build_dir: Path) -> Path:
    width, height = validated["source_width"], validated["source_height"]
    centers = (data.get("performance") or {}).get("key_centers_normalized", DEFAULT_CENTERS)
    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    label_font = font(max(20, round(height * 25 / 512)), bold=True)
    for label, point in zip(KEY_LABELS, centers):
        x, y = float(point[0]) * width, float(point[1]) * height
        box = draw.textbbox((0, 0), label, font=label_font, stroke_width=2)
        tw, th = box[2] - box[0], box[3] - box[1]
        draw.text((x - tw / 2, y - th / 2 - box[1]), label, font=label_font,
                  fill=(255, 255, 255, 255), stroke_width=2, stroke_fill=(9, 14, 20, 235))
    path = build_dir / "key_labels.png"
    atomic_png(canvas, path)
    return path


def ffmpeg_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")


def build_filter(data: dict[str, Any], validated: dict[str, Any], layout_count: int, end_index: int | None) -> str:
    crop = [float(v) for v in (data.get("performance") or {}).get("crop_normalized", [0, 0, 1, 1])]
    sw, sh = validated["source_width"], validated["source_height"]
    cx, cy = round(crop[0] * sw), round(crop[1] * sh)
    cw, ch = max(2, round(crop[2] * sw)), max(2, round(crop[3] * sh))
    px, py, pw, ph = PERFORMANCE_BOX
    filters = [
        "[0:v]setpts=PTS-STARTPTS[perf0]",
        "[1:v]format=rgba,setpts=PTS-STARTPTS[labels]",
        "[perf0][labels]overlay=0:0[perf1]",
        f"[perf1]crop={cw}:{ch}:{cx}:{cy},scale={pw}:{ph}:force_original_aspect_ratio=increase,crop={pw}:{ph},setsar=1[perf]",
        f"[2:v]scale={CANVAS[0]}:{CANVAS[1]},setsar=1,setpts=PTS-STARTPTS[bg0]",
    ]
    current = "bg0"
    for idx, page in enumerate(validated["pages"][1:], start=3):
        next_name = f"bg{idx - 2}"
        start, end = page["start"], page["end"]
        filters.append(f"[{idx}:v]scale={CANVAS[0]}:{CANVAS[1]},setsar=1,setpts=PTS-STARTPTS[p{idx}]")
        filters.append(f"[{current}][p{idx}]overlay=0:0:enable='gte(t,{start:.6f})*lt(t,{end:.6f})'[{next_name}]")
        current = next_name

    for n, row in enumerate(data.get("row_timeline") or [], start=1):
        geometry = validated["geometry"][str(int(row["page"]))]["score_content"]
        gx, gy, gw, gh = geometry
        rh = gh / 3
        rx, ry = gx + 8, gy + (int(row["row"]) - 1) * rh + 6
        rw, box_h = gw - 16, rh - 12
        next_name = f"row{n}"
        filters.append(
            f"[{current}]drawbox=x={rx:.2f}:y={ry:.2f}:w={rw:.2f}:h={box_h:.2f}:"
            f"color=0x64c7ff@0.72:t=5:enable='gte(t,{float(row['start']):.6f})*lt(t,{float(row['end']):.6f})'[{next_name}]"
        )
        current = next_name

    hook = str((data.get("video") or {}).get("opening_hook", "")).strip()
    if hook:
        seconds = float((data.get("video") or {}).get("opening_hook_seconds", 3.0))
        safe = ffmpeg_escape(hook)
        next_name = "hooked"
        filters.append(
            f"[{current}]drawtext=text='{safe}':fontcolor=white:fontsize=36:fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
            f"x=(1260-text_w)/2:y=42:borderw=2:bordercolor=0x08111dcc:enable='lt(t,{seconds:.6f})'[{next_name}]"
        )
        current = next_name

    duration = validated["duration"]
    filters.append(f"[{current}]drawbox=x=0:y=1072:w='iw*min(t/{duration:.6f},1)':h=8:color=0x64c7ff@0.90:t=fill[progress]")
    filters.append(f"[progress][perf]overlay={px}:{py}:shortest=1[composed]")
    current = "composed"
    if end_index is not None:
        start = float((data.get("video") or {})["end_card_start"])
        filters.append(f"[{end_index}:v]scale={CANVAS[0]}:{CANVAS[1]},setsar=1,setpts=PTS-STARTPTS[end]")
        filters.append(f"[{current}][end]overlay=0:0:enable='gte(t,{start:.6f})'[ended]")
        current = "ended"
    filters.append(f"[{current}]format=yuv420p[outv]")
    return ";".join(filters)


def extract_frame(video: Path, time: float, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    run(["ffmpeg", "-y", "-v", "error", "-ss", f"{max(0, time):.6f}", "-i", str(video), "-frames:v", "1", str(output)])
    image_info(output)


def page_distance(frame: Path, layout: Path) -> float:
    x, y, w, h = SCORE_BOX
    with Image.open(frame) as observed, Image.open(layout) as expected:
        a = observed.convert("RGB").crop((x, y, x + w, y + h)).resize((310, 213), Image.Resampling.BILINEAR)
        b = expected.convert("RGB").crop((x, y, x + w, y + h)).resize((310, 213), Image.Resampling.BILINEAR)
        diff = ImageChops.difference(a, b)
        histogram = diff.histogram()
        pixels = a.width * a.height * 3
        return sum((value % 256) * count for value, count in enumerate(histogram)) / pixels


def full_frame_distance(frame: Path, expected: Path) -> float:
    with Image.open(frame) as observed, Image.open(expected) as target:
        a = observed.convert("RGB").resize((480, 270), Image.Resampling.BILINEAR)
        b = target.convert("RGB").resize((480, 270), Image.Resampling.BILINEAR)
        diff = ImageChops.difference(a, b)
        histogram = diff.histogram()
        pixels = a.width * a.height * 3
        return sum((value % 256) * count for value, count in enumerate(histogram)) / pixels


def contact_sheet(items: list[dict[str, Any]], output: Path) -> None:
    if not items:
        return
    thumb = (480, 270)
    cols = 2
    rows = math.ceil(len(items) / cols)
    canvas = Image.new("RGB", (thumb[0] * cols, (thumb[1] + 44) * rows), (18, 23, 30))
    draw = ImageDraw.Draw(canvas)
    label_font = font(22, bold=True)
    for index, item in enumerate(items):
        with Image.open(item["frame"]) as image:
            image.load()
            image = image.convert("RGB").resize(thumb, Image.Resampling.LANCZOS)
        x, y = (index % cols) * thumb[0], (index // cols) * (thumb[1] + 44)
        canvas.paste(image, (x, y))
        label = f"{item['time']:.2f}s  expected P{item['expected']}  observed P{item['observed']}"
        draw.text((x + 10, y + thumb[1] + 8), label, font=label_font, fill=(238, 245, 252))
    atomic_png(canvas, output)


def verify_output(data: dict[str, Any], validated: dict[str, Any], layouts: list[Path], end_card: Path | None, output: Path, build_dir: Path) -> dict[str, Any]:
    run(["ffmpeg", "-v", "error", "-xerror", "-i", str(output), "-f", "null", "-"])
    probe = ffprobe(output)
    out_duration = float(probe["format"]["duration"])
    if abs(out_duration - validated["duration"]) > max(0.10, 2 / validated["fps"]):
        fail(f"Output duration mismatch: expected {validated['duration']:.3f}, got {out_duration:.3f}")

    frame_dir = build_dir / "qc_frames"
    checks: list[dict[str, Any]] = []
    epsilon = max(0.12, 4 / validated["fps"])
    for page in validated["pages"][1:]:
        boundary = float(page["start"])
        for suffix, time, expected in (
            ("before", boundary - epsilon, page["page"] - 1),
            ("after", boundary + epsilon, page["page"]),
        ):
            frame = frame_dir / f"P{page['page']:02d}_{suffix}_{time:.3f}.png"
            extract_frame(output, time, frame)
            distances = [page_distance(frame, layout) for layout in layouts]
            observed = int(min(range(len(distances)), key=distances.__getitem__)) + 1
            record = {
                "boundary_to_page": page["page"], "position": suffix, "time": time,
                "expected": expected, "observed": observed, "matched": observed == expected,
                "distance_by_page": {str(i + 1): round(value, 4) for i, value in enumerate(distances)},
                "frame": str(frame),
            }
            checks.append(record)
            if observed != expected:
                fail(f"Boundary verification failed at {time:.3f}s: expected P{expected}, observed P{observed}")

    sheet = output.with_name(output.stem + "_contact_sheet.png")
    contact_sheet(checks, sheet)
    end_check = None
    if end_card is not None:
        start = float((data.get("video") or {})["end_card_start"])
        sample_time = min(validated["duration"] - epsilon, start + epsilon)
        frame = frame_dir / f"end_card_{sample_time:.3f}.png"
        extract_frame(output, sample_time, frame)
        distance = full_frame_distance(frame, end_card)
        end_check = {"time": sample_time, "distance": round(distance, 4), "matched": distance < 12.0, "frame": str(frame)}
        if not end_check["matched"]:
            fail(f"End-card verification failed at {sample_time:.3f}s (distance {distance:.2f})")
    return {
        "status": "passed_with_accepted_issues" if validated.get("known_issues") else "passed",
        "known_issues": validated.get("known_issues", []),
        "output": {"path": str(output), "probe": probe},
        "boundary_checks": checks,
        "end_card_check": end_check,
        "contact_sheet": str(sheet) if checks else None,
    }


def build(data: dict[str, Any], base: Path, validated: dict[str, Any]) -> dict[str, Any]:
    output = Path(validated["output"])
    output.parent.mkdir(parents=True, exist_ok=True)
    build_dir = output.parent / (output.stem + "_build")
    build_dir.mkdir(parents=True, exist_ok=True)
    layouts, end_card, geometry = render_layouts(data, validated, build_dir)
    validated["geometry"] = geometry
    labels = render_key_labels(data, validated, build_dir)

    command = ["ffmpeg", "-y", "-v", "error", "-i", validated["performance"]]
    command += ["-loop", "1", "-framerate", str(validated["fps"]), "-i", str(labels)]
    for layout in layouts:
        command += ["-loop", "1", "-framerate", str(validated["fps"]), "-i", str(layout)]
    end_index = None
    if end_card:
        end_index = 2 + len(layouts)
        command += ["-loop", "1", "-framerate", str(validated["fps"]), "-i", str(end_card)]

    temp = output.with_name(output.stem + ".rendering.mp4")
    filter_graph = build_filter(data, validated, len(layouts), end_index)
    command += [
        "-filter_complex", filter_graph, "-map", "[outv]", "-map", "0:a?",
        "-t", f"{validated['duration']:.6f}", "-r", str(validated["fps"]),
        "-c:v", "libx264", "-preset", str((data.get("video") or {}).get("encoder_preset", "medium")),
        "-crf", str((data.get("video") or {}).get("crf", 18)),
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(temp),
    ]
    run(command)
    report = verify_output(data, validated, layouts, end_card, temp, build_dir)
    os.replace(temp, output)
    if report.get("contact_sheet"):
        temporary_sheet = Path(report["contact_sheet"])
        final_sheet = output.with_name(output.stem + "_contact_sheet.png")
        if temporary_sheet != final_sheet:
            os.replace(temporary_sheet, final_sheet)
        report["contact_sheet"] = str(final_sheet)
    report["output"]["path"] = str(output)
    report_path = output.with_suffix(".qc.json")
    atomic_json(report, report_path)
    return {"output": str(output), "qc_report": str(report_path), "contact_sheet": report["contact_sheet"]}


def preview_manifest(data: dict[str, Any]) -> dict[str, Any]:
    preview = copy.deepcopy(data)
    video = preview.setdefault("video", {})
    requested = float(video.get("preview_seconds", 12.0))
    duration = min(requested, float(video.get("duration", requested)))
    if duration <= 0:
        fail("video.preview_seconds must be positive")
    video["duration"] = duration
    video["encoder_preset"] = video.get("preview_encoder_preset", "veryfast")
    video["crf"] = video.get("preview_crf", 23)
    video.pop("end_card_start", None)
    pages = []
    for page in preview["assets"]["pages"]:
        start = float(page["start"])
        if start >= duration:
            break
        item = dict(page)
        item["end"] = min(float(item["end"]), duration)
        pages.append(item)
    preview["assets"]["pages"] = pages
    preview["row_timeline"] = [
        {**row, "end": min(float(row["end"]), duration)}
        for row in preview.get("row_timeline", [])
        if float(row["start"]) < duration
    ]
    output = Path(preview.setdefault("output", {}).get("path", "output.mp4"))
    preview["output"]["path"] = str(output.with_name(output.stem + "_preview.mp4"))
    preview["output"]["overwrite"] = True
    return preview


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("validate", "preview", "build"))
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    try:
        data, base = load_manifest(args.manifest)
        if args.command == "preview":
            data = preview_manifest(data)
        validated = validate_manifest(data, base)
        if args.command == "validate":
            print(json.dumps({"status": "valid", **validated}, ensure_ascii=False, indent=2))
        else:
            print(json.dumps({"status": "built", **build(data, base, validated)}, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, KeyError, json.JSONDecodeError, subprocess.CalledProcessError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
