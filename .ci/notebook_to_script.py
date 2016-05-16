import argparse
import json



def extract_code(file_like):
    cells = json.load(file_like)
    for cell in cells:
        

def main():
    parser = argparse.ArgumentParser(
        'Extract commands from an iPython notebook.')
    parser.add_argument('NOTEBOOK', type=argparse.FileType('r'),
                        help='An iPython notebook.')

    parser.parse_args()


