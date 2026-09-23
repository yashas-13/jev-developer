"""Full-screen TUI: sidebar files + main chat/log + status bar + input.

Keys: Tab switch pane · Enter send · /run goal · /read · /search · /test · /quit.
Runs without prompt_toolkit/textual — stdlib curses only so Termux works offline.
Falls back to rich REPL when curses is unavailable.
"""
from __future__ import annotations

from pathlib import Path

from .agent import collect_files
from .chat import ChatSession


def run_tui(root: Path) -> None:
    try:
        import curses
    except ImportError:
        ChatSession(root).repl()
        return
    try:
        curses.wrapper(_main, root)
    except Exception as e:
        print(f"TUI unavailable ({e}); falling back to chat REPL")
        ChatSession(root).repl()


def _main(stdscr, root: Path) -> None:
    import curses

    sess = ChatSession(root)
    curses.curs_set(1)
    stdscr.nodelay(False)
    files = collect_files(root)
    log: list[str] = ["Welcome to JEV-Developer TUI.", "Type /help, /run <goal>, /read <f>, /search <pat>, /quit"]
    active = "main"  # or 'side'
    sel = 0
    buf = ""
    status = "offline · guarded"

    while True:
        h, w = stdscr.getmaxyx()
        side_w = min(32, w // 3)
        stdscr.clear()
        # sidebar
        stdscr.addstr(0, 0, " FILES (Tab) ".ljust(side_w)[:side_w], curses.A_REVERSE)
        for i, f in enumerate(files[: h - 3]):
            attr = curses.A_REVERSE if (active == "side" and i == sel) else curses.A_NORMAL
            stdscr.addstr(i + 1, 0, f" {f[:side_w-2]}".ljust(side_w)[:side_w], attr)
        # main log
        stdscr.addstr(0, side_w + 1, f" JEV-Developer — {root} ".ljust(w - side_w - 1)[: w - side_w - 1], curses.A_REVERSE)
        visible = log[-(h - 4):]
        for i, line in enumerate(visible):
            stdscr.addstr(i + 1, side_w + 1, line[: w - side_w - 2])
        # status bar + input
        stdscr.addstr(h - 2, 0, f" [{status}] ".ljust(w)[:w], curses.A_REVERSE)
        prompt = f"jev> {buf}"
        stdscr.addstr(h - 1, 0, prompt[: w - 1])
        stdscr.refresh()

        ch = stdscr.getch()
        if ch == 9:  # Tab
            active = "side" if active == "main" else "main"
        elif ch in (curses.KEY_UP,):
            sel = max(0, sel - 1)
        elif ch in (curses.KEY_DOWN,):
            sel = min(max(0, len(files) - 1), sel + 1)
        elif ch in (curses.KEY_BACKSPACE, 127, 8):
            buf = buf[:-1]
        elif ch in (10, 13, curses.KEY_ENTER):  # Enter
            line = buf.strip()
            buf = ""
            if active == "side" and not line and files:
                line = f"/read {files[sel]}"
            if not line:
                continue
            out = sess.handle(line)
            log.append(f"> {line}")
            if out == "quit":
                break
            for chunk in str(out).splitlines() or [""]:
                # wrap long lines
                while len(chunk) > w - side_w - 3:
                    log.append(chunk[: w - side_w - 3])
                    chunk = chunk[w - side_w - 3:]
                log.append(chunk)
            status = f"turns={len(sess.history)} files={len(files)}"
            files = collect_files(root)
        elif 32 <= ch <= 126:
            buf += chr(ch)
