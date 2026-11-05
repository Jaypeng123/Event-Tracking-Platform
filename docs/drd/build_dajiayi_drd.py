# -*- coding: utf-8 -*-
"""產生「大家醫平台 埋點 DRD」Excel（沿用 CoDoctor DRD 範本格式）。
修改內容後重新執行：python3 docs/drd/build_dajiayi_drd.py"""
import os
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils import get_column_letter

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "大家醫平台_埋點DRD_v0.3.xlsx")
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
    "user_role": ("帳號角色；分析時排除機構管理員與管理員", "String", "org_admin（機構管理員）, admin（管理員）, doctor（醫師）, frontline_doctor（一線醫師）, frontline_staff（一線人員）", "高"),
    "org_id": ("使用者當下所選機構的識別碼", "String", "org_001", "高"),
    "page_name": ("頁面名稱", "String", "patient_detail", "高"),
    "session_id": ("本次上線的識別碼；登入或閒置 30 分鐘後回到平台時產生", "String", "ss_9k3m2p", "高"),
    "session_start_type": ("上線開始的方式", "String", "login, resume, new_tab", "中"),
    "result_type": ("照護記錄的處理結果類型", "String", "false_alarm, handled, null", "中"),
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
    "notify_session_id": ("本次小鈴鐺通知開啟的識別碼；每次打開時產生，關閉時結束", "String", "ns_4k2p9a", "高"),
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
    "is_referral_item": ("該生理體徵是否為個案目前待處理轉診的異常項目；沒有待處理轉診或非生理體徵頁籤為 null", "Boolean", "true, false, null", "高"),
    "has_multi_source": ("該生理體徵在目前時間範圍內是否同時有 Home 與 Pro 的資料；非檢測儀頁籤為 null", "Boolean", "true, false, null", "高"),
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
    "form_type": ("處置表單類型；轉診醫師表單已優化，不埋點", "String", "care_record, doctor_advice", "高"),
    "form_open_id": ("本次表單開啟的識別碼；每次打開時產生，用來配對關閉與提交", "String", "fo_2b9x7q", "高"),
    "form_open_seq": ("同一警報事件（或轉診）中，第幾次打開同一種表單；1 = 首次，≥2 = 復開", "Integer", NUM + "1", "高"),
    "close_method": ("關閉方式；leave_page 代表沒有關閉彈窗就直接離開頁面、切換個案或重新整理", "String", "cancel, close_icon, mask, leave_page", "高"),
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
     ["user_id", "user_role", "org_id", "session_id", "page_name", "platform_version", "browser", "viewport_height"],
     "分析時排除 org_admin、admin；警報相關指標（護理師端）計 frontline_staff、frontline_doctor，轉診相關指標（醫師端）計 doctor。" + TBC + "一線醫師（frontline_doctor）是否也處理警報、應歸在護理師端指標？"
     "多機構帳號的 org_id 以當下所選機構為準；場域類型（日照、居家、HaH、遠距中心）由後台機構主檔依 org_id 對應，不另外埋點。\n"
     "事件時間一律以收集端收到的伺服器時間計算時長；時區 +08:00"),

    ("0.0 全域屬性", "GLOBAL_02", "平台全域", "session_start",
     "登入成功、閒置超過 30 分鐘後回到平台、或開新分頁進入平台時（產生新的 session_id）",
     "判斷警報、轉診產生後護理師或醫師是否已上線（看到）或完整上線過（處理），並計算上線次數與上線後的回應時長；取代固定的 24 小時、7 天門檻",
     "1.0 前提、④⑤\n1.2 ②\n3.0 前提\n3.1 ①②\n4.0 前提、⑤⑥\n6.0 ①②",
     ["session_id", "session_start_type", "page_name"],
     "上線結束不另外埋點：最後一筆事件後閒置 30 分鐘即視為結束，由分析端判定。" + TBC + "閒置 30 分鐘的定義是否符合護理師的使用習慣（例如整天開著平台的遠距中心）"),
    ("0.1 後端事件（警報與轉診紀錄）", "SERVER_01", "後端／警報", "alert_created", "規則引擎判定異常、正式產生警報事件時（伺服器時間）",
     "所有警報相關指標的分母與起點", "1.0 ①②③ 分母（警報）\n1.2 ① 分母（警報）\n3.0 ① 分母（警報）\n3.1 ①② 起點",
     ["alert_event_id", "task_id", "patient_id", "org_id", "alert_level", "alert_items", "device_source", "created_at"],
     "可以用後端資料表每日匯出代替事件。同一個案已有未處理的警報事件時，新的警報項目併入原事件，不另外產生。\n" + TBC + "「警報事件 id」與報告提到的「任務 id」是否同一個？若不同，兩者是 1 對 1 還是 1 對多？\n" + TBC + "一個警報事件同時含高、低風險項目時，alert_level 是否取最高等級？"),
    ("0.1 後端事件（警報與轉診紀錄）", "SERVER_02", "後端／警報", "alert_resolved", "照護記錄或轉診醫師提交成功、警報被消除時",
     "判斷警報是否完成處理與完成時間", "3.0 ① 分子（警報）\n3.0 ② 分母排除條件（以轉診處理）\n3.1 ① 終點",
     ["alert_event_id", "patient_id", "resolve_type", "resolved_by_user_id", "resolved_at"],
     TBC + "轉診醫師提交後，警報是否立即消除？報告把轉診也算進護理師的處理閉環"),
    ("0.1 後端事件（警報與轉診紀錄）", "SERVER_03", "後端／轉診", "referral_created", "護理師轉診醫師提交成功、後端產生轉診紀錄時",
     "醫師端所有指標的分母與起點", "4.0 ①②③④ 分母（轉診）\n6.0 ① 分母、② 起點",
     ["referral_id", "alert_event_id", "patient_id", "referrer_user_id", "doctor_user_id", "created_at"],
     TBC + "一筆轉診可以同時轉給多位醫師嗎？"),
    ("0.1 後端事件（警報與轉診紀錄）", "SERVER_04", "後端／轉診", "referral_resolved", "醫師建議提交成功、轉診被標記為已處理時",
     "判斷轉診是否完成處理與完成時間", "6.0 ① 分子（轉診）\n6.0 ② 終點",
     ["referral_id", "resolved_by_user_id", "resolved_at"], ""),

    ("1.0 護理師｜發現異常：警報是否被看到", "EXPOSE_01", "小鈴鐺通知", "view_popup",
     "點擊小鈴鐺、小鈴鐺通知顯示完成時；在彈窗內切換「異常提醒／轉診提醒」分頁時也送一筆",
     "作為一次通知查看的起點；計算 1.1 的分母", "1.1 ①② 分母（開啟）",
     [("popup_name", "notification_center"), "notify_session_id", "notify_tab", "unread_count"],
     "跨章節共用：醫師的轉診提醒也用本事件（notify_tab = referral）。每次打開產生新的 notify_session_id，切換分頁沿用。" + TBC + "彈窗打開時預設停在哪一個分頁？"),
    ("1.0 護理師｜發現異常：警報是否被看到", "EXPOSE_02", "小鈴鐺通知／通知卡片", "item_impression",
     "通知卡片露出 ≥50% 進入可視範圍時；打開彈窗時首屏可見的卡片立即送出，之後捲入的卡片再送",
     "計算警報（與轉診）在通知中被看到的比例", "1.0 ①② 分子（警報）\n4.0 ①② 分子（轉診）",
     [("list_name", "notification_alert, notification_referral"), "notify_session_id", "item_type", "item_id", "patient_id",
      ("alert_level", "high_risk, low_risk, abnormal_report, null", "警報等級；item_type = referral 時為 null"), "source_filter", "position"],
     "一則卡片送一筆；同一個 notify_session_id 內同一個 item_id 只送一次（往回捲不重送）。\n" + TBC + "通知卡片是一筆警報紀錄還是一個個案？若是一筆警報紀錄，item_id 仍須帶它所屬的 alert_event_id，否則無法對到分母。\n" + "報告要的「曝光個案數」由分析端計數，不另外帶。\n" + TBC + "曝光是否要加停留門檻（例如 ≥500ms）？"),
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

    ("1.1 護理師｜發現異常：通知內的其他操作", "NOTIFY_01", "小鈴鐺通知／來源篩選", "click_button",
     "點擊來源篩選（全部／CoDoctor 檢測儀／CoDoctor Watch）、通知列表更新後", "判斷警報來源是否影響查看順序", "① 分子（開啟）",
     [("button_name", "alert_source_filter"), "notify_session_id", "from_source", "to_source"],
     "點擊目前已選的來源時不送。分析時以 notify_session_id 去重，避免一次開啟切換多次讓比率超過 100%"),
    ("1.1 護理師｜發現異常：通知內的其他操作", "NOTIFY_02", "小鈴鐺通知／前往列表", "click_button",
     "點擊「前往高風險列表／異常上報列表／自訂計劃未測量列表／低風險列表」的當下", "判斷通知中的快捷入口是否有引流效果；以及是否點到空列表", "② 分子（開啟）",
     [("button_name", "goto_list"), "notify_session_id", "target_list", "target_list_count"],
     "target_list_count 對應報告「點擊時該列表人數」；= 0 時代表點到空列表"),

    ("1.2 護理師｜發現異常：警報是否引導進入詳情", "ENTER_01", "小鈴鐺通知／通知卡片", "click_button",
     "點擊通知卡片的當下", "記錄從通知點進詳情的位置與項目；判斷是否先處理高風險", "① 輔助（警報）\n② 分子（上線）\n1.1 ③④\n4.0 ④ 輔助（轉診）",
     [("button_name", "notification_card"), "notify_session_id", "item_type", "item_id", "patient_id", "task_id", ("alert_level", "high_risk, low_risk, abnormal_report, null", "點擊的警報等級；item_type = referral 時為 null"), "position"],
     "介入率以 ENTER_03 計算；本事件用來看點擊位置，以及點擊後有沒有成功進入詳情"),
    ("1.2 護理師｜發現異常：警報是否引導進入詳情", "ENTER_02", "待處理列表／列表項目", "click_button",
     "點擊列表列或「查看」按鈕的當下", "記錄從列表點進詳情的位置與項目；判斷是否先處理高風險", "① 輔助（警報）\n② 分子（上線）\n4.0 ④ 輔助（轉診）",
     [("button_name", "list_row, view_detail"), "list_view_id", "list_type", "item_type", "item_id", "patient_id", "task_id", ("alert_level", "high_risk, low_risk, abnormal_report, null", "點擊的警報等級；item_type = referral 時為 null"), "position", "page_index"], ""),
    ("1.2 護理師｜發現異常：警報是否引導進入詳情", "ENTER_03", "個案詳情", "view_page",
     "個案詳情資料載入完成時", "計算進入詳情的警報（與轉診）數；作為 2.x 的分母、3.1 的介入時間點", 
     "① 分子（警報）\n2.0 ①② 分母\n2.1 ①② 分母\n3.0 ② 分母（警報）\n3.1 ②③ 時間點\n4.0 ④ 分子（轉診）\n5.0 ①② 分母\n6.0 ① 分母",
     [("page_name", "patient_detail"), "detail_visit_id", "patient_id",
      ("entry_source", "notification_alert, notification_referral, alert_list, doctor_pending_list, patient_list, reload, other", "進入個案詳情的來源（報告的「進入前頁面」）"),
      ("alert_event_id", "null, ae_5521", "個案當下未處理的警報事件；沒有時為 null"), ("referral_id", "null, rf_301", "個案當下未處理的轉診；沒有時為 null"), "task_id",
      "has_pending_alert", "pending_alert_items", "has_pending_referral", "tabs_with_data", "has_todo", "default_tab"],
     "跨章節共用事件，於此統一定義。每次進入產生新的 detail_visit_id。alert_event_id、referral_id 不論從哪個入口進來都要帶，否則從個案列表進入後的處理會漏算。\n"
     "tabs_with_data、has_todo 用來限定 2.0 的分母（只算該頁籤有資料、有待辦的訪問）。\n" + TBC + "所有可以進入個案詳情的入口清單"),

    ("2.0 護理師｜排查異常：主要查看哪些健康資訊", "DETAIL_01", "個案詳情／頁籤", "leave_tab",
     "切換到其他頁籤、離開詳情頁，或瀏覽器分頁被隱藏時，送出本次在該頁籤的停留秒數",
     "計算各頁籤的有效查看（停留 ≥5 秒且有資料）；醫師端判斷是否查看待處理異常的生理體徵", "① 分子（訪問）\n2.1 ①③④ 分母條件\n3.1 ③ 排除條件\n5.0 ①② 分子（訪問）",
     ["detail_visit_id", "patient_id", "tab_group", "tab_name", "metric", "has_data", "is_pending_abnormal", "is_referral_item", "has_multi_source", "dwell_seconds", "leave_reason"],
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
     "點擊「撰寫照護記錄」「醫師建議」後，彈窗顯示完成時", "計算處置發起數；作為提交率、首次直接提交率、時長的起點",
     "② 分子（警報）\n③ 分母（警報）\n3.1 ③④ 時間點\n3.2 ①②③④ 分母\n6.0 ③ 同上",
     [("popup_name", "handle_form"), "form_type", "form_open_id", "form_open_seq", "detail_visit_id", "patient_id",
      ("alert_event_id", "null, ae_5521", "本次處理的警報事件"), ("referral_id", "null, rf_301", "本次處理的轉診；醫師建議時必帶"), "task_id"],
     "跨章節共用：3.2 與 6.0 都用本事件。每次打開產生新的 form_open_id。轉診醫師表單的設計已優化，本次不埋點（不送 form_type = referral）。\n" +
     TBC + "form_open_seq 需要跨頁面、跨重新整理累計，前端不容易算準：建議由後端記錄開啟次數；做不到時前端送 null，由分析端依時間順序計算"),
    ("3.0 護理師｜完成處置：是否都有被處理", "FORM_02", "表單彈窗", "close_popup",
     "點擊「取消」、右上角關閉、點擊遮罩關閉時；或彈窗開著時直接離開頁面、切換個案、重新整理（close_method = leave_page）", "計算表單打開後沒有提交的結果與之後是否復開", "3.2 ②③ 分子（開啟）",
     [("popup_name", "handle_form"), "form_type", "form_open_id", "form_open_seq", "close_method", "has_input", "dwell_seconds"],
     "提交成功後自動關閉的情況不送。leave_page 在瀏覽器關閉前送出（visibilitychange / pagehide），可能有少量遺失"),
    ("3.0 護理師｜完成處置：是否都有被處理", "FORM_03", "表單彈窗／完成處理", "submit_form",
     "點擊「完成處理」、API 回傳結果時（成功、失敗都送）", "計算表單提交成功數、空提交與填寫字數",
     "③ 分子（警報）\n3.1 ④ 終點\n3.2 ①②④⑤⑥ 分子\n6.0 ③ 同上",
     ["form_type", "form_open_id", "form_open_seq", "total_open_count", "result", "error_code", "is_empty", "text_length",
      ("alert_level", "high_risk, low_risk, abnormal_report, null", "提交時的警報等級"), ("alert_items", "blood_pressure,ecg, null", "提交時的警報項目，多個以逗號分隔"), "result_type", "dwell_seconds"],
     "前端欄位檢核沒通過、沒有呼叫 API 時不送。" + TBC + "result_type：照護記錄是否有欄位能區分誤報／真異常？沒有的話送 null，3.2 ⑦ 暫不開發。\n不送任何填寫內容，只送字數與是否空白（醫療個資）。\n處理閉環以 SERVER_02、SERVER_04 為準，本事件用來看表單層的行為"),

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
OPP = "只計護理師上線時已存在的警報：警報產生後，該機構有護理師或個管師上線（或產生當下已在線上）"
OPPH = "只計經過護理師完整上線的警報：警報產生後，至少有一次護理師從上線到下線（閒置 30 分鐘視為下線）"
OPPR = "只計醫師上線時已存在的轉診：轉診產生後，受轉診醫師有上線（或產生當下已在線上）"
NEW = "（新增）"


