# -*- coding: utf-8 -*-
"""產生「大家醫平台 埋點 DRD」Excel（沿用 CoDoctor DRD 範本格式）。
修改內容後重新執行：python3 docs/drd/build_dajiayi_drd.py"""
import os
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils import get_column_letter

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "大家醫平台_埋點DRD_v0.2.xlsx")
TBC = "【待確認】"
HDR_FILL = PatternFill("solid", fgColor="1F3A5F")
HDR_FONT = Font(bold=True, color="FFFFFF")
SEC_FILL = PatternFill("solid", fgColor="DCE6F1")
TBC_FILL = PatternFill("solid", fgColor="FFF2CC")
thin = Side(style="thin", color="BFBFBF")
BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)
WRAP = Alignment(wrap_text=True, vertical="top")
NUM = "{{number}}, e.g. "

wb = Workbook()
wb.remove(wb.active)


def header(ws, headers):
    ws.append(headers)
    for c in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=c)
        cell.fill, cell.font, cell.border = HDR_FILL, HDR_FONT, BORDER
        cell.alignment = Alignment(wrap_text=True, vertical="center")


def style_row(ws, i, n):
    for c in range(1, n + 1):
        cell = ws.cell(row=i, column=c)
        cell.alignment, cell.border = WRAP, BORDER
        if isinstance(cell.value, str) and TBC in cell.value:
            cell.fill = TBC_FILL


def widths(ws, ws_w):
    for i, w in enumerate(ws_w, 1):
        ws.column_dimensions[get_column_letter(i)].width = w


# =====================================================================
# 章節與前綴
# =====================================================================
CHAPTERS = [
    ("0.0 全域屬性", "GLOBAL_", "所有事件都帶的屬性；跨章節共用的事件也在此定義"),
    ("0.1 後端事件（警報與轉診紀錄）", "SERVER_", "由後端記錄，不是前端埋點"),
    ("1.0 護理師｜發現異常：警報是否被看到", "EXPOSE_", "對應報告「01 發現異常 問題1」"),
    ("1.1 護理師｜發現異常：通知內的其他操作", "NOTIFY_", "對應報告「01 發現異常 問題2」"),
    ("1.2 護理師｜發現異常：警報是否引導進入詳情", "ENTER_", "對應報告「01 發現異常 問題3」"),
    ("2.0 護理師｜排查異常：主要查看哪些健康資訊", "DETAIL_", "對應報告「02 排查異常 問題1」"),
    ("2.1 護理師｜排查異常：影響排查效率的行為", "TOOL_", "對應報告「02 排查異常 問題2」"),
    ("3.0 護理師｜完成處置：是否都有被處理", "FORM_", "對應報告「03 完成異常處置 問題1」"),
    ("3.1 護理師｜完成處置：處理花費時間", "（不另外埋點）", "以 SERVER_、ENTER_03、FORM_ 的時間差計算"),
    ("3.2 護理師｜完成處置：影響處理完成的行為", "（沿用 FORM_）", "對應報告「03 完成異常處置 問題3」"),
    ("4.0 醫師｜接收轉診：轉診曝光與介入", "（沿用 EXPOSE_、ENTER_）", "以 item_type = referral 區分"),
    ("5.0 醫師｜評估病情：主要查閱哪些資訊", "DOC_", "生理體徵頁籤沿用 DETAIL_01；心電沿用 TOOL_"),
    ("6.0 醫師｜完成轉診處置", "（沿用 FORM_）", "以 form_type = doctor_advice 區分"),
]

