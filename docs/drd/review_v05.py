# -*- coding: utf-8 -*-
"""以團隊 review 後的 v0.4（v0.4_review_1）為底，產生 v0.5。
規則：團隊保留的紅字、綠字一律轉黑；團隊保留的刪除線＝確認刪除（直接拿掉）。
本輪：紅字＝補充；綠字＝修改（含錯字、命名、Sample Values 清理）；黃底只留在仍待確認的儲存格。
用法：python3 docs/drd/review_v05.py <v0.4_review_1.xlsx> <out.xlsx>"""
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
                blocks.append(TextBlock(InlineFont(rFont=FONT, sz=11, color=RED if seg[0] == "R" else GREEN), seg[1]))
            elif seg:
                blocks.append(TextBlock(InlineFont(rFont=FONT, sz=11, color="000000"), seg))
        cell.value = CellRichText(blocks)
        cell.font = Font(name=FONT, size=11, color="000000")
        return
    color = "000000"
    if isinstance(v, tuple):
        color = RED if v[0] == "R" else GREEN
        v = v[1]
    cell.value = v if v not in ("", None) else None
    cell.font = Font(name=FONT, size=11, color=color)


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
                                "y": set()})
for e in events:
    e["props"] = [p for p in e["props"] if p["key"] or p["def"]]


def ev(eid):
    return next(e for e in events if e["id"] == eid)


def prop(e, key):
    return next(p for p in e["props"] if plain(p["key"]) == key)


def has(e, key):
    return any(plain(p["key"]) == key for p in e["props"])


def newp(key, d, t, s, pri):
    return {"key": R(key), "def": R(d), "type": R(t), "sample": R(s), "pri": pri, "pri_tag": "R", "y": set()}


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
# 2) Sample Values 統一清理：Sample Values 只放會記在埋點平台上的值，說明一律移到屬性定義或備註
for e in events:
    for p in e["props"]:
        s = plain(p["sample"])
        ns = re.sub(r"[（(][^）)]*[）)]", "", s).strip()
        if ns != s:
            p["sample"] = G(ns)
            p["y"].add("sample") if "待確認" in s else None

# =====================================================================
# 3) 逐事件修改
# ---- DJY_01
e = ev("DJY_01")
p = prop(e, "event_time")
p["type"], p["sample"] = G("Integer"), G("{{timestamp}}, e.g. 1793330000")
p["def"] = G("事件發生的時間（Unix 秒，與 alert_time 同格式）")
p["y"].discard("sample")

# ---- DJY_02 / 03 / 05
e = ev("DJY_02")
p = prop(e, "alert_items")
p["def"] = G("警報的生理項目；多個用逗號分隔、不加空格，例：blood_pressure,ecg")
p["sample"] = G(VITALS)
p["y"].add("sample")
p = prop(e, "alert_time")
p["type"] = G("Integer")
p["def"] = G("警報產生時間（同一個警報編號有多個項目時，取第一個項目的時間；Unix 秒）")
e = ev("DJY_03")
e["note"] = ["由後端記錄；處理人帶在 user_id\n", G("埋在照護記錄或醫師建議提交時")]
prop(e, "resolve_type")["y"].add("sample")
prop(e, "resolve_type")["def"] = ["用什麼方式處理完成（照護", G("記錄"), "、醫師建議）"]
note_add(e, "resolve_type 第二種方式是「醫師建議」還是「轉診」待確認")
ev("DJY_05")["note"] = "由後端記錄；埋在醫師建議提交時"
for eid in ("DJY_03", "DJY_04"):
    if "照護紀錄" in plain(ev(eid)["note"]):
        pass
e = ev("DJY_04")
e["note"] = ["由後端記錄；發起轉診的人帶在 user_id\n埋在照護", G("記錄"), "提交時"]

# ---- DJY_06
e = ev("DJY_06")
e["note"] = G("「小鈴鐺通知」章節的使用率指標都以打開次數為基準")

# ---- DJY_07
e = ev("DJY_07")
prop(e, "alert_id")["def"] = G("警報編號（只有 notification_tab=alert 時有值；轉診、追蹤提醒為 null）")
p = prop(e, "alert_items")
p["def"], p["sample"] = G("警報的生理項目；多個用逗號分隔、不加空格"), G(VITALS)
p["y"].add("sample")
p = prop(e, "patient_id")
p["def"], p["sample"] = G("個案編號（平台內部編號，不送姓名）"), G("p_88231")
reorder(e, ["popup_name", "popup_visit_id", "notification_tab", "exposure_entry", "patient_id", "alert_id",
            "referral_id", "alert_level", "alert_items", "position"])

