import os
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    MessagingApiBlob,
    RichMenuRequest,
    RichMenuArea,
    RichMenuBounds,
    RichMenuSize,
    PostbackAction,
    MessageAction,
    URIAction, 
    RichMenuSwitchAction,
    CreateRichMenuAliasRequest
)
from dotenv import load_dotenv

# 1. 載入環境變數
load_dotenv()

# 💡 修正處：將 CHANNEL_ACCESS_TOKEN 更改為我們稍早統一的 LINE_TOKEN
line_token = os.getenv('LINE_TOKEN')
liff_id = os.getenv('LIFF_ID')
IG_LIFF_URL = f"https://liff.line.me/{liff_id}" 

# 2. 設定 v3 API Client
# 💡 修正處：將傳入的參數改為 line_token
configuration = Configuration(access_token=line_token)
api_client = ApiClient(configuration)
messaging_api = MessagingApi(api_client)
blob_api = MessagingApiBlob(api_client)

def reset_alias(alias_id, rich_menu_id):
    """
    刪除舊 Alias 並建立新 Alias (v3 寫法)
    """
    try:
        messaging_api.delete_rich_menu_alias(alias_id)
        print(f"🗑️ 舊的 Alias '{alias_id}' 已刪除")
    except Exception:
        pass 

    try:
        alias_request = CreateRichMenuAliasRequest(
            rich_menu_alias_id=alias_id,
            rich_menu_id=rich_menu_id
        )
        messaging_api.create_rich_menu_alias(alias_request)
        print(f"✅ Alias '{alias_id}' 綁定成功")
    except Exception as e:
        print(f"❌ Alias 綁定失敗: {e}")

def create_menus():
    # ==========================================
    # 建立 Menu A (主選單) - 依照你提供的新版型
    # ==========================================
    rich_menu_a_req = RichMenuRequest(
        size=RichMenuSize(width=2500, height=1686),
        selected=True,
        name="圖文選單 1",
        chat_bar_text="查看更多資訊",
        areas=[
            RichMenuArea(
                bounds=RichMenuBounds(x=160, y=156, width=414, height=414),
                action=MessageAction(label='關於我們', text='關於我們')
            ),
            RichMenuArea(
                bounds=RichMenuBounds(x=351, y=638, width=418, height=409),
                action=MessageAction(label='服務內容', text='服務內容')
            ),
            RichMenuArea(
                bounds=RichMenuBounds(x=173, y=1132, width=393, height=392),
                action=MessageAction(label='作品集', text='作品集')
            ),
            RichMenuArea(
                bounds=RichMenuBounds(x=1917, y=156, width=431, height=410),
                action=MessageAction(label='合作專案', text='合作專案')
            ),
            RichMenuArea(
                bounds=RichMenuBounds(x=1715, y=650, width=439, height=397),
                action=MessageAction(label='常見問題', text='常見問題')
            ),
            RichMenuArea(
                bounds=RichMenuBounds(x=1926, y=1140, width=414, height=380),
                action=MessageAction(label='優惠與活動', text='優惠與活動')
            )
        ]
    )
    
    menu_a_id = messaging_api.create_rich_menu(rich_menu_request=rich_menu_a_req).rich_menu_id
    print(f"Menu A ID: {menu_a_id}")

    print("正在上傳 Menu A 圖片...")
    with open("rich_menu/menu_a.jpg", 'rb') as f:
        image_data = f.read()
        blob_api.set_rich_menu_image(
            rich_menu_id=menu_a_id,
            body=image_data,
            _headers={'Content-Type': 'image/jpeg'}
        )

    # ==========================================
    # 建立 Menu B (次選單)
    # ==========================================
    rich_menu_b_req = RichMenuRequest(
        size=RichMenuSize(width=2500, height=1686),
        selected=False,
        name="圖文選單 2 (Sub)",
        chat_bar_text="查看更多資訊",
        areas=[
            # 1. 切換按鈕 -> 切換到 menu_a
            RichMenuArea(
                bounds=RichMenuBounds(x=25, y=17, width=1187, height=347),
                action=RichMenuSwitchAction(
                    rich_menu_alias_id="menu_a", 
                    data="switch_to_a",
                    label="切換至 Menu A"
                )
            ),
            # 2. Price List
            RichMenuArea(
                bounds=RichMenuBounds(x=284, y=436, width=614, height=594),
                action=MessageAction(label='Price List', text='price list')
            ),
            # 3. Work
            RichMenuArea(
                bounds=RichMenuBounds(x=946, y=1043, width=614, height=594),
                action=MessageAction(label='Work', text='work')
            ),
            # 4. Q&A
            RichMenuArea(
                bounds=RichMenuBounds(x=1728, y=693, width=614, height=594),
                action=MessageAction(label='Q&A', text='Q&A')
            )
        ]
    )

    menu_b_id = messaging_api.create_rich_menu(rich_menu_request=rich_menu_b_req).rich_menu_id
    print(f"Menu B ID: {menu_b_id}")

    print("正在上傳 Menu B 圖片...")
    with open("rich_menu/menu_b.jpg", 'rb') as f:
        image_data = f.read()
        blob_api.set_rich_menu_image(
            rich_menu_id=menu_b_id,
            body=image_data,
            _headers={'Content-Type': 'image/jpeg'}
        )

    return menu_a_id, menu_b_id

if __name__ == "__main__":
    try:
        print("開始設定選單 (v3 版本)...")
        id_a, id_b = create_menus()
        
        reset_alias("menu_a", id_a)
        reset_alias("menu_b", id_b)
        
        messaging_api.set_default_rich_menu(id_a)
        
        print("\n🎉 全部完成！請在手機上測試選單切換。")
        
    except Exception as e:
        print(f"\n❌ 發生錯誤: {e}")