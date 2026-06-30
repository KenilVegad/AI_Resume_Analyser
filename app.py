from flask import Flask, render_template, request,redirect,session
from db import Base,engine,SessionLocal
from ai import analyze_resume
import model
import PyPDF2
import docx
import json

app = Flask(__name__)
app.secret_key = "secret123"

Base.metadata.create_all(bind=engine)

#Home
@app.route("/")
def home():
    if "user" in session:
        return redirect("/dashboard")
    return redirect("/login")

#Signup
@app.route("/signup", methods=["GET","POST"])
def signup():
    db = SessionLocal()

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        existing_user = db.query(model.User).filter_by(email=email).first()
        if existing_user:
            return "User already Exists"
        
        user = model.User(email=email, password=password)
        db.add(user)
        db.commit()

        return redirect("/login")
    
    return render_template("signup.html")


#Login
@app.route("/login",methods=["GET","POST"])
def login():
    db =SessionLocal()

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        users = db.query(model.User).all()

        user = db.query(model.User).filter_by(email=email ,password=password).first()

        if user:
            session["user"] = user.email
            return redirect("/dashboard")
        else:
            return "Invalid credential"
        
    return render_template("login.html")


#Dashbord
@app.route("/dashboard",methods=["GET","POST"])
def dashboard():
    if "user" not in session:
        return redirect("/login")
    
    result = None
    resume_text = ""
    user_goal = ""

    if request.method == "POST":
        user_goal = request.form.get("role")

        file = request.files.get("file")
        
        #file handling
        if file and file.filename != "":
            if file.filename.endswith(".pdf"):
                try:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text() or ""
                    resume_text = text
                except Exception as e:
                    result ={"error": f"PDF error: {str(e)}"}

        elif file.filename.endswith(".docx"):
            try:

                doc= docx.Document(file)
                text = ""
                for para in doc.paragraphs:
                    text += para.text +"\n"
                resume_text = text
            except Exception as e:
                result = {"error": f"Docx error: {str(e)}"}
    
        if resume_text and user_goal:
            try:
                result = analyze_resume(resume_text,user_goal)

                #save to db
                db = SessionLocal()
                user = db.query(model.User).filter_by(email=session["user"]).first()

                reports = model.Report(
                    user_id = user.id,
                    resume_text = resume_text,
                    result = json.dumps(result)
                )

                db.add(reports)
                db.commit()
        
            except Exception as e:
                result = {"error" : f"AI error: {str(e)}"}

    return render_template(
        "dashboard.html",
        user=session["user"],
        result = result
    )

#history
@app.route("/history")
def history():
    if "user" not in session:
        return redirect("/login")
    
    db = SessionLocal()
    user = db.query(model.User).filter_by(email=session["user"]).first()

    reports = db.query(model.Report).filter_by(user_id=user.id).all()

    #convert JSON string > dict
    pasred_reports = []
    for r in reports:
        try:
            pasred_result = json.loads(r.result)
        except:
            pasred_result = []

        pasred_reports.append({
            "resume":r.resume_text,
            "result": pasred_result
        })
    
    return render_template("history.html", reports=pasred_reports)

#logout
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")

if __name__ == "__main__":
    app.run(debug=True)