# ---- DJY_08 來源篩選：與其他篩選一致改成 apply_filter
e = ev("DJY_08")
e["name"] = G("apply_filter")
e["trig"] = G("點擊來源篩選（全部／CoDoctor 檢測儀／CoDoctor Watch）、通知列表更新後")
drop(e, "button_name")
addp(e, "popup_visit_id", newp("filter_type", "篩選類型", "string", "alert_source", "高"))
p = prop(e, "filter_value")
p["def"], p["sample"] = G("切換後的來源"), G("all, monitor, watch")
e["note"] = G("其他篩選（數據來源、時間範圍、心電篩選）都已改成 apply_filter＋filter_type／filter_value，這裡一起統一；選回「全部」時 filter_value = all")

# ---- DJY_09 前往列表
e = ev("DJY_09")
prop(e, "list_name")["def"] = G("要前往的列表")
prop(e, "list_name")["y"].add("sample")
e["note"] = R("按鈕上的實際文字待確認；醫師的「轉診提醒」是否也有前往列表按鈕（doctor_pending）待確認")

# ---- DJY_10
e = ev("DJY_10")
e["note"] = G("同一個彈窗裡有來源篩選、前往列表、通知卡片三種操作，以事件名稱與 button_name 區分；醫師點轉診卡片時以 referral_id 串回轉診")

# ---- DJY_12 / 13
ev("DJY_12")["goal"] = G("紀錄哪些警報在列表中被看到")
ev("DJY_13")["note"] = ""

# ---- DJY_14～16 待醫師處理列表
ev("DJY_14")["y"].add("note")
prop(ev("DJY_15"), "alert_level")["y"].add("def")
e = ev("DJY_16")
prop(e, "button_name")["y"].add("sample")
e["note"] = R("醫師列表上的按鈕名稱待確認")

# ---- DJY_17 個案詳情：task_id → detail_visit_id
e = ev("DJY_17")
p = prop(e, "task_id")
p.update({"key": G("detail_visit_id"),
          "def": G("這次進入個案詳情的編號；每進入一次個案詳情產生一個，離開個案詳情（切換個案、回列表、關閉分頁）或閒置超過 30 分鐘後再操作就換新的；"
                   "個案詳情內的事件（頁籤、篩選、待辦、照護記錄、醫師建議）都帶同一個，用來串起「同一次排查」"),
          "type": R("string"), "sample": R("dv_7f3k2a")})
reorder(e, ["page_name", "patient_id", "detail_visit_id", "entry_source", "alert_id", "referral_id", "alert_items"])
prop(e, "alert_items")["def"] = G("還沒處理的警報項目；多個用逗號分隔，沒有時為 null")
e["note"] = [e["note"], R("；task_id 是「任務」的意思容易誤會，依命名規則（xxx_id 代表某一次的編號）改成 detail_visit_id")]

# ---- DJY_18 Header 頁籤
e = ev("DJY_18")
e["page"] = G("個案詳情／Header 頁籤")
e["trig"] = G("進入一個 Header 頁籤、內容載入完成時")
addp(e, "patient_id", DV())
p = prop(e, "duration")
p["def"] = G("上一個頁籤的停留秒數（剛進入個案詳情時為 null）")
p["y"].add("def")
e["note"] = G("停留不到 1 秒不送；事件改成「進入時送」後，送出當下還不知道這個頁籤會看多久，所以 duration 記的是上一個頁籤；"
              "也可以不送 duration，改用同一個 detail_visit_id 下一筆事件的 event_time 相減（待確認用哪一種）")

# ---- DJY_19 生理項目 tab
e = ev("DJY_19")
e["page"] = G("個案詳情／生理項目 tab")
e["trig"] = G("點擊生理項目 tab、圖表切換完成時")
addp(e, "patient_id", DV())
p = prop(e, "filter_type")
p["def"], p["sample"], p["pri"], p["pri_tag"] = G("篩選類型"), G("vital_item"), "高", "R"
p = prop(e, "filter_value")
p["def"], p["sample"] = G("切換後的生理項目"), G(VITALS)
p["y"].add("sample")
prop(e, "is_abnormal_item")["def"] = G("切換後的生理項目是否是待處理警報或這次轉診的異常項目")
prop(e, "has_data")["def"] = G("切換後的生理項目在目前時間範圍內是否有資料")
p = prop(e, "duration")
p["def"] = G("上一個生理項目的停留秒數（這次進入個案詳情第一次切換時，為預設項目的停留秒數）")
p["y"].add("def")
reorder(e, ["page_name", "patient_id", "detail_visit_id", "filter_type", "filter_value", "is_abnormal_item",
            "has_data", "duration"])
