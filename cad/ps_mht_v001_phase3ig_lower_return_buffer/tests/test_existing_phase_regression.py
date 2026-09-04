from ps_mht_v001_phase3ig_lower_return_buffer.src.phase3ig_lower_return_buffer import regression_audit_phase3ig


def test_phase3id_sha_authority_is_unchanged():
    assert regression_audit_phase3ig()["checks"]["phase3id"]["all_unchanged"]


def test_phase3if_sha_authority_is_unchanged():
    assert regression_audit_phase3ig()["checks"]["phase3if"]["all_unchanged"]


def test_all_inherited_sha_entries_exist_and_match():
    audit = regression_audit_phase3ig()
    assert audit["all_unchanged"]
    assert audit["checks"]["phase3id"]["entry_count"] == 51
    assert audit["checks"]["phase3if"]["entry_count"] == 53


def test_git_mutation_operations_not_performed():
    assert regression_audit_phase3ig()["git_mutation_operations_performed"] is False

