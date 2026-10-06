import os
import re
import logging
from typing import Dict, Any, List, Optional

from aiohttp import web, ClientSession, TCPConnector
from dotenv import load_dotenv

# =====================================================================
# 1. КОНФИГУРАЦИЯ И ДАННЫЕ
# =====================================================================
load_dotenv()

MAX_API_BASE_URL = os.getenv("MAX_API_BASE_URL", "https://platform-api2.max.ru")
BOT_TOKEN = os.getenv(
    "BOT_TOKEN",
    "f9LHodD0cOK6F9nc6kr6ky0CWdnWdY9doCzwFElXkNvqdkMKOlNNs7YZi8RcPk3linYFzlw3qGBXIWOmocDY"
)
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "-79780607715530")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://bot-1791222128-3841-dl1xxz.bothost.tech/webhook")
WEBAPP_URL = "https://bot-1791222128-3841-dl1xxz.bothost.tech/"

BOOKING_URL = "https://reservationsteps.ru/rooms/index/8dc26407-5b2f-46e5-8597-ebfc46cf8111?dfrom=11-06-2027&dto=20-06-2027&adults=2&lang=ru"
REVIEWS_YANDEX_URL = "https://yandex.ru/maps/org/rusalochka/241387417775/reviews/?ll=37.156738%2C45.028213&z=11.94"
REVIEWS_2GIS_URL = "https://2gis.ru/anapa/firm/70000001033010188"
YANDEX_ROUTE_URL = "https://yandex.ru/maps/org/rusalochka/241387417775?si=5zprzpwhdg2vqk8wegq6b3krmr"
RULES_PDF_URL = f"{WEBAPP_URL}rules.pdf"
OFERTA_PDF_URL = f"{WEBAPP_URL}oferta.pdf"

USER_STATES: Dict[str, str] = {}