e["note"] = G("filter_type 的值要用英文代碼（vital_item），不能寫中文；停留秒數的算法同 Header 頁籤（待確認）")

DT = lambda: newp("device_type", "生理項目所在的設備區塊（同一個生理項目，例如血壓、心電，檢測儀和 Watch 都有）", "string", "monitor, watch", "高")
addp(ev("DJY_19"), "detail_visit_id", DT())
addp(ev("DJY_24"), "metric", DT())
addp(ev("DJY_25"), "metric", DT())
# 生理項目清單已確認：拿掉黃底
for _e in events:
    for _p in _e["props"]:
        if VITALS in plain(_p["sample"]):
            _p["y"].discard("sample")

# ---- DJY_20 待辦事項視窗
e = ev("DJY_20")
addp(e, "patient_id", DV())
e["note"] = G("手動打開（open_type = manual）就代表「再次查看待辦」；todo_types 用來依待辦類型拆分「待辦資訊再次查看率」")

# ---- DJY_23 數據來源
e = ev("DJY_23")
addp(e, "patient_id", DV())
p = prop(e, "filter_type")
p["pri"], p["pri_tag"] = "高", "R"
p = prop(e, "filter_value")
p["def"] = G("切換後的來源")
p = prop(e, "duration")
p["def"], p["pri"], p["pri_tag"] = G("切換前停留在原本來源的秒數"), "中", "R"
p["y"].add("def")
reorder(e, ["page_name", "patient_id", "detail_visit_id", "filter_type", "filter_value", "duration"])
e["trig"] = G("點擊 Home 或 Pro、圖表切換完成時")

# ---- DJY_24 時間範圍
e = ev("DJY_24")
addp(e, "page_name", newp("patient_id", "個案編號（平台內部編號，不送姓名）", "string", "p_88231", "高"), DV())
prop(e, "filter_value")["def"] = G("切換後的時間範圍")
p = prop(e, "metric")
p["def"], p["sample"] = G("切換時間範圍時正在看的生理項目"), G(VITALS)
p["y"].discard("def")
p["y"].add("sample")
p = prop(e, "total_records")
p["def"], p["pri"], p["pri_tag"] = G("切換後圖表的資料筆數（0 代表這個範圍沒有資料）"), "中", "R"
p["y"].add("def")
p = prop(e, "duration")
p["def"], p["pri"], p["pri_tag"] = G("切換前停留在原本時間範圍的秒數"), "中", "R"
p["y"].add("def")
reorder(e, ["page_name", "patient_id", "detail_visit_id", "filter_type", "filter_value", "metric", "device_type", "total_records", "duration"])
e["trig"] = G("點擊「今日／近 7 天／近 30 天／近 1 年」、圖表更新後")

# ---- DJY_25 自訂日期：清掉重複的 filter_type／filter_value
e = ev("DJY_25")
fv = [p for p in e["props"] if plain(p["key"]) == "filter_value"]
e["props"].remove(fv[0])  # custom_range_confirm 是原本的按鈕名稱，不是篩選值
ft = [p for p in e["props"] if plain(p["key"]) == "filter_type"]
e["props"].remove(ft[1])
addp(e, "page_name", newp("patient_id", "個案編號（平台內部編號，不送姓名）", "string", "p_88231", "高"), DV())
p = prop(e, "metric")
p["def"], p["sample"] = G("切換時間範圍時正在看的生理項目"), G(VITALS)
p["y"].discard("def")
p["y"].add("sample")
p = prop(e, "filter_value")
p["def"] = G("自訂的天數，格式 custom_天數")
p["sample"] = G("custom_{{number}}, e.g. custom_14")
reorder(e, ["page_name", "patient_id", "detail_visit_id", "filter_type", "filter_value", "metric", "device_type"])
e["trig"] = G("在自訂日期選擇器按下「確認」、圖表更新後")
e["note"] = G("原本列了兩次 filter_type／filter_value，其中 custom_range_confirm 是按鈕名稱，已整併成一組")

# ---- DJY_26 心電區塊
e = ev("DJY_26")
addp(e, "page_name", newp("patient_id", "個案編號（平台內部編號，不送姓名）", "string", "p_88231", "高"), DV())
prop(e, "duration")["def"] = G("滑鼠游標停在這個區塊的累計秒數")
prop(e, "block_name")["y"].add("sample")
e["note"] = R("區塊完整清單待確認；累計不到 3 秒的區塊不送")

