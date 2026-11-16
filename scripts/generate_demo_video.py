import os
import sys
import numpy as np
import imageio
from PIL import Image, ImageDraw, ImageFont

WIDTH = 1920
HEIGHT = 1080
FPS = 10
TOTAL_SECONDS = 155
TOTAL_FRAMES = TOTAL_SECONDS * FPS  # 1550 frames

# Load fonts
try:
    font_title = ImageFont.truetype("segoeuib.ttf", 46)
    font_subtitle = ImageFont.truetype("segoeui.ttf", 26)
    font_h2 = ImageFont.truetype("segoeuib.ttf", 34)
    font_body = ImageFont.truetype("segoeui.ttf", 22)
    font_body_bold = ImageFont.truetype("segoeuib.ttf", 22)
    font_code = ImageFont.truetype("consola.ttf", 20)
    font_small = ImageFont.truetype("segoeui.ttf", 18)
    font_chapter = ImageFont.truetype("segoeuib.ttf", 16)
except Exception:
    font_title = font_subtitle = font_h2 = font_body = font_body_bold = font_code = font_small = font_chapter = ImageFont.load_default()

SCREENSHOT_TIMELINE = r"C:\Users\raman\.gemini\antigravity\brain\292f0241-1f85-4a2c-a2b9-722e69d60be5\browser_sandbox\screenshots\step_8_shot_1.png"
SCREENSHOT_PROBE = r"C:\Users\raman\.gemini\antigravity\brain\292f0241-1f85-4a2c-a2b9-722e69d60be5\browser_sandbox\screenshots\step_8_shot_2.png"
SCREENSHOT_AUDIT = r"C:\Users\raman\.gemini\antigravity\brain\292f0241-1f85-4a2c-a2b9-722e69d60be5\browser_sandbox\screenshots\step_4.png"

def load_and_frame(path, target_w, target_h):
    if not os.path.exists(path):
        return None
    try:
        im = Image.open(path)
        im.thumbnail((target_w, target_h), Image.Resampling.LANCZOS)
        framed = Image.new("RGBA", (im.width + 16, im.height + 42), (30, 41, 59, 255))
        d = ImageDraw.Draw(framed)
        d.ellipse([14, 14, 24, 24], fill=(239, 68, 68))
        d.ellipse([32, 14, 42, 24], fill=(245, 158, 11))
        d.ellipse([50, 14, 60, 24], fill=(16, 185, 129))
        d.text((80, 12), "Chronis UI • http://127.0.0.1:8000", fill=(148, 163, 184), font=font_small)
        framed.paste(im, (8, 36))
        return framed
    except Exception:
        return None

img_timeline_framed = load_and_frame(SCREENSHOT_TIMELINE, 1060, 720)
img_probe_framed = load_and_frame(SCREENSHOT_PROBE, 1060, 720)
img_audit_framed = load_and_frame(SCREENSHOT_AUDIT, 1060, 720)

def draw_header_and_footer(draw, current_frame, chapter_title, caption_text):
    draw.rectangle([0, 0, WIDTH, 70], fill=(15, 23, 42))
    draw.line([0, 70, WIDTH, 70], fill=(51, 65, 85), width=1)
    draw.rounded_rectangle([40, 15, 180, 55], radius=6, fill=(30, 41, 59), outline=(71, 85, 105))
    draw.text((55, 22), "⏱ CHRONIS", fill=(56, 189, 248), font=font_body_bold)
    draw.text((210, 23), chapter_title, fill=(241, 245, 249), font=font_chapter)
    cur_sec = current_frame // FPS
    time_str = f"{cur_sec // 60}:{cur_sec % 60:02d} / 2:35"
    draw.text((WIDTH - 180, 23), time_str, fill=(148, 163, 184), font=font_chapter)

    draw.rectangle([0, HEIGHT - 110, WIDTH, HEIGHT], fill=(15, 23, 42))
    draw.line([0, HEIGHT - 110, WIDTH, HEIGHT - 110], fill=(51, 65, 85), width=1)
    progress_w = int((current_frame / TOTAL_FRAMES) * WIDTH)
    draw.rectangle([0, HEIGHT - 110, progress_w, HEIGHT - 105], fill=(56, 189, 248))
    draw.rounded_rectangle([40, HEIGHT - 92, WIDTH - 40, HEIGHT - 20], radius=8, fill=(30, 41, 59))
    draw.text((55, HEIGHT - 82), "AUDIO NARRATION", fill=(56, 189, 248), font=font_small)
    draw.text((55, HEIGHT - 56), f"\"{caption_text}\"", fill=(248, 250, 252), font=font_body)

