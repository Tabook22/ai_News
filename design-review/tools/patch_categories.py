from pathlib import Path

old = "'video': 'الفيديو',"
new = "'video': 'الفيديو', 'video_edit': 'المونتاج', 'presentations': 'العروض',"

for name in ["app/templates/directory_v3.html", "app/templates/tool_detail_v3.html"]:
    p = Path(name)
    s = p.read_text(encoding="utf-8")
    if old not in s:
        print("missing anchor in", name)
        continue
    s = s.replace(old, new, 1)
    p.write_text(s, encoding="utf-8")
    print("patched", name)
