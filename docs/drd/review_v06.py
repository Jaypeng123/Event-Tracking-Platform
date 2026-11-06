# -*- coding: utf-8 -*-
"""以團隊 review 後的 v0.5（v0.5_3）為底，產生 v0.6。
規則：團隊保留的紅字、綠字一律轉黑；團隊保留的刪除線＝確認刪除（直接拿掉）。
本輪：紅字＝補充；綠字＝修改（含錯字、命名、Sample Values 清理）；黃底只留在仍待確認的儲存格。
用法：python3 docs/drd/review_v06.py <v0.5_3.xlsx> <out.xlsx>"""
import math
import re
import sys
import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
from openpyxl.cell.rich_text import CellRichText, TextBlock
from openpyxl.cell.text import InlineFont
from openpyxl.utils import get_column_letter

SRC, OUT = sys.argv[1], sys.argv[2]
FONT = "Calibri"
RED, GREEN = "FF0000", "00B050"
YELLOW = PatternFill("solid", fgColor="FFFF00")
NOFILL = PatternFill(fill_type=None)
HEAD_FILL = PatternFill("solid", fgColor="375623")
HEAD_FONT = Font(name=FONT, size=12, color="FFFFFF")
PRI = {"高": (PatternFill("solid", fgColor="FFC7CE"), "9C0006"),
       "中": (PatternFill("solid", fgColor="FFEB9C"), "9C5700"),
       "低": (PatternFill("solid", fgColor="C6EFCE"), "006100")}
GRID = Side(style="thin", color="D9D9D9")
DOUBLE = Side(style="double", color="000000")
BORDER = Border(left=GRID, right=GRID, top=GRID, bottom=GRID)
WRAP = Alignment(wrap_text=True, vertical="center")
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)


def R(t): return ("R", t)
def G(t): return ("G", t)


def plain(v):
    if v is None:
        return ""
    if isinstance(v, tuple):
        return v[1]
    if isinstance(v, list):
        return "".join(plain(x) for x in v)
    return str(v)


def put(cell, v):
    if isinstance(v, list):
        blocks = []
        for seg in v:
            if isinstance(seg, tuple):
                blocks.append(TextBlock(InlineFont(rFont=FONT, sz=11, color=RED if seg[0] == "R" else GREEN,
                                                   strike=seg[0] == "S"), seg[1]))
            elif seg:
                blocks.append(TextBlock(InlineFont(rFont=FONT, sz=11, color="000000"), seg))
        cell.value = CellRichText(blocks)
        cell.font = Font(name=FONT, size=11, color="000000")
        return
    color, st = "000000", False
    if isinstance(v, tuple):
        color = RED if v[0] == "R" else GREEN
        st = v[0] == "S"
        v = v[1]
    cell.value = v if v not in ("", None) else None
    cell.font = Font(name=FONT, size=11, color=color, strike=st)


def cell_text(c):
    """回傳 (去掉刪除線段落的文字, 是否整格都是刪除線)。"""
    v = c.value
    if v is None:
        return "", False
    if isinstance(v, CellRichText):
        keep, segs, allstrike = [], 0, True
        for b in v:
            if isinstance(b, TextBlock):
                st = bool(b.font and b.font.strike)
                segs += 1
                allstrike &= st
                if not st:
                    keep.append(b.text)
            else:
                segs += 1
                allstrike = False
                keep.append(b)
        return "".join(keep), allstrike and segs > 0
    st = bool(c.font and c.font.strike)
    return ("" if st else str(v)), st


def yel(c):
    return bool(c.fill and c.fill.fill_type == "solid" and c.fill.fgColor.rgb == "FFFFFF00")


# =====================================================================
# 1) 讀團隊版 DRD
src = openpyxl.load_workbook(SRC, rich_text=True)
ws0 = src["DRD"]
events = []
for r in range(2, ws0.max_row + 1):
    cells = [ws0.cell(r, c) for c in range(1, 12)]
    if cells[1].value is not None:
        t = [cell_text(x)[0] for x in cells]
        events.append({"id": t[0] or "SCROLL", "page": t[1], "name": t[2], "trig": t[3], "goal": t[4], "note": t[10],
                       "props": [], "y": set()})
    key_raw = cells[5].value
    if key_raw is None and cells[6].value is None:
        continue
    t = [cell_text(x) for x in cells]
    key, key_struck = t[5]
    if "改為非刪除線" in str(plain(key_raw) if not isinstance(key_raw, CellRichText) else "".join(
            b.text if isinstance(b, TextBlock) else b for b in key_raw)):
        key, key_struck = "is_abnormal_item", False
        t[6] = ("這個頁籤是否有待處理警報或這次轉診的異常項目", False)
        t[9] = ("高", False)
    if key_struck:
        continue  # 團隊保留刪除線＝確認刪除
    events[-1]["props"].append({"key": key, "def": t[6][0], "type": t[7][0], "sample": t[8][0], "pri": t[9][0],
                                "y": set(), "strike": False})