def render_scene_1(frame_idx):
    base = Image.new("RGB", (WIDTH, HEIGHT), (11, 17, 32))
    draw = ImageDraw.Draw(base)
    caption = "Welcome to Chronis — a production-grade, privacy-aware memory timeline designed for wearable AI companions." if frame_idx < 100 else \
              "Chronis continuously ingests multi-modal user streams and strictly enforces privacy boundaries at the backend API layer."
    draw_header_and_footer(draw, frame_idx, "CHAPTER 1: SYSTEM OVERVIEW & ARCHITECTURE", caption)
    draw.rounded_rectangle([80, 120, WIDTH - 80, 450], radius=16, fill=(15, 23, 42), outline=(51, 65, 85), width=2)
    draw.text((120, 160), "CHRONIS • Mini Privacy-Aware Memory Timeline", fill=(56, 189, 248), font=font_title)
    draw.text((120, 230), "SDE Intern Technical Evaluation • Privacy & Authorization Subsystem", fill=(226, 232, 240), font=font_subtitle)
    badges = ["FastAPI (Python 3.12)", "SQLAlchemy 2.0", "SQLite Database", "Pydantic v2", "OAuth2 / JWT Bearer", "Zero-Dependency SPA"]
    bx, by = 120, 290
    for b in badges:
        draw.rounded_rectangle([bx, by, bx + len(b)*13 + 30, by + 36], radius=6, fill=(30, 41, 59), outline=(71, 85, 105))
        draw.text((bx + 15, by + 6), b, fill=(148, 163, 184), font=font_small)
        bx += len(b)*13 + 45
        if bx > WIDTH - 350: bx, by = 120, by + 48
    draw.text((120, 390), "Core Mandate: Strict backend-enforced privacy with zero data leakage & immutable auditability.", fill=(52, 211, 153), font=font_body_bold)
    pillars = [
        ("1. Strict Backend Authorization", "Access control is enforced in SQL queries and service logic — never merely hidden in browser JavaScript.", (56, 189, 248)),
        ("2. Read-Only Forensic Audit Trail", "Every sensitive action, permission toggle, and blocked attempt is permanently recorded and tamper-proof.", (251, 191, 36)),
        ("3. Advanced Enterprise Extensibility", "Full multi-tenancy, date/keyword search, automated keyword redaction rules, and GDPR/CCPA data portability.", (52, 211, 153))
    ]
    px = 80
    for title, desc, col in pillars:
        draw.rounded_rectangle([px, 480, px + 560, 930], radius=12, fill=(15, 23, 42), outline=(51, 65, 85), width=2)
        draw.rounded_rectangle([px, 480, px + 560, 550], radius=12, fill=(30, 41, 59))
        draw.text((px + 24, 502), title, fill=col, font=font_h2)
        words = desc.split()
        lines, cur = [], []
        for w in words:
            cur.append(w)
            if len(" ".join(cur)) > 38: lines.append(" ".join(cur[:-1])); cur = [w]
        if cur: lines.append(" ".join(cur))
        dy = 580
        for ln in lines:
            draw.text((px + 24, dy), ln, fill=(203, 213, 225), font=font_body)
            dy += 36
        px += 600
    return base

