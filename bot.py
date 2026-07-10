import discord
from discord import app_commands
import os
import random
import re
import time
import asyncio

# ── Bot Setup ──────────────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

SUGGESTIONS_CHANNEL  = "❓｜suggestions"
SERVER_CHANGES_CH    = "🔧｜server-changes"
WIPE_ROLE           = "Admin"          # only members with this role can use /wipe
COMMANDS_CHANNEL    = "🔎｜commands"
MYSTERYBOX_ROLES    = ["Admin", "Owner"]   # only these roles can open mystery boxes
GIVEAWAY_ROLES      = ["Admin", "Owner"]   # only these roles can start giveaways

# ── Mystery Box Config ─────────────────────────────────────────────────────────
# Adjust these two to match how your Ticket Tool actually names channels/categories.
TICKET_CHANNEL_PREFIX     = "ticket-"          # e.g. channel name starts with "ticket-"
TICKET_CATEGORY_KEYWORDS  = ["ticket", "dono"] # fallback: category name contains one of these

# (item name, weight in %) — must sum to 100
MYSTERYBOX_ITEMS = [
    ("7 Dedi Boxes of choice — 19€",                       2.00),
    ("500 Kibble Set — 16€",                                2.00),
    ("Instant Ascension → Level 180 — 15€",                 2.00),
    ("15 BPs of choice — 13€",                               2.00),
    ("4 Dedi Boxes of choice — 13€",                        7.67),
    ("8 Breedpairs — 12€",                                  7.67),
    ("3x Origin Set (33 Tokens + 33 Blood) — 10€",          7.67),
    ("200 Kibble Set — 11€",                                7.67),
    ("10 BPs of choice — 9€",                                7.67),
    ("4 Breedpairs — 9€",                                    7.67),
    ("2x Origin Set (22 Tokens + 22 Blood) — 7€",           7.67),
    ("2 Dedi Boxes of choice — 7€",                          7.67),
    ("100 Kibble Set — 6€",                                  7.67),
    ("2 Breedpairs — 5€",                                    7.67),
    ("5 BPs of choice — 5€",                                 7.67),
    ("1x Origin Set (11 Tokens + 11 Blood) — 4€",           7.67),
]
_MYSTERYBOX_NAMES   = [item[0] for item in MYSTERYBOX_ITEMS]
_MYSTERYBOX_WEIGHTS = [item[1] for item in MYSTERYBOX_ITEMS]

