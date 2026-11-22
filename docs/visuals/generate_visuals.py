"""Generate deterministic architecture previews (Pillow required); no live data."""
from pathlib import Path
from html import escape
from math import hypot
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
# Replace these paths with local equivalents if generating outside Linux.
INK, GREEN, GOLD = '#123f34', '#148464', '#cda12e'
NODES = {
 'browser': (65, 340, 'USER BROWSER', 'PKCE session and forms', '01 / Client'),
 'pages': (335, 200, 'CLOUDFLARE PAGES', 'Static Next.js export', '02 / Frontend · Free'),
 'auth': (635, 230, 'SUPABASE AUTH', 'Google · email · TOTP', '03 / Identity · Free'),
 'mail': (945, 175, 'GMAIL SMTP', 'Codes and recovery', '04 / Delivery'),
 'api': (465, 465, 'RENDER / FASTAPI', 'JWT · roles · scope', '05 / Backend · Free'),
 'db': (925, 500, 'POSTGRESQL', 'oms · encrypted fields', '06 / Database · Free'),
 'library': (65, 540, 'BJILIBRARY', 'Covers and source links', '07 / External source'),
}
EDGES = [('browser','pages'),('browser','auth'),('auth','mail'),('browser','api'),('api','auth'),('api','db'),('browser','library')]
STEPS = [('pages', 'browser', 'pages', '01', 'Load the application', 'Cloudflare delivers static assets. No database secrets reach the browser.'),
 ('auth', 'browser', 'auth', '02', 'Verify identity', 'Supabase handles first-factor sign-in and optional TOTP. Email uses SMTP.'),
 ('api', 'browser', 'api', '03', 'Authorize the request', 'FastAPI checks identity, active account, roles, MFA policy and approved scope.'),
 ('db', 'api', 'db', '04', 'Persist with boundaries', 'Restricted SQL role, encrypted personal fields and append-only history.'),
 ('library', 'browser', 'library', '05', 'Read at the original source', 'Local syllabus metadata links outward. Saving progress remains an explicit action.')]

def font(size,bold=False): return ImageFont.truetype(BOLD if bold else FONT,size)
def center(key):
 x,y,*_=NODES[key];return x+110,y+47

def frame(index,phase=0):
 im=Image.new('RGB',(1280,800),'#f1f7f3');d=ImageDraw.Draw(im)
 for x in range(30,1280,28):
  for y in range(150,650,28):d.ellipse((x,y,x+1,y+1),fill='#d8e6dd')
 d.rounded_rectangle((25,20,1255,135),radius=22,fill=INK)
 logo=Image.open(ROOT/'apps/web/public/brand/uttara-oms-emblem.webp').convert('RGBA');logo.thumbnail((58,75));im.paste(logo,(47,40),logo)
 d.text((125,40),'UTTARA OMS',font=font(15,True),fill='#ace1c4')
 d.text((125,65),'How the system connects',font=font(32,True),fill='white')
 d.text((875,51),'FREE-HOSTED PILOT',font=font(13,True),fill='#dcbe65')
 d.text((875,78),'Illustrative flow · not live telemetry',font=font(12),fill='#d0e4d9')
 active,src,dst,no,title,description=STEPS[index]
 for a,b in EDGES:
  p,q=center(a),center(b); hot=(a,b)==(src,dst);color=GREEN if hot else '#aac7b8';width=4 if hot else 2
  d.line((p,q),fill=color,width=width)
  dx,dy=q[0]-p[0],q[1]-p[1];length=hypot(dx,dy);ux,uy=dx/length,dy/length
  tip=(p[0]+dx*.61,p[1]+dy*.61)
  d.polygon([tip,(tip[0]-ux*11+uy*5,tip[1]-uy*11-ux*5),(tip[0]-ux*11-uy*5,tip[1]-uy*11+ux*5)],fill=color)
  if hot:
   t=.26+phase*.37
   cx,cy=p[0]+dx*t,p[1]+dy*t
   d.ellipse((cx-7,cy-7,cx+7,cy+7),fill=GOLD,outline='white',width=2)
 for key,(x,y,label,sub,tag) in NODES.items():
  w,h=230,105;selected=key==active
  d.rounded_rectangle((x+7,y+18,x+w+7,y+h+18),radius=14,fill='#d4e3d9')
  d.rounded_rectangle((x,y+12,x+w,y+h+12),radius=14,fill='#0b4e39' if selected else '#b8d0c1')
  d.rounded_rectangle((x,y,x+w,y+h),radius=14,fill=GREEN if selected else '#ffffff',outline=GREEN if selected else '#bbd3c4',width=2)
  d.text((x+15,y+12),tag.upper(),font=font(10,True),fill='#c4f4dc' if selected else '#6d897b')
  d.text((x+15,y+38),label,font=font(15,True),fill='white' if selected else INK)
  d.text((x+15,y+66),sub,font=font(12),fill='#d0f0df' if selected else '#647e70')
 d.rounded_rectangle((25,675,1255,780),radius=18,fill='white',outline='#c5d9cb',width=1)
 d.rounded_rectangle((45,698,100,752),radius=12,fill=INK)
 d.text((56,710),no,font=font(22,True),fill='white')
 d.text((122,694),title,font=font(22,True),fill=INK)
 d.text((122,729),description,font=font(14),fill='#627e6f')
 for i in range(5):d.rounded_rectangle((1080+i*27,693,1098+i*27,698),radius=2,fill=GREEN if i==index else '#d6e6dc')
 return im