# ---- 心電圖滾動（團隊新增的黃底列）
e = ev("SCROLL")
e["page"] = G("心電頁籤／心電圖")
e["name"] = G("scroll_chart")
e["trig"] = G("在心電圖上第一次左右滾動（拖曳時間軸）時；同一次進入個案詳情只送一次")
e["goal"] = R("紀錄有沒有滾動心電圖查看更多波形，了解心電圖預設顯示的範圍夠不夠")
e["props"] = [newp("page_name", "頁面名稱", "string", "patient_detail", "高"),
              newp("patient_id", "個案編號（平台內部編號，不送姓名）", "string", "p_88231", "高"),
              DV(),
              newp("block_name", "區塊名稱", "string", "ecg_chart", "高")]
e["note"] = R("事件名稱依命名規則用「動作＋對象類型」（scroll_chart），哪一張圖用 block_name 區分；「是否有滾動」看有沒有這筆事件即可，不需要另外帶 true／false")

# ---- DJY_27 導程篩選
e = ev("DJY_27")
addp(e, "page_name", newp("patient_id", "個案編號（平台內部編號，不送姓名）", "string", "p_88231", "高"), DV())
prop(e, "filter_value")["sample"] = G("lead_1, lead_3, lead_12")
e["note"] = G("Sample Values 會直接記在埋點平台，改用英文代碼：lead_1＝單導、lead_3＝三導、lead_12＝12 導")

# ---- DJY_28 待處理異常篩選
e = ev("DJY_28")
e["page"] = G("心電頁籤／待處理異常篩選")
e["trig"] = G("打開或關閉「待處理異常」篩選、心電紀錄列表更新後")
e["goal"] = G("紀錄使用「待處理異常」篩選的次數")
addp(e, "page_name", newp("patient_id", "個案編號（平台內部編號，不送姓名）", "string", "p_88231", "高"), DV())
prop(e, "filter_type")["sample"] = G("pending_abnormal")
prop(e, "filter_value")["def"] = G("篩選打開或關閉")
e["note"] = G("filter_type 改成 pending_abnormal，直接表達「待處理異常」；on＝打開篩選、off＝關閉篩選")

prop(ev("DJY_17"), "alert_items")["sample"] = G("null, " + VITALS)
prop(ev("DJY_35"), "alert_items")["sample"] = G(VITALS)
prop(ev("DJY_35"), "alert_items")["def"] = G("警報的生理項目；多個用逗號分隔、不加空格")

# ---- DJY_31 照護記錄視窗
e = ev("DJY_31")
addp(e, "patient_id", DV())
p = prop(e, "has_alert")
p["type"], p["def"] = G("boolean"), G("個案目前是否有待處理的警報")
p = prop(e, "duration")
p["key"] = G("duration_from_detail_view")
p["def"] = G("從進入個案詳情到打開這張表單的秒數（打開當下還不知道表單會開多久，所以記的是排查花了多久）")
p["y"].add("def")
prop(e, "alert_id")["def"] = G("這次處理的警報編號；沒有時為 null")
prop(e, "alert_id")["sample"] = G("null, ae_5521")
reorder(e, ["popup_name", "popup_visit_id", "patient_id", "detail_visit_id", "has_alert", "alert_id", "open_seq",
            "duration_from_detail_view"])

# ---- DJY_32 取消／關閉
e = ev("DJY_32")
e["goal"] = G("紀錄打開照護記錄後沒有提交就取消或關閉的次數")
prop(e, "button_name")["sample"] = G("cancel, close")
addp(e, "popup_name",
     newp("popup_visit_id", "這次打開視窗的編號；每打開一次產生一個，視窗內的事件都帶同一個", "string", "po_2b9x7q", "高"),
     DV())
e["note"] = R("要帶 popup_visit_id 才知道關掉的是哪一次打開、哪一筆警報（同 DJY_34、DJY_35）")

# ---- DJY_34 / 35
addp(ev("DJY_34"), "popup_visit_id", DV())
e = ev("DJY_35")
e["trig"] = G("點擊「完成處理」、系統回傳成功結果時")
e["goal"] = G("紀錄照護記錄提交成功的次數與填了多少字（text_length = 0 代表沒有填文字）")
addp(e, "popup_visit_id", DV())
p = prop(e, "alert_level")
p["sample"] = G("high_risk, low_risk, abnormal_report, null")
p["def"] = G("警報等級；沒有警報時為 null")
e["note"] = ["不送填寫內容，只送字數", G("；只在提交成功時送")]

