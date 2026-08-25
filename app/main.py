from fastapi import FastAPI


app = FastAPI(title="ForgeQueue")


@app.get("/health")
def read_health() -> dict[str, str]:
    return {"status": "ok"}