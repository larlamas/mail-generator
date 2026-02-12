#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║                   📧 Mail.tm Email Generator                     ║
║              Создание временных email-ящиков через API           ║
║                     https://mail.tm                              ║
╚══════════════════════════════════════════════════════════════════╝

Возможности:
  • Создание email-аккаунтов (случайное имя или своё)
  • Массовая генерация аккаунтов
  • Проверка входящих писем
  • Чтение содержимого писем
  • Удаление писем и аккаунтов
  • Экспорт аккаунтов в файл

Powered by Mail.tm API — https://docs.mail.tm
"""

import requests
import json
import string
import random
import time
import os
import sys
from datetime import datetime

# ─────────────────────────── Конфигурация ───────────────────────────
API_BASE = "https://api.mail.tm"
ACCOUNTS_FILE = "generated_accounts.json"
HEADERS = {"Content-Type": "application/json"}

# ─────────────────────────── Цвета терминала ───────────────────────────
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"

C = Colors()

# ─────────────────────────── Утилиты ───────────────────────────

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def print_banner():
    banner = f"""
{C.CYAN}{C.BOLD}╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║        ███╗   ███╗ █████╗ ██╗██╗         ████████╗███╗   ███╗        ║
║        ████╗ ████║██╔══██╗██║██║         ╚══██╔══╝████╗ ████║        ║
║        ██╔████╔██║███████║██║██║            ██║   ██╔████╔██║        ║
║        ██║╚██╔╝██║██╔══██║██║██║            ██║   ██║╚██╔╝██║        ║
║        ██║ ╚═╝ ██║██║  ██║██║███████╗██╗    ██║   ██║ ╚═╝ ██║        ║
║        ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝╚══════╝╚═╝    ╚═╝   ╚═╝     ╚═╝        ║
║                                                                      ║ 
║                   📧  Email Generator v1.0                           ║
║                   🌐  Powered by Mail.tm API                         ║
╚══════════════════════════════════════════════════════════════════════╝{C.RESET}
"""
    print(banner)


def print_separator():
    print(f"{C.DIM}{'─' * 62}{C.RESET}")


def print_success(msg):
    print(f"  {C.GREEN}✅ {msg}{C.RESET}")


def print_error(msg):
    print(f"  {C.RED}❌ {msg}{C.RESET}")


def print_info(msg):
    print(f"  {C.CYAN}ℹ️  {msg}{C.RESET}")


def print_warning(msg):
    print(f"  {C.YELLOW}⚠️  {msg}{C.RESET}")


def generate_random_username(length=10):
    """Генерация случайного имени пользователя."""
    chars = string.ascii_lowercase + string.digits
    return "".join(random.choice(chars) for _ in range(length))


def generate_random_password(length=16):
    """Генерация случайного пароля."""
    chars = string.ascii_letters + string.digits + "!@#$%&*"
    password = [
        random.choice(string.ascii_uppercase),
        random.choice(string.ascii_lowercase),
        random.choice(string.digits),
        random.choice("!@#$%&*"),
    ]
    password += [random.choice(chars) for _ in range(length - 4)]
    random.shuffle(password)
    return "".join(password)


# ─────────────────────────── Хранилище аккаунтов ───────────────────────────

def load_accounts():
    """Загрузка сохранённых аккаунтов из файла."""
    if os.path.exists(ACCOUNTS_FILE):
        try:
            with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []


def save_accounts(accounts):
    """Сохранение аккаунтов в файл."""
    with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
        json.dump(accounts, f, indent=2, ensure_ascii=False)


def add_account(account_data):
    """Добавление нового аккаунта в хранилище."""
    accounts = load_accounts()
    accounts.append(account_data)
    save_accounts(accounts)


# ─────────────────────────── API-функции ───────────────────────────

def get_available_domains():
    """Получение списка доступных доменов."""
    try:
        resp = requests.get(f"{API_BASE}/domains", headers=HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        domains = []
        for member in data.get("hydra:member", []):
            if member.get("isActive"):
                domains.append(member["domain"])
        return domains
    except requests.RequestException as e:
        print_error(f"Ошибка получения доменов: {e}")
        return []


def create_account(address, password):
    """Создание нового email-аккаунта."""
    payload = {"address": address, "password": password}
    try:
        resp = requests.post(
            f"{API_BASE}/accounts",
            headers=HEADERS,
            json=payload,
            timeout=10,
        )
        if resp.status_code == 201:
            return resp.json()
        elif resp.status_code == 422:
            print_error("Этот email уже занят. Попробуйте другое имя.")
            return None
        else:
            print_error(f"Ошибка создания: {resp.status_code} — {resp.text}")
            return None
    except requests.RequestException as e:
        print_error(f"Ошибка сети: {e}")
        return None


def get_token(address, password):
    """Получение токена авторизации."""
    payload = {"address": address, "password": password}
    try:
        resp = requests.post(
            f"{API_BASE}/token",
            headers=HEADERS,
            json=payload,
            timeout=10,
        )
        if resp.status_code == 200:
            return resp.json().get("token")
        else:
            print_error(f"Ошибка авторизации: {resp.status_code}")
            return None
    except requests.RequestException as e:
        print_error(f"Ошибка сети: {e}")
        return None


def get_messages(token):
    """Получение списка сообщений."""
    auth_headers = {**HEADERS, "Authorization": f"Bearer {token}"}
    try:
        resp = requests.get(
            f"{API_BASE}/messages", headers=auth_headers, timeout=10
        )
        if resp.status_code == 200:
            data = resp.json()
            return data.get("hydra:member", [])
        else:
            print_error(f"Ошибка получения сообщений: {resp.status_code}")
            return []
    except requests.RequestException as e:
        print_error(f"Ошибка сети: {e}")
        return []


def get_message_detail(token, message_id):
    """Получение подробностей сообщения."""
    auth_headers = {**HEADERS, "Authorization": f"Bearer {token}"}
    try:
        resp = requests.get(
            f"{API_BASE}/messages/{message_id}",
            headers=auth_headers,
            timeout=10,
        )
        if resp.status_code == 200:
            return resp.json()
        else:
            print_error(f"Ошибка чтения сообщения: {resp.status_code}")
            return None
    except requests.RequestException as e:
        print_error(f"Ошибка сети: {e}")
        return None


def delete_message(token, message_id):
    """Удаление сообщения."""
    auth_headers = {**HEADERS, "Authorization": f"Bearer {token}"}
    try:
        resp = requests.delete(
            f"{API_BASE}/messages/{message_id}",
            headers=auth_headers,
            timeout=10,
        )
        return resp.status_code == 204
    except requests.RequestException as e:
        print_error(f"Ошибка сети: {e}")
        return False


def delete_account(token, account_id):
    """Удаление аккаунта."""
    auth_headers = {**HEADERS, "Authorization": f"Bearer {token}"}
    try:
        resp = requests.delete(
            f"{API_BASE}/accounts/{account_id}",
            headers=auth_headers,
            timeout=10,
        )
        return resp.status_code == 204
    except requests.RequestException as e:
        print_error(f"Ошибка сети: {e}")
        return False


# ─────────────────────────── Интерактивные действия ───────────────────────────

def action_create_single():
    """Создание одного email-аккаунта."""
    print()
    print(f"  {C.BOLD}📨 Создание нового email-ящика{C.RESET}")
    print_separator()

    domains = get_available_domains()
    if not domains:
        print_error("Нет доступных доменов. Попробуйте позже.")
        return

    # Показать доступные домены
    print(f"\n  {C.CYAN}Доступные домены:{C.RESET}")
    for i, domain in enumerate(domains, 1):
        print(f"    {C.YELLOW}{i}.{C.RESET} @{domain}")

    if len(domains) == 1:
        selected_domain = domains[0]
    else:
        try:
            choice = int(input(f"\n  Выберите домен (1-{len(domains)}): ")) - 1
            selected_domain = domains[choice]
        except (ValueError, IndexError):
            selected_domain = domains[0]

    # Выбор имени
    print(f"\n  {C.CYAN}Выберите имя пользователя:{C.RESET}")
    print(f"    {C.YELLOW}1.{C.RESET} Случайное имя")
    print(f"    {C.YELLOW}2.{C.RESET} Ввести своё")

    name_choice = input(f"\n  Ваш выбор (1/2): ").strip()

    if name_choice == "2":
        username = input(f"  Введите имя: ").strip().lower()
        if not username:
            username = generate_random_username()
            print_info(f"Пустое имя — используется случайное: {username}")
    else:
        username = generate_random_username()

    address = f"{username}@{selected_domain}"
    password = generate_random_password()

    print(f"\n  {C.DIM}Создание аккаунта...{C.RESET}")

    result = create_account(address, password)
    if result:
        account_data = {
            "id": result.get("id"),
            "address": address,
            "password": password,
            "created_at": datetime.now().isoformat(),
        }
        add_account(account_data)

        print()
        print(f"  {C.GREEN}{C.BOLD}✅ Аккаунт успешно создан!{C.RESET}")
        print_separator()
        print(f"  {C.BOLD}📧 Email:{C.RESET}    {C.CYAN}{address}{C.RESET}")
        print(f"  {C.BOLD}🔑 Пароль:{C.RESET}   {C.YELLOW}{password}{C.RESET}")
        print(f"  {C.BOLD}🆔 ID:{C.RESET}       {C.DIM}{result.get('id')}{C.RESET}")
        print_separator()
        print_info(f"Данные сохранены в {ACCOUNTS_FILE}")


def action_create_bulk():
    """Массовая генерация аккаунтов."""
    print()
    print(f"  {C.BOLD}📦 Массовая генерация аккаунтов{C.RESET}")
    print_separator()

    domains = get_available_domains()
    if not domains:
        print_error("Нет доступных доменов.")
        return

    selected_domain = domains[0]
    print_info(f"Используется домен: @{selected_domain}")

    try:
        count = int(input(f"\n  Количество аккаунтов (1-20): ").strip())
        count = max(1, min(count, 20))
    except ValueError:
        count = 3

    print(f"\n  {C.DIM}Генерация {count} аккаунтов...{C.RESET}\n")

    created = 0
    for i in range(count):
        username = generate_random_username()
        address = f"{username}@{selected_domain}"
        password = generate_random_password()

        result = create_account(address, password)
        if result:
            account_data = {
                "id": result.get("id"),
                "address": address,
                "password": password,
                "created_at": datetime.now().isoformat(),
            }
            add_account(account_data)
            created += 1
            print(
                f"    {C.GREEN}[{created}/{count}]{C.RESET} {C.CYAN}{address}{C.RESET}"
                f"  |  🔑 {C.YELLOW}{password}{C.RESET}"
            )
        else:
            print(f"    {C.RED}[✗]{C.RESET} Не удалось создать {address}")

        # Пауза между запросами (rate limit: 8 QPS)
        if i < count - 1:
            time.sleep(0.3)

    print()
    print_separator()
    print_success(f"Создано {created} из {count} аккаунтов")
    print_info(f"Все данные сохранены в {ACCOUNTS_FILE}")


def action_list_accounts():
    """Просмотр сохранённых аккаунтов."""
    print()
    print(f"  {C.BOLD}📋 Сохранённые аккаунты{C.RESET}")
    print_separator()

    accounts = load_accounts()
    if not accounts:
        print_warning("Нет сохранённых аккаунтов.")
        return

    for i, acc in enumerate(accounts, 1):
        created = acc.get("created_at", "N/A")
        if created != "N/A":
            try:
                dt = datetime.fromisoformat(created)
                created = dt.strftime("%d.%m.%Y %H:%M")
            except ValueError:
                pass

        print(
            f"    {C.YELLOW}{i:>3}.{C.RESET} "
            f"{C.CYAN}{acc['address']:<35}{C.RESET} "
            f"🔑 {C.DIM}{acc['password']}{C.RESET} "
            f" | {C.DIM}{created}{C.RESET}"
        )

    print()
    print_separator()
    print_info(f"Всего: {len(accounts)} аккаунт(ов)")


def action_check_inbox():
    """Проверка входящих писем."""
    print()
    print(f"  {C.BOLD}📬 Проверка входящих{C.RESET}")
    print_separator()

    accounts = load_accounts()
    if not accounts:
        print_warning("Нет сохранённых аккаунтов. Сначала создайте аккаунт.")
        return

    # Выбор аккаунта
    print(f"\n  {C.CYAN}Выберите аккаунт:{C.RESET}")
    for i, acc in enumerate(accounts, 1):
        print(f"    {C.YELLOW}{i}.{C.RESET} {acc['address']}")

    try:
        choice = int(input(f"\n  Номер аккаунта: ").strip()) - 1
        account = accounts[choice]
    except (ValueError, IndexError):
        print_error("Неверный выбор.")
        return

    print(f"\n  {C.DIM}Авторизация...{C.RESET}")
    token = get_token(account["address"], account["password"])
    if not token:
        print_error("Не удалось авторизоваться.")
        return

    print(f"  {C.DIM}Загрузка сообщений...{C.RESET}\n")
    messages = get_messages(token)

    if not messages:
        print_warning("Входящих писем нет.")
        return

    print(f"  {C.GREEN}Найдено писем: {len(messages)}{C.RESET}\n")

    for i, msg in enumerate(messages, 1):
        seen_icon = "📭" if msg.get("seen") else "📩"
        from_info = msg.get("from", {})
        from_addr = from_info.get("address", "Неизвестно")
        subject = msg.get("subject", "(без темы)")
        created = msg.get("createdAt", "")
        if created:
            try:
                dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                created = dt.strftime("%d.%m.%Y %H:%M")
            except ValueError:
                pass

        print(
            f"    {C.YELLOW}{i}.{C.RESET} {seen_icon} "
            f"{C.BOLD}{subject[:50]}{C.RESET}"
        )
        print(
            f"       {C.DIM}От: {from_addr}  |  {created}{C.RESET}"
        )
        intro = msg.get("intro", "")
        if intro:
            print(f"       {C.DIM}{intro[:80]}...{C.RESET}")
        print()

    # Чтение конкретного письма
    read_choice = input(
        f"  Введите номер письма для чтения (или Enter для выхода): "
    ).strip()
    if read_choice:
        try:
            msg_idx = int(read_choice) - 1
            msg_id = messages[msg_idx]["id"]
            detail = get_message_detail(token, msg_id)
            if detail:
                print()
                print_separator()
                print(f"  {C.BOLD}📧 {detail.get('subject', '(без темы)')}{C.RESET}")
                print_separator()
                from_info = detail.get("from", {})
                print(
                    f"  {C.CYAN}От:{C.RESET} {from_info.get('name', '')} "
                    f"<{from_info.get('address', '')}>"
                )
                to_list = detail.get("to", [])
                to_str = ", ".join(
                    t.get("address", "") for t in to_list
                )
                print(f"  {C.CYAN}Кому:{C.RESET} {to_str}")
                print_separator()

                text = detail.get("text", "")
                if text:
                    print(f"\n{text}\n")
                else:
                    html = detail.get("html", [])
                    if html:
                        print_info("Письмо содержит только HTML-контент.")
                        print(f"\n  {C.DIM}{html[0][:500]}{C.RESET}\n")
                    else:
                        print_warning("Пустое письмо.")

                # Вложения
                attachments = detail.get("attachments", [])
                if attachments:
                    print_separator()
                    print(f"  {C.BOLD}📎 Вложения ({len(attachments)}):{C.RESET}")
                    for att in attachments:
                        print(
                            f"    • {att.get('filename', 'N/A')} "
                            f"({att.get('contentType', 'N/A')}, "
                            f"{att.get('size', 0)} байт)"
                        )
        except (ValueError, IndexError):
            print_error("Неверный номер.")


def action_wait_for_mail():
    """Ожидание нового письма с автообновлением."""
    print()
    print(f"  {C.BOLD}⏳ Ожидание нового письма{C.RESET}")
    print_separator()

    accounts = load_accounts()
    if not accounts:
        print_warning("Нет сохранённых аккаунтов.")
        return

    print(f"\n  {C.CYAN}Выберите аккаунт:{C.RESET}")
    for i, acc in enumerate(accounts, 1):
        print(f"    {C.YELLOW}{i}.{C.RESET} {acc['address']}")

    try:
        choice = int(input(f"\n  Номер аккаунта: ").strip()) - 1
        account = accounts[choice]
    except (ValueError, IndexError):
        print_error("Неверный выбор.")
        return

    token = get_token(account["address"], account["password"])
    if not token:
        print_error("Не удалось авторизоваться.")
        return

    # Сохраняем текущее кол-во сообщений
    initial_messages = get_messages(token)
    initial_count = len(initial_messages)

    interval = 5  # секунд
    print(f"\n  {C.CYAN}📧 Ящик: {account['address']}{C.RESET}")
    print(f"  {C.DIM}Текущих писем: {initial_count}{C.RESET}")
    print(f"  {C.DIM}Проверка каждые {interval} сек. Нажмите Ctrl+C для отмены.{C.RESET}\n")

    try:
        check_count = 0
        while True:
            time.sleep(interval)
            check_count += 1
            messages = get_messages(token)
            current_count = len(messages)

            sys.stdout.write(
                f"\r  {C.DIM}Проверка #{check_count}... "
                f"Писем: {current_count}{C.RESET}    "
            )
            sys.stdout.flush()

            if current_count > initial_count:
                print()
                new_msg = messages[0]  # Последнее письмо
                print(f"\n  {C.GREEN}{C.BOLD}🎉 Новое письмо!{C.RESET}")
                print_separator()
                from_info = new_msg.get("from", {})
                print(
                    f"  {C.CYAN}От:{C.RESET} {from_info.get('address', 'N/A')}"
                )
                print(
                    f"  {C.CYAN}Тема:{C.RESET} {new_msg.get('subject', '(без темы)')}"
                )
                print(
                    f"  {C.CYAN}Превью:{C.RESET} {new_msg.get('intro', '')[:100]}"
                )
                print_separator()

                # Прочитать подробности?
                read = input(
                    f"\n  Прочитать полностью? (y/n): "
                ).strip().lower()
                if read == "y":
                    detail = get_message_detail(token, new_msg["id"])
                    if detail:
                        text = detail.get("text", "")
                        if text:
                            print(f"\n{text}\n")

                initial_count = current_count

    except KeyboardInterrupt:
        print(f"\n\n  {C.YELLOW}Ожидание остановлено.{C.RESET}")


def action_delete_account():
    """Удаление аккаунта."""
    print()
    print(f"  {C.BOLD}🗑️  Удаление аккаунта{C.RESET}")
    print_separator()

    accounts = load_accounts()
    if not accounts:
        print_warning("Нет сохранённых аккаунтов.")
        return

    print(f"\n  {C.CYAN}Выберите аккаунт для удаления:{C.RESET}")
    for i, acc in enumerate(accounts, 1):
        print(f"    {C.YELLOW}{i}.{C.RESET} {acc['address']}")

    try:
        choice = int(input(f"\n  Номер аккаунта: ").strip()) - 1
        account = accounts[choice]
    except (ValueError, IndexError):
        print_error("Неверный выбор.")
        return

    confirm = input(
        f"\n  {C.RED}Удалить {account['address']}? (y/n): {C.RESET}"
    ).strip().lower()

    if confirm != "y":
        print_info("Отменено.")
        return

    token = get_token(account["address"], account["password"])
    if token and delete_account(token, account["id"]):
        accounts.pop(choice)
        save_accounts(accounts)
        print_success(f"Аккаунт {account['address']} удалён!")
    else:
        print_error("Не удалось удалить аккаунт с сервера.")
        remove_local = input(
            f"  Удалить из локального файла? (y/n): "
        ).strip().lower()
        if remove_local == "y":
            accounts.pop(choice)
            save_accounts(accounts)
            print_success("Удалено из локального хранилища.")


def action_export_txt():
    """Экспорт аккаунтов в текстовый файл."""
    print()
    print(f"  {C.BOLD}💾 Экспорт аккаунтов{C.RESET}")
    print_separator()

    accounts = load_accounts()
    if not accounts:
        print_warning("Нет аккаунтов для экспорта.")
        return

    filename = f"accounts_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    with open(filename, "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write("  Mail.tm — Экспорт аккаунтов\n")
        f.write(f"  Дата: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n")
        f.write("=" * 60 + "\n\n")

        for i, acc in enumerate(accounts, 1):
            f.write(f"[{i}]\n")
            f.write(f"  Email:    {acc['address']}\n")
            f.write(f"  Password: {acc['password']}\n")
            f.write(f"  ID:       {acc.get('id', 'N/A')}\n")
            f.write(f"  Created:  {acc.get('created_at', 'N/A')}\n")
            f.write("-" * 40 + "\n")

        f.write(f"\nВсего: {len(accounts)} аккаунт(ов)\n")

    print_success(f"Экспортировано в {filename}")
    print_info(f"Всего: {len(accounts)} аккаунт(ов)")


def action_setup_env():
    """Вывод команд для настройки окружения на VPS."""
    print()
    print(f"  {C.BOLD}🛠️  Настройка окружения (VPS){C.RESET}")
    print_separator()
    print(f"  {C.CYAN}Для настройки чистого VPS выполните следующие команды:{C.RESET}\n")

    commands = """
