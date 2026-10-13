// Demo-only data: a fictional food-ordering app ("iOrder") used to walk through the tool.
export const DEMO_FIGMA_URL = "https://www.figma.com/design/kQ8dDemoIOrder2026/iOrder-Mobile-App-Redesign";
export const DEMO_FILE_NAME = "iOrder Mobile App Redesign";

export const DEMO_PAGES = [
  { id: "1:2", name: "首頁 Home", childCount: 18 },
  { id: "1:3", name: "菜單與商品 Menu", childCount: 24 },
  { id: "1:4", name: "購物車與結帳 Checkout", childCount: 21 },
  { id: "1:5", name: "會員獎勵 Rewards", childCount: 12 },
  { id: "1:6", name: "帳戶設定 Account", childCount: 9 },
  { id: "1:7", name: "Archive 舊版設計", childCount: 6 },
];

const row = (prefix, i, priority, page, area, metricName, eventName, eventType, trigger, purpose, analysisValue, metricCalculation, properties, propertyDefinitions, dataTypes, sampleValues) => ({
  id: `${prefix}_${String(i).padStart(3, "0")}`,
  priority, page, area, metricName, eventName, eventType, trigger, purpose, analysisValue, metricCalculation,
  properties, propertyDefinitions, dataTypes, sampleValues, status: "AI 產生",
});

const HOME = "首頁";
const home = [
  ["P0", "首頁 / 頁面載入", "首頁到達率", "view_home", "PageView", "使用者進入首頁且主要內容載入完成時", "了解首頁作為商品探索與購買入口的實際到達量", "判斷首頁是否仍是主要的商品入口，並比較不同流量來源的使用規模", "首頁瀏覽不重複使用者數 ÷ App 開啟不重複使用者數", "entry_source; user_type", "進入來源; 使用者類型", "string; string", "push, organic; new, returning"],
  ["P0", "首頁 / 主打飲品", "主打飲品加購率", "click_featured_add", "Click", "點擊主打飲品卡片上的「加入購物車」時", "衡量首頁主打商品是否能直接促成購買意圖", "判斷主打飲品是否值得維持在首頁主要版位", "點擊主打加購的不重複使用者數 ÷ 首頁瀏覽不重複使用者數", "product_id; product_name; position", "商品編號; 商品名稱; 版位順序", "string; string; number", "DRK-021; 海鹽焦糖拿鐵; 1"],
  ["P0", "首頁 / 搜尋列", "首頁搜尋使用率", "submit_home_search", "SearchFilter", "在首頁搜尋列輸入關鍵字並送出時", "了解使用者是否偏好直接搜尋而非瀏覽分類", "若搜尋使用率高，代表分類結構可能不夠直覺", "送出搜尋的不重複使用者數 ÷ 首頁瀏覽不重複使用者數", "keyword; result_count", "搜尋關鍵字; 結果數量", "string; number", "燕麥奶; 12"],
  ["P0", "首頁 / 購物車按鈕", "購物車開啟率", "click_open_cart", "Click", "點擊首頁右上角購物車圖示時", "了解使用者從首頁進入結帳流程的比例", "購物車開啟是轉換漏斗的關鍵節點，缺少此資料無法計算轉換", "開啟購物車的不重複使用者數 ÷ 首頁瀏覽不重複使用者數", "cart_item_count; cart_value", "購物車品項數; 購物車金額", "number; number", "3; 285"],
  ["P1", "首頁 / 商品分類", "商品分類使用率", "click_category", "Click", "點擊「咖啡」「茶飲」「輕食」等分類入口時", "了解使用者是否透過分類入口探索不同商品群組", "比較各分類入口的使用量，找出可整併的低使用分類", "點擊各分類的次數 ÷ 首頁瀏覽次數", "category_name; position", "分類名稱; 版位順序", "string; number", "咖啡; 1"],
  ["P1", "首頁 / 推薦商品", "推薦商品加購率", "click_recommend_add", "Click", "點擊「為你推薦」區塊商品的加入購物車時", "衡量推薦商品對實際加購行為的貢獻", "比較推薦商品與主打商品的加購表現，判斷推薦區是否值得保留", "推薦區加購次數 ÷ 推薦區曝光次數", "product_id; recommend_reason", "商品編號; 推薦原因", "string; string", "FD-104; 常一起購買"],
  ["P1", "首頁 / 活動 Banner", "活動 Banner 點擊率", "click_promo_banner", "Click", "點擊首頁輪播活動 Banner 時", "了解活動曝光是否帶來實際點擊", "評估 Banner 輪播順序與活動素材的成效", "Banner 點擊次數 ÷ Banner 曝光次數", "campaign_id; slide_index", "活動編號; 輪播序號", "string; number", "OCT-BOGO; 2"],
  ["P1", "首頁 / 取餐方式", "取餐方式切換率", "switch_pickup_mode", "Click", "在首頁切換「外帶自取」與「外送」時", "了解使用者偏好的取餐方式", "作為門市備餐與外送合作的資源配置參考", "切換為外送的使用者數 ÷ 首頁瀏覽使用者數", "from_mode; to_mode", "原取餐方式; 新取餐方式", "string; string", "pickup; delivery"],
  ["P1", "首頁 / 門市選擇", "門市切換率", "change_store", "CreateEdit", "使用者在首頁更換預設門市時", "了解使用者是否常需要更換取餐門市", "若切換率高，代表預設門市推薦不夠準確", "更換門市的使用者數 ÷ 首頁瀏覽使用者數", "from_store; to_store; distance_km", "原門市; 新門市; 距離（公里）", "string; string; number", "信義店; 市府店; 0.8"],
  ["P1", "首頁 / 會員點數", "點數入口點擊率", "click_points_entry", "Click", "點擊首頁上方會員點數卡片時", "了解會員是否關注點數與兌換資訊", "評估點數卡片是否需要更明顯的兌換引導", "點擊點數卡片的使用者數 ÷ 會員首頁瀏覽使用者數", "points_balance; member_tier", "點數餘額; 會員等級", "number; string", "320; gold"],
  ["P2", "首頁 / 再買一次", "再買一次使用率", "click_reorder", "Click", "點擊「再買一次」快速下單時", "觀察回購使用者是否使用快速下單功能", "作為是否擴充常買清單功能的參考", "點擊再買一次的使用者數 ÷ 回購使用者數", "order_id; item_count", "原訂單編號; 品項數", "string; number", "OD-88231; 2"],
  ["P2", "首頁 / 通知中心", "通知中心開啟率", "open_notification", "Click", "點擊首頁鈴鐺圖示開啟通知中心時", "觀察使用者是否會主動查看活動與訂單通知", "評估通知中心的使用價值與訊息數量", "開啟通知中心的使用者數 ÷ 首頁瀏覽使用者數", "unread_count", "未讀數量", "number", "4"],
];

