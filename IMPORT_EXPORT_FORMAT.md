 # Agent Import/Export File Format

 This document describes the JSON and YAML file format used by DB-ADK to export and import agent definitions, tools, and relationships.

 ## Supported Formats
 - **JSON** (`.json`)
 - **YAML** (`.yaml`, `.yml`)

 The format is determined by file extension or can be explicitly specified when using CLI/API. During import, the format is also auto-detected by inspecting file content.

 ## Schema Version
 - **schema_version** (string, required): Version of the export schema. Current value: `"1.0"`.

 ## Top-Level Fields
 | Field             | Type             | Required | Description                                           |
 |-------------------|------------------|----------|-------------------------------------------------------|
 | `schema_version`  | string           | yes      | Export schema version.                                |
 | `export_date`     | string (ISO8601) | no       | UTC timestamp when the export was generated.          |
 | `agent`           | object           | yes      | Agent metadata (see below).                           |
 | `tools`           | array of object  | no       | List of tool definitions attached to the agent.       |
 | `relationships`   | array of object  | no       | List of child-agent relationships (if any).           |

 ### `agent` Object
 Object containing the core agent definition.
 | Field             | Type             | Required | Description                                       |
 |-------------------|------------------|----------|---------------------------------------------------|
 | `name`            | string           | yes      | Unique name of the agent.                         |
 | `description`     | string or null   | no       | Human-readable description.                       |
 | `agent_type`      | string           | yes      | Type of agent (e.g., `"LLM"`).                   |
 | `prompt_template` | string or null   | no       | Prompt template for the agent.                    |
 | `model_name`      | string or null   | no       | Name of the LLM model used by the agent.          |
 | `configuration`   | object           | no       | Arbitrary configuration parameters (key/value).   |

 ### `tools` Array
 Each entry defines a tool available to the agent.
 | Field               | Type          | Required | Description                                           |
 |---------------------|---------------|----------|-------------------------------------------------------|
 | `name`              | string        | yes      | Unique tool name.                                     |
 | `description`       | string or null| no       | Human-readable description of the tool.               |
 | `tool_type`         | string        | yes      | Tool type (e.g., `"python_function"`).              |
 | `module_path`       | string        | yes      | Python module path containing the tool function.      |
 | `function_name`     | string        | yes      | Name of the function to invoke.                       |
 | `parameters_schema` | object        | no       | JSON Schema describing the tool's input parameters.   |

 ### `relationships` Array
 Each entry defines a relationship from this agent (parent) to a child agent.
 | Field               | Type    | Required | Description                                         |
 |---------------------|---------|----------|-----------------------------------------------------|
 | `child_agent_name`  | string  | yes      | Name of the child agent.                            |
 | `relationship_type` | string  | yes      | Type of relationship (custom-defined).              |
 | `execution_order`   | integer | no       | Order in which the child agent should execute (0+). |

 ## Examples
 ### JSON Example
 ```json
 {
   "schema_version": "1.0",
   "export_date": "2025-04-25T12:00:00Z",
   "agent": {
     "name": "weather_assistant",
     "description": "Provides weather information",
     "agent_type": "LLM",
     "prompt_template": "You are a weather assistant that provides weather information.",
     "model_name": "gemini-1.5-pro",
     "configuration": {}
   },
   "tools": [
     {
       "name": "get_weather",
       "description": "Get weather information for a location",
       "tool_type": "python_function",
       "module_path": "my_tools.weather",
       "function_name": "get_weather",
       "parameters_schema": {
         "type": "object",
         "properties": {
           "location": { "type": "string" }
         },
         "required": ["location"]
       }
     }
   ],
   "relationships": [
     {
       "child_agent_name": "itinerary_planner",
       "relationship_type": "helper",
       "execution_order": 0
     }
   ]
 }
 ```

 ### YAML Example
 ```yaml
 schema_version: "1.0"
 export_date: "2025-04-25T12:00:00Z"
 agent:
   name: weather_assistant
   description: Provides weather information
   agent_type: LLM
   prompt_template: >-
     You are a weather assistant that provides weather information.
   model_name: gemini-1.5-pro
   configuration: {}
 tools:
   - name: get_weather
     description: Get weather information for a location
     tool_type: python_function
     module_path: my_tools.weather
     function_name: get_weather
     parameters_schema:
       type: object
       properties:
         location:
           type: string
       required:
         - location
 relationships:
   - child_agent_name: itinerary_planner
     relationship_type: helper
     execution_order: 0
 ```

 ## Import/Export Behavior
 - **Export**: Uses `get_serializer` to select JSON or YAML serializer. Writes data from database (agent, tools, relationships).
 - **Import**: Auto-detects format with `detect_format`, deserializes, validates against `AGENT_SCHEMA`, and creates/updates database records.

 For more details, see `db_adk/import_export/exporters.py` and `db_adk/import_export/importers.py`.