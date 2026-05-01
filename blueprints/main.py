from flask import Blueprint, render_template, request, session, redirect, url_for
from flask_login import login_required, current_user
from database.extensions import db
from database.models import User, LawyerProfile, Case
from chatbot.llm_services import analyze_legal_case, chat_with_legal_bot

main_bp = Blueprint('main', __name__)

@main_bp.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        case_text = request.form.get("case")
        if case_text:
            analysis = analyze_legal_case(case_text)
            
            # Save the case to the DB if the user is logged in
            if current_user.is_authenticated and current_user.role == 'client':
                new_case = Case(
                    title=analysis.get('summary', 'Legal Case')[:50] + "...",
                    description=case_text,
                    category=analysis.get('key_issues', ['General'])[0] if analysis.get('key_issues') else 'General',
                    client_id=current_user.id,
                    status='Pending Analysis'
                )
                db.session.add(new_case)
                db.session.commit()
                
            return render_template("result.html", case=case_text, analysis=analysis)
    return render_template("index.html")

@main_bp.route("/dashboard")
@login_required
def dashboard():
    # Fetch cases for the user
    if current_user.role == 'lawyer':
        cases = Case.query.filter_by(lawyer_id=current_user.id).order_by(Case.created_at.desc()).all()
    elif current_user.role == 'client':
        cases = Case.query.filter_by(client_id=current_user.id).order_by(Case.created_at.desc()).all()
    else:
        cases = Case.query.order_by(Case.created_at.desc()).all()
        
    active_cases = len([c for c in cases if c.status != 'Resolved'])
    ai_interactions = len(session.get("chat_history", [])) // 2
    
    if current_user.role == 'lawyer':
        return render_template("dashboard/lawyer.html", cases=cases, active_cases=active_cases)
    elif current_user.role == 'admin':
        return render_template("dashboard/admin.html")
    else:
        return render_template("dashboard/client.html", cases=cases, active_cases=active_cases, ai_interactions=ai_interactions)

@main_bp.route("/chatbot", methods=["GET", "POST"])
def chatbot():
    if "chat_history" not in session:
        session["chat_history"] = []
        
    if request.method == "POST":
        question = request.form.get("question")
        if question:
            try:
                response = chat_with_legal_bot(question, session["chat_history"])
                session["chat_history"].append({"role": "user", "content": question})
                session["chat_history"].append({"role": "ai", "content": response})
                session.modified = True
            except Exception as e:
                session["chat_history"].append({"role": "user", "content": question})
                session["chat_history"].append({"role": "ai", "content": f"Error: {str(e)}. Please check your API keys."})
                session.modified = True

    return render_template("chatbot.html")

import os
from werkzeug.utils import secure_filename

from chatbot.document_processor import extract_text_from_file

@main_bp.route("/chatbot/upload", methods=["POST"])
def chatbot_upload():
    from flask import jsonify
    if "chat_history" not in session:
        session["chat_history"] = []

    if 'document' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['document']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    filename = secure_filename(file.filename)
    upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)

    # Extract text from document
    try:
        text = extract_text_from_file(filepath)
    except Exception as e:
        text = ""

    user_msg = f"📄 Please analyze this document: **{filename}**"
    session["chat_history"].append({"role": "user", "content": user_msg})

    if text and len(text.strip()) > 20 and not text.startswith("Error") and not text.startswith("Unsupported"):
        truncated_text = text[:5000]
        try:
            from chatbot.llm_services import analyze_document_text
            analysis = analyze_document_text(truncated_text, filename)

            ai_content = {
                "answer": f"✅ I've read your document **'{filename}'**. Here is my complete legal analysis:",
                "relevant_sections": analysis.get('relevant_laws', []),
                "analysis": analysis,
                "disclaimer": "⚠️ This is AI-generated legal guidance. Always consult a qualified lawyer before taking legal action."
            }
        except Exception as e:
            ai_content = f"I read your document but encountered an AI error: {str(e)}"
    else:
        err_detail = text if text else "No readable text found."
        ai_content = f"⚠️ Could not extract text from **'{filename}'**. Make sure it's a clear PDF or .txt file. Details: {err_detail}"

    session["chat_history"].append({"role": "ai", "content": ai_content})
    session.modified = True

    # Return the rendered HTML snippet for the new messages
    from flask import render_template_string
    user_bubble = f'''<div class="chat-bubble chat-user shadow-sm">
        <p class="mb-0 text-white">{user_msg}</p>
    </div>'''

    return jsonify({"success": True, "reload": True})



from flask import send_file
import io
from fpdf import FPDF
import json

