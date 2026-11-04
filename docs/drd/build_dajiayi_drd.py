# -*- coding: utf-8 -*-
"""產生「大家醫平台 埋點 DRD」Excel。修改內容後重新執行：python3 docs/drd/build_dajiayi_drd.py"""
import os
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils import get_column_letter

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "大家醫平台_埋點DRD_v0.1.xlsx")
TBC = "【待確認】"

HDR_FILL = PatternFill("solid", fgColor="1F3A5F")
HDR_FONT = Font(bold=True, color="FFFFFF")
SEC_FILL = PatternFill("solid", fgColor="DCE6F1")
TBC_FILL = PatternFill("solid", fgColor="FFF2CC")
SRV_FILL = PatternFill("solid", fgColor="E2EFDA")
thin = Side(style="thin", color="BFBFBF")
BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)
WRAP = Alignment(wrap_text=True, vertical="top")

wb = Workbook()
wb.remove(wb.active)


def sheet(title, headers, rows, widths, tbc_cols=(), section_col=None, fill_rule=None):
    ws = wb.create_sheet(title)
    ws.append(headers)
    for c in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=c)
        cell.fill, cell.font, cell.alignment, cell.border = HDR_FILL, HDR_FONT, Alignment(wrap_text=True, vertical="center"), BORDER
    for r in rows:
        if isinstance(r, str):  # 分段標題列
            ws.append([r])
            i = ws.max_row
            for c in range(1, len(headers) + 1):
                ws.cell(row=i, column=c).fill = SEC_FILL
            ws.cell(row=i, column=1).font = Font(bold=True)
            continue
        ws.append(list(r) + [""] * (len(headers) - len(r)))
        i = ws.max_row
        rowfill = fill_rule(r) if fill_rule else None
        for c in range(1, len(headers) + 1):
            cell = ws.cell(row=i, column=c)
            cell.alignment, cell.border = WRAP, BORDER
            v = cell.value
            if rowfill:
                cell.fill = rowfill
            if isinstance(v, str) and TBC in v:
                cell.fill = TBC_FILL
    for idx, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(idx)].width = w
    ws.freeze_panes = "B2" if title not in ("0_封面與版本",) else None
    ws.auto_filter.ref = f"A1:{get_column_letter(len(headers))}{ws.max_row}"
    return ws


# ---------------------------------------------------------------- 0 封面
cover = wb.create_sheet("0_封面與版本")
cover_rows = [
    ("文件", "大家醫平台 埋點需求文件（DRD）"),
    ("版本", "v0.1 初稿（2026-11-04）"),
    ("來源", "Figma：大家醫平台埋點規劃 ／ 20261013埋點報告 V3（node 2404-159006）"),
    ("產品形態", "Web 平台（B2B，機構端）；使用者為護理師／個管師／醫師"),
    ("本次範圍", "護理師：01 發現異常、02 排查異常（個案詳情）、03 完成異常處置並記錄\n醫師：01 接收轉診、02 評估病情（個案詳情）、03 完成轉診處置並記錄"),
    ("本次不做", "護理師 01 完成個案收案、05 個案待辦與未測量追蹤（報告標註：本次暫不分析）"),
    ("分頁導覽", "1_Review意見：對範例（CoDoctor DRD）與本報告指標的 review\n2_填寫說明：新版模板欄位、命名與型別規範\n3_指標對照：每個指標的分子／分母／去重規則與對應事件\n4_事件清單：一事件一列，給工程實作\n5_屬性字典：一屬性一列，全文件同 key 同義\n6_後端資料需求：非前端埋點、需後端提供的資料\n7_待確認問題：需要產品／工程／研究確認的事項"),
    ("顏色", "黃底＝待確認；綠底＝後端事件／後端資料；藍底＝分段標題"),
    ("變更紀錄", "v0.1｜2026-11-04｜由 Figma 報告整理初稿，含指標修正建議與待確認問題"),
]
for k, v in cover_rows:
    cover.append([k, v])
for row in cover.iter_rows():
    row[0].font = Font(bold=True)
    for c in row:
        c.alignment, c.border = WRAP, BORDER
cover.column_dimensions["A"].width = 14
cover.column_dimensions["B"].width = 110
for i in range(1, cover.max_row + 1):
    if "黃底" in str(cover.cell(i, 2).value):
        cover.cell(i, 2).fill = TBC_FILL

# ---------------------------------------------------------------- 1 Review
review = [
    "A. 範例模板（CoDoctor DRD）結構問題",
    ("A1", "結構", "一列一屬性＋合併儲存格：事件層資訊（名稱、觸發時機）只出現在合併區第一列", "篩選、排序、樞紐分析都會壞；工程複製到 Jira／程式碼時容易漏掉屬性", "拆成「事件清單（一事件一列）」＋「屬性字典（一屬性一列）」，事件列用 key 清單引用屬性；不用合併儲存格", "高"),
    ("A2", "結構", "共用屬性在每個事件重複定義（page_name、login_session_id、bind_flow_id 各寫了 4–6 次）", "改一個定義要改很多處，容易不一致（例：retry_count 在 BIND_04、BIND_05 定義不同）", "屬性只在「屬性字典」定義一次；事件特有的值域寫在事件列備註", "高"),
    ("A3", "欄位", "缺「觸發端」（前端／後端）", "登入成功、綁定結果、提交成功這類「結果」若由前端送，會受網路中斷、重複點擊影響；大家醫的警報生成、警報消除只有後端知道", "新增「觸發端」欄：前端 / 後端 / 前端（API 回傳後）", "高"),
    ("A4", "欄位", "缺「必填」與「空值規則」，只在備註零散寫（如「送 null 不要送空字串」）", "工程各自判斷，資料出現 null、''、0 混用", "屬性字典新增「必填」「空值規則」欄，統一：取不到送 null，不送空字串、不用 0 代替", "中"),
    ("A5", "欄位", "資料型別只有 String / Integer / Boolean", "時間、清單被迫存成字串（如 preview_notification_ids 用逗號串、preview_created_at 靠順序對應），解析容易出錯", "加入 Number（小數）、Datetime（ISO 8601 含時區）、Array<String>", "中"),
    ("A6", "欄位", "缺「驗收方式」與「負責人」，但狀態欄有「已驗收」", "沒有驗收標準，「已驗收」無法判斷", "事件清單新增「驗收方式」（操作步驟＋預期送出值）與「工程負責人」", "中"),
    ("A7", "欄位", "優先級放在屬性層，同一事件內不一致（FAMILY_01 事件為中，但 search_flow_id 為高）", "排期時無法判斷這個事件要不要做", "優先級放事件層；屬性層只標「必填／選填」", "中"),
    ("A8", "欄位", "「未採用原因」「反問AI」是工作過程欄位", "交給工程時會造成干擾", "移到 Review／變更紀錄分頁，正式 DRD 不保留", "低"),
    ("A9", "編號", "依「報告章節」編號（LOGIN_、HOME_…），跨章節共用事件只能塞在其中一章（如 TREND_01 同時給 2.2、2.3 用）", "事件歸屬混亂，指標對照還得寫「沿用 2.2 的 TREND_01」", "依「功能模組」編號（NOTIFY_、LIST_、DETAIL_、FORM_），指標與事件的對應改在「指標對照」維護，一個事件可以服務多個指標", "中"),
    ("A10", "指標對照", "K、L 欄把「類型」「單位」圖例和指標表混在同一張表", "篩選時圖例會混進資料", "圖例移到「填寫說明」", "低"),
    "B. 範例內容的具體錯誤（若之後沿用該檔請一併修正）",
    ("B1", "編號錯位", "指標對照 2.2 ② 引用 TREND_03（date_prev / date_next），但 DRD 沒有 TREND_03，直接從 TREND_02 跳到 TREND_04", "過往區間查看率沒有事件可算", "補上 TREND_03 或修正指標對照", "高"),
    ("B2", "編號錯位", "2.3：指標對照寫 HISTORY_01＝歷史列表、HISTORY_02＝單日、HISTORY_03＝單筆；DRD 是 HISTORY_01＝點擊入口、02＝列表、03＝單日、04＝單筆", "分析時會拿錯事件", "以 DRD 為準更新指標對照", "高"),
    ("B3", "事件不存在", "指標對照 4.1 ②③ 使用 notification_view，但 DRD 的 NOTIFY_02 是 view_page", "工程照 DRD 做，分析照指標對照找會找不到", "兩份統一事件名稱", "高"),
    ("B4", "同 key 不同義", "device 在首頁＝設備分頁、在歷史紀錄＝資料來源設備、在報告＝報告來源設備；source 在 4 個事件裡值域都不同", "違反範例自己「同一概念同一 key」的規則，跨事件分析時會混淆", "拆成 device_tab / data_source_device，或在屬性字典中逐事件列出值域", "中"),
    ("B5", "ID 衝突", "home_visit_id 與 history_visit_id 的範例都用 hv_ 前綴", "資料中無法從前綴辨識 ID 類型", "流程 ID 建議統一用 UUID v4，不靠前綴辨識", "低"),
    ("B6", "串接鍵不一致", "2.3 ② 說用 detail_visit_id 串接，但 DRD 已另外新增 history_visit_id", "分析規則與實作不一致", "統一改用 history_visit_id", "中"),
    ("B7", "離開事件遺失", "home_scroll_depth、leave_page 只在「離開時」送出", "App 被殺掉、斷網時事件會遺失，瀏覽深度與停留時長會偏低", "同時監聽切到背景（App）／visibilitychange（Web）；備註寫明遺失率預期", "中"),
    "C. 大家醫報告（Figma）指標的問題：已在 3_指標對照 修正，原文差異寫在「與報告差異」欄",
    ("C1", "單位不一致", "多個指標分子與分母單位不同：照護記錄填寫發起率（點擊次數 ÷ 人數）、時間範圍切換率（次數 ÷ 不重複人數）、心電篩選使用率（點擊次數 ÷ 人數）、來源篩選使用率（可能超過 100%）", "比率可能超過 100%，也無法比較", "分子、分母統一同一個單位（警報事件／詳情訪問／彈窗開啟／人）", "高"),
    ("C2", "單位定義", "「警報個案數」「警報總人數」「個案警報數」混用；但去重規則又說「同一個案發生兩次獨立異常事件時，以事件去重」", "實際單位是「警報事件」，不是人", "定義「警報事件 alert_event_id」：同一個案在未處理期間的多筆警報合併為一筆，處理後再發生就是新事件；需後端提供", "高"),
    ("C3", "複製錯誤", "轉診醫師相關指標的觸發時機寫成「醫師建議」「撰寫照護記錄」；轉診醫師中途關閉率的分母寫成「照護記錄」彈窗；醫師建議填寫提交率的觸發時機寫成「點擊醫師建議／進入個案詳情」；轉診處理閉環時長寫「撰寫照護記錄」", "工程照抄會埋錯", "已在指標對照逐條改正", "高"),
    ("C4", "重複指標", "「整體照護記錄提交成功率」與「照護記錄填寫提交率」以同一個個案／任務去重時，兩者算出來會相同", "報告裡會出現兩個一樣的數字", "保留一個，另一個改成「次數口徑」（提交次數 ÷ 開啟次數）或刪除", "中"),
    ("C5", "分母範圍", "單一頁籤查看率的分子限定「該頁籤有資料」，分母卻是所有詳情訪問；心電篩選使用率的分母是「進入個案詳情」而不是「進入心電頁籤」；待辦再次查看率的分母沒有限定「有待辦彈窗」", "比率被系統性低估", "分母加上相同的前提條件（DETAIL_01 新增 tabs_with_data、has_todo）", "高"),
    ("C6", "測量方法", "心電區塊「有效曝光」用滑鼠停留判斷", "滑鼠停在哪裡不等於在看哪裡（看圖時滑鼠常停在旁邊）；觸控板、捲動時都量不準", "建議改用「區塊在可視範圍內 ≥50% 的累計秒數」為主，滑鼠停留只當輔助", "中"),
    ("C7", "曝光定義", "列表曝光只寫「載入時統計視窗範圍內」，漏掉後續捲動、翻頁才看到的項目；通知彈窗另有「捲入才算」，兩個入口定義不同", "列表曝光被低估，兩個入口無法比較", "兩處統一：項目可見 ≥50%（可加停留 ≥500ms）即算曝光，載入、捲動、翻頁都要計", "高"),
    ("C8", "觀察窗", "閉環完成率沒有定義「多久內完成才算」", "週期末才產生的警報會被算成未完成", "定義觀察窗（建議：警報產生後 7 天內），並只計算已滿觀察窗的警報", "高"),
    ("C9", "統計量", "時長指標寫「平均數、中位數、P50/P75」，但 P50 就是中位數；處理記錄填寫時長門檻「< 30」沒寫單位，假設 B 又誤寫成「異常排查時長 > 90 秒」", "門檻無法判讀", "統一：中位數、P75、P90（平均數只當參考）；門檻補上單位", "低"),
    ("C10", "隱私", "照護記錄、轉診意見、醫師建議都是病歷內容", "如果把原文送進埋點工具會有醫療個資風險", "只送字數、是否為空、填寫欄位數，不送原文；patient_id 用內部 ID，不送姓名、身分證號", "高"),
    ("C11", "用語", "Figma 上多處 Property 誤寫成「Poverty」", "—", "DRD 一律用 Property", "低"),
    "D. 附件 CSV",
    ("D1", "檔案", "上傳的 CSV（app 埋點 DRD P1）中文字已在存檔時變成「?」，原始文字無法還原", "無法 review", "請用 Excel「另存為 → CSV UTF-8」重新匯出，或直接提供 xlsx", "—"),
]
sheet("1_Review意見", ["編號", "類別", "問題", "影響", "建議做法", "嚴重度"], review, [6, 12, 60, 45, 60, 8])

