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

# Set up bot with proper error handling
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
bot = discord.Client(intents=intents)

# Initialize Groq Client
if not GROQ_API_KEY:
    print("⚠️ WARNING: GROQ_API_KEY not found. Bot might crash if triggered.")
else:
    print(f"✅ GROQ_API_KEY found: {GROQ_API_KEY[:10]}...")

client = Groq(api_key=GROQ_API_KEY)
AI_MODEL = "llama-3.3-70b-versatile"

# Bot's application emojis (uploaded directly to the bot)
bot_emojis = []

# Track which channel to spam in (will use the last active channel)
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
        print(f"✅ Loaded {len(self.roasts)} roasts (scraped: {len(scraped)}).")

    def get_random_roasts(self, count=1):
        if not self.roasts: return self.get_hardcoded_roasts()[:count]
        return random.sample(self.roasts, min(count, len(self.roasts)))

copypasta_bank = CopypastaBank()

def get_emoji_list():
    """Get a random selection of bot's application emojis"""
    if not bot_emojis:
        return "💀 🤡 🗑️"  # Fallback to standard emojis if no bot emojis
    
    # Pick 1-3 random bot emojis
    selected = random.sample(bot_emojis, min(random.randint(1, 3), len(bot_emojis)))
    return " ".join([str(emoji) for emoji in selected])