@main_bp.route("/generate_report", methods=["POST"])
def generate_report():
    analysis_json = request.form.get("analysis_json")
    if not analysis_json:
        return redirect(url_for('main.index'))
        
    try:
        analysis = json.loads(analysis_json)
    except:
        return "Invalid JSON", 400
        
    pdf = FPDF()
    pdf.add_page()
    
    # Title
    pdf.set_font("Helvetica", style="B", size=24)
    pdf.cell(0, 15, "AI Legal Case Analysis", ln=True, align="C")
    pdf.ln(5)
    
    # Summary
    pdf.set_font("Helvetica", style="B", size=14)
    pdf.cell(0, 10, "Summary", ln=True)
    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(0, 8, analysis.get("summary", "N/A"))
    pdf.ln(5)
    
    # Key Issues
    pdf.set_font("Helvetica", style="B", size=14)
    pdf.cell(0, 10, "Key Issues", ln=True)
    pdf.set_font("Helvetica", size=12)
    for issue in analysis.get("key_issues", []):
        pdf.multi_cell(0, 8, f"- {issue}")
    pdf.ln(5)
    
    # Relevant Laws
    pdf.set_font("Helvetica", style="B", size=14)
    pdf.cell(0, 10, "Relevant Laws", ln=True)
    pdf.set_font("Helvetica", size=12)
    for law in analysis.get("relevant_laws", []):
        pdf.multi_cell(0, 8, f"- {law.get('law', '')}: {law.get('description', '')}")
    pdf.ln(5)
    
    # Potential Outcome
    pdf.set_font("Helvetica", style="B", size=14)
    pdf.cell(0, 10, "Potential Outcome", ln=True)
    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(0, 8, analysis.get("potential_outcome", "N/A"))
    pdf.ln(5)
    
    # Output to BytesIO
    pdf_bytes = pdf.output(dest="S").encode("latin1", "replace") # PyPDF2 output to string, encode
    # fpdf2 actually outputs bytes directly if no dest is provided in recent versions, 
    # but to be safe: pdf.output() returns bytearray in fpdf2
    
    out = io.BytesIO(pdf.output())
    
    return send_file(
        out,
        mimetype='application/pdf',
        as_attachment=True,
        download_name='Legal_Analysis_Report.pdf'
    )

@main_bp.route("/clear_chat")
def clear_chat():
    session.pop("chat_history", None)
    return redirect(url_for("main.chatbot"))

@main_bp.route("/lawyers")
def lawyers():
    profiles = LawyerProfile.query.join(User).all()
    return render_template("lawyers.html", lawyers=profiles)

@main_bp.route("/cases")
@login_required
def cases():
    if current_user.role == 'client':
        user_cases = Case.query.filter_by(client_id=current_user.id).all()
    elif current_user.role == 'lawyer':
        user_cases = Case.query.filter_by(lawyer_id=current_user.id).all()
    else:
        user_cases = Case.query.all()
    return render_template("cases.html", cases=user_cases)

@main_bp.route("/case/<int:case_id>")
@login_required
def case_detail(case_id):
    case = Case.query.get_or_404(case_id)
    # Check access
    if current_user.role == 'client' and case.client_id != current_user.id:
        return redirect(url_for('main.cases'))
    if current_user.role == 'lawyer' and case.lawyer_id and case.lawyer_id != current_user.id:
        return redirect(url_for('main.cases'))
        
    return render_template("case_detail.html", case=case)

@main_bp.route("/procedures")
def procedures():
    return render_template("procedures.html")

@main_bp.route("/laws")
def laws():
    return render_template("laws.html")

@main_bp.route("/contacts")
def contacts():
    return render_template("contacts.html")
@main_bp.route("/request_consultation/<int:lawyer_user_id>")
@login_required
def request_consultation(lawyer_user_id):
    if current_user.role != 'client':
        from flask import flash
        flash("Only clients can request consultations.", "danger")
        return redirect(url_for('main.lawyers'))

    lawyer = User.query.get_or_404(lawyer_user_id)
    if lawyer.role != 'lawyer':
        from flask import flash
        flash("Invalid lawyer selected.", "danger")
        return redirect(url_for('main.lawyers'))

    # Create a new Case as a consultation request
    new_case = Case(
        title=f"Consultation with {lawyer.name}",
        description=f"Consultation request initiated by {current_user.name}.",
        client_id=current_user.id,
        lawyer_id=lawyer.id,
        status='Pending'
    )
    
    db.session.add(new_case)
    db.session.commit()
    
    from flask import flash
    flash(f"Consultation request sent to {lawyer.name}!", "success")
    return redirect(url_for('main.cases'))
