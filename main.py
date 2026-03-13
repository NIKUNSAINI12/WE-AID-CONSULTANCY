from fastapi import FastAPI, Request, Form, UploadFile, File, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from supabase import create_client, Client
import os
import shutil
from datetime import datetime, timezone
from dotenv import load_dotenv
import pytz # Add if available, but we'll use standard now

load_dotenv()

app = FastAPI(title="We Aid Consultancy API")

# Middleware for sessions (login memory)
# IMPORTANT: Put a random string in your .env for SESSION_SECRET
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET", "super-secret-key-123"))

# Supabase Config
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "stitch_assets")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "stitch_assets"))

# --- Helper Functions ---
def get_current_user(request: Request):
    return request.session.get("user")

# --- Routes ---

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home_section_refined.html", {"request": request, "user": get_current_user(request)})

@app.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request, "user": get_current_user(request)})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(request: Request, email: str = Form(...), password: str = Form(...)):
    try:
        response = supabase.table("users").select("*").eq("email", email).eq("password", password).execute()
        user = response.data[0] if response.data else None
        
        if user:
            request.session["user"] = user
            return RedirectResponse(url="/", status_code=303)
        
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})
    except Exception as e:
        print(f"Login Error: {str(e)}")
        return HTMLResponse(content=f"Login Error: {str(e)}", status_code=500)

@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.post("/signup")
async def signup(request: Request, name: str = Form(...), email: str = Form(...), password: str = Form(...), phone: str = Form(...)):
    try:
        # Check if email already exists
        existing = supabase.table("users").select("email").eq("email", email).execute()
        if existing.data:
            return templates.TemplateResponse("signup.html", {"request": request, "error": "This email is already registered."})

        user_data = {
            "name": name,
            "email": email,
            "password": password,
            "phone": phone,
            "role": "viewer",
            "is_contacted": "no",
            "response": ""
        }
        supabase.table("users").insert(user_data).execute()
        
        supabase.table("users").insert(user_data).execute()

        return RedirectResponse(url="/login?signup=success", status_code=303)
    except Exception as e:
        print(f"Signup Error: {str(e)}")
        return HTMLResponse(content=f"Signup Error: {str(e)}", status_code=500)

@app.get("/blog/{post_id}", response_class=HTMLResponse)
async def blog_post(request: Request, post_id: str):
    res = supabase.table("posts").select("*").eq("id", post_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Post not found")
    
    return templates.TemplateResponse("blog_post.html", {
        "request": request, 
        "post": res.data[0], 
        "user": get_current_user(request)
    })

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)

@app.get("/blog", response_class=HTMLResponse)
async def blog(request: Request):
    response = supabase.table("posts").select("*").order("created_at", desc=True).execute()
    posts = response.data
    return templates.TemplateResponse("blog_insights.html", {"request": request, "posts": posts, "user": get_current_user(request)})

@app.post("/subscribe")
async def subscribe(email: str = Form(...)):
    try:
        supabase.table("newsletters").insert({"email": email}).execute()
        return RedirectResponse(url="/blog?subscribed=true", status_code=303)
    except:
        return RedirectResponse(url="/blog?error=already_subscribed", status_code=303)

@app.get("/admin", response_class=HTMLResponse)
async def admin(request: Request):
    user = get_current_user(request)
    if not user or user["role"] != "admin":
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse("admin_blog.html", {"request": request, "user": user})

@app.post("/upload-blog")
async def upload_blog(
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    author: str = Form(...),
    role: str = Form(...),
    category: str = Form(...),
    read_time: str = Form(...),
    image: UploadFile = File(...)
):
    user = get_current_user(request)
    if not user or user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    try:
        file_extension = image.filename.split(".")[-1]
        file_name = f"{datetime.now().timestamp()}.{file_extension}"
        file_content = await image.read()
        
        supabase.storage.from_("blog-images").upload(path=file_name, file=file_content, file_options={"content-type": image.content_type})
        image_url = supabase.storage.from_("blog-images").get_public_url(file_name)
        
        supabase.table("posts").insert({
            "title": title, 
            "description": description, 
            "author": author, 
            "role": role, 
            "category": category, 
            "read_time": read_time,
            "display_date": datetime.now().strftime("%B %d, %Y"),
            "image_url": image_url
        }).execute()
        
        return RedirectResponse(url="/blog", status_code=303)
    except Exception as e:
        return HTMLResponse(content=f"Error: {str(e)}", status_code=500)

