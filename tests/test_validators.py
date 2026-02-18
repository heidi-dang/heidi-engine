import pytest
import shutil
from heidi_engine.validator import validate_code

def test_validate_python():
    valid_python = "def hello():\n    print('world')"
    invalid_python = "def hello(\n    print('world')"
    assert validate_code("python", valid_python) is True
    assert validate_code("python", invalid_python) is False

@pytest.mark.skipif(not shutil.which("g++"), reason="g++ not installed")
def test_validate_cpp():
    valid_cpp = "#include <iostream>\nint main() { return 0; }"
    invalid_cpp = "int main() { return 0"
    assert validate_code("cpp", valid_cpp) is True
    assert validate_code("cpp", invalid_cpp) is False

@pytest.mark.skipif(not shutil.which("node"), reason="node not installed")
def test_validate_javascript():
    valid_js = "function hello() { console.log('world'); }"
    invalid_js = "function hello() { console.log('world')"
    assert validate_code("javascript", valid_js) is True
    assert validate_code("javascript", invalid_js) is False

@pytest.mark.skipif(not shutil.which("go") and not shutil.which("gofmt"), reason="go/gofmt not installed")
def test_validate_go():
    valid_go = "package main\nimport \"fmt\"\nfunc main() { fmt.Println(\"hello\") }"
    invalid_go = "func main() { fmt.Println(\"hello\" }"
    assert validate_code("go", valid_go) is True
    assert validate_code("go", invalid_go) is False

def test_empty_code():
    assert validate_code("python", "") is False
    assert validate_code("python", "   ") is False
