from .inventory import ItemInventory

class Shop:
    def __init__(self, json_data):
        items = []
        for shop_item in json_data['items']:
            items.append(ItemInventory(shop_item))
        self.shop_id: str = str(json_data['ShopID'])
        self.shop_name: str = json_data['sName']
        self.items: list[ItemInventory] = items
        self.is_member: bool = json_data['bUpgrd'] == "1"
        
    def get_item(self, item_name: str):
        for item in self.items:
            if item.item_name == item_name:
                return item
        return None

# class ShopItem:
#     def __init__(self, json_data):
#         self.item_id: str = str(json_data['ItemID'])
#         self.shop_item_id: str = str(json_data['ShopItemID'])
#         self.item_name: str = json_data['sName']
#         self.cost: int = json_data['iCost']
#         self.is_acs: bool = str(json_data['bCoins']) == "1"