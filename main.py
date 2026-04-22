import asyncio
import json
import requests
import uuid

from flask_mail import Message, Mail
from flask_apscheduler import APScheduler
from sqlalchemy.orm.sync import update

from data.liked import Liked
from data.prices import Prices
from data.users import User
import datetime
from data.verification import Verification
from editform import EditForm
from likeform import LikeForm
from loginform import LoginForm
from registerform import RegisterForm
import flask
import os.path
from flask import Flask, send_file, jsonify, redirect, render_template, make_response
from data import db_session
from data import games_
from validatemailform import MailForm

db_session.global_init("db/site.db")
db_sess = db_session.create_session()

app = Flask(__name__)
app.config['SECRET_KEY'] = str(uuid.uuid4())
app.config['MAIL_SERVER'] = 'smtp.yandex.ru'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'volganations@yandex.ru'
app.config['MAIL_PASSWORD'] = 'hzhdvplckcynmpig'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['SCHEDULER_API_ENABLED'] = True
mail = Mail(app)


@app.route("/")
def index():
    return send_file("static/index.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        existing_users = db_sess.query(User).filter(
            (User.email == form.username.data) | (User.login == form.username.data)).all()
        if existing_users:
            for i in existing_users:
                if i.password == form.password.data:
                    res = flask.make_response(redirect('/'))
                    res.set_cookie("mail_", value=str(i.email))
                    res.set_cookie("login_", value=str(i.login))
                    res.set_cookie("password_", value=str(i.password))
                    return res
        return render_template('login.html', title='Авторизация', form=form,
                               message="Неверный логин (или почта) или пароль")
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        existing_users = db_sess.query(User).filter(User.login == form.username.data).first()
        if existing_users:
            return render_template('register.html', title='Регистрация', form=form, message="Такой логин занят")
        existing_users = db_sess.query(User).filter(User.email == form.email.data).first()
        if existing_users:
            return render_template('register.html', title='Регистрация', form=form, message="Такая почта занята")
        res = flask.make_response(redirect('/validate_email'))
        res.set_cookie("mail", value=str(form.email.data))
        res.set_cookie("login", value=str(form.username.data))
        res.set_cookie("password", value=str(form.password.data))
        return res
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/validate_email', methods=['GET', 'POST'])
def validate():
    form = MailForm()
    cookie = flask.request.cookies.get('mail')
    code = db_sess.query(Verification.code).filter(Verification.email == cookie).first()
    if form.validate_on_submit():
        code = code[0]
        if form.code.data == code:
            db_sess.flush()
            user = User()
            user.email = flask.request.cookies.get('mail')
            user.password = flask.request.cookies.get('password')
            user.login = flask.request.cookies.get('login')
            db_sess.add(user)
            db_sess.commit()
            return redirect('/login')
        else:
            return render_template('validatemail.html', title='Подтверждение почты', form=form, message="Неверный код")
    if not code:
        db_sess.flush()
        cookie = flask.request.cookies.get('mail')
        code_ = str(uuid.uuid4())[:8]
        ver = Verification()
        ver.email = cookie
        ver.code = code_
        msg = Message(
            'Код подтверждения',
            sender='volganations@yandex.ru',
            recipients=[cookie]
        )
        msg.body = f'Код подтверждения: {code_}'
        mail.send(msg)
        db_sess.add(ver)
        db_sess.commit()

    return render_template('validatemail.html', title='Подтверждение почты', form=form)


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    res = flask.make_response(redirect('/'))
    res.set_cookie("mail_", value="", expires=0)
    res.set_cookie("login_", value="", expires=0)
    res.set_cookie("password_", value="", expires=0)
    return res


@app.route('/edit', methods=['GET', 'POST'])
def edit():
    form = EditForm()
    if form.validate_on_submit():
        existing_users = db_sess.query(User).filter(User.login == form.username.data).first()
        if existing_users:
            return render_template('edit.html', title='Регистрация', form=form,
                                   message="Такой логин занят")
        res = make_response(redirect('/'))
        res.set_cookie("login_", value=str(form.username.data))
        res.set_cookie("password_", value=str(form.password.data))
        db_sess.flush()
        db_sess.query(User).filter(User.email == flask.request.cookies.get("mail_")).update(
            {'login': form.username.data, 'password': form.username.data})
        db_sess.commit()
        return res
    return render_template('edit.html', title='Регистрация', form=form)


@app.route('/liked', methods=['GET', 'POST'])
def liked():
    user_email = flask.request.cookies.get('mail_')
    if not user_email:
        return redirect('/login')

    user = db_sess.query(User).filter(User.email == user_email).first()
    if not user:
        return redirect('/login')

    # Получаем избранные точки из БД
    liked_checkpoints = db_sess.query(Liked).filter(Liked.user_id == user.id).all()

    # Формируем список избранных точек с информацией
    favorites = []
    for liked_item in liked_checkpoints:
        route_id = liked_item.route_id
        checkpoint_id = liked_item.checkpoint_id

        # Находим маршрут и точку в ROUTES
        route = ROUTES.get(route_id)
        if route:
            cp = next((c for c in route['checkpoints'] if c['id'] == checkpoint_id), None)
            if cp:
                favorites.append({
                    'route_id': route_id,
                    'route_title': route['title'],
                    'checkpoint_id': checkpoint_id,
                    'checkpoint_name': cp['name'],
                    'checkpoint_address': cp['address']
                })

    return render_template("liked.html", favorites=favorites)


@app.route('/sources')
def sources():
    return render_template('sources.html')


@app.route('/route/<int:route_id>/checkpoint/<int:checkpoint_id>/toggle_favorite', methods=['POST'])
def toggle_favorite(route_id, checkpoint_id):
    user_email = flask.request.cookies.get('mail_')
    if not user_email:
        return jsonify({'success': False, 'message': 'Необходимо войти в систему'}), 401

    user = db_sess.query(User).filter(User.email == user_email).first()
    if not user:
        return jsonify({'success': False, 'message': 'Пользователь не найден'}), 404

    # Проверяем, есть ли уже в избранном
    existing = db_sess.query(Liked).filter(
        Liked.user_id == user.id,
        Liked.route_id == route_id,
        Liked.checkpoint_id == checkpoint_id
    ).first()

    if existing:
        # Удаляем из избранного
        db_sess.delete(existing)
        db_sess.commit()
        return jsonify({'success': True, 'action': 'removed'})
    else:
        # Добавляем в избранное
        new_liked = Liked()
        new_liked.user_id = user.id
        new_liked.route_id = route_id
        new_liked.checkpoint_id = checkpoint_id
        db_sess.add(new_liked)
        db_sess.commit()
        return jsonify({'success': True, 'action': 'added'})


