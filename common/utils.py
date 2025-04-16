"""
Common Utility Functions

This module includes a collection of helper functions that may be used across
the project. Functions include:

    - generate_random_string: Create a random alphanumeric string.
    - safe_cast: Safely cast a value to a desired type with a default fallback.
    - get_env_variable: Retrieve environment variables, optionally requiring them.
    - parse_boolean: Convert values (including strings) to booleans.
    - chunk_generator: Yield successive chunks from an iterable.
"""

import os
import random
import string
import logging

logger = logging.getLogger(__name__)


def generate_random_string(length=8):
    """
    Generate a random alphanumeric string of specified length.

    Args:
        length (int): The length of the generated string. Default is 8.

    Returns:
        str: A random alphanumeric string.
    """
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))


def safe_cast(val, to_type, default=None):
    """
    Safely cast a value to the specified type, returning a default if casting fails.

    Args:
        val: The value to cast.
        to_type: The type to cast the value to (e.g., int, float).
        default: The default value to return if casting fails (default is None).

    Returns:
        The value cast to the desired type, or the default.
    """
    try:
        return to_type(val)
    except (ValueError, TypeError):
        logger.warning("Failed to cast value %r to type %r; returning default %r", val, to_type, default)
        return default


def get_env_variable(var_name, default=None, required=False):
    """
    Retrieve an environment variable with an option to require its presence.

    Args:
        var_name (str): The name of the environment variable.
        default: A default value to return if the variable is not set (default is None).
        required (bool): If True, an exception is raised if the variable is not found.

    Returns:
        The value of the environment variable, or the default.

    Raises:
        Exception: If 'required' is True and the environment variable is not set.
    """
    value = os.environ.get(var_name, default)
    if required and value is None:
        raise Exception(f"Environment variable '{var_name}' is required but not set.")
    return value


def parse_boolean(value):
    """
    Parse a boolean value from a given input.

    Args:
        value: A value that should represent a boolean (e.g., "True", "false", 1, 0).

    Returns:
        bool: The parsed boolean value.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ['true', '1', 't', 'yes']
    return bool(value)


def chunk_generator(iterable, chunk_size):
    """
    Yield successive chunks of a specified size from an iterable.

    Args:
        iterable: An iterable data source.
        chunk_size (int): The maximum size of each chunk.

    Yields:
        list: Chunks of the iterable, each of size 'chunk_size' (except possibly the last one).
    """
    chunk = []
    for item in iterable:
        chunk.append(item)
        if len(chunk) == chunk_size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk


# Example usage when running this module directly.
if __name__ == "__main__":
    # Test generate_random_string
    random_str = generate_random_string(10)
    print("Random String (10 chars):", random_str)

    # Test safe_cast
    casted_value = safe_cast("123", int, default=0)
    print("Safe Cast ('123' to int):", casted_value)
    cast_fail = safe_cast("abc", int, default=-1)
    print("Safe Cast ('abc' to int):", cast_fail)

    # Test get_env_variable
    home_dir = get_env_variable("HOME", default="Not Set")
    print("HOME environment variable:", home_dir)

    # Test parse_boolean
    bool_value = parse_boolean("Yes")
    print('Parsed Boolean ("Yes"):', bool_value)

    # Test chunk_generator
    data = range(1, 11)  # 1 through 10
    print("Chunks of size 3:")
    for chunk in chunk_generator(data, 3):
        print(chunk)