for e in events:
    e["props"] = [p for p in e["props"] if p["key"] or p["def"]]


def ev(eid):
    return next(e for e in events if e["id"] == eid)


def prop(e, key):
    return next(p for p in e["props"] if plain(p["key"]) == key)


def has(e, key):
    return any(plain(p["key"]) == key for p in e["props"])


def newp(key, d, t, s, pri):
    return {"key": R(key), "def": R(d), "type": R(t), "sample": R(s), "pri": pri, "pri_tag": "R", "y": set(), "strike": False}


def addp(e, after, *ps):
    i = 0 if after is None else next(n for n, p in enumerate(e["props"]) if plain(p["key"]) == after) + 1
    e["props"][i:i] = list(ps)


def drop(e, key, nth=0):
    idx = [n for n, p in enumerate(e["props"]) if plain(p["key"]) == key]
    del e["props"][idx[nth]]


def reorder(e, keys):
    order = {k: n for n, k in enumerate(keys)}
    e["props"].sort(key=lambda p: order.get(plain(p["key"]), 99))


def note_add(e, text):
    """在備註後面補紅字。"""
    base = e["note"]
    sep = "；" if plain(base) else ""
    if isinstance(base, list):
        e["note"] = base + [R(sep + text)]
    else:
        e["note"] = ([base] if base else []) + [R(sep + text)]


VITALS = ("blood_pressure, ecg, spo2, body_temp, news2_score, blood_glucose, uric_acid, total_cholesterol, body_fat, "
          "multi_vitals, hrv, sleep, exercise, steps")
DV = lambda: newp("detail_visit_id", "這次進入個案詳情的編號（同 DJY_17）", "string", "dv_7f3k2a", "高")

# =====================================================================
# 2) 本輪修改（底稿：團隊 v0.5_3；上一輪留下的紅字、綠字一律轉黑，黃底全部重新判斷）
def S(t): return ("S", t)


def strike(e, key):
    for p in e["props"]:
        if plain(p["key"]) == key:
            p["strike"] = True


def setp(e, key, **kw):
    p = prop(e, key)
    for k, v in kw.items():
        p[k] = v
    return p


# ---- 編號格式：三種「這一次」的編號用同一套寫法
IDDEF = {
    "session_id": ("這次上線的編號；登入成功，或閒置超過 30 分鐘後再操作時產生新的。格式：ss_使用者帳號_產生時間（年月日時分秒）",
                   "{{string}}, e.g. ss_u_10293_20261105093012"),
    "detail_visit_id": ("這次進入個案詳情的編號；每進入一次個案詳情產生一個新的，個案詳情內的事件都帶同一個。格式：dv_使用者帳號_產生時間（年月日時分秒）",
                        "{{string}}, e.g. dv_u_10293_20261105093105"),
    "popup_visit_id": ("這次打開視窗的編號；每打開一次視窗產生一個新的，視窗內的事件都帶同一個。格式：po_使用者帳號_產生時間（年月日時分秒）",
                       "{{string}}, e.g. po_u_10293_20261105093512"),
}
NULL_TYPE = "null, high_risk, low_risk, abnormal_report"
for e in events:
    for p in e["props"]:
        k = plain(p["key"])
        if k in IDDEF:
            p["def"], p["sample"] = G(IDDEF[k][0]), G(IDDEF[k][1])
        elif k == "alert_level":  # 值是「檢測高風險／檢測低風險／異常上報」，是類型不是等級
            p["key"] = G("alert_type")
            if e["id"] == "DJY_02":
                p["def"] = G("警報類型（檢測高風險、檢測低風險、異常上報）")
            else:
                p["def"] = G("警報類型（檢測高風險、檢測低風險、異常上報）；沒有警報時為 null，例如單純轉診給醫師")
                p["sample"] = G(NULL_TYPE)
        elif k == "metric":
            p["key"], p["def"] = G("vital_name"), G("切換時正在看的生理項目")
        elif k == "alert_items":
            p["def"] = G("警報項目；多個用逗號分隔、不加空格；代碼見代碼對照表「生理項目」「警報項目」")
            p["sample"] = G(("null, " if "null" in plain(p["sample"]) else "") + "{{string}}, e.g. blood_pressure,ecg")

