from typing import Any, Dict
import datetime
import ast
import operator as op

# Safe math eval (no names, no calls)
_ALLOWED_OPS = {
    ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul, ast.Div: op.truediv,
    ast.Pow: op.pow, ast.USub: op.neg, ast.Mod: op.mod, ast.FloorDiv: op.floordiv
}

def _eval(node):
    if isinstance(node, ast.Num):
        return node.n
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPS:
        return _ALLOWED_OPS[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPS:
        return _ALLOWED_OPS[type(node.op)](_eval(node.operand))
    raise ValueError("Unsupported expression")

def run_tool(tool_id: str, args: Dict[str, Any]) -> Dict[str, Any]:
    if tool_id == "echo":
        return {"text": args["text"]}
    if tool_id == "time_now":
        return {"utc": datetime.datetime.utcnow().isoformat() + "Z"}
    if tool_id == "math_eval":
        expr = args["expression"]
        tree = ast.parse(expr, mode="eval").body
        val = _eval(tree)
        return {"value": val}
    raise ValueError(f"Unknown tool_id: {tool_id}")
