# -*- coding: utf-8 -*-
"""以團隊修改後的 DRD v0.3（team.xlsx）為底，產生 review 版 v0.4。
紅字＝補充（填黃底、空白、新增的列）；綠字＝修改團隊既有內容；綠字刪除線＝建議刪除。
用法：python3 docs/drd/review_v04.py <team.xlsx> <out.xlsx>"""
import math
import re
import sys
import copy
import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
from openpyxl.cell.rich_text import CellRichText, TextBlock
from openpyxl.cell.text import InlineFont
from openpyxl.utils import get_column_letter

SRC, OUT = sys.argv[1], sys.argv[2]
FONT = "Calibri"
RED, GREEN = "FF0000", "00B050"
YELLOW = PatternFill("solid", fgColor="FFFF00")
HEAD_FILL = PatternFill("solid", fgColor="375623")
HEAD_FONT = Font(name=FONT, size=12, color="FFFFFF")
PRI = {
    "高": (PatternFill("solid", fgColor="FFC7CE"), "9C0006"),
    "中": (PatternFill("solid", fgColor="FFEB9C"), "9C5700"),
    "低": (PatternFill("solid", fgColor="C6EFCE"), "006100"),
}
GRID = Side(style="thin", color="D9D9D9")
DOUBLE = Side(style="double", color="000000")
BORDER = Border(left=GRID, right=GRID, top=GRID, bottom=GRID)
WRAP = Alignment(wrap_text=True, vertical="center")
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)


# ---- 標記：("R", 文字) 紅；("G", 文字) 綠；("S", 文字) 綠刪除線；list 為多段混色
def R(t): return ("R", t)
def G(t): return ("G", t)
def S(t): return ("S", t)


def plain(v):
    if v is None:
        return ""
    if isinstance(v, tuple):
        return v[1]
    if isinstance(v, list):
        return "".join(plain(x) for x in v)
    return str(v)


def put(cell, v, base_color="000000", strike_all=False):
    """寫入儲存格並套用顏色。"""
    if isinstance(v, list):
        blocks = []
        for seg in v:
            if isinstance(seg, tuple):
                tag, t = seg
                blocks.append(TextBlock(InlineFont(rFont=FONT, sz=11, color=RED if tag == "R" else GREEN,
                                                   strike=(tag == "S")), t))
            else:
                blocks.append(TextBlock(InlineFont(rFont=FONT, sz=11, color=base_color), seg))
        cell.value = CellRichText(blocks)
        cell.font = Font(name=FONT, size=11, color=base_color)
        return
    color, strike = base_color, strike_all
    if isinstance(v, tuple):
        tag, v = v
        color = RED if tag == "R" else GREEN
        strike = strike or tag == "S"
    if strike_all:
        color = GREEN
    cell.value = v if v != "" else None
    cell.font = Font(name=FONT, size=11, color=color, strike=strike)


# =====================================================================
# 1) 讀團隊版 DRD
src = openpyxl.load_workbook(SRC)
ws0 = src["DRD"]


def yel(c):
    return bool(c.fill and c.fill.fill_type == "solid" and c.fill.fgColor.rgb == "FFFFFF00")


events = []
for r in range(2, ws0.max_row + 1):
    row = [ws0.cell(r, c) for c in range(1, 12)]
    if row[1].value is not None:  # 頁面/區塊有值＝新事件
        events.append({
            "id": row[0].value or "", "page": row[1].value, "name": row[2].value, "trig": row[3].value or "",
            "goal": row[4].value or "", "note": row[10].value or "",
            "ey": {k: yel(row[i]) for k, i in (("id", 0), ("page", 1), ("name", 2), ("trig", 3), ("goal", 4), ("note", 10))},
            "props": [], "strike": False,
        })
    if row[5].value is None and not any(yel(x) for x in row[5:10]):
        continue
    events[-1]["props"].append({
        "key": row[5].value or "", "def": row[6].value or "", "type": row[7].value or "",
        "sample": row[8].value or "", "pri": row[9].value or "",
        "y": {k: yel(row[i]) for k, i in (("key", 5), ("def", 6), ("type", 7), ("sample", 8), ("pri", 9))},
        "strike": False,
    })
# 移除團隊在空白列留下的空屬性（黃底待醫師處理那列）
for e in events:
    e["props"] = [p for p in e["props"] if p["key"] or p["def"] or p["sample"]] or e["props"][:0]


