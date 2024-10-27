import re

##########################################################
#                 Uberort compiler v1.0.1                #
##########################################################
#New with v1.0.1:
#Expressions can now be written in multiple lines
#Minor bug fixes when calling functions
#Minor rework of with-as statements

file = 'input.txt'
commented_code = [i.strip() for i in open('input.txt').readlines()]
no_comment_code = [i[:i.index('#')] if '#' in i else i for i in commented_code]


functions = {'sqrt': 'R', 'gauss_pd':'R', 'gauss_cd':'R', 'sin':'R', 'cos':'R', 'tan':'R', 'asin':'R', 'acos':'R', 'atan':'R', 'atan2':'R'}

c_code = []
bonus_c_variables = {'___b_a':0, #bonus array
                     '___c_s':0, #comprehension superposition
                     '___c_h':0, #carray holder
                     '___p_s':0, #print_superposition
                     '___o_l':0, #one-liner variable
                     '___lbl':0, #label
                     '___s_p':0, #struct pointer
                     }
max_b_c_variables = {'___c_s':0, #comprehension superposition
                     '___c_i_s':0, #convert int into string
                     '___c_h':0, #carray holder
                     '___o_l':0, #one-liner variable
                     }
malloc_needs_free = []
malloc_indent = []


variables = {}
while_in_as = {}
looped_variables = []
where_loops = []
seq_loops = []
in_where = True
in_as = []
in_as_replace = {}
structs = {}
struct_original_order = {}
percent_print = {'Z':'%d', 'R':'%f'}
decomp_print = {'Z':lambda x: x, 'R':lambda x: x}
sequence_ind = {}
#in_where = False
indentation = 1
indentation_types = []
default_data_types = {'int':'int', 'int8':'int8_t', 'int16':'int16_t', 'int32':'int32_t', 'int64':'int64_t', 'uint8':'uint8_t', 'uint16':'uint16_t', 'uint32':'uint32_t', 'uint64':'uint64_t'}

datatype_to_quant = {'{Z}':'i', '{R}':'f', 'Z':'i', 'R':'f'}
datatype_to_c = {'Z':'int64_t', 'R':'double', '{Z}':'int64_t', '{R}':'double'}

#find the last instance of any of the targets
def find_last_char(expression, targets, excluding = ()):
    last_pos = 0
    inside = 0
    in_str = False
    next_ignore = False

    for i0 in range(len(expression)-1, -1, -1):
        i = expression[i0]
        if not in_str:
            if i in {'(', '[', '{'}:
                inside += 1
            elif i in {')', ']', '}'}:
                inside -= 1
            elif i == '"':
                in_str = True
                next_ignore = False
            elif (not (any(expression[i0-j0:i0-j0+len(target)] == target for target in excluding for j0 in range(len(target))))) and (any(expression[i0:i0+len(target)] == target for target in targets) and not inside):
                return [i0 + 1, next(target for target in targets if expression[i0:i0+len(target)] == target)]
        elif next_ignore:
            next_ignore = False
        else:
            if i == '"':
                in_str = False
            elif i == '\\':
                next_ignore = True

    return 0

#check if all parentheses are paired
def never_leaves(expression):
    last_pos = 0
    inside = 0
    in_str = False
    next_ignore = False

    for i0 in range(len(expression)-1, -1, -1):
        i = expression[i0]
        if not in_str:
            if i in {'(', '[', '{'}:
                inside += 1
                if inside > 0 and expression[:i0].strip():
                    return False
            elif i in {')', ']', '}'}:
                inside -= 1
            elif i == '"':
                in_str = True
                next_ignore = False
        elif next_ignore:
            next_ignore = False
        else:
            if i == '"':
                in_str = False
            elif i == '\\':
                next_ignore = True

    return True

#check if not in parentheses
def in_paranth(expression, start=0):
    last_pos = 0
    inside = start
    in_str = False
    next_ignore = False

    for i0 in range(len(expression)):
        i = expression[i0]
        if not in_str:
            if i in {'(', '[', '{'}:
                inside += 1
            elif i in {')', ']', '}'}:
                inside -= 1
            elif i == '"':
                in_str = True
                next_ignore = False
        elif next_ignore:
            next_ignore = False
        else:
            if i == '"':
                in_str = False
            elif i == '\\':
                next_ignore = True

    return inside

#cify values seperated by commas
def cify_attrs(expression, only_second_parts=False, inline_vars=False):
    global where_loops, indentation
    outp = []
    last_break = 0
    inside = 0
    in_str = False
    next_ignore = False

    for i0, i in enumerate(expression):
        if not in_str:
            if i in {'(', '[', '{'}:
                inside += 1
            elif i in {')', ']', '}'}:
                inside -= 1
            elif i == '"':
                in_str = True
                next_ignore = False
            elif i == ',' and inside == 0:
                bef_loop_s = len(c_code)
                starting_where_loops = len(where_loops)
                outp.append(cify(expression[last_break:i0], only_second_parts))
                if inline_vars:
                    variables[outp[-1][0][1]] = outp[-1][1][0]
                    c_code.insert(bef_loop_s, '\t' * indentation + f'{datatype_to_c[outp[-1][1][0]]} {outp[-1][0][1]};')
                    c_code.append('\t' * indentation + f'{outp[-1][0][1]} = {outp[-1][0][0]}; //inline variable')
                    #for i in where_loops[starting_where_loops:]:
                    #    indentation -= 1
                    #    c_code.append('\t' * indentation + '}')
                    #where_loops = where_loops[:starting_where_loops]
                last_break = i0 + 1
        elif next_ignore:
            next_ignore = False
        else:
            if i == '"':
                in_str = False
            elif i == '\\':
                next_ignore = True
    bef_loop_s = len(c_code)
    starting_where_loops = len(where_loops)
    outp.append(cify(expression[last_break:], only_second_parts))
    if inline_vars:
        #print(outp[-1][0][1], outp[-1][1][0])
        variables[outp[-1][0][1]] = outp[-1][1][0]
        c_code.insert(bef_loop_s, '\t' * indentation + f'{datatype_to_c[outp[-1][1][0]]} {outp[-1][0][1]};')
        c_code.append('\t' * indentation + f'{outp[-1][0][1]} = {outp[-1][0][0]};')
        #for i in where_loops[starting_where_loops:]:
        #    indentation -= 1
        #    c_code.append('\t' * indentation + '}')
        #where_loops = where_loops[:starting_where_loops]
    return outp

def decompose_type(expression):
    outp = []
    last_break = 0
    inside = -1
    in_str = False
    next_ignore = False
    for i0, i in enumerate(expression):
        if not in_str:
            if i in {'<'}:
                inside += 1
                if inside == 0:
                    last_break = i0 + 1
            elif i in {'>'}:
                inside -= 1
            elif i == '"':
                in_str = True
                next_ignore = False
            elif i == ',' and inside == 0:
                outp.append(expression[last_break:i0])
                last_break = i0 + 1
        elif next_ignore:
            next_ignore = False
        else:
            if i == '"':
                in_str = False
            elif i == '\\':
                next_ignore = True
    outp.append(expression[last_break:-1])
    return outp

#find the pair of the first parantheses, return before, inside and after parts
def find_pair(expression):
    outp = []
    last_break = 0
    inside = -1
    in_str = False
    next_ignore = False
    for i0, i in enumerate(expression):
        #print(i0, i, inside)
        if not in_str:
            if i in {'(', '[', '{'}:
                inside += 1
                if inside == 0:
                    last_break = i0+1
            elif i in {')', ']', '}'}:
                inside -= 1
                if inside == -1:
                    return [expression[:last_break-1], expression[last_break:i0], expression[i0+1:]]
            elif i == '"':
                in_str = True
                next_ignore = False
        elif next_ignore:
            next_ignore = False
        else:
            if i == '"':
                in_str = False
            elif i == '\\':
                next_ignore = True