const MENU = "菜單與商品";
const menu = [
  ["P0", "菜單 / 頁面載入", "菜單頁瀏覽率", "view_menu", "PageView", "進入菜單頁且商品列表載入完成時", "了解有多少使用者進入商品瀏覽階段", "作為商品轉換漏斗的分母", "菜單頁瀏覽使用者數 ÷ App 開啟使用者數", "entry_source; category_name", "進入來源; 預設分類", "string; string", "home_category; 咖啡"],
  ["P0", "商品詳情 / 加入購物車", "商品加購率", "add_to_cart", "Click", "在商品詳情頁點擊「加入購物車」時", "衡量商品詳情頁是否能促成購買", "核心轉換指標，用來比較不同商品的吸引力", "加入購物車次數 ÷ 商品詳情瀏覽次數", "product_id; quantity; price", "商品編號; 數量; 單價", "string; number; number", "DRK-021; 1; 95"],
  ["P0", "商品詳情 / 客製化選項", "客製化完成率", "complete_customize", "FlowComplete", "選完甜度、冰塊、加料並確認時", "了解客製化流程是否造成放棄", "若完成率偏低，代表選項太多或排列不直覺", "完成客製化次數 ÷ 開啟客製化次數", "sugar_level; ice_level; topping_count", "甜度; 冰塊; 加料數", "string; string; number", "half; less; 1"],
  ["P1", "菜單 / 分類標籤", "分類標籤切換率", "switch_menu_tab", "Click", "點擊菜單頁上方分類標籤時", "了解使用者在不同分類間的瀏覽路徑", "找出熱門與冷門分類，作為菜單排序依據", "各分類標籤點擊次數 ÷ 菜單頁瀏覽次數", "tab_name; previous_tab", "點擊分類; 前一個分類", "string; string", "茶飲; 咖啡"],
  ["P1", "菜單 / 篩選", "篩選功能使用率", "apply_menu_filter", "SearchFilter", "套用「無咖啡因」「低卡」等篩選條件時", "了解使用者是否需要依需求篩選商品", "判斷篩選條件是否符合使用者實際需求", "套用篩選的使用者數 ÷ 菜單頁瀏覽使用者數", "filter_type; result_count", "篩選條件; 結果數量", "string; number", "decaf; 8"],
  ["P1", "商品詳情 / 頁面載入", "商品詳情瀏覽率", "view_product_detail", "PageView", "進入商品詳情頁時", "了解哪些商品最常被查看", "與加購率搭配，找出「看很多但買很少」的商品", "商品詳情瀏覽次數 ÷ 菜單頁瀏覽次數", "product_id; source_list", "商品編號; 來源列表", "string; string", "DRK-021; menu_grid"],
  ["P1", "商品詳情 / 加價購", "加價購接受率", "accept_upsell", "Click", "在加價購推薦中點擊「一起買」時", "衡量加價購推薦對客單價的貢獻", "評估加價購組合是否需要調整", "接受加價購次數 ÷ 加價購曝光次數", "upsell_product_id; discount", "加價購商品; 折扣金額", "string; number", "FD-104; 20"],
  ["P2", "商品詳情 / 收藏", "商品收藏率", "favorite_product", "CreateEdit", "點擊商品詳情的愛心收藏時", "觀察使用者是否會收藏常買商品", "作為個人化推薦的訊號來源", "收藏次數 ÷ 商品詳情瀏覽次數", "product_id", "商品編號", "string", "DRK-021"],
  ["P2", "商品詳情 / 售完提示", "售完商品曝光率", "view_sold_out", "ErrorDropoff", "使用者查看到「今日售完」商品時", "了解售完商品對購買流程的影響", "作為門市備貨量調整的參考", "看到售完提示的使用者數 ÷ 菜單頁瀏覽使用者數", "product_id; store_id", "商品編號; 門市編號", "string; string", "DRK-033; S-012"],
];