def ev(eid):
    for e in events:
        if e["id"] == eid:
            return e
    raise KeyError(eid)


def ev_by_page(page):
    return next(e for e in events if e["page"] == page)


def prop(e, key):
    for p in e["props"]:
        if plain(p["key"]) == key:
            return p
    raise KeyError((e["id"], key))


def newp(key, d, t, s, pri, tag="R"):
    w = (lambda x: (tag, x)) if tag else (lambda x: x)
    return {"key": w(key), "def": w(d), "type": w(t), "sample": w(s), "pri": pri, "pri_tag": tag,
            "y": {}, "strike": False}


def addp(e, after, *ps):
    if after is None:
        i = 0
    else:
        i = next(n for n, p in enumerate(e["props"]) if plain(p["key"]) == after) + 1
    e["props"][i:i] = list(ps)


def newev(eid, page, name, trig, goal, note, props, tag="R"):
    w = lambda x: (tag, x) if x else ""
    return {"id": w(eid), "page": w(page), "name": w(name), "trig": w(trig), "goal": w(goal), "note": w(note),
            "ey": {}, "props": props, "strike": False}


def insert_ev(before_id, e):
    i = next(n for n, x in enumerate(events) if x["id"] == before_id)
    events.insert(i, e)


def insert_ev_after(obj, *es):
    i = events.index(obj) + 1
    events[i:i] = list(es)


VITALS = "blood_pressure, blood_glucose, ecg, spo2, heart_rate, body_temp, weight（完整清單待確認）"

# =====================================================================
# 2) 修改與補充
# ---- DJY_01 全域屬性
e = ev("DJY_01")
e["goal"] = G("紀錄每筆事件是誰、什麼角色、在哪個機構、哪一次上線、什麼時間發生的")
e["note"] = ["分析時排除機構管理員（org_admin）與管理員（admin）；", G("事件時間以 event_time 為準"),
             R("\nsession_id 由前端產生：登入成功，或閒置超過 30 分鐘後再操作時換新的。「上線」直接用 session_id 判斷"
               "（同一個 session_id 的第一筆事件＝上線開始、最後一筆＝上線結束），所以不需要另外埋上線事件")]
p = prop(e, "Event_time")
p["key"] = G("event_time")
p["type"] = R("string")
p["sample"] = R("{{timestamp}}, e.g. 2026-11-05T09:30:12+08:00（格式待確認，需與 alert_time 一致）")
p = prop(e, "session_id")
p["def"] = ["這次上線的編號；登入或閒置後重新操作時換新的", R("（閒置 30 分鐘）")]

# ---- DJY_02
e = ev("DJY_02")
prop(e, "alert_items")["sample"] = R("blood_pressure,ecg（多個用逗號分隔）；代碼：" + VITALS)

# ---- DJY_03 / DJY_05
prop(ev("DJY_03"), "resolve_type")["sample"] = G("care_record, doctor_advice（待確認）")
ev("DJY_05")["note"] = ["由後端記錄\n", S("埋在照護紀錄提交時"), G("埋在醫師建議提交時")]

# ---- 新增：打開小鈴鐺通知（補回）
insert_ev("DJY_08", newev(
    "DJY_42", "小鈴鐺通知", "view_popup", "點擊小鈴鐺、「最新通知」彈窗顯示完成時",
    "紀錄打開小鈴鐺通知的次數、預設停在哪個 tab、打開當下有多少未讀；是來源篩選、前往列表、點通知卡片等使用率的計算基礎",
    "「小鈴鐺通知」章節的指標（來源篩選使用率、快捷入口點擊率、無效開啟率、打開到點進的時間）都要用打開次數來算，所以補回",
    [newp("popup_name", "視窗名稱", "string", "notification_center", "高"),
     newp("popup_visit_id", "這次打開視窗的編號；每打開一次產生一個，視窗內的事件都帶同一個", "string", "po_2b9x7q", "高"),
     newp("notification_tab", "打開時預設顯示的 tab", "string", "alert, referral, tracking", "高"),
     newp("total_records", "打開當下的未讀數量", "Integer", "{{number}}, e.g. 12", "中")]))

# ---- DJY_08 通知卡片曝光
e = ev("DJY_08")
e["name"] = G("item_impression")
e["goal"] = G("紀錄各 tab 的個案卡片有沒有被對應角色看到（一線人員／機構管理員看「異常提醒」、醫師看「轉診提醒」），"
              "用來計算警報、轉診的曝光率")
