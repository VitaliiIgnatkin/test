import sqlite3
import pytest
import requests_mock
from my_telegram_bot import translate_text  # Замените на импорт вашей функции для перевода

# Фикстура для создания временной базы данных SQLite в памяти
@pytest.fixture(scope="function")
def sqlite_db():
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS TranslationHistory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            chat_id INTEGER,
            original_text TEXT,
            translated_text TEXT
        )
    """)
    conn.commit()
    
    yield conn
    
    conn.close()

# Тест функции для перевода текста
def test_translate_text():
    text_to_translate = "Hello, world!"
    translation = translate_text(text_to_translate)
    
    assert isinstance(translation, str)
    assert translation != ""

# Тест функции для сохранения перевода в базу данных
def test_save_translation_to_db(sqlite_db):
    user_id = 123
    chat_id = 456
    original_text = "Hello"
    translated_text = "Привет"
    
    cursor = sqlite_db.cursor()
    
    cursor.execute("""
        INSERT INTO TranslationHistory (user_id, chat_id, original_text, translated_text)
        VALUES (?, ?, ?, ?)
    """, (user_id, chat_id, original_text, translated_text))
    sqlite_db.commit()
    
    cursor.execute("SELECT COUNT(*) FROM TranslationHistory")
    count = cursor.fetchone()[0]
    
    assert count == 1

# Тест функции для имитации запроса к внешнему API
def test_request_to_external_api():
    with requests_mock.mock() as m:
        expected_translation = "Привет, мир!"
        m.post("https://api-free.deepl.com/v2/translate", json={"translations": [{"text": expected_translation}]})
        
        text_to_translate = "Hello, world!"
        translation = translate_text(text_to_translate)
        
        assert translation == expected_translation

if __name__ == "__main__":
    pytest.main()