#cify a given expression
def cify(expression, only_second_parts=False, direct_in_as=False):
    global in_where, where_loops, seq_loops, indentation
    #print(expression)
    expression = expression.strip()
    if expr := re.match(r'^\s*([\d_]+)\s*$', expression): #integer
        return [expr[1].replace('_', ''), 'Z']
    if expr := re.match(r'^\s*([\d_]+\.[\d_]+)\s*$', expression): #float
        return [expr[1].replace('_', ''), 'R']
    elif expr := re.match(r'^\s*(\'.*\')\s*$', expression): #character
        return [expr[1], 'char']
    elif expr := re.match(r'^\s*(\".*\")\s*$', expression): #string
        return [expr[1], 'str']
    elif expression in variables: #variable
        expression = in_as_replace[expression] if expression in in_as_replace else expression
        if expression in looped_variables or expression in where_loops:
            return [f'{expression}___l2', variables[expression][1:-1]]
        elif expression in seq_loops:
            return [f'{expression}___l2', variables[expression][:-1]]
        elif in_where and variables[expression].startswith('{'):
            where_loops.append(expression)
            c_code.append('\t' * indentation + f'for (int {expression}___l1 = 0; {expression}___l1 < {expression}->size; {expression}___l1++) ' + '{')
            indentation += 1
            c_code.append('\t' * indentation + f'{datatype_to_c[variables[expression]]} {expression}___l2 = universal_set[{expression}->elements[{expression}___l1]].element.{datatype_to_quant[variables[expression]]};')
            return [f'{expression}___l2', variables[expression][1:-1]]
        else:
            return [expression, variables[expression]]
    elif expression.endswith('}') and expression.startswith('{') and (splf := find_last_char(expression[1:-1], {' where '})) and never_leaves(expression[1:-1]): #superposition comprehension
        spl = splf[0]
        in_where = True
        starting_where_loops = len(where_loops)
        c_var_name = f'___c_h{bonus_c_variables["___c_h"]}'
        bonus_c_variables['___c_h'] += 1
        if direct_in_as:
            in_as_replace[iap:=in_as.pop()] = c_var_name
            variables[c_var_name] = variables[iap]
        c_code.append('\t' * indentation + f'dy_set_i* {c_var_name} = create_set_i();')
        if flc := find_last_char(expression[1:-1], {' with '}):
            cify(expression[flc[0]+1:-1])
        else:
            flc = [-1, 0]
        c_out = cify(expression[1:spl])
        c_con = cify(expression[spl+7:flc[0]])
        c_code.append('\t' * indentation + f'if ({c_con[0]}) ' + '{' + f'append_{datatype_to_quant[c_out[1]]}({c_var_name}, '+c_out[0]+');}')
        for i in where_loops[starting_where_loops:]:
            indentation -= 1
            c_code.append('\t' * indentation + '}')
        where_loops = where_loops[:starting_where_loops]
        if not direct_in_as:
            variables[c_var_name] = c_out[1]
        where_loops.append(c_var_name)
        c_code.append('\t' * indentation + f'for (int {c_var_name}___l1 = 0; {c_var_name}___l1 < {c_var_name}->size; {c_var_name}___l1++) ' + '{')
        indentation += 1
        c_code.append('\t' * indentation + f'{datatype_to_c[variables[c_var_name]]} {c_var_name}___l2 = universal_set[{c_var_name}->elements[{c_var_name}___l1]].element.{datatype_to_quant[variables[c_var_name]]};')
        return [f'{c_var_name}___l2', variables[c_var_name]]
    elif exprnot := re.match(r'^\s*(\w+)\s*\((.*)\)\s*$', expression) and not find_pair(expression)[2]:  #function call
        expr = [0] + find_pair(expression)
        fun = expr[1].strip()
        if fun in {'sum', 'max', 'range', 'random', 'randi', 'len', 'product', 'any', 'all', 'none', 'greater', 'first', 'smaller', 'mrange', 'average', 'gauss_random', 'abs', 'log'}:
            match fun:
                case 'sum':
                    bef_loop_s = len(c_code)
                    starting_where_loops = len(where_loops)
                    c_var_name = f'___o_l{bonus_c_variables["___o_l"]}'
                    bonus_c_variables['___o_l'] += 1
                    if (gennot := re.match(r'^\s*(.*)where(.*)\s*$', expr[2])) and (splf := find_last_char(expr[2], {' where '})) and never_leaves(expr[2]):  #generator
                        gen = [0, expr[2][:splf[0]], expr[2][splf[0]+6:]]
                        if flc := find_last_char(gen[2], {' with '}):
                            cify(gen[2][flc[0]:])
                            c_code.append('\t' * indentation + f'dy_set_i* {line[1].strip()} = create_set_i();')
                            gen_do = cify(gen[1])
                            gen_where = cify(gen[2][:flc[0]])
                        else:
                            flc = [-1, 0]
                            c_code.append('\t' * indentation + f'dy_set_i* {line[1].strip()} = create_set_i();')
                            gen_do = cify(gen[1])
                            gen_where = cify(gen[2])
                        c_code.append('\t' * indentation + f'if ({gen_where[0]}) '+'{'+f'{c_var_name} += {gen_do[0]}'+';} //sum')
                        for i in where_loops[starting_where_loops:]:
                            indentation -= 1
                            c_code.append('\t' * indentation + '}')
                        where_loops = where_loops[:starting_where_loops]
                        c_code.insert(bef_loop_s, '\t' * indentation + f'{datatype_to_c[gen_do[1]]} {c_var_name} = 0;')
                        return [f'{c_var_name}', gen_do[1]]
                    else:
                        attrs = cify_attrs(expr[2])[0]
                        c_code.append('\t' * indentation + f'{c_var_name} += {attrs[0]}; //sum')
                        for i in where_loops[starting_where_loops:]:
                            indentation -= 1
                            c_code.append('\t' * indentation + '}')
                        where_loops = where_loops[:starting_where_loops]
                        c_code.insert(bef_loop_s, '\t' * indentation + f'{datatype_to_c[attrs[1]]} {c_var_name} = 0;')
                        return [f'{c_var_name}', attrs[1]]
                case 'max':
                    bef_loop_s = len(c_code)
                    starting_where_loops = len(where_loops)
                    c_var_name = f'___o_l{bonus_c_variables["___o_l"]}'
                    bonus_c_variables['___o_l'] += 1
                    c_key_name = f'___o_l{bonus_c_variables["___o_l"]}'
                    bonus_c_variables['___o_l'] += 1
                    if ':' in expr[2]:
                        value = expr[2][:expr[2].index(':')]
                        key = expr[2][expr[2].index(':')+1:]
                        if (gennot := re.match(r'^\s*(.*)where(.*)\s*$', expr[2])) and (splf := find_last_char(expr[2], {' where '})) and never_leaves(expr[2]):  # generator
                            gen = [0, expr[2][:splf[0]], expr[2][splf[0] + 6:]]
                            #gen_do = cify_attrs(gen[1])[0]
                            #gen_where = cify_attrs(gen[2])[0]
                            if flc := find_last_char(gen[2], {' with '}):
                                cify(gen[2][flc[0]:])
                                c_code.append('\t' * indentation + f'dy_set_i* {line[1].strip()} = create_set_i();')
                                gen_do = cify(gen[1])
                                gen_where = cify(gen[2][:flc[0]])
                            else:
                                flc = [-1, 0]
                                c_code.append('\t' * indentation + f'dy_set_i* {line[1].strip()} = create_set_i();')
                                gen_do = cify(gen[1])
                                gen_where = cify(gen[2])
                            key = cify(key)
                            c_code.append('\t' * indentation + f'if ({gen_where[0]} && ({c_key_name} < {key[0]})) ' + '{' + f'{c_var_name} = {gen_do[0]}; {c_key_name} = {key[0]};' + '} //max')
                            for i in where_loops[starting_where_loops:]:
                                indentation -= 1
                                c_code.append('\t' * indentation + '}')
                            where_loops = where_loops[:starting_where_loops]
                            c_code.insert(bef_loop_s, '\t' * indentation + f'{datatype_to_c[gen_do[1]]} {c_var_name} = 0;')
                            c_code.insert(bef_loop_s, '\t' * indentation + f'{datatype_to_c[key[1]]} {c_key_name} = 0;')
                            return [f'{c_var_name}', gen_do[1]]
                        else:
                            attrs = cify_attrs(value)[0]
                            key = cify(key)
                            # bonus_c_variables['___o_l'] -= 1
                            c_code.append('\t' * indentation + f'if ({c_key_name} < {key[0]}) ' + '{' + f'{c_var_name} = {attrs[0]}; {c_key_name} = {key[0]};' + '} //max')
                            for i in where_loops[starting_where_loops:]:
                                indentation -= 1
                                c_code.append('\t' * indentation + '}')
                            where_loops = where_loops[:starting_where_loops]
                            c_code.insert(bef_loop_s, '\t' * indentation + f'{datatype_to_c[attrs[1]]} {c_var_name} = 0;')
                            c_code.insert(bef_loop_s, '\t' * indentation + f'{datatype_to_c[key[1]]} {c_key_name} = 0;')
                            return [f'{c_var_name}', attrs[1]]
                    else:
                        value = expr[2]
                        if (gennot := re.match(r'^\s*(.*)where(.*)\s*$', expr[2])) and (splf := find_last_char(expr[2], {' where '})) and never_leaves(expr[2]):  # generator
                            gen = [0, expr[2][:splf[0]], expr[2][splf[0] + 6:]]
                            #gen_do = cify_attrs(gen[1])[0]
                            #gen_where = cify_attrs(gen[2])[0]
                            if flc := find_last_char(gen[2], {' with '}):
                                cify(gen[2][flc[0]:])
                                c_code.append('\t' * indentation + f'dy_set_i* {line[1].strip()} = create_set_i();')
                                gen_do = cify(gen[1])
                                gen_where = cify(gen[2][:flc[0]])
                            else:
                                flc = [-1, 0]
                                c_code.append('\t' * indentation + f'dy_set_i* {line[1].strip()} = create_set_i();')
                                gen_do = cify(gen[1])
                                gen_where = cify(gen[2])
                            c_code.append('\t' * indentation + f'if ({gen_where[0]} && ({c_key_name} < {gen_do[0]})) ' + '{' + f'{c_var_name} = {gen_do[0]}; {c_key_name} = {gen_do[0]};' + '} //max - key')
                            for i in where_loops[starting_where_loops:]:
                                indentation -= 1
                                c_code.append('\t' * indentation + '}')
                            where_loops = where_loops[:starting_where_loops]
                            c_code.insert(bef_loop_s, '\t' * indentation + f'{datatype_to_c[gen_do[1]]} {c_var_name} = 0;')
                            c_code.insert(bef_loop_s, '\t' * indentation + f'{datatype_to_c[gen_do[1]]} {c_key_name} = 0;')
                            return [f'{c_var_name}', gen_do[1]]
                        else:
                            attrs = cify_attrs(value)[0]
                            key = cify(value)
                            # bonus_c_variables['___o_l'] -= 1
                            c_code.append('\t' * indentation + f'if ({c_key_name} < {key[0]}) ' + '{' + f'{c_var_name} = {attrs[0]}; {c_key_name} = {key[0]};' + '} //max - key')
                            for i in where_loops[starting_where_loops:]:
                                indentation -= 1
                                c_code.append('\t' * indentation + '}')
                            where_loops = where_loops[:starting_where_loops]
                            c_code.insert(bef_loop_s, '\t' * indentation + f'{datatype_to_c[attrs[1]]} {c_var_name} = 0;')
                            c_code.insert(bef_loop_s, '\t' * indentation + f'{datatype_to_c[key[1]]} {c_key_name} = 0;')
                            return [f'{c_var_name}', attrs[1]]
                case 'range': #range comprehension
                    sp_name = f'___c_s_{bonus_c_variables["___c_s"]}'
                    bonus_c_variables['___c_s'] += 1
                    c_code.append('\t' * indentation + f'for (int {sp_name}___l2 = 0; {sp_name}___l2 < {cify(expr[2])[0]}; {sp_name}___l2++)' + '{ //range')
                    variables[sp_name] = '{Z}'
                    where_loops.append(sp_name)
                    indentation += 1
                    return [f'{sp_name}___l2', 'Z']
                case 'mrange':  # range comprehension
                    sp_name = f'___c_s_{bonus_c_variables["___c_s"]}'
                    bonus_c_variables['___c_s'] += 1
                    c_code.append('\t' * indentation + f'for (int {sp_name}___l2 = 1; {sp_name}___l2 <= {cify(expr[2])[0]}; {sp_name}___l2++)' + '{ //mrange')
                    variables[sp_name] = '{Z}'
                    where_loops.append(sp_name)
                    indentation += 1
                    return [f'{sp_name}___l2', 'Z']
                case 'random':  #random comprehension
                    sp_name = f'___c_s_{bonus_c_variables["___c_s"]}'
                    bonus_c_variables['___c_s'] += 1
                    rn_name = f'___c_s_{bonus_c_variables["___c_s"]}'
                    bonus_c_variables['___c_s'] += 1
                    attrs = cify_attrs(expr[2])
                    if len(attrs) == 3:
                        c_code.append('\t' * indentation + f'for (int {sp_name} = 0; {sp_name} < {attrs[2][0]}; {sp_name}++)' + '{')
                        indentation += 1
                        c_code.append('\t' * indentation + f'double {rn_name}___l2 = (({attrs[1][0]} - {attrs[0][0]}) * ((float)rand() / RAND_MAX)) + {attrs[0][0]}; //random')
                        variables[sp_name] = '{R}'
                        where_loops.append(sp_name)
                        return [f'{rn_name}___l2', 'R']
                    else:
                        return [f'((({attrs[1][0]} - {attrs[0][0]}) * ((float)rand() / RAND_MAX)) + {attrs[0][0]})', 'R']
                case 'randi':  # randi comprehension
                    sp_name = f'___c_s_{bonus_c_variables["___c_s"]}'
                    bonus_c_variables['___c_s'] += 1
                    rn_name = f'___c_s_{bonus_c_variables["___c_s"]}'
                    bonus_c_variables['___c_s'] += 1
                    attrs = cify_attrs(expr[2])
                    if len(attrs) == 2:
                        c_code.append('\t' * indentation + f'for (int {sp_name} = 0; {sp_name} < {attrs[1][0]}; {sp_name}++)' + '{')
                        indentation += 1
                        c_code.append('\t' * indentation + f'int64_t {rn_name}___l2 = rand() % ({attrs[0][0]});')
                        variables[sp_name] = '{Z}'
                        where_loops.append(sp_name)
                        return [f'{rn_name}___l2', 'Z']
                    else:
                        return [f'(rand() % ({attrs[0][0]}))', 'Z']
                case 'len':
                    bef_loop_s = len(c_code)
                    starting_where_loops = len(where_loops)
                    c_var_name = f'___o_l{bonus_c_variables["___o_l"]}'
                    bonus_c_variables['___o_l'] += 1
                    if (gennot := re.match(r'^\s*(.*)where(.*)\s*$', expr[2])) and (splf := find_last_char(expr[2], {' where '})) and never_leaves(expr[2]):  #generator
                        gen = [0, expr[2][:splf[0]], expr[2][splf[0]+6:]]
                        #gen_do = cify_attrs(gen[1])[0]
                        #gen_where = cify_attrs(gen[2])[0]
                        if flc := find_last_char(gen[2], {' with '}):
                            cify(gen[2][flc[0]:])
                            c_code.append('\t' * indentation + f'dy_set_i* {line[1].strip()} = create_set_i();')
                            gen_do = cify(gen[1])
                            gen_where = cify(gen[2][:flc[0]])
                        else:
                            flc = [-1, 0]
                            c_code.append('\t' * indentation + f'dy_set_i* {line[1].strip()} = create_set_i();')
                            gen_do = cify(gen[1])
                            gen_where = cify(gen[2])
                        c_code.append('\t' * indentation + f'if ({gen_where[0]}) ' + '{' + f'{c_var_name}++' + '; //len}')
                        for i in where_loops[starting_where_loops:]:
                            indentation -= 1
                            c_code.append('\t' * indentation + '}')
                        where_loops = where_loops[:starting_where_loops]
                        c_code.insert(bef_loop_s, '\t' * indentation + f'{datatype_to_c[gen_do[1]]} {c_var_name} = 0;')
                        return [f'{c_var_name}', gen_do[1]]
                    else:
                        attrs = cify_attrs(expr[2])[0]
                        # bonus_c_variables['___o_l'] -= 1
                        c_code.append('\t' * indentation + f'{c_var_name}++; //len')
                        for i in where_loops[starting_where_loops:]:
                            indentation -= 1
                            c_code.append('\t' * indentation + '}')
                        where_loops = where_loops[:starting_where_loops]
                        c_code.insert(bef_loop_s, '\t' * indentation + f'{datatype_to_c[attrs[1]]} {c_var_name} = 0;')
                        return [f'{c_var_name}', attrs[1]]
                case 'product':
                    bef_loop_s = len(c_code)
                    starting_where_loops = len(where_loops)
                    c_var_name = f'___o_l{bonus_c_variables["___o_l"]}'
                    bonus_c_variables['___o_l'] += 1
                    if (gennot := re.match(r'^\s*(.*)where(.*)\s*$', expr[2])) and (splf := find_last_char(expr[2], {' where '})) and never_leaves(expr[2]):  #generator
                        gen = [0, expr[2][:splf[0]], expr[2][splf[0]+6:]]
                        #gen_do = cify_attrs(gen[1])[0]
                        #gen_where = cify_attrs(gen[2])[0]
                        #gen = [0, expr[2][:oflc[0]], expr[2][oflc[0]+6:]]
                        if flc := find_last_char(gen[2], {' with '}):
                            cify(gen[2][flc[0]:])
                            c_code.append('\t' * indentation + f'dy_set_i* {line[1].strip()} = create_set_i();')
                            gen_do = cify(gen[1])
                            gen_where = cify(gen[2][:flc[0]])
                        else:
                            flc = [-1, 0]
                            c_code.append('\t' * indentation + f'dy_set_i* {line[1].strip()} = create_set_i();')
                            gen_do = cify(gen[1])
                            gen_where = cify(gen[2])
                        c_code.append('\t' * indentation + f'if ({gen_where[0]}) ' + '{' + f'{c_var_name} *= {gen_do[0]}' + ';} //product')
                        for i in where_loops[starting_where_loops:]:
                            indentation -= 1
                            c_code.append('\t' * indentation + '}')
                        where_loops = where_loops[:starting_where_loops]
                        c_code.insert(bef_loop_s, '\t' * indentation + f'{datatype_to_c[gen_do[1]]} {c_var_name} = 1;')
                        return [f'{c_var_name}', gen_do[1]]
                    else:
                        attrs = cify_attrs(expr[2])[0]
                        # bonus_c_variables['___o_l'] -= 1
                        c_code.append('\t' * indentation + f'{c_var_name} *= {attrs[0]}; //product')
                        for i in where_loops[starting_where_loops:]:
                            indentation -= 1
                            c_code.append('\t' * indentation + '}')
                        where_loops = where_loops[:starting_where_loops]
                        c_code.insert(bef_loop_s, '\t' * indentation + f'{datatype_to_c[attrs[1]]} {c_var_name} = 1;')
                        return [f'{c_var_name}', attrs[1]]
                case 'any':
                    bef_loop_s = len(c_code)
                    starting_where_loops = len(where_loops)
                    c_var_name = f'___o_l{bonus_c_variables["___o_l"]}'
                    bonus_c_variables['___o_l'] += 1
                    if (gennot := re.match(r'^\s*(.*)where(.*)\s*$', expr[2])) and (splf := find_last_char(expr[2], {' where '})) and never_leaves(expr[2]):  #generator
                        gen = [0, expr[2][:splf[0]], expr[2][splf[0]+6:]]
                        #gen_do = cify_attrs(gen[1])[0]
                        #gen_where = cify_attrs(gen[2])[0]
                        if flc := find_last_char(gen[2], {' with '}):
                            cify(gen[2][flc[0]:])
                            c_code.append('\t' * indentation + f'dy_set_i* {line[1].strip()} = create_set_i();')
                            gen_do = cify(gen[1])
                            gen_where = cify(gen[2][:flc[0]])
                        else:
                            flc = [-1, 0]
                            c_code.append('\t' * indentation + f'dy_set_i* {line[1].strip()} = create_set_i();')
                            gen_do = cify(gen[1])
                            gen_where = cify(gen[2])
                        label_name = f'___lbl{bonus_c_variables["___lbl"]}'
                        bonus_c_variables["___lbl"] += 1
                        c_code.append('\t' * indentation + f'if ({gen_where[0]} && {gen_do[0]}) ' + '{' + f'{c_var_name} = 1; goto {label_name};'+'} //any')
                        for i in where_loops[starting_where_loops:]:
                            indentation -= 1
                            c_code.append('\t' * indentation + '}')
                        c_code.append(f'{label_name}:')
                        where_loops = where_loops[:starting_where_loops]
                        c_code.insert(bef_loop_s, '\t' * indentation + f'{datatype_to_c[gen_do[1]]} {c_var_name} = 0;')
                        return [f'{c_var_name}', 'Z']
                    else:
                        attrs = cify_attrs(expr[2])[0]
                        # bonus_c_variables['___o_l'] -= 1
                        label_name = f'___lbl{bonus_c_variables["___lbl"]}'
                        bonus_c_variables["___lbl"] += 1
                        c_code.append('\t' * indentation + f'if ({attrs[0]}) ' + '{' + f'{c_var_name} = 1; goto {label_name};'+'} //any')
                        for i in where_loops[starting_where_loops:]:
                            indentation -= 1
                            c_code.append('\t' * indentation + '}')
                        c_code.append(f'{label_name}:')
                        where_loops = where_loops[:starting_where_loops]
                        c_code.insert(bef_loop_s, '\t' * indentation + f'{datatype_to_c[attrs[1]]} {c_var_name} = 0;')
                        return [f'{c_var_name}', 'Z']
                case 'none':
                    bef_loop_s = len(c_code)
                    starting_where_loops = len(where_loops)
                    c_var_name = f'___o_l{bonus_c_variables["___o_l"]}'
                    bonus_c_variables['___o_l'] += 1
                    if (gennot := re.match(r'^\s*(.*)where(.*)\s*$', expr[2])) and (splf := find_last_char(expr[2], {' where '})) and never_leaves(expr[2]):  #generator
                        gen = [0, expr[2][:splf[0]], expr[2][splf[0]+6:]]
                        #gen_do = cify_attrs(gen[1])[0]
                        #gen_where = cify_attrs(gen[2])[0]
                        if flc := find_last_char(gen[2], {' with '}):
                            cify(gen[2][flc[0]:])
                            c_code.append('\t' * indentation + f'dy_set_i* {line[1].strip()} = create_set_i();')
                            gen_do = cify(gen[1])
                            gen_where = cify(gen[2][:flc[0]])
                        else:
                            flc = [-1, 0]
                            c_code.append('\t' * indentation + f'dy_set_i* {line[1].strip()} = create_set_i();')
                            gen_do = cify(gen[1])
                            gen_where = cify(gen[2])
                        label_name = f'___lbl{bonus_c_variables["___lbl"]}'
                        bonus_c_variables["___lbl"] += 1
                        c_code.append('\t' * indentation + f'if ({gen_where[0]} && {gen_do[0]}) ' + '{' + f'{c_var_name} = 0; goto {label_name};' + '} //none')
                        for i in where_loops[starting_where_loops:]:
                            indentation -= 1
                            c_code.append('\t' * indentation + '}')
                        c_code.append(f'{label_name}:')
                        where_loops = where_loops[:starting_where_loops]
                        c_code.insert(bef_loop_s, '\t' * indentation + f'{datatype_to_c[gen_do[1]]} {c_var_name} = 1;')
                        return [f'{c_var_name}', 'Z']
                    else:
                        attrs = cify_attrs(expr[2])[0]
                        # bonus_c_variables['___o_l'] -= 1
                        label_name = f'___lbl{bonus_c_variables["___lbl"]}'
                        bonus_c_variables["___lbl"] += 1
                        c_code.append('\t' * indentation + f'if ({attrs[0]}) ' + '{' + f'{c_var_name} = 0; goto {label_name};' + '} //none')
                        for i in where_loops[starting_where_loops:]:
                            indentation -= 1
                            c_code.append('\t' * indentation + '}')
                        c_code.append(f'{label_name}:')
                        where_loops = where_loops[:starting_where_loops]
                        c_code.insert(bef_loop_s, '\t' * indentation + f'{datatype_to_c[attrs[1]]} {c_var_name} = 1;')
                        return [f'{c_var_name}', 'Z']
                case 'all':
                    bef_loop_s = len(c_code)
                    starting_where_loops = len(where_loops)
                    c_var_name = f'___o_l{bonus_c_variables["___o_l"]}'
                    bonus_c_variables['___o_l'] += 1
                    if (gennot := re.match(r'^\s*(.*)where(.*)\s*$', expr[2])) and (splf := find_last_char(expr[2], {' where '})) and never_leaves(expr[2]):  #generator
                        gen = [0, expr[2][:splf[0]], expr[2][splf[0]+6:]]
                        #gen_do = cify_attrs(gen[1])[0]
                        #gen_where = cify_attrs(gen[2])[0]
                        if flc := find_last_char(gen[2], {' with '}):
                            cify(gen[2][flc[0]:])
                            c_code.append('\t' * indentation + f'dy_set_i* {line[1].strip()} = create_set_i();')
                            gen_do = cify(gen[1])
                            gen_where = cify(gen[2][:flc[0]])
                        else:
                            flc = [-1, 0]
                            c_code.append('\t' * indentation + f'dy_set_i* {line[1].strip()} = create_set_i();')
                            gen_do = cify(gen[1])
                            gen_where = cify(gen[2])
                        label_name = f'___lbl{bonus_c_variables["___lbl"]}'
                        bonus_c_variables["___lbl"] += 1
                        c_code.append('\t' * indentation + f'if (!({gen_where[0]} && {gen_do[0]})) ' + '{' + f'{c_var_name} = 0; goto {label_name};' + '} //all')
                        for i in where_loops[starting_where_loops:]:
                            indentation -= 1
                            c_code.append('\t' * indentation + '}')
                        c_code.append(f'{label_name}:')
                        where_loops = where_loops[:starting_where_loops]
                        c_code.insert(bef_loop_s, '\t' * indentation + f'{datatype_to_c[gen_do[1]]} {c_var_name} = 1;')
                        return [f'{c_var_name}', 'Z']
                    else:
                        attrs = cify_attrs(expr[2])[0]
                        # bonus_c_variables['___o_l'] -= 1
                        label_name = f'___lbl{bonus_c_variables["___lbl"]}'
                        bonus_c_variables["___lbl"] += 1
                        c_code.append('\t' * indentation + f'if (!({attrs[0]})) ' + '{' + f'{c_var_name} = 0; goto {label_name};' + '} //all')
                        for i in where_loops[starting_where_loops:]:
                            indentation -= 1
                            c_code.append('\t' * indentation + '}')
                        c_code.append(f'{label_name}:')
                        where_loops = where_loops[:starting_where_loops]
                        c_code.insert(bef_loop_s, '\t' * indentation + f'{datatype_to_c[attrs[1]]} {c_var_name} = 1;')
                        return [f'{c_var_name}', 'Z']
                case 'greater':
                    attrs = cify_attrs(expr[2])
                    return [f'({attrs[0][0]} > {attrs[1][0]} ? {attrs[0][0]} : {attrs[1][0]})', attrs[0][1]]
                case 'smaller':
                    attrs = cify_attrs(expr[2])
                    return [f'({attrs[0][0]} < {attrs[1][0]} ? {attrs[0][0]} : {attrs[1][0]})', attrs[0][1]]
                case 'first':
                    bef_loop_s = len(c_code)
                    starting_where_loops = len(where_loops)
                    if ':' in expr[2]:
                        value = expr[2][:expr[2].index(':')]
                        if ' in ' not in value:
                            c_var_name = f'{value}___l2'
                            #c_out_name = f'{value}___l3'
                            seq_loops.append(value)
                            c_code.append('\t' * indentation + f'for (int {c_var_name}___l1 = 0; 1; {c_var_name}___l1++) ' + '{')
                            indentation += 1
                            c_code.append('\t' * indentation + f'{c_var_name} = {value}({c_var_name}___l1, {sequence_ind[value]});')
                            key = expr[2][expr[2].index(':') + 1:]
                            attrs = cify_attrs(value)[0]
                            key = cify(key)
                            # bonus_c_variables['___o_l'] -= 1
                            label_name = f'___lbl{bonus_c_variables["___lbl"]}'
                            bonus_c_variables["___lbl"] += 1
                            #c_code.append('\t' * indentation + f'if ({key[0]}) ' + '{' + f'{c_out_name} = {attrs[0]}; goto {label_name};' + '}')
                            c_code.append('\t' * indentation + f'if ({key[0]}) goto {label_name}; //first')
                            for i in where_loops[starting_where_loops:]:
                                indentation -= 1
                                c_code.append('\t' * indentation + '}')
                            where_loops = where_loops[:starting_where_loops]
                            c_code.insert(bef_loop_s, '\t' * indentation + f'{datatype_to_c[attrs[1]]} {c_var_name} = 0;')
                            #c_code.insert(bef_loop_s, '\t' * indentation + f'{datatype_to_c[key[1]]} {c_out_name} = 0;')
                            seq_loops.pop()
                            indentation -= 1
                            c_code.append('\t' * indentation + '}')
                            c_code.append(f'{label_name}:')
                            #c_code.insert(bef_loop_s, '\t' * indentation + f'{datatype_to_c[key[1]]} {c_key_name} = 0;')
                            return [f'{c_var_name}', attrs[1]]
                        elif value.split('in')[1].strip() == 'N':
                            variables[value.split('in')[0].strip()] = 'Z'
                            c_var_name = f'{value.split("in")[0].strip()}'
                            c_code.append('\t' * indentation + f'for ({c_var_name} = 0; 1; {c_var_name}++) ' + '{')
                            indentation += 1
                            key = expr[2][expr[2].index(':') + 1:]
                            attrs = cify_attrs(value)[0]
                            key = cify(key)
                            label_name = f'___lbl{bonus_c_variables["___lbl"]}'
                            bonus_c_variables["___lbl"] += 1
                            c_code.append('\t' * indentation + f'if ({key[0]}) goto {label_name}; //first')
                            for i in where_loops[starting_where_loops:]:
                                indentation -= 1
                                c_code.append('\t' * indentation + '}')
                            where_loops = where_loops[:starting_where_loops]
                            c_code.insert(bef_loop_s, '\t' * indentation + f'int64_t {c_var_name} = 0;')
                            indentation -= 1
                            c_code.append('\t' * indentation + '}')
                            c_code.append(f'{label_name}:')
                            return [c_var_name, 'Z']
                case 'average':
                    bef_loop_s = len(c_code)
                    starting_where_loops = len(where_loops)
                    c_var_name = f'___o_l{bonus_c_variables["___o_l"]}'
                    c_count_name = f'___o_l{bonus_c_variables["___o_l"]}_counter'
                    bonus_c_variables['___o_l'] += 1
                    if (gennot := re.match(r'^\s*(.*)where(.*)\s*$', expr[2])) and (splf := find_last_char(expr[2], {' where '})) and never_leaves(expr[2]):  #generator
                        gen = [0, expr[2][:splf[0]], expr[2][splf[0]+6:]]
                        #gen_do = cify_attrs(gen[1])[0]
                        #gen_where = cify_attrs(gen[2])[0]
                        if flc := find_last_char(gen[2], {' with '}):
                            cify(gen[2][flc[0]:])
                            c_code.append('\t' * indentation + f'dy_set_i* {line[1].strip()} = create_set_i();')
                            gen_do = cify(gen[1])
                            gen_where = cify(gen[2][:flc[0]])
                        else:
                            flc = [-1, 0]
                            c_code.append('\t' * indentation + f'dy_set_i* {line[1].strip()} = create_set_i();')
                            gen_do = cify(gen[1])
                            gen_where = cify(gen[2])
                        c_code.append('\t' * indentation + f'if ({gen_where[0]}) ' + '{' + f'{c_var_name} += {gen_do[0]}; {c_count_name}++' + ';} //average')
                        for i in where_loops[starting_where_loops:]:
                            indentation -= 1
                            c_code.append('\t' * indentation + '}')
                        where_loops = where_loops[:starting_where_loops]
                        c_code.insert(bef_loop_s, '\t' * indentation + f'{datatype_to_c[gen_do[1]]} {c_var_name} = 0;')
                        c_code.insert(bef_loop_s, '\t' * indentation + f'int {c_count_name} = 0;')
                        return [f'((float) {c_var_name} / {c_count_name})', 'R']
                    else:
                        attrs = cify_attrs(expr[2])[0]
                        # bonus_c_variables['___o_l'] -= 1
                        c_code.append('\t' * indentation + f'{c_var_name} += {attrs[0]}; {c_count_name}++; //average')
                        for i in where_loops[starting_where_loops:]:
                            indentation -= 1
                            c_code.append('\t' * indentation + '}')
                        where_loops = where_loops[:starting_where_loops]
                        c_code.insert(bef_loop_s, '\t' * indentation + f'{datatype_to_c[attrs[1]]} {c_var_name} = 0;')
                        c_code.insert(bef_loop_s, '\t' * indentation + f'int {c_count_name} = 0;')
                        return [f'(float) {c_var_name} / {c_count_name}', 'R']
                case 'gauss_random':  #gauss random comprehension
                    sp_name = f'___c_s_{bonus_c_variables["___c_s"]}'
                    bonus_c_variables['___c_s'] += 1
                    rn_name = f'___c_s_{bonus_c_variables["___c_s"]}'
                    bonus_c_variables['___c_s'] += 1
                    if expr[2].strip():
                        attrs = cify(expr[2])
                        c_code.append('\t' * indentation + f'for (int {sp_name} = 0; {sp_name} < {attrs[0]}; {sp_name}++)' + '{')
                        indentation += 1
                        c_code.append('\t' * indentation + f'double {rn_name}___l2 = gauss_random();')
                        variables[sp_name] = '{R}'
                        where_loops.append(sp_name)
                        return [f'{rn_name}___l2', 'R']
                    else:
                        return ['gauss_random()', 'R']
                case 'abs':
                    attr = cify(expr[2])
                    return [f'fabs({attr[0]})', 'R'] if attr[1] == 'R' else [f'abs({attr[0]})', 'Z']
                case 'log':
                    attrs = cify_attrs(expr[2])
                    if len(attrs) == 2:
                        return [f'log({attrs[1][0]}) / log({attrs[0][0]})', 'R']
                    else:
                        return [f'log({attrs[0][0]})', 'R']
        elif fun in structs: #struct
            bcv = f'___s_p{bonus_c_variables["___s_p"]}'
            bonus_c_variables["___s_p"] += 1
            c_code.append('\t'*indentation + f'{fun} ___s_p{bcv} = '+'{'+f'{", ".join(f".{i[0][0]} = {i[0][1]}" for i in cify_attrs(expr[2], True))}'+'};')
            c_code.append('\t'*indentation + f'{fun}* ___s_p{bcv}_1 = malloc(sizeof({fun}));')
            c_code.append('\t'*indentation + f'memcpy(___s_p{bcv}_1, &___s_p{bcv}, sizeof({fun}));')
            return [f'___s_p{bcv}_1', fun]
            #return [f'&___s_p{bcv}', fun]
        elif fun in functions:
            starting_where_loops = len(where_loops)
            attrs = cify_attrs(expr[2])
            #if len(where_loops) == starting_where_loops:
            return [f'{fun}({", ".join(i[0] for i in attrs)})', functions[fun]]
            #else:
            #    for i in where_loops[starting_where_loops:]:
            #        indentation -= 1
            #        c_code.append('\t' * indentation + '}')
            #    where_loops = where_loops[:starting_where_loops]
            #    return [f'{fun}({", ".join(i[0] for i in attrs)})', '{'+functions[fun]+'}']
    elif expression.startswith('with '): #inline variable
        pairs = cify_attrs(expression[5:], inline_vars = True)
        return 0
    elif lc1 := find_last_char(expression, {' with '}): #inline variable
        cify(expression[lc1[0]:])
        return cify(expression[:lc1[0]])
    elif expr := re.match(r'^\s*(.+)\?(.+):(.+)\s*$', expression):  #ternary
        lc1 = find_last_char(expression, {'?'})
        lc2 = find_last_char(expression, {':'})
        return [f'({(a := cify(expression[:lc1[0] - 1]))[0]} ? {(b := cify(expression[lc1[0]:lc2[0]-1]))[0]} : {(c := cify(expression[lc2[0]:]))[0]})', b[1]]
    elif lc1 := find_last_char(expression, {':'}): #pair
        if only_second_parts:
            return [[expression[:lc1[0] - 1], f'{(b := cify(expression[lc1[0]:]))[0]}'], [b[1]]]
        else:
            return [[f'{(a := cify(expression[:lc1[0] - 1]))[0]}', f'{(b := cify(expression[lc1[0]:]))[0]}'], [a[1], b[1]]]
    elif lc1 := find_last_char(expression, {' as '}): #with as pair inline variable
        if ' in ' in expression[lc1[0]:]:
            starting_where_loops = len(where_loops)
            var_name = expression[lc1[0]:][3:expression[lc1[0]:].index(' in ')].strip()
            variables[var_name] = expression[lc1[0]:][expression[lc1[0]:].index(' in ')+4:].strip()
            #print(variables)
            #c_code.append('\t'*indentation + f'{datatype_to_c}')
            in_as.append(var_name)
            #for i in where_loops[starting_where_loops:]:
            #    indentation -= 1
            #    c_code.append('\t' * indentation + '}')
            #where_loops = where_loops[:starting_where_loops]
            where_loops = where_loops[:starting_where_loops] + ['' for i in where_loops[starting_where_loops:]]
            return [[f'{(b := cify(expression[:lc1[0]], direct_in_as=True))[0]}', var_name], [b[1]]]
        else:
            starting_where_loops = len(where_loops)
            var_name = expression[lc1[0]+3:].strip()
            b = cify(expression[:lc1[0]], direct_in_as=True)
            variables[var_name] = b[1]
            #print(variables)
            in_as.append(var_name)
            #for i in where_loops[starting_where_loops:]:
            #    indentation -= 1
            #    c_code.append('\t' * indentation + '}')
            #where_loops = where_loops[:starting_where_loops]
            where_loops = where_loops[:starting_where_loops] + ['' for i in where_loops[starting_where_loops:]]
            return [[f'{(b)[0]}', var_name], [b[1]]]
    elif lc1 := find_last_char(expression, {' in '}): #of type
        return [expression[:lc1[0]].strip(), expression[lc1[0]+3:].strip()]
    elif lc := find_last_char(expression, {'&&', '||'}):
        return [f'({cify(expression[:lc[0]-len(lc[1])])[0]} {lc[1]} {cify(expression[lc[0]+1:])[0]})', 'Z']
    elif expr := re.match(r'^\s*!(.*)\s*$', expression):  #not
        return [f'(!{cify(expr[1])[0]})', 'Z']
    elif lc := find_last_char(expression, {'==', '<', '>', '<=', '=>', '!='}):
        #t, pos = min(([i, find_char(expression, i)] for i in ('==', '<', '>', '<=', '>=', '!=') if find_char(expression, i) != 0), key=lambda x:x[1])
        #pos -= 1
        return [f'({cify(expression[:lc[0]-len(lc[1])])[0]} {lc[1]} {cify(expression[lc[0]+1:])[0]})', 'Z']
    elif (lc := find_last_char(expression, {'+', '-'})) and not (re.match(r'^\s*-(.*)\s*$', expression)):
        return [f'({(a:=cify(expression[:lc[0]-1]))[0]} {lc[1]} {(b:=cify(expression[lc[0]:]))[0]})', 'R' if 'R' in (a[1], b[1]) else 'Z']
    elif lc := find_last_char(expression, {'*', '/', '//', '%', '!%'}, excluding={'**'}):
        if lc[1] == '!%' or (lc[1] == '%' and (flc := find_last_char(expression, {'!%'})) and flc[0] + 1 == lc[0]):
            return [f'(!((int) {(a := cify(expression[:lc[0] - 2]))[0]} % (int) {(b := cify(expression[lc[0]:]))[0]}))', 'R' if 'R' in (a[1], b[1]) else 'Z']
        elif lc[1] == '%':
            return [f'((int) {cify(expression[:lc[0] - 1])[0]} % (int) {cify(expression[lc[0]:])[0]})', 'Z']
        elif lc[1] == '//' or (lc[1] == '/' and (flc := find_last_char(expression, {'//'})) and flc[0] + 1 == lc[0]):
            return [f'((int) {(a := cify(expression[:lc[0] - 2]))[0]} / (int) {(b := cify(expression[lc[0]:]))[0]})', 'Z']
        elif lc[1] == '/':
            return [f'((float) {(a := cify(expression[:lc[0] - 2]))[0]} / {(b := cify(expression[lc[0]:]))[0]})', 'R']
        else:
            return [f'({(a := cify(expression[:lc[0] - 1]))[0]} {lc[1]} {(b := cify(expression[lc[0]:]))[0]})', 'R' if 'R' in (a[1], b[1]) else 'Z']
    elif lc := find_last_char(expression, {'**'}):
        return [f'(pow({(a := cify(expression[:lc[0] - 1]))[0]}, {(b := cify(expression[lc[0]+1:]))[0]}))', 'R' if 'R' in (a[1], b[1]) else 'Z']
    elif expr := re.match(r'^\s*-(.*)\s*$', expression): #negation
        return [f'(-{(a:=cify(expr[1]))[0]})', a[1]]
    elif expr := re.match(r'^\s*(\w+)\s*\[(.*)]\s*$', expression):  #getitem
        container = cify(expr[1])
        if container[1].endswith('.'):
            return [f'{container[0]}({cify(expr[2])[0]}, {sequence_ind[container[0]]})', container[1][:-1]]
    elif expr := re.match(r'^\s*(.*)\s*\.\s*(\w+)\s*$', expression):  #getattr
        container = cify(expr[1])
        element = expr[2].strip()
        if container[1].startswith('{'):
            return [f'{cify(container[0])[0]}->{element}', structs[container[1][1:-1]][element]]
        else:
            return [f'{container[0]}->{element}', structs[container[1]][element]]
    elif expr := re.match(r'^\s*\((.*)\)\s*$', expression):  #unneccessary parentheses
        return cify(expr[1])
    print(f'Error when compiling expression at line {h0+1}:')
    print(code[h0])
    #if expression in h:
    #    print(' '*h.index(expression) + '^'*len(expression.strip()))
    print(f'Error in expression: {expression}')
    exit(1)

