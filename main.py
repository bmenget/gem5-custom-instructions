import sys
from stages import (
    s1_verify_manifest as s1, 
    s2_record_changes as s2,
    s3_copy_gem5 as s3
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

        change_files = io.load_change_files()
        template_files = io.load_template_files()
        fu_mappings = io.load_json(paths.TEMPLATES_DIR / "FU-mappings.json")
        
        s3.copy_gem5_files(change_files, template_files, fu_mappings)





    except Exception as error:
        print(error, file=sys.stderr)
        return 1

    return 0

if __name__ == "__main__":
    raise SystemExit(main())