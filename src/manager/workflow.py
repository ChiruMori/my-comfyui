import json
import shutil
import re
from pathlib import Path
from typing import Any, Dict, List
from src.api.converter import convert_workflow_to_api


def list_workflows(workflows_dir: Path) -> List[Path]:
    """列出指定目录下的所有工作流 JSON文件

    Args:
        workflows_dir: 工作流 JSON文件目录路径

    Returns:
        工作流 JSON文件路径列表
    """
    if not workflows_dir.exists():
        return []

    return [
        p
        for p in workflows_dir.rglob("*.json")
        if not p.is_dir() and not p.name.startswith(".")
    ]


MODEL_NAME_EXTENSIONS = (".safetensors", ".ckpt", ".pt", ".bin", ".vae")
MODEL_NAME_EXCLUDE = {
    "",
    "auto",
    "bf\\d+",
    "\\d+",
    "None",
    "HuggingFace",
    "default",
}  # 排除一些常见的无效模型名称


def parse_models(workflow_path: Path) -> List[str]:
    """解析工作流 JSON文件，提取引用的模型文件名

    Args:
        workflow_path: 工作流 JSON文件路径

    Returns:
        模型文件名列表（例如，"xxx.safetensors"）。
    """
    if not workflow_path.exists():
        return []

    try:
        with open(workflow_path, "r", encoding="utf-8") as f:
            workflow: Dict[str, Any] = json.load(f)
    except (json.JSONDecodeError, IOError):
        return []

    def _is_model_name(name: str) -> bool:
        """判断字符串是否为模型文件名

        Args:
            name: 字符串

        Returns:
            是否为模型文件名，判断方式：
            1. 字符串以 ".safetensors"、".ckpt"、".pt" 或 ".bin" 结尾的肯定是模型文件名
            2. 在排除列表里的模式匹配到的字符串肯定不是模型文件名
            3. 其他情况，均视为模型文件名，后续筛选将根据实际路径是否存在进行判断
        """
        if not isinstance(name, str):
            return False

        name = name.strip()
        for exclude in MODEL_NAME_EXCLUDE:
            if re.fullmatch(exclude, name, re.IGNORECASE):
                return False

        # 检查是否以模型扩展名结尾（可跳过）
        # for ext in MODEL_NAME_EXTENSIONS:
        #     if name.endswith(ext):
        #         return True

        return True

    def _extract_models(node: Any) -> List[str]:
        widgets_values = []
        if isinstance(node, dict):
            if "nodes" in node and isinstance(node["nodes"], list):
                # 识别模型名称的方法：
                # 关注 nodes 节点列表中，type 包含 "Loader" 的节点
                # 从 widgets_values 中提取模型文件名，过滤掉无效项
                for n in node["nodes"]:
                    if "Loader" not in n.get("type", ""):
                        continue
                    candidate_widgets = n.get("widgets_values", None)
                    if candidate_widgets is not None and isinstance(
                        candidate_widgets, list
                    ):
                        widgets_values.extend(candidate_widgets)

        return [w for w in widgets_values if isinstance(w, str) and _is_model_name(w)]

    models = _extract_models(workflow)
    return list(set(models))


def export_workflows(src_dir: Path, dest_dir: Path, parsed_api_dir: Path) -> List[str]:
    """将指定目录下的所有ComfyUI工作流 JSON文件复制到本地目录，同时转换为 API 调用的所需格式

    Args:
        src_dir: 源目录路径（ComfyUI 工作流目录）
        dest_dir: 目标目录路径（本地工作流目录）
        parsed_api_dir: 解析后的 API 调用目录路径（本地工作流目录）

    Returns:
        复制的文件名列表
    """
    if not src_dir.exists():
        return []

    dest_dir.mkdir(parents=True, exist_ok=True)
    parsed_api_dir.mkdir(parents=True, exist_ok=True)
    copied: List[str] = []

    for workflow_path in list_workflows(src_dir):
        # 复制工作流 JSON文件到本地目录
        dest_path = dest_dir / workflow_path.name
        shutil.copy2(workflow_path, dest_path)
        copied.append(workflow_path.name)
        # 解析工作流 JSON 文件，保存到 API 调用目录下
        api_path = parsed_api_dir / workflow_path.name
        with open(api_path, "w", encoding="utf-8") as f:
            # 读取工作流 JSON 文件内容，解析为 API 调用格式后保存
            with open(workflow_path, "r", encoding="utf-8") as wf:
                workflow = json.load(wf)
                prompt = convert_workflow_to_api(workflow)
                f.write(json.dumps(prompt, ensure_ascii=False, indent=2))

    return copied


def import_workflows(src_dir: Path, dest_dir: Path) -> List[str]:
    """将本地目录下的所有工作流 JSON文件导入到 ComfyUI 目录

    Args:
        src_dir: 源目录路径（本地工作流目录）
        dest_dir: 目标目录路径（ComfyUI 工作流目录）

    Returns:
        导入的文件名列表
    """
    if not src_dir.exists():
        return []

    dest_dir.mkdir(parents=True, exist_ok=True)
    imported: List[str] = []

    for workflow_path in list_workflows(src_dir):
        dest_path = dest_dir / workflow_path.name
        shutil.copy2(workflow_path, dest_path)
        imported.append(workflow_path.name)

    return imported
