import re

##########################################################
#                 Uberort compiler v1.2.0                #
##########################################################
#New with v1.2.0:
#Added loops, code branches and multi-line functions
#Added superposition pairing and concatenation
#Enhanced error handling:
#-Debug mode
#-New statements: raise, check
#-Compile-time error handling
#Data is now mutable
#Function arguments and return types now can be superpositions
#Added packaging
#Added strings

c_code = []
debug = False

def cify_all(full_file, package=None, start_indent=1):
    global c_code, debug
    file = full_file[:full_file.index('.')]
    commented_code = [i.strip() for i in open(full_file, encoding='UTF-8').readlines()]
    if package:
        for i0, i in enumerate(commented_code):
            if re.match(rf'^\s*package\s+{package}\s*$', i[:i.index('#')] if '#' in i else i):
                commented_code = commented_code[i0+1:]
                break
        else:
            print(f'Error: package {package} was not found in {full_file}')
        indentation = start_indent
        overall_indent = 0
        indentation_types = [['package', overall_indent]]
    else:
        indentation = start_indent
        overall_indent = 0
        indentation_types = []
    no_comment_code = [i[:i.index('#')] if '#' in i else i for i in commented_code]


    functions = {'sqrt':'R', 'sin':'R', 'cos':'R', 'tan':'R', 'asin':'R', 'acos':'R', 'atan':'R', 'atan2':'R', 'exp':'R', 'erf':'R', 'gauss_pd':'R', 'gauss_cd':'R'}
    function_parameters = {'sqrt':['R'], 'sin':['R'], 'cos':['R'], 'tan':['R'], 'asin':['R'], 'acos':['R'], 'atan':['R'], 'atan2':['R'], 'exp':['R'], 'erf':['R'], 'gauss_pd':['R'], 'gauss_cd':['R']}
    function_nests = []

    bonus_c_variables = {'___b_a':0, #bonus array
                         '___c_s':0, #comprehension superposition
                         '___c_h':0, #carray holder
                         '___p_s':0, #print_superposition
                         '___o_l':0, #one-liner variable
                         '___lbl':0, #label
                         '___s_p':0, #struct pointer
                         '___q_p':0, #quant pointer
                         '___c_p':0, #copy struct
                         '___i_v':0, #input variable
                         '___s_s':0, #swap superposition
                         '___o_s':0, #output superposition
                         }
    max_b_c_variables = {'___c_s':0, #comprehension superposition
                         '___c_i_s':0, #convert int into string
                         '___c_h':0, #carray holder
                         '___o_l':0, #one-liner variable
                         }
    malloc_needs_free = []
    malloc_indent = [[]]

    debug_only = -1

    variables = {'M_PI':'R', 'PI':'R', 'exp(1)':'R', 'EULER':'R'}
    while_in_as = {}
    where_loops = []
    pair_loops = []
    seq_loops = []
    in_where = True
    in_as = []
    in_as_replace = {'PI':'M_PI', 'EULER':'exp(1)'}
    structs = {}
    struct_original_order = {}
    percent_print = {'Z':'%ld', 'R':'%lf', 'Str':'%s'}
    decomp_print = {'Z':lambda x: x, 'R':lambda x: x, 'Str':lambda x: x}
    decomp_scan = {'Z':lambda x: f'&{x}', 'R':lambda x: f'&{x}', 'Str':lambda x: f'&{x}'}
    #in_where = False

    datatype_to_quant = {'{Z}':'i', '{R}':'f', '{Str}':'s', 'Z':'i', 'R':'f', 'Str':'s'}
    datatype_to_c = {'Z':'int64_t', 'R':'double', '{Z}':'int64_t', '{R}':'double', 'Str':'char*', '{Str}':'char*'}

    def datatype_real_c(var):
        if var.startswith('{'):
            return 'list*'
        else:
            return datatype_to_c[var]

    #turn a value into union Quant
    def to_quant(var):
        c_var_name = f'___q_p{bonus_c_variables["___q_p"]}'
        bonus_c_variables["___q_p"] += 1
        #if var[0] in variables:
        #    c_code.append('\t' * indentation + f'Quant {c_var_name} = '+'{.'+datatype_to_quant[var[1]]+f'={file}___'+var[0]+'};')
        #else:
        c_code.append('\t' * indentation + f'Quant {c_var_name} = '+'{.'+datatype_to_quant[var[1]]+'='+var[0]+'};')
        return f'{c_var_name}'

    #copy a struct and all of its pointers (deepcopy)
    def copy_struct(var):
        if var[1] in {'Z', 'R', '{Z}', '{R}', 'Str', '{Str}'}: return [f'{var[0]}', var[1]]
        c_var_name = f'___c_p{bonus_c_variables["___c_p"]}'
        bonus_c_variables['___c_p'] += 1
        c_code.append('\t' * indentation + f'{var[1]}* {file}___{c_var_name} = malloc(sizeof({var[1]}));')
        c_code.append('\t' * indentation + f'memcpy({file}___{c_var_name}, {var[0]}, sizeof({var[1]}));')
        for i in structs[var[1]]:
            if structs[var[1]][i] not in {'Z', 'R', '{Z}', '{R}', 'Str', '{Str}'}:
                c_code.append('\t' * indentation + f'{file}___{c_var_name}->{i} = {copy_struct([f"(({var[1]}*) {file}___{c_var_name})->{i}", structs[var[1]][i]])[0]};')
        return [f'{file}___{c_var_name}', var[1]]

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

    def error_print_function_stack():
        nonlocal indentation
        c_code.append('\t' * indentation + 'printf("main -> ");')
        c_code.append('\t' * indentation + 'for (int ___debug___l1 = 0; ___debug___l1 < ___debug_function_stack->cur_size; ___debug___l1++) {')
        indentation += 1
        c_code.append('\t' * indentation + 'printf((char*) getitem(___debug_function_stack, ___debug___l1).s);')
        c_code.append('\t' * indentation + 'printf(" -> ");')
        indentation -= 1
        c_code.append('\t' * indentation + '}')
        c_code.append('\t' * indentation + 'printf("Error\\n");')

    #cify values separated by commas
    def cify_attrs(expression, only_second_parts=False, inline_vars=False, manual_pair=False, function=None):
        nonlocal where_loops, indentation
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
                    if function:
                        if function_parameters[function][len(outp)].startswith('{'):
                            outp.append(sum_up(expression[last_break:i0], only_second_parts))
                        else:
                            outp.append(cify(expression[last_break:i0], only_second_parts))
                    elif manual_pair and outp:
                        outp.append(cify(expression[last_break:i0], only_second_parts, manual_pair=True, in_with=inline_vars))
                    elif manual_pair:
                        outp.append(cify(expression[last_break:i0], only_second_parts, in_with=inline_vars))
                        pair_loops.append(outp[-1][0][:-1]+'1')
                    else:
                        outp.append(cify(expression[last_break:i0], only_second_parts, in_with=inline_vars))
                    if inline_vars: #' as '
                        variables[outp[-1][0][1]] = outp[-1][1][0]
                        c_code.append('\t' * indentation + f'{datatype_to_c[outp[-1][1][0]]} {file}___{outp[-1][0][1] } = {outp[-1][0][0]}; //inline variable')
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
        if expression[last_break:].strip():
            if function:
                if function_parameters[function][len(outp)].startswith('{'):
                    outp.append(sum_up(expression[last_break:], only_second_parts))
                else:
                    outp.append(cify(expression[last_break:], only_second_parts))
            elif manual_pair and outp:
                outp.append(cify(expression[last_break:], only_second_parts, manual_pair=True, in_with=inline_vars))
            elif manual_pair:
                outp.append(cify(expression[last_break:], only_second_parts, in_with=inline_vars))
                pair_loops.append(outp[-1][0][:-1]+'1')
            else:
                outp.append(cify(expression[last_break:], only_second_parts, in_with=inline_vars))
            if inline_vars and outp[-1][-1] == 'as':
                variables[outp[-1][0][1]] = outp[-1][1][0]
                c_code.append('\t' * indentation + f'{datatype_to_c[outp[-1][1][0]]} {file}___{outp[-1][0][1]} = {outp[-1][0][0]}; //inline variable')
        return outp

    #find the pair of the first parentheses, return before, inside and after parts
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

    def sum_up(expression, only_second_parts=False): #in_as_replace
        nonlocal where_loops
        starting_where_loops = len(where_loops)
        c_var_name = f'___c_h{bonus_c_variables["___c_h"]}'
        bonus_c_variables['___c_h'] += 1
        bef_loop = len(c_code)
        cified = cify(expression, only_second_parts)
        #if cified[1].startswith('{'):
        c_code.insert(bef_loop, '\t' * indentation + f'list* {file}___{c_var_name} = make_list();')
        malloc_indent[starting_where_len].append(['list', c_var_name])
        c_code.append('\t' * indentation + f'append({file}___{c_var_name}, {to_quant(copy_struct(cified))}); //sum-up')
        #else:
        #    c_code.append('\t' * indentation + f'{datatype_to_c[cified[1]]} {file}___{c_var_name} = {copy_struct(cified)[0]};')
        variables[c_var_name] = cified[1]
        close_where_loops(starting_where_loops)
        return [f'{file}___{c_var_name}', cified[1]]

    #free an allocated struct
    def free_struct(mal, struct):
        #for i in structs[struct]:
        #    if structs[struct][i] not in {'Z', 'R', '{Z}', '{R}'}:
        #        free_struct(f'{mal}->{i}', structs[struct][i])
        c_code.append('\t' * indentation + f'free({mal});')

    #free all allocated memory that goes out of scope
    def free_malloc_indent(mal):
        nonlocal indentation, in_as_replace
        for i in mal:
            match i[0]:
                case 'list':
                    if variables[i[1]] not in {'Z', 'R', '{Z}', '{R}'}:
                        c_code.append('\t' * indentation + f'for (int {file}___{i[1]}___l1 = 0; {file}___{i[1]}___l1 < {file}___{i[1]}->cur_size; {file}___{i[1]}___l1++) ' + '{')
                        indentation += 1
                        free_struct(f'getitem({file}___{i[1]}, {file}___{i[1]}___l1).{datatype_to_quant[variables[i[1]]]}', variables[i[1]][1:-1])
                        indentation -= 1
                        c_code.append('\t' * indentation + '}')
                    c_code.append('\t' * indentation + f'destroy_list({file}___{i[1]});')
                case 'struct':
                    free_struct(i[1], variables[i[1]])
                case 'dict':
                    if variables[i[1][:-4]] not in {'Z.', 'R.'}:
                        c_code.append('\t' * indentation + f'for (int {file}___{i[1]}___l1 = 0; {file}___{i[1]}___l1 < {file}___{i[1]}->cur_size; {file}___{i[1]}___l1++) ' + '{')
                        indentation += 1
                        free_struct(f'{file}___{i[1]}->pairs[{file}___{i[1]}___l1].value.{datatype_to_quant[variables[i[1][:-4]][:-1]]}', variables[i[1][:-4]][:-1])
                        indentation -= 1
                        c_code.append('\t' * indentation + '}')
                    c_code.append('\t' * indentation + f'destroy_dict({file}___{i[1]});')
                case 'in_as':
                    in_as_replace[i[1]] = i[1]

    def close_where_loops(starting_where_loops):
        nonlocal where_loops, indentation
        for i in where_loops[starting_where_loops:]:
            if not i or i[-1] != 'paired':
                indentation -= 1
                free_malloc_indent(malloc_indent.pop())
                c_code.append('\t' * indentation + '}')
        where_loops = where_loops[:starting_where_loops]

    #cify a given expression
    def cify(expression, only_second_parts=False, direct_in_as=False, manual_pair=False, in_with=False):
        nonlocal in_where, where_loops, seq_loops, indentation
        #print(expression)
        starting_where_len = len(malloc_indent)-1
        expression = expression.strip()
        if expr := re.match(r'^\s*([\d_]+)\s*$', expression): #integer
            return [expr[1].replace('_', ''), 'Z']
        if expr := re.match(r'^\s*([\d_]+\.[\d_]+)\s*$', expression): #float
            return [expr[1].replace('_', ''), 'R']
        elif expr := re.match(r'^\s*(\".*\")\s*$', expression): #string
            return [expr[1], 'Str']
        elif expression in variables: #variable
            expression = in_as_replace[expression] if expression in in_as_replace else expression
            if expression in where_loops or [expression, 'paired'] in where_loops:
                return [f'{file}___{expression}___l2', variables[expression][1:-1]]
            elif expression in seq_loops:
                return [f'{file}___{expression}___l2', variables[expression][:-1]]
            elif in_where and variables[expression].startswith('{') and manual_pair:
                c_code.append('\t' * indentation + f'{datatype_to_c[variables[expression]]} {file}___{expression}___l2 = getitem({file}___{expression}, {pair_loops[-1]}).{datatype_to_quant[variables[expression]]}; //pair')
                where_loops.append([expression, 'paired'])
                if debug:
                    c_code.append('\t' * indentation + f'if ({pair_loops[-1][:-5]}->cur_size != {file}___{expression}->cur_size) '+'{')
                    indentation += 1
                    c_code.append('\t' * indentation + f'printf("Runtime error on line {h0 + 1} in function pair: {pair_loops[-1][:-5]} and {expression} has different number of elements\\n");')
                    error_print_function_stack()
                    indentation -= 1
                    c_code.append('\t' * indentation + f'exit(1);')
                    c_code.append('\t' * indentation + '}')
                return [f'{file}___{expression}___l2', variables[expression][1:-1]]
            elif in_where and variables[expression].startswith('{'):
                where_loops.append(expression)
                malloc_indent.append([])
                c_code.append('\t' * indentation + f'for (int {file}___{expression}___l1 = 0; {file}___{expression}___l1 < {file}___{expression}->cur_size; {file}___{expression}___l1++) ' + '{')
                indentation += 1
                c_code.append('\t' * indentation + f'{datatype_to_c[variables[expression]]} {file}___{expression}___l2 = getitem({file}___{expression}, {file}___{expression}___l1).{datatype_to_quant[variables[expression]]};')
                return [f'{file}___{expression}___l2', variables[expression][1:-1]]
            else:
                return [f'{file}___{expression}', variables[expression]]
        elif expression.endswith('}') and expression.startswith('{') and (splf := find_last_char(expression[1:-1], {' where '})) and never_leaves(expression[1:-1]): #superposition comprehension
            spl = splf[0]
            in_where = True
            starting_where_loops = len(where_loops)
            c_var_name = f'___c_h{bonus_c_variables["___c_h"]}'
            bonus_c_variables['___c_h'] += 1

            if direct_in_as:
                in_as_replace[iap:=in_as.pop()] = c_var_name
                variables[c_var_name] = variables[iap]
                malloc_indent[starting_where_len].append(['in_as', iap])
            c_code.append('\t' * indentation + f'list* {file}___{c_var_name} = make_list();')
            malloc_indent[starting_where_len].append(['list', c_var_name])
            if flc := find_last_char(expression[1:-1], {' with '}):
                cify(expression[flc[0]+1:-1])
            else:
                flc = [-1, 0]
            c_out = cify(expression[1:spl])
            c_con = cify(expression[spl+7:flc[0]])
            c_code.append('\t' * indentation + f'if ({c_con[0]}) ' + '{' + f'append({file}___{c_var_name}, {to_quant(copy_struct(c_out))}'+');}')
            close_where_loops(starting_where_loops)
            if not direct_in_as:
                variables[c_var_name] = c_out[1]
            where_loops.append(c_var_name)
            malloc_indent.append([])
            c_code.append('\t' * indentation + f'for (int {file}___{c_var_name}___l1 = 0; {file}___{c_var_name}___l1 < {file}___{c_var_name}->cur_size; {file}___{c_var_name}___l1++) ' + '{')
            indentation += 1
            c_code.append('\t' * indentation + f'{datatype_to_c[variables[c_var_name]]} {file}___{c_var_name}___l2 = getitem({file}___{c_var_name}, {file}___{c_var_name}___l1).{datatype_to_quant[variables[c_var_name]]};')
            return [f'{file}___{c_var_name}___l2', variables[c_var_name]]
        elif exprnot := re.match(r'^\s*(\w+)\s*\((.*)\)\s*$', expression) and not find_pair(expression)[2]:  #function call
            expr = [0] + find_pair(expression)
            fun = expr[1].strip()
            if fun in {'sum', 'max', 'range', 'random', 'randi', 'len', 'product', 'any', 'all', 'none', 'greater', 'first', 'smaller', 'mrange', 'average', 'gauss_random', 'abs', 'log', 'time', 'pair', 'input', 'int'}:
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
                                gen_do = cify(gen[1])
                                gen_where = cify(gen[2][:flc[0]])
                            else:
                                flc = [-1, 0]
                                gen_do = cify(gen[1])
                                gen_where = cify(gen[2])
                            c_code.append('\t' * indentation + f'if ({gen_where[0]}) '+'{'+f'{file}___{c_var_name} += {gen_do[0]}'+';} //sum')
                            close_where_loops(starting_where_loops)
                            c_code.insert(bef_loop_s, '\t' * indentation + f'{datatype_to_c[gen_do[1]]} {file}___{c_var_name} = 0;')
                            return [f'{file}___{c_var_name}', gen_do[1]]
                        else:
                            attrs = cify_attrs(expr[2])[0]
                            c_code.append('\t' * indentation + f'{file}___{c_var_name} += {attrs[0]}; //sum')
                            close_where_loops(starting_where_loops)
                            c_code.insert(bef_loop_s, '\t' * indentation + f'{datatype_to_c[attrs[1]]} {file}___{c_var_name} = 0;')
                            return [f'{file}___{c_var_name}', attrs[1]]
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
                                if flc := find_last_char(gen[2], {' with '}):
                                    cify(gen[2][flc[0]:])
                                    gen_do = cify(gen[1])
                                    gen_where = cify(gen[2][:flc[0]])
                                else:
                                    flc = [-1, 0]
                                    gen_do = cify(gen[1])
                                    gen_where = cify(gen[2])
                                key = cify(key)
                                c_code.append('\t' * indentation + f'if ({gen_where[0]} && ({c_key_name} < {key[0]})) ' + '{' + f'{file}___{c_var_name} = {gen_do[0]}; {c_key_name} = {key[0]};' + '} //max')
                                close_where_loops(starting_where_loops)
                                c_code.insert(bef_loop_s, '\t' * indentation + f'{datatype_to_c[gen_do[1]]} {file}___{c_var_name} = 0;')
                                c_code.insert(bef_loop_s, '\t' * indentation + f'{datatype_to_c[key[1]]} {c_key_name} = 0;')
                                return [f'{file}___{c_var_name}', gen_do[1]]
                            else:
                                attrs = cify_attrs(value)[0]
                                key = cify(key)
                                # bonus_c_variables['___o_l'] -= 1
                                c_code.append('\t' * indentation + f'if ({c_key_name} < {key[0]}) ' + '{' + f'{file}___{c_var_name} = {attrs[0]}; {c_key_name} = {key[0]};' + '} //max')
                                close_where_loops(starting_where_loops)
                                c_code.insert(bef_loop_s, '\t' * indentation + f'{datatype_to_c[attrs[1]]} {file}___{c_var_name} = 0;')
                                c_code.insert(bef_loop_s, '\t' * indentation + f'{datatype_to_c[key[1]]} {c_key_name} = 0;')
                                return [f'{file}___{c_var_name}', attrs[1]]
                        else:
                            value = expr[2]
                            if (gennot := re.match(r'^\s*(.*)where(.*)\s*$', expr[2])) and (splf := find_last_char(expr[2], {' where '})) and never_leaves(expr[2]):  # generator
                                gen = [0, expr[2][:splf[0]], expr[2][splf[0] + 6:]]
                                if flc := find_last_char(gen[2], {' with '}):
                                    cify(gen[2][flc[0]:])
                                    gen_do = cify(gen[1])
                                    gen_where = cify(gen[2][:flc[0]])
                                else:
                                    flc = [-1, 0]
                                    gen_do = cify(gen[1])
                                    gen_where = cify(gen[2])
                                c_code.append('\t' * indentation + f'if ({gen_where[0]} && ({c_key_name} < {gen_do[0]})) ' + '{' + f'{file}___{c_var_name} = {gen_do[0]}; {c_key_name} = {gen_do[0]};' + '} //max - key')
                                close_where_loops(starting_where_loops)
                                c_code.insert(bef_loop_s, '\t' * indentation + f'{datatype_to_c[gen_do[1]]} {file}___{c_var_name} = 0;')
                                c_code.insert(bef_loop_s, '\t' * indentation + f'{datatype_to_c[gen_do[1]]} {c_key_name} = 0;')
                                return [f'{file}___{c_var_name}', gen_do[1]]
                            else:
                                attrs = cify_attrs(value)[0]
                                key = cify(value)
                                c_code.append('\t' * indentation + f'if ({c_key_name} < {key[0]}) ' + '{' + f'{file}___{c_var_name} = {attrs[0]}; {c_key_name} = {key[0]};' + '} //max - key')
                                close_where_loops(starting_where_loops)
                                c_code.insert(bef_loop_s, '\t' * indentation + f'{datatype_to_c[attrs[1]]} {file}___{c_var_name} = 0;')
                                c_code.insert(bef_loop_s, '\t' * indentation + f'{datatype_to_c[key[1]]} {c_key_name} = 0;')
                                return [f'{file}___{c_var_name}', attrs[1]]
                    case 'range': #range comprehension
                        sp_name = f'___c_s_{bonus_c_variables["___c_s"]}'
                        bonus_c_variables['___c_s'] += 1
                        attrs = cify_attrs(expr[2])
                        match len(attrs):
                            case 1:
                                c_code.append('\t' * indentation + f'for (int {sp_name}___l2 = 0; {sp_name}___l2 < {attrs[0][0]}; {sp_name}___l2++)' + '{ //range')
                            case 2:
                                c_code.append('\t' * indentation + f'for (int {sp_name}___l2 = {attrs[0][0]}; {sp_name}___l2 < {attrs[1][0]}; {sp_name}___l2++)' + '{ //range')
                        variables[sp_name] = '{Z}'
                        where_loops.append(sp_name)
                        malloc_indent.append([])
                        indentation += 1
                        return [f'{sp_name}___l2', 'Z']
                    case 'mrange':  # range comprehension
                        sp_name = f'___c_s_{bonus_c_variables["___c_s"]}'
                        bonus_c_variables['___c_s'] += 1
                        attrs = cify_attrs(expr[2])
                        match len(attrs):
                            case 1:
                                c_code.append('\t' * indentation + f'for (int {sp_name}___l2 = 1; {sp_name}___l2 <= {attrs[0][0]}; {sp_name}___l2++)' + '{ //range')
                            case 2:
                                c_code.append('\t' * indentation + f'for (int {sp_name}___l2 = {attrs[0][0]}; {sp_name}___l2 <= {attrs[1][0]}; {sp_name}___l2++)' + '{ //range')
                        variables[sp_name] = '{Z}'
                        where_loops.append(sp_name)
                        malloc_indent.append([])
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
                            malloc_indent.append([])
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
                            malloc_indent.append([])
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
                            if flc := find_last_char(gen[2], {' with '}):
                                cify(gen[2][flc[0]:])
                                gen_do = cify(gen[1])
                                gen_where = cify(gen[2][:flc[0]])
                            else:
                                flc = [-1, 0]
                                gen_do = cify(gen[1])
                                gen_where = cify(gen[2])
                            c_code.append('\t' * indentation + f'if ({gen_where[0]}) ' + '{' + f'{file}___{c_var_name}++' + '; //len}')
                            close_where_loops(starting_where_loops)
                            c_code.insert(bef_loop_s, '\t' * indentation + f'{datatype_to_c[gen_do[1]]} {file}___{c_var_name} = 0;')
                            return [f'{file}___{c_var_name}', gen_do[1]]
                        else:
                            attrs = cify_attrs(expr[2])[0]
                            c_code.append('\t' * indentation + f'{file}___{c_var_name}++; //len')
                            close_where_loops(starting_where_loops)
                            c_code.insert(bef_loop_s, '\t' * indentation + f'{datatype_to_c[attrs[1]]} {file}___{c_var_name} = 0;')
                            return [f'{file}___{c_var_name}', attrs[1]]
                    case 'product':
                        bef_loop_s = len(c_code)
                        starting_where_loops = len(where_loops)
                        c_var_name = f'___o_l{bonus_c_variables["___o_l"]}'
                        bonus_c_variables['___o_l'] += 1
                        if (gennot := re.match(r'^\s*(.*)where(.*)\s*$', expr[2])) and (splf := find_last_char(expr[2], {' where '})) and never_leaves(expr[2]):  #generator
                            gen = [0, expr[2][:splf[0]], expr[2][splf[0]+6:]]
                            if flc := find_last_char(gen[2], {' with '}):
                                cify(gen[2][flc[0]:])
                                gen_do = cify(gen[1])
                                gen_where = cify(gen[2][:flc[0]])
                            else:
                                flc = [-1, 0]
                                gen_do = cify(gen[1])
                                gen_where = cify(gen[2])
                            c_code.append('\t' * indentation + f'if ({gen_where[0]}) ' + '{' + f'{file}___{c_var_name} *= {gen_do[0]}' + ';} //product')
                            close_where_loops(starting_where_loops)
                            c_code.insert(bef_loop_s, '\t' * indentation + f'{datatype_to_c[gen_do[1]]} {file}___{c_var_name} = 1;')
                            return [f'{file}___{c_var_name}', gen_do[1]]
                        else:
                            attrs = cify_attrs(expr[2])[0]
                            c_code.append('\t' * indentation + f'{file}___{c_var_name} *= {attrs[0]}; //product')
                            close_where_loops(starting_where_loops)
                            c_code.insert(bef_loop_s, '\t' * indentation + f'{datatype_to_c[attrs[1]]} {file}___{c_var_name} = 1;')
                            return [f'{file}___{c_var_name}', attrs[1]]
                    case 'any':
                        bef_loop_s = len(c_code)
                        starting_where_loops = len(where_loops)
                        c_var_name = f'___o_l{bonus_c_variables["___o_l"]}'
                        bonus_c_variables['___o_l'] += 1
                        if (gennot := re.match(r'^\s*(.*)where(.*)\s*$', expr[2])) and (splf := find_last_char(expr[2], {' where '})) and never_leaves(expr[2]):  #generator
                            gen = [0, expr[2][:splf[0]], expr[2][splf[0]+6:]]
                            if flc := find_last_char(gen[2], {' with '}):
                                cify(gen[2][flc[0]:])
                                gen_do = cify(gen[1])
                                gen_where = cify(gen[2][:flc[0]])
                            else:
                                flc = [-1, 0]
                                gen_do = cify(gen[1])
                                gen_where = cify(gen[2])
                            label_name = f'___lbl{bonus_c_variables["___lbl"]}'
                            bonus_c_variables["___lbl"] += 1
                            c_code.append('\t' * indentation + f'if ({gen_where[0]} && {gen_do[0]}) ' + '{' + f'{file}___{c_var_name} = 1; goto {label_name};'+'} //any')
                            close_where_loops(starting_where_loops)
                            c_code.append(f'{label_name}:')
                            c_code.insert(bef_loop_s, '\t' * indentation + f'{datatype_to_c[gen_do[1]]} {file}___{c_var_name} = 0;')
                            return [f'{file}___{c_var_name}', 'Z']
                        else:
                            attrs = cify_attrs(expr[2])[0]
                            label_name = f'___lbl{bonus_c_variables["___lbl"]}'
                            bonus_c_variables["___lbl"] += 1
                            c_code.append('\t' * indentation + f'if ({attrs[0]}) ' + '{' + f'{file}___{c_var_name} = 1; goto {label_name};'+'} //any')
                            close_where_loops(starting_where_loops)
                            c_code.append(f'{label_name}:')
                            c_code.insert(bef_loop_s, '\t' * indentation + f'{datatype_to_c[attrs[1]]} {file}___{c_var_name} = 0;')
                            return [f'{file}___{c_var_name}', 'Z']
                    case 'none':
                        bef_loop_s = len(c_code)
                        starting_where_loops = len(where_loops)
                        c_var_name = f'___o_l{bonus_c_variables["___o_l"]}'
                        bonus_c_variables['___o_l'] += 1
                        if (gennot := re.match(r'^\s*(.*)where(.*)\s*$', expr[2])) and (splf := find_last_char(expr[2], {' where '})) and never_leaves(expr[2]):  #generator
                            gen = [0, expr[2][:splf[0]], expr[2][splf[0]+6:]]
                            if flc := find_last_char(gen[2], {' with '}):
                                cify(gen[2][flc[0]:])
                                gen_do = cify(gen[1])
                                gen_where = cify(gen[2][:flc[0]])
                            else:
                                flc = [-1, 0]
                                gen_do = cify(gen[1])
                                gen_where = cify(gen[2])
                            label_name = f'___lbl{bonus_c_variables["___lbl"]}'
                            bonus_c_variables["___lbl"] += 1
                            c_code.append('\t' * indentation + f'if ({gen_where[0]} && {gen_do[0]}) ' + '{' + f'{file}___{c_var_name} = 0; goto {label_name};' + '} //none')
                            close_where_loops(starting_where_loops)
                            c_code.append(f'{label_name}:')
                            c_code.insert(bef_loop_s, '\t' * indentation + f'{datatype_to_c[gen_do[1]]} {file}___{c_var_name} = 1;')
                            return [f'{file}___{c_var_name}', 'Z']
                        else:
                            attrs = cify_attrs(expr[2])[0]
                            label_name = f'___lbl{bonus_c_variables["___lbl"]}'
                            bonus_c_variables["___lbl"] += 1
                            c_code.append('\t' * indentation + f'if ({attrs[0]}) ' + '{' + f'{file}___{c_var_name} = 0; goto {label_name};' + '} //none')
                            close_where_loops(starting_where_loops)
                            c_code.append(f'{label_name}:')
                            c_code.insert(bef_loop_s, '\t' * indentation + f'{datatype_to_c[attrs[1]]} {file}___{c_var_name} = 1;')
                            return [f'{file}___{c_var_name}', 'Z']
                    case 'all':
                        bef_loop_s = len(c_code)
                        starting_where_loops = len(where_loops)
                        c_var_name = f'___o_l{bonus_c_variables["___o_l"]}'
                        bonus_c_variables['___o_l'] += 1
                        if (gennot := re.match(r'^\s*(.*)where(.*)\s*$', expr[2])) and (splf := find_last_char(expr[2], {' where '})) and never_leaves(expr[2]):  #generator
                            gen = [0, expr[2][:splf[0]], expr[2][splf[0]+6:]]
                            if flc := find_last_char(gen[2], {' with '}):
                                cify(gen[2][flc[0]:])
                                gen_do = cify(gen[1])
                                gen_where = cify(gen[2][:flc[0]])
                            else:
                                flc = [-1, 0]
                                gen_do = cify(gen[1])
                                gen_where = cify(gen[2])
                            label_name = f'___lbl{bonus_c_variables["___lbl"]}'
                            bonus_c_variables["___lbl"] += 1
                            c_code.append('\t' * indentation + f'if (!({gen_where[0]} && {gen_do[0]})) ' + '{' + f'{file}___{c_var_name} = 0; goto {label_name};' + '} //all')
                            close_where_loops(starting_where_loops)
                            c_code.append(f'{label_name}:')
                            c_code.insert(bef_loop_s, '\t' * indentation + f'{datatype_to_c[gen_do[1]]} {file}___{c_var_name} = 1;')
                            return [f'{file}___{c_var_name}', 'Z']
                        else:
                            attrs = cify_attrs(expr[2])[0]
                            label_name = f'___lbl{bonus_c_variables["___lbl"]}'
                            bonus_c_variables["___lbl"] += 1
                            c_code.append('\t' * indentation + f'if (!({attrs[0]})) ' + '{' + f'{file}___{c_var_name} = 0; goto {label_name};' + '} //all')
                            close_where_loops(starting_where_loops)
                            c_code.append(f'{label_name}:')
                            c_code.insert(bef_loop_s, '\t' * indentation + f'{datatype_to_c[attrs[1]]} {file}___{c_var_name} = 1;')
                            return [f'{file}___{c_var_name}', 'Z']
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
                                seq_loops.append(value)
                                c_code.append('\t' * indentation + f'for (int {file}___{c_var_name}___l1 = 0; 1; {file}___{c_var_name}___l1++) ' + '{')
                                indentation += 1
                                c_code.append('\t' * indentation + f'{file}___{c_var_name} = {file}___{value}({file}___{c_var_name}___l1);')
                                key = expr[2][expr[2].index(':') + 1:]
                                attrs = cify_attrs(value)[0]
                                key = cify(key)
                                label_name = f'___lbl{bonus_c_variables["___lbl"]}'
                                bonus_c_variables["___lbl"] += 1
                                c_code.append('\t' * indentation + f'if ({key[0]}) goto {label_name}; //first')
                                close_where_loops(starting_where_loops)
                                c_code.insert(bef_loop_s, '\t' * indentation + f'{datatype_to_c[attrs[1]]} {file}___{c_var_name} = 0;')
                                seq_loops.pop()
                                indentation -= 1
                                c_code.append('\t' * indentation + '}')
                                c_code.append(f'{label_name}:')
                                return [f'{file}___{c_var_name}', attrs[1]]
                            elif value.split('in')[1].strip() == 'N':
                                variables[value.split('in')[0].strip()] = 'Z'
                                c_var_name = f'{value.split("in")[0].strip()}'
                                c_code.append('\t' * indentation + f'for ({file}___{c_var_name} = 0; 1; {file}___{c_var_name}++) ' + '{')
                                indentation += 1
                                key = expr[2][expr[2].index(':') + 1:]
                                attrs = cify_attrs(value)[0]
                                key = cify(key)
                                label_name = f'___lbl{bonus_c_variables["___lbl"]}'
                                bonus_c_variables["___lbl"] += 1
                                c_code.append('\t' * indentation + f'if ({key[0]}) goto {label_name}; //first')
                                close_where_loops(starting_where_loops)
                                c_code.insert(bef_loop_s, '\t' * indentation + f'int64_t {file}___{c_var_name} = 0;')
                                indentation -= 1
                                c_code.append('\t' * indentation + '}')
                                c_code.append(f'{label_name}:')
                                return [f'{file}___{c_var_name}', 'Z']
                    case 'average':
                        bef_loop_s = len(c_code)
                        starting_where_loops = len(where_loops)
                        c_var_name = f'___o_l{bonus_c_variables["___o_l"]}'
                        c_count_name = f'___o_l{bonus_c_variables["___o_l"]}_counter'
                        bonus_c_variables['___o_l'] += 1
                        if (gennot := re.match(r'^\s*(.*)where(.*)\s*$', expr[2])) and (splf := find_last_char(expr[2], {' where '})) and never_leaves(expr[2]):  #generator
                            gen = [0, expr[2][:splf[0]], expr[2][splf[0]+6:]]
                            if flc := find_last_char(gen[2], {' with '}):
                                cify(gen[2][flc[0]:])
                                gen_do = cify(gen[1])
                                gen_where = cify(gen[2][:flc[0]])
                            else:
                                flc = [-1, 0]
                                gen_do = cify(gen[1])
                                gen_where = cify(gen[2])
                            c_code.append('\t' * indentation + f'if ({gen_where[0]}) ' + '{' + f'{file}___{c_var_name} += {gen_do[0]}; {c_count_name}++' + ';} //average')
                            close_where_loops(starting_where_loops)
                            c_code.insert(bef_loop_s, '\t' * indentation + f'{datatype_to_c[gen_do[1]]} {file}___{c_var_name} = 0;')
                            c_code.insert(bef_loop_s, '\t' * indentation + f'int {c_count_name} = 0;')
                            return [f'((float) {file}___{c_var_name} / {c_count_name})', 'R']
                        else:
                            attrs = cify_attrs(expr[2])[0]
                            c_code.append('\t' * indentation + f'{file}___{c_var_name} += {attrs[0]}; {c_count_name}++; //average')
                            close_where_loops(starting_where_loops)
                            c_code.insert(bef_loop_s, '\t' * indentation + f'{datatype_to_c[attrs[1]]} {file}___{c_var_name} = 0;')
                            c_code.insert(bef_loop_s, '\t' * indentation + f'int {c_count_name} = 0;')
                            return [f'(float) {file}___{c_var_name} / {c_count_name}', 'R']
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
                            malloc_indent.append([])
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
                    case 'time':
                        return ['current_time()', 'R']
                    case 'pair':
                        cify_attrs(expr[2], manual_pair=True)
                        return 'pair'
                    case 'input':
                        c_var_name = f"___i_v{bonus_c_variables['___i_v']}"
                        datatype = expr[2].strip()
                        bonus_c_variables['___i_v'] += 1
                        c_code.append('\t' * indentation + f'{datatype_to_c[datatype]} {file}___{c_var_name}{"" if datatype in {"R", "Z"} else f" = malloc(sizeof({datatype_to_c[datatype][:-1]}));"}')
                        c_code.append('\t' * indentation + f'scanf("{percent_print[datatype]}", {decomp_scan[datatype](f"{file}___{c_var_name}")});')
                        return [f'{file}___{c_var_name}', datatype]
                    case 'int':
                        return [f'((int) {cify(expr[2])[0]})', 'Z']
            elif fun in structs: #struct
                bcv = f'___s_p{bonus_c_variables["___s_p"]}'
                bonus_c_variables["___s_p"] += 1
                c_code.append('\t'*indentation + f'{fun} ___s_p{bcv} = '+'{'+f'{", ".join(f".{i[0][0]} = {i[0][1]}" for i in cify_attrs(expr[2], True))}'+'};')
                c_code.append('\t'*indentation + f'{fun}* ___s_p{bcv}_1 = malloc(sizeof({fun}));')
                variables[f'___s_p{bcv}_1'] = fun
                malloc_indent[-1].append(['struct', f'___s_p{bcv}_1'])
                c_code.append('\t'*indentation + f'memcpy(___s_p{bcv}_1, &___s_p{bcv}, sizeof({fun}));')
                return [f'___s_p{bcv}_1', fun]
            elif fun in functions: #function call
                if functions[fun].startswith('{'):
                    starting_where_loops = len(where_loops)
                    attrs = cify_attrs(expr[2], function=fun)
                    c_var_name = f'___o_s{bonus_c_variables["___o_s"]}'
                    malloc_indent[-1].append(['list', c_var_name])
                    malloc_indent.append([])
                    variables[c_var_name] = functions[fun]
                    where_loops.append(c_var_name)
                    c_code.append('\t' * indentation + f'list* {file}___{c_var_name} = {fun}({", ".join(i[0] for i in attrs)});')
                    c_code.append('\t' * indentation + f'for (int {file}___{c_var_name}___l1 = 0; {file}___{c_var_name}___l1 < {file}___{c_var_name}->cur_size; {file}___{c_var_name}___l1++) ' + '{')
                    indentation += 1
                    c_code.append('\t' * indentation + f'{datatype_to_c[functions[fun]]} {file}___{c_var_name}___l2 = getitem({file}___{c_var_name}, {file}___{c_var_name}___l1).{datatype_to_quant[functions[fun]]};')
                    return [f'{file}___{c_var_name}___l2', functions[fun][1:-1]]
                else:
                    starting_where_loops = len(where_loops)
                    attrs = cify_attrs(expr[2], function=fun)
                    return [f'{fun}({", ".join(i[0] for i in attrs)})', functions[fun]]
            elif fun == line[1]:
                print(f'Error: Cannot use type inference on recursive functions on line {h0+1}:')
                print(h)
                exit()
        elif expression.startswith('with '): #inline variable
            pairs = cify_attrs(expression[5:], inline_vars = True)
            return 'inline variable'
        elif lc1 := find_last_char(expression, {' with '}): #inline variable
            cify(expression[lc1[0]:])
            return cify(expression[:lc1[0]])
        elif expr := re.match(r'^\s*(.+)\?(.+):(.+)\s*$', expression): #ternary
            lc1 = find_last_char(expression, {'?'})
            lc2 = find_last_char(expression, {':'})
            a = cify(expression[:lc1[0] - 1])
            b = cify(expression[lc1[0]:lc2[0] - 1])
            c = cify(expression[lc2[0]:])
            if (c[1] == 'R' and b[1] == 'Z') or (c[1] == 'Z' and b[1] == 'R'):
                return [f'({a[0]} ? (double) {b[0]} : (double) {c[0]})', 'R']
            elif c[1] != b[1]:
                print(f'Error when compiling expression at line {h0 + 1}:')
                print(code[h0])
                print(f'Error in expression: {expression}')
                print(f'Ternary operator returns ambiguous datatype: {b[1]}, {c[1]}')
                exit(1)
            return [f'({a[0]} ? {b[0]} : {c[0]})', c[1]]
        elif lc1 := find_last_char(expression, {':'}): #pair
            if only_second_parts:
                return [[expression[:lc1[0] - 1], f'{(b := cify(expression[lc1[0]:]))[0]}'], [b[1]]]
            else:
                return [[f'{(a := cify(expression[:lc1[0] - 1]))[0]}', f'{(b := cify(expression[lc1[0]:]))[0]}'], [a[1], b[1]]]
        elif lc1 := find_last_char(expression, {' as '}): #with as pair inline variable
            if not in_with:
                if ' in ' in expression[lc1[0]:]:
                    starting_where_loops = len(where_loops)
                    var_name = expression[lc1[0]:][3:expression[lc1[0]:].index(' in ')].strip()
                    variables[var_name] = expression[lc1[0]:][expression[lc1[0]:].index(' in ')+4:].strip()
                    in_as.append(var_name)
                    where_loops = where_loops[:starting_where_loops] + ['' for i in where_loops[starting_where_loops:]]
                    cified = cify(expression[:lc1[0]], direct_in_as=True, manual_pair=True, in_with=in_with)
                    variables[var_name] = cified[1]
                    c_code.append('\t' * indentation + f'{datatype_to_c[cified[1]]} {file}___{var_name} = {cified[0]}; //inline variable')
                    return cify(var_name, manual_pair=True, in_with=in_with)
                else:
                    starting_where_loops = len(where_loops)
                    var_name = expression[lc1[0]+3:].strip()
                    b = cify(expression[:lc1[0]], direct_in_as=True, manual_pair=True, in_with=in_with)
                    variables[var_name] = b[1]
                    in_as.append(var_name)
                    where_loops = where_loops[:starting_where_loops] + ['' for i in where_loops[starting_where_loops:]]
                    cified = cify(expression[:lc1[0]], direct_in_as=True, manual_pair=True, in_with=in_with)
                    variables[var_name] = cified[1]
                    c_code.append('\t' * indentation + f'{datatype_to_c[cified[1]]} {file}___{var_name} = {cified[0]}; //inline variable')
                    return cify(var_name, manual_pair=True, in_with=in_with)
            else:
                if ' in ' in expression[lc1[0]:]:
                    starting_where_loops = len(where_loops)
                    var_name = expression[lc1[0]:][3:expression[lc1[0]:].index(' in ')].strip()
                    variables[var_name] = expression[lc1[0]:][expression[lc1[0]:].index(' in ')+4:].strip()
                    in_as.append(var_name)
                    where_loops = where_loops[:starting_where_loops] + ['' for i in where_loops[starting_where_loops:]]
                    return [[f'{(b := cify(expression[:lc1[0]], direct_in_as=True))[0]}', var_name], [b[1]], 'as']
                else:
                    starting_where_loops = len(where_loops)
                    var_name = expression[lc1[0]+3:].strip()
                    b = cify(expression[:lc1[0]], direct_in_as=True)
                    variables[var_name] = b[1]
                    in_as.append(var_name)
                    where_loops = where_loops[:starting_where_loops] + ['' for i in where_loops[starting_where_loops:]]
                    return [[f'{(b)[0]}', var_name], [b[1]], 'as']
        elif lc1 := find_last_char(expression, {' in '}): #of type
            return [expression[:lc1[0]].strip(), expression[lc1[0]+3:].strip()]
        elif lc := find_last_char(expression, {'&&', '||'}):
            return [f'({cify(expression[:lc[0]-len(lc[1])])[0]} {lc[1]} {cify(expression[lc[0]+1:])[0]})', 'Z']
        elif expr := re.match(r'^\s*!(.*)\s*$', expression):  #not
            return [f'(!{cify(expr[1])[0]})', 'Z']
        elif lc := find_last_char(expression, {'==', '<', '>', '<=', '>=', '!='}):
            return [f'({cify(expression[:lc[0]-len(lc[1])])[0]} {lc[1]} {cify(expression[lc[0]+1:])[0]})', 'Z']
        elif lc := find_last_char(expression, {'++'}):
            starting_where_loops = len(where_loops)
            #c_var_name = f'___c_h{bonus_c_variables["___c_h"]}'
            #bonus_c_variables['___c_h'] += 1
            #c_code.append('\t' * indentation + f'list* {file}___{c_var_name} = make_list();')
            #malloc_indent[starting_where_len].append(['list', c_var_name])
            #c_code.append('\t' * indentation + f'append({file}___{c_var_name}, {to_quant(copy_struct(a:=cify(expression[:lc[0]-2])))}); //concatenation')
            #close_where_loops(starting_where_loops)
            c_var_name = (a:=sum_up(expression[:lc[0]-2]))[0] #No main___ used, it is already returned in sum_up
            c_code.append('\t' * indentation + f'append({c_var_name}, {to_quant(copy_struct(b:=cify(expression[lc[0]+1:])))}); //concatenation')
            close_where_loops(starting_where_loops)
            variables[c_var_name] = a[1]
            if a[1] != b[1]:
                print(f'Error when compiling expression at line {h0 + 1}:')
                print(code[h0])
                print(f'Error in expression: {expression}')
                print(f'Concatenation operator used on 2 different datatypes: {a[1]}, {b[1]}')
                exit(1)
            where_loops.append(c_var_name)
            malloc_indent.append([])
            c_code.append('\t' * indentation + f'for (int {c_var_name}___l1 = 0; {c_var_name}___l1 < {c_var_name}->cur_size; {c_var_name}___l1++) ' + '{')
            indentation += 1
            c_code.append('\t' * indentation + f'{datatype_to_c[variables[c_var_name]]} {c_var_name}___l2 = getitem({c_var_name}, {c_var_name}___l1).{datatype_to_quant[variables[c_var_name]]};')
            return [f'{c_var_name}___l2', variables[c_var_name]]
        elif (lc := find_last_char(expression, {'+', '-'})) and not (re.match(r'^\s*-(.*)\s*$', expression)):
            return [f'({(a:=cify(expression[:lc[0]-1]))[0]} {lc[1]} {(b:=cify(expression[lc[0]:]))[0]})', 'R' if 'R' in (a[1], b[1]) else 'Z']
        elif lc := find_last_char(expression, {'*', '/', '//', '%', '!%'}, excluding={'**'}):
            if lc[1] == '!%' or (lc[1] == '%' and (flc := find_last_char(expression, {'!%'})) and flc[0] + 1 == lc[0]):
                b = cify(expression[lc[0]:])
                if debug:
                    c_code.append('\t' * indentation + f'if ((int64_t) {b[0]} == 0) ' + '{')
                    indentation += 1
                    c_code.append('\t' * indentation + f'printf("Runtime error on line {h0 + 1}: division by 0\\n");')
                    error_print_function_stack()
                    indentation -= 1
                    c_code.append('\t' * indentation + f'exit(1);')
                    c_code.append('\t' * indentation + '}')
                return [f'(!((int64_t) {(a := cify(expression[:lc[0] - 2]))[0]} % (int64_t) {b[0]}))', 'R' if 'R' in (a[1], b[1]) else 'Z']
            elif lc[1] == '%':
                b = cify(expression[lc[0]:])
                if debug:
                    c_code.append('\t' * indentation + f'if ((int64_t) {b[0]} == 0) ' + '{')
                    indentation += 1
                    c_code.append('\t' * indentation + f'printf("Runtime error on line {h0 + 1}: division by 0\\n");')
                    error_print_function_stack()
                    indentation -= 1
                    c_code.append('\t' * indentation + f'exit(1);')
                    c_code.append('\t' * indentation + '}')
                return [f'((int64_t) {cify(expression[:lc[0] - 1])[0]} % (int64_t) {b[0]})', 'Z']
            elif lc[1] == '//' or (lc[1] == '/' and (flc := find_last_char(expression, {'//'})) and flc[0] + 1 == lc[0]):
                b = cify(expression[lc[0]:])
                if debug:
                    c_code.append('\t' * indentation + f'if ((int64_t) {b[0]} == 0) ' + '{')
                    indentation += 1
                    c_code.append('\t' * indentation + f'printf("Runtime error on line {h0 + 1}: division by 0\\n");')
                    error_print_function_stack()
                    indentation -= 1
                    c_code.append('\t' * indentation + f'exit(1);')
                    c_code.append('\t' * indentation + '}')
                return [f'((int64_t) {(a := cify(expression[:lc[0] - 2]))[0]} / (int64_t) {b[0]})', 'Z']
            elif lc[1] == '/':
                b = cify(expression[lc[0]:])
                if debug:
                    c_code.append('\t' * indentation + f'if ((int64_t) {b[0]} == 0) ' + '{')
                    indentation += 1
                    c_code.append('\t' * indentation + f'printf("Runtime error on line {h0 + 1}: division by 0\\n");')
                    error_print_function_stack()
                    indentation -= 1
                    c_code.append('\t' * indentation + f'exit(1);')
                    c_code.append('\t' * indentation + '}')
                return [f'((float) {(a := cify(expression[:lc[0] - 2]))[0]} / {b[0]})', 'R']
            else:
                return [f'({(a := cify(expression[:lc[0] - 1]))[0]} {lc[1]} {(b := cify(expression[lc[0]:]))[0]})', 'R' if 'R' in (a[1], b[1]) else 'Z']
        elif lc := find_last_char(expression, {'**'}):
            return [f'(pow({(a := cify(expression[:lc[0] - 1]))[0]}, {(b := cify(expression[lc[0]+1:]))[0]}))', 'R' if 'R' in (a[1], b[1]) else 'Z']
        elif expr := re.match(r'^\s*-(.*)\s*$', expression): #negation
            return [f'(-({(a:=cify(expr[1]))[0]}))', a[1]]
        elif expr := re.match(r'^\s*(.*)°\s*$', expression): #degrees
            return [f'(({(a:=cify(expr[1]))[0]}/180.0)*M_PI)', 'R']
        elif expr := re.match(r'^\s*(\w+)\s*\[(.*)]\s*$', expression):  #getitem
            container = cify(expr[1])
            if container[1].endswith('.'):
                return [f'{container[0]}({cify(expr[2])[0]})', container[1][:-1]]
        elif expr := re.match(r'^\s*(.*)\s*\.\s*(\w+)\s*$', expression):  #getattr
            container = cify(expr[1])
            element = expr[2].strip()
            if container[1].startswith('{'):
                cified = cify(container[0])
                return [f'(({cified[1]}) {cified[0]})->{element}', structs[container[1][1:-1]][element]]
            else:
                return [f'{container[0]}->{element}', structs[container[1]][element]]
        elif expr := re.match(r'^\s*\((.*)\)\s*$', expression):  #unneccessary parentheses
            return cify(expr[1])
        print(f'Error when compiling expression at line {h0+1}:')
        print(code[h0])
        print(f'Error in expression: {expression}')
        exit(1)

    code = []
    last_true_line = 0
    inside_start = 0
    running = ''
    run_start = 0
    for i0, i in enumerate(no_comment_code):
        inside_start = in_paranth(i, inside_start)
        running += i + ' '
        if not inside_start:
            code.append(running[:-1])
            running = ''
            run_start = i0 + 1
        elif inside_start < 0:
            print(f"Error: closing parentheses doesn't have a pair on line {i0+1}:")
            print(commented_code[i0])
            exit()
    if running:
        print(f'Error: parentheses was never closed on line {run_start+1}:')
        print(commented_code[run_start])
        exit()

    for h0, h in enumerate(code):
        for i in malloc_needs_free:
            c_code.append('\t'*indentation + f'free({i[0]});')
        malloc_needs_free = []
        close_where_loops(overall_indent)
        starting_where_len = 0
        if line := re.match(r'^\s*(print)\s+(.*)', h): #print statement
            bef_loop = len(c_code)
            cified_line = cify(line[2])
            if len(where_loops) > overall_indent:
                c_var_name = f'___p_s{bonus_c_variables["___p_s"]}'
                bonus_c_variables['___p_s'] += 1
                c_code.insert(bef_loop, '\t' * indentation + f'list* {file}___{c_var_name} = make_list();')
                c_code.append('\t' * indentation + f'append({file}___{c_var_name}, {to_quant(copy_struct(cified_line))}); //print')
                close_where_loops(overall_indent)
                c_code.append('\t' * indentation + 'printf("{");')
                c_code.append('\t' * indentation + f'for (int {file}___{c_var_name}_1 = 0; {file}___{c_var_name}_1 < {file}___{c_var_name}->cur_size; {file}___{c_var_name}_1++) '+'{')
                stuff_to_print = f'getitem({file}___{c_var_name}, {file}___{c_var_name}_1).{datatype_to_quant[cified_line[1]]}'
                c_code.append('\t' * (indentation+1) + f'printf("{percent_print[cified_line[1]]}", {decomp_print[cified_line[1]](stuff_to_print)});')
                c_code.append('\t' * (indentation+1) + f'if ({file}___{c_var_name}_1 != {file}___{c_var_name}->cur_size-1) printf(", ");')
                c_code.append('\t' * indentation + '}')
                close_where_loops(overall_indent)
                c_code.append('\t' * indentation + 'printf("}\\n");')
                c_code.append('\t' * indentation + f'destroy_list({file}___{c_var_name});')
            elif cified_line[1].endswith('.'):
                stuff_to_print = f'{cified_line[0]}(___l_var)'
                c_code.append('\t' * indentation + f'for (int ___l_var = 0; ___l_var < 16; ___l_var++) printf("{(ptp:=percent_print[cified_line[1][:-1]])}, ", {decomp_print[cified_line[1][:-1]](stuff_to_print)});')
                c_code.append('\t' * indentation + f'printf("{ptp}...\\n", {cified_line[0]}(16));')
            else:
                c_code.append('\t' * indentation + f'printf("{percent_print[cified_line[1]]}\\n", {decomp_print[cified_line[1]](cified_line[0])});')
        elif line := re.match(r'^\s*struct\s+(.*)\s*=\s*\[(.*)]\s*$', h): #struct creation
            struct_name = line[1].strip()
            structs[line[1].strip()] = {i[0]:i[1] for i in cify_attrs(line[2])}
            struct_original_order[line[1].strip()] = [i[0] for i in cify_attrs(line[2])]
            percent_print[line[1].strip()] = f'{line[1].strip()}({", ".join(i+": "+percent_print[structs[line[1].strip()][i]] for i in struct_original_order[line[1].strip()])})'
            decomp_print[line[1].strip()] = (lambda line_val: lambda x: ", ".join(decomp_print[structs[line_val][i]](f'(({line_val}*) {x})->{i}') for i in struct_original_order[line_val]))(line[1].strip())
            decomp_scan[line[1].strip()] = (lambda line_val: lambda x: ", ".join(decomp_print[structs[line_val][i]](f'&((({line_val}*) {x})->{i})') for i in struct_original_order[line_val]))(line[1].strip())
            c_code.append('\t' * indentation + 'typedef struct {')
            for i0 in structs[line[1].strip()]:
                variables[f'{line[1].strip()}{i0}'] = structs[line[1].strip()][i0]
                c_code.append('\t' * (indentation+1) + f'{datatype_to_c[structs[line[1].strip()][i0]]} {i0};')
            c_code.append('\t' * indentation + '} ' + f'{line[1].strip()};')
            datatype_to_c[line[1].strip()] = f'{line[1].strip()}*'
            datatype_to_c['{' + line[1].strip() + '}'] = f'{line[1].strip()}*'
            datatype_to_quant[line[1].strip()] = 's'
            datatype_to_quant['{' + line[1].strip() + '}'] = 's'
        elif old_line := re.match(r'^\s*def\s+(\w+)\s*\((.*?)\)\s+in\s*(.*)\s*=>\s*(.*)$', h): #function definition
            line = [old_line[0], old_line[1], old_line[2], old_line[4], old_line[3]]
            functions[line[1]] = line[4].strip()
            malloc_indent.append([])
            inps = {i[0]:i[1] for i in cify_attrs(line[2])}
            c_code.append('\t' * indentation + f'{datatype_real_c(line[4].strip())} {line[1]}({", ".join(f"{datatype_real_c(inps[i0])} {file}___{i0}" for i0 in inps)})' +' {')
            function_parameters[line[1]] = [inps[i] for i in inps]
            for i0 in inps:
                variables[i0] = inps[i0]
            indentation += 1
            if debug:
                quanted = to_quant([f'"{line[1].strip()}"', "Str"])
                c_code.append('\t' * indentation + f'append(___debug_function_stack, {quanted});')
            if line[4].strip().startswith('{'):
                c_code.append('\t' * indentation + f'list* ___outp = make_list();')
            outp = cify(line[3])
            copied = copy_struct(outp)
            if debug:
                c_code.append('\t' * indentation + f'___debug_function_stack->cur_size -= 1;')
            if not line[4].strip().startswith('{'):
                free_malloc_indent(malloc_indent.pop())
                c_code.append('\t' * indentation + f'return {copied[0]};')
            else:
                c_code.append('\t' * indentation + f'append(___outp, {to_quant(copied)});')
                close_where_loops(overall_indent)
                free_malloc_indent(malloc_indent.pop())
                c_code.append('\t' * indentation + f'return ___outp;')
            indentation -= 1
            c_code.append('\t' * indentation + '}')
        elif old_line := re.match(r'^\s*def\s+(\w+)\s*\((.*?)\)\s*=>\s*(.*)$', h): #function definition type inference
            line = [old_line[0], old_line[1], old_line[2], old_line[3]]
            malloc_indent.append([])
            inps = {i[0]:i[1] for i in cify_attrs(line[2])}
            bef_def = len(c_code)
            #c_code.append('\t' * indentation + f'{datatype_to_c[line[4].strip()]} {line[1]}({", ".join(f"{datatype_to_c[inps[i0]]} {i0}" for i0 in inps)})' +' {')
            function_parameters[line[1]] = [inps[i] for i in inps]
            for i0 in inps:
                variables[i0] = inps[i0]
            indentation += 1
            if debug:
                quanted = to_quant([f'"{line[1].strip()}"', "Str"])
                c_code.append('\t' * indentation + f'append(___debug_function_stack, {quanted});')
            outp = cify(line[3])
            copied = copy_struct(outp)
            c_code.insert(bef_def, '\t' * indentation + f'{datatype_real_c(copied[1])} {line[1]}({", ".join(f"{datatype_real_c(inps[i0])} {file}___{i0}" for i0 in inps)})' +' {')
            free_malloc_indent(malloc_indent.pop())
            if debug:
                c_code.append('\t' * indentation + f'___debug_function_stack->cur_size -= 1;')
            c_code.append('\t' * indentation + f'return {copied[0]};')
            indentation -= 1
            c_code.append('\t' * indentation + '}')
            functions[line[1]] = copied[1]
        elif old_line := re.match(r'^\s*def\s+(\w+)\s*\((.*?)\)\s+in\s*(.*)\s*$', h): #multi-line function definition
            line = [old_line[0], old_line[1], old_line[2], '', old_line[3]]
            indentation_types.append(['def', overall_indent])
            functions[line[1]] = line[4].strip()
            malloc_indent.append([])
            inps = {i[0]:i[1] for i in cify_attrs(line[2])}
            c_code.append('\t' * indentation + f'{datatype_real_c(line[4].strip())} {line[1]}({", ".join(f"{datatype_real_c(inps[i0])} {file}___{i0}" for i0 in inps)})' +' {')
            function_parameters[line[1]] = [inps[i] for i in inps]
            for i0 in inps:
                variables[i0] = inps[i0]
            indentation += 1
            if debug:
                quanted = to_quant([f'"{line[1].strip()}"', "Str"])
                c_code.append('\t' * indentation + f'append(___debug_function_stack, {quanted});')
            where_loops.append('')
            overall_indent = len(where_loops)
            function_nests.append(line[1])
        elif old_line := re.match(r'^\s*def\s+(\w+)\s*\((.*?)\)\s*$', h): #multi-line function definition void
            line = [old_line[0], old_line[1], old_line[2]]
            indentation_types.append(['vdef', overall_indent, line[1]])
            functions[line[1]] = 'nil'
            malloc_indent.append([])
            inps = {i[0]:i[1] for i in cify_attrs(line[2])}
            bef_def = len(c_code)
            c_code.append('\t' * indentation + f'void {line[1]}({", ".join(f"{datatype_real_c(inps[i0])} {file}___{i0}" for i0 in inps)})' +' {')
            function_parameters[line[1]] = [inps[i] for i in inps]
            for i0 in inps:
                variables[i0] = inps[i0]
            indentation += 1
            if debug:
                quanted = to_quant([f'"{line[1].strip()}"', "Str"])
                c_code.append('\t' * indentation + f'append(___debug_function_stack, {quanted});')
            where_loops.append('')
            overall_indent = len(where_loops)
            function_nests.append(line[1])
        elif old_line := re.match(r'^\s*return (.*)$', h): #return statement
            if functions[function_nests[-1]].startswith('{'):
                outp = sum_up(old_line[1])
            else:
                outp = cify(old_line[1])
            copied = copy_struct(outp)
            if debug:
                c_code.append('\t' * indentation + f'___debug_function_stack->cur_size -= 1;')
            c_code.append('\t' * indentation + f'return {copied[0]};')
        elif old_line := re.match(r'^\s*end\s*$', h): #end statement
            match (it := indentation_types.pop())[0]:
                case 'loop' | 'while':
                    overall_indent = it[1]
                    close_where_loops(overall_indent)
                case 'def':
                    overall_indent = it[1]
                    close_where_loops(overall_indent)
                    function_nests.pop()
                case 'vdef':
                    if debug:
                        c_code.append('\t' * indentation + f'___debug_function_stack->cur_size -= 1;')
                    overall_indent = it[1]
                    close_where_loops(overall_indent)
                    function_nests.pop()
                case 'if' | 'elif' | 'else':
                    overall_indent = it[1]
                    close_where_loops(overall_indent)
                case 'check':
                    if debug:
                        c_code.append('if (___is_error_raised) exit(1);')
                    overall_indent = it[1]
                    close_where_loops(overall_indent)
                    if not debug:
                        c_code = c_code[:debug_only]
                    debug_only = -1
                case 'package':
                    overall_indent = it[1]
                    close_where_loops(0)
                    return (functions, function_parameters)
        elif old_line := re.match(r'^\s*loop\s+(.*)$', h): #looping
            indentation_types.append(['loop', overall_indent])
            cify('with ' + old_line[1])
            overall_indent = len(where_loops)
        elif old_line := re.match(r'^\s*while\s+(.*)$', h): #while looping
            indentation_types.append(['while', overall_indent])
            c_code.append('\t' * indentation + f'while ({cify(old_line[1])[0]})' + ' {')
            where_loops.append('')
            overall_indent = len(where_loops)
        elif old_line := re.match(r'^\s*if\s+(.*)$', h): #if statement
            indentation_types.append(['if', overall_indent])
            malloc_indent.append([])
            c_code.append('\t' * indentation + f'if ({cify(old_line[1])[0]})' + ' {')
            indentation += 1
            where_loops.append('')
            overall_indent = len(where_loops)
        elif old_line := re.match(r'^\s*elif\s+(.*)$', h): #elif statement
            overall_indent = indentation_types.pop()[1]
            close_where_loops(overall_indent)
            indentation_types.append(['elif', overall_indent])
            malloc_indent.append([])
            c_code.append('\t' * indentation + f'else if ({cify(old_line[1])[0]})' + ' {')
            indentation += 1
            where_loops.append('')
            overall_indent = len(where_loops)
        elif old_line := re.match(r'^\s*else\s*$', h): #else statement
            overall_indent = indentation_types.pop()[1]
            close_where_loops(overall_indent)
            indentation_types.append(['else', overall_indent])
            malloc_indent.append([])
            c_code.append('\t' * indentation + 'else {')
            indentation += 1
            where_loops.append('')
            overall_indent = len(where_loops)
        elif old_line := re.match(r'^\s*import\s+(\w+)\s*\.\s*(\w+)\s*$', h): #import package
            c_code.append('\t' * indentation + f'//start of {old_line[1]}.{old_line[2]}')
            imported = cify_all(old_line[1] + '.ube', old_line[2], indentation)
            for i in imported[0]:
                if i not in functions:
                    functions[i] = imported[0][i]
            for i in imported[1]:
                if i not in function_parameters:
                    function_parameters[i] = imported[1][i]
            c_code.append('\t' * indentation + f'//end of {old_line[1]}.{old_line[2]}')
        elif exprnot := re.match(r'^\s*(\w+)\s*\((.*)\)\s*$', h) and not find_pair(h)[2]: #function call
            expr = [0] + find_pair(h)
            fun = expr[1].strip()
            attrs = cify_attrs(expr[2], function=fun)
            c_code.append('\t' * indentation + f'{fun}({", ".join(i[0] for i in attrs)});')
        elif old_line := re.match(r'^\s*(.*)\[(.*)]\s+in\s+(.*)\s*=\s*(.*)', h): #variable creation - sequence
            datatype = old_line[3].replace(' ', '')
            in_where = True
            if flc := find_last_char(old_line[4], {' with '}):
                line = [old_line[0], old_line[1], old_line[2], old_line[3], old_line[4][:flc[0]], old_line[4][flc[0]+5:]]
            else:
                line = [old_line[0], old_line[1], old_line[2], old_line[3], old_line[4], '']
            c_x = line[2].strip()
            dict_name = f'{line[1].strip()}___d'
            malloc_indent[-1].append(['dict', dict_name])
            c_code.append('\t' * indentation + f'dict* {file}___{line[1].strip()}___d = make_dict();')
            c_code.append('\t' * indentation + f'{datatype_to_c[datatype]} {file}___{line[1].strip()}(int64_t {file}___{c_x}) ' + '{')
            tq = to_quant([f'{file}___{c_x}', 'Z'])
            c_code.append('\t' * indentation + f'\tif (dict_has({file}___{dict_name}, {tq})) ' + '{')
            c_code.append('\t' * indentation + f'\t\treturn dict_get({file}___{dict_name}, {tq}).{datatype_to_quant[datatype]};')
            c_code.append('\t' * indentation + '\t} else {')
            variables[line[2].strip()] = 'Z'
            variables[line[1].strip()] = f'{datatype}.'
            malloc_indent.append([])
            c_out = cify(line[4])
            indentation += 2
            c_code.append('\t' * indentation + f'{datatype_to_c[datatype]} ___outp = {c_out[0]};')
            copied = to_quant(copy_struct(["___outp", datatype]))
            for i in where_loops:
                free_malloc_indent(malloc_indent.pop())
            free_malloc_indent(malloc_indent.pop())
            c_code.append('\t' * indentation + f'return dict_set({file}___{dict_name}, {tq}, {copied}).{datatype_to_quant[datatype]};')
            indentation -= 1
            c_code.append('\t' * indentation + '}')
            indentation -= 1
            c_code.append('\t' * indentation + '}')
            for i in where_loops:
                indentation -= 1
                c_code.append('\t' * indentation + '}')
            if line[5]:
                for i in cify_attrs(line[5]): #pairs
                    c_code.append('\t' * indentation + f'dict_set({file}___{dict_name}, {to_quant([i[0][0], i[1][0]])}, {to_quant([i[0][1], i[1][1]])});')
                for i in where_loops:
                    indentation -= 1
                    c_code.append('\t' * indentation + '}')
            where_loops = []
        elif oldest_line := re.match(r'^\s*(.*)\[(.*)]\s*:=\s*(.*)', h): #variable creation - sequence inference
            old_line = [oldest_line[0], oldest_line[1], oldest_line[2], 0, oldest_line[3]]
            in_where = True
            if flc := find_last_char(old_line[4], {' with '}):
                line = [old_line[0], old_line[1], old_line[2], old_line[3], old_line[4][:flc[0]], old_line[4][flc[0]+5:]]
            else:
                line = [old_line[0], old_line[1], old_line[2], old_line[3], old_line[4], '']
            c_x = line[2].strip()
            dict_name = f'{line[1].strip()}___d'
            malloc_indent[-1].append(['dict', dict_name])
            c_code.append('\t' * indentation + f'dict* {file}___{line[1].strip()}___d = make_dict();')
            ins_1 = len(c_code)
            tq = to_quant([f'{file}___{c_x}', 'Z'])
            c_code.append('\t' * indentation + f'\tif (dict_has({file}___{dict_name}, {tq})) ' + '{')
            ins_2 = len(c_code)
            c_code.append('\t' * indentation + '\t} else {')
            variables[line[2].strip()] = 'Z'
            malloc_indent.append([])
            c_out = cify(line[4])
            indentation += 2
            datatype = c_out[1].replace(' ', '')
            c_code.insert(ins_2, '\t' * indentation + f'\t\treturn dict_get({file}___{dict_name}, {tq}).{datatype_to_quant[datatype]};')
            c_code.insert(ins_1, '\t' * indentation + f'{datatype_to_c[datatype]} {file}___{line[1].strip()}(int64_t {file}___{c_x}) ' + '{')
            c_code.append('\t' * indentation + f'{datatype_to_c[datatype]} ___outp = {c_out[0]};')
            copied = to_quant(copy_struct(["___outp", datatype]))
            for i in where_loops:
                free_malloc_indent(malloc_indent.pop())
            free_malloc_indent(malloc_indent.pop())
            c_code.append('\t' * indentation + f'return dict_set({file}___{dict_name}, {tq}, {copied}).{datatype_to_quant[datatype]};')
            variables[line[1].strip()] = f'{datatype}.'
            indentation -= 1
            c_code.append('\t' * indentation + '}')
            indentation -= 1
            c_code.append('\t' * indentation + '}')
            for i in where_loops:
                indentation -= 1
                c_code.append('\t' * indentation + '}')
            if line[5]:
                for i in cify_attrs(line[5]): #pairs
                    c_code.append('\t' * indentation + f'dict_set({file}___{dict_name}, {to_quant([i[0][0], i[1][0]])}, {to_quant([i[0][1], i[1][1]])});')
                for i in where_loops:
                    indentation -= 1
                    c_code.append('\t' * indentation + '}')
            where_loops = []
        elif line := re.match(r'^\s*(.*)\s+in\s+(.*)\s*=\s*\{(.*)where(.*)}', h): #variable creation - superposition comprehension
            datatype = line[2].replace(' ', '')
            variables[line[1].strip()] = '{' + datatype + '}'
            in_where = True
            if flc := find_last_char(line[4][1:-1], {' with '}):
                cify(line[4][flc[0]+1:])
                c_code.append('\t' * indentation + f'list* {file}___{line[1].strip()} = make_list();')
                malloc_indent[starting_where_len].append(['list', line[1].strip()])
                c_out = cify(line[3])
                c_con = cify(line[4][:flc[0]])
            else:
                flc = [-1, 0]
                c_code.append('\t' * indentation + f'list* {file}___{line[1].strip()} = make_list();')
                malloc_indent[starting_where_len].append(['list', line[1].strip()])
                c_out = cify(line[3])
                c_con = cify(line[4])
            c_code.append('\t' * indentation + f'if ({c_con[0]}) ' + '{append'+f'({file}___'+line[1].strip()+', '+to_quant(c_out)+');}')
            close_where_loops(overall_indent)
        elif old_line := re.match(r'^\s*(.*)\s*:=\s*\{(.*)where(.*)}', h): #variable creation - superposition comprehension inference
            line = [old_line[0], old_line[1], 0, old_line[2], old_line[3]]
            in_where = True
            if flc := find_last_char(line[4][1:-1], {' with '}):
                cify(line[4][flc[0]+1:])
                c_code.append('\t' * indentation + f'list* {file}___{line[1].strip()} = make_list();')
                malloc_indent[starting_where_len].append(['list', line[1].strip()])
                c_out = cify(line[3])
                c_con = cify(line[4][:flc[0]])
            else:
                flc = [-1, 0]
                c_code.append('\t' * indentation + f'list* {file}___{line[1].strip()} = make_list();')
                malloc_indent[starting_where_len].append(['list', line[1].strip()])
                c_out = cify(line[3])
                c_con = cify(line[4])
            c_code.append('\t' * indentation + f'if ({c_con[0]}) ' + '{append'+f'({file}___'+line[1].strip()+', '+to_quant(c_out)+');}')
            close_where_loops(overall_indent)
            datatype = c_out[1]
            variables[line[1].strip()] = '{' + datatype + '}'
        elif line := re.match(r'^\s*(.*)\s+in\s+(.*)\s*=\s*\{(.*)}\s*$', h): #variable creation - superposition
            datatype = line[2].replace(' ', '')
            if not re.match(r'\{\s*}', line[3].strip()):
                c_code.append('\t' * indentation + f'Quant ___b_a{bonus_c_variables["___b_a"]}[{line[3].count(",")+1}] = ' + '{' + ", ".join("{."+datatype_to_quant[i[1]]+"="+i[0]+"}" for i in cify_attrs(line[3].strip())) + '};')
                c_code.append('\t' * indentation + f'list* {file}___{line[1].strip()} = array_to_list(___b_a{bonus_c_variables["___b_a"]}, {line[3].count(",")+1});')
                bonus_c_variables['___b_a'] += 1
            variables[line[1].strip()] = '{'+datatype+'}'
        elif line := re.match(r'^\s*(.*)\s*:=\s*\{(.*)}\s*$', h): #variable creation - superposition inference
            cified = cify_attrs(line[2].strip())
            c_code.append('\t' * indentation + f'Quant ___b_a{bonus_c_variables["___b_a"]}[{line[2].count(",")+1}] = ' + '{' + ", ".join("{."+datatype_to_quant[i[1]]+"="+i[0]+"}" for i in cified) + '};')
            c_code.append('\t' * indentation + f'list* {file}___{line[1].strip()} = array_to_list(___b_a{bonus_c_variables["___b_a"]}, {line[2].count(",")+1});')
            bonus_c_variables['___b_a'] += 1
            datatype = cified[0][1].replace(' ', '')
            variables[line[1].strip()] = '{'+datatype+'}'
        elif line := re.match(r'^\s*(.*)\s+in\s+(.*)\s*=\s*(.*)', h): #variable creation
            datatype = line[2].replace(' ', '')
            bef_loop = len(c_code)
            eq_to = cify(line[3])
            if len(where_loops) > overall_indent:
                c_code.insert(bef_loop, '\t'*indentation + f'list* {file}___{line[1].strip()} = make_list();')
                malloc_indent[starting_where_len].append(['list', line[1].strip()])
                c_code.append('\t' * indentation + f'append({file}___{line[1].strip()}, {to_quant(copy_struct(eq_to))});')
                variables[line[1].strip()] = '{'+datatype+'}'
            else:
                c_code.append('\t'*indentation + f'{datatype_to_c[line[2].strip()]} {file}___{line[1].strip()} = {eq_to[0].strip()};')
                variables[line[1].strip()] = datatype
        elif line := re.match(r'^\s*(.*)\s*:=\s*(.*)', h): #variable creation type inference
            bef_loop = len(c_code)
            eq_to = cify(line[2])
            datatype = eq_to[1]
            if len(where_loops) > overall_indent:
                c_code.insert(bef_loop, '\t'*indentation + f'list* {file}___{line[1].strip()} = make_list();')
                malloc_indent[starting_where_len].append(['list', line[1].strip()])
                c_code.append('\t' * indentation + f'append({file}___{line[1].strip()}, {to_quant(copy_struct(eq_to))});')
                variables[line[1].strip()] = '{'+datatype+'}'
            else:
                c_code.append('\t'*indentation + f'{datatype_to_c[datatype]} {file}___{line[1].strip()} = {eq_to[0].strip()};')
                variables[line[1].strip()] = datatype
        elif line := re.match(r'^\s*check\s+(.*)\s*=>\s*"(.*)"\s*$', h): #check statement error handling
            if debug:
                c_code.append('\t' * indentation + f'if ({cify(line[1])[0]})' + ' {')
                indentation += 1
                c_code.append('\t' * indentation + f'printf("Runtime error on line {h0 + 1}: {line[2]}\\n");')
                error_print_function_stack()
                indentation -= 1
                c_code.append('\t' * indentation + f'exit(1);')
                c_code.append('\t' * indentation + '}')
        elif line := re.match(r'^\s*check\s+(.*)\s*$', h): #check statement multiline error handling
            debug_only = len(c_code)
            indentation_types.append(['check', overall_indent])
            malloc_indent.append([])
            c_code.append('\t' * indentation + f'if ({cify(line[1])[0]})' + ' {')
            indentation += 1
            c_code.append('\t' * indentation + f'int8_t ___is_error_raised = 0;')
            where_loops.append('')
            overall_indent = len(where_loops)
        elif line := re.match(r'^\s*raise\s*"(.*)"\s*$', h): #raise statement error handling
            if debug_only != -1:
                c_code.append('\t' * indentation + f'___is_error_raised = 1;')
                c_code.append('\t' * indentation + f'printf("Runtime error on line {h0 + 1}: {line[1]}\\n");')
                error_print_function_stack()
            elif debug:
                c_code.append('\t' * indentation + f'printf("Runtime error on line {h0 + 1}: {line[1]}\\n");')
                error_print_function_stack()
                c_code.append('\t' * indentation + f'exit(1);')
            else:
                c_code.append('\t' * indentation + f'printf("Runtime error on line {h0 + 1}: {line[1]}\\n");')
                c_code.append('\t' * indentation + f'exit(1);')
        elif line := re.match(r'^\s*(.*?)\s+(\+|-|\*|/|%||\*\*)=\s*(.*)\s*$', h): #variable change
            if line[2] == '':
                c_out = cify(line[3])
                c_code.append('\t' * indentation + f'{file}___{line[1].strip()} = {c_out[0].strip()};')
                close_where_loops(overall_indent)
            else:
                c_out = cify(line[3])
                c_code.append('\t' * indentation + f'{file}___{line[1].strip()} {line[2]}= {c_out[0].strip()};')
                close_where_loops(overall_indent)
        elif line := re.match(r'^\s*(.*?)\s+\+\+=\s*(.*)\s*$', h): #extend superposition ++
            bef_loop = len(c_code)
            c_out = cify(line[2])
            if line[1].strip() in where_loops or [line[1].strip(), 'paired'] in where_loops:
                c_var_name = f'___c_h{bonus_c_variables["___c_h"]}'
                bonus_c_variables["___c_h"] += 1
                c_code.insert(bef_loop, '\t' * indentation + f'list* {file}___{c_var_name} = make_list();')
                malloc_indent[starting_where_len].append(['list', c_var_name])
                variables[c_var_name] = variables[line[1].strip()]
                c_code.append('\t' * indentation + f'append({file}___{c_var_name}, {to_quant(copy_struct(c_out))}); //long concatenation')
                close_where_loops(overall_indent)
                c_code.append('\t' * indentation + f'for(int64_t {file}___{c_var_name}___l1 = 0; {file}___{c_var_name}___l1 < {file}___{c_var_name}->cur_size; {file}___{c_var_name}___l1++) append({file}___{line[1].strip()}, getitem({file}___{c_var_name}, {file}___{c_var_name}___l1)); //concatenation')
            else:
                c_code.append('\t' * indentation + f'append({file}___{line[1].strip()}, {to_quant(copy_struct(c_out))}); //concatenation')
                close_where_loops(overall_indent)
        elif line := re.match(r'^\s*$', h): #nothing
            pass
        elif h0 == 0 and re.match(r'^\s*debug\s*$', h): #debug mode
            debug = True
        else:
            print(f'Error when compiling line {h0+1}:')
            print(h)
            exit(1)

    close_where_loops(0)
    free_malloc_indent(malloc_indent.pop())

