import sys
from stages import (
    s1_verify_manifest as s1, 
    s2_record_changes as s2,
)
from shared import io_utils as io
from shared import paths

def main():
    '''Main function to run the verification stage.'''

    try:
        yaml_file = io.load_yaml(paths.INSTRUCTIONS_PATH)
        opclass_file = io.load_json(paths.OPCLASSES_PATH)

        s1.verify_manifest(yaml_file, opclass_file)

        registries = io.load_registries()
        
        s2.record_changes(yaml_file, registries)


    except Exception as error:
        print(error, file=sys.stderr)
        return 1

    return 0

if __name__ == "__main__":
    raise SystemExit(main())