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
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "0")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://bot-1791222128-3841-dl1xxz.bothost.tech/webhook")
WEBAPP_URL = "https://bot-1791222128-3841-dl1xxz.bothost.tech/"

BOOKING_URL = "https://reservationsteps.ru/rooms/index/8dc26407-5b2f-46e5-8597-ebfc46cf8111?dfrom=15-06-2027&dto=20-06-2027&adults=2&lang=ru"
REVIEWS_URL = "https://yandex.ru/maps/org/rusalochka/241387417775/reviews/?ll=37.156738%2C45.028213&z=11.94"

GEO_LATITUDE = 45.053805
GEO_LONGITUDE = 37.086375

USER_STATES: Dict[str, str] = {}

# Номерной фонд базы отдыха «Русалочка»
ROOMS_CATALOG: Dict[str, Dict[str, Any]] = {
    "kitchen_2p": {
        "title": "Номер с кухней (апарт.) 2-х местный + доп.место",
        "photo": "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=800&q=80",
        "capacity": "до 3 человек",
        "price": "от 4 500 ₽ / сутки",
        "description": (
            "🏡 Номер с кухней (апарт.) 2-х местный + доп.место\n\n"
            "Уютный семейный апартамент с индивидуальной кухонной зоной.\n\n"
            "В номере:\n"
            "• Двуспальная кровать + доп. место (диван / кресло-кровать)\n"
            "• Индивидуальная кухня: плита, СВЧ, холодильник, посуда, электрочайник\n"
            "• Сплит-система, ЖК ТВ, Wi-Fi\n"
            "• Санузел с душевой кабиной\n"
            "• Индивидуальная веранда/балкон для отдыха\n\n"
            "👥 Вместимость: до 3 человек\n"
            "🍽 с 3-х разовым комплексным питанием\n"
            "💰 Стоимость: от 4 500 ₽ / сутки"
        ),
    },
    "kitchen_3p": {
        "title": "Номер с кухней (апарт.) 3-х местный + доп.место",
        "photo": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=800&q=80",
        "capacity": "до 4 человек",
        "price": "от 5 500 ₽ / сутки",
        "description": (
            "🏡 Номер с кухней (апарт.) 3-х местный + доп.место\n\n"
            "Просторный апартамент для комфортного отдыха всей семьей.\n\n"
            "В номере:\n"
            "• Двуспальная кровать, 1-спальная кровать + доп. место\n"
            "• Кухонный модуль: варочная панель, СВЧ, холодильник, посуда, электрочайник\n"
            "• Сплит-система, цифровое ТВ, Wi-Fi\n"
            "• Ванная комната с душем\n"
            "• Просторная веранда\n\n"
            "👥 Вместимость: до 4 человек\n"
            "🍽 с 3-х разовым комплексным питанием\n"
            "💰 Стоимость: от 5 500 ₽ / сутки"
        ),
    },
    "eco_1k_2p": {
        "title": "Эко-домик 1-комнатный 2-х местный + доп.место",
        "photo": "https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?auto=format&fit=crop&w=800&q=80",
        "capacity": "до 3 человек",
        "price": "от 4 000 ₽ / сутки",
        "description": (
            "🏡 Эко-домик 1-комнатный 2-х местный + доп.место\n\n"
            "Отдельный домик из экологически чистого натурального бруса.\n\n"
            "В домике:\n"
            "• Двуспальная кровать + кресло-кровать\n"
            "• Сплит-система, холодильник, электрочайник, телевизор\n"
            "• Собственный санузел с душем\n"
            "• Терраса со столом и стульями на свежем воздухе\n\n"
            "👥 Вместимость: до 3 человек\n"
            "🍽 с 3-х разовым комплексным питанием\n"
            "💰 Стоимость: от 4 000 ₽ / сутки"
        ),
    },
    "eco_2k_3p": {
        "title": "Эко-домик 2-комнатный 3-х местный + доп.место",
        "photo": "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=800&q=80",
        "capacity": "до 4 человек",
        "price": "от 6 000 ₽ / сутки",
        "description": (
            "🏡 Эко-домик 2-комнатный 3-х местный + доп.место\n\n"
            "Двухкомнатный коттедж из бруса для большой семьи.\n\n"
            "В домике:\n"
            "• 2 изолированные спальные комнаты\n"
            "• 3 основных спальных места + евро-раскладушка\n"
            "• Кондиционер, холодильник, ТВ, электрочайник\n"
            "• Санузел с душевой кабиной\n"
            "• Большая деревянная терраса\n\n"
            "👥 Вместимость: до 4 человек\n"
            "🍽 с 3-х разовым комплексным питанием\n"
            "💰 Стоимость: от 6 000 ₽ / сутки"
        ),
    },
    "std_brick_3p": {
        "title": "СТАНДАРТ кирпичный домик 3-х местный",
        "photo": "https://images.unsplash.com/photo-1566665797739-1674de7a421a?auto=format&fit=crop&w=800&q=80",
        "capacity": "до 3 человек",
        "price": "от 3 500 ₽ / сутки",
        "description": (
            "🏡 СТАНДАРТ кирпичный домик 3-х местный\n\n"
            "Капитальный прохладный домик для отдыха 3 человек.\n\n"
            "В домике:\n"
            "• 3 комфортных спальных места\n"
            "• Сплит-система, холодильник, ТВ\n"
            "• Собственный санузел с душем\n"
            "• Индивидуальная веранда перед входом\n\n"
            "👥 Вместимость: до 3 человек\n"
            "🍽 с 3-х разовым комплексным питанием\n"
            "💰 Стоимость: от 3 500 ₽ / сутки"
        ),
    },
    "std_wood_2p": {
        "title": "СТАНДАРТ Деревянный домик 2-х местный",
        "photo": "https://images.unsplash.com/photo-1596394516093-501ba68a0ba6?auto=format&fit=crop&w=800&q=80",
        "capacity": "до 2 человек",
        "price": "от 2 800 ₽ / сутки",
        "description": (
            "🏡 СТАНДАРТ Деревянный домик 2-х местный\n\n"
            "Уютный деревянный домик для двоих в тишине и зелени.\n\n"
            "В домике:\n"
            "• 2 спальных места\n"
            "• Кондиционер, холодильник, ТВ\n"
            "• Санузел с душем\n"
            "• Открытая терраса со столиком\n\n"
            "👥 Вместимость: до 2 человек\n"
            "🍽 с 3-х разовым комплексным питанием\n"
            "💰 Стоимость: от 2 800 ₽ / сутки"
        ),
    },
    "std_2p": {
        "title": "СТАНДАРТ 2-х местный",
        "photo": "https://images.unsplash.com/photo-1618773928121-c32242e63f39?auto=format&fit=crop&w=800&q=80",
        "capacity": "до 2 человек",
        "price": "от 3 000 ₽ / сутки",
        "description": (
            "🏡 СТАНДАРТ 2-х местный\n\n"
            "Классический номер для 2 гостей.\n\n"
            "В номере:\n"
            "• Двуспальная кровать\n"
            "• Сплит-система, ТВ, холодильник\n"
            "• Санузел и душевая\n"
            "• Зона отдыха\n\n"
            "👥 Вместимость: до 2 человек\n"
            "🍽 с 3-х разовым комплексным питанием\n"
            "💰 Стоимость: от 3 000 ₽ / сутки"
        ),
    },
    "std_2p_extra": {
        "title": "СТАНДАРТ 2-х местный + доп.место",
        "photo": "https://images.unsplash.com/photo-1568495248636-6432b97bd949?auto=format&fit=crop&w=800&q=80",
        "capacity": "до 3 человек",
        "price": "от 3 300 ₽ / сутки",
        "description": (
            "🏡 СТАНДАРТ 2-х местный + доп.место\n\n"
            "Номер категории стандарт для семьи до 3 человек.\n\n"
            "В номере:\n"
            "• Двуспальная кровать + доп. место\n"
            "• Сплит-система, телевизор, холодильник\n"
            "• Санузел с душем\n"
            "• Терраса для отдыха\n\n"
            "👥 Вместимость: до 3 человек\n"
            "🍽 с 3-х разовым комплексным питанием\n"
            "💰 Стоимость: от 3 300 ₽ / сутки"
        ),
    },
    "std_3p": {
        "title": "СТАНДАРТ 3-х местный",
        "photo": "https://images.unsplash.com/photo-1591088398332-8a7791972843?auto=format&fit=crop&w=800&q=80",
        "capacity": "до 3 человек",
        "price": "от 3 700 ₽ / сутки",
        "description": (
            "🏡 СТАНДАРТ 3-х местный\n\n"
            "Просторный 3-местный номер стандартной категории.\n\n"
            "В номере:\n"
            "• 3 основных спальных места\n"
            "• Кондиционер, холодильник, телевизор\n"
            "• Санузел с душем\n"
            "• Веранда для вечернего отдыха\n\n"
            "👥 Вместимость: до 3 человек\n"
            "🍽 с 3-х разовым комплексным питанием\n"
            "💰 Стоимость: от 3 700 ₽ / сутки"
        ),
    },
    "std_4p": {
        "title": "СТАНДАРТ 4-х местный + доп.место",
        "photo": "https://images.unsplash.com/photo-1578683010236-d716f9a3f461?auto=format&fit=crop&w=800&q=80",
        "capacity": "до 5 человек",
        "price": "от 4 600 ₽ / сутки",
        "description": (
            "🏡 СТАНДАРТ 4-х местный + доп.место\n\n"
            "Семейный просторный номер на 4–5 гостей.\n\n"
            "В номере:\n"
            "• Спальные места: 4 основных + 1 доп. место\n"
            "• Сплит-система, холодильник, ТВ\n"
            "• Санузел с душем\n"
            "• Собственная летняя веранда\n\n"
            "👥 Вместимость: до 5 человек\n"
            "🍽 с 3-х разовым комплексным питанием\n"
            "💰 Стоимость: от 4 600 ₽ / сутки"
        ),
    },
}

