# -*- coding: utf-8 -*-
"""產生「大家醫平台 埋點 DRD」Excel（版型參照「範例_數據埋點需求表」）。
修改內容後重新執行：python3 docs/drd/build_dajiayi_drd.py"""
import os
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "大家醫平台_埋點DRD_v0.3.xlsx")

# ---- 樣式（照範例檔：Calibri 11、深綠標題列、優先級用 Excel 內建「壞／中性／好」配色）
FONT = "Calibri"
HEAD_FILL = PatternFill("solid", fgColor="375623")
HEAD_FONT = Font(name=FONT, size=12, color="FFFFFF")
BODY_FONT = Font(name=FONT, size=11, color="000000")
PRI = {
    "高": (PatternFill("solid", fgColor="FFC7CE"), Font(name=FONT, size=11, color="9C0006")),
    "中": (PatternFill("solid", fgColor="FFEB9C"), Font(name=FONT, size=11, color="9C5700")),
    "低": (PatternFill("solid", fgColor="C6EFCE"), Font(name=FONT, size=11, color="006100")),
}
GRID = Side(style="thin", color="D9D9D9")
DOUBLE = Side(style="double", color="000000")
CELL_BORDER = Border(left=GRID, right=GRID, top=GRID, bottom=GRID)
WRAP = Alignment(wrap_text=True, vertical="center")
CENTER = Alignment(horizontal="center", vertical="center")
NUM = "{{number}}, e.g. "

# =====================================================================
# 共用屬性（固定字串）：key -> (屬性定義, Data Type, Sample Values, 優先級)
# 同一個意思全文件只用一個 key；事件內可用 (key, 範例覆寫, 定義覆寫, 優先級覆寫)
# =====================================================================
P = {
    # 全域
    "user_id": ("做這個動作的使用者帳號", "string", "u_10293", "高"),
    "user_role": ("使用者的角色", "string", "org_admin, admin, doctor, frontline_doctor, frontline_staff", "高"),
    "org_id": ("使用者目前所在的機構", "string", "org_001", "高"),
    "session_id": ("這次上線的編號；登入或閒置後重新操作時換新的", "string", "ss_9k3m2p", "高"),
    "page_visit_id": ("這次進入頁面的編號；每進入一個頁面產生一個，頁面內的事件都帶同一個", "string", "pv_5h2k8m", "高"),
    "platform_version": ("平台版本號", "string", "7.0.3", "中"),
    # 頁面、視窗、按鈕
    "page_name": ("頁面名稱", "string", "patient_detail", "高"),
    "popup_name": ("視窗名稱", "string", "notification_center", "高"),
    "popup_visit_id": ("這次打開視窗的編號；每打開一次產生一個，視窗內的事件都帶同一個", "string", "po_2b9x7q", "高"),
    "button_name": ("按鈕名稱", "string", "", "高"),
    "entry_source": ("從哪裡進來", "string", "nav_menu, notification, alert_list, doctor_pending_list, patient_list", "高"),
    "position": ("第幾個，從 1 開始", "Integer", "{{number}}, e.g. 3", "中"),
    "total_records": ("資料筆數", "Integer", "{{number}}, e.g. 12", "中"),
    "duration": ("停留秒數", "Integer", "{{seconds}}, e.g. 8", "高"),
    # 個案、警報、轉診
    "patient_id": ("個案編號（平台內部編號，不送姓名）", "string", "p_88231", "高"),
    "alert_id": ("警報編號；同一個案還沒處理完的多筆警報算同一個；沒有時為 null", "string", "null, ae_5521", "高"),
    "referral_id": ("轉診編號；沒有時為 null", "string", "null, rf_301", "高"),
    "alert_level": ("警報等級", "string", "high_risk, low_risk, abnormal_report", "高"),
    "alert_items": ("警報的生理項目，多個用逗號分隔", "string", "blood_pressure,ecg", "中"),
    "list_type": ("列表類型", "string", "notification, high_risk, abnormal_report, low_risk, custom_plan_unmeasured, doctor_pending", "高"),
    # 篩選
    "filter_type": ("篩選類型", "string", "alert_source, data_source, time_range, ecg_lead, ecg_abnormal", "高"),
    "filter_value": ("選擇的篩選值", "string", "", "高"),
    # 個案詳情
    "metric": ("生理項目", "string", "blood_pressure, ecg, spo2, blood_glucose, heart_rate, body_temp", "高"),
    "tab_name": ("頁籤名稱", "string", "health_plan, care_records, patient_reports, vital_blood_pressure, vital_ecg", "高"),
    "tabs_with_data": ("有資料的頁籤，多個用逗號分隔", "string", "health_plan,care_records", "高"),
    "has_data": ("該頁籤是否有資料", "boolean", "true, false", "高"),
    "is_abnormal_item": ("這個生理項目是否是待處理警報或這次轉診的異常項目", "boolean", "true, false", "高"),
    "has_multi_source": ("這個生理項目是否同時有 Home 和 Pro 的資料", "boolean", "true, false", "中"),
    "todo_types": ("待辦類型，多個用逗號分隔", "string", "referral_opinion, doctor_advice, follow_up", "中"),
    "block_name": ("區塊名稱", "string", "ecg_summary, ecg_chart, ecg_record_list", "高"),
    # 表單
    "open_seq": ("同一筆警報（或轉診）第幾次打開這張表單，1 是第一次", "Integer", "{{number}}, e.g. 1", "高"),
    "has_input": ("離開時是否已經填了內容", "boolean", "true, false", "中"),
    "result": ("結果", "string", "success, fail", "高"),
    "error_code": ("失敗時的錯誤代碼；成功時為 null", "string", "null, E4001", "中"),
    "is_empty": ("是否所有欄位都沒填就提交", "boolean", "true, false", "高"),
    "text_length": ("文字欄位的字數（只送字數，不送內容）", "Integer", "{{number}}, e.g. 42", "高"),
    "result_type": ("處理結果是誤報還是真的異常", "string", "false_alarm, handled, null", "中"),
    # 其他
    "session_start_type": ("這次上線是怎麼開始的", "string", "login, resume", "中"),
    "notify_tab": ("通知分頁", "string", "abnormal_alert, referral", "高"),
    "device_source": ("產生警報的量測設備", "string", "monitor_home, monitor_pro, watch", "中"),
    "resolve_type": ("用什麼方式處理完成", "string", "care_record, referral", "高"),
    "doctor_user_id": ("被轉診的醫師帳號", "string", "u_20011", "高"),
}

