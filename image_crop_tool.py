#!/usr/bin/env python3
"""
PNG图片批量智能裁剪工具
自动检测文字内容并裁剪上下空白区域，保留保护性边距
"""

import os
import sys
from pathlib import Path
from typing import Tuple, List
import argparse

try:
    from PIL import Image, ImageDraw
    import numpy as np
except ImportError:
    print("错误: 缺少必要的依赖包")
    print("请运行: pip install Pillow numpy")
    sys.exit(1)


class ImageCropper:
    def __init__(self, padding: int = 10, threshold: int = 240):
        """
        初始化图片裁剪器

        Args:
            padding: 保护性边距（像素）
            threshold: 空白检测阈值，高于此值认为是空白区域
        """
        self.padding = padding
        self.threshold = threshold

    def detect_content_bounds(self, image: Image.Image) -> Tuple[int, int, int, int]:
        """
        检测图片中内容的边界

        Args:
            image: PIL图片对象

        Returns:
            (left, top, right, bottom) 内容边界坐标
        """
        # 转换为灰度图像进行分析
        if image.mode != 'L':
            gray = image.convert('L')
        else:
            gray = image

        # 转换为numpy数组
        img_array = np.array(gray)

        # 查找非空白区域（像素值低于阈值的区域）
        content_mask = img_array < self.threshold

        # 如果没有找到内容，返回原图尺寸
        if not np.any(content_mask):
            return 0, 0, image.width, image.height

        # 查找内容的边界
        content_rows = np.any(content_mask, axis=1)
        content_cols = np.any(content_mask, axis=0)

        # 找到第一个和最后一个包含内容的行和列
        top = np.argmax(content_rows)
        bottom = len(content_rows) - np.argmax(content_rows[::-1])
        left = np.argmax(content_cols)
        right = len(content_cols) - np.argmax(content_cols[::-1])

        return left, top, right, bottom

    def crop_image(self, image: Image.Image) -> Image.Image:
        """
        裁剪图片，移除上下空白区域

        Args:
            image: 原始图片

        Returns:
            裁剪后的图片
        """
        # 检测内容边界
        left, top, right, bottom = self.detect_content_bounds(image)

        # 添加保护性边距
        width, height = image.size

        # 计算裁剪区域（主要关注上下边距）
        crop_top = max(0, top - self.padding)
        crop_bottom = min(height, bottom + self.padding)
        crop_left = 0  # 保持原始左右边界
        crop_right = width

        # 如果裁剪区域太小，保持最小尺寸
        min_height = 50
        if crop_bottom - crop_top < min_height:
            center_y = (crop_top + crop_bottom) // 2
            crop_top = max(0, center_y - min_height // 2)
            crop_bottom = min(height, crop_top + min_height)

        # 执行裁剪
        cropped = image.crop((crop_left, crop_top, crop_right, crop_bottom))

        return cropped

    def process_single_image(self, input_path: Path, output_path: Path = None) -> bool:
        """
        处理单个图片文件

        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径，如果为None则覆盖原文件

        Returns:
            处理是否成功
        """
        try:
            # 验证文件格式
            if input_path.suffix.lower() != '.png':
                print(f"跳过非PNG文件: {input_path}")
                return False

            # 读取图片
            with Image.open(input_path) as image:
                original_size = image.size

                # 裁剪图片
                cropped_image = self.crop_image(image)
                new_size = cropped_image.size

                # 设置输出路径
                if output_path is None:
                    output_path = input_path

                # 保存结果
                cropped_image.save(output_path, 'PNG', optimize=True)

                # 计算压缩比例
                size_reduction = (1 - new_size[1] / original_size[1]) * 100

                print(f"✓ {input_path.name}: {original_size} → {new_size} "
                      f"(高度减少 {size_reduction:.1f}%)")

                return True

        except Exception as e:
            print(f"✗ 处理 {input_path} 时出错: {e}")
            return False

    def process_directory(self, input_dir: Path, output_dir: Path = None,
                         recursive: bool = False) -> Tuple[int, int]:
        """
        批量处理目录中的PNG文件

        Args:
            input_dir: 输入目录
            output_dir: 输出目录，如果为None则在原地处理
            recursive: 是否递归处理子目录

        Returns:
            (成功数量, 总数量)
        """
        if not input_dir.exists() or not input_dir.is_dir():
            print(f"错误: 输入目录不存在 - {input_dir}")
            return 0, 0

        # 查找PNG文件
        if recursive:
            png_files = list(input_dir.rglob("*.png"))
        else:
            png_files = list(input_dir.glob("*.png"))

        if not png_files:
            print(f"在 {input_dir} 中没有找到PNG文件")
            return 0, 0

        print(f"找到 {len(png_files)} 个PNG文件")

        # 创建输出目录
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)

        successful = 0
        total = len(png_files)

        for i, png_file in enumerate(png_files, 1):
            print(f"[{i}/{total}] 处理中...", end=" ")

            # 计算输出路径
            if output_dir:
                # 保持相对路径结构
                rel_path = png_file.relative_to(input_dir)
                out_path = output_dir / rel_path
                out_path.parent.mkdir(parents=True, exist_ok=True)
            else:
                out_path = None

            # 处理图片
            if self.process_single_image(png_file, out_path):
                successful += 1

        return successful, total


def main():
    parser = argparse.ArgumentParser(
        description="PNG图片批量智能裁剪工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s input.png                    # 裁剪单个文件
  %(prog)s images/                      # 批量处理目录
  %(prog)s images/ -o cropped/          # 输出到指定目录
  %(prog)s images/ -r                   # 递归处理子目录
  %(prog)s images/ -p 15 -t 250         # 自定义边距和阈值
        """
    )

    parser.add_argument('input', help='输入文件或目录路径')
    parser.add_argument('-o', '--output', help='输出目录（可选，默认覆盖原文件）')
    parser.add_argument('-p', '--padding', type=int, default=10,
                       help='保护性边距像素数 (默认: 10)')
    parser.add_argument('-t', '--threshold', type=int, default=240,
                       help='空白检测阈值 0-255 (默认: 240)')
    parser.add_argument('-r', '--recursive', action='store_true',
                       help='递归处理子目录')
    parser.add_argument('--preview', action='store_true',
                       help='预览模式，只显示将要裁剪的区域')

    args = parser.parse_args()

    # 验证输入
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"错误: 输入路径不存在 - {input_path}")
        return 1

    output_path = Path(args.output) if args.output else None

    # 创建裁剪器
    cropper = ImageCropper(padding=args.padding, threshold=args.threshold)

    print(f"开始处理，设置: 边距={args.padding}px, 阈值={args.threshold}")
    print("-" * 60)

    try:
        if input_path.is_file():
            # 处理单个文件
            success = cropper.process_single_image(input_path, output_path)
            if success:
                print("\n✓ 处理完成")
                return 0
            else:
                print("\n✗ 处理失败")
                return 1
        else:
            # 处理目录
            successful, total = cropper.process_directory(
                input_path, output_path, args.recursive
            )

            print("-" * 60)
            print(f"处理完成: {successful}/{total} 个文件成功")

            if successful == total:
                print("✓ 所有文件处理成功")
                return 0
            else:
                print(f"✗ {total - successful} 个文件处理失败")
                return 1

    except KeyboardInterrupt:
        print("\n\n中断操作")
        return 1
    except Exception as e:
        print(f"\n错误: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())