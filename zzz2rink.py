import json
import re
import os
import sys

def convert_enemy(src):
    dest = {}
    
    # Basic mappings
    dest["name"] = src.get("名称", "")
    dest["rank"] = src.get("位阶", "")
    dest["type"] = src.get("种类", "")
    dest["description"] = src.get("简介", "")
    dest["motivation"] = src.get("动机与战术", "")
    dest["difficulty"] = src.get("难度", "")
    
    # Threshold combination
    heavy = src.get("重度伤害阈值", "")
    severe = src.get("严重伤害阈值", "")
    dest["threshold"] = f"{heavy}/{severe}"
    
    dest["health"] = src.get("生命点", "")
    dest["stress"] = src.get("压力点", "")
    
    # Attack Bonus cleanup
    attack_bonus = src.get("攻击命中", "")
    if attack_bonus and attack_bonus.startswith("+"):
        attack_bonus = attack_bonus[1:]
    dest["attackBonus"] = attack_bonus
    
    dest["weaponName"] = src.get("攻击武器", "")
    dest["weaponRange"] = src.get("攻击范围", "")
    dest["damageDice"] = src.get("攻击伤害", "")
    dest["damageType"] = src.get("攻击属性", "")
    
    # Default styling
    dest["decoratorColor"] = "#8a1c1c"
    dest["highlightBgColor"] = "#852020"
    dest["highlightTextColor"] = "#ffffff"
    dest["isNPC"] = False
    dest["imageSrc"] = "about:blank"
    dest["imageTransform"] = ""
    dest["imageSettings"] = {
        "width": "150",
        "height": "150",
        "shape": "circle",
        "hideBorder": False
    }
    
    # Experiences list
    experiences_str = src.get("经历", "")
    if experiences_str:
        # Split by Chinese comma or English comma
        experiences = re.split(r'[，,]', experiences_str)
        dest["experiences"] = [e.strip() for e in experiences if e.strip()]
    else:
        dest["experiences"] = []
        
    # Traits
    dest["traits"] = []
    for trait in src.get("特性", []):
        new_trait = {}
        new_trait["name"] = trait.get("名称", "")
        
        t_type = trait.get("类型", "")
        t_desc = trait.get("特性描述", "")
        if t_type:
            new_trait["desc"] = f"{t_type}：{t_desc}"
        else:
            new_trait["desc"] = t_desc
            
        new_trait["flavor"] = ""
        dest["traits"].append(new_trait)
        
    dest["specialTraits"] = []
    
    return dest

def convert_environment(src):
    dest = {}
    
    dest["name"] = src.get("名称", "")
    dest["nameEn"] = src.get("原文", "")
    dest["rank"] = src.get("位阶", "")
    dest["type"] = src.get("种类", "")
    dest["description"] = src.get("简介", "")
    dest["tendencies"] = src.get("趋向", "")
    dest["difficulty"] = src.get("难度", "")
    dest["enemies"] = src.get("潜在敌人", "")
    
    # Default styling for environments
    dest["decoratorColor"] = "#1c538a"
    dest["highlightBgColor"] = "#852020"
    dest["highlightTextColor"] = "#ffffff"
    dest["imageSettings"] = {
        "src": "",
        "width": "350",
        "height": "200",
        "transform": "",
        "hideBorder": False
    }

    # Traits
    dest["traits"] = []
    for trait in src.get("特性", []):
        new_trait = {}
        # Name + En Name
        trait_name = trait.get("名称", "")
        trait_en = trait.get("原名", "")
        if trait_en:
            new_trait["name"] = f"{trait_name} {trait_en}"
        else:
            new_trait["name"] = trait_name
            
        new_trait["type"] = trait.get("类型", "")
        
        # Infer fear and cost from description or type, but here simple heuristics or defaults
        # The prompt target format has "fear": true/false and "cost": "0"/"1"
        # We can try to regex extract cost from description if present
        desc = trait.get("特性描述", "")
        cost_match = re.search(r"花费\s*(\d+)\s*恐惧点", desc)
        if cost_match:
            new_trait["fear"] = True
            new_trait["cost"] = cost_match.group(1)
        else:
            new_trait["fear"] = False
            new_trait["cost"] = "0"

        new_trait["desc"] = desc
        new_trait["qs"] = trait.get("特性问题", "")
        
        dest["traits"].append(new_trait)

    return dest

    return dest

def process_item(item):
    item_type = item.get("类型")
    if item_type == "敌人":
        return convert_enemy(item)
    elif item_type == "环境":
        return convert_environment(item)
    else:
        # If type is unknown or missing, maybe try to guess or skip?
        # For now, let's assume if it has "名称" and "特性", it might be one of them.
        # But based on user feedback, we strictly switch on type.
        # If unknown, we could return None and filter it out, or just pass it through/error.
        print(f"Warning: Unknown item type '{item_type}' for item '{item.get('名称', 'Unknown')}'. Skipping.")
        return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python zzz2rink.py <input_json_file>")
        return

    input_file = sys.argv[1]
    
    # Determine output filename: place in rink/ folder with same basename
    basename = os.path.basename(input_file)
    name_without_ext = os.path.splitext(basename)[0]
    output_filename = f"{name_without_ext}_rink.json"
    output_dir = "rink"
    output_file = os.path.join(output_dir, output_filename)
    
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found.")
        return

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            source_data = json.load(f)
            
        converted_data = []
        if isinstance(source_data, list):
            for item in source_data:
                result = process_item(item)
                if result:
                    converted_data.append(result)
        elif isinstance(source_data, dict):
            result = process_item(source_data)
            if result:
                converted_data.append(result)
        else:
            print("Error: JSON root must be a list or a dict.")
            return

        # Ensure directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(converted_data, f, ensure_ascii=False, indent=2)
            
        print(f"Successfully converted {len(converted_data)} items to '{output_file}'.")
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
