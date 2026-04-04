from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import Tuple

from PIL import Image


class ImageCompressor:
    """压缩图片，尽量满足微信公众号图片约束。"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def compress_for_wechat_upload(
        self,
        image_bytes: bytes,
        filename: str = "image.jpg",
        max_size_kb: int = 2048,
        target_dimensions: Tuple[int, int] = (1600, 1600),
        quality: int = 88,
    ) -> tuple[bytes, str]:
        """压缩为适合微信永久素材上传的 JPEG。"""
        compressed = self.compress(
            image_bytes=image_bytes,
            max_size_kb=max_size_kb,
            target_dimensions=target_dimensions,
            quality=quality,
        )
        normalized_name = Path(filename).stem or "image"
        return compressed, f"{normalized_name}.jpg"

    def compress(
        self,
        image_bytes: bytes,
        max_size_kb: int = 64,
        target_dimensions: Tuple[int, int] = (900, 500),
        quality: int = 85,
    ) -> bytes:
        try:
            img = Image.open(io.BytesIO(image_bytes))
            if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                background = Image.new("RGB", img.size, (255, 255, 255))
                alpha = img.convert("RGBA")
                background.paste(alpha, mask=alpha.split()[-1])
                img = background
            elif img.mode != "RGB":
                img = img.convert("RGB")

            img.thumbnail(target_dimensions, Image.Resampling.LANCZOS)

            compressed = self._compress_with_quality_loop(
                img=img,
                max_size_kb=max_size_kb,
                start_quality=quality,
            )
            if compressed is not None:
                return compressed

            self.logger.warning("质量降低后仍超过%sKB，开始递进缩小尺寸", max_size_kb)

            current = img
            for scale_factor in (0.9, 0.8, 0.7, 0.6, 0.5):
                new_size = (
                    max(1, int(img.width * scale_factor)),
                    max(1, int(img.height * scale_factor)),
                )
                current = img.resize(new_size, Image.Resampling.LANCZOS)
                compressed = self._compress_with_quality_loop(
                    img=current,
                    max_size_kb=max_size_kb,
                    start_quality=min(75, quality),
                )
                if compressed is not None:
                    size_kb = len(compressed) / 1024
                    self.logger.info("图片压缩成功(缩小尺寸): %.1fKB (尺寸=%s)", size_kb, current.size)
                    return compressed

            final_bytes = self._save_jpeg(current, quality=35)
            final_size_kb = len(final_bytes) / 1024
            if final_size_kb > max_size_kb:
                raise ValueError(f"图片压缩后仍超过限制: {final_size_kb:.1f}KB > {max_size_kb}KB")

            self.logger.info("图片压缩成功(最终兜底): %.1fKB (尺寸=%s)", final_size_kb, current.size)
            return final_bytes
        except Exception as exc:  # noqa: BLE001
            self.logger.error("图片压缩失败: %s", exc)
            raise ValueError(f"图片压缩失败: {exc}") from exc

    def _save_jpeg(self, img: Image.Image, quality: int) -> bytes:
        output = io.BytesIO()
        img.save(output, format="JPEG", quality=quality, optimize=True)
        return output.getvalue()

    def _compress_with_quality_loop(self, img: Image.Image, max_size_kb: int, start_quality: int) -> bytes | None:
        current_quality = start_quality
        while current_quality >= 10:
            compressed = self._save_jpeg(img, quality=current_quality)
            size_kb = len(compressed) / 1024
            if size_kb <= max_size_kb:
                self.logger.info(
                    "图片压缩成功: %.1fKB (质量=%s, 尺寸=%s)",
                    size_kb,
                    current_quality,
                    img.size,
                )
                return compressed
            current_quality -= 5
        return None