# ---- DJY_36～40 醫師建議
e = ev("DJY_36")
addp(e, "patient_id", DV())
p = prop(e, "duration")
p["key"] = G("duration_from_detail_view")
p["def"] = G("從進入個案詳情到打開這張表單的秒數")
p["y"].add("def")
reorder(e, ["popup_name", "popup_visit_id", "patient_id", "detail_visit_id", "referral_id", "open_seq",
            "duration_from_detail_view"])
e = ev("DJY_37")
e["goal"] = G("紀錄打開醫師建議後沒有提交就取消或關閉的次數")
prop(e, "button_name")["sample"] = G("cancel, close")
addp(e, "popup_visit_id", DV())
addp(ev("DJY_39"), "popup_visit_id", DV())
e = ev("DJY_40")
e["goal"] = G("紀錄醫師建議提交成功的次數與填了多少字（text_length = 0 代表沒有填文字）")
addp(e, "popup_name",
     newp("popup_visit_id", "這次打開視窗的編號；每打開一次產生一個，視窗內的事件都帶同一個", "string", "po_2b9x7q", "高"),
     DV())
p = prop(e, "is_empty")
p["def"] = G("是否所有欄位都沒填就提交（照護記錄 DJY_35 已拿掉這個屬性，兩邊要一致：建議都改用 text_length = 0 判斷，或兩邊都保留）")
p["y"].add("def")
e["note"] = ["不送填寫內容，只送字數", R("；要帶 popup_visit_id 才能和打開視窗串起來算填寫時長")]

for _e in events:  # 生理項目清單已確認：拿掉黃底
    for _p in _e["props"]:
        if VITALS in plain(_p["sample"]):
            _p["y"].discard("sample")

# ---- 時間：用看得懂的日期時間，不用 Unix 秒
UID_EG = "{{string}}, e.g. 3f2b8c1e-9a4d-4e7b-b1c2-5d6e7f8a9b0c"
DT_EG = "{{datetime}}, e.g. 2026-11-05 09:30:12"
for _e in events:
    for _p in _e["props"]:
        k = plain(_p["key"])
        smp = plain(_p["sample"])
        if k == "event_time":
            _p["type"], _p["sample"] = G("string"), G(DT_EG)
            _p["def"] = G("事件發生的日期時間（台灣時間，格式：年-月-日 時:分:秒）")
        elif k == "alert_time":
            _p["type"], _p["sample"] = G("string"), G(DT_EG)
            _p["def"] = G("警報產生的日期時間（同一個警報編號有多個項目時，取第一個項目的時間；格式同 event_time）")
        elif k in ("session_id", "popup_visit_id", "detail_visit_id"):
            _p["sample"] = G(UID_EG)
            d = plain(_p["def"])
            if "亂數" not in d:
                _p["def"] = [_p["def"]] + [G("；由系統自動產生、不會重複的亂數編號")] if not isinstance(_p["def"], list) else _p["def"] + [G("；由系統自動產生、不會重複的亂數編號")]
        elif k in ("user_id", "org_id", "patient_id", "doctor_user_id", "alert_id", "referral_id") and "{{" not in smp:
            parts = [x.strip() for x in smp.split(",")]
            ex = [x for x in parts if x != "null"]
            if ex:
                _p["sample"] = G(("null, " if "null" in parts else "") + "{{string}}, e.g. " + ex[0])

# ---- 屬性排序：全文件統一（後端事件、全域屬性維持原樣）
ORDER = ["button_name", "page_name", "popup_name", "popup_visit_id", "detail_visit_id",
         "patient_id", "alert_id", "referral_id",
         "notification_tab", "exposure_entry", "list_name", "entry_source", "block_name", "open_type", "device_type",
         "filter_type", "filter_value",
         "alert_level", "alert_items", "has_alert", "metric",
         "is_abnormal_item", "has_data", "todo_types",
         "position", "total_records", "open_seq", "has_input", "text_length", "is_empty",
         "duration", "duration_from_detail_view"]
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
    e["id_tag"] = "R" if old == "SCROLL" else ("G" if old != new else None)
