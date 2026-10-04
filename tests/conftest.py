import matplotlib as mpl
import pytest

mpl.use("Agg")


@pytest.fixture(autouse=True)
def restore_rc():
    with mpl.rc_context():
        yield