# ── Loot Drop Data ─────────────────────────────────────────────────────────────
DROPS = {
    "white": {
        "label": "⚪ White — Starter Kit",
        "normal": (
            "• Toxic Hide Armor (5 pieces)\n"
            "• 10x Bola\n"
            "• Metal Pick\n"
            "• Metal Hatchet\n"
            "• 10x Med Brew"
        ),
        "double": (
            "• Everything from Normal\n"
            "• Crossbow\n"
            "• 20x Potent Tranq Arrows\n"
            "• 1–3x Small XP Potion"
        ),
        "quality": "Primitive",
    },
    "green": {
        "label": "🟢 Green — Resources",
        "normal": (
            "• 75–175x Polymer\n"
            "• 75–175x Cementing Paste\n"
            "• 75–175x Silica Pearls\n"
            "• 75–175x Oil"
        ),
        "double": (
            "• 125–250x Polymer\n"
            "• 125–250x Cementing Paste\n"
            "• 125–250x Silica Pearls\n"
            "• 125–250x Oil"
        ),
        "quality": "—",
    },
    "blue": {
        "label": "🔵 Blue — Alpha Tier",
        "normal": (
            "**Guaranteed:**\n"
            "• 15–35x Potent/Alpha Tranq Arrows\n"
            "• 2–5x Alpha Health Potion\n"
            "• 2–5x Medium XP Potion\n\n"
            "**Gear Pool (1–5 items, no Blueprints):**\n"
            "• Crossbow · Alpha Flak Set (5 pieces)\n"
            "• Alpha Pick · Hatchet · Sickle · Pike"
        ),
        "double": (
            "**Guaranteed:**\n"
            "• 15–35x Potent/Alpha Tranq Arrows\n"
            "• 2–5x Alpha Health Potion\n"
            "• 2–5x Medium XP Potion\n\n"
            "**Gear Pool (3–7 items, 20% Blueprint chance each):**\n"
            "• Crossbow · Alpha Flak Set (5 pieces)\n"
            "• Alpha Pick · Hatchet · Sickle · Pike"
        ),
        "quality": "—",
    },
    "purple": {
        "label": "🟣 Purple — Structures",
        "normal": (
            "• 10x Metal Foundation\n"
            "• 15x Metal Wall\n"
            "• 10x Metal Ceiling\n"
            "• Dino Gateway + Gate\n"
            "• 3x Dedicated Storage"
        ),
        "double": (
            "• 20x Metal Foundation\n"
            "• 30x Metal Wall\n"
            "• 20x Metal Ceiling\n"
            "• Dino Gateway + Gate\n"
            "• 5x Dedicated Storage"
        ),
        "quality": "—",
    },
    "yellow": {
        "label": "🟡 Yellow — Volcanic Tier",
        "normal": (
            "**Guaranteed:**\n"
            "• 10–20x Tranq Dart (random: Elemental/Alpha/Potent)\n"
            "• 8–16x Elemental ADV Sniper Bullets\n"
            "• 2–5x Large XP Potion\n"
            "• 1–5x Mythic Health Potion\n\n"
            "**Gear Pool (1–5 items, no Blueprints):**\n"
            "• Longneck · Volcanic Flak Set (5 pieces)\n"
            "• Volcanic Pick · Hatchet · Sickle · Pike · Fab Sniper (Mastercraft)"
        ),
        "double": (
            "**Guaranteed:**\n"
            "• 10–20x Tranq Dart (random: Elemental/Alpha/Potent)\n"
            "• 8–24x Elemental ADV Sniper Bullets\n"
            "• 2–5x Large XP Potion\n"
            "• 1–5x Mythic Health Potion\n\n"
            "**Gear Pool (1–5 items, 20% Blueprint chance each):**\n"
            "• Longneck · Volcanic Flak Set (5 pieces)\n"
            "• Volcanic Pick · Hatchet · Sickle · Pike · Fab Sniper (Mastercraft)"
        ),
        "quality": "—",
    },
    "red": {
        "label": "🔴 Red — Endgame Exclusives",
        "normal": (
            "**Guaranteed:**\n"
            "• 8–25x Mythic/Primal ADV Sniper Bullets (random)\n"
            "• 1–2x Max XP Potion\n"
            "• 1–2x Nightmare Health Potion\n"
            "• 8–25x Primal Compound Bow Arrows\n\n"
            "**Gear Pool (1–5 items, no Blueprints):**\n"
            "• Fab Sniper · Mythic Flak Set (5 pieces)\n"
            "• Legend Riot Set (5 pieces)"
        ),
        "double": (
            "**Guaranteed:**\n"
            "• 8–25x Mythic/Primal ADV Sniper Bullets (random)\n"
            "• 1–2x Max XP Potion\n"
            "• 1–2x Nightmare Health Potion\n"
            "• 8–25x Primal Compound Bow Arrows\n"
            "• Additional guaranteed Primal ADV Sniper Bullets\n\n"
            "**Gear Pool (1–5 items, 20% Blueprint chance each):**\n"
            "• Fab Sniper · Mythic Flak Set (5 pieces)\n"
            "• Legend Riot Set (5 pieces)\n"
            "• Compound Bow Blueprint (always Blueprint)"
        ),
        "quality": "—",
    },
}

# ── Channel Lock (commands channel) ────────────────────────────────────────────
async def check_channel(interaction: discord.Interaction) -> bool:
    if interaction.channel.name != COMMANDS_CHANNEL:
        correct = discord.utils.get(interaction.guild.channels, name=COMMANDS_CHANNEL)
        channel_mention = f"<#{correct.id}>" if correct else f"**{COMMANDS_CHANNEL}**"
        await interaction.response.send_message(
            f"This command only works in {channel_mention}.",
            ephemeral=True,
        )
        return False
    return True


# ── Channel Lock (ticket channels, for Mystery Box) ────────────────────────────
def is_ticket_channel(channel: discord.abc.GuildChannel) -> bool:
    name = channel.name.lower()
    if name.startswith(TICKET_CHANNEL_PREFIX):
        return True
    category = getattr(channel, "category", None)
    if category and any(kw in category.name.lower() for kw in TICKET_CATEGORY_KEYWORDS):
        return True
    return False


async def check_ticket_channel(interaction: discord.Interaction) -> bool:
    if not is_ticket_channel(interaction.channel):
        await interaction.response.send_message(
            "❌ This command only works inside a **Dono-request** ticket. "
            "Open a ticket first to use Mystery Boxes.",
            ephemeral=True,
        )
        return False

    user_role_names = {role.name for role in interaction.user.roles}
    if not user_role_names.intersection(MYSTERYBOX_ROLES):
        roles_text = " / ".join(MYSTERYBOX_ROLES)
        await interaction.response.send_message(
            f"❌ Only **{roles_text}** can open Mystery Boxes.",
            ephemeral=True,
        )
        return False

    return True


