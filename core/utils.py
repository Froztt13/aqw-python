import json

def checkOperator(obj1, obj2, operator: str):
    if operator == ">=":
        return obj1 >= obj2
    if operator == ">":
        return obj1 > obj2
    if operator == "<=":
        return obj1 <= obj2
    if operator == "<":
        return obj1 < obj2
    if operator == "==":
        return obj1 == obj2
    if operator == "!=":
        return obj1 != obj2
    raise ValueError(f"unsupported operator: {operator!r}")

def normalize(text: str):
    return text.lower().strip().replace("`", "'").replace("❜", "'").replace("’", "'")

def is_valid_json(s):
    try:
        json.loads(s)
        return True
    except json.JSONDecodeError:
        return False