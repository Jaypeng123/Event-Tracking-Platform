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
    "user_id": ("做這個動作的使用者帳號", "string", "{{string}}, e.g. u_10293", "高"),
    "user_role": ("使用者的角色", "string", "org_admin, admin, doctor, frontline_doctor, frontline_staff", "高"),
    "org_id": ("使用者目前所在的機構", "string", "{{string}}, e.g. org_001", "高"),
    "session_id": ("這次上線的編號；登入或閒置後重新操作時換新的", "string", "{{string}}, e.g. ss_9k3m2p", "高"),
    "page_visit_id": ("這次進入頁面的編號；每進入一個頁面產生一個，頁面內的事件都帶同一個", "string", "{{string}}, e.g. pv_5h2k8m", "高"),
    "platform_version": ("平台版本號", "string", "{{string}}, e.g. 7.0.3", "中"),
    # 頁面、視窗、按鈕
    "page_name": ("頁面名稱", "string", "patient_detail", "高"),
    "popup_name": ("視窗名稱", "string", "notification_center", "高"),
    "popup_visit_id": ("這次打開視窗的編號；每打開一次產生一個，視窗內的事件都帶同一個", "string", "{{string}}, e.g. po_2b9x7q", "高"),
    "button_name": ("按鈕名稱", "string", "", "高"),
    "entry_source": ("從哪裡進來", "string", "nav_menu, notification, alert_list, doctor_pending_list, patient_list, workspace, other", "高"),
    "position": ("第幾個，從 1 開始", "Integer", "{{number}}, e.g. 3", "中"),
    "total_records": ("資料筆數", "Integer", "{{number}}, e.g. 12", "中"),
    "duration_from_view": ("從畫面顯示起算的停留秒數", "Integer", "{{seconds}}, e.g. 8", "高"),
    "duration_from_open": ("從視窗打開起算的秒數", "Integer", "{{seconds}}, e.g. 45", "高"),
    # 個案、警報、轉診
    "patient_id": ("個案編號（平台內部編號，不送姓名）", "string", "{{string}}, e.g. p_88231", "高"),
    "alert_id": ("警報編號；同一個案還沒處理完的多筆警報算同一個；沒有時送 null", "string", "{{string}}, e.g. ae_5521", "高"),
    "referral_id": ("轉診編號；沒有時送 null", "string", "{{string}}, e.g. rf_301", "高"),
    "alert_level": ("警報等級", "string", "high_risk, low_risk, abnormal_report", "高"),
    "alert_items": ("警報的生理項目，多個用逗號分隔", "string", "blood_pressure, ecg, spo2, blood_glucose, heart_rate, body_temp", "中"),
    "list_type": ("列表類型", "string", "notification, high_risk, abnormal_report, low_risk, custom_plan_unmeasured, doctor_pending", "高"),
    # 篩選
    "filter_type": ("篩選類型", "string", "alert_source, data_source, time_range, ecg_lead, ecg_abnormal", "高"),
    "filter_value": ("選擇的篩選值", "string", "", "高"),
    # 個案詳情
    "metric": ("生理項目", "string", "blood_pressure, ecg, spo2, blood_glucose, heart_rate, body_temp", "高"),
    "tab_name": ("頁籤名稱", "string", "health_plan, care_records, patient_reports, vital_blood_pressure, vital_ecg", "高"),
    "tabs_with_data": ("有資料的頁籤，多個用逗號分隔", "string", "health_plan, care_records, patient_reports, vital_blood_pressure, vital_ecg", "高"),
    "has_data": ("該頁籤是否有資料", "boolean", "true, false", "高"),
    "is_abnormal_item": ("這個生理項目是否是待處理警報或這次轉診的異常項目", "boolean", "true, false", "高"),
    "has_multi_source": ("這個生理項目是否同時有 Home 和 Pro 的資料", "boolean", "true, false", "中"),
    "todo_types": ("待辦類型，多個用逗號分隔", "string", "referral_opinion, doctor_advice, follow_up", "中"),
    "block_name": ("區塊名稱", "string", "ecg_summary, ecg_chart, ecg_record_list", "高"),
    # 表單
    "open_seq": ("同一筆警報（或轉診）第幾次打開這張表單，1 是第一次", "Integer", "{{number}}, e.g. 1", "高"),
    "has_input": ("離開時是否已經填了內容", "boolean", "true, false", "中"),
    "result": ("結果", "string", "success, fail", "高"),
    "error_code": ("失敗時的錯誤代碼；成功時送 null", "string", "{{string}}, e.g. E4001", "中"),
    "is_empty": ("是否所有欄位都沒填就提交", "boolean", "true, false", "高"),
    "text_length": ("文字欄位的字數（只送字數，不送內容）", "Integer", "{{number}}, e.g. 42", "高"),
    "result_type": ("處理結果是誤報還是真的異常", "string", "false_alarm, handled, null", "中"),
    # 其他
    "session_start_type": ("這次上線是怎麼開始的", "string", "login, resume", "中"),
    "device_type": ("產生警報的量測設備", "string", "monitor_home, monitor_pro, watch", "中"),
    "resolve_type": ("用什麼方式處理完成", "string", "care_record, referral", "高"),
    "doctor_user_id": ("被轉診的醫師帳號", "string", "{{string}}, e.g. u_20011", "高"),
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
     ["alert_id", "patient_id", "alert_level", "alert_items", "device_type"],
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
     POP("notification_center") + [("tab_name", "abnormal_alert, referral", "目前所在的通知分頁"), ("total_records", "{{number}}, e.g. 12", "打開當下的未讀數量")], ""),
    ("小鈴鐺通知／分頁", "click_button", "點擊「異常提醒」或「轉診提醒」分頁時",
     "紀錄切換通知分頁的次數",
     [("button_name", "tab_switch")] + POP("notification_center") + [("tab_name", "abnormal_alert, referral", "切換後的通知分頁")], ""),
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
     [("page_name", "pending_list"), ("list_type", "high_risk, abnormal_report, low_risk, custom_plan_unmeasured, doctor_pending"), ("total_records", "{{number}}, e.g. 37", "列表的總筆數"), ("entry_source", "nav_menu, notification, workspace", "從哪裡進入列表")],
     "醫師的「待醫師處理列表」也用這個事件（list_type = doctor_pending）"),
    ("待處理列表／列表分頁", "click_button", "點擊列表分頁（檢測高風險／異常上報／檢測低風險等）時",
     "紀錄切換列表分頁的次數",
     [("button_name", "list_tab_switch"), ("page_name", "pending_list"), ("list_type", "high_risk, abnormal_report, low_risk, custom_plan_unmeasured", "切換後的列表")], ""),
    ("待處理列表／列表項目", "item_impression", "列表項目露出一半以上進入畫面時",
     "紀錄哪些警報、轉診在列表中被看到",
     [("page_name", "pending_list"), ("list_type", "high_risk, abnormal_report, low_risk, custom_plan_unmeasured, doctor_pending"), "alert_id", "referral_id", "patient_id", "alert_level", "position"],
     "每個項目在同一次瀏覽中只送一次；載入、捲動、翻頁看到的都要送"),
    ("待處理列表／列表項目", "click_button", "點擊列表中的個案列時",
     "紀錄從列表點進個案詳情的次數",
     [("button_name", "list_row"), ("page_name", "pending_list"), ("list_type", "high_risk, abnormal_report, low_risk, custom_plan_unmeasured, doctor_pending"), "alert_id", "referral_id", "patient_id", "alert_level", "position"], ""),
    ("待處理列表／查看按鈕", "click_button", "點擊列表中的「查看」按鈕時",
     "紀錄從列表點進個案詳情的次數",
     [("button_name", "view_detail"), ("page_name", "pending_list"), ("list_type", "high_risk, abnormal_report, low_risk, custom_plan_unmeasured, doctor_pending"), "alert_id", "referral_id", "patient_id", "alert_level", "position"], ""),
    # ---- 個案詳情
    ("個案詳情", "view_page", "個案詳情畫面載入完成時",
     "紀錄進入個案詳情的次數、從哪裡進來，以及個案當下有沒有待處理的警報或轉診",
     [("page_name", "patient_detail"), "patient_id", ("entry_source", "notification, alert_list, doctor_pending_list, patient_list, other", "從哪裡進入個案詳情"),
      ("alert_id", "{{string}}, e.g. ae_5521", "個案目前還沒處理的警報編號；沒有時送 null"), ("referral_id", "{{string}}, e.g. rf_301", "個案目前還沒處理的轉診編號；沒有時送 null"),
      ("alert_items", "blood_pressure, ecg, spo2, blood_glucose, heart_rate, body_temp", "還沒處理的警報項目，多個用逗號分隔；沒有時送 null"), "tabs_with_data"],
     "不論從哪裡進來，都要帶警報與轉診編號"),
    ("個案詳情／頁籤", "leave_tab", "離開一個頁籤時（切到其他頁籤、離開個案詳情、或切到其他瀏覽器分頁）",
     "紀錄每個頁籤看了多久，了解排查時主要看哪些資訊",
     [("page_name", "patient_detail"), "patient_id", "tab_name", "metric", "has_data", "is_abnormal_item", "has_multi_source", "duration_from_view"],
     "停留不到 1 秒不送；頁籤完整清單請設計確認"),
    ("個案詳情／待辦事項視窗", "view_popup", "進入個案詳情、待辦事項視窗自動跳出時",
     "紀錄待辦事項視窗自動跳出的次數",
     POP("todo_popup") + ["patient_id", "todo_types"], ""),
    ("個案詳情／待辦區塊", "click_button", "點擊「全部內容」再次打開待辦事項時",
     "紀錄主動再次查看待辦內容的次數",
     [("button_name", "todo_view_all"), ("page_name", "patient_detail"), "patient_id", "todo_types"], ""),
    ("個案詳情／待辦事項視窗", "close_popup", "關閉待辦事項視窗時",
     "紀錄待辦事項視窗看了多久",
     POP("todo_popup") + ["duration_from_open"], ""),
    ("檢測儀頁籤／數據來源", "click_button", "點擊 Home 或 Pro 切換數據來源時",
     "紀錄切換檢測儀數據來源的次數",
     [("button_name", "data_source_switch"), ("page_name", "patient_detail"), "patient_id", "metric", ("filter_type", "data_source"), ("filter_value", "home, pro", "切換後的來源")], ""),
    ("個案詳情／時間範圍", "click_button", "點擊「今日／近 7 天／近 30 天／近 1 年」時",
     "紀錄切換時間範圍的次數與最常選的區間",
     [("button_name", "time_range"), ("page_name", "patient_detail"), "metric", ("filter_type", "time_range"), ("filter_value", "today, last_7d, last_30d, last_1y")], "預設為近 30 天"),
    ("個案詳情／自訂日期", "click_button", "在自訂日期選擇器按下「確認」時",
     "紀錄使用自訂日期的次數與天數",
     [("button_name", "custom_range_confirm"), ("page_name", "patient_detail"), "metric", ("filter_type", "time_range"), ("filter_value", "custom_{{number}}, e.g. custom_14", "自訂的天數")], ""),
    ("心電頁籤／各區塊", "view_block", "離開心電頁籤時，每個區塊各送一筆",
     "紀錄心電頁每個區塊被看了多久",
     [("page_name", "patient_detail"), "block_name", ("duration_from_view", "{{seconds}}, e.g. 12", "從區塊露出一半以上開始累計的秒數")], "累計不到 3 秒的區塊不送；區塊清單請設計確認"),
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
     POP("care_record_detail") + ["duration_from_open"], ""),
    # ---- 照護記錄
    ("照護記錄視窗", "view_popup", "點擊「撰寫照護記錄」、視窗顯示完成時",
     "紀錄打開照護記錄的次數",
     POP("care_record_form") + ["patient_id", ("alert_id", "{{string}}, e.g. ae_5521", "這次處理的警報編號"), "open_seq"],
     "第幾次打開（open_seq）若前端無法跨頁面累計，可改由後端記錄"),
    ("照護記錄視窗", "click_button", "點擊「取消」時",
     "紀錄打開照護記錄後沒有提交就取消的次數",
     [("button_name", "cancel")] + POP("care_record_form") + ["has_input", "duration_from_open"], ""),
    ("照護記錄視窗", "click_button", "點擊右上角「×」關閉時",
     "紀錄打開照護記錄後沒有提交就關閉的次數",
     [("button_name", "close")] + POP("care_record_form") + ["has_input", "duration_from_open"], ""),
    ("照護記錄視窗", "leave_page", "照護記錄視窗開著時，直接離開頁面、切換個案或重新整理時",
     "紀錄沒有提交也沒有關閉就離開的次數",
     POP("care_record_form") + ["has_input", "duration_from_open"], ""),
    ("照護記錄視窗", "submit_form", "點擊「完成處理」、系統回傳結果時",
     "紀錄照護記錄提交成功或失敗、是否空白提交、填了多少字",
     POP("care_record_form") + ["alert_id", "alert_level", "alert_items", "open_seq", "result", "error_code", "is_empty", "text_length", "result_type", "duration_from_open"],
     "不送填寫內容，只送字數；result_type 需確認照護記錄是否有欄位能區分誤報"),
    # ---- 醫師建議
    ("醫師建議視窗", "view_popup", "點擊「醫師建議」、視窗顯示完成時",
     "紀錄打開醫師建議的次數",
     POP("doctor_advice_form") + ["patient_id", ("referral_id", "{{string}}, e.g. rf_301", "這次處理的轉診編號"), "open_seq"], ""),
    ("醫師建議視窗", "click_button", "點擊「取消」時",
     "紀錄打開醫師建議後沒有提交就取消的次數",
     [("button_name", "cancel")] + POP("doctor_advice_form") + ["has_input", "duration_from_open"], ""),
    ("醫師建議視窗", "click_button", "點擊右上角「×」關閉時",
     "紀錄打開醫師建議後沒有提交就關閉的次數",
     [("button_name", "close")] + POP("doctor_advice_form") + ["has_input", "duration_from_open"], ""),
    ("醫師建議視窗", "leave_page", "醫師建議視窗開著時，直接離開頁面、切換個案或重新整理時",
     "紀錄沒有提交也沒有關閉就離開的次數",
     POP("doctor_advice_form") + ["has_input", "duration_from_open"], ""),
    ("醫師建議視窗", "submit_form", "點擊「完成處理」、系統回傳結果時",
     "紀錄醫師建議提交成功或失敗、是否空白提交、填了多少字",
     POP("doctor_advice_form") + ["referral_id", "open_seq", "result", "error_code", "is_empty", "text_length", "duration_from_open"],
     "不送填寫內容，只送字數"),
]