# =====================================================================
# 屬性字典：key -> (屬性定義, 型別, 範例值, 優先級)
# 同一個 key 全文件只有一個定義；事件內可用 (key, 範例覆寫, 定義覆寫) 調整
# =====================================================================
P = {
    # 全域
    "user_id": ("登入後的使用者唯一識別碼", "String", "u_10293", "高"),
    "user_role": ("帳號權限角色；分析時只計 provider（醫護人員），排除管理者帳號", "String", "super_admin, sub_org_admin, provider", "高"),
    "provider_type": ("醫護人員職類；user_role = provider 時才有值", "String", "nurse, case_manager, doctor, null", "高"),
    "org_id": ("使用者當下所選機構的識別碼", "String", "org_001", "高"),
    "page_name": ("頁面名稱", "String", "patient_detail", "高"),
    "platform_version": ("平台前端版本號；判斷數據變化是否與改版有關", "String", "7.0.3", "高"),
    "browser": ("瀏覽器名稱與主版本", "String", "chrome_130, edge_130, safari_18", "低"),
    "viewport_height": ("瀏覽器可視高度（px）", "Integer", NUM + "900", "中"),
    # 後端
    "alert_event_id": ("警報事件識別碼；同一個案在未處理期間的多筆警報合併為同一個，處理後再發生即為新的", "String", "ae_5521", "高"),
    "task_id": ("處理任務識別碼", "String", "tk_8830", "中"),
    "referral_id": ("轉診紀錄識別碼", "String", "rf_301", "高"),
    "patient_id": ("個案識別碼（平台內部 ID，不送姓名、證號）", "String", "p_88231", "高"),
    "alert_level": ("警報等級", "String", "high_risk, low_risk, abnormal_report", "高"),
    "alert_items": ("警報項目，多個以逗號分隔", "String", "blood_pressure,ecg", "中"),
    "device_source": ("產生警報的量測設備", "String", "monitor_home, monitor_pro, watch", "中"),
    "created_at": ("產生時間（伺服器時間，ISO 8601）", "String", "2026-11-04T10:15:30+08:00", "高"),
    "resolved_at": ("消除／處理完成時間（伺服器時間，ISO 8601）", "String", "2026-11-04T13:02:11+08:00", "高"),
    "resolve_type": ("消除方式", "String", "care_record, referral", "高"),
    "resolved_by_user_id": ("完成處理的使用者", "String", "u_10293", "中"),
    "referrer_user_id": ("發起轉診的護理師", "String", "u_10293", "中"),
    "doctor_user_id": ("受轉診的醫師", "String", "u_20011", "高"),
    # 通知與列表
    "popup_name": ("彈窗名稱", "String", "notification_center", "高"),
    "notify_session_id": ("本次通知彈窗的識別碼；每次打開時產生，關閉時結束", "String", "ns_4k2p9a", "高"),
    "notify_tab": ("通知分頁", "String", "abnormal_alert, referral", "高"),
    "unread_count": ("打開當下該分頁的未讀數；取不到時送 null，不要送 0", "Integer", NUM + "12", "中"),
    "list_name": ("曝光所在的清單", "String", "notification_alert, notification_referral", "高"),
    "list_view_id": ("本次列表瀏覽的識別碼；每次進入或切換列表時產生", "String", "lv_7d1c3e", "高"),
    "list_type": ("待處理列表類型", "String", "high_risk, abnormal_report, low_risk, custom_plan_unmeasured, doctor_pending", "高"),
    "list_total_count": ("列表載入當下的項目總數", "Integer", NUM + "37", "中"),
    "item_type": ("曝光或點擊的項目類型", "String", "alert, referral", "高"),
    "item_id": ("曝光或點擊的項目識別碼：item_type = alert 時為 alert_event_id，referral 時為 referral_id", "String", "ae_5521, rf_301", "高"),
    "source_filter": ("曝光當下所選的通知來源", "String", "all, monitor, watch", "中"),
    "position": ("項目在清單中的位置，從 1 起算", "Integer", NUM + "3", "中"),
    "page_index": ("列表頁碼，從 1 起算", "Integer", NUM + "1", "低"),
    "entry_source": ("進入來源", "String", "nav_menu, notification_shortcut, workspace", "高"),
    "button_name": ("按鈕名稱", "String", "", "高"),
    "from_source": ("切換前的來源", "String", "all, monitor, watch", "高"),
    "to_source": ("切換後的來源", "String", "all, monitor, watch", "高"),
    "target_list": ("點擊前往的列表", "String", "high_risk, abnormal_report, custom_plan_unmeasured, low_risk", "高"),
    "target_list_count": ("點擊當下目標列表的項目數；0 代表空列表", "Integer", NUM + "0", "中"),
    # 個案詳情
    "detail_visit_id": ("本次個案詳情訪問的識別碼；每次進入個案詳情時產生，離開時結束", "String", "dv_5h2k8m", "高"),
    "has_pending_alert": ("進入當下個案是否有未處理的警報事件", "Boolean", "true, false", "高"),
    "pending_alert_items": ("未處理的警報項目，多個以逗號分隔；沒有時為 null", "String", "null, blood_pressure,ecg", "中"),
    "has_pending_referral": ("進入當下個案是否有未處理的轉診", "Boolean", "true, false", "高"),
    "tabs_with_data": ("進入當下有資料的頁籤，多個以逗號分隔", "String", "health_plan,care_records", "高"),
    "has_todo": ("是否有待辦事項（會自動跳出待辦彈窗）", "Boolean", "true, false", "中"),
    "default_tab": ("進入時預設顯示的頁籤", "String", "vital_blood_pressure", "低"),
    "tab_group": ("頁籤群組", "String", "info, vital_sign", "高"),
    "tab_name": ("頁籤名稱", "String", "health_plan, care_records, patient_reports, vital_blood_pressure, vital_ecg …", "高"),
    "metric": ("生理體徵；代碼與警報項目一致", "String", "blood_pressure, ecg, spo2, blood_glucose, heart_rate, body_temp …", "高"),
    "has_data": ("該頁籤是否有資料", "Boolean", "true, false", "高"),
    "is_pending_abnormal": ("該生理體徵是否為未處理的警報項目；非生理體徵頁籤為 null", "Boolean", "true, false, null", "高"),
    "dwell_seconds": ("顯示到離開的秒數；瀏覽器分頁隱藏期間不計", "Integer", NUM + "8", "高"),
    "leave_reason": ("離開頁籤的原因", "String", "switch_tab, leave_page, page_hidden", "低"),
    "open_type": ("開啟方式", "String", "auto, manual", "高"),
    "open_seq": ("本次訪問中第幾次開啟，從 1 起算", "Integer", NUM + "2", "高"),
    "todo_types": ("待辦類型，多個以逗號分隔", "String", "referral_opinion, doctor_advice, follow_up", "中"),
    # 排查工具
    "range_option": ("選擇的時間範圍", "String", "today, last_7d, last_30d, last_1y, custom", "高"),
    "custom_range_days": ("自訂區間的天數；非自訂時為 null", "Integer", "null, {{number}}, e.g. 14", "中"),
    "lead": ("目前顯示的心電導程", "String", "I, II, III …", "中"),
    "block_name": ("心電頁的區塊名稱", "String", "ecg_summary, ecg_chart, ecg_record_list …", "高"),
    "visible_seconds": ("該區塊在可視範圍內（露出 ≥50%）的累計秒數", "Integer", NUM + "12", "高"),
    "filter_type": ("篩選類型", "String", "lead, abnormal", "高"),
    "filter_value": ("篩選條件", "String", "II, af", "中"),
    "result_count": ("套用篩選後的結果筆數", "Integer", NUM + "6", "低"),
    # 處置表單
    "form_type": ("處置表單類型", "String", "care_record, referral, doctor_advice", "高"),
    "form_open_id": ("本次表單開啟的識別碼；每次打開時產生，用來配對關閉與提交", "String", "fo_2b9x7q", "高"),
    "form_open_seq": ("同一警報事件（或轉診）中，第幾次打開同一種表單；1 = 首次，≥2 = 復開", "Integer", NUM + "1", "高"),
    "close_method": ("關閉方式", "String", "cancel, close_icon, mask", "中"),
    "has_input": ("關閉時是否有任何欄位已輸入內容", "Boolean", "true, false", "中"),
    "result": ("提交結果", "String", "success, fail", "高"),
    "error_code": ("失敗時 API 回傳的錯誤代碼；成功時為 null", "String", "null, E4001", "中"),
    "total_open_count": ("從首次打開到本次提交，累計打開這張表單的次數", "Integer", NUM + "2", "高"),
    "is_empty": ("提交時是否所有欄位都沒有內容", "Boolean", "true, false", "高"),
    "text_length": ("主文字欄位（照護建議／轉診意見／醫師建議）的字數；不送內容本身", "Integer", NUM + "42", "高"),
    # 醫師
    "record_open_id": ("本次處理紀錄詳情開啟的識別碼", "String", "ro_6m1v8k", "高"),
    "record_rank": ("點擊的是第幾筆處理紀錄，依時間由新到舊、從 1 起算", "Integer", NUM + "1", "中"),
    "record_type": ("處理紀錄類型", "String", "care_record, referral, doctor_advice", "中"),
    "record_created_at": ("該筆處理紀錄的產生時間（ISO 8601）", "String", "2026-10-28T09:20:00+08:00", "中"),
}