# =====================================================================
# 事件：(頁面/區塊, 事件名稱, 觸發時機, 目標/數據分析意義, [屬性], 備註)
# 一個事件只寫一個觸發動作；全域屬性（DJY_01）每筆事件都會帶，不重複列
# =====================================================================
POP = lambda name: [("popup_name", name), "popup_visit_id"]
E = [
    ("Global property 全域屬性", "所有事件", "每一筆事件發送時帶入",
     "紀錄每筆事件是誰、什麼角色、在哪個機構、哪一次上線、哪一次頁面瀏覽發生的",
     ["user_id", "user_role", "org_id", "session_id", "page_visit_id", "platform_version"],
     "分析時排除機構管理員（org_admin）與管理員（admin）；事件時間以系統收到的時間為準"),
    # ---- 後端
    ("後端（系統）", "alert_created", "系統判定數據異常、產生警報時",
     "紀錄每一筆警報的產生時間與內容",
     ["alert_id", "patient_id", "alert_level", "alert_items", "device_source"],
     "由後端記錄；同一個案還沒處理完時，新的警報項目併入原本的警報編號"),
    ("後端（系統）", "alert_resolved", "警報處理完成、從待處理移除時",
     "紀錄警報何時、由誰、用什麼方式處理完成",
     ["alert_id", "patient_id", "resolve_type"], "由後端記錄；處理人帶在 user_id"),
    ("後端（系統）", "referral_created", "護理師送出轉診、系統產生轉診紀錄時",
     "紀錄每一筆轉診的產生時間與被轉診的醫師",
     ["referral_id", "alert_id", "patient_id", "doctor_user_id"], "由後端記錄；發起轉診的人帶在 user_id"),
    ("後端（系統）", "referral_resolved", "醫師送出醫師建議、轉診標記為已處理時",
     "紀錄轉診何時處理完成",
     ["referral_id", "patient_id"], "由後端記錄"),
    # ---- 上線
    ("登入", "session_start", "登入成功時",
     "紀錄每次上線的時間，用來判斷警報產生後有沒有人上線、上線後多久看到",
     [("session_start_type", "login"), ("page_name", "login")], ""),
    ("平台全域", "session_start", "閒置超過 30 分鐘後，再次操作平台時",
     "紀錄閒置後重新上線的時間",
     [("session_start_type", "resume"), "page_name"], "閒置 30 分鐘的定義請產品確認"),
    # ---- 小鈴鐺通知
    ("小鈴鐺通知", "view_popup", "點擊小鈴鐺、通知視窗顯示完成時",
     "紀錄打開小鈴鐺通知的次數，與打開當下有多少未讀",
     POP("notification_center") + ["notify_tab", ("total_records", "{{number}}, e.g. 12", "打開當下的未讀數量")], ""),
    ("小鈴鐺通知／分頁", "click_button", "點擊「異常提醒」或「轉診提醒」分頁時",
     "紀錄切換通知分頁的次數",
     [("button_name", "notify_tab_switch")] + POP("notification_center") + [("notify_tab", "abnormal_alert, referral", "切換後的分頁")], ""),
    ("小鈴鐺通知／通知卡片", "item_impression", "通知卡片露出一半以上進入畫面時",
     "紀錄哪些警報、轉診在小鈴鐺通知中被看到",
     POP("notification_center") + [("list_type", "notification"), "alert_id", "referral_id", "patient_id", "alert_level", "position"],
     "每張卡片在同一次打開中只送一次"),
    ("小鈴鐺通知／來源篩選", "click_button", "點擊來源篩選（全部／CoDoctor 檢測儀／CoDoctor Watch）時",
     "紀錄依設備篩選通知的次數",
     [("button_name", "alert_source_filter")] + POP("notification_center") + [("filter_type", "alert_source"), ("filter_value", "all, monitor, watch")], ""),
    ("小鈴鐺通知／前往列表", "click_button", "點擊「前往○○列表」按鈕時",
     "紀錄從通知前往各列表的次數，以及是否點到空列表",
     [("button_name", "goto_list")] + POP("notification_center") + [("list_type", "high_risk, abnormal_report, custom_plan_unmeasured, low_risk", "要前往的列表"), ("total_records", "{{number}}, e.g. 0", "點擊當下該列表的筆數；0 代表空列表")], ""),
    ("小鈴鐺通知／通知卡片", "click_button", "點擊通知卡片時",
     "紀錄從通知點進個案詳情的次數，以及點的是哪一筆警報或轉診",
     [("button_name", "notification_card")] + POP("notification_center") + ["alert_id", "referral_id", "patient_id", "alert_level", "position"], ""),
    # ---- 待處理列表
    ("待處理列表", "view_page", "待處理列表畫面載入完成時",
     "紀錄進入待處理列表的次數與從哪裡進來",
     [("page_name", "pending_list"), "list_type", ("total_records", "{{number}}, e.g. 37", "列表的總筆數"), "entry_source"],
     "醫師的「待醫師處理列表」也用這個事件（list_type = doctor_pending）"),
    ("待處理列表／列表分頁", "click_button", "點擊列表分頁（檢測高風險／異常上報／檢測低風險等）時",
     "紀錄切換列表分頁的次數",
     [("button_name", "list_tab_switch"), ("page_name", "pending_list"), ("list_type", "high_risk, abnormal_report, low_risk, custom_plan_unmeasured", "切換後的列表")], ""),
    ("待處理列表／列表項目", "item_impression", "列表項目露出一半以上進入畫面時",
     "紀錄哪些警報、轉診在列表中被看到",
     [("page_name", "pending_list"), "list_type", "alert_id", "referral_id", "patient_id", "alert_level", "position"],
     "每個項目在同一次瀏覽中只送一次；載入、捲動、翻頁看到的都要送"),
    ("待處理列表／列表項目", "click_button", "點擊列表中的個案列時",
     "紀錄從列表點進個案詳情的次數",
     [("button_name", "list_row"), ("page_name", "pending_list"), "list_type", "alert_id", "referral_id", "patient_id", "alert_level", "position"], ""),
    ("待處理列表／查看按鈕", "click_button", "點擊列表中的「查看」按鈕時",
     "紀錄從列表點進個案詳情的次數",
     [("button_name", "view_detail"), ("page_name", "pending_list"), "list_type", "alert_id", "referral_id", "patient_id", "alert_level", "position"], ""),
    # ---- 個案詳情
    ("個案詳情", "view_page", "個案詳情畫面載入完成時",
     "紀錄進入個案詳情的次數、從哪裡進來，以及個案當下有沒有待處理的警報或轉診",
     [("page_name", "patient_detail"), "patient_id", "entry_source",
      ("alert_id", "null, ae_5521", "個案目前還沒處理的警報編號；沒有時為 null"), ("referral_id", "null, rf_301", "個案目前還沒處理的轉診編號；沒有時為 null"),
      ("alert_items", "null, blood_pressure,ecg", "還沒處理的警報項目；沒有時為 null"), "tabs_with_data"],
     "不論從哪裡進來，都要帶警報與轉診編號"),
    ("個案詳情／頁籤", "leave_tab", "離開一個頁籤時（切到其他頁籤、離開個案詳情、或切到其他瀏覽器分頁）",
     "紀錄每個頁籤看了多久，了解排查時主要看哪些資訊",
     [("page_name", "patient_detail"), "patient_id", "tab_name", "metric", "has_data", "is_abnormal_item", "has_multi_source", "duration"],
     "停留不到 1 秒不送；頁籤完整清單請設計確認"),
    ("個案詳情／待辦事項視窗", "view_popup", "進入個案詳情、待辦事項視窗自動跳出時",
     "紀錄待辦事項視窗自動跳出的次數",
     POP("todo_popup") + ["patient_id", "todo_types"], ""),
    ("個案詳情／待辦區塊", "click_button", "點擊「全部內容」再次打開待辦事項時",
     "紀錄主動再次查看待辦內容的次數",
     [("button_name", "todo_view_all"), ("page_name", "patient_detail"), "patient_id", "todo_types"], ""),
    ("個案詳情／待辦事項視窗", "close_popup", "關閉待辦事項視窗時",
     "紀錄待辦事項視窗看了多久",
     POP("todo_popup") + ["duration"], ""),
    ("檢測儀頁籤／數據來源", "click_button", "點擊 Home 或 Pro 切換數據來源時",
     "紀錄切換檢測儀數據來源的次數",
     [("button_name", "data_source_switch"), ("page_name", "patient_detail"), "patient_id", "metric", ("filter_type", "data_source"), ("filter_value", "home, pro", "切換後的來源")], ""),
    ("個案詳情／時間範圍", "click_button", "點擊「今日／近 7 天／近 30 天／近 1 年」時",
     "紀錄切換時間範圍的次數與最常選的區間",
     [("button_name", "time_range"), ("page_name", "patient_detail"), "metric", ("filter_type", "time_range"), ("filter_value", "today, last_7d, last_30d, last_1y")], "預設為近 30 天"),
    ("個案詳情／自訂日期", "click_button", "在自訂日期選擇器按下「確認」時",
     "紀錄使用自訂日期的次數與天數",
     [("button_name", "custom_range_confirm"), ("page_name", "patient_detail"), "metric", ("filter_type", "time_range"), ("filter_value", "custom_14", "自訂的天數（custom_天數）")], ""),
    ("心電頁籤／各區塊", "view_block", "離開心電頁籤時，每個區塊各送一筆",
     "紀錄心電頁每個區塊被看了多久",
     [("page_name", "patient_detail"), "block_name", ("duration", "{{seconds}}, e.g. 12", "區塊露出一半以上的累計秒數")], "累計不到 3 秒的區塊不送；區塊清單請設計確認"),
    ("心電頁籤／導程篩選", "apply_filter", "選擇導程、心電紀錄列表更新後",
     "紀錄使用導程篩選的次數",
     [("page_name", "patient_detail"), ("filter_type", "ecg_lead"), ("filter_value", "I, II, III"), ("total_records", "{{number}}, e.g. 6", "篩選後的筆數", "低")], ""),
    ("心電頁籤／異常篩選", "apply_filter", "選擇異常條件、心電紀錄列表更新後",
     "紀錄使用異常篩選的次數",
     [("page_name", "patient_detail"), ("filter_type", "ecg_abnormal"), ("filter_value", "af, pvc"), ("total_records", "{{number}}, e.g. 6", "篩選後的筆數", "低")], "異常條件完整清單請設計確認"),
    ("處理紀錄頁籤／紀錄詳情", "view_popup", "點擊單筆處理紀錄、詳情顯示時",
     "紀錄查看過往處理紀錄的次數，以及看的是第幾筆",
     POP("care_record_detail") + ["patient_id", ("position", "{{number}}, e.g. 1", "點的是第幾筆紀錄，最新的是 1")], ""),
    ("處理紀錄頁籤／紀錄詳情", "close_popup", "關閉處理紀錄詳情時",
     "紀錄處理紀錄看了多久",
     POP("care_record_detail") + ["duration"], ""),
    # ---- 照護記錄
    ("照護記錄視窗", "view_popup", "點擊「撰寫照護記錄」、視窗顯示完成時",
     "紀錄打開照護記錄的次數",
     POP("care_record_form") + ["patient_id", ("alert_id", "ae_5521", "這次處理的警報編號"), "open_seq"],
     "第幾次打開（open_seq）若前端無法跨頁面累計，可改由後端記錄"),
    ("照護記錄視窗", "click_button", "點擊「取消」時",
     "紀錄打開照護記錄後沒有提交就取消的次數",
     [("button_name", "cancel")] + POP("care_record_form") + ["has_input", "duration"], ""),
    ("照護記錄視窗", "click_button", "點擊右上角「×」關閉時",
     "紀錄打開照護記錄後沒有提交就關閉的次數",
     [("button_name", "close")] + POP("care_record_form") + ["has_input", "duration"], ""),
    ("照護記錄視窗", "leave_page", "照護記錄視窗開著時，直接離開頁面、切換個案或重新整理時",
     "紀錄沒有提交也沒有關閉就離開的次數",
     POP("care_record_form") + ["has_input", "duration"], ""),
    ("照護記錄視窗", "submit_form", "點擊「完成處理」、系統回傳結果時",
     "紀錄照護記錄提交成功或失敗、是否空白提交、填了多少字",
     POP("care_record_form") + ["alert_id", "alert_level", "alert_items", "open_seq", "result", "error_code", "is_empty", "text_length", "result_type", "duration"],
     "不送填寫內容，只送字數；result_type 需確認照護記錄是否有欄位能區分誤報"),
    # ---- 醫師建議
    ("醫師建議視窗", "view_popup", "點擊「醫師建議」、視窗顯示完成時",
     "紀錄打開醫師建議的次數",
     POP("doctor_advice_form") + ["patient_id", ("referral_id", "rf_301", "這次處理的轉診編號"), "open_seq"], ""),
    ("醫師建議視窗", "click_button", "點擊「取消」時",
     "紀錄打開醫師建議後沒有提交就取消的次數",
     [("button_name", "cancel")] + POP("doctor_advice_form") + ["has_input", "duration"], ""),
    ("醫師建議視窗", "click_button", "點擊右上角「×」關閉時",
     "紀錄打開醫師建議後沒有提交就關閉的次數",
     [("button_name", "close")] + POP("doctor_advice_form") + ["has_input", "duration"], ""),
    ("醫師建議視窗", "leave_page", "醫師建議視窗開著時，直接離開頁面、切換個案或重新整理時",
     "紀錄沒有提交也沒有關閉就離開的次數",
     POP("doctor_advice_form") + ["has_input", "duration"], ""),
    ("醫師建議視窗", "submit_form", "點擊「完成處理」、系統回傳結果時",
     "紀錄醫師建議提交成功或失敗、是否空白提交、填了多少字",
     POP("doctor_advice_form") + ["referral_id", "open_seq", "result", "error_code", "is_empty", "text_length", "duration"],
     "不送填寫內容，只送字數"),
]

