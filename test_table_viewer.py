import unittest
from datetime import datetime
from io import BytesIO
from unittest.mock import patch, MagicMock

from table_viewer import (
    repair_text,
    clean_text,
    parse_date,
    shorten,
    split_line,
    detect_and_decode,
    get_input_stream
)

class TestDataProcessor(unittest.TestCase):

    def test_clean_text(self):
        self.assertEqual(clean_text("Иванов   Иван"), "Иванов Иван")
        self.assertEqual(clean_text("Иванов\\nИван"), "Иванов Иван")
        self.assertEqual(clean_text(" Иванов Иван\\r\\n "), "Иванов Иван")
        self.assertEqual(clean_text(""), "")


    def test_repair_text(self):
        broken_text = "РЎРѕРєРѕР»РѕРІ"
        repaired = repair_text(broken_text)
        self.assertEqual(repaired, "Соколов")
        self.assertEqual(repair_text(" Обычный Текст "), " Обычный Текст ")
        self.assertEqual(repair_text(""), "")

    def test_parse_date_normal(self):
        self.assertEqual(parse_date("2022-12-23 05:56:06"), "2022-12-23 05:56:06")
        self.assertEqual(parse_date("2022-12-23T05:56:06"), "2022-12-23 05:56:06")

    def test_parse_date_swapped_month_day(self):
        self.assertEqual(parse_date("2022-23-12 05:56:06"), "2022-12-23 05:56:06")

    def test_parse_date_overflow_shifting(self):
        self.assertEqual(parse_date("2010-02-30 05:56:06"), "2010-03-02 05:56:06")
        self.assertEqual(parse_date("2010-30-02 05:56:06"), "2010-03-02 05:56:06")
        self.assertEqual(parse_date("2012-02-29 12:00:00"), "2012-02-29 12:00:00")
        self.assertEqual(parse_date("2012-02-30 12:00:00"), "2012-03-01 12:00:00")

    def test_parse_date_invalid(self):
        self.assertEqual(parse_date("2022-14-15 05:56:06"), "INVALID_DATE")
        self.assertEqual(parse_date("не дата вовсе"), "INVALID_DATE")

    def test_shorten(self):
        self.assertEqual(shorten("ДлинныйТекст", 15), "ДлинныйТекст")
        self.assertEqual(shorten("ДлинныйТекст", 10), "Длинный...")
        self.assertEqual(shorten("Тест", 2), "..")

    def test_split_line_tab(self):
        line = "Иванов Иван\t30\tМосква\t2022-12-23 05:56:06"
        res = split_line(line)
        self.assertIsNotNone(res)
        self.assertEqual(res, ("Иванов Иван", "30", "Москва", "2022-12-23 05:56:06"))

    def test_split_line_regex_fallback(self):
        line = "Соколов Андрей Николаевич 36 улица Советская, 63, Санкт-Петербург 2022-12-23 05:56:06"
        res = split_line(line)
        self.assertIsNotNone(res)
        self.assertEqual(res[0], "Соколов Андрей Николаевич")
        self.assertEqual(res[1], "36")
        self.assertEqual(res[2], "улица Советская, 63, Санкт-Петербург")
        self.assertEqual(res[3], "2022-12-23 05:56:06")

    def test_split_line_invalid(self):
        self.assertIsNone(split_line("Просто какая-то битая строка"))

    def test_detect_and_decode_utf8(self):
        raw = "Привет, мир!".encode("utf-8")
        self.assertEqual(detect_and_decode(raw).strip(), "Привет, мир!")

    def test_detect_and_decode_cp1251(self):
        raw = "Привет, мир!".encode("cp1251")
        self.assertEqual(detect_and_decode(raw).strip(), "Привет, мир!")

    @patch("urllib.request.urlopen")
    def test_get_input_stream_url(self, mock_urlopen):
        mock_urlopen.return_value = BytesIO(b"test data")
        stream = get_input_stream("http://example.com/data.txt")
        self.assertEqual(stream.read(), b"test data")
        mock_urlopen.assert_called_once_with("http://example.com/data.txt")

    @patch("builtins.open", new_callable=MagicMock)
    def test_get_input_stream_file(self, mock_open):
        get_input_stream("local_file.txt")
        mock_open.assert_called_once_with("local_file.txt", "rb")

if __name__ == "__main__":
    unittest.main()