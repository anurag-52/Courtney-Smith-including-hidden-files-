from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime
import pandas as pd
import io, httpx, asyncio
from .config import settings
from .db import Base, engine, get_db
from .models import User, Watchlist, Signal, Portfolio, UserEmail
from .security import hash_password, verify_password, create_jwt
from .schemas import *
from .nse.fetcher import latest_bhavcopy
from . import strategies
from .emailer import send_email

app = FastAPI(title=settings.APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def decode_jwt(token: str):
    from jose import jwt
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        return payload.get("sub")
    except Exception:
        return None

from fastapi.security import OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

def get_user_from_token(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    sub = decode_jwt(token)
    if not sub:
        raise HTTPException(status_code=401, detail="Invalid token")
    u = db.execute(select(User).where(User.email == sub)).scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=401, detail="User not found")
    return u

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    with Session(bind=engine) as db:
        u = db.execute(select(User).where(User.email == settings.SUPERADMIN_EMAIL)).scalar_one_or_none()
        if not u:
            u = User(email=settings.SUPERADMIN_EMAIL, name=settings.SUPERADMIN_NAME, password_hash=hash_password(settings.SUPERADMIN_PASSWORD), is_superadmin=True)
            db.add(u); db.commit()

@app.post("/api/login", response_model=Token)
def login(data: LoginIn, db: Session = Depends(get_db)):
    u = db.execute(select(User).where(User.email == data.email)).scalar_one_or_none()
    if not u or not verify_password(data.password, u.password_hash):
        raise HTTPException(status_code=401, detail="Bad credentials")
    token = create_jwt(u.email, settings.JWT_SECRET, settings.JWT_EXPIRES_MIN)
    return Token(access_token=token)

@app.post("/api/register", response_model=UserOut)
def register(data: RegisterIn, current: User = Depends(get_user_from_token), db: Session = Depends(get_db)):
    if not current.is_superadmin:
        raise HTTPException(status_code=403, detail="Only superadmin can create users")
    exists = db.execute(select(User).where(User.email == data.email)).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=400, detail="User exists")
    u = User(email=data.email, name=data.name, password_hash=hash_password(data.password), is_superadmin=False)
    db.add(u); db.commit(); db.refresh(u)
    return u

@app.get("/api/me", response_model=UserOut)
def me(current: User = Depends(get_user_from_token)):
    return current

@app.post("/api/watchlist")
def add_watchlist(data: WatchAddIn, current: User = Depends(get_user_from_token), db: Session = Depends(get_db)):
    existing = db.execute(select(Watchlist).where(Watchlist.user_id == current.id)).scalars().all()
    if len(existing) + len(data.symbols) > 15:
        raise HTTPException(status_code=400, detail="Max 15 symbols per user")
    for s in data.symbols:
        s = s.strip().upper()
        if db.execute(select(Watchlist).where(Watchlist.user_id == current.id, Watchlist.symbol == s)).scalar_one_or_none():
            continue
        db.add(Watchlist(user_id=current.id, symbol=s, active=True))
    db.commit()
    return {"ok": True}

@app.post("/api/emails")
def add_emails(data: EmailAddIn, current: User = Depends(get_user_from_token), db: Session = Depends(get_db)):
    db.query(UserEmail).filter(UserEmail.user_id == current.id).delete()
    for e in data.emails:
        db.add(UserEmail(user_id=current.id, email=e))
    db.commit()
    return {"ok": True}

def run_all_strategies(history: pd.DataFrame):
    outs = []
    for name, fn in [
        ("Channel Breakout", strategies.channel_breakout),
        ("5-Day Condition", strategies.five_day_condition),
        ("Trend Filter", strategies.trend_filter),
        ("Pyramid Trend", strategies.pyramid_trend),
    ]:
        res = fn(history)
        if res:
            outs.append((name, res))
    return outs