# =====================================================================
# Person Properties（照使用者提供的範本欄位）
# =====================================================================
PP = [
    ("使用者身分", "user_id", "u_12345abc", "string", "每個帳號的唯一編號", "登入成功時設定", "登出時清空", "串起同一個人的所有行為", "高", "規劃中"),
    ("使用者身分", "user_role", "org_admin / admin / doctor / frontline_doctor / frontline_staff", "string", "帳號角色：機構管理員、管理員、醫師、一線醫師、一線人員", "登入成功時設定；角色變更時更新", "登出時清空", "排除管理員帳號；區分一線人員與醫師的行為", "高", "規劃中"),
    ("機構", "org_id", "org_001", "string", "目前所在的機構", "登入後取得機構時設定；切換機構時更新", "登出時清空", "依機構與場域拆開分析", "高", "規劃中"),
    ("機構", "is_multi_org_user", "true, false", "boolean", "是否屬於一個以上的機構", "登入後依機構清單判斷", "機構數變成 1 時改為 false", "比較單機構與多機構帳號的使用差異", "低", "規劃中"),
    ("裝置", "platform_version", "7.0.3", "string", "平台版本號", "每次載入平台時更新", "不重置", "判斷數據變化是否跟改版有關", "中", "規劃中"),
    ("裝置", "browser", "chrome_130", "string", "瀏覽器名稱與版本", "每次載入平台時更新", "不重置", "排查特定瀏覽器的問題", "低", "規劃中"),
]


