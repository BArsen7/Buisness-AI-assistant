"""
build.py
Скрипт для сборки приложения в один исполняемый файл через PyInstaller.

Использование:
    python build.py
    
Для Windows:
    python build.py --windowed
    
Для Linux:
    python build.py
"""

import sys
import os
import subprocess
from pathlib import Path

def get_additional_files():
    """
    Возвращает список дополнительных файлов и папок для включения в сборку.
    """
    # Получаем корневую директорию проекта
    base_dir = Path(__file__).parent.absolute()
    
    additional_files = []
    
    # Добавляем .env файл если существует
    env_file = base_dir / ".env"
    if env_file.exists():
        additional_files.append((str(env_file), "."))
    
    # Добавляем пустую структуру data для ChromaDB и SQLite
    # При запуске приложение создаст эти папки в пользовательской директории
    # Но мы добавляем заглушки для надежности
    data_dir = base_dir / "data"
    if data_dir.exists():
        additional_files.append((str(data_dir), "data"))
    
    return additional_files


def get_hidden_imports():
    """
    Возвращает список скрытых импортов для PyInstaller.
    """
    return [
        # PyQt6
        "PyQt6",
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "PyQt6.QtWidgets",
        
        # ChromaDB
        "chromadb",
        "chromadb.config",
        "chromadb.db.system",
        
        # SQLAlchemy (используется внутри chromadb)
        "sqlalchemy",
        "sqlalchemy.dialects.sqlite",
        
        # HTTP клиент
        "httpx",
        "httpcore",
        
        # DuckDuckGo search (если используется)
        "duckduckgo_search",
        
        # Python-dotenv
        "dotenv",
        
        # Pydantic
        "pydantic",
        "pydantic.fields",
        
        # Другие зависимости
        "posthog",  # Может использоваться chromadb
        "overrides",
        "bcrypt",
        "pypika",
    ]


def build_executable(windowed: bool = False):
    """
    Собирает исполняемый файл приложения.
    
    Args:
        windowed: Если True, скрывает консольное окно (для Windows GUI приложений).
    """
    base_dir = Path(__file__).parent.absolute()
    main_script = base_dir / "main.py"
    
    if not main_script.exists():
        print(f"Ошибка: main.py не найден в {base_dir}")
        sys.exit(1)
    
    # Формируем команду PyInstaller
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "OpenExecutive",
        "--onefile",
        "--clean",
        "--noconfirm",
    ]
    
    # Добавляем флаг --windowed для Windows (скрывает консоль)
    if windowed and sys.platform == "win32":
        cmd.append("--windowed")
    
    # Добавляем скрытые импорты
    for imp in get_hidden_imports():
        cmd.extend(["--hidden-import", imp])
    
    # Добавляем дополнительные файлы
    for src, dst in get_additional_files():
        cmd.extend(["--add-data", f"{src}{os.pathsep}{dst}"])
    
    # Добавляем главный скрипт
    cmd.append(str(main_script))
    
    print("Команда сборки:")
    print(" ".join(cmd))
    print("\nНачало сборки...")
    
    try:
        subprocess.run(cmd, check=True)
        print("\n✅ Сборка завершена успешно!")
        
        # Определяем путь к собранному файлу
        if sys.platform == "win32":
            dist_dir = base_dir / "dist"
            exe_file = dist_dir / "OpenExecutive.exe"
        else:
            dist_dir = base_dir / "dist"
            exe_file = dist_dir / "OpenExecutive"
        
        if exe_file.exists():
            print(f"\n📦 Исполняемый файл: {exe_file}")
            print(f"   Размер: {exe_file.stat().st_size / (1024*1024):.2f} MB")
        else:
            print("\n⚠️ Файл не найден в ожидаемом месте")
            
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Ошибка сборки: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("\n❌ PyInstaller не найден. Установите: pip install pyinstaller")
        sys.exit(1)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Сборка OpenExecutive в один файл")
    parser.add_argument(
        "--windowed",
        action="store_true",
        help="Скрыть консольное окно (только для Windows)"
    )
    
    args = parser.parse_args()
    
    build_executable(windowed=args.windowed)
