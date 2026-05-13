from flask import Flask, render_template, request, redirect, url_for, session
from db import db
import threading
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = 'secret'


TARIFFS = [
    {'name': 'Старт',    'price': 299, 'gb': '10 ГБ интернета',  'minutes': '100 минут звонков',  'sms': '50 SMS',  'extra': 'Безлимит на соцсети', 'featured': False,
     'desc': 'Этот тариф идеально подходит для тех, кто только начинает свой путь в мире мобильной связи: студентов, пенсионеров или пользователей, которым нужен только базовый набор услуг для звонков и мессенджеров. Отличный вариант для малоактивного использования интернета и редких разговоров.'},
    {'name': 'Оптиум',   'price': 499, 'gb': '30 ГБ интернета',  'minutes': '500 минут звонков',  'sms': '100 SMS', 'extra': 'Безлимит на соцсети', 'featured': True,
     'desc': 'Оптимальный выбор для активного современного человека. Подойдёт для повседневной работы, общения, навигации и стриминга музыки. Хватит ресурсов на путешествия по городу, рабочие созвоны и общение с близкими — без оглядки на остатки.'},
    {'name': 'Максимум', 'price': 799, 'gb': '50 ГБ интернета',  'minutes': '800 минут звонков',  'sms': '200 SMS', 'extra': 'Безлимит на соцсети', 'featured': False,
     'desc': 'Тариф для тех, кому связь нужна без компромиссов: командировки, путешествия, удалённая работа из любой точки страны. Полный безлимит на ключевые мессенджеры, повышенные пакеты звонков и интернета — связь, которая всегда поспевает за вами.'},
]

PLAN_DETAILS = {
    'Старт':    {'price': 299, 'gb': 10, 'min': 100, 'sms': 50},
    'Оптиум':   {'price': 499, 'gb': 30, 'min': 500, 'sms': 100},
    'Максимум': {'price': 799, 'gb': 50, 'min': 800, 'sms': 200},
}

SERVICES = [
    {'title': 'Голосовая почта',     'desc': 'Принимайте сообщения когда недоступны',     'price': 'Бесплатно'},
    {'title': 'HD-видео',            'desc': 'Стриминг в высоком качестве без расхода ГБ', 'price': '340 ₽/мес'},
    {'title': 'Безлимит на ночь',    'desc': 'С 23:00 до 7:00 без ограничений',           'price': '99 ₽/мес'},
    {'title': 'Переадресация',       'desc': 'Переадресация на другой номер',             'price': '90 ₽/мес'},
    {'title': 'Дополнительно 10 ГБ', 'desc': 'Разовое пополнение пакета интернета',       'price': '150 ₽'},
    {'title': 'Роуминг Европа',      'desc': 'Звонки и интернет в странах ЕС',            'price': '290 ₽/мес'},
    {'title': 'МКСА ТВ',             'desc': '150+ каналов в Full HD качестве',           'price': '249 ₽/мес'},
]

REVIEWS = [
    {'name': 'Илья Соболев',  'rating': 5, 'text': 'По работе часто мотаюсь по области и в соседние регионы. С предыдущим оператором вечно была беда: только выезжаешь за МКАД — привет, глухие зоны. Перешёл на MobiWave по совету коллеги (спасибо, Саня!) и офигел. Во-первых, на трассе М4 теперь ловит всегда, можно спокойно подкасты слушать. Во-вторых, в командировке в Ярославле скорость вообще не просела. Очень рад, что дал шанс новому игроку. Тариф «Максимум» — топ за свои деньги.'},
    {'name': 'Марина Волкова', 'rating': 5, 'text': 'Наконец-то нашла оператора, у которого всё работает так, как надо. Пользуюсь пару месяцев — полёт нормальный. Приложение удобное, всё понятно без лишних танцев с бубном. Ребята, молодцы!'},
    {'name': 'Денис Павлов',   'rating': 5, 'text': 'Сначала сомневался, думал очередной виртуал. Оказалось, зря. Связь ловит отлично, проблем нет. Единственное — хотелось бы ещё больше всяких плюшек в будущем. Но старт мощный, 5 баллов.'},
]