e["note"] = ["曝光以 patient_id 去重（同一個案多筆警報只計 1 人）；曝光定義為卡片出現在可視範圍 ≥1 秒；",
             G("曝光率的計算基準按 tab 分開：異常提醒用警報（DJY_02）、轉診提醒用轉診（DJY_04），兩個 tab 不可共用；"
               "與待處理列表曝光（DJY_16）合計為整體警報曝光率時，本事件只取 notification_tab=alert，"
               "且同一個案跨兩條路徑只計 1 人")]
addp(e, "popup_name", newp("popup_visit_id", "這次打開視窗的編號；每打開一次產生一個，視窗內的事件都帶同一個",
                           "string", "po_2b9x7q", "高"))
prop(e, "alert_id")["sample"] = G("null, ae_5521")
addp(e, "alert_id", newp("referral_id", "轉診編號（只有 notification_tab=referral 時有值，其他 tab 為 null）",
                         "string", "null, rf_301", "高"))
p = prop(e, "alert_type")
p["key"] = G("alert_items")
p["sample"] = R("blood_pressure,ecg（多個用逗號分隔）；代碼：" + VITALS)
prop(e, "alert_level")["pri"] = "高"
prop(e, "alert_level")["pri_tag"] = "R"

# ---- DJY_11 來源篩選
e = ev("DJY_11")
p = prop(e, "filter_type")
p["key"] = G("filter_value")
p["def"] = G("切換後的來源")
addp(e, "popup_name", newp("popup_visit_id", "這次打開視窗的編號；每打開一次產生一個，視窗內的事件都帶同一個",
                           "string", "po_2b9x7q", "高"))
e["note"] = R("filter_type 在其他事件代表「篩選的種類」（例：time_range），這裡選的是「值」，所以改用 filter_value；"
              "選回「全部」要不要送待確認")

# ---- DJY_12 前往列表
e = ev("DJY_12")
e["goal"] = G("紀錄從通知前往各列表的次數")
p = prop(e, "list_type")
p["key"] = G("list_name")
p["sample"] = R("high_risk, abnormal_report, low_risk, custom_plan_unmeasured, doctor_pending（按鈕文字對照見代碼對照表；"
                "醫師的轉診提醒是否也有前往列表按鈕待確認）")
addp(e, "popup_name",
     newp("popup_visit_id", "這次打開視窗的編號；每打開一次產生一個，視窗內的事件都帶同一個", "string", "po_2b9x7q", "高"),
     newp("notification_tab", "點擊時所在的 tab", "string", "alert, referral, tracking", "高"))

# ---- DJY_13 通知卡片點擊
e = ev("DJY_13")
addp(e, None, newp("button_name", "按鈕名稱", "string", "notification_card", "高"))
addp(e, "popup_name",
     newp("popup_visit_id", "這次打開視窗的編號；每打開一次產生一個，視窗內的事件都帶同一個", "string", "po_2b9x7q", "高"),
     newp("notification_tab", "點擊時所在的 tab", "string", "alert, referral, tracking", "高"))
addp(e, "alert_id", newp("referral_id", "轉診編號（只有 notification_tab=referral 時有值，其他 tab 為 null）",
                         "string", "null, rf_301", "高"))
e["note"] = R("同一個彈窗裡有來源篩選、前往列表、通知卡片三種點擊，事件名稱都是 click_button，要靠 button_name 區分，建議保留；"
              "醫師點轉診卡片時要靠 referral_id 串回轉診")

# ---- DJY_14 待處理列表
e = ev("DJY_14")
e["note"] = G("只有一線人員的待處理列表；醫師的「待醫師處理列表」是另一個畫面，見 DJY_43")
p = prop(e, "list_name")
p["def"] = G("進入時所在的列表分頁")
p["sample"] = G("high_risk, abnormal_report, low_risk, custom_plan_unmeasured")

# ---- DJY_16 列表曝光
e = ev("DJY_16")
p = prop(e, "list_name")
p["def"] = R("目前所在的列表分頁（檢測高風險／異常上報／檢測低風險／自訂計劃未測量）")
p["sample"] = G("high_risk, abnormal_report, low_risk, custom_plan_unmeasured")
e["note"] = [e["note"], R("；曝光定義與小鈴鐺通知相同（完整出現在畫面 ≥1 秒）")]

