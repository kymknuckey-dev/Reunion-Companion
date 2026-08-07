from reunion_companion.foundation import from_semantic_database
from reunion_companion.model import Person, ReunionDatabase


def test_from_semantic_database_uses_foundation_builder() -> None:
    semantic = ReunionDatabase(
        package_path="/tmp/Test.familyfile14",
        version="14+",
        people={
            1: Person(
                id=1,
                given="Test",
                surname="Probe",
                display="Test Probe",
                sex="male",
            )
        },
        families={},
        warnings=[],
    )

    foundation = from_semantic_database(semantic)

    assert foundation.person(1).full_name == "Test Probe"
    assert foundation.package_path == semantic.package_path
