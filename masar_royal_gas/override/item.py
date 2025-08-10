import frappe
from frappe import _, scrub
from frappe.model.document import Document

class _Item(Document):
    def autoname(self):
        if self.variant_of:
            self.name = self.item_code
            return
        if self.has_variants:
            self.name = self.item_code
            return
        # if self.item_code:
        #     self.name = self.item_code
            
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
        self.item_code = "-".join(group_abbrs).upper().strip()
        self.item_name = "-".join(group_abbrs).upper().strip()
        self.name = "-".join(group_abbrs).upper().strip()

        frappe.msgprint(f"Item code and name automatically set to: <b>{self.item_code}</b>" , alert = True)
