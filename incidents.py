# WMATA Incidents Display, adapted from Ken Schneider - https://github.com/kenschneider18

from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
import time, sys, os, requests, json, logging

def compute_offset(line):
    pxLength = len(line) * 4
    offset = (64 - pxLength) / 2
    return offset

def add_line(line, lines):
    offset = compute_offset(line)
    lines.append((line, offset))


def divide_lines(words, lines):
    line = words[0]

    for word in words[1:]:
        if len(line) < 17 and len(word) + 1 + len(line) < 17:
            line += ' ' + word
        else:
            add_line(line, lines)
            line = word
    # Add in last line
    add_line(line, lines)

def split_by_length_in_place(words):
    for index, word in enumerate(words):
        n = len(word)
        if n > 17:
            insert_offset = 0
            for x in range(0, n, 16):
                if x == 0:
                    words[index] = word[x : x + 16] + '-'
                else:
                    word_extension = word[x : x + 16]
                    if len(word_extension) >= 16:
                        word_extension += '-'
                    words.insert(index + insert_offset, word_extension)
                insert_offset += 1
    return words

def draw_message(canvas, message, font_file):
    logging.info("Got to draw message")
    font = graphics.Font()
    font.LoadFont(font_file)
    red_color = graphics.Color(255,0,0)
    yellow_color = graphics.Color(200,125,0)
    title_divided = message.split(': ', 1)

    title = ''
    if len(title_divided) == 1:
        words = split_by_length_in_place(message.split(' '))
    elif len(title_divided) == 2:
        title = split_by_length_in_place(title_divided[0])
        words = split_by_length_in_place(title_divided[1].split(' '))
    else:
        words = split_by_length_in_place(message.split(' '))
        logging.error("Error! Title divided length > 2")

    title_lines = []
    # Shouldn't need to worry about a word
    # longer than 21 for now since Silver/Blue/Orange 
    # is the max # of metro lines per alert assuming all lines
    # is all lines
    if title != '':
        divide_lines(title.split(' '), title_lines)

    lines = []
    divide_lines(words, lines)

    height_delta = 8

    logging.info("Drawing lines")

    for index, title_line in enumerate(title_lines):
        lines.insert(index, title_line)

    for i in range(0, len(lines), 4):
        if len(lines) - i < 4:
            lines_to_display = len(lines) - i
        else:
            lines_to_display = 4

        for x in range(0,lines_to_display):
            color = yellow_color
            if i+x <= len(title_lines)-1:
               color = red_color
            # graphics.DrawText(canvas, font, lines[i+x][1], 7 + x*height_delta, color, lines[i+x][0])
            graphics.DrawText(canvas, font, lines[i+x][1], 7 + x*height_delta, color, lines[i+x][0])
        time.sleep(5)
        canvas.Clear()


def draw_incident(canvas, font_file, message):
    logging.info("Got to draw incident")
    height_delta = 8
    width_delta = 6

    total_width = 128

    font = graphics.Font()
    font.LoadFont(font_file)
    red_color = graphics.Color(255,0,0)
    yellow_color = graphics.Color(200,125,0)
    green_color = graphics.Color(50,150,0)

    canvas.Clear()
    
    for y in range(0, 8):
        for x in range(0, 32):
            x0 = x * 4
            x1 = x0 + 3
            if x % 2 == 0 and y <= 3:
                graphics.DrawLine(canvas, x0, y, x1, y, yellow_color)
            elif x % 2 != 0 and y > 3:
                graphics.DrawLine(canvas, x0, y, x1, y, yellow_color)

    logging.info("Got past drawing squares")

    if "scheduled maintenance" in message or "scheduled track work" in message:
        graphics.DrawText(canvas, font, 1, 15, red_color, "SCHEDULED")
        graphics.DrawText(canvas, font, 1, 23, red_color, "TRACK WORK")
        logging.info("Drawing scheduled track workd")
    else:
        logging.info("Drawing service advisory")
        service = "SERVICE"
        advisory = "ADVISORY"
        graphics.DrawText(canvas, font, compute_offset(service), 15, red_color, service)
        graphics.DrawText(canvas, font, compute_offset(advisory), 23, red_color, advisory)

    for y in range(24, 32):
        for x in range(0, 32):
            x0 = x * 4
            x1 = x0 + 3
            if x % 2 == 0 and y <= 27:
                graphics.DrawLine(canvas, x0, y, x1, y, yellow_color)
            elif x % 2 != 0 and y > 27:
                graphics.DrawLine(canvas, x0, y, x1, y, yellow_color)

    logging.info("Got past drawing other squares")

    time.sleep(5)

    canvas.Clear()
    draw_message(canvas, message, font_file)