# Номерной фонд базы отдыха «Русалочка» (Цены: июнь 2026)
ROOMS_CATALOG: Dict[str, Dict[str, Any]] = {
    "kitchen_2p": {
        "title": "Номер с кухней (апарт.) 2-х местный + доп.место",
        "folder": "kitchen_2p",
        "capacity": "2 осн. места + доп. место",
        "price": "от 10 500 ₽ / сутки",
        "description": (
            "🏡 Номер с кухней (апарт.) 2-х местный + доп.место\n\n"
            "Уютный семейный апартамент повышенной комфортности с индивидуальной кухней.\n\n"
            "В номере:\n"
            "• Двуспальная кровать + доп. место (диван / кресло-кровать)\n"
            "• Кухня: плита, СВЧ, холодильник, посуда, чайник\n"
            "• Сплит-система, ЖК ТВ, Wi-Fi, санузел с душем\n"
            "• Индивидуальная веранда/балкон\n\n"
            "👥 Вместимость: 2 осн. места + доп. место\n"
            "💰 Июнь (Все включено с 3-раз. питанием): от 10 500 ₽ / сутки\n"
            "💰 Июнь (Без питания): от 9 300 ₽ / сутки\n"
            "➕ Доп. место: 2 990 ₽/сут (с питанием) / 2 200 ₽/сут (без питания)"
        ),
    },
    "kitchen_3p": {
        "title": "Номер с кухней (апарт.) 3-х местный + доп.место",
        "folder": "kitchen_3p",
        "capacity": "3 осн. места + доп. место",
        "price": "от 15 500 ₽ / сутки",
        "description": (
            "🏡 Номер с кухней (апарт.) 3-х местный + доп.место\n\n"
            "Просторный апартамент для комфортного отдыха всей семьей.\n\n"
            "В номере:\n"
            "• Двуспальная кровать, 1-спальная кровать + доп. место\n"
            "• Кухонный модуль: варочная панель, СВЧ, холодильник, посуда, чайник\n"
            "• Сплит-система, ТВ, Wi-Fi, санузел с душем, веранда\n\n"
            "👥 Вместимость: 3 осн. места + доп. место\n"
            "💰 Июнь (Все включено с 3-раз. питанием): от 15 500 ₽ / сутки\n"
            "💰 Июнь (Без питания): от 13 700 ₽ / сутки\n"
            "➕ Доп. место: 2 990 ₽/сут (с питанием) / 2 200 ₽/сут (без питания)"
        ),
    },
    "eco_1k_2p": {
        "title": "Эко-домик 1-комнатный 2-х местный + доп.место",
        "folder": "eco_1k_2p",
        "capacity": "2 осн. места + доп. место",
        "price": "от 9 690 ₽ / сутки",
        "description": (
            "🏡 Эко-домик 1-комнатный 2-х местный + доп.место\n\n"
            "Отдельный домик из экологически чистого натурального бруса.\n\n"
            "В домике:\n"
            "• Двуспальная кровать + кресло-кровать\n"
            "• Сплит-система, холодильник, чайник, ТВ, санузел с душем\n"
            "• Терраса на свежем воздухе\n\n"
            "👥 Вместимость: 2 осн. места + доп. место\n"
            "💰 Июнь (Все включено с 3-раз. питанием): от 9 690 ₽ / сутки\n"
            "💰 Июнь (Без питания): от 8 490 ₽ / сутки\n"
            "➕ Доп. место: 2 990 ₽/сут (с питанием) / 2 200 ₽/сут (без питания)"
        ),
    },
    "eco_2k_3p": {
        "title": "Эко-домик 2-комнатный 3-х местный + доп.место",
        "folder": "eco_2k_3p",
        "capacity": "3 осн. места + доп. место",
        "price": "от 14 390 ₽ / сутки",
        "description": (
            "🏡 Эко-домик 2-комнатный 3-х местный + доп.место\n\n"
            "Двухкомнатный коттедж из бруса для большой семьи.\n\n"
            "В домике:\n"
            "• 2 спальные комнаты (3 осн. места + евро-раскладушка)\n"
            "• Кондиционер, холодильник, ТВ, чайник, санузел с душем\n"
            "• Просторная деревянная терраса\n\n"
            "👥 Вместимость: 3 осн. места + доп. место\n"
            "💰 Июнь (Все включено с 3-раз. питанием): от 14 390 ₽ / сутки\n"
            "💰 Июнь (Без питания): от 12 590 ₽ / сутки\n"
            "➕ Доп. место: 2 990 ₽/сут (с питанием) / 2 200 ₽/сут (без питания)"
        ),
    },
    "std_brick_3p": {
        "title": "СТАНДАРТ кирпичный домик 3-х местный",
        "folder": "std_brick_3p",
        "capacity": "3 осн. места",
        "price": "от 9 890 ₽ / сутки",
        "description": (
            "🏡 СТАНДАРТ кирпичный домик 3-х местный\n\n"
            "Капитальный прохладный домик для семьи или компании.\n\n"
            "В домике:\n"
            "• 3 комфортных спальных места\n"
            "• Сплит-система, холодильник, ТВ, санузел с душем, веранда\n\n"
            "👥 Вместимость: 3 осн. места\n"
            "💰 Июнь (Полный пансион с 3-раз. питанием): от 9 890 ₽ / сутки\n"
            "💰 Июнь (Без питания): от 8 090 ₽ / сутки\n"
            "➕ Доп. место: 2 800 ₽/сут (с питанием) / 2 200 ₽/сут (без питания)"
        ),
    },
    "std_wood_2p": {
        "title": "СТАНДАРТ Деревянный домик 2-х местный",
        "folder": "std_wood_2p",
        "capacity": "2 осн. места",
        "price": "от 6 590 ₽ / сутки",
        "description": (
            "🏡 СТАНДАРТ Деревянный домик 2-х местный\n\n"
            "Уютный деревянный домик для двоих в зелёной зоне.\n\n"
            "В домике:\n"
            "• 2 спальных места\n"
            "• Кондиционер, холодильник, ТВ, санузел с душем, терраса\n\n"
            "👥 Вместимость: 2 осн. места\n"
            "💰 Июнь (Полный пансион с 3-раз. питанием): от 6 590 ₽ / сутки\n"
            "💰 Июнь (Без питания): от 5 390 ₽ / сутки\n"
            "➕ Доп. место: 2 800 ₽/сут (с питанием) / 2 200 ₽/сут (без питания)"
        ),
    },
    "std_2p": {
        "title": "СТАНДАРТ 2-х местный",
        "folder": "std_2p",
        "capacity": "2 осн. места",
        "price": "от 6 390 ₽ / сутки",
        "description": (
            "🏡 СТАНДАРТ 2-х местный\n\n"
            "Классический номер для 2 гостей.\n\n"
            "В номере:\n"
            "• Двуспальная кровать, кондиционер, ТВ, холодильник, санузел\n\n"
            "👥 Вместимость: 2 осн. места\n"
            "💰 Июнь (Полный пансион с 3-раз. питанием): от 6 390 ₽ / сутки\n"
            "💰 Июнь (Без питания): от 5 190 ₽ / сутки"
        ),
    },
    "std_2p_extra": {
        "title": "СТАНДАРТ 2-х местный + доп.место",
        "folder": "std_2p_extra",
        "capacity": "2 осн. места + доп. место",
        "price": "от 6 390 ₽ / сутки",
        "description": (
            "🏡 СТАНДАРТ 2-х местный + доп.место\n\n"
            "Номер категории стандарт для семьи до 3 человек.\n\n"
            "В номере:\n"
            "• Двуспальная кровать + доп. место\n"
            "• Сплит-система, ТВ, холодильник, санузел с душем, терраса\n\n"
            "👥 Вместимость: 2 осн. места + доп. место\n"
            "💰 Июнь (Полный пансион с 3-раз. питанием): от 6 390 ₽ / сутки\n"
            "💰 Июнь (Без питания): от 5 190 ₽ / сутки\n"
            "➕ Доп. место: 2 800 ₽/сут (с питанием) / 2 200 ₽/сут (без питания)"
        ),
    },
    "std_3p": {
        "title": "СТАНДАРТ 3-х местный",
        "folder": "std_3p",
        "capacity": "3 осн. места",
        "price": "от 8 990 ₽ / сутки",
        "description": (
            "🏡 СТАНДАРТ 3-х местный\n\n"
            "Просторный 3-местный номер стандартной категории.\n\n"
            "В номере:\n"
            "• 3 основных спальных места\n"
            "• Кондиционер, холодильник, ТВ, санузел с душем, веранда\n\n"
            "👥 Вместимость: 3 осн. места\n"
            "💰 Июнь (Полный пансион с 3-раз. питанием): от 8 990 ₽ / сутки\n"
            "💰 Июнь (Без питания): от 7 190 ₽ / сутки\n"
            "➕ Доп. место: 2 800 ₽/сут (с питанием) / 2 200 ₽/сут (без питания)"
        ),
    },
    "std_4p": {
        "title": "СТАНДАРТ 4-х местный + доп.место",
        "folder": "std_4p",
        "capacity": "4 осн. места + доп. место",
        "price": "от 11 500 ₽ / сутки",
        "description": (
            "🏡 СТАНДАРТ 4-х местный + доп.место\n\n"
            "Семейный просторный номер на 4–5 гостей.\n\n"
            "В номере:\n"
            "• 4 основных спальных места + 1 доп. место\n"
            "• Сплит-система, холодильник, ТВ, санузел с душем, веранда\n\n"
            "👥 Вместимость: 4 осн. места + доп. место\n"
            "💰 Июнь (Полный пансион с 3-раз. питанием): от 11 500 ₽ / сутки\n"
            "💰 Июнь (Без питания): от 9 100 ₽ / сутки\n"
            "➕ Доп. место: 2 800 ₽/сут (с питанием) / 2 200 ₽/сут (без питания)"
        ),
    },
}