# ---- DJY_17 / DJY_18 列表點擊
e = ev("DJY_17")
e["trig"] = G("點擊列表中的個案列或「查看」按鈕時")
prop(e, "button_name")["sample"] = G("list_row, view_detail")
prop(e, "list_name")["def"] = R("目前所在的列表分頁（檢測高風險／異常上報／檢測低風險／自訂計劃未測量）")
prop(e, "referral_id")["strike"] = True
e["note"] = G("護理師的列表沒有轉診，所以拿掉 referral_id（同 DJY_16）")
e18 = ev("DJY_18")
e18["strike"] = True
e18["note"] = G("團隊已在 DJY_17 用 button_name = list_row、view 區分兩種點擊，本事件重複，建議刪除")

# ---- 待醫師處理列表（團隊新增的黃底列）＋補曝光、點擊
e = ev_by_page("待醫師處理")
e["id"] = R("DJY_43")
e["page"] = "待醫師處理列表"
e["goal"] = R("紀錄醫師進入待醫師處理列表的次數與從哪裡進來")
e["note"] = R("列表項目是轉診（referral_id），不是警報；一線醫師（frontline_doctor）會不會看到這個列表待確認")
e["props"] = [newp("page_name", "頁面名稱", "string", "doctor_pending_list", "高"),
              newp("total_records", "列表的總筆數", "Integer", "{{number}}, e.g. 5", "中"),
              newp("entry_source", "從哪裡進入列表", "string", "nav_menu, notification, workspace", "高")]
e43 = e
insert_ev_after(e43,
    newev("DJY_44", "待醫師處理列表／列表項目", "item_impression", "列表個案完整暴露時",
          "紀錄哪些轉診在待醫師處理列表中被醫師看到，用來算「待醫師處理列表曝光率」",
          "每個項目在同一次瀏覽中只送一次；載入、捲動、翻頁看到的都要送",
          [newp("page_name", "頁面名稱", "string", "doctor_pending_list", "高"),
           newp("referral_id", "轉診編號", "string", "rf_301", "高"),
           newp("patient_id", "個案編號（平台內部編號，不送姓名）", "string", "p_88231", "高"),
           newp("alert_level", "警報等級（列表上有顯示才送，待確認）", "string", "high_risk, low_risk, abnormal_report", "中"),
           newp("position", "第幾個，從 1 開始", "Integer", "{{number}}, e.g. 3", "中")]),
    newev("DJY_45", "待醫師處理列表／列表項目", "click_button", "點擊列表中的個案列或「查看」按鈕時",
          "紀錄醫師從列表點進個案詳情的次數", "",
          [newp("button_name", "按鈕名稱", "string", "list_row, view_detail（按鈕待確認）", "高"),
           newp("page_name", "頁面名稱", "string", "doctor_pending_list", "高"),
           newp("referral_id", "轉診編號", "string", "rf_301", "高"),
           newp("patient_id", "個案編號（平台內部編號，不送姓名）", "string", "p_88231", "高"),
           newp("position", "第幾個，從 1 開始", "Integer", "{{number}}, e.g. 3", "中")]))

# ---- DJY_19 個案詳情
e = ev("DJY_19")
prop(e, "entry_source")["sample"] = R("notification_alert, notification_referral, notification_tracking, pending_list, "
                                      "doctor_pending_list, patient_list, other")
prop(e, "alert_items")["sample"] = R("null, blood_pressure,ecg（代碼同 DJY_02 的 alert_items）")

# ---- DJY_20 Header 頁籤
e = ev("DJY_20")
prop(e, "header tab_name")["key"] = G("tab_name")
prop(e, "is_abnormal_item")["strike"] = True
prop(e, "has_multi_source")["strike"] = True
e["note"] = [e["note"], G("；Header 頁籤沒有單一生理項目，is_abnormal_item、has_multi_source 移到 DJY_46")]

# ---- 生理項目（團隊新增的黃底列）
e = ev_by_page("個案詳情/生理項目")
e["id"] = R("DJY_46")
e["name"] = G("leave_tab")
e["trig"] = R("離開一個生理項目時（切到其他生理項目、其他頁籤、離開個案詳情，或切到其他瀏覽器分頁）")
e["goal"] = R("紀錄每個生理項目看了多久、是不是這次警報（或轉診）的異常項目，了解排查時主要看哪些生理數據")
e["note"] = R("要算停留秒數（duration），必須在「離開」時送，所以事件名稱改成 leave_tab；停留不到 1 秒不送。"
              "如果也要知道點擊次數，可另外加 click_button")
