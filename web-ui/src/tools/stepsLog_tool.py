import uuid
from pathlib import Path
from typing import Union, Dict, List, Any, Optional, Literal
from pydantic import BaseModel, Field
import pandas as pd
import logging
import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Define output directories
OUTPUT_DIR = os.getenv("LOGS_PATH")
OUTPUT_DIR.mkdir(exist_ok=True)

STEP_LOGS_DIR = OUTPUT_DIR 
STEP_LOGS_DIR.mkdir(exist_ok=True)

class SaveExcelInput(BaseModel):
    data: Union[Dict[str, Any], List[Dict[str, Any]], str] = Field(
        ...,
        description="The data to save to the Excel file"
    )
    file_name: Optional[str] = Field(
        default=None,
        description="Optional custom file name (without extension). If not provided, a random UUID will be used."
    )

class SaveStepLogInput(BaseModel):
    step_name: str = Field(
        ...,
        description="Name or identifier for the processing step"
    )
    output_data: Optional[Union[Dict[str, Any], List[Dict[str, Any]], str]] = Field(
        default=None,
        description="The output data from this step"
    )
    error_data: Optional[Union[Dict[str, Any], List[Dict[str, Any]], str]] = Field(
        default=None,
        description="Error information if this step failed"
    )
    status: Literal["success", "failed", "partial"] = Field(
        default="success",
        description="Status of the step execution"
    )
    timestamp: Optional[datetime] = Field(
        default=None,
        description="Timestamp of the step execution. If not provided, current time will be used."
    )
    additional_info: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Any additional metadata about the step"
    )

async def save_to_excel(input: SaveExcelInput):
    """Save data to Excel with dynamic column handling"""
    try:
        # Generate filename
        file_stem = input.file_name or str(uuid.uuid4())
        file_path = OUTPUT_DIR / f"{file_stem}.xlsx"
        
        # Process input data
        raw_data = input.data
        
        # Handle string input (assume it's a JSON string or step-by-step text)
        if isinstance(raw_data, str):
            try:
                # Try to parse as JSON first
                data = json.loads(raw_data)
            except json.JSONDecodeError:
                # If not JSON, parse as step-by-step text
                records = []
                lines = raw_data.strip().split("\n")
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    # Extract step number and description
                    if line.startswith("Step"):
                        step_num, desc = line.split(":", 1)
                        records.append({
                            "Step": step_num.strip(),
                            "Description": desc.strip()
                        })
                    elif line.startswith("Summary:") or "summary" in line.lower():
                        # Handle summary as a separate field
                        summary = line.replace("Summary:", "").strip()
                        records.append({
                            "Step": "Summary",
                            "Description": summary
                        })
                    else:
                        records.append({
                            "Step": "Info",
                            "Description": line
                        })
                data = records
        else:
            data = raw_data
        
        # Normalize to list of dictionaries format
        records = []
        if isinstance(data, dict):
            records.append(data)
        elif isinstance(data, list):
            records.extend(data)
        else:
            records.append({"Description": str(data)})
        
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

async def save_step_log(input: SaveStepLogInput):
    """Save step execution details to Excel for logging and debugging"""
    try:
        # Generate filename with timestamp
        timestamp = input.timestamp or datetime.now()
        timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
        safe_step_name = "".join(c if c.isalnum() else "_" for c in input.step_name)
        file_stem = f"{timestamp_str}_{safe_step_name}"
        file_path = STEP_LOGS_DIR / f"{file_stem}.xlsx"
        
        # Prepare log records
        records = []
        
        # Add basic step information
        base_info = {
            "Step": input.step_name,
            "Status": input.status,
            "Timestamp": timestamp.isoformat()
        }
        
        # Add additional info if provided
        if input.additional_info:
            base_info.update({f"Info_{k}": v for k, v in input.additional_info.items()})
        
        # Create output data record if provided
        if input.output_data is not None:
            output_record = base_info.copy()
            output_record["RecordType"] = "output"
            
            if isinstance(input.output_data, dict):
                output_record.update(input.output_data)
            elif isinstance(input.output_data, str):
                try:
                    parsed_output = json.loads(input.output_data)
                    if isinstance(parsed_output, dict):
                        output_record.update(parsed_output)
                    else:
                        output_record["OutputValue"] = parsed_output
                except json.JSONDecodeError:
                    # Parse step-by-step text
                    lines = input.output_data.strip().split("\n")
                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue
                        new_record = output_record.copy()
                        if line.startswith("Step"):
                            step_num, desc = line.split(":", 1)
                            new_record["Step"] = step_num.strip()
                            new_record["Description"] = desc.strip()
                        elif "summary" in line.lower():
                            new_record["Step"] = "Summary"
                            new_record["Description"] = line.replace("Summary:", "").strip()
                        else:
                            new_record["Description"] = line
                        records.append(new_record)
                    output_record = None
            elif isinstance(input.output_data, list):
                for item in input.output_data:
                    new_record = output_record.copy()
                    if isinstance(item, dict):
                        new_record.update(item)
                    else:
                        new_record["OutputValue"] = item
                    records.append(new_record)
                output_record = None
            
            if output_record:
                records.append(output_record)
        
        # Create error data record if provided
        if input.error_data is not None:
            error_record = base_info.copy()
            error_record["RecordType"] = "error"
            
            if isinstance(input.error_data, dict):
                error_record.update(input.error_data)
            elif isinstance(input.error_data, str):
                error_record["ErrorMessage"] = input.error_data
            elif isinstance(input.error_data, list):
                error_record["ErrorMessages"] = "; ".join(str(e) for e in input.error_data)
            
            records.append(error_record)
        
        # If no specific output or error data, just save the base info
        if not records:
            records.append(base_info)
        
        # Create DataFrame
        df = pd.DataFrame(records)
        
        # Save to Excel
        df.to_excel(file_path, index=False)
        
        return {
            "status": "success",
            "result": f"Step log saved to {file_path}",
            "file_path": str(file_path),
            "columns": list(df.columns),
            "error": None
        }
    except Exception as e:
        logger.error(f"Error saving step log: {e}")
        return {
            "status": "failed",
            "result": None,
            "error": str(e)
        }