#!/usr/bin/env python3
"""
环境初始化脚本
"""

import argparse
import os
import subprocess
import sys


def run_command(cmd: str) -> None:
    """
    运行命令并检查结果

    Args:
        cmd: 命令字符串
    """
    try:
        print(f"执行命令: {cmd}")
        subprocess.run(cmd, check=True, shell=True)
        print("✅ 命令执行成功")
    except subprocess.CalledProcessError as e:
        print(f"❌ 命令执行失败: {e}")
        sys.exit(1)


def main() -> None:
    """主函数"""
    parser = argparse.ArgumentParser(
        description="AI实习求职Agent系统环境初始化脚本"
    )
    parser.add_argument(
        "--no-deps", action="store_true", help="不安装依赖包"
    )
    parser.add_argument(
        "--no-db", action="store_true", help="不初始化数据库"
    )

    args = parser.parse_args()

    print("🚀 开始初始化AI实习求职Agent系统环境...")

    # 检查Python版本
    if sys.version_info < (3, 10):
        print("❌ 错误: 需要Python 3.10或更高版本")
        sys.exit(1)

    # 检查pip
    if not args.no_deps:
        print("\n📦 安装Python依赖包...")
        run_command("pip install -r requirements.txt")

    # 检查.env文件
    if not os.path.exists(".env"):
        print("\n🔧 创建环境变量文件...")
        if os.path.exists(".env.example"):
            run_command("cp .env.example .env")
            print("提示: 请编辑 .env 文件并填入必要的配置")

    # 检查数据库连接
    if not args.no_db:
        print("\n💾 检查数据库连接...")
        # 这里可以添加数据库连接检查逻辑
        pass

    # 创建必要的目录
    print("\n📁 创建必要的目录...")
    for dir_path in [
        "data/raw/resumes",
        "data/processed/job_listings",
        "data/vectors",
        "logs",
    ]:
        os.makedirs(dir_path, exist_ok=True)
        print(f"✅ 创建目录: {dir_path}")

    print("\n🎉 环境初始化完成!")
    print("\n下一步操作:")
    print("1. 编辑 .env 文件，填入数据库配置和API密钥")
    print("2. 运行 `python scripts/migrate.py` 初始化数据库")
    print("3. 运行 `python src/main.py` 启动服务")


if __name__ == "__main__":
    main()