# ── /commands ──────────────────────────────────────────────────────────────────
@tree.command(name="commands", description="Shows all available bot commands")
async def commands_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📋 Available Commands",
        description="Here's everything the bot can do:",
    )
    embed.add_field(
        name="🎁 Drops",
        value=(
            "`/drop <color>` — Full contents of a specific supply crate\n"
            "`/drops` — Quick overview of all drop colors"
        ),
        inline=False,
    )
    embed.add_field(
        name="🎯 Taming",
        value="`/taming-guide` — Ammo tiers & damage multiplier explained",
        inline=False,
    )
    embed.add_field(
        name="🛡️ Armor",
        value="`/armor-guide` — All armor tiers and perks explained",
        inline=False,
    )
    embed.add_field(
        name="📊 Server Info",
        value="`/mods` — List of all active mods with descriptions",
        inline=False,
    )
    embed.add_field(
        name="💡 Suggestions",
        value="`/suggestion <text>` — Submit a suggestion",
        inline=False,
    )
    embed.add_field(
        name="📦 Mystery Box",
        value=(
            "`/mysterybox1` — Open 1 Mystery Box (inside a Dono-request ticket)\n"
            "`/mysterybox2` — Open 2 Mystery Boxes\n"
            "`/mysterybox3` — Open 3 Mystery Boxes"
        ),
        inline=False,
    )
    embed.add_field(
        name="🎉 Giveaways",
        value="`/giveaway-start` — [Admin only] Start a new giveaway",
        inline=False,
    )

    embed.set_footer(text="Primal Hell • ARK Survival Ascended")
    await interaction.response.send_message(embed=embed)


# ── /drop Command ──────────────────────────────────────────────────────────────
@tree.command(name="drop", description="Shows the contents of a loot drop")
@app_commands.describe(color="Which drop color?")
@app_commands.choices(color=[
    app_commands.Choice(name="⚪ White — Starter Kit",       value="white"),
    app_commands.Choice(name="🟢 Green — Resources",         value="green"),
    app_commands.Choice(name="🔵 Blue — Alpha Tier",         value="blue"),
    app_commands.Choice(name="🟣 Purple — Structures",       value="purple"),
    app_commands.Choice(name="🟡 Yellow — Volcanic Tier",    value="yellow"),
    app_commands.Choice(name="🔴 Red — Endgame Exclusives",  value="red"),
])
async def drop_command(interaction: discord.Interaction, color: str):
    if not await check_channel(interaction):
        return

    data = DROPS[color]
    q = f"\n**Quality:** {data['quality']}" if data["quality"] != "—" else ""

    embed = discord.Embed(title=f"Drop — {data['label']}")
    embed.add_field(name="Normal", value=data["normal"] + q, inline=False)
    embed.add_field(name="\u200b", value="\u200b", inline=False)  # spacer
    embed.add_field(name="Double (with Ring)", value=data["double"] + q, inline=False)
    embed.set_footer(text="Primal Hell • ARK Survival Ascended")
    await interaction.response.send_message(embed=embed)


# ── /drops Command ─────────────────────────────────────────────────────────────
@tree.command(name="drops", description="Shows all loot drops at a glance")
async def drops_command(interaction: discord.Interaction):
    if not await check_channel(interaction):
        return

    embed = discord.Embed(
        title="Drop — Overview",
        description=(
            "⚪ White → Starter Kit\n"
            "🟢 Green → Resources\n"
            "🔵 Blue → Alpha Tier\n"
            "🟣 Purple → Structures\n"
            "🟡 Yellow → Volcanic Tier\n"
            "🔴 Red → Endgame Exclusives\n\n"
            "Use `/drop <color>` for full details.\n"
            "**Double** = Crate with ring — always better!"
        )
    )
    embed.set_footer(text="Primal Hell • ARK Survival Ascended")
    await interaction.response.send_message(embed=embed)


