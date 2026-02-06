from __future__ import annotations

import os
from uuid import uuid4
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

from PIL import Image, ImageDraw, ImageFont

from .custom_logger import get_logger

try:
    RESAMPLE = Image.Resampling.LANCZOS
except AttributeError:  # pragma: no cover - Pillow < 10
    RESAMPLE = Image.LANCZOS

TARGET_WIDTH = 1024
TARGET_HEIGHT = 1280
TEXT_MARGIN = 50
FIELD_SECTION_MAX_HEIGHT = 180
BOTTOM_SECTION_MAX_HEIGHT = 420
DEFAULT_FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FIELD_FONT_MAX = 48
BOTTOM_FONT_MAX = 60
MIN_FONT_SIZE = 24
PRIMARY_TEXT_COLOR = "#f58009"
STROKE_WIDTH = 0
TEXT_BACKGROUND_PADDING = 12
TEXT_BACKGROUND_OPACITY = int(255 * 0.7)
TEXT_BACKGROUND_COLOR = (255, 255, 255, TEXT_BACKGROUND_OPACITY)
QUOTE_BACKGROUND_COLOR = "black"
QUOTE_TEXT_COLOR = "white"
QUOTE_TEXT_MARGIN = 80
QUOTE_FONT_MAX = 64
TAGLINE_TEXT = "@motivation_nitrous"
TAGLINE_FONT_MAX = 32
TAGLINE_SECTION_HEIGHT = 140


class BaseImageCreator:
    """Prepare base portrait images using the supplied sketches and metadata."""

    def __init__(
        self,
        env_path: str | Path = ".env",
        output_folder: str | Path | None = None,
        sketch_folder: str | Path | None = None,
    ) -> None:
        self.env_path = Path(env_path).resolve()
        self.logger = get_logger("instagram_post_creator.create_images")
        self._env_values = _load_env_file(self.env_path)
        output_value = (
            str(output_folder)
            if output_folder is not None
            else self._env_values.get("OUTPUT_FOLDER")
            or self._env_values.get("OUTPUT_FILES_LOCATION")
            or os.getenv("OUTPUT_FOLDER")
            or os.getenv("OUTPUT_FILES_LOCATION")
        )
        self.output_folder = self._resolve_folder(output_value, "OUTPUT_FOLDER")

        sketch_value = (
            str(sketch_folder)
            if sketch_folder is not None
            else self._env_values.get("SKETCH_IMAGES_FOLDER") or os.getenv("SKETCH_IMAGES_FOLDER")
        )
        self.sketch_folder = self._resolve_optional_folder(sketch_value)

    def create_base_image(self, code: str, name: str, excellence_field: str, dob: str, country: str) -> Path:
        """Overlay the name, country, and DOB on top of the supplied sketch."""
        if not self.sketch_folder:
            raise ValueError("SKETCH_IMAGES_FOLDER is missing; cannot create base image.")

        sketch_path = self.sketch_folder / f"{code}.png"
        if not sketch_path.exists():
            raise FileNotFoundError(f"Sketch not found for code {code} at {sketch_path}")

        output_path = self.sketch_folder / f"{code}_base.png"

        base_image = Image.open(sketch_path).convert("RGB")
        canvas = base_image.resize((TARGET_WIDTH, TARGET_HEIGHT), RESAMPLE).convert("RGBA")
        draw = ImageDraw.Draw(canvas, "RGBA")

        max_width = TARGET_WIDTH - TEXT_MARGIN * 2

        field_lines, field_font = _fit_text(
            draw,
            excellence_field.strip() or "Area of excellence",
            max_width,
            FIELD_SECTION_MAX_HEIGHT,
            FIELD_FONT_MAX,
        )

        dob_text = _format_dob_line(dob)
        bottom_segments: List[str] = [name.strip() or "Unknown"]
        if country.strip():
            bottom_segments.append(country.strip())
        if dob_text:
            bottom_segments.append(dob_text)

        bottom_text = "\n".join(bottom_segments)
        bottom_lines, bottom_font = _fit_text(
            draw,
            bottom_text,
            max_width,
            BOTTOM_SECTION_MAX_HEIGHT,
            BOTTOM_FONT_MAX,
        )

        field_start_y = TEXT_MARGIN
        _draw_text_block(draw, field_lines, field_font, start_y=field_start_y, align="left")

        bottom_block_height = _text_block_height(bottom_font, len(bottom_lines))
        bottom_start_y = TARGET_HEIGHT - TEXT_MARGIN - bottom_block_height
        _draw_text_block(draw, bottom_lines, bottom_font, start_y=bottom_start_y, align="center")

        canvas.convert("RGB").save(output_path)
        self.logger.info("Base image created for %s at %s", name, output_path)
        return output_path

    def create_quotes_images(self, code: str, name: str, quotes: str) -> List[Path]:
        """Create quote images for the provided code and quotes payload."""
        snippets = [part.strip() for part in quotes.split("|")] if isinstance(quotes, str) else []
        snippets = [text for text in snippets if text]

        if not snippets:
            raise ValueError("No quotes provided to generate quote images.")

        created_paths: List[Path] = []
        for index, quote_text in enumerate(snippets, start=1):
            output_path = _create_quote_image(code, name, quote_text, self.output_folder, index)
            created_paths.append(output_path)
            self.logger.info("Quote image created at %s", output_path)

        return created_paths

    def _resolve_folder(self, folder_value: str | None, env_key: str) -> Path:
        if not folder_value:
            raise ValueError(f"{env_key} is missing from the environment file.")

        folder_path = Path(os.path.expandvars(folder_value)).expanduser()
        if not folder_path.is_absolute():
            folder_path = (self.env_path.parent / folder_path).resolve()

        folder_path.mkdir(parents=True, exist_ok=True)
        return folder_path

    def _resolve_optional_folder(self, folder_value: str | None) -> Path | None:
        if not folder_value:
            return None
        return self._resolve_folder(folder_value, "SKETCH_IMAGES_FOLDER")


