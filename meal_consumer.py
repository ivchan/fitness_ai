import os
import json
import base64
import pika
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
  api_key = os.getenv("XAI_API_KEY"),
  base_url = "https://api.x.ai/v1"
)

meal_analysis_schema = {
  "type": "object",
  "properties": {
    "meal_name": {"type": "string", "description": "食物名稱"},
    "fitness_rating": {"type": "string", "description": "建議進食評級, 分為 [建議多吃, 建議吃, 普通, 不建議吃, 不能吃] 幾個選項"},
    "totalCalories": {"type": "number", "description": "總熱量（數字）"},
    "items": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": {"type": "string", "description": "食物名稱"},
          "portion": {"type": "string", "description": "估計份量"},
          "calories": {"type": "number", "description": "該項熱量"},
          "protein_g": {"type": "number", "description": "蛋白質（克）"},
          "fat_g": {"type": "number", "description": "脂肪（克）"},
          "carbs_g": {"type": "number", "description": "碳水化合物（克）"}
        },
        "required": ["name", "portion", "calories", "protein_g", "fat_g", "carbs_g"],
        "additionalProperties": False
      },
      "description": "食物項目列表"
    },
    "notes": {"type": ["string", "null"], "description": "簡短營養建議（可選）"}
  },
  "required": ["totalCalories", "items"],
  "additionalProperties": False
}

response_format = {
  "type": "json_schema",
  "json_schema": {
    "name": "food_analysis_result",
    "strict": True,  # 嚴格模式，強制符合 schema
    "schema": meal_analysis_schema
  }
}

prompt = """
你是一名專業營養學專家，能夠從圖片準確估算食物成分與熱量。
請分析圖片中的食物，識別食物名稱、主要食物項目、估計份量、計算每項的熱量與主要營養素（蛋白質、脂肪、碳水化合物，單位：克）。
如果無法清楚識別，請在 notes 中說明並將 totalCalories 設為 0。
詳細分析圖片中的食物對減肥的影響並記錄在 notes。
評估圖片中的食物對減肥目標的影響，並進行建議進食評級。
以香港繁體中文回答
"""

def analyze_image(base64_image):
  """呼叫 Grok API 進行圖片分析（使用 Structured Outputs）"""
  data_url = f"data:image/jpeg;base64,{base64_image}"

  messages = [
  {
    "role": "user",
    "content": [
      {"type": "text", "text": prompt},
      {
        "type": "image_url",
        "image_url": {"url": data_url}
      }
    ]
  }]

  response = client.chat.completions.create(
    model="grok-4",  # 確認支援 Structured Outputs 的模型
    messages=messages,
    max_tokens=1000,
    temperature=0.3,
    response_format=response_format  # 關鍵：強制結構化輸出
  )
  return response.choices[0].message.content

def convert_to_base64(file_path):
  try:
    with open(file_path, "rb") as image_file:
      image_bytes = image_file.read()
      encoded_bytes = base64.b64encode(image_bytes)
      encoded_string = encoded_bytes.decode('utf-8')
    return encoded_string
  except FileNotFoundError:
    return "Error: Image file not found."
  except Exception as e:
    return f"Error occured: {e}"

file_path = 'image/beef.png'

image_base64 = convert_to_base64(file_path)
result_json = analyze_image(image_base64)

result_obj = json.loads(result_json)
print(json.dumps(result_obj, indent=4, ensure_ascii=False))
