def oid(val):
    from bson.objectid import ObjectId
    if val is None:
        return None
    try:
        return ObjectId(val) if isinstance(val, str) else val
    except Exception:
        return None


def error_context(e=None):
    import inspect
    import os
    import traceback

    frame = inspect.currentframe()
    func_name = frame.f_back.f_code.co_name if frame and frame.f_back else 'unknown'
    script = os.path.basename(frame.f_back.f_code.co_filename) if frame and frame.f_back else 'unknown'
    line_no = frame.f_back.f_lineno if frame and frame.f_back else 'unknown'
    desc = str(e) if e else 'Unknown error'

    if e and getattr(e, '__traceback__', None):
        trace_lines = traceback.extract_tb(e.__traceback__)
        if trace_lines:
            last = trace_lines[-1]
            script = os.path.basename(last.filename)
            func_name = last.name
            line_no = last.lineno

    return f"[SCRIPT: {script} | FUNCTION: {func_name} | LINE: {line_no}] {desc}"


def paginate(page, per_page):
    try:
        page = max(int(page), 1)
    except (ValueError, TypeError):
        page = 1
    try:
        per_page = min(max(int(per_page), 1), 100)
    except (ValueError, TypeError):
        per_page = 20
    return page, per_page