def _load_env_file(env_path: Path) -> dict[str, str]:
    if not env_path.exists():
        raise FileNotFoundError(f"Unable to locate environment file at {env_path}")

    env_values: dict[str, str] = {}
    with env_path.open(encoding="utf-8") as env_file:
        for line in env_file:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            key, _, value = line.partition("=")
            env_values[key.strip()] = value.strip().strip('"').strip("'")
    return env_values


def _create_quote_image(code: str, name: str, quote_text: str, output_folder: Path, index: int) -> Path:
    image = Image.new("RGB", (TARGET_WIDTH, TARGET_HEIGHT), QUOTE_BACKGROUND_COLOR)
    draw = ImageDraw.Draw(image)

    max_width = TARGET_WIDTH - QUOTE_TEXT_MARGIN * 2
    name_lines, name_font = _fit_text(
        draw,
        name.strip() or "Unknown",
        max_width,
        120,
        TAGLINE_FONT_MAX,
    )

    name_height_total = _text_block_height(name_font, len(name_lines))
    name_start_y = QUOTE_TEXT_MARGIN
    _draw_text_block(
        draw,
        name_lines,
        name_font,
        start_y=name_start_y,
        align="center",
        fill_color=QUOTE_TEXT_COLOR,
        background=False,
    )

    quote_top = name_start_y + name_height_total + 20
    quote_area_height = TARGET_HEIGHT - quote_top - TAGLINE_SECTION_HEIGHT - QUOTE_TEXT_MARGIN

    quote_lines, quote_font = _fit_text(
        draw,
        quote_text,
        max_width,
        quote_area_height,
        QUOTE_FONT_MAX,
    )

    quote_block_height = _text_block_height(quote_font, len(quote_lines))
    quote_start_y = quote_top + max((quote_area_height - quote_block_height) // 2, 0)
    _draw_text_block(
        draw,
        quote_lines,
        quote_font,
        start_y=quote_start_y,
        align="center",
        fill_color=QUOTE_TEXT_COLOR,
        background=False,
    )

    tagline_lines, tagline_font = _fit_text(
        draw,
        TAGLINE_TEXT,
        max_width,
        TAGLINE_SECTION_HEIGHT,
        TAGLINE_FONT_MAX,
    )
    tagline_block_height = _text_block_height(tagline_font, len(tagline_lines))
    tagline_start_y = TARGET_HEIGHT - QUOTE_TEXT_MARGIN - tagline_block_height
    _draw_text_block(
        draw,
        tagline_lines,
        tagline_font,
        start_y=tagline_start_y,
        align="center",
        fill_color=QUOTE_TEXT_COLOR,
        background=False,
    )

    output_name = f"{uuid4()}.jpg"
    output_path = output_folder / output_name
    image.save(output_path, format="JPEG")
    return output_path


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype(DEFAULT_FONT_PATH, size)
    except OSError:
        return ImageFont.load_default()


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    paragraphs = text.splitlines() or [text]
    lines: list[str] = []

    for paragraph in paragraphs:
        words = paragraph.split()
        if not words:
            lines.append("")
            continue

        current_line: list[str] = []
        for word in words:
            test_line = " ".join(current_line + [word]) if current_line else word
            if draw.textlength(test_line, font=font) <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                    current_line = [word]
                else:
                    lines.append(test_line)
        if current_line:
            lines.append(" ".join(current_line))

    return lines or ["N/A"]


def _fit_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    max_width: int,
    max_height: int,
    initial_size: int,
    min_size: int = MIN_FONT_SIZE,
) -> Tuple[list[str], ImageFont.ImageFont]:
    sanitized_text = text.strip() or "N/A"
    font_size = initial_size

    while font_size >= min_size:
        font = _load_font(font_size)
        wrapped = _wrap_text(draw, sanitized_text, font, max_width)
        block_height = _text_block_height(font, len(wrapped))
        if block_height <= max_height:
            return wrapped, font
        font_size -= 2

    fallback_font = _load_font(min_size)
    return _wrap_text(draw, sanitized_text, fallback_font, max_width), fallback_font


