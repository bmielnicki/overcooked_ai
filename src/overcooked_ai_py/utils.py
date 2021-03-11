import io, json, pickle, pstats, cProfile, os, tempfile, uuid, inspect  
import numpy as np
from numpy import nan
from collections import defaultdict
from pathlib import Path
from collections.abc import Iterable
from overcooked_ai_py.static import LAYOUTS_DIR
from collections.abc import Iterable

# I/O

def save_pickle(data, filename):
    with open(fix_filetype(filename, ".pickle"), "wb") as f:
        pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)

def load_pickle(filename):
    with open(fix_filetype(filename, ".pickle"), "rb") as f:
        return pickle.load(f)

def load_dict_from_file(filepath):
    with open(filepath, "r") as f:
        return eval(f.read())

def save_dict_to_file(dic, filename):
    dic = dict(dic)
    with open(fix_filetype(filename, ".txt"),"w") as f:
        f.write(str(dic))

def load_dict_from_txt(filename):
    return load_dict_from_file(fix_filetype(filename, ".txt"))

def save_as_json(data, filename):
    with open(fix_filetype(filename, ".json"), "w") as outfile:
        json.dump(data, outfile)
    return filename

def load_from_json(filename):
    with open(fix_filetype(filename, ".json"), "r") as json_file:
        return json.load(json_file)

def load_text_file(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()
        return "".join(lines)

def iterate_over_json_files_in_dir(dir_path):
    pathlist = Path(dir_path).glob("*.json")
    return [str(path) for path in pathlist]

def fix_filetype(path, filetype):
    if path[-len(filetype):] == filetype:
        return path
    else:
        return path + filetype

def generate_temporary_file_path(file_name=None, prefix="", suffix="", extension=""):
    if file_name is None:
        file_name = str(uuid.uuid1())
    if extension and not extension.startswith("."):
        extension = "." + extension
    file_name = prefix + file_name + suffix + extension
    return os.path.join(tempfile.gettempdir(), file_name)

# MDP

def cumulative_rewards_from_rew_list(rews):
    return [sum(rews[:t]) for t in range(len(rews))]

# Gridworld

def manhattan_distance(pos1, pos2):
    """Returns manhattan distance between two points in (x, y) format"""
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

def pos_distance(pos0, pos1):
    return tuple(np.array(pos0) - np.array(pos1))

# Randomness

def rnd_uniform(low, high):
    if low == high:
        return low
    return np.random.uniform(low, high)

def rnd_int_uniform(low, high):
    if low == high:
        return low
    return np.random.choice(range(low, high + 1))

# Statistics

def std_err(lst):
    """Computes the standard error"""
    sd = np.std(lst)
    n = len(lst)
    return sd / np.sqrt(n)

def mean_and_std_err(lst):
    "Mean and standard error of list"
    mu = np.mean(lst)
    return mu, std_err(lst)

# Other utils

def dict_mean_and_std_err(d):
    """
    Takes in a dictionary with lists as keys, and returns a dictionary
    with mean and standard error for each list as values
    """
    assert all(isinstance(v, Iterable) for v in d.values())
    result = {}
    for k, v in d.items():
        result[k] = mean_and_std_err(v)
    return result

def append_dictionaries(dictionaries):
    """
    Append many dictionaries with numbers as values into one dictionary with lists as values.

    {a: 1, b: 2}, {a: 3, b: 0}  ->  {a: [1, 3], b: [2, 0]}
    """
    assert all(set(d.keys()) == set(dictionaries[0].keys()) for d in dictionaries), "All key sets are the same across all dicts"
    final_dict = defaultdict(list)
    for d in dictionaries:
        for k, v in d.items():
            final_dict[k].append(v)
    return dict(final_dict)

def merge_dictionaries(dictionaries):
    """
    Merge many dictionaries by extending them to one another.
    {a: [1, 7], b: [2, 5]}, {a: [3], b: [0]}  ->  {a: [1, 7, 3], b: [2, 5, 0]}
    """
    assert all(set(d.keys()) == set(dictionaries[0].keys()) for d in dictionaries), "All key sets are the same across all dicts"
    final_dict = defaultdict(list)
    for d in dictionaries:
        for k, v in d.items():
            final_dict[k].extend(v)
    return dict(final_dict)

def rm_idx_from_dict(d, idx):
    """
    Takes in a dictionary with lists as values, and returns
    a dictionary with lists as values, but containing 
    only the desired index

    NOTE: this is a MUTATING METHOD, returns the POPPED IDX
    """
    assert all(isinstance(v, Iterable) for v in d.values())
    new_d = {}
    for k, v in d.items():
        new_d[k] = [d[k].pop(idx)]
    return new_d

def take_indexes_from_dict(d, indices, keys_to_ignore=[]):
    """
    Takes in a dictionary with lists as values, and returns
    a dictionary with lists as values, but with subsampled indices
    based on the `indices` input 
    """
    assert all(isinstance(v, Iterable) for v in d.values())
    new_d = {}
    for k, v in d.items():
        if k in keys_to_ignore: continue
        new_d[k] = np.take(d[k], indices)
    return new_d

def profile(fnc):
    """A decorator that uses cProfile to profile a function (from https://osf.io/upav8/)"""
    def inner(*args, **kwargs):
        pr = cProfile.Profile()
        pr.enable()
        retval = fnc(*args, **kwargs)
        pr.disable()
        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats("cumulative")
        ps.print_stats()
        print(s.getvalue())
        return retval
    return inner

def numpy_to_native(x):
    if isinstance(x, np.generic):
        return x.item()
    else:
        return x

class NumpyArrayEncoder(json.JSONEncoder):
    # code taken from https://pynative.com/python-serialize-numpy-ndarray-into-json
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super(NumpyArrayEncoder, self).default(obj)

def read_layout_dict(layout_name):
    return load_dict_from_file(os.path.join(LAYOUTS_DIR, layout_name + ".layout"))

class classproperty(property):
    def __get__(self, cls, owner):
        return classmethod(self.fget).__get__(None, owner)()

def is_iterable(obj):
    return isinstance(obj, Iterable)

# based on code from https://stackoverflow.com/questions/480214/how-do-you-remove-duplicates-from-a-list-whilst-preserving-order
def delete_duplicates(seq):
    seen = set()
    seen_add = seen.add
    def serialize_if_dict_or_list(d):
        if isinstance(d, list) or isinstance(d, dict):
            return json.dumps(d, sort_keys=True)
        else:
            return d
    return [x for x in seq if not (serialize_if_dict_or_list(x) in seen or seen_add(serialize_if_dict_or_list(x)))]

def only_valid_named_args(kwargs, function, kwargs_accepted=True):
    """returns trimmed kwargs out of arguments that are not in function argument names
    if kwargs accepted=True and function accept **kwargs then pass any named arguments
    """
    arg_names, var_args_name, kwargs_name, defaults = inspect.getargspec(function)
    if kwargs_name and kwargs_accepted:
        return kwargs
    else:
        return {k:v for k,v in kwargs.items() if k in arg_names}
