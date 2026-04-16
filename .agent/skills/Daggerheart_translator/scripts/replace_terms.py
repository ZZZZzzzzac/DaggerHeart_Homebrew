import json
import os
import re
import sys

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
        
        if pattern.search(replaced_text):            
            def match_replacer(match):
                # Don't replace if it's already inside our brackets 【】
                # Use the exact matched string (match.group(0)) to preserve original casing in the bracket
                return f"【{translation} ({match.group(0)})】"

            replaced_text = pattern.sub(match_replacer, replaced_text)
            replaced_terms.add(original_term)

    return replaced_text

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python replace_terms.py <text_to_process> <path_to_terms_json> [output_path]")
        sys.exit(1)

    input_text = sys.argv[1]
    terms_path = sys.argv[2]
    output_path = sys.argv[3] if len(sys.argv) > 3 else None
    
    # If the text is a file path, read from it, otherwise treat as raw text
    if os.path.exists(input_text):
        with open(input_text, 'r', encoding='utf-8') as f:
            input_text = f.read()

    result = replace_terms(input_text, terms_path)
    
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result)
    else:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stdout.write(result + '\n')
