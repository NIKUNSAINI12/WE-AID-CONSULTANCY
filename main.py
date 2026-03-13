from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os

app = FastAPI(title="We Aid Consultancy API")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Mount static files (for CSS, JS, and Images if any are local)
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "stitch_assets")), name="static")

templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "stitch_assets"))

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home_section_refined.html", {"request": request})

@app.get("/blog", response_class=HTMLResponse)
async def blog(request: Request):
    return templates.TemplateResponse("blog_insights.html", {"request": request})

@app.get("/pricing", response_class=HTMLResponse)
async def pricing(request: Request):
    return templates.TemplateResponse("pricing_refined.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