# ---------------------------------------------------------------- 2 填寫說明
guide = [
    "事件清單欄位（4_事件清單）",
    ("事件編號", "模組前綴_流水號；同一事件只有一個編號，可服務多個指標", "DETAIL_01"),
    ("模組", "功能模組（不是報告章節），見下方前綴表", "個案詳情"),
    ("頁面／區塊", "讓設計與工程對得上畫面", "個案詳情／頁籤"),
    ("事件名稱", "snake_case；動詞_受詞。優先用通用事件 view_page / view_popup / close_popup / click_button；只有通用事件表達不了時才新增（例：item_impression、submit_form）", "view_page"),
    ("觸發端", "前端｜前端（API 回傳後）｜後端。「結果」類事件（提交成功、警報生成）一律以後端或 API 回傳為準", "前端（API 回傳後）"),
    ("觸發時機", "寫到工程能判斷的程度：哪個動作、畫面到什麼狀態、成功還是點擊當下", "彈窗渲染完成、出現在畫面時"),
    ("不觸發／排除條件", "哪些情況不送，例如重新整理、API 失敗", "API 失敗不送 success"),
    ("去重／頻率", "同一動作重複時怎麼送；曝光事件的批次規則", "同一 notify_session_id 內同一項目只送一次"),
    ("事件屬性", "列出屬性 key（不含全域屬性）；定義一律查 5_屬性字典", "detail_visit_id, patient_id"),
    ("對應指標", "填 3_指標對照 的指標編號，可多個", "N1-06, N3-07"),
    ("適用角色", "nurse / case_manager / doctor", "nurse, doctor"),
    ("優先級", "P0＝直接算主指標；P1＝輔助診斷；P2＝觀察用", "P0"),
    ("埋點狀態", "規劃中 → 開發中 → 已開發 → 已驗收；不做的填「暫不開發」並在備註寫原因", "規劃中"),
    ("驗收方式", "QA 照著操作就能驗：步驟＋預期送出值", "點鈴鐺 → 收到 1 筆 view_popup，popup_name=notification_center"),
    "屬性字典欄位（5_屬性字典）",
    ("屬性 key", "snake_case；同一概念全文件同一個 key，不同概念不得共用", "entry_source"),
    ("資料型別", "String｜Integer｜Number｜Boolean｜Datetime（ISO 8601 含時區）｜Array<String>｜Array<Integer>", "Array<String>"),
    ("允許值／格式", "列舉型列出全部值；ID 寫格式（建議 UUID v4）；數字不加千分位", "today, last_7d, last_30d"),
    ("必填", "是｜否｜條件（寫明條件）", "條件：entry_source 為 notification_alert 時必填"),
    ("空值規則", "取不到送 null；不送空字串、不用 0 代替", "null"),
    ("資料來源", "前端｜後端｜分析端計算（不需工程送）", "前端"),
    "命名與測量通則",
    ("時間", "所有時長以「後端收到時間」計算；前端另送 client_time 供排查。時區統一 +08:00", ""),
    ("曝光（impression）", "項目在可視範圍 ≥50% 即算曝光（停留門檻見待確認 Q2）；載入、捲動、翻頁都計；同一 session 同一項目只送一次；500ms 內新曝光合併成一筆，用 Array 送出", ""),
    ("停留時長", "於離開（切頁籤、離頁、關彈窗、visibilitychange=hidden）時送出 dwell_seconds；頁面隱藏期間不計", ""),
    ("流程 ID", "detail_visit_id、notify_session_id、form_open_id 等由前端在流程開始時產生 UUID v4，流程內事件沿用", ""),
    ("醫療個資", "不送任何自由文字、姓名、證號、量測值原文；只送 ID、列舉值、字數、布林", ""),
    "模組前綴",
    ("GLOBAL_", "全域屬性（每筆事件都帶）", ""),
    ("SYS_", "後端事件：警報、轉診的生成與消除", ""),
    ("NOTIFY_", "消息通知（小鈴鐺）：異常提醒、轉診提醒", ""),
    ("LIST_", "待處理列表：護理師的檢測高風險／異常上報／檢測低風險，醫師的待醫師處理", ""),
    ("DETAIL_", "個案詳情：頁籤、待辦彈窗、來源切換、時間範圍、心電、處理紀錄", ""),
    ("FORM_", "處置表單：照護記錄、轉診醫師、醫師建議（以 form_type 區分）", ""),
    "指標類型與計算單位",
    ("主指標", "直接用來判斷有沒有問題，判讀門檻設在它上面", ""),
    ("輔助判讀", "主指標異常時用來找原因，不單獨判讀", ""),
    ("前提", "計算前先篩選的條件，不是指標本身", ""),
    ("單位：人", "以 user_id 去重；不同期間的人數不能直接相加", ""),
    ("單位：警報事件", "以 alert_event_id 去重（同一個案未處理期間的警報合併）", ""),
    ("單位：轉診", "以 referral_id 去重", ""),
    ("單位：詳情訪問", "以 detail_visit_id 去重，每次進入個案詳情算一次", ""),
    ("單位：開啟", "以 form_open_id / notify_session_id 去重，每次打開彈窗算一次", ""),
]
sheet("2_填寫說明", ["欄位／項目", "怎麼填", "範例"], guide, [20, 90, 50])

# ---------------------------------------------------------------- 3 指標對照
H_M = ["指標編號", "角色", "階段／問題", "指標名稱", "類型", "單位", "公式", "分子（事件＋條件）", "分母（事件＋條件）",
       "去重／計算規則", "拆分維度", "判讀門檻（報告假設摘要）", "對應事件", "需後端資料", "與報告差異／修正說明"]
