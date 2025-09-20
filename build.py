#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CC-APISwitch v1.0 构建脚本
"""

import os
from pathlib import Path


def build_main():
    """构建主版本"""
    print("开始构建 CC-APISwitch v1.0...")

    build_args = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--name=CC-APISwitch",
        "--distpath=dist",
        "--workpath=build",
        "--clean",
        "--optimize=2",
        "--strip",
        # 排除不必要的模块
        "--exclude-module=PIL",
        "--exclude-module=matplotlib",
        "--exclude-module=numpy",
        "--exclude-module=pandas",
        "--exclude-module=scipy",
        "--exclude-module=tkinter",
        "--exclude-module=PyQt5",
        "--exclude-module=PyQt6",
        "--exclude-module=test",
        "--exclude-module=unittest",
        "--exclude-module=pydoc",
        "--exclude-module=doctest",
        "--exclude-module=sqlite3",
        # 必要的隐藏导入
        "--hidden-import=wx._core",
        "--hidden-import=wx._adv",
        "--hidden-import=winreg",
        "--hidden-import=requests",
        "--hidden-import=threading",
        # 主文件
        "cc_switcher.py"
    ]

    print(f"构建命令: pyinstaller --onefile --windowed --name=CC-APISwitch ...")
    result = os.system(" ".join(build_args))

    if result == 0:
        print("\n[SUCCESS] CC-APISwitch v1.0 构建成功!")

        # 检查文件大小
        main_path = Path("dist/CC-APISwitch.exe")
        if main_path.exists():
            size_mb = main_path.stat().st_size / (1024 * 1024)
            print(f"文件大小: {size_mb:.1f} MB")
            print(f"输出位置: {main_path.absolute()}")

        print("\n[COMPLETE] 构建完成! 可执行文件已生成到 dist/ 目录")
        return True
    else:
        print("\n[FAILED] 构建失败!")
        return False


def clean_old_builds():
    """清理旧的构建文件"""
    import shutil

    old_dirs = [
        "build_simple", "build_enhanced", "build_lite", "build_ultra", "build_wx",
        "dist_simple", "dist_enhanced", "dist_lite", "dist_ultra", "dist_wx"
    ]

    cleaned = 0
    for dir_name in old_dirs:
        dir_path = Path(dir_name)
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"清理: {dir_name}")
            cleaned += 1

    if cleaned > 0:
        print(f"[CLEANED] 清理了 {cleaned} 个旧构建目录")
    else:
        print("没有需要清理的旧构建目录")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "clean":
        clean_old_builds()
    else:
        build_main()