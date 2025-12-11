"""
Entry point for the PR summarizer service.
Run: uvicorn main:app --host 0.0.0.0 --port 8000
"""

from fastapi import FastAPI

from app.routes import router


def create_app() -> FastAPI:
    app = FastAPI(title="PR Summarizer", version="0.2.0")
    app.include_router(router)
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

