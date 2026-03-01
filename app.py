import os
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))

database_url = os.environ.get("DATABASE_URL", "")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "vibe-code-ops-hub-v1")
app.config["SQLALCHEMY_DATABASE_URI"] = database_url or f"sqlite:///{os.path.join(basedir, 'ops_hub.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# ═══════════════════════════════════════════════════════════════
#  MODELS
# ═══════════════════════════════════════════════════════════════

class Partner(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(200), default="")
    focus_area = db.Column(db.String(200), default="")
    quota_scripts = db.Column(db.Integer, default=0)
    quota_videos_edit = db.Column(db.Integer, default=0)
    quota_videos_post = db.Column(db.Integer, default=0)
    daily_logs = db.relationship("DailyLog", backref="partner", lazy=True)


class DailyLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=date.today)
    partner_id = db.Column(db.Integer, db.ForeignKey("partner.id"), nullable=False)
    scripts_written = db.Column(db.Integer, default=0)
    videos_edited = db.Column(db.Integer, default=0)
    videos_posted = db.Column(db.Integer, default=0)
    comments_replied = db.Column(db.Integer, default=0)
    trend_research = db.Column(db.Boolean, default=False)
    hooks_written = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_posted = db.Column(db.Date, nullable=False, default=date.today)
    platform = db.Column(db.String(50), default="")
    hook_used = db.Column(db.Text, default="")
    topic = db.Column(db.String(200), default="")
    length_seconds = db.Column(db.Integer, default=0)
    retention_3s = db.Column(db.Float, default=0)
    retention_50 = db.Column(db.Float, default=0)
    avg_watch_time = db.Column(db.Float, default=0)
    views = db.Column(db.Integer, default=0)
    likes = db.Column(db.Integer, default=0)
    comments_count = db.Column(db.Integer, default=0)
    shares = db.Column(db.Integer, default=0)
    saves = db.Column(db.Integer, default=0)
    format_type = db.Column(db.String(100), default="")
    winner = db.Column(db.Boolean, default=False)


class Hook(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    format_type = db.Column(db.String(100), default="")
    tested = db.Column(db.Boolean, default=False)
    avg_retention_3s = db.Column(db.Float, default=0)
    winning = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class PipelineItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(50), default="queued")
    assigned_to = db.Column(db.Integer, db.ForeignKey("partner.id"), nullable=True)
    due_date = db.Column(db.Date, nullable=True)
    content_type = db.Column(db.String(100), default="")
    notes = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    partner = db.relationship("Partner")


class EmailLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    recipients = db.Column(db.Text, default="")
    subject = db.Column(db.String(300), default="")
    body = db.Column(db.Text, default="")
    template_type = db.Column(db.String(50), default="custom")
    status = db.Column(db.String(20), default="sent")


class AppSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, default="")


class ContentPillar(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, default="")
    color = db.Column(db.String(20), default="#7c6cf0")


class VaultEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(100), default="")
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, default="")
    performance_note = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class MonetizationEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=date.today)
    source = db.Column(db.String(100), default="")
    revenue = db.Column(db.Float, default=0)
    cost = db.Column(db.Float, default=0)
    notes = db.Column(db.Text, default="")


# ═══════════════════════════════════════════════════════════════
#  STATIC SCHEDULE DATA
# ═══════════════════════════════════════════════════════════════

