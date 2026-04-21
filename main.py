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
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'mail.findkey@gmail.com'
app.config['MAIL_PASSWORD'] = 'krvv vtpp ismn eddd'
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
            sender='mail.findkey@gmail.com',
            recipients=[cookie]
        )
        msg.body = f'Код подтверждения: {code_}'
        mail.send(msg)
        db_sess.add(ver)
        db_sess.commit()


    return render_template('validatemail.html', title='Подтверждение почты', form=form)

# @app.route('/logout', methods=['GET', 'POST'])
# def logout():
#     res = flask.make_response(redirect('/'))
#     res.set_cookie("mail_", value="", expires=0)
#     res.set_cookie("login_", value="", expires=0)
#     res.set_cookie("password_", value="", expires=0)
#     return res
#
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
                       'Поволжья: Горький, Лермонтов, Гончаров, Цветаева.',
        'complexity': 'лёгкая',
        'duration': '4 часа',
        'map_iframe': (
            'https://yandex.ru/map-widget/v1/'
            '?ll=47.437400%2C55.036100'
            '&z=6'
            '&pt=43.989600%2C56.328700%2Cpm2rdl'
            '~43.619400%2C52.991700%2Cpm2rdl'
            '~48.402900%2C54.314500%2Cpm2rdl'
            '~49.121400%2C55.789200%2Cpm2rdl'
            '~52.054500%2C55.756500%2Cpm2rdl'
        ),
        'checkpoints': [
            {
                'id': 1,
                'name': 'Домик Каширина, Нижний Новгород',
                'description': 'Мемориальный музей детства Максима Горького — деревянный '
                               'дом деда писателя, где прошли его ранние годы.',
                'media': 'фото',
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
                'quiz_question': 'Какое произведение Горький написал о своём детстве в этом доме?',
                'quiz_answers': ['Мать', 'На дне', 'Детство', 'Старуха Изергиль'],
                'correct_answer': 2
            },
            {
                'id': 2,
                'name': 'Музей-заповедник «Тарханы», Пензенская область',
                'description': 'Родовая усадьба, где вырос Михаил Лермонтов. Сохранились '
                               'барский дом, парк, пруды и семейная церковь.',
                'media': 'видео',
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
                'quiz_question': 'Какой поэт провёл детство в усадьбе Тарханы?',
                'quiz_answers': ['Михаил Лермонтов', 'Александр Пушкин', 'Сергей Есенин', 'Николай Некрасов'],
                'correct_answer': 0
            },
            {
                'id': 3,
                'name': 'Дом-музей И. А. Гончарова, Ульяновск',
                'description': 'Музей в доме, где родился автор романов «Обломов» и '
                               '«Обрыв». Экспозиция воссоздаёт быт купеческого Симбирска.',
                'media': 'аудио',
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
                'quiz_question': 'Как назывался Ульяновск во времена Гончарова?',
                'quiz_answers': ['Казань', 'Самара', 'Саратов', 'Симбирск'],
                'correct_answer': 3
            },
            {
                'id': 4,
                'name': 'Литературно-мемориальный музей А. М. Горького, Казань',
                'description': 'Музей расположен в доме, где молодой Горький жил и работал '
                               'в пекарне. Казань стала его «университетами».',
                'media': 'фото',
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
                'quiz_question': 'Как называется повесть Горького о казанском периоде жизни?',
                'quiz_answers': ['Детство', 'В людях', 'Мои университеты', 'На дне'],
                'correct_answer': 2
            },
            {
                'id': 5,
                'name': 'Мемориальный комплекс М. И. Цветаевой, Елабуга',
                'description': 'Дом, где провела последние дни жизни великая поэтесса '
                               'Марина Цветаева. Музей хранит личные вещи и рукописи.',
                'media': 'видео',
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
                'quiz_question': 'В каком году Цветаева была эвакуирована в Елабугу?',
                'quiz_answers': ['1939', '1940', '1942', '1941'],
                'correct_answer': 3
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
            '&pt=50.143800%2C53.212200%2Cpm2rdl'
            '~49.319100%2C53.507900%2Cpm2rdl'
            '~48.252700%2C54.269800%2Cpm2rdl'
            '~53.204800%2C56.844600%2Cpm2rdl'
            '~52.412000%2C55.726000%2Cpm2rdl'
        ),
        'checkpoints': [
            {
                'id': 1,
                'name': 'Музейно-выставочный центр «Самара Космическая»',
                'description': 'Один из главных символов космической истории Поволжья. '
                               'У входа установлена настоящая ракета-носитель «Союз».',
                'media': 'фото',
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
                'quiz_question': 'Как называлась Самара в советское время?',
                'quiz_answers': ['Куйбышев', 'Сталинград', 'Горький', 'Свердловск'],
                'correct_answer': 0
            },
            {
                'id': 2,
                'name': 'Технический музей им. К. Г. Сахарова, Тольятти',
                'description': 'Крупнейший в России музей техники под открытым небом: '
                               'самолёты, танки, подводная лодка и автомобили.',
                'media': 'видео',
                'fact': 'В коллекции музея более 460 экспонатов, включая '
                        'настоящую подводную лодку Б-307.',
                'lat': 49.249808,
                'lon': 53.553031,
                'address': 'Тольятти, ул. Сахарова, 1',
                'map_iframe': (
                    'https://yandex.ru/map-widget/v1/'
                    '?ll=49.249808%2C53.553031'
                    '&z=15'
                    '&pt=49.249808%2C53.553031%2Cpm2rdl'
                ),
                'quiz_question': 'Какой автомобильный гигант расположен в Тольятти?',
                'quiz_answers': ['ГАЗ', 'КАМАЗ', 'УАЗ', 'АвтоВАЗ'],
                'correct_answer': 3
            },
            {
                'id': 3,
                'name': 'Музей истории гражданской авиации, Ульяновск',
                'description': 'Уникальная экспозиция из более чем 30 воздушных судов '
                               'под открытым небом на территории аэродрома.',
                'media': 'аудио',
                'fact': 'Ульяновск считается авиационной столицей России — '
                        'здесь производили самолёты Ту-204 и Ан-124 «Руслан».',
                'lat': 48.234580,
                'lon': 54.289727,
                'address': 'Ульяновск, ул. Авиационная, 20а',
                'map_iframe': (
                    'https://yandex.ru/map-widget/v1/'
                    '?ll=48.234580%2C54.289727'
                    '&z=15'
                    '&pt=48.234580%2C54.289727%2Cpm2rdl'
                ),
                'quiz_question': 'Какой тяжёлый транспортный самолёт производили в Ульяновске?',
                'quiz_answers': ['Ил-76', 'Ту-154', 'Ан-124 «Руслан»', 'Су-27'],
                'correct_answer': 2
            },
            {
                'id': 4,
                'name': 'Музей истории ОАО «КАМАЗ», Набережные Челны',
                'description': 'Музей крупнейшего в России производителя грузовых '
                               'автомобилей — многократного победителя ралли «Дакар».',
                'media': 'видео',
                'fact': 'Команда «КАМАЗ-мастер» одержала более 19 побед '
                        'на ралли «Дакар» — абсолютный рекорд.',
                'lat': 52.446574,
                'lon': 55.74731,
                'address': 'Набережные Челны, пр. Автозаводский, 2',
                'map_iframe': (
                    'https://yandex.ru/map-widget/v1/'
                    '?ll=52.446574%2C55.74731'
                    '&z=15'
                    '&pt=52.446574%2C55.74731%2Cpm2rdl'
                ),
                'quiz_question': 'В каком ралли команда «КАМАЗ-мастер» побеждала более 19 раз?',
                'quiz_answers': ['Баха', 'Ралли Монте-Карло', 'Шёлковый путь', 'Дакар'],
                'correct_answer': 3
            }
        ]
    },
    3: {
        'id': 3,
        'title': 'Духовное Поволжье',
        'theme': 'духовная',
        'description': 'Маршрут по святыням и духовным центрам Поволжья — '
                       'монастыри, соборы и места паломничества разных конфессий.',
        'complexity': 'средняя',
        'duration': '5 часов',
        'map_iframe': (
            'https://yandex.ru/map-widget/v1/'
            '?ll=47.688400%2C55.518300'
            '&z=6'
            '&pt=43.244900%2C55.039300%2Cpm2rdl'
            '~48.727500%2C55.899700%2Cpm2rdl'
            '~56.226800%2C57.389700%2Cpm2rdl'
            '~45.069300%2C56.081200%2Cpm2rdl'
            '~45.173200%2C54.181600%2Cpm2rdl'
        ),
        'checkpoints': [
            {
                'id': 1,
                'name': 'Серафимо-Дивеевский монастырь',
                'description': 'Один из крупнейших православных монастырей России, '
                               'связанный с именем преподобного Серафима Саровского.',
                'media': 'фото',
                'fact': 'Серафим Саровский — один из самых почитаемых русских '
                        'святых, канонизированный в 1903 году по указу Николая II.',
                'lat': 55.039300,
                'lon': 43.244900,
                'address': 'Нижегородская обл., с. Дивеево',
                'map_iframe': (
                    'https://yandex.ru/map-widget/v1/'
                    '?ll=43.244900%2C55.039300'
                    '&z=15'
                    '&pt=43.244900%2C55.039300%2Cpm2rdl'
                ),
                'quiz_question': 'С каким святым связан Дивеевский монастырь?',
                'quiz_answers': ['Сергий Радонежский', 'Серафим Саровский', 'Николай Чудотворец', 'Александр Невский'],
                'correct_answer': 1
            },
            {
                'id': 2,
                'name': 'Раифский Богородицкий монастырь, Татарстан',
                'description': 'Действующий мужской монастырь XVII века на берегу '
                               'Раифского озера в окружении заповедного леса.',
                'media': 'видео',
                'fact': 'Главная святыня монастыря — Грузинская икона Божией Матери, '
                        'которой приписывают чудотворную силу.',
                'lat': 55.899700,
                'lon': 48.727500,
                'address': 'Татарстан, Зеленодольский р-н, пос. Раифа',
                'map_iframe': (
                    'https://yandex.ru/map-widget/v1/'
                    '?ll=48.727500%2C55.899700'
                    '&z=15'
                    '&pt=48.727500%2C55.899700%2Cpm2rdl'
                ),
                'quiz_question': 'Какая икона является главной святыней Раифского монастыря?',
                'quiz_answers': ['Казанская', 'Владимирская', 'Грузинская', 'Иверская'],
                'correct_answer': 2
            },
            {
                'id': 3,
                'name': 'Белогорский Свято-Николаевский монастырь, Пермский край',
                'description': 'Монастырь на вершине Белой горы — «Уральский Афон». '
                               'Величественный Крестовоздвиженский собор виден издалека.',
                'media': 'фото',
                'fact': 'Крестовоздвиженский собор Белогорского монастыря — '
                        'третий по величине православный храм в России.',
                'lat': 57.389700,
                'lon': 56.226800,
                'address': 'Пермский край, Кунгурский р-н, с. Белая Гора',
                'map_iframe': (
                    'https://yandex.ru/map-widget/v1/'
                    '?ll=56.226800%2C57.389700'
                    '&z=14'
                    '&pt=56.226800%2C57.389700%2Cpm2rdl'
                ),
                'quiz_question': 'Как называют Белогорский монастырь?',
                'quiz_answers': ['Уральский Иерусалим', 'Уральская Лавра', 'Уральский Афон', 'Уральский Ватикан'],
                'correct_answer': 2
            },
            {
                'id': 4,
                'name': 'Макарьевский Желтоводский монастырь',
                'description': 'Древний монастырь на берегу Волги, основанный в XV веке '
                               'преподобным Макарием. Здесь зародилась знаменитая ярмарка.',
                'media': 'аудио',
                'fact': 'Макарьевская ярмарка, основанная у стен монастыря, '
                        'позднее переехала в Нижний Новгород и стала крупнейшей в стране.',
                'lat': 56.081200,
                'lon': 45.069300,
                'address': 'Нижегородская обл., пос. Макарьево',
                'map_iframe': (
                    'https://yandex.ru/map-widget/v1/'
                    '?ll=45.069300%2C56.081200'
                    '&z=15'
                    '&pt=45.069300%2C56.081200%2Cpm2rdl'
                ),
                'quiz_question': 'Какая знаменитая ярмарка зародилась у стен этого монастыря?',
                'quiz_answers': ['Ирбитская', 'Нижегородская', 'Казанская', 'Симбирская'],
                'correct_answer': 1
            },
            {
                'id': 5,
                'name': 'Кафедральный собор св. Феодора Ушакова, Саранск',
                'description': 'Один из крупнейших соборов России, освящённый '
                               'в честь святого праведного воина Феодора Ушакова.',
                'media': 'фото',
                'fact': 'Адмирал Фёдор Ушаков не проиграл ни одного морского '
                        'сражения и был канонизирован в 2001 году.',
                'lat': 54.181600,
                'lon': 45.173200,
                'address': 'Саранск, ул. Советская, 53',
                'map_iframe': (
                    'https://yandex.ru/map-widget/v1/'
                    '?ll=45.173200%2C54.181600'
                    '&z=16'
                    '&pt=45.173200%2C54.181600%2Cpm2rdl'
                ),
                'quiz_question': 'Кем был Феодор Ушаков до канонизации?',
                'quiz_answers': ['Монах', 'Купец', 'Архитектор', 'Адмирал'],
                'correct_answer': 3
            }
        ]
    },
    4: {
        'id': 4,
        'title': 'Крепости и оборона Поволжья',
        'theme': 'военно-историческая',
        'description': 'Маршрут по фортификационным сооружениям и оборонительным '
                       'рубежам — от древних кремлей до секретного бункера Сталина.',
        'complexity': 'сложная',
        'duration': '5 часов',
        'map_iframe': (
            'https://yandex.ru/map-widget/v1/'
            '?ll=50.207600%2C54.780700'
            '&z=5'
            '&pt=44.002700%2C56.328700%2Cpm2rdl'
            '~50.100000%2C53.195300%2Cpm2rdl'
            '~48.657200%2C55.770400%2Cpm2rdl'
            '~53.204800%2C56.844600%2Cpm2rdl'
            '~55.098600%2C51.764500%2Cpm2rdl'
        ),
        'checkpoints': [
            {
                'id': 1,
                'name': 'Нижегородский кремль',
                'description': 'Мощная кирпичная крепость начала XVI века с 13 башнями, '
                               'стоящая на высоком берегу при слиянии Оки и Волги.',
                'media': 'фото',
                'fact': 'Нижегородский кремль ни разу в своей истории не был '
                        'взят штурмом неприятеля.',
                'lat': 56.328700,
                'lon': 44.002700,
                'address': 'Нижний Новгород, Кремль, 1',
                'map_iframe': (
                    'https://yandex.ru/map-widget/v1/'
                    '?ll=44.002700%2C56.328700'
                    '&z=15'
                    '&pt=44.002700%2C56.328700%2Cpm2rdl'
                ),
                'quiz_question': 'Сколько башен у Нижегородского кремля?',
                'quiz_answers': ['9', '20', '13', '7'],
                'correct_answer': 2
            },
            {
                'id': 2,
                'name': 'Бункер Сталина, Самара',
                'description': 'Секретный бункер на глубине 37 метров — запасной '
                               'командный пункт Ставки Верховного Главнокомандующего.',
                'media': 'видео',
                'fact': 'О существовании бункера общественность узнала только '
                        'в 1990 году, спустя почти 50 лет после постройки.',
                'lat': 53.195300,
                'lon': 50.100000,
                'address': 'Самара, ул. Фрунзе, 167',
                'map_iframe': (
                    'https://yandex.ru/map-widget/v1/'
                    '?ll=50.100000%2C53.195300'
                    '&z=16'
                    '&pt=50.100000%2C53.195300%2Cpm2rdl'
                ),
                'quiz_question': 'На какой глубине расположен бункер Сталина в Самаре?',
                'quiz_answers': ['12 метров', '37 метров', '25 метров', '50 метров'],
                'correct_answer': 1
            },
            {
                'id': 3,
                'name': 'Остров-град Свияжск',
                'description': 'Крепость XVI века, основанная Иваном Грозным как '
                               'плацдарм для взятия Казани. Объект ЮНЕСКО.',
                'media': 'аудио',
                'fact': 'Свияжск был построен всего за 4 недели в 1551 году — '
                        'деревянную крепость сплавили по Волге в разобранном виде.',
                'lat': 55.770400,
                'lon': 48.657200,
                'address': 'Татарстан, Зеленодольский р-н, с. Свияжск',
                'map_iframe': (
                    'https://yandex.ru/map-widget/v1/'
                    '?ll=48.657200%2C55.770400'
                    '&z=14'
                    '&pt=48.657200%2C55.770400%2Cpm2rdl'
                ),
                'quiz_question': 'За какой срок была построена крепость Свияжск?',
                'quiz_answers': ['1 год', '6 месяцев', '3 дня', '4 недели'],
                'correct_answer': 3
            },
            {
                'id': 4,
                'name': 'Музейно-выставочный комплекс стрелкового оружия, Ижевск',
                'description': 'Музей при знаменитом Ижевском оружейном заводе — '
                               'одном из старейших оружейных предприятий России.',
                'media': 'фото',
                'fact': 'Ижевский оружейный завод основан в 1807 году и непрерывно '
                        'производит стрелковое оружие более 200 лет.',
                'lat': 56.844600,
                'lon': 53.204800,
                'address': 'Ижевск, ул. Бородина, 19',
                'map_iframe': (
                    'https://yandex.ru/map-widget/v1/'
                    '?ll=53.204800%2C56.844600'
                    '&z=16'
                    '&pt=53.204800%2C56.844600%2Cpm2rdl'
                ),
                'quiz_question': 'В каком году основан Ижевский оружейный завод?',
                'quiz_answers': ['1807', '1850', '1762', '1917'],
                'correct_answer': 0
            },
            {
                'id': 5,
                'name': 'Оренбургская крепость (Губернаторский музей)',
                'description': 'Историческое место Оренбургской крепости — форпоста '
                               'на границе Европы и Азии, воспетого Пушкиным.',
                'media': 'видео',
                'fact': 'Именно Оренбургская крепость стала прообразом Белогорской '
                        'крепости в «Капитанской дочке» Пушкина.',
                'lat': 51.764500,
                'lon': 55.098600,
                'address': 'Оренбург, ул. Набережная, 29',
                'map_iframe': (
                    'https://yandex.ru/map-widget/v1/'
                    '?ll=55.098600%2C51.764500'
                    '&z=15'
                    '&pt=55.098600%2C51.764500%2Cpm2rdl'
                ),
                'quiz_question': 'Какое произведение Пушкин написал после посещения Оренбурга?',
                'quiz_answers': ['Евгений Онегин', 'Дубровский', 'Капитанская дочка', 'Борис Годунов'],
                'correct_answer': 2
            }
        ]
    },
    5: {
        'id': 5,
        'title': 'Купеческое Поволжье',
        'theme': 'купеческая',
        'description': 'Маршрут по старинным торговым городам: ярмарки, '
                       'купеческие особняки, торговые улицы и провинциальный модерн.',
        'complexity': 'средняя',
        'duration': '4 часа',
        'map_iframe': (
            'https://yandex.ru/map-widget/v1/'
            '?ll=47.431400%2C54.000100'
            '&z=6'
            '&pt=43.956400%2C56.328200%2Cpm2rdl'
            '~50.096300%2C53.187800%2Cpm2rdl'
            '~52.059000%2C55.757000%2Cpm2rdl'
            '~45.011700%2C53.194700%2Cpm2rdl'
            '~46.034000%2C51.533000%2Cpm2rdl'
        ),
        'checkpoints': [
            {
                'id': 1,
                'name': 'Нижегородская ярмарка',
                'description': 'Главный торговый центр Российской империи — '
                               '«карман России». Ярмарочный комплекс XIX века.',
                'media': 'фото',
                'fact': 'Нижегородская ярмарка в XIX веке была крупнейшей '
                        'в России и третьей по величине в мире.',
                'lat': 56.328200,
                'lon': 43.956400,
                'address': 'Нижний Новгород, ул. Совнаркомовская, 13',
                'map_iframe': (
                    'https://yandex.ru/map-widget/v1/'
                    '?ll=43.956400%2C56.328200'
                    '&z=16'
                    '&pt=43.956400%2C56.328200%2Cpm2rdl'
                ),
                'quiz_question': 'Как образно называли Нижний Новгород за его торговое значение?',
                'quiz_answers': ['Ворота России', 'Карман России', 'Сердце России', 'Окно в Европу'],
                'correct_answer': 1
            },
            {
                'id': 2,
                'name': 'Особняк Курлиной, Самара',
                'description': 'Жемчужина самарского модерна — купеческий особняк начала '
                               'XX века с уникальными витражами и лепниной.',
                'media': 'аудио',
                'fact': 'Особняк Курлиной считается первым зданием '
                        'в стиле модерн во всей Самаре.',
                'lat': 53.187800,
                'lon': 50.096300,
                'address': 'Самара, ул. Фрунзе, 159',
                'map_iframe': (
                    'https://yandex.ru/map-widget/v1/'
                    '?ll=50.096300%2C53.187800'
                    '&z=16'
                    '&pt=50.096300%2C53.187800%2Cpm2rdl'
                ),
                'quiz_question': 'В каком архитектурном стиле построен особняк Курлиной?',
                'quiz_answers': ['Классицизм', 'Барокко', 'Готика', 'Модерн'],
                'correct_answer': 3
            },
            {
                'id': 3,
                'name': 'Музей-заповедник «Елабуга»',
                'description': 'Купеческая Елабуга — город-музей с сохранившимися '
                               'торговыми рядами и особняками XIX века.',
                'media': 'видео',
                'fact': 'Елабуга — родина художника Ивана Шишкина, '
                        'прославившего красоту русской природы.',
                'lat': 55.757000,
                'lon': 52.059000,
                'address': 'Елабуга, ул. Казанская, 26',
                'map_iframe': (
                    'https://yandex.ru/map-widget/v1/'
                    '?ll=52.059000%2C55.757000'
                    '&z=14'
                    '&pt=52.059000%2C55.757000%2Cpm2rdl'
                ),
                'quiz_question': 'Какой знаменитый художник родился в Елабуге?',
                'quiz_answers': ['Илья Репин', 'Иван Шишкин', 'Василий Суриков', 'Карл Брюллов'],
                'correct_answer': 1
            },
            {
                'id': 4,
                'name': 'Улица Московская, Пенза',
                'description': 'Главная пешеходная улица Пензы с купеческой застройкой '
                               'XIX века — «пензенский Арбат».',
                'media': 'фото',
                'fact': 'На улице Московской находится единственный в России '
                        'музей одной картины имени Мясникова.',
                'lat': 53.194700,
                'lon': 45.011700,
                'address': 'Пенза, ул. Московская',
                'map_iframe': (
                    'https://yandex.ru/map-widget/v1/'
                    '?ll=45.011700%2C53.194700'
                    '&z=16'
                    '&pt=45.011700%2C53.194700%2Cpm2rdl'
                ),
                'quiz_question': 'Как называют пешеходную улицу Московскую в Пензе?',
                'quiz_answers': ['Пензенский Невский', 'Пензенский Бродвей', 'Пензенский Арбат', 'Пензенский бульвар'],
                'correct_answer': 2
            },
            {
                'id': 5,
                'name': 'Проспект Кирова, Саратов',
                'description': 'Пешеходная улица Саратова — «саратовский Арбат» '
                               'с купеческими домами и торговыми пассажами.',
                'media': 'аудио',
                'fact': 'Саратовская консерватория на проспекте Кирова — '
                        'третья по старшинству консерватория в России.',
                'lat': 51.533000,
                'lon': 46.034000,
                'address': 'Саратов, пр. Кирова',
                'map_iframe': (
                    'https://yandex.ru/map-widget/v1/'
                    '?ll=46.034000%2C51.533000'
                    '&z=16'
                    '&pt=46.034000%2C51.533000%2Cpm2rdl'
                ),
                'quiz_question': 'Какое музыкальное учебное заведение находится на пр. Кирова?',
                'quiz_answers': ['Училище', 'Академия', 'Лицей', 'Консерватория'],
                'correct_answer': 3
            }
        ]
    },
    6: {
        'id': 6,
        'title': 'Природное Поволжье',
        'theme': 'природная',
        'description': 'Маршрут по уникальным природным объектам Поволжья — '
                       'национальные парки, пещеры, заповедники и озёра.',
        'complexity': 'сложная',
        'duration': '6 часов',
        'map_iframe': (
            'https://yandex.ru/map-widget/v1/'
            '?ll=49.812400%2C55.873500'
            '&z=5'
            '&pt=49.750000%2C53.383300%2Cpm2rdl'
            '~49.170700%2C55.901500%2Cpm2rdl'
            '~57.006800%2C57.440800%2Cpm2rdl'
            '~48.366700%2C56.150000%2Cpm2rdl'
            '~44.768000%2C56.492000%2Cpm2rdl'
        ),
        'checkpoints': [
            {
                'id': 1,
                'name': 'Национальный парк «Самарская Лука»',
                'description': 'Уникальная излучина Волги с Жигулёвскими горами — '
                               'одно из красивейших мест всего Поволжья.',
                'media': 'фото',
                'fact': 'Жигулёвские горы — единственные горы тектонического '
                        'происхождения на Русской равнине.',
                'lat': 53.383300,
                'lon': 49.750000,
                'address': 'Самарская обл., нац. парк «Самарская Лука»',
                'map_iframe': (
                    'https://yandex.ru/map-widget/v1/'
                    '?ll=49.750000%2C53.383300'
                    '&z=11'
                    '&pt=49.750000%2C53.383300%2Cpm2rdl'
                ),
                'quiz_question': 'Какие горы расположены на территории Самарской Луки?',
                'quiz_answers': ['Уральские', 'Жигулёвские', 'Кавказские', 'Хибины'],
                'correct_answer': 1
            },
            {
                'id': 2,
                'name': 'Голубые озёра, Казань',
                'description': 'Система карстовых озёр с кристально чистой водой '
                               'и постоянной температурой +4 °C круглый год.',
                'media': 'видео',
                'fact': 'Вода в Голубых озёрах настолько прозрачна, что видимость '
                        'под водой достигает 40 метров.',
                'lat': 55.901500,
                'lon': 49.170700,
                'address': 'Татарстан, Высокогорский р-н, пос. Щербаково',
                'map_iframe': (
                    'https://yandex.ru/map-widget/v1/'
                    '?ll=49.170700%2C55.901500'
                    '&z=14'
                    '&pt=49.170700%2C55.901500%2Cpm2rdl'
                ),
                'quiz_question': 'Какая температура воды в Голубых озёрах круглый год?',
                'quiz_answers': ['0 °C', '+10 °C', '+4 °C', '+20 °C'],
                'correct_answer': 2
            },
            {
                'id': 3,
                'name': 'Кунгурская ледяная пещера, Пермский край',
                'description': 'Одна из крупнейших карстовых пещер в мире — 5700 метров '
                               'ходов, 48 гротов и 70 подземных озёр.',
                'media': 'аудио',
                'fact': 'Кунгурская пещера открыта для туристов уже более '
                        '100 лет — экскурсии проводятся с 1914 года.',
                'lat': 57.440800,
                'lon': 57.006800,
                'address': 'Пермский край, г. Кунгур, ул. Степана Разина',
                'map_iframe': (
                    'https://yandex.ru/map-widget/v1/'
                    '?ll=57.006800%2C57.440800'
                    '&z=14'
                    '&pt=57.006800%2C57.440800%2Cpm2rdl'
                ),
                'quiz_question': 'Сколько гротов в Кунгурской ледяной пещере?',
                'quiz_answers': ['12', '48', '100', '25'],
                'correct_answer': 1
            },
            {
                'id': 4,
                'name': 'Национальный парк «Марий Чодра», Марий Эл',
                'description': 'Заповедный лес с реликтовыми дубравами, '
                               'карстовыми озёрами и легендарным Дубом Пугачёва.',
                'media': 'фото',
                'fact': 'По легенде, под знаменитым дубом в парке ночевал '
                        'Емельян Пугачёв во время Крестьянской войны 1773–1775 гг.',
                'lat': 56.150000,
                'lon': 48.366700,
                'address': 'Марий Эл, Звениговский р-н, пос. Красногорский',
                'map_iframe': (
                    'https://yandex.ru/map-widget/v1/'
                    '?ll=48.366700%2C56.150000'
                    '&z=11'
                    '&pt=48.366700%2C56.150000%2Cpm2rdl'
                ),
                'quiz_question': 'С каким историческим лицом связан знаменитый дуб в «Марий Чодра»?',
                'quiz_answers': ['Стенька Разин', 'Иван Грозный', 'Пугачёв', 'Пётр I'],
                'correct_answer': 2
            },
            {
                'id': 5,
                'name': 'Керженский заповедник, Нижегородская область',
                'description': 'Биосферный резерват ЮНЕСКО — леса, болота и пойменные '
                               'луга в междуречье Керженца и Волги.',
                'media': 'видео',
                'fact': 'В заповеднике обитают более 170 видов птиц, включая '
                        'редких орлана-белохвоста и чёрного аиста.',
                'lat': 56.492000,
                'lon': 44.768000,
                'address': 'Нижегородская обл., Борский р-н, пос. Рустай',
                'map_iframe': (
                    'https://yandex.ru/map-widget/v1/'
                    '?ll=44.768000%2C56.492000'
                    '&z=11'
                    '&pt=44.768000%2C56.492000%2Cpm2rdl'
                ),
                'quiz_question': 'Какой статус ЮНЕСКО имеет Керженский заповедник?',
                'quiz_answers': ['Объект наследия', 'Геопарк', 'Культурный ландшафт', 'Биосферный резерват'],
                'correct_answer': 3
            }
        ]
    }
}