# ---- DJY_01：機構管理員也會看到警報
e = ev("DJY_01")
nt = plain(e["note"])
rest = nt.split("；", 1)[1] if "；" in nt else nt
e["note"] = [G("分析時排除管理員（admin）；機構管理員（org_admin）在工作台、小鈴鐺通知也會看到並處理警報，是否列入分析待確認；"), rest]
e["y"].add("note")

# ---- DJY_07 小鈴鐺通知卡片曝光：曝光改 2 秒（與列表一致）
e = ev("DJY_07")
e["note"] = G(plain(e["note"]).replace("≥1 秒", "≥2 秒"))

# ---- DJY_09 前往列表：依「最新通知」畫面
e = ev("DJY_09")
setp(e, "list_name", sample=G("high_risk, abnormal_report, custom_plan_unmeasured, low_risk, doctor_pending"))
prop(e, "list_name")["y"].add("sample")
e["note"] = G("依「最新通知」畫面，異常提醒下方有 4 個按鈕：前往高風險列表、前往異常上報列表、前往自訂計畫未測量列表、前往低風險列表；"
              "醫師的轉診提醒是否有「前往待醫師處理列表」（doctor_pending）待確認")

# ---- DJY_11～13 待處理列表：依畫面補齊 7 個分頁
LISTS = "high_risk, abnormal_report, custom_plan_unmeasured, monthly_high_risk_unhandled, monthly_high_risk_handled, monthly_low_risk, low_risk"
for eid in ("DJY_11", "DJY_12", "DJY_13"):
    setp(ev(eid), "list_name", sample=G(LISTS))
ev("DJY_12")["goal"] = G("紀錄哪些異常個案在列表中被看到")

# ---- 新增：待處理列表的來源篩選（畫面上有「檢測儀／watch」）
LIST_FILTER = {"id": "LIST_FILTER", "page": R("待處理列表／來源篩選"), "name": R("apply_filter"),
               "trig": R("點擊「檢測儀」或「watch」、列表更新後"),
               "goal": R("紀錄在待處理列表依設備切換的次數，了解檢測儀與 Watch 的警報是不是分開處理"),
               "note": R("預設為檢測儀；點選目前已選中的來源不送"), "y": set(), "props": [
                   newp("page_name", "頁面名稱", "string", "pending_list", "高"),
                   newp("list_name", "目前所在的列表分頁", "string", LISTS, "高"),
                   newp("filter_type", "篩選類型", "string", "alert_source", "高"),
                   newp("filter_value", "切換後的來源", "string", "monitor, watch", "高")]}
events.insert(events.index(ev("DJY_11")) + 1, LIST_FILTER)

# ---- 新增：離開個案詳情（記整段停留時間）
DETAIL_LEAVE = {"id": "DETAIL_LEAVE", "page": R("個案詳情"), "name": R("leave_page"),
                "trig": R("離開個案詳情時（關閉瀏覽器分頁、切換個案、回到列表）"),
                "goal": R("紀錄每次進入個案詳情總共停留多久；搭配照護記錄、醫師建議，了解排查與處理各花多少時間"),
                "note": R("個案詳情是另開瀏覽器分頁，關閉分頁時也要送；停留不到 2 秒不送"), "y": set(), "props": [
                    newp("page_name", "頁面名稱", "string", "patient_detail", "高"),
                    newp("detail_visit_id", IDDEF["detail_visit_id"][0], "string", IDDEF["detail_visit_id"][1], "高"),
                    newp("patient_id", "個案編號（平台內部編號，不送姓名）", "string", "{{string}}, e.g. p_88231", "高"),
                    newp("duration", "這次個案詳情的停留秒數；切到其他瀏覽器分頁的時間不算", "Integer", "{{seconds}}, e.g. 180", "高")]}
events.insert(events.index(ev("DJY_17")) + 1, DETAIL_LEAVE)

