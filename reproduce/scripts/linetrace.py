"""Line-by-line tracer used by the stage 5 step scripts.

trace(functions, describe) returns a function for sys.settrace. While a watched function runs, every
executed line is printed with its line number, and after it every local variable that line created or
changed (compared by identity, and for lists and dicts also by length). Functions called from a watched
function are not traced unless they are watched too.
"""
import linecache

def default_describe(v):
    if isinstance(v, (str, int, float, bool, type(None))):
        r = repr(v); return r if len(r) <= 100 else r[:97] + "..."
    if isinstance(v, (list, tuple)):
        inner = ", ".join(default_describe(x) for x in v[:3])
        return f"{type(v).__name__} of {len(v)}: [{inner}{', ...' if len(v) > 3 else ''}]"
    if isinstance(v, dict):
        return f"dict with keys {list(v)[:6]}"
    return type(v).__name__

def _sig(v):
    return (id(v), len(v)) if isinstance(v, (list, dict, set)) else id(v)

def trace(functions, describe=default_describe, skip=("self",)):
    watch = {f.__code__: f.__qualname__ for f in functions}
    def tracer(frame, event, arg):
        if frame.f_code not in watch: return None
        name = watch[frame.f_code]; seen = {}
        def show_changes(frame):
            for k, v in frame.f_locals.items():
                if k in skip: continue
                if seen.get(k) != _sig(v):
                    seen[k] = _sig(v); print(f"{'':14}{k} = {describe(v)}")
        def local(frame, event, arg):
            if event in ("line", "return"): show_changes(frame)
            if event == "line":
                src = linecache.getline(frame.f_code.co_filename, frame.f_lineno).rstrip()
                print(f"    line {frame.f_lineno:<5}{src}")
            elif event == "return":
                print(f"  <<< {name} RETURNS {describe(arg)}\n")
            return local
        print(f"\n  >>> ENTER {name}   ({frame.f_code.co_filename.split('unified_kg_rag/')[-1]})")
        show_changes(frame)
        return local
    return tracer