def P3(lo, mid, hi):
    return "低（≤30%）：" + lo + "\n中（31%–60%）：" + mid + "\n高（≥61%）：" + hi


def T3(unit, a, b, lo, mid, hi):
    return f"短（≤{a}{unit}）：" + lo + f"\n中（>{a}～{b}{unit}）：" + mid + f"\n長（>{b}{unit}）：" + hi


def P2(lo, hi):
    return "低（≤50%）：" + lo + "\n高（≥51%）：" + hi


def W3(lo, mid, hi):
    return "少（≤20 字）：" + lo + "\n中（21～50 字）：" + mid + "\n多（>50 字）：" + hi


def N3(lo, mid, hi):
    return "1 次（當次上線就完成）：" + lo + "\n2 次：" + mid + "\n3 次以上：" + hi


OPT = "（已優化，不埋點）"
M = [
    ("1.0 護理師｜發現異常：警報是否被看到", "（前提）護理師上線時已存在的警報", "前提",
     "警報產生後，該機構至少有一位護理師或個管師上線過（session_start 晚於警報產生，或產生當下已在線上）的警報",
     "—", "—", "沒有人上線期間產生、且尚未有人上線的警報不列入分母，另列「等待上線中的警報數」；不使用固定的 24 小時等時間門檻，避免把護理師還沒上線誤判成沒看到", "SERVER_01、GLOBAL_02", "—"),
    ("1.0 護理師｜發現異常：警報是否被看到", "① 警報曝光率（整體）", "主指標／警報",
     "護理師上線時已存在的警報中，在被處理前至少被護理師曝光 1 次的比例；另計：重複曝光率＝兩個入口都曝光過 ÷ 已曝光",
     "item_impression（EXPOSE_02、EXPOSE_04）\nitem_type = alert\nuser_role ∈ frontline_staff, frontline_doctor\n曝光時間早於 alert_resolved", "alert_created\n" + OPP,
     "跨入口重複曝光只算 1 次；沒有曝光卻已被處理的警報另外列出", "分子：EXPOSE_02、04\n分母：SERVER_01＋GLOBAL_02",
     P3("護理師上線了，大部分警報卻沒被看到 → 優先改善提醒機制（登入時主動提示待處理異常、加強通知提示），並確認是否警報量過多",
        "有相當比例沒被看到 → 拆開兩個入口，找出曝光不足的入口並優化引導",
        "多數警報有被看到 → 看重複曝光率，重複曝光也在高級距時考慮把入口單一化；未曝光的警報逐筆檢查原因")),
    ("1.0 護理師｜發現異常：警報是否被看到", "② 警報曝光率（小鈴鐺通知）", "主指標／警報", "護理師上線時已存在的警報中，在小鈴鐺通知被曝光的比例",
     "item_impression\nlist_name = notification_alert\nuser_role ∈ frontline_staff, frontline_doctor", "alert_created\n" + OPP, "同入口重複曝光只算 1 次", "分子：EXPOSE_02\n分母：SERVER_01＋GLOBAL_02",
     P3("小鈴鐺不是主要管道 → 看列表曝光率；列表也在低級距時，加強通知提示（例如登入時即時彈出）",
        "通知與列表並用 → 維持設計，持續觀察兩個入口的分工",
        "小鈴鐺是主要管道 → 維持通知設計，可評估列表入口是否需要精簡")),
    ("1.0 護理師｜發現異常：警報是否被看到", "③ 警報列表曝光率（高風險／異常上報／低風險）", "主指標／警報",
     "各列表：護理師上線時已存在、且屬於該等級的警報中，在該列表被曝光的比例\n合計：護理師上線時已存在的警報中，在任一列表被曝光的比例",
     "item_impression\nlist_name = high_risk / abnormal_report / low_risk", "alert_created\n" + OPP + "\n各列表：alert_level = 該等級",
     "合計用聯集（同一警報出現在多個列表只算 1 次）。" + TBC + "異常上報是否也會產生 alert_created？",
     "分子：EXPOSE_04\n分母：SERVER_01＋GLOBAL_02",
     P3("多數護理師不走列表 → 訪談是否不知道有列表，加強宣導與入口引導",
        "部分護理師會用列表 → 維持，比較各等級列表的差異",
        "護理師會主動、規律地從列表處理 → 維持；小鈴鐺通知可定位為輔助提醒")),
    ("1.0 護理師｜發現異常：警報是否被看到", "④ 上線後首次看到警報的時長" + NEW, "主指標／分鐘",
     "警報首次被曝光的時間 − 起算時間；起算時間＝警報產生後護理師第一次上線的時間（警報產生時已在線上，則從產生時間起算）；取中位數",
     "item_impression 第一筆（item_type = alert）", "session_start（警報產生後第一筆）或 alert_created",
     "只計算護理師在線上的時間，不把下班、沒上線的時間算進去；用來驗證「小鈴鐺通知能不能讓護理師一上線就注意到異常」", "EXPOSE_02、04、GLOBAL_02、SERVER_01",
     T3("分鐘", 5, 30, "護理師一上線很快就注意到異常 → 小鈴鐺通知設計有效，維持",
        "上線後過一段時間才看到 → 看這段時間護理師先做了什麼（其他頁面），評估登入時是否要主動提示待處理異常",
        "上線後很久才看到 → 小鈴鐺通知沒有發揮提醒作用，加強登入時的待處理提示或首頁異常區塊") + "\n" + TBC + "5／30 分鐘的級距是否符合各場域的工作節奏"),
    ("1.0 護理師｜發現異常：警報是否被看到", "⑤ 警報積壓率" + NEW, "主指標／上線",
     "每次上線開始時，未處理的警報中「上一次上線時就已存在」的比例；取所有上線的中位數",
     "上線開始時未處理、且在上一次上線開始前就已產生的警報數（後端狀態）", "上線開始時未處理的警報數（後端狀態）",
     "以機構為單位，依上線時間點回推後端警報狀態計算；用來驗證「目前的發現與處理流程，能不能在一次上線內消化新進警報」", "GLOBAL_02、SERVER_01、02",
     P3("多數警報在一次上線內就處理掉 → 流程消化得了，維持",
        "部分警報會跨次上線 → 看 3.0 ④ 卡關階段，找出拖延的環節",
        "警報持續積壓 → 檢查警報量是否超過人力，以及警報分級、排序是否讓護理師先處理重要的")),
    ("1.1 護理師｜發現異常：通知內的其他操作", "① 小鈴鐺通知來源篩選使用率", "主指標／開啟",
     "有切換來源的通知開啟次數 ÷ 小鈴鐺通知的開啟次數；另計：曾經使用過來源篩選的護理師 ÷ 有開啟小鈴鐺通知的護理師",
     "click_button button_name = alert_source_filter\n以 notify_session_id 去重", "view_popup popup_name = notification_center\nnotify_tab = abnormal_alert",
     "同一次開啟切換多次只算 1 次；依開啟當下的未讀數（unread_count）分組判讀", "分子：NOTIFY_01\n分母：EXPOSE_01",
     P3("多數時候不依設備篩選 → 再看「用過的護理師比例」與 ⑤ 對效率的影響；都偏低時，弱化或收合篩選",
        "部分情境需要篩選 → 保留，依未讀數分組找出需要篩選的情境",
        "護理師依設備決定處理順序 → 維持，並評估是否提供預設排序")),
    ("1.1 護理師｜發現異常：通知內的其他操作", "② 快捷入口點擊率", "主指標／開啟", "有點擊「前往列表」的通知開啟次數 ÷ 小鈴鐺通知的開啟次數；另計各列表的點擊分布、空列表點擊佔比",
     "click_button button_name = goto_list\n空列表：target_list_count = 0", "同 ① 分母", "同一次開啟只算 1 次；分布以點擊次數計；同樣依 unread_count 分組", "分子：NOTIFY_02\n分母：EXPOSE_01",
     P3("在通知中主要是看警報 → 弱化快捷入口，擴大警報顯示空間",
        "部分護理師會依等級分流 → 保留，依各列表點擊分布調整按鈕順序",
        "護理師依等級分流處理 → 保留並依分布調整；空列表點擊佔比也在中級距以上時，區分有／無警報的按鈕狀態")),
    ("1.1 護理師｜發現異常：通知內的其他操作", "③ 小鈴鐺通知無效開啟率" + NEW, "主指標／開啟",
     "有未讀警報時打開小鈴鐺通知，卻沒有點任何警報、沒有前往列表就關閉的開啟次數 ÷ 有未讀警報時的開啟次數",
     "同一 notify_session_id 內沒有 NOTIFY_02、ENTER_01", "view_popup popup_name = notification_center\nnotify_tab = abnormal_alert\nunread_count > 0",
     "原本的 ①② 只看功能有沒有被用，無法回答「是否影響查看效率」；本指標直接看打開小鈴鐺通知後有沒有產生下一步行動", "EXPOSE_01、NOTIFY_02、ENTER_01",
     P3("小鈴鐺通知能引導下一步行動 → 維持",
        "有相當比例打開後沒有行動 → 訪談原因（只是確認數量？資訊不足以判斷？），並看 ④ 停留時間",
        "小鈴鐺通知內容不足以引導行動 → 檢視小鈴鐺通知的排序、資訊量與點擊引導")),
    ("1.1 護理師｜發現異常：通知內的其他操作", "④ 打開小鈴鐺通知到點進第一個警報的時間" + NEW, "輔助判讀／秒",
     "第一次點擊小鈴鐺通知卡片的時間 − 打開小鈴鐺通知的時間；取中位數",
     "同一 notify_session_id 第一筆 ENTER_01", "EXPOSE_01（同一 notify_session_id）",
     "依是否有切換來源、未讀數分組比較，判斷篩選或資訊量是否拖慢查看", "EXPOSE_01、ENTER_01、NOTIFY_01",
     T3("秒", 10, 30, "很快就找到要處理的警報 → 維持",
        "需要一點時間找 → 比較有／沒有切換來源的時間，判斷篩選是否有幫助",
        "要花很久才決定點哪一則 → 檢視小鈴鐺通知排序與資訊呈現，讓最需要處理的警報在最上方") + "\n" + TBC + "10／30 秒的級距"),
    ("1.2 護理師｜發現異常：警報是否引導進入詳情", "① 警報介入率", "主指標／警報",
     "護理師上線時已存在的警報中，有護理師進入個案詳情的比例；依進入來源拆分；另計：曝光後介入率＝已曝光且已介入的警報 ÷ 已曝光的警報",
     "view_page page_name = patient_detail\nalert_event_id ∈ 分母\nuser_role ∈ frontline_staff, frontline_doctor", "alert_created\n" + OPP,
     "同一警報多次進入只算 1 次；任何入口都算，再依 entry_source 拆分", "分子：ENTER_03\n分母：SERVER_01＋GLOBAL_02",
     P3("多數警報沒人點進詳情 → 先看曝光率：曝光也低就先改善曝光；曝光高就訪談為什麼不點（不知道可以點，或想在外層直接處理）",
        "部分警報沒有介入 → 依入口拆分，找出介入偏低的入口優化點擊引導",
        "多數警報有介入 → 未介入的逐筆檢查，並看曝光後介入率是否也在高級距")),
    ("1.2 護理師｜發現異常：警報是否引導進入詳情", "② 高風險優先處理率" + NEW, "主指標／上線",
     "每次上線中第一個點進詳情的警報，屬於當下未處理警報中最高風險等級的比例",
     "上線後第一筆 ENTER_01／ENTER_02 的 alert_level ＝ 當下未處理警報的最高等級", "有點進任一警報的上線次數",
     "當下未處理警報的最高等級由後端警報狀態回推；用來驗證「分級、排序與入口設計，是否引導護理師先處理最重要的異常」", "ENTER_01、02、GLOBAL_02、SERVER_01",
     P3("護理師多半沒有先處理高風險 → 調整排序（高風險置頂）、強化高風險標示",
        "部分會先處理高風險 → 拆入口看是哪個入口沒有把高風險放在前面",
        "分級與排序有引導先處理高風險 → 維持")),
    ("2.0 護理師｜排查異常：主要查看哪些健康資訊", "① 單一頁籤有效查看率", "主指標／訪問", "有效查看該頁籤的詳情訪問數 ÷ 護理師進入、個案有待處理異常、且該頁籤有資料的詳情訪問數",
     "leave_tab\ntab_name = health_plan / care_records / patient_reports\ndwell_seconds ≥ 5 且 has_data = true", "view_page patient_detail\nhas_pending_alert = true\ntabs_with_data 含該頁籤\nuser_role ∈ frontline_staff, frontline_doctor",
     "以 detail_visit_id 去重；排除該頁籤剛好是預設頁籤的訪問", "分子：DETAIL_01\n分母：ENTER_03",
     P3("排查時很少用 → 訪談原因，評估是否整合到其他頁籤或收合",
        "使用頻率符合現有層級 → 維持設計",
        "排查時經常需要 → 提高該資訊的層級，減少查找步驟")),
    ("2.0 護理師｜排查異常：主要查看哪些健康資訊", "② 待辦資訊再次查看率", "主指標／訪問", "有手動再次開啟待辦的詳情訪問數 ÷ 有自動跳出待辦的詳情訪問數",
     "view_popup popup_name = todo_popup\nopen_type = manual", "view_popup popup_name = todo_popup\nopen_type = auto", "以 detail_visit_id 去重；依 todo_types 拆分", "DETAIL_02",
     P3("初次彈窗大多已足夠 → 先訪談確認護理師知道可以再打開；確認後可把固定區塊收合到其他頁籤",
        "部分情況需要再確認 → 保留固定區塊",
        "經常需要再看完整內容 → 保留，並考慮在固定區塊直接顯示完整內容")),
    ("2.0 護理師｜排查異常：主要查看哪些健康資訊", "③ 處理前資訊查看率" + NEW, "主指標／訪問",
     "有提交照護記錄的詳情訪問中，提交前有效查看過該頁籤（或生理體徵）的比例；依頁籤列出",
     "同 detail_visit_id 內、早於 FORM_03 success 的 leave_tab（dwell_seconds ≥ 5）", "有 FORM_03 success 的 detail_visit_id",
     "① 看的是「所有訪問」，混了只是瀏覽、沒有要處理的情況；本指標只看真的完成處理的訪問，才能回答「做處置判斷時靠哪些資訊」", "DETAIL_01、FORM_03",
     P3("做判斷時很少用到 → 可降低該資訊的層級",
        "部分判斷會用到 → 維持現有層級",
        "多數判斷都會用到 → 提高層級，或直接放進照護記錄彈窗作為參考")),
    ("2.1 護理師｜排查異常：影響排查效率的行為", "① 檢測儀數據來源切換率", "主指標／人", "有切換 Home／Pro 的不重複護理師 ÷ 曾在「同時有 Home 與 Pro 資料」的檢測儀頁籤停留 ≥5 秒的不重複護理師；另計：以詳情訪問為單位的切換率",
     "click_button button_name = monitor_source", "leave_tab tab_group = vital_sign\ndwell_seconds ≥ 5\nhas_multi_source = true",
     "以 user_id 去重；分母是「個案、該生理體徵同時有兩種來源的資料」", "分子：TOOL_01\n分母：DETAIL_01",
     P3("不需要切換來源 → 可以移除切換功能", "部分護理師使用 → 保留，但收合成下拉選單", "高頻使用 → 維持現有的切換設計")),
    ("2.1 護理師｜排查異常：影響排查效率的行為", "② 日期時間範圍切換率", "主指標／訪問", "有切換時間範圍的詳情訪問數 ÷ 詳情訪問數；另計各選項佔全部切換次數的比例",
     "click_button button_name = time_range", "view_page patient_detail", "以 detail_visit_id 去重；佔比以次數計。" + TBC + "切換後換頁籤、換個案時會不會保留？",
     "分子：TOOL_02\n分母：ENTER_03",
     P3("預設的近 30 天大多足夠 → 可拿掉快捷選項，只保留日期選擇器",
        "經常切換 → 看各選項佔比；某選項佔比也在高級距時，評估改成預設值",
        "預設區間不符需求 → 依最常用的選項調整預設值，並訪談原因")),
    ("2.1 護理師｜排查異常：影響排查效率的行為", "③ 心電區塊觸及率", "輔助判讀／訪問",
     "各區塊觸及率＝該區塊累計可視 ≥3 秒的心電頁籤訪問數 ÷ 心電頁籤訪問數；另看各區塊可視秒數的中位數",
     "view_block visible_seconds ≥ 3\n依 block_name 分組", "leave_tab tab_name = vital_ecg", "依區塊位置（首屏或需捲動）分開判讀", "分子：TOOL_03\n分母：DETAIL_01",
     P3("該區塊很少被看到 → 先排除位置、捲動距離、沒有資料等因素；需要捲動才看得到的重要區塊考慮上移",
        "部分訪問會看到 → 依首屏／需捲動分開比較",
        "多數訪問會看到 → 訪談該資訊在排查中的作用；若位於下方，考慮上移")),
    ("2.1 護理師｜排查異常：影響排查效率的行為", "④ 心電紀錄篩選使用率", "主指標／人", "有套用篩選的不重複使用者 ÷ 進入心電頁籤的不重複使用者",
     "apply_filter", "leave_tab tab_name = vital_ecg", "以 user_id 去重", "分子：TOOL_04\n分母：DETAIL_01",
     P3("很少使用 → 收合成「進階搜尋」", "部分使用 → 保留，觀察導程與異常篩選哪一種較常用", "經常使用 → 維持現有設計")),
    ("2.1 護理師｜排查異常：影響排查效率的行為", "⑤ 頁籤重複進入率" + NEW, "主指標／訪問",
     "同一次詳情訪問中，重複進入同一頁籤 2 次以上的訪問數 ÷ 詳情訪問數；另列最常來回切換的頁籤組合",
     "同 detail_visit_id 內同一 tab_name 的 leave_tab ≥ 2 筆", "view_page patient_detail",
     "原本 ①～④ 只看單一功能的使用率；本指標直接衡量「資訊是否分散、需要來回翻找」", "DETAIL_01、ENTER_03",
     P3("資訊大多一次就找到 → 維持", "部分訪問需要來回翻找 → 看最常來回的頁籤組合", "資訊明顯分散 → 把常一起看的資訊整合到同一畫面")),
    ("2.1 護理師｜排查異常：影響排查效率的行為", "⑥ 功能使用對排查時長的影響" + NEW, "輔助判讀／訪問",
     "（有使用該功能的訪問排查時長中位數 − 沒使用的排查時長中位數）÷ 沒使用的排查時長中位數；功能包含來源切換、時間範圍切換、心電篩選",
     "有使用該功能的詳情訪問（TOOL_01／02／04）", "沒有使用該功能的詳情訪問",
     "排查時長定義同 3.1 ③；用來驗證這些功能到底是幫助還是拖慢排查，而不只是「有沒有人用」", "TOOL_01、02、04、ENTER_03、FORM_01",
     "縮短（差距 < −10%）：功能有幫助 → 保留，並評估是否預設開啟\n差不多（−10%～+10%）：對效率影響不大 → 依使用率（①②④）決定是否收合\n拉長（差距 > +10%）：功能可能讓排查變複雜 → 訪談使用情境，檢視操作步驟"),
    ("3.0 護理師｜完成處置：是否都有被處理", "（前提）經過護理師完整上線的警報", "前提",
     "警報產生後，至少經過一次護理師完整上線（上線開始到結束；閒置 30 分鐘視為上線結束）的警報", "—", "—",
     "不使用固定的 7 天觀察期：護理師不一定每天上線，改以「是否經過完整上線」判斷，避免把還沒機會處理的警報算成未處理", "SERVER_01、GLOBAL_02", "—"),
    ("3.0 護理師｜完成處置：是否都有被處理", "① 護理師處理閉環完成率", "主指標／警報", "經過護理師完整上線的警報中，截至統計時點已被消除的比例",
     "alert_resolved", "alert_created\n" + OPPH,
     "以 alert_event_id 去重；依 resolve_type 拆分（轉診消除的警報由後端紀錄計入）。" + TBC + "是否有系統自動消除等其他消除方式",
     "分子：SERVER_02\n分母：SERVER_01＋GLOBAL_02",
     P3("多數警報沒有處理完 → 看 ④ 卡關階段分布，找出斷點",
        "有相當比例沒處理完 → 看 ④，並拆機構、警報等級看落差",
        "多數警報有處理完 → 未完成的逐筆檢查，接著看 3.1 處理所需上線次數")),
    ("3.0 護理師｜完成處置：是否都有被處理", "② 照護記錄填寫發起率", "主指標／警報",
     "有打開照護記錄的警報數 ÷ 有護理師進入個案詳情、且沒有以轉診處理的警報數",
     "view_popup popup_name = handle_form\nform_type = care_record", "view_page patient_detail（alert_event_id 有值）\nuser_role ∈ frontline_staff, frontline_doctor\n排除 resolve_type = referral 的警報（後端）",
     "同一警報只算 1 次；轉診醫師表單已優化、不埋點", "分子：FORM_01\n分母：ENTER_03＋SERVER_02",
     P3("多數護理師沒找到處理入口 → 訪談是否不清楚處理機制，加強宣導與按鈕引導",
        "部分護理師沒有發起 → 拆機構與警報等級，找出落差較大的族群", "處理入口清楚 → 維持現有設計")),
    ("3.0 護理師｜完成處置：是否都有被處理", "③ 照護記錄填寫提交率", "主指標／警報", "照護記錄提交成功的警報數 ÷ 有打開照護記錄的警報數",
     "submit_form result = success\nform_type = care_record", "view_popup popup_name = handle_form\nform_type = care_record", "同一警報只算 1 次", "分子：FORM_03\n分母：FORM_01",
     P3("打開後多數沒有提交 → 看表單結果分布與停留時長，訪談開了沒交的原因",
        "有相當比例沒有提交 → 看 3.2 的中途關閉與復開，判斷是查資料還是暫不處理", "多數能完成提交 → 維持現有設計")),
    ("3.0 護理師｜完成處置：是否都有被處理", "④ 未完成警報的卡關階段分布" + NEW, "主指標／警報",
     "經過護理師完整上線、但尚未消除的警報，依「最後到達的步驟」分成四類，各佔未完成警報的比例：未曝光／已曝光未介入／已介入未發起／已發起未提交",
     "依同一 alert_event_id 最後一個事件判定階段", "經過護理師完整上線、但尚未消除的警報",
     "報告的問題是「未處理的卡在哪個環節」，原本沒有直接回答這題的指標；以佔比最高的階段作為優先改善對象", "SERVER_01、02、EXPOSE_02、04、ENTER_03、FORM_01、03",
     "各階段佔比同樣以低（≤30%）／中（31%–60%）／高（≥61%）判讀，佔比最高的階段優先處理：\n未曝光 → 改善提醒（同 1.0）\n已曝光未介入 → 改善點擊引導，或評估是否允許在外層處理（同 1.2）\n已介入未發起 → 處理入口不清楚或資訊不足（看 2.0、3.0 ②）\n已發起未提交 → 表單填寫有阻礙（看 3.2）"),
    ("3.0 護理師｜完成處置：是否都有被處理", "⑤ 轉診醫師填寫發起率、提交率" + OPT, "—",
     "轉診醫師的設計已優化，本次不再埋點。以轉診處理的警報仍由後端紀錄計入閉環完成率", "", "", "", "—", "—"),
    ("3.1 護理師｜完成處置：處理花費時間", "① 處理完成所需的上線次數" + NEW, "主指標／警報",
     "已消除的警報，從產生到消除之間經過幾次護理師上線（產生當下已在線上的那次也算 1 次）；看各級距的佔比",
     "alert_resolved 前的 session_start 次數（該機構護理師）", "alert_resolved",
     "取代原本的「警報處理閉環時長（小時）」：時鐘時間會把下班、沒上線的時間算進去，用上線次數才能反映流程本身的效率", "SERVER_01、02、GLOBAL_02",
     N3("流程能在一次上線內完成 → 維持，作為之後改版的比較基準",
        "需要跨一次上線 → 看是卡在哪一步（3.0 ④）",
        "要拖過多次上線 → 優先看 1.0 ④ 上線後多久才看到、以及 3.0 ④ 卡關階段") + "\n佔比判讀：「1 次」的佔比用低／中／高級距看，低於 31% 代表多數警報無法在一次上線內完成"),
    ("3.1 護理師｜完成處置：處理花費時間", "② 看到後同次上線介入率" + NEW, "輔助判讀／警報",
     "已曝光的警報中，在第一次被看到的同一次上線內就進入個案詳情的比例",
     "第一筆 ENTER_03 與第一筆 item_impression 屬於同一個 session_id", "已曝光的警報",
     "取代原本的「警報介入時長佔比」：不用時鐘時間，直接看「看到之後有沒有當下處理」", "EXPOSE_02、04、ENTER_03、GLOBAL_02",
     P3("看到後多半沒有當下處理 → 訪談原因（警報太多、不急、資訊不足），檢視警報分級與提示",
        "部分會當下處理 → 依警報等級拆分，看高風險是否有當下處理",
        "看到後多會當下處理 → 維持")),
    ("3.1 護理師｜完成處置：處理花費時間", "③ 異常排查時長", "輔助判讀／分鐘", "第一次打開照護記錄的時間 − 同一次詳情訪問的進入時間",
     "同 detail_visit_id 第一筆 view_popup handle_form", "view_page patient_detail",
     "以 detail_visit_id 為單位，本來就在同一次上線內；排除中途切到其他瀏覽器分頁的訪問", "ENTER_03、FORM_01、DETAIL_01",
     T3("分鐘", 3, 5, "能快速取得關鍵資訊 → 維持", "取得資訊稍慢 → 搭配 2.0 ③ 處理前資訊查看率，找出常被翻找的資訊", "取得資訊明顯偏慢 → 搭配 2.1 ⑤ 頁籤重複進入率，調整資訊層級與排序")),
    ("3.1 護理師｜完成處置：處理花費時間", "④ 照護記錄填寫時長", "輔助判讀／秒", "提交成功時間 − 該次表單打開時間",
     "submit_form result = success\nform_type = care_record", "同 form_open_id 的 view_popup", "以 form_open_id 為單位；只算首次打開就提交的那一次", "FORM_01、03",
     T3("秒", 30, 90, "填寫負擔低 → 維持", "有一些填寫負擔 → 搭配 3.2 字數與空提交率觀察", "填寫負擔重 → 搭配 3.2 指標優化填寫方式（例如範本、快捷選項）")),
    ("3.2 護理師｜完成處置：影響處理完成的行為", "① 照護記錄首次打開直接提交率", "主指標／開啟", "首次打開就提交成功的次數 ÷ 首次打開的次數",
     "submit_form result = success\nform_type = care_record\nform_open_seq = 1", "view_popup handle_form\nform_type = care_record\nform_open_seq = 1", "先開照護記錄、後來改走轉診的不算「未直接提交」", "FORM_01、03",
     P3("多數無法一次完成 → 看 ②③，判斷是需要離開查資料，還是暫時不想處理", "有相當比例無法一次完成 → 同上", "彈窗資訊足以一次完成 → 維持現有填寫方式")),
    ("3.2 護理師｜完成處置：影響處理完成的行為", "② 照護記錄中途關閉率（表單結果分布）", "輔助判讀／開啟",
     "中途關閉的次數 ÷ 表單打開次數；另列提交成功、直接離開頁面的比例，三者相加＝100%",
     "close_popup close_method ∈ cancel, close_icon, mask", "view_popup popup_name = handle_form\nform_type = care_record", "以 form_open_id 計", "FORM_01、02、03",
     P3("很少中途關閉 → 維持", "有相當比例中途關閉 → 搭配 ③ 短時間復開率判讀原因", "經常中途關閉 → 搭配 ③：復開也高是需要查資料；復開低是內容不符預期或暫不處理")),
    ("3.2 護理師｜完成處置：影響處理完成的行為", "③ 照護記錄短時間復開率", "輔助判讀／警報",
     "中途關閉後，在同一次詳情訪問中又重新打開的警報數 ÷ 有中途關閉的警報數；之後的訪問才復開的另外統計",
     "close_popup 之後，同 alert_event_id、同 detail_visit_id 有 view_popup", "有 close_popup 的 alert_event_id",
     "改以「同一次詳情訪問」判斷，不另設分鐘門檻", "FORM_01、02",
     P3("關閉後很少馬上回來 → 內容不符預期或當下暫不處理，優化按鈕說明", "部分會回來繼續填 → 觀察回來後的提交率（④）", "關閉多是為了查資料再回來 → 在彈窗補充關鍵參考資料（健康數據、病史摘要）")),
    ("3.2 護理師｜完成處置：影響處理完成的行為", "④ 照護記錄復開後成功提交率", "輔助判讀／開啟", "復開後提交成功的次數 ÷ 復開次數",
     "submit_form result = success\nform_open_seq ≥ 2", "view_popup form_open_seq ≥ 2", "以 form_open_id 計", "FORM_01、03",
     P3("復開後仍多半放棄 → 訪談卡住的原因", "復開後部分能完成 → 搭配 ③ 判讀", "復開後多能完成 → 補充彈窗參考資料可以減少來回")),
    ("3.2 護理師｜完成處置：影響處理完成的行為", "⑤ 照護記錄空提交率", "主指標／提交", "所有欄位都空白的成功提交數 ÷ 成功提交數；另計「勾選了處理項目但沒寫文字」的比例",
     "submit_form result = success\nis_empty = true", "submit_form result = success", "依 alert_level 拆分", "FORM_03",
     P3("護理師有填寫習慣 → 保留現有填寫流程", "部分情境不需要文字 → 依警報等級拆開看；高低風險落差大時，依風險等級設計不同流程", "多數情境不需要文字 → 可在外層加入快速處理；高低風險落差大時，高風險加必填、低風險一鍵處理")),
    ("3.2 護理師｜完成處置：影響處理完成的行為", "⑥ 照護記錄提交字數", "輔助判讀／字", "主文字欄位字數的中位數（另看 P25、P75、P90）",
     "submit_form result = success\ntext_length > 0", "—", "排除空白提交；字數以字元數計", "FORM_03",
     W3("填寫內容簡短 → 維持", "有一定填寫量 → 看 P75 是否落在「多」，判斷是否少數人寫很多", "填寫負擔重 → 提供範本或常用語")),
    ("3.2 護理師｜完成處置：影響處理完成的行為", "⑦ 處理結果類型分布" + NEW, "輔助判讀／提交",
     "成功提交的照護記錄中，處理結果為「誤報排除」與「真異常已處置」各佔的比例",
     "submit_form result = success\nresult_type", "submit_form result = success",
     "報告的業務流程有「誤報排除、真異常處置」兩種結果，但原本沒有指標驗證；依 alert_level、alert_items 拆分。" + TBC + "照護記錄是否有欄位能區分誤報／真異常？沒有的話本指標暫不開發",
     "FORM_03",
     P3("誤報很少 → 警報規則準確，維持", "有相當比例是誤報 → 依警報項目拆分，找出誤報集中的項目，回饋閾值設定", "多數是誤報 → 警報規則需要檢討，否則會讓護理師對警報麻痺（也會拉低 1.0、1.2 的指標）") + "（以「誤報」佔比判讀）"),
    ("3.2 護理師｜完成處置：影響處理完成的行為", "⑧ 轉診醫師填寫行為（首次直接提交、中途關閉、復開、空提交、字數）" + OPT, "—",
     "轉診醫師的設計已優化，本次不再埋點", "", "", "", "—", "—"),
    ("4.0 醫師｜接收轉診：轉診曝光與介入", "（前提）醫師上線時已存在的轉診", "前提",
     "轉診產生後，受轉診醫師至少上線過一次（或產生當下已在線上）的轉診", "—", "—", "不使用固定時間門檻；醫師沒有上線期間的轉診另列「等待醫師上線中的轉診數」", "SERVER_03、GLOBAL_02", "—"),
    ("4.0 醫師｜接收轉診：轉診曝光與介入", "① 轉診曝光率（整體）", "主指標／轉診", "醫師上線時已存在的轉診中，被受轉診醫師曝光的比例",
     "item_impression item_type = referral\nuser_id = 該轉診的 doctor_user_id", "referral_created\n" + OPPR, "跨入口只算 1 次；只算被轉診的那位醫師", "分子：EXPOSE_02、04\n分母：SERVER_03＋GLOBAL_02",
     P3("醫師上線了卻多半沒看到 → 加強登入時的轉診提示", "有相當比例沒看到 → 拆開兩個入口，找出曝光不足的入口", "多數轉診有被看到 → 維持；未曝光的逐筆檢查")),
    ("4.0 醫師｜接收轉診：轉診曝光與介入", "② 轉診曝光率（小鈴鐺通知）", "主指標／轉診", "醫師上線時已存在的轉診中，在小鈴鐺通知被曝光的比例",
     "item_impression list_name = notification_referral", "referral_created\n" + OPPR, "同入口只算 1 次", "分子：EXPOSE_02\n分母：SERVER_03＋GLOBAL_02",
     P3("醫師不常從鈴鐺接收 → 看整體曝光：整體在高級距表示醫師習慣從列表看，維持；整體也低就加強提醒", "鈴鐺與列表並用 → 維持，觀察兩個入口分工", "醫師習慣從鈴鐺接收 → 維持並保留通知")),
    ("4.0 醫師｜接收轉診：轉診曝光與介入", "③ 待醫師處理列表曝光率", "主指標／轉診", "醫師上線時已存在的轉診中，在待醫師處理列表被曝光的比例",
     "item_impression list_name = doctor_pending", "referral_created\n" + OPPR, "同入口只算 1 次", "分子：EXPOSE_04\n分母：SERVER_03＋GLOBAL_02",
     P3("醫師很少用列表 → 了解是否不知道有列表，加強宣導與入口引導", "部分醫師會用 → 維持", "醫師會主動從列表查看 → 維持；小鈴鐺通知可定位為輔助提醒")),
    ("4.0 醫師｜接收轉診：轉診曝光與介入", "④ 轉診介入率", "主指標／轉診", "醫師上線時已存在的轉診中，受轉診醫師進入個案詳情的比例；依進入來源拆分；另計曝光後介入率",
     "view_page patient_detail\nreferral_id ∈ 分母\nuser_id = doctor_user_id", "referral_created\n" + OPPR, "同一轉診只算 1 次；任何入口都算", "分子：ENTER_03\n分母：SERVER_03＋GLOBAL_02",
     P3("多數轉診沒人點進詳情 → 先看曝光率：曝光也低就先改善曝光；曝光高就了解為什麼不點", "部分轉診沒有介入 → 依入口拆分，找出介入偏低的入口", "多數轉診有介入 → 未介入的逐筆檢查")),
    ("4.0 醫師｜接收轉診：轉診曝光與介入", "⑤ 醫師上線頻率" + NEW, "背景數據／人",
     "有被轉診的醫師，每週有上線的天數（中位數）",
     "session_start 的不重複日期數（每週）", "有收到轉診的醫師",
     "小鈴鐺通知只在醫師上線時有效；本指標用來判斷「轉診能不能在平台內被看到」這個前提成不成立", "GLOBAL_02、SERVER_03",
     "少（≤1 天）：小鈴鐺通知很難觸及 → 增加平台外的轉診通知（簡訊、Email）\n中（2～3 天）：轉診可能要等好幾天才被看到 → 依 ⑥ 判斷是否需要平台外通知\n多（≥4 天）：醫師常上線 → 小鈴鐺通知即可"),
    ("4.0 醫師｜接收轉診：轉診曝光與介入", "⑥ 醫師上線後首次看到轉診的時長" + NEW, "主指標／分鐘",
     "轉診首次被受轉診醫師曝光的時間 − 起算時間；起算時間＝轉診產生後醫師第一次上線的時間（產生時已在線上，則從產生時間起算）；取中位數",
     "item_impression 第一筆（item_type = referral）", "session_start（轉診產生後第一筆）或 referral_created",
     "只計算醫師在線上的時間", "EXPOSE_02、04、GLOBAL_02、SERVER_03",
     T3("分鐘", 5, 30, "醫師一上線很快就注意到轉診 → 維持", "上線後過一段時間才看到 → 評估登入時是否主動提示待處理轉診", "上線後很久才看到 → 小鈴鐺通知（轉診）沒有發揮作用，加強登入時的提示") + "\n" + TBC + "5／30 分鐘的級距"),
    ("5.0 醫師｜評估病情：主要查閱哪些資訊", "① 轉診異常項目查看率", "主指標／訪問",
     "有查看「本次轉診異常項目」生理體徵頁籤 ≥3 秒的詳情訪問數 ÷ 受轉診醫師進入、且個案有待處理轉診的詳情訪問數",
     "leave_tab tab_group = vital_sign\nis_referral_item = true\ndwell_seconds ≥ 3", "view_page patient_detail\nhas_pending_referral = true\nuser_id = doctor_user_id",
     "以 detail_visit_id 去重；排除該頁籤是預設頁籤的訪問", "分子：DETAIL_01\n分母：ENTER_03",
     P3("醫師多半靠護理師轉述 → 在醫師建議彈窗中直接顯示待處理的異常數據", "部分醫師會查看 → 維持，觀察排查時長", "醫師依異常項目了解狀況 → 維持，接著看排查時長是否偏長")),
    ("5.0 醫師｜評估病情：主要查閱哪些資訊", "② 歷史處理紀錄查看率", "主指標／訪問",
     "有查看處理紀錄（列表停留 ≥5 秒，或打開單筆詳情 ≥5 秒）的詳情訪問數 ÷ 受轉診醫師進入、且個案有處理紀錄的詳情訪問數；另看查看是在寫建議之前或之後",
     "leave_tab tab_name = care_records 且 dwell_seconds ≥ 5\n或 close_popup popup_name = care_record_detail 且 dwell_seconds ≥ 5", "view_page patient_detail\ntabs_with_data 含 care_records\nuser_id = doctor_user_id",
     "以 detail_visit_id 去重", "分子：DETAIL_01、DOC_01、02\n分母：ENTER_03",
     P3("醫師很少看過往紀錄 → 維持現有設計", "部分醫師會看 → 觀察查看與寫建議的先後順序", "過往紀錄是重要參考 → 在醫師建議彈窗提供近期紀錄摘要，減少切換頁籤")),
    ("5.0 醫師｜評估病情：主要查閱哪些資訊", "③ 處理前資訊查看率（醫師）" + NEW, "主指標／訪問",
     "有提交醫師建議的詳情訪問中，提交前有效查看過該頁籤的比例；依頁籤列出", "同 detail_visit_id 內、早於 FORM_03 success 的 leave_tab（dwell_seconds ≥ 5）", "有 FORM_03 success（form_type = doctor_advice）的 detail_visit_id",
     "算法同 2.0 ③", "DETAIL_01、FORM_03", "級距與行動同 2.0 ③"),
    ("5.0 醫師｜評估病情：主要查閱哪些資訊", "④ 待辦資訊再次查看率（醫師）", "主指標／訪問", "同 2.0 ②，只計醫師", "同 2.0 ②", "同 2.0 ②", "同 2.0 ②", "DETAIL_02", "級距與行動同 2.0 ②"),
    ("5.0 醫師｜評估病情：主要查閱哪些資訊", "⑤ 心電區塊觸及率、心電紀錄篩選使用率（醫師）", "—", "同 2.1 ③④，只計醫師", "", "", "", "TOOL_03、04、DETAIL_01", "級距與行動同 2.1 ③④"),
    ("6.0 醫師｜完成轉診處置", "① 轉診處理閉環完成率", "主指標／轉診", "經過醫師完整上線的轉診中，截至統計時點已處理完成的比例",
     "referral_resolved", "referral_created\n只計經過醫師完整上線的轉診", "以 referral_id 去重", "分子：SERVER_04\n分母：SERVER_03＋GLOBAL_02",
     P3("多數轉診沒有處理完 → 看 ④ 卡關階段分布", "有相當比例沒處理完 → 看 ④，並拆醫師看落差", "多數轉診有處理完 → 未完成的逐筆檢查，接著看處理所需上線次數")),
    ("6.0 醫師｜完成轉診處置", "② 轉診處理所需的上線次數" + NEW, "主指標／轉診",
     "已處理的轉診，從產生到處理完成之間，受轉診醫師上線了幾次", "referral_resolved 前該醫師的 session_start 次數", "referral_resolved",
     "取代原本的「轉診處理閉環時長（小時）」", "SERVER_03、04、GLOBAL_02",
     N3("醫師在一次上線內完成 → 維持", "需要跨一次上線 → 看卡在哪一步（④）", "要拖過多次上線 → 看 4.0 ⑥ 上線後多久才看到、以及 ④ 卡關階段")),
    ("6.0 醫師｜完成轉診處置", "③ 醫師建議填寫發起率、提交率、首次直接提交率、中途關閉率、短時間復開率、復開後提交率、空提交率、字數；看到後同次上線介入率、排查時長、填寫時長", "—",
     "算法同 3.0 ②③、3.1 ②③④、3.2 ①～⑥；form_type = doctor_advice，以 referral_id 串接", "", "", "", "FORM_01、02、03", "級距與行動同 3.0 ②③、3.1 ②③④、3.2 ①～⑥"),
    ("6.0 醫師｜完成轉診處置", "④ 未完成轉診的卡關階段分布" + NEW, "主指標／轉診",
     "經過醫師完整上線、但尚未完成的轉診，依最後到達的步驟分成：未曝光／已曝光未介入／已介入未發起／已發起未提交，各佔比例",
     "依同一 referral_id 最後一個事件判定", "經過醫師完整上線、但尚未完成的轉診", "算法同 3.0 ④", "SERVER_03、04、EXPOSE_02、04、ENTER_03、FORM_01、03", "判讀與行動同 3.0 ④"),
]


