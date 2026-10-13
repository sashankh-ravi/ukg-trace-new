"""Convert one saved page of the chat history (as returned by the chat-history read tool) into transcript markdown.

Usage: python transcript_from_history.py <saved page file> [name to redact ...]   (markdown goes to stdout)
Each extra argument is a name replaced with "[other repository]" in the output.

Mechanical rules, nothing else is changed:
- HTML entities are decoded.
- Each tool call block becomes one line: `[tool: Name] <its description, or the file it touched>`.
- A dated system note in a person's turn becomes a date line; any other system note is dropped and marked.
- Names of the person's unrelated private repositories are replaced with [other repository].
"""
import html, re, sys

REDACT = sys.argv[2:]
PREFIXES = ["/home/claude/awslabs/unified-kg-rag-on-aws/", "/tmp/claude-0/-home-claude/bc133111-51e4-5491-aaed-c6588835038c/scratchpad/",
            "/tmp/claude-0/-home-claude-ukg-trace-new/bc133111-51e4-5491-aaed-c6588835038c/scratchpad/"]
NAMES = {"mcp__Claude_Docs__batch": "Claude Docs batch", "mcp__Claude_Docs__update": "Claude Docs update",
         "mcp__Claude_Docs__create": "Claude Docs create", "mcp__Claude_Docs__guide": "Claude Docs guide",
         "mcp__Claude_Docs__export": "Claude Docs export", "mcp__Claude_Docs__read": "Claude Docs read",
         "mcp__claude-code-remote__add_repo": "add_repo", "mcp__claude-code-remote__list_repos": "list_repos",
         "mcp__claude-code-remote__register_repo_root": "register_repo_root",
         "mcp__claude_ai__read_conversation": "read chat history"}

def short_path(p):
    for pre in PREFIXES:
        if p.startswith(pre): return p[len(pre):]
    return p

def tool_line(block):
    name = re.match(r'<tool name="([^"]+)">', block).group(1)
    params = dict(re.findall(r'<parameter name="([^"]+)">(.*?)</parameter>', block, re.S))
    label = NAMES.get(name, name)
    if "description" in params: what = params["description"].strip()
    elif "file_path" in params: what = short_path(params["file_path"].strip())
    elif "file_paths" in params: what = "several files"
    elif name == "Artifact": what = params.get("action", "publish")
    elif name == "SendUserFile": what = "send files: " + ", ".join(short_path(x) for x in re.findall(r"'([^']+)'", params.get("files", "")))
    elif name == "Skill": what = params.get("skill", "")
    elif name == "ToolSearch": what = params.get("query", "")
    elif name == "WebSearch": what = params.get("query", "")
    elif name in ("WebFetch",): what = params.get("url", "")
    elif label in ("add_repo",): what = f'{params.get("owner","")}/{params.get("repo","")}, {params.get("access","read")} access'
    elif name == "AskUserQuestion": what = "asked the person a multiple-choice question (shown in the next person turn)"
    else: what = ""
    return f"`[tool: {label}]{(' ' + what) if what else ''}`"

raw = open(sys.argv[1], encoding="utf-8").read()
out = []
for m in re.finditer(r'<turn n="(\d+)">(Human|Assistant): (.*?)</turn>', raw, re.S):
    n, who, body = m.group(1), m.group(2), html.unescape(m.group(3))
    for r in REDACT: body = body.replace(r, "[other repository]")
    if who == "Human":
        dates = re.findall(r"<system-reminder>\s*The current date is ([^<]+?)\.?\s*</system-reminder>", body)
        other = len(re.findall(r"<system-reminder>", body)) - len(dates)
        body = re.sub(r"<system-reminder>.*?</system-reminder>\s*", "", body, flags=re.S).strip()
        out.append(f"## Turn {n}, person\n")
        if dates: out.append(f"*The current date is {dates[0]}.*\n")
        if other > 0: out.append("`[app notice omitted]`\n")
        out.append(body + "\n")
    else:
        parts, pos, pending = [], 0, []
        for t in re.finditer(r'<tool name="[^"]+">.*?</tool>', body, re.S):
            text = body[pos:t.start()].strip()
            if text:
                if pending: parts.append("\n".join(pending)); pending = []
                parts.append(text)
            pending.append(tool_line(t.group(0))); pos = t.end()
        if pending: parts.append("\n".join(pending))
        tail = body[pos:].strip()
        if tail: parts.append(tail)
        out.append(f"## Turn {n}, Claude\n")
        out.append(("\n\n".join(parts) if parts else "*(This turn is empty in the chat history.)*") + "\n")
print("\n".join(out))
