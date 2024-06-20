with open("compiler.meow", 'r') as meow:
    code = meow.read()
    
lines = [i.strip() for i in code.split("\n")]

init_vars = set()

data = ["""TITLE 
INCLUDE Irvine32.inc

.data
"""]
main = [".code\nmain PROC\n"]
end = ["exit\nmain ENDP\n\nEND main\n"]
pool = []

i = 0
# Обработка токенов
def tokenizer(text: str):    
    token = ""
    tokens = []
    spec = ['-', '+', '=', '/', '*', '<', '>', '%', '&', '|', ' ', '(', ')', '@', '!']
    d_spec = "<>=!"
    is_double = False
    
    for char in text:
        if char in spec:
            if is_double and char in d_spec:
                tokens[-1] += char
            else:
                if token != "":
                    tokens += [token]
                    token = ""
                if char != ' ':
                    tokens += [char]
                    is_double = True
        else:
            is_double = False
            token += char
            
    return tokens + [token] if token != "" else tokens

class Node:
    def findType(self, token):
        if token in ['+', '-', '*', '/', '>', '<', '%', '|', '&', '>=', '<=', '==', '!=']:
            return "Operator"
        elif token in init_vars:
            return "Variable"
        else:
            return "Value"
        
    def __init__(self, token, level):
        self.value = token
        self.level = level
        self.nodetype = self.findType(token) # ["Operator","Variable","Value"]
        self.parent = None
        self.right = None
        self.left = None

class TREE:
    def __init__(self):
        self.tree = []
        self.root = None
    
    def pull(self):
        level_count = 0
        prev_count = 0
        
        
        for token in tokens:
            prev_count = len(self.tree) - 1
            if token == '(':
                level_count += 1
                continue
            if token == ')':
                level_count -= 1
                continue
            node = Node(token, level_count)
            self.tree.append(node)
            id_node = len(self.tree) - 1
            
            if id_node == 0:
                self.root = id_node
                continue
            prev_count = id_node - 1
            prev_node = self.tree[prev_count]
            if id_node == 1:
                self.root = id_node
                node.right = prev_count
                prev_node.parent = id_node
                continue
            elif prev_node.nodetype == "Operator":
                prev_node.left = prev_node.right
                prev_node.right = id_node
                node.parent = prev_count
            else:
                while prev_node.level > node.level:
                    if prev_node.parent is not None:
                        prev_count = prev_node.parent
                        prev_node = self.tree[prev_count]
                    else:
                        break
                if prev_node.nodetype != "Operator":
                    
                    prev_count = prev_node.parent
                    prev_node = self.tree[prev_count]
                if prev_node.level > node.level or not ((prev_node.value not in "*/%&") and (node in "*/%&")):
                    if prev_node.parent is not None:
                        self.tree[prev_node.parent].right = id_node
                        node.parent = prev_node.parent
                        prev_node.parent = id_node
                        node.right = prev_count
                        
                    else:
                        self.root = id_node
                        node.right = prev_count
                        prev_node.parent = id_node
                        
                else:
                    self.tree[prev_node.right].parent - id_node
                    node.right = prev_node.right 
                    prev_node.right = id_node
                    node.parent = prev_count
                    
            self.tree[prev_count] = prev_node
            self.tree[id_node] = node
            
    def print_tree(self):
        for i in self.tree:
            print("значение", i.value, "родитель", i.parent)
            
def calculate(main):
    tree = TREE()
    tree.pull()
    tree_to_asm(tree, main)
    

def tree_to_asm(tree, main):
    push_node(tree, tree.root, main)

def push_node(tree, id_node, main):
    global lab_count
    node = tree.tree[id_node]
    if node.nodetype != "Operator":
        main += [f"push {node.value}\n"]
    else:
        push_node(tree, node.right, main)
        push_node(tree, node.left, main)
        
        operation = oper_to_asm(node.value)
        
        main += [f"pop eax\n"]
        
        if operation == "idiv":
            main += [f"cdq\n"]
            
        main += [f"pop ebx\n"]
        
        main += [f"{operation} "]
        
        if operation == "idiv":
            main += [f"ebx\n"]
            
            if node.value == "%":
                main += [f"push edx\n"]
            else:
                main += [f"push eax\n"]
        else:
            main += [f"eax, ebx\n"]
            
            if operation == "cmp":
                jump = what_jump_are_you(node.value)
                main += [f"""{jump} pos{lab_count}
push 0
jmp neg{lab_count}
pos{lab_count}:
push 1
neg{lab_count}:\n"""]
                
                lab_count += 1
            else:
                main += [f"push eax\n"]
            
        
def oper_to_asm(oper: str) -> str:
    match oper:
        case "+":
            return "add"
        case "-":
            return "sub"
        case "*":
            return "imul"
        case "|":
            return "or"
        case "&":
            return "and"
        case ">" | "<" | ">=" | "<=" | "!=" | "==" :
            return "cmp"
        case "%" | "/":
            return "idiv"

        
def what_jump_are_you(token):
    match token:
        case ">":
            return "ja"
        case "<":
            return "jl"
        case "==":
            return "je"
        case ">=":
            return "jge"
        case "<=":
            return "jle"
        case "!=":
            return "jne"
        case _:
            return "jmp"


            
lab_count = 0
loop_count = 0
while i < len(lines):
    tokens = tokenizer(lines[i])
        
    if not tokens:
        i += 1
        continue

    if tokens[0] == "@":
        main.append(pool.pop())
        i += 1
        continue
        
    if tokens[0] == "while":
        tokens = tokens[1:]
        main.append(f"LOOP{loop_count}:\n")
        calculate(main)
        main.append(f"pop eax\ncmp eax, 0\njne START{lab_count}\njmp END{lab_count}\n")
        # добавление начала и конца блока кода
        main.append(f"START{lab_count}:\n")
        pool.append(f"jmp LOOP{loop_count}\nEND{lab_count}:\n")
        loop_count += 1
        lab_count += 1
        
    elif tokens[0] == "if":
        tokens = tokens[1:]
        calculate(main)
        main.append(f"pop eax\ncmp eax, 0\njne START{lab_count}\njmp END{lab_count}\n")
        # добавление начала и конца блока кода
        main.append(f"START{lab_count}:\n")
        pool.append(f"END{lab_count}:\n")
        lab_count += 1
    
    
        
    elif tokens[0] == "print":
        tokens = tokens[1:]
        
        if tokens[0][0] == "'":
            tokens[0] = tokens[0][1:]
            stroka = " ".join(tokens)
            
            for p in reversed(stroka):
                main += [f"push \'{p}\'\n"]
                
            main += [f"""mov ecx, {len(stroka)}
print_LOOP{lab_count}:
pop eax
call WriteChar
loop print_LOOP{lab_count}\n"""]
            lab_count += 1
            
        else: 
            calculate(main)
            main += ['pop eax\ncall WriteInt\n']

        main += ["""
call Crlf\n"""]
    
    else:
        name = tokens[0]
        tokens = tokens[2:]
        
        if name not in init_vars:
            init_vars.add(name)
            data += [f"{name} dd ?\n"]
        
        calculate(main)
        main += ["pop eax\n", f"mov {name}, eax\n"]
        
    i += 1
    main.append("\n")



with open("compiler.asm", "w") as f:
    f.write("".join(data) + "\n")
    f.write("".join(main) + "\n")
    f.write("".join(end))
