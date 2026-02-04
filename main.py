# -------- UPDATED EMOJI CONFIGURATION --------

# The keys now match your renamed versions with the "_gif" suffix where applicable
EMOJI_MAP = {
    # Animated (GIF) Emojis - Require <a:name:ID>
    "cat_tongue_gif": "1468613506055147774",
    "heartbreak_gif": "1468605021930393744",
    "gothknife_gif": "14686144816029798", # Verify ID if truncated in screen
    "cutemadhamster_gif": "1468613738159538217",
    "skull_dancing_gif": "1468613535847288953",
    "babes_gif": "1468613789523116289",
    "monsterdrink_gif": "1468613783214886945",
    "heartflame_gif": "1468613780652167221",
    "emoaesthetics_gif": "1468613777351250178",
    "draculaura_gif": "1468613771399532584",
    "bettyboopdance_gif": "1468613765888086160",

    # Static Emojis - Require <:name:ID>
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
    "you_died": "1468613785425281146",
    "tiredofthisshit": "1468613773404278784",
    "darkanime": "1468613769683796184",
    "gothwoman": "1468613767746162782",
    "gothnailcare": "1468613764218749020"
}

def format_emoji(name, eid):
    """
    Automatically detects if an emoji is animated based on the '_gif' suffix.
    """
    prefix = "a" if name.endswith("_gif") else ""
    return f"<{prefix}:{name}:{eid}>"

FORMATTED_EMOJIS = [format_emoji(name, eid) for name, eid in EMOJI_MAP.items()]
