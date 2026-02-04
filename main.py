import os
import threading
from flask import Flask
from dotenv import load_dotenv
import discord
import requests
from bs4 import BeautifulSoup
import random
import time
from groq import Groq
import sys
import traceback
import asyncio
import re

# -------- 1. KEEP ALIVE WEB SERVER --------
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive!"

@app.route('/health')
def health():
    return {"status": "healthy", "bot": "online", "uptime": time.time()}, 200

def run_web_server():
    port = int(os.environ.get('PORT', 8080))
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    app.run(host='0.0.0.0', port=port, threaded=True)

def keep_alive():
    t = threading.Thread(target=run_web_server, daemon=True)
    t.start()

# -------- 2. SETUP --------
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN") 
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
bot = discord.Client(intents=intents)

client = Groq(api_key=GROQ_API_KEY)
AI_MODEL = "llama-3.3-70b-versatile"

# -------- 3. EMOJI CONFIGURATION (HARDCODED FROM IMAGES) --------
EMOJI_MAP = {
    # Animated (GIF) Emojis
    "cat_tongue_gif": "1468613506055147774",
    "heartbreak_gif": "1468605021930393744",
    "gothknife_gif": "1468613744816029798",
    "cutemadhamster_gif": "1468613738159538217",
    "skull_dancing_gif": "1468613535847288953",
    "babes_gif": "1468613789523116289",
    "monsterdrink_gif": "1468613783214886945",
    "heartflame_gif": "1468613780652167221",
    "emoaesthetics_gif": "1468613777351250178",
    "draculaura_gif": "1468613771399532584",
    "bettyboopdance_gif": "1468613765888086160",

    # Static Emojis
    "x_pixelated": "1468605809297592524",
    "leave": "1468605545354104934",
    "xxx": "1468605378991358098",
    "America": "1468605175072555090",
    "thinking_butt": "1468604911804743793",
    "fih": "1468600471743631444",
    "fish": "1468600431906390171",
    "fire": "1468600364717703398",
    "thinking": "1468600282970849383",
    "nerd": "1468600267392942140",
    "gothhearteyes": "1468613760590680293",
    "hkgun": "1468613752671961118",
    "halloweenscream": "1468613750843244674",
    "handgun": "1468613748473200784",
    "teethheart": "1468613736322564166",
    "gothswitch": "1468613730932752569",
    "biteme": "1468613728097534156",
    "gothhart": "1468613726088204600",
    "skeletonpeacesign": "1468613684740755638",
    "cheekygoth": "1468613787488882699",
    "youdied": "1468613785425281146",
    "tiredofthisshit": "1468613773404278784",
    "darkanime": "1468613769683796184",
    "gothwoman": "1468613767746162782",
    "gothnailcare": "1468613764218749020"
}

def format_emoji(name, eid):
    """Adds 'a' prefix for animated gifs as per Discord API requirements."""
    prefix = "a" if name.endswith("_gif") else ""
    return f"<{prefix}:{name}:{eid}>"

FORMATTED_EMOJIS = [format_emoji(name, eid) for name, eid in EMOJI_MAP.items()]

last_active_channel = None

# -------- 4. SANITIZATION & LOGIC --------
def clean_ai_response(text):
    """Removes unicode emojis and square boxes the AI tries to generate."""
    text = text.replace("[EMOJI]", "")
    # Remove non-ASCII characters (standard emojis)
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    # Clean up excess whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def get_emoji_list():
    if not FORMATTED_EMOJIS: return ""
    selected = random.sample(FORMATTED_EMOJIS, min(random.randint(1, 3), len(FORMATTED_EMOJIS)))
    return " ".join(selected)

def add_emojis_to_text(text):
    emojis = get_emoji_list()
    if random.random() > 0.5 or len(text.split()) < 4:
        return f"{text} {emojis}"
    else:
        words = text.split()
        insert_pos = random.randint(len(words)//2, len(words)-1)
        words.insert(insert_pos, emojis)
        return " ".join(words)

# -------- 5. BOT EVENTS --------
system_prompt = """YOU ARE PACKGOD. Toxic, aggressive, high-energy roaster. 
Keep responses 1-2 sentences MAX. 
STRICT RULE: Do NOT use any emojis, symbols, or special characters. Use plain text only. 
I will handle the emojis."""

@bot.event
async def on_ready():
    print(f"🔥 {bot.user} is active. Loaded {len(FORMATTED_EMOJIS)} emojis.")
    bot.loop.create_task(voices_task())

async def voices_task():
    global last_active_channel
    while True:
        await asyncio.sleep(60)
        if last_active_channel:
            try:
                msg = f"stfu voices in my head {get_emoji_list()}"
                await last_active_channel.send(msg)
            except: pass

@bot.event
async def on_message(msg):
    global last_active_channel
    if msg.author == bot.user: return
    last_active_channel = msg.channel

    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": msg.content}
        ]
        
        completion = client.chat.completions.create(
            messages=messages, 
            model=AI_MODEL, 
            temperature=0.9,
            max_tokens=80
        )
        
        raw_reply = completion.choices[0].message.content.strip()
        clean_reply = clean_ai_response(raw_reply)
        final_reply = add_emojis_to_text(clean_reply)
        
        await msg.channel.send(final_reply)
    except Exception as e:
        print(f"Error: {e}")
        await msg.channel.send(f"L + ratio {get_emoji_list()}")

if __name__ == '__main__':
    keep_alive()
    bot.run(DISCORD_TOKEN)
