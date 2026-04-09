import uvicorn

from app.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.web.app:app",
        host="0.0.0.0",
        port=settings.WEB_PORT,
        reload=settings.DEBUG,
        log_level="info",
    )