addp(e, None, newp("page_name", "頁面名稱", "string", "patient_detail", "高"),
     newp("patient_id", "個案編號（平台內部編號，不送姓名）", "string", "p_88231", "高"))
prop(e, "has_data")["def"] = G("這個生理項目在目前時間範圍內是否有資料")
prop(e, "metric")["sample"] = G(VITALS)
addp(e, "metric", newp("has_multi_source", "這個生理項目是否同時有 Home 和 Pro 的資料", "boolean", "true, false", "中"))

# ---- DJY_21 待辦事項視窗
e = ev("DJY_21")
e["trig"] = G("待辦事項視窗打開時（進入個案詳情自動跳出，或手動打開）")
e["goal"] = G("紀錄待辦事項視窗被打開的次數，以及是自動跳出還是手動打開")
prop(e, "popup_open types")["key"] = G("open_type")
addp(e, "popup_name", newp("popup_visit_id", "這次打開視窗的編號；每打開一次產生一個，視窗內的事件都帶同一個",
                           "string", "po_2b9x7q", "高"))
addp(e, "patient_id", newp("todo_types", "待辦類型，多個用逗號分隔", "string",
                           "referral_opinion, doctor_advice, follow_up", "中"))
e["note"] = R("關閉時（DJY_23）用 popup_visit_id 串回這次打開；todo_types 用來依待辦類型拆分「待辦資訊再次查看率」")

# ---- 之後尚未討論的段落：生理項目代碼統一
for eid in ("DJY_24", "DJY_25", "DJY_26"):
    prop(ev(eid), "metric")["sample"] = G(VITALS)

# =====================================================================
# 2.5) 依表格順序重新編號（建議刪除的事件不佔編號）
IDMAP = {}
n_ = 0
for e in events:
    old = plain(e["id"])
    if e["strike"]:
        e["id"] = S(old + "（已刪除）")
        continue
    n_ += 1
    new = f"DJY_{n_:02d}"
    IDMAP[old] = new
    if isinstance(e["id"], tuple) and e["id"][0] == "R":
        e["id"] = R(new)
    elif new != old:
        e["id"] = G(new)
ID_RE = re.compile(r"DJY_\d{2}")
for _old in ("DJY_06", "DJY_07", "DJY_09", "DJY_10", "DJY_15", "DJY_18"):  # 團隊刪除或建議刪除的事件
    IDMAP.setdefault(_old, "已刪除事件")


def remap(t):
    return ID_RE.sub(lambda m: IDMAP.get(m.group(0), m.group(0)), t)


def remap_cell(cell):
    v = cell.value
    if isinstance(v, CellRichText):
        changed = False
        for i, b in enumerate(v):
            if isinstance(b, TextBlock):
                nt = remap(b.text)
                if nt != b.text:
                    b.text, changed = nt, True
            elif isinstance(b, str):
                nt = remap(b)
                if nt != b:
                    v[i], changed = nt, True
        return changed
    if isinstance(v, str) and ID_RE.search(v):
        nv = remap(v)
        if nv != v:
            ids = nv.split("、")
            if all(ID_RE.fullmatch(x) for x in ids) and len(ids) > 1:  # 純編號清單：重新排序
                nv = "、".join(sorted(ids, key=lambda x: int(x[4:])))
            cell.value = nv
            return True
    return False


# =====================================================================
# 3) 寫出 DRD
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
ws.column_dimensions["B"].width = 24

EKEYS = [("id", 1), ("page", 2), ("name", 3), ("trig", 4), ("goal", 5), ("note", 11)]
PKEYS = [("key", 6), ("def", 7), ("type", 8), ("sample", 9)]
for n, e in enumerate(events):
    start = ws.max_row + 1
    props = e["props"] or [newp("", "", "", "", "", tag=None)]
    for j, p in enumerate(props):
        r = start + j
        for c in range(1, 12):
            ws.cell(r, c).border, ws.cell(r, c).alignment = BORDER, WRAP
        st = e["strike"] or p["strike"]
        if j == 0:
            for k, c in EKEYS:
                put(ws.cell(r, c), e[k], strike_all=e["strike"] and k != "note")
                if e["ey"].get(k):
                    ws.cell(r, c).fill = YELLOW
        for k, c in PKEYS:
            put(ws.cell(r, c), p[k], strike_all=st)
            if p["y"].get(k):
                ws.cell(r, c).fill = YELLOW
        pri = p["pri"]
        pc = ws.cell(r, 10)
        pc.alignment = CENTER
        if pri in PRI:
            fill, fc = PRI[pri]
            pc.value, pc.fill = pri, fill
            col = RED if p.get("pri_tag") == "R" else (GREEN if st else fc)
            pc.font = Font(name=FONT, size=11, color=col, strike=st)
    end = start + len(props) - 1
    if end > start:
        for c in (1, 2, 3, 4, 5, 11):
            ws.merge_cells(start_row=start, start_column=c, end_row=end, end_column=c)
    if n == 0:
        for c in range(1, 12):
            ws.cell(end, c).border = Border(left=GRID, right=GRID, top=GRID, bottom=DOUBLE)