IDMAP.update({"DJY_33": IDMAP["DJY_32"], "DJY_38": IDMAP["DJY_37"]})
GONE = {"DJY_21", "DJY_22", "DJY_29", "DJY_30"}
ID_RE = re.compile(r"DJY_\d{2}|SCROLL")


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
            put(ws.cell(r, c), p[k])
            if k in p["y"]:
                ws.cell(r, c).fill = YELLOW
        pc = ws.cell(r, 10)
        pc.alignment = CENTER
        if p["pri"] in PRI:
            fill, fc = PRI[p["pri"]]
            pc.value, pc.fill = p["pri"], fill
            pc.font = Font(name=FONT, size=11, color=RED if p.get("pri_tag") == "R" else fc)
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
KEY_ALIAS = {"metric": "生理項目"}
ZH = {  # 新代碼或需要修改的中文名稱／說明
    ("page_name", "pending_list"): ("待處理列表", "一線人員的待處理列表"),
    ("page_name", "doctor_pending_list"): ("待醫師處理列表", "醫師專用，列表項目是轉診"),
    ("page_name", "patient_detail_health_plan"): ("個案詳情｜健康計畫", "Header 頁籤"),
    ("page_name", "patient_detail_care_records"): ("個案詳情｜處理紀錄", "Header 頁籤"),
    ("page_name", "patient_detail_patient_reports"): ("個案詳情｜個案上報紀錄", "Header 頁籤"),
    ("popup_name", "todo_popup"): ("待辦事項視窗", "進入個案詳情時自動跳出，也可以手動打開"),
    ("button_name", "cancel"): ("「取消」", "照護記錄、醫師建議視窗下方"),
    ("button_name", "close"): ("「×」", "照護記錄、醫師建議視窗右上角"),
    ("button_name", "list_row"): ("個案列", "待處理列表、待醫師處理列表中的每一列"),
    ("list_name", "high_risk"): ("檢測高風險列表", "「前往列表」按鈕上的文字待確認"),
    ("list_name", "doctor_pending"): ("待醫師處理列表", "只用在小鈴鐺通知的「前往列表」，醫師是否有這個按鈕待確認"),
    ("filter_type", "alert_source"): ("小鈴鐺通知的來源篩選", ""),
    ("filter_type", "vital_item"): ("生理項目 tab", "filter_value 用「生理項目」這組代碼"),
    ("filter_type", "pending_abnormal"): ("心電「待處理異常」篩選", ""),
    ("filter_value", "all"): ("全部", "filter_type = alert_source"),
    ("filter_value", "monitor"): ("CoDoctor 檢測儀", "filter_type = alert_source"),
    ("filter_value", "watch"): ("CoDoctor Watch", "filter_type = alert_source"),
    ("filter_value", "home"): ("Home", "filter_type = data_source"),
    ("filter_value", "pro"): ("Pro", "filter_type = data_source"),
    ("filter_value", "today"): ("今日", "filter_type = time_range"),
    ("filter_value", "last_7d"): ("近 7 天", "filter_type = time_range"),
    ("filter_value", "last_30d"): ("近 30 天", "filter_type = time_range（預設）"),
    ("filter_value", "last_1y"): ("近 1 年", "filter_type = time_range"),
    ("filter_value", "custom_{{number}}"): ("自訂日期", "filter_type = time_range；custom_ 加天數，例：custom_14 代表 14 天"),
    ("filter_value", "lead_1"): ("單導", "filter_type = ecg_lead"),
    ("filter_value", "lead_3"): ("三導", "filter_type = ecg_lead"),
    ("filter_value", "lead_12"): ("12 導", "filter_type = ecg_lead"),
    ("filter_value", "on"): ("打開篩選", "filter_type = pending_abnormal"),
    ("filter_value", "off"): ("關閉篩選", "filter_type = pending_abnormal"),
    ("notification_tab", "tracking"): ("追蹤提醒", "內容與對應角色待確認"),
    ("exposure_entry", "notification"): ("小鈴鐺通知", "固定帶這個值"),
    ("生理項目", "blood_pressure"): ("血壓", "檢測儀、Watch 都有；alert_items、metric、filter_value（vital_item）共用這組代碼，哪一種設備看 device_type"),
    ("生理項目", "ecg"): ("心電", "檢測儀、Watch 都有"),
    ("生理項目", "spo2"): ("血氧", "檢測儀"),
    ("生理項目", "body_temp"): ("體溫", "檢測儀"),
    ("生理項目", "news2_score"): ("NEWS2 評分", "檢測儀"),
    ("生理項目", "blood_glucose"): ("血糖", "檢測儀"),
    ("生理項目", "uric_acid"): ("尿酸", "檢測儀"),
    ("生理項目", "total_cholesterol"): ("總膽固醇", "檢測儀"),
    ("生理項目", "body_fat"): ("體脂", "檢測儀"),
    ("生理項目", "multi_vitals"): ("多合一徵象", "Watch"),
    ("生理項目", "hrv"): ("心率變異性", "Watch"),
    ("生理項目", "sleep"): ("睡眠", "Watch"),
    ("生理項目", "exercise"): ("運動", "Watch"),
    ("生理項目", "steps"): ("步數", "Watch"),
    ("device_type", "monitor"): ("CoDoctor 檢測儀", "生理項目 tab 所在的設備區塊"),
    ("device_type", "watch"): ("CoDoctor Watch", "生理項目 tab 所在的設備區塊"),
    ("resolve_type", "doctor_advice"): ("醫師建議", "待確認"),
    ("block_name", "ecg_summary"): ("心電摘要", "區塊完整清單待確認"),
    ("todo_types", "doctor_message"): ("醫師留言", "原本的 doctor_advice 改名，避免和 resolve_type 的 doctor_advice 混淆"),
    ("open_type", "automatic"): ("自動跳出", "進入個案詳情時"),
    ("open_type", "manual"): ("手動打開", ""),
}
ENUM_KEYS = ["user_role", "page_name", "popup_name", "button_name", "list_name", "notification_tab", "exposure_entry",
             "entry_source", "filter_type", "filter_value", "alert_level", "生理項目", "device_type", "resolve_type", "device_source",
             "block_name", "todo_types", "open_type"]
