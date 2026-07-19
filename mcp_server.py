#!/usr/bin/env python3
"""Tiny MCP stdio server exposing one tool: data_quality_flag.

Exposes a Model Context Protocol server over stdio so the Agent Framework
MCPStdioTool can call it. Tool:
  data_quality_flag(values_json: str) -> str
      Given a JSON list of numbers, flags whether the series looks healthy
      (returns a one-line verdict). Demonstrates the framework's native MCP
      integration without any external service.

Run by the framework via: python3 mcp_server.py  (stdio transport)
"""
import json
import sys

# Minimal MCP stdio implementation (no external deps) so it runs in the lab venv.
# We speak the JSON-RPC 2.0 envelope MCP uses over stdio.

TOOLS = {
    "data_quality_flag": {
        "description": (
            "Flag data quality issues in a numeric series. Input: a JSON array of "
            "numbers, e.g. '[1,2,3]'. Returns a verdict string."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"values_json": {"type": "string"}},
            "required": ["values_json"],
        },
    }
}


def handle_request(req: dict) -> dict | None:
    method = req.get("method")
    rid = req.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": rid,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "tiny-mcp", "version": "1.0.0"},
            },
        }
    if method == "notifications/initialized":
        return None  # notification, no response
    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": rid,
            "result": {"tools": [{"name": k, "description": v["description"],
                                  "inputSchema": v["input_schema"]}
                                 for k, v in TOOLS.items()]},
        }
    if method == "tools/call":
        name = req["params"]["name"]
        args = req["params"].get("arguments", {})
        if name == "data_quality_flag":
            try:
                vals = json.loads(args.get("values_json", "[]"))
                nums = [float(x) for x in vals]
                if not nums:
                    verdict = "EMPTY: no values provided"
                elif any(v < 0 for v in nums):
                    verdict = "NEGATIVE: contains negative values"
                elif max(nums) - min(nums) == 0:
                    verdict = "FLAT: no variance"
                else:
                    verdict = f"OK: range {min(nums):.2f}..{max(nums):.2f}, mean {sum(nums)/len(nums):.2f}"
            except Exception as e:
                verdict = f"ERROR: {e}"
            return {
                "jsonrpc": "2.0",
                "id": rid,
                "result": {"content": [{"type": "text", "text": verdict}]},
            }
    return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": "method not found"}}


def main() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
        resp = handle_request(req)
        if resp is not None:
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
