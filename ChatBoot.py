# ============================================================
# StudyBuddy Bot - Exam & Study Helper (Rule-Based AI Chatbot)
# ============================================================
# Features:
#   - Study tips by subject
#   - Exam countdown (tells you how many days left)
#   - To-do / study task list (saved to a file, persists between runs)
#   - Flashcard quiz mode (simple Q&A self-test)
#   - Motivational quotes
#   - Remembers your name during the session
# ============================================================

import re
import json
import random
import os
from datetime import date, datetime

DATA_FILE = "study_tasks.json"


class C:
    BOT = '\033[96m'   # Cyan
    USER = '\033[92m'  # Green
    SYS = '\033[93m'   # Yellow
    RESET = '\033[0m'


# ── Knowledge base ───────────────────────────────
STUDY_TIPS = {
    "math": "📐 Math tip: Practice problems daily instead of just reading formulas. Redo mistakes by hand.",
    "physics": "⚛️ Physics tip: Understand the concept behind a formula before memorizing it.",
    "chemistry": "🧪 Chemistry tip: Make a small chart of reactions/equations and revise it every day.",
    "english": "📖 English tip: Read one page out loud daily — it improves both vocab and speaking.",
    "computer": "💻 CS tip: Type out code yourself instead of copy-pasting. Debugging teaches more than tutorials.",
    "general": "🎯 General tip: Study in 25-minute focused blocks (Pomodoro) with 5-minute breaks."
}

QUOTES = [
    "\"Success is the sum of small efforts repeated day in and day out.\" – Keep going! 💪",
    "\"It always seems impossible until it's done.\" – You've got this! 🚀",
    "\"Don't watch the clock; do what it does. Keep going.\" ⏰",
]

GREETINGS = ["hello", "hi", "hey", "salam"]
BYE_WORDS = ["bye", "exit", "quit", "q", "goodbye"]


