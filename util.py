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
