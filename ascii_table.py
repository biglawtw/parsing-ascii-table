import re
import sys
import itertools

__author__ = 'GCA'


# Date: 2015/10/27

def find_occurences(s, ch):
    return [i for i, letter in enumerate(s) if letter == ch]


def give_value_to_2d_map(dic, x, y, val):
    if x not in dic:
        dic[x] = {}
    dic[x][y] = val


# for constant variable

first_row_regexp = '^┌.*┐$'
last_row_regexp = '^└.*┘$'
first_row_intersect_symbol = '┬'
first_row_last_symbol = '┐'
separated_content_symbol = '│'
separated_line_started_symbol = '├'
separated_line_end_symbol = '┤'
separated_line_intersect_symbol = '┼'
vertical_sensitive_header_keywords = ["事實"]

file_name = input()

f = open(file_name, encoding='utf-8')
content = f.read().replace(" ", "")
contentList = content.split('\n')

separated_table = {}
line_break_table = {}
max_column = 0

# get the column count by table header

for ch in contentList[0]:
    if ch == first_row_intersect_symbol or ch == first_row_last_symbol:
        max_column += 1


# get the content of table and describe it in the position
'''
0123456789
┌───┬──┬─┐
│ABC│AC│D│
├───┼──┼─┤
│DDD│DD│D│
└───┴──┴─┘
separated_table is following
[4, 7, 9]
[4, 7, 9]
[4, 7, 9]
[-1, -1, -1]

line_break_table is following
[0, 0, 0]
[-1, -1, -1]
[0, 0, 0]
[-1, -1, -1]
'''

for line_index, line in enumerate(contentList):
    if re.match(first_row_regexp, line):
        continue
    if re.match(last_row_regexp, line):
        line_break_table[line_index] = [-1] * max_column
        separated_table[line_index] = [-1] * max_column
        continue
    separated = []
    line_break = []
    for i, letter in enumerate(line):
        if i == 0:
            continue
        if letter == separated_content_symbol or letter == separated_line_started_symbol:
            separated.append(i)
            line_break.append(0)
        if letter == separated_line_end_symbol:
            separated.append(i)
            line_break.append(-1)
        if letter == separated_line_intersect_symbol:
            separated.append(i)
            line_break.append(-1)
    # if it dont correspond the header of table
    if len(separated) > max_column:
        del separated[-1]
        del line_break[-1]

    separated_table[line_index] = separated
    line_break_table[line_index] = line_break

# compress the table
'''
[0, 0, 0]                       [0, 0, 0]
[-1, -1, -1]                    [-1, -1, -1]
[0, 0, 0]             ->        [0, 0, 0]
[0, 0, 0]                       [-1, -1, -1]
[0, 0, 0]
[-1, -1, -1]
'''
line_break_keys = list(line_break_table.keys())
compress_break_table = []
compress_normal_map = {}
normal_compress_map = {}
compress_is_line = []
for line_break_index, line_break_key in enumerate(line_break_keys):
    line_break = line_break_table[line_break_key]
    if line_break_index > 0:
        previous_line_break = line_break_table[line_break_keys[line_break_index - 1]]
        normal_compress_map[line_break_key] = len(compress_break_table) - 1
        if previous_line_break == line_break:
            continue
    compress_break_table.append(line_break)
    compress_normal_map[len(compress_break_table) - 1] = line_break_key
    normal_compress_map[line_break_key] = len(compress_break_table) - 1
    for line_break_cell in line_break:
        if line_break_cell == -1:
            compress_is_line.append(len(compress_break_table) - 1)
            break


# started to count row span in row and column in table,
block = {}
block_coord = {}
span_count_table = {}
for row_index, line_break in enumerate(compress_break_table):
    is_line = True if row_index in compress_is_line else False
    for index, num in enumerate(line_break):
        if row_index == 0:
            block_coord[index] = -1
            block[index] = 0
        if num == -1:
            give_value_to_2d_map(span_count_table, block_coord[index], index, block[index])
            block_coord[index] = -1
            block[index] = 0
        elif num == 0:
            if index not in block:
                # ascii table bug
                continue
            if not is_line:
                block[index] += 1
            if block_coord[index] == -1:
                block_coord[index] = row_index