VSET = set(VITALS.split(", "))
codes = {}  # (key, value) -> set(event ids)
for e in events:
    ftype = next((plain(p["sample"]) for p in e["props"] if plain(p["key"]) == "filter_type"), "")
    for p in e["props"]:
        k, s = plain(p["key"]), plain(p["sample"])
        if k in ("alert_items", "metric") or (k == "filter_value" and ftype == "vital_item"):
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
        old_key = next((kk for kk in (k, "metric") if (kk, v) in old_rows and KEY_ALIAS.get(kk, kk) == k), None)
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
    put(wc.cell(a, 1), k if k in OLD_KEYS or k == "生理項目" else R(k))
    if b > a:
        wc.merge_cells(start_row=a, start_column=1, end_row=b, end_column=1)

# =====================================================================
# 7) 指標對照：舊顏色轉黑、拿掉刪除線段落，再同步編號與受影響的算法
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


def mset(name, col, v):
    put(wm.cell(mrow(name), col), v)


cur_doc = False
for r in range(2, wm.max_row + 1):
    a = str(wm.cell(r, 1).value or "")
    if a:
        cur_doc = a.startswith(("4.0", "5.0", "6.0"))
    c = wm.cell(r, 6)
    old = str(c.value or "")
    if not old.startswith("DJY"):
        continue
    ids = []
    for x in [x.strip() for x in old.split("、")]:
        if x in GONE:
            continue
        y = IDMAP.get(x, x)
        if y not in ids:
            ids.append(y)
    new = "、".join(sorted(ids, key=lambda s: int(s[4:])))
    put(c, new if new == remap_text(old) or set(new.split("、")) == {IDMAP.get(x, x) for x in old.split("、")} else G(new))
# 受影響的指標
mset("② 待辦資訊再次查看率", 4, G("有手動打開待辦（open_type = manual）的詳情訪問數 ÷ 有自動跳出待辦（open_type = automatic）的詳情訪問數"))
mset("② 待辦資訊再次查看率", 6, G(IDMAP["DJY_20"]))
mset("④ 待辦資訊再次查看率（醫師）", 6, G(IDMAP["DJY_20"]))
mset("② 歷史處理紀錄查看率", 4, G("有查看「處理紀錄」頁籤（停留 ≥5 秒）的詳情訪問數 ÷ 受轉診醫師進入、且個案有處理紀錄的詳情訪問數；另看查看是在寫建議之前或之後"))
mset("② 歷史處理紀錄查看率", 6, G("、".join([IDMAP["DJY_17"], IDMAP["DJY_18"], IDMAP["DJY_40"]])))
mset("① 檢測儀數據來源切換率", 4, G("有切換 Home／Pro 的不重複護理師 ÷ 有查看生理項目的不重複護理師；另計：以詳情訪問為單位的切換率"))
mset("① 檢測儀數據來源切換率", 5, G("同一個人只算一次"))
mset("③ 心電區塊觸及率", 4, G("各區塊觸及率＝該區塊滑鼠游標停留累計 ≥3 秒的心電頁籤訪問數 ÷ 心電頁籤訪問數；另看各區塊停留秒數的中位數"))
mset("⑤ 照護記錄空提交率", 4, G("沒有填文字（text_length = 0）的成功提交數 ÷ 成功提交數"))
mset("⑦ 處理結果類型分布", 2, G("⑦ 處理結果類型分布（不埋點）"))
mset("⑦ 處理結果類型分布", 3, G("—"))
mset("⑦ 處理結果類型分布", 4, G("照護記錄沒有欄位能區分誤報／真異常，DRD 已拿掉 result_type，本次不埋點"))
mset("⑦ 處理結果類型分布", 6, G("—"))
mset("⑦ 處理結果類型分布", 7, G("—"))
r6 = mrow("③ 異常排查時長")
put(wm.cell(r6, 4), G("照護記錄打開時帶的 duration_from_detail_view（從進入個案詳情到第一次打開照護記錄的秒數）"))
# 新增：心電圖滾動率（接在 2.1 最後一列）
ins = mrow("⑥ 功能使用對排查時長的影響") + 1
merges = [(m.min_row, m.min_col, m.max_row, m.max_col) for m in wm.merged_cells.ranges]
for m in list(wm.merged_cells.ranges):
    wm.unmerge_cells(str(m))