ROUTES = {
    1: {
        'id': 1,
        'title': 'Литературное Поволжье',
        'theme': 'литературная',
        'description': 'Путешествие по местам жизни великих писателей и поэтов '
                       'Поволжья: Горький, Лермонтов, Гончаров, Цветаева. '
                       'Откройте для себя уникальные музеи и исторические дома, '
                       'где создавались шедевры русской литературы. Маршрут соединяет '
                       'важнейшие литературные центры региона, позволяя вам прогуляться '
                       'по местам, вдохновившим великих писателей.',
        'complexity': 'лёгкая',
        'duration': '4 часа',
        'map_iframe': (
            'https://yandex.ru/map-widget/v1/'
            '?ll=47.437400%2C55.036100'
            '&z=6'
            '&pt=43.990733%2C56.32389%2Cpm2rdl'
            '~43.658593%2C52.992637%2Cpm2rdl'
            '~48.396481%2C54.314510%2Cpm2rdl'
            '~49.129653%2C55.793505%2Cpm2rdl'
            '~52.072013%2C55.755150%2Cpm2rdl'
        ),
        'checkpoints': [
            {
                'id': 1,
                'name': 'Домик Каширина, Нижний Новгород',
                'description': 'Мемориальный музей детства Максима Горького — деревянный '
                               'дом деда писателя, где прошли его ранние годы. Это уникальное '
                               'место позволяет заглянуть в формирующие годы одного из величайших '
                               'русских писателей. Дом полностью сохраняет атмосферу конца XIX века, '
                               'интерьеры рассказывают о быте провинциального купеческого семейства. '
                               'Здесь маленький Алёша Пешков постигал уроки жизни, которые позже '
                               'найдут отражение в его произведениях. В музее экспонируются личные вещи '
                               'семьи, фотографии и документы, дающие представление о детстве писателя. '
                               'Каждый уголок дома хранит память о прошлом и служит источником вдохновения '
                               'для литературных исследователей.',
                'media': '/static/img/Muzei_detstva_A.M._Gorkogo_Domik_Kashirina.jpg',
                'fact': 'Именно здесь маленький Алёша Пешков провёл детство, '
                        'описанное в автобиографической повести «Детство».',
                'lat': 43.990733,
                'lon': 56.32389,
                'address': 'Нижний Новгород, Почтовый съезд, 21',
                'map_iframe': (
                    'https://yandex.ru/map-widget/v1/'
                    '?ll=43.990733%2C56.32389'
                    '&z=16'
                    '&pt=43.990733%2C56.32389%2Cpm2rdl'
                ),
                'quiz': [
                    {
                        'question': 'Какое произведение Горький написал о своём детстве в этом доме?',
                        'answers': ['Мать', 'На дне', 'Детство', 'Старуха Изергиль'],
                        'correct_answer': 2
                    },
                    {
                        'question': 'Кем приходился Каширин маленькому Алёше Пешкову?',
                        'answers': ['Отцом', 'Дедом', 'Дядей', 'Братом'],
                        'correct_answer': 1
                    },
                    {
                        'question': 'Настоящее имя Максима Горького?',
                        'answers': ['Алексей Пешков', 'Иван Каширин', 'Михаил Горький', 'Пётр Максимов'],
                        'correct_answer': 0
                    }
                ]
            },
            {
                'id': 2,
                'name': 'Музей-заповедник «Тарханы», Пензенская область',
                'description': 'Родовая усадьба, где вырос Михаил Лермонтов. Сохранились '
                               'барский дом, парк, пруды и семейная церковь. Это не просто музей, '
                               'а целый памятник дворянской культуре первой половины XIX века. '
                               'Прогулка по парку с вековыми дубами и липами позволяет ощутить '
                               'атмосферу, в которой формировалось воображение поэта. Барский дом '
                               'содержит подлинные предметы мебели, портреты семьи Лермонтовых, '
                               'личные вещи Михаила Юрьевича. Здесь же находится семейная церковь, '
                               'где отпевали многих членов семьи писателя. Кладбище при усадьбе стало '
                               'местом последнего приюта поэта — он похоронен здесь по его последней воле. '
                               'Заповедник бережно сохраняет память о жизни одного из величайших поэтов России.',
                'media': '/static/img/Tarkhany_Август_2008_049.jpg',
                'fact': 'Лермонтов провёл в Тарханах первые 13 лет жизни. '
                        'Здесь же он и похоронен.',
                'lat': 43.658593,
                'lon': 52.992637,
                'address': 'Пензенская обл., с. Лермонтово',
                'map_iframe': (
                    'https://yandex.ru/map-widget/v1/'
                    '?ll=43.658593%2C52.992637'
                    '&z=14'
                    '&pt=43.658593%2C52.992637%2Cpm2rdl'
                ),
                'quiz': [
                    {
                        'question': 'Какой поэт провёл детство в усадьбе Тарханы?',
                        'answers': ['Михаил Лермонтов', 'Александр Пушкин', 'Сергей Есенин', 'Николай Некрасов'],
                        'correct_answer': 0
                    },
                    {
                        'question': 'Сколько лет Лермонтов провёл в Тарханах?',
                        'answers': ['5 лет', '10 лет', '13 лет', '20 лет'],
                        'correct_answer': 2
                    },
                    {
                        'question': 'Где похоронен М.Ю. Лермонтов?',
                        'answers': ['В Москве', 'В Петербурге', 'В Тарханах', 'На Кавказе'],
                        'correct_answer': 2
                    }
                ]
            },
            {
                'id': 3,
                'name': 'Дом-музей И. А. Гончарова, Ульяновск',
                'description': 'Музей в доме, где родился автор романов «Обломов» и '
                               '«Обрыв». Экспозиция воссоздаёт быт купеческого Симбирска. '
                               'Этот дом является национальным достоянием и одним из самых значительных '
                               'литературных музеев России. Интерьеры музея тщательно отреставрированы '
                               'и возвращают посетителей в атмосферу начала XIX века. Здесь можно увидеть '
                               'подлинные вещи семьи Гончаровых, мебель того времени, книги из личной '
                               'библиотеки писателя. Экспозиция рассказывает о жизни семьи, о купеческой '
                               'культуре Симбирска и о том, как провинциальный город сформировал '
                               'мировоззрение будущего классика. Портреты, документы и письма дают '
                               'полное представление о жизни и творчестве Гончарова.',
                'media': '/static/img/Goncharov_House,_Ulyanovsk-1.jpg',
                'fact': 'Ульяновск до 1924 года назывался Симбирском — '
                        'это родной город Ивана Гончарова.',
                'lat': 48.396481,
                'lon': 54.314510,
                'address': 'Ульяновск, ул. Ленина, 134/20',
                'map_iframe': (
                    'https://yandex.ru/map-widget/v1/'
                    '?ll=48.396481%2C54.314510'
                    '&z=16'
                    '&pt=48.396481%2C54.314510%2Cpm2rdl'
                ),
                'quiz': [
                    {
                        'question': 'Как назывался Ульяновск во времена Гончарова?',
                        'answers': ['Казань', 'Самара', 'Саратов', 'Симбирск'],
                        'correct_answer': 3
                    },
                    {
                        'question': 'Какой знаменитый роман написал И.А. Гончаров?',
                        'answers': ['Евгений Онегин', 'Обломов', 'Война и мир', 'Мёртвые души'],
                        'correct_answer': 1
                    },
                    {
                        'question': 'В каком году Симбирск переименовали в Ульяновск?',
                        'answers': ['1917', '1924', '1930', '1945'],
                        'correct_answer': 1
                    }
                ]
            },
            {
                'id': 4,
                'name': 'Литературно-мемориальный музей А. М. Горького, Казань',
                'description': 'Музей расположен в доме, где молодой Горький жил и работал '
                               'в пекарне. Казань стала его «университетами». Этот дом свидетель '
                               'одного из самых трудных, но и самых образованных периодов жизни писателя. '
                               'Горький приехал в Казань беглым мальчиком, и здесь он не только выжил, '
                               'но и получил то, что можно назвать правоверным образованием жизни. '
                               'Работа в пекарне, общение с рабочими и революционно настроенной молодёжью '
                               'формировали его взгляды и становились материалом для будущих произведений. '
                               'Музей показывает скромные условия, в которых жил молодой Горький, '
                               'его рабочий стол, книги которые он читал, письма и наброски будущих произведений. '
                               'Это место своеобразного рождения писателя-революционера.',
                'media': '/static/img/Ттарстан._Казань._Дом,_в_котором_в_1886_-_1887_гг._жил_и_работал_пекарем_Горький_Алексей_Максимович.jpg',
                'fact': 'Горький приехал в Казань в 1884 году мечтая поступить '
                        'в университет, но получил «университеты жизни».',
                'lat': 49.129653,
                'lon': 55.793505,
                'address': 'Казань, ул. Горького, 10',
                'map_iframe': (
                    'https://yandex.ru/map-widget/v1/'
                    '?ll=49.129653%2C55.793505'
                    '&z=16'
                    '&pt=49.129653%2C55.793505%2Cpm2rdl'
                ),
                'quiz': [
                    {
                        'question': 'Как называется повесть Горького о казанском периоде жизни?',
                        'answers': ['Детство', 'В людях', 'Мои университеты', 'На дне'],
                        'correct_answer': 2
                    },
                    {
                        'question': 'Кем работал молодой Горький в Казани?',
                        'answers': ['Учителем', 'Пекарем', 'Библиотекарем', 'Кузнецом'],
                        'correct_answer': 1
                    },
                    {
                        'question': 'В каком году Горький приехал в Казань?',
                        'answers': ['1880', '1884', '1890', '1895'],
                        'correct_answer': 1
                    }
                ]
            },
            {
                'id': 5,
                'name': 'Мемориальный комплекс М. И. Цветаевой, Елабуга',
                'description': 'Дом, где провела последние дни жизни великая поэтесса '
                               'Марина Цветаева. Музей хранит личные вещи и рукописи. '
                               'Это место наполнено особой трагической энергией — здесь рождалась '
                               'последняя поэзия Цветаевой, здесь она боролась с нищетой и одиночеством. '
                               'Небольшая комната, где жила поэтесса, содержит подлинные предметы её быта: '
                               'письменный стол, личные вещи, записные книжки с набросками. '
                               'Рукописи Цветаевой, выставленные в музее, показывают процесс её творчества — '
                               'исправления, вычеркивания, переработки. Здесь также находятся письма '
                               'к друзьям и близким, дающие представление о внутреннем мире поэтессы '
                               'в последние месяцы жизни. Комплекс включает также музей её памяти '
                               'и информационный центр, посвящённый её творчеству и значению для русской литературы.',
                'media': '/static/img/Memorial_House-Museum_of_Marina_Tsvetaeva_in_Elabuga.jpg',
                'fact': 'Цветаева была эвакуирована в Елабугу в 1941 году. '
                        'Здесь трагически оборвалась её жизнь.',
                'lat': 52.072013,
                'lon': 55.755150,
                'address': 'Елабуга, ул. Малая Покровская, 20',
                'map_iframe': (
                    'https://yandex.ru/map-widget/v1/'
                    '?ll=52.072013%2C55.755150'
                    '&z=16'
                    '&pt=52.072013%2C55.755150%2Cpm2rdl'
                ),
                'quiz': [
                    {
                        'question': 'В каком году Цветаева была эвакуирована в Елабугу?',
                        'answers': ['1939', '1940', '1942', '1941'],
                        'correct_answer': 3
                    },
                    {
                        'question': 'Какой жанр литературы был основным для Цветаевой?',
                        'answers': ['Проза', 'Драматургия', 'Поэзия', 'Публицистика'],
                        'correct_answer': 2
                    },
                    {
                        'question': 'Сколько времени Цветаева прожила в Елабуге?',
                        'answers': ['Несколько дней', 'Несколько недель', 'Год', 'Два года'],
                        'correct_answer': 1
                    }
                ]
            }
        ]
    },
    2: {
        'id': 2,
        'title': 'Космос и техника Поволжья',
        'theme': 'инженерная',
        'description': 'Маршрут по центрам ракетостроения, автомобилестроения, '
                       'авиации и оружейного дела Поволжского федерального округа.',
        'complexity': 'сложная',
        'duration': '5 часов',
        'map_iframe': (
            'https://yandex.ru/map-widget/v1/'
            '?ll=50.666400%2C54.712100'
            '&z=6'
            '&pt=50.145226%2C53.212701%2Cpm2rdl'
            '~49.249808%2C53.553031%2Cpm2rdl'
            '~48.252700%2C54.269800%2Cpm2rdl'
            '~52.446574%2C55.74731%2Cpm2rdl'
        ),
        'checkpoints': [
            {
                'id': 1,
                'name': 'Музейно-выставочный центр «Самара Космическая»',
                'description': 'Один из главных символов космической истории Поволжья.',
                'media': '/static/img/municipal-museum-cosmic.jpg',
                'fact': 'Самара (в советское время — Куйбышев) была закрытым центром ракетно-космической промышленности СССР.',
                'lat': 50.145226,
                'lon': 53.212701,
                'address': 'Самара, пр. Ленина, 21',
                'map_iframe': 'https://yandex.ru/map-widget/v1/?ll=50.145226%2C53.212701&z=16&pt=50.145226%2C53.212701%2Cpm2rdl',
                'quiz': [
                    {'question': 'Как называлась Самара в советское время?',
                     'answers': ['Куйбышев', 'Сталинград', 'Горький', 'Свердловск'], 'correct_answer': 0},
                    {'question': 'Какая ракета установлена у входа в музей?',
                     'answers': ['Восток', 'Союз', 'Протон', 'Ангара'], 'correct_answer': 1},
                    {'question': 'Чему посвящён музей «Самара Космическая»?',
                     'answers': ['Авиации', 'Космонавтике', 'Флоту', 'Танкам'], 'correct_answer': 1}
                ]
            },
            {
                'id': 2,
                'name': 'Технический музей им. К. Г. Сахарова, Тольятти',
                'description': 'Крупнейший в России музей техники под открытым небом.',
                'media': '/static/img/Technical_museum,_Togliatti,_Russia-5.JPG',
                'fact': 'В коллекции музея более 460 экспонатов, включая настоящую подводную лодку Б-307.',
                'lat': 49.249808,
                'lon': 53.553031,
                'address': 'Тольятти, ул. Сахарова, 1',
                'map_iframe': 'https://yandex.ru/map-widget/v1/?ll=49.249808%2C53.553031&z=16&pt=49.249808%2C53.553031%2Cpm2rdl',
                'quiz': [
                    {'question': 'Какой автомобильный гигант расположен в Тольятти?',
                     'answers': ['ГАЗ', 'КАМАЗ', 'УАЗ', 'АвтоВАЗ'], 'correct_answer': 3},
                    {'question': 'Сколько экспонатов в музее?', 'answers': ['100', '250', '460', '600'],
                     'correct_answer': 2},
                    {'question': 'Какая подводная лодка есть в музее?',
                     'answers': ['Б-307', 'К-19', 'Курск', 'Комсомолец'], 'correct_answer': 0}
                ]
            },
            {
                'id': 3,
                'name': 'Музей истории гражданской авиации, Ульяновск',
                'description': 'Уникальная экспозиция из более чем 30 воздушных судов.',
                'media': '/static/img/Tupolev_Tu-144,_Ulyanovsk_Aircraft_Museum.jpg',
                'fact': 'Ульяновск считается авиационной столицей России.',
                'lat': 48.234580,
                'lon': 54.289727,
                'address': 'Ульяновск, ул. Авиационная, 20а',
                'map_iframe': 'https://yandex.ru/map-widget/v1/?ll=48.234580%2C54.289727&z=16&pt=48.234580%2C54.289727%2Cpm2rdl',
                'quiz': [
                    {'question': 'Какой тяжёлый транспортный самолёт производили в Ульяновске?',
                     'answers': ['Ил-76', 'Ту-154', 'Ан-124 «Руслан»', 'Су-27'], 'correct_answer': 2},
                    {'question': 'Сколько самолётов в музее?', 'answers': ['10', '20', '30', '50'],
                     'correct_answer': 2},
                    {'question': 'Какой сверхзвуковой пассажирский самолёт есть в музее?',
                     'answers': ['Ту-144', 'Конкорд', 'Ту-154', 'Ил-62'], 'correct_answer': 0}
                ]
            },
            {
                'id': 4,
                'name': 'Музей истории ОАО «КАМАЗ», Набережные Челны',
                'description': 'Музей крупнейшего в России производителя грузовых автомобилей.',
                'media': '/static/img/kam.jpg',
                'fact': 'Команда «КАМАЗ-мастер» одержала более 19 побед на ралли «Дакар».',
                'lat': 52.446574,
                'lon': 55.74731,
                'address': 'Набережные Челны, пр. Автозаводский, 2',
                'map_iframe': 'https://yandex.ru/map-widget/v1/?ll=52.446574%2C55.74731&z=16&pt=52.446574%2C55.74731%2Cpm2rdl',
                'quiz': [
                    {'question': 'В каком ралли команда «КАМАЗ-мастер» побеждала более 19 раз?',
                     'answers': ['Баха', 'Ралли Монте-Карло', 'Шёлковый путь', 'Дакар'], 'correct_answer': 3},
                    {'question': 'Сколько побед у команды КАМАЗ-мастер?', 'answers': ['5', '10', '19', '25'],
                     'correct_answer': 2},
                    {'question': 'Что производит завод КАМАЗ?',
                     'answers': ['Легковые авто', 'Грузовики', 'Автобусы', 'Танки'], 'correct_answer': 1}
                ]
            }
        ]
    },
    3: {
        'id': 3,
        'title': 'Духовное Поволжье',
        'theme': 'духовная',
        'description': 'Маршрут по святыням и духовным центрам Поволжья.',
        'complexity': 'средняя',
        'duration': '5 часов',
        'map_iframe': 'https://yandex.ru/map-widget/v1/?ll=47.688400%2C55.518300&z=6',
        'checkpoints': [
            {
                'id': 1,
                'name': 'Серафимо-Дивеевский монастырь',
                'description': 'Один из крупнейших православных монастырей России.',
                'media': '/static/img/Diveyevo_(51263813251).jpg',
                'fact': 'Серафим Саровский — один из самых почитаемых русских святых.',
                'lat': 43.245493,
                'lon': 55.040409,
                'address': 'Нижегородская обл., с. Дивеево',
                'map_iframe': 'https://yandex.ru/map-widget/v1/?ll=43.245493%2C55.040409&z=16&pt=43.245493%2C55.040409%2Cpm2rdl',
                'quiz': [
                    {'question': 'С каким святым связан Дивеевский монастырь?',
                     'answers': ['Сергий Радонежский', 'Серафим Саровский', 'Николай Чудотворец', 'Александр Невский'],
                     'correct_answer': 1},
                    {'question': 'Какой это монастырь?', 'answers': ['Мужской', 'Женский', 'Смешанный', 'Детский'],
                     'correct_answer': 1},
                    {'question': 'В каком году канонизирован Серафим Саровский?',
                     'answers': ['1801', '1903', '1917', '1991'], 'correct_answer': 1}
                ]
            },
            {
                'id': 2,
                'name': 'Раифский Богородицкий монастырь, Татарстан',
                'description': 'Действующий мужской монастырь XVII века.',
                'media': '/static/img/Raifsky_Monastery_08-2016_photo6.jpg',
                'fact': 'Главная святыня — Грузинская икона Божией Матери.',
                'lat': 48.731677,
                'lon': 55.903792,
                'address': 'Татарстан, Зеленодольский р-н, пос. Раифа',
                'map_iframe': 'https://yandex.ru/map-widget/v1/?ll=48.731677%2C55.903792&z=16&pt=48.731677%2C55.903792%2Cpm2rdl',
                'quiz': [
                    {'question': 'Какая икона является главной святыней Раифского монастыря?',
                     'answers': ['Казанская', 'Владимирская', 'Грузинская', 'Иверская'], 'correct_answer': 2},
                    {'question': 'В каком веке основан монастырь?', 'answers': ['XV', 'XVI', 'XVII', 'XVIII'],
                     'correct_answer': 2},
                    {'question': 'Это какой монастырь?', 'answers': ['Мужской', 'Женский', 'Смешанный', 'Детский'],
                     'correct_answer': 0}
                ]
            },
            {
                'id': 3,
                'name': 'Белогорский Свято-Николаевский монастырь, Пермский край',
                'description': 'Монастырь на вершине Белой горы — «Уральский Афон».',
                'media': '/static/img/Белогорский_Свято-Николаевский_православно-миссионерский_мужской_монастырь.jpg',
                'fact': 'Крестовоздвиженский собор — третий по величине православный храм в России.',
                'lat': 56.230037,
                'lon': 57.392215,
                'address': 'Пермский край, Кунгурский р-н, с. Белая Гора',
                'map_iframe': 'https://yandex.ru/map-widget/v1/?ll=56.230037%2C57.392215&z=16&pt=56.230037%2C57.392215%2Cpm2rdl',
                'quiz': [
                    {'question': 'Как называют Белогорский монастырь?',
                     'answers': ['Уральский Иерусалим', 'Уральская Лавра', 'Уральский Афон', 'Уральский Ватикан'],
                     'correct_answer': 2},
                    {'question': 'На какой горе расположен монастырь?',
                     'answers': ['Красной', 'Белой', 'Чёрной', 'Синей'], 'correct_answer': 1},
                    {'question': 'Какое место по величине занимает собор?',
                     'answers': ['Первое', 'Второе', 'Третье', 'Четвёртое'], 'correct_answer': 2}
                ]
            },
            {
                'id': 4,
                'name': 'Макарьевский Желтоводский монастырь',
                'description': 'Древний монастырь на берегу Волги, основанный в XV веке.',
                'media': '/static/img/Вид_на_Макарьевский_монастырь_с_Волги_01.jfif',
                'fact': 'Макарьевская ярмарка позднее переехала в Нижний Новгород.',
                'lat': 45.064338,
                'lon': 56.083459,
                'address': 'Нижегородская обл., пос. Макарьево',
                'map_iframe': 'https://yandex.ru/map-widget/v1/?ll=45.064338%2C56.083459&z=16&pt=45.064338%2C56.083459%2Cpm2rdl',
                'quiz': [
                    {'question': 'Какая знаменитая ярмарка зародилась у стен этого монастыря?',
                     'answers': ['Ирбитская', 'Нижегородская', 'Казанская', 'Симбирская'], 'correct_answer': 1},
                    {'question': 'В каком веке основан монастырь?', 'answers': ['XIII', 'XIV', 'XV', 'XVI'],
                     'correct_answer': 2},
                    {'question': 'На берегу какой реки расположен монастырь?',
                     'answers': ['Ока', 'Кама', 'Волга', 'Дон'], 'correct_answer': 2}
                ]
            },
            {
                'id': 5,
                'name': 'Кафедральный собор св. Феодора Ушакова, Саранск',
                'description': 'Один из крупнейших соборов России.',
                'media': '/static/img/St._Theodore_Ushakov_Cathedral.jpg',
                'fact': 'Адмирал Фёдор Ушаков не проиграл ни одного морского сражения.',
                'lat': 45.181674,
                'lon': 54.181612,
                'address': 'Саранск, ул. Советская, 53',
                'map_iframe': 'https://yandex.ru/map-widget/v1/?ll=45.181674%2C54.181612&z=16&pt=45.181674%2C54.181612%2Cpm2rdl',
                'quiz': [
                    {'question': 'Кем был Феодор Ушаков до канонизации?',
                     'answers': ['Монах', 'Купец', 'Архитектор', 'Адмирал'], 'correct_answer': 3},
                    {'question': 'Сколько сражений проиграл Ушаков?', 'answers': ['Ни одного', 'Одно', 'Два', 'Три'],
                     'correct_answer': 0},
                    {'question': 'В каком городе находится собор?', 'answers': ['Саранск', 'Самара', 'Казань', 'Пенза'],
                     'correct_answer': 0}
                ]
            }
        ]
    },
    4: {
        'id': 4,
        'title': 'Крепости и оборона Поволжья',
        'theme': 'военно-историческая',
        'description': 'Маршрут по фортификационным сооружениям.',
        'complexity': 'сложная',
        'duration': '5 часов',
        'map_iframe': 'https://yandex.ru/map-widget/v1/?ll=50.207600%2C54.780700&z=5',
        'checkpoints': [
            {
                'id': 1,
                'name': 'Нижегородский кремль',
                'description': 'Мощная кирпичная крепость начала XVI века с 13 башнями.',
                'media': '/static/img/Вид_на_Нижегородский_кремль_с_высоты_cropped.jpg',
                'fact': 'Нижегородский кремль ни разу не был взят штурмом.',
                'lat': 44.003417,
                'lon': 56.328120,
                'address': 'Нижний Новгород, Кремль, 1',
                'map_iframe': 'https://yandex.ru/map-widget/v1/?ll=44.003417%2C56.328120&z=16&pt=44.003417%2C556.328120%2Cpm2rdl',
                'quiz': [
                    {'question': 'Сколько башен у Нижегородского кремля?', 'answers': ['9', '20', '13', '7'],
                     'correct_answer': 2},
                    {'question': 'Был ли кремль взят штурмом?', 'answers': ['Да', 'Нет', 'Один раз', 'Два раза'],
                     'correct_answer': 1},
                    {'question': 'В каком веке построен кремль?', 'answers': ['XIV', 'XV', 'XVI', 'XVII'],
                     'correct_answer': 2}
                ]
            },
            {
                'id': 2,
                'name': 'Бункер Сталина, Самара',
                'description': 'Секретный бункер на глубине 37 метров.',
                'media': "/static/img/Stalin's_Bunker_0020.jpg",
                'fact': 'О существовании бункера узнали только в 1990 году.',
                'lat': 50.097857,
                'lon': 53.196683,
                'address': 'Самара, ул. Фрунзе, 167',
                'map_iframe': 'https://yandex.ru/map-widget/v1/?ll=50.097857%2C53.196683&z=16&pt=50.097857%2C53.196683%2Cpm2rdl',
                'quiz': [
                    {'question': 'На какой глубине расположен бункер Сталина?',
                     'answers': ['12 метров', '37 метров', '25 метров', '50 метров'], 'correct_answer': 1},
                    {'question': 'В каком году узнали о бункере?', 'answers': ['1945', '1960', '1990', '2000'],
                     'correct_answer': 2},
                    {'question': 'Для чего был построен бункер?',
                     'answers': ['Склад', 'Командный пункт', 'Больница', 'Тюрьма'], 'correct_answer': 1}
                ]
            },
            {
                'id': 3,
                'name': 'Остров-град Свияжск',
                'description': 'Крепость XVI века, основанная Иваном Грозным.',
                'media': '/static/img/Троицкая_улица_Свияжска,_2019-01-03.jpg',
                'fact': 'Свияжск был построен всего за 4 недели.',
                'lat': 48.661172,
                'lon': 55.772000,
                'address': 'Татарстан, Зеленодольский р-н, с. Свияжск',
                'map_iframe': 'https://yandex.ru/map-widget/v1/?ll=48.661172%2C55.772000&z=14&pt=48.661172%2C55.772000%2Cpm2rdl',
                'quiz': [
                    {'question': 'За какой срок была построена крепость Свияжск?',
                     'answers': ['1 год', '6 месяцев', '3 дня', '4 недели'], 'correct_answer': 3},
                    {'question': 'Кто основал Свияжск?',
                     'answers': ['Пётр I', 'Иван Грозный', 'Екатерина II', 'Александр I'], 'correct_answer': 1},
                    {'question': 'Для чего был построен Свияжск?',
                     'answers': ['Торговля', 'Взятие Казани', 'Оборона', 'Монастырь'], 'correct_answer': 1}
                ]
            },
            {
                'id': 4,
                'name': 'Музейно-выставочный комплекс стрелкового оружия, Ижевск',
                'description': 'Музей при Ижевском оружейном заводе.',
                'media': '/static/img/Музейно-выставочный_комплекс_имени_Калашникова_(Ижевск).jpg',
                'fact': 'Ижевский оружейный завод основан в 1807 году.',
                'lat': 53.206784,
                'lon': 56.850721,
                'address': 'Ижевск, ул. Бородина, 19',
                'map_iframe': 'https://yandex.ru/map-widget/v1/?ll=53.206784%2C56.850721&z=16&pt=53.206784%2C56.850721%2Cpm2rdl',
                'quiz': [
                    {'question': 'В каком году основан Ижевский оружейный завод?',
                     'answers': ['1807', '1850', '1762', '1917'], 'correct_answer': 0},
                    {'question': 'Чему посвящён музей?',
                     'answers': ['Танкам', 'Стрелковому оружию', 'Артиллерии', 'Флоту'], 'correct_answer': 1},
                    {'question': 'Какой знаменитый конструктор работал в Ижевске?',
                     'answers': ['Королёв', 'Калашников', 'Туполев', 'Кошкин'], 'correct_answer': 1}
                ]
            },
            {
                'id': 5,
                'name': 'Оренбургская крепость (Губернаторский музей)',
                'description': 'Историческое место Оренбургской крепости.',
                'media': '/static/img/Historical_museum_of_Orenburg.jpg',
                'fact': 'Оренбургская крепость стала прообразом Белогорской крепости в «Капитанской дочке» Пушкина.',
                'lat': 55.108391,
                'lon': 51.755434,
                'address': 'Оренбург, ул. Набережная, 29',
                'map_iframe': 'https://yandex.ru/map-widget/v1/?ll=55.108391%2C51.755434&z=15&pt=55.108391%2C51.755434%2Cpm2rdl',
                'quiz': [
                    {'question': 'Какое произведение Пушкин написал после посещения Оренбурга?',
                     'answers': ['Евгений Онегин', 'Дубровский', 'Капитанская дочка', 'Борис Годунов'],
                     'correct_answer': 2},
                    {'question': 'Кто осаждал крепость?', 'answers': ['Наполеон', 'Пугачёв', 'Разин', 'Болотников'],
                     'correct_answer': 1},
                    {'question': 'На границе каких частей света стоит крепость?',
                     'answers': ['Европы и Азии', 'Азии и Африки', 'Европы и Африки', 'Азии и Америки'],
                     'correct_answer': 0}
                ]
            }
        ]
    },
    5: {
        'id': 5,
        'title': 'Купеческое Поволжье',
        'theme': 'купеческая',
        'description': 'Маршрут по старинным торговым городам.',
        'complexity': 'средняя',
        'duration': '4 часа',
        'map_iframe': 'https://yandex.ru/map-widget/v1/?ll=47.431400%2C54.000100&z=6',
        'checkpoints': [
            {
                'id': 1,
                'name': 'Нижегородская ярмарка',
                'description': 'Главный торговый центр Российской империи.',
                'media': '/static/img/NN-16-05-2022_41.jpg',
                'fact': 'Нижегородская ярмарка была крупнейшей в России.',
                'lat': 43.961313,
                'lon': 56.328324,
                'address': 'Нижний Новгород, ул. Совнаркомовская, 13',
                'map_iframe': 'https://yandex.ru/map-widget/v1/?ll=43.961313%2C56.328324&z=16&pt=43.961313%2C56.328324%2Cpm2rdl',
                'quiz': [
                    {'question': 'Как образно называли Нижний Новгород?',
                     'answers': ['Ворота России', 'Карман России', 'Сердце России', 'Окно в Европу'],
                     'correct_answer': 1},
                    {'question': 'Какой по величине была ярмарка в мире?',
                     'answers': ['Первой', 'Второй', 'Третьей', 'Четвёртой'], 'correct_answer': 2},
                    {'question': 'Сколько дней работала ярмарка?', 'answers': ['10', '30', '60', '90'],
                     'correct_answer': 1}
                ]
            },
            {
                'id': 2,
                'name': 'Особняк Курлиной, Самара',
                'description': 'Жемчужина самарского модерна.',
                'media': '/static/img/Особняк_Курлиной_(Самара).jpg',
                'fact': 'Особняк Курлиной — первое здание в стиле модерн в Самаре.',
                'lat': 50.096159,
                'lon': 53.193975,
                'address': 'Самара, ул. Фрунзе, 159',
                'map_iframe': 'https://yandex.ru/map-widget/v1/?ll=50.096159%2C53.193975&z=16&pt=50.096159%2C53.193975%2Cpm2rdl',
                'quiz': [
                    {'question': 'В каком стиле построен особняк Курлиной?',
                     'answers': ['Классицизм', 'Барокко', 'Готика', 'Модерн'], 'correct_answer': 3},
                    {'question': 'Что особенного в особняке?', 'answers': ['Витражи', 'Фонтаны', 'Лифт', 'Бассейн'],
                     'correct_answer': 0},
                    {'question': 'Кем была Курлина?',
                     'answers': ['Купчихой', 'Актрисой', 'Писательницей', 'Учительницей'], 'correct_answer': 0}
                ]
            },
            {
                'id': 3,
                'name': 'Музей-заповедник «Елабуга»',
                'description': 'Купеческая Елабуга — город-музей.',
                'media': '/static/img/Shishkinskiye_prudy_(park_in_Elabuga)-14.jpg',
                'fact': 'Елабуга — родина художника Ивана Шишкина.',
                'lat': 52.056050,
                'lon': 55.756189,
                'address': 'Елабуга, ул. Казанская, 26',
                'map_iframe': 'https://yandex.ru/map-widget/v1/?ll=52.056050%2C55.756189&z=14&pt=52.056050%2C55.756189%2Cpm2rdl',
                'quiz': [
                    {'question': 'Какой знаменитый художник родился в Елабуге?',
                     'answers': ['Илья Репин', 'Иван Шишкин', 'Василий Суриков', 'Карл Брюллов'], 'correct_answer': 1},
                    {'question': 'Чем известна Елабуга?',
                     'answers': ['Крепостью', 'Купеческими домами', 'Фабриками', 'Мостами'], 'correct_answer': 1},
                    {'question': 'Какая поэтесса жила в Елабуге?',
                     'answers': ['Ахматова', 'Цветаева', 'Пушкина', 'Берггольц'], 'correct_answer': 1}
                ]
            },
            {
                'id': 4,
                'name': 'Улица Московская, Пенза',
                'description': 'Главная пешеходная улица Пензы.',
                'media': '/static/img/Пенза,_Московская_улица_DSC08850.JPG',
                'fact': 'На улице Московской находится музей одной картины.',
                'lat': 45.017692,
                'lon': 53.194220,
                'address': 'Пенза, ул. Московская',
                'map_iframe': 'https://yandex.ru/map-widget/v1/?ll=45.017692%2C53.194220&z=16&pt=45.017692%2C53.194220%2Cpm2rdl',
                'quiz': [
                    {'question': 'Как называют улицу Московскую в Пензе?',
                     'answers': ['Пензенский Невский', 'Пензенский Бродвей', 'Пензенский Арбат', 'Пензенский бульвар'],
                     'correct_answer': 2},
                    {'question': 'Какой уникальный музей есть на улице?',
                     'answers': ['Музей одной картины', 'Музей одной книги', 'Музей одной статуи', 'Музей одной песни'],
                     'correct_answer': 0},
                    {'question': 'Что характерно для улицы?',
                     'answers': ['Фонтаны', 'Купеческая застройка', 'Небоскрёбы', 'Парки'], 'correct_answer': 1}
                ]
            },
            {
                'id': 5,
                'name': 'Проспект Столыпина, Саратов',
                'description': 'Пешеходная улица Саратова.',
                'media': '/static/img/Stolypin_Avenue_in_Saratov_(July_2025)_-_0_2.jpg',
                'fact': 'Саратовская консерватория — третья по старшинству в России.',
                'lat': 46.021770,
                'lon': 51.532307,
                'address': 'Саратов, пр. Столыпина',
                'map_iframe': 'https://yandex.ru/map-widget/v1/?ll=46.021770%2C51.532307&z=16&pt=46.021770%2C51.532307%2Cpm2rdl',
                'quiz': [
                    {'question': 'Какое учебное заведение находится на пр. Столыпина?',
                     'answers': ['Училище', 'Академия', 'Лицей', 'Консерватория'], 'correct_answer': 3},
                    {'question': 'Какое место по старшинству занимает консерватория?',
                     'answers': ['Первое', 'Второе', 'Третье', 'Четвёртое'], 'correct_answer': 2},
                    {'question': 'В честь кого названа улица?',
                     'answers': ['Столыпин', 'Столетов', 'Стоянов', 'Столбов'], 'correct_answer': 0}
                ]
            }
        ]
    },
    6: {
        'id': 6,
        'title': 'Природное Поволжье',
        'theme': 'природная',
        'description': 'Маршрут по уникальным природным объектам Поволжья.',
        'complexity': 'сложная',
        'duration': '6 часов',
        'map_iframe': 'https://yandex.ru/map-widget/v1/?ll=49.812400%2C55.873500&z=5',
        'checkpoints': [
            {
                'id': 1,
                'name': 'Национальный парк «Самарская Лука»',
                'description': 'Уникальная излучина Волги с Жигулёвскими горами.',
                'media': '/static/img/Вид_на_Усинский_курган.jpg',
                'fact': 'Жигулёвские горы — единственные горы тектонического происхождения на Русской равнине.',
                'lat': 49.290906,
                'lon': 53.266869,
                'address': 'Самарская обл., нац. парк «Самарская Лука»',
                'map_iframe': 'https://yandex.ru/map-widget/v1/?ll=49.750000%2C53.266869&z=16&pt=49.290906%2C53.266869%2Cpm2rdl',
                'quiz': [
                    {'question': 'Какие горы расположены на территории Самарской Луки?',
                     'answers': ['Уральские', 'Жигулёвские', 'Кавказские', 'Хибины'], 'correct_answer': 1},
                    {'question': 'Что такое Самарская Лука?', 'answers': ['Гора', 'Излучина Волги', 'Озеро', 'Лес'],
                     'correct_answer': 1},
                    {'question': 'Какого происхождения Жигулёвские горы?',
                     'answers': ['Вулканического', 'Тектонического', 'Ледникового', 'Эрозионного'], 'correct_answer': 1}
                ]
            },
            {
                'id': 2,
                'name': 'Голубые озёра, Казань',
                'description': 'Система карстовых озёр с кристально чистой водой.',
                'media': '/static/img/Kazan-Goluboe-lk-winter.jpg',
                'fact': 'Видимость под водой достигает 40 метров.',
                'lat': 49.154085,
                'lon': 55.913672,
                'address': 'Татарстан, Высокогорский р-н, пос. Щербаково',
                'map_iframe': 'https://yandex.ru/map-widget/v1/?ll=49.154085%2C555.913672&z=16&pt=49.154085%2C55.913672%2Cpm2rdl',
                'quiz': [
                    {'question': 'Какая температура воды в Голубых озёрах круглый год?',
                     'answers': ['0 °C', '+10 °C', '+4 °C', '+20 °C'], 'correct_answer': 2},
                    {'question': 'Какая видимость под водой?', 'answers': ['10 м', '20 м', '40 м', '60 м'],
                     'correct_answer': 2},
                    {'question': 'Какого происхождения озёра?',
                     'answers': ['Ледникового', 'Карстового', 'Вулканического', 'Речного'], 'correct_answer': 1}
                ]
            },
            {
                'id': 3,
                'name': 'Кунгурская ледяная пещера, Пермский край',
                'description': 'Одна из крупнейших карстовых пещер в мире.',
                'media': '/static/img/По_гротам_пещеры_1.jpg',
                'fact': 'Экскурсии проводятся с 1914 года.',
                'lat': 57.006092,
                'lon': 57.006092,
                'address': 'Пермский край, село Филипповка',
                'map_iframe': 'https://yandex.ru/map-widget/v1/?ll=57.006092%2C57.006092&z=16&pt=57.006092%2C57.006092%2Cpm2rdl',
                'quiz': [
                    {'question': 'Сколько гротов в Кунгурской ледяной пещере?', 'answers': ['12', '48', '100', '25'],
                     'correct_answer': 1},
                    {'question': 'С какого года проводятся экскурсии?', 'answers': ['1900', '1914', '1925', '1950'],
                     'correct_answer': 1},
                    {'question': 'Сколько озёр в пещере?', 'answers': ['20', '50', '70', '100'], 'correct_answer': 2}
                ]
            },
            {
                'id': 4,
                'name': 'Национальный парк «Марий Чодра», Марий Эл',
                'description': 'Заповедный лес с реликтовыми дубравами.',
                'media': '/static/img/Осень_на_р.Илеть.jpg',
                'fact': 'По легенде, под дубом ночевал Емельян Пугачёв.',
                'lat': 48.311615,
                'lon': 56.160590,
                'address': 'Марий Эл, Звениговский р-н, пос. Красногорский',
                'map_iframe': 'https://yandex.ru/map-widget/v1/?ll=48.311615%2C56.160590&z=16&pt=48.311615%2C56.160590%2Cpm2rdl',
                'quiz': [
                    {'question': 'С каким историческим лицом связан дуб в «Марий Чодра»?',
                     'answers': ['Стенька Разин', 'Иван Грозный', 'Пугачёв', 'Пётр I'], 'correct_answer': 2},
                    {'question': 'Что охраняется в парке?',
                     'answers': ['Горы', 'Реликтовые дубравы', 'Степи', 'Пустыни'], 'correct_answer': 1},
                    {'question': 'Сколько лет дубу Пугачёва?', 'answers': ['100', '200', '400', '600'],
                     'correct_answer': 2}
                ]
            },
            {
                'id': 5,
                'name': 'Керженский заповедник, Нижегородская область',
                'description': 'Биосферный резерват ЮНЕСКО.',
                'media': '/static/img/Керженец_-_могучая_река.jpg',
                'fact': 'Обитают более 170 видов птиц.',
                'lat': 44.815366,
                'lon': 56.497214,
                'address': 'Нижегородская обл., Борский р-н, пос. Рустай',
                'map_iframe': 'https://yandex.ru/map-widget/v1/?ll=44.815366%2C56.497214&&z=16&pt=44.815366%2C56.497214&%2Cpm2rdl',
                'quiz': [
                    {'question': 'Какой статус ЮНЕСКО имеет заповедник?',
                     'answers': ['Объект наследия', 'Геопарк', 'Культурный ландшафт', 'Биосферный резерват'],
                     'correct_answer': 3},
                    {'question': 'Сколько видов птиц обитает?', 'answers': ['50', '100', '170', '250'],
                     'correct_answer': 2},
                    {'question': 'Что охраняется в заповеднике?',
                     'answers': ['Горы', 'Степи', 'Леса и болота', 'Пустыни'], 'correct_answer': 2}
                ]
            }
        ]
    }
}


