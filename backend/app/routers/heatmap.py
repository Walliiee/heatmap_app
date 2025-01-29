from fastapi import APIRouter, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
import pandas as pd
import io
import json
import pytz
from datetime import datetime, timezone
import kaleido  # Ensure kaleido is imported

router = APIRouter()

def parse_json(contents):
    """
    Parse JSON from multiple GenAI sources, including ChatGPT with 'mapping'.
    Returns a DataFrame with 'timestamp' and 'text' columns.
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

    # 2. Claude-like
    if isinstance(data, list) and len(data) > 0 and "chat_messages" in data[0]:
        rows = []
        for conversation in data:
            for msg in conversation.get("chat_messages", []):
                rows.append({
                    "timestamp": msg.get("created_at"),
                    "text": msg.get("text", "")
                })
        return pd.DataFrame(rows)

    # 3. ChatGPT-like with "conversations"
    if isinstance(data, dict) and "conversations" in data:
        rows = []
        for convo in data["conversations"]:
            rows.append({
                "timestamp": convo.get("timestamp"),
                "text": convo.get("text", "")
            })
        return pd.DataFrame(rows)

@router.post("/api/heatmap")
async def generate_heatmap(file: UploadFile):
    try:
        # 1. Read JSON contents
        contents = await file.read()
        
        # 2. Parse JSON into a DataFrame
        df = parse_json(contents)

        # 3. Validate columns
        if 'timestamp' not in df.columns or 'text' not in df.columns:
            raise HTTPException(status_code=400, detail="Parsed data must contain 'timestamp' and 'text' fields.")

        df['usage'] = df['text'].apply(len)
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df = df.dropna(subset=['timestamp'])
        if df.empty:
            raise HTTPException(status_code=400, detail="No valid timestamps found.")

        # Extract month/day or whatever grouping you want
        df['month'] = df['timestamp'].dt.month
        df['day'] = df['timestamp'].dt.day

        # 6. Pivot to form day x month matrix
        pivot = df.pivot_table(
            index='day',
            columns='month',
            values='usage',
            aggfunc='sum',
            fill_value=0
        )
        if pivot.empty:
            raise HTTPException(status_code=400, detail="Pivot table is empty. No valid usage data to plot.")

        # 7. Create the heatmap
        fig = px.imshow(
            pivot,
            labels=dict(x="Month", y="Day", color="Usage"),
            x=pivot.columns,
            y=pivot.index,
            color_continuous_scale="Viridis"
        )

        # 8. Save plot to memory as PNG
        img_bytes = io.BytesIO()
        fig.write_image(img_bytes, format="png", engine="kaleido")
        img_bytes.seek(0)

        # Log success
        print("Heatmap generated successfully")

        return StreamingResponse(img_bytes, media_type="image/png")

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        print(f"Error generating heatmap: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