def fetch_history_for_symbol(symbol: str, asof: datetime) -> pd.DataFrame:
    with httpx.Client() as client:
        df = latest_bhavcopy(client, asof)
    df["SYMBOL"] = df["SYMBOL"].astype(str).str.upper()
    sdf = df[df["SYMBOL"] == symbol].copy()
    if sdf.empty:
        sdf = df[df["SYMBOL"].str.startswith(symbol)].copy()
    remap = {"OPEN": "OPEN", "HIGH": "HIGH", "LOW": "LOW", "CLOSE": "CLOSE", "TIMESTAMP": "DATE"}
    for k,v in remap.items():
        if k in sdf.columns: 
            sdf[v] = sdf[k]
    if "DATE" not in sdf.columns and "TIMESTAMP" in sdf.columns:
        sdf["DATE"] = sdf["TIMESTAMP"]
    if "DATE" in sdf.columns:
        sdf["DATE"] = pd.to_datetime(sdf["DATE"])
    else:
        sdf["DATE"] = pd.Timestamp(asof.date())
    return sdf.sort_values("DATE")

async def send_reco_email(to_emails, user_name, recos):
    rows = "".join([f"<tr><td>{r['symbol']}</td><td>{r['technique']}</td><td>{r['action']}</td><td>{r['buy_price']:.2f}</td><td>{r['stop_loss']:.2f}</td></tr>" for r in recos])
    html = f\"""
    <h3>Daily Signals</h3>
    <p>Hello {user_name}, here are your recommendations for today.</p>
    <table border="1" cellspacing="0" cellpadding="6">
    <tr><th>Symbol</th><th>Technique</th><th>Action</th><th>Buy</th><th>Stop</th></tr>
    {rows}
    </table>
    \"""
    await send_email(
        host=settings.SMTP_HOST, port=settings.SMTP_PORT, user=settings.SMTP_USER, password=settings.SMTP_PASS,
        from_addr=settings.SMTP_FROM, to_addrs=to_emails, subject="Courtney Signals", html_body=html
    )

from sqlalchemy.orm import Session as OrmSession

@app.get("/api/run_eod")
async def run_eod(secret: str, db: OrmSession = Depends(get_db)):
    if secret != settings.CRON_SHARED_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")
    today = datetime.utcnow()
    users = db.query(User).all()
    all_tasks = []
    for u in users:
        wl = db.execute(select(Watchlist).where(Watchlist.user_id == u.id, Watchlist.active == True)).scalars().all()
        recos = []
        for w in wl:
            hist = fetch_history_for_symbol(w.symbol, today)
            outs = run_all_strategies(hist)
            for name, res in outs:
                recos.append({
                    "symbol": w.symbol, "technique": name, "action": res["action"], "buy_price": res["buy_price"], "stop_loss": res["stop_loss"], "asof": today.isoformat(), "meta": res
                })
        for r in recos:
            db.add(Signal(user_id=u.id, symbol=r["symbol"], technique=r["technique"], action=r["action"], buy_price=r["buy_price"], stop_loss=r["stop_loss"], asof=today, meta=r["meta"]))
        db.commit()
        emails = [e.email for e in u.emails] or [u.email]
        if recos:
            all_tasks.append(send_reco_email(emails, u.name, recos))
    if all_tasks:
        await asyncio.gather(*all_tasks)
    return {"ok": True}

@app.post("/api/portfolio")
def add_portfolio(data: PortfolioIn, current: User = Depends(get_user_from_token), db: Session = Depends(get_db)):
    db.add(Portfolio(user_id=current.id, symbol=data.symbol.upper(), qty=data.qty, avg_price=data.avg_price))
    db.commit()
    return {"ok": True}

@app.post("/api/backtest")
async def backtest(file: UploadFile = File(...)):
    content = await file.read()
    df = pd.read_csv(io.BytesIO(content))
    df.columns = [c.strip().upper() for c in df.columns]
    df["DATE"] = pd.to_datetime(df["DATE"])
    outs = []
    for i in range(60, len(df)):
        window = df.iloc[:i].copy()
        for name, fn in [
            ("Channel Breakout", strategies.channel_breakout),
            ("5-Day Condition", strategies.five_day_condition),
            ("Trend Filter", strategies.trend_filter),
            ("Pyramid Trend", strategies.pyramid_trend),
        ]:
            res = fn(window)
            if res:
                outs.append({"date": df["DATE"].iloc[i-1].date().isoformat(), "technique": name, "action": res["action"], "buy": res["buy_price"], "stop": res["stop_loss"]})
    return {"trades": outs}