# =====================================================================
# 2. КЛИЕНТ API MAX (OneMe Bot API)
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
                    logging.info(f"Проверка /me в MAX API: статус={resp.status}, ответ={data}")
        except Exception as e:
            logging.error(f"Ошибка вызова /me: {e}")

    async def setup_subscription(self, webhook_target: str) -> None:
        url = f"{self.base_url}/subscriptions"
        payload = {"url": webhook_target}
        try:
            async with ClientSession(connector=self._get_connector()) as session:
                async with session.post(url, headers=self.headers, json=payload) as resp:
                    resp_text = await resp.text()
                    logging.info(f"Регистрация Webhook в MAX (/subscriptions): статус={resp.status}, ответ={resp_text}")
        except Exception as e:
            logging.error(f"Не удалось отправить запрос подписки: {e}")

    async def answer_callback(self, callback_id: str, notification: str = None) -> None:
        if not callback_id:
            return
        url = f"{self.base_url}/answers"
        params = {"callback_id": callback_id}
        payload = {}
        if notification:
            payload["notification"] = notification

        try:
            async with ClientSession(connector=self._get_connector()) as session:
                async with session.post(url, headers=self.headers, params=params, json=payload) as resp:
                    pass
        except Exception as e:
            logging.error(f"Ошибка answer_callback: {e}")

    async def send_message(
        self,
        chat_id: Any,
        text: str = "",
        buttons: List[List[Dict[str, str]]] = None
    ) -> bool:
        url = f"{self.base_url}/messages"
        target_cid = int(chat_id) if str(chat_id).lstrip("-").isdigit() else chat_id
        params = {"chat_id": target_cid}

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
                        new_row.append({"type": "callback", "text": btn_text, "payload": b.get("payload", btn_text)})
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
                async with session.post(url, headers=self.headers, params=params, json=payload) as resp:
                    if resp.status in (200, 201):
                        logging.info(f"✅ Отправлено в чат {chat_id}")
                        return True
                    resp_text = await resp.text()
                    logging.warning(f"Ошибка отправки ({resp.status}): {resp_text}")
                    return False
        except Exception as e:
            logging.error(f"Исключение при отправке сообщения: {e}")
            return False

