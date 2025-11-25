import re
import asyncio
import time
import json
import os
import logging
from collections import deque
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import RetryAfter, TimedOut, Forbidden, BadRequest

# ================= BOT TOKEN =================
BOT_TOKEN = '8279532303:AAE7YuydI5MRB68P7aRnI74d6RFlom2sJas'
# =============================================

# --------- CLEAN LOGGING (NO CONSOLE NOISE) ----------
logging.basicConfig(
    level=logging.ERROR,
    format="%(message)s"
)
logger = logging.getLogger(__name__)
# -----------------------------------------------------

DELAY_BETWEEN_POLLS = 3
POLLS_PER_BATCH = 20
BREAK_BETWEEN_BATCHES = 5
RETRY_ATTEMPTS = 3
DATA_FILE = "sot_bot_user_data.json"


class PollBot:
    def __init__(self, token):
        self.token = token
        self.app = Application.builder().token(token).build()

        self.poll_queue = deque()
        self.is_processing = False
        self.current_user_id = None
        self.last_poll_time = 0

        self.user_channels = {}
        self.user_format = {}

        self._load_data()
        self.setup_handlers()

    # ---------------------- Load & Save ----------------------
    def _load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.user_channels = {int(k): v for k, v in data.get("user_channels", {}).items()}
                self.user_format = {int(k): v for k, v in data.get("user_format", {}).items()}
            except:
                pass

    def _save_data(self):
        try:
            data = {
                "user_channels": {str(k): v for k, v in self.user_channels.items()},
                "user_format": {str(k): v for k, v in self.user_format.items()}
            }
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except:
            pass

    # ---------------------- Helpers ----------------------
    def normalize_chat_id(self, raw):
        try:
            return int(str(raw).strip())
        except:
            return raw

    # ---------------------- Parsing (supports both formats) ----------------------
    def parse_mcq_text(self, text):
        """
        Supports:
         - Old format: Question 1: ... A. ... B. ... Correct Answer: A Explanation: ...
         - New format: Question. ... A) ... B) ... Ans: A Explanation ...
         - Mixed/variants: A. or A) or 'A )' etc. 'Correct Answer', 'Ans', 'Answer' accepted.
        Returns list of polls: {question, options(list of 4), correct_answer(int 0-3), explanation}
        """

        polls = []

        # Normalize some characters & unify line endings
        t = text.replace('\r\n', '\n').replace('\r', '\n')

        # Split into blocks by headers like:
        # "Question 1:" or "Question:" or "Question." (case-insensitive)
        blocks = re.split(r'(?i)Question\s*\d*\s*[:.]', t)
        # If split produced an empty leading block (text before first Question), ignore it
        for block in blocks:
            if not block or not block.strip():
                continue

            q_text = block.strip()

            try:
                # 1) Extract question text: everything up to the first option (A. or A) or A ))
                q_match = re.search(r'^(.*?)(?=\n\s*A[\.\)]|\n\s*A\s*\))', q_text, re.DOTALL | re.IGNORECASE)
                if q_match:
                    question = q_match.group(1).strip()
                else:
                    # If not found, maybe format is "Question.\nA) ..." and question is missing
                    # Try to take the part before "A" line or first blank line
                    lines = q_text.splitlines()
                    if lines and not re.match(r'^\s*A[\.\)]', lines[0], re.IGNORECASE):
                        question = lines[0].strip()
                    else:
                        question = ""  # fallback

                # 2) Extract options A-D with flexible separators (., ), or ) with spaces)
                option_a = re.search(r'A[\.\)]\s*(.*?)(?=\n\s*B[\.\)]|\n\s*C[\.\)]|\n\s*D[\.\)]|$)', q_text, re.DOTALL | re.IGNORECASE)
                option_b = re.search(r'B[\.\)]\s*(.*?)(?=\n\s*C[\.\)]|\n\s*D[\.\)]|$)', q_text, re.DOTALL | re.IGNORECASE)
                option_c = re.search(r'C[\.\)]\s*(.*?)(?=\n\s*D[\.\)]|$)', q_text, re.DOTALL | re.IGNORECASE)
                option_d = re.search(r'D[\.\)]\s*(.*?)(?=\n|$)', q_text, re.DOTALL | re.IGNORECASE)

                if not all([option_a, option_b, option_c, option_d]):
                    # If options are on same line or different structure, try stricter pattern:
                    # Look for lines that start with 'A' optionally followed by '.' or ')'
                    lines = q_text.splitlines()
                    opts = {}
                    for line in lines:
                        m = re.match(r'^\s*([A-D])\s*[\.\)]\s*(.*)', line, re.IGNORECASE)
                        if m:
                            opts[m.group(1).upper()] = m.group(2).strip()
                    if all(k in opts for k in ['A', 'B', 'C', 'D']):
                        option_a_text = opts['A']
                        option_b_text = opts['B']
                        option_c_text = opts['C']
                        option_d_text = opts['D']
                    else:
                        # Can't parse options -> skip this block
                        continue
                else:
                    option_a_text = option_a.group(1).strip()
                    option_b_text = option_b.group(1).strip()
                    option_c_text = option_c.group(1).strip()
                    option_d_text = option_d.group(1).strip()

                # 3) Correct answer: accept "Correct Answer:", "Correct answer:", "Ans:", "Answer:", etc.
                corr = re.search(r'(?i)(?:Correct\s*Answer|Correct\s*answer|Answer|Ans)\s*[:.]?\s*([A-D])', q_text)
                if not corr:
                    # try one-line variant: "Ans.\nA" or "Ans\nA"
                    corr = re.search(r'(?i)Ans\s*[:.]?\s*\n?\s*([A-D])', q_text)
                if not corr:
                    # If still not found, skip this block (we require correct answer)
                    continue

                correct_letter = corr.group(1).upper()
                correct_index = ord(correct_letter) - ord('A')
                if correct_index < 0 or correct_index > 3:
                    continue

                # 4) Explanation: optional, everything after 'Explanation' keyword
                expl = ""
                expl_match = re.search(r'(?i)Explanation\s*[:.]?\s*(.*)', q_text, re.DOTALL)
                if expl_match:
                    expl = expl_match.group(1).strip()

                polls.append({
                    "question": question if question else "(No question text)",
                    "options": [
                        option_a_text,
                        option_b_text,
                        option_c_text,
                        option_d_text
                    ],
                    "correct_answer": correct_index,
                    "explanation": expl
                })

            except Exception as e:
                # skip problematic block but continue parsing others
                logger.error(f"parse error: {e}")
                continue

        return polls

    # ---------------------- Formatting ----------------------
    def format_question(self, q, uid):
        prefix = self.user_format.get(uid, {}).get("prefix", "")
        return f"{prefix}\n\n{q}" if prefix else q

    def format_explanation(self, e, uid):
        suffix = self.user_format.get(uid, {}).get("suffix", "")
        if e:
            return f"{e}\n\n{suffix}" if suffix else e
        return suffix if suffix else ""

    # ---------------------- Poll Sending ----------------------
    async def send_single_poll(self, ctx, poll, idx, total, chat, uid):

        for _ in range(RETRY_ATTEMPTS):
            try:
                d = time.time() - self.last_poll_time
                if d < DELAY_BETWEEN_POLLS:
                    await asyncio.sleep(DELAY_BETWEEN_POLLS - d)

                q = self.format_question(poll["question"], uid)
                ex = self.format_explanation(poll["explanation"], uid)

                await ctx.bot.send_poll(
                    chat_id=chat,
                    question=q,
                    options=poll["options"],
                    type="quiz",
                    correct_option_id=poll["correct_answer"],
                    explanation=ex,
                    is_anonymous=True
                )

                self.last_poll_time = time.time()
                return True

            except RetryAfter as e:
                await asyncio.sleep(e.retry_after + 1)
            except Exception as e:
                logger.error(f"send_single_poll error: {e}")
                return False

        return False

    # ---------------------- Queue Processor ----------------------
    async def process_queue(self, ctx, uid):

        if self.is_processing:
            return

        self.is_processing = True
        self.current_user_id = uid

        my_polls = []
        others = deque()

        # Collect polls belonging to this user; keep others in queue
        while self.poll_queue:
            item = self.poll_queue.popleft()
            if item["owner_user_id"] == uid:
                my_polls.append(item["poll_data"])
            else:
                others.append(item)

        self.poll_queue = others

        if not my_polls:
            await ctx.bot.send_message(uid, "❌ আপনার কিউতে কোনো পোল নেই।")
            self.is_processing = False
            self.current_user_id = None
            return

        target = self.user_channels.get(uid)
        if not target:
            await ctx.bot.send_message(uid, "❌ কোনো চ্যানেল সেট করা নেই। /setchannel ব্যবহার করুন।")
            self.is_processing = False
            self.current_user_id = None
            return

        total = len(my_polls)
        sent = 0

        # Inform start of sending
        await ctx.bot.send_message(uid, "Starting to send...")

        # Calculate total batches for message/estimate
        batches = (total - 1) // POLLS_PER_BATCH + 1
        # Estimate: time for poll delays + breaks between batches
        est_seconds = total * DELAY_BETWEEN_POLLS + max(0, batches - 1) * BREAK_BETWEEN_BATCHES
        est_min = est_seconds // 60
        est_sec = est_seconds % 60

        # Send in batches
        while my_polls:
            batch = my_polls[:POLLS_PER_BATCH]
            my_polls = my_polls[POLLS_PER_BATCH:]

            for poll in batch:
                if await self.send_single_poll(ctx, poll, sent + 1, total, target, uid):
                    sent += 1

            if my_polls:
                # pause message between batches
                await ctx.bot.send_message(uid, f"⏸ {BREAK_BETWEEN_BATCHES}s বিরতি...")
                await asyncio.sleep(BREAK_BETWEEN_BATCHES)

        # Final message (English as requested)
        await ctx.bot.send_message(
            uid,
            f"✅ All done! Successfully sent {sent}/{total} polls to the channel."
        )

        self.is_processing = False
        self.current_user_id = None

    # ---------------------- Commands ----------------------
    async def start(self, u: Update, c: ContextTypes.DEFAULT_TYPE):
        welcome = """
🤖 ALIF Poll Bot

প্রথমে টার্গেট চ্যানেল সেট করুন:
 /setchannel <channel_id_or_username>

উদাহরণ:
 /setchannel -1001234567890
 /setchannel @mychannel

(চ্যানেলে বটকে অ্যাড করে এবং পোস্ট করার অনুমতি দিন)

এখানে ফরম্যাট সেট করুন (ঐচ্ছিক):
 /setformat <prefix> || <suffix>

উদাহরণ:
 /setformat [SOT] || [@SOT_Academy]

তারপর MCQ টেক্সট পাঠান — বট নিম্নোক্ত দুই ফরম্যাটই পার্স করবে:

ফরম্যাট-১ -
Question 1:
প্রশ্ন
A. ...
B. ...
C. ...
D. ...
Correct Answer: A
Explanation: ...

ফরম্যাট-২ -
Question.
প্রশ্ন
A)
B)
C)
D)

Ans: A
Explanation: ...
"""
        await u.message.reply_text(welcome)

    async def setchannel(self, u: Update, c: ContextTypes.DEFAULT_TYPE):
        uid = u.effective_user.id
        if not c.args:
            await u.message.reply_text("ব্যবহার: /setchannel <channel_id_or_username>")
            return
        raw = c.args[0]
        self.user_channels[uid] = self.normalize_chat_id(raw)
        self._save_data()
        await u.message.reply_text(f"✅ Channel set: {raw}")

    async def setformat(self, u: Update, c: ContextTypes.DEFAULT_TYPE):
        uid = u.effective_user.id
        text = " ".join(c.args).strip()

        if "||" not in text:
            await u.message.reply_text("ব্যবহার: /setformat <prefix> || <suffix>")
            return

        prefix, suffix = text.split("||", 1)
        self.user_format[uid] = {"prefix": prefix.strip(), "suffix": suffix.strip()}
        self._save_data()

        await u.message.reply_text("✅ Format saved!")

    async def handle_text(self, u: Update, c: ContextTypes.DEFAULT_TYPE):
        uid = u.effective_user.id
        text = u.message.text

        # quick sanity check for required keywords (either style)
        if not re.search(r'(?i)Question', text) or not re.search(r'(?i)(Correct\s*Answer|Ans|Answer)', text):
            await u.message.reply_text("❌ MCQ ফরম্যাট সঠিক নয় — 'Question' ও 'Ans/Correct Answer' থাকার কথা।")
            return

        polls = self.parse_mcq_text(text)
        if not polls:
            await u.message.reply_text("❌ পোল তৈরি হয়নি (পার্সিং ব্যর্থ)। অনুগ্রহ করে ফরম্যাট পরীক্ষা করুন।")
            return

        # Append polls to queue
        for p in polls:
            self.poll_queue.append({"owner_user_id": uid, "poll_data": p})

        # Progress message(s)
        total = len(polls)
        batches = (total - 1) // POLLS_PER_BATCH + 1
        est_seconds = total * DELAY_BETWEEN_POLLS + max(0, batches - 1) * BREAK_BETWEEN_BATCHES
        est_min = est_seconds // 60
        est_sec = est_seconds % 60

        await u.message.reply_text(
            f"📊 Processing your polls...\n"
            f"✓ Found {total} polls.\n\n"
            f"Added to queue! 📦\n"
            f"Will be sent in {batches} batch(es) of up to {POLLS_PER_BATCH} polls each\n"
            f"⏱ Estimated time: ~{est_min} min {est_sec} sec\n"
            f"Starting to send..."
        )

        # start processing (non-blocking because process_queue awaits but called here)
        await self.process_queue(c, uid)

    # ---------------------- Setup ----------------------
    def setup_handlers(self):
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("setchannel", self.setchannel))
        self.app.add_handler(CommandHandler("setformat", self.setformat))

        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))

    # ---------------------- Run ----------------------
    def run(self):
        print("Bot is running...")
        self.app.run_polling()


def main():
    PollBot(BOT_TOKEN).run()


if __name__ == "__main__":
    main()
