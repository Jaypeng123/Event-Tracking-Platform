// Demo data for the presentation. Page list mirrors the real Figma file
// 「台灣_護理協作APP_UI_V1.3.0」; the 派工詳情 events were planned from its screens.
export const DEMO_FIGMA_URL =
  "https://www.figma.com/design/eQqCYglrY0rs6PNRXyLsU7/%E5%8F%B0%E7%81%A3_%E8%AD%B7%E7%90%86%E5%8D%94%E4%BD%9CAPP_UI_V1.3.0?node-id=3001-46132&t=2W8tZE5ycaBeNMdX-1";
export const DEMO_FILE_NAME = "台灣_護理協作APP_UI_V1.3.0";

// Same cleanup the real /api/figma-pages applies to page names.
const cleanPageName = (value) =>
  value
    .replace(/[（(]\s*\d+(?:\.\d+)?(?:\s*[~～\-–—]\s*\d+(?:\.\d+)?)?\s*[）)]/g, "")
    .replace(/\s+\d+(?:\.\d+)?(?:\s*[~～\-–—]\s*\d+(?:\.\d+)?)?\s*$/g, "")
    .replace(/\s{2,}/g, " ")
    .trim() || "Untitled page";

export const DEMO_PAGES = [
  ["14:1010", "Cover"],
  ["10967:11647", "🌈  v1.3.0 優化列點記錄匯總"],
  ["11355:67072", "---"],
  ["14916:138895", "✅ v1.3.0 童綜合16A場域試用後優化"],
  ["15717:33327", "✅ | 走查後優化項目"],
  ["11164:136172", "-----------------"],
  ["5122:46707", "V1.3.0---------------------"],
  ["15426:33123", "------"],
  ["3001:46128", "✅ ｜APP 全局定義"],
  ["3001:46129", "✅ ｜0 登入"],
  ["14:1077", "✅ ｜1 首頁"],
  ["7133:68376", "✅ ｜2 派工列表"],
  ["14:1078", "✅ ｜3 派工詳情"],
  ["3001:46130", "✅ ｜4 建立派工"],
  ["14:1079", "✅ ｜5 我的"],
  ["3001:46132", "✅ ｜6 通知"],
  ["14:1082", "---"],
  ["12692:81531", "❌｜各醫院客製化差異示意"],
  ["12692:81532", "---------------"],
  ["5931:2744", "❌｜Panding 待確認功能"],
  ["13273:65663", "英文翻譯用"],
  ["3001:46133", "👀 App UI component"],
  ["5794:128973", "優化列點"],
  ["10615:104591", "App操作說明書"],
  ["23:306", "🗒️ Draft"],
  ["8399:57707", "🗑️ Bin"],
].map(([id, name]) => ({ id, name: cleanPageName(name) }));

const PAGE = "派工詳情";
const DT = "dispatch_type";
const DT_DEF = "派工類型";
const DT_SAMPLE = "medicine, specimen, education, environment";

