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
    # Render assigns a port automatically via 'PORT' env var
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = threading.Thread(target=run_web_server)
    t.start()

# -------- 2. SETUP --------
load_dotenv()
# FIX: Make sure these match the Variable Names in Render later!
DISCORD_TOKEN = os.getenv("TOKEN") 
GROQ_API_KEY = os.getenv("GROQ_API_KEY") # Fixed variable name

# Set up bot
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

# Initialize Groq Client
if not GROQ_API_KEY:
    print("⚠️ WARNING: GROQ_API_KEY not found. Bot might crash if triggered.")
client = Groq(api_key=GROQ_API_KEY)
AI_MODEL = "llama3-70b-8192"

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
                except Exception: continue
            return list(set(all_texts))
        except Exception: return []

    def get_hardcoded_roasts(self):
        return [
            "Nobody asked + ratio + L + touch grass",
            "Shut up + you fell off + cringe + cope",
            "L + ratio + you're not funny + nobody cares",
            "Take the L + go outside",
            "Bro thinks he's him (he's not)",
        ]
    
    def load_copypastas(self):
        print("📥 Loading toxic copypastas...")
        self.roasts = self.scrape_packgod_copypastas() + self.get_hardcoded_roasts()
        print(f"✅ Loaded {len(self.roasts)} roasts.")

    def get_random_roasts(self, count=1):
        if not self.roasts: return self.get_hardcoded_roasts()[:count]
        return random.sample(self.roasts, min(count, len(self.roasts)))

copypasta_bank = CopypastaBank()
system_prompt = "YOU ARE PACKGOD. Toxic, fast, aggressive. Short roasts. Use emojis: 💀 🤡 🗑️."
conversation_history = {}

@bot.event
async def on_ready():
    print(f"🔥 {bot.user} is online!")

@bot.event
async def on_message(msg):
    if msg.author == bot.user: return
    
    # Simple history management
    hist = conversation_history.setdefault(msg.channel.id, [])
    hist.append({"role": "user", "content": msg.content})
    
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add flavor
    flavor = copypasta_bank.get_random_roasts(1)[0][:100]
    messages.append({"role": "system", "content": f"Roast style: {flavor}"})
    messages.extend(hist[-6:]) # Keep last 6 messages

    try:
        completion = client.chat.completions.create(
            messages=messages, model=AI_MODEL, temperature=0.8, max_tokens=80
        )
        reply = completion.choices[0].message.content.strip()
        hist.append({"role": "assistant", "content": reply})
        await msg.channel.send(reply)
    except Exception as e:
        print(f"Error: {e}")
        await msg.channel.send("Brain broke. 💀")

# -------- 4. STARTUP --------
if __name__ == '__main__':
    keep_alive()  # Starts the web server
    if DISCORD_TOKEN:
        bot.run(DISCORD_TOKEN) # Uses the variable properly
    else:
        print("❌ Error: TOKEN not found in environment variables")