# @app.route('/')
# def index():
#     return render_template('index.html', routes=ROUTES)


@app.route('/routes')
def routes_list():
    theme_filter = flask.request.args.get('theme', '')
    filtered = ROUTES
    if theme_filter:
        filtered = {k: v for k, v in ROUTES.items() if v['theme'] == theme_filter}
    return render_template('routes.html', routes=filtered, theme_filter=theme_filter)


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

    return render_template(
        'checkpoint.html',
        route=route,
        checkpoint=cp,
        progress=progress,
        next_cp=next_cp
    )


@app.route('/route/<int:route_id>/checkpoint/<int:checkpoint_id>/quiz',
           methods=['GET', 'POST'])
def quiz(route_id, checkpoint_id):
    route = ROUTES.get(route_id)
    if not route:
        return render_template('404.html'), 404

    cp = next((c for c in route['checkpoints'] if c['id'] == checkpoint_id), None)
    if not cp:
        return render_template('404.html'), 404

    result = None
    if flask.request.method == 'POST':
        user_answer = flask.request.form.get('answer', type=int)
        result = (user_answer == cp['correct_answer'])
        if result:
            session_key = f'progress_{route_id}'
            progress = flask.session.get(session_key, [])
            if checkpoint_id not in progress:
                progress.append(checkpoint_id)
                flask.session[session_key] = progress

    checkpoints = route['checkpoints']
    current_index = next(i for i, c in enumerate(checkpoints) if c['id'] == checkpoint_id)
    next_cp = checkpoints[current_index + 1] if current_index + 1 < len(checkpoints) else None

    return render_template(
        'quiz.html',
        route=route,
        checkpoint=cp,
        result=result,
        next_cp=next_cp
    )


# @app.route('/route/<int:route_id>/reset')
# def reset_progress(route_id):
#     session_key = f'progress_{route_id}'
#     session.pop(session_key, None)
#     return redirect(url_for('route_detail', route_id=route_id))

if __name__ == "__main__":
    app.run()


