from spkt import compile_spkt, ast_to_spkt
from spring import parse_text


def main():
    path = "test.spng"
    with open(path, "r") as file:
        text = file.read()

    program = parse_text(path, text)

    compile_spkt(ast_to_spkt(program, path), and_run=True)


if __name__ == "__main__":
    main()