def render_scene_2(frame_idx):
    base = Image.new("RGB", (WIDTH, HEIGHT), (11, 17, 32))
    draw = ImageDraw.Draw(base)
    caption = "Wearables capture four sensitive streams: ambient conversations, GPS coordinates, biometrics, and personal notes." if frame_idx < 300 else \
              "Client-side privacy masking is fatal. Chronis eliminates unpermitted data at the database layer before it ever reaches RAM."
    draw_header_and_footer(draw, frame_idx, "CHAPTER 2: MULTI-MODAL STREAMS & THREAT MODEL", caption)
    draw.text((80, 95), "The Four Wearable Telemetry Streams", fill=(241, 245, 249), font=font_h2)
    categories = [
        ("💬 Conversation", "Voice Transcripts & Memos", "Continuous audio capture, meeting dialogue, ambient speech transcripts.", (56, 189, 248)),
        ("📍 Location", "GPS Coordinates & Venues", "Real-time latitude/longitude coordinates, visited clinics, homes, and offices.", (251, 113, 133)),
        ("💓 Physiological", "Biometrics & Vitals", "Heart rate (BPM) anomalies, step counters, stress markers, vital trends.", (251, 191, 36)),
        ("📝 Note", "Personal Notes & Tasks", "User-dictated thoughts, medical reminders, passwords, confidential notes.", (52, 211, 153))
    ]
    cx = 80
    for name, sub, desc, col in categories:
        draw.rounded_rectangle([cx, 150, cx + 415, 480], radius=12, fill=(15, 23, 42), outline=(51, 65, 85), width=2)
        draw.text((cx + 20, 175), name, fill=col, font=font_h2)
        draw.text((cx + 20, 225), sub, fill=(148, 163, 184), font=font_small)
        draw.line([cx + 20, 260, cx + 395, 260], fill=(51, 65, 85), width=1)
        words = desc.split()
        lines, cur = [], []
        for w in words:
            cur.append(w)
            if len(" ".join(cur)) > 26: lines.append(" ".join(cur[:-1])); cur = [w]
        if cur: lines.append(" ".join(cur))
        dy = 280
        for l in lines:
            draw.text((cx + 20, dy), l, fill=(203, 213, 225), font=font_body)
            dy += 32
        cx += 450
    draw.rounded_rectangle([80, 520, WIDTH - 80, 930], radius=14, fill=(15, 23, 42), outline=(239, 68, 68), width=2)
    draw.rounded_rectangle([80, 520, WIDTH - 80, 580], radius=14, fill=(30, 41, 59))
    draw.text((110, 538), "🚨 THREAT MODEL: WHY CLIENT-SIDE PRIVACY FAILS", fill=(248, 113, 113), font=font_h2)
    draw.text((110, 610), "Traditional Flawed Approach (Client-Only Hiding):", fill=(251, 113, 133), font=font_body_bold)
    draw.text((110, 645), "• The backend sends ALL memory records to the client over HTTP.\n• JavaScript simply hides cards using `display: none` or CSS filters.\n• Any malicious script, browser extension, or `curl http://api/events` trivially steals sensitive records.", fill=(203, 213, 225), font=font_body)
    draw.text((110, 755), "The Chronis Architecture (Defense-in-Depth):", fill=(52, 211, 153), font=font_body_bold)
    draw.text((110, 790), "• Category permissions are queried before data retrieval.\n• SQL queries apply: `SELECT * FROM events WHERE type IN (:allowed_categories)`\n• Restricted records are NEVER fetched from disk, loaded into server RAM, or emitted onto the network.", fill=(203, 213, 225), font=font_body)
    return base

