import uuid
import aiofiles
from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

# Import the services you created in the previous step.
# Make sure the service files are in backend/app/services/
from .services.stt_service import transcribe_with_whisper
from .services.diarize_service import diarize_audio
from .services.summary_service import summarize_text
from .services.processing_pipeline import merge_transcript_and_diarization

app = FastAPI()

# Mount the 'frontend' directory to serve the index.html file and any other static assets
# This assumes your directory structure is:
# live-meeting-summarizer/
# ├── backend/
# └── frontend/
# You run the server from the 'backend' directory.
app.mount("/static", StaticFiles(directory="../frontend"), name="static")


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Serves the main HTML upload page."""
    with open("../frontend/index.html") as f:
        return HTMLResponse(content=f.read(), status_code=200)


@app.post("/process-meeting", response_class=HTMLResponse)
async def process_meeting_endpoint(file: UploadFile = File(...)):
    """
    Receives an audio file, processes it, and returns an HTML page with the results.
    """
    # --- 1. Save the file ---
    file_path = f"recordings/{uuid.uuid4()}_{file.filename}"
    async with aiofiles.open(file_path, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)

    # --- 2. Run the processing pipeline (this will take time) ---
    # Note: For this simple version, the user's browser will wait until this is all done.
    transcript_result = transcribe_with_whisper(file_path)
    diarization_result = diarize_audio(file_path)
    
    # --- 3. Merge and Summarize ---
    diarized_text = merge_transcript_and_diarization(transcript_result, diarization_result)
    summary = summarize_text(diarized_text)

    # --- 4. Create an HTML response with the results ---
    # Using triple quotes for a multi-line string to build the HTML
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Meeting Summary</title>
        <style>
            body {{ font-family: sans-serif; background-color: #f4f4f9; color: #333; padding: 20px; }}
            .container {{ max-width: 800px; margin: auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            h1, h2 {{ color: #444; border-bottom: 2px solid #eee; padding-bottom: 10px;}}
            pre {{ background-color: #fafafa; padding: 15px; border-radius: 5px; white-space: pre-wrap; word-wrap: break-word; font-size: 14px; line-height: 1.6; }}
            a {{ text-decoration: none; color: #007bff; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Meeting Results</h1>
            <a href="/">&larr; Process another file</a>
            
            <h2>Summary</h2>
            <pre>{summary}</pre>
            
            <h2>Full Diarized Transcript</h2>
            <pre>{diarized_text}</pre>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)

