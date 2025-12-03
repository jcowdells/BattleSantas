from common import Direction

"""
You need to change the server host in order to connect to multiplayer. The IP will be displayed on the board when the game
is running.
"""
SERVER_HOST = "127.0.1.1"
SERVER_PORT = 27910

def handshake() -> str:
    """
    This function will get called when your santa connects to the server. You should return a string which will be your
    team name!
    """
    return "<insert creative team name here>"

def take_turn(game_state: dict) -> Direction:
    """
    This function will get called whenever your santa takes a turn in the game. "game_state" is a dictionary that is
    formatted like so:
        game_state = {
            "grid_size": (8, 8)                       # for example!!
            "santas": [(0, 0), (1, 1)],               # for example!!
            "gifts": [(2, 2), (6, 3), (7, 1), (4, 4)] # for example!!
        }
    The grid size represents how many tiles wide and tall the grid is, so (3, 5) means 3 wide and 5 tall.
    The lists represent the coordinates of each santa and each gift in the game. Your santa will always be the first
    in the list, so you can do:
        position = game_state["santas"][0]
    to get your santa's position.

    To start with, you could focus on your own santa, loop through the list to find the closest gift, and head towards
    it. If you want to get tactical, perhaps try and collect the presents that the enemy santas will want to collect to
    try and stop them winning!

    You should return one of: Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT - this will be the direction
    that your santa will move in.
    """
    pass