def add_emojis_to_text(text):
    """Add bot's emojis to the response"""
    emojis = get_emoji_list()
    
    # Sometimes add emoji at end, sometimes sprinkle throughout
    if random.random() > 0.5:
        return f"{text} {emojis}"
    else:
        # Add emoji in the middle or at key points
        words = text.split()
        if len(words) > 5:
            insert_pos = random.randint(len(words)//2, len(words)-1)
            words.insert(insert_pos, emojis)
            return " ".join(words)
        else:
            return f"{text} {emojis}"

# Create system prompt that tells AI to use emoji placeholders
system_prompt = """YOU ARE PACKGOD. Toxic, fast, aggressive roaster. Keep responses SHORT (1-2 sentences MAX). 
Be brutal but creative. Use [EMOJI] as a placeholder where emojis should go - they'll be replaced with custom Discord emojis automatically."""

conversation_history = {}

# Heartbeat to detect if bot is still connected
last_heartbeat = time.time()

async def heartbeat_task():
    """Periodically log that bot is still alive"""
    global last_heartbeat
    while True:
        await bot.wait_until_ready()
        await asyncio.sleep(60)
        last_heartbeat = time.time()
        print(f"💓 Heartbeat - Bot connected ({len(bot.guilds)} servers, {len(bot_emojis)} bot emojis)")

async def voices_task():
    """Send 'stfu voices in my head' every minute"""
    global last_active_channel
    await bot.wait_until_ready()
    
    while True:
        try:
            await asyncio.sleep(60)  # Wait 1 minute
            
            if last_active_channel:
                # Add random bot emojis to make it spicy
                emojis = get_emoji_list()
                message = f"stfu voices in my head {emojis}"
                
                await last_active_channel.send(message)
                print(f"🗣️ Sent voices message to {last_active_channel.name}")
            else:
                print("⚠️ No active channel to send voices message")
        except Exception as e:
            print(f"❌ Error in voices_task: {e}")
            traceback.print_exc()

@bot.event
async def on_ready():
    global bot_emojis
    print(f"🔥 {bot.user} is online and ready to roast!")
    print(f"📊 Bot is in {len(bot.guilds)} server(s)")
    
    # Load ONLY the bot's application emojis (not server emojis)
    try:
        # Fetch bot's application info to get its emojis
        app_info = await bot.application_info()
        
        # Get bot emojis from the first guild (application emojis show up there)
        # Actually, application emojis are accessed differently...
        # We need to use bot.emojis which shows all emojis the bot can use
        # But we'll filter to only bot-owned emojis
        
        # For now, let's just get all emojis and you can filter manually
        # Bot application emojis will have a specific format
        for emoji in bot.emojis:
            # Application emojis belong to no specific guild
            # They're accessible via bot.emojis
            bot_emojis.append(emoji)
            print(f"  ✅ Loaded bot emoji: {emoji.name} -> {emoji}")
        
        print(f"🎨 Total bot emojis loaded: {len(bot_emojis)}")
        
        if len(bot_emojis) == 0:
            print("⚠️ WARNING: No bot emojis found! Make sure you uploaded emojis to the bot application.")
            print("   The bot will use fallback emojis (💀 🤡 🗑️) instead.")
    except Exception as e:
        print(f"❌ Error loading bot emojis: {e}")
        traceback.print_exc()
    
    # Start heartbeat
    bot.loop.create_task(heartbeat_task())
    
    # Start voices spam task
    bot.loop.create_task(voices_task())
    print("🗣️ Started 'voices in my head' task (every 1 minute)")

@bot.event
async def on_disconnect():
    print("⚠️ BOT DISCONNECTED FROM DISCORD!")
    print(f"Last heartbeat was {time.time() - last_heartbeat:.1f} seconds ago")

@bot.event
async def on_error(event, *args, **kwargs):
    print(f"❌ Discord Error in {event}:")
    traceback.print_exc()

@bot.event
async def on_message(msg):
    global last_active_channel
    
    if msg.author == bot.user: 
        return
    
    # Update last active channel
    last_active_channel = msg.channel
    
    try:
        print(f"📨 Message from {msg.author}: {msg.content[:50]}")
        
        # Simple history management
        hist = conversation_history.setdefault(msg.channel.id, [])
        hist.append({"role": "user", "content": msg.content})
        
        # Keep only last 10 messages
        if len(hist) > 10:
            hist = hist[-10:]
            conversation_history[msg.channel.id] = hist
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add flavor
        flavor = copypasta_bank.get_random_roasts(1)[0][:150]
        messages.append({"role": "system", "content": f"Roast example style: {flavor}"})
        messages.extend(hist[-6:])

        try:
            print(f"🤖 Calling Groq API...")
            completion = client.chat.completions.create(
                messages=messages, 
                model=AI_MODEL, 
                temperature=0.9,
                max_tokens=100,
                top_p=1
            )
            reply = completion.choices[0].message.content.strip()
            
            # Add bot emojis to the reply
            reply = add_emojis_to_text(reply)
            
            # Replace [EMOJI] placeholders if AI used them
            if "[EMOJI]" in reply:
                reply = reply.replace("[EMOJI]", get_emoji_list())
            
            if len(reply) > 500:
                reply = reply[:497] + "..."
                
            hist.append({"role": "assistant", "content": reply})
            print(f"✅ Sending: {reply[:50]}")
            await msg.channel.send(reply)
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ API ERROR: {error_msg}")
            
            if "model" in error_msg.lower():
                await msg.channel.send(f"Model error {get_emoji_list()}")
            elif "api" in error_msg.lower() or "key" in error_msg.lower():
                await msg.channel.send(f"API key issue {get_emoji_list()}")
            elif "rate" in error_msg.lower() or "limit" in error_msg.lower():
                await msg.channel.send(f"Too many requests. Chill. {get_emoji_list()}")
            else:
                fallback = copypasta_bank.get_random_roasts(1)[0]
                await msg.channel.send(f"{fallback} (API broke btw {get_emoji_list()})")
    
    except Exception as e:
        print(f"❌ CRITICAL ERROR in on_message:")
        traceback.print_exc()

# -------- 4. STARTUP --------
if __name__ == '__main__':
    print("🚀 Starting bot...")
    print(f"Python version: {sys.version}")
    print(f"Discord.py version: {discord.__version__}")
    
    keep_alive()
    
    if DISCORD_TOKEN:
        print("✅ Discord token found, starting bot...")
        try:
            bot.run(DISCORD_TOKEN, log_handler=None)
        except Exception as e:
            print(f"❌ FATAL ERROR:")
            traceback.print_exc()
    else:
        print("❌ Error: DISCORD_TOKEN not found in environment variables")