# ---- 停留秒數：停留結束時才送（DJY_18 頁籤、DJY_19 生理項目、DJY_21 數據來源、DJY_22 時間範圍）
STAY = "duration 的算法見共用規則「停留秒數」；停留不到 2 秒不送"
e = ev("DJY_18")
e["trig"] = G("進入一個 Header 頁籤時開始計時，到下一個操作、離開頁面或切到其他瀏覽器分頁時送出")
prop(e, "duration")["def"] = G("停留在這個頁籤的秒數")
e["note"] = G(STAY)
e = ev("DJY_19")
e["trig"] = G("點擊生理項目 tab 時開始計時，到下一個操作、離開頁面或切到其他瀏覽器分頁時送出")
prop(e, "duration")["def"] = G("停留在這個生理項目的秒數")
e["note"] = G(STAY)
e = ev("DJY_21")
e["trig"] = G("點擊 Home 或 Pro 時開始計時，到下一個操作、離開頁面或切到其他瀏覽器分頁時送出")
prop(e, "duration")["def"] = G("停留在這個來源的秒數")
e["note"] = R(STAY)
e = ev("DJY_22")
e["trig"] = G("點擊「今日／近 7 天／近 30 天／近 1 年」時開始計時，到下一個操作、離開頁面或切到其他瀏覽器分頁時送出")
e["note"] = G("預設為近 30 天；停留不到 2 秒不送（例如連續快速切換）")

# ---- DJY_24 心電區塊：依畫面定義 4 個區塊
e = ev("DJY_24")
setp(e, "block_name", sample=G("ai_diagnosis, recent_vitals, ecg_chart, health_risk"))
e["note"] = G("只記 4 個區塊（由上到下：AI 診斷結果、近期生命徵象、心電圖、健康風險評估），用來判斷區塊排序是否合理；滑鼠游標停留累計不到 3 秒的區塊不送")

# ---- 照護記錄、醫師建議：打開時的 duration 改用 event_time 計算
for eid in ("DJY_28", "DJY_32"):
    strike(ev(eid), "duration")
    note_add(ev(eid), "從進入個案詳情到打開表單的時間，用同一個 detail_visit_id 的 event_time 相減即可，不另外送 duration")
for eid in ("DJY_29", "DJY_33"):
    prop(ev(eid), "duration")["def"] = G("從打開視窗到按下取消或關閉的秒數")
for eid in ("DJY_30", "DJY_34"):
    prop(ev(eid), "duration")["def"] = G("從打開視窗到離開的秒數")
for eid in ("DJY_31", "DJY_35"):
    prop(ev(eid), "text_length")["def"] = G("文字欄位的字數（只送字數，不送內容）；0 代表沒有填文字")
strike(ev("DJY_35"), "is_empty")
note_add(ev("DJY_35"), "is_empty 和照護記錄（DJY_31）一致拿掉，改用 text_length = 0 判斷")

# ---- 仍待確認的黃底
ev("DJY_14")["y"].add("note")
prop(ev("DJY_16"), "button_name")["y"].add("sample")

# ---- 屬性排序：全文件統一
ORDER = ["button_name", "page_name", "popup_name", "popup_visit_id", "detail_visit_id",
         "patient_id", "alert_id", "referral_id",
         "notification_tab", "exposure_entry", "list_name", "entry_source", "block_name", "open_type",
         "filter_type", "filter_value",
         "alert_type", "alert_items", "has_alert", "vital_name", "is_abnormal_item", "has_data", "todo_types",
         "position", "total_records", "open_seq", "has_input", "text_length", "is_empty", "duration"]
for _e in events:
    if _e["id"] in ("DJY_01", "DJY_02", "DJY_03", "DJY_04", "DJY_05"):
        continue
    _e["props"].sort(key=lambda q: ORDER.index(plain(q["key"])) if plain(q["key"]) in ORDER else 99)


# =====================================================================
# 4) 重新編號
IDMAP, n = {}, 0
for e in events:
    n += 1
    old, new = e["id"], f"DJY_{n:02d}"
    IDMAP[old] = new
    e["new_id"] = new
    e["id_tag"] = "R" if not old.startswith("DJY_") else ("G" if old != new else None)
ID_RE = re.compile(r"DJY_\d{2}|LIST_FILTER|DETAIL_LEAVE")


def remap_text(t):
    return ID_RE.sub(lambda m: IDMAP.get(m.group(0), m.group(0)), t)


def remap_val(v):
    if isinstance(v, tuple):
        return (v[0], remap_text(v[1]))
    if isinstance(v, list):
        return [remap_val(x) for x in v]
    return remap_text(v) if isinstance(v, str) else v


for e in events:
    for k in ("trig", "goal", "note", "page"):
        e[k] = remap_val(e[k])
    for p in e["props"]:
        for k in ("def", "sample"):
            p[k] = remap_val(p[k])

# =====================================================================
# 5) 寫出 DRD
wb = src
idx = wb.sheetnames.index("DRD")
widths = {k: v.width for k, v in ws0.column_dimensions.items()}
wb.remove(ws0)
ws = wb.create_sheet("DRD", idx)
H = ["編號", "頁面/區塊", "事件名稱 (En)", "觸發時機/事件定義\n(Trigger/Event Definition)", "目標/數據分析意義",
     "屬性參數 (Property)", "屬性定義 (Property Definition)", "Data Type", "Sample Values", "優先級", "備註"]
