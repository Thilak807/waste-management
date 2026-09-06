"""
Recycling recommendation module.

Kept separate from the YOLO model so recommendations can be updated
without retraining. Extend RECOMMENDATIONS when adding new classes.
"""

from __future__ import annotations

from typing import Dict, Optional, Any

# Default guidance and upcycling ideas per waste class (admin can override via database)
DEFAULT_RECOMMENDATIONS: Dict[str, Dict[str, Any]] = {
    "plastic": {
        "category": "Recyclable – Plastic",
        "current_use": "Extensively manufactured into single-use water & soda bottles, food takeaway tubs, detergent jugs, flexible wrappers, and cosmetic dispensers due to its lightweight moisture-barrier properties.",
        "recommendation": (
            "Place clean plastic items in the appropriate recycling bin. "
            "Rinse containers, remove caps if required by local rules, and "
            "avoid putting soft films or contaminated plastic in the recycling stream."
        ),
        "disposal_tips": (
            "Do not burn plastic. Soft plastic bags often go to store take-back "
            "programs rather than curbside bins."
        ),
        "what_can_be_made": [
            {
                "title": "Eco-Friendly Apparel & Polyester Fabrics",
                "icon": "👕",
                "badge": "Fashion & Textiles",
                "description": "PET bottles are washed, shredded into flakes, melted, and spun into soft polyester fibers used in athletic jerseys, fleece jackets, and stylish backpacks.",
            },
            {
                "title": "Self-Watering Garden Planters",
                "icon": "🪴",
                "badge": "Home & Garden",
                "description": "Rigid bottles and containers are easily repurposed into durable self-watering plant pots, nursery seed-starter trays, and vertical herb gardens.",
            },
            {
                "title": "Composite Plastic Lumber & Park Benches",
                "icon": "🪵",
                "badge": "Infrastructure",
                "description": "High-density polymers (HDPE) are compounded and extruded into rot-proof, weatherproof composite lumber used for park benches, decks, and fences.",
            },
            {
                "title": "3D Printer Filament (rPET)",
                "icon": "🧵",
                "badge": "Prototyping & Tech",
                "description": "Clear plastic waste can be processed into precision 1.75mm recycled filament for 3D printing custom mechanical parts, robotics casings, and educational models.",
            },
            {
                "title": "Interlocking Eco-Bricks & Pavers",
                "icon": "🧱",
                "badge": "Eco-Construction",
                "description": "Compressed plastic polymers mixed with mineral aggregates form ultra-durable, waterproof interlocking pavement bricks, road curbing, and walkway tiles.",
            },
            {
                "title": "Heavy-Duty Backpacks & Tote Bags",
                "icon": "🎒",
                "badge": "Lifestyle & Gear",
                "description": "Recycled polymer strands are woven into tough, tear-resistant waterproof fabrics for school backpacks, laptop sleeves, and reusable tote bags.",
            },
        ],
    },
    "paper": {
        "category": "Recyclable – Paper",
        "current_use": "Heavily utilized across universities, offices, and printing presses for textbooks, newspapers, exam sheets, notebook stationery, parcel inserts, and shopping bags.",
        "recommendation": (
            "Keep paper dry and place it in the paper recycling collection. "
            "Remove plastic sleeves, binders, and food-stained paper before recycling."
        ),
        "disposal_tips": (
            "Shredded paper may need a paper bag. Greasy pizza boxes usually "
            "belong in compost or general waste, not paper recycling."
        ),
        "what_can_be_made": [
            {
                "title": "Recycled Spiral Notebooks & Journals",
                "icon": "📓",
                "badge": "Stationery & School",
                "description": "De-inked post-consumer paper fibers are re-pulped and pressed into smooth eco-friendly lined notebooks, artist sketchpads, and office stationery.",
            },
            {
                "title": "Plantable Seed Paper Sheets",
                "icon": "🌱",
                "badge": "Botanical Crafts",
                "description": "Handmade recycled paper infused with wildflower, lavender, or basil seeds. After writing or greeting card use, simply plant in soil and water to grow blooms!",
            },
            {
                "title": "Molded Fiber Egg Cartons & Protective Packaging",
                "icon": "🥚",
                "badge": "Eco-Packaging",
                "description": "Molded paper pulp slurry is pressed into shock-absorbing egg trays, fruit cradles, and cushioning corners that replace styrofoam in electronics shipping.",
            },
            {
                "title": "Sturdy Kraft Shopping Bags & Envelopes",
                "icon": "🛍️",
                "badge": "Retail & Mailing",
                "description": "Long recycled cellulose fibers produce durable, high-tensile brown kraft retail carry bags, shipping envelopes, and gift wraps.",
            },
            {
                "title": "Artisanal Paper-Mache Decor & Lampshades",
                "icon": "🎨",
                "badge": "Home Decor & Art",
                "description": "Shredded paper mixed with non-toxic organic pastes creates lightweight sculptural pendant lampshades, decorative bowls, and festive masks.",
            },
            {
                "title": "Biodegradable Pet Pellets & Thermal Wall Insulation",
                "icon": "🏠",
                "badge": "Pet Care & Building",
                "description": "Clean paper waste compressed into ultra-absorbent, odor-absorbing pet litter pellets and fire-retardant cellulose insulation for energy-efficient homes.",
            },
        ],
    },
    "cardboard": {
        "category": "Recyclable – Cardboard & Packaging",
        "current_use": "The backbone of e-commerce delivery and warehouse logistics, used universally for corrugated mailing boxes, heavy-duty shipping cartons, and retail product packaging.",
        "recommendation": (
            "Flatten all cardboard boxes to save space. Remove heavy packaging tape and plastic wrapping before recycling."
        ),
        "disposal_tips": (
            "Keep cardboard dry. Contaminated cardboard with heavy food or oil grease should go into general waste or compost."
        ),
        "what_can_be_made": [
            {
                "title": "100% Recycled Corrugated Shipping Boxes",
                "icon": "📦",
                "badge": "Logistics & Shipping",
                "description": "Repulped kraft fluting forms heavy-duty, impact-resistant corrugated shipping boxes used by post offices and e-commerce companies.",
            },
            {
                "title": "Cat Scratching Loungers & Pet Furniture",
                "icon": "🐱",
                "badge": "Pet Products",
                "description": "Densely layered corrugated honeycomb textures provide irresistible, durable scratching surfaces, cozy feline cat-caves, and climbing castles.",
            },
            {
                "title": "Modular Desktop Organizers & File Folders",
                "icon": "🗄️",
                "badge": "Office & Workspace",
                "description": "Laser-cut or scored heavy cardboard folds into sleek desktop pencil caddies, drawer dividers, magazine holders, and document organizers.",
            },
            {
                "title": "Organic Sheet Mulch for Gardens",
                "icon": "🌾",
                "badge": "Gardening & Agriculture",
                "description": "Unprinted brown cardboard laid under garden topsoil smothers pesky weeds, locks in ground moisture, and decomposes into rich worm-friendly humus.",
            },
            {
                "title": "Pop-Up Architectural Stools & Exhibition Furniture",
                "icon": "🪑",
                "badge": "Industrial Design",
                "description": "Engineered multi-fold cardboard geometry can support over 150 kg, creating featherlight portable stools, event pedestals, and pop-up store displays.",
            },
        ],
    },
    "glass": {
        "category": "Recyclable – Glass",
        "current_use": "Universally chosen for impermeable, sterile, and non-reactive storage of soda and juice bottles, wine bottles, food jars, cosmetic vessels, and pharmaceutical vials.",
        "recommendation": (
            "Separate glass from general waste and send it to a glass recycling "
            "facility. Empty and rinse bottles and jars; remove lids if needed."
        ),
        "disposal_tips": (
            "Broken glass should be wrapped safely. Ceramics, mirrors, and "
            "light bulbs are often not accepted with bottle glass."
        ),
        "what_can_be_made": [
            {
                "title": "Brand New Bottles & Food Jars",
                "icon": "🍾",
                "badge": "Zero-Loss Recycling",
                "description": "Glass is 100% and infinitely recyclable with zero loss in purity. Recycled cullet melts at lower furnace temperatures, saving huge energy to produce fresh bottles.",
            },
            {
                "title": "Polished Terrazzo Countertops & Mosaic Tiles",
                "icon": "🧱",
                "badge": "Interior Architecture",
                "description": "Tumbled, smooth colored glass chips embedded in cast concrete or clear resin create luxurious, sparkling kitchen countertops, vanity surfaces, and wall tiles.",
            },
            {
                "title": "Fiberglass Thermal & Acoustic Home Insulation",
                "icon": "🏠",
                "badge": "Green Construction",
                "description": "Molten recycled glass is spun into fine thermal fiberglass batting that lines building walls and ceilings to drastically slash heating and cooling bills.",
            },
            {
                "title": "Reflective Eco-Glassphalt Road Paving",
                "icon": "🛣️",
                "badge": "Civil Engineering",
                "description": "Pulverized glass granules replace natural quarry sand in asphalt pavement, delivering superior water drainage, higher skid resistance, and road reflectivity.",
            },
            {
                "title": "Upcycled Scented Candle Vessels & Drinkware",
                "icon": "🕯️",
                "badge": "Handmade Craft",
                "description": "Neatly cut, diamond-sanded, and flame-polished wine and soda bottles convert into premium scented soy candle vessels, beverage tumblers, and vase planters.",
            },
        ],
    },
    "metal": {
        "category": "Recyclable – Metal & E-Waste",
        "current_use": "Widely deployed for carbonated soda and energy drink cans, preserved food tins, aerosol cans, cooking foil, electronics casings, and electrical wiring.",
        "recommendation": (
            "Place recyclable metal containers in the metal recycling collection. "
            "Rinse cans and crush them if space is limited. Deposit electronic items in e-waste bins."
        ),
        "disposal_tips": (
            "Aerosol cans must be empty. Scrap metal, wiring, and batteries belong in designated hazardous/e-waste hubs."
        ),
        "what_can_be_made": [
            {
                "title": "Fresh Aluminum Cans (Back on Shelves in 60 Days)",
                "icon": "🥫",
                "badge": "Closed-Loop Miracle",
                "description": "Recycling aluminum requires 95% less energy than mining raw bauxite. A tossed soda can can be remelted, rolled, printed, filled, and back on a store shelf in 60 days!",
            },
            {
                "title": "High-Performance Bicycle Frames & Wheel Rims",
                "icon": "🚲",
                "badge": "Mobility & Sports",
                "description": "Structural-grade recycled aluminum and steel alloys are extruded and welded into lightweight bicycle frames, scooter decks, and automotive heat shields.",
            },
            {
                "title": "Hardware Tools & Precision Fasteners",
                "icon": "🔧",
                "badge": "Tools & Engineering",
                "description": "Recycled steel scrap is forged into durable wrenches, structural rebar for construction, bolts, shelf brackets, and heavy-duty machinery parts.",
            },
            {
                "title": "Melodic Garden Wind Chimes & Metal Wall Art",
                "icon": "🔔",
                "badge": "Outdoor Living",
                "description": "Cut aluminum tubes, bottle caps, and brass gears tuned and polished to produce soothing acoustic garden wind chimes and modern industrial wall art.",
            },
            {
                "title": "Non-Stick Cookware & Baking Sheets",
                "icon": "🍳",
                "badge": "Kitchen & Culinary",
                "description": "Purified aluminum alloy castings produce even-heating frying pans, saucepans, and commercial baking trays for culinary kitchens.",
            },
        ],
    },
    "organic": {
        "category": "Compostable – Organic & Food Waste",
        "current_use": "Generated daily from canteen meal preparation, food scraps, fruit and vegetable peels, tea bags, coffee grounds, and discarded garden clippings.",
        "recommendation": (
            "Place fruit peels, food leftovers, vegetable waste, and coffee grounds into the green organic compost bin."
        ),
        "disposal_tips": (
            "Do not mix plastic wrappers or cutlery with organic waste. Use biodegradable bags where permitted."
        ),
        "what_can_be_made": [
            {
                "title": "Nutrient-Dense Living Garden Compost",
                "icon": "🌱",
                "badge": "Organic Farming",
                "description": "Aerobic decomposition transforms discarded produce and peels into dark, rich humus that restores soil vitality, nourishes plants, and retains natural moisture.",
            },
            {
                "title": "Renewable Biogas Energy for Cooking & Power",
                "icon": "⚡",
                "badge": "Clean Energy",
                "description": "Anaerobic bio-digesters break down food scraps to produce methane-rich biogas, supplying clean cooking gas and fueling micro-generators for electricity.",
            },
            {
                "title": "Microbial Liquid Bio-Fertilizer (Compost Tea)",
                "icon": "🧃",
                "badge": "Plant Nutrition",
                "description": "Brewed liquid fertilizer loaded with beneficial aerobic bacteria, enzymes, and trace minerals that strengthen plant immunity against pests and fungi.",
            },
            {
                "title": "Nutritional Livestock & Poultry Feed",
                "icon": "🍲",
                "badge": "Sustainable Agriculture",
                "description": "Dehydrated, sterilized organic fruit and grain discards are processed into safe, high-protein supplemental feed pellets for farm animals.",
            },
        ],
    },
    "other": {
        "category": "General / Non-Recyclable Waste",
        "current_use": "Found in multi-layer metallized chip sachets, composite coffee cups, thermal receipts, and blended synthetic wrappers with inseparable material layers.",
        "recommendation": (
            "Place non-recyclable multi-layer packaging, sanitary items, and mixed household trash into the general waste bin."
        ),
        "disposal_tips": (
            "Ensure no hazardous materials or lithium batteries are discarded in general waste."
        ),
        "what_can_be_made": [
            {
                "title": "Refuse-Derived Fuel (RDF) Pellets",
                "icon": "🏭",
                "badge": "Waste-to-Energy",
                "description": "High-calorific mixed non-recyclable wastes are shredded, dehydrated, and compressed into RDF fuel pellets that replace coal in industrial cement kilns.",
            },
            {
                "title": "Polymer-Modified Asphalt Road Additive",
                "icon": "🛣️",
                "badge": "Road Construction",
                "description": "Shredded multi-layer packaging is blended with molten bitumen to enhance road elasticity, preventing potholes and extending road lifespan by years.",
            },
            {
                "title": "Composite Construction Sound Barrier Panels",
                "icon": "🧱",
                "badge": "Infrastructure",
                "description": "Mixed composite scrap is heat-fused under heavy pressure into dense acoustic insulation barriers for highways and industrial construction sites.",
            },
        ],
    },
    "trash": {
        "category": "General Waste",
        "current_use": "Single-use mixed packaging, soiled paper towels, contaminated hygiene products, and unrecyclable municipal debris.",
        "recommendation": (
            "Place general non-recyclable waste in the municipal sorting bin."
        ),
        "disposal_tips": (
            "Separate recyclables whenever possible before disposal."
        ),
        "what_can_be_made": [
            {
                "title": "Refuse-Derived Clean Thermal Energy",
                "icon": "⚡",
                "badge": "Waste-to-Energy",
                "description": "Modern waste-to-energy conversion plants incinerate sorted residual municipal waste under controlled filters to generate community electrical power.",
            },
            {
                "title": "Composite Paving Sub-Base Aggregate",
                "icon": "🏗️",
                "badge": "Civil Works",
                "description": "Inert treated bottom ash from municipal processing is transformed into certified aggregate foundation material for roads and construction sub-bases.",
            },
        ],
    },
}


