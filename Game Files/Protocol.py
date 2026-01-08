import ast


def unpack(msg):
    """
    unpack messages according to protocol
    :return:
    """
    ret = "", ""
    split = msg.split('^')
    if len(split) == 2:
        if split[0] in ['b', 'u', 'o']:
            split[1] = ast.literal_eval(split[1])
        ret = split[0], split[1]
    return ret


def build_msg(opcode, msg):
    """
    create a message according to protocol
    :return:
    """
    return f"{opcode}^{msg}"