const CHECKOUT = "購物車與結帳";
const checkout = [
  ["P0", "購物車 / 頁面載入", "購物車瀏覽率", "view_cart", "PageView", "進入購物車頁且品項載入完成時", "作為結帳漏斗的起點", "缺少此資料無法計算購物車到下單的轉換", "購物車瀏覽使用者數 ÷ 加入購物車使用者數", "cart_item_count; cart_value", "品項數; 購物車金額", "number; number", "3; 285"],
  ["P0", "結帳 / 前往結帳", "結帳開始率", "begin_checkout", "Click", "在購物車點擊「前往結帳」時", "了解使用者從購物車進入結帳的比例", "判斷購物車頁是否有阻礙結帳的因素", "前往結帳使用者數 ÷ 購物車瀏覽使用者數", "cart_value; coupon_applied", "購物車金額; 是否使用優惠券", "number; boolean", "285; true"],
  ["P0", "結帳 / 付款完成", "下單完成率", "purchase_complete", "FlowComplete", "付款成功並顯示訂單完成頁時", "衡量整個購買流程的最終轉換", "核心營收指標，用來評估所有改版成效", "完成付款使用者數 ÷ 前往結帳使用者數", "order_id; payment_method; order_value", "訂單編號; 付款方式; 訂單金額", "string; string; number", "OD-90412; line_pay; 285"],
  ["P0", "結帳 / 付款失敗", "付款失敗率", "payment_failed", "ErrorDropoff", "付款失敗或被拒絕時", "找出付款環節造成的流失", "依付款方式比較失敗率，判斷是否需要調整金流", "付款失敗次數 ÷ 付款嘗試次數", "payment_method; error_code", "付款方式; 錯誤代碼", "string; string", "credit_card; 3DS_TIMEOUT"],
  ["P1", "結帳 / 優惠券", "優惠券使用率", "apply_coupon", "CreateEdit", "在結帳頁套用優惠券時", "了解優惠活動對下單的影響", "評估優惠券是否真的提升轉換", "套用優惠券的訂單數 ÷ 完成訂單數", "coupon_id; discount_amount", "優惠券編號; 折抵金額", "string; number", "OCT20; 20"],
  ["P1", "結帳 / 取餐時間", "預約取餐使用率", "select_pickup_time", "CreateEdit", "選擇「預約時間」而非「立即取餐」時", "了解使用者是否需要預約取餐", "作為門市尖峰備餐排程的參考", "選擇預約取餐的訂單數 ÷ 完成訂單數", "pickup_time; lead_minutes", "預約時間; 提前分鐘數", "string; number", "12:30; 45"],
  ["P1", "購物車 / 修改品項", "購物車品項修改率", "edit_cart_item", "CreateEdit", "在購物車修改數量或客製化選項時", "了解使用者是否常在購物車調整訂單", "若修改率高，代表商品頁的選項設定不夠清楚", "修改品項的使用者數 ÷ 購物車瀏覽使用者數", "product_id; change_type", "商品編號; 修改類型", "string; string", "DRK-021; quantity"],
  ["P1", "購物車 / 移除品項", "品項移除率", "remove_cart_item", "ErrorDropoff", "在購物車刪除品項時", "觀察哪些商品最常被放棄", "找出價格或選項設定可能有問題的商品", "移除品項次數 ÷ 加入購物車次數", "product_id; price", "商品編號; 單價", "string; number", "FD-118; 120"],
  ["P2", "結帳 / 付款方式", "付款方式切換率", "change_payment_method", "Click", "在結帳頁切換付款方式時", "觀察使用者偏好的付款方式", "作為付款選項排序的參考", "切換付款方式的使用者數 ÷ 前往結帳使用者數", "from_method; to_method", "原付款方式; 新付款方式", "string; string", "credit_card; line_pay"],
  ["P2", "訂單完成 / 分享", "訂單分享率", "share_order", "ExportDownload", "在訂單完成頁點擊分享時", "觀察使用者是否會分享訂單給朋友", "作為揪團與分享功能的需求參考", "分享次數 ÷ 完成訂單數", "share_channel", "分享管道", "string", "line"],
];

