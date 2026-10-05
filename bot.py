import os
import re
import logging
from typing import Dict, Any, List

from aiohttp import web, ClientSession
from dotenv import load_dotenv

# =====================================================================
# 1. КОНФИГУРАЦИЯ И ДАННЫЕ
# =====================================================================
load_dotenv()

# Токен доступа платформы MAX
BOT_TOKEN = os.getenv(
    "BOT_TOKEN",
    "f9LHodD0cOK6F9nc6kr6ky0CWdnWdY9doCzwFElXkNvqdkMKOlNNs7YZi8RcPk3linYFzlw3qGBXIWOmocDY"
)
MAX_API_BASE_URL = os.getenv("MAX_API_BASE_URL", "https://api.max.ru/v1")

# ID группы администраторов в MAX (0 — по умолчанию, пока не пойман в логах)
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "0")

BOOKING_URL = "https://reservationsteps.ru/rooms/index/8dc26407-5b2f-46e5-8597-ebfc46cf8111?dfrom=15-06-2027&dto=20-06-2027&adults=2&lang=ru"
REVIEWS_URL = "https://yandex.ru/maps/org/rusalochka/241387417775/reviews/?ll=37.156738%2C45.028213&z=11.94"
PDF_RULES_PATH = "rules.pdf"

GEO_LATITUDE = 45.053805
GEO_LONGITUDE = 37.086375

USER_STATES: Dict[str, str] = {}