TIME_BLOCKS = [
    {
        "key": "partner1",
        "role": "Research & Script Lead",
        "color": "#7c6cf0",
        "blocks": [
            {"start": "7:00 AM", "end": "7:45 AM", "task": "Trend + Topic Research",
             "detail": "Mine trends, study 5 viral videos, extract patterns"},
            {"start": "7:45 AM", "end": "8:30 AM", "task": "Write 5-10 Short Scripts",
             "detail": "Convert hooks into scripts, keep under 120 words"},
            {"start": "12:00 PM", "end": "12:30 PM", "task": "Review Performance Metrics",
             "detail": "Check 3s retention, completion %, engagement"},
            {"start": "8:00 PM", "end": "8:20 PM", "task": "Queue Ideas for Next Day",
             "detail": "Prepare tomorrow's hook list and topics"},
        ],
        "deliverables": ["15 hooks minimum", "5-10 completed scripts", "Titles + captions drafted"],
    },
    {
        "key": "partner2",
        "role": "Production Lead",
        "color": "#00c897",
        "blocks": [
            {"start": "8:30 AM", "end": "10:00 AM", "task": "Record Voiceovers",
             "detail": "Batch record all scripts"},
            {"start": "10:00 AM", "end": "12:00 PM", "task": "Edit 5-10 Videos",
             "detail": "Batch edit, subtitles, pattern interrupts every 5-7s"},
            {"start": "6:00 PM", "end": "7:00 PM", "task": "Final Rendering + Formatting",
             "detail": "Format for TikTok/IG/YT, hook in first 1.5s"},
        ],
        "deliverables": ["5-10 fully edited videos", "Proper platform formatting", "Subtitles on all"],
    },
    {
        "key": "partner3",
        "role": "Distribution & Growth Lead",
        "color": "#f0834d",
        "blocks": [
            {"start": "12:00 PM", "end": "1:00 PM", "task": "Upload & Optimize",
             "detail": "Strong titles, SEO keywords, thumbnails, pinned comments"},
            {"start": "4:00 PM", "end": "4:30 PM", "task": "Engage Comments",
             "detail": "Reply to comments on all platforms"},
            {"start": "8:30 PM", "end": "9:00 PM", "task": "Analytics Review + Adjustments",
             "detail": "Track performance, adjust tomorrow's hooks"},
        ],
        "deliverables": ["All videos posted", "Keywords optimized", "Performance tracked"],
    },
]

EMAIL_TEMPLATES = {
    "daily_structure": {
        "subject": "Daily Structure + Quota System (Starting Immediately)",
        "body": "Team,\n\nWe are implementing a structured daily production system effective immediately.\n\nOur target: 10 videos per day collectively.\n\nEach of us has defined responsibilities to eliminate confusion and increase output.\n\nPartner 1 - Research & Scripts\n- Deliver 5-10 completed scripts daily\n- Provide hooks and captions\n- Track trends\n\nPartner 2 - Production\n- Record voiceovers\n- Edit and finalize 5-10 short-form videos\n- Ensure subtitles + formatting\n\nPartner 3 - Distribution & Analytics\n- Post all videos\n- Optimize titles & descriptions\n- Engage audience\n- Track daily analytics\n\nDaily check-in time: 9:15 PM\nEach person reports:\n- Deliverables completed\n- What worked\n- What failed\n- Plan for tomorrow\n\nConsistency is non-negotiable.\n\n-- Luis",
    },
    "daily_reminder": {
        "subject": "Daily Quota Reminder",
        "body": "Team,\n\nReminder: Today's quota is active.\n\nPlease complete:\n- Script targets\n- Production targets\n- Posting & analytics review\n\nReport completion by 9:15 PM.\n\nConsistency compounds.\n\n-- Luis",
    },
    "weekly_review": {
        "subject": "Weekly Performance Review",
        "body": "Team,\n\nHere is this week's performance summary:\n\nTotal Videos: [INSERT]\nAvg Retention: [INSERT]\nTop Performing Content: [INSERT]\nWeakest Format: [INSERT]\n\nAdjustments for next week:\n1. [INSERT]\n2. [INSERT]\n3. [INSERT]\n\nKeep building.\n\n-- Luis",
    },
    "missed_quota": {
        "subject": "Missed Quota Notice",
        "body": "Team,\n\nOne or more quotas were missed today.\n\nThis is a notice, not a punishment.\n\nPlease review:\n- What prevented completion\n- How to prevent recurrence\n- Updated plan for tomorrow\n\nTwo misses per week triggers a performance review.\nFour misses per month triggers role restructure.\n\nNo emotion. Just math.\n\n-- Luis",
    },
}


# ═══════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════

def get_setting(key, default=""):
    s = AppSettings.query.filter_by(key=key).first()
    return s.value if s else default


def set_setting(key, value):
    s = AppSettings.query.filter_by(key=key).first()
    if s:
        s.value = str(value)
    else:
        db.session.add(AppSettings(key=key, value=str(value)))
    db.session.commit()


def send_email_smtp(to_emails, subject, body):
    host = get_setting("smtp_host")
    port = int(get_setting("smtp_port", "587"))
    user = get_setting("smtp_user")
    password = get_setting("smtp_pass")
    from_addr = get_setting("from_email", user)
    if not all([host, user, password]):
        return False, "SMTP not configured. Go to Settings first."
    try:
        msg = MIMEMultipart()
        msg["From"] = from_addr
        msg["To"] = ", ".join(to_emails)
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        with smtplib.SMTP(host, port) as server:
            server.starttls()
            server.login(user, password)
            server.sendmail(from_addr, to_emails, msg.as_string())
        return True, "Sent"
    except Exception as exc:
        return False, str(exc)