# concat cell content if they are the same cell.
compress_content_list_table = {}
compress_content_table = {}
compress_width_count_table = {}
for line_index in separated_table:
    separated = separated_table[line_index]
    line_break = line_break_table[line_index]
    line_content = contentList[line_index]
    if line_index == 0:
        continue
    compress_line_index = normal_compress_map[line_index]
    if compress_line_index not in compress_content_table:
        compress_content_table[compress_line_index] = {}
    if compress_line_index not in compress_width_count_table:
        compress_width_count_table[compress_line_index] = {}
    if compress_line_index not in compress_content_list_table:
        compress_content_list_table[compress_line_index] = {}
    previous_pos = 0
    for index, pos in enumerate(separated):
        if line_break[index] != -1:
            if index not in compress_content_table[compress_line_index]:
                compress_content_table[compress_line_index][index] = ""
            if index not in compress_width_count_table[compress_line_index]:
                compress_width_count_table[compress_line_index][index] = 0
            if index not in compress_content_list_table[compress_line_index]:
                compress_content_list_table[compress_line_index][index] = []
            compress_content_table[compress_line_index][index] += line_content[previous_pos + 1:pos]
            compress_content_list_table[compress_line_index][index].append(line_content[previous_pos + 1:pos])
            compress_width_count_table[compress_line_index][index] = max(
                compress_width_count_table[compress_line_index][index], pos - previous_pos - 1)

        previous_pos = pos


# flag the keyword column for vertical text
vertical_column = []
for column_key in compress_content_table[0]:
    for keyword in vertical_sensitive_header_keywords:
        if keyword in compress_content_table[0][column_key]:
            vertical_column.append(column_key)

# combined all the cell content if then are merged cell.

compress_combined_table = {}
compress_content_table_keys = list(compress_content_table.keys())
for line_index, line in enumerate(compress_content_table):

    for column_index, column in enumerate(compress_content_table[line]):

        if line in span_count_table and column in span_count_table[line]:
            remain_line_count = span_count_table[line][column]
        else:
            remain_line_count = 0
        i = line_index + 1
        while i < line_index + remain_line_count:
            iterator_line_key = compress_content_table_keys[i]
            compress_content_table[line][column] += compress_content_table[iterator_line_key][column]
            compress_content_list_table[line][column] += compress_content_list_table[iterator_line_key][column]
            compress_content_table[iterator_line_key][column] = ""
            compress_content_list_table[iterator_line_key][column] = []
            give_value_to_2d_map(compress_combined_table, iterator_line_key, column, 1)
            if iterator_line_key in compress_is_line:
                remain_line_count += 1
            i += 1

# turn into vertical text
for line in compress_content_table:
    for column in vertical_column:
        if line not in compress_content_list_table or column not in compress_content_list_table[line]:
            continue

        origin_text = compress_content_list_table[line][column]
        vertical_list = list(map(list, (itertools.zip_longest(*origin_text))))
        vertical_list_content = [''.join(char for char in context if char) for context in vertical_list]
        vertical_list_content = ''.join(vertical_list_content)
        vertical_text = vertical_list_content
        compress_content_table[line][column] = vertical_text

header = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
table, th, td {
    border: 1px solid black;
}
</style>
</head>
<body>

<table>

"""

footer = """

</table>

</body>
</html>
"""
html_content = ""
for line in compress_content_table:

    tr_content = ""
    for column in compress_content_table[line]:
        if line in compress_combined_table and column in compress_combined_table[line]:
            continue
        row_span = 0
        tr_content += "  <td"
        if line in span_count_table and column in span_count_table[line]:
            row_span = span_count_table[line][column]
            if row_span > 1:
                tr_content += ' rowspan="' + str(row_span) + '">' + compress_content_table[line][column] + "</td>\n"
            else:
                tr_content += ">" + compress_content_table[line][column] + "</td>\n"
        else:
            tr_content += ">" + compress_content_table[line][column] + "</td>\n"
    if tr_content != "":
        html_content += "<tr>\n" + tr_content + "</tr>\n"

f = open('test_ascii_table.html', 'w', encoding='utf-8')
f.write(header + html_content + footer)
f.close()