cify_all('main.ube')

print('''//Compiled by Uberort v1.2.0
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>
#include <math.h>
#include <string.h>
#include <sys/time.h>

typedef union {
    int64_t i;
    double f;
    void* s;
} Quant;

typedef struct {
    Quant* elements;
    int32_t size;
    int32_t cur_size;
} list;

list* make_list() {
    list* outp = malloc(sizeof(list));
    outp->size = 16;
    outp->cur_size = 0;
    outp->elements = malloc(sizeof(Quant)*16);
    return outp;
}

void destroy_list(list* self) {
    free(self->elements);
    free(self);
}

void append(list* self, Quant n) {
    if (self->size == self->cur_size) {
        self->elements = realloc(self->elements, sizeof(Quant)*self->size*2);
        self->size *= 2;
    }
    self->elements[self->cur_size++] = n;
}

list* array_to_list(Quant* arr, int32_t size) {
    list* outp = malloc(sizeof(list));
    outp->size = size;
    outp->cur_size = size;
    outp->elements = malloc(sizeof(Quant)*size);
    memcpy(outp->elements, arr, sizeof(Quant)*size);
    return outp;
}

Quant getitem(list* self, int32_t n) {
    return self->elements[n];
}

typedef struct {
    Quant key;
    Quant value;
    int32_t next; // index of next pair in case of collision
} KeyValuePair;

typedef struct {
    KeyValuePair* pairs;
    int32_t* table;
    int32_t size;
    int32_t cur_size;
    int32_t pair_count;
} dict;

uint32_t hash_int(Quant a) {
    return a.i*3 + ((a.i%63) << 3);
}

dict* make_dict() {
    dict* outp = malloc(sizeof(dict));
    outp->size = 16;
    outp->cur_size = 0;
    outp->pair_count = 0;
    outp->pairs = malloc(sizeof(KeyValuePair) * outp->size);
    outp->table = malloc(sizeof(int32_t) * outp->size);
    for (int i = 0; i < outp->size; i++) outp->table[i] = -1;
    return outp;
}

void destroy_dict(dict* self) {
    free(self->pairs);
    free(self->table);
    free(self);
}

void resize_and_rehash(dict* self) {
    int32_t old_size = self->size;
    self->size *= 4;
    self->pairs = realloc(self->pairs, sizeof(KeyValuePair) * self->size);
    int32_t* new_table = malloc(sizeof(int32_t) * self->size);
    for (int i = 0; i < self->size; i++) new_table[i] = -1;
    for (int i = 0; i < self->pair_count; i++) {
        uint32_t hash = hash_int(self->pairs[i].key) % self->size;
        self->pairs[i].next = new_table[hash];
        new_table[hash] = i;
    }
    free(self->table);
    self->table = new_table;
}


Quant dict_set(dict* self, Quant key, Quant value) {
    uint32_t hash = hash_int(key) % self->size;
    int32_t pair_index = self->table[hash];
    while (pair_index != -1) {
        if (memcmp(&self->pairs[pair_index].key, &key, sizeof(Quant)) == 0) {
            self->pairs[pair_index].value = value;
            return value;
        }
        pair_index = self->pairs[pair_index].next;
    }
    if (self->pair_count >= self->size*0.6) resize_and_rehash(self);
    self->pairs[self->pair_count].key = key;
    self->pairs[self->pair_count].value = value;
    self->pairs[self->pair_count].next = self->table[hash];
    self->table[hash] = self->pair_count;
    self->pair_count++;
    self->cur_size++;
    return value;
}

Quant dict_get(dict* self, Quant key) {
    uint32_t hash = hash_int(key) % self->size;
    int32_t pair_index = self->table[hash];
    while (pair_index != -1) {
        if (memcmp(&self->pairs[pair_index].key, &key, sizeof(Quant)) == 0) {
            return self->pairs[pair_index].value;
        }
        pair_index = self->pairs[pair_index].next;
    }
    printf("Error: dictionary key doesn't exist");
    exit(1);
}


int dict_has(dict* self, Quant key) {
    uint32_t hash = hash_int(key) % self->size;
    int32_t pair_index = self->table[hash];
    while (pair_index != -1) {
        if (memcmp(&self->pairs[pair_index].key, &key, sizeof(Quant)) == 0) {
            return 1;
            return 1;
        }
        pair_index = self->pairs[pair_index].next;
    }
    return 0;
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

double current_time() {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return tv.tv_sec + tv.tv_usec / 1000000.0;
}

double gauss_cd(double x) {
    return 0.5 * (1 + erf(x / sqrt(2)));
}
''')

if debug:
    print('list* ___debug_function_stack;\n')
print()
#if 'main' in functions:
#    print('\n'.join((['___debug_function_stack = make_list();'] if debug else []) + [i[1:] for i in c_code]))
#else:
print('\n'.join(['int main() {\n\tsrand ( time(NULL) );'] + (['___debug_function_stack = make_list();'] if debug else []) + c_code + ['}']))
print()