def compute_partner_scores(partners, since):
    scores = []
    for p in partners:
        logs = DailyLog.query.filter(
            DailyLog.partner_id == p.id, DailyLog.date >= since
        ).all()
        days_active = len({l.date for l in logs})
        total_output = sum(
            l.scripts_written + l.videos_edited + l.videos_posted for l in logs
        )
        days_expected = (date.today() - since).days or 1
        consistency = min(days_active / days_expected * 100, 100)
        output_score = min(total_output / (days_expected * 5) * 100, 100)
        score = round(0.4 * output_score + 0.6 * consistency, 1)
        scores.append(
            {"partner": p, "score": score, "days_active": days_active, "total_output": total_output}
        )
    return scores


# ═══════════════════════════════════════════════════════════════
#  MAIN PAGE
# ═══════════════════════════════════════════════════════════════

@app.route("/")
def index():
    partners = Partner.query.order_by(Partner.id).all()
    today = date.today()
    thirty_days_ago = today - timedelta(days=30)

    today_logs = DailyLog.query.filter_by(date=today).all()
    total_videos_today = sum(l.videos_posted for l in today_logs)
    total_videos_all = Video.query.count()

    recent_videos = Video.query.order_by(Video.date_posted.desc()).limit(100).all()
    hooks = Hook.query.order_by(Hook.created_at.desc()).all()
    pipeline_items = PipelineItem.query.order_by(PipelineItem.created_at.desc()).all()
    daily_logs = (
        DailyLog.query.filter(DailyLog.date >= thirty_days_ago)
        .order_by(DailyLog.date.desc())
        .all()
    )
    vault_entries = VaultEntry.query.order_by(VaultEntry.created_at.desc()).all()
    monetization = MonetizationEntry.query.order_by(MonetizationEntry.date.desc()).all()
    email_logs = EmailLog.query.order_by(EmailLog.sent_at.desc()).limit(30).all()
    pillars = ContentPillar.query.all()
    partner_scores = compute_partner_scores(partners, thirty_days_ago)

    week_videos = Video.query.filter(Video.date_posted >= today - timedelta(days=7)).all()
    retentions = [v.retention_3s for v in week_videos if v.retention_3s]
    avg_retention = round(sum(retentions) / len(retentions), 1) if retentions else 0

    first_log = DailyLog.query.order_by(DailyLog.date.asc()).first()
    days_in = (today - first_log.date).days + 1 if first_log else 0
    if days_in <= 30:
        phase, phase_name = 1, "Build Engine"
    elif days_in <= 60:
        phase, phase_name = 2, "Optimize & Scale"
    else:
        phase, phase_name = 3, "Multiply & Monetize"

    total_revenue = sum(m.revenue for m in monetization)
    total_cost = sum(m.cost for m in monetization)

    return render_template(
        "index.html",
        partners=partners,
        time_blocks=TIME_BLOCKS,
        email_templates=EMAIL_TEMPLATES,
        daily_logs=daily_logs,
        today_logs=today_logs,
        recent_videos=recent_videos,
        hooks=hooks,
        pipeline_items=pipeline_items,
        vault_entries=vault_entries,
        monetization=monetization,
        email_logs=email_logs,
        pillars=pillars,
        partner_scores=partner_scores,
        total_videos_today=total_videos_today,
        total_videos_all=total_videos_all,
        avg_retention=avg_retention,
        days_in=days_in,
        phase=phase,
        phase_name=phase_name,
        today=today,
        total_revenue=total_revenue,
        total_cost=total_cost,
    )


# ═══════════════════════════════════════════════════════════════
#  API ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@app.route("/api/daily-log", methods=["POST"])
def api_add_daily_log():
    d = request.json
    log = DailyLog(
        date=datetime.strptime(d["date"], "%Y-%m-%d").date() if d.get("date") else date.today(),
        partner_id=int(d["partner_id"]),
        scripts_written=int(d.get("scripts_written", 0)),
        videos_edited=int(d.get("videos_edited", 0)),
        videos_posted=int(d.get("videos_posted", 0)),
        comments_replied=int(d.get("comments_replied", 0)),
        trend_research=bool(d.get("trend_research", False)),
        hooks_written=int(d.get("hooks_written", 0)),
        notes=d.get("notes", ""),
    )
    db.session.add(log)
    db.session.commit()
    return jsonify(success=True, id=log.id)


