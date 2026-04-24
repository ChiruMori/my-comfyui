"""ComfyUI API 客户端- 处理与 ComfyUI 服务器的通信"""

import os
from typing import Dict, Any, List
from httpx import AsyncClient, HTTPError
import traceback

COMFYUI_URL = os.getenv("COMFYUI_URL", "http://localhost:8181")


async def submit_task(prompt: Dict[str, Any]) -> Dict[str, Any]:
    """提交任务到 ComfyUI
    Args:
        prompt: 工作流提示
    Returns:
        包含任务 ID 的响应
    Raises:
        HTTPError: 无法连接到 ComfyUI 服务器
        ValueError: 请求格式错误
    """
    url = f"{COMFYUI_URL}/prompt"
    try:
        async with AsyncClient() as client:
            response = await client.post(url, json={"prompt": prompt}, timeout=30.0)
            response.raise_for_status()
            return response.json()
    except HTTPError as e:
        raise HTTPError(f"无法连接到 ComfyUI 服务器: {COMFYUI_URL}")
    except Exception as e:
        traceback.print_exc()
        raise ValueError(f"提交任务失败: {e}")


def build_outputs_info(
    job_response: Dict[str, Any], add_download_url: bool = False
) -> Dict[str, Any]:
    """获取任务的输出信息（如果已完成，则提取物料列表）
    Args:
        prompt_id: 任务 ID
    Returns:
        包含任务状态和物料列表的字典
    """
    status = job_response.get("status", "unknown")
    output_list = []
    outputs_count = 0
    if status == "completed":
        outputs = job_response.get("outputs", [])
        outputs_count = job_response.get("outputs_count", 0)
        for o in outputs.values():
            for ftype, flist in o.items():
                for f in flist:
                    now_out = {"type": ftype, "res": f}
                    if (
                        add_download_url
                        and type(f) == dict
                        and "filename" in f
                        and "type" in f
                        and "subfolder" in f
                    ):
                        now_out["res"]["download_url"] = build_output_download_link(
                            f["filename"], f["type"], f["subfolder"]
                        )
                    output_list.append(now_out)
    return {"status": status, "output": output_list, "outputs_count": outputs_count}


async def get_progress(
    prompt_id: str, add_download_url: bool = False
) -> Dict[str, Any]:
    """查询任务进度
    Args:
        prompt_id: 任务 ID
    Returns:
        包含任务状态和输出的字典
    Raises:
        HTTPError: 无法连接到 ComfyUI 服务器
        ValueError: 请求格式错误或任务不存在
    """
    url = f"{COMFYUI_URL}/api/jobs/{prompt_id}"
    try:
        async with AsyncClient() as client:
            response = await client.get(url, timeout=30.0)
            response.raise_for_status()
            job_response = response.json()
            return build_outputs_info(job_response, add_download_url)
    except HTTPError as e:
        raise HTTPError(f"无法连接到 ComfyUI 服务器: {COMFYUI_URL}")
    except Exception as e:
        traceback.print_exc()
        raise ValueError(f"查询任务进度失败: {e}")


def build_output_download_link(
    filename: str, type: str = "output", subfolder: str = ""
) -> str:
    """构建输出文件的下载链接
    Args:
        output_info: 输出信息字典
    Returns:
        该文件的下载链接
    """
    return (
        f"{COMFYUI_URL}/api/view?filename={filename}&type={type}&subfolder={subfolder}"
    )