# =====================================================================
# Person Properties（照使用者提供的範本欄位）
# =====================================================================
PP = [
    ("使用者身分", "user_id", "{{string}}, e.g. u_12345abc", "string", "每個帳號的唯一編號", "登入成功時設定", "登出時清空", "串起同一個人的所有行為", "高", "規劃中"),
    ("使用者身分", "user_role", "org_admin, admin, doctor, frontline_doctor, frontline_staff", "string", "帳號角色：機構管理員、管理員、醫師、一線醫師、一線人員", "登入成功時設定；角色變更時更新", "登出時清空", "排除管理員帳號；區分一線人員與醫師的行為", "高", "規劃中"),
    ("機構", "org_id", "{{string}}, e.g. org_001", "string", "目前所在的機構", "登入後取得機構時設定；切換機構時更新", "登出時清空", "依機構與場域拆開分析", "高", "規劃中"),
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
import json, math, re

_TIER = re.compile(r"^(低|中|高|短|長|少|多|縮短|差不多|拉長)（")


def number_tiers(text):
    """級距每一行前面加 1. 2. 3.；遇到非級距的行就重新起算"""
    out, n = [], 0
    for line in (text or "").split("\n"):
        if _TIER.match(line):
            n += 1
            out.append(f"{n}. {line}")
        else:
            n = 0 if not line.startswith("・") else n
            out.append(line)
    return "\n".join(out)

M = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "dajiayi_metrics.json"), encoding="utf-8"))
ws3 = wb.create_sheet("指標對照")
H3 = ["報告章節", "指標名稱", "類型／單位", "計算方式", "補充說明", "使用事件（DRD 編號）", "判讀級距與行動"]
style_header(ws3, H3)
prev, start = None, 2
for m in M:
    ws3.append([m["chapter"], m["name"], m["type"], m["calc"], m["note"], m["events"], number_tiers(m["tiers"])])
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