MATERIAL_GUIDE: Dict[str, Dict[str, str]] = {
    "plastic": {
        "segregation_bin": "Plastic / Dry Waste Bin",
        "recycling_method": "Rinse PET bottles, remove residual liquid, and deposit in the plastic stream or reverse vending machine. Material is shredded into flakes and spun into polyester fibre.",
        "future_summary": "Clothes, bags, furniture, construction materials",
        "smart_action": "Deposit in vending machine → Receive reward",
    },
    "paper": {
        "segregation_bin": "Paper Recycling Bin",
        "recycling_method": "Keep dry, remove plastic covers, and place in the paper stream. Fibres are de-inked and re-pulped into new stationery.",
        "future_summary": "Notebooks, packaging, insulation, seed paper",
        "smart_action": "Place in paper hub → Track campus diversion",
    },
    "cardboard": {
        "segregation_bin": "Cardboard / Packaging Bin",
        "recycling_method": "Flatten boxes, strip heavy tape, and keep dry. Corrugated fibre is re-pulped into new cartons and organisers.",
        "future_summary": "Shipping boxes, pet furniture, garden mulch",
        "smart_action": "Drop at packaging station → Reduce landfill load",
    },
    "glass": {
        "segregation_bin": "Glass Recycling Bin",
        "recycling_method": "Rinse bottles and jars; keep ceramics out of the stream. Cullet is melted and recast with no quality loss.",
        "future_summary": "New bottles, tiles, insulation, road aggregate",
        "smart_action": "Glass depot drop-off → Closed-loop recycling",
    },
    "metal": {
        "segregation_bin": "Metal / Can Recycling Bin",
        "recycling_method": "Rinse and crush cans. Aluminium is remelted with ~95% energy savings versus virgin ore.",
        "future_summary": "New cans, bicycle frames, tools, cookware",
        "smart_action": "Insert cans in vending machine → Cash or points",
    },
    "organic": {
        "segregation_bin": "Organic / Wet Waste Bin",
        "recycling_method": "Keep plastics out. Food scraps are composted or digested into biogas and soil amendment.",
        "future_summary": "Compost, biogas, bio-fertiliser",
        "smart_action": "Cafeteria compost station → Campus garden reuse",
    },
    "other": {
        "segregation_bin": "General Waste / Sorting Bin",
        "recycling_method": "Send mixed residuals to the sorting station. Recoverable fractions are diverted; remainder may become RDF.",
        "future_summary": "RDF pellets, road additive, barrier panels",
        "smart_action": "Main-gate sorting → Residual recovery",
    },
    "trash": {
        "segregation_bin": "General Waste Bin",
        "recycling_method": "Separate recyclables first. Residual waste goes to municipal processing.",
        "future_summary": "Energy recovery, construction aggregate",
        "smart_action": "Municipal bin → Residual processing",
    },
}


