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

# -------- 1. KEEP ALIVE WEB SERVER (REQUIRED FOR CLOUD) --------
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

if not GROQ_API_KEY:
    print("⚠️ WARNING: GROQ_API_KEY not found.")
else:
    print(f"✅ GROQ_API_KEY found: {GROQ_API_KEY[:10]}...")

client = Groq(api_key=GROQ_API_KEY)
AI_MODEL = "llama-3.3-70b-versatile"

# -------- EMOJI CONFIGURATION (HARDCODED IDs) --------
# Mapped exactly from your screenshots
EMOJI_MAP = {
    # Image 1
    "cat_tongue": "1468613506055147774",
    "x_pixelated": "1468605809297592524",
    "leave": "1468605545354104934",
    "xxx": "1468605378991358098",
    "America": "1468605175072555090",
    "heartbreak": "1468605021930393744",
    "thinking_butt": "1468604911804743793",
    "fih": "1468600471743631444",
    "fish": "1468600431906390171",
    "fire": "1468600364717703398",
    "thinking": "1468600282970849383",
    "nerd": "1468600267392942140",
    # Image 2
    "gothhearteyes": "1468613760590680293",
    "hkgun": "1468613752671961118",
    "halloweenscream": "1468613750843244674",
    "handgun": "1468613748473200784",
    "gothknife": "1468613744816029798",
    "cutemadhamster": "1468613738159538217",
    "teethheart": "1468613736322564166",
    "gothswitch": "1468613730932752569",
    "biteme": "1468613728097534156",
    "gothhart": "1468613726088204600",
    "skeletonpeacesign": "1468613684740755638",
    "skull_dancing": "1468613535847288953",
    # Image 3
    "babes": "1468613789523116289",
    "cheekygoth": "1468613787488882699",
    "youdied": "1468613785425281146",
    "monsterdrink": "1468613783214886945",
    "heartflame": "1468613780652167221",
    "emoaesthetics": "1468613777351250178",
    "tiredofthisshit": "1468613773404278784",
    "draculaura": "1468613771399532584",
    "darkanime": "1468613769683796184",
    "gothwoman": "1468613767746162782",
    "bettyboopdance": "1468613765888086160",
    "gothnailcare": "1468613764218749020"
}

# Convert map to list of formatted Discord strings: <:name:ID>
FORMATTED_EMOJIS = [f"<:{name}:{eid}>" for name, eid in EMOJI_MAP.items()]

last_active_channel = None

