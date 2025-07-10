
import frappe 

def validate(self , method):
    validate_item_group(self)
def validate_item_group(self):
    """
    Validate the item group to ensure it is not 'All Item Groups'.
    """
    if self.parent_item_group != "All Item Groups" or self.name != "All Item Groups":
        prent_fg = frappe.db.get_value("Item Group", self.parent_item_group, "custom_is_finish_goods")
        if self.custom_is_finish_goods != prent_fg:
            frappe.throw(
                ("Custom Finish Goods status for Item Group {0} must match its parent group {1}.").format(
                    self.name, self.parent_item_group
                )
            )
        
        