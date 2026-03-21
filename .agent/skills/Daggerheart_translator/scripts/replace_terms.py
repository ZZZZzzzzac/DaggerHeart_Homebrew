import json
import os
import re
import sys

# Ensure stdout uses UTF-8 on Windows (avoids GBK UnicodeEncodeError)
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def replace_terms(text, terms_file_path):
    if not os.path.exists(terms_file_path):
        return text

    try:
        with open(terms_file_path, 'r', encoding='utf-8') as f:
            terms_data = json.load(f)
    except Exception as e:
        print(f"Error loading terms file: {e}")
        return text

    # Sort terms by length in descending order to avoid partial replacements
    # e.g., replacing "Spell" before "Spellcast Roll"
    terms_data.sort(key=lambda x: len((x.get('term') or '').strip()), reverse=True)

    replaced_text = text
    replaced_terms = set()

    # Pattern to split text into protected 【...】 segments and unprotected segments
    PROTECTED_PATTERN = re.compile(r'(【[^】]*】)')

    for term_entry in terms_data:
        original_term = (term_entry.get('term') or '').strip()
        translation = (term_entry.get('translation') or '').strip()
        
        # VERY AGGRESSIVELY clean up newlines and extra spaces from the translation
        translation = " ".join(translation.split())

        if not original_term or not translation:
            continue

        # Escape the original term to handle regex special characters safely
        escaped_term = re.escape(original_term)
        
        # Build the pattern
        try:
            pattern = re.compile(r'\b' + escaped_term + r'\b', re.IGNORECASE)
        except re.error as err:
            continue
        
        # Only replace in unprotected segments (outside 【】 brackets)
        # to prevent re-processing already-replaced content
        if not pattern.search(replaced_text):
            continue

        segments = PROTECTED_PATTERN.split(replaced_text)
        new_segments = []
        term_found = False
        for seg in segments:
            if PROTECTED_PATTERN.fullmatch(seg):
                # This segment is already protected – leave it as-is
                new_segments.append(seg)
            else:
                replaced_seg = pattern.sub(lambda m: f"【{translation} ({m.group(0)})】", seg)
                if replaced_seg != seg:
                    term_found = True
                new_segments.append(replaced_seg)
        replaced_text = ''.join(new_segments)
        if term_found:
            replaced_terms.add(original_term)

    return replaced_text

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python replace_terms.py <input_file> <terms_json> [output_file]")
        sys.exit(1)

    input_arg = sys.argv[1]
    terms_path = sys.argv[2]
    output_path = sys.argv[3] if len(sys.argv) > 3 else None

    # If the first arg is a file path, read from it, otherwise treat as raw text
    if os.path.exists(input_arg):
        with open(input_arg, 'r', encoding='utf-8') as f:
            input_text = f.read()
    else:
        input_text = input_arg

    result = replace_terms(input_text, terms_path)

    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result)
    else:
        print(result)
