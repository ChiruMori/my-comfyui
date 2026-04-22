import click

from pathlib import Path
from typing import List


# ComfyUI/models/ 下的子目录，用于扫描模型文件
MODEL_SUBDIRS = ["checkpoints", "loras", "vae", "unet", "clip", "controlnet"]

# 模型文件扩展名
MODEL_EXTENSIONS = {".safetensors", ".ckpt", ".pt", ".bin"}


def scan_model_files(models_dir: Path) -> List[Path]:
    """递归扫描 models_dir 下的所有模型文件

    Args:
        models_dir: ComfyUI/models/ 目录路径

    Returns:
        所有找到的模型文件路径列表
    """
    if not models_dir.exists():
        return []

    model_files: List[Path] = []
    for subdir in MODEL_SUBDIRS:
        subdir_path = models_dir / subdir
        if subdir_path.exists():
            for extension in MODEL_EXTENSIONS:
                model_files.extend(subdir_path.rglob(f"*{extension}"))

    return model_files


def find_unused_models(
    model_files: List[Path],
    referenced_models: set[str],
) -> List[Path]:
    """查找未被任何工作流引用的模型文件

    Args:
        model_files: 模型文件路径列表
        referenced_models: 已被工作流引用的模型文件名集合

    Returns:
        未被任何工作流引用的模型文件路径列表
    """
    unused: List[Path] = []

    for model_path in model_files:
        if model_path.name not in referenced_models:
            unused.append(model_path)

    return unused


def prompt_delete(unused: List[Path]) -> None:
    """用户删除未被任何工作流引用的模型文件，需逐个确认

    Args:
        unused: 未被任何工作流引用的模型文件路径列表
    """
    if not unused:
        click.echo("未发现可删除的模型文件。")
        return

    click.echo(f"\n共 {len(unused)} 个未被引用的模型文件:\n")
    for i, path in enumerate(unused, 1):
        click.echo(f"{i}. {path}")

    all_delete = click.confirm("全部删除?")
    deleted_count = 0

    for path in unused:
        try:
            if path.is_file() and (all_delete or click.confirm(f"是否删除 {path}?")):
                path.unlink()
                click.echo(f"已删除: {path}")
                deleted_count += 1
        except Exception as e:
            click.echo(f"删除失败 {path}: {e}")

    click.echo(f"\n共删除 {deleted_count} 个文件。")