# =====================================================================
# 事件：(章節, 編號, 頁面/區塊, 事件名稱, 觸發時機, 目標/分析意義, 對應報告指標, [屬性...], 備注)
# 屬性可寫 key，或 (key, 範例覆寫) / (key, 範例覆寫, 定義覆寫)
# =====================================================================
E = [
    ("0.0 全域屬性", "GLOBAL_01", "Global property 全域屬性", "所有事件", "每一筆事件發送時帶入",
     "辨識操作者與機構，讓「按人」計算的指標能去重、各章節能依角色與機構拆分",
     "全部指標的去重與拆分依據",
     ["user_id", "user_role", "provider_type", "org_id", "page_name", "platform_version", "browser", "viewport_height"],
     "分析時只計 user_role = provider；護理師與醫師以 provider_type 區分。" + TBC + "provider 之下是否有職類欄位（護理師／個管師／醫師）？若沒有，醫師端指標改以「是否為受轉診醫師」判斷。\n"
     "多機構帳號的 org_id 以當下所選機構為準；場域類型（日照、居家、HaH、遠距中心）由後台機構主檔依 org_id 對應，不另外埋點。\n"
     "事件時間一律以收集端收到的伺服器時間計算時長；時區 +08:00"),

    ("0.1 後端事件（警報與轉診紀錄）", "SERVER_01", "後端／警報", "alert_created", "規則引擎判定異常、正式產生警報事件時（伺服器時間）",
     "所有警報相關指標的分母與起點", "1.0 ①②③ 分母（警報）\n1.2 ① 分母（警報）\n3.0 ① 分母（警報）\n3.1 ①② 起點",
     ["alert_event_id", "task_id", "patient_id", "org_id", "alert_level", "alert_items", "device_source", "created_at"],
     "可以用後端資料表每日匯出代替事件。同一個案已有未處理的警報事件時，新的警報項目併入原事件，不另外產生。\n" + TBC + "「警報事件 id」與報告提到的「任務 id」是否同一個？若不同，兩者是 1 對 1 還是 1 對多？\n" + TBC + "一個警報事件同時含高、低風險項目時，alert_level 是否取最高等級？"),
    ("0.1 後端事件（警報與轉診紀錄）", "SERVER_02", "後端／警報", "alert_resolved", "照護記錄或轉診醫師提交成功、警報被消除時",
     "判斷警報是否完成處理與完成時間", "3.0 ① 分子（警報）\n3.1 ① 終點",
     ["alert_event_id", "patient_id", "resolve_type", "resolved_by_user_id", "resolved_at"],
     TBC + "轉診醫師提交後，警報是否立即消除？報告把轉診也算進護理師的處理閉環"),
    ("0.1 後端事件（警報與轉診紀錄）", "SERVER_03", "後端／轉診", "referral_created", "護理師轉診醫師提交成功、後端產生轉診紀錄時",
     "醫師端所有指標的分母與起點", "4.0 ①②③④ 分母（轉診）\n6.0 ① 分母、② 起點",
     ["referral_id", "alert_event_id", "patient_id", "referrer_user_id", "doctor_user_id", "created_at"],
     TBC + "一筆轉診可以同時轉給多位醫師嗎？"),
    ("0.1 後端事件（警報與轉診紀錄）", "SERVER_04", "後端／轉診", "referral_resolved", "醫師建議提交成功、轉診被標記為已處理時",
     "判斷轉診是否完成處理與完成時間", "6.0 ① 分子（轉診）\n6.0 ② 終點",
     ["referral_id", "resolved_by_user_id", "resolved_at"], ""),

    ("1.0 護理師｜發現異常：警報是否被看到", "EXPOSE_01", "頂部小鈴鐺／最新通知彈窗", "view_popup",
     "點擊鈴鐺、通知彈窗顯示完成時；在彈窗內切換「異常提醒／轉診提醒」分頁時也送一筆",
     "作為一次通知查看的起點；計算 1.1 的分母", "1.1 ①② 分母（開啟）",
     [("popup_name", "notification_center"), "notify_session_id", "notify_tab", "unread_count"],
     "跨章節共用：醫師的轉診提醒也用本事件（notify_tab = referral）。每次打開產生新的 notify_session_id，切換分頁沿用。" + TBC + "彈窗打開時預設停在哪一個分頁？"),
    ("1.0 護理師｜發現異常：警報是否被看到", "EXPOSE_02", "最新通知彈窗／通知卡片", "item_impression",
     "通知卡片露出 ≥50% 進入可視範圍時；打開彈窗時首屏可見的卡片立即送出，之後捲入的卡片再送",
     "計算警報（與轉診）在通知中被看到的比例", "1.0 ①② 分子（警報）\n4.0 ①② 分子（轉診）",
     [("list_name", "notification_alert, notification_referral"), "notify_session_id", "item_type", "item_id", "patient_id",
      ("alert_level", "high_risk, low_risk, abnormal_report, null", "警報等級；item_type = referral 時為 null"), "source_filter", "position"],
     "一則卡片送一筆；同一個 notify_session_id 內同一個 item_id 只送一次（往回捲不重送）。報告要的「曝光個案數」由分析端計數，不另外帶。\n" + TBC + "曝光是否要加停留門檻（例如 ≥500ms）？"),
    ("1.0 護理師｜發現異常：警報是否被看到", "EXPOSE_03", "待處理列表", "view_page",
     "待處理列表資料載入完成時；切換列表分頁時也送一筆", "計算列表的進入次數；作為列表曝光的瀏覽單位", "1.0 ③ 輔助（列表瀏覽）\n4.0 ③ 輔助",
     [("page_name", "pending_list"), "list_view_id", "list_type", "list_total_count", ("entry_source", "nav_menu, notification_shortcut, workspace", "進入列表的來源")],
     "跨章節共用：醫師的「待醫師處理列表」也用本事件（list_type = doctor_pending）。" + TBC + "列表分頁完整清單；「自訂計劃未測量列表」是否納入警報曝光？"),
    ("1.0 護理師｜發現異常：警報是否被看到", "EXPOSE_04", "待處理列表／列表項目", "item_impression",
     "列表項目露出 ≥50% 進入可視範圍時，包含載入、捲動、翻頁後看到的項目",
     "計算警報（與轉診）在列表中被看到的比例", "1.0 ①③ 分子（警報）\n4.0 ①③ 分子（轉診）",
     [("list_name", "high_risk, abnormal_report, low_risk, doctor_pending", "曝光所在的列表"), "list_view_id", "item_type", "item_id", "patient_id",
      ("alert_level", "high_risk, low_risk, abnormal_report, null", "警報等級；item_type = referral 時為 null"), "position", "page_index"],
     "一個項目送一筆；同一個 list_view_id 內同一個 item_id 只送一次。報告原本只算「載入時」視窗內的項目，這裡改成含捲動與翻頁，避免低估"),

    ("1.1 護理師｜發現異常：通知內的其他操作", "NOTIFY_01", "最新通知彈窗／來源篩選", "click_button",
     "點擊來源篩選（全部／CoDoctor 檢測儀／CoDoctor Watch）、通知列表更新後", "判斷警報來源是否影響查看順序", "① 分子（開啟）",
     [("button_name", "alert_source_filter"), "notify_session_id", "from_source", "to_source"],
     "點擊目前已選的來源時不送。分析時以 notify_session_id 去重，避免一次開啟切換多次讓比率超過 100%"),
    ("1.1 護理師｜發現異常：通知內的其他操作", "NOTIFY_02", "最新通知彈窗／前往列表", "click_button",
     "點擊「前往高風險列表／異常上報列表／自訂計劃未測量列表／低風險列表」的當下", "判斷通知中的快捷入口是否有引流效果；以及是否點到空列表", "② 分子（開啟）",
     [("button_name", "goto_list"), "notify_session_id", "target_list", "target_list_count"],
     "target_list_count 對應報告「點擊時該列表人數」；= 0 時代表點到空列表"),

    ("1.2 護理師｜發現異常：警報是否引導進入詳情", "ENTER_01", "最新通知彈窗／通知卡片", "click_button",
     "點擊通知卡片的當下", "記錄從通知點進詳情的位置與項目", "① 輔助（警報）\n4.0 ④ 輔助（轉診）",
     [("button_name", "notification_card"), "notify_session_id", "item_type", "item_id", "patient_id", "task_id", "position"],
     "介入率以 ENTER_03 計算；本事件用來看點擊位置，以及點擊後有沒有成功進入詳情"),
    ("1.2 護理師｜發現異常：警報是否引導進入詳情", "ENTER_02", "待處理列表／列表項目", "click_button",
     "點擊列表列或「查看」按鈕的當下", "記錄從列表點進詳情的位置與項目", "① 輔助（警報）\n4.0 ④ 輔助（轉診）",
     [("button_name", "list_row, view_detail"), "list_view_id", "list_type", "item_type", "item_id", "patient_id", "task_id", "position", "page_index"], ""),
    ("1.2 護理師｜發現異常：警報是否引導進入詳情", "ENTER_03", "個案詳情", "view_page",
     "個案詳情資料載入完成時", "計算進入詳情的警報（與轉診）數；作為 2.x 的分母、3.1 的介入時間點", 
     "① 分子（警報）\n2.0 ①② 分母\n2.1 ①② 分母\n3.0 ②③ 分母（警報）\n3.1 ②③ 時間點\n4.0 ④ 分子（轉診）\n5.0 ①② 分母\n6.0 ① 分母",
     [("page_name", "patient_detail"), "detail_visit_id", "patient_id",
      ("entry_source", "notification_alert, notification_referral, alert_list, doctor_pending_list, patient_list, reload, other", "進入個案詳情的來源（報告的「進入前頁面」）"),
      ("alert_event_id", "null, ae_5521", "個案當下未處理的警報事件；沒有時為 null"), ("referral_id", "null, rf_301", "個案當下未處理的轉診；沒有時為 null"), "task_id",
      "has_pending_alert", "pending_alert_items", "has_pending_referral", "tabs_with_data", "has_todo", "default_tab"],
     "跨章節共用事件，於此統一定義。每次進入產生新的 detail_visit_id。alert_event_id、referral_id 不論從哪個入口進來都要帶，否則從個案列表進入後的處理會漏算。\n"
     "tabs_with_data、has_todo 用來限定 2.0 的分母（只算該頁籤有資料、有待辦的訪問）。\n" + TBC + "所有可以進入個案詳情的入口清單"),

    ("2.0 護理師｜排查異常：主要查看哪些健康資訊", "DETAIL_01", "個案詳情／頁籤", "leave_tab",
     "切換到其他頁籤、離開詳情頁，或瀏覽器分頁被隱藏時，送出本次在該頁籤的停留秒數",
     "計算各頁籤的有效查看（停留 ≥5 秒且有資料）；醫師端判斷是否查看待處理異常的生理體徵", "① 分子（訪問）\n2.1 ①③④ 分母條件\n5.0 ① 分子（訪問）",
     ["detail_visit_id", "patient_id", "tab_group", "tab_name", "metric", "has_data", "is_pending_abnormal", "dwell_seconds", "leave_reason"],
     "跨章節共用：2.1 心電、檢測儀切換的分母，與 5.0 生理體徵查看都用本事件。停留不到 1 秒（快速切過）不送。≥5 秒、≥3 秒等門檻由分析端判斷，前端照實送秒數。\n" + TBC + "頁籤完整清單（資訊類＋生理體徵類）與代碼"),
    ("2.0 護理師｜排查異常：主要查看哪些健康資訊", "DETAIL_02", "個案詳情／待辦事項彈窗", "view_popup",
     "進入詳情時自動跳出，或點擊「全部內容」再次開啟，彈窗顯示完成時", "判斷護理師（醫師）是否需要再次打開待辦內容", "② 分子／分母（訪問）\n5.0 ③ 分子／分母",
     [("popup_name", "todo_popup"), "detail_visit_id", "patient_id", "open_type", "open_seq", "todo_types", "has_pending_alert", "pending_alert_items"],
     "分母＝open_type = auto 的訪問；分子＝同一訪問中有 open_type = manual"),
    ("2.0 護理師｜排查異常：主要查看哪些健康資訊", "DETAIL_03", "個案詳情／待辦事項彈窗", "close_popup",
     "點擊關閉或點擊彈窗外部、彈窗關閉時", "記錄待辦彈窗的停留時間", "② 輔助",
     [("popup_name", "todo_popup"), "detail_visit_id", "open_type", "open_seq", "dwell_seconds"], ""),

    ("2.1 護理師｜排查異常：影響排查效率的行為", "TOOL_01", "個案詳情／檢測儀頁籤／數據來源", "click_button",
     "點擊 Home／Pro、圖表更新後", "判斷 Home、Pro 來源切換的實際需求，評估是否可以移除", "① 分子（人）",
     [("button_name", "monitor_source"), "detail_visit_id", "patient_id", "metric", ("from_source", "home, pro"), ("to_source", "home, pro")],
     "點擊目前已選的來源時不送。分母的「機構同時有 Home 與 Pro」由後台機構主檔（出貨設備）取得，不另外埋點"),
    ("2.1 護理師｜排查異常：影響排查效率的行為", "TOOL_02", "個案詳情／時間範圍篩選", "click_button",
     "點擊今日／近 7 天／近 30 天／近 1 年，或在自訂日期選擇器按確認、圖表更新後", "判斷預設的近 30 天是否符合需求，以及最常用的區間", "② 分子（訪問）",
     [("button_name", "time_range"), "detail_visit_id", "metric", "range_option", "custom_range_days"], "預設為近 30 天；點擊目前已選的選項時不送"),
    ("2.1 護理師｜排查異常：影響排查效率的行為", "TOOL_03", "個案詳情／心電頁籤／各區塊", "view_block",
     "離開心電頁籤時，每個區塊送一筆本次的累計可視秒數", "了解心電各區塊實際被看的程度，作為調整資訊排序的依據", "③ 分子（秒）",
     ["detail_visit_id", "lead", "block_name", "visible_seconds"],
     "單一區塊累計不到 3 秒不送。分母＝DETAIL_01 tab_name = vital_ecg 的 dwell_seconds。\n" + TBC + "報告用「滑鼠停留」判斷，這裡建議改用「可視範圍停留」：看圖時滑鼠常停在旁邊，用滑鼠量不準。需確認採用哪一種，以及區塊清單"),
    ("2.1 護理師｜排查異常：影響排查效率的行為", "TOOL_04", "個案詳情／心電頁籤／紀錄篩選", "apply_filter",
     "實際套用導程或異常條件、心電紀錄列表更新後", "判斷心電篩選的使用率，評估是否收合成進階搜尋", "④ 分子（人）\n5.0 輔助",
     ["detail_visit_id", "filter_type", "filter_value", "result_count"],
     "條件沒有變動時不送。分母改為「進入心電頁籤的人」（報告原本是進入個案詳情的人）。" + TBC + "導程與異常篩選的完整值域"),

    ("3.0 護理師｜完成處置：是否都有被處理", "FORM_01", "個案詳情／處置按鈕／表單彈窗", "view_popup",
     "點擊「撰寫照護記錄」「轉診醫師」「醫師建議」後，彈窗顯示完成時", "計算表單發起數；作為提交率、首次直接提交率、時長的起點",
     "②③ 分子（警報）\n④ 分母（警報）\n3.1 ③④ 時間點\n3.2 ①②③④ 分母\n6.0 ①②③ 同上",
     [("popup_name", "handle_form"), "form_type", "form_open_id", "form_open_seq", "detail_visit_id", "patient_id",
      ("alert_event_id", "null, ae_5521", "本次處理的警報事件"), ("referral_id", "null, rf_301", "本次處理的轉診；醫師建議時必帶"), "task_id"],
     "跨章節共用：3.2 與 6.0 都用本事件。每次打開產生新的 form_open_id。\n"
     "form_open_seq 需要跨頁面、跨重新整理累計，前端不容易算準：建議由後端記錄開啟次數；做不到時前端送 null，由分析端依時間順序計算"),
    ("3.0 護理師｜完成處置：是否都有被處理", "FORM_02", "表單彈窗", "close_popup",
     "點擊「取消」、右上角關閉，或點擊遮罩關閉時", "計算中途關閉與之後是否復開", "3.2 ②③ 分子（開啟）",
     [("popup_name", "handle_form"), "form_type", "form_open_id", "form_open_seq", "close_method", "has_input", "dwell_seconds"],
     "提交成功後自動關閉的情況不送"),
    ("3.0 護理師｜完成處置：是否都有被處理", "FORM_03", "表單彈窗／完成處理", "submit_form",
     "點擊「完成處理」、API 回傳結果時（成功、失敗都送）", "計算表單提交成功數、空提交與填寫字數",
     "④ 分子（警報）\n3.1 ④ 終點\n3.2 ①④⑤⑥ 分子\n6.0 ①②③ 同上",
     ["form_type", "form_open_id", "form_open_seq", "total_open_count", "result", "error_code", "is_empty", "text_length",
      ("alert_level", "high_risk, low_risk, abnormal_report, null", "提交時的警報等級"), ("alert_items", "blood_pressure,ecg, null", "提交時的警報項目，多個以逗號分隔"), "dwell_seconds"],
     "前端欄位檢核沒通過、沒有呼叫 API 時不送。不送任何填寫內容，只送字數與是否空白（醫療個資）。\n處理閉環以 SERVER_02、SERVER_04 為準，本事件用來看表單層的行為"),

    ("5.0 醫師｜評估病情：主要查閱哪些資訊", "DOC_01", "個案詳情／處理紀錄頁籤／紀錄詳情", "view_popup",
     "點擊單筆處理紀錄、詳情顯示完成時", "了解醫師在提出建議前是否查閱過往處理紀錄", "② 分子（訪問）",
     [("popup_name", "care_record_detail"), "record_open_id", "detail_visit_id", "patient_id", "record_rank", "record_type", "record_created_at", "has_pending_alert"],
     "報告的「個案異常時間」由 SERVER_01 依 patient_id 對應，不另外帶。查看與寫建議的先後，以本事件和 FORM_01（form_type = doctor_advice）的時間比較"),
    ("5.0 醫師｜評估病情：主要查閱哪些資訊", "DOC_02", "個案詳情／處理紀錄頁籤／紀錄詳情", "close_popup",
     "關閉處理紀錄詳情時", "判斷是否為有效查看（≥5 秒）", "② 分子條件",
     [("popup_name", "care_record_detail"), "record_open_id", "detail_visit_id", "dwell_seconds"], "≥5 秒的門檻由分析端判斷"),
]

