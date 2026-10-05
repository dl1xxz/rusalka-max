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

BOOKING_URL = "https://reservationsteps.ru/rooms/index/8dc26407-5b2f-46e5-8597-ebfc46cf8111?dfrom=15-06-2027&dto=20-06-2027&adults=2&lang=ru"
REVIEWS_URL = "https://yandex.ru/maps/org/rusalochka/241387417775/reviews/?ll=37.156738%2C45.028213&z=11.94"

GEO_LATITUDE = 45.053805
GEO_LONGITUDE = 37.086375

USER_STATES: Dict[str, str] = {}

# Каталог номеров базы отдыха «Русалочка» с прямыми ссылками на фотографии
ROOMS_CATALOG: Dict[str, Dict[str, Any]] = {
    "kitchen_2p": {
        "title": "Номер с кухней (апарт.) 2-х местный + доп.место",
        "photo_url": "https://rusalo4ka.com/images/rooms/apart-2p.jpg",
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
        "photo_url": "https://rusalo4ka.com/images/rooms/apart-3p.jpg",
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
        "photo_url": "https://rusalo4ka.com/images/rooms/eco-1k-2p.jpg",
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
        "photo_url": "https://rusalo4ka.com/images/rooms/eco-2k-3p.jpg",
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
        "photo_url": "https://rusalo4ka.com/images/rooms/std-brick-3p.jpg",
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
        "photo_url": "https://rusalo4ka.com/images/rooms/std-wood-2p.jpg",
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
        "photo_url": "https://rusalo4ka.com/images/rooms/std-2p.jpg",
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
        "photo_url": "https://rusalo4ka.com/images/rooms/std-2p-extra.jpg",
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
        "photo_url": "https://rusalo4ka.com/images/rooms/std-3p.jpg",
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
        "photo_url": "https://rusalo4ka.com/images/rooms/std-4p.jpg",
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
        chat_id: Optional[Any] = None,
        user_id: Optional[Any] = None,
        text: str = "",
        buttons: List[List[Dict[str, str]]] = None,
        photo_url: Optional[str] = None
    ) -> bool:
        url = f"{self.base_url}/messages"

        attachments = []

        # 1. Прикрепление фото
        if photo_url:
            attachments.append({
                "type": "image",
                "payload": {
                    "url": photo_url
                }
            })

        # 2. Прикрепление клавиатуры
        if buttons:
            max_buttons = []
            for row in buttons:
                new_row = []
                for b in row:
                    btn_text = b.get("text", "")
                    if "url" in b:
                        new_row.append({
                            "type": "link",
                            "text": btn_text,
                            "url": b["url"]
                        })
                    else:
                        new_row.append({
                            "type": "callback",
                            "text": btn_text,
                            "payload": b.get("payload", btn_text)
                        })
                max_buttons.append(new_row)

            attachments.append({
                "type": "inline_keyboard",
                "payload": {
                    "buttons": max_buttons
                }
            })

        payload = {"text": text}
        if attachments:
            payload["attachments"] = attachments

        try:
            async with ClientSession(connector=self._get_connector()) as session:
                # Отправка по user_id (личка)
                if user_id:
                    target_uid = int(user_id) if str(user_id).isdigit() else user_id
                    async with session.post(url, headers=self.headers, params={"user_id": target_uid}, json=payload) as resp:
                        if resp.status in (200, 201):
                            logging.info(f"✅ Сообщение успешно отправлено через ?user_id={target_uid}")
                            return True
                        resp_text = await resp.text()
                        logging.warning(f"Ошибка отправки ?user_id={target_uid} ({resp.status}): {resp_text}")

                # Отправка по chat_id (группа/диалог)
                if chat_id:
                    target_cid = int(chat_id) if str(chat_id).lstrip("-").isdigit() else chat_id
                    async with session.post(url, headers=self.headers, params={"chat_id": target_cid}, json=payload) as resp:
                        if resp.status in (200, 201):
                            logging.info(f"✅ Сообщение успешно отправлено через ?chat_id={target_cid}")
                            return True
                        resp_text = await resp.text()
                        logging.warning(f"Ошибка отправки ?chat_id={target_cid} ({resp.status}): {resp_text}")

                return False
        except Exception as e:
            logging.error(f"Исключение при отправке сообщения в MAX: {e}")
            return False

max_bot = MaxBotClient(BOT_TOKEN, MAX_API_BASE_URL)

# =====================================================================
# 3. КНОПКИ
# =====================================================================
def get_main_menu_buttons() -> List[List[Dict[str, str]]]:
    return [
        [{"text": "🏡 Наши номера", "payload": "menu_rooms"}, {"text": "📝 Забронировать", "payload": "menu_book"}],
        [{"text": "🌴 О базе", "payload": "menu_about"}, {"text": "🎡 Инфраструктура и услуги", "payload": "menu_infra"}],
        [{"text": "⭐ Отзывы", "payload": "menu_reviews"}, {"text": "❓ Вопросы и ответы (FAQ)", "payload": "menu_faq"}],
        [{"text": "📞 Контакты и локация", "payload": "menu_contacts"}],
        [{"text": "💬 Остались вопросы? Напишите нам", "payload": "menu_feedback"}]
    ]

def get_cancel_buttons() -> List[List[Dict[str, str]]]:
    return [[{"text": "❌ Отменить вопрос", "payload": "cancel_feedback"}]]

def get_rooms_list_buttons() -> List[List[Dict[str, str]]]:
    buttons = []
    for key, data in ROOMS_CATALOG.items():
        buttons.append([{"text": f"🏡 {data['title']}", "payload": f"view_room_{key}"}])
    buttons.append([{"text": "⬅️️ В главное меню", "payload": "menu_root"}])
    return buttons

def get_single_room_buttons() -> List[List[Dict[str, str]]]:
    return [
        [{"text": "🛎 Забронировать этот номер", "url": BOOKING_URL}],
        [{"text": "⬅️ Назад к номерам", "payload": "menu_rooms"}]
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
    user_id = (
        sender.get("user_id")
        or callback.get("user_id")
        or data.get("user_id")
    )
    sender_name = sender.get("name") or sender.get("first_name") or "Гость"

    text = (body.get("text") or message.get("text") or "").strip()
    payload = callback.get("payload") or data.get("payload") or ""

    if not chat_id and not user_id:
        return web.json_response({"status": "ok"})

    user_id_str = str(user_id) if user_id else ""
    chat_id_str = str(chat_id) if chat_id else ""

    async def reply(msg_text: str, btns: list = None, photo: str = None):
        return await max_bot.send_message(
            chat_id=chat_id,
            user_id=user_id,
            text=msg_text,
            buttons=btns,
            photo_url=photo
        )

    # 1. Ответ администратора из группы поддержки MAX (через цитирование)
    if ADMIN_CHAT_ID != "0" and chat_id_str == str(ADMIN_CHAT_ID):
        reply_to = message.get("reply_to", {})
        reply_body = reply_to.get("body", {})
        reply_text = reply_body.get("text", "") or reply_to.get("text", "")
        match = re.search(r"#user_(\d+)", reply_text)
        if match:
            target_user_id = match.group(1)
            admin_answer = f"💬 Ответ от администрации базы отдыха «Русалочка»:\n\n{text}"
            await max_bot.send_message(user_id=target_user_id, text=admin_answer)
            await reply("✅ Ответ успешно доставлен гостю!")
            return web.json_response({"status": "ok"})

    # 2. Обработка ввода вопроса гостем
    if USER_STATES.get(user_id_str) == "waiting_feedback":
        if payload == "cancel_feedback" or text.lower() in ["отмена", "❌ отменить вопрос"]:
            USER_STATES.pop(user_id_str, None)
            await reply("Отправка вопроса отменена.", get_main_menu_buttons())
            return web.json_response({"status": "ok"})

        USER_STATES.pop(user_id_str, None)
        await reply(
            "✅ Ваш вопрос передан администраторам базы отдыха «Русалочка»!\n\nМы ответим вам прямо в этот диалог в ближайшее время.",
            get_main_menu_buttons()
        )

        if ADMIN_CHAT_ID != "0":
            admin_ticket = (
                f"📩 НОВЫЙ ВОПРОС ОТ ГОСТЯ В MAX\n"
                f"👤 Гость: {sender_name}\n"
                f"🆔 ID: {user_id_str}\n\n"
                f"💬 Вопрос:\n{text}\n\n"
                f"👉 Чтобы ответить гостю, ответьте цитатой (Reply) на это сообщение.\n"
                f"#user_{user_id_str}"
            )
            await max_bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_ticket)
        return web.json_response({"status": "ok"})

    # 3. Реакция на старт (/start, приветствие или переход в главное меню)
    is_start = (
        text.startswith("/start")
        or text.lower() in ["привет", "здравствуйте", "старт", "начать"]
        or payload == "menu_root"
        or update_type in ["bot_started", "chat_started"]
    )

    if is_start:
        welcome_text = (
            "Добро пожаловать в базу отдыха «Русалочка»! 🌊\n\n"
            "Отдых на песчаном побережье Черного моря (Анапа, ст. Благовещенская).\n"
            "Ухоженная зеленая территория, уютные эко-домики и номера с оборудованной кухней!\n\n"
            "📅 Период работы: с 15 июня по 15 сентября\n"
            "🕒 Заезд — с 13:00 | Выезд — до 11:00\n\n"
            "Ознакомьтесь с номерным фондом и услугами базы в меню ниже ⬇️"
        )
        await reply(welcome_text, get_main_menu_buttons())
        return web.json_response({"status": "ok"})

    elif text == "🏡 Наши номера" or payload == "menu_rooms":
        rooms_text = "🏡 Номерной фонд базы отдыха «Русалочка»:\n\nВыберите категорию для просмотра описания и стоимости:"
        await reply(rooms_text, get_rooms_list_buttons())

    elif payload.startswith("view_room_"):
        room_key = payload.replace("view_room_", "")
        room = ROOMS_CATALOG.get(room_key)
        if room:
            await reply(
                msg_text=room["description"],
                btns=get_single_room_buttons(),
                photo=room.get("photo_url")
            )

    elif text == "📝 Забронировать" or payload == "menu_book":
        book_info = (
            "📝 Онлайн-бронирование номеров\n\n"
            "В нашем официальном модуле бронирования вы можете в реальном времени выбрать удобные даты отдыха, "
            "узнать актуальное наличие свободных номеров и моментально оформить бронь с гарантией!\n\n"
            "📌 Условия проживания:\n"
            "• Период работы: с 15 июня по 15 сентября\n"
            "• Заезд: с 13:00 | Выезд: до 11:00\n"
            "• Предоплата для брони: 30.00% от стоимости\n"
            "• Остаток: оплачивается при заселении\n"
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
            "✅ ВКЛЮЧЕНО В СТОИМОСТЬ:\n\n"
            "👶 Детская площадка\n"
            "⚽ Спортивный инвентарь (теннис, футбол, шахматы)\n"
            "🥩 Мангальная зона (решетки, шампуры, печь, казан 12 л)\n"
            "🌸 Зеленая зона: 350 кустов роз и 1100 кустов лаванды\n\n"
            "------------------------------------\n\n"
            "💲 ДОПОЛНИТЕЛЬНЫЕ УСЛУГИ:\n\n"
            "🎨 Студия творчества и мастер-классы\n"
            "🧺 Прачечная и гладильная комната\n"
            "⚡ Зарядная станция для электромобилей GB/T 7kwt (Цена 22₽ / 1 кВт.ч)."
        )
        await reply(infra_text, get_main_menu_buttons())

    elif text == "🌴 О базе" or payload == "menu_about":
        about_text = (
            "🌴 База отдыха «Русалочка»\n\n"
            "• Закрытая охраняемая зеленая территория\n"
            "• Шаговая доступность к просторному пляжу и теплому морю\n"
            "• Детский игровой комплекс, анимация и уютная атмосфера\n"
            "• Период работы: с 15 июня по 15 сентября\n"
            "• Сайт: https://rusalo4ka.com/"
        )
        buttons = [
            [{"text": "🌐 Открыть сайт rusalo4ka.com", "url": "https://rusalo4ka.com/"}],
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
        ans = "Во сколько заселение?\n\n— с 13:00, но если Вы приедете раньше и ваш номер будет уже свободен, мы Вас заселим раньше."
        await reply(ans, [[{"text": "⬅️ Назад в FAQ", "payload": "menu_faq"}]])

    elif payload == "faq_checkout":
        ans = "Во сколько выселение из номера?\n\n— освободить номер нужно до 11:00, ключи, брелоки и браслеты от номера нужно сдать в администрации."
        await reply(ans, [[{"text": "⬅️️ Назад в FAQ", "payload": "menu_faq"}]])

    elif payload == "faq_prepayment":
        ans = "При бронировании нужно вносить предоплату?\n\n— бронирование выбранной категории номера (домика) производится после перечисления предоплаты (30% от полной стоимости проживания)."
        await reply(ans, [[{"text": "⬅️ Назад в FAQ", "payload": "menu_faq"}]])

    elif payload == "faq_refund":
        ans = "Предоплата возвратная?\n\n— бесплатная отмена бронирования возможна за 14 дней до забронированной даты, после - взимается 100% от размера предоплаты. В экстренном случае обращайтесь на электронную почту."
        await reply(ans, [[{"text": "⬅️ Назад в FAQ", "payload": "menu_faq"}]])

    elif payload == "faq_pets":
        ans = (
            "Возможно размещение с животными?\n\n"
            "— Возможность размещения исключительно с декоративными собаками, весом до 6 кг., предусмотрена в номерах категории «Номер с кухней (апарт.)» эко.\n\n"
            "— Тариф на размещение: 800 руб./сутки.\n\n"
            "— Выгул собак на территории Базы отдыха «Русалочка» ЗАПРЕЩЕН."
        )
        buttons = [
            [{"text": "📄 Посмотреть правила", "payload": "faq_pdf"}],
            [{"text": "⬅️ Назад в FAQ", "payload": "menu_faq"}]
        ]
        await reply(ans, buttons)

    elif payload == "faq_pdf":
        await reply(
            "📄 Официальные правила проживания на базе отдыха «Русалочка» доступны на сайте:\nhttps://rusalo4ka.com/",
            [[{"text": "⬅️ Назад в FAQ", "payload": "menu_faq"}]]
        )

    elif text == "💬 Остались вопросы? Напишите нам" or payload == "menu_feedback":
        USER_STATES[user_id_str] = "waiting_feedback"
        prompt = (
            "💬 Задать вопрос администратору базы отдыха\n\n"
            "Напишите ваш вопрос следующим сообщением. Мы получим его и ответим вам прямо в этот диалог!"
        )
        await reply(prompt, get_cancel_buttons())

    return web.json_response({"status": "ok"})

# =====================================================================
# 5. GET ДЛЯ ПРОВЕРКИ СЕРВЕРА
# =====================================================================
async def handle_get(request: web.Request):
    html_page = """<!DOCTYPE html>
    <html lang="ru">
    <head><meta charset="UTF-8"><title>Русалочка</title></head>
    <body style="font-family: sans-serif; background: #0f172a; color: white; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0;">
        <div style="background: #1e293b; padding: 30px; border-radius: 16px; text-align: center;">
            <h2>База отдыха «Русалочка» 🌊</h2>
            <p style="color: #94a3b8;">Сервер активен (200 OK)</p>
        </div>
    </body>
    </html>"""
    return web.Response(text=html_page, content_type="text/html", status=200)

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