@app.route('/route/<int:route_id>')
def route_detail(route_id):
    route = ROUTES.get(route_id)
    if not route:
        return render_template('404.html'), 404

    session_key = f'progress_{route_id}'
    if session_key not in flask.session:
        flask.session[session_key] = []

    progress = flask.session.get(session_key, [])
    total = len(route['checkpoints'])
    completed = len(progress)

    # Проверяем избранные точки для текущего пользователя
    user_email = flask.request.cookies.get('mail_')
    favorites = []
    user_logged_in = False

    if user_email:
        user = db_sess.query(User).filter(User.email == user_email).first()
        if user:
            user_logged_in = True
            liked_items = db_sess.query(Liked).filter(Liked.user_id == user.id, Liked.route_id == route_id).all()
            favorites = [item.checkpoint_id for item in liked_items]

    return render_template(
        'route_detail.html',
        route=route,
        progress=progress,
        completed=completed,
        total=total,
        favorites=favorites,
        user_logged_in=user_logged_in
    )


@app.route('/route/<int:route_id>/checkpoint/<int:checkpoint_id>')
def checkpoint(route_id, checkpoint_id):
    route = ROUTES.get(route_id)
    if not route:
        return render_template('404.html'), 404

    cp = next((c for c in route['checkpoints'] if c['id'] == checkpoint_id), None)
    if not cp:
        return render_template('404.html'), 404

    session_key = f'progress_{route_id}'
    progress = flask.session.get(session_key, [])

    checkpoints = route['checkpoints']
    current_index = next(i for i, c in enumerate(checkpoints) if c['id'] == checkpoint_id)
    next_cp = checkpoints[current_index + 1] if current_index + 1 < len(checkpoints) else None

    # Проверяем, в избранном ли эта точка
    user_email = flask.request.cookies.get('mail_')
    is_favorite = False
    user_logged_in = False

    if user_email:
        user = db_sess.query(User).filter(User.email == user_email).first()
        if user:
            user_logged_in = True
            liked = db_sess.query(Liked).filter(
                Liked.user_id == user.id,
                Liked.route_id == route_id,
                Liked.checkpoint_id == checkpoint_id
            ).first()
            is_favorite = bool(liked)

    return render_template(
        'checkpoint.html',
        route=route,
        checkpoint=cp,
        progress=progress,
        next_cp=next_cp,
        is_favorite=is_favorite,
        user_logged_in=user_logged_in
    )