# ---------------- 代碼對照表
CODES = [
    ("page_name", [("login", "登入頁", ""), ("pending_list", "待處理列表", "包含醫師的「待醫師處理列表」"), ("patient_detail", "個案詳情", "")]),
    ("popup_name", [("notification_center", "小鈴鐺通知", "頁面右上角點小鈴鐺打開的通知視窗"),
                    ("todo_popup", "待辦事項視窗", "進入個案詳情時自動跳出"),
                    ("care_record_detail", "處理紀錄詳情", "處理紀錄頁籤中點單筆紀錄打開"),
                    ("care_record_form", "照護記錄視窗", "個案詳情點「撰寫照護記錄」打開"),
                    ("doctor_advice_form", "醫師建議視窗", "個案詳情點「醫師建議」打開")]),
    ("button_name", [("tab_switch", "通知分頁", "小鈴鐺通知內的「異常提醒／轉診提醒」"),
                     ("alert_source_filter", "來源篩選", "小鈴鐺通知內的「全部／CoDoctor 檢測儀／CoDoctor Watch」"),
                     ("goto_list", "前往列表", "小鈴鐺通知內的「前往○○列表」"),
                     ("notification_card", "通知卡片", "小鈴鐺通知內的每一則警報或轉診"),
                     ("list_tab_switch", "列表分頁", "待處理列表上方的分頁"),
                     ("list_row", "個案列", "待處理列表中的每一列"),
                     ("view_detail", "「查看」按鈕", "待處理列表每一列右側"),
                     ("todo_view_all", "「全部內容」", "個案詳情的待辦區塊"),
                     ("data_source_switch", "Home／Pro 切換", "檢測儀頁籤的數據來源"),
                     ("time_range", "時間範圍快捷選項", "個案詳情圖表上方的今日、近 7 天等"),
                     ("custom_range_confirm", "自訂日期「確認」", "自訂日期選擇器"),
                     ("cancel", "「取消」", "照護記錄、醫師建議視窗下方"),
                     ("close", "「×」", "照護記錄、醫師建議視窗右上角")]),
    ("tab_name", [("health_plan", "健康計畫", ""), ("care_records", "處理紀錄", ""), ("patient_reports", "個案上報紀錄", ""),
                  ("vital_blood_pressure", "生理體徵｜血壓", "其他生理項目同樣用 vital_ 加生理項目代碼，例：vital_spo2"),
                  ("vital_ecg", "生理體徵｜心電", "頁籤完整清單待設計確認"),
                  ("abnormal_alert", "異常提醒", "小鈴鐺通知的分頁"), ("referral", "轉診提醒", "小鈴鐺通知的分頁")]),
    ("list_type", [("notification", "小鈴鐺通知", "不是列表，代表在小鈴鐺通知中被看到"),
                   ("high_risk", "檢測高風險列表", ""), ("abnormal_report", "異常上報列表", ""), ("low_risk", "檢測低風險列表", ""),
                   ("custom_plan_unmeasured", "自訂計劃未測量列表", ""), ("doctor_pending", "待醫師處理列表", "")]),
    ("filter_type", [("alert_source", "小鈴鐺通知的來源篩選", ""), ("data_source", "檢測儀數據來源", ""), ("time_range", "時間範圍", ""),
                     ("ecg_lead", "心電導程篩選", ""), ("ecg_abnormal", "心電異常篩選", "")]),
    ("filter_value", [("all", "全部", "來源篩選"), ("monitor", "CoDoctor 檢測儀", "來源篩選"), ("watch", "CoDoctor Watch", "來源篩選"),
                      ("home", "Home", "檢測儀數據來源"), ("pro", "Pro", "檢測儀數據來源"),
                      ("today", "今日", "時間範圍"), ("last_7d", "近 7 天", "時間範圍"), ("last_30d", "近 30 天", "時間範圍（預設）"), ("last_1y", "近 1 年", "時間範圍"),
                      ("custom_{{number}}", "自訂日期", "custom_ 加天數，例：custom_14 代表 14 天"),
                      ("I", "導程 I", "導程完整清單待設計確認"), ("II", "導程 II", ""), ("III", "導程 III", ""),
                      ("af", "心房顫動", "暫定，異常條件清單待設計確認"), ("pvc", "早期心室收縮", "暫定")]),
    ("entry_source", [("nav_menu", "左側選單", ""), ("notification", "小鈴鐺通知", ""), ("workspace", "工作台", ""),
                      ("alert_list", "待處理列表", ""), ("doctor_pending_list", "待醫師處理列表", ""), ("patient_list", "個案列表", ""), ("other", "其他", "")]),
    ("user_role", [("org_admin", "機構管理員", "分析時排除"), ("admin", "管理員", "分析時排除"), ("doctor", "醫師", ""),
                   ("frontline_doctor", "一線醫師", ""), ("frontline_staff", "一線人員", "")]),
    ("alert_level", [("high_risk", "檢測高風險", ""), ("low_risk", "檢測低風險", ""), ("abnormal_report", "異常上報", "")]),
    ("metric", [("blood_pressure", "血壓", "alert_items 也用這組代碼"), ("ecg", "心電", ""), ("spo2", "血氧", ""), ("blood_glucose", "血糖", ""),
                ("heart_rate", "心率", ""), ("body_temp", "體溫", "完整清單待確認")]),
    ("resolve_type", [("care_record", "照護記錄", ""), ("referral", "轉診醫師", "")]),
    ("device_type", [("monitor_home", "CoDoctor 檢測儀（Home）", ""), ("monitor_pro", "CoDoctor 檢測儀（Pro）", ""), ("watch", "CoDoctor Watch", "")]),
    ("session_start_type", [("login", "登入", ""), ("resume", "閒置後重新操作", "")]),
    ("block_name", [("ecg_summary", "心電摘要", "暫定，區塊清單待設計確認"), ("ecg_chart", "心電圖", ""), ("ecg_record_list", "心電紀錄列表", "")]),
    ("todo_types", [("referral_opinion", "轉診意見", ""), ("doctor_advice", "醫師建議", ""), ("follow_up", "追蹤內容", "")]),
    ("result", [("success", "成功", ""), ("fail", "失敗", "")]),
    ("result_type", [("false_alarm", "誤報", "待確認照護記錄是否有欄位能區分"), ("handled", "真異常已處置", "")]),
]


