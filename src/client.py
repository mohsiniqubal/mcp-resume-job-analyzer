import asyncio
import json
import os
import sys
from pathlib import Path

from mcp import Client, StdioServerParameters


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ============================================================
# PYTHON EXECUTABLE
# ============================================================
#
# Use the current Python interpreter.
#
# This works for:
# - Windows virtual environment
# - Linux
# - Docker
# - CI/CD
#
# ============================================================

PYTHON_EXECUTABLE = sys.executable


# ============================================================
# MCP SERVER PARAMETERS
# ============================================================

def create_server_parameters():

    return StdioServerParameters(
        command=PYTHON_EXECUTABLE,
        args=[
            "-m",
            "src.server",
        ],
        cwd=str(PROJECT_ROOT),
        env=os.environ.copy(),
    )


# ============================================================
# MCP CLIENT
# ============================================================

class MCPClient:

    def __init__(self):

        self.server_parameters = (
            create_server_parameters()
        )

        self.client = None
        self._context_manager = None


    async def __aenter__(self):

        self._context_manager = Client(
            self.server_parameters
        )

        self.client = await (
            self._context_manager.__aenter__()
        )

        return self


    async def __aexit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ):

        return await (
            self._context_manager.__aexit__(
                exc_type,
                exc_value,
                traceback,
            )
        )


    async def list_tools(self):

        if self.client is None:

            raise RuntimeError(
                "MCP client is not connected."
            )

        return await self.client.list_tools()


    async def call_tool(
        self,
        tool_name: str,
        arguments: dict,
    ):

        if self.client is None:

            raise RuntimeError(
                "MCP client is not connected."
            )

        return await self.client.call_tool(
            tool_name,
            arguments=arguments,
        )


# ============================================================
# PARSE MCP JSON
# ============================================================

def parse_mcp_json(result):

    if result.is_error:

        raise RuntimeError(
            "MCP tool returned an error."
        )

    if not result.content:

        raise RuntimeError(
            "MCP tool returned no content."
        )

    response_text = (
        result.content[0].text
    )

    try:

        return json.loads(
            response_text
        )

    except json.JSONDecodeError as error:

        raise RuntimeError(
            f"Invalid JSON returned by MCP tool: {error}"
        )