# 中間級距沒有獨立行動的指標，改用兩個級距
TWO = {'② 警報曝光率（小鈴鐺通知）': ('小鈴鐺通知不是主要管道 → 看列表曝光率；列表也偏低時，加強提示（例如登入時即時彈出）', '小鈴鐺通知是主要管道 → 維持設計，可評估列表入口是否需要精簡'), '③ 警報列表曝光率': ('多數護理師不走列表 → 訪談是否不知道有列表，加強宣導與入口引導', '護理師會主動從列表處理 → 維持；小鈴鐺通知可定位為輔助提醒'), '④ 心電紀錄篩選使用率': ('很少使用 → 收合成「進階搜尋」', '經常使用 → 維持現有設計，觀察導程與異常篩選哪一種較常用'), '① 照護記錄首次打開直接提交率': ('多數無法一次完成 → 看 ②③，判斷是需要離開查資料，還是暫時不想處理', '彈窗資訊足以一次完成 → 維持現有填寫方式'), '④ 照護記錄復開後成功提交率': ('復開後仍多半放棄 → 訪談卡住的原因', '復開後多能完成 → 在彈窗補充參考資料，可以減少來回'), '② 轉診曝光率（小鈴鐺通知）': ('醫師不常從小鈴鐺通知接收 → 看整體曝光：整體也偏低就加強登入時的提示', '醫師習慣從小鈴鐺通知接收 → 維持'), '③ 待醫師處理列表曝光率': ('醫師很少用列表 → 了解是否不知道有列表，加強宣導與入口引導', '醫師會主動從列表查看 → 維持；小鈴鐺通知可定位為輔助提醒'), '① 轉診異常項目查看率': ('醫師多半靠護理師轉述 → 在醫師建議彈窗中直接顯示待處理的異常數據', '醫師會依異常項目了解狀況 → 維持，接著看排查時長'), '② 歷史處理紀錄查看率': ('醫師很少看過往紀錄 → 維持現有設計', '過往紀錄是重要參考 → 在醫師建議彈窗提供近期紀錄摘要，減少切換頁籤')}
def _two(name):
    return next((v for k, v in TWO.items() if name.startswith(k)), None)


