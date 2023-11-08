import re
import time

import common_functions as cf
import fetch


def chunk_file(chapter):

  words = chapter.split()
  
  current_chunk = []
  chapter_chunks = []
  
  for word in words:
    if len(current_chunk) < 2000:
      current_chunk.append(word)
    else:
      chapter_chunks.append(" ".join(current_chunk))
      current_chunk = [word]

  if current_chunk:
    chapter_chunks.append(" ".join(current_chunk))


  return chapter_chunks

def google_chunk_file(chapter):
  
  words = chapter.split()
  
  current_chunk = []
  current_length = 0
  chapter_chunks = []
  
  for word in words:
    word_length = len(word) + 1
    if current_length + word_length <= 3500:
      current_chunk.append(word)
      current_length += word_length
    else:
      chapter_chunks.append(" ".join(current_chunk))
      print(len(current_chunk))
      current_chunk = [word]
      current_length = word_length
  
  if current_chunk:
    chapter_chunks.append(" ".join(current_chunk))

  
  return chapter_chunks
  
def compare_names(inner_values):

  compared_names = {}

  for i, value_i in enumerate(inner_values):
    for j, value_j in enumerate(inner_values):
      if i != j and value_i != value_j and not value_i.endswith(")") and (value_i.startswith(value_j) or value_i.endswith(value_j)):
          shorter_value, longer_value = sorted([value_i, value_j], key = len)
          compared_names[shorter_value] = longer_value

  longer_name = [compared_names.get(name, name) for name in inner_values]
  inner_values = list(dict.fromkeys(longer_name)) #Deduplicate


  return inner_values

def sort_names(character_lists):

  parse_tuples = {}
  attribute_table = {}
  
  character_info_pattern = re.compile(r"\((?!interior|exterior).+\)$", re.IGNORECASE)
  inverted_setting_pattern = re.compile(r"(interior|exterior)\s+\((\w+)\)", re.IGNORECASE)
  leading_colon_pattern = re.compile(r"\s*:\s+")
  list_formatting_pattern = re.compile(r"^[\d.-]\s*|^\.\s|^\*\s*|^\+\s*|^\\t")
  missing_newline_before_pattern = re.compile(r"(?<=\w)(?=[A-Z][a-z]*:)")
  missing_newline_between_pattern = re.compile(r"(\w+ \(\w+\))\s+(\w+)")
  missing_newline_after_pattern = re.compile(r"(?<=\w):\s*(?=\w)")
  
  junk_lines = ["additional", "note", "none"]
  stop_words = ["mentioned", "unknown", "he", "they", "she", "we", "it", "boy", "girl", "main", "him", "her", "narrator", "I", "</s>", "a"]

  for model, proto_dict in character_lists:
    if model not in parse_tuples:
      parse_tuples[model] = proto_dict
    else:
      parse_tuples[model] += "\n" + proto_dict

  for model, proto_dict in parse_tuples.items():

    attribute_table[model] = {}
    inner_dict = {}
    attribute_name = None
    inner_values = []

    lines = proto_dict.split("\n")
    
    i = 0
    while i < len(lines):
      
      line = lines[i]
      line = list_formatting_pattern.sub("", line)
      line = re.sub(r'(interior|exterior)', lambda m: m.group().lower(), line, flags=re.IGNORECASE)

      if line.startswith("interior:") or line.startswith("exterior:"):
        
        prefix, places = line.split(":", 1)
        setting = "(interior)" if prefix == "interior" else "(exterior)"
        split_lines = [f"{place.strip()} {setting}" for place in places.split(",")]
        lines[i:i + 1] = split_lines
        continue
        
      line = inverted_setting_pattern.sub(r"\2 (\1)", line)
        
      if ", " in line:
        comma_split = line.split(", ")
        lines[i:i + 1] = comma_split
        continue

      added_newline = missing_newline_before_pattern.sub("\n", line)
      if added_newline != line:
        added_newlines = added_newline.split("\n")
        lines[i: i + 1] = added_newlines
        continue
        
      added_newline = missing_newline_between_pattern.sub(r"\1\n\2", line)
      if added_newline != line:
        added_newlines = added_newline.split("\n")
        lines[i: i + 1] = added_newlines
        continue

      added_newline = missing_newline_after_pattern.sub(":\n", line)
      if added_newline != line:
        added_newlines = added_newline.split("\n")
        lines[i: i + 1] = added_newlines
        continue
        
      line = leading_colon_pattern.sub("", line)
      line = line.strip()
      
      if line == "":
        i += 1
        continue
        
      if line.lower() in [word.lower() for word in stop_words]:
          i += 1
          continue
        
      if any(junk in line.lower() for junk in junk_lines):
        i += 1
        continue
        
      if line.count("(") != line.count(")"):
        line.replace("(", "").replace(")", "")
        
      line = character_info_pattern.sub("", line)

      #Remaining lines ending with a colon are attribute names and lines following belong in a list for that attribute
      if line.endswith(":"):
        if attribute_name:
          inner_dict.setdefault(attribute_name, []).extend(inner_values)
          inner_values = []
        attribute_name = line[:-1].title()
      else:
        inner_values.append(line)

      i += 1

    if attribute_name:
      inner_dict.setdefault(attribute_name, []).extend(inner_values)
      inner_values = []

    if inner_dict:
      for attribute_name, inner_values in inner_dict.items():
        if attribute_name.endswith("s") and attribute_name[:-1]:
          inner_values.extend(inner_dict[attribute_name[:-1]])
          inner_dict[attribute_name[:-1]] = []
        inner_values = compare_names(inner_values)
        attribute_table[model][attribute_name] = inner_values
      inner_values = []

  # Remove empty attribute_name keys
  for model in list(attribute_table.keys()):
    for attribute_name, inner_values in list(attribute_table[model].items()):
      if not inner_values:
        del attribute_table[model][attribute_name]


  return attribute_table


