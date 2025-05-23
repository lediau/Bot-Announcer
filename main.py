from dotenv import load_dotenv
import discord
from discord.ext import commands
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from notion_client import Client as NotionClient
import os
from openai import OpenAI
import pandas as pd
from datetime import datetime
import re

# Load environment variables
load_dotenv()

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
NOTION_TOKEN = os.getenv("NOTION_API_TOKEN")
OPENAI_TOKEN = os.getenv("OPENAI_TOKEN")

KEYS_SHEET_URL = os.getenv("KEYS_SHEET_URL")
RESOURCE_SHEET_URL = os.getenv("RESOURCE_SHEET_URL")

client = OpenAI(base_url="https://litellm.aks-hs-prod.int.hyperskill.org/v1",
                api_key=OPENAI_TOKEN)

COHORT_DICT = pd.read_csv(KEYS_SHEET_URL, dtype=str).set_index("cohort").to_dict(orient="index")

with open("resource_template.txt", "r", encoding="utf-8") as file:
    RESOURCE_TEMPLATE = file.read()

with open("schedule_template.txt", "r", encoding="utf-8") as file:
    SCHEDULE_TEMPLATE = file.read()

with open("schedule_2_tracks_template.txt", "r", encoding="utf-8") as file:
    SCHEDULE_2_TEMPLATE = file.read()

# Initialize clients
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
notion = NotionClient(auth=NOTION_TOKEN)

# Scheduler
scheduler = AsyncIOScheduler()


@bot.event
async def on_ready():
    await asyncio.sleep(5)
    print(f"Bot is ready. Logged in as {bot.user}")

    # Schedule the Monday Schedule weekly message every Monday at 18:00 UTC
    scheduler.add_job(send_monday_schedule,
                      CronTrigger(day_of_week="mon", hour=18, minute=0, timezone="UTC"))
    # TODO: Uncomment the row below for immediate testing
    # scheduler.add_job(send_monday_schedule)

    # Schedule the Friday 18:00 UTC Resource Drop
    scheduler.add_job(send_friday_resource,
                      CronTrigger(day_of_week="fri", hour=18, minute=0, timezone="UTC"))
    # TODO: Uncomment the row below for immediate testing
    # scheduler.add_job(send_friday_resource)

    scheduler.start()


async def generate_ai_message(prompt: str):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=800,
    )
    return response.choices[0].message.content


async def send_message(get_message_func, key_type, activity):
    await asyncio.sleep(1)  # Optional buffer

    for cohort_name, values in COHORT_DICT.items():
        # if stop marked as 1 in the table, do nothing
        if int(values[f"stop_{key_type}"]) == 1:
            print(f"[{activity} MESSAGE] Stopped manually by admins for cohort {cohort_name}...")
            continue
        try:
            channel_id = int(values[f"discord_{key_type}"])
            try:
                # Try cache first
                channel = bot.get_channel(channel_id)
                if channel is None:
                    # Fallback to API fetch
                    channel = await bot.fetch_channel(channel_id)
            except Exception as fetch_error:
                print(f"[ERROR] Could not fetch channel for cohort {cohort_name} (ID: {channel_id}): {fetch_error}")
                continue

            if channel:
                message = await get_message_func(str(values[f"info_{key_type}"]),
                                                 str(values[f"link_{key_type}"]),
                                                 cohort_name)
                try:
                    await channel.send(message)
                    print(f"[{activity} MESSAGE] Sent message to channel {channel.name} ({channel_id})")
                except Exception as send_error:
                    print(f"[ERROR] Failed to send message to {channel.name}: {send_error}")
                    await channel.send(f"{activity} loading ... ⌛")
            else:
                print(f"[ERROR] Channel not found for cohort {cohort_name} (ID: {channel_id})")
        except Exception as e:
            print(f"[ERROR] General failure for cohort {cohort_name}: {e}")


def get_week_resource_data(gid: str):
    df = pd.read_csv(f"{RESOURCE_SHEET_URL}&gid={gid}")
    df["day"] = pd.to_datetime(df["day"])

    # Find the row with a date within ±5 days
    today = pd.to_datetime(datetime.today().date())
    mask = (df["day"] - today).abs().dt.days < 5
    row = df[mask]

    if row.empty:
        return None, None

    row = row.iloc[0]
    links = row.get("links")
    comments = row.get("comment")

    if pd.isna(links) and pd.isna(comments):
        return None, None

    return str(links), str(comments)


