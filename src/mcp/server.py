from fastmcp import FastMCP
from typing import Dict, Any, List
from pathlib import Path

import json
import os

from src.comfyui.client import (
    submit_task as comfyui_submit_task,
    get_progress as comfyui_query_task,
)
from src.comfyui.converter import prepare_api_workflow
from .schema import WorkflowSchema, SchemaLoader


mcp = FastMCP("ComfyUI MCP Server")
mcp_schema_dir = os.getenv("MCP_SCHEMA_DIR", "workflow/mcp")


@mcp.tool
def get_workflows() -> List[WorkflowSchema]:
    """获取所有可用的工作流信息，包括工作流名称、描述、参数 Schema

    Returns:
        所有可用的工作流信息列表，每个元素为一个 `WorkflowSchema` 对象
        每个对象包含工作流名称、描述、参数 Schema
    """
    return SchemaLoader.load_all_schemas(Path(mcp_schema_dir))


@mcp.tool
async def submit_task(workflow: str, kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """提交任务到 ComfyUI

    Args:
        workflow: 工作流名称，可以通过 `get_workflows` 查看所有可用的工作流信息
        kwargs: 任务参数，使用一个对象来表示，其中的键必须在工作流的 Schema 中有定义
    Returns:
        包含 `prompt_id` 字段的响应对象，`prompt_id` 是 ComfyUI 中任务的唯一标识符（UUID 形式）可以用于后续查询任务状态和结果
    """
    useable_workflows = get_workflows()
    target_workflow = next((w for w in useable_workflows if w.name == workflow), None)
    if not target_workflow:
        return {
            "error": "工作流不存在，请通过 get_workflows 查看所有可用的工作流信息后重试"
        }
    api_wf = prepare_api_workflow(workflow, kwargs)
    return await comfyui_submit_task(json.loads(api_wf))


@mcp.tool
async def query_task(prompt_id: str) -> Dict[str, Any]:
    """查询任务进度

    Args:
        prompt_id: 任务 ID，通过 `submit_task` 提交任务时返回的 `prompt_id` 字段
    Returns:
        包含任务状态和输出的字典，结构如下（注意，res 的格式根据 type 不同而不同）：
        {
            "status": "in_progress" | "completed" | "failed" | "unknown",
            "output": [
                {
                    "type": "images" | "text" | ...,
                    "res": {
                        "filename": "xxx.png",
                        "subfolder": "yyy",
                        "type": "output",
                        "download_url": "http://xxx.com/xxx.png"
                    }
                },
            ...]
        }
    """
    return await comfyui_query_task(prompt_id, add_download_url=True)


def start_mcp_server(host: str, port: int):
    mcp.run(
        transport="http",
        host=host,
        port=port,
    )