def get_room_photos(folder_name: str) -> List[str]:
    folder_path = os.path.join("images", folder_name)
    if not os.path.isdir(folder_path):
        return []

    photos = []
    valid_extensions = ('.webp', '.jpg', '.jpeg', '.png')
    try:
        files = sorted(os.listdir(folder_path))
        for f in files:
            if f.lower().endswith(valid_extensions):
                photos.append(f"/images/{folder_name}/{f}")
    except Exception as e:
        logging.error(f"Ошибка чтения папки {folder_path}: {e}")
    return photos

# =====================================================================
# 2. КЛИЕНТ API MAX
# =====================================================================
class MaxBotClient:
    def __init__(self, token: str, base_url: str):
        self.token = token
        self.base_url = base_url.rstrip("/")

    @property
    def headers(self) -> Dict[str, str]:
        return {
            "Authorization": self.token,
            "Content-Type": "application/json"
        }

    def _get_connector(self) -> TCPConnector:
        return TCPConnector(ssl=False)

    async def get_me(self) -> None:
        url = f"{self.base_url}/me"
        try:
            async with ClientSession(connector=self._get_connector()) as session:
                async with session.get(url, headers=self.headers) as resp:
                    data = await resp.text()
                    logging.info(f"Проверка /me: статус={resp.status}, ответ={data}")
        except Exception as e:
            logging.error(f"Ошибка вызова /me: {e}")

    async def setup_subscription(self, webhook_target: str) -> None:
        url = f"{self.base_url}/subscriptions"
        payload = {"url": webhook_target}
        try:
            async with ClientSession(connector=self._get_connector()) as session:
                async with session.post(url, headers=self.headers, json=payload) as resp:
                    resp_text = await resp.text()
                    logging.info(f"Регистрация Webhook (/subscriptions): статус={resp.status}, ответ={resp_text}")
        except Exception as e:
            logging.error(f"Не удалось отправить запрос подписки: {e}")

    async def answer_callback(self, callback_id: str) -> None:
        if not callback_id:
            return
        url = f"{self.base_url}/answers"
        params = {"callback_id": callback_id}
        try:
            async with ClientSession(connector=self._get_connector()) as session:
                async with session.post(url, headers=self.headers, params=params, json={}) as resp:
                    pass
        except Exception as e:
            logging.error(f"Ошибка answer_callback: {e}")

    async def send_message(
        self,
        chat_id: Optional[Any] = None,
        user_id: Optional[Any] = None,
        text: str = "",
        buttons: List[List[Dict[str, str]]] = None
    ) -> bool:
        url = f"{self.base_url}/messages"

        attachments = []
        if buttons:
            max_buttons = []
            for row in buttons:
                new_row = []
                for b in row:
                    btn_text = b.get("text", "")
                    if "url" in b:
                        new_row.append({"type": "link", "text": btn_text, "url": b["url"]})
                    else:
                        new_row.append({
                            "type": "callback",
                            "text": btn_text,
                            "payload": b.get("payload", btn_text)
                        })
                max_buttons.append(new_row)

            attachments.append({
                "type": "inline_keyboard",
                "payload": {"buttons": max_buttons}
            })

        payload = {"text": text}
        if attachments:
            payload["attachments"] = attachments

        try:
            async with ClientSession(connector=self._get_connector()) as session:
                if chat_id:
                    target_cid = int(chat_id) if str(chat_id).lstrip("-").isdigit() else chat_id
                    async with session.post(url, headers=self.headers, params={"chat_id": target_cid}, json=payload) as resp:
                        if resp.status in (200, 201):
                            return True
                        resp_text = await resp.text()
                        logging.warning(f"Ошибка chat_id ({resp.status}): {resp_text}")

                if user_id:
                    target_uid = int(user_id) if str(user_id).isdigit() else user_id
                    async with session.post(url, headers=self.headers, params={"user_id": target_uid}, json=payload) as resp:
                        if resp.status in (200, 201):
                            return True
                        resp_text = await resp.text()
                        logging.warning(f"Ошибка user_id ({resp.status}): {resp_text}")

                return False
        except Exception as e:
            logging.error(f"Исключение send_message: {e}")
            return False

