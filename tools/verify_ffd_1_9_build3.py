#!/usr/bin/env python3
import subprocess
files=['tests/test_ffd_1_9_build3_clean_recovery.py', 'tests/test_beta3_2_sprint1_timeline_ui.py', 'tests/test_ffd_1_8_build1_2_presentation_publishing_ux.py', 'tests/test_ffd_build1_1_home_presentation.py', 'tests/test_ffd_build1_2_presentation_mode.py', 'tests/test_ffd_build1_3_2_visual_alignment.py', 'tests/test_ffd_build1_3_3_timeline_visual_alignment.py', 'tests/test_ffd_build1_3_4_person_story_event_style.py', 'tests/test_ffd_build1_3_5_presentation_metadata.py', 'tests/test_ffd_build1_3_person_story.py']
r=subprocess.run(["python","-m","pytest","-q"]+files)
print("\nFFD 1.9 Build 3 verification "+("PASSED." if r.returncode==0 else "FAILED."))
raise SystemExit(r.returncode)
