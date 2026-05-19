""" Utility functions for handling images """


def is_image_name_valid(image_name):
    """ Check if the image name is not None and not an empty string.

    Args:
        image_name (str): The name of the image file.

    Returns:
        bool: True if the image name is valid, False otherwise.
    """
    return image_name is not None and image_name != ""


def get_default_user_image():
    """ Get the default user image

    Returns:
        str: The filename of the default user image.
    """
    return "default_user_image.png"
