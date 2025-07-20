import frappe
from frappe import _, scrub
from frappe.model.document import Document

class _Item(Document):
    def autoname(self):
        # Only apply to base items (not variant, not template)
        if self.variant_of:
            # frappe.msgprint("Skipping: This item is a variant.")
            return

        if self.has_variants:
            frappe.msgprint("Skipping: This item is a template (has variants).")
            return

        # Skip if item_code already exists
        if self.item_code:
            frappe.msgprint("Skipping: item_code already set.")
            return

        # Build list of item group hierarchy
        item_groups = []
        current_group = self.item_group
        while current_group:
            if current_group != 'All Item Groups':
                item_groups.insert(0, current_group)
            current_group = frappe.db.get_value("Item Group", current_group, "parent_item_group")
        
        # Get abbreviations from each group
        group_abbrs = []
        for group in item_groups:
            abbr = frappe.db.get_value("Item Group", group, "custom_abbr")
            if not abbr:
                frappe.throw(_("Abbreviation missing for Item Group: {}").format(group))
            group_abbrs.append(abbr)

        # Set item_code from abbreviations
        self.item_code = "-".join(group_abbrs).upper().strip()
        self.item_name = self.item_code
        self.name = self.item_code

        frappe.msgprint(f"Item code and name automatically set to: <b>{self.item_code}</b>")