# =====================================================================
# 4) 代碼對照表：重建（保留團隊內容，標上修改）
wc = wb["代碼對照表"]
crow = []
cur = None
for r in range(2, wc.max_row + 1):
    v = [wc.cell(r, c).value for c in range(1, 6)]
    if v[0]:
        cur = v[0]
    crow.append([cur] + v[1:] + [cur])


def cfind(key, val):
    for x in crow:
        if (plain(x[0]) == key or x[5] == key) and plain(x[1]) == val:
            return x
    raise KeyError((key, val))


def cstrike(key, val):
    x = cfind(key, val)
    x[1:5] = [S(plain(y)) if y else y for y in x[1:5]]


def cset(key, val, col, newv):
    cfind(key, val)[col] = newv


def cadd(after_key, after_val, *rows):
    i = crow.index(cfind(after_key, after_val)) + 1
    crow[i:i] = [[k] + [R(y) if y else y for y in row] + [k] for k, *row in rows]


def crename(old, new):
    for x in crow:
        if x[5] == old:
            x[0] = G(new)


cstrike("page_name", "login")
cset("page_name", "pending_list", 3, G("只有一線人員的待處理列表；醫師的見 doctor_pending_list"))
cset("page_name", "pending_list", 4, G("DJY_14、DJY_16、DJY_17"))
cadd("page_name", "pending_list", ("page_name", "doctor_pending_list", "待醫師處理列表", "醫師專用，列表項目是轉診", "DJY_43、DJY_44、DJY_45"))
cset("page_name", "patient_detail", 4, G("DJY_19、DJY_20、DJY_22、DJY_24、DJY_25、DJY_26、DJY_27、DJY_28、DJY_29、DJY_46"))
cset("popup_name", "notification_center", 3, G("頁面右上角點小鈴鐺打開的「最新通知」彈窗，有異常提醒、轉診提醒、追蹤提醒三個 tab"))
cset("popup_name", "notification_center", 4, G("DJY_42、DJY_08、DJY_11、DJY_12、DJY_13"))
cset("popup_name", "todo_popup", 3, G("進入個案詳情時自動跳出，也可以手動打開"))
cstrike("button_name", "notify_tab_switch")
cstrike("button_name", "list_tab_switch")
cset("button_name", "list_row", 4, G("DJY_17、DJY_45"))
cset("button_name", "view_detail", 3, G("待處理列表、待醫師處理列表每一列右側"))
cset("button_name", "view_detail", 4, G("DJY_17、DJY_45"))
cstrike("tab_name", "vital_blood_pressure")
cstrike("tab_name", "vital_ecg")
for v in ("health_plan", "care_records", "patient_reports"):
    pass
cset("tab_name", "health_plan", 3, R("Header 頁籤；生理項目改用 DJY_46 的 metric"))
crename("list_type", "list_name")
cstrike("list_type", "notification")
for v in ("high_risk", "abnormal_report", "low_risk", "custom_plan_unmeasured"):
    cset("list_type", v, 4, G("DJY_12、DJY_14、DJY_16、DJY_17"))