def style_header(ws, headers, height=36):
    ws.append(headers)
    for c in range(1, len(headers) + 1):
        cell = ws.cell(1, c)
        cell.fill, cell.font, cell.border = HEAD_FILL, HEAD_FONT, CELL_BORDER
        cell.alignment = Alignment(wrap_text=True, vertical="center")
    ws.row_dimensions[1].height = height
    ws.freeze_panes = "A2"
    ws.sheet_view.showGridLines = True


wb = Workbook()
wb.remove(wb.active)

# ---------------- DRD
ws = wb.create_sheet("DRD")
H = ["編號", "頁面/區塊", "事件名稱 (En)", "觸發時機/事件定義\n(Trigger/Event Definition)", "目標/數據分析意義",
     "屬性參數 (Property)", "屬性定義 (Property Definition)", "Data Type", "Sample Values", "優先級", "備註"]
style_header(ws, H)
PRI_COL = H.index("優先級") + 1
for n, (page, name, trig, goal, props, note) in enumerate(E, start=1):
    eid = f"DJY_{n:02d}"
    start = ws.max_row + 1
    for j, p in enumerate(props):
        if isinstance(p, str):
            key, sample_o, def_o, pri_o = p, None, None, None
        else:
            key, sample_o, def_o, pri_o = (list(p) + [None, None, None])[:4]
        d, t, s, pri = P[key]
        pri = pri_o or pri
        ws.append([eid, page, name, trig, goal, key, def_o or d, t, sample_o if sample_o is not None else s, pri, note] if j == 0
                  else [None, None, None, None, None, key, def_o or d, t, sample_o if sample_o is not None else s, pri, None])
        r = ws.max_row
        for c in range(1, len(H) + 1):
            cell = ws.cell(r, c)
            cell.font, cell.alignment, cell.border = BODY_FONT, WRAP, CELL_BORDER
        fill, font = PRI[pri]
        pc = ws.cell(r, PRI_COL)
        pc.fill, pc.font, pc.alignment = fill, font, CENTER
    end = ws.max_row
    if end > start:
        for col in (1, 2, 3, 4, 5, 11):
            ws.merge_cells(start_row=start, start_column=col, end_row=end, end_column=col)
    if n == 1:  # 全域屬性下方加雙線，與一般事件分開（同範例）
        for c in range(1, len(H) + 1):
            cell = ws.cell(end, c)
            cell.border = Border(left=GRID, right=GRID, top=GRID, bottom=DOUBLE)