# Каталог номеров базы отдыха «Русалочка»
ROOMS_CATALOG: Dict[str, Dict[str, Any]] = {
    "kitchen_2p": {
        "title": "Номер с кухней (апарт.) 2-х местный + доп.место",
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
# 2. КЛИЕНТ API MAX
# =====================================================================
class MaxBotClient:
    def __init__(self, token: str, base_url: str):
        self.token = token
        self.base_url = base_url.rstrip("/")

    async def send_message(
        self,
        chat_id: str,
        text: str,
        buttons: List[List[Dict[str, str]]] = None,
        keyboard_type: str = "reply"
    ) -> bool:
        url = f"{self.base_url}/messages.send"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        payload = {"chat_id": chat_id, "text": text}
        if buttons:
            payload["keyboard"] = {"type": keyboard_type, "buttons": buttons}

        try:
            async with ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as resp:
                    return resp.status == 200
        except Exception as e:
            logging.error(f"Ошибка отправки сообщения: {e}")
            return False

    async def send_document(self, chat_id: str, file_path: str, caption: str = "") -> bool:
        url = f"{self.base_url}/messages.sendDocument"
        headers = {"Authorization": f"Bearer {self.token}"}

        if not os.path.exists(file_path):
            return await self.send_message(
                chat_id=chat_id,
                text=f"{caption}\n(Официальные правила доступны на сайте: https://rusalo4ka.com/)",
                keyboard_type="inline"
            )

        try:
            data = web.FormData()
            data.add_field('chat_id', str(chat_id))
            data.add_field('caption', caption)
            data.add_field('document', open(file_path, 'rb'), filename=os.path.basename(file_path))

            async with ClientSession() as session:
                async with session.post(url, headers=headers, data=data) as resp:
                    return resp.status == 200
        except Exception as e:
            logging.error(f"Ошибка отправки файла: {e}")
            return False

max_bot = MaxBotClient(BOT_TOKEN, MAX_API_BASE_URL)

# =====================================================================
# 3. КЛАВИАТУРЫ
# =====================================================================
def get_main_menu_reply_keyboard() -> List[List[Dict[str, str]]]:
    return [
        [{"text": "🏡 Наши номера", "payload": "menu_rooms"}, {"text": "📝 Забронировать", "payload": "menu_book"}],
        [{"text": "🌴 О базе", "payload": "menu_about"}, {"text": "🎡 Инфраструктура и услуги", "payload": "menu_infra"}],
        [{"text": "⭐ Отзывы", "payload": "menu_reviews"}, {"text": "❓ Вопросы и ответы (FAQ)", "payload": "menu_faq"}],
        [{"text": "📞 Контакты и локация", "payload": "menu_contacts"}],
        [{"text": "💬 Остались вопросы? Напишите нам", "payload": "menu_feedback"}]
    ]

def get_cancel_reply_keyboard() -> List[List[Dict[str, str]]]:
    return [[{"text": "❌ Отменить вопрос", "payload": "cancel_feedback"}]]

def get_rooms_list_inline_buttons() -> List[List[Dict[str, str]]]:
    buttons = []
    for key, data in ROOMS_CATALOG.items():
        buttons.append([{"text": f"🏡 {data['title']}", "payload": f"view_room_{key}"}])
    buttons.append([{"text": "⬅️ В главное меню", "payload": "menu_root"}])
    return buttons

def get_single_room_inline_buttons() -> List[List[Dict[str, str]]]:
    return [
        [{"text": "🛎 Забронировать этот номер", "url": BOOKING_URL}],
        [{"text": "⬅️ Назад к номерам", "payload": "menu_rooms"}]
    ]

def get_faq_inline_buttons() -> List[List[Dict[str, str]]]:
    return [
        [{"text": "Во сколько заселение?", "payload": "faq_checkin"}],
        [{"text": "Во сколько выселение из номера?", "payload": "faq_checkout"}],
        [{"text": "При бронировании нужно вносить предоплату?", "payload": "faq_prepayment"}],
        [{"text": "Предоплата возвратная?", "payload": "faq_refund"}],
        [{"text": "Возможно размещение с животными?", "payload": "faq_pets"}],
        [{"text": "📄 Посмотреть полные правила (PDF)", "payload": "faq_pdf"}],
        [{"text": "💬 Задать свой вопрос", "payload": "menu_feedback"}],
        [{"text": "⬅️ В главное меню", "payload": "menu_root"}]
    ]

# =====================================================================
# 4. ОБРАБОТЧИК WEBHOOK (POST)
# =====================================================================
async def handle_webhook(request: web.Request):
    try:
        data = await request.json()
    except Exception:
        return web.Response(status=400)

    # Логирование входящих данных для BotHost
    logging.info(f"--- ВХОДЯЩИЙ WEBHOOK MAX ---: {data}")

    event_type = data.get("type", "")
    message = data.get("message", {})
    chat_id = str(message.get("chat_id") or data.get("chat_id") or "")
    sender = message.get("from", {})
    sender_id = str(sender.get("id") or "")
    sender_name = sender.get("name") or "Гость"
    text = (message.get("text") or "").strip()
    payload = data.get("payload") or message.get("payload") or ""

    if not chat_id:
        return web.Response(text="OK")

    # 1. Ответ администратора из группы поддержки (через Reply)
    if ADMIN_CHAT_ID != "0" and chat_id == str(ADMIN_CHAT_ID):
        reply_to = message.get("reply_to", {})
        reply_text = reply_to.get("text", "")
        match = re.search(r"#user_(\d+)", reply_text)
        if match:
            target_user_id = match.group(1)
            admin_answer = f"💬 Ответ от администрации базы отдыха «Русалочка»:\n\n{text}"
            await max_bot.send_message(chat_id=target_user_id, text=admin_answer, keyboard_type="reply")
            await max_bot.send_message(chat_id=chat_id, text="✅ Ответ успешно доставлен гостю!", keyboard_type="inline")
            return web.Response(text="OK")

    # 2. Обработка ввода вопроса гостем
    if USER_STATES.get(sender_id) == "waiting_feedback":
        if payload == "cancel_feedback" or text.lower() in ["отмена", "❌ отменить вопрос"]:
            USER_STATES.pop(sender_id, None)
            await max_bot.send_message(
                chat_id=chat_id,
                text="Отправка вопроса отменена.",
                buttons=get_main_menu_reply_keyboard(),
                keyboard_type="reply"
            )
            return web.Response(text="OK")

        USER_STATES.pop(sender_id, None)
        await max_bot.send_message(
            chat_id=chat_id,
            text="✅ Ваш вопрос передан администраторам базы отдыха «Русалочка»!\n\nМы ответим вам прямо в этот диалог в ближайшее время.",
            buttons=get_main_menu_reply_keyboard(),
            keyboard_type="reply"
        )

        if ADMIN_CHAT_ID != "0":
            admin_ticket = (
                f"📩 НОВЫЙ ВОПРОС ОТ ГОСТЯ В MAX\n"
                f"👤 Гость: {sender_name}\n"
                f"🆔 ID: {sender_id}\n\n"
                f"💬 Вопрос:\n{text}\n\n"
                f"👉 Чтобы ответить гостю, ответьте цитатой (Reply) на это сообщение.\n"
                f"#user_{sender_id}"
            )
            await max_bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_ticket, keyboard_type="inline")
        return web.Response(text="OK")

    # 3. Реакция на старт (кнопка «Начать», /start или системное открытие)
    is_start = (
        text.startswith("/start")
        or payload == "menu_root"
        or event_type in ["bot_started", "chat_started", "user_added", "start"]
        or (not text and not payload)
    )

    if is_start:
        welcome_text = (
            "Добро пожаловать в базу отдыха «Русалочка»! 🌊\n\n"
            "Отдых на песчаном побережье Черного моря (Анапа, ст. Благовещенская).\n"
            "Ухоженная зеленая территория, уютные эко-домики и номера с оборудованной кухней!\n\n"
            "📅 Период работы: с 15 июня по 15 сентября\n"
            "🕒 Заезд — с 13:00 | Выезд — до 11:00\n\n"
            "Ознакомьтесь с номерным фондом и услугами базы в меню ниже ⬇"
        )
        await max_bot.send_message(
            chat_id=chat_id,
            text=welcome_text,
            buttons=get_main_menu_reply_keyboard(),
            keyboard_type="reply"
        )
        return web.Response(text="OK")

    elif text == "🏡 Наши номера" or payload == "menu_rooms":
        rooms_text = "🏡 Номерной фонд базы отдыха «Русалочка»:\n\nВыберите категорию для просмотра описания и стоимости:"
        await max_bot.send_message(
            chat_id=chat_id,
            text=rooms_text,
            buttons=get_rooms_list_inline_buttons(),
            keyboard_type="inline"
        )

    elif payload.startswith("view_room_"):
        room_key = payload.replace("view_room_", "")
        room = ROOMS_CATALOG.get(room_key)
        if room:
            await max_bot.send_message(
                chat_id=chat_id,
                text=room["description"],
                buttons=get_single_room_inline_buttons(),
                keyboard_type="inline"
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
        await max_bot.send_message(chat_id=chat_id, text=book_info, buttons=buttons, keyboard_type="inline")

    elif text == "🎡 Инфраструктура и услуги" or payload == "menu_infra":
        infra_text = (
            "🎡 ИНФРАСТРУКТУРА И УСЛУГИ\n\n"
            "✅ ВКЛЮЧЕНО В СТОИМОСТЬ:\n\n"
            "👶 Детская площадка\n"
            "Игровой комплекс для малышей на свежем воздухе.\n\n"
            "⚽ Спортивный инвентарь\n"
            "Мячи, ракетки, настольный теннис, шахматы, шашки и настольный футбол — всё для активного отдыха.\n\n"
            "🥩 Мангальная зона\n"
            "Оборудованная зона отдыха с бесплатным предоставлением решеток, шампуров, печи и казана (12 л).\n\n"
            "🌸 Зеленая зона\n"
            "Зеленая территория: 350 кустов роз и 1100 кустов лаванды.\n\n"
            "------------------------------------\n\n"
            "💲 ДОПОЛНИТЕЛЬНЫЕ УСЛУГИ:\n\n"
            "🎨 Студия творчества и шоу\n"
            "Регулярные шоу-программы и мастер-классы.\n\n"
            "🧺 Полезный сервис\n"
            "Прачечная и гладильная комната.\n"
            "Зарядная станция для электромобилей GB/T 7kwt (Цена 22₽ / 1 кВт.ч)."
        )
        await max_bot.send_message(
            chat_id=chat_id,
            text=infra_text,
            buttons=get_main_menu_reply_keyboard(),
            keyboard_type="reply"
        )

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
            [{"text": "⬅️️ В главное меню", "payload": "menu_root"}]
        ]
        await max_bot.send_message(chat_id=chat_id, text=about_text, buttons=buttons, keyboard_type="inline")

    elif text == "⭐ Отзывы" or payload == "menu_reviews":
        buttons = [
            [{"text": "⭐ Открыть отзывы на Яндекс.Картах", "url": REVIEWS_URL}],
            [{"text": "⬅️ В главное меню", "payload": "menu_root"}]
        ]
        await max_bot.send_message(
            chat_id=chat_id,
            text="⭐ Отзывы наших гостей на Яндекс.Картах:",
            buttons=buttons,
            keyboard_type="inline"
        )

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
            [{"text": "📄 Скачать правила проживания (PDF)", "payload": "faq_pdf"}],
            [{"text": "💬 Задать вопрос в чате", "payload": "menu_feedback"}],
            [{"text": "⬅️ В главное меню", "payload": "menu_root"}]
        ]
        await max_bot.send_message(chat_id=chat_id, text=contacts_text, buttons=buttons, keyboard_type="inline")

    elif text == "❓ Вопросы и ответы (FAQ)" or payload == "menu_faq":
        await max_bot.send_message(
            chat_id=chat_id,
            text="Часто задаваемые вопросы:",
            buttons=get_faq_inline_buttons(),
            keyboard_type="inline"
        )

    elif payload == "faq_checkin":
        ans = "Во сколько заселение?\n\n— с 13:00, но если Вы приедете раньше и ваш номер будет уже свободен, мы Вас заселим раньше."
        await max_bot.send_message(
            chat_id=chat_id,
            text=ans,
            buttons=[[{"text": "⬅️ Назад в FAQ", "payload": "menu_faq"}]],
            keyboard_type="inline"
        )

    elif payload == "faq_checkout":
        ans = "Во сколько выселение из номера?\n\n— освободить номер нужно до 11:00, ключи, брелоки и браслеты от номера нужно сдать в администрации."
        await max_bot.send_message(
            chat_id=chat_id,
            text=ans,
            buttons=[[{"text": "⬅️ Назад в FAQ", "payload": "menu_faq"}]],
            keyboard_type="inline"
        )

    elif payload == "faq_prepayment":
        ans = "При бронировании нужно вносить предоплату?\n\n— бронирование выбранной категории номера (домика) производится после перечисления предоплаты (30% от полной стоимости проживания)."
        await max_bot.send_message(
            chat_id=chat_id,
            text=ans,
            buttons=[[{"text": "⬅️ Назад в FAQ", "payload": "menu_faq"}]],
            keyboard_type="inline"
        )

    elif payload == "faq_refund":
        ans = "Предоплата возвратная?\n\n— бесплатная отмена бронирования возможна за 14 дней до забронированной даты, после - взимается 100% от размера предоплаты. В экстренном случае обращайтесь на электронную почту."
        await max_bot.send_message(
            chat_id=chat_id,
            text=ans,
            buttons=[[{"text": "⬅️️ Назад в FAQ", "payload": "menu_faq"}]],
            keyboard_type="inline"
        )

    elif payload == "faq_pets":
        ans = (
            "Возможно размещение с животными?\n\n"
            "— Возможность размещения исключительно с декоративными собаками, весом до 6 кг., предусмотрена в номерах категории «Номер с кухней (апарт.)» эко.\n\n"
            "— Тариф на размещение: 800 руб./сутки.\n\n"
            "— Выгул собак на территории Базы отдыха «Русалочка» ЗАПРЕЩЕН."
        )
        buttons = [
            [{"text": "📄 Посмотреть полные правила (PDF)", "payload": "faq_pdf"}],
            [{"text": "⬅️ Назад в FAQ", "payload": "menu_faq"}]
        ]
        await max_bot.send_message(chat_id=chat_id, text=ans, buttons=buttons, keyboard_type="inline")

    elif payload == "faq_pdf":
        await max_bot.send_document(
            chat_id=chat_id,
            file_path=PDF_RULES_PATH,
            caption="📄 Официальные правила проживания на базе отдыха «Русалочка» (PDF)"
        )

    elif text == "💬 Остались вопросы? Напишите нам" or payload == "menu_feedback":
        USER_STATES[sender_id] = "waiting_feedback"
        prompt = (
            "💬 Задать вопрос администратору базы отдыха\n\n"
            "Напишите ваш вопрос следующим сообщением. Мы получим его и ответим вам прямо в этот диалог!"
        )
        await max_bot.send_message(
            chat_id=chat_id,
            text=prompt,
            buttons=get_cancel_reply_keyboard(),
            keyboard_type="reply"
        )

    return web.Response(text="OK")

