import frappe
from frappe import _
from frappe.utils import cstr
import json
from erpnext.controllers.item_variant import get_variant , generate_keyed_value_combinations , copy_attributes_to_variant

def make_variant_item_code(template_item_code, template_item_name, variant):
    """Build item code in fixed digit format based on attribute order and brand-based serial"""

    if variant.item_code:
        return
    attribute_order = {
        "Country": 2,
        "Brand": 2,
        "Family": 3,
        "Size": 2,
        "Colour": 2,
    }
    values = {}
    for attr in variant.attributes:
        if attr.attribute in attribute_order:
            item_attribute = frappe.db.sql(
                """
                SELECT i.numeric_values, v.abbr
                FROM `tabItem Attribute` i
                LEFT JOIN `tabItem Attribute Value` v ON (i.name = v.parent)
                WHERE i.name = %(attribute)s
                AND (v.attribute_value = %(attribute_value)s OR i.numeric_values = 1)
                """,
                {"attribute": attr.attribute, "attribute_value": attr.attribute_value},
                as_dict=True,
            )

            if not item_attribute:
                frappe.throw(_("Missing abbreviation or value for attribute: {0}").format(attr.attribute))

            if item_attribute[0].numeric_values:
                values[attr.attribute] = cstr(attr.attribute_value)
            else:
                values[attr.attribute] = item_attribute[0].abbr
    if "Brand" not in values:
        brand = frappe.db.get_value("Item", template_item_code, "brand")
        if not brand:
            frappe.throw(_("Brand is not set for the template item: {0}").format(template_item_code))
        values["Brand"] = brand
    missing = [k for k in attribute_order if k not in values]
    if missing:
        frappe.throw(_("Missing required attributes: {0}").format(", ".join(missing)))
    serial = get_next_serial_for_item(values["Family"])
    values["Serial"] = str(serial).zfill(3)
    code_parts = list()
    
    for attr in ["Country", "Brand", "Family", "Size", "Colour", "Serial"]:
        val = values[attr]
        length = attribute_order.get(attr, 3) if attr != "Serial" else 3
        part = val[:length].upper()
        code_parts.append(part)
    item_code_str = "-".join(code_parts)
    variant.item_code = item_code_str
    variant.item_name = "{}-{}".format(template_item_name, item_code_str)


def get_next_serial_for_item(brand_abbr):
    """
    Get the next serial number for items under the same brand.
    This assumes the brand abbreviation is part of the item code in a fixed position.
    """
    like_pattern = f"%{brand_abbr}%"
    last_code = frappe.db.sql(
        """
        SELECT item_code FROM `tabItem`
        WHERE item_code LIKE %s
        AND item_code LIKE %s
        ORDER BY creation DESC LIMIT 1
        """, (like_pattern, f"%{brand_abbr}%"),
        as_dict=True
    )

    if last_code:
        last_serial = last_code[0]['item_code'][-3:]
        try:
            return int(last_serial) + 1
        except ValueError:
            return 1
    return 1

@frappe.whitelist()
def enqueue_multiple_variant_creation(item, args, use_template_image=False):
	use_template_image = frappe.parse_json(use_template_image)
	# #There can be innumerable attribute combinations, enqueue
	if isinstance(args, str):
		variants = json.loads(args)
	total_variants = 1
	for key in variants:
		total_variants *= len(variants[key])
	if total_variants >= 600:
		frappe.throw(_("Please do not create more than 500 items at a time"))
		return
	if total_variants < 10:
		return create_multiple_variants(item, args, use_template_image)
	else:
		frappe.enqueue(
			"masar_royal_gas.override.item.create_multiple_variants",
			item=item,
			args=args,
			use_template_image=use_template_image,
			now=frappe.flags.in_test,
		)
		return "queued"


def create_multiple_variants(item, args, use_template_image=False):
	count = 0
	if isinstance(args, str):
		args = json.loads(args)

	template_item = frappe.get_doc("Item", item)
	args_set = generate_keyed_value_combinations(args)

	for attribute_values in args_set:
		if not get_variant(item, args=attribute_values):
			variant = create_variant(item, attribute_values)
			if use_template_image and template_item.image:
				variant.image = template_item.image
			variant.save()
			count += 1

	return count



@frappe.whitelist()
def create_variant(item, args, use_template_image=False):
	use_template_image = frappe.parse_json(use_template_image)
	if isinstance(args, str):
		args = json.loads(args)

	template = frappe.get_doc("Item", item)
	variant = frappe.new_doc("Item")
	variant.variant_based_on = "Item Attribute"
	variant_attributes = []

	for d in template.attributes:
		variant_attributes.append({"attribute": d.attribute, "attribute_value": args.get(d.attribute)})

	variant.set("attributes", variant_attributes)
	copy_attributes_to_variant(template, variant)

	if use_template_image and template.image:
		variant.image = template.image

	make_variant_item_code(template.item_code, template.item_name, variant)

	return variant