import sys # Add sys import
print("--- Starting api/main.py ---", file=sys.stderr) # Print to stderr

try:
    from fastapi import FastAPI, HTTPException, File, UploadFile, Form
    from pydantic import BaseModel
    from typing import Optional, List
    print("--- Imported FastAPI/Pydantic ---", file=sys.stderr)

    # Print before the crucial import
    print("--- Importing Supabase client ---", file=sys.stderr)
    from utils.supabase.db import supabase
    print("--- Supabase client imported successfully ---", file=sys.stderr)

    import traceback
    from api.resume_extraction import extract_pdf_text, extract_titles_and_skills
    from api.search_rapidapi import router as search_router
    from io import BytesIO
    #from api.search_google_api import router as google_search_router
    #from archived.pinecone_sync import router as pinecone_router
    #from archived.pinecone_search import router as pinecone_search_router
    from api.skill_insights import router as insights_router
    import asyncio
    import logging
    print("--- Imported other modules ---", file=sys.stderr)

    # CORS Middleware (ensure it's here if you added it)
    from fastapi.middleware.cors import CORSMiddleware
    print("--- Imported CORS ---", file=sys.stderr)

except Exception as import_err:
    print(f"---!!! IMPORT ERROR: {import_err} !!!---", file=sys.stderr)
    # Optionally print full traceback
    import traceback
    traceback.print_exc(file=sys.stderr)
    raise # Re-raise the exception to ensure the app stops

print("--- Creating FastAPI app instance ---", file=sys.stderr)
app = FastAPI()
print("--- FastAPI app instance created ---", file=sys.stderr)


# Add CORS middleware (ensure origins allow testing or your future Streamlit URL)
origins = [
    "https://ai-boosted-job-search-agent.streamlit.app/", # The deployed Streamlit app URL
    "http://localhost:8501",              # Keep for local Streamlit testing
    # Add any other specific origins if needed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
print("--- CORS Middleware added ---", file=sys.stderr)

# Configure logger for this endpoint (might move later)
logger = logging.getLogger("api_main") # Give it a distinct name
logging.basicConfig(level=logging.INFO, stream=sys.stderr, format='%(levelname)s:%(name)s:%(message)s')
print("--- Logger configured ---", file=sys.stderr)

# Pydantic models for request validation
class JobSearch(BaseModel):
    title: str
    location: str
    description: Optional[str] = None




@app.post("/api/users/upload-analyze-resume")
async def upload_analyze_resume(
    user_id: str = Form(...),
    resumes: List[UploadFile] = File(...)
):
    logger.info(f"Received resume upload/analysis request for user_id: {user_id}")
    resume_texts = []
    processed_files_count = 0
    try:
        # 1. Process PDFs
        for resume in resumes:
            if resume.filename.lower().endswith('.pdf'):
                content = await resume.read()
                pdf_file = BytesIO(content)
                try:
                    text = extract_pdf_text(pdf_file)
                    if text:
                        resume_texts.append(text)
                        processed_files_count += 1
                        logger.info(f"Successfully extracted text from {resume.filename} for user {user_id}")
                    else:
                        logger.warning(f"Extracted empty text from {resume.filename} for user {user_id}")
                except Exception as pdf_err:
                    logger.error(f"Error extracting text from {resume.filename} for user {user_id}: {pdf_err}")
            else:
                logger.warning(f"Skipping non-PDF file: {resume.filename} for user {user_id}")

        if not resume_texts:
            raise HTTPException(status_code=400, detail="No valid PDF resumes processed or text extracted.")

        # 2. Extract Titles/Skills using LLM
        combined_resume_text = " \n\n--- RESUME SEPARATOR ---\n\n ".join(resume_texts)
        logger.info(f"Calling LLM for title/skill extraction for user {user_id}...")
        extracted_data = await extract_titles_and_skills(combined_resume_text)
        suggested_titles = extracted_data.get("titles", [])
        extracted_skills = extracted_data.get("skills", [])
        logger.info(f"LLM extraction complete for user {user_id}. Titles: {len(suggested_titles)}, Skills: {len(extracted_skills)}")


        # 3. Update Supabase User Record
        update_payload = {
            "resumes": resume_texts,
            "suggested_titles": suggested_titles,
            "extracted_skills": extracted_skills
        }
        logger.info(f"Attempting Supabase update for user {user_id}...")

        # --- Database Interaction (using run_in_executor for sync Supabase client) ---
        loop = asyncio.get_running_loop()
        update_result = await loop.run_in_executor(
            None,
            lambda: supabase.table("users")
                       .update(update_payload)
                       .eq("user_id", user_id)
                       .execute()
        )
        # --- End Database Interaction ---

        # Check result carefully - .execute() returns an APIResponse object
        if hasattr(update_result, 'data') and update_result.data:
             logger.info(f"Successfully updated user record for {user_id}")
             # Return extracted data along with success message
             return {
                 "success": True,
                 "message": f"Successfully processed {processed_files_count} resume(s) and updated profile.",
                 "suggested_titles": suggested_titles,
                 "extracted_skills": extracted_skills
             }
        elif hasattr(update_result, 'error') and update_result.error:
             logger.error(f"Supabase update failed for user {user_id}: {update_result.error}")
             raise HTTPException(status_code=500, detail=f"Database update failed: {update_result.error.message}")
        else:
             # This might happen if the user_id didn't match any row or RLS prevented update
             logger.warning(f"Supabase update for user {user_id} completed but returned no data/rows affected. User may not exist or RLS issue?. Response: {update_result}")
             # Check if data is empty list, which means update happened but affected 0 rows matching the filter
             if hasattr(update_result, 'data') and not update_result.data:
                 raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found or no changes needed.")
             raise HTTPException(status_code=500, detail="Failed to update user profile in database (unknown reason).")

    except HTTPException as he:
        # Log the specific HTTP exception details if helpful
        logger.error(f"HTTP Exception during resume processing for user {user_id}: Status={he.status_code}, Detail={he.detail}")
        raise he # Re-raise specific known errors
    except Exception as e:
        logger.error(f"Unexpected error processing resume upload for user {user_id}: {str(e)}")
        error_details = traceback.format_exc()
        logger.error(error_details)
        raise HTTPException(status_code=500, detail=f"An internal error occurred during resume processing.")

app.include_router(search_router, prefix="/api")
#app.include_router(google_search_router, prefix="/api")
#app.include_router(pinecone_router, prefix="/api")
#app.include_router(pinecone_search_router, prefix="/api")
app.include_router(insights_router, prefix="/api")