# -------- 3. COPYPASTA & LOGIC --------
class CopypastaBank:
    def __init__(self):
        self.roasts = []
        self.load_copypastas()
    
    def scrape_packgod_copypastas(self):
        try:
            all_texts = []
            base_url = "https://copypastatext.com/tag/packgod"
            for page in range(1, 2):  
                url = base_url + "/" if page == 1 else f"{base_url}/page/{page}/"
                try:
                    response = requests.get(url, timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
                    if response.status_code != 200: continue
                    soup = BeautifulSoup(response.text, 'html.parser')
                    articles = soup.find_all('article', class_='post')
                    if not articles: articles = soup.find_all('div', class_='entry-content')
                    
                    for article in articles:
                        for p in article.find_all('p'):
                            text = p.get_text().strip()
                            if len(text) > 30 and any(w in text.lower() for w in ['you', 'trash', 'bozo']):
                                all_texts.append(' '.join(text.split()))
                    time.sleep(0.5)
                except Exception as e:
                    print(f"Scrape error: {e}")
                    continue
            return list(set(all_texts))
        except Exception as e:
            print(f"Scraping failed: {e}")
            return []

    def get_hardcoded_roasts(self):
        return [
            "Nobody asked + ratio + L + touch grass",
            "Shut up + you fell off + cringe + cope",
            "L + ratio + you're not funny + nobody cares",
            "Take the L + go outside",
            "Bro thinks he's him (he's not)",
            "Skill issue + cope + seethe",
            "Didn't ask + don't care + L + ratio",
            "You're the human equivalent of a participation trophy"
        ]
    
    def load_copypastas(self):
        print("📥 Loading toxic copypastas...")
        scraped = self.scrape_packgod_copypastas()
        self.roasts = scraped + self.get_hardcoded_roasts()
        print(f"✅ Loaded {len(self.roasts)} roasts.")

    def get_random_roasts(self, count=1):
        if not self.roasts: return self.get_hardcoded_roasts()[:count]
        return random.sample(self.roasts, min(count, len(self.roasts)))

copypasta_bank = CopypastaBank()

def get_emoji_list():
    """Get a random selection of the HARDCODED emojis"""
    if not FORMATTED_EMOJIS:
        return "💀" 
    
    # Pick 1-3 random emojis from our formatted list
    selected = random.sample(FORMATTED_EMOJIS, min(random.randint(1, 3), len(FORMATTED_EMOJIS)))
    return " ".join(selected)

def add_emojis_to_text(text):
    """Add bot's emojis to the response"""
    emojis = get_emoji_list()
    
    if random.random() > 0.5:
        return f"{text} {emojis}"
    else:
        words = text.split()
        if len(words) > 5:
            insert_pos = random.randint(len(words)//2, len(words)-1)
            words.insert(insert_pos, emojis)
            return " ".join(words)
        else:
            return f"{text} {emojis}"

system_prompt = """YOU ARE PACKGOD. Toxic, fast, aggressive roaster. Keep responses SHORT (1-2 sentences MAX). 
Be brutal but creative. Use [EMOJI] as a placeholder where emojis should go."""

conversation_history = {}
last_heartbeat = time.time()

async def heartbeat_task():
    global last_heartbeat
    while True:
        await bot.wait_until_ready()
        await asyncio.sleep(60)
        last_heartbeat = time.time()
        print(f"💓 Heartbeat - Bot connected. Emoji Count: {len(FORMATTED_EMOJIS)}")

async def voices_task():
    global last_active_channel
    await bot.wait_until_ready()
    while True:
        try:
            await asyncio.sleep(60)
            if last_active_channel:
                emojis = get_emoji_list()
                message = f"stfu voices in my head {emojis}"
                await last_active_channel.send(message)
                print(f"🗣️ Sent voices message to {last_active_channel.name}")
        except Exception as e:
            print(f"❌ Error in voices_task: {e}")

@bot.event
async def on_ready():
    print(f"🔥 {bot.user} is online and ready to roast!")
    print(f"✅ Loaded {len(FORMATTED_EMOJIS)} Hardcoded Application Emojis")
    
    # Start background tasks
    bot.loop.create_task(heartbeat_task())
    bot.loop.create_task(voices_task())
    print("🗣️ Started tasks")

@bot.event
async def on_message(msg):
    global last_active_channel
    
    if msg.author == bot.user: 
        return
    
    last_active_channel = msg.channel
    
    try:
        print(f"📨 Message from {msg.author}: {msg.content[:50]}")
        
        hist = conversation_history.setdefault(msg.channel.id, [])
        hist.append({"role": "user", "content": msg.content})
        
        if len(hist) > 10:
            hist = hist[-10:]
            conversation_history[msg.channel.id] = hist
        
        messages = [{"role": "system", "content": system_prompt}]
        flavor = copypasta_bank.get_random_roasts(1)[0][:150]
        messages.append({"role": "system", "content": f"Roast example style: {flavor}"})
        messages.extend(hist[-6:])

        try:
            completion = client.chat.completions.create(
                messages=messages, 
                model=AI_MODEL, 
                temperature=0.9,
                max_tokens=100,
                top_p=1
            )
            reply = completion.choices[0].message.content.strip()
            
            # Add emojis
            reply = add_emojis_to_text(reply)
            if "[EMOJI]" in reply:
                reply = reply.replace("[EMOJI]", get_emoji_list())
            
            if len(reply) > 500:
                reply = reply[:497] + "..."
                
            hist.append({"role": "assistant", "content": reply})
            await msg.channel.send(reply)
            
        except Exception as e:
            print(f"❌ API ERROR: {e}")
            fallback = copypasta_bank.get_random_roasts(1)[0]
            await msg.channel.send(f"{fallback} {get_emoji_list()}")
    
    except Exception as e:
        print(f"❌ CRITICAL ERROR in on_message:")
        traceback.print_exc()

if __name__ == '__main__':
    keep_alive()
    if DISCORD_TOKEN:
        bot.run(DISCORD_TOKEN, log_handler=None)
    else:
        print("❌ Error: DISCORD_TOKEN not found")
