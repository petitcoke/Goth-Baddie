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

# -------- 1. KEEP ALIVE WEB SERVER (REQUIRED FOR CLOUD) --------
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive!"

def run_web_server():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = threading.Thread(target=run_web_server, daemon=True)
    t.start()

# -------- 2. SETUP --------
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN") 
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Set up bot
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

# Initialize Groq Client
if not GROQ_API_KEY:
    print("⚠️ WARNING: GROQ_API_KEY not found. Bot might crash if triggered.")
else:
    print(f"✅ GROQ_API_KEY found: {GROQ_API_KEY[:10]}...")

client = Groq(api_key=GROQ_API_KEY)
AI_MODEL = "llama-3.3-70b-versatile"  # Updated model name

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
            "Nobody asked + ratio + L + touch grass 💀",
            "Shut up + you fell off + cringe + cope 🤡",
            "L + ratio + you're not funny + nobody cares 🗑️",
            "Take the L + go outside 💀",
            "Bro thinks he's him (he's not) 🤡",
            "Skill issue + cope + seethe 💀",
            "Didn't ask + don't care + L + ratio 🗑️",
            "You're the human equivalent of a participation trophy 🤡"
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
system_prompt = "YOU ARE PACKGOD. Toxic, fast, aggressive roaster. Keep responses SHORT (1-2 sentences MAX). Use emojis: 💀 🤡 🗑️. Be brutal but creative."
conversation_history = {}

@bot.event
async def on_ready():
    print(f"🔥 {bot.user} is online and ready to roast!")
    print(f"📊 Bot is in {len(bot.guilds)} server(s)")

@bot.event
async def on_message(msg):
    if msg.author == bot.user: 
        return
    
    # Debug logging
    print(f"📨 Message from {msg.author}: {msg.content[:50]}")
    
    # Simple history management
    hist = conversation_history.setdefault(msg.channel.id, [])
    hist.append({"role": "user", "content": msg.content})
    
    # Keep only last 10 messages to avoid token limits
    if len(hist) > 10:
        hist = hist[-10:]
        conversation_history[msg.channel.id] = hist
    
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add flavor
    flavor = copypasta_bank.get_random_roasts(1)[0][:150]
    messages.append({"role": "system", "content": f"Roast example style: {flavor}"})
    messages.extend(hist[-6:])  # Keep last 6 messages

    try:
        print(f"🤖 Calling Groq API with model: {AI_MODEL}")
        completion = client.chat.completions.create(
            messages=messages, 
            model=AI_MODEL, 
            temperature=0.9,
            max_tokens=100,
            top_p=1
        )
        reply = completion.choices[0].message.content.strip()
        
        # Ensure reply isn't too long
        if len(reply) > 500:
            reply = reply[:497] + "..."
            
        hist.append({"role": "assistant", "content": reply})
        print(f"✅ Sending reply: {reply[:50]}")
        await msg.channel.send(reply)
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ ERROR: {error_msg}")
        
        # More helpful error messages
        if "model" in error_msg.lower():
            await msg.channel.send("Model error. Try 'llama-3.3-70b-versatile' 💀")
        elif "api" in error_msg.lower() or "key" in error_msg.lower():
            await msg.channel.send("API key issue. Check your GROQ_API_KEY 🔑")
        elif "rate" in error_msg.lower() or "limit" in error_msg.lower():
            await msg.channel.send("Too many requests. Chill. 💀")
        else:
            # Fallback to a random roast if API fails
            fallback = copypasta_bank.get_random_roasts(1)[0]
            await msg.channel.send(f"{fallback} (API broke btw 💀)")

# -------- 4. STARTUP --------
if __name__ == '__main__':
    print("🚀 Starting bot...")
    keep_alive()  # Starts the web server
    if DISCORD_TOKEN:
        print("✅ Discord token found, starting bot...")
        bot.run(DISCORD_TOKEN)
    else:
        print("❌ Error: DISCORD_TOKEN not found in environment variables")