max_bot = MaxBotClient(BOT_TOKEN, MAX_API_BASE_URL)

# =====================================================================
# 3. КНОПКИ ДЛЯ ЧАТА
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
        [{"text": "📱 Посмотреть фото в Mini Web", "url": f"{WEBAPP_URL}#room-{room_key}"}],
        [{"text": "🛎 Забронировать этот номер", "url": BOOKING_URL}],
        [{"text": "⬅️ Назад к списку", "payload": "menu_rooms"}]
    ]

def get_faq_buttons() -> List[List[Dict[str, str]]]:
    return [
        [{"text": "Во сколько заселение?", "payload": "faq_checkin"}],
        [{"text": "Во сколько выселение из номера?", "payload": "faq_checkout"}],
        [{"text": "При бронировании нужно вносить предоплату?", "payload": "faq_prepayment"}],
        [{"text": "Предоплата возвратная?", "payload": "faq_refund"}],
        [{"text": "Возможно размещение с животными?", "payload": "faq_pets"}],
        [{"text": "📄 Посмотреть правила (PDF)", "payload": "faq_pdf"}],
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

    logging.info(f"--- ВХОДЯЩИЙ WEBHOOK MAX ---: {data}")

    update_type = data.get("update_type", "")
    message = data.get("message", {})
    body = message.get("body", {})
    recipient = message.get("recipient", {})
    sender = message.get("sender", {}) or data.get("user", {})
    callback = data.get("callback", {})
    callback_id = callback.get("callback_id")

    if callback_id:
        await max_bot.answer_callback(callback_id)

    chat_id = (
        recipient.get("chat_id")
        or message.get("chat_id")
        or callback.get("chat_id")
        or data.get("chat_id")
    )
    user_id = str(
        sender.get("user_id")
        or callback.get("user_id")
        or data.get("user_id")
        or ""
    )
    sender_name = sender.get("name") or sender.get("first_name") or "Гость"

    text = (body.get("text") or message.get("text") or "").strip()
    payload = callback.get("payload") or data.get("payload") or ""

    if not chat_id:
        return web.json_response({"status": "ok"})

    chat_id_str = str(chat_id)

    async def reply(msg_text: str, btns: list = None):
        return await max_bot.send_message(
            chat_id=chat_id,
            text=msg_text,
            buttons=btns
        )

    # 1. Ответ администратора из группы поддержки
    if ADMIN_CHAT_ID != "0" and chat_id_str == str(ADMIN_CHAT_ID):
        reply_to = message.get("reply_to", {})
        reply_body = reply_to.get("body", {})
        reply_text = reply_body.get("text", "") or reply_to.get("text", "")
        match = re.search(r"#user_(\d+)", reply_text)
        if match:
            target_chat_id = match.group(1)
            admin_answer = f"💬 Ответ от администрации базы отдыха «Русалочка»:\n\n{text}"
            await max_bot.send_message(chat_id=target_chat_id, text=admin_answer)
            await reply("✅ Ответ успешно доставлен гостю!")
            return web.json_response({"status": "ok"})

    # 2. Обработка ввода вопроса гостем
    if USER_STATES.get(user_id) == "waiting_feedback":
        if payload == "cancel_feedback" or text.lower() in ["отмена", "❌ отменить вопрос"]:
            USER_STATES.pop(user_id, None)
            await reply("Отправка вопроса отменена.", get_main_menu_buttons())
            return web.json_response({"status": "ok"})

        USER_STATES.pop(user_id, None)
        await reply(
            "✅ Ваш вопрос передан администраторам базы отдыха «Русалочка»!\n\nМы ответим вам прямо в этот диалог в ближайшее время.",
            get_main_menu_buttons()
        )

        if ADMIN_CHAT_ID != "0":
            admin_ticket = (
                f"📩 НОВЫЙ ВОПРОС ОТ ГОСТЯ В MAX\n"
                f"👤 Гость: {sender_name}\n"
                f"🆔 ID: {chat_id_str}\n\n"
                f"💬 Вопрос:\n{text}\n\n"
                f"👉 Чтобы ответить гостю, ответьте цитатой (Reply) на это сообщение.\n"
                f"#user_{chat_id_str}"
            )
            await max_bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_ticket)
        return web.json_response({"status": "ok"})

    # 3. Старт / Приветствие
    is_start = (
        text.startswith("/start")
        or text.lower() in ["привет", "здравствуйте", "старт", "начать"]
        or payload == "menu_root"
        or update_type in ["bot_started", "chat_started"]
    )

    if is_start:
        welcome_text = (
            "Добро пожаловать в базу отдыха «Русалочка»! 🌊\n\n"
            "Отдых на первой береговой линии Черного моря (Анапа, станица Благовещенская).\n"
            "Ухоженная территория, уютные эко-домики и номера с оборудованной кухней!\n\n"
            "📅 Период работы: с 15 июня по 15 сентября\n"
            "🕒 Заезд — с 13:00 | Выезд — до 11:00\n\n"
            "Нажмите «📱 Витрина с фото номеров», чтобы открыть интерактивный каталог с фотографиями ⬇️"
        )
        await reply(welcome_text, get_main_menu_buttons())
        return web.json_response({"status": "ok"})

    elif text == "🏡 Наши номера" or payload == "menu_rooms":
        rooms_text = "🏡 Номерной фонд базы отдыха «Русалочка»:\n\nВыберите категорию или откройте визуальную витрину с фото:"
        await reply(rooms_text, get_rooms_list_buttons())

    elif payload.startswith("view_room_"):
        room_key = payload.replace("view_room_", "")
        room = ROOMS_CATALOG.get(room_key)
        if room:
            await reply(
                msg_text=room["description"],
                btns=get_single_room_buttons(room_key)
            )

    elif text == "📝 Забронировать" or payload == "menu_book":
        book_info = (
            "📝 Онлайн-бронирование номеров\n\n"
            "В нашем официальном модуле вы можете в реальном времени выбрать удобные даты, "
            "проверить наличие свободных мест и мгновенно забронировать проживание!\n\n"
            "📌 Условия бронирования:\n"
            "• Период работы: с 15 июня по 15 сентября\n"
            "• Заезд: с 13:00 | Выезд: до 11:00\n"
            "• Предоплата: 30% от общей стоимости\n"
            "• Бесплатная отмена: возможна за 14 дней до заезда"
        )
        buttons = [
            [{"text": "💳 Перейти к бронированию и оплате", "url": BOOKING_URL}],
            [{"text": "⬅️ В главное меню", "payload": "menu_root"}]
        ]
        await reply(book_info, buttons)

    elif text == "🎡 Инфраструктура и услуги" or payload == "menu_infra":
        infra_text = (
            "🎡 ИНФРАСТРУКТУРА И УСЛУГИ\n\n"
            "✅ ВКЛЮЧЕНО В СТОИМОСТЬ:\n"
            "• 👶 Детская игровая площадка\n"
            "• ⚽ Настольный теннис, футбол, шахматы, спортинвентарь\n"
            "• 🥩 Оборудованная мангальная зона (решетки, шампуры, печь, казан 12 л)\n"
            "• 🌸 Зеленая ухоженная территория (350 кустов роз, 1100 кустов лаванды)\n\n"
            "💲 ДОПОЛНИТЕЛЬНО:\n"
            "• 🎨 Творческие мастер-классы и шоу\n"
            "• 🧺 Прачечная и гладильная комната\n"
            "• ⚡ Зарядная станция GB/T 7 кВт для электромобилей (22 ₽ / кВт·ч)"
        )
        await reply(infra_text, get_main_menu_buttons())

    elif text == "🌴 О базе" or payload == "menu_about":
        about_text = (
            "🌴 База отдыха «Русалочка»\n\n"
            "• Чистейший широкий песчаный пляж Черного моря\n"
            "• Охраняемая закрытая зеленая территория\n"
            "• Комплексное 3-разовое питание включено во все категории номеров\n"
            "• Период сезона: с 15 июня по 15 сентября\n"
            "• Официальный сайт: https://rusalo4ka.com/"
        )
        buttons = [
            [{"text": "🌐 Перейти на сайт rusalo4ka.com", "url": "https://rusalo4ka.com/"}],
            [{"text": "⬅️ В главное меню", "payload": "menu_root"}]
        ]
        await reply(about_text, buttons)

    elif text == "⭐ Отзывы" or payload == "menu_reviews":
        buttons = [
            [{"text": "⭐ Открыть отзывы на Яндекс.Картах", "url": REVIEWS_URL}],
            [{"text": "⬅️ В главное меню", "payload": "menu_root"}]
        ]
        await reply("⭐ Отзывы наших гостей на Яндекс.Картах:", buttons)

    elif text == "📞 Контакты и локация" or payload == "menu_contacts":
        contacts_text = (
            "📞 Контакты базы отдыха «Русалочка»:\n\n"
            "📍 Адрес: Краснодарский край, г. Анапа, ст. Благовещенская, б/о «Русалочка»\n"
            "📞 Отдел бронирования: +7 (918) 47-74-366\n"
            "✉️ E-mail: anaparusalochka@rambler.ru\n"
            "🌐 Сайт: https://rusalo4ka.com/\n\n"
            f"📍 Координаты навигатора: {GEO_LATITUDE}, {GEO_LONGITUDE}"
        )
        buttons = [
            [{"text": "📄 Посмотреть правила (PDF)", "payload": "faq_pdf"}],
            [{"text": "💬 Задать вопрос в чате", "payload": "menu_feedback"}],
            [{"text": "⬅️ В главное меню", "payload": "menu_root"}]
        ]
        await reply(contacts_text, buttons)

    elif text == "❓ Вопросы и ответы (FAQ)" or payload == "menu_faq":
        await reply("Часто задаваемые вопросы:", get_faq_buttons())

    elif payload == "faq_checkin":
        ans = "Во сколько заселение?\n\n— с 13:00, но если Вы приедете раньше и ваш номер будет уже свободен, мы заселим Вас раньше."
        await reply(ans, [[{"text": "⬅️ Назад в FAQ", "payload": "menu_faq"}]])

    elif payload == "faq_checkout":
        ans = "Во сколько выселение?\n\n— освободить номер нужно до 11:00, ключи и браслеты сдаются в администрацию."
        await reply(ans, [[{"text": "⬅️ Назад в FAQ", "payload": "menu_faq"}]])

    elif payload == "faq_prepayment":
        ans = "При бронировании нужно вносить предоплату?\n\n— бронирование выбранной категории номера производится после перечисления предоплаты (30% от полной стоимости проживания)."
        await reply(ans, [[{"text": "⬅️ Назад в FAQ", "payload": "menu_faq"}]])

    elif payload == "faq_refund":
        ans = "Предоплата возвратная?\n\n— бесплатная отмена бронирования возможна за 14 дней до заезда, после — взимается 100% от суммы предоплаты."
        await reply(ans, [[{"text": "⬅️ Назад в FAQ", "payload": "menu_faq"}]])

    elif payload == "faq_pets":
        ans = (
            "Возможно размещение с животными?\n\n"
            "— Разрешено исключительно с декоративными собаками весом до 6 кг в категории «Номер с кухней эко».\n"
            "— Тариф: 800 руб./сутки.\n"
            "— Выгул собак по территории базы запрещен."
        )
        buttons = [
            [{"text": "📄 Посмотреть полные правила", "payload": "faq_pdf"}],
            [{"text": "⬅️ Назад в FAQ", "payload": "menu_faq"}]
        ]
        await reply(ans, buttons)

    elif payload == "faq_pdf":
        await reply(
            "📄 Официальные правила проживания на базе отдыха «Русалочка» доступны на сайте:\nhttps://rusalo4ka.com/",
            [[{"text": "⬅️ Назад в FAQ", "payload": "menu_faq"}]]
        )

    elif text == "💬 Остались вопросы? Напишите нам" or payload == "menu_feedback":
        USER_STATES[user_id] = "waiting_feedback"
        prompt = (
            "💬 Задать вопрос администратору базы отдыха\n\n"
            "Напишите ваш вопрос следующим сообщением. Мы получим его и ответим вам прямо в этот диалог!"
        )
        await reply(prompt, get_cancel_buttons())

    return web.json_response({"status": "ok"})