max_bot = MaxBotClient(BOT_TOKEN, MAX_API_BASE_URL)

# =====================================================================
# 3. КНОПКИ
# =====================================================================
def get_main_menu_buttons() -> List[List[Dict[str, str]]]:
    return [
        [{"text": "📱 Витрина с фото номеров (Web)", "url": WEBAPP_URL}],
        [{"text": "🏡 Список номеров", "payload": "menu_rooms"}, {"text": "📝 Забронировать", "payload": "menu_book"}],
        [{"text": "🌴 О базе", "payload": "menu_about"}, {"text": "🎡 Услуги и сервис", "payload": "menu_infra"}],
        [{"text": "⭐ Отзывы", "payload": "menu_reviews"}, {"text": "❓ Вопросы и ответы (FAQ)", "payload": "menu_faq"}],
        [{"text": "📞 Контакты и локация", "payload": "menu_contacts"}],
        [{"text": "💬 Задать вопрос администратору", "payload": "menu_feedback"}]
    ]

def get_cancel_buttons() -> List[List[Dict[str, str]]]:
    return [[{"text": "❌ Отменить вопрос", "payload": "cancel_feedback"}]]

def get_rooms_list_buttons() -> List[List[Dict[str, str]]]:
    buttons = [
        [{"text": "📱 Открыть фото-витрину всех номеров", "url": WEBAPP_URL}]
    ]
    for key, data in ROOMS_CATALOG.items():
        buttons.append([{"text": f"🏡 {data['title']}", "payload": f"view_room_{key}"}])
    buttons.append([{"text": "⬅️ В главное меню", "payload": "menu_root"}])
    return buttons

def get_single_room_buttons(room_key: str) -> List[List[Dict[str, str]]]:
    return [
        [{"text": "📱 Посмотреть все фото номера", "url": f"{WEBAPP_URL}#room-{room_key}"}],
        [{"text": "🛎 Забронировать этот номер", "url": BOOKING_URL}],
        [{"text": "⬅️ Назад к списку номеров", "payload": "menu_rooms"}]
    ]

def get_faq_buttons() -> List[List[Dict[str, str]]]:
    return [
        [{"text": "Во сколько заселение?", "payload": "faq_checkin"}],
        [{"text": "Во сколько выселение из номера?", "payload": "faq_checkout"}],
        [{"text": "При бронировании нужно вносить предоплату?", "payload": "faq_prepayment"}],
        [{"text": "Предоплата возвратная?", "payload": "faq_refund"}],
        [{"text": "Возможно размещение с животными?", "payload": "faq_pets"}],
        [{"text": "📄 Правила проживания (PDF)", "url": RULES_PDF_URL}],
        [{"text": "📑 Договор оферты (PDF)", "url": OFERTA_PDF_URL}],
        [{"text": "💬 Задать свой вопрос", "payload": "menu_feedback"}],
        [{"text": "⬅️ В главное меню", "payload": "menu_root"}]
    ]

