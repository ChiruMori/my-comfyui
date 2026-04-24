from pathlib import Path
from dotenv import load_dotenv
import os
import click
import logging

from src.config import Config, load_config
from src.manager.model import scan_model_files, find_unused_models, prompt_delete
from src.manager.workflow import (
    list_workflows,
    parse_models,
    export_workflows,
    import_workflows,
)
from src.mcp.server import start_mcp_server, get_workflows

# 加载 .env
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

# 配置日志
logging.basicConfig(level=logging.INFO)


@click.group()
@click.pass_context
def cli(ctx: click.Context) -> None:
    """ComfyUI 工作流、模型管理器，命令行界面主入口"""
    ctx.ensure_object(dict)
    ctx.obj["config"] = load_config()


@cli.group()
def workflow() -> None:
    """ComfyUI 工作流管理器"""


@workflow.command("list")
@click.option("--local", "-l", is_flag=True, help="列出本地工作流")
@click.pass_context
def workflow_list(ctx: click.Context, local: bool) -> None:
    """列出所有本地工作流"""
    config: Config = ctx.obj["config"]

    if local:
        workflows = list_workflows(config.local_workflows_dir)
        if workflows:
            click.echo(f"\n本地工作流 ({len(workflows)}):\n")
            for w in workflows:
                click.echo(f"  {w.name}")
        else:
            click.echo("本地没有工作流。")
    else:
        workflows = list_workflows(config.comfyui_workflows_dir)
        if workflows:
            click.echo(f"\nComfyUI 工作流 ({len(workflows)}):\n")
            for w in workflows:
                click.echo(f"  {w.name}")
        else:
            click.echo("ComfyUI 没有工作流。")


@workflow.command("export")
@click.option(
    "--dry-run", "-n", is_flag=True, help="仅显示将要导出的工作流，不实际复制"
)
@click.pass_context
def workflow_export(ctx: click.Context, dry_run: bool) -> None:
    """导出所有ComfyUI工作流到本地目录"""
    config: Config = ctx.obj["config"]

    workflows = list_workflows(config.comfyui_workflows_dir)
    if not workflows:
        click.echo("ComfyUI 没有工作流可导出。")
        return

    if dry_run:
        click.echo(f"\n将要导出的工作流 ({len(workflows)}):\n")
        for w in workflows:
            click.echo(f"  {w.name}")
    else:
        copied = export_workflows(
            config.comfyui_workflows_dir,
            config.local_workflows_dir,
            config.parsed_api_dir,
        )
        click.echo(f"\n已导出 {len(copied)} 个工作流到 {config.local_workflows_dir}")


@workflow.command("import")
@click.option(
    "--dry-run", "-n", is_flag=True, help="仅显示将要导入的工作流，不实际复制"
)
@click.pass_context
def workflow_import(ctx: click.Context, dry_run: bool) -> None:
    """从本地目录导入所有工作流到ComfyUI"""
    config: Config = ctx.obj["config"]

    workflows = list_workflows(config.local_workflows_dir)
    if not workflows:
        click.echo("本地没有工作流可导入。")
        return

    if dry_run:
        click.echo(f"\n将要导入的工作流 ({len(workflows)}):\n")
        for w in workflows:
            click.echo(f"  {w.name}")
    else:
        imported = import_workflows(
            config.local_workflows_dir, config.comfyui_workflows_dir
        )
        click.echo(
            f"\n已导入 {len(imported)} 个工作流到 {config.comfyui_workflows_dir}"
        )


@workflow.command("info")
@click.argument("name")
@click.pass_context
def workflow_info(ctx: click.Context, name: str) -> None:
    """显示指定工作流的详细信息"""
    config: Config = ctx.obj["config"]

    workflow_path = config.local_workflows_dir / (name + ".json")
    if not workflow_path.exists():
        click.echo(f"工作流不存在: {name}")
        return

    models = parse_models(workflow_path)
    click.echo(f"\n工作流: {name}\n")
    click.echo(f"引用的模型 ({len(models)}):")
    for m in models:
        click.echo(f"  - {m}")


@cli.group()
def model() -> None:
    """ComfyUI 模型管理器"""


@model.command("scan")
@click.option("--dry-run", "-n", is_flag=True, help="仅显示将要删除的模型，不实际删除")
@click.pass_context
def model_scan(ctx: click.Context, dry_run: bool) -> None:
    """扫描所有模型文件，查找未被引用的模型，并提示删除"""
    config: Config = ctx.obj["config"]

    # 扫描所有模型文件
    model_files = scan_model_files(config.comfyui_models_dir)
    if not model_files:
        click.echo("未发现模型文件。")
        return

    # 解析工作流中引用的模型
    referenced_models = set()
    for workflow_path in list_workflows(config.comfyui_workflows_dir):
        referenced_models.update(parse_models(workflow_path))
    click.echo(f"\n扫描到 {len(referenced_models)} 个可能的模型名称：")
    for m in sorted(referenced_models):
        click.echo(f"  - {m}")

    # 查找未使用的模型
    unused = find_unused_models(model_files, referenced_models)

    if not unused:
        click.echo("\n未发现可删除的模型文件。")
        return

    if dry_run:
        click.echo(f"\n发现 {len(unused)} 个未被引用的模型文件:\n")
        for path in sorted(unused):
            click.echo(f"  {path}")
        click.echo(f"\n总计 {len(model_files)} 个模型文件，{len(unused)} 个可删除。")
    else:
        click.echo(f"\n发现 {len(unused)} 个未被引用的模型文件:\n")
        for i, path in enumerate(sorted(unused), 1):
            click.echo(f"{i}. {path}")

        click.echo(f"\n总计 {len(model_files)} 个模型文件，{len(unused)} 个可删除。\n")

        if not click.confirm("是否删除这些文件?"):
            click.echo("取消删除操作。")
            return

        prompt_delete(unused)


@cli.command("server")
@click.option("--host", default="127.0.0.1", help="监听地址")
@click.option("--port", "-p", default=8181, type=int, help="监听端口")
@click.option(
    "--comfyui-url",
    default=None,
    help="ComfyUI API 地址（默认 http://localhost:8181）",
)
@click.pass_context
def server_command(_: click.Context, host: str, port: int, comfyui_url: str) -> None:
    """启动 ComfyUI 代理服务器"""
    if comfyui_url:
        os.environ["COMFYUI_URL"] = comfyui_url
    from src.server import app
    import uvicorn

    uvicorn.run(app, host=host, port=port)


@cli.command("mcp-server")
@click.option("--host", default="127.0.0.1", help="监听地址")
@click.option("--port", "-p", default=8181, type=int, help="监听端口")
@click.pass_context
def mcp_server_command(_: click.Context, host: str, port: int) -> None:
    """启动 MCP 服务器"""
    start_mcp_server(host, port)


def main():
    cli()


if __name__ == "__main__":
    main()
