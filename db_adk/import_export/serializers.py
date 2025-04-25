"""
Serializers for converting agent data to and from JSON and YAML formats.
"""

import enum
import json
from pathlib import Path
from typing import Any, Dict, Optional, Type, Union, cast

import yaml


class SerializerFormat(str, enum.Enum):
    """Supported serialization formats."""

    JSON = "json"
    YAML = "yaml"


class AgentSerializer:
    """Base serializer class for agent import/export."""

    FORMAT: Optional[SerializerFormat] = None

    @classmethod
    def serialize(cls, data: Dict[str, Any]) -> str:
        """
        Serialize agent data to string.

        Args:
            data: Agent data dictionary

        Returns:
            String representation in the target format
        """
        raise NotImplementedError("Subclasses must implement this method")

    @classmethod
    def deserialize(cls, content: str) -> Dict[str, Any]:
        """
        Deserialize string content to agent data.

        Args:
            content: String in the target format

        Returns:
            Agent data dictionary
        """
        raise NotImplementedError("Subclasses must implement this method")

    @classmethod
    def serialize_to_file(
        cls, data: Dict[str, Any], file_path: Union[str, Path]
    ) -> None:
        """
        Serialize agent data and write to file.

        Args:
            data: Agent data dictionary
            file_path: Path to output file
        """
        content = cls.serialize(data)
        with open(file_path, "w") as f:
            f.write(content)

    @classmethod
    def deserialize_from_file(cls, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Read file and deserialize to agent data.

        Args:
            file_path: Path to input file

        Returns:
            Agent data dictionary
        """
        with open(file_path, "r") as f:
            content = f.read()
        return cls.deserialize(content)


class JSONAgentSerializer(AgentSerializer):
    """JSON serializer for agent import/export."""

    FORMAT: SerializerFormat = SerializerFormat.JSON

    @classmethod
    def serialize(cls, data: Dict[str, Any]) -> str:
        """Serialize agent data to JSON string."""
        return json.dumps(data, indent=2)

    @classmethod
    def deserialize(cls, content: str) -> Dict[str, Any]:
        """Deserialize JSON string to agent data."""
        return cast(Dict[str, Any], json.loads(content))


class YAMLAgentSerializer(AgentSerializer):
    """YAML serializer for agent import/export."""

    FORMAT: SerializerFormat = SerializerFormat.YAML

    @classmethod
    def serialize(cls, data: Dict[str, Any]) -> str:
        """Serialize agent data to YAML string."""
        return yaml.dump(data, sort_keys=False, default_flow_style=False)

    @classmethod
    def deserialize(cls, content: str) -> Dict[str, Any]:
        """Deserialize YAML string to agent data."""
        return cast(Dict[str, Any], yaml.safe_load(content))


def get_serializer(
    format_name: Optional[str] = None, file_path: Optional[Union[str, Path]] = None
) -> Type[AgentSerializer]:
    """
    Get the appropriate serializer based on format name or file extension.

    Args:
        format_name: Format name ('json' or 'yaml')
        file_path: File path to determine format from extension

    Returns:
        Serializer class

    Raises:
        ValueError: If format cannot be determined or is unsupported
    """
    if format_name:
        # Get by explicit format name
        format_name = format_name.lower()
        if format_name == SerializerFormat.JSON:
            return JSONAgentSerializer
        elif format_name == SerializerFormat.YAML:
            return YAMLAgentSerializer

    if file_path:
        # Get by file extension
        path = Path(file_path)
        extension = path.suffix.lower()

        if extension in (".json"):
            return JSONAgentSerializer
        elif extension in (".yaml", ".yml"):
            return YAMLAgentSerializer

    # Default to JSON if no information provided
    if not format_name and not file_path:
        return JSONAgentSerializer

    raise ValueError(f"Unsupported or undetermined format: {format_name or file_path}")


def detect_format(content: str) -> Type[AgentSerializer]:
    """
    Detect format based on content.

    Args:
        content: String content to analyze

    Returns:
        Serializer class

    Raises:
        ValueError: If format cannot be determined
    """
    # Try to parse as JSON first (more strict)
    try:
        json.loads(content)
        return JSONAgentSerializer
    except json.JSONDecodeError:
        # Try YAML next (more permissive)
        try:
            yaml.safe_load(content)
            return YAMLAgentSerializer
        except yaml.YAMLError:
            raise ValueError(
                "Unable to determine format. Content is neither valid JSON nor YAML."
            )