M = [
    "護理師｜01 發現異常｜Q1 異常是否能有效被護理師看到？",
    ("N1-01", "護理師", "01 發現異常／Q1", "警報曝光率（整體）", "主指標", "警報事件", "至少被曝光 1 次的警報事件數 ÷ 期間內產生的警報事件數",
     "item_impression（NOTIFY_02 或 LIST_02）\nitem_type = alert\nalert_event_id ∈ 分母\n曝光時間早於 alert_resolved", "alert_created（SYS_01）\n期間內產生",
     "跨入口重複曝光只算 1 次；只計 role ∈ nurse, case_manager 的曝光；另計「重複曝光率」＝兩個入口都曝光過 ÷ 已曝光", "alert_level, org_id, 入口",
     "＝100%：看各入口分布，重複曝光 >50% 時考慮把入口單一化\n<100%：判斷是警報太多來不及看，還是根本沒看到", "SYS_01, NOTIFY_02, LIST_02", "是", "單位由「個案／人」統一為「警報事件」（見 Review C2）"),
    ("N1-02", "護理師", "01 發現異常／Q1", "警報曝光率（消息通知）", "主指標", "警報事件", "在通知彈窗被曝光的警報事件數 ÷ 期間內產生的警報事件數",
     "NOTIFY_02\nlist_name = notification_alert", "SYS_01", "同入口重複曝光只算 1 次", "alert_level, source_filter",
     ">80%：小鈴鐺是主要接收管道，維持設計\n<50%：看其他入口；若也 <50%，就要加強通知提示", "SYS_01, NOTIFY_02", "是", "曝光定義與列表統一（Review C7）"),
    ("N1-03", "護理師", "01 發現異常／Q1", "警報列表曝光率（高風險／異常上報／低風險）", "主指標", "警報事件", "在該列表被曝光的警報事件數 ÷ 期間內產生的警報事件數；另計三個列表合計",
     "LIST_02\nlist_type = high_risk / abnormal_report / low_risk", "SYS_01（合計口徑）\n另提供分級口徑：分母只算該等級的警報",
     "同入口重複曝光只算 1 次；載入、捲動、翻頁都計", "list_type",
     "合計 >80%：護理師會主動、規律地處理\n合計 <10%：可能不知道有這個列表，需加強宣導與引導", "SYS_01, LIST_01, LIST_02", "是",
     "報告只計「載入時」視窗內的項目，改為含捲動與翻頁；新增分級口徑，避免高風險列表被低風險警報稀釋"),
    "護理師｜01 發現異常｜Q2 查看通知時，是否還有其他操作影響查看效率？",
    ("N1-04", "護理師", "01 發現異常／Q2", "消息通知來源篩選使用率", "主指標", "開啟", "有切換來源的通知開啟次數 ÷ 異常提醒開啟次數",
     "NOTIFY_03 的不重複 notify_session_id", "NOTIFY_01\nnotify_tab = abnormal_alert 的不重複 notify_session_id", "同一次開啟切換多次只算 1 次", "to_source",
     ">50%：護理師依設備決定處理順序，維持設計\n<50%：可以弱化或移除來源篩選，把空間留給警報", "NOTIFY_01, NOTIFY_03", "否",
     "報告的口徑是「切換次數 ÷ 開啟次數」，可能超過 100%；改成以開啟次數去重"),
    ("N1-05", "護理師", "01 發現異常／Q2", "通知內「前往列表」快捷入口點擊率", "主指標", "開啟", "有點擊快捷入口的通知開啟次數 ÷ 異常提醒開啟次數；另計各列表的點擊分布、空列表點擊佔比",
     "NOTIFY_04 的不重複 notify_session_id\n空列表：target_list_count = 0", "NOTIFY_01\nnotify_tab = abnormal_alert", "同一次開啟只算 1 次；分布以點擊次數計", "target_list",
     ">50%：保留入口，依分布調整按鈕配置；有空列表點擊時，區分有／無警報的按鈕狀態\n<50%：弱化入口，擴大警報顯示空間", "NOTIFY_01, NOTIFY_04", "否", "同上"),
    "護理師｜01 發現異常｜Q3 異常警報是否有效引導點擊進入詳情？",
    ("N1-06", "護理師", "01 發現異常／Q3", "警報介入率", "主指標", "警報事件", "有進入個案詳情的警報事件數 ÷ 期間內產生的警報事件數；另計「曝光後介入率」＝介入數 ÷ N1-01 分子",
     "DETAIL_01\nalert_event_id ∈ 分母\nentry_source ∈ notification_alert, alert_list\n進入時間早於 alert_resolved", "SYS_01",
     "同一警報事件多次進入只算 1 次", "entry_source",
     "＝100%：流程沒有斷點\n<100% 且曝光＝100%：看到了沒點進去，需了解原因\n曝光 <100%：先優化曝光", "SYS_01, DETAIL_01, NOTIFY_05, LIST_03", "是",
     "新增「曝光後介入率」，才能把漏斗斷點拆成「沒看到」和「看到沒點」兩段。" + TBC + "從其他入口（如個案列表）進入是否也算介入？"),
    "護理師｜02 排查異常｜Q1 排查異常時主要看哪些健康資訊？",
    ("N2-01", "護理師", "02 排查異常／Q1", "單一頁籤有效查看率", "主指標", "詳情訪問", "有效查看該頁籤的詳情訪問數 ÷ 個案有待處理異常、且該頁籤有資料的詳情訪問數",
     "DETAIL_02\ntab_name = health_plan / care_records / patient_reports\ndwell_seconds ≥ 5 且 has_data = true", "DETAIL_01\nhas_pending_alert = true\ntab_name ∈ tabs_with_data",
     "同一次訪問重複進入同一頁籤，只要有一次 ≥5 秒就算", "tab_name, alert_level",
     "<20%：訪談了解原因，評估是否整合資訊\n20–60%：符合現有層級\n>60%：考慮提高資訊層級", "DETAIL_01, DETAIL_02", "否",
     "分母加上「該頁籤有資料」的條件（Review C5）。" + TBC + "頁籤完整清單"),
    ("N2-02", "護理師", "02 排查異常／Q1", "待辦資訊再次查看率", "主指標", "詳情訪問", "有手動再次開啟待辦彈窗的詳情訪問數 ÷ 有自動跳出待辦彈窗的詳情訪問數",
     "DETAIL_03\nopen_type = manual", "DETAIL_03\nopen_type = auto", "同一次訪問多次手動開啟只算 1 次；另看 todo_types 分布", "todo_types",
     ">30%：保留固定區塊\n<30%：初次彈窗已經足夠，可以收合到其他頁籤", "DETAIL_03, DETAIL_04", "否",
     "報告分母是「進入個案詳情的人數」，改成「有自動跳出待辦的訪問」。" + TBC + "報告寫的「不重複人數」是指護理師還是個案？"),
    "護理師｜02 排查異常｜Q2 哪些行為影響排查與取得資訊的效率？",
    ("N2-03", "護理師", "02 排查異常／Q2", "檢測儀數據來源切換率（Home／Pro）", "主指標", "人", "有切換來源的不重複使用者數 ÷ 進入檢測儀頁籤 ≥5 秒、且機構同時有 Home 和 Pro 的不重複使用者數",
     "DETAIL_05", "DETAIL_02\ntab_group = vital_sign 且 dwell_seconds ≥ 5\n機構出貨設備同時含 Home、Pro（後端機構主檔）", "以 user_id 去重", "metric, from_source → to_source",
     "<20%：可以移除\n21–60%：保留，但改成下拉選單\n>60%：維持現有設計", "DETAIL_02, DETAIL_05", "是：機構出貨設備", "—"),
    ("N2-04", "護理師", "02 排查異常／Q2", "日期時間範圍切換率", "主指標", "詳情訪問", "有切換時間範圍的詳情訪問數 ÷ 詳情訪問數；另計各選項佔全部切換次數的比例",
     "DETAIL_06", "DETAIL_01", "同一次訪問只算 1 次；佔比以次數計", "range_option, metric",
     "某選項 >60%：預設區間（近 30 天）可能不符需求\n20–60%：維持\n<20%：可以拿掉快捷選項，只保留日期選擇器", "DETAIL_01, DETAIL_06", "否",
     "報告是「次數 ÷ 不重複人數」，單位不一致；改成以詳情訪問為單位"),
    ("N2-05", "護理師／醫師", "02 排查異常／Q2", "心電資訊區塊有效曝光率", "輔助判讀", "秒", "各區塊有效停留秒數總和 ÷ 心電頁籤停留秒數總和",
     "DETAIL_07\nvisible_seconds（單次 ≥3 秒才計）", "DETAIL_02\ntab_name = vital_ecg 的 dwell_seconds", "區塊可能同時可見，各區塊比例加總可能 >100%", "block_name, lead, role",
     "比例高：訪談確認該資訊的作用\n比例低：先排除位置、捲動距離、沒有資料等因素", "DETAIL_02, DETAIL_07", "否",
     TBC + "測量方式：報告用滑鼠停留，建議改成可視範圍停留（Review C6）"),
    ("N2-06", "護理師／醫師", "02 排查異常／Q2", "心電紀錄篩選使用率", "主指標", "人", "有套用篩選的不重複使用者數 ÷ 進入心電頁籤的不重複使用者數",
     "DETAIL_08", "DETAIL_02\ntab_name = vital_ecg", "以 user_id 去重；另看 filter_type 分布", "filter_type, role",
     ">30%：維持\n<30%：收合成「進階搜尋」", "DETAIL_02, DETAIL_08", "否", "分母從「進入個案詳情」改成「進入心電頁籤」；分子從點擊次數改成人數"),
    "護理師｜03 完成異常處置｜Q1 是否所有異常都有被處理？卡在哪個環節？",
    ("N3-01", "護理師", "03 處置／Q1", "護理師處理閉環完成率", "主指標", "警報事件", "觀察窗內被消除的警報事件數 ÷ 已滿觀察窗的警報事件數",
     "alert_resolved（SYS_02）\nresolved_at − created_at ≤ 觀察窗", "SYS_01\ncreated_at ≤ 統計截止 − 觀察窗", "以 alert_event_id 去重", "resolve_type（care_record / referral）, alert_level, org_id",
     "＝100%：接著看時長\n<100%：依序檢查曝光率 → 介入率 → 發起率 → 提交率", "SYS_01, SYS_02", "是",
     TBC + "觀察窗建議 7 天（Review C8）"),
    ("N3-02", "護理師", "03 處置／Q1", "照護記錄填寫發起率", "主指標", "警報事件", "有打開照護記錄的警報事件數 ÷ 有進入個案詳情的警報事件數",
     "FORM_01\nform_type = care_record", "DETAIL_01（帶 alert_event_id）", "同一警報事件多次開啟只算 1 次", "alert_level",
     ">80%：入口清楚\n<80%：訪談是否不清楚處理機制，或按鈕引導不足", "DETAIL_01, FORM_01", "否", "報告是「點擊次數 ÷ 人數」；改成兩邊都以警報事件為單位"),
    ("N3-03", "護理師", "03 處置／Q1", "轉診醫師填寫發起率", "主指標", "警報事件", "有打開轉診醫師表單的警報事件數 ÷ 有進入個案詳情的警報事件數",
     "FORM_01\nform_type = referral", "DETAIL_01（帶 alert_event_id）", "同上", "alert_level",
     "<5%：了解沒有用轉診的原因，先加強宣導再觀察", "DETAIL_01, FORM_01", "否", "報告觸發時機誤寫為「點擊醫師建議」，已更正"),
    ("N3-04", "護理師", "03 處置／Q1", "照護記錄／轉診醫師填寫提交率", "主指標", "警報事件", "有提交成功的警報事件數 ÷ 有打開表單的警報事件數（依 form_type 分開算）",
     "FORM_03\nresult = success", "FORM_01", "同一警報事件、同一 form_type 只算 1 次", "form_type",
     ">90%：符合預期\n<80%：看彈窗停留時長、中途關閉率", "FORM_01, FORM_03", "否", "與報告「整體提交成功率」口徑相同，見 N3-14"),
    "護理師｜03 完成異常處置｜Q2 從發現到完成要多久？哪個環節最久？",
    ("N3-05", "護理師", "03 處置／Q2", "警報處理閉環時長", "主指標", "分鐘", "alert_resolved 時間 − alert_created 時間",
     "SYS_02.resolved_at", "SYS_01.created_at", "以 alert_event_id 為單位；只算觀察窗內有消除的警報", "alert_level, resolve_type, org_id",
     "中位數 <24 小時：符合預期\n>48 小時：拆開下面三段，找出最久的環節", "SYS_01, SYS_02", "是", "統計量統一為中位數、P75、P90，平均數只當參考（Review C9）"),
    ("N3-06", "護理師", "03 處置／Q2", "警報介入時長", "輔助判讀", "分鐘", "第一次進入個案詳情的時間 − alert_created 時間",
     "該 alert_event_id 第一筆 DETAIL_01", "SYS_01.created_at", "只取第一次進入", "entry_source",
     "閉環 >24 小時且介入時長佔 >50%：問題在提醒與入口，不在處理本身", "SYS_01, DETAIL_01", "是", "—"),
    ("N3-07", "護理師", "03 處置／Q2", "異常排查時長", "輔助判讀", "秒", "第一次打開表單的時間 − 同一次詳情訪問的進入時間",
     "同 detail_visit_id 的第一筆 FORM_01", "DETAIL_01", "以 detail_visit_id 為單位；沒有打開表單的訪問不計", "form_type",
     "<3 分鐘：符合預期\n>5 分鐘：搭配頁籤查看率，優化資訊取得", "DETAIL_01, FORM_01", "否", "—"),
    ("N3-08", "護理師", "03 處置／Q2", "照護記錄／轉診醫師填寫時長", "輔助判讀", "秒", "提交成功時間 − 該次表單打開時間",
     "FORM_03（success）", "同 form_open_id 的 FORM_01", "以 form_open_id 為單位", "form_type",
     "<30 秒：符合預期\n>90 秒：填寫負擔重，考慮優化填寫方式", "FORM_01, FORM_03", "否", "補上門檻單位；修正假設 B 的指標名稱誤植"),
    "護理師｜03 完成異常處置｜Q3 哪些行為影響處理完成？（適用 form_type = care_record / referral）",
    ("N3-09", "護理師", "03 處置／Q3", "首次打開直接提交率", "主指標", "開啟", "第一次打開就提交成功的次數 ÷ 第一次打開的次數",
     "首次開啟（同一 alert_event_id＋form_type 的第一筆 FORM_01）且同 form_open_id 有 FORM_03 success", "首次開啟的 FORM_01", "open_seq 由分析端依時間排序計算", "form_type, alert_level",
     ">80%：彈窗資訊足夠\n<60%：看 N3-10～N3-12，判斷是需要查資料還是暫時不想處理", "FORM_01, FORM_03", "否", "—"),
    ("N3-10", "護理師", "03 處置／Q3", "中途關閉率", "輔助判讀", "開啟", "取消或關閉的次數 ÷ 表單打開次數", "FORM_02", "FORM_01", "以 form_open_id 計", "form_type, close_method, has_input",
     ">40% 時搭配復開率判讀", "FORM_01, FORM_02", "否", "報告轉診醫師版本的分母誤寫為「照護記錄」，已更正"),
    ("N3-11", "護理師", "03 處置／Q3", "關閉後復開率", "輔助判讀", "警報事件", "中途關閉後又重新打開的警報事件數 ÷ 有中途關閉的警報事件數",
     "有 FORM_02 且之後同 alert_event_id＋form_type 又有 FORM_01", "有 FORM_02 的 alert_event_id", "依 form_type 分開", "form_type",
     "關閉 >40% 且復開 >80%、復開後提交 >90%：需要查資料再回來填，考慮在彈窗補參考資料\n關閉 >40% 且復開 <20%：內容不符預期或暫不處理", "FORM_01, FORM_02", "否", "—"),
    ("N3-12", "護理師", "03 處置／Q3", "復開後成功提交率", "輔助判讀", "開啟", "復開（open_seq ≥2）後提交成功的次數 ÷ 復開次數", "open_seq ≥ 2 的 FORM_01，同 form_open_id 有 FORM_03 success", "open_seq ≥ 2 的 FORM_01", "以 form_open_id 計", "form_type", "同上", "FORM_01, FORM_03", "否", "—"),
    ("N3-13", "護理師", "03 處置／Q3", "表單空提交率", "主指標", "提交", "所有欄位都空白的成功提交數 ÷ 成功提交數", "FORM_03\nresult = success 且 is_empty = true", "FORM_03\nresult = success", "以提交次數計", "form_type, alert_level",
     ">40%：非必填策略成立，可以考慮在外層加快速處理\n<10% 且平均 >80 字：有填寫習慣，保留填寫流程\n低風險 >50%、高風險 <10%：依風險等級設計不同的處理機制", "FORM_03", "否", "—"),
    ("N3-14", "護理師", "03 處置／Q3", "提交字數分布", "輔助判讀", "字", "主文字欄位字數的中位數、P25、P75、P90（平均數只當參考）", "FORM_03\nresult = success 且 text_length > 0", "—", "排除空白提交", "form_type, alert_level",
     "平均 <20 字：沒有負擔\n平均 >50 字且 P50 >50：提供範本功能\nP75 <50：只是少數極端值", "FORM_03", "否",
     "報告另有「整體提交成功率」，與 N3-04 口徑相同，建議合併（Review C4）"),
    "醫師｜01 接收轉診｜Q1 轉診是否有效被醫師看到？",
    ("D1-01", "醫師", "01 接收轉診／Q1", "轉診曝光率（整體）", "主指標", "轉診", "至少被曝光 1 次的轉診數 ÷ 期間內產生的轉診數",
     "NOTIFY_02 或 LIST_02\nitem_type = referral\n曝光時間早於 referral_resolved", "referral_created（SYS_03）", "跨入口只算 1 次；只計 role = doctor", "doctor_user_id",
     "＝100%：維持\n<100%：看醫師的平台活躍度；每週使用 <1 次的醫師，考慮加簡訊、Email 通知", "SYS_03, NOTIFY_02, LIST_02", "是", "—"),
    ("D1-02", "醫師", "01 接收轉診／Q1", "轉診提醒通知曝光率", "主指標", "轉診", "在通知彈窗被曝光的轉診數 ÷ 期間內產生的轉診數", "NOTIFY_02\nlist_name = notification_referral", "SYS_03", "同入口只算 1 次", "—",
     ">50%：醫師習慣從鈴鐺接收\n<50%：看整體曝光，整體 >80% 表示醫師習慣主動去列表看", "SYS_03, NOTIFY_02", "是", "—"),
    ("D1-03", "醫師", "01 接收轉診／Q1", "待醫師處理列表曝光率", "主指標", "轉診", "在待醫師處理列表被曝光的轉診數 ÷ 期間內產生的轉診數", "LIST_02\nlist_type = doctor_pending", "SYS_03", "同入口只算 1 次；載入、捲動、翻頁都計", "—",
     ">20%：仍有醫師主動去列表看\n<20%：了解是否不知道有這個列表", "SYS_03, LIST_01, LIST_02", "是", "—"),
    "醫師｜01 接收轉診｜Q2 轉診是否有效引導進入詳情？",
    ("D1-04", "醫師", "01 接收轉診／Q2", "轉診介入率", "主指標", "轉診", "有進入個案詳情的轉診數 ÷ 期間內產生的轉診數；另計曝光後介入率",
     "DETAIL_01\nreferral_id ∈ 分母\nentry_source ∈ notification_referral, doctor_pending_list", "SYS_03", "同一轉診多次進入只算 1 次", "entry_source",
     "同 N1-06", "SYS_03, DETAIL_01", "是", "報告假設段落寫成「警報介入率」「護理師」，應為轉診、醫師"),
    "醫師｜02 評估病情｜Q1 提出處置建議前主要看哪些資訊？",
    ("D2-01", "醫師", "02 評估病情／Q1", "待辦資訊再次查看率（醫師）", "主指標", "詳情訪問", "同 N2-02，role = doctor", "DETAIL_03 open_type = manual", "DETAIL_03 open_type = auto", "同 N2-02", "todo_types",
     ">30%：保留固定區塊\n<30%：可以收合", "DETAIL_03", "否", "與 N2-02 共用定義"),
    ("D2-02", "醫師", "02 評估病情／Q1", "生理體徵待處理異常資訊查看率", "主指標", "詳情訪問", "有查看待處理異常生理體徵頁籤 ≥3 秒的詳情訪問數 ÷ 醫師進入、且個案有待處理轉診的詳情訪問數",
     "DETAIL_02\ntab_group = vital_sign\nis_pending_abnormal = true\ndwell_seconds ≥ 3", "DETAIL_01\nrole = doctor\nhas_pending_referral = true", "同一次訪問只算 1 次", "metric",
     "<50%：醫師多半靠護理師轉述，考慮在醫師建議彈窗中直接顯示異常數據\n>50%：維持，接著看排查時長", "DETAIL_01, DETAIL_02", "否",
     TBC + "醫師端的「待處理異常」指的是「有待處理轉診」，還是「有未消除的警報」？"),
    ("D2-03", "醫師", "02 評估病情／Q1", "歷史處理紀錄查看率", "主指標", "詳情訪問", "有查看處理紀錄詳情 ≥5 秒的詳情訪問數 ÷ 醫師進入、且個案有歷史處理紀錄的詳情訪問數；另看查看紀錄是在寫建議之前還是之後",
     "DETAIL_10\ndwell_seconds ≥ 5", "DETAIL_01\nrole = doctor\ncare_records ∈ tabs_with_data", "同一次訪問只算 1 次", "record_rank",
     "<30%：維持\n>30%：考慮在醫師建議彈窗提供近期紀錄摘要", "DETAIL_01, DETAIL_09, DETAIL_10, FORM_01", "否", "報告是「不重複人數 ÷ 不重複人數」，改成以詳情訪問為單位，才能分析與寫建議的先後順序"),
    ("D2-04", "醫師", "02 評估病情／Q2", "心電區塊有效曝光率、心電紀錄篩選使用率", "—", "—", "同 N2-05、N2-06，role = doctor", "", "", "", "", "", "DETAIL_07, DETAIL_08", "否", "與護理師共用定義"),
    "醫師｜03 完成轉診處置｜Q1 轉診是否都有被處理？卡在哪個環節？",
    ("D3-01", "醫師", "03 處置／Q1", "轉診處理閉環完成率", "主指標", "轉診", "觀察窗內處理完成的轉診數 ÷ 已滿觀察窗的轉診數", "referral_resolved（SYS_04）", "SYS_03", "以 referral_id 去重", "doctor_user_id, org_id",
     "<100%：依序檢查曝光 → 介入 → 發起 → 提交", "SYS_03, SYS_04", "是", TBC + "觀察窗"),
    ("D3-02", "醫師", "03 處置／Q1", "醫師建議填寫發起率", "主指標", "轉診", "有打開醫師建議的轉診數 ÷ 有進入個案詳情的轉診數", "FORM_01\nform_type = doctor_advice", "DETAIL_01（帶 referral_id）", "同一轉診只算 1 次", "—",
     ">80%：入口清楚\n<80%：訪談處理機制或按鈕引導", "DETAIL_01, FORM_01", "否", "—"),
    ("D3-03", "醫師", "03 處置／Q1", "醫師建議填寫提交率", "主指標", "轉診", "有提交成功的轉診數 ÷ 有打開醫師建議的轉診數", "FORM_03\nform_type = doctor_advice\nresult = success", "FORM_01\nform_type = doctor_advice", "同一轉診只算 1 次", "—",
     ">90%：符合預期\n<80%：看彈窗停留時長", "FORM_01, FORM_03", "否", "報告觸發時機誤寫為「點擊醫師建議／進入個案詳情」，已更正"),
    "醫師｜03 完成轉診處置｜Q2 從接到轉診到完成要多久？",
    ("D3-04", "醫師", "03 處置／Q2", "轉診處理閉環時長", "主指標", "分鐘", "referral_resolved 時間 − referral_created 時間", "SYS_04", "SYS_03", "以 referral_id 為單位", "doctor_user_id",
     "<24 小時：符合預期\n>48 小時：拆開下面三段", "SYS_03, SYS_04", "是", "報告觸發時機誤寫為「撰寫照護記錄」，已更正"),
    ("D3-05", "醫師", "03 處置／Q2", "轉診介入時長／異常排查時長／醫師建議填寫時長", "輔助判讀", "分鐘／秒", "同 N3-06～N3-08，用 referral_id、form_type = doctor_advice 計算", "", "", "", "", "同 N3-06～N3-08", "SYS_03, DETAIL_01, FORM_01, FORM_03", "是", "與護理師共用定義"),
    "醫師｜03 完成轉診處置｜Q3 哪些行為影響完成？",
    ("D3-06", "醫師", "03 處置／Q3", "醫師建議：首次打開直接提交率、中途關閉率、復開率、復開後提交率、空提交率、字數分布", "—", "—", "同 N3-09～N3-14，form_type = doctor_advice，串接鍵用 referral_id", "", "", "", "", "同 N3-09～N3-14", "FORM_01, FORM_02, FORM_03", "否", "報告空提交率的分母誤寫為「照護記錄」，已更正"),
]
sheet("3_指標對照", H_M, M, [8, 9, 14, 24, 9, 9, 34, 34, 30, 30, 18, 40, 20, 10, 40])