# =====================================================================
# 指標對照：(章節, 指標, 類型／單位, 計算方式, 分子, 分母, 去重／計算規則, 對應事件, 對應情境)
# =====================================================================
M = [
    ("1.0 護理師｜發現異常：警報是否被看到", "① 警報曝光率（整體）", "主指標／警報", "至少被曝光 1 次的警報事件數 ÷ 期間內產生的警報事件數；另計重複曝光率＝兩個入口都曝光過 ÷ 已曝光",
     "item_impression（EXPOSE_02、EXPOSE_04）\nitem_type = alert\n曝光時間早於 alert_resolved", "alert_created\n期間內產生", "跨入口重複曝光只算 1 次；只計 user_role = provider", "分子：EXPOSE_02、04\n分母：SERVER_01", "A：=100%，看重複曝光，>50% 考慮入口單一化\nB：<100%，判斷是警報太多還是沒看到"),
    ("1.0 護理師｜發現異常：警報是否被看到", "② 警報曝光率（消息通知）", "主指標／警報", "在通知彈窗被曝光的警報事件數 ÷ 期間內產生的警報事件數",
     "item_impression\nlist_name = notification_alert", "alert_created", "同入口重複曝光只算 1 次", "分子：EXPOSE_02\n分母：SERVER_01", "A：>80%，維持設計\nB：<50%，看其他入口；也 <50% 則加強通知提示"),
    ("1.0 護理師｜發現異常：警報是否被看到", "③ 警報列表曝光率（高風險／異常上報／低風險）", "主指標／警報", "在該列表被曝光的警報事件數 ÷ 期間內產生的警報事件數；另計三個列表合計",
     "item_impression\nlist_name = high_risk / abnormal_report / low_risk", "alert_created（合計口徑）\n另提供分級口徑：分母只算該等級警報", "同入口只算 1 次；含捲動與翻頁", "分子：EXPOSE_04\n分母：SERVER_01", "A：合計 >80%，主動規律處理\nB：合計 <10%，可能不知道有列表"),
    ("1.1 護理師｜發現異常：通知內的其他操作", "① 消息通知來源篩選使用率", "主指標／開啟", "有切換來源的通知開啟次數 ÷ 異常提醒開啟次數",
     "click_button button_name = alert_source_filter\n以 notify_session_id 去重", "view_popup popup_name = notification_center\nnotify_tab = abnormal_alert", "同一次開啟切換多次只算 1 次（報告原為次數 ÷ 次數，可能超過 100%）", "分子：NOTIFY_01\n分母：EXPOSE_01", "A：>50%，維持\nB：<50%，弱化或移除來源篩選"),
    ("1.1 護理師｜發現異常：通知內的其他操作", "② 快捷入口點擊率", "主指標／開啟", "有點擊「前往列表」的通知開啟次數 ÷ 異常提醒開啟次數；另計各列表點擊分布、空列表點擊佔比",
     "click_button button_name = goto_list\n空列表：target_list_count = 0", "同 ① 分母", "同一次開啟只算 1 次；分布以點擊次數計", "分子：NOTIFY_02\n分母：EXPOSE_01", "A：>50%，保留並依分布調整\nB：<50%，弱化入口"),
    ("1.2 護理師｜發現異常：警報是否引導進入詳情", "① 警報介入率", "主指標／警報", "有從通知或待處理列表進入個案詳情的警報事件數 ÷ 期間內產生的警報事件數；另計曝光後介入率＝介入數 ÷ 1.0 ① 分子",
     "view_page page_name = patient_detail\nentry_source ∈ notification_alert, alert_list\nalert_event_id ∈ 分母", "alert_created", "同一警報事件多次進入只算 1 次；進入時間早於 alert_resolved", "分子：ENTER_03\n分母：SERVER_01", "A：=100%，無斷點\nB：<100% 且曝光 =100%，看了沒點；曝光 <100%，先優化曝光"),
    ("2.0 護理師｜排查異常：主要查看哪些健康資訊", "① 單一頁籤有效查看率", "主指標／訪問", "有效查看該頁籤的詳情訪問數 ÷ 有待處理異常且該頁籤有資料的詳情訪問數",
     "leave_tab\ntab_name = health_plan / care_records / patient_reports\ndwell_seconds ≥ 5 且 has_data = true", "view_page patient_detail\nhas_pending_alert = true\ntabs_with_data 含該頁籤", "以 detail_visit_id 去重", "分子：DETAIL_01\n分母：ENTER_03", "A：<20%，訪談原因\nB：20–60%，維持\nC：>60%，提高資訊層級"),
    ("2.0 護理師｜排查異常：主要查看哪些健康資訊", "② 待辦資訊再次查看率", "主指標／訪問", "有手動再次開啟待辦的詳情訪問數 ÷ 有自動跳出待辦的詳情訪問數",
     "view_popup popup_name = todo_popup\nopen_type = manual", "view_popup popup_name = todo_popup\nopen_type = auto", "以 detail_visit_id 去重；依 todo_types 拆分", "DETAIL_02", "A：>30%，保留固定區塊\nB：<30%，收合到其他頁籤"),
    ("2.1 護理師｜排查異常：影響排查效率的行為", "① 檢測儀數據來源切換率", "主指標／人", "有切換 Home／Pro 的不重複使用者數 ÷ 在檢測儀頁籤停留 ≥5 秒、且機構同時有 Home 與 Pro 的不重複使用者數",
     "click_button button_name = monitor_source", "leave_tab tab_group = vital_sign\ndwell_seconds ≥ 5\n＋後台機構出貨設備", "以 user_id 去重", "分子：TOOL_01\n分母：DETAIL_01＋後台資料", "A：<20%，可移除\nB：21–60%，改為下拉選單\nC：>60%，維持"),
    ("2.1 護理師｜排查異常：影響排查效率的行為", "② 日期時間範圍切換率", "主指標／訪問", "有切換時間範圍的詳情訪問數 ÷ 詳情訪問數；另計各選項佔全部切換次數的比例",
     "click_button button_name = time_range", "view_page patient_detail", "以 detail_visit_id 去重；佔比以次數計（報告原為次數 ÷ 人數）", "分子：TOOL_02\n分母：ENTER_03", "A：某選項 >60%，預設區間不符需求\nB：20–60%，維持\nC：<20%，可拿掉快捷選項"),
    ("2.1 護理師｜排查異常：影響排查效率的行為", "③ 心電資訊區塊有效曝光率", "輔助判讀／秒", "各區塊可視秒數總和 ÷ 心電頁籤停留秒數總和",
     "view_block visible_seconds（≥3 秒才送）\n依 block_name 分組", "leave_tab tab_name = vital_ecg 的 dwell_seconds", "區塊可能同時可見，加總可能 >100%", "分子：TOOL_03\n分母：DETAIL_01", "A：比例高，訪談該資訊的作用\nB：比例低，先排除位置、捲動、無資料等因素"),
    ("2.1 護理師｜排查異常：影響排查效率的行為", "④ 心電紀錄篩選使用率", "主指標／人", "有套用篩選的不重複使用者數 ÷ 進入心電頁籤的不重複使用者數",
     "apply_filter", "leave_tab tab_name = vital_ecg", "以 user_id 去重（報告原為點擊次數 ÷ 進入詳情人數）", "分子：TOOL_04\n分母：DETAIL_01", "A：>30%，維持\nB：<30%，收合成進階搜尋"),
    ("3.0 護理師｜完成處置：是否都有被處理", "① 護理師處理閉環完成率", "主指標／警報", "觀察窗內被消除的警報事件數 ÷ 已滿觀察窗的警報事件數",
     "alert_resolved\nresolved_at − created_at ≤ 觀察窗", "alert_created\n已滿觀察窗", "以 alert_event_id 去重；依 resolve_type 拆分。" + TBC + "觀察窗建議 7 天", "分子：SERVER_02\n分母：SERVER_01", "A：=100%，接著看時長\nB：<100%，依序看曝光 → 介入 → 發起 → 提交"),
    ("3.0 護理師｜完成處置：是否都有被處理", "② 照護記錄填寫發起率", "主指標／警報", "有打開照護記錄的警報事件數 ÷ 有進入個案詳情的警報事件數",
     "view_popup popup_name = handle_form\nform_type = care_record", "view_page patient_detail（alert_event_id 有值）", "同一警報事件只算 1 次（報告原為點擊次數 ÷ 人數）", "分子：FORM_01\n分母：ENTER_03", "A：>80%，維持\nB：<80%，訪談處理機制或按鈕引導"),
    ("3.0 護理師｜完成處置：是否都有被處理", "③ 轉診醫師填寫發起率", "主指標／警報", "有打開轉診醫師表單的警報事件數 ÷ 有進入個案詳情的警報事件數",
     "view_popup form_type = referral", "同 ② 分母", "同 ②（報告的觸發時機誤寫為「點擊醫師建議」，已更正）", "分子：FORM_01\n分母：ENTER_03", "C：<5%，了解沒有用轉診的原因"),
    ("3.0 護理師｜完成處置：是否都有被處理", "④ 照護記錄／轉診醫師填寫提交率", "主指標／警報", "有提交成功的警報事件數 ÷ 有打開表單的警報事件數（依 form_type 分開）",
     "submit_form result = success", "view_popup popup_name = handle_form", "同一警報事件、同一 form_type 只算 1 次。報告另有「整體提交成功率」，口徑相同，已合併於此", "分子：FORM_03\n分母：FORM_01", "A：>90%，符合預期\nB：<80%，看停留時長與中途關閉"),
    ("3.1 護理師｜完成處置：處理花費時間", "① 警報處理閉環時長", "主指標／分鐘", "alert_resolved 時間 − alert_created 時間；看中位數、P75、P90（平均數只當參考）",
     "alert_resolved.resolved_at", "alert_created.created_at", "只算觀察窗內有消除的警報", "SERVER_01、02", "A：中位數 <24 小時，符合預期\nB：>48 小時，拆開 ②③④"),
    ("3.1 護理師｜完成處置：處理花費時間", "② 警報介入時長", "輔助判讀／分鐘", "第一次進入個案詳情的時間 − alert_created 時間",
     "該 alert_event_id 第一筆 view_page patient_detail", "alert_created.created_at", "只取第一次進入", "SERVER_01、ENTER_03", "閉環 >24 小時且介入佔 >50%：問題在提醒與入口"),
    ("3.1 護理師｜完成處置：處理花費時間", "③ 異常排查時長", "輔助判讀／秒", "第一次打開表單的時間 − 同一次詳情訪問的進入時間",
     "同 detail_visit_id 第一筆 view_popup handle_form", "view_page patient_detail", "以 detail_visit_id 為單位", "ENTER_03、FORM_01", "A：<3 分鐘，符合預期\nB：>5 分鐘，優化資訊取得"),
    ("3.1 護理師｜完成處置：處理花費時間", "④ 照護記錄／轉診醫師填寫時長", "輔助判讀／秒", "提交成功時間 − 該次表單打開時間",
     "submit_form result = success", "同 form_open_id 的 view_popup", "以 form_open_id 為單位", "FORM_01、03", "A：<30 秒，符合預期\nB：>90 秒，填寫負擔重"),
    ("3.2 護理師｜完成處置：影響處理完成的行為", "① 首次打開直接提交率", "主指標／開啟", "首次打開就提交成功的次數 ÷ 首次打開的次數",
     "submit_form result = success\nform_open_seq = 1", "view_popup handle_form\nform_open_seq = 1", "依 form_type 分開", "FORM_01、03", "A：>80%，維持\nB：<60%，看 ②③④"),
    ("3.2 護理師｜完成處置：影響處理完成的行為", "② 中途關閉率", "輔助判讀／開啟", "取消或關閉的次數 ÷ 表單打開次數",
     "close_popup popup_name = handle_form", "view_popup popup_name = handle_form", "以 form_open_id 計；報告轉診醫師版本的分母誤寫為「照護記錄」，已更正", "FORM_01、02", "與 ③④ 一起判讀"),
    ("3.2 護理師｜完成處置：影響處理完成的行為", "③ 關閉後復開率", "輔助判讀／警報", "中途關閉後又重新打開的警報事件數 ÷ 有中途關閉的警報事件數",
     "close_popup 之後同 alert_event_id＋form_type 有 form_open_seq ≥ 2 的 view_popup", "有 close_popup 的 alert_event_id", "依 form_type 分開", "FORM_01、02", "B-1：關閉 >40%、復開 >80%、復開後提交 >90%：需要查資料，考慮在彈窗補參考資料\nB-2：關閉 >40%、復開 <20%：內容不符預期或暫不處理"),
    ("3.2 護理師｜完成處置：影響處理完成的行為", "④ 復開後成功提交率", "輔助判讀／開啟", "復開後提交成功的次數 ÷ 復開次數",
     "submit_form result = success\nform_open_seq ≥ 2", "view_popup form_open_seq ≥ 2", "以 form_open_id 計", "FORM_01、03", "同 ③"),
    ("3.2 護理師｜完成處置：影響處理完成的行為", "⑤ 空提交率", "主指標／提交", "所有欄位都空白的成功提交數 ÷ 成功提交數",
     "submit_form result = success\nis_empty = true", "submit_form result = success", "依 form_type、alert_level 拆分", "FORM_03", "A：>40%，可加快速處理\nB：<10% 且平均 >80 字，保留填寫\nC：低風險 >50%、高風險 <10%，依風險分流程\nD：都 >40%，處理機制統一"),
    ("3.2 護理師｜完成處置：影響處理完成的行為", "⑥ 提交字數分布", "輔助判讀／字", "主文字欄位字數的中位數、P25、P75、P90（平均數只當參考）",
     "submit_form result = success\ntext_length > 0", "—", "排除空白提交", "FORM_03", "A：平均 <20 字，無負擔\nB：平均 >50 字且 P50 >50，提供範本；P75 <50 為少數極端值"),
    ("4.0 醫師｜接收轉診：轉診曝光與介入", "① 轉診曝光率（整體）", "主指標／轉診", "至少被曝光 1 次的轉診數 ÷ 期間內產生的轉診數",
     "item_impression item_type = referral\n只計受轉診醫師", "referral_created", "跨入口只算 1 次", "分子：EXPOSE_02、04\n分母：SERVER_03", "A：=100%，維持\nB：<100%，看醫師活躍度；每週 <1 次考慮簡訊、Email"),
    ("4.0 醫師｜接收轉診：轉診曝光與介入", "② 轉診提醒通知曝光率", "主指標／轉診", "在通知被曝光的轉診數 ÷ 期間內產生的轉診數",
     "item_impression list_name = notification_referral", "referral_created", "同入口只算 1 次", "分子：EXPOSE_02\n分母：SERVER_03", "A：>50%，維持\nB：<50%，看整體曝光"),
    ("4.0 醫師｜接收轉診：轉診曝光與介入", "③ 待醫師處理列表曝光率", "主指標／轉診", "在待醫師處理列表被曝光的轉診數 ÷ 期間內產生的轉診數",
     "item_impression list_name = doctor_pending", "referral_created", "同入口只算 1 次", "分子：EXPOSE_04\n分母：SERVER_03", "A：>20%，維持\nB：<20%，了解是否不知道列表"),
    ("4.0 醫師｜接收轉診：轉診曝光與介入", "④ 轉診介入率", "主指標／轉診", "有從轉診提醒或待醫師處理列表進入詳情的轉診數 ÷ 期間內產生的轉診數；另計曝光後介入率",
     "view_page patient_detail\nentry_source ∈ notification_referral, doctor_pending_list", "referral_created", "同一轉診只算 1 次", "分子：ENTER_03\n分母：SERVER_03", "同 1.2 ①"),
    ("5.0 醫師｜評估病情：主要查閱哪些資訊", "① 生理體徵待處理異常資訊查看率", "主指標／訪問", "有查看待處理異常生理體徵 ≥3 秒的詳情訪問數 ÷ 醫師進入、且個案有待處理轉診的詳情訪問數",
     "leave_tab tab_group = vital_sign\nis_pending_abnormal = true\ndwell_seconds ≥ 3", "view_page patient_detail\nhas_pending_referral = true\nprovider_type = doctor", "以 detail_visit_id 去重。" + TBC + "醫師端的「待處理異常」是指有待處理轉診，還是有未消除的警報？", "分子：DETAIL_01\n分母：ENTER_03", "A：<50%，考慮在醫師建議彈窗顯示異常數據\nB：>50%，維持"),
    ("5.0 醫師｜評估病情：主要查閱哪些資訊", "② 歷史處理紀錄查看率", "主指標／訪問", "有查看處理紀錄詳情 ≥5 秒的詳情訪問數 ÷ 醫師進入、且個案有處理紀錄的詳情訪問數；另看查看是在寫建議之前或之後",
     "close_popup popup_name = care_record_detail\ndwell_seconds ≥ 5", "view_page patient_detail\ntabs_with_data 含 care_records", "以 detail_visit_id 去重", "分子：DOC_01、02\n分母：ENTER_03", "A：<30%，維持\nB：>30%，在醫師建議彈窗提供近期紀錄摘要"),
    ("5.0 醫師｜評估病情：主要查閱哪些資訊", "③ 待辦資訊再次查看率（醫師）", "主指標／訪問", "同 2.0 ②，只計醫師", "同 2.0 ②", "同 2.0 ②", "同 2.0 ②", "DETAIL_02", "同 2.0 ②"),
    ("5.0 醫師｜評估病情：主要查閱哪些資訊", "④ 心電區塊有效曝光率、心電紀錄篩選使用率（醫師）", "—", "同 2.1 ③④，只計醫師", "", "", "", "TOOL_03、04、DETAIL_01", "同 2.1 ③④"),
    ("6.0 醫師｜完成轉診處置", "① 轉診處理閉環完成率", "主指標／轉診", "觀察窗內處理完成的轉診數 ÷ 已滿觀察窗的轉診數",
     "referral_resolved", "referral_created", "以 referral_id 去重", "分子：SERVER_04\n分母：SERVER_03", "A：=100%，看時長\nB：<100%，依序看曝光 → 介入 → 發起 → 提交"),
    ("6.0 醫師｜完成轉診處置", "② 轉診處理閉環時長", "主指標／分鐘", "referral_resolved 時間 − referral_created 時間；另拆轉診介入時長、排查時長、醫師建議填寫時長（算法同 3.1 ②③④）",
     "referral_resolved.resolved_at", "referral_created.created_at", "以 referral_id 為單位（報告觸發時機誤寫為「撰寫照護記錄」，已更正）", "SERVER_03、04、ENTER_03、FORM_01、03", "A：<24 小時，符合預期\nB：>48 小時，拆開各段"),
    ("6.0 醫師｜完成轉診處置", "③ 醫師建議填寫發起率、提交率，以及首次直接提交率、中途關閉率、復開率、空提交率、字數分布", "—", "算法同 3.0 ②④、3.2 ①～⑥；form_type = doctor_advice，以 referral_id 串接", "", "", "報告醫師建議的空提交率分母誤寫為「照護記錄」，已更正", "FORM_01、02、03", "同 3.0、3.2"),
]