if __name__=='__main__':
 frames=[frame(i,j/5) for i in range(5) for j in range(6)]
 frames[0].save(HERE/'architecture.gif',save_all=True,append_images=frames[1:],duration=280,loop=0,optimize=True)
 # Exact static vector fallback. HTML supplies the interactive CSS 3D experience.
 parts=['<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="800" viewBox="0 0 1280 800" role="img" aria-labelledby="title desc">',
 '<title id="title">Uttara OMS architecture</title><desc id="desc">Browser downloads Cloudflare static assets, authenticates with Supabase Auth and calls FastAPI. Auth sends email through Gmail. FastAPI uses PostgreSQL and verifies Auth keys. Browser can open BJILibrary source links.</desc>',
 '<rect width="1280" height="800" fill="#f1f7f3"/><rect x="25" y="20" width="1230" height="115" rx="22" fill="#123f34"/>',
 '<text x="55" y="70" font-family="sans-serif" font-size="30" font-weight="700" fill="white">Uttara OMS · Architecture</text>',
 '<text x="55" y="105" font-family="sans-serif" font-size="16" fill="#c9e8d4">Free-hosted pilot · Authentication is separate from organizational authority</text>',
 '<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0L8 4L0 8Z" fill="#5c917a"/></marker></defs>']
 for a,b in EDGES:
  p,q=center(a),center(b);dx,dy=q[0]-p[0],q[1]-p[1]
  # Place directional arrow visibly between cards rather than under a card.
  end=(p[0]+dx*.64,p[1]+dy*.64)
  parts.append(f'<path d="M{p[0]} {p[1]} L{end[0]} {end[1]}" stroke="#8fb4a0" stroke-width="3" fill="none" marker-end="url(#arrow)"/>')
 for key,(x,y,label,sub,tag) in NODES.items():
  parts.append(f'<rect x="{x}" y="{y+12}" width="230" height="105" rx="14" fill="#bdd2c3"/><rect x="{x}" y="{y}" width="230" height="105" rx="14" fill="white" stroke="#aacbbb"/>')
  for yy,txt,size,color,weight in [(y+24,tag.upper(),10,'#6d897b',700),(y+54,label,15,INK,700),(y+80,sub,12,'#647e70',400)]:
   parts.append(f'<text x="{x+15}" y="{yy}" font-family="sans-serif" font-size="{size}" fill="{color}" font-weight="{weight}">{escape(txt)}</text>')
 parts.append('<text x="40" y="730" font-family="sans-serif" font-size="16" fill="#123f34">Server-only SQL · Scope checks · Encrypted personal fields · Append-only history</text></svg>')
 (HERE/'architecture.svg').write_text('\n'.join(parts)+'\n')
 print('Generated architecture.gif and architecture.svg')