# ---------------------------------------------------------------- 4 事件清單
H_E = ["事件編號", "模組", "頁面／區塊", "事件名稱", "中文說明", "觸發端", "觸發時機", "不觸發／排除條件", "去重／頻率",
       "事件屬性（定義見 5_屬性字典）", "對應指標", "適用角色", "優先級", "埋點狀態", "驗收方式", "備註／待確認"]
E = [
    "GLOBAL｜全域屬性",
    ("GLOBAL_01", "全域", "所有事件", "（所有事件）", "每筆事件都要帶的屬性", "前端", "每筆事件送出時", "—", "—",
     "user_id, role, org_id, session_id, page_name, client_time, platform_version, browser, viewport_width, viewport_height", "全部", "全部", "P0", "規劃中",
     "任選 3 個事件，檢查全域屬性都有值、時間帶 +08:00",
     "role 以「當下登入身分」為準；多機構帳號的 org_id 以當下所選機構為準。場域類型（日照、居家、HaH、遠距中心）由後端機構主檔依 org_id 對應，不另外埋。" + TBC + "role 的完整列舉值"),
    "SYS｜後端事件（也可以用資料表提供，見 6_後端資料需求）",
    ("SYS_01", "後端", "警報", "alert_created", "警報事件產生", "後端", "規則引擎判定異常、正式產生警報事件時（伺服器時間）", "同一個案已有未處理的警報事件時，不產生新事件，只把新警報項目併入", "每個 alert_event_id 一筆",
     "alert_event_id, patient_id, org_id, alert_level, alert_items, device_source, created_at", "N1-01～N1-06, N3-01, N3-05, N3-06", "—", "P0", "規劃中", "觸發一筆測試異常 → 後端記錄 1 筆，alert_event_id 唯一",
     TBC + "alert_event_id 與 Figma 提到的「任務 id」是不是同一個東西？若不是，兩者是什麼關係？"),
    ("SYS_02", "後端", "警報", "alert_resolved", "警報事件消除", "後端", "照護記錄或轉診醫師提交成功、警報被消除時", "—", "每個 alert_event_id 一筆",
     "alert_event_id, patient_id, resolve_type, resolved_by_user_id, resolved_at", "N1-01, N1-06, N3-01, N3-05", "—", "P0", "規劃中", "提交照護記錄 → 該警報事件出現 1 筆消除紀錄",
     TBC + "轉診醫師提交後，警報是否立即消除？報告把它算進護理師的閉環"),
    ("SYS_03", "後端", "轉診", "referral_created", "轉診產生", "後端", "護理師轉診醫師提交成功、後端產生轉診紀錄時", "—", "每個 referral_id 一筆",
     "referral_id, alert_event_id, patient_id, referrer_user_id, doctor_user_id, created_at", "D1-01～D1-04, D3-01, D3-04", "—", "P0", "規劃中", "送出轉診 → 後端 1 筆", ""),
    ("SYS_04", "後端", "轉診", "referral_resolved", "轉診處理完成", "後端", "醫師建議提交成功、轉診被標記為已處理時", "—", "每個 referral_id 一筆",
     "referral_id, resolved_by_user_id, resolved_at", "D3-01, D3-04", "—", "P0", "規劃中", "醫師提交建議 → 後端 1 筆", ""),
    "NOTIFY｜消息通知（小鈴鐺）",
    ("NOTIFY_01", "消息通知", "頂部小鈴鐺／最新通知彈窗", "view_popup", "打開通知彈窗、切換通知分頁", "前端", "點擊鈴鐺、彈窗顯示完成時；在彈窗內切換「異常提醒／轉診提醒」分頁時也送一筆", "—", "每次打開產生新的 notify_session_id；切換分頁沿用",
     "popup_name, notify_session_id, notify_tab, unread_count", "N1-04, N1-05", "全部", "P0", "規劃中", "點鈴鐺 → 1 筆 popup_name=notification_center；切分頁 → 再 1 筆，notify_session_id 相同",
     TBC + "彈窗打開時預設停在哪個分頁？"),
    ("NOTIFY_02", "消息通知", "最新通知彈窗／通知卡片", "item_impression", "通知卡片曝光", "前端", "通知卡片 ≥50% 進入可視範圍時；打開彈窗時首屏可見的卡片馬上計算，之後捲入的卡片再追加", "彈窗在背景分頁時不計", "同一 notify_session_id 內同一項目只送一次；500ms 內的新曝光合併成一筆，用 Array 送出",
     "list_name, notify_session_id, item_type, item_ids, patient_ids, source_filter", "N1-01, N1-02, D1-01, D1-02", "全部", "P0", "規劃中", "打開彈窗、首屏 5 張 → 1 筆 item_ids 長度 5；往下捲 3 張 → 再 1 筆長度 3；往回捲不再送",
     "item_ids 依 item_type 放 alert_event_id 或 referral_id。" + TBC + "曝光要不要加停留門檻（例如 ≥500ms）？"),
    ("NOTIFY_03", "消息通知", "最新通知彈窗／來源篩選", "click_button", "切換通知來源", "前端", "點擊來源篩選（全部／CoDoctor 檢測儀／CoDoctor Watch）、列表更新後", "點擊目前已選的來源時不送", "每次切換送一筆",
     "button_name, notify_session_id, from_source, to_source", "N1-04", "全部", "P1", "規劃中", "點「CoDoctor Watch」→ button_name=alert_source_filter, to_source=watch", ""),
    ("NOTIFY_04", "消息通知", "最新通知彈窗／前往列表", "click_button", "點擊「前往 XX 列表」快捷入口", "前端", "點擊「前往高風險／異常上報／自訂計畫未測量／低風險列表」的當下", "—", "每次點擊送一筆",
     "button_name, notify_session_id, target_list, target_list_count", "N1-05", "護理師", "P1", "規劃中", "點「前往高風險列表」→ button_name=goto_list, target_list=high_risk, target_list_count=當下數字", "target_list_count 用來判斷是否點到空列表"),
    ("NOTIFY_05", "消息通知", "最新通知彈窗／通知卡片", "click_button", "點擊通知卡片進入個案詳情", "前端", "點擊通知卡片的當下", "—", "每次點擊送一筆",
     "button_name, notify_session_id, item_type, alert_event_id, referral_id, patient_id, card_position", "N1-06, D1-04", "全部", "P1", "規劃中", "點第 2 張卡片 → card_position=2，接著收到 DETAIL_01 entry_source=notification_alert", "介入率以 DETAIL_01 計算；本事件用於確認點擊位置與點擊後是否成功進入詳情"),
    "LIST｜待處理列表",
    ("LIST_01", "待處理列表", "待處理警報列表／待醫師處理列表", "view_page", "進入待處理列表", "前端", "列表資料載入完成時；切換列表分頁時也送一筆", "—", "每次進入送一筆",
     "page_name, list_view_id, list_type, list_total_count, entry_source", "N1-03, D1-03", "全部", "P1", "規劃中", "從選單進高風險列表 → list_type=high_risk, entry_source=nav_menu", TBC + "列表分頁完整清單；自訂計畫未測量列表是否納入曝光計算"),
    ("LIST_02", "待處理列表", "待處理列表／列表項目", "item_impression", "列表項目曝光", "前端", "列表項目 ≥50% 進入可視範圍時（含載入、捲動、翻頁）", "—", "同一次列表瀏覽（list_view_id）內同一項目只送一次；500ms 合併",
     "list_name, list_view_id, item_type, item_ids, patient_ids", "N1-01, N1-03, D1-01, D1-03", "全部", "P0", "規劃中", "載入首屏 10 列 → 1 筆長度 10；翻到第 2 頁 → 再 1 筆", "list_name 的值與 list_type 相同"),
    ("LIST_03", "待處理列表", "待處理列表／列表項目", "click_button", "點擊列表項目進入個案詳情", "前端", "點擊列表列或「查看」按鈕的當下", "—", "每次點擊送一筆",
     "button_name, list_view_id, list_type, item_type, alert_event_id, referral_id, patient_id, row_position, page_index", "N1-06, D1-04", "全部", "P1", "規劃中", "點第 3 列 → row_position=3", ""),
    "DETAIL｜個案詳情",
    ("DETAIL_01", "個案詳情", "個案詳情", "view_page", "進入個案詳情", "前端", "個案詳情頁資料載入完成時", "同一頁重新整理時產生新的 detail_visit_id，但 entry_source=reload", "每次進入產生新的 detail_visit_id",
     "page_name, detail_visit_id, patient_id, entry_source, alert_event_id, referral_id, has_pending_alert, pending_alert_items, has_pending_referral, tabs_with_data, has_todo, default_tab",
     "N1-06, N2-01～N2-04, N3-02, N3-03, N3-06, N3-07, D1-04, D2-02, D2-03, D3-02", "全部", "P0", "規劃中", "從通知卡片進入 → entry_source=notification_alert，alert_event_id 有值",
     "alert_event_id、referral_id 是個案「當下」未處理的事件，不管從哪個入口進來都要帶，否則從個案列表進入的處理會漏算"),
    ("DETAIL_02", "個案詳情", "個案詳情／頁籤", "leave_tab", "離開頁籤（帶停留秒數）", "前端", "切換到其他頁籤、離開詳情頁、或瀏覽器頁面隱藏時", "停留 <1 秒不送（快速切過）", "每次離開送一筆",
     "detail_visit_id, patient_id, tab_group, tab_name, metric, has_data, is_pending_abnormal, dwell_seconds, leave_reason", "N2-01, N2-03, N2-05, N2-06, D2-02", "全部", "P0", "規劃中", "在「處理紀錄」停 8 秒後切到「健康計畫」→ 1 筆 tab_name=care_records, dwell_seconds=8",
     TBC + "頁籤完整清單（資訊類＋生理體徵類）與代碼"),
    ("DETAIL_03", "個案詳情", "個案詳情／待辦事項彈窗", "view_popup", "待辦事項彈窗顯示", "前端", "進入詳情自動跳出，或點擊「全部內容」再次開啟、彈窗顯示完成時", "—", "每次顯示送一筆",
     "popup_name, detail_visit_id, patient_id, open_type, open_seq, todo_types", "N2-02, D2-01", "全部", "P1", "規劃中", "進入詳情 → open_type=auto；關掉再點「全部內容」→ open_type=manual, open_seq=2", ""),
    ("DETAIL_04", "個案詳情", "個案詳情／待辦事項彈窗", "close_popup", "待辦事項彈窗關閉", "前端", "點擊關閉、或點擊彈窗外部關閉時", "—", "每次關閉送一筆",
     "popup_name, detail_visit_id, open_type, open_seq, dwell_seconds", "N2-02, D2-01", "全部", "P2", "規劃中", "開 6 秒後關閉 → dwell_seconds=6", ""),
    ("DETAIL_05", "個案詳情", "個案詳情／檢測儀頁籤／數據來源", "click_button", "切換檢測儀數據來源（Home／Pro）", "前端", "點擊 Home／Pro、圖表更新後", "點擊目前已選的來源時不送", "每次切換送一筆",
     "button_name, detail_visit_id, patient_id, metric, from_source, to_source", "N2-03", "全部", "P1", "規劃中", "血壓頁從 Home 切到 Pro → from_source=home, to_source=pro", "機構出貨的設備（Pro／Home／Watch）由後端機構主檔取得，不另外埋"),
    ("DETAIL_06", "個案詳情", "個案詳情／時間範圍篩選", "click_button", "切換時間範圍", "前端", "點擊今日／近 7 天／近 30 天／近 1 年，或在自訂日期選擇器按下確認、圖表更新後", "點擊目前已選的選項時不送", "每次套用送一筆",
     "button_name, detail_visit_id, metric, range_option, custom_range_days", "N2-04", "全部", "P1", "規劃中", "點「近 7 天」→ range_option=last_7d", "預設為近 30 天"),
    ("DETAIL_07", "個案詳情", "個案詳情／心電頁籤／各區塊", "view_block", "心電各區塊的可視停留", "前端", "離開心電頁籤時，一次送出本次各區塊的累計可視秒數", "單一區塊累計 <3 秒不送", "每次離開心電頁籤送一筆（區塊用 Array）",
     "detail_visit_id, lead, block_names, block_visible_seconds, measure_method", "N2-05", "全部", "P2", "規劃中", "停在心電頁 20 秒、只看到上半部 → block_names 只含上半部區塊",
     TBC + "區塊清單與代碼；測量方式要用可視範圍還是滑鼠停留（Review C6）"),
    ("DETAIL_08", "個案詳情", "個案詳情／心電頁籤／紀錄篩選", "apply_filter", "套用心電紀錄篩選", "前端", "套用導程或異常條件、心電紀錄列表更新後", "條件沒有變動時不送", "每次套用送一筆",
     "detail_visit_id, filter_type, filter_value, result_count", "N2-06", "全部", "P1", "規劃中", "選導程 II → filter_type=lead, filter_value=II", TBC + "導程與異常篩選的完整值域"),
    ("DETAIL_09", "個案詳情", "個案詳情／處理紀錄頁籤／紀錄詳情", "view_popup", "打開處理紀錄詳情", "前端", "點擊單筆處理紀錄、詳情顯示完成時", "—", "每次打開送一筆；產生 popup_open_id",
     "popup_name, popup_open_id, detail_visit_id, patient_id, record_rank, record_type, record_created_at", "D2-03", "全部", "P1", "規劃中", "點最新一筆 → record_rank=1", ""),
    ("DETAIL_10", "個案詳情", "個案詳情／處理紀錄頁籤／紀錄詳情", "close_popup", "關閉處理紀錄詳情", "前端", "關閉處理紀錄詳情時", "—", "每次關閉送一筆",
     "popup_name, popup_open_id, detail_visit_id, dwell_seconds", "D2-03", "全部", "P1", "規劃中", "開 7 秒後關閉 → dwell_seconds=7", "有效查看門檻 ≥5 秒由分析端判斷"),
    "FORM｜處置表單（照護記錄／轉診醫師／醫師建議）",
    ("FORM_01", "處置表單", "個案詳情／左側處置按鈕／表單彈窗", "view_popup", "處置表單彈窗顯示", "前端", "點擊「撰寫照護記錄」「轉診醫師」「醫師建議」後，彈窗顯示完成時", "—", "每次打開產生新的 form_open_id",
     "popup_name, form_type, form_open_id, detail_visit_id, patient_id, alert_event_id, referral_id", "N3-02～N3-04, N3-07～N3-12, D2-03, D3-02, D3-03, D3-05, D3-06", "全部", "P0", "規劃中",
     "點「撰寫照護記錄」→ popup_name=handle_form, form_type=care_record，alert_event_id 有值",
     "open_seq（第幾次打開）由分析端依同一 alert_event_id／referral_id＋form_type 的時間順序計算，前端不需要累計（重新整理會歸零，不可靠）"),
    ("FORM_02", "處置表單", "表單彈窗", "close_popup", "表單中途關閉", "前端", "點擊「取消」、右上角關閉、或點擊遮罩關閉時", "提交成功後自動關閉不送", "每次關閉送一筆",
     "popup_name, form_type, form_open_id, close_method, has_input, dwell_seconds", "N3-10, N3-11, D3-06", "全部", "P0", "規劃中", "打開後輸入文字再按取消 → close_method=cancel, has_input=true", ""),
    ("FORM_03", "處置表單", "表單彈窗／完成處理", "submit_form", "表單提交結果", "前端（API 回傳後）", "點擊「完成處理」、API 回傳結果時（成功或失敗都送）", "前端欄位檢核沒通過、沒有呼叫 API 時不送", "每次 API 回傳送一筆",
     "form_type, form_open_id, result, error_code, is_empty, filled_field_count, text_length, alert_level, alert_items, dwell_seconds", "N3-04, N3-08, N3-09, N3-12～N3-14, D3-03, D3-05, D3-06", "全部", "P0", "規劃中",
     "空白直接提交 → result=success, is_empty=true, text_length=0", "不送任何文字內容，只送字數。閉環以後端 SYS_02、SYS_04 為準，本事件用來看表單層的行為"),
]