// [priority, area, metricName, eventName, eventType, trigger, purpose, analysisValue, metricCalculation, properties, propertyDefinitions, dataTypes, sampleValues]
const dispatchDetail = [
  // 全局：所有派工類型共用
  ["P0", "派工詳情 / 頁面載入", "派工詳情到達率", "view_dispatch_detail", "PageView", "進入派工詳情頁，且派工狀態卡片載入完成時", "了解護理師查看派工進度的頻率與入口來源", "作為派工詳情所有指標的分母，並比較從首頁、派工列表、通知進入的比例", "派工詳情瀏覽不重複使用者數 ÷ 當日有派工的不重複使用者數", `${DT}; dispatch_status; entry_source`, `${DT_DEF}; 派工狀態; 進入來源`, "string; string; string", `${DT_SAMPLE}; pending, in_progress, ended; home, dispatch_list, notification`],
  ["P1", "派工詳情 / 切換頁籤", "詳情頁籤切換率", "switch_detail_tab", "Click", "點擊「執行進度」與「區域藥品清單／區域檢體清單／衛教詳情／病患詳情」頁籤時", "了解護理師在派工中最常查看進度還是清單內容", "比較各派工類型的頁籤使用比例，判斷預設頁籤是否符合使用習慣", "切換到清單類頁籤的次數 ÷ 派工詳情瀏覽次數", `${DT}; from_tab; to_tab; dispatch_status`, `${DT_DEF}; 原頁籤; 目標頁籤; 派工狀態`, "string; string; string; string", `${DT_SAMPLE}; execution_progress; area_list; in_progress`],
  ["P1", "派工詳情 / 刪除派工", "刪除派工意圖率", "click_delete_dispatch", "Click", "在待執行狀態點擊右上角刪除派工按鈕時", "了解派工建立後被取消的比例與時間點", "若刪除意圖偏高，代表建立派工流程可能容易誤建或資訊不足", "點擊刪除派工的派工數 ÷ 待執行派工數", `${DT}; minutes_before_start`, `${DT_DEF}; 距離開始執行分鐘數`, "string; number", `${DT_SAMPLE}; 15`],
  ["P0", "派工詳情 / 刪除派工彈窗", "刪除派工完成率", "delete_dispatch_confirm", "FlowComplete", "在「刪除派工？」彈窗點擊「刪除派工」並成功刪除時", "衡量實際取消的派工量，避免機器人資源被無效派工佔用", "與建立派工數對照，計算派工取消率並追蹤取消原因", "成功刪除的派工數 ÷ 已建立派工數", `${DT}; minutes_before_start; created_by_role`, `${DT_DEF}; 距離開始執行分鐘數; 建立者角色`, "string; number; string", `${DT_SAMPLE}; 15; head_nurse`],
  ["P1", "派工詳情 / 刪除失敗提示", "派工刪除失敗率", "delete_dispatch_failed", "ErrorDropoff", "顯示「派工已開始執行，刪除失敗」提示時", "找出護理師在派工已開始後才想取消的情境", "若失敗次數高，代表需要在派工開始前提供更明確的提醒或確認", "刪除失敗次數 ÷ 點擊刪除派工次數", `${DT}; dispatch_status`, `${DT_DEF}; 派工狀態`, "string; string", `${DT_SAMPLE}; in_progress`],
  ["P1", "派工詳情 / 病患資訊", "病患資訊確認率", "view_patient_info", "Click", "點擊病患床號旁的資訊圖示，開啟病患資訊（姓名、病歷號）時", "了解護理師交接物品時是否需要再次核對病患身分", "確認率高代表清單上的病患資訊不足以辨識，可評估是否直接顯示病歷號", "開啟病患資訊次數 ÷ 清單頁籤瀏覽次數", `${DT}; source_tab; dispatch_status`, `${DT_DEF}; 來源頁籤; 派工狀態`, "string; string; string", `${DT_SAMPLE}; area_list; in_progress`],
  ["P0", "派工詳情 / 任務異常終止", "任務異常終止率", "view_task_aborted", "ErrorDropoff", "派工狀態卡片顯示「任務終止執行」時", "掌握機器人執行任務時發生異常的頻率與發生階段", "依派工類型與發生階段（抵達定點後／移動中）分析，作為機器人穩定性改善依據", "異常終止的派工數 ÷ 開始執行的派工數", `${DT}; abort_stage; robot_id; stop_index`, `${DT_DEF}; 終止階段; 機器人編號; 終止時所在站點`, "string; string; string; number", `${DT_SAMPLE}; moving_between_points; ROBOT-A; 3`],
  ["P0", "派工詳情 / 異常後取物提示", "異常取物提示點擊率", "click_abort_retrieve_notice", "Click", "任務終止後點擊「請從機器人身上取出藥品／檢體」提示的「查看」時", "確認護理師是否看見提示並處理機器人上的物品", "物品未被取出可能造成用藥或檢體延誤，屬於高風險流程", "點擊取物提示的派工數 ÷ 異常終止且機器人上有物品的派工數", `${DT}; item_count; minutes_after_abort`, `${DT_DEF}; 待取出物品數; 異常後經過分鐘數`, "string; number; number", `${DT_SAMPLE}; 2; 3`],
  ["P1", "派工詳情 / 無法執行派工", "派工無法執行率", "view_dispatch_unavailable", "ErrorDropoff", "派工詳情顯示「無法執行此派工」或「機器人目前無法派工」狀態時", "了解派工因機器人不可用而無法執行的比例", "作為機器人數量與排程容量規劃的依據", "無法執行的派工數 ÷ 已建立派工數", `${DT}; unavailable_reason`, `${DT_DEF}; 無法執行原因`, "string; string", `${DT_SAMPLE}; robot_busy`],
  ["P1", "派工詳情 / 抵達提示", "機器人抵達提示曝光", "view_robot_arrived", "PageView", "狀態卡片顯示「請前往 X 區交付／領取」時", "記錄機器人抵達區域的時間點，作為護理師回應時間的起點", "與交付／領取完成事件相減，計算護理師平均回應時間", "交付或領取完成時間 − 抵達提示曝光時間（平均分鐘數）", `${DT}; area; scheduled_time`, `${DT_DEF}; 區域; 預計抵達時間`, "string; string; string", "specimen; A-2; 10:08"],

  // 藥品配送
  ["P0", "藥品配送 / 領藥完成", "藥品領取完成率", "medicine_pickup_complete", "FlowComplete", "護理師刷卡領藥後，區域藥品清單狀態變為「已領取」時", "衡量藥品配送是否準時送到負責的護理師手上", "藥品配送的核心成效指標，可依區域比較領取完成率", "已領取藥品項數 ÷ 配送藥品總項數", "area; item_count; is_proxy_pickup", "區域; 領取項數; 是否由他人代領", "string; number; boolean", "A-3; 3; false"],
  ["P0", "藥品配送 / 超時未領取", "藥品超時未領取率", "medicine_pickup_timeout", "ErrorDropoff", "區域藥品清單出現「超時未領取」狀態時", "找出藥品無人領取、機器人被迫離開的區域與時段", "超時代表給藥可能延誤，需追蹤是否集中在特定區域或時段", "超時未領取藥品項數 ÷ 配送藥品總項數", "area; item_count; wait_minutes", "區域; 未領取項數; 等待分鐘數", "string; number; number", "B-1; 2; 5"],
  ["P0", "藥品配送 / 他區領取提示", "藥品被他區領取率", "view_medicine_taken_by_other", "ErrorDropoff", "顯示「你的藥品被他區的人取走，請聯繫領取人」彈窗時", "掌握藥品被錯誤領取的頻率，屬於用藥安全風險", "可依區域與領取人分析誤領原因，評估是否需要加強身分驗證", "被他區領取的藥品項數 ÷ 已領取藥品項數", "taken_count; owner_area; taker_area", "被取走項數; 原本所屬區域; 領取人區域", "number; string; string", "2; A-2; B-1"],
  ["P1", "藥品配送 / 配送結束", "配送結果摘要查看率", "view_delivery_summary", "PageView", "藥品配送結束，顯示配送結果與異常彙整時", "了解護理師是否會回顧配送結果與異常", "多種異常並存時的處理情況，可作為異常彙整版面的優化依據", "查看配送結果的派工數 ÷ 配送結束的派工數", "exception_types; exception_count", "異常類型; 異常數量", "string; number", "timeout, taken_by_other; 2"],

  // 檢體取送
  ["P0", "檢體取送 / 交付完成", "檢體交付完成率", "specimen_handover_complete", "FlowComplete", "護理師將檢體交付給機器人，清單狀態變為「已交付」時", "衡量檢體是否在機器人停留時間內順利交付", "檢體取送的核心成效指標，可依區域與是否為急件分析", "已交付檢體項數 ÷ 預約交付檢體項數", "area; specimen_count; urgent_count; handover_round", "區域; 交付項數; 急件數; 第幾次交付", "string; number; number; number", "A-2; 3; 1; 1"],
  ["P0", "檢體取送 / 超時未交付", "檢體超時未交付率", "specimen_handover_timeout", "ErrorDropoff", "清單出現「超時未交付」或狀態卡顯示「超時未交付，機器人已離去」時", "找出檢體未能及時交付的區域與原因", "超時會延誤檢驗時間，需追蹤發生區域與時段以調整排程", "超時未交付檢體項數 ÷ 預約交付檢體項數", "area; specimen_count; urgent_count", "區域; 未交付項數; 急件數", "string; number; number", "A-2; 2; 0"],
  ["P0", "檢體取送 / 再次預約", "檢體再次預約點擊率", "click_rebook_specimen", "Click", "檢體超時未交付後，點擊「再次預約」按鈕時", "了解超時後護理師是否會立即補救", "補救比例可評估再次預約功能的價值與入口明顯度", "點擊再次預約的派工數 ÷ 超時未交付且可再次預約的派工數", "area; specimen_count; minutes_after_timeout", "區域; 待交付項數; 超時後經過分鐘數", "string; number; number", "A-2; 2; 4"],
  ["P1", "檢體取送 / 新派工建立", "檢體重新派工成功率", "rebook_specimen_success", "CreateEdit", "再次預約後顯示「已建立一個新的檢體派工」時", "確認補救流程能成功建立新派工", "與再次預約點擊數比較，找出補救流程中的失敗點", "重新派工成功數 ÷ 點擊再次預約次數", "new_dispatch_id; specimen_count", "新派工編號; 檢體項數", "string; number", "D-20260313-018; 2"],
  ["P1", "檢體取送 / 無法重新派工", "無法再次預約率", "view_rebook_unavailable", "ErrorDropoff", "顯示「無法重新派工」或再次預約按鈕失效時", "了解超時後無法補救的情況有多常發生", "若比例偏高，需評估重新預約的時效與規則是否過於嚴格", "無法再次預約的派工數 ÷ 超時未交付的派工數", "unavailable_reason", "無法重新派工原因", "string", "rebook_window_expired"],
  ["P1", "檢體取送 / 取送結束", "取送結果查看率", "view_specimen_summary", "PageView", "檢體取送結束，顯示取送紀錄與放置結果時", "了解護理師是否確認檢體已送達檢體站", "可依是否有急件、機器人是否收回檢體分析結束情境", "查看取送結果的派工數 ÷ 取送結束的派工數", "has_normal; has_urgent; robot_collected", "是否有一般件; 是否有急件; 機器人是否收回檢體", "boolean; boolean; boolean", "true; false; true"],

  // 護理衛教
  ["P0", "護理衛教 / 開始衛教", "衛教開始率", "education_started", "FlowComplete", "護理師接洽機器人後，狀態卡片進入「衛教中」時", "衡量排定的衛教是否真正開始執行", "與待執行衛教數比較，可找出排定後未執行的衛教", "開始衛教的派工數 ÷ 已排定的衛教派工數", "item_total; target_count", "衛教項目數; 衛教對象數", "number; number", "3; 2"],
  ["P0", "護理衛教 / 衛教完成", "衛教完成率", "education_complete", "FlowComplete", "狀態卡片顯示「完成衛教，指導完成」時", "衡量衛教從開始到完成的成效", "護理衛教的核心成效指標，可依衛教項目數分析完成情況", "完成衛教的派工數 ÷ 開始衛教的派工數", "completed_items; item_total; duration_minutes", "完成項目數; 衛教項目數; 衛教總時長", "number; number; number", "3; 3; 18"],
  ["P1", "護理衛教 / 結束方式", "衛教結束方式分布", "education_ended", "FlowComplete", "衛教任務結束時（護理師協助結束或機器人自動結束）", "了解衛教多半是正常完成，還是需要護理師介入結束", "若需護理師協助結束的比例高，代表衛教流程或機器人引導需要調整", "各結束方式的派工數 ÷ 結束的衛教派工數", "end_type; completed_items; item_total", "結束方式; 完成項目數; 衛教項目數", "string; number; number", "nurse_assisted; 2; 3"],
  ["P1", "護理衛教 / 作答詳情", "測驗結果查看率", "view_quiz_detail", "Click", "在衛教詳情點擊衛教項目，開啟「答題詳情」時", "了解護理師是否會確認病患與家屬的測驗結果", "可依測驗合格與否分析查看行為，判斷是否需要後續追蹤衛教", "開啟答題詳情次數 ÷ 衛教詳情瀏覽次數", "item_index; quiz_result; wrong_count", "衛教項目序號; 測驗結果; 答錯題數", "number; string; number", "1; failed; 2"],
  ["P1", "護理衛教 / 測驗不合格", "衛教測驗不合格率", "quiz_failed", "ErrorDropoff", "衛教項目測驗結果為「測驗不合格」時", "找出病患與家屬最容易誤解的衛教主題", "依衛教項目與題目統計不合格比例，作為衛教內容改善依據", "測驗不合格的項目數 ÷ 含測驗的衛教項目數", "item_name; wrong_questions", "衛教項目名稱; 答錯題號", "string; string", "如何預防高齡長者譫妄; 2,3"],
  ["P0", "護理衛教 / 新增衛教對象", "衛教對象新增率", "add_education_target", "CreateEdit", "在「新增衛教對象」填寫姓名、選擇關係並儲存成功時", "了解衛教是否擴及家屬與照顧者", "家屬參與衛教是照護品質的重要指標，可依關係類型分析", "新增衛教對象的派工數 ÷ 衛教派工數", "relationship; target_count", "與病患關係; 衛教對象總數", "string; number", "parent; 2"],
  ["P2", "護理衛教 / 編輯衛教對象", "衛教對象編輯率", "edit_education_target", "CreateEdit", "編輯既有衛教對象的姓名或關係並儲存時", "觀察衛教對象資料是否常需要修正", "若編輯比例高，代表新增時的欄位或預設值可能容易出錯", "編輯衛教對象次數 ÷ 新增衛教對象次數", "edited_field", "修改欄位", "string", "relationship"],
  ["P2", "護理衛教 / 刪除衛教對象", "衛教對象刪除率", "delete_education_target", "CreateEdit", "確認刪除衛教對象時", "觀察衛教對象被移除的情況", "搭配新增與編輯數據，了解衛教對象管理是否順暢", "刪除衛教對象次數 ÷ 新增衛教對象次數", "relationship", "與病患關係", "string", "spouse"],
  ["P1", "護理衛教 / 衛教對象不存在", "衛教對象失效提示率", "view_target_not_found", "ErrorDropoff", "顯示「此衛教對象不存在」提示時", "找出衛教對象資料與機器人端不同步的情況", "若頻繁出現，需檢查資料同步或提示「請至機器人刷新列表」的時機", "出現對象不存在提示的次數 ÷ 開啟衛教對象清單次數", "target_source", "對象來源", "string", "system_import"],
  ["P1", "護理衛教 / QR Code 掃碼", "機器人配對掃碼成功率", "scan_robot_qr_code", "Click", "掃描機器人顯示的 QR Code 完成配對，或出現「掃描錯誤，請重新確認」時", "了解護理師與機器人配對是否順利，這是衛教開始前的關鍵步驟", "掃碼失敗會延後衛教開始，可依失敗原因與重試次數排查", "掃碼配對成功次數 ÷ 開始掃碼次數", "scan_result; retry_count; fail_reason", "掃碼結果; 重試次數; 失敗原因", "string; number; string", "failed; 1; invalid_code"],
  ["P0", "護理衛教 / 超時未引導", "衛教超時未引導率", "education_guide_timeout", "ErrorDropoff", "狀態卡片顯示「超時未引導，機器人已離去」時", "掌握機器人到場後無人接洽的比例", "超時代表衛教未能進行，需追蹤是否集中在特定時段或病房", "超時未引導的衛教派工數 ÷ 已排定的衛教派工數", "ward; can_rebook", "病房; 是否可再次預約", "string; boolean", "W106-17; true"],
  ["P0", "護理衛教 / 重新預約", "衛教重新預約率", "click_rebook_education", "Click", "超時未引導後，在 24 小時內點擊「預約護理衛教」時", "了解錯過衛教後是否會重新安排", "可評估 24 小時重新預約機制是否有效挽回衛教", "點擊重新預約的派工數 ÷ 超時未引導且可再次預約的派工數", "hours_left; item_total", "剩餘可預約小時數; 衛教項目數", "number; number", "20; 3"],

  // 環境介紹
  ["P1", "環境介紹 / 前往會合", "會合等待提示曝光", "view_meet_patient", "PageView", "狀態卡片顯示「前往與病患會合」時", "記錄機器人前往會合的時間點，作為等待時間的起點", "與環境介紹開始時間相減，計算病患與機器人的會合等待時間", "環境介紹開始時間 − 會合提示曝光時間（平均分鐘數）", "intro_type; ward", "介紹類型; 病房", "string; string", "full_tour; 18"],
  ["P1", "環境介紹 / 區域介紹進度", "區域介紹到達率", "environment_area_reached", "PageView", "機器人抵達並開始介紹每一個區域（如 A 區、B 區）時", "了解環境介紹在哪個區域最常中斷", "依區域統計到達比例，找出介紹路線中容易流失的站點", "到達各區域的派工數 ÷ 開始環境介紹的派工數", "area_name; stop_index; stop_total", "區域名稱; 第幾站; 總站數", "string; number; number", "A區; 4; 6"],
  ["P0", "環境介紹 / 介紹完成", "環境介紹完成率", "environment_intro_complete", "FlowComplete", "狀態卡片顯示「環境介紹結束」時", "衡量新入院病患是否完整完成環境介紹", "環境介紹的核心成效指標，可比較完整介紹與帶入病室兩種類型", "完成環境介紹的派工數 ÷ 開始環境介紹的派工數", "intro_type; duration_minutes; stop_total", "介紹類型; 介紹總時長; 介紹站數", "string; number; number", "full_tour; 15; 6"],
  ["P1", "環境介紹 / 帶入病室", "帶入病室完成率", "bring_to_room_complete", "FlowComplete", "機器人將病患帶入病室，流程完成時", "了解「帶入病室」型派工是否順利完成", "與完整介紹的完成率比較，判斷哪種介紹方式較適合新入院病患", "完成帶入病室的派工數 ÷ 開始帶入病室的派工數", "room_no; duration_minutes", "病室號碼; 所需時間", "string; number", "18; 6"],
];

const toEvents = (rows) =>
  rows.map((r, i) => {
    const [priority, area, metricName, eventName, eventType, trigger, purpose, analysisValue, metricCalculation, properties, propertyDefinitions, dataTypes, sampleValues] = r;
    return {
      id: `AI_${String(i + 1).padStart(3, "0")}`,
      page: PAGE, area, metricName, eventName, eventType, trigger, purpose, analysisValue, metricCalculation,
      properties, propertyDefinitions, dataTypes, sampleValues, priority, status: "AI 產生",
    };
  });

const EVENTS = { 派工詳情: toEvents(dispatchDetail) };

// Pages without planned demo data return no events; the app then falls back to
// its own Figma-structure rows, exactly as the real tool does.
export function eventsForPage(pageName) {
  const key = Object.keys(EVENTS).find((k) => pageName.includes(k));
  return key ? EVENTS[key] : [];
}