def render_scene_3(frame_idx):
    base = Image.new("RGB", (WIDTH, HEIGHT), (11, 17, 32))
    draw = ImageDraw.Draw(base)
    caption = "Here is the live Chronis Timeline interface. Events are ingested chronologically with exact IST timestamps." if frame_idx < 510 else \
              "The background wearable simulator streams live sensor updates, while the user has instantaneous visibility into their history."
    draw_header_and_footer(draw, frame_idx, "CHAPTER 3: LIVE MEMORY TIMELINE & WEARABLE TELEMETRY", caption)
    draw.rounded_rectangle([60, 100, 760, 930], radius=12, fill=(15, 23, 42), outline=(51, 65, 85), width=2)
    draw.text((90, 130), "Timeline Interface Highlights", fill=(56, 189, 248), font=font_h2)
    bullets = [
        ("User Profile & Context", "Displays 'Demo User (ID: 1)' with active timezone badge: IST (UTC+5:30).", (241, 245, 249)),
        ("Multi-Stream Categorization", "Distinct visual icons and semantic badges for conversation, location, physiological, and note.", (52, 211, 153)),
        ("Telemetry Stream Simulator", "Built-in wearable telemetry engine (simulator.py) streams real-time heart rate peaks and GPS updates.", (251, 191, 36)),
        ("Filter & Search Controls", "Quick-filter pills and search bars to isolate specific categories or search across text contents.", (56, 189, 248)),
        ("Time Normalization", "All timestamps stored in ISO 8601 UTC and rendered in client's local timezone (Indian Standard Time).", (226, 232, 240))
    ]
    by = 190
    for title, desc, col in bullets:
        draw.text((90, by), f"• {title}", fill=col, font=font_body_bold)
        words = desc.split()
        cur = []
        for w in words:
            cur.append(w)
            if len(" ".join(cur)) > 42:
                draw.text((110, by + 30), " ".join(cur[:-1]), fill=(203, 213, 225), font=font_body)
                cur = [w]; by += 28
        if cur:
            draw.text((110, by + 30), " ".join(cur), fill=(203, 213, 225), font=font_body)
            by += 32
        by += 38
    if img_timeline_framed: base.paste(img_timeline_framed, (800, 110))
    return base

def render_scene_4(frame_idx):
    base = Image.new("RGB", (WIDTH, HEIGHT), (11, 17, 32))
    draw = ImageDraw.Draw(base)
    caption = "Users can dynamically toggle any category ON or OFF. An API call updates the privacy permission table." if frame_idx < 730 else \
              "Subsequent collection queries execute SQL-level filtering where restricted categories are completely omitted from the query result."
    draw_header_and_footer(draw, frame_idx, "CHAPTER 4: DYNAMIC PRIVACY CONTROLS & ENFORCEMENT", caption)
    draw.text((80, 95), "Dynamic Category Permission Engine", fill=(241, 245, 249), font=font_h2)
    draw.rounded_rectangle([80, 150, 920, 930], radius=14, fill=(15, 23, 42), outline=(51, 65, 85), width=2)
    draw.rounded_rectangle([80, 150, 920, 210], radius=14, fill=(30, 41, 59))
    draw.text((110, 168), "1. Dynamic Control Toggle (PUT /permissions)", fill=(56, 189, 248), font=font_h2)
    draw.text((110, 240), "User Action via UI or API Client:", fill=(241, 245, 249), font=font_body_bold)
    json_req = "PUT /permissions\nContent-Type: application/json\n\n{\n  \"category\": \"location\",\n  \"is_enabled\": false\n}"
    draw.rounded_rectangle([110, 280, 890, 440], radius=8, fill=(2, 6, 23))
    draw.text((130, 300), json_req, fill=(52, 211, 153), font=font_code)
    draw.text((110, 470), "Backend Actions:", fill=(241, 245, 249), font=font_body_bold)
    draw.text((110, 510), "1. Atomically updates `permissions` table for user_id = 1.\n2. Emits audit log entry: `action='PERMISSION_SET_OFF'`, `category='location'`.\n3. Changes take effect instantaneously across all subsequent requests.\n4. No server reboot or cache invalidation delay.", fill=(203, 213, 225), font=font_body)
    draw.rounded_rectangle([960, 150, WIDTH - 80, 930], radius=14, fill=(15, 23, 42), outline=(51, 65, 85), width=2)
    draw.rounded_rectangle([960, 150, WIDTH - 80, 210], radius=14, fill=(30, 41, 59))
    draw.text((990, 168), "2. Strict Query-Level Elimination (GET /events)", fill=(52, 211, 153), font=font_h2)
    draw.text((990, 240), "Database Query Executed by EventService:", fill=(241, 245, 249), font=font_body_bold)
    sql_code = "-- Only permitted categories are requested:\nSELECT id, timestamp, type, title, content\nFROM events\nWHERE user_id = :user_id\n  AND type IN ('conversation', 'physiological', 'note')\nORDER BY timestamp DESC\nLIMIT 20 OFFSET 0;"
    draw.rounded_rectangle([990, 280, WIDTH - 110, 440], radius=8, fill=(2, 6, 23))
    draw.text((1010, 300), sql_code, fill=(56, 189, 248), font=font_code)
    draw.text((990, 470), "Guarantee of Absolute Privacy:", fill=(241, 245, 249), font=font_body_bold)
    draw.text((990, 510), "• Location events are never queried from disk.\n• They never exist in FastAPI Python memory.\n• They never cross the network wire in JSON packets.\n• Even if an attacker inspects raw HTTP traffic, zero location data exists.", fill=(203, 213, 225), font=font_body)
    return base

