import sys
from stages import (
    stage1_verify as s1, 
    stage2_find_changes as s2,
)
from shared import io_utils as io
from shared import paths

def main():
    '''Main function to run the verification stage.'''

    try:
        yaml_file = io.load_yaml(paths.INSTRUCTIONS_PATH)
        opclass_file = io.load_json(paths.OPCLASSES_PATH)

        s1.verify_yaml(yaml_file, opclass_file)

        registries = io.load_registries()
        s2.record_changes(yaml_file, registries)


    except ValueError as error:
        print(error, file=sys.stderr)
        return 1

    return 0

if __name__ == "__main__":
    raise SystemExit(main())