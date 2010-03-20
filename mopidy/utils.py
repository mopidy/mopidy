import logging
from multiprocessing.reduction import reduce_connection
import pickle

logger = logging.getLogger('mopidy.utils')

def flatten(the_list):
    result = []
    for element in the_list:
        if isinstance(element, list):
            result.extend(flatten(element))
        else:
            result.append(element)
    return result

def get_class(name):
    module_name = name[:name.rindex('.')]
    class_name = name[name.rindex('.') + 1:]
    logger.info('Loading: %s', name)
    module = __import__(module_name, globals(), locals(), [class_name], -1)
    class_object = getattr(module, class_name)
    return class_object

def indent(string, places=4, linebreak='\n'):
    lines = string.split(linebreak)
    if len(lines) == 1:
        return string
    result = u''
    for line in lines:
        result += linebreak + ' ' * places + line
    return result

def pickle_connection(connection):
    return pickle.dumps(reduce_connection(connection))

def unpickle_connection(pickled_connection):
    # From http://stackoverflow.com/questions/1446004
    unpickled = pickle.loads(pickled_connection)
    func = unpickled[0]
    args = unpickled[1]
    return func(*args)