ws.append(H)
for c in range(1, 12):
    cell = ws.cell(1, c)
    cell.fill, cell.font, cell.border, cell.alignment = HEAD_FILL, HEAD_FONT, BORDER, WRAP
ws.row_dimensions[1].height = 36
ws.freeze_panes = "A2"
for col, w in widths.items():
    ws.column_dimensions[col].width = w
for n, e in enumerate(events):
    start = ws.max_row + 1
    for j, p in enumerate(e["props"]):
        r = start + j
        for c in range(1, 12):
            ws.cell(r, c).border, ws.cell(r, c).alignment = BORDER, WRAP
        if j == 0:
            put(ws.cell(r, 1), (e["id_tag"], e["new_id"]) if e["id_tag"] else e["new_id"])
            for k, c in (("page", 2), ("name", 3), ("trig", 4), ("goal", 5), ("note", 11)):
                put(ws.cell(r, c), e[k])
                if k in e["y"]:
                    ws.cell(r, c).fill = YELLOW
        for k, c in (("key", 6), ("def", 7), ("type", 8), ("sample", 9)):
            put(ws.cell(r, c), S(plain(p[k])) if p.get("strike") else p[k])
            if k in p["y"]:
                ws.cell(r, c).fill = YELLOW
        pc = ws.cell(r, 10)
        pc.alignment = CENTER
        if p["pri"] in PRI:
            fill, fc = PRI[p["pri"]]
            pc.value, pc.fill = p["pri"], fill
            pc.font = Font(name=FONT, size=11, color=GREEN if p.get("strike") else (RED if p.get("pri_tag") == "R" else fc),
                           strike=bool(p.get("strike")))
    end = start + len(e["props"]) - 1
    if end > start:
        for c in (1, 2, 3, 4, 5, 11):
            ws.merge_cells(start_row=start, start_column=c, end_row=end, end_column=c)
    if n == 0:
        for c in range(1, 12):
            ws.cell(end, c).border = Border(left=GRID, right=GRID, top=GRID, bottom=DOUBLE)

# =====================================================================
# 6) 代碼對照表：依 DRD 的 Sample Values 重新產生，中文名稱沿用團隊版
wc = wb["代碼對照表"]
old_rows, cur = {}, None
old_order = []
for r in range(2, wc.max_row + 1):
    a, _ = cell_text(wc.cell(r, 1))
    if a:
        cur = a
    b, bs = cell_text(wc.cell(r, 2))
    if bs or not b:
        continue
    zh = cell_text(wc.cell(r, 3))[0]
    nt = cell_text(wc.cell(r, 4))[0]
    old_rows[(cur, b)] = (zh, nt)
    if cur not in old_order:
        old_order.append(cur)
# 舊版的鍵名對應到新版
KEY_ALIAS = {"metric": "生理項目", "alert_level": "alert_type"}
ZH = {  # 新代碼或需要修改的中文名稱／說明
    ("user_role", "org_admin"): ("機構管理員", "也會處理警報，分析時是否排除待確認"),
    ("page_name", "patient_detail_health_plan"): ("個案詳情｜健康計畫", "Header 頁籤"),
    ("filter_type", "alert_source"): ("來源篩選", "小鈴鐺通知、待處理列表的「檢測儀／watch」"),
    ("filter_value", "monitor"): ("CoDoctor 檢測儀", "filter_type = alert_source"),
    ("filter_value", "watch"): ("CoDoctor Watch", "filter_type = alert_source"),
    ("list_name", "high_risk"): ("檢測高風險列表", ""),
    ("list_name", "custom_plan_unmeasured"): ("自訂計畫-未測量列表", ""),
    ("list_name", "monthly_high_risk_unhandled"): ("月度高風險-未處理列表", ""),
    ("list_name", "monthly_high_risk_handled"): ("月度高風險-已處理列表", ""),
    ("list_name", "monthly_low_risk"): ("月度低風險列表", ""),
    ("list_name", "doctor_pending"): ("待醫師處理列表", "只用在小鈴鐺通知的「前往列表」，醫師是否有這個按鈕待確認"),
    ("生理項目", "blood_pressure"): ("血壓", "檢測儀、Watch 都有；vital_name、filter_value（vital_item）、alert_items 共用這組代碼"),
    ("警報項目", "heart_rate"): ("心率", "Watch 的警報項目；alert_items 除了「生理項目」的代碼，還會有這一組"),
    ("警報項目", "shortness_of_breath"): ("呼吸不暢", "Watch 上報的症狀；症狀完整清單待確認"),
    ("警報項目", "dizziness"): ("頭暈", "Watch 上報的症狀"),
    ("警報項目", "abnormal_report_tag"): ("異常上報標籤", "Watch 上報"),
    ("resolve_type", "doctor_advice"): ("醫師建議", ""),
    ("block_name", "ai_diagnosis"): ("AI 診斷結果", "心電頁第 1 個區塊"),
    ("block_name", "recent_vitals"): ("近期生命徵象", "心電頁第 2 個區塊"),
    ("block_name", "ecg_chart"): ("心電圖", "心電頁第 3 個區塊"),
    ("block_name", "health_risk"): ("健康風險評估", "心電頁第 4 個區塊"),
}
ENUM_KEYS = ["user_role", "page_name", "popup_name", "button_name", "list_name", "notification_tab", "exposure_entry",
             "entry_source", "filter_type", "filter_value", "alert_type", "生理項目", "警報項目", "resolve_type", "device_source",
             "block_name", "todo_types", "open_type"]
