import frappe
from frappe import _, scrub
from erpnext.stock.doctype.item.item import Item as ERPNextItem

class Item(ERPNextItem):
    def autoname(self):
        # Skip if it's a variant or has variants
        # if self.variant_of or self.has_variants:
        #     frappe.msgprint("Skipping item_code generation: This item is a variant or has variants.")
        #     return
        if self.item_code:
            frappe.msgprint("Skipping item_code generation: item_code already set.")
            return
        
        item_groups = []
        current_group = self.item_group
        while current_group:
            if current_group != 'All Item Groups':
                item_groups.insert(0, current_group)
            current_group = frappe.db.get_value("Item Group", current_group, "parent_item_group")
            
        group_abbrs = []
        for group in item_groups:
            abbr = frappe.db.get_value("Item Group", group, "custom_abbr")
            if not abbr:
                frappe.throw(_("Abbreviation missing for Item Group: {}").format(group))
            group_abbrs.append(abbr)

        self.item_code = "-".join(group_abbrs).upper()
        frappe.msgprint(f"Item code automatically set to: <b>{self.item_code}</b>")

        self.item_code = self.item_code.strip()
        self.name = self.item_code