def _events_using(key, value):
    ids = []
    for n, (_, _, _, _, props, _) in enumerate(E, start=1):
        for p in props:
            k = p if isinstance(p, str) else p[0]
            if k != key and not (key == "metric" and k == "alert_items"):
                continue
            sample = P[k][2] if isinstance(p, str) or len(p) < 2 or p[1] is None else p[1]
            vals = [v.strip() for v in sample.replace(",", ", ").split(", ")]
            if value in vals:
                ids.append(f"DJY_{n:02d}")
                break
    return "、".join(ids) or "—"


ws4 = wb.create_sheet("代碼對照表", index=2)
H4 = ["屬性參數 (Property)", "代碼值 (Value)", "中文名稱", "畫面位置／說明", "使用事件（DRD 編號）"]
style_header(ws4, H4)
for key, vals in CODES:
    start = ws4.max_row + 1
    for v, zh, where in vals:
        ws4.append([key, v, zh, where, _events_using(key, v)])
        r = ws4.max_row
        for c in range(1, len(H4) + 1):
            cell = ws4.cell(r, c)
            cell.font, cell.alignment, cell.border = BODY_FONT, WRAP, CELL_BORDER
    if ws4.max_row > start:
        ws4.merge_cells(start_row=start, start_column=1, end_row=ws4.max_row, end_column=1)
