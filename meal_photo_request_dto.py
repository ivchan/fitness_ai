import json

class MealPhotoRequestDto:
  def __init__(self, request_id, imageBase64):
    self.request_id = request_id
    self.imageBase64 = imageBase64
