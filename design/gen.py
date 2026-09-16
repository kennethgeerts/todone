# Generates the three artboards from one token set lifted from the running Omarchy shell.
FG="#d4be98"; BG="#282828"; ACC="#7daea3"; DESK="#1e1e1e"
PROJECTS={"NABU":"#7daea3","Home":"#a9b665","Garden":"#d8a657","Admin":"#d3869b","Car":"#e1875c","Holiday":"#89b482"}

CSS = f"""
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&display=swap">
<style>
  body {{ margin: 0; background: {DESK}; font-family: "Operator Mono SSm Nerd Lig", "JetBrains Mono", ui-monospace, monospace; color: {FG}; -webkit-font-smoothing: antialiased; }}
  a {{ color: {ACC}; }} a:hover {{ color: {FG}; }}
</style>
"""

def head(title):
    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <script src="./support.js"></script>
</head>
<body>
<x-dc>
<helmet>{CSS}</helmet>
"""
TAIL = "</x-dc>\n</body>\n</html>\n"

def svg_circle(kind, color):
    if kind=="todo":
        return f'<svg width="14" height="14" viewBox="0 0 14 14" style="flex: 0 0 auto"><circle cx="7" cy="7" r="5.5" fill="none" stroke="{color}" stroke-width="1.5"></circle></svg>'
    if kind=="prog":
        return f'<svg width="14" height="14" viewBox="0 0 14 14" style="flex: 0 0 auto"><circle cx="7" cy="7" r="5.5" fill="none" stroke="{color}" stroke-width="1.5"></circle><path d="M7 1.5 A5.5 5.5 0 0 1 7 12.5 Z" fill="{color}"></path></svg>'
    return f'<svg width="14" height="14" viewBox="0 0 14 14" style="flex: 0 0 auto"><circle cx="7" cy="7" r="5.5" fill="{color}" stroke="{color}" stroke-width="1.5"></circle><path d="M4.2 7.2 L6.2 9.2 L9.9 5.3" fill="none" stroke="{BG}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"></path></svg>'

def chip(name):
    return f'<span style="display: inline-flex; align-items: center; height: 18px; padding: 0 6px; font-size: 11px; line-height: 18px; color: {FG}cc; background: {FG}1f">@{name}</span>'

def button(label, selected=False, bordered=False, color=None):
    c = color or FG
    bg = f"{c}2e" if selected else "transparent"
    border = f"1px solid {FG}66" if bordered else "1px solid transparent"
    return f'<div style="display: flex; align-items: center; height: 28px; padding: 0 10px; box-sizing: border-box; font-size: 12px; line-height: 16px; color: {c}; background: {bg}; border: {border}">{label}</div>'

def row(kind, text, people=(), selected=False, dim=False, project="NABU"):
    color = ACC if selected else FG
    glyph_color = PROJECTS[project]
    if dim: color=f"{FG}80"; glyph_color=f"{PROJECTS[project]}99"
    chips = "".join(chip(p) for p in people)
    bg = f"{FG}14" if selected else "transparent"
    return f'''<div style="display: flex; align-items: center; gap: 10px; height: 32px; padding: 0 12px; background: {bg}">
      {svg_circle(kind, glyph_color)}
      <div style="font-size: 14px; line-height: 20px; color: {color}; white-space: nowrap">{text}</div>
      <div style="display: flex; gap: 4px; align-items: center">{chips}</div>
    </div>'''

def heading(name):
    return f'<div style="height: 24px; padding: 6px 12px 0; box-sizing: border-box; font-size: 12px; line-height: 16px; color: {PROJECTS[name]}">#{name}</div>'

def bar(width=1440):
    ws = "".join(f'<div style="display: flex; align-items: center; justify-content: center; width: 22px; height: 26px; font-size: 12px; color: {FG}; background: {FG}2e if False else transparent">{n}</div>' for n in [])
    workspaces = (
      f'<div style="display: flex; align-items: center; justify-content: center; width: 24px; height: 26px; font-size: 12px; color: {FG}; background: {FG}2e">1</div>'
      f'<div style="display: flex; align-items: center; justify-content: center; width: 24px; height: 26px; font-size: 12px; color: {FG}94">2</div>'
      f'<div style="display: flex; align-items: center; justify-content: center; width: 24px; height: 26px; font-size: 12px; color: {FG}94">3</div>'
    )
    check = f'<svg width="12" height="12" viewBox="0 0 12 12" style="flex: 0 0 auto"><path d="M2.5 6.2 L4.8 8.5 L9.6 3.6" fill="none" stroke="{FG}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"></path></svg>'
    return f'''<div style="display: flex; align-items: center; justify-content: space-between; width: {width}px; height: 26px; padding: 0 8px; box-sizing: border-box; background: {BG}; font-size: 12px; line-height: 16px">
  <div style="display: flex; align-items: center; gap: 2px">{workspaces}</div>
  <div style="display: flex; align-items: center; gap: 0; font-size: 12px; color: {FG}94">alacritty — ~/Work/todone</div>
  <div style="display: flex; align-items: center; gap: 14px">
    <div style="display: flex; align-items: center; gap: 6px; height: 26px; padding: 0 5px; color: {FG}">{check}<span>7</span></div>
    <div style="font-size: 12px; color: {FG}94">en</div>
    <div style="font-size: 12px; color: {FG}">Tue 16 Sep  12:37</div>
  </div>
</div>'''

def overlay(projects, people_row, list_html, quickadd_html, sel_project, sel_person):
    prow = "".join(button("#"+p, selected=(p==sel_project), color=PROJECTS[p]) for p in projects)
    hrow = "".join(button("@"+p, selected=(p==sel_person)) for p in people_row)
    search = f'<div style="display: flex; align-items: center; height: 34px; font-size: 16px; line-height: 20px; color: {FG}94">Search tasks…</div>'
    hint = f'<div style="display: flex; gap: 14px; font-size: 10px; line-height: 14px; color: {FG}73; padding-top: 6px"><span>↑↓ select</span><span>space state</span><span>enter edit</span><span>⌫ delete</span><span>/ search</span><span>a add</span><span>esc close</span></div>'
    return f'''<div style="position: relative; width: 1440px; height: 900px; overflow: hidden; background: {DESK}">
  {bar()}
  <div style="position: absolute; inset: 0; background: {BG}80"></div>
  <div style="position: absolute; left: 282px; top: 150px; width: 875px; height: 600px; box-sizing: border-box; background: {BG}; border: 2px solid {FG}; padding: 18px; display: flex; flex-direction: column; gap: 6px">
    {search}
    <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap">{prow}</div>
    <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap">{hrow}</div>
    <div style="height: 1px; background: {FG}33; margin: 6px 0"></div>
    <div style="display: flex; flex-direction: column; gap: 2px; flex: 1 1 auto; overflow: hidden">{list_html}</div>
    <div style="height: 1px; background: {FG}33; margin: 6px 0"></div>
    <div style="display: flex; align-items: center; gap: 8px; height: 28px">{quickadd_html}</div>
    {hint}
  </div>
</div>'''

plus = f'<svg width="14" height="14" viewBox="0 0 14 14" style="flex: 0 0 auto"><path d="M7 2.5 V11.5 M2.5 7 H11.5" fill="none" stroke="{FG}" stroke-width="1.5" stroke-linecap="round"></path></svg>'
chev = f'<svg width="10" height="10" viewBox="0 0 10 10" style="flex: 0 0 auto"><path d="M2 3.5 L5 6.5 L8 3.5" fill="none" stroke="{FG}" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"></path></svg>'

def field(inner, placeholder=True):
    color = f"{FG}94" if placeholder else FG
    return f'<div style="display: flex; align-items: center; gap: 6px; flex: 1 1 auto; height: 28px; padding: 0 10px; box-sizing: border-box; border: 1px solid {FG}66; font-size: 12px; color: {color}">{inner}</div>'

projects=["NABU","Home","Garden","Admin","Car","Holiday"]
people_row=["Kenneth","Katrien","Cisse","Stan"]

# ---- Default state
default_list = "".join([
  row("todo","Todo task",["Kenneth"],selected=True,project="NABU"),
  row("todo","Buy paint for the hallway",["Katrien","Stan"],project="Home"),
  row("prog","Fix the fence",["Cisse"],project="Garden"),
  row("todo","Renew car insurance",["Kenneth"],project="Admin"),
  row("prog","In-progress task",project="NABU"),
  row("todo","Call the plumber",project="Home"),
  row("todo","Order seeds",project="Garden"),
  row("done","Done task",dim=True,project="NABU"),
])
default_quick = plus + field(f'Add to <span style="color: {PROJECTS["NABU"]}">#NABU</span>… <span style="opacity: .7">(# project, @ people)</span>')
open("Main.dc.html","w").write(head("Todone overlay")+overlay(projects,people_row,default_list,default_quick,None,None)+TAIL)

# ---- Filtered state: Home + Mine
filtered_list = "".join([
  row("todo","Paint the hallway",["Kenneth","Katrien"],selected=True,project="Home"),
  row("prog","Mount the shelves",["Kenneth"],project="Home"),
])
caret = f'<span style="display: inline-block; width: 1px; height: 14px; background: {FG}"></span>'
filtered_quick = plus + field(chip("Kenneth")+caret+f'<span style="color: {FG}94">Add to <span style="color: {PROJECTS["Home"]}">#Home</span>…</span>', placeholder=False)
open("Filtered.dc.html","w").write(head("Todone overlay, filtered")+overlay(projects,people_row,filtered_list,filtered_quick,"Home","Kenneth")+TAIL)

# ---- Bar strip
open("Bar.dc.html","w").write(head("Todone bar widget")+f'<div style="width: 1440px; height: 26px">{bar()}</div>'+TAIL)

import json
json.dump({
  "artboards":[
    {"file":"Bar.dc.html","x":0,"y":0,"w":1440,"h":26,"title":"Bar widget"},
    {"file":"Main.dc.html","x":0,"y":160,"w":1440,"h":900,"title":"Overlay, default"},
    {"file":"Filtered.dc.html","x":1540,"y":160,"w":1440,"h":900,"title":"Overlay, Home + Mine"}
  ],
  "annotations":[
    {"id":"tokens","x":1540,"y":-10,"w":420,"text":"Drawn with the running shell's tokens: current gruvbox theme, monospace at 12px base, corner radius 0, menu card 875×600 with 2px foreground border and 18px padding, 28px controls.\nProject names other than NABU are placeholders. Font stands in for the system monospace."}
  ],
  "launch":{"view":"canvas"}
}, open("canvas.json","w"), indent=2)
print("ok")