VSET = set(VITALS.split(", "))
codes = {}  # (key, value) -> set(event ids)
for e in events:
    ftype = next((plain(p["sample"]) for p in e["props"] if plain(p["key"]) == "filter_type"), "")
    for p in e["props"]:
        k, s = plain(p["key"]), plain(p["sample"])
        if k == "alert_items":
            for v in VITALS.split(", "):
                codes.setdefault(("生理項目", v), set()).add(e["new_id"])
            for v in ("heart_rate", "shortness_of_breath", "dizziness", "abnormal_report_tag"):
                codes.setdefault(("警報項目", v), set()).add(e["new_id"])
            continue
        if k == "vital_name" or (k == "filter_value" and ftype == "vital_item"):
            k = "生理項目"
        if k not in ENUM_KEYS:
            continue
        vals = [v.strip() for v in s.split(",")]
        if k == "filter_value" and s.startswith("custom_"):
            vals = ["custom_{{number}}"]
        for v in vals:
            if not v or v == "null" or "{{" in v and k != "filter_value":
                continue
            codes.setdefault((k, v), set()).add(e["new_id"])
for (k, v), ids in list(codes.items()):
    if k == "生理項目":
        pass
rows = []
for k in ENUM_KEYS:
    vals = [v for (kk, v) in codes if kk == k]
    old_vals = [v for (kk, v) in old_rows if (KEY_ALIAS.get(kk, kk)) == k]
    vals.sort(key=lambda v: old_vals.index(v) if v in old_vals else 999)
    for v in vals:
        old_key = next((kk for (kk, vv) in old_rows if vv == v and KEY_ALIAS.get(kk, kk) == k), None)
        old = old_rows.get((old_key, v)) if old_key else None
        zh, nt = ZH.get((k, v), old or ("", ""))
        if old is None:
            zc, nc, vc = R(zh), R(nt) if nt else "", R(v)
        else:
            zc = zh if zh == old[0] else G(zh)
            nc = nt if nt == old[1] else (G(nt) if nt else "")
            vc = v
        rows.append([k, vc, zc, nc, "、".join(sorted(codes[(k, v)]))])
cidx = wb.sheetnames.index("代碼對照表")
cw = {k: v.width for k, v in wc.column_dimensions.items()}
chead = [wc.cell(1, c).value for c in range(1, 6)]
wb.remove(wc)
wc = wb.create_sheet("代碼對照表", cidx)
wc.append(chead)
for c in range(1, 6):
    cell = wc.cell(1, c)
    cell.fill, cell.font, cell.border, cell.alignment = HEAD_FILL, HEAD_FONT, BORDER, WRAP
wc.row_dimensions[1].height = 36
wc.freeze_panes = "A2"
for k, w in cw.items():
    wc.column_dimensions[k].width = w
r, grp = 2, []
for row in rows:
    for c in range(1, 6):
        wc.cell(r, c).border, wc.cell(r, c).alignment = BORDER, WRAP
        put(wc.cell(r, c), row[c - 1] if c > 1 else "")
    if "待確認" in plain(row[3]):
        wc.cell(r, 4).fill = YELLOW
    if grp and grp[-1][0] == row[0]:
        grp[-1][2] = r
    else:
        grp.append([row[0], r, r])
    r += 1