# ── /taming-guide ──────────────────────────────────────────────────────────────
@tree.command(name="taming-guide", description="Tranq ammo tiers & Fab Sniper multiplier explained")
async def taming_guide_command(interaction: discord.Interaction):
    if not await check_channel(interaction):
        return

    embed = discord.Embed(
        title="🎯 Taming Guide — Primal Chaos",
        description=(
            "Primal Chaos adds tiered tranq ammo — the higher the tier, the more torpor per hit. "
            "Combined with a higher % Fab Sniper blueprint, the effect multiplies significantly.\n\u200b"
        ),
    )

    embed.add_field(
        name="🔫 Fab Sniper — ADV Sniper Bullets @ 100% weapon",
        value=(
            "• Potent → **2.1k** torpor\n"
            "• Alpha → **4.6k** torpor\n"
            "• Elemental → **8.6k** torpor\n"
            "• Mythic → **13k** torpor\n"
            "• Primal → **20.8k** torpor"
        ),
        inline=True,
    )

    embed.add_field(
        name="🎯 Longneck — Tranq Darts @ 100% weapon",
        value=(
            "• Potent → **1.9k** torpor\n"
            "• Alpha → **3.8k** torpor\n"
            "• Elemental → **7.4k** torpor\n"
            "• Mythic → **11.3k** torpor"
        ),
        inline=True,
    )

    embed.add_field(
        name="🪃 Crossbow — Tranq Arrows @ 100% weapon",
        value=(
            "• Potent → **640** torpor\n"
            "• Alpha → **1.2k** torpor"
        ),
        inline=True,
    )

    embed.add_field(
        name="📈 Weapon % Multiplier (Fab Sniper Example)",
        value=(
            "The weapon % on a blueprint scales torpor directly.\n\n"
            "**Formula:** `Base Torpor × (Weapon % ÷ 100)`\n\n"
            "Example with **Mythic ADV Bullet (13k base)**:\n"
            "• 100% → **13k** torpor\n"
            "• 200% → **26k** torpor\n"
            "• 300% → **39k** torpor\n\n"
            "⚠️ *Values tested on a Bronto. Torpor per hit varies by dino.*"
        ),
        inline=False,
    )

    embed.add_field(
        name="💡 Taming Tips",
        value=(
            "• Use the **Awesome Spyglass** to monitor torpor & max torpor in real time\n"
            "• Higher tier ammo isn't always needed — Potent/Alpha works fine on weaker dinos\n"
            "• Mythic/Primal Bullets recommended for high-level Chaos dinos or boss tames\n"
            "• **Boss dinos** must be brought below 20% HP before they take any torpor"
        ),
        inline=False,
    )

    embed.set_footer(text="Primal Hell • ARK Survival Ascended")
    await interaction.response.send_message(embed=embed)


# ── /suggestion ────────────────────────────────────────────────────────────────
@tree.command(name="suggestion", description="Submit a suggestion to the admins")
@app_commands.describe(text="Your suggestion")
async def suggestion_command(interaction: discord.Interaction, text: str):
    suggestions_ch = discord.utils.get(interaction.guild.channels, name=SUGGESTIONS_CHANNEL)

    if suggestions_ch is None:
        await interaction.response.send_message(
            f"❌ Could not find the **{SUGGESTIONS_CHANNEL}** channel.",
            ephemeral=True,
        )
        return

    embed = discord.Embed(
        title="💡 New Suggestion",
        description=text,
        color=discord.Color.gold(),
    )
    embed.set_author(
        name=interaction.user.display_name,
        icon_url=interaction.user.display_avatar.url,
    )
    embed.set_footer(text=f"User ID: {interaction.user.id} | Primal Hell • ARK Survival Ascended")

    msg = await suggestions_ch.send(embed=embed)

    # Add voting reactions
    await msg.add_reaction("✅")
    await msg.add_reaction("➖")
    await msg.add_reaction("❌")

    await interaction.response.send_message(
        f"✅ Your suggestion has been submitted to {suggestions_ch.mention}!",
        ephemeral=True,
    )


# ── /mods ──────────────────────────────────────────────────────────────────────
@tree.command(name="mods", description="Shows all active mods on the server")
async def mods_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🔧 Active Mods — Primal Hell",
        description="These mods are currently running on the server:",
    )
    embed.add_field(
        name="⚔️ Gameplay Overhaul",
        value=(
            "**ARK Primal Chaos** — Full overhaul mod: new dino tiers, weapons, armor & bosses\n"
            
        ),
        inline=False,
    )
    embed.add_field(
        name="🦕 Dino Tools",
        value=(
            "**Awesome Spyglass** — Extended spyglass with live stat display for dinos\n"
            "**Dino Depot** — Dino management & storage\n"
            "**Der Dino Finder** — Locate any dino on the map"
        ),
        inline=False,
    )
    embed.add_field(
        name="⚙️ Quality of Life",
        value=(
            "**TG Stacking Mod 1000-50** — Stack size ×1000, weight reduced by 50%\n"
            "**A Simple Performance Mod (60 FPS)** — Automatically runs performance commands on join "
            "(see below for full list)\n"
            "**Crash Protector** — Protects your character from wild dinos and drowning when you crash\n"
            "**Better Breeding** — Garanties always the better stats while breeding\n"
            "**Tribute Table** — Craft and summon all boss fights directly — no artifact or tribute farming required"
        ),
        inline=False,
    )
    embed.add_field(
        name="🖥️ Performance Mod — Applied Commands (PC)",
        value=(
            "`r.VolumetricCloud 0` — Disables clouds\n"
            "`r.Nanite.MaxPixelsPerEdge 4` — Reduces triangle count\n"
            "`foliage.MaxTrianglesToRender 500000` — Limits foliage rendering"
        ),
        inline=False,
    )
    embed.add_field(
        name="🎮 Performance Mod — Additional Commands (Console only)",
        value=(
            "`sg.GlobalIlluminationQuality 2` · `sg.ResolutionQuality 80`\n"
            "`sg.AntiAliasingQuality 1` · `sg.ShadowQuality 2` · `sg.ShadingQuality 1`\n"
            "`sg.PostProcessQuality 1` · `sg.FoliageQuality 1` · `sg.EffectsQuality 1`\n"
            "`sg.ReflectionQuality 1` · `sg.TextureQuality 2` · `r.Vsync 1`\n"
            "`r.ScreenPercentage 50` · `r.DynamicRes.MinScreenPercentage 50`\n"
            "`r.Lumen.ScreenProbeGather.RadianceCache.ProbeResolution 16`"
        ),
        inline=False,
    )
    embed.set_footer(text="Primal Hell • ARK Survival Ascended")
    await interaction.response.send_message(embed=embed)


