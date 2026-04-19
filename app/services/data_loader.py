import json
import os
from typing import List, Dict, Any, Optional, Type, TypeVar, Union
from pydantic import BaseModel
from config import settings

T = TypeVar("T", bound=BaseModel)

class DataLoader:
    """Service for loading and saving mock data using Pydantic schemas."""
    
    @staticmethod
    def _load_raw(file_path: str) -> List[Dict[str, Any]]:
        if not os.path.exists(file_path):
            return []
        with open(file_path, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []

    @staticmethod
    def _save_raw(file_path: str, data: List[Dict[str, Any]]):
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)

    @classmethod
    def load_collection(cls, file_path: str, schema: Type[T]) -> List[T]:
        raw_data = cls._load_raw(file_path)
        return [schema(**item) for item in raw_data]

    @classmethod
    def find_by_id(cls, file_path: str, schema: Type[T], id_field: str, id_value: str) -> Optional[T]:
        collection = cls.load_collection(file_path, schema)
        for item in collection:
            if getattr(item, id_field) == id_value:
                return item
        return None

    @classmethod
    def find_many_by_field(cls, file_path: str, schema: Type[T], field_name: str, value: str) -> List[T]:
        collection = cls.load_collection(file_path, schema)
        return [item for item in collection if getattr(item, field_name, None) == value]

    @classmethod
    def save_item(cls, file_path: str, item: BaseModel, id_field: str):
        collection = cls._load_raw(file_path)
        item_dict = item.model_dump()
        
        # Update existing or append new
        updated = False
        for i, existing in enumerate(collection):
            if existing.get(id_field) == item_dict.get(id_field):
                collection[i] = item_dict
                updated = True
                break
        
        if not updated:
            collection.append(item_dict)
            
        cls._save_raw(file_path, collection)
