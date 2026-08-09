"""The full phase x file-class permission table for the edit gate.

The audit found the gate's actual behaviour drifting from its documented
contract in ways no single-case test caught (notably: `phase: document` was
blocked from doing its own retro work). This table IS the contract — every
phase, every class of target, one expected verdict each.

Read the tables below as: in phase <row>, writing <column> is allow/block.
"""

import pytest

from conftest import plan_with, run_hook

ALLOW, BLOCK = 0, 2

IN_SCOPE = "taskler.py"
IN_SCOPE_DOC = "tests/notes.md"   # doc-extension file inside the plan's scope
OUT_OF_SCOPE = "src/unrelated.py"
SPECS_FILE = "specs/001-x/notes.md"
ROOT_CHANGELOG = "CHANGELOG.md"
ROOT_README = "README.md"

# phase -> is the plan gate approved in that phase
PLAN_APPROVED = {"requirements": False, "plan": False, "implement": True,
                 "verify": True, "document": True, "done": True}

# phase -> {target: expected exit code}
EDIT_MATRIX = {
    "requirements": {IN_SCOPE: BLOCK, IN_SCOPE_DOC: BLOCK, OUT_OF_SCOPE: BLOCK,
                     SPECS_FILE: ALLOW, ROOT_CHANGELOG: ALLOW, ROOT_README: ALLOW},
    "plan":         {IN_SCOPE: BLOCK, IN_SCOPE_DOC: BLOCK, OUT_OF_SCOPE: BLOCK,
                     SPECS_FILE: ALLOW, ROOT_CHANGELOG: ALLOW, ROOT_README: ALLOW},
    "implement":    {IN_SCOPE: ALLOW, IN_SCOPE_DOC: ALLOW, OUT_OF_SCOPE: BLOCK,
                     SPECS_FILE: ALLOW, ROOT_CHANGELOG: ALLOW, ROOT_README: ALLOW},
    "verify":       {IN_SCOPE: ALLOW, IN_SCOPE_DOC: ALLOW, OUT_OF_SCOPE: BLOCK,
                     SPECS_FILE: ALLOW, ROOT_CHANGELOG: ALLOW, ROOT_README: ALLOW},
    # document does the retro's own DOC work, in scope — but code stays frozen
    # once verified: shipped must equal verified (review finding, v1.2.1)
    "document":     {IN_SCOPE: BLOCK, IN_SCOPE_DOC: ALLOW, OUT_OF_SCOPE: BLOCK,
                     SPECS_FILE: ALLOW, ROOT_CHANGELOG: ALLOW, ROOT_README: ALLOW},
    # a shipped feature re-locks everything
    "done":         {IN_SCOPE: BLOCK, IN_SCOPE_DOC: BLOCK, OUT_OF_SCOPE: BLOCK,
                     SPECS_FILE: ALLOW, ROOT_CHANGELOG: ALLOW, ROOT_README: ALLOW},
}


def _feature(repo, phase):
    repo.write_feature(phase=phase, spec=True, plan=PLAN_APPROVED[phase],
                       plan_md=plan_with(IN_SCOPE, "tests/test_taskler.py"))


@pytest.mark.parametrize(
    "phase,target,expected",
    [(phase, target, expected)
     for phase, row in EDIT_MATRIX.items()
     for target, expected in row.items()],
    ids=lambda v: str(v),
)
def test_edit_permission_matrix(repo, phase, target, expected):
    _feature(repo, phase)
    payload = {"cwd": str(repo), "tool_name": "Edit",
               "tool_input": {"file_path": str(repo / target)}}
    code, out = run_hook("gate_check.py", payload)
    assert code == expected, f"{phase} x {target}: exit {code}\n{out}"


@pytest.mark.parametrize(
    "phase,target,expected",
    [(phase, target, EDIT_MATRIX[phase][target])
     for phase in EDIT_MATRIX
     for target in (IN_SCOPE, OUT_OF_SCOPE)],
    ids=lambda v: str(v),
)
def test_bash_write_follows_the_same_matrix(repo, phase, target, expected):
    """A shell redirect is judged exactly like the equivalent Edit."""
    _feature(repo, phase)
    payload = {"cwd": str(repo), "tool_name": "Bash",
               "tool_input": {"command": f"echo x > {target}"}}
    code, out = run_hook("gate_check.py", payload)
    assert code == expected, f"{phase} x {target}: exit {code}\n{out}"
