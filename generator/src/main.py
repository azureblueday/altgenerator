import sys, os
from time import gmtime, strftime, sleep
from generate_counter import generate_counter
from generate import Generate
from threading import Thread
from util import Util

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

config = Util.get_config()

THREAD_AMOUNT = config["threads"]


def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def set_title(text: str) -> None:
    """Set the terminal title cross-platform."""
    if os.name == "nt":
        try:
            import ctypes
            ctypes.windll.kernel32.SetConsoleTitleW(text)
            return
        except Exception:
            pass
    # macOS / Linux terminals: xterm title escape sequence
    sys.stdout.write(f"\33]0;{text}\a")
    sys.stdout.flush()


def cpm_checker() -> None:
    elapsed = 0
    cpm_time = 0

    while True:
        generated = generate_counter.get_generated()
        cpm = round((60 / cpm_time) * generated) if cpm_time != 0 else 0

        set_title(f"FunBypass | Generated: {generated} | CPM: {cpm} | T: {strftime('%H:%M:%S', gmtime(elapsed))}")

        if generated != 0:
            cpm_time += 1

        elapsed += 1
        sleep(1)


def main() -> None:
    threads = []

    for _ in range(THREAD_AMOUNT):
        t = Thread(target=Generate.gen, args=(generate_counter,), daemon=True)
        threads.append(t)
        t.start()

    Thread(target=cpm_checker, daemon=True).start()

    # Keep the main thread alive
    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        print("\nStopping...")


if __name__ == "__main__":
    clear_screen()
    main()