M = [tuple(list(m[:8]) + [P2(*_two(m[1]))]) if _two(m[1]) else m for m in M]
for k in TWO:
    assert any(m[1].startswith(k) for m in M), k

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
    ("未採用原因（同事版本對照）", "對照同事版本後，評估不建議加入的事件或參數整列以灰字列出，並在此欄寫原因；評估確認後可整列刪除", "已在全域屬性帶入，不需重複列出"),
]
for g in guide:
    ws.append(g)
    style_row(ws, ws.max_row, 3)
ws.append([])
ws.append(["報告章節", "編號前綴", ""])
for c in range(1, 4):
    ws.cell(ws.max_row, c).fill, ws.cell(ws.max_row, c).font = SEC_FILL, Font(bold=True)
for ch in CHAPTERS:
    ws.append(ch)
    style_row(ws, ws.max_row, 3)
widths(ws, [34, 100, 46])
ws.freeze_panes = "A2"

# =====================================================================
# Sheet 2：指標對照
# =====================================================================
ws = wb.create_sheet("指標對照")
header(ws, ["報告章節", "指標", "類型／單位", "計算方式", "分子：事件與條件", "分母：事件與條件", "去重／計算規則", "對應事件編號", "對應情境（固定級距與行動）"])
for m in M:
    ws.append(list(m))
    style_row(ws, ws.max_row, 9)