def render_scene_5(frame_idx):
    base = Image.new("RGB", (WIDTH, HEIGHT), (11, 17, 32))
    draw = ImageDraw.Draw(base)
    caption = "Our built-in Security Probe allows direct testing of single-resource retrieval. If a category is OFF, lookups trigger 403 Forbidden." if frame_idx < 950 else \
              "The backend halts execution, rejects the request, and atomically logs a forensic DENIED entry in the audit database."
    draw_header_and_footer(draw, frame_idx, "CHAPTER 5: SECURITY PROBE & 403 FORBIDDEN ENFORCEMENT", caption)
    draw.rounded_rectangle([60, 100, 760, 930], radius=12, fill=(15, 23, 42), outline=(239, 68, 68), width=2)
    draw.text((90, 130), "Direct Resource Probe", fill=(248, 113, 113), font=font_h2)
    draw.text((90, 190), "Scenario: Attacker knows Event ID #3 (Location)", fill=(241, 245, 249), font=font_body_bold)
    draw.text((90, 225), "Attacker sends direct single-resource query:", fill=(148, 163, 184), font=font_small)
    call_code = "GET /events/3\nHost: api.chronis.ai\nAuthorization: Bearer <token>"
    draw.rounded_rectangle([90, 260, 730, 370], radius=8, fill=(2, 6, 23))
    draw.text((110, 280), call_code, fill=(251, 191, 36), font=font_code)
    draw.text((90, 400), "FastAPI Backend Authorization Guard:", fill=(241, 245, 249), font=font_body_bold)
    resp_code = "HTTP/1.1 403 Forbidden\nContent-Type: application/json\n\n{\n  \"detail\": \"Access to 'location' events is\n   restricted by your active privacy settings.\"\n}"
    draw.rounded_rectangle([90, 440, 730, 600], radius=8, fill=(2, 6, 23))
    draw.text((110, 460), resp_code, fill=(248, 113, 113), font=font_code)
    draw.text((90, 630), "Forensic Audit Logging:", fill=(52, 211, 153), font=font_body_bold)
    draw.text((90, 670), "An immutable record is immediately written:\n• Action: GET_EVENT_DETAIL\n• Category: location\n• Result: DENIED\n• Timestamp: 2026-11-16T13:20:00Z", fill=(203, 213, 225), font=font_body)
    if img_probe_framed: base.paste(img_probe_framed, (800, 110))
    return base