def search_names(chapter_chunks, model, character_lists, chunk_prices):

  api_start = time.time()

  price = 0
  
  temperature = 0.2
  max_tokens = 500
  role_script = (
    "You are a script supervisor compiling a list of characters in each scene. For the following selection, determine who are the characters, giving only their name and no other information. Please also determine the settings, both interior (e.g. ship's bridge, classroom, bar) and   exterior (e.g. moon, Kastea, Hell's Kitchen)."
    "If the scene is written in the first person, identify the narrator by their name if possible or simply state 'narrator' if the text doesn't make it apparent. Ignore special characters. If you cannot identify the narraotr, just skip it."
    "Be as brief as possible, using one or two words for each entry, and avoid descriptions. For example, 'On board the Resolve' should be 'Resolve'. 'Debris field of leftover asteroid pieces' should be 'Asteroid debris field'. ' Unmarked section of wall (potentially a hidden door)' should be 'unmarked wall section'"
    "If you are unsure of a setting or no setting is shown in the text, please respond with 'None found' on the same line as the word 'Setting'"
    "Please format the output exactly like this without any further commentary about what hou could or couldn't find:"
    "Characters:"
    "character1"
    "character2"
    "character3"
    "Setting:"
    "Setting1 (interior)"
    "Setting2 (exterior)"
  )
    
  for chunk in chapter_chunks:

    prompt = chunk
  
    character_list, chunk_price = cf.call_openrouter_api(model, prompt, role_script, temperature, max_tokens)
    character_lists.append((model, character_list))
    chunk_prices.append((model, chunk_price))

    price += chunk_price
    
  cf.write_json_file(character_lists, "character_lists.json")
  cf.write_json_file(chunk_prices, "chunk_prices.json")
  
  api_end = time.time()
  api_time = api_end - api_start

  api_time = "{:.2f}".format(api_time)
  
  print(f"API time: {api_time} seconds")
  print(f"Price: ${price}")


  return character_lists, chunk_prices, price, api_time

def main():
  
  character_lists = []
  chunk_prices = []
  attribute_table = {}
  model_stats = {}
  
  chapter = cf.read_text_file("chapter.txt")
  chapter_chunks = chunk_file(chapter)

  models = fetch.sort_models()

  for model in models:

    if "google" in model:
      continue

    character_lists, chunk_prices, price, api_time = search_names(chapter_chunks, model, character_lists, chunk_prices)
    model_stats[model] = {"price": price, "api_time": api_time}
  
  cf.write_json_file(model_stats, "model_stats.json")
  attribute_table = sort_names(character_lists)
  cf.write_json_file(attribute_table, "attribute_table.json")




if __name__ == "__main__":
  main()