cd ~/mail-generator
sudo apt update
sudo apt install -y python3-venv python3-full

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
pip install requests
"""
    print(f"{C.YELLOW}{commands.strip()}{C.RESET}")
    print()
    print_info("Скопируйте и выполните эти команды в терминале.")
    input(f"\n  Нажмите Enter для продолжения...")


# ─────────────────────────── Главное меню ───────────────────────────

def main_menu():
    """Главное интерактивное меню."""
    while True:
        print()
        print(f"  {C.BOLD}{C.CYAN}╔═══════════════════════════════════════╗{C.RESET}")
        print(f"  {C.BOLD}{C.CYAN}║         📋 ГЛАВНОЕ МЕНЮ              ║{C.RESET}")
        print(f"  {C.BOLD}{C.CYAN}╚═══════════════════════════════════════╝{C.RESET}")
        print()
        print(f"    {C.YELLOW}1.{C.RESET} 📨 Создать email-ящик")
        print(f"    {C.YELLOW}2.{C.RESET} 📦 Массовая генерация")
        print(f"    {C.YELLOW}3.{C.RESET} 📋 Мои аккаунты")
        print(f"    {C.YELLOW}4.{C.RESET} 📬 Проверить входящие")
        print(f"    {C.YELLOW}5.{C.RESET} ⏳ Ждать новое письмо")
        print(f"    {C.YELLOW}6.{C.RESET} 🗑️  Удалить аккаунт")
        print(f"    {C.YELLOW}7.{C.RESET} 💾 Экспорт в .txt")
        print(f"    {C.YELLOW}8.{C.RESET} 🛠️  Настройка окружения (VPS)")
        print(f"    {C.YELLOW}0.{C.RESET} 🚪 Выход")
        print()

        choice = input(f"  {C.BOLD}Выберите действие ▶ {C.RESET}").strip()

        if choice == "1":
            action_create_single()
        elif choice == "2":
            action_create_bulk()
        elif choice == "3":
            action_list_accounts()
        elif choice == "4":
            action_check_inbox()
        elif choice == "5":
            action_wait_for_mail()
        elif choice == "6":
            action_delete_account()
        elif choice == "7":
            action_export_txt()
        elif choice == "8":
            action_setup_env()
        elif choice == "0":
            print(f"\n  {C.CYAN}👋 До свидания!{C.RESET}\n")
            break
        else:
            print_error("Неверный выбор. Попробуйте снова.")


# ─────────────────────────── Точка входа ───────────────────────────

def main():
    clear_screen()
    print_banner()

    # Быстрый тест соединения
    print(f"  {C.DIM}Проверка соединения с Mail.tm...{C.RESET}")
    domains = get_available_domains()
    if domains:
        print_success(f"Подключено! Доступные домены: {', '.join(domains)}")
    else:
        print_error("Не удалось подключиться к Mail.tm API.")
        print_info("Проверьте интернет-соединение и попробуйте позже.")
        return

    accounts = load_accounts()
    if accounts:
        print_info(f"Загружено {len(accounts)} сохранённых аккаунтов")

    main_menu()


if __name__ == "__main__":
    main()