@app.route('/route/<int:route_id>/checkpoint/<int:checkpoint_id>/quiz', methods=['GET', 'POST'])
def quiz(route_id, checkpoint_id):
    route = ROUTES.get(route_id)
    if not route:
        return render_template('404.html'), 404

    cp = next((c for c in route['checkpoints'] if c['id'] == checkpoint_id), None)
    if not cp:
        return render_template('404.html'), 404

    session_key = f'quiz_progress_{route_id}_{checkpoint_id}'

    # Инициализация прогресса викторины
    if session_key not in flask.session:
        flask.session[session_key] = {
            'current_question': 0,
            'correct_answers': 0,
            'completed': False
        }

    quiz_progress = flask.session[session_key]
    current_q_index = quiz_progress['current_question']
    quiz_questions = cp.get('quiz', [])

    result = None
    quiz_completed = quiz_progress.get('completed', False)
    show_next_button = False

    if flask.request.method == 'POST' and not quiz_completed:
        if 'answer' in flask.request.form:
            # Пользователь ответил на вопрос
            user_answer = flask.request.form.get('answer', type=int)
            current_question = quiz_questions[current_q_index]

            if user_answer == current_question['correct_answer']:
                quiz_progress['correct_answers'] += 1
                result = True
            else:
                result = False

            show_next_button = True
            flask.session[session_key] = quiz_progress

        else:
            # Пользователь нажал "Следующий вопрос"
            quiz_progress['current_question'] += 1

            # Проверка завершения викторины
            if quiz_progress['current_question'] >= len(quiz_questions):
                quiz_progress['completed'] = True

                # Если все ответы правильные, засчитываем точку
                if quiz_progress['correct_answers'] == len(quiz_questions):
                    progress_key = f'progress_{route_id}'
                    progress = flask.session.get(progress_key, [])
                    if checkpoint_id not in progress:
                        progress.append(checkpoint_id)
                        flask.session[progress_key] = progress

            flask.session[session_key] = quiz_progress
            # Перенаправляем на ту же страницу, чтобы обновить вопрос
            return redirect(flask.url_for('quiz', route_id=route_id, checkpoint_id=checkpoint_id))

    checkpoints = route['checkpoints']
    current_index = next(i for i, c in enumerate(checkpoints) if c['id'] == checkpoint_id)
    next_cp = checkpoints[current_index + 1] if current_index + 1 < len(checkpoints) else None

    # Обновляем current_q_index после возможного изменения
    current_q_index = quiz_progress['current_question']
    current_question = quiz_questions[current_q_index] if current_q_index < len(quiz_questions) else None

    return render_template(
        'quiz.html',
        route=route,
        checkpoint=cp,
        current_question=current_question,
        question_number=current_q_index + 1,
        total_questions=len(quiz_questions),
        result=result,
        show_next_button=show_next_button,
        quiz_completed=quiz_completed,
        correct_answers=quiz_progress['correct_answers'],
        next_cp=next_cp
    )


@app.route('/route/<int:route_id>/checkpoint/<int:checkpoint_id>/reset_quiz')
def reset_quiz(route_id, checkpoint_id):
    session_key = f'quiz_progress_{route_id}_{checkpoint_id}'
    flask.session.pop(session_key, None)
    return redirect(flask.url_for('quiz', route_id=route_id, checkpoint_id=checkpoint_id))


if __name__ == "__main__":
    app.run()