for i, w in enumerate([10, 22, 16, 34, 34, 22, 34, 10, 40, 8, 36], 1):
    ws.column_dimensions[get_column_letter(i)].width = w

# ---------------- Person Properties
ws2 = wb.create_sheet("Person Properties")
H2 = ["屬性分類", "屬性名稱 (Key)", "範例值 (Sample Values)", "資料型別（Data Type）", "描述", "觸發時機", "重置時機", "數據分析意義", "優先級", "埋點狀態"]
style_header(ws2, H2)
for row in PP:
    ws2.append(list(row))
    r = ws2.max_row
    for c in range(1, len(H2) + 1):
        cell = ws2.cell(r, c)
        cell.font, cell.alignment, cell.border = BODY_FONT, WRAP, CELL_BORDER
    fill, font = PRI[row[8]]
    pc = ws2.cell(r, 9)
    pc.fill, pc.font, pc.alignment = fill, font, CENTER
for i, w in enumerate([12, 20, 40, 14, 34, 34, 22, 34, 8, 10], 1):
    ws2.column_dimensions[get_column_letter(i)].width = w

# ---------------- 指標對照
import json, math
M = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "dajiayi_metrics.json"), encoding="utf-8"))
ws3 = wb.create_sheet("指標對照")
H3 = ["報告章節", "指標名稱", "類型／單位", "計算方式", "補充說明", "使用事件（DRD 編號）", "判讀級距與行動"]
style_header(ws3, H3)
prev, start = None, 2
for m in M:
    ws3.append([m["chapter"], m["name"], m["type"], m["calc"], m["note"], m["events"], m["tiers"]])
    r = ws3.max_row
    for c in range(1, len(H3) + 1):
        cell = ws3.cell(r, c)
        cell.font, cell.alignment, cell.border = BODY_FONT, WRAP, CELL_BORDER
    if m["chapter"] != prev:
        if prev is not None and r - 1 > start:
            ws3.merge_cells(start_row=start, start_column=1, end_row=r - 1, end_column=1)
        prev, start = m["chapter"], r
