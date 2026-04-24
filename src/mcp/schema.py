"""Schema 定义和解析器"""

from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import yaml
import logging

logger = logging.getLogger(__name__)


class WorkflowSchema(BaseModel):
    """工作流 Schema 定义"""

    name: str
    description: str
    arg_schema: Dict[str, Any]


class SchemaLoader:
    """Schema 文件加载器"""

    @staticmethod
    def find_schema_files(dir_path: Path) -> List[Path]:
        """查找目录下所有 schema 文件"""
        if not dir_path.exists():
            return []
        return list(dir_path.glob("*.yml")) + list(dir_path.glob("*.yaml"))

    @staticmethod
    def load_schema_file(file_path: Path) -> WorkflowSchema:
        """加载单个 schema 文件"""
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return WorkflowSchema(**data)

    @staticmethod
    def load_all_schemas(dir_path: Path) -> List[WorkflowSchema]:
        """加载目录下所有 schema 文件"""
        schemas = []
        for file_path in SchemaLoader.find_schema_files(dir_path):
            schema = SchemaLoader.load_schema_file(file_path)
            schemas.append(schema)
        logger.info(f"成功加载 {len(schemas)} 个 schema 文件")
        return schemas

    @staticmethod
    def get_schema_by_name(dir_path: Path, name: str) -> Optional[WorkflowSchema]:
        """根据名称获取 schema"""
        schemas = SchemaLoader.load_all_schemas(dir_path)
        for schema in schemas:
            if schema.name == name:
                return schema
        return None