OLD_KEYS = {KEY_ALIAS.get(k, k) for k in old_order}
for k, a, b in grp:
    put(wc.cell(a, 1), k if k in OLD_KEYS or k == "生理項目" else (G(k) if k == "alert_type" else R(k)))
    if b > a:
        wc.merge_cells(start_row=a, start_column=1, end_row=b, end_column=1)

# =====================================================================
# 7) 指標對照：舊顏色轉黑，同步編號與受影響的說明
wm = wb["指標對照"]
for row in wm.iter_rows(min_row=2):
    for c in row:
        if c.value is None:
            continue
        t, _ = cell_text(c)
        put(c, t)
        c.alignment = WRAP


def mrow(name):
    return next(r for r in range(2, wm.max_row + 1) if str(wm.cell(r, 2).value or "").startswith(name))


for r in range(2, wm.max_row + 1):
    for col in (2, 3, 4, 5):
        c = wm.cell(r, col)
        t = str(c.value or "")
        if "警報等級" in t:
            put(c, G(t.replace("警報等級", "警報類型")))
    c = wm.cell(r, 6)
    old = str(c.value or "")
    if old.startswith("DJY"):
        new = "、".join(sorted({IDMAP.get(x.strip(), x.strip()) for x in old.split("、")}, key=lambda s: int(s[4:])))
        put(c, new)
put(wm.cell(mrow("③ 異常排查時長"), 4), G("第一次打開照護記錄的 event_time − 同一個 detail_visit_id 進入個案詳情的 event_time"))
put(wm.cell(mrow("③ 異常排查時長"), 6), G("、".join([IDMAP["DJY_17"], IDMAP["DJY_28"]])))
r19 = mrow("③ 心電區塊觸及率")
put(wm.cell(r19, 5), G("4 個區塊由上到下：AI 診斷結果、近期生命徵象、心電圖、健康風險評估；觸及率沒有隨位置往下遞減的區塊，代表排序可以調整"))


def insert_metric(after_name, cells):
    ins = mrow(after_name) + 1
    merges = [(m.min_row, m.min_col, m.max_row, m.max_col) for m in wm.merged_cells.ranges]
    for m in list(wm.merged_cells.ranges):
        wm.unmerge_cells(str(m))
    wm.insert_rows(ins)
    for (a, b, c2, d) in merges:
        if a >= ins:
            a, c2 = a + 1, c2 + 1
        elif c2 >= ins:
            c2 += 1
        wm.merge_cells(start_row=a, start_column=b, end_row=c2, end_column=d)
    for c, v in enumerate(cells, 1):
        cell = wm.cell(ins, c)
        if c > 1:
            put(cell, R(v))
        cell.alignment, cell.border = WRAP, BORDER


insert_metric("④ 照護記錄填寫時長", ["", "⑤ 個案詳情停留時長", "輔助判讀／分鐘",
              "每次進入個案詳情的停留時間（離開個案詳情時的 duration），看中位數；依這次有沒有提交照護記錄拆開比較",
              "和 ③ 異常排查時長一起看：③ 是「看到打開表單」，本指標是「整段停留」",
              "、".join([IDMAP["DJY_17"], IDMAP["DETAIL_LEAVE"], IDMAP["DJY_31"]]),
              "1. 短（≤3 分鐘）：很快完成判斷 → 維持\n2. 中（>3～5 分鐘）：需要一些時間查資料 → 看各頁籤停留秒數，找出最花時間的資訊\n3. 長（>5 分鐘）：查資料的負擔重 → 檢查資訊是否分散、是否需要整合"])

# =====================================================================
# 8) 埋點共用規則：重建
wr = wb["埋點共用規則"]
old_rules = []
cur = ""
for r in range(2, wr.max_row + 1):
    a = cell_text(wr.cell(r, 1))[0] or cur
    cur = a
    b, bs = cell_text(wr.cell(r, 2))
    if bs:
        continue
    old_rules.append([a, b, cell_text(wr.cell(r, 3))[0], cell_text(wr.cell(r, 4))[0]])
used_names = []
for e in events:
    nm = plain(e["name"])
    if nm not in used_names and nm != "所有事件" and not nm.startswith(("alert_", "referral_")):
        used_names.append(nm)