class StudyBuddy:
    def __init__(self, data_file=DATA_FILE):
        self.name = None
        self.data_file = data_file
        self.tasks = self._load_tasks()
        self.quiz_bank = []          # flashcards added during session
        self.quiz_score = {"correct": 0, "total": 0}

    # ---------- persistence ----------
    def _load_tasks(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                return []
        return []

    def _save_tasks(self):
        try:
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(self.tasks, f, indent=2, ensure_ascii=False)
        except OSError as e:
            print(f"{C.SYS}(Could not save tasks: {e}){C.RESET}")

    # ---------- helpers ----------
    def clean(self, text):
        return re.sub(r'[^\w\s/|:.-]', '', text.lower().strip())

    def detect_name(self, text):
        match = re.search(r'\bmy name is (\w+)\b', text)
        if match:
            self.name = match.group(1).capitalize()
            return f"Nice to meet you, {self.name}! Ready to study? 📚"
        return None

    # ---------- feature: exam countdown ----------
    def exam_countdown(self, text):
        # expects format: exam on YYYY-MM-DD  (e.g., "exam on 2026-08-15")
        match = re.search(r'exam on (\d{4}-\d{2}-\d{2})', text)
        if match:
            try:
                exam_date = datetime.strptime(match.group(1), "%Y-%m-%d").date()
                days_left = (exam_date - date.today()).days
                if days_left > 0:
                    return f"📅 Your exam is in {days_left} day(s). Let's make a plan!"
                elif days_left == 0:
                    return "📅 Your exam is TODAY! Stay calm, you've prepared for this. 💪"
                else:
                    return "📅 That date has already passed!"
            except ValueError:
                return "Hmm, please use format: exam on YYYY-MM-DD"
        return None

    # ---------- feature: task list ----------
    def handle_tasks(self, text):
        add_match = re.search(r'add task (.+)', text)
        if add_match:
            task = add_match.group(1).strip()
            self.tasks.append({"task": task, "done": False})
            self._save_tasks()
            return f"✅ Added to your study list: '{task}'"

        if "show tasks" in text or "my tasks" in text or "list tasks" in text:
            if not self.tasks:
                return "🗒️ Your study list is empty. Try: 'add task revise chapter 3'"
            lines = []
            for i, t in enumerate(self.tasks, 1):
                status = "✔️" if t["done"] else "⬜"
                lines.append(f"{status} {i}. {t['task']}")
            return "🗒️ Your study tasks:\n" + "\n".join(lines)

        done_match = re.search(r'done (\d+)', text)
        if done_match:
            idx = int(done_match.group(1)) - 1
            if 0 <= idx < len(self.tasks):
                self.tasks[idx]["done"] = True
                self._save_tasks()
                return f"🎉 Marked task {idx + 1} as done!"
            return "That task number doesn't exist."

        return None

    # ---------- feature: flashcard quiz ----------
    def handle_quiz(self, text, raw_text):
        add_match = re.search(r'add flashcard (.+)\|(.+)', raw_text, re.IGNORECASE)
        if add_match:
            q, a = add_match.group(1).strip(), add_match.group(2).strip()
            self.quiz_bank.append({"q": q, "a": a})
            return f"🃏 Flashcard added: '{q}'"

        if "quiz me" in text or "start quiz" in text:
            if not self.quiz_bank:
                return "You don't have flashcards yet. Add one like:\nadd flashcard What is gravity? | A force that attracts objects"
            card = random.choice(self.quiz_bank)
            self._active_card = card
            return f"🃏 Q: {card['q']}\n(Type 'answer: your answer' to check)"

        answer_match = re.search(r'answer:\s*(.+)', raw_text, re.IGNORECASE)
        if answer_match and hasattr(self, "_active_card"):
            given = answer_match.group(1).strip().lower()
            correct = self._active_card["a"].strip().lower()
            self.quiz_score["total"] += 1
            if given == correct:
                self.quiz_score["correct"] += 1
                return "✅ Correct! Great job."
            else:
                return f"❌ Not quite. Correct answer: {self._active_card['a']}"

        return None

    # ---------- main response logic ----------
    def get_response(self, raw_input):
        text = self.clean(raw_input)

        if not text:
            return "Please type something! 😊"

        if text in BYE_WORDS:
            return None  # signal to quit

        name_reply = self.detect_name(text)
        if name_reply:
            return name_reply

        for reply_fn in (self.exam_countdown, lambda t: self.handle_tasks(t),
                          lambda t: self.handle_quiz(t, raw_input)):
            result = reply_fn(text)
            if result:
                return result

        if text in GREETINGS:
            return "Hello! I'm StudyBuddy 📚 Ask me for study tips, add tasks, or say 'quiz me'!"

        if "quote" in text or "motivate" in text:
            return random.choice(QUOTES)

        if "tip" in text or "study tips" in text:
            for subject, tip in STUDY_TIPS.items():
                if subject in text:
                    return tip
            return STUDY_TIPS["general"]

        if "help" in text:
            return ("Try:\n"
                    "- 'tip for math' / 'physics tip'\n"
                    "- 'add task revise chapter 3'\n"
                    "- 'show tasks' / 'done 1'\n"
                    "- 'exam on 2026-08-15'\n"
                    "- 'add flashcard Q | A' then 'quiz me'\n"
                    "- 'quote' for motivation")

        return "🤔 I'm not sure about that. Type 'help' to see what I can do."


def main():
    bot = StudyBuddy()
    print(f"{C.SYS}{'='*55}{C.RESET}")
    print(f"{C.SYS} 📚 StudyBuddy — Your Exam & Study Helper Bot{C.RESET}")
    print(f"{C.SYS} Type 'help' to see commands, 'quit' to exit{C.RESET}")
    print(f"{C.SYS}{'='*55}{C.RESET}")

    while True:
        try:
            user_input = input(f"\n{C.USER}You: {C.RESET}")
            response = bot.get_response(user_input)

            if response is None:
                print(f"{C.BOT}StudyBuddy: Good luck with your studies! Bye! 👋{C.RESET}")
                if bot.quiz_score["total"] > 0:
                    print(f"{C.SYS}Quiz score this session: "
                          f"{bot.quiz_score['correct']}/{bot.quiz_score['total']}{C.RESET}")
                break

            print(f"{C.BOT}StudyBuddy: {response}{C.RESET}")

        except KeyboardInterrupt:
            print(f"\n{C.BOT}StudyBuddy: Session ended. Bye! 👋{C.RESET}")
            break


if __name__ == "__main__":
    main()