const REWARDS = "會員獎勵";
const rewards = [
  ["P0", "會員獎勵 / 頁面載入", "獎勵頁瀏覽率", "view_rewards", "PageView", "進入會員獎勵頁時", "了解會員是否主動查看點數與獎勵", "作為會員經營成效的基礎指標", "獎勵頁瀏覽會員數 ÷ 活躍會員數", "member_tier; points_balance", "會員等級; 點數餘額", "string; number", "gold; 320"],
  ["P0", "會員獎勵 / 兌換", "點數兌換完成率", "redeem_reward", "FlowComplete", "完成點數兌換並取得兌換券時", "衡量點數制度是否能帶動回訪", "核心會員指標，判斷獎勵品項是否有吸引力", "完成兌換次數 ÷ 點擊兌換次數", "reward_id; points_used", "獎勵編號; 使用點數", "string; number", "RW-07; 150"],
  ["P1", "會員獎勵 / 任務", "會員任務參與率", "start_member_mission", "Click", "點擊「參加任務」時", "了解會員任務是否吸引使用者參與", "評估任務設計與獎勵是否需要調整", "參加任務會員數 ÷ 獎勵頁瀏覽會員數", "mission_id; mission_type", "任務編號; 任務類型", "string; string", "MS-03; weekly_visit"],
  ["P1", "會員獎勵 / 等級說明", "等級說明查看率", "view_tier_info", "Click", "點擊會員等級說明時", "了解會員是否理解升等規則", "若查看率高但升等率低，代表規則不夠清楚", "查看等級說明會員數 ÷ 獎勵頁瀏覽會員數", "member_tier", "會員等級", "string", "silver"],
  ["P1", "會員獎勵 / 禮品卡", "禮品卡入口點擊率", "click_gift_card", "Click", "點擊禮品卡入口時", "了解禮品卡是否有需求", "判斷禮品卡入口是否值得維持在獎勵頁", "點擊禮品卡會員數 ÷ 獎勵頁瀏覽會員數", "entry_position", "入口位置", "string", "rewards_top"],
  ["P2", "會員獎勵 / 點數紀錄", "點數紀錄查看率", "view_points_history", "Click", "點擊點數明細時", "觀察會員是否關注點數變動", "作為點數明細頁優化的參考", "查看點數紀錄會員數 ÷ 獎勵頁瀏覽會員數", "date_range", "查詢區間", "string", "last_30_days"],
  ["P2", "會員獎勵 / 兌換失敗", "兌換失敗率", "redeem_failed", "ErrorDropoff", "點數不足或兌換失敗時", "找出兌換流程中的阻礙", "若失敗率高，需要在兌換前提示點數需求", "兌換失敗次數 ÷ 點擊兌換次數", "reward_id; error_reason", "獎勵編號; 失敗原因", "string; string", "RW-07; insufficient_points"],
];

