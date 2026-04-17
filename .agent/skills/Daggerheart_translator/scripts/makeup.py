import re
import argparse
import os

def remove_image_filename(markdown_text):
    """删除 ![](_page_0_Picture_2.jpeg) 格式的图像链接"""
    # 任务 1: 删除图片语法
    # modified_text = re.sub(r'!\[\]\((.*?)\)', '', markdown_text)
    modified_text = re.sub(r'!\[\]\(_page.*?\)', '', markdown_text)
    return modified_text

def remove_span(markdown_text):
    """删除 <span.*></span> 标签"""
    modified_text = re.sub(r'<span.*?></span>', '', markdown_text, flags=re.DOTALL)
    return modified_text

def format_resource_phrases_fn(markdown_text):
    """
    查找并格式化资源相关的短语。
    例如："恢复 1 点生命点" -> "**恢复 1 生命点**"
    """
    pattern = r'\*{0,2}\s*(恢复|回复|标记|清除|移除|获得|花费|消耗)\s*(\d{1,2}d\d{1,2}|\d{1,2}|[一二三四五六])\s*(?:点|个)?\s*((?:生命|希望|压力|恐惧|绝望|恩宠|专注)(?:点)?|护甲(?:槽)?)\s*\*{0,2}'
    
    def replace_match(match):
        action = match.group(1)
        amount_str = match.group(2)
        resource_core = match.group(3)

        # 标准化动词
        if action == "回复":
            action = "恢复"
        elif action == "移除":
            action = "清除"
        elif action == "消耗":
            action = "花费"

        if resource_core == "绝望":
            resource_core = "恐惧"

        # 标准化数字
        num_map = {'一': '1', '二': '2', '三': '3', '四': '4', '五': '5', '六': '6'}
        amount = num_map.get(amount_str, amount_str)

        # 构建资源文本和后缀
        resource_full = resource_core
        if "护甲" in resource_core:
            if not resource_core.endswith("槽"):
                resource_full += "槽"
        elif not resource_core.endswith("点"):
             resource_full += "点"
        
        return f"**{action} {amount} {resource_full}**"

    return re.sub(pattern, replace_match, markdown_text)

def add_space_around_italics_fn(markdown_text):
    """
    在符合条件的斜体文本（内容为1-5个汉字，且前后紧邻汉字）周围添加空格。
    例如: "处于*灌注*状态时" -> "处于 *灌注* 状态时"
    """
    # 正则表达式：匹配前后都是汉字的，内容为1-5个汉字的单斜体
    # (?<=[\u4e00-\u9fa5])  : 正向后行断言，确保前面是一个汉字
    # \*{1}                : 匹配一个星号 (开始的斜体标记)
    # [\u4e00-\u9fa5]{1,5} : 匹配1到5个汉字 (斜体内容)
    # \*{1}                : 匹配一个星号 (结束的斜体标记)
    # (?=[\u4e00-\u9fa5])   : 正向先行断言，确保后面是一个汉字
    pattern = r'(?<=[\u4e00-\u9fa5,.，。])\*{1}[\u4e00-\u9fa5]{1,5}\*{1}(?=[\u4e00-\u9fa5,.，。])'
    
    return re.sub(pattern, lambda m: f" {m.group(0)} ", markdown_text)

def simplify_markdown_links_fn(markdown_text):
    """
    简化 Markdown 链接。
    如果链接文本是 "奥术"，则删除整个链接。
    否则，只保留链接文本，移除方括号和圆括号。
    例如: "[奥术](#page-328-0)" -> ""
           "[其他文本](链接)" -> "其他文本"
    """
    if markdown_text.startswith("![]"):
        # 如果文本以 ![] 开头，直接返回原文本
        return markdown_text
    # 正则表达式：匹配 Markdown 链接
    # \[          : 匹配开方括号
    # ([^\]]+)   : 捕获组1 (link_text) - 方括号内的任何非闭方括号字符
    # \]          : 匹配闭方括号
    # \(          : 匹配开圆括号
    # [^\)]*      : 匹配圆括号内的任何非闭圆括号字符 (链接目标)
    # \)          : 匹配闭圆括号
    pattern = r'\[([^\]]+)\]\([^\)]*\)'

    return re.sub(pattern, lambda match:match.group(1), markdown_text)

def replace_pc_gm_fn(markdown_text):
    """
    将独立的 "PC" 替换为 "玩家角色"，将独立的 "GM" 替换为 "游戏主持人"。
    确保 "PC" 和 "GM" 是独立的词语，即它们前后没有其他字母。
    例如: "PC and GM" -> "玩家角色 and 游戏主持人"
           "NPC or PGM" -> "NPC or PGM" (no change)
    """
    # (?<![A-Za-z]) 表示前面不是字母 (negative lookbehind)
    # (?![A-Za-z]) 表示后面不是字母 (negative lookahead)
    # \b 匹配单词边界，更简洁，但为了明确排除字母上下文，使用 lookaround
    text = re.sub(r'(?<![A-Za-z\(（])PC(?![A-Za-z\)）])', '玩家角色', markdown_text)
    text = re.sub(r'(?<![A-Za-z\(（])GM(?![A-Za-z\)）])', '游戏主持人', text)
    return text

