import sqlite3
import random as ran
from typing import Literal
from functools import wraps



def using_sql_con(func:callable) -> callable:
    @wraps(func)
    def wrapper(*args, **kwargs):
        con = sqlite3.connect("db.db")
        cur = con.cursor()
        try: 
            result = func(cur, *args, **kwargs)
            con.commit()
        except Exception as e:
            con.rollback()
            print(f"ERROR:    {e}\n")
        finally:
            con.close()
        return result
    return wrapper


@using_sql_con
def create_tables(cur) -> None:
    cur.execute("""
    CREATE TABLE IF NOT EXISTS players(
        player_id INTEGER,
        username TEXT,
        role TEXT,
        mafia_vote INTEGER,
        citizen_vote INTEGER,
        voted INTEGER,
        dead INTEGER
    )""")

@using_sql_con
def insert_player(cur, player_id:int, username:str) -> None: #сделать проверку
    sql = f"INSERT INTO players (player_id, username, mafia_vote, citizen_vote, voted, dead)\
        VALUES (?, ?, ?, ?, ?, ?)"
    cur.execute(sql, (player_id, username, 0, 0, 0, 0))

@using_sql_con
def players_amount(cur) -> int:
    sql = "SELECT * FROM players"
    cur.execute(sql)
    res = cur.fetchall()
    return len(res)

@using_sql_con
def get_players_roles(cur) -> list:
    sql = "SELECT player_id, role FROM players "
    cur.execute(sql)
    data = cur.fetchall()
    return data

@using_sql_con
def get_mafia_usernames(cur) -> str:
    sql = "SELECT username FROM players WHERE role = 'mafia' "
    cur.execute(sql)

    data = cur.fetchall()
    names = ""
    for row in data:
        name = row[0]
        names+=name + "\n"
    return names

@using_sql_con
def get_all_alive(cur) -> list[str]:
    sql = "SELECT username FROM players WHERE dead = 0" 
    cur.execute(sql)
    alive_players = cur.fetchall()
    alive_list = [name[0] for name in alive_players]

    return alive_list

@using_sql_con
def set_roles(cur, players:int) -> None:
    # extended = False if players<7 else extended
    # if not extended:
    game_roles = ["citizen"] * players
    mafias = int(players*0.4)
    for i in range(mafias):
        game_roles[i] = 'mafia'
    ran.shuffle(game_roles)
    # if extended:
    #     game_roles = ["citizen"] * players
    #     mafias = int(players*0.4)
    #     left = len(game_roles) - mafias
    #     for i in range(mafias):
    #         game_roles[i] = 'mafia'
    #     game_roles[left-2] = 'sheriff'
    #     game_roles[left-1] = 'maniac'
    #     game_roles[left] = 'doctor'
    #     game_roles[left+1] = "robber" 
    #     ran.shuffle(game_roles)
    cur.execute("SELECT player_id FROM players")
    players_id = cur.fetchall()
    for role, player_id in zip(game_roles, players_id):
        sql = "UPDATE players SET role =? WHERE player_id =?"
        cur.execute(sql, (role, player_id[0]))

        
@using_sql_con
def vote(cur, type: Literal["mafia_vote", "citizen_vote"], username:str, player_id:int) -> bool:
    cur.execute("SELECT username FROM players WHERE player_id=? AND dead=0 AND voted=0", (player_id,))
    can_vote = cur.fetchone()
    if can_vote: 
        cur.execute(f"UPDATE players SET {type} = {type} + 1 WHERE username=?", (username,))
        cur.execute("UPDATE players SET voted=1 WHERE player_id=?", (player_id,))
        return True
    return False
    
# @using_sql_con
# def sheriff_check(cur, username, player_id) -> str or None:
#     cur.execute("SELECT username FROM players WHERE player_id=? AND role='sheriff' AND dead=0 AND used_special=0", (player_id,))
#     can_check = cur.fetchone()
#     if can_check:
#         cur.execute("UPDATE players SET used_special=1 WHERE player_id=?", (player_id,))
#         cur.execute("SELECT role FROM players WHERE username=?", (username,))
#         role = cur.fetchone()[0]
#         return role
#     return "Вы не можете узнать роль данного игрока в данный момент."
        

# @using_sql_con
# def maniac_kill(cur):
#     ...

# @using_sql_con
# def doctor_cure(cur):
#     ...

# @using_sql_con
# def robber_rob(cur):
#     ...

@using_sql_con
def mafia_kill(cur) -> str:
    cur.execute("SELECT MAX(mafia_vote) FROM players")
    max_votes = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM players WHERE role = 'mafia' AND dead=0")
    mafia_alive = cur.fetchone()[0]
    username_killed = "никого"
    if max_votes >= 0.5*mafia_alive:
        cur.execute("SELECT username FROM players WHERE mafia_vote=?", (max_votes,))
        username_killed = cur.fetchone()[0]
        cur.execute("UPDATE players SET dead=1 WHERE username=? AND dead=0", (username_killed,))
    return username_killed

@using_sql_con
def citizen_kill(cur) -> str:
    cur.execute("SELECT MAX(citizen_vote) FROM players")
    max_votes = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM players WHERE citizen_vote=?", (max_votes,))
    max_count = cur.fetchone()[0]
    username_killed = "никого"
    if max_count == 1:
        cur.execute("SELECT username FROM players WHERE citizen_vote=?", (max_votes,))
        username_killed = cur.fetchone()[0]
        cur.execute("UPDATE players SET dead=1 WHERE username=? AND dead=0", (username_killed,))
    return username_killed

@using_sql_con
def check_winner(cur) -> str | None:
    cur.execute("SELECT COUNT(*) FROM players WHERE role='mafia' AND dead=0")
    mafia_alive = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM players WHERE role!='mafia' AND dead=0")
    citizens_alive = cur.fetchone()[0]
    if mafia_alive >= citizens_alive:
        return "Mafia"
    elif mafia_alive == 0:
        return "Citizens"
    return None

@using_sql_con
def clear(cur, game_over:bool = False) -> None:
    sql = "UPDATE players SET citizen_vote=0, mafia_vote=0, voted=0"
    if game_over:
        sql += ", dead=0"
    cur.execute(sql)


if __name__ == "__main__":
    ...
    create_tables()
    # insert_player(12, "гиде")
    # set_roles(7, True)
    # print(players_amount())
    # print(get_mafia_usernames())
    # print(get_players_roles())
    # print(get_all_alive())

    # print(vote("mafia_vote", "JL8QJLCY", 3))
    # print(vote("mafia_vote", "бебра", 2))
    # print(vote("mafia_vote", "олень", 1))
    # print(vote("mafia_vote", "вася пупкин", 1))

    # print(mafia_kill())

    # print(citizen_kill())

    # print(set_roles())

    # print(check_winner())
    # clear(True)

    # print(sheriff_check('e', 6))



    