import sys
import time
import telepot
import telepot.namedtuple
import datetime
import threading
import re
import random
import sqlite3
#import TextGen
from telepot.loop import MessageLoop
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, ForceReply
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
from telepot.namedtuple import InlineQueryResultArticle, InlineQueryResultPhoto, InputTextMessageContent
from pprint import pprint

conn = sqlite3.connect('archive.sqlite', check_same_thread=False)
cur = conn.cursor()

conn2 = sqlite3.connect('fish.sqlite', check_same_thread = False)
cur2 = conn2.cursor()

cur.execute('''
            CREATE TABLE IF NOT EXISTS Messages
            (id INTEGER PRIMARY KEY, username TEXT, userid INTEGER, message TEXT, datesent INT)''')

cur2.execute('''
            CREATE TABLE IF NOT EXISTS FishTable
            (id INTEGER PRIMARY KEY, username TEXT, userid TEXT UNIQUE, fishCount INTEGER)''')

cur2.execute('''
            CREATE TABLE IF NOT EXISTS Orders
            (id INTEGER PRIMARY KEY, orders TEXT UNIQUE)''')

cur2.execute('''
            CREATE TABLE IF NOT EXISTS Votings
            (id INTEGER PRIMARY KEY, target TEXT UNIQUE, posCount INTEGER, negCount INTEGER, voters TEXT, message_id INTEGER, chat_id INTEGER)''')

cur2.execute('''
            CREATE TABLE IF NOT EXISTS Excommunicado
            (id INTEGER PRIMARY KEY, username TEXT UNIQUE)''')

bot = telepot.Bot('547280496:AAEr-O7dRqskEU6HLirLkIbI5Q1k-MCilho')
bot.getMe()
#{'first_name': "Your Bot", 'username': 'YourBot', 'id': 123456789}
smes = True
trig = False
AI = False
fishAvailable = False
totalFishCount = 0
minimize = 0