# =====================================================================
# 5. ОБРАБОТЧИК ДЛЯ ВЕБ-ОКНА И GET-ЗАПРОСОВ
# =====================================================================
async def handle_get(request: web.Request):
    html_page = """<!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>База отдыха «Русалочка»</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #0f172a;
                color: #f8fafc;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                text-align: center;
                padding: 20px;
                box-sizing: border-box;
            }
            .card {
                background: #1e293b;
                padding: 30px;
                border-radius: 16px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.5);
                max-width: 400px;
                width: 100%;
            }
            h1 { font-size: 20px; margin-bottom: 12px; color: #38bdf8; }
            p { font-size: 14px; color: #94a3b8; line-height: 1.5; margin-bottom: 20px; }
            .badge {
                display: inline-block;
                background: #10b981;
                color: white;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>База отдыха «Русалочка» 🌊</h1>
            <p>Чат-бот успешно запущен и готов к приёму сообщений в мессенджере MAX.</p>
            <span class="badge">Сервер активен (200 OK)</span>
        </div>
    </body>
    </html>"""
    return web.Response(text=html_page, content_type="text/html", status=200)

# =====================================================================
# 6. ТОЧКА ВХОДА
# =====================================================================
app = web.Application()

# Маршруты поддерживают GET и POST по обоим путям
app.router.add_get("/", handle_get)
app.router.add_post("/", handle_webhook)
app.router.add_get("/webhook", handle_get)
app.router.add_post("/webhook", handle_webhook)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    port = int(os.getenv("PORT", 3000))
    logging.info(f"Запуск сервера бота MAX на порту {port}...")
    web.run_app(app, host="0.0.0.0", port=port)
