import asyncio
import json
import requests
import uuid

from flask_mail import Message, Mail
from flask_apscheduler import APScheduler
from sqlalchemy.dialects.sqlite import insert
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
app.config['MAIL_SERVER']='smtp.yandex.ru'
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



# @app.route("/search", methods=['GET', 'POST'])
# def search():
#     if flask.request.method == "POST":
#         typed = flask.request.json["typed"]
#         print(db_sess.query(games_.Game.name).filter(games_.Game.name.contains(typed)).all())
#         return jsonify(
#             {
#                 "games" : [i[0] for i in db_sess.query(games_.Game.name).filter(games_.Game.name.contains(typed)).all()]
#             }
#         )
#     if flask.request.method == "GET":
#         return send_file("static/search.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        existing_users = db_sess.query(User).filter((User.email == form.username.data) | (User.login == form.username.data)).all()
        if existing_users:
            for i in existing_users:
                if i.password == form.password.data:
                    res = flask.make_response(redirect('/'))
                    res.set_cookie("mail_", value=str(i.email))
                    res.set_cookie("login_", value=str(i.login))
                    res.set_cookie("password_", value=str(i.password))
                    return res
        return render_template('login.html', title='Авторизация', form=form, message="Неверный логин (или почта) или пароль")
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
        db_sess.query(User).filter(User.email == flask.request.cookies.get("mail_")).update({'login':form.username.data, 'password':form.username.data})
        db_sess.commit()
        return res
    return render_template('edit.html', title='Регистрация', form=form)