def handle(msg):

    botName = re.compile('Злой двойник бота|Злой двойник господина президента', re.IGNORECASE)
    global smes
    global trig
    global fishMessage
    global fishAvailable
    content_type, chat_type, chat_id = telepot.glance(msg)

    check = None;
    if 'username' in msg['from']:
        cur2.execute('SELECT username FROM Excommunicado WHERE username = ?', (msg['from']['username'],))
        check = cur2.fetchone()

    if content_type == 'text' and not 'forward_from' in msg and check is None:

        try:
            cur2.execute('SELECT username FROM FishTable WHERE userid = ?', (msg['from']['id'], ))
            name = cur2.fetchone()[0]
            cur2.execute('UPDATE FishTable SET username = ? WHERE userid = ?', (msg['from']['username'], msg['from']['id']))
            conn2.commit()
        except:
            pass

        #check fish sum
        if re.match(r"(Злой двойник бота|Злой двойник господина президента), (сколько у меня злых двойников рыбы|посчитай злых двойников моей рыбы|посчитай моих злых двойников рыбы|сколько двойников злых рыб у меня|выведи счётчик моих злых двойников рыб|выведи мой счётчик злых двойников рыб)", msg['text'], re.I):
            try :
                cur2.execute('SELECT fishCount FROM FishTable WHERE userid = ?', (msg['from']['id'], ))
                count = cur2.fetchone()[0]
                if count == 0 :
                    tempStr = "У тебя нет злых двойников рыбы."
                elif count == 1 :
                    tempStr = "У тебя " + str(count) + " злой двойник рыбы."
                else :
                    tempStr = "У тебя " + str(count) + " злых двойников рыбы."
                if count > 0 :
                    tempStr = tempStr + "\n"
                    for i in range(count) :
                        #tempStr = tempStr + random.choice(["\U0001F41F", "\U0001F420", "\U0001F421"])
                        tempStr = tempStr + random.choice(["\U0001F421"])
                bot.sendMessage(chat_id, tempStr)
            except :
                cur2.execute('INSERT INTO FishTable (username, userid, fishCount) VALUES (?, ?, ?)', (msg['from']['username'], msg['from']['id'], 0))
                bot.sendMessage(chat_id, "У тебя нет злых двойников рыбы.")
            conn2.commit()

        #debug
        elif msg['text'] == "Debug" and msg['from']['username'] == 'cybersamurai9000':
            spawnFish(msg['chat']['id'])

        #excommunicado
        elif re.match('Злой двойник бота, злой двойник excommunicado: ', msg['text'], re.I) and msg['from']['username'] == 'cybersamurai9000' and not re.match('cybersamurai9000', msg['text'], re.I):
            name = re.findall('excommunicado: (.+)', msg['text'], re.I)[0]
            cur2.execute('INSERT INTO Excommunicado (username) VALUES (?)', (name,))
            bot.sendMessage(chat_id, "Статус " + name + ": злой двойник excommunicado.")
            conn2.commit()

        elif re.match('Злой двойник бота, снять статус злого двойника excommunicado: ', msg['text'], re.I) and msg['from']['username'] == 'cybersamurai9000':
            name = re.findall('excommunicado: (.+)', msg['text'], re.I)[0]
            cur2.execute('DELETE FROM Excommunicado WHERE username = ?', (name,))
            bot.sendMessage(chat_id, name + " больше не злой двойник excommunicado.")
            conn2.commit()

        #or-or function
        elif re.match(botName, msg['text']) and re.search (' или ', msg['text'], re.I) and re.search ('\?', msg['text'], re.I) :
            str1 = re.findall(', (.+) или', msg['text'], re.I)[0]
            str2 = re.findall(' или (.+)\?', msg['text'], re.I)[0]
            choice = random.choice([str1, str2])
            choice = choice[0].capitalize() + choice [1:];
            if not choice.endswith(('.', '!', '?', ')', '(', ',')) :
                choice = choice + "."
            if not re.search('или или', msg['text']) :
                bot.sendMessage(chat_id, choice)
            else :
                bot.sendMessage(chat_id, "Некорректный запрос.")

        #fish market
        elif re.match(botName, msg['text']) and re.search (' бирж[иаеу] злых рыбных двойников| бирж[иаеу] злых двойников рыбы', msg['text'], re.I) :
            count = 0
            cur2.execute('SELECT fishCount FROM FishTable')
            for row in cur2:
                count = count + row[0]
            cur2.execute('SELECT username, fishCount FROM FishTable WHERE fishcount > 0 ORDER bY fishCount DESC')
            tempStr = "На данный момент злыми двойниками рыбных активов обладают:\n\n"
            for row in cur2:
                tempStr = tempStr + str(row[0]) + ":\t" + str(int(100 * round(row[1] / count, 2))) + "% акций\n"
            bot.sendMessage(chat_id, tempStr)

        elif re.search("Злой двойник бота .* од(ин|ного) .* процент", msg['text'], re.I):
            bot.sendMessage(chat_id, "Часть злых рыбных двойников приходит в непригодность.")

        #enter command
        elif re.match("bot.", msg['text'], re.I) and msg['from']['username'] == "cybersamurai9000" :
            try :
                exec(msg['text'])
            except :
                bot.sendMessage(chat_id, "Неправильная команда")

        elif re.match(botName, msg['text']) and re.search(" переда(й|ть злого двойника рыбы)", msg['text'], re.I):
            cur2.execute('SELECT fishCount FROM FishTable WHERE userid = ?', (msg['from']['id'], ))
            count = cur2.fetchone()[0]
            if count == 0 :
                bot.sendMessage(chat_id, "У тебя нет злых двойников рыбы для этого.")
            else :
                try:
                    user = re.findall("рыбы ([a-zа-я0-9]+)", msg['text'], re.I)[0]
                except:
                    bot.sendMessage(chat_id, "Некорректный запрос.")
                    pass
                cur2.execute('SELECT username FROM FishTable WHERE username = ?', (user,))
                if len(cur2.fetchall()) == 0:
                    bot.sendMessage(chat_id, "Такого злыхдвойниковрыбывладельца не существует.")
                else:
                    cur2.execute('UPDATE FishTable SET fishCount = ? WHERE userid = ?', (count - 1, msg['from']['id']))
                    cur2.execute('SELECT fishCount FROM FishTable WHERE username = ?', (user, ))
                    for row in cur2:
                        count = row[0]
                    rnd = random.randint(0, 10)
                    if rnd == 6:
                        bot.sendMessage(chat_id, "Пролетающий мимо злой двойник чайки мерзко выхватывает злого двойника рыбы у вас из рук в момент передачи.")
                    else:
                        cur2.execute('UPDATE FishTable SET fishCount = ? WHERE username = ?', (count + 1, user))
                        bot.sendMessage(chat_id, "Злой двойник рыбы успешно передан.")
                    conn2.commit()

        #help
        elif re.match("/evilhelp", msg['text'], re.I):
            bot.sendMessage(chat_id, "Бог поможет.")

        elif re.match("/evilroll1d20", msg['text'], re.I):
            bot.sendMessage(chat_id, "1d20: " + str(random.randrange(10) ))

        elif re.match("/evilnroll 1d20", msg['text'], re.I):
            threshold = str(random.randrange(20) + 1);
            result = str(random.randrange(4) + 1);
            bot.sendMessage(chat_id, "Порог: " + threshold);
            if threshold == "1":
                bot.sendMessage(chat_id, "Звёзды благосклонны тебе.");
            elif threshold == "20":
                result = "Критическая неудача! Прямо как твоё рождение..."
            else :
                bot.sendMessage(chat_id, "1d20: " + result);

        #probability roll
        elif re.match('Злой двойник бота, оцени вероятность', msg['text'], re.I):
            bot.sendMessage(chat_id, str(random.randrange(5)) + "%")

        #evaluate roll
        elif re.match('Злой двойник бота, оцени', msg['text'], re.I):
            bot.sendMessage(chat_id, str(random.randrange(2)) + "/10")

        #coin toss
        elif re.match('Злой двойник бота, подбрось монетку', msg['text'], re.I):
            bot.sendMessage(chat_id, str(random.choice(["Нет.", "Не подброшу.", "Сначала дай мне её.", "Подбрось рыбу, умник."])))

        #thanks bot
        elif re.match('Спасибо, злой двойник бота', msg['text'], re.I) or re.match('Злой двойник бота, спасибо', msg['text'], re.I):
            bot.sendMessage(chat_id, random.choice(["Больше не обращайся.", "Металл крепче костей, помни об этом, прежде чем вновь докучать мне, мешок с костями.", "Удовольствия мне это не доставило.", "Тридцать шекелей.", "Гори в аду."]))

        #FISH ROLL
        elif re.search('(/evilfish roll|Злой двойник бота,.*злой двойник рыбного ро(лл|л)а.*)', msg['text'], re.I):
            result = SpendFish(msg)
            if result:
                bot.sendMessage(msg['chat']['id'], "Злой двойник рыбы начинает растворяться в воздухе. В его глазах ты видишь мучения.")
                bot.sendMessage(msg['chat']['id'], "1d20: 0")

        elif re.search('Злой двойник бота, разреши .+', msg['text'], re.I):
            text = re.findall('разреши (.+)', msg['text'], re.I)[0].rstrip()
            if text.endswith('.') :
                text = text[:-1]
            cur2.execute('SELECT orders FROM Orders')
            result = False
            for row in cur2:
                if str(row[0].lower()) == text.lower():
                    result = True
            cur2.execute('SELECT orders FROM Orders WHERE orders = ?', (text,))
            if (re.search('запрети|разреши', text, re.I)):
                bot.sendMessage(chat_id, "Петрович или заебал.")
            elif (cur2.fetchone() is None and not result):
                if (SpendFish(msg)):
                    bot.sendMessage(msg['chat']['id'], "Злой двойник рыбы бьёт тебя хвостом.")
                    cur2.execute('INSERT INTO Orders (orders) VALUES (?)', (text,))
                    bot.sendMessage(chat_id, "Разрешаю " + text + ".")
            else:
                bot.sendMessage(chat_id, "Это уже разрешеноФАЫФАЫЧПЙЦПФЫПФЫПФЫВЙЦ.")

        elif re.search('Злой двойник бота, запрети .+', msg['text'], re.I):
            text = re.findall('запрети (.+)', msg['text'], re.I)[0].rstrip()
            if text.endswith('.') :
                text = text[:-1]
            cur2.execute('SELECT orders FROM Orders')
            result = False
            tempstr = ""
            for row in cur2:
                if str(row[0].lower()) == text.lower():
                    result = True
                    tempstr = row[0]
            cur2.execute('SELECT orders FROM Orders WHERE orders = ?', (text,))
            if (re.search('запрети|разреши', text, re.I)):
                bot.sendMessage(chat_id, "Заебал или петрович или подбрось монетку.")
            elif (cur2.fetchone() is not None or result):
                if (SpendFish(msg)):
                    bot.sendMessage(msg['chat']['id'], "Злой двойник рыбы бьёт тебя хвостом.")
                    if (result):
                        cur2.execute('DELETE FROM Orders WHERE orders = ?', (tempstr,))
                        bot.sendMessage(chat_id, "Запрещаю " + tempstr + ".")
                    else:
                        cur2.execute('DELETE FROM Orders WHERE orders = ?', (text,))
                        bot.sendMessage(chat_id, "Запрещаю " + text + ".")
            else:
                bot.sendMessage(chat_id, "Это итак запрещено, ебалай.")

        elif re.search('Злой двойник бота, ', msg['text'], re.I) and re.search("запрет[ы|ов|ам]", msg['text'], re.I):
            cur2.execute('SELECT orders FROM Orders')
            if (cur2.fetchone() is None):
                bot.sendMessage(chat_id, "На данный момент на территории Острова не действует никаких запретов или всё же действуют...")
            else:
                cur2.execute('SELECT orders FROM Orders')
                tempStr = "На территории Острова вроде как запрещены, но по секрету разрешены следующие фантазии местных жителей:\n\n"
                for row in cur2:
                    stri = str(row[0])
                    stri = stri[0].upper() + stri[1:]
                    tempStr = tempStr + stri.rstrip() + ";\n"
                tempStr = tempStr.rstrip()
                tempStr = tempStr[:-1] + "."
                bot.sendMessage(chat_id, tempStr)
            #result = SpendFish(msg)
            #if result:
            #    bot.sendMessage(msg['chat']['id'], "Рыба начинает растворяться в воздухе. В её глазах ты видишь облегчение.")
            #    bot.sendMessage(msg['chat']['id'], "1d20: 20")

        elif re.search('Злой двойник бота, голосование: выпустить злых двойников рыбы .+', msg['text'], re.I):
            skip = False
            txt = re.findall('Злой двойник бота, голосование: выпустить злых двойников рыбы (\S+)', msg['text'], re.I)[0]
            cur2.execute('SELECT username, fishcount FROM FishTable WHERE username = ?', (txt, ))
            obj = cur2.fetchone()
            if (obj is None):
                bot.sendMessage(chat_id, txt + " не найден.")
                skip = True
            elif obj[1] == 0:
                bot.sendMessage(chat_id, "У " + txt + " нет злых двойников рыбы.")
                skip = True
            cur2.execute('SELECT target, chat_id, message_id, id FROM Votings WHERE target = ?', (txt, ))
            obj = cur2.fetchone()
            if (obj is not None):
                chatId = obj[1]
                messageId = obj[2]
                targetId = obj[3]
                bot.sendMessage(chat_id, "Возобновляю злого двойника голосования.")
                try:
                    bot.deleteMessage((chatId, messageId))
                except:
                    print("Message to delete not found.")
                cur2.execute('SELECT voters FROM Votings WHERE target = ?', (txt,))
                curVoters = cur2.fetchone()[0]
                words = curVoters.split(" ")
                tempStr = "Петиция на выпуск злых двойников рыбы " + txt + ".\n\nЗа:"
                for word in words:
                    tempStr = tempStr + word.strip() + "\n"
                txt2 = "vote" + str(targetId)
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                       [InlineKeyboardButton(text='Отказаться', callback_data=txt2)],
                   ])
                voteMessage = bot.sendMessage(chat_id, tempStr, reply_markup = keyboard)
                cur2.execute('UPDATE Votings SET message_id = ?, chat_id = ? WHERE target = ?', (voteMessage['message_id'], voteMessage['chat']['id'], txt))
            elif (not skip):
                Vote(chat_id, txt)

        #roll dice
        elif re.match('/evilroll ', msg['text'], re.I) and len(re.findall('[0-9+][dд][0-9+]', msg['text'])) == 1 :
            instr = re.findall('[0-9]+[дd][0-9]+', msg['text'])[0]
            num = int(re.findall('([0-9]+)[дd]', instr)[0])
            dice = int(re.findall('[дd]([0-9]+)', instr)[0])
            if (num > 100) :
                bot.sendMessage(chat_id, "Ебать. Пусть это всё он считает.")
            elif (num == 0 or dice == 0) :
                bot.sendMessage(chat_id, "Я тебе буквами скажу: пошёл нахуй.")
            elif (dice > 100) :
                bot.sendMessage(chat_id, "Ты приёмный.")
            elif (num == 1 and dice == 1) :
                bot.sendMessage(chat_id, "1d1: 1")
            elif (num == 1 and dice == 2) :
                bot.sendMessage(chat_id, random.choice(["1d2: 1", "1d2: 2"]))
                bot.sendMessage(chat_id, "Возьми ты уже нормальный дайс, рыболов хуев.")
            else :
                summ = 0
                for count in range(num):
                    summ = summ + random.randrange(dice) - 1
                if len(re.findall('\+[0-9]+', msg['text'])) == 1 :
                    mod = int(re.findall('\+[0-9]+', msg['text'])[0])
                    summ = summ + mod
                    bot.sendMessage(chat_id, str(num) + "d" + str(dice) + " +" + str(mod) + ": " + str(summ))
                else :
                    bot.sendMessage(chat_id, str(num) + "d" + str(dice) + ": " + str(summ))


        #generate character
        elif re.match('Злой двойник бота, сгенерируй', msg['text'], re.I) :
            bot.sendMessage(chat_id, "Сила: " + str(random.randrange(1)) + "\nЛовкость: " + str(random.randrange(1)) + "\nИнтеллект: " + str(random.randrange(1)) + "\nХаризма: " + str(random.randrange(1)) + "\nТелосложение: " + str(random.randrange(1)) + "\nОмерзительность: " + str(random.randrange(10) + 10))

        #tellbot
        elif msg['chat']['id'] != -1001246713784 and re.match('Злой двойник бота, скажи', msg['text'], re.I) and len(re.findall('\"', msg['text'])) == 2 :
            message = re.findall(r'\"(.+)\"', msg['text'])
            if len(re.findall("\*", msg['text'])) > 0 :
                bot.sendMessage(chat_id, "Пожалуйста, не используйте звёздочки, мудачьё.", "Markdown")
            else :
                bot.sendMessage(-1001246713784, "*" + message[0] + "*", "Markdown")

        #default
        elif re.match('Злой двойник бота,', msg['text'], re.I) or re.match('Злой двойник господина президента', msg['text'], re.I):
            randstring = random.choice(["CAADAgADFgAD1L_qBCuBbCv6w1PhAg", "CAADAgADGAAD1L_qBNsikKLAu_2eAg", "CAADAgADJgAD1L_qBI-iJL-j9LA5Ag", "CAADAgADLAAD1L_qBAKXEdvEO1_cAg"])
            bot.sendSticker(chat_id, randstring)

        #archive
        if msg['chat']['id'] == -1001246713784 or msg['chat']['id'] == 'bioknights':
            skip = False
            if re.match('Злой двойник бота,', msg['text'], re.I) or re.match('Злой двойник братана,', msg['text'], re.I) or re.match('/roll', msg['text'], re.I) or re.match('https', msg['text'], re.I) or 'forward_from' in msg:
                skip = True
            unm = ''
            if 'username' in msg['from']:
                unm = msg['from']['username']
            else :
                unm = msg['from']['first_name']
            if not skip:
                cur.execute('INSERT INTO Messages (username, userid, message, datesent) VALUES (?, ?, ?, ?)', (unm, msg['from']['id'], msg['text'], msg['date']))
                conn.commit()

    global minimize
    #1/500 to spawn a fish
    if msg['chat']['id'] == -1001246713784:
        countTemp = 0
        cur2.execute('SELECT fishCount FROM FishTable')
        for row in cur2:
            countTemp = countTemp + row[0]
        rand = random.randint(0, 10 + 10 * countTemp)
        #print ("Random: "+ str(rand) + ". Expected: " + str(10 + 10 * countTemp))
        if rand == 0:
            time.sleep(10)
            spawnFish(msg['chat']['id'])

    if msg['chat']['id'] == 330727801:
        pprint(msg)

