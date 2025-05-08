import uuid
from pathlib import Path
from typing import Union, Dict, List, Any, Optional
from pydantic import BaseModel, Field
import pandas as pd
import logging
import os
import json
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Define a static output directory
OUTPUT_DIR = os.getenv("EXCEL_FILE_PATH")
OUTPUT_DIR.mkdir(exist_ok=True)

class SaveExcelInput(BaseModel):
    data: Union[Dict[str, Any], List[Dict[str, Any]], str] = Field(
        ...,
        description="The data to save to the Excel file"
    )
    file_name: Optional[str] = Field(
        default=None,
        description="Optional custom file name (without extension). If not provided, a random UUID will be used."
    )

async def save_to_excel(input: SaveExcelInput):
    """Save data to Excel with dynamic column handling"""
    try:
        # Generate filename
        file_stem = input.file_name or str(uuid.uuid4())
        file_path = OUTPUT_DIR / f"{file_stem}.xlsx"
        
        # Process input data
        raw_data = input.data
        
        # Handle string input (either JSON or delimited text)
        if isinstance(raw_data, str):
            try:
                # Try to parse as JSON first
                data = json.loads(raw_data)
            except json.JSONDecodeError:
                # If not JSON, try to parse as key-value pairs
                data = {}
                pairs = [p.strip() for p in raw_data.split(",") if p.strip()]
                for pair in pairs:
                    if ":" in pair:
                        key, val = pair.split(":", 1)
                        data[key.strip()] = val.strip()
                    else:
                        data[f"Column_{len(data)+1}"] = pair
        
        # Normalize to list of dictionaries format
        records = []
        if isinstance(data, dict):
            records.append(data)
        elif isinstance(data, list):
            records.extend(data)
        else:
            records.append({"Value": str(data)})
        
        # Create DataFrame with dynamic columns
        df = pd.DataFrame(records)
        
        # Save to Excel
        df.to_excel(file_path, index=False)
        
        return {
            "status": "success",
            "result": f"Data saved to {file_path}",
            "file_path": str(file_path),
            "columns": list(df.columns),
            "error": None
        }
    except Exception as e:
        logger.error(f"Error saving Excel file: {e}")
        return {
            "status": "failed",
            "result": None,
            "error": str(e)
        }