# ── /armor-guide ───────────────────────────────────────────────────────────────
@tree.command(name="armor-guide", description="Armor tier overview with perks")
async def armor_command(interaction: discord.Interaction):
    if not await check_channel(interaction):
        return

    embed = discord.Embed(
        title="🛡️ Primal Chaos Armor Guide",
        description=(
            "Armor progresses through 5 tiers. Higher tiers offer better protection "
            "and unique passive perks on certain pieces. All Primal Chaos flak armors "
            "drop exclusively as Blueprints.\n\u200b"
        ),
    )
    embed.add_field(
        name="1️⃣ Hide Toxic — Starter",
        value=(
            "Basic protection for early game survival.\n"
            "Available from the ⚪ **White drop**."
        ),
        inline=False,
    )
    embed.add_field(
        name="2️⃣ Alpha Flak — Alpha Tier",
        value=(
            "Solid mid-game armor, upgrade from Toxic Hide.\n"
            "Available from the 🔵 **Blue drop** (Blueprint, Double only)."
        ),
        inline=False,
    )
    embed.add_field(
        name="3️⃣ Volcanic Flak — Volcanic Tier",
        value=(
            "Strong late-game armor with improved stats.\n"
            "Available from the 🟡 **Yellow drop** (Blueprint, Double only)."
        ),
        inline=False,
    )
    embed.add_field(
        name="4️⃣ Mythic Flak — Mythic Tier ⭐ (2500 armor)",
        value=(
            "High-end armor with piece-specific passive perks.\n"
            "Available from the 🔴 **Red drop** (Blueprint, Double only).\n\n"
            "🪖 Helmet → **×4 Food & Water**\n"
            "👕 Chestpiece → **×4 Weight**\n"
            "🧤 Gauntlets → **×4 Crafting Speed**\n"
            "👖 Leggings → **×4 Stamina**\n"
            "👢 Boots → **×4 Fall Damage Reduction**"
        ),
        inline=False,
    )
    embed.add_field(
        name="5️⃣ Legend Riot — Legend Tier ⭐⭐ (3000 armor)",
        value=(
            "Top-tier armor with the strongest passive perks.\n"
            "Available from the 🔴 **Red drop** (Blueprint, Double only).\n\n"
            "🪖 Helmet → **×4 Health**\n"
            "👕 Chestpiece → **×4 Torpor Resistance**\n"
            "🧤 Gauntlets → **×4 Melee Damage**\n"
            "👖 Leggings → **×4 Stamina**\n"
            "👢 Boots → **+25% Movement Speed**"
        ),
        inline=False,
    )
    embed.add_field(name="​", value="​", inline=False)
    embed.add_field(
        name="📊 Base Stats — Armor Values (per piece)",
        value=(
            "• Alpha Flak → **500** armor\n"
            "• Volcanic Flak → **1000** armor\n"
            "• Mythic Flak → **2500** armor\n"
            "• Legend Riot → **3000** armor"
        ),
        inline=True,
    )
    embed.add_field(
        name="📝 Notes",
        value=(
            "• Flak Blueprints can be found in supply drops\n"
            "• The **Upgrade Station** can upgrade finished armor pieces to higher quality\n"
            "• ⚠️ The Upgrade Station works on **ARK base items only** — "
            "Primal Chaos items with no base ARK equivalent (e.g. Reaper saddle) cannot be upgraded"
        ),
        inline=True,
    )
    embed.set_footer(text="Primal Hell • ARK Survival Ascended")
    await interaction.response.send_message(embed=embed)