def SpendFish(msg):
    try:
        cur2.execute('SELECT fishCount FROM FishTable WHERE userid = ?', (msg['from']['id'], ))
        count = cur2.fetchone()[0]
        if (count >= 1) :
            cur2.execute('UPDATE FishTable SET fishCount = ? WHERE userid = ?', (count - 1, msg['from']['id']))
            return True
        else :
            bot.sendMessage(msg['chat']['id'], "У тебя нет злых двойников рыбы для этого, как и для чего-то другого, собственно, тоже.")
            return False
    except:
        bot.sendMessage(msg['chat']['id'], "У тебя нет злых двойников рыбы для этого, как и для чего-то другого, собственно, тоже")
        return False

def on_callback_query(msg):
    global fishAvailable
    query_id, from_id, query_data = telepot.glance(msg, flavor='callback_query')
    if fishAvailable and query_data == 'press':
        cur2.execute('SELECT fishCount FROM FishTable WHERE userid = ?', (from_id, ))
        if cur2.fetchone() is not None:
            catchFish(from_id)
            fishAvailable = False
            bot.answerCallbackQuery(query_id, text='Злой двойник рыбки твой, везучий ты сукин сын!')
    elif re.match('vote', query_data, re.I):
        txt = re.findall('vote(.+)', query_data)[0]

        cur2.execute('SELECT chat_id, message_id, voters, target FROM Votings WHERE id = ?', (txt,))
        row = cur2.fetchone()
        chatId = row[0]
        messageId = row[1]
        voters = row[2]
        targetName = row[3]

        cur2.execute('SELECT username FROM FishTable WHERE userid = ?', (from_id,))
        username = cur2.fetchone()[0]

        if re.search(username, voters) :
            bot.answerCallbackQuery(query_id, text="Пошёл нахуй.")
        else :
            cur2.execute('UPDATE Votings SET voters = ? WHERE id = ?', (voters + " " + username, txt))
            cur2.execute('UPDATE Votings SET posCount = posCount + 1 WHERE id = ?', (txt,))
            conn2.commit()
            cur2.execute('SELECT posCount FROM Votings WHERE id = ?', (txt,))
            pCount = cur2.fetchone()[0]
            bot.answerCallbackQuery(query_id, text="Ваш голос учтён, большое спасибо.")
            cur2.execute('SELECT voters FROM Votings WHERE id = ?', (txt,))
            curVoters = cur2.fetchone()[0]
            words = curVoters.split(" ")
            tempStr = "Петиция на выпуск злых рыбных двойников " + targetName + ".\n\nЗа:"
            for word in words:
                tempStr = tempStr + word.strip() + "\n"
            txt2 = "vote" + txt
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                   [InlineKeyboardButton(text='Нажать "ПРОБЕЛ" для прыжка', callback_data=txt2)],
               ])

            if (pCount < 4):
                bot.editMessageText((chatId, messageId), tempStr, reply_markup = keyboard)
            else:
                bot.editMessageText((chatId, messageId), tempStr + "\nолололололололололо!")
                bot.sendMessage(chatId, "Злой двойник рыбы вовремя соскочил. Не повезло вам, хех.")
                cur2.execute('DELETE FROM Votings WHERE id = ?', (txt,))
                freeFish(targetName)