# =====================================================================
# 4. ОБРАБОТЧИК ВЕБХУКА MAX
# =====================================================================
async def handle_webhook(request: web.Request):
    try:
        data = await request.json()
    except Exception:
        return web.Response(status=400)

    update_type = data.get("update_type", "")
    message = data.get("message", {})
    body = message.get("body", {})
    recipient = message.get("recipient", {})
    callback = data.get("callback", {})
    callback_user = callback.get("user", {})
    msg_sender = message.get("sender", {})
    root_user = data.get("user", {})

    sender = callback_user or msg_sender or root_user or {}

    if sender.get("is_bot") is True:
        return web.json_response({"status": "ok"})

    callback_id = callback.get("callback_id") or data.get("callback_id")
    if callback_id:
        await max_bot.answer_callback(callback_id)

    chat_id = (
        callback.get("chat_id")
        or callback.get("message", {}).get("recipient", {}).get("chat_id")
        or recipient.get("chat_id")
        or message.get("chat_id")
        or data.get("chat_id")
    )
    user_id = (
        callback.get("user_id")
        or sender.get("user_id")
        or data.get("user_id")
    )
    user_id_str = str(user_id) if user_id else ""
    sender_name = sender.get("name") or sender.get("first_name") or "Гость"

    payload = callback.get("payload") or data.get("payload") or ""
    text = (body.get("text") or message.get("text") or "").strip()
    action = payload if payload else text

    if not chat_id and not user_id:
        return web.json_response({"status": "ok"})

    chat_id_str = str(chat_id) if chat_id else ""

    async def reply(msg_text: str, btns: list = None):
        return await max_bot.send_message(
            chat_id=chat_id,
            user_id=user_id,
            text=msg_text,
            buttons=btns
        )

    # 1. ОТВЕТ АДМИНИСТРАТОРА
    if str(ADMIN_CHAT_ID) != "0" and chat_id_str == str(ADMIN_CHAT_ID):
        raw_msg_str = str(message)
        match = re.search(r"#user_(\d+)", raw_msg_str)
        if match and text:
            target_guest_chat = match.group(1)
            guest_answer = (
                f"💬 Ответ от администрации базы отдыха «Русалочка»:\n\n"
                f"{text}\n\n"
                f"---------------------------------\n"
                f"Если у вас есть еще вопросы, напишите их прямо сюда!"
            )
            success = await max_bot.send_message(chat_id=target_guest_chat, user_id=target_guest_chat, text=guest_answer)
            if success:
                await reply("✅ Ответ успешно доставлен гостю!")
            else:
                await reply(f"⚠️ Не удалось доставить ответ гостю (ID: {target_guest_chat}).")
            return web.json_response({"status": "ok"})

    # 2. ОЖИДАНИЕ ВВОДА ВОПРОСА
    if USER_STATES.get(user_id_str) == "waiting_feedback":
        if action == "cancel_feedback" or text.lower() in ["отмена", "❌ отменить вопрос"]:
            USER_STATES.pop(user_id_str, None)
            await reply("Отправка вопроса отменена.", get_main_menu_buttons())
            return web.json_response({"status": "ok"})

        USER_STATES.pop(user_id_str, None)
        await reply(
            "✅ Ваш вопрос передан администраторам базы отдыха «Русалочка»!\n\n"
            "Мы ответим вам прямо в этот диалог в ближайшее время.",
            get_main_menu_buttons()
        )

        if str(ADMIN_CHAT_ID) != "0":
            guest_ref = chat_id_str if chat_id_str else user_id_str
            admin_ticket = (
                f"📩 НОВЫЙ ВОПРОС ОТ ГОСТЯ В MAX\n"
                f"👤 Имя: {sender_name}\n"
                f"💬 Вопрос:\n«{text}»\n\n"
                f"👉 Чтобы ответить гостю, нажмите «Ответить» (Reply) на это сообщение.\n"
                f"#user_{guest_ref}"
            )
            await max_bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_ticket)
        return web.json_response({"status": "ok"})

    # 3. МЕНЮ
    if action in ["menu_root", "/start", "start"] or update_type in ["bot_started", "chat_started"]:
        welcome_text = (
            "Добро пожаловать в базу отдыха «Русалочка»! 🌊\n\n"
            "Семейный отдых на песчаном побережье Черного моря (Анапа, ст. Благовещенская).\n"
            "Зеленая территория, уютные эко-домики и номера с оборудованной кухней!\n\n"
            "📅 Период работы: с 11 июня по 15 сентября\n"
            "🕒 Заезд — с 13:00 | Выезд — до 11:00\n\n"
            "Нажмите «📱 Витрина с фото номеров», чтобы открыть интерактивный каталог с фотографиями ⬇️"
        )
        await reply(welcome_text, get_main_menu_buttons())
        return web.json_response({"status": "ok"})

    elif action in ["menu_rooms", "🏡 Наши номера", "🏡 Список номеров"]:
        rooms_text = "🏡 Номерной фонд базы отдыха «Русалочка»:\n\nВыберите категорию для просмотра описания и цен или откройте витрину:"
        await reply(rooms_text, get_rooms_list_buttons())
        return web.json_response({"status": "ok"})

    elif action.startswith("view_room_"):
        room_key = action.replace("view_room_", "")
        room = ROOMS_CATALOG.get(room_key)
        if room:
            await reply(
                msg_text=room["description"],
                btns=get_single_room_buttons(room_key)
            )
        return web.json_response({"status": "ok"})

    elif action in ["menu_book", "📝 Забронировать"]:
        book_info = (
            "📝 Онлайн-бронирование номеров\n\n"
            "В нашем официальном модуле вы можете в реальном времени выбрать удобные даты, "
            "проверить наличие свободных мест и мгновенно забронировать проживание!\n\n"
            "📌 Условия бронирования:\n"
            "• Период работы: с 11 июня по 15 сентября\n"
            "• Заезд: с 13:00 | Выезд: до 11:00\n"
            "• Предоплата: 30% от общей стоимости\n"
            "• Бесплатная отмена: за 14 дней до заезда"
        )
        buttons = [
            [{"text": "💳 Перейти к бронированию и оплате", "url": BOOKING_URL}],
            [{"text": "⬅️ В главное меню", "payload": "menu_root"}]
        ]
        await reply(book_info, buttons)
        return web.json_response({"status": "ok"})

    elif action in ["menu_infra", "🎡 Услуги и сервис", "🎡 Инфраструктура и услуги"]:
        infra_text = (
            "🎡 ИНФРАСТРУКТУРА И УСЛУГИ\n\n"
            "✅ ВКЛЮЧЕНО В СТОИМОСТЬ:\n"
            "• 👶 Детская игровая площадка\n"
            "• ⚽ Настольный теннис, футбол, шахматы, спортинвентарь\n"
            "• 🥩 Мангальная зона (решетки, шампуры, печь, казан 12 л)\n"
            "• 🌸 Зеленая территория: 350 кустов роз и 2000 кустов лаванды\n\n"
            "💲 ДОПОЛНИТЕЛЬНЫЕ УСЛУГИ:\n"
            "• 👶 Детская кроватка (до 3 лет): 800 ₽/сут (от 10 суток — бесплатно)\n"
            "• 🐶 Проживание с питомцем (до 5–7 кг): 800 ₽/сут (депозит 5 000 ₽)\n"
            "• 🍽 3-разовое комплексное питание (в розницу): 1 500 ₽/сут\n"
            "• 🧺 Прачечная и гладильная комната\n"
            "• ⚡ Зарядная станция GB/T 7 кВт для электромобилей:\n"
            "  — Цена: 25 ₽ / 1 кВт·ч\n"
            "  — Режим: с 9:00 до 19:00, для гостей базы отдыха — круглосуточно"
        )
        await reply(infra_text, get_main_menu_buttons())
        return web.json_response({"status": "ok"})

    elif action in ["menu_about", "🌴 О базе"]:
        about_text = (
            "🌴 База отдыха «Русалочка»\n\n"
            "• Чистейший широкий песчаный пляж Черного моря\n"
            "• Охраняемая закрытая зеленая территория\n"
            "• Комплексное 3-разовое питание включено в основные тарифы\n"
            "• Период сезона: с 11 июня по 15 сентября\n\n"
            "🌐 Официальные сайты:\n"
            "• https://rusalo4ka.com/\n"
            "• https://русалочка.рф"
        )
        buttons = [
            [{"text": "🌐 rusalo4ka.com", "url": "https://rusalo4ka.com/"}],
            [{"text": "🌐 русалочка.рф", "url": "https://русалочка.рф"}],
            [{"text": "⬅️ В главное меню", "payload": "menu_root"}]
        ]
        await reply(about_text, buttons)
        return web.json_response({"status": "ok"})

    elif action in ["menu_reviews", "⭐ Отзывы"]:
        buttons = [
            [{"text": "⭐ Отзывы на Яндекс.Картах", "url": REVIEWS_YANDEX_URL}],
            [{"text": "🗺️ Отзывы в 2ГИС", "url": REVIEWS_2GIS_URL}],
            [{"text": "⬅️ В главное меню", "payload": "menu_root"}]
        ]
        await reply("⭐ Отзывы наших гостей на онлайн-картах:", buttons)
        return web.json_response({"status": "ok"})

    elif action in ["menu_contacts", "📞 Контакты и локация"]:
        contacts_text = (
            "📞 Контакты базы отдыха «Русалочка»:\n\n"
            "📍 Адрес: Краснодарский край, г. Анапа, ст. Благовещенская, ул. Прибрежная, д. 13, б/о «Русалочка»\n"
            "📞 Отдел бронирования: +7 (918) 47-74-366\n"
            "✉️ E-mail: anaparusalochka@rambler.ru\n"
            "🌐 Сайты: https://rusalo4ka.com/ | https://русалочка.рф"
        )
        buttons = [
            [{"text": "🧭 Маршрут в Яндекс Картах", "url": YANDEX_ROUTE_URL}],
            [{"text": "📄 Правила проживания (PDF)", "url": RULES_PDF_URL}],
            [{"text": "📑 Договор оферты (PDF)", "url": OFERTA_PDF_URL}],
            [{"text": "💬 Задать вопрос в чате", "payload": "menu_feedback"}],
            [{"text": "⬅️ В главное меню", "payload": "menu_root"}]
        ]
        await reply(contacts_text, buttons)
        return web.json_response({"status": "ok"})

    elif action in ["menu_faq", "❓ Вопросы и ответы (FAQ)"]:
        await reply("Часто задаваемые вопросы:", get_faq_buttons())
        return web.json_response({"status": "ok"})

    elif action == "faq_checkin":
        ans = "Во сколько заселение?\n\n— с 13:00, но если Вы приедете раньше и ваш номер будет уже свободен, мы заселим Вас раньше."
        await reply(ans, [[{"text": "⬅️ Назад в FAQ", "payload": "menu_faq"}]])
        return web.json_response({"status": "ok"})

    elif action == "faq_checkout":
        ans = "Во сколько выселение?\n\n— освободить номер нужно до 11:00, ключи и браслеты сдаются в администрацию."
        await reply(ans, [[{"text": "⬅️ Назад в FAQ", "payload": "menu_faq"}]])
        return web.json_response({"status": "ok"})

    elif action == "faq_prepayment":
        ans = "При бронировании нужно вносить предоплату?\n\n— бронирование выбранной категории номера производится после перечисления предоплаты (30% от полной стоимости проживания)."
        await reply(ans, [[{"text": "⬅️ Назад в FAQ", "payload": "menu_faq"}]])
        return web.json_response({"status": "ok"})

    elif action == "faq_refund":
        ans = "Предоплата возвратная?\n\n— бесплатная отмена бронирования возможна за 14 дней до заезда, после — взимается 100% от суммы предоплаты."
        await reply(ans, [[{"text": "⬅️ Назад в FAQ", "payload": "menu_faq"}]])
        return web.json_response({"status": "ok"})

    elif action == "faq_pets":
        ans = (
            "Возможно размещение с животными?\n\n"
            "— Разрешено с декоративными собаками весом до 5–7 кг в категории «Номер с кухней эко».\n"
            "— Тариф: 800 руб./сутки.\n"
            "— Рекомендуется возвратный депозит: 5 000 руб.\n"
            "— Выгул собак по территории базы запрещен.\n\n"
            "📄 Ознакомьтесь с официальными документами по кнопкам ниже:"
        )
        buttons = [
            [{"text": "📄 Правила проживания (PDF)", "url": RULES_PDF_URL}],
            [{"text": "📑 Договор оферты (PDF)", "url": OFERTA_PDF_URL}],
            [{"text": "⬅️ Назад в FAQ", "payload": "menu_faq"}]
        ]
        await reply(ans, buttons)
        return web.json_response({"status": "ok"})

    elif action in ["menu_feedback", "💬 Задать вопрос администратору"]:
        USER_STATES[user_id_str] = "waiting_feedback"
        prompt = (
            "💬 Задать вопрос администратору базы отдыха\n\n"
            "Напишите ваш вопрос следующим сообщением. Мы получим его и ответим вам прямо в этот диалог!"
        )
        await reply(prompt, get_cancel_buttons())
        return web.json_response({"status": "ok"})

    elif text:
        prompt = (
            "Я получил ваше сообщение! 🌊\n\n"
            "Если вы хотите передать вопрос администратору базы «Русалочка», нажмите кнопку ниже:"
        )
        buttons = [
            [{"text": "💬 Задать вопрос администратору", "payload": "menu_feedback"}],
            [{"text": "⬅️ В главное меню", "payload": "menu_root"}]
        ]
        await reply(prompt, buttons)
        return web.json_response({"status": "ok"})

    return web.json_response({"status": "ok"})

