import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List
async def send_email(host, port, user, password, from_addr, to_addrs: List[str], subject: str, html_body: str):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = ", ".join(to_addrs)
    part = MIMEText(html_body, "html")
    msg.attach(part)
    await aiosmtplib.send(msg, hostname=host, port=port, start_tls=True, username=user, password=password)