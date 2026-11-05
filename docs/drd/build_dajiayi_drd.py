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
# 屬性：key -> (屬性定義, Data Type, Sample Values, 優先級)
# 事件內可用 (key, 範例覆寫) 或 (key, 範例覆寫, 定義覆寫, 優先級覆寫)
# =====================================================================
P = {
    "user_id": ("登入的使用者帳號", "string", "u_10293", "高"),
    "user_role": ("使用者的角色", "string", "org_admin, admin, doctor, frontline_doctor, frontline_staff", "高"),
    "org_id": ("使用者目前所在的機構", "string", "org_001", "高"),
    "session_id": ("這次上線的編號，每次登入或閒置後重新操作時換一個新的", "string", "ss_9k3m2p", "高"),
    "platform_version": ("平台版本號", "string", "7.0.3", "中"),
    "session_start_type": ("這次上線是怎麼開始的", "string", "login, resume", "中"),
    "alert_event_id": ("警報編號；同一個案還沒處理完的多筆警報算同一個編號", "string", "ae_5521", "高"),
    "task_id": ("處理任務編號", "string", "tk_8830", "中"),
    "referral_id": ("轉診編號", "string", "rf_301", "高"),
    "patient_id": ("個案編號（平台內部編號，不送姓名）", "string", "p_88231", "高"),
    "alert_level": ("警報等級", "string", "high_risk, low_risk, abnormal_report", "高"),
    "alert_items": ("警報的生理項目，多個用逗號分隔", "string", "blood_pressure,ecg", "中"),
    "device_source": ("產生警報的量測設備", "string", "monitor_home, monitor_pro, watch", "中"),
    "created_at": ("產生時間", "string", "2026-11-04T10:15:30+08:00", "高"),
    "resolved_at": ("處理完成時間", "string", "2026-11-04T13:02:11+08:00", "高"),
    "resolve_type": ("用什麼方式處理完成", "string", "care_record, referral", "高"),
    "resolved_by_user_id": ("完成處理的人", "string", "u_10293", "中"),
    "referrer_user_id": ("發起轉診的人", "string", "u_10293", "中"),
    "doctor_user_id": ("被轉診的醫師", "string", "u_20011", "高"),
    "page_name": ("頁面名稱", "string", "patient_detail", "高"),
    "popup_name": ("視窗名稱", "string", "notification_center", "高"),
    "button_name": ("按鈕名稱", "string", "", "高"),
    "notify_session_id": ("這次打開小鈴鐺通知的編號，用來串起同一次打開內的所有動作", "string", "ns_4k2p9a", "高"),
    "notify_tab": ("通知分頁", "string", "abnormal_alert, referral", "高"),
    "unread_count": ("打開當下的未讀數量", "Integer", NUM + "12", "中"),
    "list_name": ("被看到的位置", "string", "notification_alert, notification_referral", "高"),
    "list_view_id": ("這次進入列表的編號，用來串起同一次瀏覽內的所有動作", "string", "lv_7d1c3e", "高"),
    "list_type": ("列表類型", "string", "high_risk, abnormal_report, low_risk, custom_plan_unmeasured, doctor_pending", "高"),
    "list_total_count": ("列表的總筆數", "Integer", NUM + "37", "中"),
    "item_type": ("是警報還是轉診", "string", "alert, referral", "高"),
    "item_id": ("警報編號或轉診編號", "string", "ae_5521, rf_301", "高"),
    "source_filter": ("目前選的通知來源", "string", "all, monitor, watch", "中"),
    "position": ("在列表中的第幾個，從 1 開始", "Integer", NUM + "3", "中"),
    "page_index": ("列表第幾頁，從 1 開始", "Integer", NUM + "1", "低"),
    "entry_source": ("從哪裡進來", "string", "nav_menu, notification_shortcut, workspace", "高"),
    "from_source": ("切換前的來源", "string", "all, monitor, watch", "高"),
    "to_source": ("切換後的來源", "string", "all, monitor, watch", "高"),
    "target_list": ("要前往的列表", "string", "high_risk, abnormal_report, custom_plan_unmeasured, low_risk", "高"),
    "target_list_count": ("點擊當下該列表的筆數；0 代表空列表", "Integer", NUM + "0", "中"),
    "detail_visit_id": ("這次進入個案詳情的編號，用來串起同一次瀏覽內的所有動作", "string", "dv_5h2k8m", "高"),
    "has_pending_alert": ("個案目前是否有還沒處理的警報", "boolean", "true, false", "高"),
    "pending_alert_items": ("還沒處理的警報項目，多個用逗號分隔；沒有時為 null", "string", "null, blood_pressure,ecg", "中"),
    "has_pending_referral": ("個案目前是否有還沒處理的轉診", "boolean", "true, false", "高"),
    "tabs_with_data": ("有資料的頁籤，多個用逗號分隔", "string", "health_plan,care_records", "高"),
    "has_todo": ("是否有待辦事項", "boolean", "true, false", "中"),
    "default_tab": ("一進來預設顯示的頁籤", "string", "vital_blood_pressure", "低"),
    "tab_group": ("頁籤類型", "string", "info, vital_sign", "高"),
    "tab_name": ("頁籤名稱", "string", "health_plan, care_records, patient_reports, vital_blood_pressure, vital_ecg", "高"),
    "metric": ("生理項目", "string", "blood_pressure, ecg, spo2, blood_glucose, heart_rate, body_temp", "高"),
    "has_data": ("該頁籤是否有資料", "boolean", "true, false", "高"),
    "is_pending_abnormal": ("這個生理項目是否是還沒處理的警報項目", "boolean", "true, false, null", "高"),
    "is_referral_item": ("這個生理項目是否是這次轉診的異常項目", "boolean", "true, false, null", "高"),
    "has_multi_source": ("這個生理項目是否同時有 Home 和 Pro 的資料", "boolean", "true, false, null", "高"),
    "dwell_seconds": ("停留秒數", "Integer", "{{seconds}}, e.g. 8", "高"),
    "leave_reason": ("怎麼離開的", "string", "switch_tab, leave_page, page_hidden", "低"),
    "open_type": ("自動跳出或手動打開", "string", "auto, manual", "高"),
    "todo_types": ("待辦類型，多個用逗號分隔", "string", "referral_opinion, doctor_advice, follow_up", "中"),
    "range_option": ("選擇的時間範圍", "string", "today, last_7d, last_30d, last_1y", "高"),
    "custom_range_days": ("自訂日期的天數", "Integer", NUM + "14", "中"),
    "lead": ("目前顯示的心電導程", "string", "I, II, III", "中"),
    "block_name": ("心電頁的區塊名稱", "string", "ecg_summary, ecg_chart, ecg_record_list", "高"),
    "visible_seconds": ("區塊露出一半以上的累計秒數", "Integer", "{{seconds}}, e.g. 12", "高"),
    "filter_type": ("篩選類型", "string", "lead, abnormal", "高"),
    "filter_value": ("篩選條件", "string", "II, af", "中"),
    "result_count": ("篩選後的筆數", "Integer", NUM + "6", "低"),
    "record_open_id": ("這次打開處理紀錄的編號", "string", "ro_6m1v8k", "高"),
    "record_rank": ("點的是第幾筆紀錄，最新的是 1", "Integer", NUM + "1", "中"),
    "record_type": ("紀錄類型", "string", "care_record, referral, doctor_advice", "中"),
    "record_created_at": ("紀錄產生時間", "string", "2026-10-28T09:20:00+08:00", "中"),
    "form_type": ("表單類型", "string", "care_record, doctor_advice", "高"),
    "form_open_id": ("這次打開表單的編號，用來配對之後的取消、關閉或提交", "string", "fo_2b9x7q", "高"),
    "form_open_seq": ("同一筆警報（或轉診）第幾次打開這張表單，1 是第一次", "Integer", NUM + "1", "高"),
    "has_input": ("離開時是否已經填了內容", "boolean", "true, false", "中"),
    "result": ("提交結果", "string", "success, fail", "高"),
    "error_code": ("失敗時的錯誤代碼；成功時為 null", "string", "null, E4001", "中"),
    "total_open_count": ("從第一次打開到這次提交，總共打開幾次", "Integer", NUM + "2", "高"),
    "is_empty": ("是否所有欄位都沒填就提交", "boolean", "true, false", "高"),
    "text_length": ("文字欄位的字數（只送字數，不送內容）", "Integer", NUM + "42", "高"),
    "result_type": ("處理結果是誤報還是真的異常", "string", "false_alarm, handled, null", "中"),
}