# ── /wipe ──────────────────────────────────────────────────────────────────────
@tree.command(name="wipe", description="[Admin only] Announce an upcoming wild dino wipe in #announcements")
async def wipe_command(interaction: discord.Interaction):
    role = discord.utils.get(interaction.guild.roles, name=WIPE_ROLE)
    if role not in interaction.user.roles:
        await interaction.response.send_message(
            f"❌ You need the **{WIPE_ROLE}** role to use this command.",
            ephemeral=True,
        )
        return

    announcements_ch = discord.utils.get(interaction.guild.channels, name="📣｜announcements")
    if announcements_ch is None:
        await interaction.response.send_message(
            "❌ Could not find the **📣｜announcements** channel.",
            ephemeral=True,
        )
        return

    embed = discord.Embed(
        title="⚠️ Wild Dino Wipe — 15 Minute Warning",
        description=(
            "**A wild dino wipe will take place in 15 minutes.**\n\n"
            "All wild dinosaurs on the map will be removed and will begin respawning shortly after. "
            "This is a routine reset to restore creature spawns that are no longer appearing in the world.\n\n"
            "Please make sure your tames are secured before the wipe takes place.\n"
            "There may be a brief lag spike when the wipe is executed — this is normal."
        ),
        color=discord.Color.red(),
    )
    embed.set_footer(text=f"Announced by {interaction.user.display_name} • Primal Hell")

    await announcements_ch.send(content="@everyone", embed=embed)

    await interaction.response.send_message(
        f"✅ Wipe warning posted in {announcements_ch.mention}.",
        ephemeral=True,
    )


# ── Active Giveaway State ─────────────────────────────────────────────────────
active_giveaway = {}   # guild_id → {"number", "guess_channel_id", "announce_channel_id", "range_max", "reward"}

# ── Event Configs — add new tiers here if needed ───────────────────────────────
EVENT_CONFIGS = {
    "100":  {"range_max": 100,  "reward": "5€"},
    "500":  {"range_max": 500,  "reward": "10€"},
    "1000": {"range_max": 1000, "reward": "20€"},
}


# ── Generic Event Starter (shared logic for all guessing giveaways) ───────────
async def start_guess_event(interaction: discord.Interaction, range_max: int, reward: str):
    role = discord.utils.get(interaction.guild.roles, name=WIPE_ROLE)
    if role not in interaction.user.roles:
        await interaction.response.send_message(
            f"❌ You need the **{WIPE_ROLE}** role to use this command.",
            ephemeral=True,
        )
        return

    if not await check_channel(interaction):
        return

    events_ch = discord.utils.get(interaction.guild.channels, name="🎉｜events")
    if events_ch is None:
        await interaction.response.send_message(
            "❌ Could not find the **🎉｜events** channel.", ephemeral=True
        )
        return

    global_ch = discord.utils.get(interaction.guild.channels, name="🌍｜chat")
    if global_ch is None:
        await interaction.response.send_message(
            "❌ Could not find the **🌍｜chat** channel.", ephemeral=True
        )
        return

    number = random.randint(1, range_max)

    active_giveaway[interaction.guild.id] = {
        "number": number,
        "guess_channel_id": global_ch.id,
        "announce_channel_id": events_ch.id,
        "range_max": range_max,
        "reward": reward,
    }

    embed = discord.Embed(
        title="🎉 Global Chat Giveaway!",
        description=(
            "A giveaway is now live in the **Global Chat**!\n\n"
            f"Guess a number between **1 and {range_max}**.\n"
            f"The first player to guess the correct number wins **{reward} Shop Credit**! 🎁\n\n"
            "Type your guess directly in this channel. Good luck! 🍀"
        ),
        color=discord.Color.gold(),
    )
    embed.set_footer(text="Primal Hell • ARK Survival Ascended")

    await events_ch.send(content="@everyone", embed=embed)

    await interaction.response.send_message(
        f"✅ Giveaway started in {events_ch.mention}. Range: 1–{range_max} | "
        f"Reward: {reward} | Secret number: **{number}**",
        ephemeral=True,
    )


# ── /event-100-5 ────────────────────────────────────────────────────────────────
@tree.command(name="event-100-5", description="[Admin only] Start a 1-100 guessing giveaway — 5€ Shop Credit reward")
async def event_100_5_command(interaction: discord.Interaction):
    cfg = EVENT_CONFIGS["100"]
    await start_guess_event(interaction, cfg["range_max"], cfg["reward"])


# ── /event-500-10 ───────────────────────────────────────────────────────────────
@tree.command(name="event-500-10", description="[Admin only] Start a 1-500 guessing giveaway — 10€ Shop Credit reward")
async def event_500_10_command(interaction: discord.Interaction):
    cfg = EVENT_CONFIGS["500"]
    await start_guess_event(interaction, cfg["range_max"], cfg["reward"])


# ── /event-1000-20 ──────────────────────────────────────────────────────────────
@tree.command(name="event-1000-20", description="[Admin only] Start a 1-1000 guessing giveaway — 20€ Shop Credit reward")
async def event_1000_20_command(interaction: discord.Interaction):
    cfg = EVENT_CONFIGS["1000"]
    await start_guess_event(interaction, cfg["range_max"], cfg["reward"])


# ── Giveaway System ─────────────────────────────────────────────────────────────
active_giveaways = {}  # message_id → {prize, host_id, winners_count, entries, end_time, channel_id}

_DURATION_PATTERN = re.compile(r'(\d+)\s*(d|h|m|s)', re.IGNORECASE)


