import json
import re
import time
import traceback

import requests

mesaage_word_count = 0
token_conversion_factor = 0.7


def read_text_file(file_path):
  
  try:
    with open(file_path, "r") as f:
      read_file = f.read()


    return read_file

  except FileNotFoundError:
    print(f"Error: File '{file_path}' not found.")
    exit()

def read_json_file(file_path):
  
  try:
    with open(file_path, "r") as f:
      read_file = json.load(f)

    
    return read_file
    
  except FileNotFoundError:
    print(f"Error: File '{file_path}' not found.")
    exit()

def write_json_file(content, file_path):
  with open(file_path, "w") as f:
    json.dump(content, f, indent=2)


def error_handle(e, error, retry_count):

  if isinstance(error, dict):
    error_message = error.get("message", "OpenRouter sucks")
    error_code = error.get("code", 400)
  else:
    error_code = error
    error_message = e
  
  max_retries = 3
  fail_state = [401, 402]
  
  if isinstance(error_code, int):
    pass
  elif isinstance(error_code, str):
    try:
      error_code = int(error_code)
    except ValueError:
      error_code = 400
  else:
    error_code = 400
    
  if error_code == 403:
    print("content moderation flag. Skipping...")
    status_flag = "skip"
    return status_flag, retry_count
  elif error_code in fail_state:
    print(error_message)
    retry_count = max_retries
    status_flag = "fail"
  elif error_code == 429:
    print("OpenRouter rate limit reached. Resetting timer...")
    time.sleep(10)
    retry_count -= 1
    status_flag = "retry"
  else:
    print(f"\nAn exception occurred: {e}")
    status_flag = "retry"

  
  retry_count += 1

  if retry_count < max_retries:
    exponential_sleep = 2 ** retry_count
    print(f"Retrying in {exponential_sleep} seconds...")
    time.sleep(exponential_sleep)

  else:
    print("Maximum retries reached. Exiting...")
    traceback.print_exc()
    exit()

  
  return status_flag, retry_count

def call_openrouter_api(model, prompt, role_script, temperature, max_tokens, retry_count = 0):

  answer = ""
  price = 0
  
  OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY')

  headers = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "http://localhost:3000",
    "X-Title": "ProsePal"
  }


  if "anthropic" in model:
    removed_sys_role = re.sub(r'^.*?[.!?]', '', role_script, count=1).lstrip()
    combined_prompt = f"\n\nHuman: {removed_sys_role}\nHere is the text inside XML tags:\n<text>\n{prompt}\n</text>\n\nAssistant: "
    payload = {
      "model": model,
      "prompt": combined_prompt,
      "max_tokens": max_tokens,
      "temperature": temperature
    }

  else:
    messages = [
        {"role": "system", "content": role_script},
        {"role": "user", "content": prompt}
    ]
    
    payload = {
      "model": model,
      "messages": messages,
      "max_tokens": max_tokens,
      "temperature": temperature
    }

  response = None
  error = None
  
  try:
    response = requests.post(
      url = "https://openrouter.ai/api/v1/chat/completions",
      headers = headers,
      data =json.dumps(payload)
    )
    response_data = response.json()
    print(response_data)
    error = response_data.get("error", None)
    if error:
      raise Exception("API error")
    else:
      response.raise_for_status()
      error = response.status_code
      
  except Exception as e:
    print(retry_count)
    status_flag, retry_count = error_handle(e, error, retry_count)

    if status_flag == "skip":
      answer = "flagged: none found"

    
      return answer, price
      
    else:
    
    
      return call_openrouter_api(model, prompt, role_script, temperature, max_tokens, retry_count = retry_count)

  choices = response_data['choices'][0]
  message_content = choices.get('message', {}).get('content')
  text_content = choices.get('text')

  if message_content:
    answer = message_content.strip()
  elif text_content:
    answer = text_content.strip()
  else:
    answer = "Bad response: None found"
    
  if "characters".lower() not in answer.lower():
    answer = "Bad response: None found"
    
    
    return answer, price

  generation_id = response_data['id']
  generation_info = requests.get(
    url = f"https://openrouter.ai/api/v1/generation?id={generation_id}",
    headers = headers)
  if generation_info.status_code:
    generation_stats = generation_info.json()
    if "data" in generation_stats and "usage" in generation_stats['data']:
      price = generation_stats['data']['usage']
  else:
    price = 0
  
  
  return answer, price
  