# =====================================================================
# Sheet 1：填寫說明（沿用範本）
# =====================================================================
ws = wb.create_sheet("填寫說明")
header(ws, ["欄位", "怎麼填", "範例"])
guide = [
    ("報告章節", "對應報告的章節編號與標題；全域屬性統一放在「0.0 全域屬性」", "1.2 護理師｜發現異常：警報是否引導進入詳情"),
    ("編號", "章節前綴_流水號，依事件編，同一事件多個屬性共用一個編號；前綴見下方對照表。跨章節共用的事件放在第一個用到的章節，並在備注寫明", "ENTER_03"),
    ("頁面/區塊", "頁面名稱/區塊名稱，讓設計和工程對得上畫面", "個案詳情／頁籤"),
    ("事件名稱（Event Name）", "優先沿用通用動詞：view_page、view_popup、close_popup、click_button；只有通用動詞表達不了的才新增專屬事件（item_impression、leave_tab、submit_form…）", "click_button、submit_form"),
    ("觸發時機/事件定義（Trigger）", "寫「用戶做了什麼 / 畫面到什麼狀態」的當下，要具體到工程能判斷時機；結果類事件寫明「API 回傳後」", "點擊「完成處理」、API 回傳結果時"),
    ("目標/數據分析意義", "寫這個事件要回答什麼問題、為什麼要埋（指標對應寫在下一欄）", "計算表單提交成功數"),
    ("對應報告指標", "寫這個事件是報告哪個指標的分子或分母；不直接算指標的寫「輔助」。完整公式見「指標對照」分頁", "④ 分子（警報）"),
    ("屬性參數（Property）", "snake_case 英文 key；同一概念全文件用同一個 key", "form_type"),
    ("屬性定義（Property Definition）", "用一句話說明這個屬性代表什麼（不要填成值）", "處置表單類型"),
    ("資料型別（Data Type）", "只用下拉選單的 String / Integer / Boolean；時間用 String 填 ISO 8601（含 +08:00），多個值用逗號分隔的 String", "String"),
    ("範例值（Sample Values）", "列出所有可能值（列舉型）或格式範例；數字不要加千分位", "care_record, referral, doctor_advice"),
    ("優先級", "直接支撐報告指標＝高；輔助診斷＝中；觀察用＝低", "高"),
    ("埋點狀態", "規劃中 → 開發中 → 已開發 → 已驗收；第二階段或決定不做的項目填「暫不開發」", "規劃中"),
    ("備注", "去重規則、空值處理、與工程待確認事項；待確認事項以「【待確認】」開頭並標黃", "提交成功後自動關閉不送"),
]
for g in guide:
    ws.append(g)
    style_row(ws, ws.max_row, 3)