@app.route("/api/video", methods=["POST"])
def api_add_video():
    d = request.json
    v = Video(
        date_posted=datetime.strptime(d["date_posted"], "%Y-%m-%d").date()
        if d.get("date_posted") else date.today(),
        platform=d.get("platform", ""),
        hook_used=d.get("hook_used", ""),
        topic=d.get("topic", ""),
        length_seconds=int(d.get("length_seconds", 0)),
        retention_3s=float(d.get("retention_3s", 0)),
        retention_50=float(d.get("retention_50", 0)),
        avg_watch_time=float(d.get("avg_watch_time", 0)),
        views=int(d.get("views", 0)),
        likes=int(d.get("likes", 0)),
        comments_count=int(d.get("comments_count", 0)),
        shares=int(d.get("shares", 0)),
        saves=int(d.get("saves", 0)),
        format_type=d.get("format_type", ""),
        winner=bool(d.get("winner", False)),
    )
    db.session.add(v)
    db.session.commit()
    return jsonify(success=True, id=v.id)


@app.route("/api/hook", methods=["POST"])
def api_add_hook():
    d = request.json
    h = Hook(
        text=d["text"],
        format_type=d.get("format_type", ""),
        tested=bool(d.get("tested", False)),
        avg_retention_3s=float(d.get("avg_retention_3s", 0)),
        winning=bool(d.get("winning", False)),
    )
    db.session.add(h)
    db.session.commit()
    return jsonify(success=True, id=h.id)


@app.route("/api/hook/<int:hid>", methods=["PUT"])
def api_update_hook(hid):
    h = Hook.query.get_or_404(hid)
    d = request.json
    if "tested" in d:
        h.tested = bool(d["tested"])
    if "winning" in d:
        h.winning = bool(d["winning"])
    if "avg_retention_3s" in d:
        h.avg_retention_3s = float(d["avg_retention_3s"])
    db.session.commit()
    return jsonify(success=True)


@app.route("/api/pipeline", methods=["POST"])
def api_add_pipeline():
    d = request.json
    item = PipelineItem(
        title=d["title"],
        status=d.get("status", "queued"),
        assigned_to=int(d["assigned_to"]) if d.get("assigned_to") else None,
        due_date=datetime.strptime(d["due_date"], "%Y-%m-%d").date() if d.get("due_date") else None,
        content_type=d.get("content_type", ""),
        notes=d.get("notes", ""),
    )
    db.session.add(item)
    db.session.commit()
    return jsonify(success=True, id=item.id)


@app.route("/api/pipeline/<int:pid>", methods=["PUT"])
def api_update_pipeline(pid):
    item = PipelineItem.query.get_or_404(pid)
    d = request.json
    if "status" in d:
        item.status = d["status"]
    db.session.commit()
    return jsonify(success=True)


@app.route("/api/vault", methods=["POST"])
def api_add_vault():
    d = request.json
    e = VaultEntry(
        category=d.get("category", ""),
        title=d["title"],
        content=d.get("content", ""),
        performance_note=d.get("performance_note", ""),
    )
    db.session.add(e)
    db.session.commit()
    return jsonify(success=True, id=e.id)


@app.route("/api/monetization", methods=["POST"])
def api_add_monetization():
    d = request.json
    e = MonetizationEntry(
        date=datetime.strptime(d["date"], "%Y-%m-%d").date() if d.get("date") else date.today(),
        source=d.get("source", ""),
        revenue=float(d.get("revenue", 0)),
        cost=float(d.get("cost", 0)),
        notes=d.get("notes", ""),
    )
    db.session.add(e)
    db.session.commit()
    return jsonify(success=True, id=e.id)


@app.route("/api/pillar", methods=["POST"])
def api_add_pillar():
    d = request.json
    p = ContentPillar(name=d["name"], description=d.get("description", ""), color=d.get("color", "#7c6cf0"))
    db.session.add(p)
    db.session.commit()
    return jsonify(success=True, id=p.id)


@app.route("/api/partner/<int:pid>", methods=["PUT"])
def api_update_partner(pid):
    p = Partner.query.get_or_404(pid)
    d = request.json
    if "name" in d:
        p.name = d["name"]
    if "email" in d:
        p.email = d["email"]
    if "role" in d:
        p.role = d["role"]
    if "quota_scripts" in d:
        p.quota_scripts = int(d["quota_scripts"])
    if "quota_videos_edit" in d:
        p.quota_videos_edit = int(d["quota_videos_edit"])
    if "quota_videos_post" in d:
        p.quota_videos_post = int(d["quota_videos_post"])
    db.session.commit()
    return jsonify(success=True)