# =====================================================================
# 5. MINI WEB APP С МУЛЬТИ-ФОТО ГАЛЕРЕЕЙ (.WEBP)
# =====================================================================
async def handle_get(request: web.Request):
    cards_html = ""
    for key, room in ROOMS_CATALOG.items():
        folder_name = room.get("folder", key)
        photos = get_room_photos(folder_name)
        
        if photos:
            photos_count = len(photos)
            gallery_inner = "".join([
                f'<img src="{p}" alt="{room["title"]}" class="gallery-img" loading="lazy">' 
                for p in photos
            ])
            gallery_tag = f'''
            <div class="gallery-wrapper">
                <div class="gallery-container">{gallery_inner}</div>
                <div class="photo-counter">📸 {photos_count} фото (листайте вправо)</div>
            </div>
            '''
        else:
            gallery_tag = '<div class="img-placeholder">🏖 Фото базы отдыха «Русалочка»</div>'

        cards_html += f"""
        <div class="card" id="room-{key}">
            {gallery_tag}
            <div class="card-content">
                <div class="badge">🍽 с 3-х разовым питанием</div>
                <h3 class="room-title">{room['title']}</h3>
                <div class="room-meta">
                    <span>👥 {room['capacity']}</span>
                    <span class="price">{room['price']}</span>
                </div>
                <pre class="room-desc">{room['description']}</pre>
                <a href="{BOOKING_URL}" target="_blank" class="book-btn">Забронировать этот номер</a>
            </div>
        </div>
        """

    full_html = f"""<!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>База отдыха «Русалочка» | Номера</title>
        <style>
            * {{ box-sizing: border-box; margin: 0; padding: 0; }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                background-color: #0b1329;
                color: #f1f5f9;
                padding-bottom: 50px;
                line-height: 1.5;
            }}
            header {{
                background: linear-gradient(180deg, #1e293b 0%, #0b1329 100%);
                padding: 24px 16px;
                text-align: center;
                border-bottom: 1px solid #334155;
            }}
            .logo {{
                font-size: 24px;
                font-weight: 800;
                color: #38bdf8;
                margin-bottom: 6px;
            }}
            .subtitle {{
                font-size: 14px;
                color: #94a3b8;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                padding: 16px;
            }}
            .card {{
                background: #1e293b;
                border-radius: 16px;
                overflow: hidden;
                margin-bottom: 24px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.4);
                border: 1px solid #334155;
            }}
            .gallery-wrapper {{
                position: relative;
                background: #0f172a;
            }}
            .gallery-container {{
                display: flex;
                overflow-x: auto;
                scroll-snap-type: x mandatory;
                gap: 10px;
                padding: 12px;
                scrollbar-width: thin;
                scrollbar-color: #38bdf8 #1e293b;
                -webkit-overflow-scrolling: touch;
            }}
            .gallery-container::-webkit-scrollbar {{
                height: 5px;
            }}
            .gallery-container::-webkit-scrollbar-thumb {{
                background: #38bdf8;
                border-radius: 3px;
            }}
            .gallery-img {{
                flex: 0 0 88%;
                height: 230px;
                object-fit: cover;
                border-radius: 12px;
                scroll-snap-align: center;
                display: block;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            }}
            .photo-counter {{
                font-size: 11px;
                color: #94a3b8;
                padding: 0 14px 10px 14px;
                text-align: right;
            }}
            .img-placeholder {{
                width: 100%;
                height: 160px;
                background: #0f172a;
                color: #64748b;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 14px;
                font-weight: 600;
            }}
            .card-content {{
                padding: 18px;
            }}
            .badge {{
                display: inline-block;
                background: #0284c7;
                color: #ffffff;
                font-size: 12px;
                font-weight: 700;
                padding: 4px 10px;
                border-radius: 20px;
                margin-bottom: 10px;
            }}
            .room-title {{
                font-size: 18px;
                font-weight: 700;
                color: #ffffff;
                margin-bottom: 10px;
            }}
            .room-meta {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 14px;
                padding-bottom: 12px;
                border-bottom: 1px dashed #334155;
            }}
            .price {{
                color: #34d399;
                font-weight: 800;
                font-size: 16px;
            }}
            .room-desc {{
                white-space: pre-wrap;
                font-family: inherit;
                font-size: 13px;
                color: #cbd5e1;
                margin-bottom: 18px;
            }}
            .book-btn {{
                display: block;
                text-align: center;
                background: #0284c7;
                color: #ffffff;
                text-decoration: none;
                font-weight: 700;
                font-size: 15px;
                padding: 12px;
                border-radius: 10px;
                transition: background 0.2s;
            }}
            .book-btn:active {{
                background: #0369a1;
            }}
            .footer-info {{
                text-align: center;
                padding: 20px;
                color: #64748b;
                font-size: 12px;
            }}
        </style>
    </head>
    <body>
        <header>
            <div class="logo">Русалочка 🌊</div>
            <div class="subtitle">База отдыха на Черном море (ст. Благовещенская)</div>
        </header>
        <div class="container">
            {cards_html}
            <div class="footer-info">
                База отдыха «Русалочка» • Период работы: с 11 июня по 15 сентября<br>
                Анапа, ст. Благовещенская, ул. Прибрежная, д. 13 • +7 (918) 47-74-366
            </div>
        </div>
    </body>
    </html>"""
    return web.Response(text=full_html, content_type="text/html", status=200)

