import os

import uvicorn
from fastapi import FastAPI
from application.controller.station_controller import router as station_route
from application.controller.auth_controller import router as auth_route
from application.controller.station_batch import router as station_batch


app = FastAPI(title="Gerenciamento das estações", root_path="/station_manager")

app.include_router(auth_route)
app.include_router(station_route)
app.include_router(station_batch)

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8004")),
        reload=True,
    )