code = []
last_true_line = 0
inside_start = 0
running = ''
for i0, i in enumerate(no_comment_code):
    inside_start = in_paranth(i, inside_start)
    running += i + ' '
    if not inside_start:
        code.append(running[:-1])
        running = ''

for h0, h in enumerate(code):
    for i in malloc_needs_free:
        c_code.append('\t'*indentation + f'free({i[0]});')
    malloc_needs_free = []
    for i in where_loops:
        indentation -= 1
        c_code.append('\t' * indentation + '}')
    where_loops = []
    if line := re.match(r'^\s*(print)\s+(.*)', h): #print statement
        bef_loop = len(c_code)
        if (cified_line := cify(line[2]))[1] == 'Z':
            if where_loops:
                c_code.insert(bef_loop, '\t' * indentation + f'dy_set_i* ___p_s{bonus_c_variables["___p_s"]} = create_set_i();')
                c_code.append('\t' * indentation + f'append_i(___p_s{bonus_c_variables["___p_s"]}, {cified_line[0]}); //print')
                for i in where_loops:
                    indentation -= 1
                    c_code.append('\t' * indentation + '}')
                where_loops = []
                c_code.append('\t' * indentation + f'print_set_i(___p_s{bonus_c_variables["___p_s"]});')
                c_code.append('\t' * indentation + f'clear_set_i(___p_s{bonus_c_variables["___p_s"]});')
                bonus_c_variables['___p_s'] += 1
            elif cified_line[1] == 'Z':
                c_code.append('\t' * indentation + f'printf("%d\\n", {cified_line[0]});')
        elif cified_line[1] == 'R':
            if where_loops:
                c_code.insert(bef_loop, '\t' * indentation + f'dy_set_i* ___p_s{bonus_c_variables["___p_s"]} = create_set_f();')
                c_code.append('\t' * indentation + f'append_f(___p_s{bonus_c_variables["___p_s"]}, {cified_line[0]}); //print')
                for i in where_loops:
                    indentation -= 1
                    c_code.append('\t' * indentation + '}')
                where_loops = []
                c_code.append('\t' * indentation + f'print_set_f(___p_s{bonus_c_variables["___p_s"]});')
                c_code.append('\t' * indentation + f'clear_set_f(___p_s{bonus_c_variables["___p_s"]});')
                bonus_c_variables['___p_s'] += 1
            elif cified_line[1] == 'R':
                c_code.append('\t' * indentation + f'printf("%f\\n", {cified_line[0]});')
        elif cified_line[1] == 'Z.':
            c_code.append('\t' * indentation + f'for (int ___l_var = 0; ___l_var < 16; ___l_var++) printf("%d, ", {cified_line[0]}(___l_var, {sequence_ind[cified_line[0]]}));')
            c_code.append('\t' * indentation + f'printf("%d...\\n", {cified_line[0]}(16, {sequence_ind[cified_line[0]]}));')
        elif cified_line[1] == 'R.':
            c_code.append('\t' * indentation + f'for (int ___l_var = 0; ___l_var < 16; ___l_var++) printf("%f, ", {cified_line[0]}(___l_var, {sequence_ind[cified_line[0]]}));')
            c_code.append('\t' * indentation + f'printf("%f...\\n", {cified_line[0]}(16, {sequence_ind[cified_line[0]]}));')
        elif cified_line[1] in structs:
            c_code.append('\t' * indentation + f'printf("{percent_print[cified_line[1]]}\\n", {decomp_print[cified_line[1]](cified_line[0])});')
        else:
            print(f'Cannot print out unknown type: {cified_line[1]}')
            print(h)
            exit(1)
    elif line := re.match(r'^\s*struct\s+(.*)\s*=\s*\[(.*)]\s*$', h): #struct creation
        structs[line[1].strip()] = {i[0]:i[1] for i in cify_attrs(line[2])}
        struct_original_order[line[1].strip()] = [i[0] for i in cify_attrs(line[2])]
        percent_print[line[1].strip()] = f'{line[1].strip()}({", ".join(i+": "+percent_print[structs[line[1].strip()][i]] for i in struct_original_order[line[1].strip()])})'
        decomp_print[line[1].strip()] = (lambda line_val: lambda x: ", ".join(decomp_print[structs[line_val][i]](f'{x}->{i}') for i in struct_original_order[line_val]))(line[1].strip())
        c_code.append('\t' * indentation + 'typedef struct {')
        for i0 in structs[line[1].strip()]:
            variables[f'{line[1].strip()}{i0}'] = structs[line[1].strip()][i0]
            c_code.append('\t' * (indentation+1) + f'{datatype_to_c[structs[line[1].strip()][i0]]} {i0};')
        c_code.append('\t' * indentation + '} ' + f'{line[1].strip()};')
        datatype_to_c[line[1].strip()] = f'{line[1].strip()}*'
        datatype_to_c['{' + line[1].strip() + '}'] = f'{line[1].strip()}*'
        datatype_to_quant[line[1].strip()] = 's'
        datatype_to_quant['{' + line[1].strip() + '}'] = 's'
    elif line := re.match(r'^\s*def\s+(\w+)\s*\((.*?)\)\s*=>\s*(.*)\s+in\s+(.*)$', h): #function definition
        inps = {i[0]:i[1] for i in cify_attrs(line[2])}
        c_code.append('\t' * indentation + f'{datatype_to_c[line[4].strip()]} {line[1]}({", ".join(f"{datatype_to_c[inps[i0]]} {i0}" for i0 in inps)})' +' {')
        for i0 in inps:
            variables[i0] = inps[i0]
        indentation += 1
        c_code.append('\t' * indentation + f'return {cify(line[3])[0]};')
        indentation -= 1
        c_code.append('\t' * indentation + '}')
        functions[line[1]] = line[4].strip()
    elif line := re.match(r'^\s*(.*)\[(.*)]\s+in\s+(.*)\s*=\s*(.*)with(.*)', h): #variable creation - sequence recursive
        datatype = line[3].replace(' ', '')
        sequence_ind[line[1].strip()] = len(sequence_ind)
        #if datatype == 'Z':
        in_where = True
        c_x = line[2].strip()
        c_code.append('\t' * indentation + f'{datatype_to_c[datatype]} {line[1].strip()}(int64_t {c_x}, int ___ind) '+'{')
        c_code.append('\t' * indentation + f'\tif (is_cached_i({c_x}, ___ind)) '+'{')
        c_code.append('\t' * indentation + f'\t\treturn get_cache_{datatype_to_quant[datatype]}({c_x}, ___ind{f", sizeof({datatype})" if datatype_to_quant[datatype] == "s" else ""});')
        c_code.append('\t' * indentation + '\t} else {')
        variables[line[2].strip()] = 'Z'
        variables[line[1].strip()] = f'{datatype}.'
        c_out = cify(line[4])
        indentation += 2
        c_code.append('\t' * indentation + f'{datatype_to_c[datatype]} ___outp = {c_out[0]};')
        c_code.append('\t' * indentation + f'return cache_{datatype_to_quant[datatype]}({c_x}, ___outp, ___ind{f", sizeof({datatype})" if datatype_to_quant[datatype] == "s" else ""});')
        indentation -= 1
        c_code.append('\t' * indentation + '}')
        indentation -= 1
        c_code.append('\t' * indentation + '}')
        for i in cify_attrs(line[5]): #pairs
            c_code.append('\t' * indentation + f'cache_{datatype_to_quant[datatype]}({i[0][0]}, {i[0][1]}, {sequence_ind[line[1].strip()]}{f", sizeof({datatype})" if datatype_to_quant[datatype] == "s" else ""});')
        for i in where_loops:
            indentation -= 1
            c_code.append('\t' * indentation + '}')
        where_loops = []
    elif line := re.match(r'^\s*(.*)\[(.*)]\s+in\s+(.*)\s*=\s*(.*)', h): #variable creation - sequence
        datatype = line[3].replace(' ', '')
        sequence_ind[line[1].strip()] = len(sequence_ind)
        in_where = True
        c_x = line[2].strip()
        c_code.append('\t' * indentation + f'{datatype_to_c[datatype]} {line[1].strip()}(int64_t {c_x}, int ___ind) '+'{')
        c_code.append('\t' * indentation + f'\tif (is_cached_i({c_x}, ___ind)) '+'{')
        c_code.append('\t' * indentation + f'\t\treturn get_cache_{datatype_to_quant[datatype]}({c_x}, ___ind{f", sizeof({datatype})" if datatype_to_quant[datatype] == "s" else ""});')
        c_code.append('\t' * indentation + '\t} else {')
        variables[line[2].strip()] = 'Z'
        variables[line[1].strip()] = f'{datatype}.'
        c_out = cify(line[4])
        indentation += 2
        c_code.append('\t' * indentation + f'{datatype_to_c[datatype]} ___outp = {c_out[0]};')
        c_code.append('\t' * indentation + f'return cache_{datatype_to_quant[datatype]}({c_x}, ___outp, ___ind{f", sizeof({datatype})" if datatype_to_quant[datatype] == "s" else ""});')
        indentation -= 1
        c_code.append('\t' * indentation + '}')
        indentation -= 1
        c_code.append('\t' * indentation + '}')
        for i in where_loops:
            indentation -= 1
            c_code.append('\t' * indentation + '}')
        where_loops = []
    elif line := re.match(r'^\s*(.*)\s+in\s+(.*)\s*=\s*\{(.*)where(.*)}', h): #variable creation - superposition comprehension
        datatype = line[2].replace(' ', '')
        variables[line[1].strip()] = '{' + datatype + '}'
        in_where = True
        if flc := find_last_char(line[4][1:-1], {' with '}):
            cify(line[4][flc[0]+1:-1])
            c_code.append('\t' * indentation + f'dy_set_i* {line[1].strip()} = create_set_i();')
            c_out = cify(line[3])
            c_con = cify(line[4][:flc[0]])
        else:
            flc = [-1, 0]
            c_code.append('\t' * indentation + f'dy_set_i* {line[1].strip()} = create_set_i();')
            c_out = cify(line[3])
            c_con = cify(line[4])
        c_code.append('\t' * indentation + f'if ({c_con[0]}) ' + '{append_'+datatype_to_quant[datatype]+'('+line[1].strip()+', '+c_out[0]+(f", sizeof({datatype})" if datatype_to_quant[datatype] == "s" else "")+');}')
        for i in where_loops:
            indentation -= 1
            c_code.append('\t' * indentation + '}')
        where_loops = []
    elif line := re.match(r'^\s*(.*)\s+in\s+(.*)\s*=\s*\{(.*)}', h): #variable creation - superposition
        datatype = line[2].replace(' ', '')
        #if datatype == 'Z':
        c_code.append('\t'*indentation + f'dy_set_i* {line[1].strip()} = create_set_i();')
        if not re.match(r'\{\s*}', line[3].strip()):
            c_code.append('\t' * indentation + f'{datatype_to_c[datatype]} ___b_a{bonus_c_variables["___b_a"]}[{line[3].count(",")+1}] = ' + '{' + line[3].strip() + '};')
            c_code.append('\t' * indentation + f'array_to_set_{datatype_to_quant[datatype]}({line[1].strip()}, ___b_a{bonus_c_variables["___b_a"]}, {line[3].count(",")+1});')
            bonus_c_variables['___b_a'] += 1
        variables[line[1].strip()] = '{'+datatype+'}'
    elif line := re.match(r'^\s*(.*)\s+in\s+(.*)\s*=\s*(.*)', h): #variable creation
        datatype = line[2].replace(' ', '')
        bef_loop = len(c_code)
        if 1:
            eq_to = cify(line[3])[0].strip()
            if where_loops:
                c_code.insert(bef_loop, '\t'*indentation + f'dy_set_i* {line[1].strip()} = create_set_i();')
                c_code.append('\t' * indentation + f'append_{datatype_to_quant[datatype]}({line[1].strip()}, {eq_to}{f", sizeof({datatype})" if datatype_to_quant[datatype] == "s" else ""});')
                variables[line[1].strip()] = '{'+datatype+'}'
            else:
                c_code.append('\t'*indentation + f'{datatype_to_c[line[2].strip()]} {line[1].strip()} = {eq_to};')
                variables[line[1].strip()] = datatype
    elif line := re.match(r'^\s*(.*)\s*=\s*(.*)', h): #variable change
        bef_loop = len(c_code)
        eq_to = cify(line[2])[0].strip()
        if where_loops:
            c_code.insert(bef_loop, '\t'*indentation + f'clear_set_i({line[1].strip()});')
            c_code.append('\t' * indentation + 'append_i(' + line[1].strip() +', ' + eq_to + ');')
        else:
            c_code.append('\t'*indentation + f'{line[1].strip()} = {eq_to};')
    elif line := re.match(r'^\s*(.*)\.extend\((.*)\)', h): #superposition extension
        bef_loop = len(c_code)
        eq_to = cify(line[2])[0].strip()
        if where_loops:
            c_code.append('\t' * indentation + f'append_{datatype_to_quant[variables[line[1].strip()]]}({line[1].strip()}, {eq_to});')
    elif line := re.match(r'^\s*$', h): #nothing
        pass
    else:
        print(f'Error when compiling line {h0+1}:')
        print(h)
        exit(1)

