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

# -------- 3. COMPREHENSIVE EMOJI CONFIGURATION --------
EMOJI_MAP = {
    # --- ANIMATED GIFS (<a:name:ID>) ---
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
    "thinkweird_gif": "1468626969007751169",
    "scuffledflustered_gif": "1468626956449874244",
    "depressed_gif": "1468626954558373973",
    "elmofire_gif": "1468629304412737631",

    # --- STATIC EMOTES (<:name:ID>) ---
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
    "gothnailcare": "1468613764218749020",
    "why": "1468626986661449738",
    "shy": "1468626983444414494",
    "gamerpills": "1468626973759766648",
    "weirdthink": "1468626971138457701",
    "shyconcern": "1468626965018841301",
    "waiting": "1468626963374805219",
    "pepeover": "1468626961508208683",
    "jerry": "1468626958693961851",
    "deepfriedcry": "1468626952322551858",
    "insanelaughing": "1468627006756491306",
    "pepemegalul": "1468627003598049454",
    "suicide": "1468627000980934757",
    "what": "1468626999047094366",
    "weirdflush": "1468626996710871080",
    "heyy": "1468626994920165418",
    "weirdpepe": "1468626992378282036",
    "suspicious": "1468626990322941963",
    "dogewtf": "1468629274998341870",
    "fireskull": "1468629272489889925",
    "STONKS": "1468629270388670625",
    "cutestaringpussinboots": "1468629268677398765",
    "elmorise": "1468629266383114372",
    "sadcatsleep": "1468629264554528898",
    "garfieldemote": "1468629262633537844",
    "dyinglaughred": "1468629260788039780",
    "chaosgoose": "1468629258745282561",
    "wormonstring": "1468629256828489808",
    "beanerz": "1468629254097866953",
    "chestpain": "1468629252097314857",
    "OGTriggered": "1468629308577808545",
    "garfield": "1468629306895765506",
    "joesuperangry": "1468629301237911594",
    "trumpcheeto": "1468629299266322595",
    "showerpls": "1468629297534079127",
    "hub": "1468629295940370605",
    "skullissue": "1468629293528645978",
    "angrygun": "1468629290806677670",
    "woah": "1468629288990281872",
    "orangewtf": "1468629282614935716",
    "drakeyes": "1468629278840197120"
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
    # Picking 1-3 random emojis from the massive list
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