for i, w in enumerate([22, 24, 22, 44, 36], 1):
    ws4.column_dimensions[get_column_letter(i)].width = w

# ---------------- 埋點共用規則
RULES = [
    ("命名", "事件名稱", "照「互動類型」命名，記的是發生了哪一種互動，不是功能名稱或結果；是哪個按鈕、哪一頁由屬性區分。英文小寫加底線，動詞在前", "view_page、view_popup、close_popup、click_button、item_impression、leave_tab、leave_page、submit_form、apply_filter、view_block、session_start"),
    ("命名", "屬性名稱", "只記事實，不記判讀結果；依資料類型加後綴：xxx_name（名稱）、xxx_id（編號）、xxx_type（類型）、xxx_status（狀態）、duration_from_<起點>（秒數）。同一個意思全文件只用一個屬性名稱，屬性值請查「代碼對照表」", "page_name、alert_id、list_type、duration_from_open"),
    ("命名", "Sample Values", "列舉值列出所有可能的值；非列舉值寫「型態＋範例」；布林值寫 true, false", "列舉：high_risk, low_risk｜非列舉：{{number}}, e.g. 3、{{seconds}}, e.g. 45、{{string}}, e.g. D001"),
    ("全域屬性", "每筆事件都要帶", "DRD 的 DJY_01 列出的屬性，所有事件都要帶，各事件不再重複列", "user_id、user_role、org_id、session_id、page_visit_id、platform_version"),
    ("時間", "事件時間", "以系統收到事件的時間為準；時區一律 +08:00", "2026-11-05T09:30:12+08:00"),
    ("時間", "秒數 duration_from_<起點>", "秒數一律寫明從什麼時候開始算：duration_from_view 從畫面（頁籤、區塊）顯示起算，duration_from_open 從視窗打開起算；四捨五入到整數，切到其他瀏覽器分頁的時間不算", "duration_from_view: 8"),
    ("編號", "page_visit_id", "每進入一個頁面產生一個新的（重新整理也算新的一次），頁面內的事件都帶同一個", "pv_5h2k8m（建議用 UUID）"),
    ("編號", "popup_visit_id", "每打開一次視窗產生一個新的，視窗內的事件（含關閉、提交）都帶同一個", "po_2b9x7q（建議用 UUID）"),
    ("編號", "session_id", "登入成功，或閒置超過 30 分鐘後再次操作時產生新的；最後一個動作後閒置 30 分鐘就算這次上線結束，不另外送事件", "ss_9k3m2p（建議用 UUID）"),
    ("被看到", "曝光（item_impression）", "項目露出一半以上進入畫面才算；載入、捲動、翻頁後看到的都要送；同一次瀏覽或打開中，同一筆只送一次", "往回捲到已送過的卡片不再送"),
    ("離開", "離開類事件", "切換頁籤、離開頁面、切到其他瀏覽器分頁、關閉瀏覽器時都要送（可用 visibilitychange、pagehide）", "leave_tab、leave_page"),
    ("結果", "提交類事件", "等系統回傳結果後才送，成功、失敗都送；前端欄位檢核沒通過、沒有呼叫系統時不送", "submit_form"),
    ("重複", "不要重複送", "同一個按鈕連點、畫面重新整理資料時不要重送；點選目前已經選中的選項不送", "已在「近 30 天」又點一次「近 30 天」不送"),
    ("格式", "空值", "取不到值時送 null，不要送空字串，也不要用 0 代替", "alert_id: null"),
    ("格式", "多個值", "用逗號分隔，不加空格", "blood_pressure,ecg"),
    ("格式", "布林值與數字", "布林值用小寫 true／false；數字不加千分位", "true、1000"),
    ("隱私", "不送個資與填寫內容", "不送姓名、身分證、電話等個資，也不送照護記錄、醫師建議的文字內容；只送編號、代碼和字數", "text_length: 42"),
    ("後端", "後端事件", "DJY_02～DJY_05 由後端記錄；也可以改用資料表提供給分析端", "alert_created、alert_resolved"),
    ("角色", "所有角色都要送", "管理員的事件也照常送，分析時再排除", "user_role = admin"),
]
ws5 = wb.create_sheet("埋點共用規則", index=3)
H5 = ["類別", "規則", "說明", "範例"]
style_header(ws5, H5)
start, prev = 2, None
for cat, rule, desc, ex in RULES:
    ws5.append([cat, rule, desc, ex])
    r = ws5.max_row
    for c in range(1, len(H5) + 1):
        cell = ws5.cell(r, c)
        cell.font, cell.alignment, cell.border = BODY_FONT, WRAP, CELL_BORDER
    if cat != prev:
        if prev is not None and r - 1 > start:
            ws5.merge_cells(start_row=start, start_column=1, end_row=r - 1, end_column=1)
        prev, start = cat, r
if ws5.max_row > start:
    ws5.merge_cells(start_row=start, start_column=1, end_row=ws5.max_row, end_column=1)
for i, w in enumerate([12, 24, 60, 44], 1):
    ws5.column_dimensions[get_column_letter(i)].width = w


# ---------------- 依內容設定列高（避免線上版文字被切掉）
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
        need[r] = lines * 18 + 8
    for r, h in need.items():
        ws.row_dimensions[r].height = h
    # 合併儲存格：高度不夠時加在最後一列
    for (r0, c0), span in merged.items():
        if not span:
            continue
        r1, c1 = span
        width = sum((ws.column_dimensions[get_column_letter(c)].width or 10) for c in range(c0, c1 + 1))
        h = _lines(ws.cell(r0, c0).value, width) * 18 + 8
        have = sum(ws.row_dimensions[r].height or 21 for r in range(r0, r1 + 1))
        if h > have:
            ws.row_dimensions[r1].height = (ws.row_dimensions[r1].height or 21) + (h - have)


for sheet in wb.worksheets:
    fit_rows(sheet)

wb.save(OUT)
print("saved", OUT, "events", len(E))
