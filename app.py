"""Application"""
import uvicorn
from fastapi import FastAPI
from routers.sample_router import router as sample_router

# Initialize FastAPI app
app = FastAPI(
    title="Template API",
    description="A bare minimum FastAPI template with separation of concerns.",
    version="1.0.0"
)

# Include routers
app.include_router(sample_router, prefix="/api/v1")

# Root route for health check
@app.get("/")
async def root():
    return {"message": "Service is running", "health": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3000)
