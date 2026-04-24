import os
import traceback
import json

from pydantic import Field

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from httpx import AsyncClient, HTTPStatusError
from pydantic import BaseModel
from src.comfyui.client import submit_task, get_progress, build_output_download_link

from src.comfyui.converter import prepare_api_workflow

COMFYUI_URL = os.getenv("COMFYUI_URL", "http://localhost:8181")

app = FastAPI(title="ComfyUI Proxy Server")


class TaskSubmitRequest(BaseModel):
    """提交任务请求模型"""

    workflow: str = Field(default="", description="工作流名称")
    kwargs: dict = Field(default={}, description="替换占位符的参数字典")


@app.post("/submit")
async def submit(req: TaskSubmitRequest):
    """提交任务：将工作流转换后转发到 ComfyUI /prompt 接口。"""
    # 根据 workflow 名找获取 api 格式
    api_wf = prepare_api_workflow(req.workflow, req.kwargs)
    return await submit_task(json.loads(api_wf))


@app.get("/progress/{prompt_id}")
async def query_progress(prompt_id: str):
    """查询任务进度，不包含原始下载链接，避免暴露 ComfyUI 链接。"""
    return await get_progress(prompt_id, add_download_url=False)


@app.get("/download")
async def download_file(filename: str, type: str = "output", subfolder: str = ""):
    """下载生成的物料文件，直接透传，因为启动了Web服务转发，可以避免暴露 ComfyUI 链接。"""
    try:
        download_link = build_output_download_link(filename, type, subfolder)
        resp = await AsyncClient().get(download_link)
        resp.raise_for_status()
        content_disposition = resp.headers.get("content-disposition")
        extra_headers = {}
        if content_disposition:
            extra_headers["Content-Disposition"] = content_disposition
        return Response(
            content=resp.content,
            media_type=resp.headers.get("content-type", "application/octet-stream"),
            headers=extra_headers,
        )
    except HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