def efill(r):
    return SRV_FILL if r and str(r[0]).startswith("SYS_") else None


ws_e = sheet("4_事件清單", H_E, E, [11, 10, 22, 14, 20, 12, 36, 26, 28, 40, 24, 9, 7, 9, 36, 44], fill_rule=efill)

# ---------------------------------------------------------------- 5 屬性字典
H_P = ["屬性 key", "中文名", "定義", "資料型別", "允許值／格式", "範例", "必填", "空值規則", "範圍", "使用事件", "資料來源", "備註"]
P = [
    "全域屬性",
    ("user_id", "操作者帳號 ID", "目前登入的醫護人員帳號", "String", "平台內部 ID", "u_10293", "是", "—", "全域", "全部", "前端", "不送姓名、Email"),
    ("role", "操作者角色", "當下登入身分", "String", "nurse, case_manager, doctor, admin", "nurse", "是", "—", "全域", "全部", "前端", TBC + "完整角色清單；一個帳號能不能同時有多個角色？"),
    ("org_id", "機構 ID", "當下所選機構", "String", "平台內部 ID", "org_001", "是", "—", "全域", "全部", "前端", "場域類型由後端機構主檔對應"),
    ("session_id", "登入工作階段 ID", "每次登入產生，登出或逾時結束", "String", "UUID v4", "3f1c…", "是", "—", "全域", "全部", "前端", ""),
    ("page_name", "目前頁面", "事件發生時所在頁面", "String", "home, workspace, pending_list, patient_detail, patient_list …", "patient_detail", "是", "—", "全域", "全部", "前端", TBC + "頁面代碼清單"),
    ("client_time", "前端時間", "事件在瀏覽器發生的時間", "Datetime", "ISO 8601 +08:00", "2026-11-04T10:15:30.120+08:00", "是", "—", "全域", "全部", "前端", "計算時長以後端收到時間為準，這個欄位只用來排查"),
    ("platform_version", "平台版本", "前端版本號", "String", "語意化版本", "7.0.3", "是", "—", "全域", "全部", "前端", "判斷數據變化是否跟改版有關"),
    ("browser", "瀏覽器", "瀏覽器名稱與主版本", "String", "chrome_130, edge_130, safari_18 …", "chrome_130", "否", "null", "全域", "全部", "前端", ""),
    ("viewport_width", "視窗寬", "瀏覽器可視寬度（px）", "Integer", "", "1440", "否", "null", "全域", "全部", "前端", ""),
    ("viewport_height", "視窗高", "瀏覽器可視高度（px）", "Integer", "", "900", "否", "null", "全域", "全部", "前端", "心電區塊分析需要（報告提到 900px 的限制）"),
    "業務 ID",
    ("patient_id", "個案 ID", "被查看或處理的個案", "String", "平台內部 ID", "p_88231", "條件：有個案時必填", "null", "事件", "NOTIFY_05, LIST_03, DETAIL_*, FORM_01, SYS_*", "前端／後端", "不送姓名、證號"),
    ("patient_ids", "曝光個案 ID 清單", "本批曝光項目對應的個案，順序與 item_ids 相同", "Array<String>", "", "[\"p_1\",\"p_2\"]", "是", "[]", "事件", "NOTIFY_02, LIST_02", "前端", ""),
    ("alert_event_id", "警報事件 ID", "同一個案在未處理期間的警報合併為一個事件；處理後再發生就是新事件", "String", "後端產生", "ae_5521", "條件：個案有未處理警報時必填", "null", "事件", "SYS_01, SYS_02, SYS_03, NOTIFY_05, LIST_03, DETAIL_01, FORM_01", "後端", TBC + "與「任務 id」的關係"),
    ("referral_id", "轉診 ID", "一筆轉診紀錄", "String", "後端產生", "rf_301", "條件：個案有未處理轉診時必填", "null", "事件", "SYS_03, SYS_04, NOTIFY_05, LIST_03, DETAIL_01, FORM_01", "後端", ""),
    ("item_type", "項目類型", "曝光或點擊的項目是警報還是轉診", "String", "alert, referral", "alert", "是", "—", "事件", "NOTIFY_02, NOTIFY_05, LIST_02, LIST_03", "前端", ""),
    ("item_ids", "曝光項目 ID 清單", "本批曝光的 alert_event_id 或 referral_id", "Array<String>", "", "[\"ae_1\",\"ae_2\"]", "是", "—", "事件", "NOTIFY_02, LIST_02", "前端", ""),
    "流程 ID（前端產生 UUID v4）",
    ("notify_session_id", "通知彈窗開啟 ID", "每次打開通知彈窗產生，關閉時結束", "String", "UUID v4", "", "是", "—", "事件", "NOTIFY_01～05", "前端", ""),
    ("list_view_id", "列表瀏覽 ID", "每次進入或切換待處理列表時產生", "String", "UUID v4", "", "是", "—", "事件", "LIST_01, LIST_02, LIST_03", "前端", ""),
    ("detail_visit_id", "詳情訪問 ID", "每次進入個案詳情時產生，離開時結束", "String", "UUID v4", "", "是", "—", "事件", "DETAIL_*, FORM_01", "前端", ""),
    ("form_open_id", "表單開啟 ID", "每次打開處置表單時產生，用來配對關閉與提交", "String", "UUID v4", "", "是", "—", "事件", "FORM_01～03", "前端", ""),
    ("popup_open_id", "彈窗開啟 ID", "每次打開處理紀錄詳情時產生", "String", "UUID v4", "", "是", "—", "事件", "DETAIL_09, DETAIL_10", "前端", ""),
    "通知與列表",
    ("popup_name", "彈窗名稱", "", "String", "notification_center, todo_popup, care_record_detail, handle_form", "handle_form", "是", "—", "事件", "NOTIFY_01, DETAIL_03/04/09/10, FORM_01/02", "前端", ""),
    ("notify_tab", "通知分頁", "", "String", "abnormal_alert, referral", "abnormal_alert", "是", "—", "事件", "NOTIFY_01", "前端", TBC + "是否還有其他分頁"),
    ("unread_count", "未讀數", "打開當下該分頁的未讀數", "Integer", "", "12", "否", "取不到送 null，不送 0", "事件", "NOTIFY_01", "前端", ""),
    ("list_name", "曝光所在清單", "", "String", "notification_alert, notification_referral, high_risk, abnormal_report, low_risk, custom_plan_unmeasured, doctor_pending", "high_risk", "是", "—", "事件", "NOTIFY_02, LIST_02", "前端", ""),
    ("list_type", "列表類型", "", "String", "high_risk, abnormal_report, low_risk, custom_plan_unmeasured, doctor_pending", "high_risk", "是", "—", "事件", "LIST_01, LIST_03", "前端", TBC + "列表清單"),
    ("list_total_count", "列表總數", "載入當下列表的總項目數", "Integer", "", "37", "是", "—", "事件", "LIST_01", "前端", ""),
    ("source_filter", "目前來源篩選", "曝光當下選的來源", "String", "all, monitor, watch", "all", "是", "—", "事件", "NOTIFY_02", "前端", ""),
    ("from_source", "切換前來源", "通知為 all/monitor/watch；檢測儀為 home/pro", "String", "all, monitor, watch, home, pro", "home", "是", "—", "事件", "NOTIFY_03, DETAIL_05", "前端", "同 key 在兩個事件的值域不同，依事件判讀"),
    ("to_source", "切換後來源", "同上", "String", "同上", "pro", "是", "—", "事件", "NOTIFY_03, DETAIL_05", "前端", ""),
    ("target_list", "前往的列表", "", "String", "high_risk, abnormal_report, custom_plan_unmeasured, low_risk", "high_risk", "是", "—", "事件", "NOTIFY_04", "前端", ""),
    ("target_list_count", "目標列表數量", "點擊當下該列表的項目數", "Integer", "", "0", "是", "—", "事件", "NOTIFY_04", "前端", "0＝空列表"),
    ("card_position", "卡片位置", "從 1 起算", "Integer", "", "2", "是", "—", "事件", "NOTIFY_05", "前端", ""),
    ("row_position", "列表列位置", "在目前頁中的位置，從 1 起算", "Integer", "", "3", "是", "—", "事件", "LIST_03", "前端", ""),
    ("page_index", "列表頁碼", "從 1 起算", "Integer", "", "1", "是", "—", "事件", "LIST_03", "前端", ""),
    ("entry_source", "進入來源", "", "String", "LIST_01：nav_menu, notification_shortcut, workspace\nDETAIL_01：notification_alert, notification_referral, alert_list, doctor_pending_list, patient_list, reload, other", "notification_alert", "是", "—", "事件", "LIST_01, DETAIL_01", "前端", TBC + "所有可以進入個案詳情的入口"),
    ("button_name", "按鈕名稱", "", "String", "alert_source_filter, goto_list, notification_card, list_row, view_detail, monitor_source, time_range", "goto_list", "是", "—", "事件", "所有 click_button", "前端", ""),
    "個案詳情",
    ("has_pending_alert", "有未處理警報", "進入時個案是否有未處理的警報事件", "Boolean", "true, false", "true", "是", "—", "事件", "DETAIL_01", "前端", ""),
    ("pending_alert_items", "未處理警報項目", "", "Array<String>", "metric 代碼", "[\"blood_pressure\",\"ecg\"]", "條件：has_pending_alert=true", "[]", "事件", "DETAIL_01", "前端", ""),
    ("has_pending_referral", "有未處理轉診", "", "Boolean", "true, false", "false", "是", "—", "事件", "DETAIL_01", "前端", ""),
    ("tabs_with_data", "有資料的頁籤", "進入時有資料的頁籤清單", "Array<String>", "tab_name 代碼", "[\"health_plan\",\"care_records\"]", "是", "[]", "事件", "DETAIL_01", "前端", "N2-01、D2-03 的分母條件"),
    ("has_todo", "有待辦", "是否有待辦事項（會自動跳出彈窗）", "Boolean", "true, false", "true", "是", "—", "事件", "DETAIL_01", "前端", ""),
    ("default_tab", "預設頁籤", "", "String", "tab_name 代碼", "vital_blood_pressure", "是", "—", "事件", "DETAIL_01", "前端", ""),
    ("tab_group", "頁籤群組", "", "String", "info, vital_sign", "info", "是", "—", "事件", "DETAIL_02", "前端", ""),
    ("tab_name", "頁籤名稱", "", "String", "health_plan, care_records, patient_reports, vital_<metric>（例：vital_ecg）", "care_records", "是", "—", "事件", "DETAIL_01, DETAIL_02", "前端", TBC + "完整清單"),
    ("metric", "生理體徵", "與警報項目共用代碼", "String", "blood_pressure, ecg, spo2, blood_glucose, heart_rate, body_temp …", "ecg", "條件：生理體徵相關時必填", "null", "事件", "DETAIL_02, 05, 06", "前端", TBC + "與 CoDoctor App 的 metric 代碼要不要統一？"),
    ("has_data", "頁籤有資料", "", "Boolean", "true, false", "true", "是", "—", "事件", "DETAIL_02", "前端", ""),
    ("is_pending_abnormal", "是否為待處理異常項目", "該生理體徵是否在未處理警報項目中", "Boolean", "true, false", "true", "條件：tab_group=vital_sign", "null", "事件", "DETAIL_02", "前端", ""),
    ("dwell_seconds", "停留秒數", "顯示到離開的秒數，頁面隱藏期間不計", "Number", "到小數 1 位", "8.4", "是", "—", "事件", "DETAIL_02/04/10, FORM_02/03", "前端", ""),
    ("leave_reason", "離開原因", "", "String", "switch_tab, leave_page, page_hidden", "switch_tab", "是", "—", "事件", "DETAIL_02", "前端", ""),
    ("open_type", "開啟方式", "", "String", "auto, manual", "auto", "是", "—", "事件", "DETAIL_03, DETAIL_04", "前端", ""),
    ("open_seq", "本次訪問第幾次開啟", "同一 detail_visit_id 內的開啟次序，從 1 起算", "Integer", "", "2", "是", "—", "事件", "DETAIL_03, DETAIL_04", "前端", ""),
    ("todo_types", "待辦類型", "", "Array<String>", "referral_opinion, doctor_advice, follow_up", "[\"doctor_advice\"]", "是", "[]", "事件", "DETAIL_03", "前端", ""),
    ("range_option", "時間範圍", "", "String", "today, last_7d, last_30d, last_1y, custom", "last_7d", "是", "—", "事件", "DETAIL_06", "前端", ""),
    ("custom_range_days", "自訂天數", "自訂區間的天數", "Integer", "", "14", "條件：range_option=custom", "null", "事件", "DETAIL_06", "前端", ""),
    ("lead", "心電導程", "目前顯示的導程", "String", TBC, "II", "否", "null", "事件", "DETAIL_07", "前端", ""),
    ("block_names", "區塊清單", "", "Array<String>", TBC + "心電區塊代碼", "", "是", "—", "事件", "DETAIL_07", "前端", ""),
    ("block_visible_seconds", "區塊可視秒數", "與 block_names 順序對應", "Array<Integer>", "", "[12, 5]", "是", "—", "事件", "DETAIL_07", "前端", ""),
    ("measure_method", "測量方式", "", "String", "viewport, hover", "viewport", "是", "—", "事件", "DETAIL_07", "前端", ""),
    ("filter_type", "篩選類型", "", "String", "lead, abnormal", "lead", "是", "—", "事件", "DETAIL_08", "前端", ""),
    ("filter_value", "篩選條件", "", "String", TBC, "II", "是", "—", "事件", "DETAIL_08", "前端", ""),
    ("result_count", "篩選結果筆數", "", "Integer", "", "6", "是", "—", "事件", "DETAIL_08", "前端", ""),
    ("record_rank", "第幾筆紀錄", "依時間由新到舊，從 1 起算", "Integer", "", "1", "是", "—", "事件", "DETAIL_09", "前端", ""),
    ("record_type", "紀錄類型", "", "String", "care_record, referral, doctor_advice", "care_record", "是", "—", "事件", "DETAIL_09", "前端", ""),
    ("record_created_at", "紀錄產生時間", "", "Datetime", "ISO 8601", "", "是", "—", "事件", "DETAIL_09", "前端", ""),
    "處置表單",
    ("form_type", "表單類型", "", "String", "care_record, referral, doctor_advice", "care_record", "是", "—", "事件", "FORM_01～03", "前端", ""),
    ("close_method", "關閉方式", "", "String", "cancel, close_icon, mask", "cancel", "是", "—", "事件", "FORM_02", "前端", ""),
    ("has_input", "是否已輸入", "關閉時是否有任何欄位有內容", "Boolean", "true, false", "true", "是", "—", "事件", "FORM_02", "前端", ""),
    ("result", "提交結果", "", "String", "success, fail", "success", "是", "—", "事件", "FORM_03", "前端", ""),
    ("error_code", "錯誤代碼", "API 回傳的錯誤代碼", "String", "", "E4001", "條件：result=fail", "null", "事件", "FORM_03", "前端", ""),
    ("is_empty", "是否空白提交", "所有欄位都沒有內容", "Boolean", "true, false", "false", "是", "—", "事件", "FORM_03", "前端", ""),
    ("filled_field_count", "已填欄位數", "", "Integer", "", "3", "是", "—", "事件", "FORM_03", "前端", TBC + "各表單的欄位清單"),
    ("text_length", "主文字欄位字數", "照護建議／轉診意見／醫師建議的字數（中英文每字算 1）", "Integer", "", "42", "是", "—", "事件", "FORM_03", "前端", "不送內容本身"),
    ("alert_level", "警報等級", "", "String", "high_risk, low_risk, abnormal_report", "high_risk", "條件：有警報事件時", "null", "事件", "SYS_01, FORM_03", "後端／前端", TBC + "一個警報事件裡同時有高低風險時，取最高等級？"),
    ("alert_items", "警報項目", "", "Array<String>", "metric 代碼", "[\"blood_pressure\"]", "條件：有警報事件時", "[]", "事件", "SYS_01, FORM_03", "後端／前端", ""),
    "後端事件專用",
    ("device_source", "警報來源設備", "", "String", "monitor_home, monitor_pro, watch", "watch", "是", "—", "事件", "SYS_01", "後端", ""),
    ("created_at", "產生時間", "伺服器時間", "Datetime", "ISO 8601", "", "是", "—", "事件", "SYS_01, SYS_03", "後端", ""),
    ("resolved_at", "消除／完成時間", "伺服器時間", "Datetime", "ISO 8601", "", "是", "—", "事件", "SYS_02, SYS_04", "後端", ""),
    ("resolve_type", "消除方式", "", "String", "care_record, referral", "care_record", "是", "—", "事件", "SYS_02", "後端", ""),
    ("resolved_by_user_id", "處理人", "", "String", "", "u_10293", "是", "—", "事件", "SYS_02, SYS_04", "後端", ""),
    ("referrer_user_id", "轉診發起人", "", "String", "", "u_10293", "是", "—", "事件", "SYS_03", "後端", ""),
    ("doctor_user_id", "受轉診醫師", "", "String", "", "u_20011", "是", "—", "事件", "SYS_03", "後端", TBC + "可以轉診給多位醫師嗎？"),
]
sheet("5_屬性字典", H_P, P, [22, 16, 36, 14, 40, 26, 18, 16, 8, 30, 12, 40])

