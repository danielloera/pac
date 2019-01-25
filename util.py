from difflib import SequenceMatcher

class Colors:
    reset = "\033[0m"
    fg = {
        "black": "\033[30m",
        "red": "\033[31m",
        "green": "\033[32m",
        "orange": "\033[33m",
        "blue": "\033[34m",
        "purple": "\033[35m",
        "cyan": "\033[36m",
        "white": "\033[37m",
        "darkgrey": "\033[90m",
        "lightred": "\033[91m",
        "lightgreen": "\033[92m",
        "yellow": "\033[93m",
        "lightblue": "\033[94m",
        "pink": "\033[95m",
        "lightcyan": "\033[96m"
    }


def colored(output, color):
    return Colors.fg[color] + str(output) + Colors.reset


def lastname_lex(users):
    return sorted(users, key=lambda user: user.name.split()[1].upper())


def get_selection(items, item_type):
    if len(items) == 1:
        return 0
    for i, item in enumerate(items):
        print("{i}: {name}".format(i=i, name=item.name))
    print()
    return int(input(
        "Which {} would you like to select? ".format(item_type)))

def get_diff_ratio(string_a, string_b):
    return SequenceMatcher(lambda x: x == " ", string_a, string_b).ratio()
