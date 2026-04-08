def assert__is_str(obj):
    if not isinstance(obj, str):
        raise TypeError("❌ param must be of type str")
    return True

def assert__is_list_of_str(obj):
    if not (isinstance(obj, list) and all(isinstance(s, str) for s in obj)):
        raise TypeError("❌ param must be of type list[str]")
    return True

def assert__is_list_of_list_of_str(obj):
    if not (isinstance(obj, list) and all(isinstance(sub, list) and all(isinstance(s, str) for s in sub) for sub in obj)):
        raise TypeError("❌ param must be of type list[list[str]]")
    return True

def assert__is_list_of_tuple_of_str(obj):
    if not (isinstance(obj, list) and all(isinstance(sub, tuple) and all(isinstance(s, str) for s in sub) for sub in obj)):
        raise TypeError("❌ param must be of type list[tuple[str]]")
    return True