# ---------------------------------------------------------------- 6 後端資料需求
H_B = ["編號", "資料", "用途（對應指標）", "需要的欄位", "替代方案", "待確認"]
B = [
    ("BE-01", "警報事件紀錄（SYS_01、SYS_02）", "曝光率、介入率、閉環完成率、所有時長的分母與起點", "alert_event_id, patient_id, org_id, alert_level, alert_items, device_source, created_at, resolved_at, resolve_type, resolved_by_user_id", "若不想從後端發事件，可以每日匯出資料表給分析端", TBC + "合併規則（同一個案未處理期間的多筆警報 → 1 個事件）是否已存在？已讀或刪除的資料會不會保留？"),
    ("BE-02", "轉診紀錄（SYS_03、SYS_04）", "醫師端所有指標", "referral_id, alert_event_id, patient_id, referrer_user_id, doctor_user_id, created_at, resolved_at", "同上", ""),
    ("BE-03", "機構主檔", "依場域、機構拆分；檢測儀來源切換率的分母", "org_id, 機構名稱, 場域類型, 出貨設備（home／pro／watch）", "—", TBC + "場域類型是否已有欄位？"),
    ("BE-04", "帳號主檔", "依角色拆分；醫師活躍度", "user_id, role, org_id 清單, 建立日期, 狀態", "—", ""),
    ("BE-05", "時間基準", "所有時長指標", "埋點收集端記錄 server_received_time", "—", "前端與後端時間統一用 +08:00"),
]
sheet("6_後端資料需求", H_B, B, [8, 26, 34, 50, 30, 50], fill_rule=lambda r: SRV_FILL)

