"""
Schema validation utilities for DB-ADK.
"""

import jsonschema
from jsonschema import ValidationError

from .logging import get_logger

# Initialize logger
logger = get_logger(__name__)


def validate_tool_parameters_schema(schema):
    """Validate that a tool parameters schema is valid JSON Schema.

    Args:
        schema (dict): The parameters schema to validate.

    Returns:
        bool: True if the schema is valid.

    Raises:
        ValueError: If the schema is invalid.
    """
    try:
        # Basic JSON Schema meta-schema validation
        jsonschema.validate(schema, jsonschema.Draft7Validator.META_SCHEMA)

        # Additional validation specific to ADK tool parameters
        required_properties = ["type", "properties"]
        for prop in required_properties:
            if prop not in schema:
                raise ValueError(
                    f"Tool parameters schema missing required property: {prop}"
                )

        logger.info("Tool parameters schema is valid")
        return True
    except ValidationError as e:
        logger.error(f"Invalid tool parameters schema: {str(e)}")
        raise ValueError(f"Invalid tool parameters schema: {str(e)}")
    except Exception as e:
        logger.error(f"Error validating tool parameters schema: {str(e)}")
        raise ValueError(f"Error validating tool parameters schema: {str(e)}")


def validate_agent_config(config):
    """Validate agent configuration.

    Args:
        config (dict): The agent configuration to validate.

    Returns:
        bool: True if the configuration is valid.

    Raises:
        ValueError: If the configuration is invalid.
    """
    # Required fields for all agent types
    required_fields = ["name", "description", "agent_type"]

    for field in required_fields:
        if field not in config:
            raise ValueError(f"Agent configuration missing required field: {field}")

    # Validate agent type
    # Note: 'Coordinator' type is supported for backward compatibility,
    # but actually uses LlmAgent with sub_agents under the hood
    valid_agent_types = ["LLM", "Coordinator", "Sequential", "Parallel"]
    if config["agent_type"] not in valid_agent_types:
        raise ValueError(
            f"Invalid agent type: {config['agent_type']}. "
            f"Must be one of: {', '.join(valid_agent_types)}"
        )

    # LLM agent specific validation
    if config["agent_type"] == "LLM":
        if "prompt_template" not in config:
            raise ValueError(
                "LLM agent configuration missing required field: prompt_template"
            )

    # Coordinator agent specific validation
    if config["agent_type"] == "Coordinator":
        if "prompt_template" not in config:
            raise ValueError(
                "Coordinator agent configuration missing required field: prompt_template"
            )

    logger.info("Agent configuration is valid")
    return True
