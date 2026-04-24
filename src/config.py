import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv


@dataclass
class Config:
    """配置类，用于存储 ComfyUI 和本地工作流目录的路径。"""

    comfyui_base_dir: Path
    comfyui_workflows_dir: Path
    comfyui_models_dir: Path
    local_workflows_dir: Path
    parsed_api_dir: Path

    def __init__(
        self,
        comfyui_base_dir: Path,
        comfyui_workflows_dir: Path,
        comfyui_models_dir: Path,
        local_workflows_dir: Path,
        parsed_api_dir: Path,
    ):
        self.comfyui_base_dir = Path(comfyui_base_dir).expanduser().resolve()
        self.comfyui_workflows_dir = Path(comfyui_workflows_dir).expanduser().resolve()
        self.comfyui_models_dir = Path(comfyui_models_dir).expanduser().resolve()
        self.local_workflows_dir = Path(local_workflows_dir).expanduser().resolve()
        self.parsed_api_dir = Path(parsed_api_dir).expanduser().resolve()


def load_config(env_file: Path | str | None = None) -> Config:
    """从 .env 文件加载配置。

    Args:
        env_file: .env 文件路径，默认为项目根目录下的 .env。

    Returns:
        配置实例，包含所有路径。

    Raises:
        FileNotFoundError: .env 文件未找到。
        ValueError: 必填环境变量未设置。
    """
    if load_dotenv is None:
        raise RuntimeError("请安装 python-dotenv: pip install python-dotenv")

    # 查找 .env 文件
    if env_file is not None:
        env_path = Path(env_file)
    else:
        env_path = get_env_path(Path(".env"))

    # 加载 .env 文件
    load_dotenv(env_path)

    # 获取 ComfyUI 基础目录（必填）
    comfyui_base = os.getenv("COMFYUI_BASE_DIR", "")
    if not comfyui_base:
        raise ValueError(f"COMFYUI_BASE_DIR 未设置，请在 {env_path} 中设置。")
    comfyui_base = Path(comfyui_base).expanduser().resolve()
    if not comfyui_base.exists():
        raise FileNotFoundError(
            f"COMFYUI_BASE_DIR 目录不存在: {comfyui_base}"
        )

    # 从 base_dir 推导子目录
    comfyui_workflows = (
        Path(
            os.getenv(
                "COMFYUI_WORKFLOWS_DIR",
                str(comfyui_base / "user" / "default" / "workflows"),
            )
        )
        .expanduser()
        .resolve()
    )
    comfyui_models = (
        Path(os.getenv("COMFYUI_MODELS_DIR", str(comfyui_base / "models")))
        .expanduser()
        .resolve()
    )

    # 获取本地工作流备份目录
    local_workflows = (
        Path(os.getenv("LOCAL_WORKFLOWS_DIR", "workflow")).expanduser().resolve()
    )

    # 获取解析后的 API 调用目录
    parsed_api_dir = (
        Path(os.getenv("PARSED_API_DIR", "parsed_api")).expanduser().resolve()
    )

    return Config(
        comfyui_base_dir=comfyui_base,
        comfyui_workflows_dir=comfyui_workflows,
        comfyui_models_dir=comfyui_models,
        local_workflows_dir=local_workflows,
        parsed_api_dir=parsed_api_dir,
    )


def get_env_path(path: Path | None = None) -> Path:
    """查找 .env 文件路径。

    Args:
        path: .env 文件路径。

    Returns:
        .env 文件路径。

    Raises:
        FileNotFoundError: .env 文件未找到。
    """
    if path is None:
        path = Path(".env")

    # 检查当前目录
    current = Path.cwd() / path
    if current.exists():
        return current

    # 检查 home 目录
    home = Path.home() / path
    if home.exists():
        return home

    raise FileNotFoundError(f".env 文件未找到于 {path}")
