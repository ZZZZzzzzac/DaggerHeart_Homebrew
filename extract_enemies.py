import json
import re
import os
import uuid

INPUT_FILE = 'raw/非凡生物.md'
OUTPUT_FILE = 'raw/非凡生物.json'

def parse_creatures(filepath):
    entities = []
    current_entity = None
    
    # Regex patterns
    # 位阶：1；类型：斗士；  (Note: colons can be fullwidth or halfwidth)
    meta_regex = re.compile(r'位阶[：:]\s*(\d+)[；;]\s*类型[：:]\s*(.+?)[；;]?\s*$')
    
    # Stats parsing (broken down)
    difficulty_regex = re.compile(r'难度[：:]\s*(\d+)')
    threshold_regex = re.compile(r'阈值[：:]\s*([^|]+)')
    hp_regex = re.compile(r'生命点[：:]\s*(\d+|无)')
    stress_regex = re.compile(r'压力点[：:]\s*(\d+|无)')
    
    # 攻击：+1 | 利爪：近战 | 1d8+6 物理
    attack_regex = re.compile(r'攻击[：:]\s*([+–-]?\d+|[–-]).*?\|\s*(.+?)[：:]\s*(.+?)\s*\|\s*(.+)')
    
    # Feature: Name - Type: Description
    # Matches "Name - Type: Description" or "Name - Type (Cost): Description"
    feature_regex = re.compile(r'^(.+?)\s+[–-]\s+(.+?)[：:]\s*(.+)$')
    
    # Description
    desc_regex = re.compile(r'^描述[：:]\s*(.+)$')
    
    # Motives
    motive_regex = re.compile(r'^(动机与战术|战术)[：:]\s*(.+)$')
    
    # Tendency (Environment)
    tendency_regex = re.compile(r'^趋向[：:]\s*(.+)$')

    # Potential Enemies
    enemies_regex = re.compile(r'^潜在敌人[：:]\s*(.+)$')

    # Experience
    exp_regex = re.compile(r'^经历[：:]\s*(.+)$')

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        line = line.strip()
        
        # Skip empty or separator lines for "Name" tracking
        # But we need them to find names via lookback
        if not line or line.startswith('---'):
            continue
            
        # Check for Metadata Line (Start of Entity)
        meta_match = meta_regex.search(line)
        if meta_match:
            # Save previous entity if exists
            if current_entity:
                entities.append(current_entity)
            
            # Start new entity
            # Name is the last non-separator line we saw BEFORE this one.
            name = "Unknown"
            # Look backwards from i-1
            j = i - 1
            while j >= 0:
                prev_line = lines[j].strip()
                if prev_line and not prev_line.startswith('---') and not prev_line.startswith('位阶'):
                    # Check if it looks like a header (e.g. "位阶1" or "干旱沙漠")
                    # Heuristic: If there are multiple lines, the one closest to Meta is Name.
                    # The lines above might be context.
                    # Let's take the immediate predecessor that isn't --- or empty.
                    name = prev_line
                    break
                j -= 1
            
            # Special case cleanup for name
            # Sometimes name line might have trailing info? Unlikely based on file.
            
            tier = meta_match.group(1)
            kind = meta_match.group(2).strip()
            
            current_entity = {
                "名称": name,
                # "原文": "", # Placeholder
                "位阶": tier,
                "种类": kind,
                "类型": "敌人",
                "特性": [],
                "简介": "",
                "动机与战术": "",
                "难度": "",
                "重度伤害阈值": "",
                "严重伤害阈值": "",
                "生命点": "",
                "压力点": "",
                "攻击命中": "",
                "攻击武器": "",
                "攻击范围": "",
                "攻击伤害": "",
                "攻击属性": "",
                "经历": "",
                "来源": "非凡生物",
                "潜在敌人": "", # For environments
                "趋向": "" # For environments
            }
            continue

        if current_entity is None:
            continue

        # Parsing Body
        
        # Description
        desc_match = desc_regex.search(line)
        if desc_match:
            current_entity["简介"] = desc_match.group(1)
            continue
            
        # Motives
        motive_match = motive_regex.search(line)
        if motive_match:
            current_entity["动机与战术"] = motive_match.group(2)
            continue
            
        # Tendency
        tendency_match = tendency_regex.search(line)
        if tendency_match:
            current_entity["趋向"] = tendency_match.group(1)
            current_entity["类型"] = "环境"
            continue
            
        # Potential Enemies
        enemies_match = enemies_regex.search(line)
        if enemies_match:
            current_entity["潜在敌人"] = enemies_match.group(1)
            continue

        # Stats parsing
        if '难度' in line:
            diff_match = difficulty_regex.search(line)
            if diff_match:
                current_entity["难度"] = diff_match.group(1)
            
            thresh_match = threshold_regex.search(line)
            if thresh_match:
                thresholds_str = thresh_match.group(1).strip()
                if '/' in thresholds_str:
                    parts = thresholds_str.split('/')
                    current_entity["重度伤害阈值"] = parts[0].strip()
                    current_entity["严重伤害阈值"] = parts[1].strip()
                else:
                    current_entity["重度伤害阈值"] = thresholds_str
                    current_entity["严重伤害阈值"] = ""
            
            hp_match = hp_regex.search(line)
            if hp_match:
                current_entity["生命点"] = hp_match.group(1)
                
            stress_match = stress_regex.search(line)
            if stress_match:
                current_entity["压力点"] = stress_match.group(1)
            
            # If we found at least difficulty, assume this was a stats line and continue
            if diff_match:
                continue
            
        # Stats 2 (Attack)
        attack_match = attack_regex.search(line)
        if attack_match:
            current_entity["攻击命中"] = attack_match.group(1).replace('–', '-')
            current_entity["攻击武器"] = attack_match.group(2)
            current_entity["攻击范围"] = attack_match.group(3)
            damage_full = attack_match.group(4)
            # Try to split damage and type (e.g. "1d8+6 物理")
            parts = damage_full.strip().rsplit(' ', 1)
            if len(parts) == 2:
                current_entity["攻击伤害"] = parts[0]
                current_entity["攻击属性"] = parts[1]
            else:
                current_entity["攻击伤害"] = damage_full
                current_entity["攻击属性"] = ""
            continue
            
        # Experience
        exp_match = exp_regex.search(line)
        if exp_match:
            current_entity["经历"] = exp_match.group(1)
            continue
            
        # Features
        feature_match = feature_regex.search(line)
        if feature_match:
            feature_name = feature_match.group(1)
            feature_type = feature_match.group(2)
            feature_desc = feature_match.group(3)
            
            current_entity["特性"].append({
                "名称": feature_name,
                # "原名": "",
                "类型": feature_type,
                "特性描述": feature_desc
            })
            continue
        
        # Feature Questions/Continuation
        if current_entity and current_entity["特性"]:
            last_feature = current_entity["特性"][-1]
            if line.endswith('?') or line.endswith('？') or line.startswith('*') or line.startswith('-'):
                # Check if it's a list item inside description or a question
                if line.startswith('- '):
                     # Likely continuation of a list in description (like in Lab)
                     last_feature["特性描述"] += "\n" + line
                elif "特性问题" not in last_feature:
                     last_feature["特性问题"] = line
                else:
                     last_feature["特性问题"] += "\n" + line

    # Append last entity
    if current_entity:
        entities.append(current_entity)

    # Cleanup fields
    final_entities = []
    for e in entities:
        if e["类型"] == "敌人":
            template_keys = ["名称", "位阶", "种类", "特性", "类型", "简介", "动机与战术", "难度", "重度伤害阈值", "严重伤害阈值", "生命点", "压力点", "攻击命中", "攻击武器", "攻击范围", "攻击伤害", "攻击属性", "经历", "来源"]
            final = {k: e.get(k, "") for k in template_keys}
        else:
            template_keys = ["名称", "位阶", "种类", "特性", "类型", "简介", "趋向", "难度", "潜在敌人", "来源"]
            final = {k: e.get(k, "") for k in template_keys}
        
        # Ensure values are not None
        for k in final:
            if final[k] is None:
                final[k] = ""

        final["id"] = str(uuid.uuid4())
        final_entities.append(final)

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_entities, f, indent=4, ensure_ascii=False)
    
    print(f"Processed {len(final_entities)} entities.")

if __name__ == "__main__":
    parse_creatures(INPUT_FILE)
