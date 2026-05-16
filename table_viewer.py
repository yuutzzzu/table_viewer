import argparse
import os
import re
import shutil
import sys
import urllib.request
from datetime import datetime, timedelta

DATE_FORMATS = [
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
    "%Y%m%d %H:%M:%S",
    "%Y%m%d %H%M%S",
    "%Y%m%dT%H%M%S",
]

def repair_text(text):
    if not text:
        return text

    if "Р" in text or "С" in text:
        try:
            b_list = []
            for ch in text:
                try:
                    b_list.extend(ch.encode("cp1251"))
                except:
                    if ord(ch) < 256:
                        b_list.append(ord(ch))
            
            repaired = bytes(b_list).decode("utf-8", errors="ignore")
            if repaired:
                text = repaired
        except:
            pass

    return text


def clean_text(text):
    text = text.replace("\\n", " ")
    text = text.replace("\\r", " ")
    text = text.replace("\n", " ")
    text = text.replace("\r", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_date(date_str):
    date_str = clean_text(date_str)

    match_dash = re.match(r"^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2}):(\d{2})$", date_str)
    match_comp1 = re.match(r"^(\d{4})(\d{2})(\d{2})\s+(\d{2}):(\d{2}):(\d{2})$", date_str)
    match_comp2 = re.match(r"^(\d{4})(\d{2})(\d{2})[T ](\d{2})(\d{2})(\d{2})$", date_str)

    match = match_dash or match_comp1 or match_comp2

    if match:
        try:
            y, m, d, h, mi, s = map(int, match.groups())

            if m > 12:
                m, d = d, m

            if m == 0 or d == 0:
                return "INVALID_DATE"

            if 1 <= m <= 12:
                base_date = datetime(y, m, 1, h, mi, s)
                final_date = base_date + timedelta(days=d - 1)
                return final_date.strftime("%Y-%m-%d %H:%M:%S")
        except:
            pass

    for fmt in DATE_FORMATS:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            continue

    return "INVALID_DATE"


def shorten(text, width):
    if len(text) <= width:
        return text

    if width <= 3:
        return "." * width

    return text[:width - 3] + "..."


def split_line(line):
    line = clean_text(line)

    parts = line.split("\t")

    if len(parts) >= 4:
        fio = parts[0].strip()
        age = parts[1].strip()
        address = parts[2].strip()
        date = parts[3].strip()

        return fio, age, address, date

    pattern = (
        r"^(.*?)\s+"
        r"(\d{1,3})\s+"
        r"(.*?)\s+"
        r"(\d{4}[-\dT: ]+)$"
    )

    match = re.match(pattern, line)

    if match:
        return match.groups()

    return None


def get_input_stream(path):
    if path.startswith("http://") or path.startswith("https://"):
        return urllib.request.urlopen(path)

    return open(path, "rb")


def detect_and_decode(raw_line):
    encodings = [
        "utf-8",
        "cp1251"
    ]

    best = None
    best_score = -999999

    for enc in encodings:
        try:
            text = raw_line.decode(enc)
            repaired = repair_text(text)

            cyr = sum(
                1 for ch in repaired
                if ("А" <= ch <= "я") or ch in "Ёё"
            )

            garbage = (
                repaired.count("Р")
                + repaired.count("С")
                + repaired.count("Ð")
                + repaired.count("Ñ")
            )

            score = cyr - garbage * 5

            if score > best_score:
                best_score = score
                best = repaired

        except:
            continue

    if best is None:
        best = raw_line.decode("utf-8", errors="replace")

    return best


def print_separator(widths):
    line = "|"
    for width in widths:
        line += "-" * (width + 2) + "|"
    print(line)


def print_row(values, widths):
    row = "|"
    for value, width in zip(values, widths):
        value = shorten(value, width)
        row += " " + value.ljust(width) + " |"
    print(row)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="Path or URL to input file"
    )
    args = parser.parse_args()

    console_width = shutil.get_terminal_size((120, 20)).columns

    headers = [
        "ФИО",
        "Возраст",
        "Адрес",
        "Дата"
    ]

    # ИСПРАВЛЕНИЕ: уменьшили минимальные пороги, чтобы таблица влезала в узкий экран
    min_widths = [10, 5, 12, 10]
    total_borders = 13
    free_space = console_width - total_borders
    ratios = [0.30, 0.10, 0.40, 0.20]

    widths = [
        max(min_widths[i], int(free_space * ratios[i]))
        for i in range(4)
    ]

    # Дополнительная страховка: если экран СЛИШКОМ узкий, пропорционально сожмем колонки,
    # чтобы их сумма + рамки гарантированно не превышали ширину консоли.
    while sum(widths) + total_borders > console_width:
        for i in range(4):
            if widths[i] > min_widths[i]:
                widths[i] -= 1
            if sum(widths) + total_borders <= console_width:
                break

    title = "СПИСОК ЛЮДЕЙ"

    print()
    print(title.center(console_width))
    print()

    print_separator(widths)
    print_row(headers, widths)
    print_separator(widths)

    try:
        with get_input_stream(args.input) as file:
            for raw_line in file:
                decoded = detect_and_decode(raw_line)

                sub_lines = decoded.replace("\\r\\n", "\n").replace("\\n", "\n").replace("\\r", "\n").split("\n")

                for sub_line in sub_lines:
                    if not sub_line.strip():
                        continue

                    parsed = split_line(sub_line)
                    if not parsed:
                        continue

                    fio, age, address, date = parsed

                    fio = clean_text(fio)
                    age = clean_text(age)
                    address = clean_text(address)
                    normalized_date = parse_date(date)

                    row = [
                        fio,
                        age if age else "-",
                        address,
                        normalized_date
                    ]

                    print_row(row, widths)

    except FileNotFoundError:
        print("Файл не найден")
        sys.exit(1)
    except Exception as e:
        print(f"Ошибка: {e}")
        sys.exit(1)

    print_separator(widths)


if __name__ == "__main__":
    main()