def render_scene_6(frame_idx):
    base = Image.new("RGB", (WIDTH, HEIGHT), (11, 17, 32))
    draw = ImageDraw.Draw(base)
    caption = "The Audit Trail provides complete transparency. Every sensitive operation—creation, deletion, permission update, and blocked access—is logged." if frame_idx < 1170 else \
              "The audit trail is strictly immutable and read-only, preventing any tampering or deletion of security logs."
    draw_header_and_footer(draw, frame_idx, "CHAPTER 6: IMMUTABLE FORENSIC AUDIT TRAIL", caption)
    draw.rounded_rectangle([60, 100, 760, 930], radius=12, fill=(15, 23, 42), outline=(51, 65, 85), width=2)
    draw.text((90, 130), "Audit Trail Architecture", fill=(251, 191, 36), font=font_h2)
    points = [
        ("Atomic Log Commits", "Every action commits an audit entry synchronously in SQLite, guaranteeing zero lost records.", (241, 245, 249)),
        ("Structured Schema", "Stores timestamp, user_id, action, event_type, and result ('ALLOWED', 'DENIED', 'CREATED').", (56, 189, 248)),
        ("Immutable & Read-Only", "GET /audit-log is the only exposed endpoint. Mutating via POST, PUT, or DELETE returns 405 Method Not Allowed.", (52, 211, 153)),
        ("Evaluator Visibility", "Evaluators and compliance auditors can trace the exact sequence of privacy actions in real time.", (226, 232, 240))
    ]
    by = 190
    for title, desc, col in points:
        draw.text((90, by), f"• {title}", fill=col, font=font_body_bold)
        words = desc.split()
        cur = []
        for w in words:
            cur.append(w)
            if len(" ".join(cur)) > 42:
                draw.text((110, by + 30), " ".join(cur[:-1]), fill=(203, 213, 225), font=font_body)
                cur = [w]; by += 28
        if cur:
            draw.text((110, by + 30), " ".join(cur), fill=(203, 213, 225), font=font_body)
            by += 32
        by += 38
    if img_audit_framed: base.paste(img_audit_framed, (800, 110))
    return base

def render_scene_7(frame_idx):
    base = Image.new("RGB", (WIDTH, HEIGHT), (11, 17, 32))
    draw = ImageDraw.Draw(base)
    caption = "We have also implemented four advanced enterprise architectures: JWT multi-tenancy, date-range and full-text keyword search," if frame_idx < 1380 else \
              "Automated granular privacy rules with keyword redactions, and GDPR/CCPA data export in both JSON and CSV formats."
    draw_header_and_footer(draw, frame_idx, "CHAPTER 7: ADVANCED ARCHITECTURAL APPROACHES", caption)
    draw.text((80, 95), "Four Advanced Approaches Implemented & Verified", fill=(241, 245, 249), font=font_h2)
    cards = [
        ("1. Full Authentication & Multi-Tenancy",
         "Endpoints: POST /auth/register, POST /auth/login, GET /auth/me\n• PBKDF2-HMAC password hashing (100,000 iterations)\n• Signed JWT access tokens (OAuth2 Bearer)\n• Row-level tenant isolation: User A cannot access User B\n• Turnkey fallback to Demo User for zero-friction evaluation",
         (56, 189, 248)),
        ("2. Date-Range & Full-Text Search",
         "Query: GET /events?start_date=...&end_date=...&q=...\n• ISO 8601 UTC date-range filtering for timeline analysis\n• Case-insensitive full-text keyword search across title & content\n• Seamlessly composable with category privacy filters\n• Blazing-fast B-tree indexing",
         (251, 191, 36)),
        ("3. Automated Granular Privacy Rules",
         "Endpoints: GET/POST/DELETE /privacy-rules\n• Keyword Redaction: replaces sensitive terms (e.g. 'confidential') with [REDACTED BY PRIVACY RULE] in memory\n• Raw database records remain intact and uncorrupted\n• Pattern Drop: automatically omits matching events & returns 403",
         (52, 211, 153)),
        ("4. Export & Data Portability (GDPR/CCPA)",
         "Endpoints: POST /export, GET /export\n• GDPR Article 20 / CCPA Data Portability compliance\n• Full timeline, active permissions & audit logs export\n• Dual formats: structured JSON or downloadable CSV\n• Privacy-respecting: disabled data is never leaked in export",
         (251, 113, 133))
    ]
    coords = [(80, 150, 920, 520), (960, 150, WIDTH - 80, 520), (80, 550, 920, 920), (960, 550, WIDTH - 80, 920)]
    for i, (title, content, col) in enumerate(cards):
        x1, y1, x2, y2 = coords[i]
        draw.rounded_rectangle([x1, y1, x2, y2], radius=12, fill=(15, 23, 42), outline=(51, 65, 85), width=2)
        draw.rounded_rectangle([x1, y1, x2, y1 + 55], radius=12, fill=(30, 41, 59))
        draw.text((x1 + 20, y1 + 14), title, fill=col, font=font_h2)
        lines = content.split("\n")
        cy = y1 + 75
        for l in lines:
            draw.text((x1 + 20, cy), l, fill=(203, 213, 225), font=font_body)
            cy += 32
    return base