@app.route("/api/send-email", methods=["POST"])
def api_send_email():
    d = request.json
    recipients = [e.strip() for e in d.get("recipients", []) if e.strip()]
    subject = d.get("subject", "")
    body = d.get("body", "")
    if not recipients or not subject:
        return jsonify(success=False, error="Recipients and subject required")
    success, message = send_email_smtp(recipients, subject, body)
    db.session.add(
        EmailLog(
            recipients=", ".join(recipients),
            subject=subject,
            body=body,
            template_type=d.get("template_type", "custom"),
            status="sent" if success else "failed",
        )
    )
    db.session.commit()
    return jsonify(success=success, message=message)


@app.route("/api/settings", methods=["GET"])
def api_get_settings():
    return jsonify({s.key: s.value for s in AppSettings.query.all()})


@app.route("/api/settings", methods=["POST"])
def api_save_settings():
    for key, value in request.json.items():
        set_setting(key, value)
    return jsonify(success=True)


@app.route("/api/delete/<string:model>/<int:item_id>", methods=["DELETE"])
def api_delete(model, item_id):
    models = {
        "video": Video,
        "hook": Hook,
        "pipeline": PipelineItem,
        "vault": VaultEntry,
        "monetization": MonetizationEntry,
        "daily_log": DailyLog,
        "pillar": ContentPillar,
        "email_log": EmailLog,
    }
    cls = models.get(model)
    if not cls:
        return jsonify(success=False, error="Invalid model")
    obj = cls.query.get_or_404(item_id)
    db.session.delete(obj)
    db.session.commit()
    return jsonify(success=True)


@app.route("/api/analytics")
def api_analytics():
    today = date.today()
    daily = []
    for i in range(30):
        d = today - timedelta(days=29 - i)
        daily.append({"date": d.isoformat(), "count": Video.query.filter_by(date_posted=d).count()})

    platforms = db.session.query(Video.platform, db.func.count(Video.id)).group_by(Video.platform).all()
    formats = (
        db.session.query(
            Video.format_type,
            db.func.avg(Video.retention_3s),
            db.func.avg(Video.views),
            db.func.count(Video.id),
        )
        .group_by(Video.format_type)
        .all()
    )
    top = Video.query.order_by(Video.views.desc()).limit(10).all()
    return jsonify(
        daily=daily,
        platforms=[{"platform": p[0] or "Unknown", "count": p[1]} for p in platforms],
        formats=[
            {
                "format": f[0] or "Unknown",
                "avg_retention": round(f[1] or 0, 1),
                "avg_views": round(f[2] or 0),
                "count": f[3],
            }
            for f in formats
        ],
        top_videos=[
            {"topic": v.topic, "views": v.views, "retention_3s": v.retention_3s, "platform": v.platform}
            for v in top
        ],
    )


# ═══════════════════════════════════════════════════════════════
#  DATABASE INIT + SEED
# ═══════════════════════════════════════════════════════════════

def init_db():
    db.create_all()
    if Partner.query.count() == 0:
        db.session.add_all(
            [
                Partner(
                    name="Partner 1", role="Research & Script Lead",
                    focus_area="Ideas + Hooks + Script writing",
                    quota_scripts=10, quota_videos_edit=0, quota_videos_post=0,
                ),
                Partner(
                    name="Partner 2", role="Production Lead",
                    focus_area="Voice, visuals, editing",
                    quota_scripts=0, quota_videos_edit=10, quota_videos_post=0,
                ),
                Partner(
                    name="Luis", role="Distribution & Growth Lead",
                    focus_area="Posting, analytics, scaling",
                    quota_scripts=0, quota_videos_edit=0, quota_videos_post=10,
                ),
            ]
        )
        db.session.add_all(
            [
                ContentPillar(name="Educational", description="Teaching and informing", color="#7c6cf0"),
                ContentPillar(name="Story-based", description="Narrative-driven content", color="#00c897"),
                ContentPillar(name="Emotional", description="Trigger emotional response", color="#f0834d"),
                ContentPillar(name="Reactive / Trend", description="Current trends and reactions", color="#eab308"),
                ContentPillar(name="Conversion", description="Direct CTA and sales", color="#3b82f6"),
            ]
        )
        db.session.commit()


with app.app_context():
    init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