# =====================================================================
# 事件：(頁面/區塊, 事件名稱, 觸發時機, 目標/數據分析意義, [屬性], 備註)
# 一個事件只寫一個觸發動作
# =====================================================================
FORM_CR = [("popup_name", "care_record_form"), "form_open_id", "form_open_seq", "detail_visit_id", "patient_id", ("alert_event_id", "ae_5521", "這次處理的警報編號"), "task_id"]
FORM_DA = [("popup_name", "doctor_advice_form"), "form_open_id", "form_open_seq", "detail_visit_id", "patient_id", ("referral_id", "rf_301", "這次處理的轉診編號")]
E = [
    ("Global property 全域屬性", "所有事件", "每一筆事件發送時帶入",
     "紀錄每筆事件是誰、什麼角色、在哪個機構、哪一次上線發生的",
     ["user_id", "user_role", "org_id", "session_id", "platform_version"],
     "分析時排除機構管理員（org_admin）與管理員（admin）"),
    # ---- 後端
    ("後端（系統）", "alert_created", "系統判定數據異常、產生警報時",
     "紀錄每一筆警報的產生時間與內容",
     ["alert_event_id", "task_id", "patient_id", "org_id", "alert_level", "alert_items", "device_source", "created_at"],
     "由後端記錄；同一個案還沒處理完時，新的警報項目併入原本的警報編號"),
    ("後端（系統）", "alert_resolved", "警報被處理完成、從待處理移除時",
     "紀錄警報何時、用什麼方式處理完成",
     ["alert_event_id", "patient_id", "resolve_type", "resolved_by_user_id", "resolved_at"], "由後端記錄"),
    ("後端（系統）", "referral_created", "護理師送出轉診、系統產生轉診紀錄時",
     "紀錄每一筆轉診的產生時間與被轉診的醫師",
     ["referral_id", "alert_event_id", "patient_id", "referrer_user_id", "doctor_user_id", "created_at"], "由後端記錄"),
    ("後端（系統）", "referral_resolved", "醫師送出醫師建議、轉診標記為已處理時",
     "紀錄轉診何時處理完成",
     ["referral_id", "resolved_by_user_id", "resolved_at"], "由後端記錄"),
    # ---- 上線
    ("登入", "session_start", "登入成功時",
     "紀錄每次上線的時間，用來判斷警報產生後有沒有人上線、上線後多久看到",
     [("session_start_type", "login"), "session_id", "page_name"], ""),
    ("平台全域", "session_start", "閒置超過 30 分鐘後，再次操作平台時",
     "紀錄閒置後重新上線的時間",
     [("session_start_type", "resume"), "session_id", "page_name"], "閒置 30 分鐘的定義請產品確認是否符合護理師的使用習慣"),
    # ---- 小鈴鐺通知
    ("小鈴鐺通知", "view_popup", "點擊小鈴鐺、通知視窗顯示完成時",
     "紀錄打開小鈴鐺通知的次數，與打開當下有多少未讀",
     [("popup_name", "notification_center"), "notify_session_id", "notify_tab", "unread_count"], "每次打開產生新的 notify_session_id"),
    ("小鈴鐺通知／分頁", "click_button", "點擊「異常提醒」或「轉診提醒」分頁時",
     "紀錄切換通知分頁的次數",
     [("button_name", "notify_tab_switch"), "notify_session_id", ("notify_tab", "abnormal_alert, referral", "切換後的分頁")], ""),
    ("小鈴鐺通知／通知卡片", "item_impression", "通知卡片露出一半以上進入畫面時",
     "紀錄哪些警報、轉診在小鈴鐺通知中被看到",
     [("list_name", "notification_alert, notification_referral"), "notify_session_id", "item_type", "item_id", "patient_id", "alert_level", "source_filter", "position"],
     "每張卡片在同一次打開中只送一次"),
    ("小鈴鐺通知／來源篩選", "click_button", "點擊來源篩選（全部／CoDoctor 檢測儀／CoDoctor Watch）時",
     "紀錄依設備篩選通知的次數",
     [("button_name", "alert_source_filter"), "notify_session_id", "from_source", "to_source"], ""),
    ("小鈴鐺通知／前往列表", "click_button", "點擊「前往○○列表」按鈕時",
     "紀錄從通知前往各列表的次數，以及是否點到空列表",
     [("button_name", "goto_list"), "notify_session_id", "target_list", "target_list_count"], ""),
    ("小鈴鐺通知／通知卡片", "click_button", "點擊通知卡片時",
     "紀錄從通知點進個案詳情的次數，以及點的是哪一筆警報或轉診",
     [("button_name", "notification_card"), "notify_session_id", "item_type", "item_id", "patient_id", "alert_level", "position"], ""),
    # ---- 待處理列表
    ("待處理列表", "view_page", "待處理列表畫面載入完成時",
     "紀錄進入待處理列表的次數與從哪裡進來",
     [("page_name", "pending_list"), "list_view_id", "list_type", "list_total_count", "entry_source"], "醫師的「待醫師處理列表」也用這個事件（list_type = doctor_pending）"),
    ("待處理列表／列表分頁", "click_button", "點擊列表分頁（檢測高風險／異常上報／檢測低風險等）時",
     "紀錄切換列表分頁的次數",
     [("button_name", "list_tab_switch"), "list_view_id", ("list_type", "high_risk, abnormal_report, low_risk, custom_plan_unmeasured", "切換後的列表")], ""),
    ("待處理列表／列表項目", "item_impression", "列表項目露出一半以上進入畫面時",
     "紀錄哪些警報、轉診在列表中被看到",
     [("list_name", "high_risk, abnormal_report, low_risk, doctor_pending"), "list_view_id", "item_type", "item_id", "patient_id", "alert_level", "position", "page_index"],
     "每個項目在同一次瀏覽中只送一次；載入、捲動、翻頁看到的都要送"),
    ("待處理列表／列表項目", "click_button", "點擊列表中的個案列時",
     "紀錄從列表點進個案詳情的次數",
     [("button_name", "list_row"), "list_view_id", "list_type", "item_type", "item_id", "patient_id", "alert_level", "position"], ""),
    ("待處理列表／查看按鈕", "click_button", "點擊列表中的「查看」按鈕時",
     "紀錄從列表點進個案詳情的次數",
     [("button_name", "view_detail"), "list_view_id", "list_type", "item_type", "item_id", "patient_id", "alert_level", "position"], ""),
    # ---- 個案詳情
    ("個案詳情", "view_page", "個案詳情畫面載入完成時",
     "紀錄進入個案詳情的次數、從哪裡進來，以及個案當下有沒有待處理的警報或轉診",
     [("page_name", "patient_detail"), "detail_visit_id", "patient_id",
      ("entry_source", "notification_alert, notification_referral, alert_list, doctor_pending_list, patient_list, other"),
      ("alert_event_id", "null, ae_5521", "個案目前還沒處理的警報編號；沒有時為 null"), ("referral_id", "null, rf_301", "個案目前還沒處理的轉診編號；沒有時為 null"),
      "has_pending_alert", "pending_alert_items", "has_pending_referral", "tabs_with_data", "has_todo", "default_tab"],
     "每次進入產生新的 detail_visit_id；不論從哪裡進來，都要帶警報與轉診編號"),
    ("個案詳情／頁籤", "leave_tab", "離開一個頁籤時（切到其他頁籤、離開個案詳情、或切到其他瀏覽器分頁）",
     "紀錄每個頁籤看了多久，了解排查時主要看哪些資訊",
     ["detail_visit_id", "patient_id", "tab_group", "tab_name", "metric", "has_data", "is_pending_abnormal", "is_referral_item", "has_multi_source", "dwell_seconds", "leave_reason"],
     "停留不到 1 秒不送；頁籤完整清單請設計確認"),
    ("個案詳情／待辦事項視窗", "view_popup", "進入個案詳情、待辦事項視窗自動跳出時",
     "紀錄待辦事項視窗自動跳出的次數",
     [("popup_name", "todo_popup"), "detail_visit_id", "patient_id", ("open_type", "auto"), "todo_types"], ""),
    ("個案詳情／待辦區塊", "click_button", "點擊「全部內容」再次打開待辦事項時",
     "紀錄主動再次查看待辦內容的次數",
     [("button_name", "todo_view_all"), "detail_visit_id", "patient_id", "todo_types"], ""),
    ("個案詳情／待辦事項視窗", "close_popup", "關閉待辦事項視窗時",
     "紀錄待辦事項視窗看了多久",
     [("popup_name", "todo_popup"), "detail_visit_id", "open_type", "dwell_seconds"], ""),
    ("檢測儀頁籤／數據來源", "click_button", "點擊 Home 或 Pro 切換數據來源時",
     "紀錄切換檢測儀數據來源的次數",
     [("button_name", "monitor_source"), "detail_visit_id", "patient_id", "metric", ("from_source", "home, pro"), ("to_source", "home, pro")], ""),
    ("個案詳情／時間範圍", "click_button", "點擊「今日／近 7 天／近 30 天／近 1 年」時",
     "紀錄切換時間範圍的次數與最常選的區間",
     [("button_name", "time_range"), "detail_visit_id", "metric", "range_option"], "預設為近 30 天"),
    ("個案詳情／自訂日期", "click_button", "在自訂日期選擇器按下「確認」時",
     "紀錄使用自訂日期的次數與天數",
     [("button_name", "custom_range_confirm"), "detail_visit_id", "metric", "custom_range_days"], ""),
    ("心電頁籤／各區塊", "view_block", "離開心電頁籤時，每個區塊各送一筆",
     "紀錄心電頁每個區塊被看了多久",
     ["detail_visit_id", "lead", "block_name", "visible_seconds"], "累計不到 3 秒的區塊不送；區塊清單請設計確認"),
    ("心電頁籤／導程篩選", "apply_filter", "選擇導程、心電紀錄列表更新後",
     "紀錄使用導程篩選的次數",
     ["detail_visit_id", ("filter_type", "lead"), ("filter_value", "I, II, III"), "result_count"], ""),
    ("心電頁籤／異常篩選", "apply_filter", "選擇異常條件、心電紀錄列表更新後",
     "紀錄使用異常篩選的次數",
     ["detail_visit_id", ("filter_type", "abnormal"), ("filter_value", "af, pvc"), "result_count"], "異常條件完整清單請設計確認"),
    ("處理紀錄頁籤／紀錄詳情", "view_popup", "點擊單筆處理紀錄、詳情顯示時",
     "紀錄查看過往處理紀錄的次數，以及看的是第幾筆",
     [("popup_name", "care_record_detail"), "record_open_id", "detail_visit_id", "patient_id", "record_rank", "record_type", "record_created_at"], ""),
    ("處理紀錄頁籤／紀錄詳情", "close_popup", "關閉處理紀錄詳情時",
     "紀錄處理紀錄看了多久",
     [("popup_name", "care_record_detail"), "record_open_id", "detail_visit_id", "dwell_seconds"], ""),
    # ---- 照護記錄
    ("照護記錄視窗", "view_popup", "點擊「撰寫照護記錄」、視窗顯示完成時",
     "紀錄打開照護記錄的次數",
     FORM_CR, "第幾次打開（form_open_seq）若前端無法跨頁面累計，可改由後端記錄"),
    ("照護記錄視窗", "click_button", "點擊「取消」時",
     "紀錄打開照護記錄後沒有提交就取消的次數",
     [("button_name", "care_record_cancel"), "form_open_id", "has_input", "dwell_seconds"], ""),
    ("照護記錄視窗", "click_button", "點擊右上角「×」關閉時",
     "紀錄打開照護記錄後沒有提交就關閉的次數",
     [("button_name", "care_record_close"), "form_open_id", "has_input", "dwell_seconds"], ""),
    ("照護記錄視窗", "leave_page", "照護記錄視窗開著時，直接離開頁面、切換個案或重新整理時",
     "紀錄沒有提交也沒有關閉就離開的次數",
     [("popup_name", "care_record_form"), "form_open_id", "has_input", "dwell_seconds"], ""),
    ("照護記錄視窗", "submit_form", "點擊「完成處理」、系統回傳結果時",
     "紀錄照護記錄提交成功或失敗、是否空白提交、填了多少字",
     [("form_type", "care_record"), "form_open_id", "form_open_seq", "total_open_count", "result", "error_code", "is_empty", "text_length", "alert_level", "alert_items", "result_type", "dwell_seconds"],
     "不送填寫內容，只送字數；result_type 需確認照護記錄是否有欄位能區分誤報"),
    # ---- 醫師建議
    ("醫師建議視窗", "view_popup", "點擊「醫師建議」、視窗顯示完成時",
     "紀錄打開醫師建議的次數",
     FORM_DA, ""),
    ("醫師建議視窗", "click_button", "點擊「取消」時",
     "紀錄打開醫師建議後沒有提交就取消的次數",
     [("button_name", "doctor_advice_cancel"), "form_open_id", "has_input", "dwell_seconds"], ""),
    ("醫師建議視窗", "click_button", "點擊右上角「×」關閉時",
     "紀錄打開醫師建議後沒有提交就關閉的次數",
     [("button_name", "doctor_advice_close"), "form_open_id", "has_input", "dwell_seconds"], ""),
    ("醫師建議視窗", "leave_page", "醫師建議視窗開著時，直接離開頁面、切換個案或重新整理時",
     "紀錄沒有提交也沒有關閉就離開的次數",
     [("popup_name", "doctor_advice_form"), "form_open_id", "has_input", "dwell_seconds"], ""),
    ("醫師建議視窗", "submit_form", "點擊「完成處理」、系統回傳結果時",
     "紀錄醫師建議提交成功或失敗、是否空白提交、填了多少字",
     [("form_type", "doctor_advice"), "form_open_id", "form_open_seq", "total_open_count", "result", "error_code", "is_empty", "text_length", "dwell_seconds"],
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

wb.save(OUT)
print("saved", OUT, "events", len(E))