cset("list_type", "high_risk", 3, R("「前往列表」按鈕上的文字待確認"))
cset("list_type", "doctor_pending", 3, R("只用在小鈴鐺通知的「前往列表」，醫師是否有這個按鈕待確認"))
cset("list_type", "doctor_pending", 4, G("DJY_12"))
cstrike("filter_type", "alert_source")
cstrike("filter_value", "all")
cset("filter_value", "monitor", 3, G("小鈴鐺通知的來源篩選"))
cset("filter_value", "watch", 3, G("小鈴鐺通知的來源篩選"))
crename("notify_tab", "notification_tab")
cset("notify_tab", "abnormal_alert", 4, G("DJY_42、DJY_08、DJY_12、DJY_13"))
cset("notify_tab", "abnormal_alert", 1, G("alert"))
cset("notify_tab", "referral", 4, G("DJY_42、DJY_08、DJY_12、DJY_13"))
cadd("notify_tab", "referral", ("notification_tab", "tracking", "追蹤提醒", "內容與對應角色待確認", "DJY_42、DJY_08、DJY_12、DJY_13"))
cset("entry_source", "nav_menu", 4, G("DJY_14、DJY_43"))
cset("entry_source", "notification", 4, G("DJY_14、DJY_43"))
cset("entry_source", "workspace", 4, G("DJY_14、DJY_43"))
cset("entry_source", "alert_list", 1, G("pending_list"))
cadd("entry_source", "notification",
     ("entry_source", "notification_alert", "小鈴鐺通知｜異常提醒", "", "DJY_19"),
     ("entry_source", "notification_referral", "小鈴鐺通知｜轉診提醒", "", "DJY_19"),
     ("entry_source", "notification_tracking", "小鈴鐺通知｜追蹤提醒", "", "DJY_19"))
for v in ("high_risk", "low_risk", "abnormal_report"):
    cset("alert_level", v, 4, G("DJY_02、DJY_08、DJY_13、DJY_16、DJY_17、DJY_36、DJY_44"))
for v in ("blood_pressure", "ecg", "spo2", "blood_glucose", "heart_rate", "body_temp"):
    cset("metric", v, 4, G("DJY_02、DJY_08、DJY_19、DJY_24、DJY_25、DJY_26、DJY_36、DJY_46"))
cset("metric", "blood_glucose", 3, G("團隊版 DJY_08 寫 blood_sugar，統一用 blood_glucose"))
cadd("metric", "body_temp", ("metric", "weight", "體重", "完整清單待確認", "DJY_02、DJY_08、DJY_19、DJY_24、DJY_25、DJY_26、DJY_36、DJY_46"))
cset("resolve_type", "referral", 2, G("醫師建議（待確認）"))
cset("resolve_type", "referral", 1, G("doctor_advice"))
cset("device_source", "monitor_home", 1, G("home"))
cset("device_source", "monitor_pro", 1, G("pro"))
cstrike("session_start_type", "login")
cstrike("session_start_type", "resume")
cadd("block_name", "ecg_record_list",
     ("open_type", "automatic", "自動跳出", "進入個案詳情時", "DJY_21"),
     ("open_type", "manual", "手動打開", "", "DJY_21"))

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
r = 2
groups = []
for x in crow:
    for c in range(1, 6):
        wc.cell(r, c).border, wc.cell(r, c).alignment = BORDER, WRAP
    for c in range(1, 5):
        put(wc.cell(r, c + 1), x[c] if x[c] is not None else "")
    k = plain(x[0])
    if groups and groups[-1][0] == k:
        groups[-1][2] = r
    else:
        groups.append([k, r, r, x[0]])
    r += 1
for k, a, b, v in groups:
    # 整組都是新增的列 → 紅字；改名 → 綠字
    allnew = all(isinstance(crow[i - 2][1], tuple) and crow[i - 2][1][0] == "R" for i in range(a, b + 1))
    allstrike = all(isinstance(crow[i - 2][1], tuple) and crow[i - 2][1][0] == "S" for i in range(a, b + 1))
    put(wc.cell(a, 1), S(k) if allstrike else (R(k) if allnew else v))
    if b > a:
        wc.merge_cells(start_row=a, start_column=1, end_row=b, end_column=1)

# =====================================================================
# 5) 指標對照：更新事件編號與受影響的說明
wm = wb["指標對照"]
DOC_ROWS = set()
for r in range(2, wm.max_row + 1):
    if str(wm.cell(r, 1).value or "").startswith(("4.0", "5.0", "6.0")):
        DOC_ROWS.add(r)