def get_recommendation(class_name: str, custom_map: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Map a predicted waste class to recycling guidance and what can be made from it.

    Args:
        class_name: Predicted class (e.g. 'plastic').
        custom_map: Optional override dictionary from the database.

    Returns:
        Dict with keys: category, current_use, recommendation, disposal_tips, what_can_be_made.
    """
    key = (class_name or "").strip().lower()

    # Look up in custom overrides, fallback to default catalogue
    entry = None
    if custom_map and key in custom_map:
        entry = custom_map[key]
    elif key in DEFAULT_RECOMMENDATIONS:
        entry = DEFAULT_RECOMMENDATIONS[key]

    guide = MATERIAL_GUIDE.get(key, MATERIAL_GUIDE["other"])

    if entry:
        default_entry = DEFAULT_RECOMMENDATIONS.get(key, {})
        return {
            "class_name": key,
            "category": entry.get("category") or default_entry.get("category", f"Recyclable – {key.title()}"),
            "current_use": entry.get("current_use") or default_entry.get("current_use", "Widely used in everyday commercial and consumer packaging."),
            "recommendation": entry.get("recommendation") or default_entry.get("recommendation", "Follow local recycling guidelines."),
            "disposal_tips": entry.get("disposal_tips") or default_entry.get("disposal_tips", ""),
            "what_can_be_made": entry.get("what_can_be_made") or default_entry.get("what_can_be_made", []),
            "segregation_bin": entry.get("segregation_bin") or guide["segregation_bin"],
            "recycling_method": entry.get("recycling_method") or guide["recycling_method"],
            "future_summary": entry.get("future_summary") or guide["future_summary"],
            "smart_action": entry.get("smart_action") or guide["smart_action"],
        }

    return {
        "class_name": key or "unknown",
        "category": "Unknown / General Waste",
        "current_use": "Mixed or unrecognized everyday waste item.",
        "recommendation": (
            "Class not recognized in the recommendation database. "
            "Dispose according to local municipal waste rules."
        ),
        "disposal_tips": "Contact your local recycling center for guidance.",
        "what_can_be_made": DEFAULT_RECOMMENDATIONS.get("other", {}).get("what_can_be_made", []),
        "segregation_bin": guide["segregation_bin"],
        "recycling_method": guide["recycling_method"],
        "future_summary": guide["future_summary"],
        "smart_action": guide["smart_action"],
    }


def list_all_recommendations(custom_map: Optional[Dict] = None) -> Dict[str, Dict[str, Any]]:
    """Return all recommendations (defaults merged with optional custom overrides)."""
    merged = {k: dict(v) for k, v in DEFAULT_RECOMMENDATIONS.items()}
    if custom_map:
        for k, v in custom_map.items():
            merged[k] = {**merged.get(k, {}), **v}
    return merged