def bold_numbers_and_dice_fn(markdown_text):
    """
    Bolds numbers and dice expressions that are in a Chinese context,
    following the user's specified logic.
    """
    chinese_chars_and_punctuation = r'\u4e00-\u9fa5'
    
    # Pattern to find numbers/dice, including optional signs and spaces.
    find_pattern = r'([-−+]?)\s*(\d*d\d+(?:[-−+]\s*\d+)?|\d+)'

    # --- Pass 1: Fix spacing for already bolded items ---
    dice_or_number_pattern_no_space = r'[-−+]?\d*d\d+(?:[-−+]\d+)?|[-−+]?\d+'
    pattern_pre_bold = f'([{chinese_chars_and_punctuation}])(?<!\\s)\\*\\*({dice_or_number_pattern_no_space})\\*\\*'
    processed_text = re.sub(pattern_pre_bold, r'\1 **\2**', markdown_text)
    pattern_post_bold = f'\\*\\*({dice_or_number_pattern_no_space})\\*\\*(?!\\s)([{chinese_chars_and_punctuation}])'
    processed_text = re.sub(pattern_post_bold, r'**\1** \2', processed_text)

    # --- Pass 2: Process each non-bold segment based on user logic ---
    parts = processed_text.split('**')
    new_parts = []
    for i, part in enumerate(parts):
        if i % 2 != 0:  # If it's a bold part, just add it back and continue.
            new_parts.append(part)
            continue

        new_sub_part = ""
        last_end = 0
        for match in re.finditer(find_pattern, part):
            new_sub_part += part[last_end:match.start()]
            
            start, end = match.start(), match.end()
            
            pre_char = part[start - 1] if start > 0 else ''
            post_char = part[end] if end < len(part) else ''

            # Exemption for parentheses
            if (pre_char == '(' and post_char == ')') or \
               (pre_char == '（' and post_char == '）'):
                new_sub_part += match.group(0)
                last_end = end
                continue

            # Check if the immediate surrounding characters are Chinese or Chinese punctuation
            is_pre_chinese = re.search(f'[{chinese_chars_and_punctuation}]', pre_char)
            is_post_chinese = re.search(f'[{chinese_chars_and_punctuation}]', post_char)

            if is_pre_chinese or is_post_chinese:
                # Format the match
                cleaned_match = re.sub(r'\s', '', match.group(0))
                pre_space = '' if pre_char.isspace() or not pre_char else ' '
                post_space = '' if post_char.isspace() or not post_char else ' '
                new_sub_part += f"{pre_space}**{cleaned_match}**{post_space}"
            else:
                # If not, return the original matched string
                new_sub_part += match.group(0)
            
            last_end = end

        new_sub_part += part[last_end:]
        new_parts.append(new_sub_part)
            
    return '**'.join(new_parts)

makeup_list = [
    remove_image_filename,
    remove_span,
    format_resource_phrases_fn,
    # bold_numbers_and_dice_fn, # Must run before italics
    add_space_around_italics_fn,
    simplify_markdown_links_fn,
    replace_pc_gm_fn,
]

def process_markdown_file(input_filepath, suffix="_makeup"):
    """
    读取指定的 Markdown 文件，对每段文本应用 makeup_list 中的所有函数，
    然后将结果写入新的 Markdown 文件。
    """
    if not os.path.exists(input_filepath):
        print(f"错误：文件 '{input_filepath}' 不存在。")
        return

    try:
        with open(input_filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"读取文件 '{input_filepath}' 时出错: {e}")
        return

    # 按空行分割文本段落
    paragraphs = content.split('\n\n')
    processed_paragraphs = []

    for paragraph in paragraphs:
        processed_paragraph = paragraph
        for func in makeup_list:
            processed_paragraph = func(processed_paragraph) # 默认阈值
        processed_paragraphs.append(processed_paragraph)

    processed_content = '\n\n'.join(processed_paragraphs)

    base, ext = os.path.splitext(input_filepath)
    output_filepath = f"{base}{suffix}{ext}"

    try:
        with open(output_filepath, 'w', encoding='utf-8') as f:
            f.write(processed_content)
        print(f"处理完成，结果已写入 '{output_filepath}'")
    except Exception as e:
        print(f"写入文件 '{output_filepath}' 时出错: {e}")

def main():
    parser = argparse.ArgumentParser(description="处理 Markdown 文件，应用一系列转换函数。")
    parser.add_argument("input_file", help="要处理的 Markdown 文件的路径。")
    args = parser.parse_args()
    process_markdown_file(args.input_file)

if __name__ == "__main__":
    main()