const ACCOUNT = "帳戶設定";
const account = [
  ["P0", "帳戶 / 登入", "登入完成率", "login_complete", "FlowComplete", "完成登入並回到原頁面時", "了解登入流程是否造成流失", "登入是下單前的必經步驟，缺少此資料無法判斷流失原因", "登入成功次數 ÷ 開始登入次數", "login_method", "登入方式", "string", "line"],
  ["P1", "帳戶 / 常用門市", "常用門市設定率", "set_favorite_store", "CreateEdit", "設定或變更常用門市時", "了解使用者是否需要固定的取餐門市", "作為首頁預設門市推薦的依據", "設定常用門市使用者數 ÷ 帳戶頁瀏覽使用者數", "store_id", "門市編號", "string", "S-012"],
  ["P1", "帳戶 / 推播設定", "推播關閉率", "disable_push", "CreateEdit", "關閉推播通知時", "觀察推播是否造成打擾", "若關閉率上升，需要調整推播頻率", "關閉推播使用者數 ÷ 帳戶頁瀏覽使用者數", "push_type", "推播類型", "string", "promotion"],
  ["P1", "帳戶 / 訂單紀錄", "訂單紀錄查看率", "view_order_history", "Click", "點擊歷史訂單時", "了解使用者是否常回顧訂單", "作為再買一次功能的需求參考", "查看訂單紀錄使用者數 ÷ 帳戶頁瀏覽使用者數", "order_count", "訂單數量", "number", "12"],
  ["P2", "帳戶 / 發票設定", "載具設定率", "set_invoice_carrier", "CreateEdit", "設定手機條碼載具時", "觀察使用者是否需要電子發票功能", "作為結帳流程簡化的參考", "設定載具使用者數 ÷ 帳戶頁瀏覽使用者數", "carrier_type", "載具類型", "string", "mobile_barcode"],
  ["P2", "帳戶 / 刪除帳號", "帳號刪除率", "delete_account", "ErrorDropoff", "完成刪除帳號流程時", "觀察使用者流失的極端狀況", "搭配刪除原因，找出產品問題", "刪除帳號使用者數 ÷ 活躍使用者數", "delete_reason", "刪除原因", "string", "too_many_notifications"],
];

const archive = [
  ["P2", "舊版設計 / 首頁", "舊版首頁瀏覽率", "view_legacy_home", "PageView", "進入舊版首頁時", "保留舊版設計的基準數據，作為改版前後比較", "改版後可用來比較新舊首頁的使用差異", "舊版首頁瀏覽使用者數 ÷ App 開啟使用者數", "app_version", "App 版本", "string", "3.2.1"],
  ["P2", "舊版設計 / 菜單", "舊版菜單點擊率", "click_legacy_menu", "Click", "點擊舊版菜單入口時", "保留改版前的菜單使用基準", "與新版菜單頁的使用率做比較", "舊版菜單點擊次數 ÷ 舊版首頁瀏覽次數", "app_version", "App 版本", "string", "3.2.1"],
];

const build = (prefix, pageLabel, rows) => rows.map((r, i) => row(prefix, i + 1, r[0], pageLabel, ...r.slice(1)));

const EVENTS = {
  "首頁 Home": build("HOME", HOME, home),
  "菜單與商品 Menu": build("MENU", MENU, menu),
  "購物車與結帳 Checkout": build("CHK", CHECKOUT, checkout),
  "會員獎勵 Rewards": build("RWD", REWARDS, rewards),
  "帳戶設定 Account": build("ACC", ACCOUNT, account),
  "Archive 舊版設計": build("ARC", "舊版設計", archive),
};

export function eventsForPage(pageName) {
  return EVENTS[pageName] ?? EVENTS["首頁 Home"];
}