async def handle_rules_pdf(request: web.Request):
    pdf_path = "rules.pdf"
    if os.path.exists(pdf_path):
        return web.FileResponse(pdf_path)
    return web.Response(text="Файл с правилами не найден на сервере.", status=404)

async def handle_oferta_pdf(request: web.Request):
    pdf_path = "oferta.pdf"
    if os.path.exists(pdf_path):
        return web.FileResponse(pdf_path)
    return web.Response(text="Файл оферты не найден на сервере.", status=404)

async def on_startup(app_instance: web.Application):
    os.makedirs("images", exist_ok=True)
    logging.info("Проверка токена в MAX API...")
    await max_bot.get_me()
    logging.info(f"Регистрируем подписку на Webhook: {WEBHOOK_URL}...")
    await max_bot.setup_subscription(WEBHOOK_URL)

app = web.Application()
app.on_startup.append(on_startup)

os.makedirs("images", exist_ok=True)
app.router.add_static("/images", path="images", name="images")

app.router.add_get("/rules.pdf", handle_rules_pdf)
app.router.add_get("/oferta.pdf", handle_oferta_pdf)

app.router.add_get("/", handle_get)
app.router.add_post("/", handle_webhook)
app.router.add_get("/webhook", handle_get)
app.router.add_post("/webhook", handle_webhook)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    port = int(os.getenv("PORT", 3000))
    logging.info(f"Запуск сервера бота MAX на порту {port}...")
    web.run_app(app, host="0.0.0.0", port=port)