# ---------------------------------------------------------------- 7 待確認
H_Q = ["#", "問題", "影響", "建議預設", "需誰確認", "狀態", "回覆"]
Q = [
    ("Q1", "「警報事件 alert_event_id」怎麼定義？Figma 上的「任務 id」和「警報事件 id」差在哪裡？", "所有護理師指標的計算單位", "同一個案在未處理期間的多筆警報合併為 1 個事件；處理後再發生就是新事件；任務 id＝處理任務，與警報事件 1:1", "產品／後端", "待回覆", ""),
    ("Q2", "曝光要不要加停留門檻？", "N1-01～03、D1-01～03", "≥50% 可見即算，不加停留門檻（B2B 列表通常停留時間不長）", "研究", "待回覆", ""),
    ("Q3", "心電區塊要用可視範圍還是滑鼠停留來量？", "N2-05", "可視範圍為主，measure_method 保留擴充空間", "研究／前端", "待回覆", ""),
    ("Q4", "閉環完成率的觀察窗多長？", "N3-01、D3-01", "7 天", "產品", "待回覆", ""),
    ("Q5", "轉診醫師提交後，警報是否立即消除？", "N3-01 的 resolve_type", "是，resolve_type=referral", "產品", "待回覆", ""),
    ("Q6", "介入率要不要算「從個案列表等其他入口進入」？", "N1-06、D1-04", "主口徑只算通知與待處理列表（跟報告一致），另外附「全部入口」口徑", "研究", "待回覆", ""),
    ("Q7", "待辦再次查看率的「不重複人數」是指護理師還是個案？", "N2-02、D2-01", "改用詳情訪問為單位", "研究", "待回覆", ""),
    ("Q8", "醫師端的「待處理異常」是指有待處理轉診，還是有未消除的警報？", "D2-02", "有待處理轉診", "產品", "待回覆", ""),
    ("Q9", "完整的頁籤、列表、頁面、心電區塊與篩選值清單", "DETAIL_02、07、08，LIST_01", "請提供最新版 Figma 或規格頁連結", "設計／前端", "待回覆", ""),
    ("Q10", "角色清單（是否有個管師、管理員）？一個帳號能同時有多個角色嗎？", "全域 role", "nurse, case_manager, doctor, admin，以當下登入身分為準", "產品", "待回覆", ""),
    ("Q11", "埋點工具是哪一套（GA4／Mixpanel／自建）？支不支援 Array 屬性？", "item_ids 等 Array 屬性的格式", "若不支援 Array，改成逗號字串，或曝光改成一個項目送一筆", "工程", "待回覆", ""),
    ("Q12", "自訂計畫未測量列表要不要算進警報曝光？", "N1-03", "不算，只記錄 NOTIFY_04 的點擊", "研究", "待回覆", ""),
]
sheet("7_待確認問題", H_Q, Q, [6, 56, 26, 50, 14, 10, 40])

# 下拉選單
dv_status = DataValidation(type="list", formula1='"規劃中,開發中,已開發,已驗收,暫不開發"', allow_blank=True)
dv_pri = DataValidation(type="list", formula1='"P0,P1,P2"', allow_blank=True)
ws_e.add_data_validation(dv_status)
ws_e.add_data_validation(dv_pri)
dv_status.add(f"N2:N{ws_e.max_row}")
dv_pri.add(f"M2:M{ws_e.max_row}")
ws_p = wb["5_屬性字典"]
dv_type = DataValidation(type="list", formula1='"String,Integer,Number,Boolean,Datetime,Array<String>,Array<Integer>"', allow_blank=True)
ws_p.add_data_validation(dv_type)
dv_type.add(f"D2:D{ws_p.max_row}")

wb.save(OUT)
print("saved", OUT)