def send_payment_email(to_email, payment_data):
    smtp_server = "smtp.gmail.com"
    port = 587
    sender_email = ""
    password = ""

    message = f"""
    Спасибо за пополнение счёта MobiWave!

    Ваш платёж:
    Сумма: {payment_data['amount']} ₽
    Способ оплаты: {payment_data['method']}
    ID платежа: {payment_data['id']}

    Средства уже зачислены на ваш счёт.
    """

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = "Пополнение счёта MobiWave"

    msg.attach(MIMEText(message, 'plain'))

    try:
        server = smtplib.SMTP(smtp_server, port)
        server.starttls()
        server.login(sender_email, password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Ошибка отправки email: {e}")
        return False


@app.route('/')
@app.route('/mobiwave/')
@app.route('/mobiwave/home/')
def home():
    return render_template('home.html', reviews=REVIEWS)


@app.route('/mobiwave/logout/')
def logout():
    session.clear()
    return redirect(url_for('home'))


@app.route('/mobiwave/tariffs/')
def tariffs():
    with_desc = request.args.get('detail') == '1'
    return render_template('tariffs.html', tariffs=TARIFFS, with_desc=with_desc)


@app.route('/mobiwave/services/')
def services_public():
    return render_template('services.html', services=SERVICES)


@app.route('/mobiwave/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    data = request.get_json()
    if not data:
        return {'error': 'Нет данных'}, 400
    phone = data.get('phone')
    password = data.get('password')
    if not all([phone, password]):
        return {'error': 'Заполните все поля'}, 400

    user = db.get_user(phone, password)
    if user:
        session['username'] = f"{user['first_name']} {user['last_name']}"
        session['user_id'] = user['id']
        session['user_email'] = user['email']
        session['user_phone'] = user['phone']
        return {'message': 'Вход выполнен'}, 200
    return {'error': 'Неверные данные'}, 401


@app.route('/mobiwave/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')

    data = request.get_json()
    if not data:
        return {'error': 'Нет данных'}, 400
    first_name = data.get('first_name', 'Пользователь')
    last_name = data.get('last_name', '')
    phone = data.get('phone')
    email = data.get('email')
    password = data.get('password')
    confirm = data.get('confirm')
    if not all([phone, email, password, confirm]):
        return {'error': 'Заполните все поля'}, 400
    if password != confirm:
        return {'error': 'Пароли не совпадают'}, 400

    result = db.add_user(first_name, last_name, phone, email, password)
    if 'error' in result:
        return result, 400

    session['username'] = f"{first_name} {last_name}".strip()
    session['user_id'] = result['id']
    session['user_email'] = email
    session['user_phone'] = phone
    return {'message': 'Регистрация успешна'}, 200


def login_required():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return None


@app.route('/mobiwave/my_tariff/')
def my_tariff():
    redir = login_required()
    if redir:
        return redir
    user = db.get_user_by_id(session['user_id'])
    plan = user['tariff'] if user and user['tariff'] in PLAN_DETAILS else 'Оптиум'
    plan_data = PLAN_DETAILS[plan]
    return render_template('my_tariff.html', user=user, plan=plan, plan_data=plan_data)


@app.route('/mobiwave/change_tariff/', methods=['POST'])
def change_tariff():
    if 'user_id' not in session:
        return {'error': 'Не авторизован'}, 401
    data = request.get_json()
    tariff = data.get('tariff')
    if tariff not in PLAN_DETAILS:
        return {'error': 'Неверный тариф'}, 400
    db.update_tariff(session['user_id'], tariff)
    return {'message': 'Тариф изменён'}, 200


@app.route('/mobiwave/dashboard_services/')
def dashboard_services():
    redir = login_required()
    if redir:
        return redir
    active_services = db.get_user_services(session['user_id'])
    return render_template('dashboard_services.html', services=SERVICES, active_services=active_services)


@app.route('/mobiwave/toggle_service/', methods=['POST'])
def toggle_service():
    if 'user_id' not in session:
        return {'error': 'Не авторизован'}, 401
    data = request.get_json()
    service = data.get('service')
    price = data.get('price', '')
    action = data.get('action')
    if action == 'connect':
        db.connect_service(session['user_id'], service, price)
    else:
        db.disconnect_service(session['user_id'], service)
    return {'message': 'Готово'}, 200


@app.route('/mobiwave/profile/', methods=['GET', 'POST'])
def profile():
    redir = login_required()
    if redir:
        return redir
    if request.method == 'POST':
        data = request.get_json()
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        email = data.get('email')
        phone = data.get('phone')
        new_password = data.get('new_password')
        confirm = data.get('confirm_password')

        result = db.update_profile(session['user_id'], first_name, last_name, email, phone)
        if 'error' in result:
            return result, 400

        if new_password:
            if new_password != confirm:
                return {'error': 'Пароли не совпадают'}, 400
            db.update_password(session['user_id'], new_password)

        session['username'] = f"{first_name} {last_name}".strip()
        session['user_email'] = email
        session['user_phone'] = phone
        return {'message': 'Профиль обновлён'}, 200

    user = db.get_user_by_id(session['user_id'])
    return render_template('profile.html', user=user)


@app.route('/mobiwave/topup/')
def topup():
    redir = login_required()
    if redir:
        return redir
    user = db.get_user_by_id(session['user_id'])
    return render_template('topup.html', user=user)


@app.route('/mobiwave/process_payment/', methods=['POST'])
def process_payment():
    data = request.get_json()
    if not data:
        return {'error': 'Нет данных'}, 400

    user_email = session.get('user_email')
    user_id = session.get('user_id')
    if not user_id:
        return {'error': 'Пользователь не авторизован'}, 401

    payment_id = str(uuid.uuid4())[:8]
    payment_data = {
        'id': payment_id,
        'amount': int(data.get('amount', 0)),
        'method': data.get('method', 'СБП'),
        'user_id': user_id,
        'email': user_email,
        'status': 'pending',
    }

    result = db.add_payment(payment_data)
    if 'error' in result:
        return {'error': result['error']}, 500

    threading.Thread(target=_auto_confirm, args=(payment_id,)).start()

    return {'payment_id': payment_id, 'message': 'Платеж создан'}, 200


def _auto_confirm(payment_id):
    import time
    time.sleep(2)
    if db.check_payment(payment_id) == 'pending':
        db.update_payment_status(payment_id, 'confirmed')
        payment = db.get_payment(payment_id)
        if payment:
            db.add_balance(payment['user_id'], payment['amount'])
            if payment['email']:
                send_payment_email(payment['email'], payment)


@app.route('/mobiwave/confirm_payment/', methods=['POST'])
def confirm_payment():
    data = request.get_json()
    payment_id = data.get('payment_id')
    status = data.get('status')

    current_status = db.check_payment(payment_id)
    if current_status and current_status == 'pending':
        db.update_payment_status(payment_id, status)
        if status == 'confirmed':
            payment = db.get_payment(payment_id)
            if payment:
                db.add_balance(payment['user_id'], payment['amount'])
                if payment['email']:
                    send_payment_email(payment['email'], payment)
        return {'message': f'Платеж {status}'}, 200
    return {'error': 'Платеж не найден или уже обработан'}, 404


@app.route('/mobiwave/payment_status/<payment_id>')
def payment_status(payment_id):
    status = db.check_payment(payment_id)
    if status:
        return {'status': status}
    return {'status': 'pending'}


if __name__ == '__main__':
    app.run(debug=True)
