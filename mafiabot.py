from telebot import TeleBot
from telebot.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import database as db
import os
from random import choice, randint
from time import sleep
# from randnamegen import generate_name



if not os.path.exists("db.db"):
    db.create_tables()

token = ""
bot = TeleBot(token)

game = False
night = True

def get_killed(night:bool) -> str:
    if not night:
        username_killed = db.citizen_kill()
        return f"Citizens voted out: {username_killed}"
    username_killed = db.mafia_kill()
    return f"Mafia killed: {username_killed}"

def autoplay_citizen(message: Message):
    players_roles = db.get_players_roles()
    for player_id, _ in players_roles:
        usernames = db.get_all_alive()
        name = f"robot{player_id}"
        if player_id < 5 and name in usernames:
            usernames.remove(name)
            vote_username = choice(usernames)
            db.vote("citizen_vote", vote_username, player_id)
            bot.send_message(message.chat.id, f"{name} voted against {vote_username}")
            sleep(randint(5, 15)/10)

def autoplay_mafia():
    players_roles = db.get_players_roles()
    for player_id, role in players_roles:
        usernames = db.get_all_alive()
        name = f"robot_{player_id}"
        if player_id < 5 and name in usernames and role == "mafia":
            usernames.remove(name)
            vote_username = choice(usernames)
            db.vote("mafia_vote", vote_username, player_id)


def game_loop(message:Message):
    global night, game
    bot.send_message(message.chat.id, "Welcome to the game! You have 20 seconds to get to know each other before the game starts.")
    sleep(10)
    while True:
        msg = get_killed(night)
        bot.send_message(message.chat.id, msg)
        if not night:
            bot.send_message(message.chat.id, "It's nighttime, the city is asleep, while the mafia is awake!")
        else:
            bot.send_message(message.chat.id, "It's daytime, the city is awake!")
        winner = db.check_winner()
        if winner == "Mafia" or winner == "Citizens":
            game = False
            bot.send_message(message.chat.id, f"Game over! The {winner} have won!")
            db.clear(True)
            return
        db.clear()
        night = not night
        alive = ", ".join(db.get_all_alive())
        bot.send_message(message.chat.id, f"Players alive: {alive}")
        sleep(10)
        autoplay_mafia() if night else autoplay_citizen(message)




@bot.message_handler(func=lambda message: message.text.lower() == 'готов!', chat_types=['private'])
def send_text(message:Message):
    bot.send_message(message.chat.id, f"{message.from_user.username} играет")
    bot.send_message(message.chat.id, "Вы добавлены в игру")
    db.insert_player(message.from_user.id, message.from_user.username)
    ReplyKeyboardRemove()


@bot.message_handler(commands=['start'])
def game_on(message:Message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("Готов!"))
    bot.send_message(message.chat.id, "Для того, тобы играть, нажмиите кнопку ниже!", reply_markup=keyboard)


@bot.message_handler(commands=['game'])
def start_game(message:Message):
    global game
    players = db.players_amount()
    if players >= 5 and not game:
        db.set_roles(players)
        players_roles = db.get_players_roles()
        mafia_usernames = db.get_mafia_usernames()
        for player_id, role in players_roles:
            try:
                bot.send_message(player_id, role)
            except:
                # print(f"ID: {player_id}\nROLE: {role}")   
                continue
            if role == "mafia":
                bot.send_message(player_id, f"Все мафиози:\n{mafia_usernames}")
        game=True
        bot.send_message(message.chat.id, "Игра началась!")
        game_loop(message)
        return
    bot.send_message(message.chat.id, "Не хватает людей!")
    for i in range(5 - players):
        bot_name = f"robot_{i}"
        db.insert_player(i, bot_name)
        bot.send_message(message.chat.id, f"{bot_name} was added to the game!")
        sleep(0.2)
    start_game(message)


@bot.message_handler(commands=['kick', 'vote'])
def kick(message: Message):
    username = ''.join(message.text.split()[1:])
    usernames = db.get_all_alive()
    if not night:
        if not username in usernames:
            bot.send_message(message.chat.id, "Такого игрока нет!")
            return
        voted = db.vote("citizen_vote", username, message.from_user.id)
        if voted:
            bot.send_message(message.chat.id, "Ваш голос учтён!")
            return
        bot.send_message(message.chat.id, "Вы уже голосовали!")
        return
    bot.send_message(message.chat.id, "Сейчас ночь, вы не можете проголосовать")

@bot.message_handler(commands=['kill'])
def kill(message:Message):
    username = ''.join(message.text.split()[1:])
    usernames = db.get_all_alive()
    mafia_usernames = db.get_mafia_usernames()
    if night: 
        if message.from_user.username in mafia_usernames:
            if not username in usernames:
                bot.send_message(message.chat.id, "There's no such player!")
                return
            voted = db.vote("mafia_vote", username, message.from_user.id)
            if voted:
                bot.send_message(message.chat.id, "Your vote has been counted!")
                return
            bot.send_message(message.chat.id, "You've already voted!")
            return
        bot.send_message(message.chat.id, "You can't kill, you are a citizen!")
        return
    bot.send_message(message.chat.id, "It's daytime, you can't kill now!")
    return
            

bot.polling(non_stop=True)
