from fastapi import FastAPI
from cors import setup_cors
from service.db import init_db
from routes import auth_routes, resume_routes, job_routes, recommendation_routes, dashboard_routes, user_profile_routes, candidates_routes, matches_routes
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="Resume_job Matcher",
    description="API for managing job postings, candidates, and recruitment workflows",
    version="1.0.0",
    lifespan=lifespan
)

setup_cors(app)

@app.get("/")
def home():
    return {"message": "Resume-Job Matcher API is running 🚀"}

# Routers
app.include_router(auth_routes.router)
app.include_router(resume_routes.router)
app.include_router(job_routes.router)
app.include_router(recommendation_routes.router)
app.include_router(dashboard_routes.router)
app.include_router(user_profile_routes.router)
app.include_router(candidates_routes.router)
app.include_router(matches_routes.router)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)