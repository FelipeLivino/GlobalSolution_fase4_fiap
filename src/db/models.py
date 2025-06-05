from pydantic import BaseModel
from typing import Tuple, List

class SensorsData(BaseModel):
    dados: List[Tuple[float, int]]


class SuccessResponse(BaseModel):
    message: List

class FileUploadResponse(BaseModel):
    message: str