ws.append([])
ws.append(["報告章節", "編號前綴", "說明"])
for c in range(1, 4):
    ws.cell(ws.max_row, c).fill, ws.cell(ws.max_row, c).font = SEC_FILL, Font(bold=True)
for ch in CHAPTERS:
    ws.append(ch)
    style_row(ws, ws.max_row, 3)
ws.append([])
ws.append(["指標類型與單位", "說明", ""])
for c in range(1, 4):
    ws.cell(ws.max_row, c).fill, ws.cell(ws.max_row, c).font = SEC_FILL, Font(bold=True)
for k, v in [
    ("主指標", "直接用來判斷有沒有問題，情境的門檻設在它上面"),
    ("輔助判讀", "不單獨判讀，主指標異常時用來找原因"),
    ("人", "以 user_id 去重；不同天的人數不能直接相加；只計 user_role = provider"),
    ("警報", "以 alert_event_id 為單位：同一個案未處理期間的多筆警報合併為一個"),
    ("轉診", "以 referral_id 為單位"),
    ("訪問", "以 detail_visit_id 為單位，每次進入個案詳情算一次"),
    ("開啟", "以 notify_session_id／form_open_id 為單位，每打開一次彈窗算一次"),
    ("曝光", "項目露出 ≥50% 進入可視範圍即算；載入、捲動、翻頁都計；同一次開啟或瀏覽中，同一項目只算一次"),
    ("時長", "以伺服器時間計算；看中位數、P75、P90，平均數只當參考"),
    ("醫療個資", "不送任何填寫內容、姓名、證號；只送 ID、列舉值、字數、是否空白"),
]:
    ws.append([k, v, ""])
    style_row(ws, ws.max_row, 3)
