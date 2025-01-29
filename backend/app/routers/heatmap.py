from fastapi import APIRouter, UploadFile, HTTPException, File, Query
from fastapi.responses import JSONResponse
import pandas as pd
import io
import json
from datetime import datetime, timedelta
import numpy as np

router = APIRouter()

def parse_chatgpt_json(contents):
    """
    Parse JSON from ChatGPT conversations.
    """
    data = json.loads(contents)
    rows = []
    for conversation in data:
        mapping = conversation.get("mapping", {})
        for node_id, node_data in mapping.items():
            message = node_data.get("message")
            if not message:
                continue
            timestamp = message.get("create_time")
            content = message.get("content", {})
            parts = content.get("parts", [])
            if all(isinstance(p, str) for p in parts):
                text = "\n".join(parts)
            else:
                text_pieces = []
                for p in parts:
                    if isinstance(p, dict) and "text" in p:
                        text_pieces.append(p["text"])
                    elif isinstance(p, str):
                        text_pieces.append(p)
                text = "\n".join(text_pieces)
            rows.append({"timestamp": timestamp, "text": text})
    return pd.DataFrame(rows)

def parse_claude_json(contents):
    """
    Parse JSON from Claude conversations.
    """
    data = json.loads(contents)
    rows = []
    for conversation in data:
        for msg in conversation.get("chat_messages", []):
            timestamp = msg.get("created_at")
            text = msg.get("text", "")
            rows.append({"timestamp": timestamp, "text": text})
    return pd.DataFrame(rows)

def parse_json(contents):
    """
    Generic JSON parser.
    """
    data = json.loads(contents)
    rows = []
    for entry in data:
        timestamp = entry.get("timestamp") or entry.get("create_time") or entry.get("created_at")
        text = entry.get("text", "")
        if timestamp:
            rows.append({"timestamp": timestamp, "text": text})
    return pd.DataFrame(rows)

@router.post("/api/heatmap")
async def generate_heatmap(
    files: list[UploadFile] = File(...),
    year: int = Query(None, description="Filter data by year."),
):
    try:
        all_data = []

        for file in files:
            contents = await file.read()
            filename = file.filename.lower()
            if 'claude' in filename:
                df = parse_claude_json(contents)
            elif 'gpt' in filename or 'chatgpt' in filename:
                df = parse_chatgpt_json(contents)
            else:
                df = parse_json(contents)
            all_data.append(df)

        df = pd.concat(all_data, ignore_index=True)

        if 'timestamp' not in df.columns or 'text' not in df.columns:
            raise HTTPException(status_code=400, detail="Parsed data must contain 'timestamp' and 'text' fields.")

        df['usage'] = df['text'].apply(len)
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df = df.dropna(subset=['timestamp'])
        if df.empty:
            raise HTTPException(status_code=400, detail="No valid timestamps found.")

        if year:
            df = df[df['timestamp'].dt.year == year]
        else:
            year = df['timestamp'].dt.year.min()

        if df.empty:
            raise HTTPException(status_code=400, detail="No valid timestamps found for the specified year.")

        df['week'] = df['timestamp'].dt.isocalendar().week
        df['weekday'] = df['timestamp'].dt.weekday
        df['month'] = df['timestamp'].dt.month

        usage_df = df.groupby(['week', 'weekday'], as_index=False).agg({'usage': 'sum'})

        min_week = usage_df['week'].min()
        max_week = usage_df['week'].max() + 1

        all_weeks = range(min_week, max_week + 1)
        all_weekdays = range(7)

        usage_df = usage_df.set_index(['week', 'weekday']).unstack(fill_value=0)
        usage_df = usage_df.reindex(all_weeks, fill_value=0)

        usage_df.columns = usage_df.columns.get_level_values(1)
        usage_df = usage_df.reset_index()

        usage_df.rename(columns={'week': 'Week'}, inplace=True)
        usage_df.rename(columns=lambda x: f'Day_{x}' if isinstance(x, int) else x, inplace=True)

        for day in all_weekdays:
            day_col = f'Day_{day}'
            if day_col not in usage_df.columns:
                usage_df[day_col] = 0

        x = list(usage_df['Week'])
        y = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        z = usage_df[[f'Day_{i}' for i in all_weekdays]].values.tolist()

        # Add month names
        month_names = []
        for week in x:
            week_start = datetime.strptime(f'{year}-W{int(week)-1}-1', "%Y-W%W-%w")
            month_names.append(week_start.strftime('%b'))

        return JSONResponse(content={"x": x, "y": y, "z": z, "months": month_names})

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        print(f"Error generating heatmap: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
