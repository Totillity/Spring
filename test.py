from parser import parse
from scanner import scan
from dragon_error import DragonError


def main():
    with open("test.spng", "r") as file:
        text = file.read()
    try:
        print(parse(scan(text)))
    except DragonError as e:
        e.finish("<string>", text)




main()