ws.append([])
ws.append(["版本", "v0.2｜2026-11-04｜改用 CoDoctor DRD 範本格式；新增用戶屬性（Person Properties）分頁；角色改為 user_role（super_admin / sub_org_admin / provider）＋ provider_type", ""])
style_row(ws, ws.max_row, 3)
widths(ws, [34, 100, 46])
ws.freeze_panes = "A2"

# =====================================================================
# Sheet 2：指標對照
# =====================================================================
ws = wb.create_sheet("指標對照")
header(ws, ["報告章節", "指標", "類型／單位", "計算方式", "分子：事件與條件", "分母：事件與條件", "去重／計算規則", "對應事件編號", "對應情境（報告假設）"])
for m in M:
    ws.append(list(m))
    style_row(ws, ws.max_row, 9)
widths(ws, [28, 30, 13, 42, 38, 34, 38, 22, 44])
ws.freeze_panes = "C2"
ws.auto_filter.ref = f"A1:I{ws.max_row}"

# =====================================================================
# Sheet 3：DRD（一列一屬性，事件層欄位合併）
# =====================================================================
ws = wb.create_sheet("DRD")
H = ["報告章節", "編號", "頁面/區塊", "事件名稱（Event Name）", "觸發時機/事件定義（Trigger）", "目標/數據分析意義", "對應報告指標",
     "屬性參數（Property）", "屬性定義（Property Definition）", "資料型別（Data Type）", "範例值（Sample Values）", "優先級", "埋點狀態", "備注"]