async def get_friday_resource(gid: str, link, cohort) -> str:
    links, comments = get_week_resource_data(gid)

    if not links and not comments:
        return "Friday Resource Drop loading ... ⌛"

    with open("resource_prompt.txt", 'r', encoding='utf-8') as f:
        prompt_template = f.read()

    prompt = prompt_template.format(
        links=links or "No links provided",
        comments=comments or "No comments available",
        TEMPLATE_MESSAGE=RESOURCE_TEMPLATE,
    )

    return await generate_ai_message(prompt)


async def send_friday_resource():
    params = {
        "get_message_func": get_friday_resource,
        "key_type": "resource",
        "activity": "Friday Resource Drop"
    }

    await send_message(**params)


# ==============================================================================================
# ==============================================================================================

def extract_text_from_rich_text(rich_text_array):
    return ''.join(part.get('plain_text', '') for part in rich_text_array)


def extract_date_range(text):
    match = re.search(r'\((\w+ \d{1,2})\s*-\s*(\w+ \d{1,2})\)', text)
    if not match:
        return None, None

    start_str, end_str = match.groups()
    year = datetime.now().year
    try:
        start_date = datetime.strptime(f"{start_str} {year}", "%B %d %Y")
        end_date = datetime.strptime(f"{end_str} {year}", "%B %d %Y")
    except ValueError:
        return None, None
    return start_date, end_date


def get_all_children(notion_, parent_id):
    children = []
    start_cursor = None

    while True:
        response = notion_.blocks.children.list(block_id=parent_id, start_cursor=start_cursor, page_size=100)
        children.extend(response.get("results", []))

        if not response.get("next_cursor"):
            break
        start_cursor = response["next_cursor"]

    return children


def process_block_text(block):
    block_type = block["type"]
    rich_text = block.get(block_type, {}).get("rich_text", [])
    return block_type, extract_text_from_rich_text(rich_text)


def extract_active_heading_content_as_text(notion_, page_id, reference_date=None):
    reference_date = reference_date or datetime.today()
    top_blocks = notion_.blocks.children.list(page_id)["results"]
    week = 1000
    current_week = 0
    output_lines = []

    for block in top_blocks:
        # looking for Sprint (From - To) headings to find the current sprint
        if block["type"] != "heading_1":
            continue

        heading_text = extract_text_from_rich_text(block["heading_1"]["rich_text"])
        start_date, end_date = extract_date_range(heading_text)

        # Find the current ongoing sprint
        if start_date and end_date and start_date <= reference_date <= end_date:
            output_lines.append(f"# {heading_text} ({start_date.date()} – {end_date.date()})\n")

            children = get_all_children(notion, block["id"])
            for child in children:
                child_type, child_text = process_block_text(child)

                # Find the current ongoing week of the spring
                if child_type == "heading_3":
                    match = re.search(r"Weeks?\s*(\d+)", child_text)
                    if match and week > int(match.group(1)):
                        week = int(match.group(1))
                        # print(week)
                        current_week = int(week + (reference_date - start_date).days / 7)  # double check correctness
                        # print(current_week)
                if child_text.strip():
                    output_lines.append(child_text)

                # Find all Week X-Y dropdowns and their content
                if child_type == "heading_3":
                    nested_children = get_all_children(notion, child["id"])
                    for nested in nested_children:
                        nested_type, nested_text = process_block_text(nested)
                        if nested_text.strip():
                            output_lines.append(nested_text)

    return "\n".join(output_lines), current_week


async def get_monday_schedule(notion_page: str, notion_link: str, cohort_name: str):
    with open("schedule_prompt.txt", 'r', encoding='utf-8') as f:
        prompt_template = f.read()

    sprint_text, week_nr = extract_active_heading_content_as_text(notion, notion_page)

    prompt = prompt_template.format(
        cohort_name=cohort_name,
        notion_link=notion_link,
        week_nr=week_nr,
        sprint_text=sprint_text,
        message_template=SCHEDULE_TEMPLATE,
        two_tracks_template=SCHEDULE_2_TEMPLATE
    )
    return await generate_ai_message(prompt)


async def send_monday_schedule():
    params = {
        "get_message_func": get_monday_schedule,
        "key_type": "schedule",
        "activity": "Weekly Schedule"
    }

    await send_message(**params)


bot.run(DISCORD_BOT_TOKEN)