heights = {r: wm.row_dimensions[r].height for r in range(1, wm.max_row + 1)}
wm.insert_rows(ins)
for (a, b, c2, d) in merges:
    if a >= ins:
        a, c2 = a + 1, c2 + 1
    elif c2 >= ins:
        c2 += 1
    wm.merge_cells(start_row=a, start_column=b, end_row=c2, end_column=d)
newm = ["", R("⑦ 心電圖滾動率"), R("輔助判讀／訪問"),
        R("有滾動心電圖的心電頁籤訪問數 ÷ 心電頁籤訪問數"),
        R("同一次個案詳情瀏覽只算一次；用來判斷心電圖預設顯示的範圍夠不夠"),
        R("、".join([IDMAP["DJY_18"], IDMAP["SCROLL"]])),
        R("1. 低（≤50%）：很少需要滾動 → 預設顯示範圍大致足夠，維持現有設計\n2. 高（≥51%）：經常需要滾動看更多波形 → 評估加大預設顯示範圍或提供縮放")]
for c, v in enumerate(newm, 1):
    cell = wm.cell(ins, c)
    if c > 1:
        put(cell, v)
    cell.alignment, cell.border = WRAP, BORDER

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
    if nm not in used_names and nm != "所有事件":
        used_names.append(nm)
front = [x for x in used_names if not x.startswith(("alert_", "referral_"))]
rules = []
for a, b, c, d in old_rules:
    row = [a, b, c, d]
    if b == "事件名稱":
        row[3] = G("、".join(front))
    elif b == "事件時間":
        row[2] = G("以 event_time（事件發生當下的日期時間，台灣時間）為準；格式：年-月-日 時:分:秒")
        row[3] = G("2026-11-05 09:30:12")
    elif b == "停留秒數 duration":
        row[2] = [c, R("；duration_from_<起點> 代表從某個起點到這個事件的秒數，例：duration_from_detail_view＝從進入個案詳情到打開表單")]
        row[3] = [d, R("、duration_from_detail_view: 95")]
    elif b in ("popup_visit_id", "session_id"):
        row[2] = [c, G("；由系統自動產生、不會重複的亂數編號")]
        row[3] = G("3f2b8c1e-9a4d-4e7b-b1c2-5d6e7f8a9b0c")
    elif b == "離開類事件":
        row[3] = G("leave_page")
    elif b == "提交類事件":
        row[2] = G("只在系統回傳成功後送；失敗、前端欄位檢核沒通過、沒有呼叫系統時都不送")
    rules.append(row)
    if b == "session_id":
        rules.append([a, R("detail_visit_id"), R("每進入一次個案詳情產生一個新的；離開個案詳情或閒置超過 30 分鐘後再操作就換新的；個案詳情內的事件（頁籤、篩選、待辦、照護記錄、醫師建議）都帶同一個；由系統自動產生、不會重複的亂數編號"),
                      R("3f2b8c1e-9a4d-4e7b-b1c2-5d6e7f8a9b0c")])
    if b == "格式" or b == "空值":
        pass
rules.insert(next(i for i, x in enumerate(rules) if x[1] == "布林值與數字") + 1,
             ["格式", R("Sample Values"), R("只寫會記在埋點平台上的值：列舉值寫完整清單（用「, 」分隔），其他寫 {{string}}／{{number}}／{{seconds}}／{{datetime}} 加一個例子；不寫中文說明，說明放在屬性定義或備註"),
              R("lead_1, lead_3, lead_12")])
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

# Person Properties：舊顏色轉黑
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