rules = []
for a, b, c, d in old_rules:
    row = [a, b, c, d]
    if b == "事件名稱":
        row[3] = "、".join(used_names) if "、".join(used_names) == d else G("、".join(used_names))
    elif b == "停留秒數 duration":
        row[2] = G("從畫面顯示（或切換）開始計時，到使用者下一個操作、離開頁面或切到其他瀏覽器分頁為止；切到其他瀏覽器分頁的時間不算；"
                   "四捨五入到整數。需要停留秒數的事件，在停留結束時才送出，event_time 記開始的時間；停留不到 2 秒不送")
        row[3] = G("點「血壓」看了 8 秒後點「心電」→ 送一筆 filter_value = blood_pressure、duration = 8")
    elif b in IDDEF:
        row[2] = G(IDDEF[b][0])
        row[3] = G(IDDEF[b][1].split("e.g. ")[1])
    elif b.startswith("曝光"):
        row[2] = G(c.replace("≥1 秒", "≥2 秒"))
    rules.append(row)
rules.insert(next(i for i, x in enumerate(rules) if x[1] == "detail_visit_id") + 1,
             ["編號", R("編號重複的可能"), R("同一個人在同一秒產生兩個同類編號才會重複，實務上幾乎不會發生；若開發端已有自己的編號產生方式，也可以沿用，只要不重複即可"), ""])
ridx = wb.sheetnames.index("埋點共用規則")
rw = {k: v.width for k, v in wr.column_dimensions.items()}
rhead = [wr.cell(1, c).value for c in range(1, 5)]
wb.remove(wr)
wr = wb.create_sheet("埋點共用規則", ridx)
wr.append(rhead)
for c in range(1, 5):
    cell = wr.cell(1, c)
    cell.fill, cell.font, cell.border, cell.alignment = HEAD_FILL, HEAD_FONT, BORDER, WRAP
wr.row_dimensions[1].height = 36
wr.freeze_panes = "A2"
for k, w in rw.items():
    wr.column_dimensions[k].width = w
grp = []
for i, row in enumerate(rules):
    r = i + 2
    for c in range(1, 5):
        wr.cell(r, c).border, wr.cell(r, c).alignment = BORDER, WRAP
        if c > 1:
            put(wr.cell(r, c), row[c - 1])
    if grp and grp[-1][0] == row[0]:
        grp[-1][2] = r
    else:
        grp.append([row[0], r, r])
for k, a, b in grp:
    put(wr.cell(a, 1), k)
    if b > a:
        wr.merge_cells(start_row=a, start_column=1, end_row=b, end_column=1)

for row in wb["Person Properties"].iter_rows(min_row=2):
    for c in row:
        if c.value is not None and not (c.fill and c.fill.fill_type == "solid" and c.fill.fgColor.rgb in ("FFFFC7CE", "00FFC7CE")):
            t, _ = cell_text(c)
            put(c, t)


# =====================================================================
# 9) 列高
def _w(ch):
    return 2 if ord(ch) > 0x2E80 else 1


def _lines(text, width):
    if not text:
        return 1
    cap = max(1, int(width * 0.95) - 2)
    return sum(max(1, math.ceil(sum(_w(c) for c in line) / cap)) for line in str(text).split("\n"))


def fit_rows(ws):
    merged = {}
    for mr in ws.merged_cells.ranges:
        merged[(mr.min_row, mr.min_col)] = (mr.max_row, mr.max_col)
        for r in range(mr.min_row, mr.max_row + 1):
            for c in range(mr.min_col, mr.max_col + 1):
                if (r, c) != (mr.min_row, mr.min_col):
                    merged[(r, c)] = None
    for row in ws.iter_rows(min_row=2):
        r = row[0].row
        lines = 1
        for cell in row:
            if (r, cell.column) in merged:
                continue
            w = ws.column_dimensions[get_column_letter(cell.column)].width or 10
            lines = max(lines, _lines(cell.value, w))
        ws.row_dimensions[r].height = lines * 18 + 8
    for (r0, c0), span in merged.items():
        if not span:
            continue
        r1, c1 = span
        width = sum((ws.column_dimensions[get_column_letter(c)].width or 10) for c in range(c0, c1 + 1))
        h = _lines(ws.cell(r0, c0).value, width) * 18 + 8
        have = sum(ws.row_dimensions[r].height or 21 for r in range(r0, r1 + 1))
        if h > have:
            ws.row_dimensions[r1].height = (ws.row_dimensions[r1].height or 21) + (h - have)


# 檢查：所有編號都對得到事件
alive = {e["new_id"] for e in events}
for sh in wb.worksheets:
    for row in sh.iter_rows(min_row=2):
        for cell in row:
            for m in ID_RE.findall(str(cell.value or "")):
                if m not in alive:
                    print("WARN", sh.title, cell.coordinate, m)
for sh in wb.worksheets:
    fit_rows(sh)
wb.active = wb.sheetnames.index("DRD")
wb.save(OUT)
print("saved", OUT, len(events), "events;", {k: v for k, v in IDMAP.items() if k != v})