cur_doc = False
for r in range(2, wm.max_row + 1):
    a = str(wm.cell(r, 1).value or "")
    if a:
        cur_doc = a.startswith(("4.0", "5.0", "6.0"))
    c = wm.cell(r, 6)
    old = c.value
    if not old or not str(old).startswith("DJY"):
        continue
    ids = [x.strip() for x in str(old).split("、")]
    out = []
    for x in ids:
        if x in ("DJY_06", "DJY_07"):
            x = "DJY_01"
        elif x == "DJY_08":
            x = "DJY_42"
        elif x == "DJY_10":
            x = "DJY_08"
        elif x == "DJY_16" and cur_doc:
            x = "DJY_44"
        elif x == "DJY_18":
            continue
        if x not in out:
            out.append(x)
    name = str(wm.cell(r, 2).value or "")
    if "DJY_20" in out and any(k in name for k in ("單一頁籤", "處理前資訊", "檢測儀數據來源", "轉診異常項目")):
        out.insert(out.index("DJY_20") + 1, "DJY_46")
    if cur_doc and "DJY_19" in out and any(k in name for k in ("介入率", "卡關", "各環節")):
        out.append("DJY_45")
    new = "、".join(sorted(out, key=lambda s: int(s.split("_")[1])))
    if new != old:
        put(c, G(new))
        c.alignment = WRAP
# 快捷入口：拿掉空列表（團隊已刪除列表筆數）
for r in range(2, wm.max_row + 1):
    d = wm.cell(r, 4)
    if d.value and "空列表點擊佔比" in str(d.value):
        t = str(d.value)
        i = t.index("、空列表點擊佔比")
        put(d, [t[:i], S("、空列表點擊佔比"), t[i + len("、空列表點擊佔比"):]])
        d.alignment = WRAP
    b = wm.cell(r, 2)
    if b.value and str(b.value).startswith("（前提）") and "上線" in str(b.value):
        e_ = wm.cell(r, 5)
        put(e_, [str(e_.value or ""), R(("；" if e_.value else "") + "「上線」用 session_id 判斷（DJY_01）")])
        e_.alignment = WRAP

# =====================================================================
# 6) 埋點共用規則
wr = wb["埋點共用規則"]
for r in range(2, wr.max_row + 1):
    b = str(wr.cell(r, 2).value or "")
    if b == "每筆事件都要帶":
        put(wr.cell(r, 4), G("user_id、user_role、org_id、event_time、session_id"))
    elif b == "事件時間":
        put(wr.cell(r, 3), G("以 event_time（事件發生當下）為準；時區一律 +08:00；格式待確認"))
    elif b == "page_visit_id":
        for c in (2, 3, 4):
            put(wr.cell(r, c), S(str(wr.cell(r, c).value or "")))
        put(wr.cell(r, 1), wr.cell(r, 1).value or "")
    elif b == "session_id":
        put(wr.cell(r, 3), [str(wr.cell(r, 3).value), G("；「上線」直接用 session_id 判斷：同一個 session_id 的第一筆事件＝上線開始")])
    elif b.startswith("曝光"):
        put(wr.cell(r, 3), [S("項目露出一半以上進入畫面才算"), G("項目完整出現在畫面中、持續 ≥1 秒才算"),
                            "；載入、捲動、翻頁後看到的都要送；同一次瀏覽或打開中，同一筆只送一次",
                            G("；小鈴鐺通知以 patient_id 去重")])
    for c in range(1, 5):
        wr.cell(r, c).alignment = WRAP


# =====================================================================
# 7) 列高
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


# 全部分頁的編號引用同步
for sh in wb.worksheets:
    for row in sh.iter_rows(min_row=2):
        for cell in row:
            if sh.title == "DRD" and cell.column == 1:
                continue
            if cell.value is None:
                continue
            col = cell.font.color.rgb if cell.font and cell.font.color and cell.font.color.type == "rgb" else None
            if remap_cell(cell) and not isinstance(cell.value, CellRichText) and col not in ("00" + RED, "FF" + RED, "00" + GREEN, "FF" + GREEN):
                f = copy.copy(cell.font)
                cell.font = Font(name=f.name or FONT, size=f.sz or 11, color=GREEN, strike=f.strike)
print("ID map:", {k: v for k, v in IDMAP.items() if k != v})
# 檢查：剩下的編號都要是存在的事件
alive = {plain(e["id"]) for e in events}
for sh in wb.worksheets:
    for row in sh.iter_rows(min_row=2):
        for cell in row:
            for m in ID_RE.findall(str(cell.value or "")):
                if m not in alive:
                    print("WARN", sh.title, cell.coordinate, m)

for sh in (wb["DRD"], wb["代碼對照表"], wb["指標對照"], wb["埋點共用規則"]):
    fit_rows(sh)
wb.active = wb.sheetnames.index("DRD")
wb.save(OUT)
print("saved", OUT, len(events), "events")
