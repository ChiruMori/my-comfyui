import os
import traceback
import json

from pathlib import Path
from pydantic import Field

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from httpx import AsyncClient, HTTPStatusError
from pydantic import BaseModel

from src.api.converter import convert_workflow_to_api, prepare_api_workflow

# 加载 .env
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

COMFYUI_URL = os.getenv("COMFYUI_URL", "http://localhost:8181")

app = FastAPI(title="ComfyUI Proxy Server")


class TaskSubmitRequest(BaseModel):
    """提交任务请求模型"""

    workflow: str = Field(default="", description="工作流名称")
    kwargs: dict = Field(default={}, description="替换占位符的参数字典")


@app.post("/submit")
async def submit_task(req: TaskSubmitRequest):
    """提交任务：将工作流转换后转发到 ComfyUI /prompt 接口。"""
    try:
        # 根据 workflow 名找获取 api 格式
        api_wf = prepare_api_workflow(req.workflow, req.kwargs)
        async with AsyncClient() as client:
            resp = await client.post(
                f"{COMFYUI_URL}/prompt", json={"prompt": json.loads(api_wf)}
            )
            resp.raise_for_status()
            return resp.json()
    except HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/progress/{prompt_id}")
async def get_progress(prompt_id: str):
    """查询任务进度。"""
    try:
        async with AsyncClient() as client:
            resp = await client.get(f"{COMFYUI_URL}/api/jobs/{prompt_id}")
            resp.raise_for_status()
            raw_data = resp.json()
            # 提取任务状态，如果已完成，则提取物料列表
            status = raw_data["status"]
            output_list = []
            outputs_count = 0
            if status == "completed":
                outputs = raw_data.get("outputs", [])
                outputs_count = raw_data.get("outputs_count", 0)
                for o in outputs.values():
                    for ftype, flist in o.items():
                        for f in flist:
                            output_list.append({"type": ftype, "res": f})
            return {
                "status": status,
                "output": output_list,
                "outputs_count": outputs_count,
            }
    except HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/download")
async def download_file(filename: str, type: str = "output", subfolder: str = ""):
    """下载生成的物料文件。"""
    try:
        async with AsyncClient() as client:
            resp = await client.get(
                f"{COMFYUI_URL}/api/view",
                params={"filename": filename, "type": type, "subfolder": subfolder},
            )
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