def render_scene_8(frame_idx):
    base = Image.new("RGB", (WIDTH, HEIGHT), (11, 17, 32))
    draw = ImageDraw.Draw(base)
    caption = "All 16 unit tests and 11 end-to-end verification steps pass in under 2 seconds. Chronis is complete and ready for evaluation."
    draw_header_and_footer(draw, frame_idx, "CHAPTER 8: AUTOMATED VERIFICATION & CONCLUSION", caption)
    draw.rounded_rectangle([200, 140, WIDTH - 200, 900], radius=16, fill=(15, 23, 42), outline=(52, 211, 153), width=2)
    draw.text((WIDTH // 2 - 320, 200), "CHRONIS • EVALUATION READY", fill=(52, 211, 153), font=font_title)
    results = [
        ("✓ 16/16 Automated Pytest Tests Passing", "100% pass rate in 1.94s covering all privacy checks, error paths, and new approaches.", (56, 189, 248)),
        ("✓ 11-Step Automated Verification Runner", "Single command `python automate_demo.py` verifies the entire privacy lifecycle.", (52, 211, 153)),
        ("✓ Zero-Friction Turnkey Setup", "FastAPI + SQLite + Vanilla SPA. No Docker, external DB, or node_modules needed.", (251, 191, 36)),
        ("✓ Interactive Security Probe & Simulator", "Evaluators can physically test 403 Forbidden responses directly in the browser UI.", (251, 113, 133))
    ]
    ry = 310
    for title, desc, col in results:
        draw.rounded_rectangle([260, ry, WIDTH - 260, ry + 105], radius=10, fill=(30, 41, 59))
        draw.text((290, ry + 18), title, fill=col, font=font_h2)
        draw.text((290, ry + 62), desc, fill=(203, 213, 225), font=font_body)
        ry += 125
    draw.text((WIDTH // 2 - 350, 830), "Repository: github.com/RamanujAgrawal/Mini-Privacy-Aware-Memory-Timeline", fill=(148, 163, 184), font=font_body)
    return base

def main():
    out_path = "demo_video.mp4"
    print(f"Generating Full HD 1080p Demo Video: {out_path} ({TOTAL_FRAMES} frames @ {FPS} fps = {TOTAL_SECONDS}s)...")
    writer = imageio.get_writer(out_path, fps=FPS, codec="libx264", quality=8, macro_block_size=1)
    for f in range(TOTAL_FRAMES):
        if f % 100 == 0:
            pct = int((f / TOTAL_FRAMES) * 100); sec = f // FPS
            print(f"Rendering frame {f}/{TOTAL_FRAMES} ({pct}%) • {sec // 60}:{sec % 60:02d}...")
        if f < 200: img = render_scene_1(f)
        elif f < 400: img = render_scene_2(f)
        elif f < 620: img = render_scene_3(f)
        elif f < 840: img = render_scene_4(f)
        elif f < 1060: img = render_scene_5(f)
        elif f < 1280: img = render_scene_6(f)
        elif f < 1480: img = render_scene_7(f)
        else: img = render_scene_8(f)
        writer.append_data(np.array(img))
    writer.close()
    file_size_mb = os.path.getsize(out_path) / (1024 * 1024)
    print(f"SUCCESS: Demo video created successfully at {out_path} ({file_size_mb:.2f} MB, {TOTAL_SECONDS}s)")

if __name__ == "__main__":
    main()