ws.cell(1, 11, "類型").fill = HDR_FILL
ws.cell(1, 12, "說明").fill = HDR_FILL
LEGEND = [
    ("主指標", "直接用來判斷有沒有問題，情境的門檻設在它上面"),
    ("輔助判讀", "不單獨判讀，主指標異常時用來找原因"),
    ("前提", "計算前先篩選的條件，不是指標本身"),
    ("單位", "說明"),
    ("人", "以 user_id 去重，同一個人只算一次；排除 org_admin、admin；不同天的人數不能直接相加"),
    ("警報", "以 alert_event_id 為單位：同一個案未處理期間的多筆警報合併為一個"),
    ("轉診", "以 referral_id 為單位"),
    ("訪問", "以 detail_visit_id 為單位，每次進入個案詳情算一次"),
    ("開啟", "以 notify_session_id／form_open_id 為單位，每打開一次彈窗算一次"),
    ("提交", "以每一次提交為單位"),
    ("上線", "以 session_id 為單位；登入或閒置 30 分鐘後回到平台算一次新的上線"),
    ("上線時已存在／完整上線", "曝光、介入只算護理師（醫師）上線時已存在的警報（轉診）；閉環只算經過完整上線（從上線到下線，閒置 30 分鐘視為下線）的警報；不使用固定的 24 小時、7 天門檻"),
    ("小鈴鐺通知", "頁面右上角鈴鐺打開的通知彈窗；報告中「消息通知」「異常提醒通知」「最新通知」都統一稱為小鈴鐺通知，醫師端稱小鈴鐺通知（轉診）"),
    ("秒／分鐘／字", "時長以伺服器時間計算；看中位數、P75、P90，平均數只當參考"),
    ("曝光定義", "項目露出 ≥50% 進入可視範圍即算；載入、捲動、翻頁都計；同一次開啟或瀏覽中，同一項目只算一次"),
    ("級距", "說明"),
    ("比率類（三級距）", "低（≤30%）｜中（31%–60%）｜高（≥61%）；比率四捨五入到整數後歸級，三個級距涵蓋 0–100%"),
    ("比率類（兩級距）", "低（≤50%）｜高（≥51%）；用於中間級距沒有獨立行動的指標"),
    ("上線次數", "1 次（當次上線就完成）｜2 次｜3 次以上，看各級距佔比"),
    ("上線後回應時長", "短（≤5 分鐘）｜中（>5～30 分鐘）｜長（>30 分鐘），只計上線時間，以中位數歸級（待確認）"),
    ("通知內時長", "短（≤10 秒）｜中（>10～30 秒）｜長（>30 秒），以中位數歸級（待確認）"),
    ("排查時長", "短（≤3 分鐘）｜中（>3～5 分鐘）｜長（>5 分鐘），以中位數歸級"),
    ("填寫時長", "短（≤30 秒）｜中（>30～90 秒）｜長（>90 秒），以中位數歸級"),
    ("字數", "少（≤20 字）｜中（21～50 字）｜多（>50 字），以中位數歸級"),
    ("已優化，不埋點", "轉診醫師表單的設計已優化，相關指標本次不追蹤"),
]
for i, (k, v) in enumerate(LEGEND, start=2):
    ws.cell(i, 11, k); ws.cell(i, 12, v)
    for c in (11, 12):
        ws.cell(i, c).alignment, ws.cell(i, c).border = WRAP, BORDER
    if k in ("單位", "級距"):
        ws.cell(i, 11).fill = ws.cell(i, 12).fill = HDR_FILL