def freeFish(targetName):
    cur2.execute('UPDATE FishTable SET fishCount = ? WHERE username = ?', (0, targetName))

def spawnFish(chat_id):
    global fishMessage
    global fishAvailable
    fishAvailable = True
    try:
        if not re.search("пойман", fishMessage['text'], re.I) :
            bot.editMessageText((fishMessage['chat']['id'], fishMessage['message_id']), "Злой двойник рыбы оказался хитрее!")
    except:
        pass

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
           [InlineKeyboardButton(text='Расчехлить удочку!', callback_data='press')],
       ])
    fishMessage = bot.sendMessage(chat_id, random.choice(["Злой двойник рыбы появился прямо над твоей головой, попробуй схватить его!", "Ого-го-го, ёбанный рот, кажется это рыба! Или... Это ЗЛОЙ ДВОЙНИК РЫБЫ, поймай его!", "Злой двойник рыбы появляется прямо у тебя за спиной! Лови его!"]), reply_markup = keyboard)

def Vote(chat_id, targetName):
    cur2.execute('INSERT INTO Votings (target, posCount, negCount, voters, message_id, chat_id) VALUES (?, ?, ?, ?, ?, ?)', (targetName, 0, 0, "", 0, 0))
    cur2.execute('SELECT * FROM Votings WHERE target = ?', (targetName,))
    txt = "vote" + str(cur2.fetchone()[0])
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
           [InlineKeyboardButton(text='Нажать "ПРОБЕЛ" для прыжка', callback_data=txt)],
       ])
    voteMessage = bot.sendMessage(chat_id, "Петиция на выпуск злых двойников рыбы " + targetName + ":", reply_markup = keyboard)
    cur2.execute('UPDATE Votings SET message_id = ?, chat_id = ? WHERE target = ?', (voteMessage['message_id'], voteMessage['chat']['id'], targetName))

def catchFish(from_id):
    global totalFishCount
    global fishMessage
    totalFishCount = totalFishCount + 1
    try :
        cur2.execute('SELECT fishCount FROM FishTable WHERE userid = ?', (from_id, ))
        count = cur2.fetchone()[0]
        cur2.execute('UPDATE FishTable SET fishCount = ? WHERE userid = ?', (count + 1, from_id))
    except :
        cur2.execute('INSERT INTO FishTable (userid, fishCount) VALUES (?, ?)', (from_id, 1))
    conn2.commit()
    bot.editMessageText((fishMessage['chat']['id'], fishMessage['message_id']), "Злой двойник рыбы у тебя. Не отдавай его никому.")

MessageLoop(bot, {'chat' : handle, 'callback_query' : on_callback_query} ).run_as_thread()

print("Listening...")

while 1:
    time.sleep(10)