def _text_block_height(font: ImageFont.ImageFont, line_count: int) -> int:
    ascent, descent = font.getmetrics()
    line_height = ascent + descent + 6
    return line_count * line_height


def _draw_text_block(
    draw: ImageDraw.ImageDraw,
    lines: list[str],
    font: ImageFont.ImageFont,
    start_y: int,
    align: str = "center",
    fill_color: str | None = None,
    background: bool = True,
) -> None:
    line_height = _text_block_height(font, 1)
    for line in lines:
        line_width = draw.textlength(line, font=font)
        if align == "left":
            x_position = TEXT_MARGIN
        else:
            x_position = (TARGET_WIDTH - line_width) // 2

        if background and TEXT_BACKGROUND_OPACITY > 0:
            _draw_text_background(draw, x_position, start_y, line_width, line_height)
        draw.text(
            (x_position, start_y),
            line,
            font=font,
            fill=fill_color or PRIMARY_TEXT_COLOR,
            stroke_width=STROKE_WIDTH,
        )
        start_y += line_height


def _draw_text_background(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    width: float,
    height: int,
) -> None:
    if TEXT_BACKGROUND_OPACITY <= 0:
        return

    left = max(x - TEXT_BACKGROUND_PADDING, 0)
    top = max(y - TEXT_BACKGROUND_PADDING, 0)
    right = min(x + width + TEXT_BACKGROUND_PADDING, TARGET_WIDTH)
    bottom = min(y + height + TEXT_BACKGROUND_PADDING, TARGET_HEIGHT)

    draw.rectangle((left, top, right, bottom), fill=TEXT_BACKGROUND_COLOR)


def _format_dob_line(dob: str) -> str:
    dob = dob.strip()
    if not dob:
        return ""

    normalized = _format_dob(dob)
    return f"Born on {normalized}"


def _format_dob(dob_value: str) -> str:
    for fmt in ("%Y-%m-%d", "%m-%d-%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            parsed = datetime.strptime(dob_value, fmt)
        except ValueError:
            continue
        return parsed.strftime("%m-%d-%Y")

    return dob_value


"""if __name__ == "__main__":
    
    
    bic = BaseImageCreator()

    bic.create_quotes_images( code="Jan_1_1", quotes="Count us, because we count too. | Children with disabilities are not problems to solve. | Your homeland is not a hotel you can check out of. | I am not a number... I am a human. | We can’t wait any longer.")"""