# =====================================================================
# 5. ВСТРОЕННОЕ MINI WEB APP С ФОТОГРАФИЯМИ И КАТАЛОГОМ
# =====================================================================
async def handle_get(request: web.Request):
    cards_html = ""
    for key, room in ROOMS_CATALOG.items():
        cards_html += f"""
        <div class="card" id="room-{key}">
            <img src="{room['photo']}" alt="{room['title']}" class="room-img" loading="lazy">
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
        <title>База отдыха «Русалочка» | Фото номеров</title>
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
            .room-img {{
                width: 100%;
                height: 220px;
                object-fit: cover;
                display: block;
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
                База отдыха «Русалочка» • Период работы: с 15 июня по 15 сентября<br>
                Анапа, ст. Благовещенская • +7 (918) 47-74-366
            </div>
        </div>
    </body>
    </html>"""
    return web.Response(text=full_html, content_type="text/html", status=200)

async def on_startup(app_instance: web.Application):
    logging.info("Проверка токена в MAX API...")
    await max_bot.get_me()
    logging.info(f"Регистрируем подписку на Webhook: {WEBHOOK_URL}...")
    await max_bot.setup_subscription(WEBHOOK_URL)

app = web.Application()
app.on_startup.append(on_startup)

app.router.add_get("/", handle_get)
app.router.add_post("/", handle_webhook)
app.router.add_get("/webhook", handle_get)
app.router.add_post("/webhook", handle_webhook)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    port = int(os.getenv("PORT", 3000))
    logging.info(f"Запуск сервера бота MAX на порту {port}...")
    web.run_app(app, host="0.0.0.0", port=port)