@app.get("/admin/edit/{post_id}", response_class=HTMLResponse)
async def edit_blog_page(request: Request, post_id: str):
    user = get_current_user(request)
    if not user or user["role"] != "admin":
        return RedirectResponse(url="/login", status_code=303)
    
    response = supabase.table("posts").select("*").eq("id", post_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Post not found")
        
    return templates.TemplateResponse("admin_edit_blog.html", {"request": request, "post": response.data[0], "user": user})

@app.post("/admin/edit/{post_id}")
async def update_blog(
    request: Request,
    post_id: str,
    title: str = Form(...),
    description: str = Form(...),
    author: str = Form(...),
    role: str = Form(...),
    category: str = Form(...),
    read_time: str = Form(...),
    image: UploadFile = File(None)
):
    user = get_current_user(request)
    if not user or user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    update_data = {
        "title": title,
        "description": description,
        "author": author,
        "role": role,
        "category": category,
        "read_time": read_time,
        "display_date": datetime.now().strftime("%B %d, %Y")
    }

    try:
        # Only upload new image if provided
        if image and image.filename:
            file_extension = image.filename.split(".")[-1]
            file_name = f"{datetime.now().timestamp()}.{file_extension}"
            file_content = await image.read()
            supabase.storage.from_("blog-images").upload(path=file_name, file=file_content, file_options={"content-type": image.content_type})
            image_url = supabase.storage.from_("blog-images").get_public_url(file_name)
            update_data["image_url"] = image_url

        supabase.table("posts").update(update_data).eq("id", post_id).execute()
        return RedirectResponse(url="/blog", status_code=303)
    except Exception as e:
        return HTMLResponse(content=f"Error: {str(e)}", status_code=500)

@app.post("/register-service")
async def register_service(
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    profession: str = Form(None),
    service_type: str = Form(...),
    description: str = Form(None),
    meeting_date: str = Form(None),
    meeting_time: str = Form(None)
):
    data = {
        "name": name,
        "email": email,
        "phone": phone,
        "profession": profession,
        "service_type": service_type,
        "description": description,
        "meeting_date": meeting_date,
        "meeting_time": meeting_time,
        "status": "uncontacted",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    try:
        supabase.table("registrations").insert(data).execute()
        # Redirect to a permanent Google Meet room
        # You can change this to a dynamic generator later
        return RedirectResponse(url="https://meet.google.com/weaid-consultancy-meeting", status_code=303)
    except Exception as e:
        print(f"Registration Error: {e}")
        return RedirectResponse(url="/?status=error", status_code=303)

@app.get("/admin/leads", response_class=HTMLResponse)
async def admin_leads(request: Request, filter: str = "all", response: str = "all"):
    user = get_current_user(request)
    if not user or user["role"] != "admin":
        return RedirectResponse(url="/login", status_code=303)
    
    # Fetch from registrations
    reg_query = supabase.table("registrations").select("*")
    # Fetch from users (viewer signups)
    user_query = supabase.table("users").select("*").eq("role", "viewer")
    
    # Apply time filter
    if filter == "today":
        # Using UTC today as Supabase stores in UTC
        today = datetime.utcnow().strftime("%Y-%m-%d")
        reg_query = reg_query.gte("created_at", f"{today}T00:00:00")
        user_query = user_query.gte("created_at", f"{today}T00:00:00")
    
    reg_data = reg_query.execute().data
    user_data = user_query.execute().data
    
    # Merge and standardize
    combined_leads = []
    
    for r in reg_data:
        combined_leads.append({
            "id": r["id"],
            "name": r["name"],
            "email": r["email"],
            "phone": r["phone"],
            "service_type": r["service_type"],
            "description": r.get("description", ""),
            "status": r.get("status", "uncontacted"),
            "response": r.get("response", ""),
            "created_at": r["created_at"],
            "source": "registration"
        })
        
    for u in user_data:
        combined_leads.append({
            "id": u["id"],
            "name": u["name"],
            "email": u["email"],
            "phone": u["phone"],
            "service_type": "New User Account",
            "description": "User created a new account.",
            "status": "contacted" if u.get("is_contacted") == "yes" else "uncontacted",
            "response": u.get("response", ""),
            "created_at": u["created_at"],
            "source": "user"
        })
    
    # Apply filters to combined list
    if filter == "uncontacted":
        combined_leads = [l for l in combined_leads if l["status"] == "uncontacted"]
        
    if response != "all":
        combined_leads = [l for l in combined_leads if l["response"] == response]
        
    # Sort by created_at desc
    combined_leads.sort(key=lambda x: x["created_at"], reverse=True)
    
    return templates.TemplateResponse("admin_registrations.html", {
        "request": request, 
        "leads": combined_leads, 
        "user": user,
        "current_filter": filter,
        "current_response": response
    })

@app.post("/admin/leads/update")
async def update_lead(
    request: Request,
    lead_id: str = Form(...),
    lead_source: str = Form(...),
    status: str = Form(...),
    response: str = Form(None)
):
    user = get_current_user(request)
    if not user or user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if lead_source == "registration":
        supabase.table("registrations").update({
            "status": status,
            "response": response
        }).eq("id", lead_id).execute()
    else:
        # Update users table
        is_contacted_val = "yes" if status == "contacted" else "no"
        supabase.table("users").update({
            "is_contacted": is_contacted_val,
            "response": response
        }).eq("id", lead_id).execute()
    
    return RedirectResponse(url="/admin/leads?status=updated", status_code=303)

@app.get("/pricing", response_class=HTMLResponse)
async def pricing(request: Request):
    response = supabase.table("pricing").select("*").execute()
    # Convert list of rows to a simple dict: {"tax_individual": "₹999", ...}
    prices = {item['id']: item['price'] for item in response.data}
    return templates.TemplateResponse("pricing_refined.html", {"request": request, "user": get_current_user(request), "prices": prices})

@app.get("/admin/pricing", response_class=HTMLResponse)
async def admin_pricing(request: Request):
    user = get_current_user(request)
    if not user or user["role"] != "admin":
        return RedirectResponse(url="/login", status_code=303)
    
    response = supabase.table("pricing").select("*").execute()
    return templates.TemplateResponse("admin_pricing.html", {"request": request, "pricing": response.data})

@app.post("/admin/pricing/update")
async def update_pricing(
    request: Request,
    plan_id: str = Form(...),
    price: str = Form(...)
):
    user = get_current_user(request)
    if not user or user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    supabase.table("pricing").update({"price": price}).eq("id", plan_id).execute()
    return RedirectResponse(url="/admin/pricing?status=updated", status_code=303)

@app.post("/admin/delete/{post_id}")
async def delete_blog(request: Request, post_id: str):
    user = get_current_user(request)
    if not user or user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    try:
        # Get the post first to find the image URL
        response = supabase.table("posts").select("image_url").eq("id", post_id).execute()
        if response.data:
            image_url = response.data[0].get("image_url")
            if image_url:
                # Extract filename from URL (assuming standard Supabase public URL)
                file_name = image_url.split("/")[-1]
                try:
                    supabase.storage.from_("blog-images").remove([file_name])
                except:
                    pass # Continue if image removal fails
        
        supabase.table("posts").delete().eq("id", post_id).execute()
        return RedirectResponse(url="/blog?status=deleted", status_code=303)
    except Exception as e:
        return HTMLResponse(content=f"Error: {str(e)}", status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
