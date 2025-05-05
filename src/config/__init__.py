"""
This is the config package.

This package is responsible for reading the config data from a 
yaml file and retuning the Config pydantic object.

Example usage:

    from src.config.config import Config

    # Example of binding data to the field data
    cfg = Config.from_yaml(
        "path_to_the_config folder", "environment_name" 
    )
"""