import json
import os

import requests

import common_functions as cf

def fetch_models():

  OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY')

  url = "https://openrouter.ai/api/v1/models"
  headers = {
    'Authorization': f'Bearer {OPENROUTER_API_KEY}'
  }

  response = requests.get(url, headers = headers)

  data = json.loads(response.text)

  cf.write_json_file(data, "models_full.json")

  return data

def sort_models():

  data = cf.read_json_file("models_full1.json")
  models = [model['id'] for model in data['data']]
  new_open_ai_models = "1106"

  models_set = set(models)
  remove_base_model = set()
  remove_subset_model = set()
  model_dictionaries = {}

  for model1 in models_set:
    if model1 in remove_subset_model:
      continue
    for model2 in models_set:
      if model1 == model2:
        continue
      else:
        if model1 in model2:
          if new_open_ai_models in model2:
            remove_base_model.add(model1)
          else:
            remove_subset_model.add(model2)
          
        
  models_set -= remove_subset_model
  models_set -= remove_base_model  
  models = sorted(models_set)
  
  model_dictionaries = {model['id']: {k: v for k, v in model.items() if k != 'id'} for model in data['data'] if model['id'] in models}

  cf.write_json_file(model_dictionaries, "models_sorted.json")


  return model_dictionaries