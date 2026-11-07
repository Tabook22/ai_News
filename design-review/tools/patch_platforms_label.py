from pathlib import Path

old = "'agents': 'الوكلاء', 'other': 'أخرى'"
new = "'agents': 'الوكلاء', 'platforms': 'المنصات', 'other': 'أخرى'"

for name in ["app/templates/directory_v3.html", "app/templates/tool_detail_v3.html", "app/templates/rankings_v3.html"]:
    p = Path(name)
    s = p.read_text(encoding="utf-8")
    if old not in s:
        print("anchor missing", name)
        continue
    s = s.replace(old, new, 1)
    p.write_text(s, encoding="utf-8")
    print("patched", name)