if ws3.max_row > start:
    ws3.merge_cells(start_row=start, start_column=1, end_row=ws3.max_row, end_column=1)
# 級距說明
LEG = [("級距說明", ""),
       ("比率（三級距）", "低（≤30%）｜中（31%–60%）｜高（≥61%）；四捨五入到整數後歸級"),
       ("比率（兩級距）", "低（≤50%）｜高（≥51%）；用在中間級距沒有獨立行動的指標"),
       ("排查時長", "短（≤3 分鐘）｜中（>3～5 分鐘）｜長（>5 分鐘），看中位數"),
       ("填寫時長", "短（≤30 秒）｜中（>30～90 秒）｜長（>90 秒），看中位數"),
       ("上線後看到的時長", "短（≤5 分鐘）｜中（>5～30 分鐘）｜長（>30 分鐘），只算上線時間，看中位數"),
       ("打開通知到點進的時間", "短（≤10 秒）｜中（>10～30 秒）｜長（>30 秒），看中位數"),
       ("字數", "少（≤20 字）｜中（21～50 字）｜多（>50 字），看中位數")]
ws3.append([])
for i, (k, v) in enumerate(LEG):
    ws3.append([k, v])
    r = ws3.max_row
    ws3.merge_cells(start_row=r, start_column=2, end_row=r, end_column=4)
    for c in range(1, 5):
        cell = ws3.cell(r, c)
        cell.font, cell.alignment, cell.border = (HEAD_FONT if i == 0 else BODY_FONT), WRAP, CELL_BORDER
        if i == 0:
            cell.fill = HEAD_FILL