# @app.route('/game/<name>', methods=['GET', 'POST'])
# def game(name):
#     game = db_sess.query(Prices).filter(Prices.name == name).first()
#     all_ = {}
#     form = LikeForm()
#     if form.validate_on_submit():
#         n_g = json.loads("[]")
#         games = db_sess.query(Liked.games).filter(Liked.login == flask.request.cookies.get('login_')).first()
#         if games:
#             n_g = json.loads(games[0])
#         if name not in n_g:
#             n_g.append(name)
#             db_sess.query(Liked).filter(Liked.login == flask.request.cookies.get('login_')).update(
#                 {'games': json.dumps(n_g)})
#             db_sess.commit()
#             form.submit.label.text = "Удалить из избранного"
#         else:
#             n_g.pop(n_g.index(name))
#             db_sess.query(Liked).filter(Liked.login == flask.request.cookies.get('login_')).update(
#                 {'games': json.dumps(n_g)})
#             db_sess.commit()
#             form.submit.label.text = "Добавить в избранное"
#
#     if not game:
#         game = Prices()
#         game.app_id = int(db_sess.query(games_.Game.app_id).filter(games_.Game.name == name).first()[0])
#         game.last_modification = str(datetime.date.today())
#         game.name = name
#         game.all_paths = str(steam_keys.find_key("".join([i for i in name if ord(i) != 8482 and ord(i) != 174]).replace(" ", "-").lower()))
#         all_ = json.loads(game.all_paths.replace("'", '"'))
#         db_sess.flush()
#         db_sess.add(game)
#         db_sess.commit()
#     elif datetime.datetime.strptime(game.last_modification, "%Y-%m-%d") < datetime.datetime.strptime(str(datetime.datetime.today())[:str(datetime.datetime.today()).find(" ")], "%Y-%m-%d"):
#         all_ = steam_keys.find_key("".join([i for i in name if ord(i) != 8482 and ord(i) != 174]).replace(" ", "-").lower())
#         db_sess.flush()
#         db_sess.query(Prices).filter(Prices.name == name).update({'last_modification': str(datetime.date.today()), 'all_paths':str(all_)})
#         db_sess.commit()
#     else:
#         all_ = json.loads(game.all_paths.replace("'", '"'))
#     return render_template('game.html', prices=all_[0], links=all_[1], name_=name, form=form)
#
#
# @app.route("/liked", methods=['GET', 'POST'])
# def liked():
#     all_ = []
#
#     games = db_sess.query(Liked.games).filter(Liked.login == flask.request.cookies.get('login_')).first()
#     if games:
#         all_ = json.loads(games[0])
#     return render_template("liked.html", games = all_)


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
                       'авиации и оружейного дела Поволжского федерального округа. '
                       'Посетите места, где создавалась техника, покорявшая космос и '
                       'дороги. Узнайте о достижениях российского инженерного гения, '
                       'в том числе о легендарных советских ракетах-носителях, танках '
                       'и самолётах, которые определяли ход истории XX века.',
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
                'description': 'Один из главных символов космической истории Поволжья. '
                               'У входа установлена настоящая ракета-носитель «Союз». '
                               'Это не просто музей — это храм советской космической мечты. '
                               'Величественная ракета на входе сразу производит неизгладимое впечатление. '
                               'Внутри центра разместилась одна из лучших коллекций космических аппаратов, '
                               'спускаемых аппаратов и оборудования. Здесь вы можете увидеть настоящие '
                               'кабины космических кораблей, скафандры космонавтов, приборы из кабин '
                               '«Союзов» и научные инструменты. Интерактивные экспонаты позволяют '
                               'почувствовать, что такое невесомость. Музей рассказывает о роли Самары '
                               '(Куйбышева) в советской космической программе, о вкладе её инженеров '
                               'и конструкторов в освоение космоса. Видеолекции и кинофильмы дополняют '
                               'впечатление от экспозиции.',
                'media': '/static/img/municipal-museum-cosmic.jpg',
                'fact': 'Самара (в советское время — Куйбышев) была закрытым центром '
                        'ракетно-космической промышленности СССР.',
                'lat': 50.145226,
                'lon': 53.212701,
                'address': 'Самара, пр. Ленина, 21',
                'map_iframe': (
                    'https://yandex.ru/map-widget/v1/'
                    '?ll=50.145226%2C53.212701'
                    '&z=16'
                    '&pt=50.145226%2C53.212701%2Cpm2rdl'
                ),
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
                'description': 'Крупнейший в России музей техники под открытым небом: '
                               'самолёты, танки, подводная лодка и автомобили. '
                               'Это грандиозный парк военной и гражданской техники, '
                               'который захватывает дух своим масштабом. На территории музея '
                               'выстроены в боевые порядки советские и российские самолёты, '
                               'начиная с легендарных штурмовиков И-16 и заканчивая современными '
                               'истребителями. Здесь же находятся грозные танки, начиная с '
                               'лёгких Т-26 и кончая мощными боевыми машинами поздних версий. '
                               'Подлинная подводная лодка Б-307, выкрашенная в чёрный цвет, '
                               'позволяет побывать внутри настоящей боевой машины и понять, '
                               'в каких условиях работали советские подводники. Автомобили, '
                               'начиная с редких моделей советской эпохи и заканчивая современными, '
                               'показывают развитие отечественного автомобилестроения. '
                               'Музей — это оборотень, способный вернуть вас на восемь десятков лет назад.',
                'media': '/static/img/Technical_museum,_Togliatti,_Russia-5.JPG',
                'fact': 'В коллекции музея более 460 экспонатов, включая '
                        'настоящую подводную лодку Б-307.',
                'lat': 49.249808,
                'lon': 53.553031,
                'address': 'Тольятти, ул. Сахарова, 1',
                'map_iframe': (
                    'https://yandex.ru/map-widget/v1/'
                    '?ll=49.249808%2C53.553031'
                    '&z=16'
                    '&pt=49.249808%2C53.553031%2Cpm2rdl'
                ),
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
                'description': 'Уникальная экспозиция из более чем 30 воздушных судов '
                               'под открытым небом на территории аэродрома. '
                               'Это музей в подлинном смысле слова — каждый самолёт можно не только '
                               'рассматривать снаружи, но и заходить внутрь, садиться в кабины и проходить '
                               'по салонам. Здесь расположены легендарные ТУ-104, первый советский реактивный '
                               'пассажирский самолёт, красавец ТУ-144, АН-12, АН-2 (кукуруза) и многие другие. '
                               'Каждый самолёт имеет подробную табличку с информацией о его истории. '
                               'Ульяновский аэродром всегда был не просто площадкой для испытаний, '
                               'но и творческой лабораторией авиационной мысли. Музей создан в честь '
                               'вклада Ульяновска в развитие российской гражданской авиации. '
                               'Это место, где чувствуется дух авиационной эпохи.',
                'media': '/static/img/Tupolev_Tu-144,_Ulyanovsk_Aircraft_Museum.jpg',
                'fact': 'Ульяновск считается авиационной столицей России — '
                        'здесь производили самолёты Ту-204 и Ан-124 «Руслан».',
                'lat': 48.234580,
                'lon': 54.289727,
                'address': 'Ульяновск, ул. Авиационная, 20а',
                'map_iframe': (
                    'https://yandex.ru/map-widget/v1/'
                    '?ll=48.234580%2C54.289727'
                    '&z=16'
                    '&pt=48.234580%2C54.289727%2Cpm2rdl'
                ),
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
                'description': 'Музей крупнейшего в России производителя грузовых '
                               'автомобилей — многократного победителя ралли «Дакар». '
                               'КАМАЗ — это история успеха советской и российской техники. '
                               'Музей расположен при заводе и показывает эволюцию КАМАЗа от первых '
                               'тяжелогруженых грузовиков до современных мощных машин. '
                               'Здесь можно увидеть макеты цехов, где производятся автомобили, '
                               'исторические прототипы, первые выпущенные машины с автографами '
                               'конструкторов. Особенно впечатляющей является секция, посвящённая '
                               'участию КАМАЗа в ралли «Дакар» — здесь выставлены настоящие '
                               'раллийные машины, обтянутые в боевую раскраску и с видимыми следами '
                               'пустынных испытаний. Фотографии и кинохроники рассказывают о подвигах '
                               'КАМАЗ-мастера в самом сложном ралли в мире. Музей демонстрирует, '
                               'как инженерная мысль и упорство могут преодолевать любые препятствия.',
                'media': '/static/img/kam.jpg',
                'fact': 'Команда «КАМАЗ-мастер» одержала более 19 побед '
                        'на ралли «Дакар» — абсолютный рекорд.',
                'lat': 52.446574,
                'lon': 55.74731,
                'address': 'Набережные Челны, пр. Автозаводский, 2',
                'map_iframe': (
                    'https://yandex.ru/map-widget/v1/'
                    '?ll=52.446574%2C55.74731'
                    '&z=16'
                    '&pt=52.446574%2C55.74731%2Cpm2rdl'
                ),
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
        'description': 'Маршрут по святыням и духовным центрам Поволжья — '
                       'монастыри, соборы и места паломничества разных конфессий. '
                       'Откройте для себя места, где на протяжении столетий люди '
                       'искали спасение и смысл жизни. Посетите величественные монастыри '
                       'и святые места, где ощущается особая благодать и спокойствие.',
        'map_iframe': (
            'https://yandex.ru/map-widget/v1/'
            '?ll=47.688400%2C55.518300'
            '&z=6'
            '&pt=43.245493%2C55.040409%2Cpm2rdl'
            '~48.731677%2C55.903792%2Cpm2rdl'
            '~56.230037%2C57.392215%2Cpm2rdl'
            '~45.064338%2C56.083459%2Cpm2rdl'
            '~45.181674%2C54.181612%2Cpm2rdl'
        ),
        'checkpoints': [
            {
                'id': 1,
                'name': 'Серафимо-Дивеевский монастырь',
                'description': 'Один из крупнейших православных монастырей России, '
                               'связанный с именем преподобного Серафима Саровского. '
                               'Это священное место притяжения паломников со всего мира. '
                               'Дивеевский монастырь является женским и известен своей благодатью. '
                               'Здесь сохранилась «канава» — святая борозда, прорытая ногами '
                               'Преподобного Серафима, которую паломники со смирением обходят '
                               'для очищения. Монастырь включает несколько величественных храмов, '
                               'выстроенных в разное время, с золотыми куполами, видимыми издалека. '
                               'В духовной сокровищнице монастыря хранятся мощи святых, в том числе '
                               'мощи преподобного Серафима Саровского. Ежегодно сюда приходят '
                               'тысячи паломников, ищущих исцеления и духовного возрождения. '
                               'Молитвенная атмосфера этого места ощущается на каждом шагу.',
                'media': '/static/img/Diveyevo_(51263813251).jpg',
                'fact': 'Серафим Саровский — один из самых почитаемых русских '
                        'святых, канонизированный в 1903 году по указу Николая II.',
                'lat': 43.245493,
                'lon': 55.040409,
                'address': 'Нижегородская обл., с. Дивеево',
                'map_iframe': (
                    'https://yandex.ru/map-widget/v1/'
                    '?ll=43.245493%2C55.040409'
                    '&z=16'
                    '&pt=43.245493%2C55.040409%2Cpm2rdl'
                ),
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
                'description': 'Действующий мужской монастырь XVII века на берегу '
                               'Раифского озера в окружении заповедного леса. '
                               'Раифский монастырь славится своей отдалённостью и спокойствием — '
                               'его расположение вдалеке от больших городов делает его истинным '
                               'монашеским центром, где можно услышать пение, перекрывающее шум мира. '
                               'Красивая территория монастыря обнесена стеной, увенчанной куполами. '
                               'Главный храм поражает своей архитектурой и убранством. '
                               'Монастырь имеет давнюю историю — он был основан в XVII веке '
                               'иноками, пришедшими из Палестины. Раифское озеро, на берегу которого '
                               'стоит монастырь, дополняет впечатление святости этого места. '
                               'Здесь издавна приносят клятвы и просят исцеления. '
                               'Монастырь привлекает не только верующих, но и любителей природы, '
                               'так как окружающий его лес — это охраняемый природный объект.',
                'media': '/static/img/Raifsky_Monastery_08-2016_photo6.jpg',
                'fact': 'Главная святыня монастыря — Грузинская икона Божией Матери, '
                        'которой приписывают чудотворную силу.',
                'lat': 48.731677,
                'lon': 55.903792,
                'address': 'Татарстан, Зеленодольский р-н, пос. Раифа',
                'map_iframe': (
                    'https://yandex.ru/map-widget/v1/'
                    '?ll=48.731677%2C55.903792'
                    '&z=16'
                    '&pt=48.731677%2C55.903792%2Cpm2rdl'
                ),
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
                'description': 'Монастырь на вершине Белой горы — «Уральский Афон». '
                               'Величественный Крестовоздвиженский собор виден издалека. '
                               'Белогорский монастырь — это чудо архитектуры, возникшее на вершине '
                               'горы среди уральских лесов. Добраться до него — это само по себе подвиг. '
                               'Крестовоздвиженский собор, для строительства которого потребовалось '
                               'несколько десятилетий упорного труда, выглядит как дворец неземной красоты. '
                               'Его высокие стены, золотые кресты и куполы делают его видимым за многие '
                               'километры вокруг. Монастырь заслужил прозвище «Уральский Афон» за то, '
                               'что, подобно афонским монастырям, он расположен на вершине горы и служит '
                               'центром монашеской жизни. Здесь не только молятся, но и восстанавливают '
                               'деревянные шедевры древней Руси. Музей, входящий в комплекс, демонстрирует '
                               'работы по восстановлению икон и церковных предметов. Панорама с вершины Белой '
                               'горы захватывает дух неповторимой красотой уральского ландшафта.',
                'media': '/static/img/Белогорский_Свято-Николаевский_православно-миссионерский_мужской_монастырь.jpg',
                'fact': 'Крестовоздвиженский собор Белогорского монастыря — '
                        'третий по величине православный храм в России.',
                'lat': 56.230037,
                'lon': 57.392215,
                'address': 'Пермский край, Кунгурский р-н, с. Белая Гора',
                'map_iframe': (
                    'https://yandex.ru/map-widget/v1/'
                    '?ll=56.230037%2C57.392215'
                    '&z=16'
                    '&pt=56.230037%2C57.392215%2Cpm2rdl'
                ),
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
                'description': 'Древний монастырь на берегу Волги, основанный в XV веке '
                               'преподобным Макарием. Здесь зародилась знаменитая ярмарка. '
                               'Макарьевский монастырь — это не просто религиозный центр, '
                               'но и историческое место, где перекрещиваются судьбы людей разных поколений. '
                               'На берегу Волги, на месте, которое выбрал сам преподобный Макарий, '
                               'выросли стены монастыря. Близость к воде, тишина и святость этого места '
                               'привлекали паломников на протяжении столетий. Возле монастыря развивалась '
                               'торговля, и вскоре здесь возникла ярмарка, которая станет самой крупной '
                               'в России. Макарьевская ярмарка превращала окрестности в временный город, '
                               'где встречались купцы со всего света. Монастырь, таким образом, '
                               'был не только духовным, но и экономическим центром. Сегодня здесь '
                               'ощущается слой истории — стены хранят воспоминания о событиях, '
                               'которые пересекали столетия.',
                'media': '/static/img/Вид_на_Макарьевский_монастырь_с_Волги_01.jfif',
                'fact': 'Макарьевская ярмарка, основанная у стен монастыря, '
                        'позднее переехала в Нижний Новгород и стала крупнейшей в стране.',
                'lat': 45.064338,
                'lon': 56.083459,
                'address': 'Нижегородская обл., пос. Макарьево',
                'map_iframe': (
                    'https://yandex.ru/map-widget/v1/'
                    '?ll=45.064338%2C56.083459'
                    '&z=16'
                    '&pt=45.064338%2C56.083459%2Cpm2rdl'
                ),
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
                'description': 'Один из крупнейших соборов России, освящённый '
                               'в честь святого праведного воина Феодора Ушакова. '
                               'Собор святого Феодора Ушакова в Саранске — это архитектурный шедевр '
                               'современности. Его белокаменные стены и золотые кресты отражают небо '
                               'и создают впечатление света и чистоты. Собор посвящён памяти великого '
                               'русского адмирала, чья неустанная служба спасла многие жизни. '
                               'Архитектура собора сочетает традиции древней Руси с современной строительной '
                               'техникой. Внутри собора поражает гармония пропорций, роспись стен '
                               'и мозаики, которые требовали многолетней кропотливой работы. '
                               'Каждая деталь говорит о чистоте веры и любви к искусству. '
                               'Собор становится центром духовной жизни города и привлекает не только '
                               'верующих, но и исследователей архитектуры. Его звон колоколов '
                               'слышен далеко за пределами города и напоминает об основных ценностях бытия.',
                'media': '/static/img/St._Theodore_Ushakov_Cathedral.jpg',
                'fact': 'Адмирал Фёдор Ушаков не проиграл ни одного морского '
                        'сражения и был канонизирован в 2001 году.',
                'lat': 45.181674,
                'lon': 54.181612,
                'address': 'Саранск, ул. Советская, 53',
                'map_iframe': (
                    'https://yandex.ru/map-widget/v1/'
                    '?ll=45.181674%2C54.181612'
                    '&z=16'
                    '&pt=45.181674%2C54.181612%2Cpm2rdl'
                ),
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
        'description': 'Маршрут по фортификационным сооружениям и оборонительным '
                       'рубежам — от древних кремлей до секретного бункера Сталина. '
                       'Отследите историю воинской славы России, узнайте о стратегических '
                       'местах и бункерах, скрывавших судьбоносные решения. '
                       'Посетите крепости, которые служили щитом Российского государства.',
        'complexity': 'сложная',
        'duration': '5 часов',
        'map_iframe': (
            'https://yandex.ru/map-widget/v1/'
            '?ll=50.207600%2C54.780700'
            '&z=5'
            '&pt=44.003417%2C556.328120%2Cpm2rdl'
            '~50.097857%2C53.196683%2Cpm2rdl'
            '~48.661172%2C55.772000%2Cpm2rdl'
            '~53.206784%2C56.850721%2Cpm2rdl'
            '~55.108391%2C51.755434%2Cpm2rdl'
        ),
        'checkpoints': [
            {
                'id': 1,
                'name': 'Нижегородский кремль',
                'description': 'Мощная кирпичная крепость начала XVI века с 13 башнями, '
                               'стоящая на высоком берегу при слиянии Оки и Волги. '
                               'Нижегородский кремль — это один из самых грозных и красивых кремлей России. '
                               'Его красные кирпичные стены, возвышающиеся над водами двух рек, '
                               'производят неизгладимое впечатление. Каждая из 13 башен имеет своё имя '
                               'и историю, рассказывающие о событиях прошлого. Одни башни охраняли ворота, '
                               'другие служили узлами обороны. Некоторые были жилыми, другие использовались '
                               'для хранения припасов. Между башнями пролегают стены длиной около двух километров, '
                               'отвоёвывающие пространство у вод. Высота стен достигает 13 метров — '
                               'эта величина была оптимальна для защиты от врага на расстоянии выстрела. '
                               'Стены кремля никогда не были взяты штурмом — они были непреодолимой преградой '
                               'для враждебных войск. Сегодня кремль — это не только памятник истории, '
                               'но и центр культурной жизни города.',
                'media': '/static/img/Вид_на_Нижегородский_кремль_с_высоты_cropped.jpg',
                'fact': 'Нижегородский кремль ни разу в своей истории не был '
                        'взят штурмом неприятеля.',
                'lat': 44.003417,
                'lon': 56.328120,
                'address': 'Нижний Новгород, Кремль, 1',
                'map_iframe': (
                    'https://yandex.ru/map-widget/v1/'
                    '?ll=44.003417%2C56.328120'
                    '&z=16'
                    '&pt=44.003417%2C556.328120%2Cpm2rdl'
                ),
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
                'description': 'Секретный бункер на глубине 37 метров — запасной '
                               'командный пункт Ставки Верховного Главнокомандующего. '
                               'Этот бункер — одна из самых засекреченных строек советской эпохи. '
                               'Построенный в годы Великой Отечественной войны, он служил неприступным '
                               'убежищем для высшего советского командования. На глубине 37 метров, '
                               'под толстым слоем грунта и железобетона, располагались операционные залы, '
                               'где генерал-полковник Александр Василевский координировал военные операции. '
                               'Бункер оснащён системой вентиляции, фильтрации воздуха и водоснабжения, '
                               'рассчитанной на длительное пребывание. Его стены защищены от ядерного взрыва, '
                               'а коридоры спроектированы так, чтобы максимально амортизировать ударные волны. '
                               'После войны бункер продолжал использоваться как оперативный центр. '
                               'Только в 1990 году тайна была раскрыта, и бункер стал доступен для посещения. '
                               'Сегодня это свидетельство напряженности холодной войны и инженерной мысли '
                               'советского военного ведомства.',
                'media': "/static/img/Stalin's_Bunker_0020.jpg",
                'fact': 'О существовании бункера общественность узнала только '
                        'в 1990 году, спустя почти 50 лет после постройки.',
                'lat': 50.097857,
                'lon': 53.196683,
                'address': 'Самара, ул. Фрунзе, 167',
                'map_iframe': (
                    'https://yandex.ru/map-widget/v1/'
                    '?ll=50.097857%2C53.196683'
                    '&z=16'
                    '&pt=50.097857%2C53.196683%2Cpm2rdl'
                ),
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
                'description': 'Крепость XVI века, основанная Иваном Грозным как '
                               'плацдарм для взятия Казани. Объект ЮНЕСКО. '
                               'Свияжск — это уникальный исторический памятник, созданный в экстремальных '
                               'условиях. Когда Иван Грозный решил завоевать Казань, он понял, что ему нужна '
                               'опорная точка на подступах к городу. За четыре недели был построен целый град '
                               'из деревянных бревен, который был сплавлен по Волге на 1000 км в разобранном '
                               'состоянии и собран на месте. Свияжск расположен на острове, что делало его '
                               'естественно укреплённой позицией. Стены и башни, выстроенные столь быстро, '
                               'оказались неприступны для татарского войска. Со своего неприступного острова '
                               'русские войска совершали вылазки, терзали врага и готовили плацдарм для '
                               'наступления на саму Казань. После взятия Казани Свияжск остался важным центром, '
                               'где строились деревянные храмы с фресковой росписью. Сегодня остров Свияжск '
                               'включён в список ЮНЕСКО как памятник архитектуры и инженерной мысли.',
                'media': '/static/img/Троицкая_улица_Свияжска,_2019-01-03.jpg',
                'fact': 'Свияжск был построен всего за 4 недели в 1551 году — '
                        'деревянную крепость сплавили по Волге в разобранном виде.',
                'lat': 48.661172,
                'lon': 55.772000,
                'address': 'Татарстан, Зеленодольский р-н, с. Свияжск',
                'map_iframe': (
                    'https://yandex.ru/map-widget/v1/'
                    '?ll=48.661172%2C55.772000'
                    '&z=14'
                    '&pt=48.661172%2C55.772000%2Cpm2rdl'
                ),
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
                'description': 'Музей при знаменитом Ижевском оружейном заводе — '
                               'одном из старейших оружейных предприятий России. '
                               'Ижевский оружейный завод — это легенда отечественного оружейного мастерства. '
                               'Музей демонстрирует эволюцию русского стрелкового оружия от первых мушкетов '
                               'и ружей XIX века до современных боевых систем. Здесь выставлены винтовки, '
                               'которые использовались в войнах и революциях, боевые карабины, которые '
                               'меняли историю боевых действий. Особенно впечатляют экспонаты, показывающие, '
                               'как развивалась конструкция оружия: от простых гладкоствольных до сложных '
                               'систем с высокой скорострельностью. Музей наглядно демонстрирует связь между '
                               'техническим прогрессом и боевой эффективностью. На стендах представлены '
                               'чертежи, макеты производственных процессов, фотографии заводских цехов. '
                               'Это не просто оружейная коллекция — это повествование о роли '
                               'отечественного ружья в истории России.',
                'media': '/static/img/Музейно-выставочный_комплекс_имени_Калашникова_(Ижевск).jpg',
                'fact': 'Ижевский оружейный завод основан в 1807 году и непрерывно '
                        'производит стрелковое оружие более 200 лет.',
                'lat': 53.206784,
                'lon': 56.850721,
                'address': 'Ижевск, ул. Бородина, 19',
                'map_iframe': (
                    'https://yandex.ru/map-widget/v1/'
                    '?ll=53.206784%2C56.850721'
                    '&z=16'
                    '&pt=53.206784%2C56.850721%2Cpm2rdl'
                ),
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
                'description': 'Историческое место Оренбургской крепости — форпоста '
                               'на границе Европы и Азии, воспетого Пушкиным. '
                               'Оренбургская крепость стояла на перекрёстке дорог, ведущих в Азию. '
                               'Здесь встречались миры — европейский и азиатский, христианский и мусульманский. '
                               'Крепость была разработана как оборонительная позиция против казацких набегов '
                               'и калмыцких кочевников. Её стены видели героическую защиту от войск Емельяна '
                               'Пугачёва, когда гарнизон, опираясь на дух и профессионализм офицеров, '
                               'выдержал осаду мятежной армии. Александр Сергеевич Пушкин посетил крепость '
                               'и воспроизвел её образ в своем романе «Капитанская дочка», назвав крепость '
                               'Белогорской. Губернаторский музей, расположенный в исторических зданиях '
                               'на территории бывшей крепости, рассказывает историю города и края. '
                               'Это место, где литература встречается с историей, вымысел — с реальностью.',
                'media': '/static/img/Historical_museum_of_Orenburg.jpg',
                'fact': 'Именно Оренбургская крепость стала прообразом Белогорской '
                        'крепости в «Капитанской дочке» Пушкина.',
                'lat': 55.108391,
                'lon': 51.755434,
                'address': 'Оренбург, ул. Набережная, 29',
                'map_iframe': (
                    'https://yandex.ru/map-widget/v1/'
                    '?ll=55.108391%2C51.755434'
                    '&z=15'
                    '&pt=55.108391%2C51.755434%2Cpm2rdl'
                ),
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
        'description': 'Маршрут по старинным торговым городам: ярмарки, '
                       'купеческие особняки, торговые улицы и провинциальный модерн. '
                       'Узнайте, как процветала торговля в XIX веке, посетите роскошные '
                       'дома богатых купцов и почувствуйте дух эпохи, когда Поволжье '
                       'было экономическим сердцем империи.',
        'complexity': 'средняя',
        'duration': '4 часа',
        'map_iframe': (
            'https://yandex.ru/map-widget/v1/'
            '?ll=47.431400%2C54.000100'
            '&z=6'
            '&pt=43.961313%2C56.328324%2Cpm2rdl'
            '~50.096159%2C53.193975%2Cpm2rdl'
            '~52.056050%2C55.756189%2Cpm2rdl'
            '~45.017692%2C53.194220%2Cpm2rdl'
            '~46.021770%2C51.532307%2Cpm2rdl'
        ),
        'checkpoints': [
            {
                'id': 1,
                'name': 'Нижегородская ярмарка',
                'description': 'Главный торговый центр Российской империи — '
                               '«карман России». Ярмарочный комплекс XIX века. '
                               'Нижегородская ярмарка была легендарной торговой структурой, '
                               'которая привлекала купцов со всего света. На её площадях '
                               'велись торговли чаями из Китая, шёлками из Персии, '
                               'драгоценностями из далёких земель и товарами из всех уголков '
                               'Российской империи. Ярмарка существовала всего 30 дней в году, '
                               'но сосредотачивала такой объём товаров, что её оборот превышал '
                               'годовой оборот многих европейских портов. Ярмарочные здания '
                               'были спроектированы лучшими архитекторами и представляли собой '
                               'настоящие сокровищницы разных архитектурных стилей. '
                               'Здесь возникла целая инфраструктура: торговые ряды, '
                               'складские помещения, трактиры, гостиницы и даже театр. '
                               'Нижегородская ярмарка была не просто местом куплю-продажи, '
                               'но центром деловой жизни и культурного обмена.',
                'media': '/static/img/NN-16-05-2022_41.jpg',
                'fact': 'Нижегородская ярмарка в XIX веке была крупнейшей '
                        'в России и третьей по величине в мире.',
                'lat': 43.961313,
                'lon': 56.328324,
                'address': 'Нижний Новгород, ул. Совнаркомовская, 13',
                'map_iframe': (
                    'https://yandex.ru/map-widget/v1/'
                    '?ll=43.961313%2C56.328324'
                    '&z=16'
                    '&pt=43.961313%2C56.328324%2Cpm2rdl'
                ),
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
                'description': 'Жемчужина самарского модерна — купеческий особняк начала '
                               'XX века с уникальными витражами и лепниной. '
                               'Особняк Курлиной — это воплощение мечты богатого купца о красоте '
                               'и современности. Он был построен в начале XX века, когда в моду входил '
                               'модерн с его текучими линиями, растительными мотивами и стремлением '
                               'к синтезу функции и красоты. Фасад особняка поражает изяществом: '
                               'здесь и арочные окна, украшенные резными наличниками, и балконы '
                               'с кованными перилами, и портал входа, украшенный мозаикой. '
                               'Интерьеры особняка ещё более впечатляющи: потолки расписаны по трафарету, '
                               'стены украшены лепниной, в окнах размещены прекрасные витражи. '
                               'Каждая комната в доме — это произведение искусства. Лестница, ведущая '
                               'на второй этаж, кажется парящей в воздухе благодаря искусной конструкции. '
                               'Этот особняк считается одной из лучших достопримечательностей Самары '
                               'и ярким примером модерна в провинциальной России.',
                'media': '/static/img/Особняк_Курлиной_(Самара).jpg',
                'fact': 'Особняк Курлиной считается первым зданием '
                        'в стиле модерн во всей Самаре.',
                'lat': 50.096159,
                'lon': 53.193975,
                'address': 'Самара, ул. Фрунзе, 159',
                'map_iframe': (
                    'https://yandex.ru/map-widget/v1/'
                    '?ll=50.096159%2C53.193975'
                    '&z=16'
                    '&pt=50.096159%2C53.193975%2Cpm2rdl'
                ),
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
                'description': 'Купеческая Елабуга — город-музей с сохранившимися '
                               'торговыми рядами и особняками XIX века. '
                               'Елабуга — это целый город-музей, где время как будто остановилось '
                               'в середине XIX века. Её улицы, выложенные булыжником, '
                               'сохранили облик провинциального купеческого города. '
                               'Торговые ряды с их невысокими, компактными зданиями, приспособленными '
                               'для лавок и складов, в некотором смысле рассказывают о повседневной жизни '
                               'купечества. Особняки, принадлежавшие местным богатым торговцам, '
                               'выстроены в разных стилях — от скромного классицизма до более яркого модерна. '
                               'Елабуга славится не только архитектурой, но и своей связью с литературой и искусством. '
                               'Здесь родился великий художник Иван Шишкин, творчество которого определило '
                               'направление развития русской живописи. Музей имени Шишкина позволяет подробнее '
                               'узнать о его жизни и творчестве. Елабуга сегодня — это уникальный музей живой истории, '
                               'где каждый камень говорит о прошлом.',
                'media': '/static/img/Shishkinskiye_prudy_(park_in_Elabuga)-14.jpg',
                'fact': 'Елабуга — родина художника Ивана Шишкина, '
                        'прославившего красоту русской природы.',
                'lat': 52.056050,
                'lon': 55.756189,
                'address': 'Елабуга, ул. Казанская, 26',
                'map_iframe': (
                    'https://yandex.ru/map-widget/v1/'
                    '?ll=52.056050%2C55.756189'
                    '&z=14'
                    '&pt=52.056050%2C55.756189%2Cpm2rdl'
                ),
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
                'description': 'Главная пешеходная улица Пензы с купеческой застройкой '
                               'XIX века — «пензенский Арбат». '
                               'Улица Московская в Пензе — это главная артерия города, '
                               'где сконцентрирована вся культурная и торговая жизнь. '
                               'Вдоль улицы выстроены трёхэтажные здания с магазинами на первом этаже '
                               'и жилыми или офисными помещениями выше. Архитектура зданий отражает '
                               'переходный период от классицизма к модерну, демонстрируя вкусовые '
                               'предпочтения купечества конца XIX — начала XX века. Улица регулярно '
                               'становилась предметом реконструкции, но её характер остался неизменным: '
                               'это место встреч, торговли и развлечений. На улице Московской находится '
                               'множество кафе, ресторанов и магазинов. Особенно примечателен здесь '
                               'её музей одной картины — уникальный в России музейный проект. '
                               'Улица Московская справедливо называется «пензенским Арбатом» — здесь '
                               'чувствуется дух провинциального русского города, его культура и история.',
                'media': '/static/img/Пенза,_Московская_улица_DSC08850.JPG',
                'fact': 'На улице Московской находится единственный в России '
                        'музей одной картины имени Мясникова.',
                'lat': 45.017692,
                'lon': 53.194220,
                'address': 'Пенза, ул. Московская',
                'map_iframe': (
                    'https://yandex.ru/map-widget/v1/'
                    '?ll=45.017692%2C53.194220'
                    '&z=16'
                    '&pt=45.017692%2C53.194220%2Cpm2rdl'
                ),
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
                'description': 'Пешеходная улица Саратова — «саратовский Арбат» '
                               'с купеческими домами и торговыми пассажами. '
                               'Проспект Столыпина в Саратове — это главная культурная ось города. '
                               'Названный в честь выдающегося реформатора Петра Столыпина, '
                               'проспект протянулся на несколько километров, соединяя исторический центр '
                               'с более новыми районами города. На проспекте расположены купеческие дома, '
                               'выстроенные в разные эпохи и отражающие эволюцию архитектурных вкусов. '
                               'Здесь находятся торговые пассажи с их стеклянными крышами, '
                               'позволяющими делать покупки в любую погоду. Проспект известен как центр '
                               'интеллектуальной жизни Саратова: здесь расположена консерватория, '
                               'музеи и театры. Саратовская консерватория, основанная в 1912 году, '
                               'является третьей по старшинству консерваторией России и выпустила '
                               'множество талантливых музыкантов. Прогулка по проспекту Столыпина '
                               '— это путешествие через эпохи, встреча с архитектурой, '
                               'культурой и историей провинциального русского города.',
                'media': '/static/img/Stolypin_Avenue_in_Saratov_(July_2025)_-_0_2.jpg',
                'fact': 'Саратовская консерватория на проспекте Столыпина — '
                        'третья по старшинству консерватория в России.',
                'lat': 46.021770,
                'lon': 51.532307,
                'address': 'Саратов, пр. Столыпина',
                'map_iframe': (
                    'https://yandex.ru/map-widget/v1/'
                    '?ll=46.021770%2C51.532307'
                    '&z=16'
                    '&pt=46.021770%2C51.532307%2Cpm2rdl'
                ),
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
        'description': 'Маршрут по уникальным природным объектам Поволжья — '
                       'национальные парки, пещеры, заповедники и озёра. '
                       'Откройте для себя дикую природу, которая охраняется государством '
                       'и научным сообществом. Побывайте в местах, где нетронутая природа '
                       'демонстрирует всю красоту и мощь земли.',
        'complexity': 'сложная',
        'duration': '6 часов',
        'map_iframe': (
            'https://yandex.ru/map-widget/v1/'
            '?ll=49.812400%2C55.873500'
            '&z=5'
            '&pt=49.290906%2C53.266869%2Cpm2rdl'
            '~49.154085%2C55.913672%2Cpm2rdl'
            '~57.006092%2C57.006092%2Cpm2rdl'
            '~48.311615%2C56.160590%2Cpm2rdl'
            '~44.815366%2C56.497214&%2Cpm2rdl'
        ),
        'checkpoints': [
            {
                'id': 1,
                'name': 'Национальный парк «Самарская Лука»',
                'description': 'Уникальная излучина Волги с Жигулёвскими горами — '
                               'одно из красивейших мест всего Поволжья. '
                               'Самарская Лука — это географический феномен, '
                               'где Волга делает огромную подкову, охватывая территорию площадью '
                               'около 1650 квадратных километров. Внутри этой излучины находятся '
                               'Жигулёвские горы, возвышающиеся на 380 метров над уровнем Волги. '
                               'Эти горы являются единственной горной цепью тектонического происхождения '
                               'на Русской равнине, что делает их геологически уникальными. '
                               'Национальный парк охраняет не только горы, но и богатый животный мир: '
                               'здесь обитают редкие виды птиц, в том числе орёл и сокол, и млекопитающих. '
                               'Парк известен своими пещерами, самая известная из которых — пещера Штани. '
                               'Самарская Лука привлекает туристов своим ландшафтным разнообразием: '
                               'сосновые леса, луга, скалистые берега Волги. '
                               'Парк предлагает множество туристических маршрутов разной сложности, '
                               'от простых пеших прогулок до сложных альпинистских восхождений.',
                'media': '/static/img/Вид_на_Усинский_курган.jpg',
                'fact': 'Жигулёвские горы — единственные горы тектонического '
                        'происхождения на Русской равнине.',
                'lat': 49.290906,
                'lon': 53.266869,
                'address': 'Самарская обл., нац. парк «Самарская Лука»',
                'map_iframe': (
                    'https://yandex.ru/map-widget/v1/'
                    '?ll=49.750000%2C53.266869'
                    '&z=16'
                    '&pt=49.290906%2C53.266869%2Cpm2rdl'
                ),
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
                'description': 'Система карстовых озёр с кристально чистой водой '
                               'и постоянной температурой +4 °C круглый год. '
                               'Голубые озёра — это чудо природы, созданное тысячелетиями растворения '
                               'известняка подземными водами. Озёра расположены в окружении лесов '
                               'и представляют собой идеальное место для наблюдения природы. '
                               'Вода в озёрах имеет насыщенный голубой цвет благодаря своей чистоте '
                               'и глубине. Температура воды остаётся постоянной +4 °C круглый год, '
                               'что объясняется глубиной озёр и их подземным питанием. '
                               'Видимость под водой достигает 40 метров, что делает озёра '
                               'раем для дайверов и любителей подводной съёмки. '
                               'Озёра сохраняют обитателей, приспособленные к холодной воде: '
                               'редкие виды рыб и других водных организмов. '
                               'Место известно также как центр подводного туризма: здесь часто '
                               'проводятся соревнования по подводному плаванию и фотосъёмке. '
                               'Голубые озёра охраняются как памятник природы и привлекают туристов '
                               'со всего мира, желающих своими глазами увидеть это подземное чудо.',
                'media': '/static/img/Kazan-Goluboe-lk-winter.jpg',
                'fact': 'Вода в Голубых озёрах настолько прозрачна, что видимость '
                        'под водой достигает 40 метров.',
                'lat': 49.154085,
                'lon': 55.913672,
                'address': 'Татарстан, Высокогорский р-н, пос. Щербаково',
                'map_iframe': (
                    'https://yandex.ru/map-widget/v1/'
                    '?ll=49.154085%2C555.913672'
                    '&z=16'
                    '&pt=49.154085%2C55.913672%2Cpm2rdl'
                ),
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
                'description': 'Одна из крупнейших карстовых пещер в мире — 5700 метров '
                               'ходов, 48 гротов и 70 подземных озёр. '
                               'Кунгурская пещера — это одно из самых впечатляющих подземных чудес '
                               'в мире. Её протяжённость превышает 5700 метров, из которых '
                               'более километра открыто для туристического посещения. '
                               'Пещера образована подземной рекой, которая на протяжении миллионов лет '
                               'вырезала в известняке настоящий лабиринт, состоящий из 48 гротов '
                               'разных размеров и форм. Каждый грот имеет своё имя и уникальные особенности. '
                               'В пещере находится 70 подземных озёр, вода в которых кристально чиста. '
                               'Некоторые озёра достаточно глубоки для существования редких видов животных, '
                               'не встречающихся больше нигде. Стены и своды пещеры украшены кристаллами '
                               'льда (отсюда название «ледяная»), хотя это происходит далеко не всегда. '
                               'Экскурсии в пещеру проводятся с 1914 года, что делает её одним '
                               'из старейших туристических объектов в России. Современное освещение '
                               'позволяет оценить красоту геологических формаций. '
                               'Посещение пещеры дарует незабываемое переживание встречи с первозданной природой.',
                'media': '/static/img/По_гротам_пещеры_1.jpg',
                'fact': 'Кунгурская пещера открыта для туристов уже более '
                        '100 лет — экскурсии проводятся с 1914 года.',
                'lat': 57.006092,
                'lon': 57.006092,
                'address': 'Пермский край, село Филипповка',
                'map_iframe': (
                    'https://yandex.ru/map-widget/v1/'
                    '?ll=57.006092%2C57.006092'
                    '&z=16'
                    '&pt=57.006092%2C57.006092%2Cpm2rdl'
                ),
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
                'description': 'Заповедный лес с реликтовыми дубравами, '
                               'карстовыми озёрами и легендарным Дубом Пугачёва. '
                               'Марий Чодра — это волшебный лес в сердце Поволжья, '
                               'где природа сохранила свой первозданный облик. '
                               'Парк известен своими реликтовыми дубравами — лесами, '
                               'которые существовали ещё в ледниковый период. '
                               'Эти дубы являются генетическим сокровищем, содержащим информацию '
                               'о климате прошлых эпох. В парке обитают редкие виды животных, '
                               'в том числе дикие кабаны, лоси и рыси. Птичье сообщество парка '
                               'включает более 100 видов, от коростеля до редкого чёрного сокола. '
                               'Озёра парка, образованные карстом, поражают своей синевой и чистотой. '
                               'Главная достопримечательность парка — знаменитый Дуб Пугачёва, '
                               'согласно легенде, укрывавший под своей кроной самого Емельяна Пугачёва '
                               'во время его бегства. Дуб имеет возраст более 400 лет и является живой '
                               'памятью истории. Парк предлагает множество туристических маршрутов, '
                               'от спокойных прогулок по лесу до сложных пеших переходов.',
                'media': '/static/img/Осень_на_р.Илеть.jpg',
                'fact': 'По легенде, под знаменитым дубом в парке ночевал '
                        'Емельян Пугачёв во время Крестьянской войны 1773–1775 гг.',
                'lat': 48.311615,
                'lon': 56.160590,
                'address': 'Марий Эл, Звениговский р-н, пос. Красногорский',
                'map_iframe': (
                    'https://yandex.ru/map-widget/v1/'
                    '?ll=48.311615%2C56.160590'
                    '&z=16'
                    '&pt=48.311615%2C56.160590%2Cpm2rdl'
                ),
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
                'description': 'Биосферный резерват ЮНЕСКО — леса, болота и пойменные '
                               'луга в междуречье Керженца и Волги. '
                               'Керженский заповедник — это огромный природный комплекс, '
                               'занимающий площадь около 45 тысяч гектаров. '
                               'Заповедник охраняет типичные экосистемы Русской равнины, '
                               'включая смешанные леса, болота разных типов и пойменные луга. '
                               'В лесах обитают лоси, бобры, водяные полёвки и другие млекопитающие. '
                               'Птичье население заповедника исключительно богато: здесь встречаются '
                               'более 170 видов птиц, включая редких орлана-белохвоста, чёрного аиста, '
                               'глухаря и тетеревов. Болота заповедника — это экологически важные экосистемы, '
                               'которые служат фильтром для воды и убежищем для редких растений и животных. '
                               'Статус биосферного резервата ЮНЕСКО означает, что заповедник признан '
                               'научным сообществом как место исключительной экологической ценности. '
                               'Здесь проводятся долгосрочные исследования влияния человеческой деятельности '
                               'на природные экосистемы. Керженский заповедник демонстрирует, '
                               'как можно сохранить природу в её первозданном состоянии.',
                'media': '/static/img/Керженец_-_могучая_река.jpg',
                'fact': 'В заповеднике обитают более 170 видов птиц, включая '
                        'редких орлана-белохвоста и чёрного аиста.',
                'lat': 44.815366,
                'lon': 56.497214,
                'address': 'Нижегородская обл., Борский р-н, пос. Рустай',
                'map_iframe': (
                    'https://yandex.ru/map-widget/v1/'
                    '?ll=44.815366%2C56.497214&'
                    '&z=16'
                    '&pt=44.815366%2C56.497214&%2Cpm2rdl'
                ),
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


# @app.route('/')
# def index():
#     return render_template('index.html', routes=ROUTES)





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

    return render_template(
        'route_detail.html',
        route=route,
        progress=progress,
        completed=completed,
        total=total
    )


@app.route('/route/<int:route_id>/checkpoint/<int:checkpoint_id>')
def checkpoint(route_id, checkpoint_id):
    checkpoint_id = checkpoint_id - 1
    route = ROUTES.get(route_id)
    if not route:
        return render_template('404.html'), 404
    cp = next((c for c in route['checkpoints'] if c['id'] == checkpoint_id + 1), None)
    if not cp:
        return render_template('404.html'), 404

    session_key = f'progress_{route_id}'
    progress = flask.session.get(session_key, [])

    checkpoints = route['checkpoints']
    current_index = next(i for i, c in enumerate(checkpoints) if c['id'] == checkpoint_id + 1)
    next_cp = checkpoints[current_index + 1] if current_index + 1 < len(checkpoints) else None
    points_ = db_sess.query(Liked.points).filter(
        Liked.login == flask.request.cookies.get("login_")
    ).first()
    if not points_:
        favorite_ids = []
    else:
        favorite_ids = points_[0].split('-')
    return render_template('checkpoint.html',
                           route=route,
                           checkpoint=checkpoints[checkpoint_id],
                           next_cp=next_cp,
                           progress=progress,
                           favorite_ids=favorite_ids,
                           id=str(route_id) + "." + str(checkpoint_id),
    )

def add_to_favorite(points_array, checkpoint_id, login_):
    points_array.append(str(checkpoint_id))
    action = insert(Liked).values(login=login_, points='-'.join(points_array)).on_conflict_do_update(
        index_elements=['login'],
        set_=dict(points='-'.join(points_array))
    )
    db_sess.flush()
    db_sess.execute(action)
    db_sess.commit()

@app.route('/favorite/toggle/<checkpoint_id>', methods=['POST'])
def toggle_favorite(checkpoint_id):
    login_ = flask.request.cookies.get("login_")
    points_ = db_sess.query(Liked.points).filter(
        Liked.login==login_
    ).first()
    if not points_:
        points_ = []
    else:
        points_ = points_[0].split('-')
    existing = checkpoint_id in points_
    if existing:
        points_.remove(checkpoint_id)
        action = insert(Liked).values(login=login_, points='-'.join(points_)).on_conflict_do_update(
            index_elements=['login'],
            set_=dict(points='-'.join(points_))
        )
        db_sess.flush()
        db_sess.execute(action)
        db_sess.commit()
        added = False
    else:
        add_to_favorite(points_, checkpoint_id, login_)
        added = True

    if flask.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'added': added})
    route_id = flask.request.form.get('route_id')
    return redirect(flask.url_for('checkpoint',
                            route_id=route_id,
                            checkpoint_id=checkpoint_id))


@app.route('/route/<int:route_id>/checkpoint/<int:checkpoint_id>/quiz', methods=['GET', 'POST'])
def quiz(route_id, checkpoint_id):
    route = ROUTES.get(route_id)
    if not route:
        return render_template('404.html'), 404

    cp = next((c for c in route['checkpoints'] if c['id'] == checkpoint_id), None)
    if not cp:
        return render_template('404.html'), 404

    session_key = f'quiz_progress_{route_id}_{checkpoint_id}'

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
            quiz_progress['current_question'] += 1

            if quiz_progress['current_question'] >= len(quiz_questions):
                quiz_progress['completed'] = True
                
                if quiz_progress['correct_answers'] == len(quiz_questions):
                    progress_key = f'progress_{route_id}'
                    progress = flask.session.get(progress_key, [])
                    if checkpoint_id not in progress:
                        progress.append(checkpoint_id)
                        flask.session[progress_key] = progress

            flask.session[session_key] = quiz_progress
            return redirect(flask.url_for('quiz', route_id=route_id, checkpoint_id=checkpoint_id))

    checkpoints = route['checkpoints']
    current_index = next(i for i, c in enumerate(checkpoints) if c['id'] == checkpoint_id)
    next_cp = checkpoints[current_index + 1] if current_index + 1 < len(checkpoints) else None

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


@app.route('/favorites')
def favorites():
    login_ = flask.request.cookies.get("login_")
    if not login_:
        return redirect('/login')

    result = db_sess.query(Liked.points).filter(
        Liked.login == login_
    ).first()

    all_points = []

    if result and result[0]:
        for fav in result[0].split("-"):
            if not fav or "." not in fav:
                continue
            try:
                route_id, checkpoint_id = fav.split(".")
                route_id = int(route_id)
                checkpoint_id = int(checkpoint_id)
                route = ROUTES.get(route_id)
                if not route:
                    continue
                cp = route['checkpoints'][checkpoint_id]
                if cp:
                    all_points.append({
                        'checkpoint': cp,
                        'route': route,
                        'fav_id': fav
                    })
            except (ValueError, KeyError):
                continue

    return render_template('favorites.html', favorites=all_points)

if __name__ == "__main__":
    app.run()

