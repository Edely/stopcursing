#!/usr/bin/env python
import os, time, re, sqlite3, sys, datetime
from slackclient import SlackClient

token = os.environ['SLACK_BOT_TOKEN']
sc = SlackClient(token)

# constants
RTM_READ_DELAY = 1
ADD_COMMAND = "add"
INIT = "init"
LIST_ALL_COMMANDS = "list all"
TOTAL_COMMAND = "total"
REMOVE_COMMAND = "remove"
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"


def parse_bot_commands(slack_events):
    """
        Parses a list of events coming from the Slack RTM API to find bot commands.
        If a bot command is found, this function returns a tuple of command and channel.
        If its not found, then this function returns None, None.
    """
    for event in slack_events:
        if event["type"] == "message" and not "subtype" in event:
            user_id, message = parse_direct_mention(event["text"])
            if user_id == starterbot_id:
                return message, event["channel"]
    return None, None

def parse_direct_mention(message_text):
    """
        Finds a direct mention (a mention that is at the beginning) in message text
        and returns the user ID which was mentioned. If there is no direct mention, returns None
    """
    matches = re.search(MENTION_REGEX, message_text)
    # the first group contains the username, the second group contains the remaining message
    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)

def connect_db(*args):
    conn = sqlite3.connect("curses.db")
    cursor = conn.cursor()
    while(conn is None):
        try:
            conn = sqlite3.connect("curses.db")
            cursor = conn.cursor()
        except Exception as e:
            print(e)

    if(len(args) != 1):
        print('connnection')
        print(conn)
        return conn
    else:
        print('first connection')
        print(conn)
        try:
            cursor.execute("""
                CREATE TABLE curses (times INTEGER, month INTEGER, year INTEGER, PRIMARY KEY (month, year))
            """)
        except Exception as e:
            print(e)

        try:    
            cursor.execute("""
                SELECT * FROM curses 
            """)
            dados = cursor.fetchall()
            print(dados)
    
            if len(dados) == 0:
                print('Empty DB. Populating Again')
                
                cursor.execute("""
                    INSERT INTO curses (times, month, year) VALUES (0, 2, 1990)
                """)
                conn.commit()
                cursor.execute("""
                    SELECT * FROM curses
                """)
        except Exception as e:
            print(e)

        print('closing connection')
        conn.close()


def update_curses(operator):
    conn = connect_db()
    cursor = conn.cursor()

    now = datetime.datetime.now()
    month = now.month
    year = now.year
    response = 'Didn\'t work'
    try:
        cursor.execute("SELECT SUM(times) FROM curses WHERE month=? AND year=?", (month, year,))
        number_of_curses = cursor.fetchall()[0][0]
    except Exception as e:
        print(e)

    if number_of_curses is None:
        cursor.execute("INSERT INTO curses (times, month, year) VALUES (0, {}, {})".format( month, year))
        conn.commit()
        number_of_curses = 0
        
    if operator == 'plus':
        number_of_curses +=  1
    elif operator == 'minus':
        number_of_curses -= 1

    try:
        print(year)
    
        cursor.execute("UPDATE curses SET times=? WHERE month=? AND year=?", (number_of_curses,month, year,))
        conn.commit()
        cursor.execute("SELECT * FROM curses")
        print(cursor.fetchall())
        if number_of_curses is None:
            number_of_curses = 0

        print(number_of_curses * 5)
        response = "Number of curses this month was: {}. You owe {} cents.".format(number_of_curses, number_of_curses * 5)

    except Exception as e:
        print(e)

    print(response)    
    return response


def read_curses():
    conn = connect_db() 
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT SUM(times) FROM CURSES
        """)
        number_of_curses = cursor.fetchall()[0][0]
        if number_of_curses is None:
            number_of_curses = 0
        response = "Number of curses this month was: {}. You owe {} cents.".format(number_of_curses, number_of_curses * 5)
    except Exception as e:
        response = 'Something Happened!'
    print('closing connection')
    conn.close()
    return response

def handle_command(command, channel):
    """
        Executes bot command if the command is known
    """
    
    # Default response is help text for the user
    default_response = "Not sure what you mean. Try *{}*.".format(LIST_ALL_COMMANDS)

    response = None
    
    if command.startswith(LIST_ALL_COMMANDS):
        response = """
    These are the commands:
    add - add a curse
    list all commands - print this list
    total - brings the total of curses
    remove - remove a curse
    """

    if command.startswith(ADD_COMMAND):
        response = update_curses('plus')

    if command.startswith(REMOVE_COMMAND):
        response = update_curses('minus')

    if command.startswith(INIT):
       response = read_curses()

    if command.startswith(TOTAL_COMMAND):
       response = read_curses()
        

    # Sends the response back to the channel
    sc.api_call(
        "chat.postMessage",
        channel=channel,
        text=response or default_response
    )

if __name__ == "__main__":
    connect_db('first_connection')    

    if sc.rtm_connect(with_team_state=False):
        print("Stop Cursing is online. Keep your mouth clean, kiddo!")
        # Read bot's user ID by calling Web API method `auth.test`
        starterbot_id = sc.api_call("auth.test")["user_id"] 
        while True:
            command, channel = parse_bot_commands(sc.rtm_read())
            if command:
                handle_command(command, channel)
            time.sleep(RTM_READ_DELAY)
    else:
        print("Connection failed.")