for i, w in enumerate([24, 26, 12, 44, 40, 20, 56], 1):
    ws3.column_dimensions[get_column_letter(i)].width = w


# ---------------- 依內容設定列高（避免線上版文字被切掉）
def _w(ch):
    return 2 if ord(ch) > 0x2E80 else 1


def _lines(text, width):
    if not text:
        return 1
    cap = max(1, int(width * 1.1) - 1)
    return sum(max(1, math.ceil(sum(_w(c) for c in line) / cap)) for line in str(text).split("\n"))


def fit_rows(ws):
    merged = {}
    for mr in ws.merged_cells.ranges:
        merged[(mr.min_row, mr.min_col)] = (mr.max_row, mr.max_col)
        for r in range(mr.min_row, mr.max_row + 1):
            for c in range(mr.min_col, mr.max_col + 1):
                if (r, c) != (mr.min_row, mr.min_col):
                    merged[(r, c)] = None
    need = {}
    for row in ws.iter_rows(min_row=2):
        r = row[0].row
        lines = 1
        for cell in row:
            key = (r, cell.column)
            if key in merged:
                continue
            w = ws.column_dimensions[get_column_letter(cell.column)].width or 10
            lines = max(lines, _lines(cell.value, w))
        need[r] = lines * 15 + 6
    for r, h in need.items():
        ws.row_dimensions[r].height = h
    # 合併儲存格：高度不夠時加在最後一列
    for (r0, c0), span in merged.items():
        if not span:
            continue
        r1, c1 = span
        width = sum((ws.column_dimensions[get_column_letter(c)].width or 10) for c in range(c0, c1 + 1))
        h = _lines(ws.cell(r0, c0).value, width) * 15 + 6
        have = sum(ws.row_dimensions[r].height or 21 for r in range(r0, r1 + 1))
        if h > have:
            ws.row_dimensions[r1].height = (ws.row_dimensions[r1].height or 21) + (h - have)


for sheet in wb.worksheets:
    fit_rows(sheet)

wb.save(OUT)
print("saved", OUT, "events", len(E))
