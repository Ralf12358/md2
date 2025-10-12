from md2 import runtime


def test_rebuild_image_function_exists():
    assert hasattr(runtime, 'rebuild_image')
    assert callable(runtime.rebuild_image)


def test_runtime_module_functions():
    assert hasattr(runtime, 'get_container_runtime')
    assert hasattr(runtime, 'ensure_image')
    assert hasattr(runtime, 'rebuild_image')
    assert hasattr(runtime, 'image_exists')