for c in (11, 12):
    ws.cell(1, c).font, ws.cell(1, c).border = HDR_FONT, BORDER
for i, (k, _) in enumerate(LEGEND, start=2):
    if k in ("單位", "級距"):
        ws.cell(i, 11).font = ws.cell(i, 12).font = HDR_FONT
widths(ws, [28, 30, 13, 42, 38, 34, 38, 22, 60, 3, 14, 50])
ws.freeze_panes = "C2"

# =====================================================================
# Sheet 3：DRD（一列一屬性，事件層欄位合併）
# =====================================================================
ws = wb.create_sheet("DRD")
H = ["報告章節", "編號", "頁面/區塊", "事件名稱（Event Name）", "觸發時機/事件定義（Trigger）", "目標/數據分析意義", "對應報告指標",
     "屬性參數（Property）", "屬性定義（Property Definition）", "資料型別（Data Type）", "範例值（Sample Values）", "優先級", "埋點狀態", "備注", "未採用原因（同事版本對照）"]
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
        row += [key, def_o or d, t, sample_o if sample_o is not None else s, pri, "規劃中", note if j == 0 else None, None]
        ws.append(row)
        style_row(ws, ws.max_row, len(H))
    end = ws.max_row
    if end > start:
        for col in list(range(1, 8)) + [14]:
            ws.merge_cells(start_row=start, start_column=col, end_row=end, end_column=col)
    if TBC in (note or ""):
        ws.cell(start, 14).fill = TBC_FILL
widths(ws, [24, 11, 22, 16, 32, 30, 24, 22, 40, 11, 34, 7, 9, 56, 24])
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
    ("使用者身分", "user_role", "org_admin / admin / doctor / frontline_doctor / frontline_staff", "String", "帳號角色：機構管理員、管理員、醫師、一線醫師、一線人員", "登入成功、取得帳號權限時設定；角色變更時更新", "登出時清空", "排除管理員帳號；區分警報處理端（一線人員、一線醫師）與轉診端（醫師）的指標", "高", "規劃中"),
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

wb.save(OUT)
print("saved", OUT)