for i in where_loops:
    indentation -= 1
    c_code.append('\t' * indentation + '}')
where_loops = []

print('''//Compiled by Uberort v1.0.1
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>
#include <math.h>
#include <string.h>

#define INITIAL_CAPACITY 16
#define US_SIZE 262144

int cur_set_i_ind = 0;

struct Cache;

union Quant{
    int64_t i;
    double f;
    struct Cache* c;
    void* s;
};

typedef struct {
    uint8_t allocated; // 0-not allocated, 1-allocated, 2-freed up
    union Quant element;
    uint16_t rev_ind; // index in the dy_set_i
    uint8_t is_ptr; // 0-not pointer, 1-void, 2-cache
} si_e;

si_e universal_set[US_SIZE]; // 18-bit hash array containing integers

// 18-bit hash for integers
uint hash_int(int a, int sp_index) {
    return (a*3 + ((a%63) << 3) + (sp_index*10397)) % US_SIZE;
}

uint64_t float_to_int_bits(double f) {
    union {
        double f;
        uint64_t i;
    } u;
    u.f = f;
    return u.i & ((1<<16)-1);
}

// 18-bit hash for floats
uint hash_float(double f, int sp_index) {
    uint64_t a = float_to_int_bits(f);
    return (a*3 + ((a%63) << 3) + (sp_index*10397)) % US_SIZE;
}

// 18-bit hash for structs
uint hash_struct(int64_t* f, int sp_index, int size) {
    int outp = 0;
    for (int i = 0; i<size/8; i++) {
        int64_t a = f[i] & ((1<<16)-1);
        outp += (a*3 + ((a%63) << 3) + (sp_index*10397)) % US_SIZE;
        outp = outp*3 + ((outp%63) << 3);
    }
    return outp % US_SIZE;
}

typedef struct {
    int* elements;   // array to hold element indices
    int size;        // number of elements in the set
    int capacity;    // current allocated capacity
    int ind;         // index of the set (for better hash) 
} dy_set_i;

dy_set_i* create_set_i() {
    dy_set_i *self = malloc(sizeof(dy_set_i));
    self->elements = malloc(INITIAL_CAPACITY * sizeof(int64_t));
    self->size = 0;
    self->capacity = INITIAL_CAPACITY;
    self->ind = cur_set_i_ind++;
    return self;
}

typedef struct Cache {
    union Quant key;
    union Quant element;
} Cache;

int is_cached_i(int item, int ind) {
    for (int i = hash_int(item, ind); 1; i++) {
        if (universal_set[i%US_SIZE].allocated == 0) { // not in universal set at all
            return 0;
        } else if (universal_set[i%US_SIZE].allocated == 1 &&
        universal_set[i%US_SIZE].rev_ind == 65535) {
            if (universal_set[i%US_SIZE].element.c->key.i == item) { // no false matches
                return 1;
            }
        }
    }
}

int64_t get_cache_i(int item, int ind) {
    for (int i = hash_int(item, ind); 1; i++) {
        if (universal_set[i%US_SIZE].allocated == 1 &&
        universal_set[i%US_SIZE].rev_ind == 65535) {
            if (universal_set[i%US_SIZE].element.c->key.i == item) { // no false matches
                return universal_set[i%US_SIZE].element.c->element.i;
            }
        }
    }
}

int64_t cache_i(int item, int value, int ind) {
    for (int i = hash_int(item, ind); 1; i++) {
        if (universal_set[i%US_SIZE].allocated != 1) { // not allocated or freed up
            universal_set[i%US_SIZE].element.c = malloc(sizeof(struct Cache));
            universal_set[i%US_SIZE].element.c->key.i = item;
            universal_set[i%US_SIZE].element.c->element.i = value;
            universal_set[i%US_SIZE].rev_ind = -1;
            universal_set[i%US_SIZE].allocated = 1;
            return value;
        }
    }
}

double get_cache_f(int item, int ind) {
    for (int i = hash_int(item, ind); 1; i++) {
        if (universal_set[i%US_SIZE].allocated == 1 &&
        universal_set[i%US_SIZE].rev_ind == 65535) {
            if (universal_set[i%US_SIZE].element.c->key.i == item) { // no false matches
                return universal_set[i%US_SIZE].element.c->element.f;
            }
        }
    }
}

double cache_f(int item, double value, int ind) {
    for (int i = hash_int(item, ind); 1; i++) {
        if (universal_set[i%US_SIZE].allocated != 1) { // not allocated or freed up
            universal_set[i%US_SIZE].element.c = malloc(sizeof(struct Cache));
            universal_set[i%US_SIZE].element.c->key.i = item;
            universal_set[i%US_SIZE].element.c->element.f = value;
            universal_set[i%US_SIZE].rev_ind = -1;
            universal_set[i%US_SIZE].allocated = 1;
            return value;
        }
    }
}

void* get_cache_s(int item, int ind, int size) {
    for (int i = hash_int(item, ind); 1; i++) {
        if (universal_set[i%US_SIZE].allocated == 1 &&
            universal_set[i%US_SIZE].rev_ind == 65535 &&
            universal_set[i%US_SIZE].is_ptr == 2) {
            if (universal_set[i%US_SIZE].element.c->key.i == item) { // no false matches
                return universal_set[i%US_SIZE].element.c->element.s;
            }
        }
    }
}

void* cache_s(int item, void* value, int ind, int size) {
    for (int i = hash_int(item, ind); 1; i++) {
        if (universal_set[i%US_SIZE].allocated != 1) { // not allocated or freed up
            universal_set[i%US_SIZE].element.c = malloc(sizeof(struct Cache));
            universal_set[i%US_SIZE].element.c->element.s = malloc(size);
            if (universal_set[i%US_SIZE].element.s == NULL) {
                fprintf(stderr, "Error: Memory allocation failed\\n");
                exit(1);
            }
            memcpy(universal_set[i%US_SIZE].element.c->element.s, value, size);
            universal_set[i%US_SIZE].element.c->key.i = item;
            universal_set[i%US_SIZE].rev_ind = -1;
            universal_set[i%US_SIZE].allocated = 1;
            universal_set[i%US_SIZE].is_ptr = 2;
            return value;
        }
    }
}

int contains_i(dy_set_i* self, int item) {
    for (int i = hash_int(item, self->ind); 1; i++) {
        if (universal_set[i%US_SIZE].allocated == 0) { // not in universal set at all
            return 0;
        } else if (universal_set[i%US_SIZE].allocated == 1) {
            if (universal_set[i%US_SIZE].element.i == item) { // no false matches
                return 1;
            }
        }
    }
}

void append_i(dy_set_i* self, int item) {
    if (!contains_i(self, item)) {
        for (int i = hash_int(item, self->ind); 1; i++) {
            if (universal_set[i%US_SIZE].allocated != 1) { // not allocated or freed up
                universal_set[i%US_SIZE].element.i = item;
                universal_set[i%US_SIZE].allocated = 1;
                universal_set[i%US_SIZE].rev_ind = self->size;
                universal_set[i%US_SIZE].is_ptr = 0;
                if (self->size == self->capacity) {
                    self->capacity *= 2;
                    self->elements = realloc(self->elements, self->capacity * sizeof(int64_t));
                    if (self->elements == NULL) {
                        fprintf(stderr, "Error: Memory allocation failed\\n");
                        exit(1);
                    }
                }
                self->elements[self->size] = i%US_SIZE;
                self->size += 1;
                return;
            }
        }
    }
}

void remove_i(dy_set_i* self, int item) {
    for (int i = hash_int(item, self->ind); 1; i++) {
        if (universal_set[i%US_SIZE].allocated == 0) { // already not in set
            return;
        } else if (universal_set[i%US_SIZE].allocated == 1) {
            if (universal_set[i%US_SIZE].element.i == item) { // no false matches
                universal_set[i%US_SIZE].allocated = 2;
                self->size -= 1;
                self->elements[universal_set[i%US_SIZE].rev_ind] =
                        self->elements[self->size];
                universal_set[self->elements[self->size]].rev_ind = 
                        universal_set[i%US_SIZE].rev_ind;
                return;
            }
        }
    }
}

void print_set_i(dy_set_i* self) {
    printf("{");
    for (int i = 0; i < self->size; i++) {
        printf("%d", universal_set[self->elements[i]].element.i);
        if (i != self->size-1) {
            printf(", ");
        }
    }
    printf("}\\n");
}

void array_to_set_i(dy_set_i* self, int64_t* arr, int size) {
    for (int i = 0; i < size; i++) {
        append_i(self, arr[i]);
    }
}

dy_set_i* add_set_i(dy_set_i* self, dy_set_i* other) {
    dy_set_i* outp = create_set_i();
    for (int i = 0; i < self->size; i++) {
        for (int j = 0; j < other->size; j++) {
            append_i(outp, universal_set[self->elements[i]].element.i +
                    universal_set[other->elements[j]].element.i);
        }
    }
    return outp;
}

void clear_set_i(dy_set_i* self) {
    for (;self->size;) {
        remove_i(self, universal_set[self->elements[0]].element.i);
    }
}

dy_set_i* create_set_f() {
    dy_set_i *self = malloc(sizeof(dy_set_i));
    self->elements = malloc(INITIAL_CAPACITY * sizeof(double));
    self->size = 0;
    self->capacity = INITIAL_CAPACITY;
    self->ind = cur_set_i_ind++;
    return self;
}

int contains_f(dy_set_i* self, double item) {
    for (int i = hash_float(item, self->ind); 1; i++) {
        if (universal_set[i%US_SIZE].allocated == 0) { // not in universal set at all
            return 0;
        } else if (universal_set[i%US_SIZE].allocated == 1) {
            if (universal_set[i%US_SIZE].element.f == item) { // no false matches
                return 1;
            }
        }
    }
}

void append_f(dy_set_i* self, double item) {
    if (!contains_f(self, item)) {
        for (int i = hash_float(item, self->ind); 1; i++) {
            if (universal_set[i%US_SIZE].allocated != 1) { // not allocated or freed up
                universal_set[i%US_SIZE].element.f = item;
                universal_set[i%US_SIZE].allocated = 1;
                universal_set[i%US_SIZE].rev_ind = self->size;
                universal_set[i%US_SIZE].is_ptr = 0;
                if (self->size == self->capacity) {
                    self->capacity *= 2;
                    self->elements = realloc(self->elements, self->capacity * sizeof(double));
                    if (self->elements == NULL) {
                        fprintf(stderr, "Error: Memory allocation failed\\n");
                        exit(1);
                    }
                }
                self->elements[self->size] = i%US_SIZE;
                self->size += 1;
                return;
            }
        }
    }
}

void remove_f(dy_set_i* self, double item) {
    for (int i = hash_float(item, self->ind); 1; i++) {
        if (universal_set[i%US_SIZE].allocated == 0) { // already not in set
            return;
        } else if (universal_set[i%US_SIZE].allocated == 1) {
            if (universal_set[i%US_SIZE].element.f == item) { // no false matches
                universal_set[i%US_SIZE].allocated = 2;
                self->size -= 1;
                self->elements[universal_set[i%US_SIZE].rev_ind] =
                        self->elements[self->size];
                universal_set[self->elements[self->size]].rev_ind = 
                        universal_set[i%US_SIZE].rev_ind;
                return;
            }
        }
    }
}

void print_set_f(dy_set_i* self) {
    printf("{");
    for (int i = 0; i < self->size; i++) {
        printf("%f", universal_set[self->elements[i]].element.f);
        if (i != self->size-1) {
            printf(", ");
        }
    }
    printf("}\\n");
}

void array_to_set_f(dy_set_i* self, double* arr, int size) {
    for (int i = 0; i < size; i++) {
        append_f(self, arr[i]);
    }
}

void clear_set_f(dy_set_i* self) {
    for (;self->size;) {
        remove_f(self, universal_set[self->elements[0]].element.f);
    }
}

int contains_s(dy_set_i* self, void* item, int size) {
    for (int i = hash_struct(item, self->ind, size); 1; i++) {
        if (universal_set[i%US_SIZE].allocated == 0) { // not in universal set at all
            return 0;
        } else if (universal_set[i%US_SIZE].allocated == 1 && universal_set[i%US_SIZE].is_ptr == 1) {
            if (!memcmp(universal_set[i%US_SIZE].element.s, item, size)) { // no false matches
                return 1;
            }
        }
    }
}

void append_s(dy_set_i* self, void* item, int size) {
    if (!contains_s(self, item, size)) {
        for (int i = hash_struct(item, self->ind, size); 1; i++) {
            if (universal_set[i%US_SIZE].allocated != 1) { // not allocated or freed up
                universal_set[i%US_SIZE].element.s = malloc(size);
                if (universal_set[i%US_SIZE].element.s == NULL) {
                    fprintf(stderr, "Error: Memory allocation failed\\n");
                    exit(1);
                }
                memcpy(universal_set[i%US_SIZE].element.s, item, size);
                universal_set[i%US_SIZE].allocated = 1;
                universal_set[i%US_SIZE].rev_ind = self->size;
                universal_set[i%US_SIZE].is_ptr = 1;
                if (self->size == self->capacity) {
                    self->capacity *= 2;
                    self->elements = realloc(self->elements, self->capacity * sizeof(double));
                    if (self->elements == NULL) {
                        fprintf(stderr, "Error: Memory allocation failed\\n");
                        exit(1);
                    }
                }
                self->elements[self->size] = i%US_SIZE;
                self->size += 1;
                return;
            }
        }
    }
}

void remove_s(dy_set_i* self, void* item, int size) {
    for (int i = hash_struct(item, self->ind, size); 1; i++) {
        if (universal_set[i%US_SIZE].allocated == 0) { // already not in set
            return;
        } else if (universal_set[i%US_SIZE].allocated == 1) {
            if (!memcmp(universal_set[i%US_SIZE].element.s, item, size)) { // no false matches
                universal_set[i%US_SIZE].allocated = 2;
                self->size -= 1;
                self->elements[universal_set[i%US_SIZE].rev_ind] =
                        self->elements[self->size];
                universal_set[self->elements[self->size]].rev_ind = 
                        universal_set[i%US_SIZE].rev_ind;
                return;
            }
        }
    }
}

void clear_set_s(dy_set_i* self, int size) {
    for (;self->size;) {
        remove_s(self, universal_set[self->elements[0]].element.s, size);
    }
}

double gauss_pd(double x) {
    return (1.0 / sqrt(2 * M_PI)) * exp(-0.5 * x * x);
}

double gauss_random() {
    // Generate two independent random numbers uniformly distributed in (0, 1)
    double u1 = ((double) rand() / (RAND_MAX));
    double u2 = ((double) rand() / (RAND_MAX));

    // Apply Box-Muller transform
    double z0 = sqrt(-2.0 * log(u1)) * cos(2.0 * M_PI * u2);

    // z0 is a normally distributed random variable with mean 0 and std deviation 1
    return z0;
}

double gauss_cd(double x) {
    return 0.5 * (1 + erf(x / sqrt(2)));
}
''')

print()
print('\n'.join(['int main() {\n\tsrand ( time(NULL) );'] + c_code + ['}']))
print()