header(ws, H)
for ch, eid, page, name, trig, goal, metric, props, note in E:
    start = ws.max_row + 1
    for j, p in enumerate(props):
        if isinstance(p, str):
            key, sample_o, def_o = p, None, None
        else:
            key, sample_o, def_o = (list(p) + [None, None])[:3]
        d, t, s, pri = P[key]
        row = [ch, eid, page, name, trig, goal, metric] if j == 0 else [None] * 7
        row += [key, def_o or d, t, sample_o if sample_o is not None else s, pri, "規劃中", note if j == 0 else None]
        ws.append(row)
        style_row(ws, ws.max_row, len(H))
    end = ws.max_row
    if end > start:
        for col in list(range(1, 8)) + [14]:
            ws.merge_cells(start_row=start, start_column=col, end_row=end, end_column=col)
    if TBC in (note or ""):
        ws.cell(start, 14).fill = TBC_FILL
widths(ws, [24, 11, 22, 16, 32, 30, 24, 22, 40, 11, 34, 7, 9, 56])
ws.freeze_panes = "C2"
dv_type = DataValidation(type="list", formula1='"String,Integer,Boolean"', allow_blank=True)
dv_pri = DataValidation(type="list", formula1='"高,中,低"', allow_blank=True)
dv_st = DataValidation(type="list", formula1='"規劃中,開發中,已開發,已驗收,暫不開發"', allow_blank=True)
for dv, col in ((dv_type, "J"), (dv_pri, "L"), (dv_st, "M")):
    ws.add_data_validation(dv)
    dv.add(f"{col}2:{col}{ws.max_row}")

# =====================================================================
# Sheet 4：用戶屬性（Person Properties）— 依使用者提供的範本欄位
# =====================================================================
ws = wb.create_sheet("用戶屬性（Person Properties）")
HP = ["屬性分類", "屬性名稱 (Key)", "範例值 (Sample Values)", "資料型別（Data Type）", "描述", "觸發時機", "重置時機", "數據分析意義", "優先級", "埋點狀態"]
header(ws, HP)
PP = [
    ("使用者身分", "user_id", "u_12345abc", "String", "系統發給每個帳號的唯一識別碼", "登入成功時設定", "登出時清空", "串接同一位使用者的所有行為，「按人」計算的指標以此去重", "高", "規劃中"),
    ("使用者身分", "user_role", "super_admin / sub_org_admin / provider", "String", "帳號的權限角色", "登入成功、取得帳號權限時設定；權限變更時更新", "登出時清空", "分析時排除管理者帳號，只計醫護人員（provider）的行為", "高", "規劃中"),
    ("使用者身分", "provider_type", "nurse / case_manager / doctor", "String", "醫護人員的職類；user_role = provider 時才有值", "登入成功時依帳號資料設定", "登出時清空", "報告的指標分成護理師與醫師兩條線，需要用職類區分。" + TBC + "帳號資料中是否有這個欄位？", "高", "規劃中"),
    ("機構", "org_id", "org_001", "String", "使用者當下所選機構的識別碼", "登入後取得機構時設定；多機構帳號切換機構時更新", "登出時清空", "依機構與場域（日照、居家、HaH、遠距中心）拆分指標；場域由後台機構主檔對應", "高", "規劃中"),
    ("機構", "is_multi_org_user", "true, false", "Boolean", "帳號是否關聯一個以上的機構", "登入後依後台機構清單判定", "關聯機構數變為 1 時改為 false", "必要時區分單機構與多機構帳號的使用差異", "低", "規劃中"),
    ("裝置", "platform_version", "7.0.3", "String", "平台前端版本號", "每次載入平台時更新", "不重置", "判斷數據變化是否與改版有關", "高", "規劃中"),
    ("裝置", "browser", "chrome_130", "String", "瀏覽器名稱與主版本", "每次載入平台時更新", "不重置", "排查特定瀏覽器的相容性問題", "低", "規劃中"),
]
for r in PP:
    ws.append(list(r))
    style_row(ws, ws.max_row, len(HP))
ws.append([])
ws.append(["說明：範本原檔中文字因編碼損毀無法讀取，描述等欄位依可讀的 key 與範例值重寫；is_multi_org_user 的資料型別原為 String，依值域改為 Boolean。流程識別碼（detail_visit_id、form_open_id 等）只在單次流程中有用，不是「這個人」的長期資料，所以放在 DRD 各事件裡，不列為用戶屬性。"])
ws.cell(ws.max_row, 1).alignment = WRAP
ws.merge_cells(start_row=ws.max_row, start_column=1, end_row=ws.max_row, end_column=len(HP))
ws.row_dimensions[ws.max_row].height = 48
widths(ws, [12, 20, 36, 14, 34, 36, 22, 44, 7, 9])
ws.freeze_panes = "C2"

# =====================================================================
# Sheet 5：待確認問題
# =====================================================================
ws = wb.create_sheet("待確認問題")
header(ws, ["#", "問題", "影響範圍", "目前預設", "需誰確認", "狀態", "回覆"])
QS = [
    ("Q1", "「警報事件 id」與報告中的「任務 id」是否同一個？同一個案未處理期間的多筆警報，是否合併為一個警報事件？", "所有護理師指標的計算單位", "合併為一個警報事件；task_id 先保留為屬性", "產品／後端"),
    ("Q2", "provider 之下有沒有職類欄位（護理師／個管師／醫師）？", "全部指標的角色拆分", "新增 provider_type", "產品／後端"),
    ("Q3", "閉環完成率的觀察窗多長？", "3.0 ①、6.0 ①", "7 天", "產品"),
    ("Q4", "轉診醫師提交後，警報是否立即消除？", "3.0 ①", "是，resolve_type = referral", "產品"),
    ("Q5", "曝光是否要加停留門檻？", "1.0、4.0", "露出 ≥50% 即算，不加停留門檻", "研究"),
    ("Q6", "心電區塊要用可視範圍還是滑鼠停留來量？", "2.1 ③", "可視範圍", "研究／前端"),
    ("Q7", "醫師端的「待處理異常」是指有待處理轉診，還是有未消除的警報？", "5.0 ①", "有待處理轉診", "產品"),
    ("Q8", "表單「第幾次打開」能否由後端記錄？", "3.2 ①③④", "後端記錄；做不到時由分析端計算", "工程"),
    ("Q9", "頁籤、列表、頁面代碼、心電區塊、心電篩選值的完整清單", "DETAIL_01、TOOL_03、TOOL_04、EXPOSE_03", "請提供最新設計稿或規格", "設計／前端"),
    ("Q10", "「自訂計劃未測量列表」是否納入警報曝光？", "1.0 ③", "不納入，只記錄 NOTIFY_02 的點擊", "研究"),
    ("Q11", "一個警報事件同時含高、低風險時，alert_level 取最高等級？", "1.0 ③、3.2 ⑤", "取最高", "產品"),
]
for q in QS:
    ws.append(list(q) + ["待回覆", ""])
    style_row(ws, ws.max_row, 7)
widths(ws, [6, 60, 28, 40, 14, 10, 40])
ws.freeze_panes = "A2"

wb.save(OUT)
print("saved", OUT)