def parse_duration(duration_str: str) -> int | None:
    """Parses strings like '1d2h30m' or '2h' into total seconds. Returns None if invalid."""
    matches = _DURATION_PATTERN.findall(duration_str.replace(" ", ""))
    if not matches:
        return None
    unit_seconds = {"d": 86400, "h": 3600, "m": 60, "s": 1}
    total = sum(int(value) * unit_seconds[unit.lower()] for value, unit in matches)
    return total if total > 0 else None


def format_duration(seconds: int) -> str:
    days, rem = divmod(int(seconds), 86400)
    hours, rem = divmod(rem, 3600)
    minutes, _ = divmod(rem, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    return " ".join(parts) if parts else "< 1m"


def build_giveaway_embed(giveaway: dict, ended: bool = False) -> discord.Embed:
    end_ts = int(giveaway["end_time"])
    title = f"🎉 {giveaway['prize']}" + (" — ENDED" if ended else "")
    embed = discord.Embed(
        title=title,
        description=(
            f"Ends: <t:{end_ts}:R> (<t:{end_ts}:f>)\n"
            f"Hosted by: <@{giveaway['host_id']}>\n"
            f"Entries: **{len(giveaway['entries'])}**\n"
            f"Winners: **{giveaway['winners_count']}**"
        ),
        color=discord.Color.dark_grey() if ended else discord.Color.blurple(),
    )
    embed.set_footer(text="Primal Hell • ARK Survival Ascended")
    return embed


class GiveawayView(discord.ui.View):
    def __init__(self, message_id: int):
        super().__init__(timeout=None)
        self.message_id = message_id

    @discord.ui.button(label="🎉 Join Giveaway", style=discord.ButtonStyle.blurple, custom_id="giveaway_join")
    async def join_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        giveaway = active_giveaways.get(self.message_id)
        if giveaway is None:
            await interaction.response.send_message("❌ This giveaway has already ended.", ephemeral=True)
            return

        if interaction.user.id in giveaway["entries"]:
            await interaction.response.send_message("✅ You're already entered in this giveaway!", ephemeral=True)
            return

        giveaway["entries"].add(interaction.user.id)
        await interaction.response.send_message("🎉 You've entered the giveaway! Good luck!", ephemeral=True)

        embed = build_giveaway_embed(giveaway)
        try:
            await interaction.message.edit(embed=embed)
        except discord.HTTPException:
            pass


class GiveawayModal(discord.ui.Modal, title="🎉 Start a Giveaway"):
    prize = discord.ui.TextInput(label="Prize", placeholder="e.g. Solo 180 Ascension", max_length=200)
    duration = discord.ui.TextInput(label="Duration (e.g. 1d, 2h30m, 45m)", placeholder="1d", max_length=20)
    winners = discord.ui.TextInput(label="Number of Winners", placeholder="1", max_length=3)

    def __init__(self, channel: discord.TextChannel):
        super().__init__()
        self.channel = channel

    async def on_submit(self, interaction: discord.Interaction):
        seconds = parse_duration(self.duration.value)
        if seconds is None:
            await interaction.response.send_message(
                "❌ Invalid duration format. Use combinations like `1d`, `2h30m`, `45m`.",
                ephemeral=True,
            )
            return

        try:
            winners_count = int(self.winners.value)
            if winners_count < 1:
                raise ValueError
        except ValueError:
            await interaction.response.send_message(
                "❌ Winners must be a positive whole number.", ephemeral=True
            )
            return

        end_time = time.time() + seconds

        giveaway = {
            "prize": self.prize.value,
            "host_id": interaction.user.id,
            "winners_count": winners_count,
            "entries": set(),
            "end_time": end_time,
            "channel_id": self.channel.id,
        }

        embed = build_giveaway_embed(giveaway)
        view = GiveawayView(message_id=0)  # message_id patched right after sending
        msg = await self.channel.send(embed=embed, view=view)
        view.message_id = msg.id
        active_giveaways[msg.id] = giveaway

        await interaction.response.send_message(
            f"✅ Giveaway started in {self.channel.mention}! Ends in {format_duration(seconds)}.",
            ephemeral=True,
        )

        asyncio.create_task(end_giveaway_after(msg.id, seconds))


async def end_giveaway_after(message_id: int, delay: float):
    await asyncio.sleep(delay)
    await finish_giveaway(message_id)


async def finish_giveaway(message_id: int):
    giveaway = active_giveaways.pop(message_id, None)
    if giveaway is None:
        return  # already ended or bot restarted in the meantime

    channel = client.get_channel(giveaway["channel_id"])
    if channel is None:
        return

    try:
        msg = await channel.fetch_message(message_id)
        await msg.edit(embed=build_giveaway_embed(giveaway, ended=True), view=None)
    except discord.HTTPException:
        pass

    entries = list(giveaway["entries"])
    if not entries:
        await channel.send(f"😔 No one entered the **{giveaway['prize']}** giveaway — no winner could be drawn.")
        return

    winners_count = min(giveaway["winners_count"], len(entries))
    winners = random.sample(entries, winners_count)
    winner_mentions = ", ".join(f"<@{uid}>" for uid in winners)

    result_embed = discord.Embed(
        title="🎉 Giveaway Ended!",
        description=(
            f"**Prize:** {giveaway['prize']}\n"
            f"**Winner{'s' if winners_count > 1 else ''}:** {winner_mentions}\n\n"
            "Please open a ticket in **#ticket-system** to claim your prize!"
        ),
        color=discord.Color.green(),
    )
    result_embed.set_footer(text="Primal Hell • ARK Survival Ascended")
    await channel.send(content=winner_mentions, embed=result_embed)


# ── /giveaway-start ─────────────────────────────────────────────────────────────
@tree.command(name="giveaway-start", description="[Admin only] Start a new giveaway")
@app_commands.describe(channel="Channel to post the giveaway in (defaults to the current channel)")
async def giveaway_start_command(interaction: discord.Interaction, channel: discord.TextChannel = None):
    user_role_names = {role.name for role in interaction.user.roles}
    if not user_role_names.intersection(GIVEAWAY_ROLES):
        roles_text = " / ".join(GIVEAWAY_ROLES)
        await interaction.response.send_message(
            f"❌ Only **{roles_text}** can start giveaways.", ephemeral=True
        )
        return

    target_channel = channel or interaction.channel
    await interaction.response.send_modal(GiveawayModal(target_channel))


# ── Mystery Box Logic ──────────────────────────────────────────────────────────
def draw_mysterybox(amount: int) -> list[str]:
    """Draws `amount` items independently (duplicates possible) based on weights."""
    return random.choices(_MYSTERYBOX_NAMES, weights=_MYSTERYBOX_WEIGHTS, k=amount)


async def send_mysterybox_result(interaction: discord.Interaction, amount: int):
    if not await check_ticket_channel(interaction):
        return

    results = draw_mysterybox(amount)

    embed = discord.Embed(
        title=f"📦 Mystery Box{'es' if amount > 1 else ''} Opened!",
        description="\n".join(f"🎁 **{item}**" for item in results),
        color=discord.Color.orange(),
    )
    embed.set_footer(text="Primal Hell • A staff member will fulfill this shortly")

    await interaction.response.send_message(embed=embed)


# ── /mysterybox1, /mysterybox2, /mysterybox3 ──────────────────────────────────
@tree.command(name="mysterybox1", description="Open 1 Mystery Box (Dono-request tickets only)")
async def mysterybox1_command(interaction: discord.Interaction):
    await send_mysterybox_result(interaction, 1)


@tree.command(name="mysterybox2", description="Open 2 Mystery Boxes (Dono-request tickets only)")
async def mysterybox2_command(interaction: discord.Interaction):
    await send_mysterybox_result(interaction, 2)


@tree.command(name="mysterybox3", description="Open 3 Mystery Boxes (Dono-request tickets only)")
async def mysterybox3_command(interaction: discord.Interaction):
    await send_mysterybox_result(interaction, 3)


# ── GitHub Webhook → @everyone ping ───────────────────────────────────────────
@client.event
async def on_message(message: discord.Message):
    # Ignore own messages to prevent infinite loop
    if message.author == client.user:
        return
    # Only react to the GitHub webhook bot in the server-changes channel
    # GitHub webhook → @everyone
    if (message.author.bot
            and message.author != client.user
            and message.channel.name == SERVER_CHANGES_CH):
        await message.channel.send("@everyone")

    # Giveaway guess detection
    if not message.author.bot and message.guild:
        giveaway = active_giveaway.get(message.guild.id)
        if giveaway and message.channel.id == giveaway["guess_channel_id"]:
            try:
                guess = int(message.content.strip())
            except ValueError:
                return
            if guess == giveaway["number"]:
                del active_giveaway[message.guild.id]
                announce_ch = message.guild.get_channel(giveaway["announce_channel_id"])
                reward = giveaway["reward"]
                embed = discord.Embed(
                    title="🎉 We have a winner!",
                    description=(
                        f"Congratulations {message.author.mention}! 🏆\n\n"
                        f"The correct number was **{guess}**!\n"
                        f"You won **{reward} Shop Credit**! 🎁\n"
                        "Please open a ticket in **#ticket-system** to claim your reward!"
                    ),
                    color=discord.Color.green(),
                )
                embed.set_footer(text="Primal Hell • ARK Survival Ascended")
                if announce_ch:
                    await announce_ch.send(content="@everyone", embed=embed)


# ── Start ──────────────────────────────────────────────────────────────────────
@client.event
async def on_ready():
    await tree.sync()
    print(f"✅ Bot online as {client.user}")

client.run(os.environ["DISCORD_TOKEN"])
