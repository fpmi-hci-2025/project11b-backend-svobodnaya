from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI(
    title="Demo FastAPI Service",
    description="Демонстрационный сервис с healthcheck",
    version="1.0.0",
)


@app.get("/healthcheck")
async def healthcheck():
    """Проверка работоспособности приложения"""
    return JSONResponse(
        status_code=200, content={"status": "healthy", "service": "demo-fastapi"}
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
